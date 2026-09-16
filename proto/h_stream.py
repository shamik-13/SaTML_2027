"""
Shared stream construction for the Phase 2 (H*) experiments.

Every H* script needs the same pipeline: load the timestamp-sorted LSPR23 flow file, fit a
detector on an early chronological window, form conformal e-values against a benign
calibration window, group the deployment window into episodes, and order those episodes.
Re-implementing that per script is how tie-breaks and off-by-ones diverge, so it lives here
once and is regression-tested against the numbers already in the record
(see t22a_stream_selftest.py).

The construction is byte-for-byte the one in t19_T5_T6.py / t21_H6_procedures.py:

  * split indices  i2 = int(pos*N), i1 = i2 - int(cal_f*N), i3 = min(N, i2 + int(test_f*N))
  * benign subsampling confined to the TRAINING window, rng = default_rng(seed)
  * calibration = benign flows in [i1, i2); every flow retained
  * conformal rank  K = 1 + #{c in C : c >= s};  e = CEIL * 1{K <= k}  with CEIL = (|C|+1)/k
  * episode key (src, dst, floor(ts / bucket))
  * episode order  np.lexsort((first_pos, first_ts))   -- ties by first stream occurrence
  * episode evidence  Ev = sum(e)/n   (arithmetic-mean rule, section 2.3)

A .npy cache of the parsed columns is kept under /tmp/lspr_cache so repeated runs skip the
~45 s CSV parse.  It is derived data and is rebuilt automatically if missing.
"""
import numpy as np, pandas as pd, os, gc, time
from pathlib import Path

CSV = "/tmp/lspr_full.csv"
CACHE = Path("/tmp/lspr_cache")
_COLS = ["ts", "src", "dst", "label", "proto"] + [f"f{i}" for i in range(32)]
_FEAT = ["proto"] + [f"f{i}" for i in range(32)]


PORTS = "/tmp/lspr_ports.csv"      # SrcPort,DstPort in ORIGINAL csv row order


def _slash24_codes(cats):
    """Map IP-string categories to /24 prefix codes.  Non-dotted-quad values (IPv6 or
    malformed) map to their own singleton prefix so they are never silently merged."""
    pref = np.array([s.rsplit(".", 1)[0] if s.count(".") == 3 else s for s in cats.astype(str)])
    _, codes = np.unique(pref, return_inverse=True)
    return codes.astype(np.int32)


def _build_cache(verbose=True):
    t0 = time.time()
    dt = {"ts": "int64", "src": "category", "dst": "category", "label": "int8",
          "proto": "float32"}
    dt.update({f"f{i}": "float32" for i in range(32)})
    df = pd.read_csv(CSV, header=None, names=_COLS, dtype=dt, low_memory=False)
    # the stable sort permutation is saved so that side files extracted in ORIGINAL row
    # order (ports) can be aligned to the cached, sorted arrays
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
    # pandas uses -1 for a missing category, which would index the LAST /24 prefix and
    # silently scramble the subnet grouping.  Fail loudly instead.
    if (src_codes < 0).any() or (dst_codes < 0).any():
        raise ValueError("missing src/dst category codes; /24 mapping would be wrong")
    np.save(CACHE / "src.npy", src_codes)
    np.save(CACHE / "dst.npy", dst_codes)
    # /24 prefix codes, for the subnet grouping family (H4)
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
    """Load an optional cached column: 'src24', 'dst24', 'sport', 'dport'.
    Raises if it is absent, rather than silently returning something wrong."""
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


# ----------------------------------------------------------------------------------
def split_indices(N, pos, cal_f=0.15, test_f=0.15):
    i2 = int(pos * N); i1 = i2 - int(cal_f * N); i3 = min(N, i2 + int(test_f * N))
    return i1, i2, i3


def train_index(y, i1, seed, subsample_benign=0.5):
    """Training rows: every malicious flow plus a `subsample_benign` fraction of benign,
    drawn with default_rng(seed).  Confined to [0, i1)."""
    rng = np.random.default_rng(seed)
    tr = np.arange(i1); ben = tr[y[tr] == 0]
    keep = ben[rng.random(len(ben)) < subsample_benign]
    return np.sort(np.concatenate([tr[y[tr] == 1], keep]))


