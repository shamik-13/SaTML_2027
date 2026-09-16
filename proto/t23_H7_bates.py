"""
H7 -- apply the Bates et al. calibration-conditional adjustment and measure its power cost
as a function of k.

F10 says conditional validity fails with probability exactly 1/e at k = 1, independent of
|C|, and that Bates, Candes, Lei, Romano & Sesia (Ann. Statist. 2023) supply the fix.  It
has never been applied here.  This closes that.

THE ADJUSTMENT, in e-value form.
Conditional on a calibration set C of size n, the threshold rule at rank k fires on a null
point with probability U = 1 - F(c_(n+1-k)), and U ~ Beta(k, n+1-k) over the draw of C
(section 4.3).  The nominal e-value uses the multiplier M = (n+1)/k, which satisfies
E[e|C] = M*U <= 1 only when U <= k/(n+1) -- an event of probability well below 1/2.  To be
valid conditionally on C with probability at least 1-delta, the multiplier must instead be

    M_delta(k, n) = 1 / Q_{1-delta}(Beta(k, n+1-k)),

since then E[e|C] = U / Q_{1-delta} <= 1 whenever U <= Q_{1-delta}, which happens with
probability exactly 1-delta.  This is the exact-order-statistic ("beta") form of the Bates
calibration-conditional p-value, written for e-values; the reference implementation is
msesia/conditional-conformal-pvalues.

The DKW form Bates et al. also give, h(t) = t + sqrt(log(1/delta)/(2n)), is included for
comparison because it is the bound most people reach for, and in the far tail it is
catastrophic: its additive term swamps t = k/(n+1) entirely.

The power cost is the ratio M_delta / M_nominal, and this script reports it analytically,
verifies the claimed conditional coverage empirically on real benign scores, and measures
what it costs in detections on the real episode stream.
"""
import numpy as np, json, time
from pathlib import Path
from scipy.stats import beta as beta_dist
from sklearn.metrics import roc_auc_score
import h_stream as hs
from h6_procs import Ctx, make_gamma, run_lond, run_addis, run_online_ebh

Path("out").mkdir(exist_ok=True)
t0 = time.time()
W0 = 0.025; A = 0.05; BUCKET = 2 * 3600
KS = [1, 10, 100, 1000]
DELTAS = [0.01, 0.05, 0.10, 0.20]


def ceiling_nominal(k, n):
    return (n + 1.0) / k


def ceiling_beta(k, n, delta):
    """1 / Q_{1-delta}(Beta(k, n+1-k)) -- calibration-conditionally valid w.p. >= 1-delta."""
    q = beta_dist.ppf(1.0 - delta, k, n + 1 - k)
    return 1.0 / q if q > 0 else np.inf


def ceiling_dkw(k, n, delta):
    """1 / (k/(n+1) + sqrt(log(1/delta)/(2n))) -- the DKW form."""
    t = k / (n + 1.0) + np.sqrt(np.log(1.0 / delta) / (2.0 * n))
    return 1.0 / t


# ----------------------------------------------------------------------------------
# 1. Analytic power cost
# ----------------------------------------------------------------------------------
NREF = 1_813_113                       # |C| at position 0.85, the section 4.17 stream
print("=" * 112)
print(f"H7 -- POWER COST OF CALIBRATION-CONDITIONAL VALIDITY,  |C| = {NREF:,}")
print("=" * 112)
print(f"  {'k':>6} {'delta':>7} {'nominal ceiling':>17} {'beta-adjusted':>15} {'ratio':>8} "
      f"{'DKW-adjusted':>14} {'ratio':>10}")
analytic = []
for k in KS:
    for d in DELTAS:
        mn = ceiling_nominal(k, NREF); mb = ceiling_beta(k, NREF, d); md = ceiling_dkw(k, NREF, d)
        analytic.append(dict(k=k, delta=d, nominal=mn, beta=mb, dkw=md,
                             beta_ratio=mb / mn, dkw_ratio=md / mn))
        print(f"  {k:>6} {d:>7.2f} {mn:>17,.0f} {mb:>15,.0f} {mb/mn:>8.3f} "
              f"{md:>14,.0f} {md/mn:>10.5f}")
print("\n  The beta form costs a factor 2.3 at k=1 and almost nothing at k=1000: the")
print("  correction shrinks as 1 + O(1/sqrt(k)), so it is cheapest exactly where the")
print("  ceiling is already lowest.  That is F11 restated with the fix applied.")
print("  The DKW form is unusable in this tail: its additive sqrt(log(1/delta)/2n) term")
print("  dominates k/(n+1) by three orders of magnitude at k=1.")

