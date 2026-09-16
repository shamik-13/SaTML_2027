"""Unit tests for t63_blindkey.py (what a SECRET canonical-order seed costs the inserter).

Same discipline as t56b-t60b: the tests drive the SHIPPED functions, AST-lifted from
`src/lib/t63_blindkey.py`, never a restatement of them.

Three things are worth attacking here, and each gets a test whose answer is known by hand:

  1. `_elond_prefix` stops at the first infeasible step.  That is sound only because the level is
     non-increasing in the step index at fixed R and R cannot advance while nothing can fire.  If
     the reasoning is wrong the replay silently misses late rejections, and every cost in the stage
     is too small.  Tested against `h6_procs.run_lond` on random streams INCLUDING streams built so
     that a late high-evidence episode sits past the feasible prefix.
  2. `shifts_from_hashes` must count insertions per episode by BUCKET and then by hash.  An
     off-by-one here changes every budget.
  3. `_interp_budget` must return the smallest budget reaching the target success, and None when
     the grid never reaches it -- not the largest budget, and not a silent 0.

Run:  proto/.venv/bin/python proto/t63b_blindkey_selftest.py
"""
import ast, json, sys, types, pathlib
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parent / "src" / "lib" / "t63_blindkey.py"
OUT = HERE.parent / "src" / "lib" / "out" / "t63_blindkey.json"
FAIL = []


def ck(label, cond, detail=""):
    if not cond:
        FAIL.append(f"{label}   {detail}" if detail else label)
    print(f"  {'ok  ' if cond else 'FAIL'}  {label}" + (f"   {detail}" if detail and not cond else ""))