def fit_detector(X, y, i1, seed, kind="hgb", verbose=True):
    """Return a callable score(rows_slice) -> higher means more attack-like.

    kind='hgb'  supervised HistGradientBoosting, the settings mandated by the record
                (l2_regularization=1.0 and min_samples_leaf=200 are NOT optional: with
                ~0.6% positives and l2=0 the leaf values explode and tail ranking dies).
    kind='iforest'  unsupervised IsolationForest.  Uses NO labels at fit time, so its
                training rows are the whole training window rather than a label-balanced
                subsample -- see t22_H1_detector.py for what that changes.
    """
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
        # unsupervised: sample from the training window without consulting y at all
        n_fit = min(i1, 2_000_000)
        rows = np.sort(rng.choice(i1, n_fit, replace=False)) if n_fit < i1 else np.arange(i1)
        clf = IsolationForest(n_estimators=200, max_samples=8192, contamination="auto",
                              random_state=seed, n_jobs=-1).fit(np.asarray(X[rows]))
        fn = lambda Z: -clf.score_samples(Z)      # higher = more anomalous = more attack-like
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
    """Threshold conformal e-value at rank k (section 2.2).

    p = (1 + #{c in C : c >= s}) / (|C|+1);  e = ((|C|+1)/k) * 1{K <= k}.
    Returns (e_te, cal_sorted, NC, CEIL).
    """
    cal = np.sort(s_cal[y_cal == 0]); NC = len(cal)
    CEIL = (NC + 1.0) / k
    Kr = 1 + (NC - np.searchsorted(cal, s_te, side='left'))
    return np.where(Kr <= k, CEIL, 0.0), cal, NC, CEIL


# ----------------------------------------------------------------------------------
# CANONICAL WITHIN-BUCKET ORDER (review-7 item R3).
#
# A group's evidence uses every flow in its time bucket, so the hypothesis cannot be decided
# until the bucket closes; the controller orders hypotheses by bucket close and must break ties
# among groups closing in the SAME bucket by a pre-committed, evidence-independent rule.  The
# rule the pipeline originally shipped is first-flow arrival, and t53 shows it is a poor
# canonical choice on two counts: it is the LARGEST detection count among evidence-independent
# orders (so headline numbers built on it are the detector-favouring end), and it is
# ATTACKER-INFLUENCEABLE -- the adversary controls when its own episode first appears, so
# delaying a first flow pushes the episode to a later, lower-alpha_t slot.
#
# The canonical order is instead a deterministic splitmix64 hash of the group's OWN raw key.  Its
# SORT KEY is a function of that group's metadata alone, so it is evidence-independent and invariant
# to arrival times, and appending flows to an existing group moves NO other group's slot -- which is
# exactly what the per-hypothesis Assumption-1 argument needs (a pad must not move any other group's
# spending weight gamma_j).  Two things it does NOT give, both measured rather than assumed away:
# a group's ABSOLUTE rank still depends on which other keys are present, so an adversary that
# CREATES new keys does move other groups; and with a public seed the hash is GRINDABLE over the
# attacker-selectable (SrcIP,DstIP), so it removes the timing lever and not the metadata lever.
#
# These three functions are the SINGLE definition: t53_ordering re-exports them, and t48
# imports them from t53, so the canonical order cannot drift between the stage that measures
# order sensitivity and the stages that ship under it.
# A PUBLIC CONSTANT standing in for a seed a deployment would keep secret.  It exists so the keyed
# order is reproducible from this artifact; it is NOT itself a secret and confers no grinding
# resistance here.  A deployment wanting the keyed variant must supply an external, private,
# rotated seed -- a threat-model assumption the paper prices but does not make.
KEYED_SEED = 0xC0FFEE123456789


def _mix64(x):
    """SplitMix64 finaliser: a deterministic avalanching 64-bit hash, no external dependency."""
    with np.errstate(over="ignore"):
        x = np.asarray(x, dtype=np.uint64).copy()
        x ^= (x >> np.uint64(30)); x *= np.uint64(0xBF58476D1CE4E5B9)
        x ^= (x >> np.uint64(27)); x *= np.uint64(0x94D049BB133111EB)
        x ^= (x >> np.uint64(31))
    return x


def key_hash(*key_vals, seed=0):
    """Hash of a group's OWN key tuple -- not of its index among the keys PRESENT.

    The group index is the lexicographic rank of the packed key among present keys, so it is a
    function of the whole key SET; hashing the key VALUES makes the order a function of each
    group's own metadata alone.  `seed` is the pre-committed hash key: seed=0 is the PUBLIC
    canonical order, a nonzero secret seed the keyed (grinding-resistant) variant.  A public
    hash of attacker-selectable (SrcIP,DstIP) fields is grindable -- an adversary controlling
    several source hosts can pick whichever gives a favourable slot -- so seed=0 is a
    TIMING-INDEPENDENT CANONICALIZATION, not a security mechanism.
    """
    if not key_vals:
        raise ValueError("key_hash needs at least one key array")
    n = len(np.asarray(key_vals[0]))
    with np.errstate(over="ignore"):
        h = np.full(n, np.uint64(0x9E3779B97F4A7C15), dtype=np.uint64) ^ np.uint64(seed)
        for a in key_vals:
            h = _mix64(h ^ np.asarray(a, dtype=np.int64).astype(np.uint64))
    return h


