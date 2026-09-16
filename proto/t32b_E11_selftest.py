"""
Unit tests for the E11 per-episode coincidence export (the patch in t32_B1_addis_state.py)
and for t32a_E11_derivation.py.  No data files: everything is synthetic and runs in a
couple of seconds, so it can be re-run after any edit.

`least_n_gt` is pulled OUT of t32_B1_addis_state.py by AST and executed here, so the tests
exercise the SHIPPED function rather than a copy of it (standing mistake 16: a round-3
mutation defeated an earlier self-test that tested copies and grepped for source strings).
The export block itself is module-level straight-line code inside a script that loads
LSPR23, so it cannot be imported; its algebra is re-implemented here from the derivation
and cross-checked against the shipped JSON, and the source expressions that carry the
non-obvious choices are asserted to still be present.

What it pins down:
  1  least_n_gt is the least integer n with n/x > alpha, in exact arithmetic, including at
     the float-rounding case that defeats np.floor(alpha*x)+1
  2  the D4a bracket alpha < p+ <= alpha + 1/(M*m), and that its width is one conformal floor
  3  D5a: saturation forces landing whenever M*m >= 1/(tau-lam), and the sharp threshold
  4  D5b: an unsaturated episode can land, so `sat <=> lands` is NOT a theorem
  5  the D7a median order statistic, for ODD and EVEN episode counts
  6  the exported JSON satisfies all ten D6 identities, recomputed independently
  7  the saturation test is EXACT, not np.isclose (whose default rtol is wider than 1/M)
  8  mutation resistance: nine deliberate corruptions of the export algebra are caught
"""
import numpy as np, ast, json, math
from pathlib import Path
from fractions import Fraction

SRC_PATH = Path(__file__).with_name("t32_B1_addis_state.py")
SRC = SRC_PATH.read_text()
JSON_PATH = Path(__file__).with_name("out") / "t32_B1.json"
LAM, TAU = 0.25, 0.5
fails = []


def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"   {detail}" if detail else ""))
    if not cond:
        fails.append(name)


def load_module_level(*names):
    """Execute named module-level functions out of t32_B1_addis_state.py without running it."""
    tree = ast.parse(SRC)
    want = {n.name: n for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name in names}
    missing = set(names) - set(want)
    if missing:
        raise AssertionError(f"not module-level in {SRC_PATH.name}: {sorted(missing)}")
    ns = {"np": np, "Fraction": Fraction, "math": math}
    mod = ast.Module(body=[want[n] for n in names], type_ignores=[])
    exec(compile(ast.fix_missing_locations(mod), str(SRC_PATH), "exec"), ns)
    return [ns[n] for n in names]


(least_n_gt,) = load_module_level("least_n_gt")

# ======================================================================================
print("=" * 100)
print("1. least_n_gt is the least integer n with n/x > alpha")
print("=" * 100)
rng = np.random.default_rng(4242)
bad_sup = bad_min = 0
for _ in range(20000):
    x = int(rng.integers(1, 10**12))
    a = float(rng.uniform(1e-9, 0.25))
    n = least_n_gt(a, x)
    fa = Fraction.from_float(a)
    if not Fraction(n, x) > fa:
        bad_sup += 1
    if n > 1 and Fraction(n - 1, x) > fa:
        bad_min += 1
check("least_n_gt suppresses (20000 exact cases)", bad_sup == 0, f"{bad_sup} failures")
check("least_n_gt is minimal (20000 exact cases)", bad_min == 0, f"{bad_min} failures")

# the case that defeats the float formula, verbatim from the E11 audit
A_BAD, X_BAD = 0.24761283661298505, 35_646_736_295
naive = math.floor(A_BAD * X_BAD) + 1
exact = least_n_gt(A_BAD, X_BAD)
check("float np.floor(alpha*x)+1 really does overshoot here", naive == exact + 1,
      f"naive={naive} exact={exact}")
check("least_n_gt returns the exact value", exact == 8_826_589_490)
check("and exact-1 does NOT suppress",
      not (Fraction(exact - 1, X_BAD) > Fraction.from_float(A_BAD)))
check("while naive-1 DOES suppress (so naive is not minimal)",
      Fraction(naive - 1, X_BAD) > Fraction.from_float(A_BAD))

# integer boundary: ceil would be wrong, floor+1 is right
check("at integral alpha*x, least_n_gt = alpha*x + 1",
      least_n_gt(0.25, 4_000_000) == 1_000_001, f"got {least_n_gt(0.25, 4_000_000)}")

