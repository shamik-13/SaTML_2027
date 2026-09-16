"""
E5 -- the two gaps the A1 forensics flagged itself.  Extends section 4.31.

06_PHASE3_REPORT.md section 1.5 lists three uncovered items.  Two are closed here:

  E5a  NEAR-NEIGHBOUR GEOMETRY.  Section 4.31 tested only EXACT duplicates.  For each
       extreme-tail benign-labelled flow, the distance in standardised model-feature space to
       the nearest labelled malicious flow (d_M), the nearest ordinary benign deployment flow
       (d_B) and the nearest calibration benign flow (d_C).
  E5b  PER-FEATURE COMPARISON.  Section 4.31 characterises the tail in SCORE space only.
       Standardised differences and percentile locations of the tail against the benign and
       the malicious populations, plus categorical enrichment.

The third — proximity to attack periods — stays declined: seconds-to-nearest-malicious-flow
is 0.0 at p10, median and p90 for the tail AND for ordinary benign flows, because the window
is saturated with attack traffic.  A metric that cannot separate anything is not run again.

**INTERPRETATION RULE, FIXED BEFORE THE NUMBERS ARE SEEN** (02_WORKPLAN_PHASE4.md E5):
  tail looks attack-like      -> strengthens "consistent with post-compromise label error"
  tail does not look attack-like -> keep only the localisation claim
NEITHER OUTCOME IS PROOF.  F9's wording caps at "the best-supported explanation", and E5
cannot lift it; section 4.31's own conclusion is that a shift confined to the extreme tail
would look the same and cannot be separated without the exercise's own logs.

THE CONTROL THAT MAKES rho MEAN ANYTHING ------------------------------------------------
An absolute `rho = d_M/d_B` is uninterpretable: in a 33-dimensional space filled mostly with
benign traffic, everything has a nearer benign neighbour than malicious one.  Two baselines
are computed the same way on ordinary benign flows:
  * RANDOM       a uniform sample of benign deployment flows
  * HOST-MATCHED benign flows from the SAME (src, dst) host pairs as the tail
The host-matched baseline is the one that matters, because section 4.31 shows the tail is
concentrated in three host pairs of 25,864 — a random baseline would confound "is attack-like"
with "belongs to one of those three hosts".

Standardisation uses the CALIBRATION window's benign mean and standard deviation, never the
evaluation split (standing mistake 4).

Runtime ~8 min.  Run from proto/.
"""
import numpy as np, json, time, sys, gc
from pathlib import Path

import h_stream as H

Path("out").mkdir(exist_ok=True)
SMOKE = "--smoke" in sys.argv
t0 = time.time()

POS = 0.85                       # the window F9's anomaly lives in
DSEEDS = [0, 1]
K = 1
N_BASE = 200 if SMOKE else 400   # baseline flows per arm
REF_CHUNK = 50_000
rng_global = np.random.default_rng(20260826)


def standardise(Z, mu, sd):
    return (Z - mu) / sd


def nearest_distances(Q, R, qchunk=8, rchunk=20_000, exclude_self_rows=None):
    """Min Euclidean distance from each row of Q to any row of R.

    SUBTRACT FIRST.  The textbook ||a-b||^2 = ||a||^2 + ||b||^2 - 2ab form cancels
    catastrophically exactly where the answer matters here: ordinary benign flows are highly
    repetitive, so their nearest-benign distances are ~1e-3 against standardised norms that
    can be large, and the difference of two nearly-equal large numbers loses every significant
    digit.  An earlier version used that form with np.maximum(d2, 0), which silently turned
    small positive distances into exact zeros -- and d_B is the DENOMINATOR of the reported
    ratio.  Forming the differences directly costs memory, hence the small query chunk, but is
    exact to within an ulp.

    `exclude_self_rows`, if given, holds for each query the index INTO R that is the query
    itself (or -1), so a flow is never its own nearest neighbour."""
    best = np.full(len(Q), np.inf)
    for q0 in range(0, len(Q), qchunk):
        q1 = min(q0 + qchunk, len(Q))
        Qc = Q[q0:q1]
        b = best[q0:q1].copy()
        for r0 in range(0, len(R), rchunk):
            Rc = R[r0:r0 + rchunk]
            diff = Qc[:, None, :] - Rc[None, :, :]
            d2 = np.einsum("qrd,qrd->qr", diff, diff, optimize=True)
            if exclude_self_rows is not None:
                loc = exclude_self_rows[q0:q1] - r0
                hit = (loc >= 0) & (loc < len(Rc))
                if hit.any():
                    d2[np.flatnonzero(hit), loc[hit]] = np.inf
            np.minimum(b, d2.min(1), out=b)
            del diff, d2
        best[q0:q1] = b
    return np.sqrt(best)


