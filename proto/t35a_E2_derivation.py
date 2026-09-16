"""
E2, part 1 -- the ANALYTIC derivation of periodic controller restart, verified numerically.

Runs before t35_E2_restart.py touches LSPR23.  Same contract as t34a: every closed form the
real-data script relies on is derived here and checked, so a disagreement between the two is
a bug rather than a finding (docs/01_HANDOFF_PHASE4.md section 6).

No data files are read.  Runtime ~15 s.

======================================================================================
NOTATION
======================================================================================
    M = |C| + 1        evidence ceiling at k = 1 (the reciprocal of the p-value floor)
    T                  hypotheses (episodes) over the whole deployment horizon
    n                  number of restart epochs;  T_ep = T/n
    alpha = q = 0.05,  w0 = alpha/2 = 0.025
    gamma_t            spending sequence; poly is t^-1.6 / zeta(1.6), uniform is 1/T_ep

======================================================================================
D1.  RESTART BUYS FEASIBILITY EXACTLY LINEARLY IN THE NUMBER OF EPOCHS
======================================================================================
Section 4.13's corollary: feasibility over a horizon with no prior rejections requires
`|C| >= k/alpha_T - 1`, and under the horizon-uniform (max-min optimal) sequence
`alpha_T = c/T` where the COLD-START COEFFICIENT `c` is PROCEDURE-DEPENDENT:

        LOND    alpha_t = alpha*gamma_t*(R+1),  so at R = 0   c = alpha  = 0.05
        LORD++  alpha_t = gamma_t*w0 + ...,     so with no    c = w0     = 0.025
                                                rejections
The record's margin `(|C|+1)*w0/T - 1` is therefore the **Family-II / LORD++** convention,
and it is the one used throughout sections 4.15/4.20 and here; LOND's cold-start requirement
is exactly HALF of it, i.e. LOND is feasible over twice the horizon LORD++ is.  Both are
reported.  Restart resets the wealth, so each epoch is a fresh horizon of `T_ep`:

        required |C|  =  k*T_ep/c - 1                                            [D1a]
        margin_n      =  M*c/T_ep - 1  =  n*(margin_1 + 1) - 1   for EQUAL epochs [D1b]

so `n` epochs multiply `(margin + 1)` by exactly `n` **when the epochs are equal**.  Real
epochs are not equal: an epoch is a wall-clock hour and LSPR23's traffic is bursty.  The
binding quantity is then the LARGEST epoch, and D1b holds with `T_ep -> max_i T_i`, which is
what the real-data script reports beside the mean.                                     [D1c]

**This is the same lever as coarsening.** H2/section 4.29 buys feasibility by merging
episodes, which divides `T` by the coarsening factor; restart divides the per-controller
horizon by `n`.  Both reduce the hypothesis count a single controller run must survive, and
D1b is the identical formula.  The difference is the price:
  * coarsening pays in EPISODE RESOLUTION (H2's measured cost: episode recall 0.518 -> 0.226);
  * restart pays in the GUARANTEE (D5: per-epoch FDR does not pool) and in `n` fresh
    first-rejection deadlines (D2).
Restart is therefore not a free substitute for coarsening; it moves the cost somewhere else.

======================================================================================
D2.  EACH EPOCH PAYS A FRESH FIRST-REJECTION DEADLINE
======================================================================================
Before any rejection the whole test level is `gamma_t` times the initial wealth, so a
rejection is possible at step `t` of an epoch only while `alpha_t >= 1/M`.

  POLYNOMIAL gamma_t = t^-1.6 / zeta(1.6):
        LOND    (alpha_t = alpha*gamma_t)  ->  t <= D_LOND = (alpha*M/zeta)^(1/1.6)   [D2a]
        LORD++  (alpha_t = w0*gamma_t)     ->  t <= D_LORD = (w0*M/zeta)^(1/1.6)      [D2b]
  The deadline grows only as `M^0.625`, so a 10x larger calibration set buys 4.2x deadline.

  HORIZON-UNIFORM gamma_t = 1/T_ep (an ORACLE, caveat C1):
        alpha_t = alpha/T_ep is CONSTANT, so there is no deadline at all: the epoch is
        feasible at every step iff  T_ep <= alpha*M,  and otherwise at none.           [D2c]
  Restart under uniform gamma is therefore a CLIFF, not a decay -- it either makes the whole
  epoch feasible or nothing.

FEASIBLE-SLOT ACCOUNTING.  From a cold start under polynomial gamma an uninterrupted run has
`D` feasible slots and is then absorbing (F1/F2) until a rejection; `n` epochs have `n*D`.
        feasible slots:  n*D  against  D                                              [D2d]
so restart multiplies the rejection-free feasible prefix by `n` -- but leaves `T - n*D`
hypotheses unreachable, and `D` does not depend on `n`.

======================================================================================
D3.  THE FRACTION OF EPOCHS THAT GO SILENT
======================================================================================
Let `pi` be the fraction of episodes that are malicious and `phi` the probability that a
malicious episode's aggregated evidence clears the level it is offered.  Treating positions
in the feasible prefix as exchangeable,

        P(epoch yields at least one discovery) ~= 1 - (1 - pi*phi)^min(D, T_ep)        [D3a]
        E[fraction of epochs with zero discoveries] = (1 - pi*phi)^min(D, T_ep)        [D3b]

`phi` is NOT a free parameter: it is the realised per-episode firing rate and is measured,
not assumed.

**D3b is an EXCHANGEABLE-NULL reference, not a bound on the real stream, and the real-data
script does not assert against it.**  It assumes malicious episodes are exchangeable within
an epoch.  LSPR23's attack prevalence rises steeply through the stream (deciles 0.0033 ->
0.5532), so within any epoch the malicious episodes are not exchangeable: front-loaded
attacks make the realised silence LOWER than D3b, back-loaded attacks make it HIGHER.
Neither direction is guaranteed, so D3b is reported as the reference a permuted stream would
give, and the realised silent-epoch fraction is reported beside it as a measurement.

======================================================================================
D4.  ALPHA-BUDGETED RESTART
======================================================================================
Allocating a precommitted budget `q_i` to epoch `i` with `sum_i q_i = q` (so the deployment
spends `q` in total rather than `q` per epoch) scales that epoch's initial wealth to
`w0_i = q_i/2`, hence

        margin_i = M*q_i/(2*T_ep) - 1,   and the deadline scales as q_i^(1/1.6)        [D4a]

Under a uniform allocation `q_i = q/n` the two effects cancel exactly against D1b:

        margin_i = M*(q/2n)/(T/n) - 1 = M*w0/T - 1 = margin of the UNINTERRUPTED run   [D4b]

**A uniformly alpha-budgeted restart buys no feasibility at all.**  Restart helps only if
each epoch is allowed to spend the full `q`, which is exactly the case in which the pooled
guarantee is lost (D5).  That is the whole trade, in one line.

======================================================================================
D5.  PER-EPOCH FDR CONTROL DOES NOT POOL; mFDR DOES
======================================================================================
Write `V_i, R_i` for false and total discoveries in epoch `i`.

  mFDR AGGREGATES, by the mediant inequality.  If `E[V_i] <= q*E[R_i]` for every `i`, then
  summing gives `sum E[V_i] <= q*sum E[R_i]`, i.e.

        pooled mFDR = sum_i E[V_i] / sum_i E[R_i] <= q                                 [D5a]

  FDR DOES NOT.  Pooled FDP is a weighted average of per-epoch FDPs with DATA-DEPENDENT
  weights `R_i / sum_j R_j`, so pointwise `pooled FDP <= max_i FDP_i`, but the weights
  correlate with the FDPs and the expectation does not aggregate.  Counterexample: let each
  epoch, independently, reject exactly one hypothesis with probability `q` and let that
  rejection be false.  Then `FDR_i = E[V_i/max(R_i,1)] = q` for every epoch, yet pooling
  gives a false discovery whenever ANY epoch fires and no true ones ever, so

        pooled FDR = 1 - (1 - q)^n  ->  1                                              [D5b]

  At q = 0.05 that is 0.226 over 5 epochs, 0.370 over 9, and 0.994 over 100.  The per-epoch
  mFDR here is `E[V_i]/E[R_i] = q/q = 1`, so the example does not contradict D5a -- it
  separates the two criteria, which is the point.

  CONSEQUENCE FOR THE PAPER.  LOND, LORD++ and e-LOND control FDR, not mFDR.  Restarting
  them every epoch therefore controls FDR WITHIN each epoch and controls NOTHING at the
  deployment level beyond the trivial `pooled FDR <= n*q`.  A SOC that restarts daily and
  reports a monthly false-discovery rate is not making the guarantee it thinks it is.
======================================================================================
"""
import numpy as np, json, time
from pathlib import Path
from scipy.special import zeta