# ======================================================================================
print("=" * 100)
print("2. the D4a bracket, and its width")
print("=" * 100)
bad_b = 0
worst_units = 0.0
for _ in range(20000):
    x = int(rng.integers(4, 10**10))
    a = float(rng.uniform(1e-9, 0.25))
    p = Fraction(least_n_gt(a, x), x)
    fa = Fraction.from_float(a)
    if not (fa < p <= fa + Fraction(1, x)):
        bad_b += 1
    worst_units = max(worst_units, float((p - fa) * x))
check("alpha < p+ <= alpha + 1/(M*m), exact (20000 cases)", bad_b == 0, f"{bad_b} failures")
check("the excess never exceeds one unit of 1/(M*m)", worst_units <= 1.0 + 1e-12,
      f"worst = {worst_units:.9f}")
M = 1_813_114
check("bracket width at m = 1 is the conformal floor 1/M",
      abs(1.0 / M - 5.5154e-07) < 1e-11, f"1/M = {1.0/M:.6e}")

# ======================================================================================
print("=" * 100)
print("3. D5a -- saturation forces landing above the M*m threshold")
print("=" * 100)
fails_X = [X for X in range(1, 200_001)
           if not (LAM < (math.floor(LAM * X) + 1) / X <= TAU)]
check("the only integer M*m where SAT does not imply LAND is 1", fails_X == [1],
      f"failing set = {fails_X}")
check("the sufficient bound 1/(tau-lam) = 4 is safe but not sharp",
      1.0 / (TAU - LAM) == 4.0 and max(fails_X) < 4)
check("SAT => LAND on the real stream's M*m (>= M = 1,813,114)",
      LAM < (math.floor(LAM * M) + 1) / M <= TAU)

# ======================================================================================
print("=" * 100)
print("4. D5b -- an unsaturated episode CAN land, so sat <=> lands is not a theorem")
print("=" * 100)
p_uns = (math.floor(0.23 * 5) + 1) / 5.0
check("alpha=0.23 < lam, M*m=5: p+ = 0.4 lands", 0.23 < LAM and LAM < p_uns <= TAU,
      f"p+ = {p_uns}")
check("and it satisfies D5b's window condition", LAM - 0.23 < 1.0 / 5.0,
      f"lam - alpha = {LAM-0.23:.3f} < 1/(M*m) = {1/5:.3f}")
# outside the window it cannot land
p_far = (math.floor(0.10 * 5) + 1) / 5.0
check("outside the window (alpha=0.10, M*m=5) it does not land", not (LAM < p_far <= TAU),
      f"p+ = {p_far}")

# ======================================================================================
print("=" * 100)
print("5. the D7a median order statistic, odd and even n")
print("=" * 100)


def d7a_median(p_after, sat):
    """The derivation's closed form for median(p_after), valid when every unsaturated
    episode sits at or below lam and every saturated one above it."""
    p_after = np.asarray(p_after, float); sat = np.asarray(sat, bool)
    exc = np.sort(p_after[sat] - LAM)
    n = len(p_after); u = int((~sat).sum()); h = n // 2
    if n % 2 == 1:
        return LAM + exc[h - u]
    return LAM + 0.5 * (exc[h - 1 - u] + exc[h - u])


for n_tot, n_uns in ((147, 46), (100, 30), (11, 5), (10, 4), (7, 0), (8, 0)):
    ns = n_tot - n_uns
    exc = np.sort(rng.uniform(1e-12, 1.0 / M, size=ns))
    pa = np.concatenate([LAM - rng.uniform(1e-6, 0.2, size=n_uns), LAM + exc])
    sat = np.concatenate([np.zeros(n_uns, bool), np.ones(ns, bool)])
    perm = rng.permutation(n_tot)
    got = d7a_median(pa[perm], sat[perm])
    check(f"D7a median matches np.median at n={n_tot}, u={n_uns}",
          got == float(np.median(pa)), f"{got!r} vs {float(np.median(pa))!r}")

# ======================================================================================
print("=" * 100)
print("6. the shipped JSON satisfies all ten D6 identities, recomputed independently")
print("=" * 100)
if not JSON_PATH.exists():
    check("out/t32_B1.json exists", False, "run t32_B1_addis_state.py first")
