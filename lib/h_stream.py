import numpy as np, pandas as pd, os, gc, time
from pathlib import Path

_D = os.environ.get("LSPR_DIR", "/tmp")
CSV = os.environ.get("LSPR_CSV", f"{_D}/lspr_full.csv")
CACHE = Path(os.environ.get("LSPR_CACHE", f"{_D}/lspr_cache"))
_COLS = ["ts", "src", "dst", "label", "proto"] + [f"f{i}" for i in range(32)]
_FEAT = ["proto"] + [f"f{i}" for i in range(32)]


PORTS = os.environ.get("LSPR_PORTS", f"{_D}/lspr_ports.csv")


def _slash24_codes(cats):
    """Map IP-string categories to /24 prefix codes.  Non-dotted-quad values (IPv6 or"""
    pref = np.array([s.rsplit(".", 1)[0] if s.count(".") == 3 else s for s in cats.astype(str)])
    _, codes = np.unique(pref, return_inverse=True)
    return codes.astype(np.int32)


def _build_cache(verbose=True):
    t0 = time.time()
    dt = {"ts": "int64", "src": "category", "dst": "category", "label": "int8",
          "proto": "float32"}
    dt.update({f"f{i}": "float32" for i in range(32)})
    df = pd.read_csv(CSV, header=None, names=_COLS, dtype=dt, low_memory=False)
    perm = np.argsort(df["ts"].to_numpy(), kind="mergesort")
    df = df.iloc[perm].reset_index(drop=True)
    X = df[_FEAT].to_numpy(dtype=np.float32, copy=True)
    np.nan_to_num(X, copy=False, nan=0.0, posinf=0.0, neginf=0.0)
    CACHE.mkdir(parents=True, exist_ok=True)
    np.save(CACHE / "X.npy", X)
    np.save(CACHE / "y.npy", df["label"].to_numpy())
    np.save(CACHE / "ts.npy", df["ts"].to_numpy())
    np.save(CACHE / "perm.npy", perm)
    src_codes = df["src"].cat.codes.to_numpy(dtype=np.int32)
    dst_codes = df["dst"].cat.codes.to_numpy(dtype=np.int32)
    if (src_codes < 0).any() or (dst_codes < 0).any():
        raise ValueError("missing src/dst category codes; /24 mapping would be wrong")
    np.save(CACHE / "src.npy", src_codes)
    np.save(CACHE / "dst.npy", dst_codes)
    np.save(CACHE / "src24.npy", _slash24_codes(df["src"].cat.categories.to_numpy())[src_codes])
    np.save(CACHE / "dst24.npy", _slash24_codes(df["dst"].cat.categories.to_numpy())[dst_codes])
    del df, X; gc.collect()
    if os.path.exists(PORTS):
        pr = pd.read_csv(PORTS, header=None, names=["sport", "dport"],
                         dtype={"sport": "float32", "dport": "float32"}, low_memory=False)
        if len(pr) != len(perm):
            raise ValueError(f"{PORTS} has {len(pr):,} rows but the flow file has {len(perm):,}; "
                             "it must be extracted from the same csv with the same NR>1 filter")
        np.save(CACHE / "sport.npy", np.nan_to_num(pr["sport"].to_numpy())[perm].astype(np.int32))
        np.save(CACHE / "dport.npy", np.nan_to_num(pr["dport"].to_numpy())[perm].astype(np.int32))
        del pr; gc.collect()
    if verbose:
        print(f"  [h_stream] built cache in {time.time()-t0:.0f}s -> {CACHE}")


def load_extra(name):
    """Load an optional cached column: 'src24', 'dst24', 'sport', 'dport'."""
    f = CACHE / f"{name}.npy"
    if not f.exists():
        raise FileNotFoundError(
            f"{f} missing. Delete {CACHE} and re-run to rebuild; ports additionally need "
            f"{PORTS}, produced by:  awk -F',' 'NR>1 {{print $4\",\"$5}}' ls23pr_v1.csv > {PORTS}")
    return np.load(f)


def load(verbose=True):
    """Return (X, y, ts, src, dst), memory-mapped where possible."""
    need = ["X.npy", "y.npy", "ts.npy", "src.npy", "dst.npy", "src24.npy", "dst24.npy"]
    if not all((CACHE / f).exists() for f in need):
        if not os.path.exists(CSV):
            raise FileNotFoundError(
                f"{CSV} is missing. Regenerate it with the awk recipe in docs/01_HANDOFF_PHASE4.md section 2.2.")
        _build_cache(verbose)
    t0 = time.time()
    X = np.load(CACHE / "X.npy", mmap_mode="r")
    y = np.load(CACHE / "y.npy")
    ts = np.load(CACHE / "ts.npy")
    src = np.load(CACHE / "src.npy")
    dst = np.load(CACHE / "dst.npy")
    if verbose:
        print(f"  [h_stream] loaded N={len(y):,} malicious={int(y.sum()):,} "
              f"({100*y.mean():.2f}%) in {time.time()-t0:.1f}s")
    return X, y, ts, src, dst


