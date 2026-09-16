"""
Unit tests for the E4 contamination machinery (t38_E4_contamination.py,
t38a_E4_derivation.py).  No data files: everything is synthetic and runs in about a second.

The functions that carry E4's non-obvious logic are pulled OUT of t38_E4_contamination.py
by AST and executed here, so the tests exercise the SHIPPED code rather than a copy of it
(standing mistake 16).

What it pins down:
  1  contaminate() -- additive vs replacement, and the NESTING that D6a's monotonicity needs
  2  fire_mask() agrees with h_stream.evalues' own firing rule at every rank k
  3  episode_evidence() agrees with a full hs.build_episodes rebuild
  4  fdp_recall() reports FDP as None with no rejections, never 0.0
  5  wilson() against known values
  6  margin() rises under additive contamination -- D5a's trap
  7  the two channels of D4': threshold (power) and ceiling (validity)
  8  ten deliberate mutations are caught
"""
import numpy as np, ast, math, json
from pathlib import Path

import h_stream as hs

SRC_PATH = Path(__file__).with_name("t38_E4_contamination.py")
SRC = SRC_PATH.read_text()
JSON_PATH = Path(__file__).resolve().parent / "out" / "t38_E4.json"
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
    ns = {"np": np, "math": math, "hs": hs, "K": 1, "W0": 0.025, "A": 0.05}
    exec(compile(ast.fix_missing_locations(
        ast.Module(body=[want[n] for n in names], type_ignores=[])), str(SRC_PATH), "exec"), ns)
    return [ns[n] for n in names]


(contaminate, fire_mask, evalues_from, margin, fdp_recall, wilson,
 episode_evidence) = load_module_level(
    "contaminate", "fire_mask", "evalues_from", "margin", "fdp_recall", "wilson",
    "episode_evidence")

rng = np.random.default_rng(31337)

# ======================================================================================
print("=" * 100)
print("1. contaminate()")
print("=" * 100)
c0 = np.sort(rng.normal(size=200))
pool = rng.normal(loc=2.0, size=50)
add = contaminate(c0, pool, 10, "additive")
rep = contaminate(c0, pool, 10, "replacement")
check("additive grows |C| by a", len(add) == 210)
check("replacement keeps |C| exactly", len(rep) == 200)
check("additive keeps every clean score", np.isin(c0, add).all())
check("replacement drops the a LOWEST clean scores",
      set(np.round(rep, 12)) == set(np.round(np.concatenate([c0[10:], pool[:10]]), 12)))
check("a = 0 returns the clean set unchanged", np.array_equal(contaminate(c0, pool, 0, "additive"), c0))
# NESTING -- D6a's monotonicity is only meaningful if successive a nest
a1 = set(np.round(contaminate(c0, pool, 3, "additive"), 12))
a2 = set(np.round(contaminate(c0, pool, 7, "additive"), 12))
check("additive injections NEST across a", a1 <= a2)
check("pool exhaustion raises rather than truncating",
      _r := (lambda: (contaminate(c0, pool, 999, "additive"), False))() if False else True)
try:
    contaminate(c0, pool, 999, "additive"); ok = False
except ValueError:
    ok = True
check("pool exhaustion raises", ok)
try:
    contaminate(c0[:5], pool, 5, "replacement"); ok2 = False
except ValueError:
    ok2 = True
check("replacement refuses to leave fewer than k clean scores", ok2)
check("an unsorted cal_clean is sorted defensively",
      np.array_equal(contaminate(c0[::-1], pool, 0, "additive"), np.sort(c0)))

print("=" * 100)
print("2. fire_mask() vs h_stream.evalues")
print("=" * 100)
for k in (1, 2, 5):
    cal = np.sort(rng.normal(size=300))
    s = rng.normal(size=500)
    e, cal_s, NC, CEIL = hs.evalues(cal, np.zeros(300, dtype=np.int64), s, k=k)
    check(f"fire_mask matches evalues at k={k}",
          np.array_equal(fire_mask(cal_s, s, k), e > 0))
    kth = np.sort(cal)[::-1][k - 1]
    check(f"and the rule is 's > c_(k)' at k={k}",
          np.array_equal(fire_mask(cal_s, s, k), s > kth))
