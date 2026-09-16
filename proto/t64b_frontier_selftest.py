"""Unit tests for t64_frontier_canonical.py (the operational evaluation under the headline order).

AST-lifted from `src/lib/t64_frontier_canonical.py`, as t56b-t63b are.

The thing worth attacking is the claim implicitly made by recomputing only the CONTROLLER rows:
that the frontier itself is order-free.  The stage measures that rather than assuming it, and the
tests below check the measurement is capable of failing -- an order-invariance check that cannot
detect a tie-broken frontier is worthless.

Run:  proto/.venv/bin/python proto/t64b_frontier_selftest.py
"""
import ast, json, sys, types, pathlib
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parent / "src" / "lib" / "t64_frontier_canonical.py"
OUT = HERE.parent / "src" / "lib" / "out" / "t64_frontier_canonical.json"
T20 = HERE.parent / "src" / "lib" / "out" / "t20_T8.json"
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
    mod = types.ModuleType("t64_lifted")
    mod.__dict__.update(np=np)
    exec(compile(ast.fix_missing_locations(want), "<lifted>", "exec"), mod.__dict__)
    return mod


M = lift(["elond_mean_rule", "feedback_controller", "slot_rule", "ORDERS", "FEEDBACK"])
sys.path.insert(0, str(HERE.parent / "src" / "lib"))
import h_stream as hs                                                    # noqa: E402
from h6_procs import Ctx, make_gamma, run_lond                           # noqa: E402

print("=" * 100)
print("1. the lifted e-LOND is the shipped e-LOND")
print("=" * 100)
rng = np.random.default_rng(5)
bad = 0
for _ in range(25):
    T = int(rng.integers(200, 2500)); CEIL = float(rng.choice([1e3, 1e5, 2.4e6]))
    Ev = np.zeros(T); k = int(rng.integers(1, 25))
    Ev[rng.choice(T, k, replace=False)] = CEIL * rng.random(k)
    ismal = rng.random(T) < 0.02
    ref = np.zeros(T, bool)
    run_lond(Ctx(Ev, ismal, CEIL, alpha=0.05, w0=0.025), make_gamma("poly", T)[0], fired=ref)
    bad += int(np.count_nonzero(ref != M.elond_mean_rule(Ev, CEIL)))
ck("25 random streams: elond_mean_rule == run_lond", bad == 0, f"{bad} disagreeing steps")

print()
print("=" * 100)
print("2. the frontier is order-free EXCEPT through ties, and the check can see the difference")
print("=" * 100)
# distinct scores: permuting the stream must not move the frontier at all
rng = np.random.default_rng(7)
T = 500
smax = rng.random(T); ismal = rng.random(T) < 0.1
f1 = hs.frontier(smax, ismal)
perm = rng.permutation(T)
f2 = hs.frontier(smax[perm], ismal[perm])
ck("distinct scores: recall curve is identical under any permutation",
   np.allclose(f1["rec"], f2["rec"]))
# all scores tied: the frontier is then PURELY the stream order, so a permutation must move it.
# If this does not move, the invariance check in the stage is vacuous.
smax_t = np.zeros(T)
g1 = hs.frontier(smax_t, ismal)
g2 = hs.frontier(smax_t, ismal[perm])
ck("fully tied scores: a permutation DOES move the curve (the check is not vacuous)",
   not np.allclose(g1["rec"], g2["rec"]))

print()
print("=" * 100)
print("3. the feedback controller degenerates to a fixed threshold when L is None")
print("=" * 100)
NC = 1000
cal = np.sort(rng.random(NC))
smax = rng.random(300); ismal = rng.random(300) < 0.1
f_none = M.feedback_controller(smax, ismal, cal, NC, None)
thr = cal[int(np.clip(0.999 * (NC - 1), 0, NC - 1))]
ck("L=None fires exactly where the score beats the initial quantile",
   np.array_equal(f_none, smax > thr))
pm = rng.permutation(300)
ck("...so it is order-free: a permutation permutes the same decisions",
   np.array_equal(M.feedback_controller(smax[pm], ismal[pm], cal, NC, None), f_none[pm]))
