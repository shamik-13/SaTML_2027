"""
Can the attacker actually put pad flows into the target's episode?

The padding attack of sections 4.16/4.30 dilutes an episode's arithmetic mean.  The episode
key is (SrcIP, DstIP, time bucket), so a pad flow must land on THE TARGET'S OWN HOST PAIR --
the attacker sending ordinary traffic to the victim.  None of section 4.30's five pools is
matched that way: generic is window-wide, attacker-origin is matched on SOURCE only,
protocol- and service-matched on the episode's modal protocol / destination port, and
black-box on the window's most common service.  So the cost model assumes that attacker-
generated ordinary traffic TO THE VICTIM scores like ordinary traffic generally, and that
assumption has never been checked.

This script settles it in two steps, and the order matters:

  1  THE EMPIRICAL ROUTE IS CLOSED, and that has to be measured rather than assumed.  If the
     attack host pairs carried ordinary benign traffic, a host-pair-matched pool could be
     built out of it and priced like the other five.  They do not: every detected episode's
     host pair is 100% malicious in every window.  There is no example in LSPR23 of ordinary
     traffic on an attack pair, so no measurement on this dataset can answer the question.

  2  THE STRUCTURAL ROUTE ANSWERS IT ANYWAY.  The detector's feature vector is Protocol plus
     32 per-flow timing and volume statistics.  It contains NO IP address, NO port and no
     host identity of any kind, so a flow's score cannot depend on which host pair it sits
     on.  An ordinary HTTPS or DNS flow therefore scores identically whether it is sent to
     the victim or anywhere else, and the black-box pool's e-value distribution transfers to
     the attack pair BY CONSTRUCTION rather than by assumption.

  The scope this buys, and its limit: the argument is a property of FLOW-LEVEL feature sets.
  A detector using host reputation, per-host baselines, or any feature conditioned on
  endpoint identity would break it, and for such a detector the question would have to be
  settled on a testbed.  That limit is the thing to state in print.

Outputs out/t46_hostpair.json.
"""
import numpy as np, json, time
from pathlib import Path

import h_stream as hs

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)
t0 = time.time()

POS = [0.55, 0.62, 0.70, 0.77, 0.85]
SEEDS = [0, 1]
W0 = 0.025; K = 1; BUCKET = 2 * 3600
out = {"config": dict(pos=POS, seeds=SEEDS, k=K, w0=W0, bucket_s=BUCKET)}
FAIL = []


def note(cond, msg):
    if not cond:
        FAIL.append(msg)
        print(f"    *** ASSERTION FAILED: {msg}")
    return cond


# =======================================================================================
# STEP 2 FIRST, because it costs nothing: what does the detector actually see?
# =======================================================================================
print("=" * 112)
print("THE FEATURE SET -- can a score depend on the host pair at all?")
print("=" * 112)
# h_stream._FEAT is ["proto"] + f0..f31, and docs/01_HANDOFF_PHASE4.md section 2.2 fixes
# f_i as ls23pr_v1.csv column i+9.  The names below are that column range, read from the
# file's own header ONCE and pinned here so this check does not depend on the raw CSV.
FEATURE_NAMES = [
    "Protocol",
    "Flow Duration", "Flow Bytes/s", "Flow Packets/s", "Tot Fwd Pkts", "Tot Bwd Pkts",
    "Total Length of Fwd Packet", "Total Length of Bwd Packet",
    "Fwd Packet Length Min", "Fwd Packet Length Max", "Fwd Packet Length Mean",
    "Fwd Packet Length Std", "Bwd Packet Length Min", "Bwd Packet Length Max",
    "Bwd Packet Length Mean", "Bwd Packet Length Std",
    "Flow IAT Mean", "Flow IAT Min", "Flow IAT Max", "Flow IAT Stddev",
    "Fwd IAT Min", "Fwd IAT Max", "Fwd IAT Mean", "Fwd IAT Std", "Fwd IAT Tot",
    "Bwd IAT Min", "Bwd IAT Max", "Bwd IAT Mean", "Bwd IAT Std", "Bwd IAT Tot",
    "Fwd PSH flags", "Bwd PSH flags", "Fwd URG flags",
]
note(len(FEATURE_NAMES) == len(hs._FEAT),
     f"feature-name list has {len(FEATURE_NAMES)} entries, h_stream._FEAT has {len(hs._FEAT)}")
IDENTITY = ("ip", "addr", "src", "dst", "port", "host", "mac", "id", "subnet", "prefix")
offend = [n for n in FEATURE_NAMES
          if any(tok in n.lower().replace("fwd", "").replace("bwd", "") for tok in IDENTITY)]
print(f"  {len(FEATURE_NAMES)} features, all per-flow timing / volume / protocol statistics")
print(f"  features naming an endpoint identity: {offend if offend else 'NONE'}")
note(not offend, f"a feature names an endpoint identity: {offend}")
# and the arrays that DO carry identity are used only for GROUPING, never for scoring
src_used_in_fit = "src" in hs._FEAT or "dst" in hs._FEAT
note(not src_used_in_fit, "src/dst appear in the fitted feature set")
print(f"  src/dst/ports enter the pipeline only through build_episodes' grouping key, never")
print(f"  through fit_detector -- so a flow's SCORE is invariant to which host pair it is on.")
out["feature_set"] = dict(n_features=len(FEATURE_NAMES), names=FEATURE_NAMES,
                          identity_features=offend,
                          score_invariant_to_host_pair=bool(not offend))