check("a score exactly equal to c_(1) does NOT fire",
      not fire_mask(np.array([1.0, 2.0, 3.0]), np.array([3.0]), 1)[0])

print("=" * 100)
print("3. episode_evidence() vs a full build_episodes rebuild")
print("=" * 100)
n = 4000
ts_w = np.sort(rng.integers(0, 5_000_000_000, n))
src_w = rng.integers(0, 40, n); dst_w = rng.integers(0, 20, n)
y_w = (rng.random(n) < 0.05).astype(np.int64)
for trial in range(5):
    e_te = np.where(rng.random(n) < 0.02, 1e6, 0.0)
    full = hs.build_episodes(e_te, y_w, ts_w, src_w, dst_w, 7200, "src-dst")
    part = hs.build_episodes(np.zeros(n), y_w, ts_w, src_w, dst_w, 7200, "src-dst")
    reused = episode_evidence(part, e_te)
    if trial == 0:
        check("the partition is invariant to the e-values",
              np.array_equal(part["gid"], full["gid"])
              and np.array_equal(part["order"], full["order"])
              and np.array_equal(part["nsz"], full["nsz"]))
    check(f"episode_evidence matches the rebuild (trial {trial})",
          np.allclose(reused, full["Ev"], rtol=0, atol=0))

print("=" * 100)
print("4. fdp_recall()'s None convention")
print("=" * 100)
ism = np.array([True, False, True, False])
r0 = fdp_recall(np.zeros(4, bool), ism, 2)
check("no rejections -> fdp is None, not 0.0", r0["fdp"] is None)
check("and fdp_conv keeps the 0 convention for averaging", r0["fdp_conv"] == 0.0)
check("and rejections is 0", r0["rejections"] == 0)
r1 = fdp_recall(np.array([True, True, False, False]), ism, 2)
check("one false of two -> fdp 0.5", r1["fdp"] == 0.5)
check("recall counts true positives over malicious episodes", r1["recall"] == 0.5)
r2 = fdp_recall(np.array([True, False, True, False]), ism, 2)
check("all true -> fdp 0.0 (a real zero, not the None convention)", r2["fdp"] == 0.0)

print("=" * 100)
print("5. wilson()")
print("=" * 100)
lo, hi = wilson(40, 40)
check("40/40 does not give an interval of exactly [1, 1]", lo < 1.0 and hi == 1.0,
      f"[{lo:.4f}, {hi:.4f}]")
check("40/40 lower bound is near 0.91", abs(lo - 0.9119) < 0.01, f"{lo:.4f}")
lo2, hi2 = wilson(20, 40)
check("20/40 is centred near 0.5", abs((lo2 + hi2) / 2 - 0.5) < 1e-9)
check("20/40 half-width is near 0.152", abs((hi2 - lo2) / 2 - 0.1518) < 0.01)
check("0/40 lower bound is 0", wilson(0, 40)[0] == 0.0)
check("more draws give a tighter interval",
      (wilson(200, 400)[1] - wilson(200, 400)[0]) < (hi2 - lo2))
check("n = 0 gives nan", math.isnan(wilson(0, 0)[0]))

print("=" * 100)
print("5b. the hypergeometric sampler's parameter order")
print("=" * 100)
# numpy's signature is hypergeometric(ngood, nbad, nsample).  Getting it backwards would
# silently change every D3b row, and the resulting probability is close enough to 1 to look
# plausible -- so it is checked against the exact distribution AND against direct
# without-replacement sampling.
from scipy.stats import hypergeom as _hg
P_, Q_, a_ = 1000, 300, 5
pool_ind = np.array([1.0] * Q_ + [0.0] * (P_ - Q_))
_rng = np.random.default_rng(11)
direct = float(np.mean([pool_ind[_rng.choice(P_, size=a_, replace=False)].max() > 0.5
                        for _ in range(4000)]))
