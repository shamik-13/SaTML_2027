"""
E3, part 1 -- the ANALYTIC derivation of deterministic precommitted weighting under
attacker-controlled ordering, verified numerically.

Runs before t36_E3_asymmetric.py touches LSPR23.  Same contract as t34a/t35a: every closed
form the real-data script relies on is derived here and checked, so a disagreement between
the two is a bug rather than a finding (docs/01_HANDOFF_PHASE4.md section 6).

No data files are read.  Runtime ~20 s.

======================================================================================
WHAT IS ALREADY SETTLED AND IS NOT REDONE HERE
======================================================================================
Section 4.16's theorem: no family of symmetric e-merging functions that ATTAINS tau is
tau-padding-robust.  Its corollary already proves the escape: `F(e) = e_slot` for a slot
fixed in advance is a valid e-merging function under arbitrary dependence and is
padding-invariant, and section 4.12 policy D already prices it (109.4/284 episodes, power
decaying as 1/m under padding).  The record also already names the true condition:

    the adversary must not be able to choose which slot its events occupy.

E3 tests exactly that condition, and nothing else.

======================================================================================
NOTATION
======================================================================================
    M            evidence ceiling = |C|+1 at rank k = 1; per-flow e in {0, M}
    w            a PRECOMMITTED weight sequence w_1, w_2, ... >= 0, fixed before any score
                 is observed and indexed by POSITION WITHIN THE EPISODE
    F(e)         = sum_i w_i e_i                          the merged evidence
    tau          = 1/alpha_t                              the rejection threshold at step t
    beta         = tau/M = 1/(alpha_t * M)                the WEIGHT MASS a detection needs
    S            the set of positions at which attack flows fire
    r            = |S|

======================================================================================
D1.  WHAT THE PRECOMMITTED-WEIGHT CLASS IS, AND WHY IT IS PADDING-INVARIANT
======================================================================================
Each per-flow e-value satisfies E[e_i] <= 1 under the episode null.  By linearity, for any
NON-NEGATIVE w,

        E[F(e)] = sum_i w_i E[e_i] <= sum_i w_i,

so F is a valid e-merging function under ARBITRARY dependence iff  sum_i w_i <= 1.   [D1a]
No independence assumption enters; this is the same linearity that makes the arithmetic mean
valid (section 2.3), and it is why the class is worth testing at all.

PADDING-INVARIANCE.  Appending r zero-evidence flows at positions m+1..m+r leaves
w_1..w_m and e_1..e_m untouched, so F is UNCHANGED for every r.                       [D1b]
The single-slot rule of section 4.16's corollary is the special case w = (1, 0, 0, ...).

The invariance requires the weights to be indexed by ABSOLUTE position from the start of the
episode.  A rule indexed from the END -- "last-event-only" -- is NOT padding-invariant: one
appended zero moves the counted slot onto the pad and sends F to 0.  Last-event-only is
therefore excluded by D1b, not by a measurement, and the real-data script asserts it.  [D1c]

======================================================================================
D2.  THE POWER LEG: HOW MANY POSITIONS CAN EVER CARRY A DETECTION
======================================================================================
With two-point evidence, F = M * sum_{i in S} w_i, so

        reject  <=>  sum_{i in S} w_i >= beta,      beta = 1/(alpha_t * M)             [D2a]

Call position i INDIVIDUALLY DETECTABLE if a lone attack flow there fires the rule, i.e.
w_i >= beta.  Let P = #{i : w_i >= beta}.  Since sum_i w_i <= 1,

        P * beta <= sum_{i : w_i >= beta} w_i <= 1,    hence   P <= 1/beta = alpha_t * M
                                                                                       [D2b]
More generally, if detection is required whenever r attack flows fire at r positions of
equal weight, each needs w >= beta/r and

        P_r <= r / beta = r * alpha_t * M                                              [D2c]

**alpha_t * M is the same quantity that governs F1's feasibility horizon** -- there it is the
number of stream steps at which a rejection is possible, here it is the number of WITHIN-
EPISODE positions at which one can be triggered.  It falls as alpha_t does, so the usable
prefix shrinks along the stream exactly as the feasible set does.

======================================================================================
D3.  THE ORDERING LEG: THE FRONT-LOAD COST IS A TAIL SUM, AND IT IS FINITE
======================================================================================
Let the attacker prepend L flows carrying ZERO evidence -- not merely benign-labelled ones.
The distinction matters: a leading flow that happened to fire would occupy a high-weight
position and help the defender.  Operationally the requirement is mild, because the benign
firing rate is the conformal floor: at the guarantee window a benign flow fires with
probability ~4.4e-7 (section 4.31's 1.07x of 1/M), so an ordinary connection is zero-evidence
with probability 1 - 4.4e-7.  The attack flows are then pushed to positions L+1, ....  The most
favourable case for the defender is that EVERY remaining flow fires, giving
F <= M * sum_{i > L} w_i.  Detection is therefore impossible for any placement of the attack
once

        sum_{i > L} w_i  <  beta.

Define the FRONT-LOAD COST

        L*(w, beta) = min { L >= 0 : sum_{i > L} w_i < beta }.                         [D3a]

> **Proposition E3.**  For every precommitted non-negative weight sequence with
> `sum_i w_i <= 1` and every beta > 0, `L*(w, beta)` is FINITE.  No choice of precommitted
> weights escapes: a finite number of leading benign flows makes detection impossible.

**Proof.** Summability gives `sum_{i>L} w_i -> 0` as `L -> infinity`, so the set is
non-empty and its minimum is finite. QED                                               [D3b]

This uses the SAME summable-tail convergence lemma as section 4.13's Proposition 2, which
bounds the absorbing state by `S(Delta) = sum_{d >= Delta} gamma_d`.  There the summable
sequence is the spending sequence and the axis is stream time; here it is the weight sequence
and the axis is position within the episode.  It is the same LEMMA, not the same theorem:
Proposition 2 additionally needs rejection-free runs, distinct lags and the absorbing-state
argument, none of which appear here.                                                   [D3c]

CLOSED FORMS.
    first-event-only  w = (1, 0, 0, ...)                    L* = 1                     [D3d]
    uniform over m0   w_i = 1/m0 for i <= m0    L* = max(0, floor(m0*(1-beta)) + 1)     [D3e]
    exponential rho   w_i = (1-rho) rho^(i-1)   L* = max(0, floor(log beta/log rho) + 1) [D3f]
The max(0, .) matters: when beta > 1 the required mass exceeds the whole weight budget, so
detection is impossible with no padding at all and the cost is 0.  The raw expressions go
negative there.  That regime is reached whenever alpha_t*M < 1, which the run below covers.
    two-block         w_1 = a, rest on 2..K         L* ~ K(1 - beta/(1-a))              [D3g]
`floor(.) + 1`, not `ceil(.)`: when the expression is exactly an integer k the tail at L = k
equals beta rather than falling below it, so the cost is k + 1.

======================================================================================
D4.  THE TRIANGLE CLOSES
======================================================================================
Combining D2b and D3a.  Suppose every position in 1..K must be individually detectable, so
`w_i >= beta` for all i <= K.  Then D2b gives `K <= 1/beta`.  And the front-load cost cannot
exceed the last position carrying weight the defender relies on:

For a NON-INCREASING w the individually-detectable set is a prefix 1..P, and since
`tail_{P-1} >= w_P >= beta` the attacker must push past at least that prefix:

        L*  >=  P          for non-increasing w                                        [D4a]

The inequality runs this way, not the other: positions beyond P are individually
undetectable yet still carry mass collectively, and the attacker has to clear all of it.
Exponential decay at rho = 0.99 and alpha_t = 1e-2 has P = 548 but L* = 1006.

> **The triangle.**  A precommitted weight scheme cannot have all three of
>   (a) padding-invariance          -- needs weights indexed by absolute position [D1b]
>   (b) usable power                -- needs weight mass >= beta where attacks land [D2a]
>   (c) resistance to ordering      -- needs L* large [D3a]
> **Validity** forces `sum w <= 1`; (a) additionally forces the weights to be fixed by
> ABSOLUTE position.  Given `sum w <= 1`, (b) caps the reach of the scheme at
> `P <= alpha_t*M` positions [D2b] -- the SAME quantity as F1's feasibility horizon -- and
> (c) is impossible outright, because `L*` is finite for every summable `w` [D3b].  The
> design choice sets only the PRICE, and the price is bought entirely out of power:
> concentrating weight early maximises `P`-per-position and minimises `L*`; spreading it
> raises `L*` and drives every `w_i` below `beta`, so `P` falls to 0 and no lone attack flow
> is detectable anywhere.  The extreme points are first-event-only (`L* = 1`, full power at
> one position) and a thin tail such as `w_i ~ i^-1.05` (`L*` in the millions, `P = 0`).
>                                                                                       [D4c]

**alpha_t*M is small where it matters.**  It is the same number as F1's feasibility horizon,
and it decays with alpha_t along the stream: under LOND with gamma ~ j^-1.6 at the guarantee
window it starts near 5.4e4 and falls below 1 within the first ~10^3 episodes, so late in a
stream NO precommitted scheme can be triggered by a lone attack flow at any position at all.

======================================================================================
D5.  WHAT THE ATTACKER PAYS, AND WHAT IT PAYS AGAINST THE MEAN RULE
======================================================================================
Against the symmetric arithmetic mean, section 4.16's bound gives a suppressing pad of
`floor(sum(x)/tau - m) + 1` flows appended ANYWHERE.  Against a precommitted weight scheme
the attacker must instead place `L*` flows FIRST.  The two costs are not comparable in the
abstract, so the real-data script reports both on the same episodes.               [D5a]
An attacker that cannot influence ordering pays infinity against a precommitted scheme
(padding is invariant), which is the genuine benefit the corollary already claims; the
question E3 answers is what that benefit is worth once ordering is available.
======================================================================================
"""
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