def split_indices(N, pos, cal_f=0.15, test_f=0.15):
    i2 = int(pos * N); i1 = i2 - int(cal_f * N); i3 = min(N, i2 + int(test_f * N))
    return i1, i2, i3


def train_index(y, i1, seed, subsample_benign=0.5):
    """Training rows: every malicious flow plus a `subsample_benign` fraction of benign,"""
    rng = np.random.default_rng(seed)
    tr = np.arange(i1); ben = tr[y[tr] == 0]
    keep = ben[rng.random(len(ben)) < subsample_benign]
    return np.sort(np.concatenate([tr[y[tr] == 1], keep]))


def fit_detector(X, y, i1, seed, kind="hgb", verbose=True):
    """Return a callable score(rows_slice) -> higher means more attack-like."""
    t0 = time.time()
    if kind == "hgb":
        from sklearn.ensemble import HistGradientBoostingClassifier
        tr_idx = train_index(y, i1, seed)
        clf = HistGradientBoostingClassifier(
            max_iter=200, learning_rate=0.1, l2_regularization=1.0, min_samples_leaf=200,
            random_state=seed, early_stopping=False).fit(np.asarray(X[tr_idx]), y[tr_idx])
        fn = lambda Z: clf.decision_function(Z)
    elif kind == "iforest":
        from sklearn.ensemble import IsolationForest
        rng = np.random.default_rng(seed)
        n_fit = min(i1, 2_000_000)
        rows = np.sort(rng.choice(i1, n_fit, replace=False)) if n_fit < i1 else np.arange(i1)
        clf = IsolationForest(n_estimators=200, max_samples=8192, contamination="auto",
                              random_state=seed, n_jobs=-1).fit(np.asarray(X[rows]))
        fn = lambda Z: -clf.score_samples(Z)
    else:
        raise ValueError(kind)
    if verbose:
        print(f"  [h_stream] fitted {kind} seed={seed} in {time.time()-t0:.0f}s")
    return fn


def score_windows(score_fn, X, i1, i2, i3, chunk=2_000_000):
    """Score the calibration and test windows in chunks (X may be memory-mapped)."""
    def _sc(a, b):
        out = np.empty(b - a, dtype=np.float64)
        for s in range(a, b, chunk):
            e = min(s + chunk, b)
            out[s - a:e - a] = score_fn(np.asarray(X[s:e]))
        return out
    return _sc(i1, i2), _sc(i2, i3)


def evalues(s_cal, y_cal, s_te, k=1):
    """Threshold conformal e-value at rank k (section 2.2)."""
    cal = np.sort(s_cal[y_cal == 0]); NC = len(cal)
    CEIL = (NC + 1.0) / k
    Kr = 1 + (NC - np.searchsorted(cal, s_te, side='left'))
    return np.where(Kr <= k, CEIL, 0.0), cal, NC, CEIL


KEYED_SEED = 0xC0FFEE123456789


def _mix64(x):
    with np.errstate(over="ignore"):
        x = np.asarray(x, dtype=np.uint64).copy()
        x ^= (x >> np.uint64(30)); x *= np.uint64(0xBF58476D1CE4E5B9)
        x ^= (x >> np.uint64(27)); x *= np.uint64(0x94D049BB133111EB)
        x ^= (x >> np.uint64(31))
    return x


def key_hash(*key_vals, seed=0):
    if not key_vals:
        raise ValueError("key_hash needs at least one key array")
    n = len(np.asarray(key_vals[0]))
    with np.errstate(over="ignore"):
        h = np.full(n, np.uint64(0x9E3779B97F4A7C15), dtype=np.uint64) ^ np.uint64(seed)
        for a in key_vals:
            h = _mix64(h ^ np.asarray(a, dtype=np.int64).astype(np.uint64))
    return h


def hashed_order(hkey, *key_vals):
    if not key_vals:
        raise ValueError("hashed_order needs at least one key array")
    h63 = (np.asarray(hkey, dtype=np.uint64) & np.uint64((1 << 63) - 1)).astype(np.int64)
    bucket = np.asarray(key_vals[-1], dtype=np.int64)
    tie = [np.asarray(a, dtype=np.int64) for a in key_vals[:-1]]
    return np.lexsort(tuple(reversed(tie)) + (h63, bucket))


ORDERS = ("first-flow", "keyhash", "keyed")


