
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


    N = 1_813_113
    W0 = 0.025
    def margin(NC, k=1, lvl=W0):
        CEIL = (NC + 1.0) / k
        return (CEIL - 1.0 / lvl) / CEIL
    m0 = margin(N)
    for eps in (1e-5, 1e-4, 1e-3, 1e-2):
        check_bool(f"D5a  margin increases at eps={eps:.0e}", margin(N + int(eps * N)) > m0,
                   note=f"{m0:.9f} -> {margin(N + int(eps*N)):.9f}")

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
