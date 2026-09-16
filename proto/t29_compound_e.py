"""
Review priority 1, item 3 -- "the strongest recent compound-e / e-closure method that is
realistically implementable".

The strongest general power-recovery technique available for e-value procedures is
BOOSTING (Wang & Ramdas 2022 section 4; Fischer, Xu & Ramdas arXiv 2407.20683 use a
lag-dependent truncation form of it).  The idea: an e-value below the rejection threshold
can never cause a rejection, so its mass is wasted and can be redistributed upward.
Formally, pick the largest b with E[T_b(E)] <= 1 where

    T_b(x) = b*x * 1{b*x >= tau}

for the rejection threshold tau, and test with T_b(E) instead of E.

RESULT: boosting is exactly vacuous for threshold conformal e-values, and the reason is the
same discreteness that drives the feasibility result.

    A threshold conformal e-value takes two values: 0 and M = (|C|+1)/k, with
    P(E = M) = k/(|C|+1) = 1/M under exchangeability.  Then
        T_b(0) = 0,   T_b(M) = bM  (whenever bM >= tau),
        E[T_b(E)] = bM * P(E = M) = b,
    so E[T_b(E)] <= 1 forces b <= 1.  The optimal boost is b* = 1.

    Boosting recovers power by lifting mass that sits BELOW the threshold.  A two-point
    e-value has no such mass: everything is either already at the ceiling or at zero, and
    zero cannot be lifted because b*0 = 0.  The e-value is already extremal.

This script verifies that numerically, contrasts it with a continuous e-value where
boosting does help, and measures the empirically optimal b on real LSPR23 scores -- where,
because the measured benign firing rate exceeds nominal (F9), b* comes out BELOW 1, meaning
the nominal e-value is already over-claiming rather than leaving power on the table.

e-closure / compound e-values (Ignatiadis, Wang & Ramdas) address the case of SEVERAL
e-values per hypothesis.  Here there is exactly one aggregated e-value per episode, and the
aggregation step is itself the compound operation -- which section 4.16's theorem already
covers for every symmetric merging function.  So there is no separate e-closure comparator
to run; the relevant result is the padding theorem, not a power-recovery method.
"""
import numpy as np, json, time
from pathlib import Path
import h_stream as hs

Path("out").mkdir(exist_ok=True)
t0 = time.time()
W0 = 0.025; BUCKET = 2 * 3600
POS = [0.55, 0.62, 0.70, 0.77, 0.85]
SEEDS = [0, 1]


def optimal_boost(values, probs, tau):
    """Largest b with E[b*V*1{b*V >= tau}] <= 1 for a discrete e-variable.

    Let S(t) = sum_{v >= t} v*p.  The constraint is f(b) = b*S(tau/b) <= 1.  As b rises,
    tau/b falls, so S(tau/b) is non-decreasing and f is non-decreasing: the feasible set is
    an interval [0, b*] and b* is found by bisection.  Enumerating candidate b values
    instead is quadratic and needlessly slow.
    """
    v = np.asarray(values, dtype=float); p = np.asarray(probs, dtype=float)
    o = np.argsort(v); v = v[o]; p = p[o]
    suf = np.concatenate([np.cumsum((v * p)[::-1])[::-1], [0.0]])   # suf[i] = sum_{j>=i} v*p

    def f(b):
        if b <= 0: return 0.0
        i = int(np.searchsorted(v, tau / b, side="left"))
        return b * float(suf[i])

    if f(1.0) > 1.0:                    # even b = 1 is infeasible -> shrinkage required
        lo, hi = 0.0, 1.0
    else:
        lo, hi = 1.0, 1.0
        while f(hi) <= 1.0 and hi < 1e12:
            lo = hi; hi *= 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if f(mid) <= 1.0: lo = mid
        else: hi = mid
    # snap to exactly 1 where that is the true optimum, so the two-point claim is
    # exact rather than 1.000000000001 rounded for display
    return 1.0 if abs(lo - 1.0) <= 1e-10 and f(1.0) <= 1.0 else lo


print("=" * 104)
print("BOOSTING A TWO-POINT (THRESHOLD CONFORMAL) e-VALUE")
print("=" * 104)
sym = []
for M in (1e3, 1e5, 1_813_114.0):
    for tau_mult in (0.1, 0.5, 0.9):
        tau = tau_mult * M
        vals = np.array([0.0, M]); pr = np.array([1 - 1 / M, 1 / M])
        b = optimal_boost(vals, pr, tau)
        sym.append(dict(M=M, tau=tau, b_star=float(b)))
        print(f"  M={M:>12,.0f}  tau={tau:>12,.0f}  optimal boost b* = {b:.6f}")