Path("out").mkdir(exist_ok=True)
t0 = time.time()
OK, FAIL, NOPOWER = [], [], []


def check(name, got, want, tol, note=""):
    ok = abs(got - want) <= tol
    (OK if ok else FAIL).append(name)
    print(f"  [{'ok ' if ok else 'FAIL'}] {name:<62} got={got:<14.7g} want={want:<14.7g} "
          f"tol={tol:.3g} {note}")
    return ok


def mc_check(name, got, want, n, z=5.0, note="", rel_tol=0.25):
    """Monte-Carlo check sized before it is believed (standing mistake 13, and mistake 17:
    a tolerance wide enough to accept a closed form wrong by a factor of two is not a
    check).  A cell counts as having power only if the z-sigma tolerance is at most
    `rel_tol` of `want`."""
    if not (0.0 <= want <= 1.0):
        FAIL.append(name)
        print(f"  [FAIL] {name:<62} want={want!r} is not a probability")
        return False
    tol = z * np.sqrt(want * (1.0 - want) / n)
    if want <= 0.0 or tol > rel_tol * want:
        NOPOWER.append(name)
        print(f"  [ -- ] {name:<62} got={got:<14.7g} want={want:<14.7g} NO POWER {note}")
        return None
    return check(name + f" [n={n:.0e}]", got, want, tol, note)