def hashed_order(hkey, *key_vals):
    """Bucket-batched, then hashed key, then the raw key itself for hash collisions.

    `key_vals` are the group's raw key fields in key order; the LAST one is the time bucket,
    which is the batching field (groups in an earlier bucket close first, and no group may be
    decided before its own bucket closes).  Everything before it breaks hash collisions
    deterministically, so the order is a total order that depends on nothing but the keys.
    """
    if not key_vals:
        raise ValueError("hashed_order needs at least one key array")
    h63 = (np.asarray(hkey, dtype=np.uint64) & np.uint64((1 << 63) - 1)).astype(np.int64)
    bucket = np.asarray(key_vals[-1], dtype=np.int64)
    tie = [np.asarray(a, dtype=np.int64) for a in key_vals[:-1]]
    return np.lexsort(tuple(reversed(tie)) + (h63, bucket))


ORDERS = ("first-flow", "keyhash", "keyed")


# ----------------------------------------------------------------------------------
def build_episodes(e_te, y_te, ts_w, src_w=None, dst_w=None, bucket_s=None,
                   family="src-dst", keys=None, tie_key=None, order="first-flow"):
    """Group one deployment window into episodes and return the ordered stream.

    Two ways to specify the key:
      * family + src_w/dst_w, for the common cases (kept so existing callers are unchanged)
      * keys=[array, ...], an explicit list of integer arrays, for arbitrary families (H4)

    bucket_s is in SECONDS; bucket_s=None means NO time field at all, which is the
    "host-pair only" grouping (an episode is a source-destination pair over the whole
    window).

    Ordering is np.lexsort((first_pos, first_ts)): primary key first timestamp, ties broken
    by first occurrence in the stream.  np.argsort on first_ts alone breaks ties
    arbitrarily and moves the online rejection sequence (standing mistake 5).

    tie_key, if given, replaces first_pos as the SECONDARY sort key only.  The primary key
    is still first_ts, so the across-timestamp order is untouched and only genuinely tied
    episodes can move.  It exists for t42_E9_ties.py, which quantifies the variance the
    deterministic tie-break suppresses; it must be an array of length T (the number of
    episodes) indexed by GROUP ID, like nsz and sum_e before reordering.  Default None
    reproduces the record exactly.

    order selects the WITHIN-BUCKET tie-break (review-7 item R3):

      "first-flow"  the shipped order, lexsort((first_pos, first_ts)) -- an optimistic UPPER
                    bound on detection power and attacker-influenceable (see the ORDERS block
                    above).  Default, so no existing caller changes silently.
      "keyhash"     the CANONICAL order: bucket-batched, then splitmix64 of the group's OWN raw
                    key, collisions broken on the raw key.  seed=0, public.
      "keyed"       the same with a secret seed (KEYED_SEED) -- the grinding-resistant variant,
                    at the cost of a new threat-model assumption.

    Both hashed orders are still bucket-batched, so causality is unchanged: no group is decided
    before its own bucket closes.  When bucket_s is None there is no time field in the key at
    all (the "host-pair only" family), every group closes at the same instant -- the end of the
    window -- so every order over them is admissible and the hash orders the whole window.

    Ordering does not touch grouping: gid, T, nsz, sum_e and mal are computed before `order` is
    consulted, so the three orders are permutations of ONE episode set and differ only in the
    sequence the controller sees.
    """
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
    # Every key field must carry one value PER FLOW.  numpy broadcasts a length-1 array through
    # both np.unique(return_inverse) and the per-group scatter below without complaint, so a
    # short key array would silently be treated as a constant field -- the partition would be
    # coarser than asked for AND the per-group key recovered for the hash order would be wrong.
    # Neither shows up as an error, so it is checked here rather than trusted.
    n_flows = len(ts_w)
    for i, a in enumerate(keys):
        if a.shape != (n_flows,):
            raise ValueError(f"key field {i} has shape {a.shape}, expected ({n_flows},): every "
                             "key array must carry one value per flow")
    if bucket_s is not None:
        keys = keys + [ts_w // (int(bucket_s) * 1_000_000)]
    # Pack the key tuple into a single int64 rather than building a structured array:
    # np.unique on a structured dtype falls back to generic element comparisons and costs
    # tens of seconds on multi-million-row windows.  Factorising each field and combining
    # them positionally gives the identical partition AND the identical lexicographic
    # group numbering, because the most significant field is applied first.
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
    # per-group RAW key values.  Every flow of a group shares each key field by construction of
    # the partition, so the scatter-assign is exact (last write wins, all writes equal); it is
    # the group's own metadata, never its index among the keys present.
    gkeys = []
    for a in keys:
        v = np.zeros(T, dtype=np.int64); v[gid] = a; gkeys.append(v)
    if bucket_s is None:                       # no time field: one common close instant
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
    """Oracle Pareto frontier for the episode max-score threshold family (section 4.19).
    Deterministic tie-break: np.lexsort((arange, -smax))."""
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
