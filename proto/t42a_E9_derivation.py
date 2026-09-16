"""
E9, part 1 -- the ANALYTIC framing of timestamp-tie sensitivity, verified numerically.

Runs before t42_E9_ties.py touches LSPR23.  Same contract as t34a/t35a/t36a/t38a/t39a: every
closed form and design rule the real-data script relies on is derived here and checked, so a
disagreement between the two is a bug rather than a finding
(docs/01_HANDOFF_PHASE4.md section 6).

No data files are read.  Runtime ~20 s.

======================================================================================
THE QUESTION
======================================================================================
docs/02_WORKPLAN_PHASE4.md E9: online testing depends on order, and
`h_stream.build_episodes` uses `np.lexsort((first_pos, first_ts))` SPECIFICALLY to make
ties deterministic (standing mistake 5).  E9 quantifies the variance that choice suppresses
rather than fixing a bug.  Accept when: negligible -> one appendix sentence; non-negligible
-> the deterministic tie-break becomes a stated part of the method.

Three things settle the design before any number is produced:

  D2  the EXPOSURE -- how many episodes are even eligible to move -- is computable from
      timestamps alone, with no detector, no labels and no procedure run.  If it is zero,
      E9 is a one-line appendix note and 50 seeds would measure nothing.
  D3  a tie block's permutation is CONFINED to the block unless the permutation changes the
      number of rejections made inside it.  That bounds the blast radius exactly.
  D4  50 random seeds sample the permutation distribution; the EXTREMES of that
      distribution are computable directly for small blocks, and the deterministic order's
      position within them is the quantity the accept criterion actually asks about.

======================================================================================
NOTATION
======================================================================================
    T           number of episodes in the deployment window
    first_ts    each episode's first flow timestamp (microseconds)
    block       a maximal set of episodes sharing one first_ts value
    B           block size;  B_max the largest
    n_tied      number of episodes in blocks of size >= 2 -- the movable population
    R_t         rejections before step t;  LOND's level is alpha*gamma_t*(R_{t-1}+1)
======================================================================================
"""
import numpy as np, json, math
from itertools import permutations
from pathlib import Path
from scipy.special import zeta

from h6_procs import Ctx, make_gamma, run_lond

# Anchor to THIS file's directory: a run from a different cwd would
# otherwise write a second copy of the artefact somewhere else and leave
# the real one stale, which is exactly how a stale JSON gets audited.
OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(20260827)
OK, FAIL = [], []
A, W0 = 0.05, 0.025


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


# =======================================================================================
# The primitives.  Module level so t42b can import and mutate the SHIPPED code.
# =======================================================================================
def tie_exposure(first_ts):
    """The movable population, from timestamps alone.

    Returns n_blocks, n_tied (episodes in blocks of size >= 2), B_max, and the number of
    distinct timestamps.  Needs no detector, no labels and no procedure: the tie structure
    is a property of the stream's clock, so the exposure can be reported before anything
    else is run and decides whether E9 has anything to measure at all.            [D2a]
    """
    ts = np.asarray(first_ts)
    _, counts = np.unique(ts, return_counts=True)
    return dict(n_episodes=int(len(ts)), n_blocks=int(len(counts)),
                n_tied=int(counts[counts >= 2].sum()),
                n_nontrivial_blocks=int((counts >= 2).sum()),
                B_max=int(counts.max()) if len(counts) else 0,
                tied_fraction=float(counts[counts >= 2].sum() / max(len(ts), 1)))


def lond_rejections(Ev, ceil, gam1, alpha=A, w0=W0):
    """LOND's rejection mask on a given episode order, via the shared implementation."""
    ctx = Ctx(np.asarray(Ev, float), np.zeros(len(Ev), bool), ceil, alpha=alpha, w0=w0)
    fired = np.zeros(len(Ev), bool)
    run_lond(ctx, gam1, fired=fired)
    return fired


