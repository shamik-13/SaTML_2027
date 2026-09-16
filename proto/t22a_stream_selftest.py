"""
Regression test for h_stream.py against numbers already in the record.

If any of these fail, the shared module is NOT the pipeline that produced sections
4.15-4.21 and nothing built on it may be believed.

Targets, position 0.85 / two-hour grouping / seed 0 / k = 1:
  section 4.17  AUROC 0.9992, |C| = 1,813,113, T = 31,568, 255 malicious episodes
  section 4.17  e-LOND under gamma ~ j^-1.6: 72 rejections, 0 false, silent 65.4%,
                first infeasible 10,929;  LORD++: 72, silent 60.8%, first infeasible 12,383
  section 4.19  frontier at FDP 0.000: recall 0.459 on 117 alerts
  section 4.20  ADDIS under gamma ~ j^-1.6: 152 rejections, 147 true, FDP 0.033
                online e-BH under horizon-uniform gamma: 152 rejections, k*_T = 152
"""
import numpy as np
import h_stream as hs
from h6_procs import Ctx, make_gamma, run_lond, run_lordpp, run_addis, run_online_ebh

FAIL = []


def check(name, got, want, tol=None):
    ok = (abs(got - want) <= tol) if tol is not None else (got == want)
    print(f"  [{'ok ' if ok else 'FAIL'}] {name}: got {got}, want {want}")
    if not ok: FAIL.append(name)


X, y, ts, src, dst = hs.load()
N = len(y)
i1, i2, i3 = hs.split_indices(N, 0.85)
score = hs.fit_detector(X, y, i1, seed=0, kind="hgb")
s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
y_cal, y_te = y[i1:i2], y[i2:i3]
e_te, cal, NC, CEIL = hs.evalues(s_cal, y_cal, s_te, k=1)

from sklearn.metrics import roc_auc_score
auroc = roc_auc_score(y_te, s_te)
print("\nstream")
check("|C|", NC, 1_813_113)
check("ceiling", int(CEIL), 1_813_114)
check("AUROC (4dp)", round(float(auroc), 4), 0.9992, tol=1e-9)

ep = hs.build_episodes(e_te, y_te, ts[i2:i3], src[i2:i3], dst[i2:i3], 2 * 3600, "src-dst")
check("T episodes", ep["T"], 31_568)
check("malicious episodes", ep["n_mal"], 255)

ctx = Ctx(ep["Ev"], ep["ismal"], CEIL, alpha=0.05, w0=0.025)
g1p, g0p = make_gamma("poly", ep["T"])
g1u, _ = make_gamma("uniform", ep["T"])

print("\nsection 4.17 procedures")
r = run_lond(ctx, g1p)
check("e-LOND rejections", r[0], 72)
check("e-LOND true positives", r[1], 72)
check("e-LOND first infeasible", r[3], 10_929)
check("e-LOND silent %", round(100 * r[2] / ep["T"], 1), 65.4, tol=1e-9)
r = run_lordpp(ctx, g1p)
check("LORD++ rejections", r[0], 72)
check("LORD++ first infeasible", r[3], 12_383)
check("LORD++ silent %", round(100 * r[2] / ep["T"], 1), 60.8, tol=1e-9)

print("\nsection 4.20 procedures")
r = run_addis(ctx, g0p, lam=0.25, tau_=0.5)
check("ADDIS rejections", r[0], 152)
check("ADDIS true positives", r[1], 147)
eb = run_online_ebh(ctx, g1u)
check("online e-BH rejections (uniform)", eb[0], 152)
check("online e-BH k*_T (uniform)", eb[4], 152)

print("\nsection 4.19 frontier")
smax = np.full(ep["T"], -np.inf)
np.maximum.at(smax, ep["gid"], s_te)
smax = smax[ep["order"]]
fr = hs.frontier(smax, ep["ismal"])
rec, fdp, alerts = hs.frontier_at_fdp(fr, 0.0)
check("frontier alerts at FDP 0", alerts, 117)
check("frontier recall at FDP 0 (3dp)", round(rec, 3), 0.459, tol=1e-9)

print("\n" + "=" * 78)
print("ALL REGRESSION CHECKS PASSED" if not FAIL else "FAILURES: " + ", ".join(FAIL))
print("=" * 78)
raise SystemExit(1 if FAIL else 0)