# ---------------------------------------------------------------------------------------
X, y, ts, src, dst = H.load()
N = len(y)
i1, i2, i3 = H.split_indices(N, POS)
y_te = y[i2:i3]
src_w, dst_w = src[i2:i3], dst[i2:i3]
ben_w = (y_te == 0)
mal_w = ~ben_w
try:
    DPORT = H.load_extra("dport")[i2:i3]
except FileNotFoundError:
    DPORT = None

out = {"config": dict(pos=POS, dseeds=DSEEDS, k=K, n_baseline=N_BASE, smoke=SMOKE),
       "seeds": {}}

for dseed in DSEEDS:
    sc = H.fit_detector(X, y, i1, dseed, kind="hgb")
    s_cal, s_te = H.score_windows(sc, X, i1, i2, i3)
    y_cal = y[i1:i2]
    e_te, cal, NC, CEIL = H.evalues(s_cal, y_cal, s_te, k=K)
    tail = np.flatnonzero((e_te > 0) & ben_w)
    print(f"\n  seed {dseed}: {len(tail)} benign-labelled flows fire "
          f"(s > max of {NC:,} calibration benign scores)   [{time.time()-t0:.0f}s]")

    # ---- standardise on the CALIBRATION benign window only ----------------------------
    cal_ben_rows = np.arange(i1, i2)[y_cal == 0]
    sub = cal_ben_rows if len(cal_ben_rows) <= 400_000 else \
        np.sort(rng_global.choice(cal_ben_rows, 400_000, replace=False))
    Xc = np.asarray(X[sub], dtype=np.float64)
    mu_all, sd_all = Xc.mean(0), Xc.std(0)
    # A feature with zero variance in CALIBRATION cannot be standardised.  Setting its sd to 1
    # lets it enter the Euclidean distance in RAW units, where it can dominate every distance
    # and inflate the norms.  Drop such features from the geometry and report them.
    keep = sd_all > 1e-12
    ALLF = ["proto"] + [f"f{i}" for i in range(32)]
    dropped_feats = [f for f, k in zip(ALLF, keep) if not k]
    mu, sd = mu_all[keep], sd_all[keep]
    Zc = standardise(Xc[:, keep], mu, sd)
    del Xc; gc.collect()

    Xw = np.asarray(X[i2:i3], dtype=np.float64)
    Zw = standardise(Xw[:, keep], mu, sd)
    del Xw; gc.collect()
    max_norm = float(np.sqrt((Zw ** 2).sum(1)).max())
    print(f"    standardised on calibration benign only; dropped {len(dropped_feats)} "
          f"zero-variance features {dropped_feats}; max standardised norm {max_norm:.3g}")

    Z_tail = Zw[tail]
    mal_idx = np.flatnonzero(mal_w)
    ben_idx = np.flatnonzero(ben_w)
    ord_ben_idx = np.setdiff1d(ben_idx, tail, assume_unique=False)

    # reference clouds (subsampled where necessary, and the sizes are reported)
    def subsample(idx, cap):
        return idx if len(idx) <= cap else np.sort(rng_global.choice(idx, cap, replace=False))

    ref_mal = subsample(mal_idx, 400_000)
    ref_ben = subsample(ord_ben_idx, 400_000)
    Zm, Zb = Zw[ref_mal], Zw[ref_ben]

    # ---- baselines ---------------------------------------------------------------------
    base_rand = subsample(ord_ben_idx, N_BASE)
    tail_pairs = set(zip(src_w[tail].tolist(), dst_w[tail].tolist()))
    same_pair = np.array([(a, b) in tail_pairs
                          for a, b in zip(src_w[ord_ben_idx].tolist(),
                                          dst_w[ord_ben_idx].tolist())])
    hostmatched_pool = ord_ben_idx[same_pair]
    base_host = subsample(hostmatched_pool, N_BASE)
    print(f"    host-matched pool: {len(hostmatched_pool):,} ordinary benign flows on the "
          f"tail's {len(tail_pairs)} host pairs; sampling {len(base_host)}")
    # PORT-matched as well.  86% of the tail is dport 443, so a pair-only baseline may be
    # comparing TLS tail flows against non-TLS ordinary flows on the same hosts, which would
    # manufacture the separation.  This is the control that carries the claim.
    base_hostport, n_hp_pool = np.array([], dtype=np.int64), 0
    if DPORT is not None:
        tail_keys = set(zip(src_w[tail].tolist(), dst_w[tail].tolist(), DPORT[tail].tolist()))
        same_pp = np.array([(a, b, pp) in tail_keys
                            for a, b, pp in zip(src_w[ord_ben_idx].tolist(),
                                                dst_w[ord_ben_idx].tolist(),
                                                DPORT[ord_ben_idx].tolist())])
        pool_hp = ord_ben_idx[same_pp]
        n_hp_pool = int(len(pool_hp))
        base_hostport = subsample(pool_hp, N_BASE)
        print(f"    host+PORT-matched pool: {n_hp_pool:,} flows on the tail's "
              f"{len(tail_keys)} (src, dst, dport) keys; sampling {len(base_hostport)}")

    arms = {"tail": tail, "baseline_random_benign": base_rand,
            "baseline_hostmatched_benign": base_host,
            "baseline_host_and_port_matched_benign": base_hostport}
    geo = {}
    for nm, idx in arms.items():
        if len(idx) == 0:
            geo[nm] = None; continue
        Q = Zw[idx]
        # for benign queries drawn from the reference cloud, skip self
        pos_in_ref = np.searchsorted(ref_ben, idx)
        self_row = np.where((pos_in_ref < len(ref_ben)) & (ref_ben[np.minimum(
            pos_in_ref, len(ref_ben) - 1)] == idx), pos_in_ref, -1)
        dM = nearest_distances(Q, Zm)
        dB = nearest_distances(Q, Zb, exclude_self_rows=self_row)
        dC = nearest_distances(Q, Zc)
        rho = dM / np.maximum(dB, 1e-12)
        q = lambda v: [float(np.percentile(v, p)) for p in (10, 50, 90)]
        geo[nm] = dict(n=int(len(idx)), d_M=q(dM), d_B=q(dB), d_C=q(dC), rho=q(rho),
                       rho_mean=float(rho.mean()), frac_rho_lt_1=float((rho < 1).mean()))
        print(f"    {nm:>28}  n={len(idx):>5}  d_M(p50)={np.median(dM):8.3f}  "
              f"d_B(p50)={np.median(dB):8.3f}  d_C(p50)={np.median(dC):8.3f}  "
              f"rho(p50)={np.median(rho):7.3f}  frac rho<1 = {(rho<1).mean():.3f}")
        del Q, dM, dB, dC, rho

    # ---- E5b: per-feature comparison -----------------------------------------------------
    FEAT = [f for f, k in zip(ALLF, keep) if k]
    mu_b, sd_b = Zw[ord_ben_idx].mean(0), Zw[ord_ben_idx].std(0)
    mu_m, sd_m = Zw[mal_idx].mean(0), Zw[mal_idx].std(0)
    mu_t = Z_tail.mean(0)
    # standardised difference of the tail from each population, in that population's own sd
    d_from_ben = (mu_t - mu_b) / np.where(sd_b > 0, sd_b, 1.0)
    d_from_mal = (mu_t - mu_m) / np.where(sd_m > 0, sd_m, 1.0)
    # percentile location of the tail's median within each population
    # Percentile location of the tail's MEDIAN.  Uncertainty is dominated by n_tail, not by
    # the population size: the SE of a sample-median percentile is about 50/sqrt(n) points,
    # ~7 points at n = 46.  Reported to whole percents, and with midranks for ties.
    pct_ben, pct_mal = [], []
    for j in range(Zw.shape[1]):
        med = float(np.median(Z_tail[:, j]))
        lo = (Zw[ord_ben_idx, j] < med).mean(); hi = (Zw[ord_ben_idx, j] <= med).mean()
        pct_ben.append(float(50.0 * (lo + hi)))
        lo = (Zw[mal_idx, j] < med).mean(); hi = (Zw[mal_idx, j] <= med).mean()
        pct_mal.append(float(50.0 * (lo + hi)))
    pct_se = 50.0 / np.sqrt(len(tail))
    # Compare on a COMMON scale.  Dividing one side by sd_b and the other by sd_m makes
    # "closer to malicious" easier whenever the malicious population is more dispersed, which
    # would manufacture the conclusion.  Both are already in calibration-standardised units.
    closer_to_mal = int((np.abs(mu_t - mu_m) < np.abs(mu_t - mu_b)).sum())
    closer_to_mal_scaled = int((np.abs(d_from_mal) < np.abs(d_from_ben)).sum())
    order_feat = np.argsort(-np.abs(d_from_ben))
    print(f"    per-feature: the tail's mean is closer to the MALICIOUS population than to "
          f"the benign one on {closer_to_mal} of {len(FEAT)} retained features "
          f"(common scale; {closer_to_mal_scaled} if each side uses its own sd)")
    print(f"    {'feature':>8} {'|d| from benign':>16} {'|d| from malicious':>19} "
          f"{'pct in benign':>14} {'pct in malicious':>17}")
    print(f"    (percentiles carry an SE of about {pct_se:.0f} points from n_tail="
          f"{len(tail)}; the top-8 listing is descriptive, not a multiple-testing result)")
    for j in order_feat[:8]:
        print(f"    {FEAT[j]:>8} {d_from_ben[j]:>16.3f} {d_from_mal[j]:>19.3f} "
              f"{pct_ben[j]:>12.0f}%  {pct_mal[j]:>15.0f}%")

    # categorical enrichment on the destination port
    dport_enrich = None
    if DPORT is not None:
        tp, cnt = np.unique(DPORT[tail], return_counts=True)
        rows_dp = []
        for p_, c_ in sorted(zip(tp.tolist(), cnt.tolist()), key=lambda z: -z[1])[:8]:
            f_tail = c_ / len(tail)
            f_ben = float((DPORT[ord_ben_idx] == p_).mean())
            f_mal = float((DPORT[mal_idx] == p_).mean())
            rows_dp.append(dict(dport=int(p_), n_tail=int(c_), frac_tail=f_tail,
                                frac_benign=f_ben, frac_malicious=f_mal,
                                enrich_vs_benign=(f_tail / f_ben) if f_ben > 0 else None,
                                enrich_vs_malicious=(f_tail / f_mal) if f_mal > 0 else None))
        dport_enrich = rows_dp
        print(f"    {'dport':>7} {'n':>4} {'% tail':>8} {'% benign':>10} {'% malicious':>12} "
              f"{'enrich vs ben':>14} {'enrich vs mal':>14}")
        for r in rows_dp:
            eb = r["enrich_vs_benign"]; em = r["enrich_vs_malicious"]
            print(f"    {r['dport']:>7} {r['n_tail']:>4} {100*r['frac_tail']:>7.1f}% "
                  f"{100*r['frac_benign']:>9.3f}% {100*r['frac_malicious']:>11.3f}% "
                  f"{(eb if eb else float('nan')):>14.1f} {(em if em else float('nan')):>14.1f}")

    out["seeds"][str(dseed)] = dict(
        n_tail=int(len(tail)), NC=int(NC), n_benign_window=int(ben_w.sum()),
        n_malicious_window=int(mal_w.sum()), n_host_matched_pool=int(len(hostmatched_pool)),
        n_ref_malicious=int(len(ref_mal)), n_ref_benign=int(len(ref_ben)),
        n_ref_calibration=int(len(sub)), n_host_port_matched_pool=n_hp_pool,
        geometry=geo,
        per_feature=dict(features=FEAT,
                         d_from_benign=[float(v) for v in d_from_ben],
                         d_from_malicious=[float(v) for v in d_from_mal],
                         pct_in_benign=pct_ben, pct_in_malicious=pct_mal,
                         n_closer_to_malicious=closer_to_mal,
                         n_closer_to_malicious_own_sd=closer_to_mal_scaled,
                         n_features=len(FEAT), dropped_features=dropped_feats,
                         max_standardised_norm=max_norm, pct_se_points=float(pct_se)),
        dport_enrichment=dport_enrich)
    del Zw, Zc, Zm, Zb, Z_tail
    gc.collect()