def lift(names):
    tree = ast.parse(SRC.read_text())
    want = ast.Module(body=[], type_ignores=[]); got = set()
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name in names:
            want.body.append(n); got.add(n.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id in names:
                    want.body.append(n); got.add(t.id)
    missing = set(names) - got
    if missing:
        raise SystemExit(f"cannot lift {missing} from {SRC}")
    sys.path.insert(0, str(HERE.parent / "src" / "lib"))
    from scipy.special import zeta
    mod = types.ModuleType("t63_lifted")
    mod.__dict__.update(np=np, zeta=zeta)
    exec(compile(ast.fix_missing_locations(want), "<lifted>", "exec"), mod.__dict__)
    return mod


M = lift(["_elond_prefix", "shifts_from_hashes", "blind_curve", "_interp_budget",
          "A", "W0", "K", "Z16", "HMAX", "POS", "ORDERS", "BUDGETS", "N_REP"])
sys.path.insert(0, str(HERE.parent / "src" / "lib"))
from h6_procs import Ctx, make_gamma, run_lond                                    # noqa: E402

print("=" * 100)
print("1. the replay engine reproduces the shipped controller, including past the prefix")
print("=" * 100)
rng = np.random.default_rng(11)
worst = 0
for trial in range(30):
    T = int(rng.integers(300, 3000))
    CEIL = float(rng.choice([1e3, 1e5, 2.4e6]))
    Ev = np.zeros(T)
    n_hot = int(rng.integers(1, 30))
    Ev[rng.choice(T, n_hot, replace=False)] = CEIL * rng.random(n_hot)
    ismal = rng.random(T) < 0.01
    ref = np.zeros(T, bool)
    run_lond(Ctx(Ev, ismal, CEIL, alpha=M.A, w0=M.W0), make_gamma("poly", T)[0], fired=ref)
    mine = M._elond_prefix(Ev, CEIL, np.zeros(T, np.int64))
    worst += int(np.count_nonzero(ref != mine))
ck("30 random streams: replay == run_lond exactly", worst == 0, f"{worst} disagreeing steps")

# The early stop is sound ONLY for non-decreasing shifts (round-8 audit, MINOR 1): a mask that
# shifts a prefix and leaves later episodes in place makes the level rise again, so the module must
# REFUSE it rather than silently return a truncated fire mask.
try:
    M._elond_prefix(np.zeros(10), 1e5, np.array([0, 0, 5, 5, 1, 1, 1, 1, 1, 1], np.int64))
    ck("a NON-monotone shift is refused, not silently truncated", False, "no exception raised")
except ValueError:
    ck("a NON-monotone shift is refused, not silently truncated", True)
ck("...and a monotone one is accepted",
   M._elond_prefix(np.zeros(10), 1e5, np.array([0, 0, 1, 1, 5, 5, 9, 9, 9, 9], np.int64)).shape
   == (10,))

# the adversarial case for the early-stop: a ceiling-carrying episode placed LATE, past the point
# at which the level has already fallen below 1/CEIL.  If the stop were unsound this would fire.
T = 5000; CEIL = 1e5
Ev = np.zeros(T); Ev[0] = CEIL; Ev[4000] = CEIL
ref = np.zeros(T, bool)
run_lond(Ctx(Ev, np.zeros(T, bool), CEIL, alpha=M.A, w0=M.W0),
         make_gamma("poly", T)[0], fired=ref)
mine = M._elond_prefix(Ev, CEIL, np.zeros(T, np.int64))
ck("a ceiling episode past the feasible prefix: replay agrees with run_lond",
   np.array_equal(ref, mine), f"ref fires {np.flatnonzero(ref)} vs replay {np.flatnonzero(mine)}")
ck("...and it is genuinely past the prefix (the late one does not fire)", not ref[4000])

print()
print("=" * 100)
print("2. shifting moves the step index by exactly the count inserted ahead")
print("=" * 100)
# One episode carrying the ceiling at index p fires iff its STEP is inside the cold-start window.
# Inserting G ahead of it moves it to step p+1+G, so the boundary is exact and computable.
CEIL = 1e4; T = 4000; p = 10
Ev = np.zeros(T); Ev[p] = CEIL
w = 0
while M.A * ((w + 1) ** -1.6 / M.Z16) * 1.0 * CEIL >= 1.0:
    w += 1                                             # last step at which the ceiling clears
# after the loop w is the LAST step that clears, so the episode at index p (step p+1+G) still
# fires at G = w-p-1 and is suppressed at G = w-p.  The minimal suppressing shift is w-p.
G_expect = max(0, w - p)
fires = [bool(M._elond_prefix(Ev, CEIL, np.full(T, g, np.int64))[p]) for g in
         (G_expect - 1, G_expect, G_expect + 1)]
ck("shift = G*-1 still fires, G* does not, G*+1 does not",
   fires == [True, False, False], f"G*={G_expect} gave {fires}")

print()
print("=" * 100)
print("3. shifts_from_hashes counts by bucket, then by hash")
print("=" * 100)
h = np.array([10, 20, 30, 40], dtype=np.int64)
bucket = np.array([0, 0, 1, 1], dtype=np.int64)
c = M.shifts_from_hashes(h, bucket, 0, np.array([5, 15, 25, 35], dtype=np.int64))
ck("in-bucket episodes count only the hashes below them", list(c[:2]) == [1, 2], f"{c}")
ck("later-bucket episodes are preceded by ALL insertions", list(c[2:]) == [4, 4], f"{c}")
c0 = M.shifts_from_hashes(h, bucket, 0, np.array([], dtype=np.int64))
ck("no draws shifts nothing", list(c0) == [0, 0, 0, 0], f"{c0}")
# an insertion whose hash equals an episode's must not be counted as preceding it: `side="left"`
ceq = M.shifts_from_hashes(h, bucket, 0, np.array([10], dtype=np.int64))
ck("an insertion with the SAME hash does not precede the episode", int(ceq[0]) == 0, f"{ceq}")
# insertions into a LATER bucket precede nothing in the first
c2 = M.shifts_from_hashes(h, bucket, 1, np.array([5, 35], dtype=np.int64))
ck("insertions in bucket 1 do not move bucket-0 episodes", list(c2[:2]) == [0, 0], f"{c2}")

print()
print("=" * 100)
print("4. the budget interpolation is a SMALLEST-reaching budget, not a largest")
print("=" * 100)
B = [10, 100, 1000, 10000]
ck("exact hit returns that grid point", M._interp_budget(B, [0.0, 0.5, 0.9, 1.0], 0.5) == 100.0)
ck("first grid point already sufficient returns it",
   M._interp_budget(B, [0.99, 1.0, 1.0, 1.0], 0.5) == 10.0)
ck("never reached returns None", M._interp_budget(B, [0.0, 0.0, 0.1, 0.2], 0.9) is None)
mid = M._interp_budget(B, [0.0, 0.4, 0.8, 1.0], 0.6)
ck("interpolates strictly inside the bracketing interval", 100.0 < mid < 1000.0, f"{mid}")
ck("...log-interpolated, so the midpoint of a decade is its geometric mean",
   abs(M._interp_budget([100, 1000], [0.0, 1.0], 0.5) - np.sqrt(100 * 1000)) < 1e-6)
ck("monotone in the target: N99 >= N50",
   M._interp_budget(B, [0.0, 0.4, 0.8, 1.0], 0.99) >= M._interp_budget(B, [0.0, 0.4, 0.8, 1.0], 0.5))

print()
print("=" * 100)
print("5. blind_curve is monotone in budget, and a zero-hash target is free")
print("=" * 100)
CEIL = 1e4; T = 2000
Ev = np.zeros(T); Ev[5] = CEIL; Ev[6] = CEIL
h = (np.linspace(0.05, 0.95, T) * M.HMAX).astype(np.int64)
bucket = np.zeros(T, np.int64)
psucc = M.blind_curve(Ev, CEIL, h, bucket, 0, np.array([5]), [10, 100, 1000, 10000], 40,
                      np.random.default_rng(3))
ck("success probability is non-decreasing in the key budget",
   bool(np.all(np.diff(psucc[:, 0]) >= -1e-12)), f"{psucc[:, 0]}")
ck("a large budget suppresses a low-hash target", psucc[-1, 0] == 1.0, f"{psucc[-1, 0]}")

print()
print("=" * 100)
print("6. the artefact says what the stage claims it says")
print("=" * 100)
if not OUT.exists():
    ck("artefact present", False, f"{OUT} missing -- run the stage first")
else:
    d = json.load(open(OUT)); s = d["summary"]; live = [r for r in d["rows"] if r.get("n_targets")]
    ck("no assertion failed in the run", not s["assertions_failed"], str(s["assertions_failed"]))
    ck("every public G* was verified by replay, both placements",
       s["public_gstar_verified_everywhere"])
    ck("the replay never falls materially below its binomial lower bound",
       s["max_binomial_lower_bound_violation"] <= 0.05,
       f"{s['max_binomial_lower_bound_violation']:+.4f}")
    ck("the front placement is never dearer than the targeted one",
       all(f <= t for r in live for f, t in zip(r["public_gstar_front"], r["public_gstar_targeted"])
           if t is not None),
       "front placement also suppresses the earlier detections, so it can only be cheaper")
    ck("blind is never cheaper than public at MATCHED reliability: every ratio >= 1",
       all(x >= 1.0 for r in live for x in r["blind_over_public_ratio"] if x is not None))
    ck("...and the ratio is N99 over G*, not N50 over G*",
       s["ratio_basis"].startswith("N99 / G*_front"), s.get("ratio_basis", "<missing>"))
    ck("the optimistic N50 ratio is kept separately and is never larger",
       all(a is None or b is None or b <= a + 1e-9
           for r in live for a, b in zip(r["blind_over_public_ratio"],
                                         r["blind_over_public_ratio_at_50pct"])))
    ck("'all targets fall' is read off the last grid row, not inferred from N50",
       s["every_target_certain_at_max_budget"]
       and s["n_targets_certain_at_max_budget"] == s["n_targets_total"],
       f"{s['n_targets_certain_at_max_budget']}/{s['n_targets_total']}, "
       f"worst p={s['min_p_success_at_max_budget']}")
    ck("the single-bucket insertion premise holds at every live cell",
       all(r["all_targets_in_one_bucket"] for r in live))
    ck("no earlier bucket exists anywhere -- otherwise insertion there is free",
       s["target_bucket_is_first_of_window_everywhere"])
    ck("every reported budget carries the grid bracket that is its real precision",
       s["bracket_width_max"] <= 1.5, f"{s['bracket_width_max']:.3f}x")
    ck("each N50 lies inside its own reported bracket",
       all(lo is None or hi is None or lo <= n <= hi
           for r in live for n, (lo, hi) in zip(r["N50"], r["N50_bracket"]) if n is not None))
    ck("every success curve is monotone in the budget",
       all(all(r["p_success"][i][j] <= r["p_success"][i + 1][j] + 1e-12
               for i in range(len(r["budgets"]) - 1) for j in range(r["n_targets"]))
           for r in live))
    ck("N50 <= N90 <= N99 wherever all three are reached",
       all((a <= b + 1e-9 and b <= c + 1e-9)
           for r in live for a, b, c in zip(r["N50"], r["N90"], r["N99"])
           if None not in (a, b, c)))
    ck("target hash quantiles lie in (0,1)",
       all(0.0 < x < 1.0 for r in live for x in r["target_hash_quantile"]))
    ck("cells with no detection carry no cost claim",
       all("note" in r for r in d["rows"] if not r.get("n_targets")))
    ck("the keyed arm is measured at every window where it detects anything",
       {r["pos"] for r in live if r["order"] == "keyed"} == {0.62, 0.70, 0.77, 0.85},
       str(sorted({r["pos"] for r in live if r["order"] == "keyed"})))

print()
print("=" * 100)
print(f"  {len(FAIL)} failure(s)")
for f in FAIL:
    print("   -", f)
print("=" * 100)
sys.exit(1 if FAIL else 0)
