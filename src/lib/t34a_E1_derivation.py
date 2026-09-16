"""E1, part 1 -- the ANALYTIC derivation of both routes, verified numerically at small scale."""


def main():
    import numpy as np, json, time
    from math import lgamma, log, exp
    from pathlib import Path
    from scipy.stats import binom

    Path("out").mkdir(exist_ok=True)
    t0 = time.time()
    OK = []
    FAIL = []


    NOPOWER = []


    def check(name, got, want, tol, note=""):
        ok = abs(got - want) <= tol
        (OK if ok else FAIL).append(name)
        print(f"  [{'ok ' if ok else 'FAIL'}] {name:<58} got={got:<14.7g} want={want:<14.7g} "
              f"tol={tol:.3g} {note}")
        return ok


    def mc_check(name, got, want, n, z=5.0, note="", rel_tol=0.25):
        """Monte-Carlo check on a proportion, SIZED BEFORE IT IS BELIEVED (standing mistake"""
        if not (0.0 <= want <= 1.0):
            FAIL.append(name)
            print(f"  [FAIL] {name:<58} want={want!r} is not a probability {note}")
            return False
        tol = z * np.sqrt(want * (1.0 - want) / n)
        if want <= 0.0 or tol > rel_tol * want:
            NOPOWER.append(name)
            print(f"  [ -- ] {name:<58} got={got:<14.7g} want={want:<14.7g} "
                  f"NO POWER (5-sigma tol {tol:.3g} > {rel_tol:g}*want) {note}")
            return None
        return check(name + f"  [n={n:.0e}]", got, want, tol, note)


    def e_of_truncated(b, lam, tau, span=600.0, npts=2_000_001):
        """E[b*e*1{b*e >= tau}] for e = lam*p^(lam-1), p ~ U(0,1), by quadrature in"""
        p_b = (b * lam / tau) ** (1.0 / (1.0 - lam))
        if p_b <= 0.0: return 0.0
        if p_b >= 1.0: return float(b)
        x = np.linspace(-np.log(p_b), -np.log(p_b) + span, npts)
        return float(np.trapezoid(b * lam * np.exp(-lam * x), x))


    def e_of_calibrator(lam, span=600.0, npts=2_000_001):
        """E[lam*p^(lam-1)] for p ~ U(0,1), by the same substitution.  Monte Carlo cannot be"""
        x = np.linspace(0.0, span, npts)
        return float(np.trapezoid(lam * np.exp(-lam * x), x))


    print("=" * 100)
    print("D1  smoothed conformal p is exactly uniform, and p_d is the right endpoint of its support")
    print("=" * 100)

    rng = np.random.default_rng(20260826)

    NN, REP = 25, 400_000
    V = rng.standard_normal((REP, NN + 1))
    s = V[:, -1]; cal = V[:, :NN]
    G = (cal > s[:, None]).sum(1); Etie = (cal == s[:, None]).sum(1)
    U = rng.random(REP)
    p_u = (G + U * (1 + Etie)) / (NN + 1.0)
    p_d = (1 + G + Etie) / (NN + 1.0)
    for a in (0.05, 0.2, 0.5, 0.9):
        mc_check(f"D1a P(p_u<=a) == a  [continuous, a={a}]", float((p_u <= a).mean()), a, REP)
    check("D1b p_u <= p_d always [continuous]", float((p_u <= p_d).mean()), 1.0, 0.0)

    Vt = rng.integers(0, 4, size=(REP, NN + 1)).astype(float)
    st = Vt[:, -1]; calt = Vt[:, :NN]
    Gt = (calt > st[:, None]).sum(1); Et = (calt == st[:, None]).sum(1)
    Ut = rng.random(REP)
    p_ut = (Gt + Ut * (1 + Et)) / (NN + 1.0)
    p_dt = (1 + Gt + Et) / (NN + 1.0)
    for a in (0.05, 0.2, 0.5, 0.9):
        mc_check(f"D1a P(p_u<=a) == a  [4-point ties, a={a}]", float((p_ut <= a).mean()), a, REP)
    check("D1b p_u <= p_d always [ties]", float((p_ut <= p_dt).mean()), 1.0, 0.0)
    check("D1c P(p_d<=0.2) <= 0.2 [ties: conservative]",
          float(max(0.0, (p_dt <= 0.2).mean() - 0.2)), 0.0, 1e-9,
          f"realised {float((p_dt<=0.2).mean()):.4f}")

    Mtest = NN + 1.0
    check("D1c P(p_d <= a) == 0 for a < 1/M", float((p_dt <= (1.0 / Mtest) * 0.999).mean()),
          0.0, 0.0, f"1/M={1/Mtest:.4f}")
    mc_check("D1c P(p_u <= a) == a for the same a", float((p_ut <= (1.0 / Mtest) * 0.999).mean()),
             (1.0 / Mtest) * 0.999, REP)

    print()
    print("=" * 100)
    print("D2  Route A -- smoothed p straight into a p-value procedure")
    print("=" * 100)

    M_ = 1000.0
    for (Gv, Ev_, a) in ((0, 0, 5e-4), (0, 0, 2e-3), (3, 0, 5e-3), (2, 4, 4e-3), (7, 1, 2e-3)):
        n = 2_000_000
        Uv = rng.random(n)
        got = float(((Gv + Uv * (1 + Ev_)) / M_ <= a).mean())
        want = float(np.clip((a * M_ - Gv) / (1 + Ev_), 0, 1))
        mc_check(f"D2a P(reject|G={Gv},E={Ev_},a={a:g})", got, want, n)

    M_LSPR = 1_813_114.0
    for a in (1e-8, 1e-7, 5.516e-7, 1e-6):
        n = 4_000_000
        Uv = rng.random(n)
        got = float((Uv / M_LSPR <= a).mean())
        want = min(1.0, a * M_LSPR)
        mc_check(f"D2b P(reject) == min(1,a*(|C|+1)) at a={a:g}", got, want, n,
                 note=f"|C|+1={M_LSPR:.0f}")

    _r = np.random.default_rng(11)
    _n = 4_000_000
    _c = _r.standard_normal(_n)
    _s1 = _r.standard_normal(_n); _s2 = _r.standard_normal(_n)
    _p1 = ((_c > _s1) + _r.random(_n)) / 2.0
    _p2 = ((_c > _s2) + _r.random(_n)) / 2.0
    mc_check("D2c holds for a FIXED level a=0.1", float((_p2 <= 0.1).mean()), 0.1, _n)
    _a2 = np.where(_p1 <= 0.2, 0.5, 0.01)
    _Ea2 = 0.2 * 0.5 + 0.8 * 0.01
    _exact = 0.2 * (2.0 / 3.0) + 0.8 * ((0.5 - 0.2 * 2.0 / 3.0) / 0.8) * 0.02
    mc_check("D2c under an adaptive level: P(reject) matches the exact value, NOT E[alpha]",
             float((_p2 <= _a2).mean()), _exact, _n,
             note=f"E[alpha_2]={_Ea2:.4f}, exact P(reject_2)={_exact:.6f}")
    check("D2c adaptive rejection rate EXCEEDS E[alpha_2] (calibration-conditional failure)",
          float(_exact > _Ea2), 1.0, 0.0,
          f"{_exact:.4f} > {_Ea2:.4f}; ratio {_exact/_Ea2:.3f}x")
    del _c, _s1, _s2, _p1, _p2, _a2
    print(f"         lift of ceiling evidence over a null hypothesis = M = {M_LSPR:.0f}x")

    from scipy.special import zeta
    ZE = float(zeta(1.6, 1))
    ALPHA, W0 = 0.05, 0.025
    gam = lambda t: t ** -1.6 / ZE
    t_star = int(np.floor((ALPHA * M_LSPR / ZE) ** (1 / 1.6)))
    check("D2d hard horizon t* solves alpha*gamma_t*M == 1",
          ALPHA * gam(t_star) * M_LSPR, 1.0, 0.6,
          f"t*={t_star}, next step gives {ALPHA*gam(t_star+1)*M_LSPR:.3f}")
    tail = float(zeta(1.6, t_star + 1) / ZE)
    tail_trunc = float(np.sum([gam(t) for t in range(t_star + 1, 4_000_000)]))
    soft_yield = ALPHA * M_LSPR * tail
    check("D2d truncating the gamma tail at 4e6 is NOT adequate",
          float(ALPHA * M_LSPR * (tail - tail_trunc) > 1.0), 1.0, 0.0,
          f"exact {soft_yield:.1f} vs truncated {ALPHA*M_LSPR*tail_trunc:.1f}")
    print(f"         t* = {t_star}; sum_(t>t*) gamma_t = {tail:.5f} (exact, Hurwitz);\n"
          f"         alpha*M*tail = {soft_yield:.1f} expected rejections available beyond the "
          f"hard horizon\n"
          f"         AT R = 0, spread over ALL hypotheses there (attack and benign alike).\n"
          f"         This is the rejection-free bound only: once R > 0 the LOND level is\n"
          f"         alpha*gamma_t*(R+1) and the yield scales with it, so the real-data script\n"
          f"         measures the realised number rather than quoting this one.")

    print()
    print("=" * 100)
    print("D3  Route B -- smoothed p -> p-to-e calibrator -> e-value procedure")
    print("=" * 100)

    LAMS = [0.1, 0.25, 0.5, 0.75]
    for lam in LAMS:
        check(f"D3a E[lam p^(lam-1)] == 1  [lam={lam}]", e_of_calibrator(lam), 1.0, 1e-6,
              "quadrature in x=-log p; MC is invalid here, Var[e]=inf for lam<=0.5")

    check("D3b Vovk 0.5*p^-0.5 is the lam=0.5 member", 0.5 * (0.3 ** -0.5),
          0.5 * 0.3 ** (0.5 - 1.0), 0.0)
    check("D3c e = sqrt(M)/2 / sqrt(U) coefficient", np.sqrt(M_LSPR) / 2, 673.2, 0.15)
    u_need = (673.2 / (1.0 / 1.5873e-6)) ** 2
    check("D3c U threshold at 1/a = 6.3e5", u_need, 1.1e-6, 0.06e-6,
          "work plan quotes U <= 1.1e-6")

    for lam in LAMS:
        for a in (1e-8, 1e-7, 1e-6):
            n = 3_000_000
            Uv = rng.random(n)
            e = lam * (Uv / M_LSPR) ** (lam - 1.0)
            got = float((e >= 1.0 / a).mean())
            want = min(1.0, (a * lam) ** (1.0 / (1.0 - lam)) * M_LSPR)
            mc_check(f"D3e P(reject) closed form [lam={lam}, a={a:g}]", got, want, n)

    worst = 0.0
    for lam in np.linspace(0.01, 0.99, 99):
        for a in np.logspace(-9, -1, 33):
            worst = max(worst, (a * lam) ** (1.0 / (1.0 - lam)) - a)
    check("D3g p*(a,lam) <= a for all lam in (0,1), a<=0.1", worst, 0.0, 0.0,
          "max of p* - a over a 99x33 grid")

    print("\n  best calibrator exponent, and the residual gap to Route A:")
    print(f"    {'a':>10} {'lam*':>8} {'P_B(lam*)':>12} {'P_B(Vovk)':>12} {'P_A':>12} "
          f"{'P_A/P_B(lam*)':>14}")
    lamstar_rows = []
    for a in (1e-9, 1e-8, 1e-7, 1e-6):
        grid = np.linspace(1e-4, 1 - 1e-4, 200_000)
        lp = np.log(a * grid) / (1.0 - grid)
        j = int(np.argmax(lp)); lam_s = float(grid[j])
        PB = min(1.0, float(np.exp(lp[j])) * M_LSPR)
        PBv = min(1.0, (a * 0.5) ** 2 * M_LSPR)
        PA = min(1.0, a * M_LSPR)
        lamstar_rows.append(dict(a=a, lam_star=lam_s, P_B_best=PB, P_B_vovk=PBv, P_A=PA))
        print(f"    {a:>10.0e} {lam_s:>8.4f} {PB:>12.4g} {PBv:>12.4g} {PA:>12.4g} "
              f"{(PA/PB if PB > 0 else float('inf')):>14.4g}")
        foc = (1.0 - lam_s) / lam_s + np.log(a * lam_s)
        check(f"D3h first-order condition at a={a:g}", foc, 0.0, 2e-3, f"lam*={lam_s:.4f}")

    print()
    for lam in LAMS:
        for tau in (2.0, 5.0, 20.0, 100.0):
            bstar = (tau / lam) ** lam
            check(f"D3i E[T_b*(e)]==1 at b*=(tau/lam)^lam [lam={lam}, tau={tau:g}]",
                  e_of_truncated(bstar, lam, tau), 1.0, 1e-6, f"b*={bstar:.4f}")
            check(f"D3i E[T_b]>1 just above b* [lam={lam}, tau={tau:g}]",
                  float(e_of_truncated(bstar * 1.01, lam, tau) > 1.0), 1.0, 0.0,
                  f"E[T_1.01b*]={e_of_truncated(bstar*1.01, lam, tau):.4f}")
            check(f"D3i E[T_b]<1 just below b* [lam={lam}, tau={tau:g}]",
                  float(e_of_truncated(bstar * 0.99, lam, tau) < 1.0), 1.0, 0.0,
                  f"E[T_0.99b*]={e_of_truncated(bstar*0.99, lam, tau):.4f}")
    check("D3i b* == sqrt(2 tau) at lam=0.5, tau=20 (section 4.28 closed form)",
          (20.0 / 0.5) ** 0.5, np.sqrt(2 * 20.0), 1e-12)
    check("D3i b* == sqrt(2 tau) at lam=0.5, tau=100", (100.0 / 0.5) ** 0.5,
          np.sqrt(2 * 100.0), 1e-12)

    for lam in LAMS:
        for a in (1e-8, 1e-6):
            tau = 1.0 / a
            bstar = (tau / lam) ** lam
            n = 3_000_000
            Uv = rng.random(n)
            p = Uv / M_LSPR
            got = float((bstar * lam * p ** (lam - 1.0) >= tau).mean())
            want = min(1.0, lam * a * M_LSPR)
            mc_check(f"D3j boosted region is p <= lam*a [lam={lam}, a={a:g}]", got, want, n)

    for a in (1e-3, 1e-2):
        n = 4_000_000
        mc_hits = (rng.random(n) <= a)
        check(f"D3k optimal calibrator E[e]==1 under the null [a={a:g}, E[hits]={n*a:.0f}]",
              float(mc_hits.mean() / a), 1.0, 6.0 / np.sqrt(n * a))
    for a in (1e-8, 1e-6):
        n = 2_000_000
        Uv = rng.random(n)
        p = Uv / M_LSPR
        e_opt = np.where(p <= a, 1.0 / a, 0.0)
        mc_check(f"D3k optimal calibrator reproduces Route A [a={a:g}]",
                 float((e_opt >= 1.0 / a).mean()), min(1.0, a * M_LSPR), n)

    print()
    print("=" * 100)
    print("D4  episode level -- m flows under each merge")
    print("=" * 100)


    def irwin_hall_cdf(x, m):
        """P(sum of m iid U(0,1) <= x)."""
        if x <= 0: return 0.0
        if x >= m: return 1.0
        if x > m / 2.0:
            return max(0.0, min(1.0, 1.0 - irwin_hall_cdf(m - x, m)))
        import math as _m
        tot = _m.fsum(((-1) ** j) * _m.comb(m, j) * (x - j) ** m
                      for j in range(int(_m.floor(x)) + 1) if x > j)
        return max(0.0, min(1.0, tot / _m.factorial(m)))


    for m in (1, 2, 5, 20):
        for a in (1e-7, 1e-6):
            n = 2_000_000
            Uv = rng.random((n, m))
            p = Uv / M_LSPR
            got = float((np.minimum(1.0, m * p.min(1)) <= a).mean())
            want = 1.0 - (1.0 - min(1.0, a * M_LSPR / m)) ** m
            mc_check(f"D4a Bonferroni all-ceiling [m={m}, a={a:g}]", got, want, n)
            got2 = float((np.minimum(1.0, 2.0 * p.mean(1)) <= a).mean())
            want2 = irwin_hall_cdf(a * M_LSPR * m / 2.0, m)
            mc_check(f"D4c mean-p x2 all-ceiling [m={m}, a={a:g}]", got2, want2, n)
            del Uv, p

    for m in (2, 5, 20):
        a = 1e-6
        n = 2_000_000
        U1 = rng.random(n)
        got = float((np.minimum(1.0, m * (U1 / M_LSPR)) <= a).mean())
        mc_check(f"D4b Bonferroni one-of-m at ceiling [m={m}]", got,
                 min(1.0, a * M_LSPR / m), n)
        p_inert = np.ones(m - 1)
        val = 2.0 * (U1[0] / M_LSPR + p_inert.sum()) / m
        print(f"  [ok ] D4c mean-p x2 with one ceiling flow and {m-1} inert: P_ep = "
              f"{min(1.0, val):.4f} >> a, i.e. never rejects")

    print("\n  D4d Route B episode level, measured against m^(-lam/(1-lam)) * single:")
    for lam in (0.25, 0.5):
        for m in (1, 5, 20):
            a = 1e-6
            n = 3_000_000
            Uv = rng.random((n, m))
            e = lam * (Uv / M_LSPR) ** (lam - 1.0)
            got = float((e.mean(1) >= 1.0 / a).mean())
            single = (a * lam) ** (1.0 / (1.0 - lam)) * M_LSPR
            approx = m ** (-lam / (1.0 - lam)) * single
            rel = got / approx if approx > 0 else np.nan
            print(f"    lam={lam} m={m:>3}  measured={got:.5g}  one-big-jump={approx:.5g}  "
                  f"ratio={rel:.3f}")
            if m == 1:
                mc_check(f"D4d m=1 reduces to D3e [lam={lam}]", got, min(1.0, single), n)
            del Uv, e

    print()
    print("=" * 100)
    print("D3/D4 boundary checks -- EXACT, for the cells where Monte Carlo has no power")
    print("=" * 100)
    EPS = 1e-9
    for lam in LAMS:
        for a in (1e-8, 1e-7, 1e-6):
            u_thr = (a * lam) ** (1.0 / (1.0 - lam)) * M_LSPR
            if not (0 < u_thr < 1):
                continue
            lo = u_thr * (1 - EPS); hi = u_thr * (1 + EPS)
            e_lo = lam * (lo / M_LSPR) ** (lam - 1.0)
            e_hi = lam * (hi / M_LSPR) ** (lam - 1.0)
            check(f"D3e boundary flips at U=(a*lam)^(1/(1-lam))*M [lam={lam}, a={a:g}]",
                  float((e_lo >= 1.0 / a) and (e_hi < 1.0 / a)), 1.0, 0.0,
                  f"U*={u_thr:.6g}, e(U*-)={e_lo:.6g}, e(U*+)={e_hi:.6g}, 1/a={1/a:.6g}")
    for (Gv, Ev_, a) in ((0, 0, 5e-4), (3, 0, 5e-3), (2, 4, 4e-3), (7, 1, 2e-3)):
        u_thr = (a * M_ - Gv) / (1.0 + Ev_)
        if not (0 < u_thr < 1):
            continue
        lo = u_thr * (1 - EPS); hi = u_thr * (1 + EPS)
        check(f"D2a boundary flips [G={Gv},E={Ev_},a={a:g}]",
              float(((Gv + lo * (1 + Ev_)) / M_ <= a) and ((Gv + hi * (1 + Ev_)) / M_ > a)),
              1.0, 0.0, f"U*={u_thr:.6g}")
    from numpy.polynomial import polynomial as _P
    def ih_exact_grid(m, xs):
        """P(sum of m U(0,1) <= x) by direct m-fold numerical convolution on a fine grid."""
        h = 1e-4; n1 = int(round(1.0 / h))
        dens = np.full(n1, h)
        cur = dens.copy()
        for _ in range(m - 1):
            cur = np.convolve(cur, dens)
        cdf = np.concatenate([[0.0], np.cumsum(cur)])
        grid = np.arange(len(cdf)) * h
        return np.interp(xs, grid, cdf)
    for m in (2, 5):
        xs = np.array([0.3, 1.0, 2.0])
        got = ih_exact_grid(m, xs); want = np.array([irwin_hall_cdf(float(x), m) for x in xs])
        check(f"D4c Irwin-Hall closed form vs {m}-fold convolution",
              float(np.max(np.abs(got - want))), 0.0, 2e-3,
              f"at x={list(xs)}: {np.round(want,6).tolist()}")
    for m in (5, 20):
        x = 0.4
        check(f"D4c small-x form x^m/m! [m={m}]", irwin_hall_cdf(x, m),
              x ** m / np.exp(lgamma(m + 1)), 1e-12 * max(1.0, x ** m / np.exp(lgamma(m + 1))))
    def ibj_importance(lam, m, a, n=4_000_000, kk=40, seed=7):
        r = np.random.default_rng(seed)
        U = r.random((n, m))
        j = r.integers(0, m, size=n)
        V = r.random(n)
        U[np.arange(n), j] = V ** kk
        g = (1.0 / kk) * U ** (1.0 / kk - 1.0)
        dens = g.mean(1)
        w = 1.0 / dens
        e = lam * (U / M_LSPR) ** (lam - 1.0)
        hit = e.mean(1) >= 1.0 / a
        est = float((w * hit).mean())
        se = float(np.std(w * hit) / np.sqrt(n))
        return est, se, int(hit.sum())

    print("\n  D4d one-big-jump, checked IN its asymptotic regime by importance sampling:")
    for lam in (0.25, 0.5):
        for m in (2, 5, 20):
            a = 1e-6
            est, se, nh = ibj_importance(lam, m, a)
            single = (a * lam) ** (1.0 / (1.0 - lam)) * M_LSPR
            approx = m ** (-lam / (1.0 - lam)) * single
            print(f"    lam={lam} m={m:>3} a={a:g}  IS estimate={est:.5g} (+-{se:.2g}, "
                  f"{nh} tilted hits)  one-big-jump={approx:.5g}  ratio={est/approx:.3f}")
            check(f"D4d one-big-jump within 2x [lam={lam}, m={m}]",
                  float(0.5 <= est / approx <= 2.0), 1.0, 0.0,
                  "asymptotic form, not an identity")

    print()
    print("=" * 100)
    print("D5  stability reference values")
    print("=" * 100)
    for label, q in (("deterministic (q in {0,1})", np.array([1.0] * 50 + [0.0] * 950)),
                     ("uniform q=0.5", np.full(1000, 0.5)),
                     ("uniform q=0.02", np.full(1000, 0.02))):
        ER = q.sum(); VR = (q * (1 - q)).sum()
        J = (q ** 2).sum() / (2 * q - q ** 2).sum()
        n = 40_000
        A = rng.random((n, len(q))) < q
        B = rng.random((n, len(q))) < q
        inter = (A & B).sum(1); union = (A | B).sum(1)
        Jmc = float(inter.sum() / union.sum())
        check(f"D5c Jaccard ratio-of-expectations [{label}]", Jmc, J,
              max(5 * float(np.std(inter) / union.mean()) / np.sqrt(n), 2e-3))
        check(f"D5b Var(R) [{label}]", float(A.sum(1).var()), VR,
              6 * VR * np.sqrt(2.0 / n))
        del A, B

    print()
    print("=" * 100)
    print(f"D1-D5:  {len(OK)} checks passed, {len(FAIL)} failed, "
          f"{len(NOPOWER)} skipped for lack of power   [{time.time()-t0:.0f}s]")
    if FAIL:
        print("  FAILED: " + ", ".join(FAIL))
    if NOPOWER:
        print("  NO POWER (closed form not exercised by Monte Carlo at this n; the cells that")
        print("  DO have power cover the same closed form at larger a):")
        for nm in NOPOWER: print(f"    - {nm}")
    print("=" * 100)

    pred = {
        "M_reference": M_LSPR,
        "alpha": ALPHA, "w0": W0, "zeta_1_6": ZE,
        "D2b": "P(reject | ceiling evidence) = min(1, alpha_t * (|C|+1))",
        "D2c": "P(reject | null) = alpha_t exactly; lift = |C|+1",
        "D2d_hard_horizon_t_star_LOND_R0": t_star,
        "D2d_soft_yield_beyond_t_star": soft_yield,
        "D3e": "P(reject | ceiling) = min(1, (alpha_t*lam)^(1/(1-lam)) * (|C|+1))",
        "D3g": "Route B rejection region is a strict subset of Route A's at the same level",
        "D3i_boost": "b* = (tau/lam)^lam; = sqrt(2 tau) at lam=1/2, matching section 4.28",
        "D3j": "boosted Route B rejection region is p <= lam*alpha_t",
        "D3k": "the optimal p-to-e calibrator at tau=1/alpha_t IS the threshold e-value",
        "D4a": "Bonferroni all-ceiling: 1-(1-min(1,aM/m))^m",
        "D4b": "Bonferroni one-of-m at ceiling: min(1, aM/m)",
        "D4c": "mean-p x2 all-ceiling: IrwinHall_m(aMm/2); ~ (aMm/2)^m/m!",
        "D4d": "Route B episode: ~ m^(-lam/(1-lam)) * single-hypothesis value",
        "D5b": "Var(R) = sum q(1-q)", "D5c": "J ~= sum q^2 / sum (2q - q^2)",
        "lam_star": lamstar_rows,
        "n_checks_passed": len(OK), "n_checks_failed": len(FAIL), "failed": FAIL,
        "n_checks_no_power": len(NOPOWER), "no_power": NOPOWER,
    }
    json.dump(pred, open("out/t34a_E1_derivation.json", "w"), indent=1)
    print(f"  wrote out/t34a_E1_derivation.json")
    if FAIL:
        raise SystemExit(1)

    return pred


if __name__ == "__main__":
    main()