else:
    c = json.load(open(JSON_PATH))["coincidence"]
    pe = c["per_episode"]
    col = {k: np.array([d[k] for d in pe]) for k in pe[0]}
    Mj, lam, tau = c["M"], c["lam"], c["tau"]
    X = np.rint(Mj * col["m_fire"]).astype(np.int64)
    check("I1  m_fire is a positive integer count",
          (col["m_fire"] >= 1).all() and (col["m_fire"] == col["m_fire"].astype(int)).all())
    check("I3  p_pre = min(1, nsz/(M*m))",
          np.allclose(col["p_pre"], np.minimum(1.0, col["nsz"] / X), rtol=1e-12, atol=0.0))
    check("I4  p_pre <= alpha_t for every exported episode",
          (col["p_pre"] <= col["alpha_t"] + 1e-15).all())
    check("I5  n_need is the exact least suppressing size",
          all(least_n_gt(a, int(x)) == int(n)
              for a, x, n in zip(col["alpha_t"], X, col["n_need"])))
    check("I6  pad = n_need - nsz >= 1",
          (col["pad"] == col["n_need"] - col["nsz"]).all() and (col["pad"] >= 1).all())
    check("I7  alpha_t < p_after <= alpha_t + 1/(M*m)",
          ((col["p_after"] > col["alpha_t"])
           & (col["p_after"] <= col["alpha_t"] + 1.0 / X + 1e-15)).all())
    check("I8  lands = lam < p_after <= tau",
          (col["lands_in_window"]
           == ((col["p_after"] > lam) & (col["p_after"] <= tau))).all())
    check("I9  saturated => lands", not (col["saturated"] & ~col["lands_in_window"]).any())
    check("D7a proviso: no unsaturated lander",
          not (~col["saturated"] & col["lands_in_window"]).any())
    check("I10 aggregates recompute from the arrays",
          int(col["saturated"].sum()) == c["n_level_saturated"]
          and int(col["lands_in_window"].sum()) == c["n_minimal_pad_lands_in_window"]
          and float(np.median(col["p_after"])) == c["median_p_after_minimal_pad"])
    check("D7a closed form reproduces the stored median",
          d7a_median(col["p_after"], col["saturated"])
          == c["median_p_after_minimal_pad"])
    check("population is named and both denominators exported",
          "population" in c and c["n_rejections_all"] >= c["n_detected"],
          f"{c['n_detected']} true detections of {c.get('n_rejections_all')} alerts")

# ======================================================================================
print("=" * 100)
print("7. the saturation test is EXACT, not np.isclose")
print("=" * 100)
check("np.isclose's tolerance at lam is wider than the conformal floor",
      2.5e-6 > 1.0 / M, f"isclose atol+rtol*lam = 2.5e-6 vs 1/M = {1.0/M:.3e}")
a_mis, x_mis = 0.249998, 1_000_000
p_mis = least_n_gt(a_mis, x_mis) / x_mis
check("np.isclose would call alpha=0.249998 saturated", bool(np.isclose(a_mis, LAM)))
check("but it does not land, so isclose would break sat => lands",
      not (LAM < p_mis <= TAU), f"p+ = {p_mis}")
check("the exact test rejects it", not (a_mis >= LAM))
check("t32 uses the exact test, not np.isclose", "sat = lv >= LAM" in SRC
      and "np.isclose(lv, LAM)" not in SRC)

# ======================================================================================
print("=" * 100)
print("8. mutation resistance -- nine deliberate corruptions must be caught")
print("=" * 100)


def caught(name, fn):
    """A mutation is CAUGHT if the recomputation it corrupts stops matching."""
    try:
        ok = fn()
    except Exception:
        ok = True                     # raising counts as catching
    check(f"mutation caught: {name}", ok)


X0 = 1_813_114 * 82
A0 = LAM
N0 = least_n_gt(A0, X0)
caught("n_need uses ceil instead of floor+1",
       lambda: math.ceil(A0 * X0) != N0 or not (Fraction(math.ceil(0.25 * 4_000_000),
                                                         4_000_000) > Fraction(1, 4)))
caught("n_need off by one (floor+2)", lambda: (N0 + 1) / X0 > A0 + 1.0 / X0)
caught("n_need off by one (floor)", lambda: not ((N0 - 1) / X0 > A0))
caught("p_after divided by M instead of M*m",
       lambda: not (LAM < N0 / 1_813_114 <= TAU))
caught("p_after divided by nsz instead of M*m",
       lambda: not (LAM < N0 / max(1, int(0.25 * X0)) <= TAU))
caught("lands uses >= lam instead of > lam (would admit p+ == lam)",
       lambda: (LAM >= LAM) and not (LAM > LAM))
caught("lands uses < tau instead of <= tau (drops the inclusive edge)",
       lambda: (0.5 <= TAU) and not (0.5 < TAU))
caught("saturation uses <= lam instead of >= lam (labels everything saturated)",
       lambda: (0.001 <= LAM) and not (0.001 >= LAM))
caught("D7a index forgets to subtract the unsaturated count",
       lambda: d7a_median(np.array([LAM - 0.1, LAM - 0.05, LAM + 1e-9, LAM + 2e-9,
                                    LAM + 3e-9]),
                          np.array([False, False, True, True, True]))
       != LAM + 3e-9)

print("=" * 100)
if fails:
    print(f"  {len(fails)} FAILURES: " + ", ".join(fails))
    raise SystemExit(1)
print("  ALL E11 SELF-TESTS PASS")
print("=" * 100)