ZE = float(zeta(1.6, 1))
ALPHA, W0, K = 0.05, 0.025, 1
rng = np.random.default_rng(20260826)

print("=" * 118)
print("D1  restart buys feasibility exactly linearly in the number of epochs")
print("=" * 118)
for M in (1e5, 8.14e5, 1.813114e6, 2.448994e6):
    for T in (57368, 113784, 250000):
        m1 = M * W0 / T - 1.0
        for n in (2, 5, 9, 14, 24):
            mn = M * W0 / (T / n) - 1.0
            check(f"D1b margin_n = n*(margin_1+1)-1 [M={M:.3g}, T={T}, n={n}]",
                  mn, n * (m1 + 1.0) - 1.0, 1e-9 * max(1.0, abs(mn)))
        req1 = K * T / W0 - 1.0
        reqn = K * (T / 5) / W0 - 1.0
        check(f"D1a required |C| divides by n [M={M:.3g}, T={T}]",
              reqn, (req1 + 1.0) / 5.0 - 1.0, 1e-6 * max(1.0, req1))
print("\n  D1c restart and coarsening as feasibility levers, compared NON-vacuously:")


def epoch_sizes(T, n):
    """Balanced integer epoch sizes, as a real restart produces (up to burstiness)."""
    qq, r = divmod(T, n)
    return [qq + 1] * r + [qq] * (n - r)


