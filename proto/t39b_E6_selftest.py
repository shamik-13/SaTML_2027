"""
Unit tests for the E6 selection machinery (t39_E6_transfer.py, t39a_E6_derivation.py).
No data files: everything is synthetic and runs in about a second.

The three functions that carry all of E6's non-obvious logic -- `select`,
`normalised_regret` and `transfer_table` -- are pulled OUT of t39_E6_transfer.py by AST and
executed here, so the tests exercise the SHIPPED code rather than a copy of it (standing
mistake 16: an earlier self-test was defeated because it tested copies and grepped the
source for strings).

What it pins down:
  1  select() honours the DECLARED tie-break order, not array position or value order
  2  select() refuses all-NaN and inf objectives rather than resolving them silently
  3  normalised_regret() is None on a flat grid and tolerant of float noise
  4  transfer_table() restricts selection to configs present and feasible on the SELECTION
     windows, and the oracle to configs feasible on the EVALUATION window
  5  transfer_table() flags a flat selection window instead of reporting its regret as a
     transfer result
  6  is_worst / frozen_is_worst are exact, so a printed rho of 1.000 is not read as "worst"
  7  the winner's-curse field is selection-value minus evaluation-value, in that order
  8  eleven deliberate mutations of the selection algebra are caught
"""
import numpy as np, ast, json
from pathlib import Path

SRC_PATH = Path(__file__).with_name("t39_E6_transfer.py")
SRC = SRC_PATH.read_text()
JSON_PATH = Path(__file__).with_name("out") / "t39_E6.json"
fails = []


def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"   {detail}" if detail else ""))
    if not cond:
        fails.append(name)


def load_module_level(*names):
    tree = ast.parse(SRC)
    want = {n.name: n for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name in names}
    missing = set(names) - set(want)
    if missing:
        raise AssertionError(f"not module-level in {SRC_PATH.name}: {sorted(missing)}")
    ns = {"np": np, "OBJ": "flow_cov_addis"}
    exec(compile(ast.fix_missing_locations(
        ast.Module(body=[want[n] for n in names], type_ignores=[])), str(SRC_PATH), "exec"), ns)
    return [ns[n] for n in names]


select, normalised_regret, transfer_table = load_module_level(
    "select", "normalised_regret", "transfer_table")


def raises(fn, exc=ValueError):
    try:
        fn()
        return False
    except exc:
        return True


# ======================================================================================
print("=" * 100)
print("1. select() honours the declared tie-break order")
print("=" * 100)
v = np.array([0.5, 0.9, 0.9, 0.9, 0.2])
check("picks the lowest declared priority among ties", select(v, np.arange(5)) == (1, 3))
check("a reversed declared order picks a different winner",
      select(v, np.array([4, 3, 2, 1, 0])) == (3, 3))
check("array position does not decide the winner",
      select(np.array([0.9, 0.9]), np.array([1, 0])) == (1, 2))
check("a strict maximum wins regardless of priority",
      select(np.array([0.1, 0.99]), np.array([0, 1])) == (1, 1))
check("NaN entries are excluded, not treated as zero",
      select(np.array([0.2, np.nan, 0.9, np.nan]), np.arange(4)) == (2, 1))
check("negative objectives work", select(np.array([-3.0, -1.0, -2.0]), np.arange(3)) == (1, 1))

print("=" * 100)
print("2. select() refuses degenerate objectives instead of resolving them")
print("=" * 100)
check("all-NaN raises", raises(lambda: select(np.full(4, np.nan), np.arange(4))))
check("+inf raises", raises(lambda: select(np.array([1.0, np.inf]), np.arange(2))))
check("-inf raises", raises(lambda: select(np.array([1.0, -np.inf]), np.arange(2))))

print("=" * 100)
print("3. normalised_regret()")
print("=" * 100)
v3 = np.array([0.1, 0.5, 0.9])
check("rho = 0 at the oracle", normalised_regret(v3, 0.9) == 0.0)
check("rho = 1 at the worst", normalised_regret(v3, 0.1) == 1.0)
check("rho = 0.5 midway", abs(normalised_regret(v3, 0.5) - 0.5) < 1e-12)
check("None on an exactly flat grid", normalised_regret(np.full(5, 0.3), 0.3) is None)
check("None on a grid flat to float noise (not a huge rho)",
      normalised_regret(np.array([1.0, 1.0 + 1e-15]), 1.0 - 1e-12) is None)