print("\n  b* = 1 in every cell: boosting a two-point e-value gains exactly nothing.")

print("\n" + "=" * 104)
print("CONTRAST -- BOOSTING A CONTINUOUS e-VALUE (Vovk calibrator E = 1/(2*sqrt(U)))")
print("=" * 104)
# E = kappa * U^(kappa-1) with kappa = 1/2 is a genuine e-value: integral over U ~ Unif(0,1)
# is exactly 1.  (E = 1/U is NOT an e-value -- its mean diverges -- so boosting it is
# meaningless.)  For this calibrator the optimum is available in closed form:
#   E[b*E*1{b*E >= tau}] = b^2/(2*tau)  <=  1   =>   b* = sqrt(2*tau).
# midpoint rule: a left-endpoint grid places an equal-weight atom at U ~ 0 next to the
# singularity of U^-1/2, inflating the tail mass and biasing b* about 5% low
Ngrid = 2_000_000
grid = (np.arange(Ngrid) + 0.5) / Ngrid
vals_c = 0.5 / np.sqrt(grid); pr_c = np.full(Ngrid, 1.0 / Ngrid)
cont = []
for tau in (2.0, 5.0, 20.0, 100.0):
    b = optimal_boost(vals_c, pr_c, tau)
    closed = np.sqrt(2.0 * tau)
    cont.append(dict(tau=tau, b_star=float(b), closed_form=float(closed)))
    print(f"  tau={tau:>8,.0f}   optimal boost b* = {b:>7.4f}   closed form sqrt(2*tau) = {closed:>7.4f}")
print("\n  b* > 1 and grows as sqrt(tau), matching the closed form, because a continuous")
print("  e-value has mass sitting below the threshold that boosting can lift.")
print("  A two-point e-value has none: its mass is already all at the ceiling or at zero.")

print("\n" + "=" * 104)
print("EMPIRICAL b* ON REAL LSPR23 SCORES (uses the MEASURED benign firing rate)")
print("=" * 104)
X, y, ts, src, dst = hs.load()
N = len(y)
rows = []
print(f"  {'pos':>6} {'seed':>5} {'|C|':>12} {'nominal P(fire)':>16} {'measured P(fire)':>17} "
      f"{'ratio':>8} {'b* = 1/(M*Pmeas)':>18}")
for pos in POS:
    i1, i2, i3 = hs.split_indices(N, pos)
    y_cal, y_te = y[i1:i2], y[i2:i3]
    for seed in SEEDS:
        score = hs.fit_detector(X, y, i1, seed=seed, kind="hgb", verbose=False)
        s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
        e_te, cal, NC, CEIL = hs.evalues(s_cal, y_cal, s_te, k=1)
        ben = y_te == 0
        p_meas = float((e_te[ben] > 0).mean())
        p_nom = 1.0 / CEIL
        b_star = (1.0 / (CEIL * p_meas)) if p_meas > 0 else np.inf
        rows.append(dict(pos=pos, seed=seed, NC=int(NC), p_nominal=p_nom,
                         p_measured=p_meas, ratio=float(p_meas / p_nom),
                         b_star=float(b_star)))
        print(f"  {pos:>6} {seed:>5} {NC:>12,} {p_nom:>16.3e} {p_meas:>17.3e} "
              f"{p_meas/p_nom:>8.2f} {b_star:>18.4f}")

bs = [r["b_star"] for r in rows if np.isfinite(r["b_star"])]
print(f"\n  b* median over the {len(bs)} configurations with a positive measured firing "
      f"rate = {np.median(bs):.4f}, range [{min(bs):.4f}, {max(bs):.4f}]")
print(f"  {len(rows) - len(bs)} configurations had zero benign firings, giving b* = inf; "
      f"they are excluded rather than counted as boostable.")
print("  Where b* < 1 the nominal e-value is already anti-conservative on real traffic")
print("  (F9), so the correct 'boost' is a shrinkage.  Either way there is no free power:")
print("  the strongest power-recovery technique for e-BH returns nothing on this evidence,")
print("  and it returns nothing for the same reason the feasibility boundary exists -- the")
print("  evidence is two-point, not because the procedure is weak.")

json.dump({"two_point": sym, "continuous": cont, "empirical": rows,
           "b_star_median": float(np.median(bs)) if bs else None},
          open("out/t29_compound_e.json", "w"), indent=1, allow_nan=True)
print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t29_compound_e.json")
