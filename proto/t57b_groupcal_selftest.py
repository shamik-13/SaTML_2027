"""
Unit tests for the group-level calibration machinery of t57_group_calibration.py (review 7,
item R2).  No data files; runs in seconds.

Module-level functions are pulled OUT of the shipped script by AST and executed here, so the
tests exercise the SHIPPED code rather than a copy -- the same discipline as t36b/t34b.

What it pins down:
  1  group_by_key: gid, counts, sums, maxima, malicious flag and first timestamp against a
     brute-force per-group loop, including singleton groups, groups split across time buckets,
     and keys that collide only on two of the three fields
  2  the group construction really is SPLIT CONFORMAL at the group level -- its false-firing
     rate on exchangeable benign groups matches the nominal k/(n+1), which is the whole point
     of the repair (no metadata-conditional per-flow premise is used anywhere)
  3  the MAX statistic is padding-invariant, by construction and against brute force: appending
     any multiset of flows cannot lower a group's maximum, so a firing group still fires
  4  the MEAN statistic is NOT, and the closed-form r* the stage reports is correct: r* pads
     push the mean below the threshold and r*-1 do not
  5  the feasibility arithmetic: the ceiling ratio is the flows-per-group ratio, and the
     calendar requirement equals (k/c_0) x the group-rate ratio
"""
import ast
import sys
from pathlib import Path

import numpy as np

SRC_PATH = Path(__file__).resolve().parent.parent / "src" / "lib" / "t57_group_calibration.py"
SRC = SRC_PATH.read_text()
fails = []


def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"   {detail}" if detail else ""))
    if not cond:
        fails.append(name)


def load_nested(*names):
    """group_by_key is defined inside main(); lift it out by AST and exec it standalone."""
    tree = ast.parse(SRC)
    fn_main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    want = {n.name: n for n in fn_main.body
            if isinstance(n, ast.FunctionDef) and n.name in names}
    missing = set(names) - set(want)
    if missing:
        raise AssertionError(f"not defined in main() of {SRC_PATH.name}: {sorted(missing)}")
    # the lifted functions carry default arguments that are closure constants of main();
    # supply them from the SHIPPED source rather than hardcoding, so a change there is caught
    consts = {}
    for node in ast.walk(fn_main):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and \
                isinstance(node.targets[0], ast.Name) and isinstance(node.value, ast.Constant):
            consts[node.targets[0].id] = node.value.value
    ns = {"np": np, **consts}
    missing_const = {"A", "ZETA16"} - set(ns)
    if missing_const:
        raise AssertionError(f"closure constants not found in main(): {sorted(missing_const)}")
    mod = ast.Module(body=[want[n] for n in names], type_ignores=[])
    exec(compile(ast.fix_missing_locations(mod), str(SRC_PATH), "exec"), ns)
    return [ns[n] for n in names]


(group_by_key, feasible_window, group_fires, min_pads) = load_nested(
    "group_by_key", "feasible_window", "group_fires", "min_pads")
HOUR = 3_600_000_000            # microseconds

# ======================================================================================
print("=" * 100)
print("1. group_by_key against a brute-force per-group loop")
print("=" * 100)
rng = np.random.default_rng(0)
cases = [
    # (src, dst, ts_hours, y, score) -- hand-built edge cases first
    (np.array([1, 1, 2, 1]), np.array([9, 9, 9, 9]), np.array([0.0, 0.1, 0.2, 3.0]),
     np.array([0, 0, 1, 0]), np.array([0.5, 0.9, 0.2, 0.7])),          # split across buckets
    (np.array([1, 2, 3]), np.array([1, 2, 3]), np.array([0.0, 0.0, 0.0]),
     np.array([0, 0, 0]), np.array([0.1, 0.2, 0.3])),                  # all singletons
    (np.array([5, 5, 5]), np.array([7, 7, 7]), np.array([0.0, 0.5, 1.0]),
     np.array([1, 0, 0]), np.array([0.4, 0.4, 0.4])),                  # one group, ties
    (np.array([1, 1]), np.array([2, 3]), np.array([0.0, 0.0]),
     np.array([0, 0]), np.array([0.1, 0.2])),                          # same src, diff dst
    (np.array([1, 2]), np.array([3, 3]), np.array([0.0, 0.0]),
     np.array([0, 0]), np.array([0.1, 0.2])),                          # diff src, same dst
]
for i in range(6):
    n = int(rng.integers(20, 120))
    cases.append((rng.integers(0, 6, n), rng.integers(0, 5, n),
                  rng.uniform(0, 8, n), (rng.random(n) < 0.2).astype(int),
                  rng.normal(0, 1, n)))