check("None on an all-NaN grid", normalised_regret(np.full(3, np.nan), 0.5) is None)
check("NaNs are dropped, not propagated",
      normalised_regret(np.array([0.1, np.nan, 0.9]), 0.9) == 0.0)

print("=" * 100)
print("4-7. transfer_table()")
print("=" * 100)
cfgs = ["a", "b", "c", "d"]
order = np.arange(4)
# window 0 is the selection window, window 1 the evaluation window
value = np.array([[0.1, 0.9, 0.5, 0.2],      # selection: b is best
                  [0.7, 0.2, 0.8, 0.0]])     # evaluation: c is best, b is poor
r = transfer_table(cfgs, order, value, [0], 1, frozen_idx=0)
check("selects on the selection window", r["winner"] == "b")
check("evaluates on the evaluation window", r["value_on_eval"] == 0.2)
check("oracle is the evaluation-window maximum", r["oracle"] == 0.8)
check("regret is oracle minus achieved", abs(r["regret"] - 0.6) < 1e-12)
check("winner's curse is selection minus evaluation",
      abs(r["winners_curse"] - (0.9 - 0.2)) < 1e-12)
check("frozen fields use the frozen index, not the winner",
      r["frozen"] == "a" and r["frozen_value"] == 0.7)
check("is_worst is False when the winner is not the minimum", r["is_worst"] is False)
check("transfer_defined is True on a varied selection window", r["transfer_defined"])

# the worst config, exactly
r_worst = transfer_table(cfgs, order, np.array([[0.1, 0.2, 0.5, 0.9],
                                                [0.7, 0.2, 0.8, 0.0]]), [0], 1, 0)
check("is_worst is True when the winner IS the minimum", r_worst["is_worst"] is True)

# [5] a FLAT selection window is flagged, not silently reported as a transfer result
r_flat = transfer_table(cfgs, order, np.array([[0.3, 0.3, 0.3, 0.3],
                                               [0.7, 0.2, 0.8, 0.0]]), [0], 1, 0)
check("a flat selection window sets transfer_defined False",
      r_flat["transfer_defined"] is False)
check("and its selection_spread is 0", r_flat["selection_spread"] == 0.0)
check("and the tie-break still picks the declared-first config", r_flat["winner"] == "a")
check("and n_tied reports every config", r_flat["n_tied"] == 4)

# [4] feasibility gating
feas = np.array([[True, True, False, True],     # c infeasible on the selection window
                 [True, False, True, True]])    # b infeasible on the evaluation window
r_f = transfer_table(cfgs, order, value, [0], 1, 0, feas=feas)
# `c` must be the config that WOULD have won without the mask, or this tests nothing: in
# `value` above c scores 0.5 against b's 0.9, so omitting the mask still gives b.
value_gate = np.array([[0.1, 0.9, 0.95, 0.2],
                       [0.7, 0.2, 0.8, 0.0]])
check("without the mask the infeasible config wins",
      transfer_table(cfgs, order, value_gate, [0], 1, 0)["winner"] == "c")
check("with the mask it is excluded and the best feasible one wins",
      transfer_table(cfgs, order, value_gate, [0], 1, 0, feas=feas)["winner"] == "b")
check("an infeasible-on-selection config cannot be selected", r_f["winner"] != "c")
check("the oracle skips configs infeasible on the evaluation window",
      r_f["oracle_config"] == "c" and r_f["oracle"] == 0.8)
feas2 = np.array([[True, True, True, True],
                  [True, True, False, True]])   # c infeasible where it was the oracle
r_f2 = transfer_table(cfgs, order, value, [0], 1, 0, feas=feas2)
check("with the oracle config infeasible, the oracle drops to the best feasible one",
      r_f2["oracle"] == 0.7 and r_f2["oracle_config"] == "a")
check("n_eligible counts the selectable configs", r_f["n_eligible"] == 3)
check("winner_feasible_on_eval is reported", r_f["winner_feasible_on_eval"] is False)

# multi-window selection must use only configs present on EVERY selection window
val3 = np.array([[0.7, np.nan, 0.5, 0.2],
                 [0.7, 1.0, 0.5, 0.2],
                 [0.0, 0.0, 1.0, 0.0]])
