"""
Self-test for h6_procs.py.  No real data.  Checks the fast implementations against
literal transcriptions of the published formulas, and against three identities the
source papers state:

  1. online e-BH with gamma_i = 1/K, evaluated at t = K, IS the offline e-BH procedure.
  2. R^{e-LOND}_t is a subset of R^{online e-BH}_t   (arXiv 2407.20683 section 2.2).
  3. e-LORD with omega sequence {w_t} IS e-LOND with gamma_t = w_t prod_{j<t}(1-w_j)
     (arXiv 2506.01452 section 3.2).
  4. e-SAFFRON with lam = 0 IS e-LORD (arXiv 2506.01452, remark after Algorithm 2).

Plus literal-vs-fast agreement for SAFFRON and ADDIS, which is where the
index-rewriting D_t - B_j could go wrong.
"""
import numpy as np
from h6_procs import (Ctx, make_gamma, run_lond, run_lordpp, run_saffron, run_addis,
                      run_online_ebh, online_ebh_kstar, run_egai, egai_implied_gamma,
                      _rai_omega)

FAIL = []


def check(name, cond, detail=""):
    print(f"  [{'ok ' if cond else 'FAIL'}] {name}{('  ' + detail) if detail else ''}")
    if not cond: FAIL.append(name)


# ----------------------------------------------------------------------------------
# Literal reference implementations -- O(T^2), transcribed straight from the papers.
# ----------------------------------------------------------------------------------
def ref_saffron(ctx, gam1, lam):
    P = ctx.Pv; T = ctx.T
    rej = tp = silent = 0; first = None; taus = []
    for t in range(1, T + 1):
        C0 = sum(1 for i in range(1, t) if P[i - 1] <= lam)          # tau_0 = 0
        ah = ctx.W0 * gam1[min(t - C0, T + 1)]
        if len(taus) >= 1:
            Cj = sum(1 for i in range(taus[0] + 1, t) if P[i - 1] <= lam)
            idx = t - taus[0] - Cj
            if idx >= 1: ah += (ctx.A - ctx.W0) * gam1[min(idx, T + 1)]
        for tau in taus[1:]:
            Cj = sum(1 for i in range(tau + 1, t) if P[i - 1] <= lam)
            idx = t - tau - Cj
            if idx >= 1: ah += ctx.A * gam1[min(idx, T + 1)]
        lvl = min(lam, (1.0 - lam) * ah)
        if ctx.infeasible(lvl):
            silent += 1
            if first is None: first = t
        elif P[t - 1] <= lvl:
            rej += 1; taus.append(t)
            if ctx.ismal[t - 1]: tp += 1
    return rej, tp, silent, first


def ref_addis(ctx, gam0, lam, tau_):
    P = ctx.Pv; T = ctx.T
    rej = tp = silent = 0; first = None; kaps = []
    for t in range(1, T + 1):
        S = sum(1 for i in range(1, t) if P[i - 1] <= tau_)
        C0 = sum(1 for i in range(1, t) if P[i - 1] <= lam)
        ah = ctx.W0 * gam0[min(S - C0, T + 1)]
        if len(kaps) >= 1:
            k1 = kaps[0]
            kstar = sum(1 for i in range(1, k1 + 1) if P[i - 1] <= tau_)
            Cj = sum(1 for i in range(k1 + 1, t) if P[i - 1] <= lam)
            idx = S - kstar - Cj
            if idx >= 0: ah += (ctx.A - ctx.W0) * gam0[min(idx, T + 1)]
        for kj in kaps[1:]:
            kstar = sum(1 for i in range(1, kj + 1) if P[i - 1] <= tau_)
            Cj = sum(1 for i in range(kj + 1, t) if P[i - 1] <= lam)
            idx = S - kstar - Cj
            if idx >= 0: ah += ctx.A * gam0[min(idx, T + 1)]
        lvl = min(lam, (tau_ - lam) * ah)
        if ctx.infeasible(lvl):
            silent += 1
            if first is None: first = t
        elif P[t - 1] <= lvl:
            rej += 1; kaps.append(t)
            if ctx.ismal[t - 1]: tp += 1
    return rej, tp, silent, first


def ref_offline_ebh(E, alpha):
    """Offline e-BH: k* = max{k : #{j : E_j >= K/(k alpha)} >= k}."""
    K = len(E); best = 0
    for k in range(1, K + 1):
        if np.sum(E >= K / (k * alpha)) >= k: best = k
    if best == 0: return np.zeros(K, dtype=bool)
    return E >= K / (best * alpha)


def ref_elond_set(E, gam1, alpha, T):
    """e-LOND rejection set as an index mask."""
    R = 0; mask = np.zeros(T, dtype=bool)
    for t in range(1, T + 1):
        lvl = alpha * gam1[t] * (R + 1)
        if lvl > 0 and E[t - 1] >= 1.0 / lvl:
            mask[t - 1] = True; R += 1
    return mask


# ----------------------------------------------------------------------------------
print("=" * 84)
print("H6 SELF-TEST")
print("=" * 84)

rng = np.random.default_rng(7)

