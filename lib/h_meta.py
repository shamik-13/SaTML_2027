import numpy as np, pandas as pd, json, time, os
from pathlib import Path

import h_stream as hs

_D = os.environ.get("LSPR_DIR", "/tmp")
META_CSV = os.environ.get("LSPR_META_CSV", f"{_D}/lspr_meta.csv")
MCACHE = Path(os.environ.get("LSPR_META_CACHE", f"{_D}/lspr_meta_cache"))

_STR = ["srcip", "dstip", "conn", "service", "seg_src", "seg_dst"]
_NUM = ["sport", "dport", "l3l4", "label_src", "label_dst", "ext_src", "ext_dst"]
_COLS = ["srcip", "dstip", "sport", "dport", "l3l4", "conn", "service",
         "label_src", "label_dst", "ext_src", "ext_dst", "seg_src", "seg_dst"]


def _build(verbose=True):
    if not os.path.exists(META_CSV):
        raise FileNotFoundError(
            f"{META_CSV} missing.  From the directory holding ls23pr_v1.csv (see data/README.md) run:\n"
            "  awk -F',' 'NR>1 {print $2\",\"$3\",\"$4\",\"$5\",\"$89\",\"$91\",\"$92\",\"$93"
            "\",\"$94\",\"$96\",\"$97\",\"$98\",\"$99}' ls23pr_v1.csv > /tmp/lspr_meta.csv")
    perm = np.load(hs.CACHE / "perm.npy")
    t0 = time.time()
    dt = {c: "string" for c in _STR}
    dt.update({c: "float64" for c in _NUM})
    df = pd.read_csv(META_CSV, header=None, names=_COLS, dtype=dt,
                     keep_default_na=True, low_memory=False)
    if len(df) != len(perm):
        raise ValueError(f"{META_CSV} has {len(df):,} rows, flow cache has {len(perm):,}; "
                         "re-extract with the same NR>1 filter from the same csv")
    MCACHE.mkdir(parents=True, exist_ok=True)
    cats = {}
    for c in _COLS:
        v = df[c].to_numpy()
        v = v[perm]
        if c in _STR:
            s = pd.Series(v).fillna("").astype(str).to_numpy()
            u, code = np.unique(s, return_inverse=True)
            np.save(MCACHE / f"{c}.npy", code.astype(np.int32))
            cats[c] = [str(x) for x in u]
        else:
            np.save(MCACHE / f"{c}.npy", np.nan_to_num(v, nan=-1.0).astype(np.int32))
        del v
    json.dump(cats, open(MCACHE / "cats.json", "w"))
    del df
    if verbose:
        print(f"  [h_meta] built cache in {time.time()-t0:.0f}s -> {MCACHE}")


def load(verbose=True):
    """Return (meta, cats).  meta[name] is an int32 array in h_stream row order;"""
    if not all((MCACHE / f"{c}.npy").exists() for c in _COLS) or \
       not (MCACHE / "cats.json").exists():
        _build(verbose)
    meta = {c: np.load(MCACHE / f"{c}.npy") for c in _COLS}
    cats = json.load(open(MCACHE / "cats.json"))
    return meta, cats


def verify(meta, src, dst, rng=None, n=None):
    """Check the metadata really is row-aligned with h_stream's cached arrays."""
    ok_ports = False
    try:
        sp = np.load(hs.CACHE / "sport.npy"); dp = np.load(hs.CACHE / "dport.npy")
    except FileNotFoundError:
        print("  [h_meta] WARNING: h_stream port cache absent; alignment check is the weak "
              "partition test only")
    else:
        if len(sp) != len(meta["sport"]):
            raise ValueError("h_meta and h_stream port arrays differ in length")
        bad = int((sp != meta["sport"]).sum() + (dp != meta["dport"]).sum())
        if bad:
            raise ValueError(f"h_meta ports disagree with h_stream's independently extracted "
                             f"port cache on {bad:,} rows; delete {MCACHE} and re-extract")
        ok_ports = True
    rng = rng or np.random.default_rng(0)
    N = len(src)
    idx = np.arange(N) if (n is None or n >= N) else \
        rng.choice(N, n, replace=False)
    for nm, host, ipc in (("src", src, meta["srcip"]), ("dst", dst, meta["dstip"])):
        a, b = host[idx].astype(np.int64), ipc[idx].astype(np.int64)
        ua = np.unique(a); ub = np.unique(b)
        if (b.max() + 1) * (a.max() + 1) > (1 << 62):
            raise OverflowError("host/ip code product does not fit in int64")
        ok_ab = len(np.unique(a * (b.max() + 1) + b)) == len(ua)
        ok_ba = len(np.unique(b * (a.max() + 1) + a)) == len(ub)
        if not (ok_ab and ok_ba):
            raise ValueError(f"h_meta/{nm}: ip codes are not row-aligned with h_stream "
                             f"host codes (a->b {ok_ab}, b->a {ok_ba}); delete {MCACHE} "
                             "and re-extract")
    return dict(rows_checked=int(len(idx)), port_crosscheck=ok_ports)


def ip_table(meta, cats, host_codes, side="src"):
    """Return an array `ip[c]` giving the dotted-quad string for h_stream host code c."""
    ipc = meta[f"{side}ip"]
    ncode = int(host_codes.max()) + 1
    out = np.full(ncode, "", dtype=object)
    first = np.full(ncode, -1, dtype=np.int64)
    seen = np.unique(host_codes, return_index=True)
    first[seen[0]] = seen[1]
    names = cats[f"{side}ip"]
    for c in range(ncode):
        if first[c] >= 0:
            out[c] = names[ipc[first[c]]]
    return out