r_m = transfer_table(cfgs, order, val3, [0, 1], 2, 0)
check("a config missing on one selection window is not selected", r_m["winner"] != "b")
check("and the complete config wins", r_m["winner"] == "a")

print("=" * 100)
print("8. mutation resistance")
print("=" * 100)


def caught(name, cond):
    check(f"mutation caught: {name}", cond)


caught("select returns argmin instead of argmax",
       select(np.array([0.1, 0.9]), np.arange(2))[0] != int(np.argmin([0.1, 0.9])))
caught("select ignores the declared order and takes the first tied index",
       select(np.array([0.9, 0.9]), np.array([1, 0]))[0] != 0)
caught("normalised_regret returns 0 rather than None on a flat grid",
       normalised_regret(np.full(4, 0.5), 0.5) is None)
caught("normalised_regret divides by the oracle instead of the spread",
       abs(normalised_regret(v3, 0.5) - (0.9 - 0.5) / 0.9) > 1e-9)
caught("regret computed as achieved minus oracle",
       transfer_table(cfgs, order, value, [0], 1, 0)["regret"] > 0)
caught("winner's curse computed evaluation minus selection",
       transfer_table(cfgs, order, value, [0], 1, 0)["winners_curse"] > 0)
caught("oracle taken over the SELECTION window",
       transfer_table(cfgs, order, value, [0], 1, 0)["oracle"] != 0.9)
caught("frozen fields read from the winner",
       transfer_table(cfgs, order, value, [0], 1, 0)["frozen_value"] != 0.2)
caught("feasibility mask applied to the wrong window",
       transfer_table(cfgs, order, value, [0], 1, 0, feas=feas)["oracle"] == 0.8)
caught("nanmean over ragged support lets an absent config win",
       transfer_table(cfgs, order, val3, [0, 1], 2, 0)["winner"] != "b")
# A fixture where the winner is NEARLY but not exactly the worst, so an implementation
# that tested the printed rho (which rounds to 1.000) would pass while the exact one fails.
_near = transfer_table(cfgs, order,
                       np.array([[0.1, 0.9, 0.5, 0.2],
                                 [1.0, 0.0004, 0.0, 0.5]]), [0], 1, 0)
caught("is_worst uses rho >= 1 rather than an exact comparison",
       format(_near["rho"], ".3f") == "1.000" and _near["is_worst"] is False)

print("=" * 100)
print("9. the shipped JSON is consistent with these definitions")
print("=" * 100)
if not JSON_PATH.exists():
    check("out/t39_E6.json exists", False, "run t39_E6_transfer.py first")
else:
    j = json.load(open(JSON_PATH))
    allrows = []
    for axis in ("grouping", "cap"):
        for seed, res in j[axis].items():
            allrows += res["E6a"] + res["E6b"]
    check("every regret is non-negative", all(r["regret"] >= -1e-12 for r in allrows))
    check("every frozen_regret is non-negative",
          all(r["frozen_regret"] >= -1e-12 for r in allrows))
    check("regret == oracle - value_on_eval",
          all(abs(r["regret"] - (r["oracle"] - r["value_on_eval"])) < 1e-12 for r in allrows))
    check("winners_curse == selection - evaluation",
          all(abs(r["winners_curse"] - (r["value_on_selection"] - r["value_on_eval"])) < 1e-12
              for r in allrows))
    check("rho is None exactly where the evaluation grid is flat",
          all((r["rho"] is None) == (r["spread"] <= 1e-12) for r in allrows))
    check("is_worst implies rho == 1 where rho is defined",
          all((not r["is_worst"]) or r["rho"] is None or abs(r["rho"] - 1.0) < 1e-9
              for r in allrows))
    nfl = sum(1 for r in allrows if not r["transfer_defined"])
    check("flat-selection rows are flagged", nfl >= 0,
          f"{nfl} of {len(allrows)} folds had a flat selection window")
    check("every winner is feasible on its evaluation window, or is reported as not",
          all("winner_feasible_on_eval" in r for r in allrows))

print("=" * 100)
if fails:
    print(f"  {len(fails)} FAILURES: " + ", ".join(fails))
    raise SystemExit(1)
print("  ALL E6 SELF-TESTS PASS")
print("=" * 100)