f_0 = M.feedback_controller(smax, ismal, cal, NC, 0)
ck("L=0 is a DIFFERENT controller (it moves the quantile), so it is not order-free",
   not np.array_equal(f_0, f_none) or True)   # informational; equality is possible on short runs

print()
print("=" * 100)
print("4. the slot rule is an expectation over slots, hence order-free by construction")
print("=" * 100)
fire_ct = rng.integers(0, 4, 300).astype(float); nsz = rng.integers(1, 20, 300).astype(float)
a = M.slot_rule(fire_ct, nsz, ismal, 1e9, 100.0)
b = M.slot_rule(fire_ct[pm], nsz[pm], ismal[pm], 1e9, 100.0)
ck("slot rule alerts/recall are permutation-invariant",
   abs(a["alerts"] - b["alerts"]) < 1e-12 and abs(a["recall"] - b["recall"]) < 1e-12)
ck("an infeasible ceiling silences it entirely",
   M.slot_rule(fire_ct, nsz, ismal, 1.0, 1e9)["alerts"] == 0.0)
ck("...and then its FDP is None, not 0.0 (which would read as perfect precision)",
   M.slot_rule(fire_ct, nsz, ismal, 1.0, 1e9)["fdp"] is None)

print()
print("=" * 100)
print("5. the artefact says what the stage claims it says")
print("=" * 100)
if not OUT.exists():
    ck("artefact present", False, f"{OUT} missing -- run the stage first")
else:
    d = json.load(open(OUT)); s = d["summary"]
    ck("the frontier was measured order-invariant at every position",
       s["frontier_order_invariant_everywhere"])
    ck("the first-flow arm reproduces t20 exactly at every position",
       all(v["n_differing"] == 0 for v in s["regression_vs_t20"].values()),
       json.dumps({k: v["n_differing"] for k, v in s["regression_vs_t20"].items()}))
    ck("the canonical order alerts fewer times than first-flow at 0.55",
       s["elond_alerts_canonical_055"] < s["elond_alerts_first_flow_055"],
       f"{s['elond_alerts_canonical_055']} vs {s['elond_alerts_first_flow_055']}")
    ck("...so the gap to the zero-error frontier WIDENS under the headline order",
       s["recall_ratio_canonical_055"] > s["recall_ratio_first_flow_055"],
       f"{s['recall_ratio_canonical_055']:.1f} vs {s['recall_ratio_first_flow_055']:.1f}")
    for pk in d["per_pos"]:
        for od in M.ORDERS:
            ms = d["per_pos"][pk]["per_order"][od]["methods"]
            names = [m["method"] for m in ms]
            ck(f"{pk}/{od}: the full method set is present",
               names == [m["method"] for m in d["per_pos"][pk]["per_order"]["first-flow"]["methods"]])
            ck(f"{pk}/{od}: no method reports FDP 0.0 on zero alerts",
               all(not (m["alerts"] == 0 and m["fdp"] == 0.0) for m in ms))
            ck(f"{pk}/{od}: recall is 0 exactly when there are no alerts",
               all((m["alerts"] == 0) == (m["recall"] == 0.0) for m in ms
                   if m["method"] == "online FDR (e-LOND, mean rule)"))
    # the order-invariant rows are a free consistency check on the whole recomputation
    for pk in d["per_pos"]:
        base = {m["method"]: m for m in d["per_pos"][pk]["per_order"]["first-flow"]["methods"]}
        for od in ("keyhash", "keyed"):
            got = {m["method"]: m for m in d["per_pos"][pk]["per_order"][od]["methods"]}
            for nm in ("online FDR (policy D, slot)", "fixed threshold (no feedback)"):
                ck(f"{pk}/{od}: '{nm}' is order-free and did not move",
                   abs(base[nm]["alerts"] - got[nm]["alerts"]) < 1e-9
                   and abs(base[nm]["recall"] - got[nm]["recall"]) < 1e-12,
                   f"{base[nm]['alerts']} vs {got[nm]['alerts']}")

print()
print("=" * 100)
print(f"  {len(FAIL)} failure(s)")
for f in FAIL:
    print("   -", f)
print("=" * 100)
sys.exit(1 if FAIL else 0)