# ---- 1. SAFFRON / ADDIS: fast vs literal, on several random streams -----------------
print("\nSAFFRON / ADDIS fast implementation vs literal transcription")
ok_s = ok_a = True
for trial in range(6):
    T = 120
    # a mix of zeros (p = 1), moderate and huge e-values, so candidate/selected
    # indicators actually vary -- otherwise the D_t - B_j rewrite is not exercised
    u = rng.random(T)
    Ev = np.where(u < 0.45, 0.0, np.where(u < 0.75, rng.uniform(1.0, 6.0, T),
                                          rng.uniform(6.0, 5e3, T)))
    ismal = rng.random(T) < 0.2
    ctx = Ctx(Ev, ismal, CEIL=1e4)
    for gk in ("poly", "uniform"):
        g1, g0 = make_gamma(gk, T)
        a = run_saffron(ctx, g1, lam=0.5); b = ref_saffron(ctx, g1, 0.5)
        if a != b: ok_s = False; print(f"    SAFFRON mismatch trial={trial} gamma={gk}: {a} vs {b}")
        a = run_addis(ctx, g0, lam=0.25, tau_=0.5); b = ref_addis(ctx, g0, 0.25, 0.5)
        if a != b: ok_a = False; print(f"    ADDIS   mismatch trial={trial} gamma={gk}: {a} vs {b}")
check("SAFFRON fast == literal (6 streams x 2 gamma families)", ok_s)
check("ADDIS   fast == literal (6 streams x 2 gamma families)", ok_a)

# ---- 2. online e-BH with uniform gamma == offline e-BH -----------------------------
print("\nonline e-BH identities")
ok = True
for trial in range(8):
    K = 60
    E = np.where(rng.random(K) < 0.5, 0.0, rng.uniform(0.1, 400.0, K))
    g1 = np.zeros(K + 2); g1[1:K + 1] = 1.0 / K
    ks, m = online_ebh_kstar(E, g1, 0.05, K)
    mine = np.isfinite(m) & (m <= ks[K])
    theirs = ref_offline_ebh(E, 0.05)
    if not np.array_equal(mine, theirs):
        ok = False; print(f"    mismatch trial={trial}: k*={ks[K]} mine={mine.sum()} theirs={theirs.sum()}")
check("online e-BH (gamma=1/K, t=K) == offline e-BH", ok)

ok = True
for trial in range(8):
    T = 200
    E = np.where(rng.random(T) < 0.6, 0.0, rng.uniform(0.1, 1e5, T))
    for gk in ("poly", "uniform"):
        g1, _ = make_gamma(gk, T)
        ks, m = online_ebh_kstar(E, g1, 0.05, T)
        ebh = np.isfinite(m) & (m <= ks[T])
        elond = ref_elond_set(E, g1, 0.05, T)
        if not np.all(ebh[elond]):
            ok = False; print(f"    e-LOND not a subset, trial={trial} gamma={gk}")
check("R(e-LOND) subset of R(online e-BH)  [arXiv 2407.20683 sec 2.2]", ok)

# k*_t must be nondecreasing
ok = True
for trial in range(4):
    T = 300
    E = np.where(rng.random(T) < 0.7, 0.0, rng.uniform(0.1, 1e6, T))
    g1, _ = make_gamma("poly", T)
    ks, _ = online_ebh_kstar(E, g1, 0.05, T)
    if np.any(np.diff(ks) < 0): ok = False
check("k*_t is nondecreasing in t", ok)

# ---- 3. e-LORD == e-LOND with gamma_t = w_t prod(1-w_j) ----------------------------
print("\ne-GAI identities")
ok = True
for trial in range(6):
    T = 400
    E = np.where(rng.random(T) < 0.6, 0.0, rng.uniform(0.1, 1e6, T))
    ismal = rng.random(T) < 0.3
    ctx = Ctx(E, ismal, CEIL=1e6)
    ws = rng.uniform(0.001, 0.02, T)                    # arbitrary fixed omega sequence
    gam = np.zeros(T + 2)
    prod = 1.0
    for t in range(1, T + 1):
        gam[t] = ws[t - 1] * prod; prod *= (1.0 - ws[t - 1])
    a = run_egai(ctx, "e-LORD", w1=ws[0], omega_seq=ws)
    b = run_lond(ctx, gam)
    if a != b: ok = False; print(f"    mismatch trial={trial}: {a} vs {b}")
check("e-LORD(omega) == e-LOND(gamma_t = w_t prod(1-w_j))  [arXiv 2506.01452 sec 3.2]", ok)

ok = True
for trial in range(6):
    T = 300
    E = np.where(rng.random(T) < 0.6, 0.0, rng.uniform(0.1, 1e6, T))
    ismal = rng.random(T) < 0.3
    ctx = Ctx(E, ismal, CEIL=1e6)
    a = run_egai(ctx, "e-SAFFRON", w1=1.0 / T, lam=0.0)
    b = run_egai(ctx, "e-LORD", w1=1.0 / T)
    if a != b: ok = False; print(f"    mismatch trial={trial}: {a} vs {b}")
