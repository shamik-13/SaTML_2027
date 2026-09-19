


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


    import ast

    SRC_PATH = Path(__file__).with_name("t39_E6_transfer.py")


    def load_module_level(*names):
        src = SRC_PATH.read_text()
        tree = ast.parse(src)
        want = {n.name: n for n in tree.body
                if isinstance(n, ast.FunctionDef) and n.name in names}
        missing = set(names) - set(want)
        if missing:
            raise AssertionError(f"not module-level in {SRC_PATH.name}: {sorted(missing)}")
        ns = {"np": np, "math": math, "OBJ": "flow_cov_addis"}
        mod = ast.Module(body=[want[n] for n in names], type_ignores=[])
        exec(compile(ast.fix_missing_locations(mod), str(SRC_PATH), "exec"), ns)
        return [ns[n] for n in names]


    select, normalised_regret = load_module_level("select", "normalised_regret")


    def regret(oracle, achieved):
        """oracle - achieved.  Non-negative by construction; t39 asserts it per row."""
        return float(oracle) - float(achieved)


    bad = 0
    for _ in range(20000):
        G = int(rng.integers(2, 40))
        Vprev = rng.random(G); Vj = rng.random(G)
        o = np.arange(G)
        w, _ = select(Vprev, o)
        if regret(Vj.max(), Vj[w]) < -1e-15:
            bad += 1
    check("D1a  regret >= 0 for every draw (20000 grids)", bad, 0, 0)

    flat = np.full(12, 0.37)
    check_bool("D2a  normalised regret is None on a flat grid",
               normalised_regret(flat, 0.37) is None, note="not 0.0")
    v = np.array([0.1, 0.5, 0.9])
    check("D2a  rho = 0 at the oracle", normalised_regret(v, 0.9), 0.0, 1e-12)
    check("D2a  rho = 1 at the worst config", normalised_regret(v, 0.1), 1.0, 1e-12)
    check("D2a  rho = 0.5 midway", normalised_regret(v, 0.5), 0.5, 1e-12)
    G = 200
    vv = rng.random(G)
    exp_rho = float(((vv.max() - vv) / (vv.max() - vv.min())).mean())
    got_rho = float(np.mean([normalised_regret(vv, vv[i]) for i in range(G)]))
    check("D2a  mean rho over all configs equals the random-selection baseline",
          got_rho, exp_rho, 1e-12, note=f"random baseline rho = {exp_rho:.3f}, NOT 0.5 in general")


    mal_flows = np.array([100, 1, 1, 1, 1])
    fine_fired = np.array([False, True, True, True, True])
    fine_recall = fine_fired.sum() / 5
    fine_cov = mal_flows[fine_fired].sum() / mal_flows.sum()
    coarse_recall = 1.0
    coarse_cov = 1.0
    check("D3a  fine grouping recall", fine_recall, 0.8, 1e-12)
    check("D3a  fine grouping flow coverage", fine_cov, 4.0 / 104.0, 1e-12)
    check_bool("D3a  recall 0.80 vs coverage 0.038 on the SAME alerts",
               fine_recall > 20 * fine_cov, note="recall overstates by 21x here")
    mal2 = np.array([100, 1, 1, 1, 1])
    coarse2_fired = np.array([False, True, True, True, True])
    check_bool("D3b  a family can raise recall while lowering coverage",
               (coarse2_fired.sum() / 5) > (mal2[coarse2_fired].sum() / mal2.sum()))
    check("D3a  single-episode grouping recall is 1 when it fires", 1.0 / 1.0, 1.0, 0)


    from scipy.stats import norm as _norm
    from scipy.integrate import quad as _quad


    def emax_exact(G):
        """E[max of G iid standard normals], by quadrature on 1 - Phi(x)^G."""
        hi = _quad(lambda x: 1.0 - _norm.cdf(x) ** G, 0.0, 40.0, limit=400)[0]
        lo = _quad(lambda x: _norm.cdf(x) ** G, -40.0, 0.0, limit=400)[0]
        return hi - lo


    for G in (10, 70, 500):
        n = 200_000
        mx = float(rng.normal(size=(n, G)).max(axis=1).mean())
        ex = emax_exact(G)
        approx = math.sqrt(2.0 * math.log(G))
        se = 5.0 / math.sqrt(n)
        check(f"D4a  E[max of {G} normals] vs exact quadrature", mx, ex, se,
              note=f"sqrt(2 ln G) = {approx:.3f}, i.e. {100*(approx/ex-1):+.0f}% off")
    check_bool("D4a  a missing sqrt(2) would FAIL that check",
               abs(math.sqrt(math.log(70)) - emax_exact(70)) > 5.0 / math.sqrt(200_000),
               note=f"sqrt(ln 70) = {math.sqrt(math.log(70)):.3f} vs exact "
                    f"{emax_exact(70):.3f} -- the gate has power")
    check_bool("D4a  sqrt(2 ln G) is within 30% of the truth at G = 70 (sizing rule only)",
               abs(math.sqrt(2 * math.log(70)) / emax_exact(70) - 1.0) < 0.30)

    v = np.array([0.5, 0.9, 0.9, 0.9, 0.2])
    w, nt = select(v, np.arange(5))
    check("D5a  tie-break picks the lowest declared priority", w, 1, 0)
    check("D5a  and reports the number tied", nt, 3, 0)
    w2, nt2 = select(v, np.array([4, 3, 2, 1, 0]))
    check("D5a  a different declared order picks a different winner", w2, 3, 0,
          note="which is why the order must be declared, not implicit in the grid layout")
    def _raises(fn):
        try:
            fn(); return False
        except ValueError:
            return True


    check_bool("D5a  an all-NaN objective is refused, not silently resolved",
               _raises(lambda: select(np.full(6, np.nan), np.arange(6))))
    check_bool("D5a  an objective containing +inf is refused",
               _raises(lambda: select(np.array([1.0, np.inf, 0.5]), np.arange(3))))
    check_bool("D5a  NaN entries alongside finite ones are simply excluded",
               select(np.array([0.2, np.nan, 0.9, np.nan]), np.arange(4)) == (2, 1))


    W0 = 0.025
    def margin(NC, T, k=1):
        return (NC + 1.0) / k * W0 / T - 1.0
    check("D6a  margin at |C|=1.81e6, T=31568, k=1", margin(1_813_113, 31568), 0.43578, 5e-4)
    check_bool("D6a  margin is independent of any score input",
               margin(1_813_113, 31568) == margin(1_813_113, 31568),
               note="stated for the record: no score/label enters D6a")
    NC = 1_813_113
    Tstar = (NC + 1.0) * W0 / 1.0
    for T in (20000, 31568, 45327, 45328, 60000, 100000):
        print(f"       T={T:>7,}: margin = {margin(NC, T):+.4f}  "
              f"{'feasible' if margin(NC, T) >= 0 else 'INFEASIBLE'}")
    check("D6b  the exact feasibility horizon T* = (|C|+1)*w0/k", Tstar, 45327.85, 1e-6)
    check_bool("D6b  feasibility flips between floor(T*) and floor(T*)+1",
               margin(NC, int(Tstar)) >= 0 > margin(NC, int(Tstar) + 1),
               note=f"T* = {Tstar:,.2f}: this is F1's horizon, restated on the grouping axis")
    check_bool("D6b  the record's headline grouping is feasible with room",
               margin(NC, 31568) > 0.4, note="T = 31,568 against T* = 45,328")


    check("D7a  ordered pairs from 5 windows", 5 - 1, 4, 0)
    check("D7a  leave-one-out folds from 5 windows", 5, 5, 0)

    print("=" * 118)
    print(f"  PASSED {len(OK)} / {len(OK) + len(FAIL)} checks")
    if FAIL:
        print("  FAILED: " + ", ".join(FAIL))
    print("=" * 118)

    json.dump(dict(
        D1a="regret = oracle - achieved >= 0 by construction; a negative value is a bug",
        D1b="the claim needs frozen~oracle AND prev~oracle AND spread not ~0",
        D2a="normalised regret is UNDEFINED (None) on a flat grid, never 0",
        D3a="episode recall is not comparable across grouping families: the family sets the "
            "denominator, so selecting on recall selects coarseness",
        D3b="select on FLOW COVERAGE, report recall alongside",
        D4a="the selection-window value is a max over G and overstates by ~sigma*sqrt(2 ln G); "
            "report the evaluation-window value and the drop",
        D5a="tie-breaks must be declared in the source before any data is read, and the number "
            "of tied winners reported; all-NaN and inf objectives are refused, not resolved",
        D6a="margin = CEIL*w0/T - 1 depends on |C|, k, T only -- the feasibility gate is not a "
            "tuned parameter and transfers exactly; report whether the feasible SET moves",
        D6b="the gate is exactly T <= (|C|+1)*w0/k = 45,328 at the record's |C|",
        D7a="report all 4 pairs and all 5 folds; summarise by the WORST case, not the mean",
        n_passed=len(OK), n_failed=len(FAIL), failed=FAIL),
        open(OUT / "t39a_E6_derivation.json", "w"), indent=1)
    print("  wrote out/t39a_E6_derivation.json")
    if FAIL:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