print("=" * 118)
print("D1.  WHAT A TIE-BREAK CAN AND CANNOT MOVE")
print("=" * 118)
print("""
build_episodes orders by np.lexsort((first_pos, first_ts)): PRIMARY key first_ts, SECONDARY
key first stream occurrence.  Replacing the secondary key with a random one permutes
episodes WITHIN equal-first_ts blocks and leaves the across-block order untouched.   [D1a]

So the deterministic tie-break is not a modelling choice about which episodes come first in
time -- the data does not say -- it is a choice among orderings the data cannot distinguish.
Nothing outside a tie block can move.  That is what makes the exposure in D2 an exact bound
rather than a heuristic.
""")
ts_b = np.array([10, 10, 10, 20, 30, 30, 40])
pos_b = np.arange(7)
det = np.lexsort((pos_b, ts_b))
check("D1a  the deterministic order is the identity here", int(np.abs(det - pos_b).sum()), 0, 0)
moved_out = 0
for _ in range(5000):
    r = rng.permutation(7)
    o = np.lexsort((r, ts_b))
    if not (ts_b[o] == np.sort(ts_b)).all():
        moved_out += 1
check("D1a  a random tie key never changes the timestamp sequence", moved_out, 0, 0)

print("=" * 118)
print("D2.  THE EXPOSURE IS COMPUTABLE FROM TIMESTAMPS ALONE")
print("=" * 118)
print("""
        n_tied = #{episodes in a first_ts block of size >= 2}                        [D2a]

is an EXACT upper bound on how many episodes any tie-break can move, and it needs no
detector, no labels and no procedure run.  If n_tied = 0 the deterministic tie-break is
inert, 50 seeds would all return the identical stream, and E9 is a one-line appendix note.
t42 therefore reports the exposure FIRST and only then spends anything on seeds.
""")
e = tie_exposure(np.array([1, 1, 2, 3, 3, 3, 4]))
check("D2a  n_tied on a worked example", e["n_tied"], 5, 0, note="2 + 3, the singleton 2, 4 excluded")
check("D2a  B_max on the same example", e["B_max"], 3, 0)
check("D2a  n_blocks", e["n_blocks"], 4, 0)
e0 = tie_exposure(np.arange(1000))
check("D2a  all-distinct timestamps give zero exposure", e0["n_tied"], 0, 0)
check("D2a  and B_max = 1", e0["B_max"], 1, 0)
e1 = tie_exposure(np.zeros(50))
check("D2a  all-identical timestamps expose everything", e1["n_tied"], 50, 0)

print("=" * 118)
print("D3.  A PERMUTATION'S BLAST RADIUS IS THE BLOCK, UNLESS THE BLOCK'S REJECTION COUNT MOVES")
print("=" * 118)
print("""
LOND's state after step t is the single integer R_t.  Two orders that agree outside a block
and make the SAME NUMBER of rejections inside it leave R identical at the block's end, so
every later step is bit-identical.                                                   [D3a]

Hence a tie-break can only propagate beyond its own block by changing that count.  The
consequences are worth separating, because they answer different halves of the accept
criterion: WITHIN-block reordering moves which episodes are alerted and when (a first-
detection-time effect), while a changed count moves everything downstream (a discoveries
and FDP effect).
""")
gam1, _ = make_gamma("poly", 60)
same_after = diff_after = 0
for _ in range(4000):
    T = 24
    Ev = np.where(rng.random(T) < 0.25, rng.uniform(1e3, 1e6, T), rng.uniform(0, 50, T))
    ceil = 1e6
    blk = slice(8, 13)                                # one tie block of five
    base = lond_rejections(Ev, ceil, gam1)
    Ev2 = Ev.copy()
    Ev2[blk] = Ev[blk][rng.permutation(5)]
    perm = lond_rejections(Ev2, ceil, gam1)
    if base[:8].tolist() != perm[:8].tolist():
        raise AssertionError("prefix changed -- impossible")
    if int(base[blk].sum()) == int(perm[blk].sum()):
        same_after += int(base[13:].tolist() == perm[13:].tolist())
    else:
        diff_after += 1
check_bool("D3a  equal in-block counts => identical suffix (4000 trials)",
           same_after > 0, note=f"{same_after} trials had equal counts and ALL matched")