# ---------------------------------------------------------------------------------------
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
    """L*(w, beta) = min{L >= 0 : sum_{i>L} w_i < beta}   [D3a].  Returns len(w) if the tail
    never falls below beta within the represented prefix.

    beta must be positive: at beta = 0 the condition `tail < 0` is unsatisfiable for
    non-negative weights and the quantity is not defined.  At beta > sum(w) the answer is 0 --
    the required mass exceeds everything available, so detection is already impossible with
    no padding at all.

    Index care: w is 0-indexed, positions are 1-indexed.  `sum_{i > L} w_i` over 1-indexed
    positions is `w[L:].sum()` over the 0-indexed array, so tail[L] = sum_{j>=L} w[j] is
    already the quantity wanted and must NOT be shifted.  Shifting it by one returns L* - 1
    and reports the cost of defeating first-event-only as 0 flows rather than 1."""
    w = np.asarray(w, dtype=float)
    if beta <= 0:
        raise ValueError("beta must be positive")
    if np.any(w < 0):
        raise ValueError("weights must be non-negative")
    tail = np.concatenate([np.cumsum(w[::-1])[::-1], [0.0]])   # tail[L] = sum_{j>=L} w[j]
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
    # E[F] <= 1 under ARBITRARY dependence: use maximally adverse dependence -- one uniformly
    # random position carries the whole mass (perfectly negatively dependent e-values)
    n = 400_000
    pos = rng.integers(0, 200, n)
    e = np.zeros((n, 200)); e[np.arange(n), pos] = 200.0     # each E[e_i] = 1 exactly
    F = e @ w[:200]
    se = float(F.std()) / np.sqrt(n)
    check(f"D1a E[F] <= 1 under maximally adverse dependence [{scheme}]",
          float(F.mean()), min(1.0, float(w[:200].sum())), max(6 * se, 1e-3),
          f"E[F]={F.mean():.4f}, sum w[:200]={w[:200].sum():.4f}")
    del e, F
    # D1b padding-invariance: append zeros, F unchanged
    x = np.zeros(200); x[[3, 17, 88]] = M
    base = float(x @ w[:200])
    for r in (10, 1000, 100_000):
        xr = np.concatenate([x, np.zeros(r)])
        wr = weights(scheme, 200 + r, **kw)
        check(f"D1b padding-invariant at r={r} [{scheme}]", float(xr @ wr), base,
              1e-9 * max(1.0, base))

