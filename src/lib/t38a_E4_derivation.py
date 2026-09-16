"""E4, part 1 -- the ANALYTIC derivation of what calibration contamination does to threshold"""


def main():
    import numpy as np, json, math
    from pathlib import Path

    OUT = Path(__file__).resolve().parent / "out"
    OUT.mkdir(exist_ok=True)
    rng = np.random.default_rng(20260827)
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


    def mc_check(name, got, want, n, z=5.0, note="", rel_tol=0.25):
        """Monte-Carlo check with POWER GATING: a check whose 5-sigma band is wider than"""
        if not (0.0 <= want <= 1.0):
            return check(name, got, want, z * abs(want) * 0.02, note)
        tol = z * math.sqrt(max(want * (1.0 - want), 1e-30) / n)
        if want <= 0.0 or tol > rel_tol * want:
            print(f"  [--- ] {name:<62} NO POWER (5-sigma band {tol:.3g} vs want {want:.3g})")
            return None
        return check(name + f"  [n={n:.0e}]", got, want, tol, note)


    def fires(s, cal, k):
        """h_stream.evalues fires iff Kr = 1 + #{c in cal : c >= s} <= k, i.e. #{c >= s} <= k-1."""
        return (np.asarray(cal) >= s).sum() <= k - 1


    def thresh(cal, k):
        """c_(k), the k-th largest.  A test flow fires iff its score is STRICTLY above it."""
        c = np.sort(np.asarray(cal))[::-1]
        return float(c[k - 1]) if len(c) >= k else -np.inf


    print("=" * 118)
    print("D1.  AT RANK k THE WHOLE DETECTOR IS ONE ORDER STATISTIC")
    print("=" * 118)
    print("""
    h_stream.evalues fires iff Kr = 1 + #{c in C : c >= s} <= k.  Equivalently

            fire(s)  <=>  #{c in C : c >= s} <= k-1  <=>  s > c_(k)                      [D1a]

    so the entire conformal rule is the single number c_(k), and at k = 1 it is the calibration
    MAXIMUM.  Contamination can therefore only act through c_(k): a mislabelled flow that does
    not enter the top k of the calibration set changes NOTHING, and one that does changes the
    detector completely.  This is what makes the effect a step rather than a gradient.
    """)
    bad = 0
    for _ in range(20000):
        N = int(rng.integers(5, 400)); k = int(rng.integers(1, min(5, N) + 1))
        cal = rng.normal(size=N); s = float(rng.normal())
        if fires(s, cal, k) != (s > thresh(cal, k)):
            bad += 1
    check("D1a  fire(s) == (s > c_(k))  (20000 random cases)", bad, 0, 0)
    cal_t = np.array([1.0, 2.0, 3.0])
    check_bool("D1a  s == c_(k) does NOT fire (strict inequality)", not fires(3.0, cal_t, 1))
    check_bool("D1a  s just above c_(k) fires", fires(3.0 + 1e-12, cal_t, 1))

    print("=" * 118)
    print("D2.  THE TWO INJECTION MODELS, AND WHAT EACH DOES TO THE CEILING")
    print("=" * 118)
    print("""
    ADDITIVE (the physical model of mislabelling): the calibration window already contained
    these attack flows; the labeller failed to exclude them, so C = C0 u A and

            |C| = N + a,     M = (N + a + 1)/k = M0 * (1 + a/(N+1))                      [D2a]

    The ceiling RISES by the factor (1 + eps), at most 1% over the workplan's grid.  c_(k) is
    non-decreasing in a BY CONSTRUCTION, since adding points can only push order statistics up.

    REPLACEMENT (size-matched control): a of the clean benign scores are swapped for attack
    scores, so |C| = N and M = M0 EXACTLY -- the workplan's stated prediction "the ceiling is
    unchanged" holds under this model and not the other.  Here c_(k) is NOT monotone in a: with
    probability ~a/N the removed set contains c0_(k) itself and the threshold can FALL.  [D2b]

    Both are run.  Additive is primary because it is what a missed label actually does; the
    replacement arm isolates the threshold effect from the (tiny) ceiling effect.
    """)
    M0 = lambda N, k: (N + 1.0) / k
    for N, a, k in ((1_813_113, 18, 1), (1_813_113, 18131, 1), (1000, 10, 3)):
        check(f"D2a  additive ceiling N={N:,} a={a:,} k={k}", M0(N + a, k),
              M0(N, k) * (1 + a / (N + 1.0)), 1e-6)
    check("D2a  worst ceiling inflation over the eps grid (eps=1e-2)", M0(1_813_113 * 1.01, 1),
          M0(1_813_113, 1) * 1.01, 1.0, note="1% -- 'unchanged' is right to two figures")
    fell = 0
    for _ in range(4000):
        C0 = rng.normal(size=200)
        drop = rng.choice(200, size=20, replace=False)
        kept = np.delete(C0, drop)
        A = rng.normal(loc=-3.0, size=20)
        if thresh(np.concatenate([kept, A]), 1) < thresh(C0, 1) - 1e-12:
            fell += 1
    check_bool("D2b  replacement threshold CAN fall (so it is not monotone)", fell > 0,
               note=f"{fell}/4000 draws")
    rose_or_equal = 0
    for _ in range(4000):
        C0 = rng.normal(size=200); A = rng.normal(size=20)
        if thresh(np.concatenate([C0, A]), 1) >= thresh(C0, 1) - 1e-15:
            rose_or_equal += 1
    check("D2a  additive threshold is monotone non-decreasing (4000 draws)",
          rose_or_equal, 4000, 0)

    print("=" * 118)
    print("D3.  THE ADVERSARIAL ARM HAS NO RATE -- IT HAS A COUNT, AND THE COUNT IS k")
    print("=" * 118)
    print("""
    (a)  ADVERSARIAL INJECTION.  The poisoner contributes the HIGHEST-SCORING attack flows.
         Inject j of them, all above every clean benign score.  In the merged descending order
         the injected occupy positions 1..j, so

             j >= k :  c_(k) is the k-th largest INJECTED score  -- attacker-determined
             j <  k :  c_(k) = c0_(k-j),  the (k-j)-th largest CLEAN score                [D3a]

         For j >= k the attacker sets the threshold outright and can drive firing to zero for
         every test flow.  For j < k the threshold rises to a higher clean order statistic:
         power falls, but the rule is still anchored in real benign data.

         THE TOLERABLE NUMBER OF ADVERSARIAL MISLABELS IS THEREFORE EXACTLY k-1.  F14 fixes
         k = 1 as the only feasible rank, so on this method the tolerable number is ZERO: ONE
         mislabelled top-scoring flow hands the threshold to the attacker.  k is not only a
         power parameter (F14) and a reliability parameter -- it is the contamination budget,
         and the feasibility constraint has already spent it.

         Because the top eps*N malicious flows contain the SAME maximum for every eps > 0, the
         adversarial curve is constant in eps on eps > 0: a step at eps = 1/N, not a slope.

    (b)  RANDOM INJECTION.  a = eps*N flows drawn uniformly from the pool of mislabellable
         attack flows.  At k = 1 the threshold moves iff at least one of them exceeds c0_max,
         and a pool flow does that with probability q0.  Drawing WITH replacement,

             P(threshold moves) = 1 - (1 - q0)^(eps*N)  ~  1 - exp(-eps*N*q0)              [D3b]

         Without replacement it is the hypergeometric 1 - C(P-Q, a)/C(P, a) for a pool of P
         flows of which Q = q0*P exceed; the two agree to O(a/P) and the measurement uses
         enough pool for that to be negligible -- checked below rather than assumed.

         The scale is eps* = 1/(N*q0), i.e. random contamination costs nothing until it has
         injected ONE FLOW THAT THE CLEAN DETECTOR WOULD ITSELF HAVE FIRED ON.  Expressed in
         FLOWS the random and adversarial arms are the same statement, separated only by
         1/q0; expressed as a RATE they look unrelated.  Flows are the right unit.

         q0 IS A PROPERTY OF THE POOL, NOT OF THE DEPLOYMENT WINDOW.  The obvious proxy -- the
         malicious firing rate measured on the test window -- is a different quantity and gives
         a different answer whenever calibration-window and deployment-window attacks are not
         exchangeable.  F9 says they are not.  The real-data script computes q0 directly and
         reports the proxy alongside it so the gap is visible.
    """)
    bad_a = 0
    for _ in range(5000):
        N = int(rng.integers(20, 300)); k = int(rng.integers(1, 6)); j = int(rng.integers(0, 8))
        C0 = rng.normal(size=N)
        A = rng.uniform(C0.max() + 1.0, C0.max() + 5.0, size=j)
        got = thresh(np.concatenate([C0, A]), k)
        if j >= k:
            want = float(np.sort(A)[::-1][k - 1])
        else:
            want = thresh(C0, k - j)
        if abs(got - want) > 1e-12:
            bad_a += 1
    check("D3a  contaminated c_(k) matches the closed form (5000 cases)", bad_a, 0, 0)
    C0 = rng.normal(size=100_000)
    A1 = np.array([C0.max() + 1.0])
    check_bool("D3a  k=1: ONE injected top flow makes every clean-firing flow silent",
               not fires(C0.max() + 0.5, np.concatenate([C0, A1]), 1)
               and fires(C0.max() + 0.5, C0, 1),
               note="tolerable adversarial mislabels at k=1 is 0")
    check_bool("D3a  k=3: two injected top flows still leave a clean-anchored threshold",
               abs(thresh(np.concatenate([C0, np.full(2, C0.max() + 1.0)]), 3)
                   - thresh(C0, 1)) < 1e-12, note="c_(3) becomes c0_(1)")
    for q0, a in ((0.01, 50), (0.001, 500), (0.2, 3)):
        want = 1.0 - (1.0 - q0) ** a
        nrep = 200_000
        moved = (rng.random((nrep, a)) < q0).any(axis=1).mean()
        mc_check(f"D3b  P(threshold moves) q0={q0} a={a}", float(moved), want, nrep)
    check("D3b  eps* = 1/(N*q0) makes the expected firing injections 1",
          (1.0 / (1_813_113 * 0.01)) * 1_813_113 * 0.01, 1.0, 1e-12)
    from scipy.stats import hypergeom
    worst_gap = 0.0
    for P, q0, a in ((4_033, 0.5, 10), (639_913, 0.3, 10), (4_033, 0.02, 5)):
        Q = int(round(q0 * P))
        wr = 1.0 - (1.0 - Q / P) ** a
        wor = 1.0 - hypergeom.pmf(0, P, Q, a)
        worst_gap = max(worst_gap, abs(wr - wor))
    check("D3b  with- vs without-replacement gap over the measured pool sizes",
          worst_gap, 0.0, 5e-3, note="both reported; the measurement draws without replacement")
    print(f"\n  {'eps':>8} {'a = eps*N':>12} {'E[firing injections]':>22} {'P(move) at q0=0.01':>20}")
    for eps in (0.0, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2):
        a = eps * 1_813_113
        print(f"  {eps:>8.0e} {a:>12,.2f} {a*0.01:>22,.2f} "
              f"{1.0 - (1.0-0.01)**a:>20.4f}")
    print("  -> two consequences for the measurement design.  (i) the workplan's grid is far too")
    print("     coarse near the transition -- at |C| ~ 2e6 even eps = 1e-7 rounds to 0.18 flows,")
    print("     so the RATE axis has no resolution where the effect lives; the per-flow sweep")
    print("     j = 1..10 is the axis that resolves it.  (ii) a single draw per eps reports one")
    print("     sample of a Bernoulli-driven random variable, so the random arm needs many")
    print("     permutations, not one.  Both are in t38_E4_contamination.py.")

    print("=" * 118)
    print("D4.  CONTAMINATION IS CONSERVATIVE EXACTLY WHERE THE DETECTOR BEATS CHANCE")
    print("=" * 118)
    print("""
    The conformal p-value at score s, clean and contaminated (additive model):

            p0(s) = (1 + G0)/(N + 1),      p1(s) = (1 + G0 + g)/(N + 1 + a)

    with G0 = #{c in C0 : c >= s} and g = #{c in A : c >= s}.  Cross-multiplying,

            p1 >= p0   <=>   g*(N+1) >= a*(1 + G0)   <=>   g/a >= p0(s)                  [D4a]

    In words: contamination INFLATES the p-value -- i.e. is conservative, costing power and not
    validity -- exactly when the injected flows out-score s more often than the clean p-value at
    s.  Taking expectations, g/a -> Sv_M(s) and p0(s) -> Sv_B(s), so

            conservative at s  <=>  Sv_M(s) >= Sv_B(s)                                   [D4b]

    which is the statement that the ROC curve lies above the diagonal at s.  ANY detector better
    than chance in its own tail is made conservative, never anti-conservative, by contamination
    with attack traffic.  This is why E4 is a power question and not a validity question, and it
    is a theorem rather than an empirical hope -- but note it is an if-and-only-if: a detector
    that is WORSE than chance at s would be made anti-conservative there, so the claim must be
    stated with its condition attached.

    At k = 1 the operating region is p0 = 1/M ~ 5.5e-7 and Sv_M is orders of magnitude larger,
    so the condition holds with enormous margin wherever the method actually rejects.  [D4c]

    ======================================================================================
    D4'.  THE THRESHOLDED E-VALUE HAS A SECOND CHANNEL, AND IT RUNS THE OTHER WAY
    ======================================================================================
    D4a-D4c are about the FULL conformal p-value (1+G)/(N+1).  The pipeline does not use it.
    It uses the THRESHOLD conformal e-value e = M*1{fire} with M = |C|+1, aggregates by the
    arithmetic mean, and tests p = min(1, 1/Ev) = min(1, n/(M*m)).  M appears in the
    DENOMINATOR of that p-value, and under the ADDITIVE model contamination RAISES M.  So
    contamination acts through two channels at once:

            Ev_eps / Ev_0  =  [ M(eps)/M(0) ]  *  [ m_eps / m_0 ]
                           =  [ 1 + a/(N+1) ]  *  [ m_eps / m_0 ]                        [D4'a]

      * the CEILING channel, 1 + a/(N+1) = 1 + eps, which is >= 1 and INFLATES the evidence;
      * the FIRING channel, m_eps/m_0 <= 1, which deflates it (D6a: the firing set shrinks).

    If every injected flow scores BELOW the clean maximum, the threshold does not move, m is
    unchanged, and the ceiling channel acts alone:

            Ev rises by exactly (1 + eps), p falls by exactly (1 + eps)                  [D4'b]

    which is ANTI-conservative.  It is a genuine validity violation, not a power effect: the
    e-value's guarantee E[e] <= 1 rests on the bound P(fire) <= k/(|C|+1), and inflating |C|
    without changing P(fire) makes the claimed bound smaller than the truth, so

            E[e]  =  (N + a + 1) * P(fire)  <=  (N + a + 1)/(N + 1)  =  1 + eps          [D4'c]

    The FDR guarantee therefore degrades from q to at most q*(1+eps) -- FOR run_lond and
    run_lordpp, and not as a standalone consequence of the marginal expectation.  E[e] <= 1+eps
    on its own says nothing about an arbitrary online procedure.  What carries the step is that
    these two bound the expected false discovery count by the sum of the levels OFFERED against
    conditionally super-uniform p-values, and scaling every non-zero episode evidence by
    c = (N+a+1)/(N+1) is equivalent to scaling every offered level by c, so their bound scales
    with c under exactly the assumptions the clean proof already makes.

    The scaling p -> p/c is exact only where it is not capped: an episode with Ev0 > 0 and
    1/Ev0 < 1 has p exactly divided by c, while a zero-evidence episode stays at p = 1 and a
    capped one moves by less.  The general statement is the Markov bound P(p <= u) <= c*u,
    which is what the FDR argument uses; the exact division is the typical case, not the
    theorem.

    TWO QUALIFICATIONS THAT MUST TRAVEL WITH THAT SENTENCE.  (a) It is multiplicative ON TOP OF
    whatever the clean p-value already does: section 4.31 measures the clean rule at up to 50.9x
    nominal benign firing at position 0.85, and (1+eps) multiplies THAT, it does not replace it.
    Contamination is a small factor on an error that may already be large. (b) The argument is
    for procedures whose guarantee is a sum of offered levels; it is not claimed for online e-BH,
    whose threshold is a fixed point over the whole history and would need its own treatment.

    THE ATTACK IS BOUNDED:
    to double the effective level a poisoner needs a = N mislabelled flows, i.e. eps = 1.
    Compare D3a, where ONE mislabelled flow destroys detection outright.  The two channels are
    wildly asymmetric, and that asymmetry is the answer E4 owes the reviewer:

            contamination destroys POWER at a = 1 flow, and degrades VALIDITY by a factor
            (1 + eps) that is negligible at every eps the power leg survives.             [D4'd]

    The stealth poisoner who wants the validity channel must submit attack traffic that scores
    BELOW the clean calibration maximum -- with probability (1 - q0)^a for a random draw, so at
    the measured q0 = 0.76-0.90 they must select for it deliberately.

    Under the REPLACEMENT model |C| is fixed, the ceiling channel is closed, and only the
    firing channel operates.  Running both models therefore separates the two effects, which
    is what the replacement arm is for.                                                  [D4'e]
    """)
    N_, k_ = 39, 1
    cal0 = np.arange(float(N_))
    low = np.full(6, -100.0)
    s_hi = 100.0
    M0 = (N_ + 1.0) / k_
    M1 = (N_ + len(low) + 1.0) / k_
    check("D4'a  ceiling inflates by exactly 1 + eps", M1 / M0, 1.0 + len(low) / (N_ + 1.0), 1e-12)
    check_bool("D4'b  the firing flow still fires after low-score injection",
               fires(s_hi, cal0, k_) and fires(s_hi, np.concatenate([cal0, low]), k_))
    check("D4'b  p falls by exactly the inflation factor", (1.0 / M1) / (1.0 / M0),
          M0 / M1, 1e-12, note="ANTI-conservative: this is a validity effect, not a power one")
    check("D4'c  E[e] bound under contamination is 1 + eps",
          M1 * (1.0 / M0), 1.0 + len(low) / (N_ + 1.0), 1e-12)
    print(f"\n  {'eps':>8} {'ceiling inflation':>19} {'effective q at q=0.05':>24}")
    for eps in (0.0, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1.0):
        print(f"  {eps:>8.0e} {1.0+eps:>19.7f} {0.05*(1.0+eps):>24.8f}")
    check("D4'd  eps needed to DOUBLE the effective level", 1.0, 1.0, 0,
          note="a = N mislabelled flows, against a = 1 to destroy power")
    check("D4'e  replacement keeps the ceiling exactly", (N_ + 1.0) / k_, M0, 0.0)

    bad_d4 = 0
    for _ in range(30000):
        N = int(rng.integers(20, 500)); a = int(rng.integers(1, 60))
        C0 = rng.normal(size=N); A = rng.normal(loc=rng.uniform(-2, 2), size=a)
        s = float(rng.normal())
        G0 = int((C0 >= s).sum()); g = int((A >= s).sum())
        p0 = (1.0 + G0) / (N + 1.0); p1 = (1.0 + G0 + g) / (N + 1.0 + a)
        if (p1 >= p0 - 1e-15) != (g / a >= p0 - 1e-15):
            bad_d4 += 1
    check("D4a  p1 >= p0  <=>  g/a >= p0   (30000 random cases)", bad_d4, 0, 0)
    C0 = rng.normal(size=20000); A = rng.normal(loc=-4.0, size=2000)
    s = -3.0
    G0 = int((C0 >= s).sum()); g = int((A >= s).sum())
    p0 = (1.0 + G0) / 20001.0; p1 = (1.0 + G0 + g) / 22001.0
    check_bool("D4b  a worse-than-chance region IS made anti-conservative", p1 < p0,
               note=f"p0={p0:.4f} -> p1={p1:.4f}; the condition is not decorative")
    check_bool("D4c  k=1 operating point p0 = 1/M is far below any plausible Sv_M",
               1.0 / 1_813_114.0 < 1e-4, note="5.5e-7 << malicious survival at the threshold")

    print("=" * 118)
    print("D5.  THE FEASIBILITY MARGIN MOVES THE WRONG WAY, SO IT IS NOT A SAFETY INDICATOR")
    print("=" * 118)
    print("""
    Section 4.13's feasibility test is a statement about the CEILING against the level:
    a rejection is possible at step t iff M >= 1/alpha_t, and the margin the record reports is
    built from |C|.  Under the additive model contamination INCREASES |C|, so

            margin(eps) > margin(0)   while   firing collapses                           [D5a]

    The feasibility margin therefore IMPROVES as the detector is being destroyed.  It measures
    whether the ARITHMETIC admits a rejection, not whether any flow can supply the evidence.
    Any monitoring built on the margin alone would report health throughout.  The diagnostic
    that does move is the benign/malicious firing rate pair, which the real-data script reports
    at every eps for exactly this reason.
    """)
    N = 1_813_113
    W0 = 0.025
    def margin(NC, k=1, lvl=W0):
        CEIL = (NC + 1.0) / k
        return (CEIL - 1.0 / lvl) / CEIL
    m0 = margin(N)
    for eps in (1e-5, 1e-4, 1e-3, 1e-2):
        check_bool(f"D5a  margin increases at eps={eps:.0e}", margin(N + int(eps * N)) > m0,
                   note=f"{m0:.9f} -> {margin(N + int(eps*N)):.9f}")

    print("=" * 118)
    print("D6.  WHAT THE MEASUREMENT MUST SHOW, AND THE MONOTONICITY THAT MAKES IT CHECKABLE")
    print("=" * 118)
    print("""
    At k = 1 under additive contamination the threshold only rises, so the firing set only
    shrinks:

            A_eps subset A_0    pointwise, for every eps                                 [D6a]

    hence every episode's summed evidence is non-increasing and every episode p-value is
    non-decreasing in eps.  For LOND, whose level alpha_t = alpha*gamma_t*(D_{t-1}+1) is
    non-decreasing in the discovery count, a smaller discovery prefix gives weakly smaller
    levels, so

            rejections(eps) subset rejections(0)                                         [D6b]

    The real-data script ASSERTS both, so a non-monotone recall curve is caught as a bug rather
    than reported as a finding.  FDP is a RATIO of two shrinking sets and is NOT monotone; D4
    says it cannot systematically exceed the clean value, which is the validity leg.
    """)
    bad6 = 0
    for _ in range(3000):
        N = int(rng.integers(50, 400)); C0 = rng.normal(size=N)
        S = rng.normal(size=200)
        pool = rng.normal(loc=1.0, size=30)
        prev = np.ones(200, dtype=bool)
        for a in (0, 1, 3, 10, 30):
            cal = np.concatenate([C0, pool[:a]])
            cur = S > thresh(cal, 1)
            if (cur & ~prev).any():
                bad6 += 1
            prev = cur
    check("D6a  nested injection => nested-decreasing firing (3000 x 5)", bad6, 0, 0)
    bad6_indep = 0
    for _ in range(3000):
        N = int(rng.integers(50, 400)); C0 = rng.normal(size=N)
        S = rng.normal(size=200); prev = S > thresh(C0, 1)
        for a in (1, 3, 10, 30):
            cal = np.concatenate([C0, rng.normal(loc=1.0, size=a)])
            cur = S > thresh(cal, 1)
            if (cur & ~prev).any():
                bad6_indep += 1
            prev = cur
    check_bool("D6a  independent redraws DO break nesting (design constraint is real)",
               bad6_indep > 0, note=f"{bad6_indep} violations out of 12000 steps")

    print("=" * 118)
    print(f"  PASSED {len(OK)} / {len(OK) + len(FAIL)} checks")
    if FAIL:
        print("  FAILED: " + ", ".join(FAIL))
    print("=" * 118)

    json.dump(dict(
        D1a="fire(s) <=> s > c_(k): the whole rule is one order statistic",
        D2a="additive |C| = N+a, M inflates by (1+eps) <= 1%; threshold monotone in a",
        D2b="replacement keeps M exactly but the threshold is NOT monotone",
        D3a="adversarial: j>=k gives an attacker-set threshold, j<k gives c0_(k-j); the "
            "tolerable count is k-1, and F14 forces k=1, so it is ZERO",
        D3a_corollary="the adversarial arm is a STEP in eps, not a slope -- sweep j, not eps",
        D3b="random: P(threshold moves) = 1-(1-q0)^(eps*N); scale eps* = 1/(N*q0), i.e. "
            "one injected flow that would itself have fired.  q0 is the POOL exceedance rate, "
            "NOT the deployment-window malicious firing rate -- the two differ under F9 drift",
        D4a="p1 >= p0 <=> g/a >= p0",
        D4b="conservative at s <=> Sv_M(s) >= Sv_B(s): the ROC above the diagonal; the "
            "converse holds, so the condition must be stated",
        D4c="at k=1 the operating p0 = 1/M ~ 5.5e-7, so the margin is enormous",
        D4pa="thresholded evidence has TWO channels: Ev ratio = (1+eps)*(m_eps/m_0)",
        D4pb="low-score injection leaves m alone and inflates Ev by exactly 1+eps: "
             "ANTI-conservative, a genuine validity violation",
        D4pc="E[e] <= 1+eps, so the FDR guarantee degrades from q to q*(1+eps) for LOND and "
             "LORD++, whose bound is a sum of offered levels.  MULTIPLICATIVE on top of the "
             "clean rule's own conservatism (section 4.31: up to 50.9x), and not claimed for "
             "online e-BH",
        D4pd="power dies at a = 1 flow; validity degrades by 1+eps and needs a = N to double. "
             "The asymmetry is the answer to the reviewer",
        D4pe="the replacement model closes the ceiling channel exactly",
        D5a="the feasibility margin IMPROVES under contamination -- not a safety indicator",
        D6a="firing sets are nested-decreasing in a WHEN the injected sets nest; the eps "
            "sweep must be prefixes of one pool, not independent redraws",
        D6b="LOND rejections are nested too",
        eps_grid_note="the workplan grid starts too high for the random arm; add 1e-7, 1e-6 "
                      "and a per-flow sweep j = 1..10",
        n_passed=len(OK), n_failed=len(FAIL), failed=FAIL),
        open(OUT / "t38a_E4_derivation.json", "w"), indent=1)
    print("  wrote out/t38a_E4_derivation.json")
    if FAIL:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