def build_episodes(e_te, y_te, ts_w, src_w=None, dst_w=None, bucket_s=None,
                   family="src-dst", keys=None, tie_key=None, order="first-flow"):
    if order not in ORDERS:
        raise ValueError(f"order={order!r} must be one of {ORDERS}")
    if tie_key is not None and order != "first-flow":
        raise ValueError("tie_key is a first-flow secondary key; it is meaningless under "
                         f"order={order!r}")
    if keys is None:
        if family == "src-dst":   keys = [src_w, dst_w]
        elif family == "src":     keys = [src_w]
        elif family == "dst":     keys = [dst_w]
        else: raise ValueError(f"family={family!r} needs an explicit keys= list")
    keys = [np.asarray(a, dtype=np.int64) for a in keys]
    n_flows = len(ts_w)
    for i, a in enumerate(keys):
        if a.shape != (n_flows,):
            raise ValueError(f"key field {i} has shape {a.shape}, expected ({n_flows},): every "
                             "key array must carry one value per flow")
    if bucket_s is not None:
        keys = keys + [ts_w // (int(bucket_s) * 1_000_000)]
    comb = np.zeros(len(ts_w), dtype=np.int64); tot = 1
    for a in keys:
        _, c = np.unique(a, return_inverse=True)
        m = int(c.max()) + 1 if len(c) else 1
        if tot * m > (1 << 62):
            raise OverflowError("episode key space too large to pack into int64")
        comb = comb * m + c
        tot *= m
    _, gid = np.unique(comb, return_inverse=True)
    T = int(gid.max() + 1)
    nsz = np.bincount(gid, minlength=T)
    mal = np.bincount(gid, weights=y_te.astype(float), minlength=T)
    sum_e = np.bincount(gid, weights=e_te, minlength=T)
    first_ts = np.full(T, np.iinfo(np.int64).max); np.minimum.at(first_ts, gid, ts_w)
    first_pos = np.full(T, np.iinfo(np.int64).max)
    np.minimum.at(first_pos, gid, np.arange(len(gid), dtype=np.int64))
    gkeys = []
    for a in keys:
        v = np.zeros(T, dtype=np.int64); v[gid] = a; gkeys.append(v)
    if bucket_s is None:
        gkeys = gkeys + [np.zeros(T, dtype=np.int64)]
    if order == "first-flow":
        if tie_key is None:
            ordr = np.lexsort((first_pos, first_ts))
        else:
            tie_key = np.asarray(tie_key)
            if tie_key.shape != (T,):
                raise ValueError(f"tie_key must have shape ({T},), got {tie_key.shape}")
            ordr = np.lexsort((tie_key, first_ts))
    else:
        seed = 0 if order == "keyhash" else KEYED_SEED
        ordr = hashed_order(key_hash(*gkeys, seed=seed), *gkeys)
    Ev = (sum_e / np.maximum(nsz, 1))[ordr]
    ismal = (mal > 0)[ordr]
    return dict(Ev=Ev, ismal=ismal, nsz=nsz[ordr], sum_e=sum_e[ordr], gid=gid,
                order=ordr, T=T, n_mal=int(ismal.sum()), order_kind=order,
                first_ts_g=first_ts, first_pos_g=first_pos, bucket_g=gkeys[-1])


def frontier(smax, ismal):
    T = len(smax); NM = int(ismal.sum())
    ordr = np.lexsort((np.arange(T), -smax)); m = ismal[ordr]
    tp = np.cumsum(m); fp = np.cumsum(~m); kk = np.arange(1, T + 1)
    return dict(tp=tp, fp=fp, kk=kk, fdp=fp / kk, rec=tp / NM, m=m, NM=NM)


def frontier_at_budget(fr, nb):
    tp, fp, m, NM, T = fr["tp"], fr["fp"], fr["m"], fr["NM"], len(fr["m"])
    b = float(np.clip(nb, 0.0, T))
    if b <= 0: return 0.0, 0.0
    k = int(np.floor(b)); frac = b - k
    base = float(tp[k - 1]) if k else 0.0
    extra = float(m[k]) if k < T else 0.0
    fp_b = (float(fp[k - 1]) if k else 0.0) + frac * (1.0 - extra)
    return float((base + frac * extra) / NM), float(fp_b / b)


def frontier_at_fdp(fr, q):
    ok = np.flatnonzero(fr["fdp"] <= q)
    if not len(ok): return None, None, None
    best = fr["tp"][ok].max(); cand = ok[fr["tp"][ok] == best]
    i = cand[np.argmin(fr["fdp"][cand])]
    return float(fr["rec"][i]), float(fr["fdp"][i]), int(fr["kk"][i])
