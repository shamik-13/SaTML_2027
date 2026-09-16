"""
Unit tests for the E3 machinery (t36_E3_asymmetric.py, t36a_E3_derivation.py).  No data
files; runs in a second, so it can be re-run after any edit.

Module-level functions are pulled OUT of t36_E3_asymmetric.py by AST and executed here, so
the tests exercise the SHIPPED code rather than a copy.  An adversarial audit showed that
four deliberate defects -- a dropped `[order]`, a 0-based within-episode rank, last-only
silently becoming first-only, and a broken prior-port base term -- passed the script's own
checks, which is why this file exists.

What it pins down:
  1  within_episode_rank against a brute-force per-episode loop, including singleton groups,
     the last group, and non-contiguous gids
  2  merged_evidence's group-id -> episode-order pairing, and each scheme's own branch
  3  last-only really is the LAST arriving flow, and really is not padding-invariant
  4  the prior-port within-episode high-risk rank, including a group whose first flow is
     itself high-risk
  5  frontload_cost against brute force, and against the analytic closed forms
  6  weight_sequence sums to <= 1 and is non-increasing where it should be
"""
import numpy as np, ast, sys
from pathlib import Path

SRC_PATH = Path(__file__).with_name("t36_E3_asymmetric.py")
SRC = SRC_PATH.read_text()
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
    ns = {"np": np, "N_SUPPORT": 100_000}
    mod = ast.Module(body=[want[n] for n in names], type_ignores=[])
    exec(compile(ast.fix_missing_locations(mod), str(SRC_PATH), "exec"), ns)
    return [ns[n] for n in names]


(weight_sequence, frontload_cost, frontload_cost_analytic, within_episode_rank,
 merged_evidence) = load_module_level(
    "weight_sequence", "frontload_cost", "frontload_cost_analytic",
    "within_episode_rank", "merged_evidence")

# ======================================================================================
print("=" * 100)
print("1. within_episode_rank against brute force")
print("=" * 100)
rng = np.random.default_rng(0)
for trial, gid in enumerate([
        np.array([0, 0, 1, 0, 2, 1, 1, 2]),                 # interleaved
        np.array([0, 1, 2, 3, 4]),                           # all singletons
        np.array([0, 0, 0, 0]),                              # one group
        np.unique(rng.integers(0, 40, 300), return_inverse=True)[1]]):
    n = len(gid)
    rank, nsz = within_episode_rank(gid, n)
    brute = np.zeros(n, dtype=np.int64)
    seen = {}
    for i, g in enumerate(gid):          # flows arrive in stream order
        seen[g] = seen.get(g, 0) + 1
        brute[i] = seen[g]
    check(f"rank matches brute force [case {trial}]", np.array_equal(rank, brute),
          f"n={n}, T={int(gid.max())+1}")
    check(f"rank is 1-BASED (min == 1) [case {trial}]", int(rank.min()) == 1)
    check(f"nsz matches bincount [case {trial}]",
          np.array_equal(nsz, np.bincount(gid, minlength=int(gid.max()) + 1)))
    check(f"each group's ranks are exactly 1..m [case {trial}]",
          all(sorted(rank[gid == g].tolist()) == list(range(1, int((gid == g).sum()) + 1))
              for g in np.unique(gid)))
# a 0-based rank would be a different array
rank, _ = within_episode_rank(np.array([0, 0, 1]), 3)
check("a 0-based rank would differ (so the base matters)",
      not np.array_equal(rank, rank - 1))

# ======================================================================================
print("\n" + "=" * 100)
print("2. merged_evidence: pairing, and each scheme's own branch")
print("=" * 100)
gid = np.array([0, 0, 0, 1, 1, 2])
n, T = len(gid), 3
M = 1000.0
e = np.array([M, 0.0, M, 0.0, M, M])
rank, nsz = within_episode_rank(gid, n)
order = np.array([2, 0, 1])                       # a deliberately non-identity ordering
hi_rank = np.array([1, 0, 2, 0, 1, 1])

F, wf = merged_evidence("first-only", e, gid, rank, nsz, T)
check("first-only counts only position 1 of each episode",
      np.allclose(F, [M, 0.0, M]), f"F={F.tolist()}")
check("first-only weights: exactly the rank-1 flows carry 1.0",
      np.allclose(wf, (rank == 1).astype(float)))

F, wf = merged_evidence("last-only", e, gid, rank, nsz, T)
check("last-only counts only the LAST arriving flow of each episode",
      np.allclose(F, [M, M, M]), f"F={F.tolist()}")
