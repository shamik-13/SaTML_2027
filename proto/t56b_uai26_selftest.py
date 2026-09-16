"""
Unit tests for the Xu/Fischer/Ramdas UAI 2026 procedures added to h6_procs.py
(arXiv 2603.24792v3).  No data files; runs in about a minute, so it can be re-run after
any edit.  Exercises the SHIPPED code by importing h6_procs directly.

The two claims that matter most are the PAPER'S OWN, because they pin our reading of an
ambiguous definition and of a DP we re-derived:

  1  e-TOAD with d_i = i        must equal e-LOND exactly          (their App. D.2)
  2  e-TOAD with d_i = infinity must equal online e-BH exactly     (their App. D.2)
  3  the (19)-(22) DP must equal brute-force enumeration of (15)-(16) over all subsets
  4  donation e-LOND, closed e-LOND and donation e-BH must each DOMINATE their baseline
     (their Theorems 2, 8, 13)

and then OUR two new propositions, which are what the paper will state:

  5  donation e-LOND's cold-start boost never exceeds 1/(1-delta)   [-> thm:family1]
  6  closed e-LOND's level never exceeds delta*gamma_{Z+1}*(R+1)    [-> new argument]

plus a validity sanity check under the null.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import h6_procs as hp

fails = []


def check_shipped_copy_is_current():
    """`src/lib/*.py` is generated from `proto/*.py` by tools/strip_comments.py --keep-doc, and
    the experiment stages import the SHIPPED copy.  A fix made here that is not regenerated would
    therefore never reach out/*.json.  Verify the two are in sync rather than trusting it."""
    import subprocess, tempfile, os
    root = Path(__file__).resolve().parent.parent
    proto = root / "proto" / "h6_procs.py"
    shipped = root / "src" / "lib" / "h6_procs.py"
    if not shipped.exists():
        return None, "src/lib/h6_procs.py missing"
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
        out = tmp.name
    try:
        subprocess.run([sys.executable, str(root / "src" / "tools" / "strip_comments.py"),
                        str(proto), out, "--keep-doc"],
                       check=True, capture_output=True)
        same = Path(out).read_text() == shipped.read_text()
        return same, ("in sync" if same else
                      "STALE -- rerun: python src/tools/strip_comments.py "
                      "proto/h6_procs.py src/lib/h6_procs.py --keep-doc")
    finally:
        os.unlink(out)


def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"   {detail}" if detail else ""))
    if not cond:
        fails.append(name)


def two_point_stream(T, npos, M, rng, mal_frac=0.5):
    """A stream shaped like ours: evidence is 0 or a multiple of the ceiling M, and only a
    small fraction of hypotheses fire at all."""
    Ev = np.zeros(T)
    pos = rng.choice(T, size=npos, replace=False)
    Ev[pos] = M * rng.uniform(0.02, 1.0, size=npos)
    ismal = np.zeros(T, bool)
    ismal[rng.choice(pos, size=max(1, int(mal_frac * npos)), replace=False)] = True
    return Ev, ismal


def mask(fn, ctx, gam, **kw):
    m = np.zeros(ctx.T, bool)
    out = fn(ctx, gam, fired=m, **kw)
    return m, out


# ======================================================================================
print("=" * 100)
print("1. e-TOAD with d_i = i is EXACTLY e-LOND  (their App. D.2 limiting case)")
print("=" * 100)
nontrivial_t1 = 0
for trial, (T, npos, M) in enumerate([(60, 12, 500.0), (200, 25, 5_000.0),
                                      (300, 3, 2_000.0), (120, 40, 300.0)]):
    rng = np.random.default_rng(100 + trial)
    Ev, ismal = two_point_stream(T, npos, M, rng)
    ctx = hp.Ctx(Ev, ismal, M, alpha=0.05, w0=0.025)
    g1, _ = hp.make_gamma("poly", T)
    m_lond, r_lond = mask(hp.run_lond, ctx, g1)
    dl = hp.make_deadlines("immediate", T)
    m_toad, r_toad = mask(hp.run_etoad, ctx, g1, deadline=dl)
    check(f"rejection masks identical [T={T}, npos={npos}]",
          np.array_equal(m_lond, m_toad),
          f"e-LOND {int(m_lond.sum())} vs e-TOAD {int(m_toad.sum())}")
    check(f"  silence identical [T={T}]", r_lond[2] == r_toad[2],
          f"{r_lond[2]} vs {r_toad[2]}")
    nontrivial_t1 += int(m_lond.sum() > 0)

check("test 1 is not vacuous (some trial actually rejects)", nontrivial_t1 >= 2,
      f"{nontrivial_t1} of 4 trials had rejections")

# ======================================================================================
print("=" * 100)
print("2. e-TOAD with d_i = infinity is EXACTLY online e-BH  (their App. D.2)")
print("=" * 100)
nontrivial_t2 = 0
for trial, (T, npos, M) in enumerate([(60, 12, 500.0), (200, 25, 5_000.0),
                                      (150, 60, 1_000.0), (300, 3, 2_000.0)]):
    rng = np.random.default_rng(200 + trial)
    Ev, ismal = two_point_stream(T, npos, M, rng)
    ctx = hp.Ctx(Ev, ismal, M, alpha=0.05, w0=0.025)
    g1, _ = hp.make_gamma("poly", T)
    m_ebh = np.zeros(T, bool)
    ks, mvals = hp.online_ebh_kstar(ctx.Ev, g1, ctx.A, T)
    kfin = int(ks[T])
    m_ebh[:] = np.isfinite(mvals) & (mvals <= kfin)
    rej_e, tp_e, sil_e, first_e, _, _, _ = hp.run_online_ebh(ctx, g1)
    dl = hp.make_deadlines("arc", T)
    m_toad, (rej_t, tp_t, sil_t, first_t) = mask(hp.run_etoad, ctx, g1, deadline=dl)
    check(f"rejection MASKS identical [T={T}, npos={npos}]", np.array_equal(m_ebh, m_toad),
          f"online e-BH {int(m_ebh.sum())} vs e-TOAD {int(m_toad.sum())} (k*_T={kfin})")
    check(f"  true positives identical [T={T}]", tp_e == tp_t, f"{tp_e} vs {tp_t}")
    # The two silence columns are DIFFERENT quantities and must not be asserted equal:
    # run_online_ebh uses the necessary condition "CEIL clears 1/(a gam_t t)", while
    # run_etoad runs the actual step-up on the E_t = CEIL counterfactual.  The necessary
    # condition can only under-count, so the exact figure must dominate it.
    check(f"  exact silence >= necessary-condition silence [T={T}]", sil_t >= sil_e,
          f"e-TOAD exact {sil_t} >= online e-BH necessary-only {sil_e}")
    nontrivial_t2 += int(m_ebh.sum() > 0)

check("test 2 is not vacuous (some trial actually rejects)", nontrivial_t2 >= 2,
      f"{nontrivial_t2} of 4 trials had rejections")

# ======================================================================================
print("=" * 100)
print("3. the (19)-(22) dynamic program equals brute force over ALL subsets")
print("=" * 100)


def brute_v(E, g, rejmask, upto, d, Rn):
    """v_t(upto, k) = max over S subset [upto], |S| = k, of |S ∩ R| - d E_S (|R|+1),
    with E_S = sum_{i in S} gamma_{rank of i in S} E_i.  Exponential; small upto only."""
    from itertools import combinations
    out = np.full(upto + 1, -np.inf); out[0] = 0.0
    for k in range(1, upto + 1):
        best = -np.inf
        for S in combinations(range(1, upto + 1), k):
            ES = sum(g[j + 1] * E[i - 1] for j, i in enumerate(S))
            val = sum(1.0 for i in S if rejmask[i - 1]) - d * ES * Rn
            best = max(best, val)
        out[k] = best
    return out


rng = np.random.default_rng(7)
for trial in range(6):
    upto = int(rng.integers(3, 11))
    E = np.where(rng.random(upto) < 0.5, 0.0, rng.uniform(0, 40, upto))
    rejmask = rng.random(upto) < 0.3
    d = 0.05; Rn = int(rng.integers(1, 4))
    g1, _ = hp.make_gamma("poly", upto + 2)
    v_dp = hp._closed_build(E, g1, rejmask, upto, d, Rn)
    v_bf = brute_v(E, g1, rejmask, upto, d, Rn)
    check(f"DP == brute force [upto={upto}, Rn={Rn}, trial {trial}]",
          np.allclose(v_dp, v_bf, atol=1e-9),
          f"max |diff| = {np.max(np.abs(v_dp - v_bf)):.2e}")

# ======================================================================================
print("=" * 100)
print("4. each procedure DOMINATES its baseline (their Thms 2, 8, 13)")
print("=" * 100)
nontrivial_t4 = 0
for trial, (T, npos, M) in enumerate([(80, 15, 800.0), (150, 30, 3_000.0),
                                      (200, 8, 20_000.0), (100, 50, 400.0),
                                      (250, 2, 100_000.0)]):
    rng = np.random.default_rng(300 + trial)
    Ev, ismal = two_point_stream(T, npos, M, rng)
    ctx = hp.Ctx(Ev, ismal, M, alpha=0.05, w0=0.025)
    g1, _ = hp.make_gamma("poly", T)
    m_lond, _ = mask(hp.run_lond, ctx, g1)
    m_don, _ = mask(hp.run_donation_elond, ctx, g1)
    m_cls, _ = mask(hp.run_closed_elond, ctx, g1)
    check(f"donation e-LOND >= e-LOND [T={T}]", bool(np.all(m_don >= m_lond)),
          f"{int(m_lond.sum())} -> {int(m_don.sum())}")
    check(f"closed e-LOND >= e-LOND [T={T}]", bool(np.all(m_cls >= m_lond)),
          f"{int(m_lond.sum())} -> {int(m_cls.sum())}")
    rej_e = hp.run_online_ebh(ctx, g1)[0]
    m_deb, (rej_d, _, _, _) = mask(hp.run_donation_ebh, ctx, g1, history="union")
    m_ebh_b = np.zeros(T, bool)
    ks_b, mv_b = hp.online_ebh_kstar(ctx.Ev, g1, ctx.A, T)
    m_ebh_b[:] = np.isfinite(mv_b) & (mv_b <= int(ks_b[T]))
    check(f"donation e-BH >= online e-BH, by MASK [T={T}]",
          bool(np.all(m_deb >= m_ebh_b)), f"{int(m_ebh_b.sum())} -> {int(m_deb.sum())}")
    nontrivial_t4 += int(m_lond.sum() > 0)

check("test 4 is not vacuous (dominance is exercised on non-empty baselines)",
      nontrivial_t4 >= 3, f"{nontrivial_t4} of 5 trials had e-LOND rejections")

# ======================================================================================
print("=" * 100)
print("5. OUR PROPOSITION A -- donation e-LOND's cold-start boost <= 1/(1-delta)")
print("=" * 100)
print("   Wbar_t <= sum(gamma) <= 1, so on a rejection-free run the level is at most")
print("   delta*gamma_t/(1-delta): a bounded multiplicative boost, i.e. thm:family1 with")
print("   c = 1/(1-delta).  The calibration requirement therefore relaxes by (1-delta) only.")
for trial, (T, npos, M, alpha) in enumerate([
        (500, 200, 1e4, 0.05), (500, 490, 5e5, 0.05), (300, 300, 1e6, 0.05),
        (400, 100, 1e3, 0.2), (400, 400, 1e7, 0.1)]):
    rng = np.random.default_rng(400 + trial)
    Ev, ismal = two_point_stream(T, npos, M, rng)
    ctx = hp.Ctx(Ev, ismal, M, alpha=alpha, w0=alpha / 2)
    g1, _ = hp.make_gamma("poly", T)
    dg = {}
    hp.run_donation_elond(ctx, g1, diag=dg)
    check(f"cold-start boost <= 1/(1-a) [T={T}, a={alpha}]",
          dg["max_boost_coldstart"] <= dg["boost_ceiling"] + 1e-12,
          f"{dg['max_boost_coldstart']:.6f} <= {dg['boost_ceiling']:.6f}"
          f"  (any-R boost {dg['max_boost']:.4f}, negative-wealth steps {dg['n_neg_wealth']})")

# an adversarial stream: every hypothesis carries the largest evidence that still cannot
# reject, which is the configuration that maximises donated wealth
for T, alpha in [(1000, 0.05), (1000, 0.5), (200, 0.05)]:
    g1, _ = hp.make_gamma("poly", T)
    M = 1e9
    Ev = np.full(T, 1.0 / (alpha * g1[1]) - 1e-6)          # just under the first-step bar
    ctx = hp.Ctx(Ev, np.zeros(T, bool), M, alpha=alpha, w0=alpha / 2)
    dg = {}
    hp.run_donation_elond(ctx, g1, diag=dg)
    check(f"adversarial max-wealth stream [T={T}, a={alpha}]",
          dg["max_boost_coldstart"] <= dg["boost_ceiling"] + 1e-12,
          f"boost {dg['max_boost_coldstart']:.6f} <= {dg['boost_ceiling']:.6f}, "
          f"max Wbar {dg['max_wealth']:.6f} (<= sum gamma = 1)")

# ======================================================================================
print("=" * 100)
print("6. OUR PROPOSITION B -- closed e-LOND's level <= delta*gamma_{Z+1}*(R+1)")
print("=" * 100)
print("   The Z zero-evidence hypotheses form an admissible S with D_t(S) = 1, so the")
print("   minimum in (15) is at most delta*gamma_{Z+1}*(|R|+1).  This is what covers a")
print("   procedure whose level is NOT gamma_t times a bounded factor.")
for trial, (T, npos, M) in enumerate([(400, 20, 1e4), (400, 200, 1e5), (300, 3, 1e6),
                                      (250, 250, 1e3), (500, 50, 1e7)]):
    rng = np.random.default_rng(500 + trial)
    Ev, ismal = two_point_stream(T, npos, M, rng)
    ctx = hp.Ctx(Ev, ismal, M, alpha=0.05, w0=0.025)
    g1, _ = hp.make_gamma("poly", T)
    dg = {}
    hp.run_closed_elond(ctx, g1, diag=dg)
    check(f"level <= zero-evidence bound [T={T}, npos={npos}]",
          dg["worst_lvl_over_zero_bound"] <= 1.0 + 1e-9,
          f"worst ratio {dg['worst_lvl_over_zero_bound']:.6f}, Z={dg['n_zero_evidence']}")

# ======================================================================================
print("=" * 100)
print("6b. INDEPENDENT references -- brute force from the source equations, not diagnostics")
print("=" * 100)


def ref_closed_level(E, g, rejmask, t, d, Rn):
    """alpha_t from (15)-(16) by EXHAUSTIVE enumeration of S, independent of the DP."""
    from itertools import combinations
    upto = t - 1
    best = np.inf
    for k in range(0, upto + 1):
        for S in combinations(range(1, upto + 1), k):
            ES = sum(g[j + 1] * E[i - 1] for j, i in enumerate(S))
            D = 1.0 + sum(1.0 for i in S if rejmask[i - 1]) - d * ES * Rn
            if D > 0.0:
                best = min(best, d * g[k + 1] * Rn / D)
    return 0.0 if not np.isfinite(best) else best


def ref_closed_run(E, g, CEIL, d, T):
    """Whole closed e-LOND run from (15)-(16) by enumeration: level, bar, rejections."""
    rejmask = np.zeros(T, bool); R = 0; levels = []
    for t in range(1, T + 1):
        lvl = ref_closed_level(E, g, rejmask, t, d, R + 1)
        levels.append(lvl)
        if lvl > 0 and CEIL >= 1.0 / lvl and E[t - 1] >= 1.0 / lvl:
            rejmask[t - 1] = True; R += 1
    return rejmask, np.array(levels)


rng = np.random.default_rng(31)
for trial in range(5):
    T = int(rng.integers(6, 13))
    E = np.where(rng.random(T) < 0.55, 0.0, rng.uniform(0, 400, T))
    g1, _ = hp.make_gamma("poly", T + 2)
    M = 1e4
    ctx = hp.Ctx(E, np.zeros(T, bool), M, alpha=0.05, w0=0.025)
    m_impl, _ = mask(hp.run_closed_elond, ctx, g1)
    m_ref, lv_ref = ref_closed_run(E, g1, M, 0.05, T)
    check(f"closed e-LOND run == enumeration of (15)-(16) [T={T}, trial {trial}]",
          np.array_equal(m_impl, m_ref),
          f"impl {int(m_impl.sum())} vs ref {int(m_ref.sum())} rejections")
    # Proposition B measured against an INDEPENDENTLY computed bound, not the diagnostic
    Z = 0; R = 0; worst = 0.0; rj = np.zeros(T, bool)
    for t in range(1, T + 1):
        lvl = ref_closed_level(E, g1, rj, t, 0.05, R + 1)
        if Z > 0:
            worst = max(worst, lvl / (0.05 * g1[Z + 1] * (R + 1)))
        if lvl > 0 and M >= 1.0 / lvl and E[t - 1] >= 1.0 / lvl:
            rj[t - 1] = True; R += 1
        elif E[t - 1] == 0.0:
            Z += 1
    check(f"  Prop B against an independent bound [T={T}]", worst <= 1.0 + 1e-9,
          f"worst level/bound = {worst:.6f}")

# the rebuild path: a stream engineered to reject repeatedly, so Rn changes often and the
# O(t^2) rebuild after each rejection is exercised.  T is kept small because the reference
# enumerates all 2^(t-1) subsets at every step.
g1, _ = hp.make_gamma("poly", 20)
E = np.zeros(14); E[[1, 3, 6, 9, 12]] = 1e6
ctx = hp.Ctx(E, np.zeros(14, bool), 1e7, alpha=0.05, w0=0.025)
m_impl, _ = mask(hp.run_closed_elond, ctx, g1)
m_ref, _ = ref_closed_run(E, g1, 1e7, 0.05, 14)
check("closed e-LOND REBUILD path == enumeration",
      np.array_equal(m_impl, m_ref) and int(m_ref.sum()) >= 3,
      f"impl {int(m_impl.sum())} vs ref {int(m_ref.sum())} rejections (>=3 exercises rebuilds)")


def ref_donation_ebh(E, g, d, T):
    """(102) transcribed from the source, returning BOTH readings it licenses:

      snapshot -- "the r_t largest indices of gamma_i E_i among i in [t]" at t = T, which is
                  literally what (102) and the sentence after it define and what the donation
                  balance certifies;
      union    -- the ever-rejected set, which is what irrevocable ARC decisions would emit.

    They differ, which is the inconsistency in the source.  Returned separately so neither
    test can be satisfied by the other's answer."""
    u = g * E
    union = np.zeros(T, bool); snapshot = np.zeros(T, bool)
    for t in range(1, T + 1):
        o = np.argsort(-u[:t], kind="stable")
        us = u[:t][o]; gs = g[:t][o]; Es = E[:t][o]
        cp = gs * np.minimum(Es, 1.0)
        tail = np.concatenate([np.cumsum(cp[::-1])[::-1], [0.0]])
        best = 0
        for r in range(1, t + 1):
            if np.minimum(us[:r] - 1.0 / (d * r), gs[:r]).sum() + tail[r] >= 0.0:
                best = r
        snapshot = np.zeros(T, bool)
        if best:
            snapshot[o[:best]] = True
            union |= snapshot
    return snapshot, union


def ref_balance(E, g, d, T, r):
    """The (102) balance at a given r over the whole stream -- used to show which reading the
    source actually certifies."""
    u = g * E; o = np.argsort(-u, kind="stable")
    us = u[o]; gs = g[o]; Es = E[o]
    cp = gs * np.minimum(Es, 1.0)
    tail = np.concatenate([np.cumsum(cp[::-1])[::-1], [0.0]])
    return float(np.minimum(us[:r] - 1.0 / (d * r), gs[:r]).sum() + tail[r])


print()
print("  donation e-BH against a direct per-step evaluation of (102)")
# the regression case: the source's own sets are NOT nested, so a final snapshot loses one
d = 0.1; T = 7
g_flat = np.zeros(T + 2); g_flat[1:T + 1] = 1.0 / T
E = np.array([6.899, 78.075, 73.067, 98.354, 66.194, 58.858, 7.758])
ctx = hp.Ctx(E, np.zeros(T, bool), 1e9, alpha=d, w0=d / 2)
m_snap, _ = mask(hp.run_donation_ebh, ctx, g_flat, history="snapshot")
m_un, _ = mask(hp.run_donation_ebh, ctx, g_flat, history="union")
r_snap, r_un = ref_donation_ebh(E, g_flat[1:T + 1], d, T)
check("REGRESSION A: (102) snapshots are NOT nested -- an index is un-rejected",
      not np.array_equal(r_snap, r_un) and np.array_equal(m_snap, r_snap)
      and np.array_equal(m_un, r_un),
      f"snapshot {sorted(np.flatnonzero(r_snap) + 1)} vs union "
      f"{sorted(np.flatnonzero(r_un) + 1)}")

# the other horn: the union is not certified by the balance the source proves control from
d2 = 0.1; T2 = 20
g2 = np.zeros(T2 + 2); g2[1:T2 + 1] = 1.0 / 20.0
E2 = np.array([204.199992, 9.454431, 2969.74272, 4.80816409, 19.7742586, 0.198108812,
               718.304941, 0.469713687, 1.07314203, 0, 737.750908, 3.34147153, 0.110796884,
               1644.52378, 5.58748056, 1104.78936, 27.682788, 897.606872, 7.11649503,
               11.3058396])
ctx2 = hp.Ctx(E2, np.zeros(T2, bool), 1e9, alpha=d2, w0=d2 / 2)
s2, u2 = ref_donation_ebh(E2, g2[1:T2 + 1], d2, T2)
bal_union = ref_balance(E2, g2[1:T2 + 1], d2, T2, int(u2.sum()))
bal_snap = ref_balance(E2, g2[1:T2 + 1], d2, T2, int(s2.sum()))
m2s, _ = mask(hp.run_donation_ebh, ctx2, g2, history="snapshot")
m2u, _ = mask(hp.run_donation_ebh, ctx2, g2, history="union")
check("REGRESSION B: the union is NOT certified by the (102) balance",
      bal_snap >= 0.0 > bal_union and np.array_equal(m2s, s2) and np.array_equal(m2u, u2),
      f"balance at r=|snapshot|={int(s2.sum())} is {bal_snap:+.4f}; "
      f"at r=|union|={int(u2.sum())} is {bal_union:+.4f}")
check("  -- so the source licenses two readings and we report both, defaulting to (102) literal",
      int(s2.sum()) != int(u2.sum()),
      f"snapshot {int(s2.sum())} vs union {int(u2.sum())} rejections")

for trial in range(6):
    rng = np.random.default_rng(700 + trial)
    T = int(rng.integers(5, 26))
    E = np.where(rng.random(T) < 0.4, 0.0, rng.uniform(0, 200, T))
    for gk in ("poly", "uniform"):
        g1, _ = hp.make_gamma(gk, T)
        ctx = hp.Ctx(E, np.zeros(T, bool), 1e9, alpha=0.1, w0=0.05)
        m_s, _ = mask(hp.run_donation_ebh, ctx, g1, history="snapshot")
        m_u, _ = mask(hp.run_donation_ebh, ctx, g1, history="union")
        r_s, r_u = ref_donation_ebh(E, g1[1:T + 1], 0.1, T)
        check(f"donation e-BH snapshot == (102) [T={T}, {gk}, trial {trial}]",
              np.array_equal(m_s, r_s), f"{int(m_s.sum())} vs {int(r_s.sum())}")
        check(f"donation e-BH union == ARC history [T={T}, {gk}, trial {trial}]",
              np.array_equal(m_u, r_u), f"{int(m_u.sum())} vs {int(r_u.sum())}")

print()
print("  the fast path must agree with exact=True, including on adversarial streams")
for trial in range(8):
    rng = np.random.default_rng(800 + trial)
    T = int(rng.integers(30, 200))
    frac = [0.99, 0.9, 0.5, 0.1][trial % 4]
    E = np.where(rng.random(T) < frac, 0.0, rng.uniform(0, 1e5, T))
    for gk in ("poly", "uniform"):
        g1, _ = hp.make_gamma(gk, T)
        ctx = hp.Ctx(E, np.zeros(T, bool), 1e9, alpha=0.05, w0=0.025)
        mf = np.zeros(T, bool)
        hp.run_donation_ebh(ctx, g1, fired=mf, exact=False, history="union")
        mx = np.zeros(T, bool)
        hp.run_donation_ebh(ctx, g1, fired=mx, exact=True, history="union")
        check(f"fast == exact [T={T}, zero-frac {frac}, {gk}]", np.array_equal(mf, mx),
              f"{int(mf.sum())} vs {int(mx.sum())}")

print()
print("  donation e-LOND against a direct transcription of (26)-(28)")


def ref_donation_elond(E, g, CEIL, d, T):
    """(26)-(28) transcribed from the source, with no shared code with the implementation."""
    rej = np.zeros(T, bool); levels = np.zeros(T)
    for t in range(1, T + 1):
        Rn = int(rej[:t - 1].sum()) + 1
        W = 0.0
        for i in range(1, t):
            if rej[i - 1]:
                W += g[i] * min(E[i - 1] - 1.0 / (d * g[i] * Rn), 1.0) if g[i] > 0 else 0.0
            else:
                W += g[i] * min(E[i - 1], 1.0)
        den = 1.0 - min(d * Rn * W, 1.0)
        if g[t] <= 0.0:
            lvl = 0.0
        elif den <= 0.0:
            lvl = np.inf
        else:
            lvl = d * g[t] * Rn / den
        levels[t - 1] = lvl
        if lvl <= 0 or CEIL < 1.0 / lvl:
            continue
        if np.isinf(lvl) or E[t - 1] >= 1.0 / lvl:
            rej[t - 1] = True
    return rej, levels


nontrivial_dl = 0
for trial in range(8):
    rng = np.random.default_rng(950 + trial)
    T = int(rng.integers(20, 70))
    frac = [0.5, 0.85, 0.2][trial % 3]
    E = np.where(rng.random(T) < frac, 0.0, rng.uniform(0, 1e5, T))
    for gk in ("poly", "uniform"):
        g1, _ = hp.make_gamma(gk, T)
        M = 1e6
        ctx = hp.Ctx(E, np.zeros(T, bool), M, alpha=0.05, w0=0.025)
        m_impl, _ = mask(hp.run_donation_elond, ctx, g1)
        m_ref, lv = ref_donation_elond(E, g1, M, 0.05, T)
        nontrivial_dl += int(m_ref.sum() > 0)
        check(f"donation e-LOND == (26)-(28) [T={T}, {gk}, trial {trial}]",
              np.array_equal(m_impl, m_ref),
              f"{int(m_impl.sum())} vs {int(m_ref.sum())} rejections")
        # Proposition A measured on INDEPENDENTLY computed levels, not on a diagnostic
        R = 0; worst = 0.0
        for t in range(1, T + 1):
            if R == 0 and np.isfinite(lv[t - 1]) and g1[t] > 0:
                worst = max(worst, lv[t - 1] / (0.05 * g1[t]))
            if m_ref[t - 1]: R += 1
        check(f"  Prop A on independent levels [T={T}, {gk}]", worst <= 1.0 / (1.0 - 0.05) + 1e-9,
              f"cold-start boost {worst:.6f} <= {1/0.95:.6f}")
check("donation e-LOND reference cases are non-trivial", nontrivial_dl >= 8,
      f"{nontrivial_dl} of 16 reference runs rejected something")

print()
print("  e-TOAD at FINITE, non-trivial deadlines against a direct evaluation of (103)-(104)")


def ref_etoad(E, g, d, T, dl):
    """(103)-(104) evaluated directly, under the corrected reading A_t = {i<=t : d_i >= t}."""
    rej = np.zeros(T, bool)
    for t in range(1, T + 1):
        act = [i for i in range(1, t + 1) if dl[i - 1] >= t]
        aset = set(act)
        locked = sum(1 for i in range(1, T + 1) if rej[i - 1] and i not in aset)
        m_t = len(act)
        best = 0; found = False
        for r in range(locked, locked + m_t + 1):
            cnt = 0 if r == 0 else sum(1 for i in act if E[i - 1] * (d * g[i] * r) >= 1.0)
            if cnt >= r - locked:
                best = r; found = True
        r = best if found else 0
        if r > 0:
            for i in act:
                if E[i - 1] * (d * g[i] * r) >= 1.0:
                    rej[i - 1] = True
    return rej


nontrivial = 0
for trial in range(8):
    rng = np.random.default_rng(900 + trial)
    T = int(rng.integers(20, 60))
    E = np.where(rng.random(T) < [0.5, 0.8, 0.3][trial % 3], 0.0, rng.uniform(0, 5e4, T))
    width = int(rng.integers(3, 12))
    bucket = np.repeat(np.arange(T // width + 1), width)[:T]
    for dname, dl in (("bucket", hp.make_deadlines("bucket", T, bucket=bucket)),
                      ("time", hp.make_deadlines("time", T,
                                                 ts=np.arange(T, dtype=float),
                                                 horizon_s=float(width)))):
        g1, _ = hp.make_gamma("poly", T)
        ctx = hp.Ctx(E, np.zeros(T, bool), 1e9, alpha=0.05, w0=0.025)
        m_impl, _ = mask(hp.run_etoad, ctx, g1, deadline=dl)
        m_ref = ref_etoad(E, g1, 0.05, T, dl)
        if m_ref.sum() > 0: nontrivial += 1
        check(f"e-TOAD({dname}) == (103)-(104) [T={T}, width={width}, trial {trial}]",
              np.array_equal(m_impl, m_ref),
              f"{int(m_impl.sum())} vs {int(m_ref.sum())} rejections")
check("finite-deadline cases are non-trivial (not all zero-rejection)", nontrivial >= 8,
      f"{nontrivial} of 16 reference runs rejected something")

# ======================================================================================
print("=" * 100)
print("6c. gamma_i = 0 leaves the bar unsatisfiable at any wealth")
print("=" * 100)
T = 22
g0 = np.zeros(T + 2); g0[1:21] = 1.0 / 20.0          # gamma_21 = gamma_22 = 0
E = np.zeros(T); E[:20] = 1e9
ctx = hp.Ctx(E, np.zeros(T, bool), 1e12, alpha=0.05, w0=0.025)
for nm, fn in (("donation e-LOND", hp.run_donation_elond),
               ("donation e-BH", hp.run_donation_ebh),
               ("closed e-LOND", hp.run_closed_elond)):
    m, _ = mask(fn, ctx, g0)
    check(f"{nm}: no zero-gamma hypothesis is rejected",
          not m[20:].any(), f"rejected indices >= 21: {list(np.flatnonzero(m[20:]) + 21)}")

# ======================================================================================
print("=" * 100)
print("7. validity sanity under the null (FDP averaged over replicates <= delta)")
print("=" * 100)
print("   Not a proof -- their theorems are.  A gross implementation error would show here.")
T, M, alpha, B = 300, 200.0, 0.2, 200
g1, _ = hp.make_gamma("poly", T)
acc = {k: [] for k in ("e-LOND", "donation e-LOND", "closed e-LOND",
                       "online e-BH", "donation e-BH", "e-TOAD(bucket)")}
bucket = np.repeat(np.arange(T // 30), 30)[:T]
dl_b = hp.make_deadlines("bucket", T, bucket=bucket)
for b in range(B):
    rng = np.random.default_rng(9000 + b)
    # all-null two-point e-values: P(e = M) = 1/M so E[e] = 1
    Ev = np.where(rng.random(T) < 1.0 / M, M, 0.0)
    ctx = hp.Ctx(Ev, np.zeros(T, bool), M, alpha=alpha, w0=alpha / 2)
    for nm, fn, kw in (("e-LOND", hp.run_lond, {}),
                       ("donation e-LOND", hp.run_donation_elond, {}),
                       ("closed e-LOND", hp.run_closed_elond, {}),
                       ("donation e-BH", hp.run_donation_ebh, {}),
                       ("e-TOAD(bucket)", hp.run_etoad, dict(deadline=dl_b))):
        r = fn(ctx, g1, **kw)[0]
        acc[nm].append(1.0 if r > 0 else 0.0)          # all nulls: FDP = 1 iff any rejection
    acc["online e-BH"].append(1.0 if hp.run_online_ebh(ctx, g1)[0] > 0 else 0.0)
for nm, v in acc.items():
    fdr = float(np.mean(v))
    check(f"{nm}: all-null FDR <= {alpha}", fdr <= alpha + 3 * np.sqrt(alpha * (1 - alpha) / B),
          f"{fdr:.4f} over {B} replicates")

# ======================================================================================
print("=" * 100)
print("8. the deadline is a genuine interpolation (power is monotone in it)")
print("=" * 100)
for trial, (T, npos, M) in enumerate([(300, 40, 5_000.0), (300, 15, 50_000.0)]):
    rng = np.random.default_rng(600 + trial)
    Ev, ismal = two_point_stream(T, npos, M, rng, mal_frac=1.0)
    ctx = hp.Ctx(Ev, ismal, M, alpha=0.05, w0=0.025)
    g1, _ = hp.make_gamma("poly", T)
    bucket = np.repeat(np.arange(T // 50 + 1), 50)[:T]
    got = []
    for nm, dl in (("immediate", hp.make_deadlines("immediate", T)),
                   ("bucket", hp.make_deadlines("bucket", T, bucket=bucket)),
                   ("arc", hp.make_deadlines("arc", T))):
        dgg = {}
        r = hp.run_etoad(ctx, g1, dl, diag=dgg)
        got.append((nm, r[0], r[1], r[2], dgg["max_r"]))
    print("      deadline      rej   tp  silent  max_r")
    for nm, r, tp, sil, mr in got:
        print(f"      {nm:<12} {r:>5} {tp:>4} {sil:>7} {mr:>6}")
    check(f"rejections non-decreasing in the deadline [T={T}]",
          got[0][1] <= got[1][1] <= got[2][1],
          " <= ".join(str(x[1]) for x in got))

# ======================================================================================
print("=" * 100)
print("9. the shipped copy the experiment stages import is current")
print("=" * 100)
same, why = check_shipped_copy_is_current()
check("src/lib/h6_procs.py is the current strip of proto/h6_procs.py", bool(same), why)

# ======================================================================================
print("=" * 100)
print(f"{len(fails)} failure(s)" + ("" if not fails else ": " + "; ".join(fails)))
print("=" * 100)
sys.exit(1 if fails else 0)