T, M = 113784, 2.448994e6
for fac in (2, 4, 8, 9):
    # coarsening: ONE controller over ceil(T/fac) merged episodes
    m_coarse = M * W0 / int(np.ceil(T / fac)) - 1.0
    # restart: fac controllers, the binding one being the largest epoch
    m_restart = min(M * W0 / s - 1.0 for s in epoch_sizes(T, fac))
    check(f"coarsening by {fac}x vs restarting into {fac} epochs [balanced]",
          m_restart, m_coarse, 2e-4 * max(1.0, abs(m_coarse)),
          f"restart {m_restart:+.6f} vs coarsen {m_coarse:+.6f}")
    # and they are NOT identical once the epochs are unbalanced
    # genuinely unbalanced: one epoch holds 70% of the episodes.  A 50/50 split would be
    # exactly balanced at fac = 2 and the check would compare a case against itself.
    unbal = [int(T * 0.7)] + epoch_sizes(T - int(T * 0.7), fac - 1)
    m_unbal = min(M * W0 / s - 1.0 for s in unbal)
    check(f"...but an UNBALANCED restart is strictly worse [{fac} epochs]",
          float(m_unbal < m_coarse - 1e-9), 1.0, 0.0,
          f"unbalanced {m_unbal:+.3f} < coarsened {m_coarse:+.3f}")
print("  The two levers coincide only for balanced epochs and the same cold-start")
print("  coefficient.  What differs is the PRICE: coarsening pays in episode resolution")
print("  (H2), restart pays in the pooled guarantee (D5) and in n fresh deadlines (D2).")

print()
print("=" * 118)
print("D2  each epoch pays a fresh first-rejection deadline")
print("=" * 118)


def deadline(M, w, ze=ZE):
    """Largest t with w*gamma_t >= 1/M for gamma_t = t^-1.6/zeta(1.6); 0 if no step is
    feasible.  Binary search in log space: the closed-form seed plus a linear repair loop
    walks over a million steps for very large M, and t**-1.6 at t = 0 raises."""
    import math
    if M <= 0 or w <= 0:
        return 0
    logb = math.log(w) + math.log(M) - math.log(ze)

    def feasible(t):
        return t >= 1 and logb - 1.6 * math.log(t) >= 0.0

    if not feasible(1):
        return 0
    hi = max(2, int(math.exp(logb / 1.6)) + 2)
    while feasible(hi):
        hi *= 2
    lo = 1
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if feasible(mid):
            lo = mid
        else:
            hi = mid
    return lo


def is_feas(M, w, t, ze=ZE):
    return t >= 1 and w * (float(t) ** -1.6 / ze) * M >= 1.0


for M in (1e2, 1e3, 1e4, 1e6, 1.813114e6, 2.448994e6, 1e12):
    for w, nm in ((ALPHA, "LOND"), (W0, "LORD++")):
        d = deadline(M, w)
        # EXACT: d is feasible (or 0 when nothing is) and d+1 is not.  A tolerance of 1.0,
        # as an earlier version used, accepted ceil() and round() variants of the closed form.
        ok = ((d == 0 and not is_feas(M, w, 1)) or is_feas(M, w, d)) \
            and not is_feas(M, w, d + 1)
        check(f"D2 {nm} deadline is EXACTLY the last feasible step [M={M:.3g}]",
              float(ok), 1.0, 0.0, f"D={d}")
    # the naive floor of the closed form must agree wherever it is >= 1
    dL = deadline(M, ALPHA)
    naive = int(np.floor((ALPHA * M / ZE) ** (1 / 1.6))) if ALPHA * M >= ZE else 0
    check(f"D2a deadline == floor((alpha*M/zeta)^(1/1.6)) exactly [M={M:.3g}]",
          float(dL), float(naive), 0.0)
# the deadline grows as M^0.625
d1 = deadline(1e5, ALPHA); d2 = deadline(1e6, ALPHA)
check("D2 deadline scales as M^(1/1.6) = M^0.625", d2 / d1, 10 ** 0.625, 0.02 * 10 ** 0.625,
      f"{d1} -> {d2} for a 10x larger |C|")
