"""E11, part 1 -- the ANALYTIC derivation behind the per-episode coincidence export,"""


def main():
    import numpy as np, json, math
    from pathlib import Path

    OUT = Path(__file__).resolve().parent / "out"
    OUT.mkdir(exist_ok=True)
    rng = np.random.default_rng(20260827)

    LAM, TAU = 0.25, 0.5
    OK, FAIL = [], []


    def check(name, got, want, tol, note=""):
        ok = abs(got - want) <= tol
        (OK if ok else FAIL).append(name)
        print(f"  [{'ok ' if ok else 'FAIL'}] {name:<62} got={got:<15.9g} want={want:<15.9g} "
              f"tol={tol:.3g} {note}")
        return ok


    def check_bool(name, got, note=""):
        (OK if got else FAIL).append(name)
        print(f"  [{'ok ' if got else 'FAIL'}] {name:<62} {'holds' if got else 'VIOLATED':<15} "
              f"{note}")
        return got


    def pval(n, m, M):
        """Markov p-value of an episode of n flows, m of which fire, at ceiling M."""
        if m <= 0:
            return 1.0
        return min(1.0, n / (M * m))


    EPS = float(np.finfo(np.float64).eps)


    def N_int(alpha_t, m, M):
        """floor(alpha_t*M*m) + 1 as a float, without the p_after round trip."""
        return math.floor(alpha_t * M * m) + 1.0


    def n_need(alpha_t, m, M):
        """Smallest TOTAL episode size whose p-value strictly exceeds alpha_t."""
        return math.floor(alpha_t * M * m) + 1.0


    print("=" * 118)
    print("D1.  THE PADDING MAP IS STRICTLY MONOTONE, SO A MINIMAL SUPPRESSING PAD EXISTS")
    print("=" * 118)
    print("""
    Appending r flows that do not fire leaves m untouched and takes n -> n + r:

            Ev(r) = M*m/(n+r)         P(r) = min(1, (n+r)/(M*m))                        [D1a]

    P(r) is non-decreasing in r and strictly increasing while it is below 1, so
    {r : P(r) > alpha_t} is an up-set and has a least element.  The minimal suppressing pad is
    therefore well defined and is what section 4.30 prices.  (Padding CANNOT lower a p-value:
    this is the same monotonicity that makes the section 4.16 attack one-directional.)
    """)
    bad_mono = 0
    for _ in range(20000):
        M = float(rng.integers(10, 10**7)); m = float(rng.integers(1, 5000))
        n = float(rng.integers(1, 10**6))
        r1, r2 = sorted(rng.integers(0, 10**6, size=2).tolist())
        if pval(n + r1, m, M) > pval(n + r2, m, M) + 1e-15:
            bad_mono += 1
    check("D1a  P(r) non-decreasing in r (20000 random pairs)", bad_mono, 0, 0)

    print("=" * 118)
    print("D2.  THE MINIMAL SUPPRESSING PAD, EXACTLY")
    print("=" * 118)
    print("""
            N*(alpha_t, m) = floor(alpha_t*M*m) + 1     smallest n with P > alpha_t     [D2a]
            r*             = max(N* - n, 0)             minimal pad                     [D2b]

    Verified by exhaustive scan: N* suppresses and N*-1 does not.
    """)
    bad_hi = bad_lo = 0
    for _ in range(20000):
        M = float(rng.integers(4, 10**7)); m = float(rng.integers(1, 5000))
        a = float(rng.uniform(1e-9, LAM))
        N = n_need(a, m, M)
        if not pval(N, m, M) > a:
            bad_hi += 1
        if N - 1 >= 1 and pval(N - 1, m, M) > a:
            bad_lo += 1
    check("D2a  N* suppresses            (20000 random cases)", bad_hi, 0, 0)
    check("D2a  N*-1 does not suppress   (20000 random cases)", bad_lo, 0, 0)

    for M, m, a in ((1_000_000.0, 4.0, 0.25), (2_000_000.0, 2.0, 0.5), (100.0, 1.0, 0.1)):
        x = a * M * m
        check(f"D2a  boundary alpha*M*m={x:.0f} integer -> N*=x+1",
              n_need(a, m, M), x + 1.0, 0, note="ceil(x) would give x and FAIL to suppress")
        check_bool(f"D2a  boundary: P(N*)>alpha at alpha*M*m={x:.0f}", pval(n_need(a, m, M), m, M) > a)
        check_bool(f"D2a  boundary: P(x)<=alpha at alpha*M*m={x:.0f}", pval(x, m, M) <= a)

    print("=" * 118)
    print("D3.  EVERY REJECTED EPISODE NEEDS AT LEAST ONE PAD FLOW")
    print("=" * 118)
    print("""
    ADDIS rejected the episode, so P <= alpha_t, so n <= alpha_t*M*m, and n is an integer, so

            n <= floor(alpha_t*M*m) = N* - 1     hence   r* = N* - n >= 1                [D3a]

    The max(., 0) in the measurement code is therefore an ASSERTION, not a clamp: if it ever
    binds on a detected episode, the level path and the episode stream have gone out of sync.
    The patched t32 asserts pad >= 1 rather than silently clamping.
    """)
    bad_r = 0
    for _ in range(50000):
        M = float(rng.integers(4, 10**7)); m = float(rng.integers(1, 5000))
        a = float(rng.uniform(1e-9, LAM))
        hi = math.floor(a * M * m)
        if hi < 1:
            continue
        n = float(rng.integers(1, hi + 1))
        if not pval(n, m, M) <= a:
            continue
        if n_need(a, m, M) - n < 1:
            bad_r += 1
    check("D3a  rejected => minimal pad >= 1 (50000 random cases)", bad_r, 0, 0)

    print("=" * 118)
    print("D4.  THE PADDED P-VALUE SITS WITHIN ONE CONFORMAL FLOOR UNIT ABOVE alpha_t")
    print("=" * 118)
    print("""
            p+ := P(r*) = N*/(M*m)         and   alpha_t*M*m < N* <= alpha_t*M*m + 1

    so

            alpha_t  <  p+  <=  alpha_t + 1/(M*m)   <=  alpha_t + 1/M                    [D4a]

    1/M is the conformal floor (section 2.2).  The cheapest suppression does not push the
    episode somewhere arbitrary -- it lands it JUST above the level, within one floor unit.
    That is the whole mechanism behind the coincidence.

    A FLOAT CAVEAT THAT IS NOT HARMLESS.  D2a is exact arithmetic; np.floor(alpha_t*M*m)+1 is
    not.  alpha_t*M*m is a float product of magnitude ~1e10, and when the true value sits just
    below an integer the product can round UP to it, making floor -- and therefore N*, the pad
    and p+ -- one too large.  A worked case: alpha_t = 0.24761283661298505, M*m = 35646736295
    gives a float product of exactly 8826589490.0, so the naive form returns 8826589491 while
    8826589490 already suppresses.  The overstatement is one flow in a pad of ~3e7, so it
    changes no reported total, but it breaks the MINIMALITY of n_need, which is the property
    D3a and the bracket both rest on.  t32 therefore computes N* with Fraction on the exact
    binary value of alpha_t, and asserts minimality in exact rational arithmetic rather than
    through the float comparison that is itself the thing that rounds.
    """)
    bad_b = 0
    worst = 0.0
    bad_frac = 0.0
    for _ in range(50000):
        M = float(rng.integers(4, 10**7)); m = float(rng.integers(1, 5000))
        a = float(rng.uniform(1e-9, LAM))
        X = M * m
        p_after = n_need(a, m, M) / X
        if not (a < p_after <= a + 1.0 / X + 1e-15):
            bad_b += 1
        ex = (p_after - a) * X
        bad_frac = max(bad_frac,
                       abs(ex - (N_int(a, m, M) - a * X))
                       / (8.0 * EPS * max(1.0, abs(a * X), abs(N_int(a, m, M)))))
        worst = max(worst, ex)
    check("D4a  bracket alpha < p+ <= alpha + 1/(M*m)  (50000 cases)", bad_b, 0, 0)
    check_bool("D4a  round-trip residual within 8*eps*max(1, alpha*M*m, N*)",
               bad_frac <= 1.0, note=f"worst residual = {bad_frac:.3f} x the bound")
    for a_t, X_t in ((1e-9, 10.0), (5.5e-226, 9.8e9), (0.25, 4e6)):
        N_t = math.floor(a_t * X_t) + 1.0
        ex_t = (N_t / X_t - a_t) * X_t
        bnd = 8.0 * EPS * max(1.0, abs(a_t * X_t), abs(N_t))
        check_bool(f"D4a  bound holds at alpha={a_t:.1e}, M*m={X_t:.1e}",
                   abs(ex_t - (N_t - a_t * X_t)) <= bnd,
                   note=f"residual {abs(ex_t - (N_t - a_t*X_t)):.3e} <= {bnd:.3e}")
    check_bool("D4a  supremum of excess*(M*m) is <= 1", worst <= 1.0 + 1e-12,
               note=f"max over 50000 draws = {worst:.9f}")
    from fractions import Fraction as Fr
    bad_exact = 0
    for _ in range(2000):
        M = int(rng.integers(4, 10**7)); m = int(rng.integers(1, 5000))
        a = Fr(int(rng.integers(1, 10**9)), 4 * 10**9)
        X = Fr(M * m)
        N = Fr(math.floor(a * X) + 1)
        if (N / X - a) * X != 1 - (a * X - math.floor(a * X)):
            bad_exact += 1
    check("D4a  identity excess*(M*m) == 1 - frac in EXACT rational arithmetic",
          bad_exact, 0, 0, note="2000 cases, Fraction -- rules out an algebra error")
    check("D4a  excess*(M*m) == 1 exactly at integral alpha*M*m",
          (n_need(0.25, 4.0, 10**6) / (4.0 * 10**6) - 0.25) * 4.0 * 10**6, 1.0, 1e-9,
          note="alpha*M*m = 1e6, N* = 1e6+1")

    print("=" * 118)
    print("D5.  THE COINCIDENCE IS A THEOREM, NOT A SAMPLE ACCIDENT")
    print("=" * 118)
    print(f"""
    ADDIS advances its spending index on episodes with p in (lam, tau], and CAPS its level at
    lam:  alpha_t = min(lam, (tau-lam)*ah)  (h6_procs.run_addis).  Write
    SAT for alpha_t = lam and LAND for lam < p+ <= tau.

    (a)  SAT => LAND.  If alpha_t = lam then D4a gives p+ > alpha_t = lam for free: the LOWER
         half of the landing condition is automatic.  For the upper half, D4a gives
         p+ <= lam + 1/(M*m), so p+ <= tau whenever

                M*m >= 1/(tau - lam) = {1.0/(TAU-LAM):.0f}                               [D5a]

         D5a is SUFFICIENT, not sharp.  Writing X = M*m (a positive integer, since M = |C|+1
         and m are), the sharp condition is floor(lam*X) + 1 <= tau*X, and at
         (lam, tau) = (0.25, 0.5) the only positive integer that fails it is X = 1.  The
         dimension-free bound X >= 1/(tau-lam) is the one to quote because it does not depend
         on the particular thresholds.  Any episode with a single firing flow has X >= M, and
         M = |C|+1 is in the millions on every window in the record, so D5a is satisfied with
         ~six orders of magnitude to spare.  Cap-saturation therefore FORCES landing.

    (b)  LAND => SAT, except at a boundary of width one floor unit.  If alpha_t < lam then
         landing needs p+ > lam, and p+ <= alpha_t + 1/(M*m), so

                lam - alpha_t < 1/(M*m) <= 1/M                                           [D5b]

         An unsaturated episode can land only if its level is within one CONFORMAL FLOOR of
         lam -- on this stream a window of width 1/M ~ 5.5e-7 out of lam = 0.25.  A blind
         random search over alpha never enters that window, so D5b is checked by drawing
         alpha deliberately inside and outside it.

    (c)  Hence  #LAND >= #SAT  always, with equality unless some detected episode's level
         falls in [lam - 1/M, lam).  The reported 101 = 101 is that equality.  Figure 4B must
         therefore plot alpha_t against p+ with the (lam, tau] band drawn, so the reader sees
         the saturated column sitting on lam and the unsaturated ones sitting on their own
         levels -- NOT a scatter that suggests a correlation.                            [D5c]
    """)
    bad_a = 0
    for M in [4, 5, 8, 16, 100, 1000, 10**4, 10**5, 10**6, 1_813_114]:
        for m in [1, 2, 3, 7, 41, 999, 5000]:
            p_after = n_need(LAM, m, float(M)) / (M * m)
            if not (LAM < p_after <= TAU):
                bad_a += 1
    check("D5a  SAT => LAND on the whole M >= 4 grid (70 cells)", bad_a, 0, 0)
    fails = [X for X in range(1, 200_001)
             if not (LAM < (math.floor(LAM * X) + 1) / X <= TAU)]
    check("D5a  integers X = M*m in 1..2e5 where SAT does NOT imply LAND", len(fails), 1, 0,
          note=f"the failing set is {fails}")
    check("D5a  the single failing X is 1", float(fails[0]) if fails else -1.0, 1.0, 0,
          note="so the sufficient bound X >= 4 is safe but NOT sharp; sharp is X >= 2")
    check_bool("D5a  X = 1 really escapes the band", (math.floor(LAM * 1) + 1) / 1 > TAU,
               note="p+ = 1.0 > tau: one firing flow and a ceiling of 1")
    check_bool("D5a  X = 2 (below the sufficient bound) already lands",
               LAM < (math.floor(LAM * 2) + 1) / 2 <= TAU, note="p+ = 0.5 = tau, inclusive edge")
    bad_b2 = 0; found_near = 0; missed_far = 0
    for _ in range(200000):
        M = float(rng.integers(10**4, 10**7)); m = float(rng.integers(1, 5000))
        X = M * m
        inside = rng.random() < 0.5
        gap = rng.uniform(0.0, 1.0) / X if inside else rng.uniform(1.0, 10.0) / X
        a = LAM - gap
        if a <= 0:
            continue
        p_after = n_need(a, m, M) / X
        landed = LAM < p_after <= TAU
        if landed:
            found_near += 1
            if LAM - a >= 1.0 / X:
                bad_b2 += 1
        elif not inside:
            missed_far += 1
    check("D5b  no unsaturated lander outside the floor window (2e5 targeted cases)",
          bad_b2, 0, 0)
    check_bool("D5b  the test HAS power: unsaturated landers do occur inside the window",
               found_near > 1000, note=f"{found_near} found inside")
    check_bool("D5b  and do not occur outside it", missed_far > 1000,
               note=f"{missed_far} non-landers drawn beyond the window")
    _pe = (math.floor(0.23 * 5) + 1) / 5.0
    check_bool("D5b  concrete unsaturated lander exists (lam=.25, M*m=5, alpha=.23)",
               0.23 < LAM and (LAM < _pe <= TAU),
               note=f"p+ = {_pe}: so 'sat <=> lands' is NOT a theorem, only 'sat => lands'")
    viol = 0
    for _ in range(3000):
        T = int(rng.integers(5, 60))
        M = float(rng.integers(10**5, 2 * 10**6)); m = rng.integers(1, 500, size=T).astype(float)
        a = np.where(rng.random(T) < 0.6, LAM, rng.uniform(1e-6, LAM, size=T))
        N = np.floor(a * M * m) + 1.0
        p_after = N / (M * m)
        sat = a >= LAM; lands = (p_after > LAM) & (p_after <= TAU)
        if int(lands.sum()) < int(sat.sum()):
            viol += 1
    check("D5c  #LAND >= #SAT on 3000 synthetic streams", viol, 0, 0)

    print("=" * 118)
    print("D6.  THE IDENTITIES THE EXPORT MUST SATISFY, AND WHAT FIGURE 4B PLOTS")
    print("=" * 118)
    print("""
    Per detected episode the patched t32 writes rank, m_fire, nsz, alpha_t, n_need, pad,
    p_after, lands, saturated, and the recomputed pre-pad p.  Ten identities tie them
    together; the patch asserts all ten and the aggregates are recomputed FROM THE ARRAYS, so
    the stored scalars can no longer drift from the figure:

       I1  m_fire = sum_e/M is a non-negative integer          (two-point evidence, k = 1)
       I2  Ev     = M*m_fire/nsz
       I3  p      = min(1, nsz/(M*m_fire))
       I4  p     <= alpha_t                                    (every exported episode fired)
       I5  n_need = floor(alpha_t*M*m_fire) + 1                                        [D2a]
       I6  pad    = n_need - nsz >= 1                                                  [D3a]
       I7  alpha_t < p_after <= alpha_t + 1/(M*m_fire)                                 [D4a]
       I8  lands  = (p_after > lam) & (p_after <= tau)
       I9  saturated => lands                                                          [D5a]
       I10 sum(saturated), sum(lands), median(p_after) reproduce the stored aggregates

    Figure 4B: x = alpha_t (log), y = p_after, band (lam, tau] shaded, points split by
    saturated/not.  D5 says the saturated points form a vertical line at x = lam whose y sits
    one floor unit above it -- inside the band by six orders of magnitude.
    """)
    T = 4000
    M = 1_813_114.0
    m_fire = rng.integers(1, 800, size=T).astype(float)
    alpha_t = np.where(rng.random(T) < 0.65, LAM, rng.uniform(1e-7, LAM, size=T))
    nsz = np.floor(rng.uniform(1, 1, size=T) * np.floor(alpha_t * M * m_fire)).astype(float)
    nsz = np.maximum(nsz, 1.0)
    sum_e = M * m_fire
    keep = (nsz <= alpha_t * M * m_fire)
    m_fire, alpha_t, nsz, sum_e = m_fire[keep], alpha_t[keep], nsz[keep], sum_e[keep]
    Ev = sum_e / nsz
    p = np.minimum(1.0, nsz / (M * m_fire))
    N = np.floor(alpha_t * M * m_fire) + 1.0
    pad = N - nsz
    p_after = N / (M * m_fire)
    sat = alpha_t >= LAM
    lands = (p_after > LAM) & (p_after <= TAU)
    check("I1   m_fire integral", float(np.abs(sum_e / M - np.round(sum_e / M)).max()), 0.0, 1e-9)
    check("I2   Ev = M*m/nsz", float(np.abs(Ev - M * m_fire / nsz).max()), 0.0, 1e-9)
    check("I3/I4 p <= alpha_t for all exported", float((p > alpha_t).sum()), 0.0, 0)
    check("I6   pad >= 1 for all exported", float((pad < 1).sum()), 0.0, 0)
    check("I7   bracket holds for all exported",
          float(((p_after <= alpha_t) | (p_after > alpha_t + 1.0 / (M * m_fire) + 1e-15)).sum()),
          0.0, 0)
    check("I9   saturated => lands, all exported", float((sat & ~lands).sum()), 0.0, 0)
    print(f"       synthetic set: {len(p_after)} episodes, {int(sat.sum())} saturated, "
          f"{int(lands.sum())} landing")

    print("=" * 118)
    print("D7.  WHAT THE RECORDED AGGREGATES IMPLY, AS A PRE-CHECK ON THE PATCH")
    print("=" * 118)
    REC = dict(n_detected=147, n_level_saturated=101, n_minimal_pad_lands_in_window=101,
               median_p_after_minimal_pad=0.25000000190185273)
    print(f"""
    out/t32_B1.json currently records {REC['n_detected']} detected episodes,
    {REC['n_level_saturated']} saturated, {REC['n_minimal_pad_lands_in_window']} landing,
    median p+ = {REC['median_p_after_minimal_pad']:.17g}.

    D5c predicts landing >= saturated: {REC['n_minimal_pad_lands_in_window']} >= {REC['n_level_saturated']}.
    D5c predicts equality unless a level lies within 1/M ~ 5.5e-7 of lam: they are EQUAL.
    D4a predicts the median excess median(p+) - lam to be positive and at most 1/M, since more
    than half the detected episodes are saturated ({REC['n_level_saturated']} of {REC['n_detected']}) and for those p+ - lam
    is in (0, 1/(M*m)].
    """)
    excess = REC["median_p_after_minimal_pad"] - LAM
    FLOOR = 1.0 / 1_813_114.0
    check("D7   recorded landing >= saturated",
          float(REC["n_minimal_pad_lands_in_window"] >= REC["n_level_saturated"]), 1.0, 0)
    check_bool("D7   recorded median excess is positive", excess > 0,
               note=f"median(p+) - lam = {excess:.4e}")
    check_bool("D7   recorded median excess <= 1/M", excess <= FLOOR,
               note=f"{excess:.4e} <= {FLOOR:.4e}")
    print(f"       implied M*m at the median episode: 1/excess = {1.0/excess:,.0f}, i.e. that ONE")
    print(f"       episode has m ~ {1.0/(excess*1_813_114.0):,.0f} firing flows.  This is NOT a bound on the median")
    print(f"       m_fire -- the median of p+ and the median of m are different episodes.  The")
    print(f"       exact relation the patch asserts instead:  PROVIDED no unsaturated episode")
    print(f"       lands, every unsaturated p+ is <= lam and every saturated one is > lam, so")
    print(f"       with n episodes and u unsaturated the median is lam plus a specific saturated")
    print(f"       order statistic -- index floor(n/2) - u for odd n, and the mean of indices")
    print(f"       floor(n/2)-1-u and floor(n/2)-u for even n.  The proviso is NOT automatic:")
    print(f"       D5b permits an unsaturated lander (lam=0.25, M*m=5, alpha_t=0.23 gives")
    print(f"       p+ = 0.4, unsaturated AND landing), so t32 asserts the count is zero rather")
    print(f"       than assuming it.  On this stream it is zero.                        [D7a]")

    print("=" * 118)
    print(f"  PASSED {len(OK)} / {len(OK) + len(FAIL)} checks")
    if FAIL:
        print("  FAILED: " + ", ".join(FAIL))
    print("=" * 118)

    json.dump(dict(lam=LAM, tau=TAU,
                   D1a="P(r) = min(1, (n+r)/(M*m)) is non-decreasing: padding cannot lower p",
                   D2a="N* = floor(alpha_t*M*m)+1 is the least size with P > alpha_t "
                       "(ceil(x) is WRONG at integer x)",
                   D2b="r* = N* - n",
                   D3a="rejected => n <= floor(alpha_t*M*m) => r* >= 1; max(.,0) is an assertion",
                   D4a="alpha_t < p+ <= alpha_t + 1/(M*m) <= alpha_t + 1/M (one conformal floor)",
                   D5a="SAT => LAND whenever M*m >= 1/(tau-lam) = 4 (SUFFICIENT, not sharp;"
                       " the only integer M*m that fails is 1)",
                   D5b="LAND & not SAT => lam - alpha_t < 1/(M*m): a floor-width boundary only",
                   D5c="#LAND >= #SAT always; the recorded 101 = 101 is forced, not accidental",
                   fig4b="x = alpha_t (log), y = p_after, shade (lam, tau], split by saturated",
                   D7a="PROVIDED no unsaturated episode lands (asserted, not assumed -- D5b "
                       "permits one at small M*m), median(p+) = lam + a specific saturated "
                       "order statistic; odd and even n handled separately",
                   identities=["m_fire integral", "Ev = M*m/nsz", "p = min(1, nsz/(M*m))",
                               "p <= alpha_t", "n_need = floor(alpha_t*M*m)+1", "pad >= 1",
                               "alpha_t < p_after <= alpha_t + 1/(M*m)",
                               "lands = lam < p_after <= tau", "saturated => lands",
                               "aggregates recomputed from the arrays"],
                   recorded=REC,
                   n_passed=len(OK), n_failed=len(FAIL), failed=FAIL),
              open(OUT / "t32a_E11_derivation.json", "w"), indent=1)
    print("  wrote out/t32a_E11_derivation.json")
    if FAIL:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