# =======================================================================================
print("\n" + "=" * 120)
print("E5a — NEAR-NEIGHBOUR GEOMETRY.  rho = d_M / d_B; rho < 1 means the flow's nearest")
print("      malicious neighbour is closer than its nearest ordinary benign one.")
print("=" * 120)
print(f"  {'seed':>5} {'arm':>30} {'n':>6} {'d_M p50':>9} {'d_B p50':>9} {'d_C p50':>9} "
      f"{'rho p50':>9} {'frac rho<1':>11}")
for sd_, r in out["seeds"].items():
    for nm, gv in r["geometry"].items():
        if gv is None: continue
        print(f"  {sd_:>5} {nm:>30} {gv['n']:>6} {gv['d_M'][1]:>9.3f} {gv['d_B'][1]:>9.3f} "
              f"{gv['d_C'][1]:>9.3f} {gv['rho'][1]:>9.3f} {gv['frac_rho_lt_1']:>11.3f}")
print("\n  The HOST-MATCHED baseline is the control that matters: section 4.31 shows the tail")
print("  is concentrated in three host pairs of 25,864, so a random-benign baseline would")
print("  confound 'attack-like' with 'belongs to those hosts'.")

print("\n" + "=" * 120)
print("INTERPRETATION, against the rule fixed before the numbers were seen")
print("=" * 120)
for sd_, r in out["seeds"].items():
    g = r["geometry"]
    t_rho = g["tail"]["rho"][1]
    h_rho = g["baseline_hostmatched_benign"]["rho"][1] if g["baseline_hostmatched_benign"] else None
    rnd = g["baseline_random_benign"]["rho"][1]
    cm = r["per_feature"]["n_closer_to_malicious"]; nf = r["per_feature"]["n_features"]
    print(f"  seed {sd_}: tail rho(p50) = {t_rho:.3f}; host-matched benign "
          f"{h_rho if h_rho is None else format(h_rho, '.3f')}; random benign {rnd:.3f}. "
          f"Tail mean closer to malicious on {cm}/{nf} features.")
print("\n  Neither outcome is proof.  F9's wording caps at 'the best-supported explanation',")
print("  and E5 cannot lift it: a distribution shift confined to the extreme tail would")
print("  produce the same geometry, and separating the two needs the exercise's own logs.")

json.dump(out, open("out/t37_E5_a1gaps.json", "w"), indent=1, allow_nan=True)
print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t37_E5_a1gaps.json")