check("last-only is NOT the same as first-only on this input",
      not np.allclose(F, merged_evidence("first-only", e, gid, rank, nsz, T)[0]),
      "a mutation swapping the two must fail here")
check("last-only weights: exactly the rank-m flows carry 1.0",
      np.allclose(wf, (rank == nsz[gid]).astype(float)))

F, wf = merged_evidence("uniform-m0", e, gid, rank, nsz, T, m0=2)
check("uniform-m0 counts the first m0 positions at 1/m0",
      np.allclose(F, [M / 2, M / 2, M / 2]), f"F={F.tolist()}")
F, wf = merged_evidence("exp-decay", e, gid, rank, nsz, T, rho=0.5)
check("exp-decay weights fall geometrically by position",
      np.allclose(F, [0.5 * M + 0.125 * M, 0.25 * M, 0.5 * M]), f"F={F.tolist()}")

# the [order] pairing: merged_evidence returns GROUP-ID order, the caller applies [order]
F, _ = merged_evidence("first-only", e, gid, rank, nsz, T)
check("merged_evidence returns GROUP-ID order (F[g] belongs to group g)",
      np.isclose(F[0], M) and np.isclose(F[1], 0.0) and np.isclose(F[2], M))
check("applying [order] permutes it (so a dropped [order] is a different array)",
      not np.allclose(F[order], F), f"F={F.tolist()} F[order]={F[order].tolist()}")

# ======================================================================================
print("\n" + "=" * 100)
print("3. last-only is not padding-invariant; the position schemes are")
print("=" * 100)
# append one zero-evidence flow to episode 0 and recompute through the SHIPPED function
gid2 = np.concatenate([gid, [0]])
e2 = np.concatenate([e, [0.0]])
rank2, nsz2 = within_episode_rank(gid2, len(gid2))
for scheme, kw in (("first-only", {}), ("uniform-m0", dict(m0=2)),
                   ("exp-decay", dict(rho=0.5))):
    F0, _ = merged_evidence(scheme, e, gid, rank, nsz, T, **kw)
    F1, _ = merged_evidence(scheme, e2, gid2, rank2, nsz2, T, **kw)
    check(f"{scheme} is padding-invariant for episode 0", np.isclose(F0[0], F1[0]),
          f"{F0[0]:.1f} -> {F1[0]:.1f}")
F0, _ = merged_evidence("last-only", e, gid, rank, nsz, T)
F1, _ = merged_evidence("last-only", e2, gid2, rank2, nsz2, T)
check("last-only is DESTROYED by a single appended zero", not np.isclose(F0[0], F1[0]),
      f"{F0[0]:.1f} -> {F1[0]:.1f}")

# ======================================================================================
print("\n" + "=" * 100)
print("4. prior-port within-episode high-risk rank")
print("=" * 100)
F, wf = merged_evidence("prior-port", e, gid, rank, nsz, T, hi_rank=hi_rank, n_hi=2)
check("prior-port counts the first n_hi high-risk flows at 1/n_hi",
      np.allclose(wf, np.where((hi_rank > 0) & (hi_rank <= 2), 0.5, 0.0)),
      f"wf={wf.tolist()}")
check("prior-port ignores non-high-risk flows entirely",
      np.allclose(wf[hi_rank == 0], 0.0))
# The cap must BIND: an episode with MORE than n_hi high-risk flows must have the surplus
# ignored, or the weights exceed 1/episode and validity is lost.  Without a case like this
# a mutation that drops the cap changes nothing and passes.
gid_c = np.array([0, 0, 0, 0, 0])
rank_c, nsz_c = within_episode_rank(gid_c, 5)
hi_c = np.array([1, 2, 3, 4, 5])
e_c = np.full(5, M)
Fc, wfc = merged_evidence("prior-port", e_c, gid_c, rank_c, nsz_c, 1, hi_rank=hi_c, n_hi=2)
check("prior-port CAPS at n_hi: high-risk flows beyond the cap carry zero weight",
      np.allclose(wfc, [0.5, 0.5, 0.0, 0.0, 0.0]), f"wf={wfc.tolist()}")
check("prior-port total weight in an episode never exceeds 1 (validity)",
      float(wfc.sum()) <= 1.0 + 1e-12, f"sum={wfc.sum()}")
check("prior-port merged evidence is capped at M, not 2.5*M",
      np.isclose(Fc[0], M), f"F={Fc[0]:.1f}")