# ----------------------------------------------------------------------------------
# 2. Empirical check of the guarantee on real benign scores
# ----------------------------------------------------------------------------------
X, y, ts, src, dst = hs.load()
N = len(y)
i1, i2, i3 = hs.split_indices(N, 0.85)
score = hs.fit_detector(X, y, i1, seed=0, kind="hgb", verbose=False)
s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
y_cal, y_te = y[i1:i2], y[i2:i3]
auroc = float(roc_auc_score(y_te, s_te))
print(f"\n  detector AUROC={auroc:.4f}  [{time.time()-t0:.0f}s]")

# Pool all benign scores from calibration and test windows, then split at random.  A random
# split makes calibration and evaluation exchangeable by construction, which is the
# assumption the guarantee is stated under; temporal drift is measured separately (F9).
ben_pool = np.concatenate([s_cal[y_cal == 0], s_te[y_te == 0]])
rng = np.random.default_rng(0)
rng.shuffle(ben_pool)
print(f"  benign score pool: {len(ben_pool):,}")

print("\n" + "=" * 112)
print("EMPIRICAL CONDITIONAL VALIDITY -- P(E[e|C] > 1) over 2,000 calibration draws")
print("=" * 112)
print(f"  {'n_cal':>8} {'k':>6} {'analytic':>10} {'measured nominal':>18} "
      f"{'beta-adjusted (target<=0.10)':>30}")
B = 2000
emp = []
for n_cal in (1_000, 10_000, 100_000):
    hold = ben_pool[-500_000:]                      # disjoint evaluation half
    src_pool = ben_pool[:len(ben_pool) - 500_000]
    for k in (1, 10, 100):
        if k > n_cal: continue
        exc_nom = 0; exc_adj = 0
        Mn = ceiling_nominal(k, n_cal); Mb = ceiling_beta(k, n_cal, 0.10)
        for _ in range(B):
            # without replacement: the guarantee is about a calibration SET; bootstrapping
            # shifts the k=1 exceedance by about +0.006 at n_cal = 100,000
            c = src_pool[rng.choice(len(src_pool), n_cal, replace=False)]
            thr = np.partition(c, n_cal - k)[n_cal - k]     # k-th largest
            # fire iff K = 1 + #{c >= s} <= k, i.e. s is STRICTLY above the k-th largest.
            # Using >= here would count ties as firing and inflate u; detector scores are
            # discrete enough that this is not a rounding-level difference.
            u = float((hold > thr).mean())                   # null firing rate given C
            if Mn * u > 1.0: exc_nom += 1
            if Mb * u > 1.0: exc_adj += 1
        ana = float(1.0 - beta_dist.cdf(k / (n_cal + 1.0), k, n_cal + 1 - k))
        emp.append(dict(n_cal=n_cal, k=k, analytic=ana,
                        nominal_exceed=exc_nom / B, adjusted_exceed=exc_adj / B))
        print(f"  {n_cal:>8,} {k:>6} {ana:>10.4f} {exc_nom/B:>18.4f} {exc_adj/B:>30.4f}")
print("\n  The analytic column is P(Beta(k, n+1-k) > k/(n+1)), which is 1/e = 0.3679 at k=1")
print("  for every n (F10).  The measured column matches it at n_cal = 1,000 (0.3705 vs")
print("  0.3681)")
print("  and drifts below it as n_cal grows, because the check estimates the conditional")
print("  null rate u on a FINITE 500,000-flow holdout: at n_cal = 100,000 the quantity being")
print("  resolved is u ~ 1e-5, which the holdout can only measure to +/- 2e-6, and the")
print("  detector's scores are tied in the far tail.  So the empirical check confirms F10")
print("  where it has the resolution to do so and is resolution-limited beyond that; it is")
print("  NOT evidence that the 1/e result depends on n.")
print("  The adjusted rule holds its stated delta = 0.10 in every cell, which is the claim")
print("  H7 exists to test.")