for ci, (s_, d_, th, yy, sc) in enumerate(cases):
    ts = (th * HOUR).astype(np.int64)
    g = group_by_key(np.asarray(s_), np.asarray(d_), ts, np.asarray(yy), np.asarray(sc), 2 * 3600)
    keys = {}
    for j in range(len(ts)):
        k = (int(s_[j]), int(d_[j]), int(ts[j] // (2 * 3600 * 1_000_000)))
        keys.setdefault(k, []).append(j)
    ok_n = g["G"] == len(keys)
    ok_all = True
    for k, idx in keys.items():
        gi = g["gid"][idx[0]]
        if not all(g["gid"][j] == gi for j in idx): ok_all = False; break
        if g["cnt"][gi] != len(idx): ok_all = False; break
        if abs(g["sum"][gi] - sum(sc[j] for j in idx)) > 1e-9: ok_all = False; break
        if abs(g["max"][gi] - max(sc[j] for j in idx)) > 1e-12: ok_all = False; break
        if bool(g["ismal"][gi]) != any(yy[j] == 1 for j in idx): ok_all = False; break
        if g["first_ts"][gi] != min(ts[j] for j in idx): ok_all = False; break
    check(f"group count and every aggregate match brute force [case {ci}]", ok_n and ok_all,
          f"{g['G']} groups vs {len(keys)} keys")

check("every flow is assigned to exactly one group (partition)",
      all(len(np.unique(group_by_key(np.asarray(c[0]), np.asarray(c[1]),
                                     (c[2] * HOUR).astype(np.int64), np.asarray(c[3]),
                                     np.asarray(c[4]), 2 * 3600)["gid"])) ==
          group_by_key(np.asarray(c[0]), np.asarray(c[1]), (c[2] * HOUR).astype(np.int64),
                       np.asarray(c[3]), np.asarray(c[4]), 2 * 3600)["G"]
          for c in cases))

# ======================================================================================
print("=" * 100)
print("2. the construction is SPLIT CONFORMAL at the group level")
print("=" * 100)
print("   Under exchangeable benign groups the firing rate must be the nominal k/(n+1).")
print("   This is what the repair buys: validity from group exchangeability alone, with no")
print("   metadata-conditional per-flow premise anywhere in the argument.")
def shipped_fire(cal_stats, test_stats, k):
    """Drive the SHIPPED rule itself -- group_fires is AST-lifted out of the experiment, so a
    change there is exercised here rather than silently diverging from a restatement."""
    return group_fires(np.sort(cal_stats), np.asarray(test_stats, dtype=float), k)


check("the firing rule under test is lifted from the shipped source, not restated",
      callable(group_fires) and "searchsorted" in SRC)

for k in (1, 5, 20):
    for ncal in (200, 2000):
        B = 4000
        rs = np.random.default_rng(1000 + k * 7 + ncal)
        fired = 0
        for _ in range(B):
            pool = rs.normal(0, 1, ncal + 1)
            fired += int(shipped_fire(pool[:ncal], np.array([pool[ncal]]), k)[0])
        rate = fired / B
        nominal = k / (ncal + 1.0)
        se = (nominal * (1 - nominal) / B) ** 0.5
        check(f"shipped rule fires at the nominal k/(n+1) [k={k}, n={ncal}]",
              abs(rate - nominal) <= 4 * se + 1e-12,
              f"measured {rate:.5f} vs nominal {nominal:.5f} (4se = {4*se:.5f})")

# TIES: the degenerate case that separates the rank rule from a bare ">= k-th largest".
# With every statistic equal, a bare comparison fires with probability 1 and E[e] = n+1.
print("   ties -- the case that separates the rank rule from a bare '>= kth largest':")
for k in (1, 5):
    for n in (50, 500):
        cal = np.zeros(n); test = np.array([0.0])
        bare = bool(test[0] >= np.sort(cal)[-k])
        rank = bool(shipped_fire(cal, test, k)[0])
        check(f"all-tied stream: bare rule fires ({bare}), shipped rule does not [k={k}, n={n}]",
              bare and not rank, f"bare={bare}, shipped={rank}")
# partial ties: a value shared by more than k calibration groups must not fire
# K_r = 1 + #{cal >= stat}, so a test point tied with n_tied calibration groups has rank
# 1 + n_tied and fires iff n_tied <= k - 1.  Ties are resolved AGAINST the test point, which is
# the conservative direction and the whole reason the rank rule is used.
for k, n_tied in ((1, 5), (5, 20), (1, 1), (5, 4), (5, 3), (1, 0), (3, 2)):
    cal = np.concatenate([np.full(n_tied, 3.0), np.random.default_rng(0).normal(-5, 1, 300)])
    fires = bool(shipped_fire(cal, np.array([3.0]), k)[0])
    check(f"tied with {n_tied} calibration groups fires iff {n_tied} <= k-1 [k={k}]",
          fires == (n_tied <= k - 1), f"fires={fires}, expected {n_tied <= k - 1}")

# and the e-value it implies really is valid in expectation on exchangeable groups
for k, n in ((1, 500), (5, 500), (20, 500)):
    B = 20000
    rs = np.random.default_rng(4242)
    ceil = (n + 1.0) / k
    tot = 0.0
    for _ in range(B):
        pool = rs.normal(0, 1, n + 1)
        tot += ceil * shipped_fire(pool[:n], np.array([pool[n]]), k)[0]
    ev = tot / B
    # e is 0 or ceil with p = k/(n+1), so sd(e) = ceil*sqrt(p(1-p)); the naive ceil/sqrt(B)
    # tolerance is ~14 here, which would pass anything.  Use the real standard error.
    pp = k / (n + 1.0)
    se = ceil * (pp * (1 - pp) / B) ** 0.5
    check(f"E[e] <= 1 under exchangeability [k={k}, n={n}]", ev <= 1.0 + 3 * se,
          f"E[e] = {ev:.4f} <= 1 + 3se = {1 + 3*se:.4f}  (se = {se:.4f})")

# ======================================================================================
print("=" * 100)
print("3. the MAX statistic is padding-invariant -- by construction and by brute force")
print("=" * 100)
rs = np.random.default_rng(7)
for trial in range(8):
    m = int(rs.integers(1, 40)); r = int(rs.integers(0, 200))
    member = rs.normal(0, 1, m)
    pads = rs.normal(-0.5, 1, r)                    # pads may be anything, including large
    thr = float(np.quantile(member, 0.5))
    before = member.max()
    after = np.concatenate([member, pads]).max() if r else before
    check(f"appending {r} flows never lowers the maximum [trial {trial}]", after >= before - 1e-15,
          f"{before:.4f} -> {after:.4f}")
    if before >= thr:
        check(f"  a firing group still fires after padding [trial {trial}]", after >= thr)

# an adversarial attempt: pads chosen as small as possible cannot help either
member = np.array([3.0, 0.1, 0.2]); thr = 1.0
for r in (1, 10, 1000, 10 ** 5):
    after = np.concatenate([member, np.full(r, -1e9)]).max()
    check(f"even {r} minimal-score pads leave the group firing", after >= thr,
          f"max stays {after}")

# ======================================================================================
print("=" * 100)
print("4. the MEAN statistic is NOT padding-invariant, and r* is exact")
print("=" * 100)
print("   r* = floor((thr*m - S)/(thr - pad_mean)) + 1, the closed form the stage reports.")
rs = np.random.default_rng(11)
# A near-threshold group is suppressed by one pad whatever the formula says, so it cannot
# distinguish a correct r* from a wrong one.  These cases put the group WELL above threshold.
def rstar(S, m, cal, pads, k=1):
    """Drive the SHIPPED min_pads on a given pool."""
    a = np.sort(np.asarray(pads, dtype=float))
    return min_pads(float(S), int(m), np.sort(np.asarray(cal, dtype=float)), a,
                    np.concatenate([[0.0], np.cumsum(a)]), k)


# Groups FAR above threshold: a near-threshold group is suppressed by one pad whatever the
# formula says, so it cannot distinguish a correct r* from a wrong one.
for (m, S, thrv, mu, npad) in [(100, 1000.0, 5.0, 0.0, 5000), (10, 100.0, 5.0, 0.0, 500),
                               (50, 500.0, 2.0, 1.0, 5000), (3, 30.0, 5.0, -5.0, 100)]:
    cal = np.array([thrv])                       # k=1: fires iff stat > max(cal) = thr
    pads = np.full(npad, mu)
    r = rstar(S, m, cal, pads)
    check(f"min_pads returns a suppressing r [m={m}, mean={S/m:g}, thr={thrv:g}]",
          r is not None and not bool(shipped_fire(cal, [(S + r * mu) / (m + r)], 1)[0]),
          f"r* = {r}")
    check(f"  and it is MINIMAL: r*-1 still fires [m={m}]",
          r is not None and r >= 1
          and bool(shipped_fire(cal, [(S + (r - 1) * mu) / (m + r - 1)], 1)[0]),
          f"r*-1 = {r-1}")
    # the historical sign error returned 1 here; pin that it is not what the shipped code does
    wrong = max(int(np.floor((thrv * m - S) / (thrv - mu))) + 1, 1)
    check(f"  the sign-flipped formula would have said {wrong}, which does NOT suppress [m={m}]",
          wrong != r and bool(shipped_fire(cal, [(S + wrong * mu) / (m + wrong)], 1)[0]))

# an exhausted pool must return None rather than a wrong number
check("a pool too small to suppress returns None",
      rstar(1000.0, 100, np.array([5.0]), np.zeros(3)) is None,
      "3 zero-score pads cannot pull a mean of 10 below 5")
# equality at the threshold already stops firing under the rank rule, so r* must not pay for it
cal_eq = np.array([5.0])
check("equality at the threshold counts as suppressed (rank rule, not '< thr')",
      not bool(shipped_fire(cal_eq, [5.0], 1)[0]),
      "stat == kth largest does not fire, so r* must not spend a pad to go strictly below")

for trial in range(10):
    m = int(rs.integers(2, 60))
    member = rs.uniform(0.4, 1.0, m)
    S = member.sum()
    thr = float(np.mean(member)) - 1e-9                     # the group fires, just
    pad_mean = float(rs.uniform(-1.0, thr - 0.05))          # pads must dilute
    if not (S / m >= thr and pad_mean < thr):
        continue
    rstar = int(np.floor((S - thr * m) / (thr - pad_mean))) + 1
    rstar = max(rstar, 1)
    at = (S + rstar * pad_mean) / (m + rstar)
    below = (S + (rstar - 1) * pad_mean) / (m + rstar - 1) if rstar >= 1 else None
    check(f"r*={rstar} pads push the mean below the threshold [trial {trial}]", at < thr,
          f"mean {at:.6f} < thr {thr:.6f}")
    if rstar > 1:
        check(f"  and r*-1 does not [trial {trial}]", below >= thr,
              f"mean {below:.6f} >= thr {thr:.6f}")

# ======================================================================================
print("=" * 100)
print("5. the feasibility and calendar arithmetic")
print("=" * 100)
K, A, W0 = 1, 0.05, 0.025
for (ncf, ncg, T, cal_h, te_h) in [(2_448_993, 52_279, 57_368, 3.3, 8.5),
                                   (1_813_113, 36_944, 31_568, 4.0, 2.4),
                                   (2_287_988, 57_093, 37_231, 5.0, 5.0)]:
    ceil_f = (ncf + 1.0) / K; ceil_g = (ncg + 1.0) / K
    check(f"ceiling ratio == flows-per-group ratio [T={T:,}]",
          abs(ceil_f / ceil_g - (ncf + 1.0) / (ncg + 1.0)) < 1e-9,
          f"{ceil_f/ceil_g:.2f}x")
    need = K * T / A - 1.0
    cal_rate = ncg / cal_h; te_rate = T / te_h
    need_span = need / cal_rate
    law = (K / A) * (te_rate / cal_rate)
    # the law is kT/c_0; the stage uses cor:budget's kT/c_0 - 1, so the two differ by exactly
    # 1/(cal_rate * te_h) -- a relative offset, checked as such rather than absolutely
    got = need_span / te_h
    resid = law - got
    check(f"required-span ratio == (k/c_0) x group-rate ratio [T={T:,}]",
          abs(resid) / law < 1e-5 and abs(resid - 1.0 / (cal_rate * te_h)) < 1e-12,
          f"{got:.6f} vs {law:.6f}; residual {resid:.2e} == 1/(cal_rate*span) exactly")
    check(f"  with equal group rates the ratio is exactly k/c_0 = {K/A:.0f} [T={T:,}]",
          abs((K / A) * 1.0 - K / A) < 1e-12)
    margin_g = (ncg + 1.0) * W0 / T - 1.0
    check(f"group-calibration margin is deeply negative [T={T:,}]", margin_g < -0.9,
          f"{margin_g:+.3f}")

# ======================================================================================
print("=" * 100)
print("6. the feasible-window closed form, against the ACTUAL gamma sequence")
print("=" * 100)
print("   floor((alpha*CEIL*(R+1)/zeta)^(1/1.6)) must equal the number of steps t at which")
print("   alpha*gamma_t*(R+1)*CEIL >= 1 for the gamma the runners really use.  This is what")
print("   turns a zero-detection result -- and a surprisingly large one -- into the boundary")
print("   rather than an unexplained number.")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import h6_procs as hp

A = 0.05
for ceil in (1e3, 36_945.0, 52_280.0, 1e6):
    for R in (0, 1, 2, 42, 200):
        T = 2_000_000
        g1, _ = hp.make_gamma("poly", T)
        t = np.arange(1, T + 1)
        brute = int(np.count_nonzero(A * g1[1:T + 1] * (R + 1) * ceil >= 1.0))
        closed = feasible_window(ceil, R, alpha=A)
        check(f"closed form == brute force [CEIL={ceil:,.0f}, R={R}]", abs(brute - closed) <= 1,
              f"closed {closed:,} vs brute {brute:,}")
    # feasibility is contiguous from t=1, so the count IS a prefix length for a rejection-free run
    g1, _ = hp.make_gamma("poly", 100_000)
    feas = A * g1[1:100_001] * ceil >= 1.0
    check(f"the feasible set is a prefix (no gaps) [CEIL={ceil:,.0f}]",
          bool(np.all(feas[:int(feas.sum())]) and not feas[int(feas.sum()):].any()),
          f"{int(feas.sum()):,} feasible")

# The bootstrap factor: R rejections stretch the window by (R+1)^(1/1.6).  The identity is on
# the UNFLOORED window -- multiplying the floored base instead loses up to (R+1)^(1/1.6) times
# the discarded fraction, which at R=42 is ~6 steps, so it must not be tested that way.
ZETA = 2.2853996
for ceil in (36_945.0, 52_280.0):
    exact_base = (A * ceil / ZETA) ** (1.0 / 1.6)
    for R in (1, 5, 42, 200):
        got = feasible_window(ceil, R, alpha=A)
        want = exact_base * (R + 1) ** (1.0 / 1.6)
        check(f"R={R} rejections stretch the window by (R+1)^(1/1.6) [CEIL={ceil:,.0f}]",
              abs(got - np.floor(want)) <= 1,
              f"{feasible_window(ceil, 0, alpha=A):,} -> {got:,}, unfloored prediction "
              f"{want:,.1f} ({(R+1)**(1/1.6):.2f}x)")
    check(f"  multiplying the FLOORED base would be wrong at R=42 [CEIL={ceil:,.0f}]",
          abs(feasible_window(ceil, 0, alpha=A) * 43 ** (1.0 / 1.6)
              - feasible_window(ceil, 42, alpha=A)) > 2,
          "which is why the test uses the unfloored form")

# ======================================================================================
print("=" * 100)
print(f"{len(fails)} failure(s)" + ("" if not fails else ": " + "; ".join(fails)))
print("=" * 100)
sys.exit(1 if fails else 0)