# reproduce the driver's hi_rank construction and check it against brute force, including a
# group whose FIRST flow is high risk (the base term the audit flagged)
for is_hi in (np.array([1, 0, 1, 0, 1, 1], dtype=np.int64),
              np.array([1, 1, 1, 1, 1, 1], dtype=np.int64),
              np.array([0, 0, 0, 0, 0, 0], dtype=np.int64)):
    srt = np.argsort(gid, kind='stable')
    hi_sorted = is_hi[srt]
    starts = np.concatenate(([0], np.cumsum(nsz)[:-1]))
    csum = np.cumsum(hi_sorted)
    base = np.repeat(csum[starts] - hi_sorted[starts], nsz)
    hr_sorted = np.where(hi_sorted > 0, csum - base, 0)
    got = np.empty(len(gid), dtype=np.int64); got[srt] = hr_sorted
    brute = np.zeros(len(gid), dtype=np.int64); seen = {}
    for i, g in enumerate(gid):
        if is_hi[i]:
            seen[g] = seen.get(g, 0) + 1
            brute[i] = seen[g]
    check(f"hi_rank matches brute force [{is_hi.tolist()}]", np.array_equal(got, brute),
          f"got={got.tolist()}")

# ======================================================================================
print("\n" + "=" * 100)
print("5. frontload_cost against brute force and the analytic closed forms")
print("=" * 100)
def L_brute(w, beta):
    for L in range(0, len(w) + 1):
        if w[L:].sum() < beta:
            return L
    return len(w)

bad = 0
for _ in range(2000):
    m = int(rng.integers(1, 120))
    w = rng.random(m) ** 3
    if rng.random() < 0.5:
        w = np.sort(w)[::-1]
    w /= w.sum()
    beta = float(10 ** rng.uniform(-4, 0.2))
    if frontload_cost(w, beta) != L_brute(w, beta):
        bad += 1
check("frontload_cost == brute force over 2000 random (w, beta)", bad == 0, f"{bad} mismatches")
try:
    frontload_cost(np.array([1.0]), 0.0); ok = False
except ValueError:
    ok = True
check("frontload_cost rejects beta <= 0 rather than returning a meaningless value", ok)
check("frontload_cost is 0 when beta exceeds the whole budget",
      frontload_cost(np.array([0.5, 0.3]), 0.9) == 0)

for scheme, kw in (("first-only", {}), ("uniform-m0", dict(m0=10)),
                   ("uniform-m0", dict(m0=137)), ("exp-decay", dict(rho=0.5)),
                   ("exp-decay", dict(rho=0.99))):
    for beta in (1e-6, 1e-3, 0.01, 0.3, 0.9, 1.5):
        w = weight_sequence(scheme, 100_000, **kw)
        a = frontload_cost_analytic(scheme, kw, beta)
        b = frontload_cost(w, beta)
        check(f"analytic == array L* [{scheme}{kw}, beta={beta:g}]",
              a == b or b >= 100_000, f"analytic={a} array={b}")
        del w
# the exact-integer boundary, where ceil() and floor()+1 differ
w = weight_sequence("uniform-m0", 1000, m0=10)
check("uniform-m0 at an exact-integer boundary uses floor()+1, not ceil()",
      frontload_cost(w, 0.3) == 8 and frontload_cost_analytic("uniform-m0", dict(m0=10), 0.3) == 8,
      f"L*={frontload_cost(w, 0.3)} (ceil(10*0.7)=7 would be wrong)")

# ======================================================================================
print("\n" + "=" * 100)
print("6. weight_sequence")
print("=" * 100)
for scheme, kw in (("first-only", {}), ("uniform-m0", dict(m0=1)),
                   ("uniform-m0", dict(m0=1000)), ("exp-decay", dict(rho=0.5)),
                   ("exp-decay", dict(rho=0.999))):
    w = weight_sequence(scheme, 200_000, **kw)
    check(f"sum w <= 1 [{scheme}{kw}]", w.sum() <= 1.0 + 1e-12, f"sum={w.sum():.12f}")
    check(f"w >= 0 [{scheme}{kw}]", bool((w >= 0).all()))
    check(f"w is non-increasing [{scheme}{kw}]", bool(np.all(np.diff(w) <= 1e-18)))
    del w

print("\n" + "=" * 100)
print(f"{len(fails)} failures" if fails else "ALL PASS")
if fails:
    for f in fails: print("  FAILED: " + f)
print("=" * 100)
sys.exit(1 if fails else 0)