# =======================================================================================
# STEP 1: is a host-pair-matched pool available anywhere in this dataset?
# =======================================================================================
print("\n" + "=" * 112)
print("IS A HOST-PAIR-MATCHED PADDING POOL AVAILABLE?  (all five windows x two seeds)")
print("=" * 112)
X, y, ts, src, dst = hs.load()
N = len(y)
print(f"  {'window':>8} {'seed':>5} {'detected':>9} {'pairs 100% malicious':>21} "
      f"{'benign flows on pair: med':>26} {'>= 35 available':>16}")
rows = []
for pos in POS:
    i1, i2, i3 = hs.split_indices(N, pos)
    y_te = y[i2:i3]
    sw, dw = src[i2:i3], dst[i2:i3]
    ben = (y_te == 0)
    for seed in SEEDS:
        score = hs.fit_detector(X, y, i1, seed=seed, kind="hgb", verbose=False)
        s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
        e_te, cal, NC, CEIL = hs.evalues(s_cal, y[i1:i2], s_te, k=K)
        ep = hs.build_episodes(e_te, y_te, ts[i2:i3], sw, dw, BUCKET, "src-dst")
        T = ep["T"]; tau = T / W0
        det = np.nonzero(ep["ismal"] & (ep["Ev"] >= tau))[0]
        if not len(det):
            rows.append(dict(pos=pos, seed=seed, n_detected=0))
            print(f"  {pos:>8.2f} {seed:>5} {0:>9} {'—':>21} {'—':>26} {'—':>16}")
            continue
        inv = np.empty(T, dtype=np.int64); inv[ep["order"]] = np.arange(T)
        ep_of_flow = inv[ep["gid"]]
        # Pair identity is taken from the episode's first flow.  Every flow in an episode
        # shares the pair by construction (it is part of the key), asserted below once.
        avail, pure = [], 0
        for j in det:
            k0 = np.flatnonzero(ep_of_flow == j)
            a, b = int(sw[k0[0]]), int(dw[k0[0]])
            if j == det[0]:
                note(bool((sw[k0] == a).all() and (dw[k0] == b).all()),
                     f"an episode spans more than one host pair at pos={pos} seed={seed}")
            on_pair = (sw == a) & (dw == b)
            avail.append(int((on_pair & ben).sum()))
            if int((on_pair & (y_te == 1)).sum()) == int(on_pair.sum()):
                pure += 1
        avail = np.array(avail)
        rows.append(dict(pos=pos, seed=seed, n_detected=int(len(det)),
                         n_pairs_all_malicious=int(pure),
                         benign_on_pair_median=float(np.median(avail)),
                         benign_on_pair_max=int(avail.max()),
                         n_with_35_available=int((avail >= 35).sum())))
        print(f"  {pos:>8.2f} {seed:>5} {len(det):>9} {f'{pure} of {len(det)}':>21} "
              f"{np.median(avail):>26,.0f} {int((avail>=35).sum()):>16}")
out["rows"] = rows

done = [r for r in rows if r["n_detected"]]
tot_det = sum(r["n_detected"] for r in done)
tot_pure = sum(r["n_pairs_all_malicious"] for r in done)
tot_avail = sum(r["n_with_35_available"] for r in done)
print(f"\n  Over {len(done)} (window, seed) cells and {tot_det} detected episodes:")
print(f"    host pairs that are 100% malicious            : {tot_pure} of {tot_det}")
print(f"    episodes with >= 35 benign flows on their pair : {tot_avail} of {tot_det}")
note(tot_pure == tot_det, "some attack host pair carries benign traffic -- a host-pair-matched "
                          "pool IS available and should be priced")
out["summary"] = dict(n_cells=len(done), n_detected=tot_det,
                      n_pairs_all_malicious=tot_pure,
                      n_with_pool_available=tot_avail,
                      empirical_route_closed=bool(tot_pure == tot_det))

print(f"""
  THE EMPIRICAL ROUTE IS CLOSED.  Every detected episode's host pair carries only attack
  traffic, in every window and at both seeds, so LSPR23 contains no example of ordinary
  traffic on an attack pair and no host-pair-matched pool can be built from it.

  THE STRUCTURAL ROUTE ANSWERS THE QUESTION.  The detector scores a flow from Protocol and
  32 per-flow timing and volume statistics, with no endpoint identity among them, so the
  score is invariant to the host pair and the black-box pool's e-value distribution
  (P(fire) = 0 at all five windows, section 4.42) transfers to the attack pair by
  construction.  The attacker needs only to make ordinary connections to the victim.

  SCOPE, AND ITS LIMIT.  This is a property of FLOW-LEVEL feature sets.  A detector using
  host reputation, per-host baselines, or any feature conditioned on endpoint identity would
  break the argument, and for such a detector the question would have to be settled on a
  testbed rather than on paper.  [{time.time()-t0:.0f}s]""")

out["assertions_failed"] = FAIL
json.dump(out, open(OUT / "t46_hostpair.json", "w"), indent=1)
print(f"\n  wrote out/t46_hostpair.json")
if FAIL:
    print("  ASSERTIONS FAILED:")
    for m in FAIL:
        print("   -", m)
    raise SystemExit(1)
print("  all assertions held")