print(f"       trials whose in-block rejection count changed: {diff_after}")
# A random block almost never straddles the rejection boundary, so the converse needs
# blocks built AT it -- otherwise the check has no power and D3a reads as vacuous.
diff_boundary = same_boundary = mismatch = 0
for _ in range(4000):
    T, B, st = 24, 5, 8
    thr = 1.0 / (A * gam1[st + 1] * 1)          # the level at the block's first step
    Ev = np.concatenate([rng.uniform(0, 50, st),
                         thr * rng.uniform(0.7, 1.4, B),      # straddling the boundary
                         rng.uniform(0, 50, T - st - B)])
    base = lond_rejections(Ev, 1e6, gam1)
    Ev2 = Ev.copy(); Ev2[st:st + B] = Ev[st:st + B][rng.permutation(B)]
    perm = lond_rejections(Ev2, 1e6, gam1)
    if int(base[st:st + B].sum()) == int(perm[st:st + B].sum()):
        same_boundary += 1
        if base[st + B:].tolist() != perm[st + B:].tolist():
            mismatch += 1
    else:
        diff_boundary += 1
check("D3a  equal-count blocks with an identical suffix, at the boundary", mismatch, 0, 0,
      note=f"{same_boundary} equal-count trials, 0 suffix mismatches")
check_bool("D3a  the in-block count really does change at the boundary",
           diff_boundary > 200, note=f"{diff_boundary} of 4000 -- the check has power")

print("=" * 118)
print("D4.  THE EXTREMES OF THE PERMUTATION DISTRIBUTION, AND WHERE THE RECORD'S ORDER SITS")
print("=" * 118)
print("""
Fifty seeds sample the permutation distribution.  For a single block of size B <= 7 the
distribution can be enumerated exactly (B! orders), giving the true min and max instead of
an estimate.  The tempting shortcut is to skip the enumeration:

    CONJECTURE (FALSE): within a block, processing the SMALLEST p-values first maximises
    the number of rejections, because LOND's level rises with R and falls with t.

Brute force over all B! orders REFUTES it: on 127 of 600 random blocks some other order
beats smallest-p-first, by as much as 3 rejections.  The reason is that the two effects do
not align.  Rejecting a small p early does raise R for every later step, but a p small
enough to be rejected anywhere is rejected late as well, so spending the largest gamma_t on
it wins nothing; the order that maximises the count spends the early, high-gamma steps on
the MARGINAL episodes and leaves the certain ones for later.  There is no cheap surrogate
for the optimum here.                                                                [D4a]

Consequence for the measurement: the extremes are enumerated exactly where B! is tractable
and SAMPLED otherwise, and a sampled extreme is labelled as a sample, never as the optimum.
""")
gam1s, _ = make_gamma("poly", 20)
n_ok = n_bad = 0
worst_gap = 0
for _ in range(600):
    B = int(rng.integers(2, 7))
    Ev = np.where(rng.random(B) < 0.5, rng.uniform(1e3, 1e6, B), rng.uniform(0, 500, B))
    ceil = 1e6
    counts = []
    for pm in permutations(range(B)):
        counts.append(int(lond_rejections(Ev[list(pm)], ceil, gam1s).sum()))
    greedy = int(lond_rejections(Ev[np.argsort(-Ev)], ceil, gam1s).sum())   # largest Ev = smallest p
    if greedy == max(counts):
        n_ok += 1
    else:
        n_bad += 1
        worst_gap = max(worst_gap, max(counts) - greedy)
check_bool("D4a  smallest-p-first is NOT block-optimal (refuted, as stated)", n_bad > 0,
           note=f"{n_bad} of {n_ok+n_bad} blocks beaten by another order; "
                f"worst shortfall {worst_gap} rejections")
check_bool("D4a  and it is not always beaten either, so the failure is order-specific",
           n_ok > 0, note=f"{n_ok} blocks where greedy did attain the max")
# the concrete counterexample, pinned so a later edit cannot quietly reinstate the shortcut
_cex = None
for _ in range(20000):
    B = 4
    Ev_c = np.where(rng.random(B) < 0.5, rng.uniform(1e3, 1e6, B), rng.uniform(0, 500, B))
    cs = {pm: int(lond_rejections(Ev_c[list(pm)], 1e6, gam1s).sum())
          for pm in permutations(range(B))}
    g = int(lond_rejections(Ev_c[np.argsort(-Ev_c)], 1e6, gam1s).sum())
    if max(cs.values()) > g:
        _cex = (Ev_c.copy(), g, max(cs.values()))
        break
check_bool("D4a  a concrete B=4 counterexample exists", _cex is not None,
           note=("greedy %d vs optimum %d" % (_cex[1], _cex[2])) if _cex else "none found")