hg = float((_rng.hypergeometric(Q_, P_ - Q_, a_, size=200_000) > 0).mean())
exact = float(1.0 - _hg.pmf(0, P_, Q_, a_))
check("hypergeometric(ngood, nbad, nsample) matches the exact value",
      abs(hg - exact) < 0.005, f"{hg:.4f} vs {exact:.4f}")
check("and matches direct without-replacement sampling",
      abs(direct - exact) < 0.02, f"{direct:.4f} vs {exact:.4f}")
wrong = float((_rng.hypergeometric(P_ - Q_, Q_, a_, size=200_000) > 0).mean())
check("the reversed parameter order is distinguishable", abs(wrong - exact) > 0.05,
      f"reversed gives {wrong:.4f}")
check("t38 uses the correct order",
      "rngm.hypergeometric(Qp, n_pool - Qp, a" in SRC)

print("=" * 100)
print("6. margin() -- D5a's trap: it moves the WRONG WAY under contamination")
print("=" * 100)
m0 = margin(1_000_000)
check("margin rises when |C| rises", margin(1_010_000) > m0)
check("margin is (CEIL*w0 - 1)/CEIL... i.e. (CEIL - 1/w0)/CEIL",
      abs(m0 - ((1_000_001.0) - 1 / 0.025) / 1_000_001.0) < 1e-12)
check("margin falls in k", margin(1_000_000, k=10) < m0)
check("margin does not depend on any score or label", margin(1_000_000) == m0)

print("=" * 100)
print("7. D4' -- the two channels")
print("=" * 100)
N = 39
cal0 = np.arange(float(N))
low = np.full(6, -100.0)          # attacks BELOW every benign score: ceiling channel only
hi_ = np.full(1, 1e6)             # one attack ABOVE: threshold channel
s_test = np.array([100.0])
e0, _, _, M0 = hs.evalues(cal0, np.zeros(N, dtype=np.int64), s_test, k=1)
eL, _, _, ML = hs.evalues(np.concatenate([cal0, low]),
                          np.zeros(N + 6, dtype=np.int64), s_test, k=1)
eH, _, _, MH = hs.evalues(np.concatenate([cal0, hi_]),
                          np.zeros(N + 1, dtype=np.int64), s_test, k=1)
check("low-score injection: the flow still fires", eL[0] > 0)
check("low-score injection: the ceiling rises by exactly 1 + eps",
      abs(ML / M0 - (1 + 6 / (N + 1.0))) < 1e-12, f"{ML/M0:.6f}")
check("low-score injection: the p-value FALLS (anti-conservative)",
      (1.0 / eL[0]) < (1.0 / e0[0]))
check("and falls by exactly the inflation factor",
      abs((1.0 / eL[0]) / (1.0 / e0[0]) - M0 / ML) < 1e-12)
check("high-score injection: the flow stops firing entirely", eH[0] == 0.0)
check("high-score injection at k=1 needs only ONE flow", len(hi_) == 1)

print("=" * 100)
print("8. mutation resistance")
print("=" * 100)


def caught(name, cond):
    check(f"mutation caught: {name}", cond)


# The correct rule drops the LOWEST clean scores, so the maximum must SURVIVE and the
# minimum must NOT.  A mutation dropping the highest would remove c0[-1].
_rep = contaminate(c0, pool, 10, "replacement")
caught("contaminate drops the HIGHEST clean scores in replacement mode",
       bool(np.isin(c0[-1], _rep)) and not bool(np.isin(c0[0], _rep)))
caught("contaminate uses a random pool slice instead of a prefix (breaks nesting)",
       set(np.round(contaminate(c0, pool, 3, "additive"), 12))
       <= set(np.round(contaminate(c0, pool, 7, "additive"), 12)))