# D1a CONVERSE: sum w > 1 really does break validity under an admissible dependence.  The
# forward check above only ever sees w[:200], so it cannot detect an over-weighted tail.
_n = 400_000
_pos = rng.integers(0, 200, _n)
_e = np.zeros((_n, 200)); _e[np.arange(_n), _pos] = 200.0     # each E[e_i] = 1 exactly
for excess in (1.01, 1.5, 3.0):
    w_bad = np.full(200, excess / 200)
    _F = _e @ w_bad
    _se = float(_F.std()) / np.sqrt(_n)
    check(f"D1a converse: sum w = {excess} gives E[F] = {excess} > 1, i.e. NOT valid",
          float(_F.mean()), excess, max(6 * _se, 1e-3))
del _e, _F

# D1c: last-event-only is NOT padding-invariant
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
# D2b is TIGHT and needs no monotonicity: floor(1/beta) positions at exactly weight beta
for beta_t in (0.2, 0.1, 1.0 / 7):
    npos = int(np.floor(1.0 / beta_t))
    w = np.zeros(4 * npos); w[::4][:npos] = beta_t          # non-monotone, spread out
    check(f"D2b is tight and needs no monotonicity [beta={beta_t:.4g}]",
          float(detectable_positions(w, beta_t)), float(npos), 0.0,
          f"P={detectable_positions(w, beta_t)} = floor(1/beta) = {npos}")
    del w