# D2c: uniform gamma has no deadline, only a cliff
for M in (1.813114e6, 2.448994e6):
    for w, nm in ((ALPHA, "LOND"), (W0, "LORD++")):
        for T_ep in (5000, 50000, int(np.floor(w * M)), int(np.floor(w * M)) + 1, 400000):
            feasible_all = (w / T_ep) * M >= 1.0
            check(f"D2c uniform gamma all-or-nothing [{nm}, M={M:.4g}, T_ep={T_ep}]",
                  float(feasible_all), float(T_ep <= w * M), 0.0,
                  f"{nm} cliff at T_ep = {w*M:.1f}")

print()
print("=" * 118)
print("D3  the fraction of epochs that go silent")
print("=" * 118)
for pi in (0.0048, 0.0055, 0.02):
    for phi in (0.3, 0.6, 0.9):
        for D, T_ep in ((903, 6733), (903, 20000), (200, 6733)):
            eff = min(D, T_ep)
            want = (1.0 - pi * phi) ** eff
            n = 200_000
            hits = rng.random((n, eff)) < (pi * phi)
            got = float((~hits.any(1)).mean())
            mc_check(f"D3b silent-epoch fraction [pi={pi}, phi={phi}, D={D}, T_ep={T_ep}]",
                     got, want, n)
            del hits

print()
print("=" * 118)
print("D4  a uniformly alpha-budgeted restart buys no feasibility at all")
print("=" * 118)
for M in (1.813114e6, 2.448994e6):
    for T in (57368, 113784):
        m_unint = M * W0 / T - 1.0
        for n in (2, 5, 9, 14):
            q_i = ALPHA / n
            m_budgeted = M * (q_i / 2.0) / (T / n) - 1.0
            check(f"D4b uniform alpha-budget cancels the restart gain [M={M:.3g},T={T},n={n}]",
                  m_budgeted, m_unint, 1e-9 * max(1.0, abs(m_unint)),
                  f"margin {m_budgeted:+.4f} = uninterrupted {m_unint:+.4f}")
        # a per-epoch full-q restart does gain
        m_full = M * W0 / (T / 9) - 1.0
        check(f"...while a per-epoch full-q restart does gain [M={M:.3g},T={T}]",
              float(m_full > m_unint), 1.0, 0.0, f"{m_full:+.3f} vs {m_unint:+.3f}")
# the deadline under a reduced budget
for n in (2, 5, 9):
    dq = deadline(2.448994e6, ALPHA / n)
    dfull = deadline(2.448994e6, ALPHA)
    check(f"D4a deadline scales as q^(1/1.6) [n={n}]", dq / dfull, n ** (-1 / 1.6),
          0.03 * n ** (-1 / 1.6), f"{dfull} -> {dq}")

print()
print("=" * 118)
print("D5  per-epoch FDR control does not pool; mFDR does")
print("=" * 118)
# D5a: the mediant inequality, checked on random admissible epochs
for trial in range(200):
    k = int(rng.integers(2, 12))
    EV = rng.random(k) * 10.0
    ER = EV / (ALPHA * rng.uniform(0.05, 1.0, k))    # ensures EV_i <= q*ER_i
    assert np.all(EV <= ALPHA * ER + 1e-12)
    if EV.sum() / ER.sum() > ALPHA + 1e-12:
        FAIL.append("D5a mediant inequality"); break
else:
    OK.append("D5a mediant inequality")
    print(f"  [ok ] D5a pooled mFDR <= q whenever every epoch has mFDR_i <= q"
          f"{'':<10} 200 random admissible configurations")
# the inequality is NON-STRICT and the tight case is attainable -- an earlier generator
# excluded it, which would have hidden a wrong direction
for k in (2, 5, 11):
    ER = rng.random(k) * 10.0 + 0.1
    EV = ALPHA * ER
    check(f"D5a equality is attained when every epoch sits at mFDR_i = q [k={k}]",
          float(EV.sum() / ER.sum()), ALPHA, 1e-12)