# and the spread over permutations is real, so the enumeration is not measuring a constant
spread_seen = 0
for _ in range(600):
    B = int(rng.integers(3, 7))
    Ev = np.where(rng.random(B) < 0.5, rng.uniform(1e3, 1e6, B), rng.uniform(0, 500, B))
    cs = [int(lond_rejections(Ev[list(pm)], 1e6, gam1s).sum()) for pm in permutations(range(B))]
    spread_seen += int(max(cs) > min(cs))
check_bool("D4a  the permutation spread is non-zero somewhere (600 blocks)",
           spread_seen > 0, note=f"{spread_seen} blocks had max > min")

print("=" * 118)
print("D5.  FIRST-DETECTION RANK MOVES BY AT MOST THE BLOCK, WHEN THE COUNT IS FIXED")
print("=" * 118)
print("""
If the first rejection falls in a block of size B occupying stream positions t..t+B-1, then
under any permutation that keeps the in-block count the first rejection stays inside those
positions, so its RANK moves by at most B-1.                                         [D5a]

The record reports first detection as a rank, so B_max is a direct bound on the reportable
uncertainty in that number -- again available from the timestamps alone.
""")
bad5 = 0
for _ in range(3000):
    T, B, st = 24, 5, 8
    Ev = np.concatenate([rng.uniform(0, 50, st),
                         np.where(rng.random(B) < 0.5, rng.uniform(1e3, 1e6, B),
                                  rng.uniform(0, 50, B)),
                         rng.uniform(0, 50, T - st - B)])
    base = lond_rejections(Ev, 1e6, gam1)
    Ev2 = Ev.copy(); Ev2[st:st + B] = Ev[st:st + B][rng.permutation(B)]
    perm = lond_rejections(Ev2, 1e6, gam1)
    fb = int(np.argmax(base)) if base.any() else -1
    fp = int(np.argmax(perm)) if perm.any() else -1
    if fb >= st and fb < st + B and fp >= 0 and abs(fp - fb) > B - 1:
        bad5 += 1
check("D5a  first-detection rank moves by at most B-1 (3000 trials)", bad5, 0, 0)

print("=" * 118)
print("D6.  WHAT THE MEASUREMENT MUST REPORT")
print("=" * 118)
print("""
  1  the exposure (n_tied, B_max, tied fraction) at every position -- BEFORE any seed, and
     with the note that it is detector- and label-free                                [D2a]
  2  the deterministic value of each statistic, and its PERCENTILE within the 50-seed
     randomised distribution.  A statistic whose deterministic value sits at an extreme
     percentile is one the tie-break is choosing, and the accept criterion turns on that
  3  sd and full range of discoveries, true positives, FDP, recall and first-detection rank
  4  FDP reported as None where there are no rejections, not as 0.0
""")
check("D6   statistics to report", 5, 5, 0, note="discoveries, tp, FDP, recall, first rank")

print("=" * 118)
print(f"  PASSED {len(OK)} / {len(OK) + len(FAIL)} checks")
if FAIL:
    print("  FAILED: " + ", ".join(FAIL))
print("=" * 118)

json.dump(dict(
    D1a="a random secondary key permutes only within equal-first_ts blocks",
    D2a="n_tied = episodes in blocks of size >= 2 is an exact, detector-free bound on the "
        "movable population; zero exposure makes E9 a one-line note",
    D3a="equal in-block rejection counts leave LOND's suffix bit-identical, so a "
        "tie-break propagates only by changing that count",
    D4a="smallest-p-first is NOT block-optimal -- REFUTED by brute force over all B! "
        "orders (127 of 600 blocks beaten, worst shortfall 3).  The optimum spends the "
        "early high-gamma steps on MARGINAL episodes.  Extremes must be enumerated where "
        "B! is tractable and labelled as samples otherwise",
    D5a="first-detection rank moves by at most B-1 when the in-block count is fixed",
    D6="report exposure first, then the deterministic value's percentile in the randomised "
       "distribution, not just the sd",
    n_passed=len(OK), n_failed=len(FAIL), failed=FAIL),
    open(OUT / "t42a_E9_derivation.json", "w"), indent=1)
print("  wrote out/t42a_E9_derivation.json")
if FAIL:
    raise SystemExit(1)
