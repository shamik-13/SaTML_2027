"""
Forensic metadata columns for LSPR23, aligned to the h_stream sorted arrays.

h_stream.py caches only what the statistics need (features, label, timestamp, host codes).
The forensic questions of section 4.31 -- who sent the extreme-tail benign flows, to what
service, from what segment, and whether those hosts appear in attack traffic -- need the
annotation columns of the raw csv as well:

    2 SrcIP   3 DstIP   4 SrcPort   5 DstPort   89 L3/L4 Protocol   91 Conn_state
    92 Service   93 Label_src   94 Label_dst   96 External_src   97 External_dst
    98 Segment_src   99 Segment_dst

They are extracted in ORIGINAL csv row order by

    awk -F',' 'NR>1 {print $2","$3","$4","$5","$89","$91","$92","$93","$94","$96","$97","$98","$99}' \
        ls23pr_v1.csv > /tmp/lspr_meta.csv

and re-ordered here with the same `perm` h_stream saved when it built its cache, so row i of
every array below is row i of h_stream.load().

Alignment is VERIFIED, not assumed.  `verify()` requires the SrcPort/DstPort columns
extracted here to agree, on all 16,353,511 rows, with the ones h_stream extracted in its own
independent pass from a different side file -- and additionally requires the ip-string codes
to induce the same host partition as h_stream's category codes.  The port check is the strong
one: a row shift would have to preserve every flow's port pair to survive it.  A silent
misalignment would attribute one host's traffic to another, which is exactly the kind of
error the forensic conclusion would rest on.

Label_src / Label_dst are the dataset's own per-endpoint annotations.  Measured over the
whole stream, `Label == 1` holds exactly when `Label_src == 1 or Label_dst == 1`, so they
are NOT an independent label source -- they are a decomposition of the same instrumentation
that says WHICH endpoint made the flow malicious.  Used as such, never as corroboration.
"""
import numpy as np, pandas as pd, json, time, os
from pathlib import Path

import h_stream as hs

META_CSV = "/tmp/lspr_meta.csv"
MCACHE = Path("/tmp/lspr_meta_cache")

_STR = ["srcip", "dstip", "conn", "service", "seg_src", "seg_dst"]
_NUM = ["sport", "dport", "l3l4", "label_src", "label_dst", "ext_src", "ext_dst"]
_COLS = ["srcip", "dstip", "sport", "dport", "l3l4", "conn", "service",
         "label_src", "label_dst", "ext_src", "ext_dst", "seg_src", "seg_dst"]


def _build(verbose=True):
    if not os.path.exists(META_CSV):
        raise FileNotFoundError(
            f"{META_CSV} missing.  From proto/data/lspr23/ run:\n"
            "  awk -F',' 'NR>1 {print $2\",\"$3\",\"$4\",\"$5\",\"$89\",\"$91\",\"$92\",\"$93"
            "\",\"$94\",\"$96\",\"$97\",\"$98\",\"$99}' ls23pr_v1.csv > /tmp/lspr_meta.csv")
    perm = np.load(hs.CACHE / "perm.npy")
    t0 = time.time()
    dt = {c: "string" for c in _STR}
    dt.update({c: "float64" for c in _NUM})       # float so empty fields become NaN
    df = pd.read_csv(META_CSV, header=None, names=_COLS, dtype=dt,
                     keep_default_na=True, low_memory=False)
    if len(df) != len(perm):
        raise ValueError(f"{META_CSV} has {len(df):,} rows, flow cache has {len(perm):,}; "
                         "re-extract with the same NR>1 filter from the same csv")
    MCACHE.mkdir(parents=True, exist_ok=True)
    cats = {}
    for c in _COLS:
        v = df[c].to_numpy()
        v = v[perm]                                # -> timestamp-sorted order
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
    """Return (meta, cats).  meta[name] is an int32 array in h_stream row order;
    cats[name] is the category list for the string-valued columns."""
    if not all((MCACHE / f"{c}.npy").exists() for c in _COLS) or \
       not (MCACHE / "cats.json").exists():
        _build(verbose)
    meta = {c: np.load(MCACHE / f"{c}.npy") for c in _COLS}
    cats = json.load(open(MCACHE / "cats.json"))
    return meta, cats


def verify(meta, src, dst, rng=None, n=None):
    """Check the metadata really is row-aligned with h_stream's cached arrays.

    Two independent checks, both on EVERY row by default:

    1. Ports.  h_stream extracts SrcPort/DstPort from a separate side file (/tmp/lspr_ports
       .csv, columns 4 and 5 of the raw csv) and applies the same `perm`.  h_meta extracts
       them again in its own pass.  If the two agree on all 16.35M rows then the extraction
       and the permutation are both right; a row shift would have to preserve the port pair
       of every flow to survive this.
    2. Host codes.  The ip-string code and h_stream's host code must induce the SAME
       partition, checked as a two-way single-valued map.  On its own this check is weak --
       a permutation that maps each row to another row of the same host passes it -- which
       is exactly why check 1 exists; the ports vary within a host pair.

    Check 1 is skipped with a warning only if the port cache is absent.
    """
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
    """Return an array `ip[c]` giving the dotted-quad string for h_stream host code c.

    Built by the verified join rather than by assuming pandas and numpy order categories
    the same way.
    """
    ipc = meta[f"{side}ip"]
    ncode = int(host_codes.max()) + 1
    out = np.full(ncode, "", dtype=object)
    first = np.full(ncode, -1, dtype=np.int64)
    # first occurrence of each host code
    seen = np.unique(host_codes, return_index=True)
    first[seen[0]] = seen[1]
    names = cats[f"{side}ip"]
    for c in range(ncode):
        if first[c] >= 0:
            out[c] = names[ipc[first[c]]]
    return out