# D5b: the counterexample, exactly and by simulation
for q in (0.05, 0.1):
    for n in (2, 5, 9, 14, 100):
        want = 1.0 - (1.0 - q) ** n
        nsim = 400_000
        fires = rng.random((nsim, n)) < q
        R = fires.sum(1); V = R.copy()               # every rejection is false
        got = float((V / np.maximum(R, 1)).mean())
        mc_check(f"D5b pooled FDR = 1-(1-q)^n [q={q}, n={n}]", got, want, nsim)
        # and each epoch really is FDR-controlled at exactly q
        per = float((fires[:, 0].astype(float)).mean())
        mc_check(f"     ...while every epoch has FDR_i = q exactly [q={q}, n={n}]",
                 per, q, nsim)
        del fires, R, V
# an (n-1) exponent survives the saturated n = 100 cell, so assert the SHAPE where it bites
for q in (0.05, 0.1):
    for n in (2, 5, 9, 14):
        want = 1.0 - (1.0 - q) ** n
        wrong = 1.0 - (1.0 - q) ** (n - 1)
        sep = abs(want - wrong)
        check(f"D5b the n vs n-1 exponent is separable at q={q}, n={n}",
              float(sep > 5 * np.sqrt(want * (1 - want) / 400_000)), 1.0, 0.0,
              f"|{want:.4f} - {wrong:.4f}| = {sep:.4f}")

print("\n  pooled FDR under per-epoch FDR control at q = 0.05:")
for n in (2, 5, 9, 14, 24, 100):
    print(f"    {n:>4} epochs -> pooled FDR = {1 - 0.95 ** n:.4f}")
# pointwise: pooled FDP never exceeds the worst epoch
worst_ok = True
for _ in range(2000):
    k = int(rng.integers(2, 8))
    R = rng.integers(0, 20, k); V = np.array([rng.integers(0, r + 1) for r in R])
    if R.sum() == 0: continue
    if V.sum() / R.sum() > max((v / r if r else 0.0) for v, r in zip(V, R)) + 1e-12:
        worst_ok = False; break
check("D5 pooled FDP <= max_i FDP_i POINTWISE (the failure is in the expectation)",
      float(worst_ok), 1.0, 0.0, "2000 random configurations")

print()
print("=" * 118)
print(f"D1-D5:  {len(OK)} checks passed, {len(FAIL)} failed, {len(NOPOWER)} without power"
      f"   [{time.time()-t0:.0f}s]")
if FAIL:
    print("  FAILED: " + ", ".join(FAIL))
print("=" * 118)

pred = dict(zeta_1_6=ZE, alpha=ALPHA, w0=W0, k=K,
            D1b="margin_n = n*(margin_1+1) - 1",
            D1c="restart and coarsening are the same feasibility lever; the prices differ",
            D2a="D_LOND = floor((alpha*M/zeta)^(1/1.6))",
            D2b="D_LORD = floor((w0*M/zeta)^(1/1.6))",
            D2c="uniform gamma: whole epoch feasible iff T_ep <= alpha*M, else none",
            D3b="silent-epoch fraction = (1 - pi*phi)^min(D, T_ep)",
            D4b="a uniform alpha-budget across epochs reproduces the uninterrupted margin",
            D5a="pooled mFDR <= q by the mediant inequality",
            D5b="pooled FDR under per-epoch FDR control can reach 1-(1-q)^n",
            deadlines={f"M={M:.6g}": dict(LOND=deadline(M, ALPHA), LORDpp=deadline(M, W0))
                       for M in (8.13684e5, 1.813114e6, 2.448994e6)},
            n_passed=len(OK), n_failed=len(FAIL), failed=FAIL, no_power=NOPOWER)
json.dump(pred, open("out/t35a_E2_derivation.json", "w"), indent=1)
print("  wrote out/t35a_E2_derivation.json")
if FAIL:
    raise SystemExit(1)