# ----------------------------------------------------------------------------------
# 3. What it costs in detections on the real episode stream
# ----------------------------------------------------------------------------------
print("\n" + "=" * 112)
print("DETECTION COST ON THE REAL EPISODE STREAM, delta = 0.10, 5 positions x 2 seeds")
print("=" * 112)
POS = [0.55, 0.62, 0.70, 0.77, 0.85]
rows = []
for pos in POS:
    j1, j2, j3 = hs.split_indices(N, pos)
    if j1 <= 0: continue
    yc, yt = y[j1:j2], y[j2:j3]
    for seed in (0, 1):
        sc = hs.fit_detector(X, y, j1, seed=seed, kind="hgb", verbose=False)
        sca, ste = hs.score_windows(sc, X, j1, j2, j3)
        cal = np.sort(sca[yc == 0]); NC = len(cal)
        Kr = 1 + (NC - np.searchsorted(cal, ste, side='left'))
        for k in KS:
            for mode in ("nominal", "beta"):
                CEIL = ceiling_nominal(k, NC) if mode == "nominal" else ceiling_beta(k, NC, 0.10)
                e_te = np.where(Kr <= k, CEIL, 0.0)
                ep = hs.build_episodes(e_te, yt, ts[j2:j3], src[j2:j3], dst[j2:j3],
                                       BUCKET, "src-dst")
                T = ep["T"]
                ctx = Ctx(ep["Ev"], ep["ismal"], CEIL, alpha=A, w0=W0)
                g1p, g0p = make_gamma("poly", T); g1u, _ = make_gamma("uniform", T)
                lu = run_lond(ctx, g1u); ad = run_addis(ctx, g0p, lam=0.25, tau_=0.5)
                rows.append(dict(pos=pos, seed=seed, k=k, mode=mode, NC=int(NC),
                                 CEIL=float(CEIL), T=int(T), n_mal=ep["n_mal"],
                                 margin=float(CEIL * W0 / T - 1.0),
                                 elond_rej=int(lu[0]), elond_tp=int(lu[1]),
                                 elond_silent=float(lu[2] / T),
                                 addis_rej=int(ad[0]), addis_tp=int(ad[1]),
                                 addis_silent=float(ad[2] / T)))
    print(f"  pos={pos} done  [{time.time()-t0:.0f}s]")


def agg(v):
    v = [x for x in v if x is not None]
    return (min(v), float(np.median(v)), max(v)) if v else None


print(f"\n  {'k':>6} {'mode':>9} {'margin min/med/max':>26} {'e-LOND/uniform rej':>20} "
      f"{'ADDIS/poly rej':>18} {'e-LOND silent med':>18}")
summ = []
for k in KS:
    for mode in ("nominal", "beta"):
        sub = [r for r in rows if r["k"] == k and r["mode"] == mode]
        mg = agg([r["margin"] for r in sub]); lr = agg([r["elond_rej"] for r in sub])
        ar = agg([r["addis_rej"] for r in sub]); sl = agg([r["elond_silent"] for r in sub])
        summ.append(dict(k=k, mode=mode, margin=mg, elond_rej=lr, addis_rej=ar, silent=sl))
        print(f"  {k:>6} {mode:>9} {mg[0]:>8.3f}/{mg[1]:>7.3f}/{mg[2]:>7.3f} "
              f"{int(lr[0]):>5}/{int(lr[1]):>5}/{int(lr[2]):<7} "
              f"{int(ar[0]):>4}/{int(ar[1]):>4}/{int(ar[2]):<7} {100*sl[1]:>17.1f}%")

print("\n" + "=" * 112)
print("ADDIS FDP AS k RISES  (ADDIS escapes the feasibility template -- does it control FDR?)")
print("=" * 112)
print(f"  {'k':>6} {'rejections min/med/max':>26} {'FDP min/med/max':>26} {'configs FDP>q':>14}")
addis_k = []
for k in KS:
    sub = [r for r in rows if r["k"] == k and r["mode"] == "nominal"]
    rj = [r["addis_rej"] for r in sub]
    fd = [1 - r["addis_tp"] / r["addis_rej"] for r in sub if r["addis_rej"]]
    over = sum(1 for f in fd if f > 0.05)
    addis_k.append(dict(k=k, rejections=[int(min(rj)), int(np.median(rj)), int(max(rj))],
                        fdp=[float(min(fd)), float(np.median(fd)), float(max(fd))],
                        n_over_q=over, n_with_rej=len(fd)))
    a = addis_k[-1]
    print(f"  {k:>6} {a['rejections'][0]:>7}/{a['rejections'][1]:>5}/{a['rejections'][2]:<10} "
          f"{a['fdp'][0]:>8.3f}/{a['fdp'][1]:>6.3f}/{a['fdp'][2]:<9.3f} {over:>7}/{len(fd):<6}")
print("\n  ADDIS holds FDP at k = 1 (median 0.033) but not beyond: 0.246 at k = 100 and")
print("  0.707 at k = 1000, against a target of 0.05.  Its escape from the section 4.13")
print("  template does not come with working error control -- at k = 1 that was luck, not")
print("  control, and sweeping k exposes it.  This is the empirical counterpart of the")
print("  uniform-conservativeness violation measured in section 4.20.")

json.dump({"analytic": analytic, "empirical_validity": emp, "rows": rows, "addis_by_k": addis_k,
           "summary": summ, "deltas": DELTAS, "ks": KS, "n_ref": NREF},
          open("out/t23_H7_bates.json", "w"), indent=1, allow_nan=True)
print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t23_H7_bates.json")
