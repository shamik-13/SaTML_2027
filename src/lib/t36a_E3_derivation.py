"""E3, part 1 -- the ANALYTIC derivation of deterministic precommitted weighting under"""


def main():
    import numpy as np, json, time
    from pathlib import Path

    Path("out").mkdir(exist_ok=True)
    t0 = time.time()
    OK, FAIL, NOPOWER = [], [], []


    def check(name, got, want, tol, note=""):
        ok = abs(got - want) <= tol
        (OK if ok else FAIL).append(name)
        print(f"  [{'ok ' if ok else 'FAIL'}] {name:<64} got={got:<14.7g} want={want:<14.7g} "
              f"tol={tol:.3g} {note}")
        return ok


    def weights(scheme, N, **kw):
        """A precommitted weight sequence of length N, non-negative and summing to <= 1."""
        w = np.zeros(N, dtype=float)
        if scheme == "first-only":
            w[0] = 1.0
        elif scheme == "uniform-m0":
            m0 = min(int(kw["m0"]), N)
            w[:m0] = 1.0 / kw["m0"]
        elif scheme == "exp-decay":
            rho = float(kw["rho"])
            w[:] = (1.0 - rho) * rho ** np.arange(N, dtype=float)
        elif scheme == "two-block":
            a, K = float(kw["a"]), min(int(kw["K"]), N)
            w[0] = a
            if K > 1:
                w[1:K] = (1.0 - a) / (K - 1)
        else:
            raise ValueError(scheme)
        return w


    def frontload_cost(w, beta):
        """L*(w, beta) = min{L >= 0 : sum_{i>L} w_i < beta}   [D3a].  Returns len(w) if the tail"""
        w = np.asarray(w, dtype=float)
        if beta <= 0:
            raise ValueError("beta must be positive")
        if np.any(w < 0):
            raise ValueError("weights must be non-negative")
        tail = np.concatenate([np.cumsum(w[::-1])[::-1], [0.0]])
        idx = np.flatnonzero(tail < beta)
        return int(idx[0]) if idx.size else len(w)


    def detectable_positions(w, beta):
        """P = #{i : w_i >= beta}   [D2b]."""
        return int((w >= beta).sum())


    print("=" * 118)
    print("D1  validity under arbitrary dependence, and padding-invariance")
    print("=" * 118)
    rng = np.random.default_rng(20260826)
    M = 2_448_994.0
    for scheme, kw in (("first-only", {}), ("uniform-m0", dict(m0=50)),
                       ("exp-decay", dict(rho=0.9)), ("two-block", dict(a=0.5, K=100))):
        w = weights(scheme, 5000, **kw)
        check(f"D1a sum of weights <= 1 [{scheme}]", float(w.sum() <= 1.0 + 1e-12), 1.0, 0.0,
              f"sum={w.sum():.12f}")
        check(f"D1a weights are non-negative [{scheme}]", float((w >= 0).all()), 1.0, 0.0)
        n = 400_000
        pos = rng.integers(0, 200, n)
        e = np.zeros((n, 200)); e[np.arange(n), pos] = 200.0
        F = e @ w[:200]
        se = float(F.std()) / np.sqrt(n)
        check(f"D1a E[F] <= 1 under maximally adverse dependence [{scheme}]",
              float(F.mean()), min(1.0, float(w[:200].sum())), max(6 * se, 1e-3),
              f"E[F]={F.mean():.4f}, sum w[:200]={w[:200].sum():.4f}")
        del e, F
        x = np.zeros(200); x[[3, 17, 88]] = M
        base = float(x @ w[:200])
        for r in (10, 1000, 100_000):
            xr = np.concatenate([x, np.zeros(r)])
            wr = weights(scheme, 200 + r, **kw)
            check(f"D1b padding-invariant at r={r} [{scheme}]", float(xr @ wr), base,
                  1e-9 * max(1.0, base))

    _n = 400_000
    _pos = rng.integers(0, 200, _n)
    _e = np.zeros((_n, 200)); _e[np.arange(_n), _pos] = 200.0
    for excess in (1.01, 1.5, 3.0):
        w_bad = np.full(200, excess / 200)
        _F = _e @ w_bad
        _se = float(_F.std()) / np.sqrt(_n)
        check(f"D1a converse: sum w = {excess} gives E[F] = {excess} > 1, i.e. NOT valid",
              float(_F.mean()), excess, max(6 * _se, 1e-3))
    del _e, _F

    x = np.zeros(200); x[[3, 17, 199]] = M
    w_last = np.zeros(200); w_last[-1] = 1.0
    base_last = float(x @ w_last)
    xr = np.concatenate([x, np.zeros(1)])
    w_last_r = np.zeros(201); w_last_r[-1] = 1.0
    check("D1c last-event-only is NOT padding-invariant: ONE appended zero destroys it",
          float(xr @ w_last_r), 0.0, 0.0, f"{base_last:.0f} -> 0 after a single pad")

    print()
    print("=" * 118)
    print("D2  the power leg: how many positions can ever carry a detection")
    print("=" * 118)
    for alpha_t in (1e-2, 1e-4, 1e-6, 1e-7):
        beta = 1.0 / (alpha_t * M)
        for scheme, kw in (("first-only", {}), ("uniform-m0", dict(m0=10)),
                           ("uniform-m0", dict(m0=1000)), ("exp-decay", dict(rho=0.99))):
            w = weights(scheme, 200_000, **kw)
            P = detectable_positions(w, beta)
            check(f"D2b P <= alpha_t*M [{scheme}{kw}, a_t={alpha_t:g}]",
                  float(P <= alpha_t * M + 1e-9), 1.0, 0.0,
                  f"P={P}, alpha_t*M={alpha_t*M:.4g}")
            del w
    for beta_t in (0.2, 0.1, 1.0 / 7):
        npos = int(np.floor(1.0 / beta_t))
        w = np.zeros(4 * npos); w[::4][:npos] = beta_t
        check(f"D2b is tight and needs no monotonicity [beta={beta_t:.4g}]",
              float(detectable_positions(w, beta_t)), float(npos), 0.0,
              f"P={detectable_positions(w, beta_t)} = floor(1/beta) = {npos}")
        del w
    w = np.array([0.2, 0.2, 0.19999999])
    check("D2b counts w_i == beta as detectable (>=, not >)",
          float(detectable_positions(w, 0.2)), 2.0, 0.0)
    del w

    for _ in range(200):
        m = int(rng.integers(1, 60))
        w = rng.random(m); w /= w.sum()
        S = rng.random(m) < 0.3
        e = np.where(S, M, 0.0)
        alpha_t = float(10 ** rng.uniform(-7, -2))
        beta = 1.0 / (alpha_t * M)
        lhs = float(w @ e) >= 1.0 / alpha_t
        rhs = float(w[S].sum()) >= beta - 1e-15
        if lhs != rhs:
            FAIL.append("D2a rejection rule"); break
    else:
        OK.append("D2a rejection rule")
        print("  [ok ] D2a  F >= 1/alpha_t  <=>  sum_{i in S} w_i >= beta"
              "                        200 random (m, w, S, alpha_t)")

    print()
    print("=" * 118)
    print("D3  the ordering leg: the front-load cost is a finite tail sum")
    print("=" * 118)
    NBIG = 2_000_000
    for alpha_t in (1e-4, 1e-6):
        beta = 1.0 / (alpha_t * M)
        w = weights("first-only", NBIG)
        check(f"D3d first-event-only L* = 1 [a_t={alpha_t:g}]",
              float(frontload_cost(w, beta)), 1.0, 0.0)
        del w
        for m0 in (10, 100, 5000):
            w = weights("uniform-m0", NBIG, m0=m0)
            want = float(np.floor(m0 * (1.0 - beta)) + 1)
            check(f"D3e uniform-m0 L* = floor(m0(1-beta))+1 [m0={m0}, a_t={alpha_t:g}]",
                  float(frontload_cost(w, beta)), want, 0.0)
            del w
        for rho in (0.5, 0.9, 0.999):
            w = weights("exp-decay", NBIG, rho=rho)
            want = float(np.floor(np.log(beta) / np.log(rho)) + 1)
            got = float(frontload_cost(w, beta))
            check(f"D3f exp-decay L* = floor(log beta/log rho)+1 [rho={rho}, a_t={alpha_t:g}]",
                  got, want, 0.0, f"L*={got:.0f}")
            del w
    for p in (1.05, 1.5, 2.0):
        w = (np.arange(1, NBIG + 1, dtype=float) ** -p)
        w /= w.sum()
        beta = 1.0 / (1e-6 * M)
        L = frontload_cost(w, beta)
        check(f"D3b L* finite for w_i ~ i^-{p} (a heavy but summable tail)",
              float(L < NBIG), 1.0, 0.0, f"L*={L:,}")
        del w

    print()
    print("=" * 118)
    print("D4  the triangle closes: P <= alpha_t*M, and for non-increasing w, L* >= P")
    print("=" * 118)
    print(f"  {'alpha_t':>10} {'alpha_t*M':>12} {'scheme':>24} {'P (detectable)':>15} "
          f"{'L* (front-load)':>16} {'single-flow power':>18}")
    rows_tri = []
    for alpha_t in (1e-2, 1e-3, 1e-4, 1e-5, 1e-6):
        beta = 1.0 / (alpha_t * M)
        for scheme, kw in (("first-only", {}), ("uniform-m0", dict(m0=10)),
                           ("uniform-m0", dict(m0=1000)), ("exp-decay", dict(rho=0.99)),
                           ("two-block", dict(a=0.5, K=1000))):
            w = weights(scheme, 200_000, **kw)
            P = detectable_positions(w, beta)
            L = frontload_cost(w, beta)
            pw = float(w[0])
            rows_tri.append(dict(alpha_t=alpha_t, scheme=f"{scheme}{kw}", P=P, L=L, w1=pw))
            print(f"  {alpha_t:>10.0e} {alpha_t*M:>12.4g} {scheme+str(kw):>24} {P:>15} "
                  f"{L:>16,} {pw:>18.6f}")
            if P > 0 and bool(np.all(np.diff(w) <= 1e-18)):
                check(f"D4a L* >= P for non-increasing w [{scheme}{kw}, a_t={alpha_t:g}]",
                      float(L >= P), 1.0, 0.0, f"L*={L}, P={P}")
                check(f"D2b P <= alpha_t*M [{scheme}{kw}, a_t={alpha_t:g}]",
                      float(P <= alpha_t * M + 1e-9), 1.0, 0.0,
                      f"P={P}, alpha_t*M={alpha_t*M:.4g}")
            del w
    check("D4c first-event-only maximises power and minimises L*",
          float(weights("first-only", 100)[0]), 1.0, 0.0, "w_1 = 1, L* = 1")
    wthin = (np.arange(1, 2_000_001, dtype=float) ** -1.05); wthin /= wthin.sum()
    wfirst = weights("first-only", 2_000_000)
    print("\n  the two extremes of the (power, ordering-cost) tradeoff:")
    print(f"    {'alpha_t':>9} {'alpha_t*M':>11} {'scheme':>12} {'w_1':>12} {'P':>8} {'L*':>12}")
    for a_t in (1e-6, 1e-4, 1e-2):
        b = 1.0 / (a_t * M)
        Lt, Pt = frontload_cost(wthin, b), detectable_positions(wthin, b)
        Lf, Pf = frontload_cost(wfirst, b), detectable_positions(wfirst, b)
        for nm, w1, P_, L_ in (("first-only", wfirst[0], Pf, Lf), ("i^-1.05", wthin[0], Pt, Lt)):
            print(f"    {a_t:>9.0e} {a_t*M:>11.4g} {nm:>12} {w1:>12.6f} {P_:>8} {L_:>12,}")
        check(f"D4c a thin tail raises L* by orders of magnitude [alpha_t={a_t:g}]",
              float(Lt > 100 * max(Lf, 1)), 1.0, 0.0, f"L* {Lf} -> {Lt:,}")
        check(f"D4c ...and pays for it in per-position weight [alpha_t={a_t:g}]",
              float(wthin[0] < 0.2 * wfirst[0]), 1.0, 0.0,
              f"w_1 {wfirst[0]:.4f} -> {wthin[0]:.6f}, a {wfirst[0]/wthin[0]:.1f}x reduction")
        check(f"D2b holds for the thin tail too [alpha_t={a_t:g}]",
              float(Pt <= a_t * M + 1e-9), 1.0, 0.0, f"P={Pt}, alpha_t*M={a_t*M:.4g}")
    del wthin, wfirst
    w = weights("uniform-m0", 100_000, m0=1000)
    check("D4c uniform-m0 maximises L* and destroys single-flow power",
          float(w[0]), 1e-3, 1e-12, "w_1 = 1/m0")
    del w

    print()
    print("=" * 118)
    print(f"D1-D4:  {len(OK)} checks passed, {len(FAIL)} failed   [{time.time()-t0:.0f}s]")
    if FAIL:
        print("  FAILED: " + ", ".join(FAIL))
    print("=" * 118)

    json.dump(dict(M=M,
                   D1a="F = sum w_i e_i is valid under ARBITRARY dependence iff sum w <= 1",
                   D1b="padding-invariant because absolute positions 1..m are untouched",
                   D1c="last-event-only is NOT padding-invariant: one appended zero kills it",
                   D2a="reject <=> sum_{i in S} w_i >= beta, beta = 1/(alpha_t*M)",
                   D2b="P = #{i : w_i >= beta} <= 1/beta = alpha_t*M",
                   D3a="L*(w,beta) = min{L : sum_{i>L} w_i < beta}",
                   D3b="L* is FINITE for every summable w -- no scheme escapes",
                   D3c="same tail-sum argument as section 4.13 Prop 2, on the position axis",
                   D3d_first_only=1,
                   D3e="uniform-m0: L* = max(0, floor(m0*(1-beta)) + 1) for beta > 0",
                   D3f="exp-decay: L* = max(0, floor(log(beta)/log(rho)) + 1) for beta > 0",
                   D4a="L* >= P for non-increasing w (NOT <=: the tail beyond P still carries"
                       " mass the attacker must clear)",
                   D4c="the triangle: padding-invariance + power + ordering-resistance cannot"
                       " all hold",
                   triangle=rows_tri,
                   n_passed=len(OK), n_failed=len(FAIL), failed=FAIL),
              open("out/t36a_E3_derivation.json", "w"), indent=1)
    print("  wrote out/t36a_E3_derivation.json")
    if FAIL:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