check("e-SAFFRON(lam=0) == e-LORD  [arXiv 2506.01452, after Alg 2]", ok)

# RAI update must survive long rejection streaks without cancelling to zero.
# Naive 1 + a - b loses w1*psi^n once psi^n < eps (n >= 53 at psi = 0.5); a floor at 1e-15
# would then INFLATE the level by orders of magnitude and manufacture extra rejections.
check("RAI omega exact after 60 consecutive rejections",
      np.isclose(_rai_omega(1e-3, 0.5, 0.5, 0, 60), 1e-3 * 2.0 ** -60, rtol=1e-12),
      f"got {_rai_omega(1e-3, 0.5, 0.5, 0, 60):.6e}, want {1e-3 * 2.0**-60:.6e}")
E = np.r_[np.full(60, 1e100), [1e15], np.zeros(4)]
ctxR = Ctx(E, np.ones(len(E), dtype=bool), CEIL=1e100)
check("no floor-induced extra e-GAI rejection after a 60-rejection streak",
      run_egai(ctxR, "e-LORD", 1e-3)[0] == 60, f"rejections={run_egai(ctxR, 'e-LORD', 1e-3)[0]}")
check("RAI omega stays in (0,1) across the parameter grid",
      all(0.0 < _rai_omega(w, ph, ps, na, nr) < 1.0
          for w in (1e-5, 1e-3, 0.05, 0.4) for ph in (0.0, 0.1, 0.5)
          for ps in (0.0, 0.1, 0.5) for na in (0, 1, 7, 200) for nr in (0, 1, 7, 200)))

# implied gamma must be a valid spending sequence: nonnegative and summing to <= 1
T = 5000
ctx = Ctx(np.zeros(T), np.zeros(T, dtype=bool), CEIL=1e6)
g = egai_implied_gamma(ctx, 1.0 / T)
check("e-LORD implied gamma is a valid spending sequence",
      bool((g >= 0).all() and g.sum() <= 1.0 + 1e-12), f"sum={g.sum():.6f}")

# online e-BH: the shared `silent` column must be the AT-ARRIVAL notion, and
# never_rejectable must be no larger than it.
T = 100; CEILt = 100.0
g1 = np.zeros(T + 2); g1[1:T + 1] = 1.0 / T
ctxE = Ctx(np.full(T, CEILt), np.zeros(T, dtype=bool), CEIL=CEILt)
rj, tp_, sil, fi, kf, lg, never = run_online_ebh(ctxE, g1)
arr = int(np.sum(CEILt * 0.05 * g1[1:T + 1] * np.arange(1, T + 1) < 1.0))
check("online e-BH `silent` is the at-arrival metric", sil == arr, f"silent={sil}, at-arrival={arr}")
check("online e-BH never_rejectable <= at-arrival silent", never <= sil, f"{never} <= {sil}")

# ---- 4. baselines: LOND/LORD++ sanity ---------------------------------------------
print("\nbaseline sanity")
# horizon chosen so the feasibility boundary is actually crossed inside the stream:
# LOND at R=0 is feasible iff alpha*gamma_t*CEIL >= 1, which fails from t ~ 274 here.
T = 2000; CEIL = 1e5
ctx = Ctx(np.zeros(T), np.zeros(T, dtype=bool), CEIL=CEIL)
g1, _ = make_gamma("poly", T)
r_lond = run_lond(ctx, g1); r_lord = run_lordpp(ctx, g1)
check("all-zero evidence gives no rejections", r_lond[0] == 0 and r_lord[0] == 0)
check("all-zero evidence: LOND goes silent and stays silent",
      r_lond[3] is not None and r_lond[2] == T - r_lond[3] + 1,
      f"first infeasible t={r_lond[3]}, silent={r_lond[2]} of {T}")

# a rejection must raise the LOND level, so the first-infeasible time moves later
Ev2 = np.zeros(T); Ev2[0] = CEIL
ctxB = Ctx(Ev2, np.zeros(T, dtype=bool), CEIL=CEIL)
b = run_lond(ctxB, g1)
check("a rejection extends the LOND feasibility horizon",
      b[3] is not None and b[3] > r_lond[3], f"{r_lond[3]} -> {b[3]}")

# ---- 5. feasibility condition matches the section 4.13 closed form -----------------
# LOND with R=0 is feasible at t iff alpha*gamma_t*CEIL >= 1
T = 2000; CEIL = 1e5
ctx = Ctx(np.zeros(T), np.zeros(T, dtype=bool), CEIL=CEIL)
g1, _ = make_gamma("poly", T)
pred = int(np.sum(0.05 * g1[1:T + 1] * CEIL < 1.0))
got = run_lond(ctx, g1)[2]
check("LOND silent count matches closed form alpha*gamma_t*CEIL < 1", pred == got,
      f"closed form={pred}, simulated={got}")

print("\n" + "=" * 84)
print(f"{'ALL CHECKS PASSED' if not FAIL else 'FAILURES: ' + ', '.join(FAIL)}")
print("=" * 84)
raise SystemExit(1 if FAIL else 0)