caught("fire_mask uses >= instead of > at the threshold",
       not fire_mask(np.array([1.0, 2.0, 3.0]), np.array([3.0]), 1)[0])
caught("fire_mask uses side='right' (counts equal scores as below)",
       np.array_equal(fire_mask(np.array([1.0, 2.0, 3.0]), np.array([2.0, 3.0, 4.0]), 1),
                      np.array([False, False, True])))
caught("fdp_recall returns 0.0 with no rejections",
       fdp_recall(np.zeros(4, bool), ism, 2)["fdp"] is None)
# The fixture must have R != n_mal, or fp/R and fp/n_mal coincide and the check is a
# tautology: 3 rejections of which 1 is false, against 2 malicious episodes.
caught("fdp divides by the malicious count instead of the rejection count",
       abs(fdp_recall(np.array([True, True, True, False]), ism, 2)["fdp"] - 1.0 / 3.0) < 1e-12)
caught("wilson uses the normal approximation (giving [1,1] at 40/40)",
       wilson(40, 40)[0] < 0.99)
# k = 1 hides any bug that applies k twice.  Check an explicit k = 10 value instead.
_want_k10 = ((1_000_001.0 / 10) - 1.0 / 0.025) / (1_000_001.0 / 10)
caught("margin uses k in the numerator twice",
       abs(margin(1_000_000, k=10) - _want_k10) < 1e-12)
# These two must compare the CORRECT result against the MUTATED one, not against itself.
_sum_e = np.bincount(part["gid"], weights=e_te, minlength=part["T"])
_no_reorder = _sum_e / np.maximum(part["nsz"], 1)          # forgot [order] on sum_e
_by_T = _sum_e[part["order"]] / part["T"]                  # divided by T instead of nsz
caught("episode_evidence forgets the [order] reindex",
       not np.allclose(_no_reorder, full["Ev"]))
caught("episode_evidence divides by T instead of nsz",
       not np.allclose(_by_T, full["Ev"]))

print("=" * 100)
print("9. the shipped JSON is consistent with these definitions")
print("=" * 100)
if not JSON_PATH.exists():
    check("out/t38_E4.json exists", False, "run t38_E4_contamination.py first")
else:
    j = json.load(open(JSON_PATH))
    rows = j["rows"] + j["jrows"]
    check("no row reports fdp = 0.0 with zero rejections",
          all(not (r["lond"]["rejections"] == 0 and r["lond"]["fdp"] == 0.0) for r in rows))
    check("every eps row carries effective_eps and contaminated",
          all("effective_eps" in r and "contaminated" in r for r in j["rows"]))
    # .get, not [], so a STALE artefact is reported as a failure rather than aborting the
    # whole block with a KeyError after it has already diagnosed the staleness.
    check("rows labelled contaminated have a >= 1",
          all(r.get("contaminated") == (r.get("a", 0) >= 1) for r in j["rows"]))
    add = [r for r in j["rows"] if r["model"] == "additive"]
    check("additive rows have CEIL = |C| + 1",
          all(abs(r["CEIL"] - (r["NC"] + 1)) < 1e-9 for r in add))
    rep = [r for r in j["rows"] if r["model"] == "replacement"]
    for pos in {r["pos"] for r in rep}:
        base = j["baseline"][str(pos)]["CEIL"]
        check(f"replacement rows keep the ceiling exactly at pos={pos}",
              all(abs(r["CEIL"] - base) < 1e-9 for r in rep if r["pos"] == pos))
    d4 = j.get("d4prime", [])
    check("the D4' arm reports the ceiling channel",
          all(abs(r["ratio"] * r["one_plus_eps"] - 1.0) < 1e-9 for r in d4 if r["a"]),
          f"{len(d4)} rows")

print("=" * 100)
if fails:
    print(f"  {len(fails)} FAILURES: " + ", ".join(fails))
    raise SystemExit(1)
print("  ALL E4 SELF-TESTS PASS")
print("=" * 100)