w = np.array([0.2, 0.2, 0.19999999])
check("D2b counts w_i == beta as detectable (>=, not >)",
      float(detectable_positions(w, 0.2)), 2.0, 0.0)
del w

# D2a: the rejection rule, brute-forced
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
    # D3d first-event-only
    w = weights("first-only", NBIG)
    check(f"D3d first-event-only L* = 1 [a_t={alpha_t:g}]",
          float(frontload_cost(w, beta)), 1.0, 0.0)
    del w
    # D3e uniform over m0
    for m0 in (10, 100, 5000):
        w = weights("uniform-m0", NBIG, m0=m0)
        # L* = min{L : (m0-L)/m0 < beta} = min{L : L > m0(1-beta)} = floor(m0(1-beta)) + 1.
        # ceil() is wrong when m0(1-beta) is exactly an integer: there L must be one larger.
        want = float(np.floor(m0 * (1.0 - beta)) + 1)
        check(f"D3e uniform-m0 L* = floor(m0(1-beta))+1 [m0={m0}, a_t={alpha_t:g}]",
              float(frontload_cost(w, beta)), want, 0.0)
        del w
    # D3f exponential decay
    for rho in (0.5, 0.9, 0.999):
        w = weights("exp-decay", NBIG, rho=rho)
        # tail_L = rho^L, so L* = min{L : rho^L < beta} = floor(log beta / log rho) + 1
        want = float(np.floor(np.log(beta) / np.log(rho)) + 1)
        got = float(frontload_cost(w, beta))
        check(f"D3f exp-decay L* = floor(log beta/log rho)+1 [rho={rho}, a_t={alpha_t:g}]",
              got, want, 0.0, f"L*={got:.0f}")
        del w
# D3b: L* is finite for every summable sequence -- including a deliberately heavy tail
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
        # D4a: for a NON-INCREASING w the detectable set is a prefix, and the attacker's
        # cost is at LEAST its length -- tail_{P-1} >= w_P >= beta, so L* >= P.  (An earlier
        # version of this file asserted L* <= P, which is false: the positions beyond P are
        # individually undetectable but collectively still carry mass, and the attacker must
        # push past all of it.  exp-decay rho=0.99 at alpha_t=1e-2 has P=548, L*=1006.)
        if P > 0 and bool(np.all(np.diff(w) <= 1e-18)):
            check(f"D4a L* >= P for non-increasing w [{scheme}{kw}, a_t={alpha_t:g}]",
                  float(L >= P), 1.0, 0.0, f"L*={L}, P={P}")
            check(f"D2b P <= alpha_t*M [{scheme}{kw}, a_t={alpha_t:g}]",
                  float(P <= alpha_t * M + 1e-9), 1.0, 0.0,
                  f"P={P}, alpha_t*M={alpha_t*M:.4g}")
        del w
# the extreme points of the tradeoff
check("D4c first-event-only maximises power and minimises L*",
      float(weights("first-only", 100)[0]), 1.0, 0.0, "w_1 = 1, L* = 1")
# The other extreme: a thin summable tail buys a much larger L*, and pays for it in
# per-position weight.  P is NOT zero unconditionally -- at a large alpha_t*M the thin tail
# still has many individually-detectable positions -- so the claim is the TRADEOFF, and D2b
# is what caps the reach in every case.
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
