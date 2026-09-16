"""
E4 -- calibration contamination.  What happens to threshold conformal evidence when the
"clean benign" calibration set silently contains attack flows.

Reviewer objection (docs/02_WORKPLAN_PHASE4.md E4): "You assume a large clean benign
calibration set.  In security, how do you know the calibration period is attack-free?"
Sharpened by A1 (section 4.31), which found label problems in this very dataset.

Every closed form used here is derived and numerically verified in t38a_E4_derivation.py.
A disagreement between the two is a bug, not a finding.  The derivation changed the
measurement design in three ways, and each is marked [D..] where it bites:

  D3a  the ADVERSARIAL arm has no rate dependence at k = 1 -- the top eps*N attack flows
       share the same maximum for every eps > 0 -- so the eps sweep is supplemented by a
       per-FLOW sweep j = 1..10, which is the axis that actually moves.
  D3b  the RANDOM arm's transition sits at eps* = 1/(N*q0), where q0 is the exceedance rate
       OF THE CONTAMINATION POOL against the clean calibration maximum -- NOT the test-window
       malicious firing rate.  The two differ whenever the calibration and deployment windows
       have different attack score distributions, which F9 says they do; a first version of
       this script used the test-window rate and predicted a transition at ~30 flows where
       the measurement showed 2.  The workplan grid starts at 1e-5, so 1e-7 and 1e-6 are
       added to bracket the transition from below -- and even 1e-7 rounds to ZERO flows at
       |C| ~ 2e6, so the per-flow sweep is the only axis with resolution near eps*.
  D6a  monotonicity holds only if the contaminating sets NEST, so the sweep takes prefixes
       of ONE shuffled pool rather than redrawing at each eps.

Runs at positions 0.55 (guarantee) and 0.85 (stress), k = 1, both injection models, and
both the additive and size-matched-replacement calibration models.

Outputs out/t38_E4.json.
"""
import numpy as np, json, time, math
from pathlib import Path
from scipy.special import zeta
from scipy.stats import hypergeom, beta as beta_dist

import h_stream as hs
from h6_procs import Ctx, make_gamma, run_lond, run_lordpp

# Anchor to THIS file's directory: a run from a different cwd would
# otherwise write a second copy of the artefact somewhere else and leave
# the real one stale, which is exactly how a stale JSON gets audited.
OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)
t0 = time.time()

POS = (0.55, 0.85)
K = 1; A = 0.05; W0 = 0.025; BUCKET = 2 * 3600; SEED = 0
EPS = (0.0, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2)          # [D3b] extended below 1e-5
JSWEEP = (0, 1, 2, 3, 5, 10)                             # [D3a] the axis that moves
ACOUNT = (1, 2, 3, 5, 10)          # per-flow counts for the two Monte-Carlo arms
NPERM_T = 20_000                   # permutations for the cheap threshold-move probability
NPERM_R = 400                      # full-pipeline draws for the recall spread; 40 gave a
                                   # binomial SE of ~0.08 on P(recall = 0), too coarse to
                                   # quote the numbers the sweep produces
out = {"config": dict(pos=list(POS), k=K, alpha=A, w0=W0, bucket_s=BUCKET, seed=SEED,
                      eps=list(EPS), j_sweep=list(JSWEEP), a_counts=list(ACOUNT),
                      n_perm_threshold=NPERM_T, n_perm_recall=NPERM_R,
                      derivation="t38a_E4_derivation.py")}
FAIL = []


def note(cond, msg):
    """A recorded assertion: violations are collected and re-raised at the end rather than
    aborting a 20-minute run halfway through and losing the rows already computed."""
    if not cond:
        FAIL.append(msg)
        print(f"    *** ASSERTION FAILED: {msg}")
    return cond


# =======================================================================================
# The primitives.  Module level so t38b_E4_selftest.py can import and mutate the SHIPPED
# code rather than a copy of it (the round-3 mutation lesson, standing mistake 16).
# =======================================================================================
def contaminate(cal_clean, pool, a, model):
    """Build a contaminated calibration score array.

    model 'additive'     : C = C0 u A[:a]        |C| = N + a   [D2a] ceiling rises (1+eps)
    model 'replacement'  : C = C0[a:] u A[:a]    |C| = N       ceiling EXACTLY unchanged

    The replacement arm exists only to show that the <=1% ceiling shift of the additive arm
    explains nothing, so the flows it removes are the a LOWEST-scoring clean ones.  Under
    D2b's random removal the threshold can FALL (the removed set may contain c0_(k)), which
    would put sampling noise into a control whose whole job is to isolate the injection
    effect.  Removing from the bottom cannot move c_(k) by itself, so any threshold change
    on this arm is attributable to the injection alone.  It is a deliberately favourable
    removal rule and is reported as such, not as the physical model -- additive is that.

    `pool` must already be in the order the sweep consumes it, so that successive a give
    NESTED injected sets -- D6a fails otherwise and monotonicity cannot be asserted.
    """
    cal_clean = np.sort(np.asarray(cal_clean, dtype=float))
    a = int(a)
    if a <= 0:
        return np.asarray(cal_clean)
    if a > len(pool):
        raise ValueError(f"pool exhausted: need {a}, have {len(pool)}")
    if model == "replacement" and a > len(cal_clean) - K:
        raise ValueError(f"bottom-drop replacement would leave fewer than k={K} clean "
                         f"scores: a={a}, |C0|={len(cal_clean)}")
    inj = np.asarray(pool[:a])
    if model == "additive":
        return np.concatenate([cal_clean, inj])
    if model == "replacement":
        return np.concatenate([cal_clean[a:], inj])   # drop the a LOWEST clean scores
    raise ValueError(f"unknown model {model!r}")


def fire_mask(cal_sorted, s_te, k=1):
    """h_stream.evalues' firing rule, as a mask.  Kr = 1 + #{c >= s}; fire iff Kr <= k,
    equivalently s > c_(k)  [D1a]."""
    NC = len(cal_sorted)
    Kr = 1 + (NC - np.searchsorted(cal_sorted, s_te, side="left"))
    return Kr <= k


def evalues_from(cal_unsorted, s_te, k=1):
    """Re-implement nothing: sort, then call h_stream.evalues' own arithmetic through a
    label vector of all zeros, so the shipped function is what produces the e-values."""
    cal_u = np.asarray(cal_unsorted, dtype=float)
    e, cal, NC, CEIL = hs.evalues(cal_u, np.zeros(len(cal_u), dtype=np.int64), s_te, k=k)
    return e, cal, NC, CEIL


def margin(NC, k=1, lvl=W0):
    """A safety-indicator diagnostic, NOT the paper's eq:margin.  This returns
    (CEIL - 1/lvl)/CEIL, a monotone-in-CEIL quantity used only to show the indicator moves the
    WRONG WAY under contamination.  The paper's feasibility margin is (|C|+1)*w0/T - 1, which
    also rises under contamination (it increases |C|); both make the same point.  Do not read
    this field as eq:margin -- see paper sec:contamination."""
    CEIL = (NC + 1.0) / k
    return (CEIL - 1.0 / lvl) / CEIL


def wilson(x, n, z=1.959963985):
    """Wilson score interval.  P(recall = 0) is a binomial proportion and 40 draws put a
    standard error of ~0.08 on it; quoting 1.00 from 40/40 claims a precision the sample
    does not have.  Reported as an interval throughout."""
    if n == 0:
        return (float("nan"), float("nan"))
    ph = x / n
    d = 1.0 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def fdp_recall(fired, ismal, n_mal):
    """FDP is UNDEFINED with no rejections, not 0.  Reporting 0.0 there makes a collapsed
    configuration read as "no false discoveries" when it means "no discoveries" -- and most
    of this sweep's rows are collapsed.  fdp is None in that case and fdp_conv keeps the
    0-convention for anything that has to average."""
    r = int(fired.sum()); tp = int((fired & ismal).sum())
    return dict(rejections=r, tp=tp, fp=r - tp,
                fdp=(float((r - tp) / r) if r else None),
                fdp_conv=float((r - tp) / r) if r else 0.0,
                recall=float(tp / n_mal) if n_mal else 0.0)


def episode_evidence(part, e_te):
    """Re-aggregate e-values onto a FIXED episode partition.

    The partition (gid, order, nsz, ismal) is a function of the keys and timestamps only,
    so contamination cannot move it -- only sum_e changes.  Rebuilding it for every one of
    the ~2,500 settings in this sweep would dominate the runtime and buy nothing.  The
    partition still comes from hs.build_episodes; only the bincount is repeated here, and
    check_partition_invariance() below asserts against a full rebuild rather than trusting
    the argument.
    """
    sum_e = np.bincount(part["gid"], weights=e_te, minlength=part["T"])[part["order"]]
    return sum_e / np.maximum(part["nsz"], 1)


def run_one(cal_unsorted, s_te, y_te, ts_w, src_w, dst_w, k=K, part=None):
    """One contamination setting, end to end: e-values -> episodes -> LOND and LORD++."""
    e_te, cal, NC, CEIL = evalues_from(cal_unsorted, s_te, k=k)
    if part is None:
        ep = hs.build_episodes(e_te, y_te, ts_w, src_w, dst_w, BUCKET, "src-dst")
    else:
        ep = dict(part, Ev=episode_evidence(part, e_te))
    ctx = Ctx(ep["Ev"], ep["ismal"], CEIL, alpha=A, w0=W0)
    g1, g0 = make_gamma("poly", ep["T"])
    res = {}
    for nm, fn in (("lond", run_lond), ("lordpp", run_lordpp)):
        fired = np.zeros(ep["T"], bool)
        fn(ctx, g1, fired=fired)
        res[nm] = fdp_recall(fired, ep["ismal"], ep["n_mal"])
    fire = e_te > 0
    return dict(NC=int(NC), CEIL=float(CEIL), thresh=float(cal[-1]),
                # [D4'a] the per-flow p-value of a FIRING flow is 1/CEIL, so the ceiling
                # channel is visible directly: a larger |C| makes a firing flow's evidence
                # larger and its p-value smaller, with the threshold held fixed.
                p_per_firing_flow=float(1.0 / CEIL),
                margin=float(margin(NC, k)),
                f_benign=float(fire[y_te == 0].mean()),
                f_malicious=float(fire[y_te == 1].mean()) if (y_te == 1).any() else 0.0,
                n_fire=int(fire.sum()), T=int(ep["T"]), n_mal_ep=int(ep["n_mal"]),
                **res), fire, ep


# =======================================================================================
print("=" * 118)
print("E4 -- CALIBRATION CONTAMINATION")
print("=" * 118)
X, y, ts, src, dst = hs.load()
N = len(y)
out["rows"] = []
out["jrows"] = []

for pos in POS:
    print("\n" + "=" * 118)
    print(f"POSITION {pos}")
    print("=" * 118)
    i1, i2, i3 = hs.split_indices(N, pos)
    score = hs.fit_detector(X, y, i1, seed=SEED, kind="hgb", verbose=False)
    s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
    y_cal = y[i1:i2]; y_te = y[i2:i3]
    cal_clean = np.sort(s_cal[y_cal == 0])
    Ncal = len(cal_clean)

    # The contamination pool is the malicious flows OF THE CALIBRATION WINDOW ITSELF: the
    # physical model is "the labeller missed attacks that were already there".  Drawing
    # from the training window would use in-sample scores (the detector was fitted on those
    # rows) and would overstate the adversarial arm; drawing from the TEST window would
    # leak the evaluation split (standing mistake 4).
    pool_all = s_cal[y_cal == 1]
    n_pool = len(pool_all)
    print(f"  |C| = {Ncal:,}  calibration-window malicious flows available = {n_pool:,}  "
          f"test flows = {len(y_te):,} ({int(y_te.sum()):,} malicious)  "
          f"[{time.time()-t0:.0f}s]")

    # The episode partition, built ONCE from the shared module and then reused.
    e0, _, _, _ = hs.evalues(cal_clean, np.zeros(len(cal_clean), dtype=np.int64), s_te, k=K)
    part = hs.build_episodes(e0, y_te, ts[i2:i3], src[i2:i3], dst[i2:i3], BUCKET, "src-dst")
    base, base_fire, base_ep = run_one(cal_clean, s_te, y_te, ts[i2:i3], src[i2:i3],
                                       dst[i2:i3], part=part)
    fM0 = base["f_malicious"]
    # [D3b] the estimand is the POOL's exceedance rate against the clean calibration
    # maximum -- the probability that ONE randomly mislabelled calibration-window attack
    # flow would itself have fired.  The test-window malicious firing rate fM0 is a
    # DIFFERENT number (different window, F9 drift) and substituting it mis-predicts the
    # transition by an order of magnitude.  Both are reported.
    q0 = float((pool_all > cal_clean[-1]).mean())
    eps_star = 1.0 / (Ncal * q0) if q0 > 0 else np.inf
    _f = lambda v: "  -  " if v is None else f"{v:.3f}"
    print(f"  clean: threshold={base['thresh']:.6f}  f_benign={base['f_benign']:.3e}  "
          f"f_malicious(test)={fM0:.4f}  LOND recall={base['lond']['recall']:.3f} "
          f"FDP={_f(base['lond']['fdp'])}")
    print(f"  [D3b] pool exceedance q0 = {q0:.4f} ({int((pool_all > cal_clean[-1]).sum()):,}"
          f" of {n_pool:,} pool flows would themselves fire)")
    print(f"        eps* = 1/(N*q0) = {eps_star:.3e} = {eps_star*Ncal:.2f} flows;  using the"
          f" test-window rate {fM0:.4f} instead would say {1.0/(Ncal*fM0)*Ncal:.1f} flows")

    # The two pools, each in the ORDER THE SWEEP CONSUMES THEM so prefixes nest [D6a].
    rng = np.random.default_rng(20260827 + int(pos * 100))
    pools = {"random": pool_all[rng.permutation(n_pool)],
             "adversarial": np.sort(pool_all)[::-1]}       # highest-scoring first [D3a]
    print(f"  pool score max = {pool_all.max():.6f} vs clean calibration max = "
          f"{cal_clean[-1]:.6f}  -> one top attack flow "
          f"{'DOES' if pool_all.max() > cal_clean[-1] else 'does NOT'} move the threshold")

    for model in ("additive", "replacement"):
        for inj, pool in pools.items():
            print(f"\n  --- {model} / {inj} " + "-" * (100 - len(model) - len(inj)))
            print(f"  {'eps':>8} {'a':>10} {'|C|':>11} {'CEIL':>12} {'thresh':>10} "
                  f"{'f_ben':>10} {'f_mal':>9} {'margin':>9} {'recall':>8} {'FDP':>7}")
            prev_fire = None
            for eps in EPS:
                a = int(round(eps * Ncal))
                if a > n_pool:
                    print(f"  {eps:>8.0e} {a:>10,}  POOL EXHAUSTED ({n_pool:,} available)"
                          f" -- not run")
                    continue
                cal_c = contaminate(cal_clean, pool, a, model)
                r, fire, _ = run_one(cal_c, s_te, y_te, ts[i2:i3], src[i2:i3],
                                     dst[i2:i3], part=part)
                # PARTITION INVARIANCE, asserted rather than argued: on the first two
                # contaminated settings of each block, rebuild the episodes from scratch
                # through hs.build_episodes and require identical Ev.
                if a and len([1 for _ in (0,)]) and r["NC"] and a <= 2:
                    _full, _, _ = run_one(cal_c, s_te, y_te, ts[i2:i3], src[i2:i3],
                                          dst[i2:i3], part=None)
                    note(_full["lond"] == r["lond"] and _full["CEIL"] == r["CEIL"],
                         f"partition reuse disagrees with a full rebuild at pos={pos} "
                         f"{model}/{inj} a={a}")
                r.update(pos=pos, eps=eps, a=a, model=model, injection=inj,
                         effective_eps=a / Ncal, contaminated=bool(a))
                out["rows"].append(r)
                print(f"  {eps:>8.0e} {a:>10,} {r['NC']:>11,} {r['CEIL']:>12,.0f} "
                      f"{r['thresh']:>10.5f} {r['f_benign']:>10.3e} "
                      f"{r['f_malicious']:>9.4f} {r['margin']:>9.6f} "
                      f"{r['lond']['recall']:>8.3f} "
                      f"{'   -' if r['lond']['fdp'] is None else format(r['lond']['fdp'], '>7.3f')}")
                if model == "additive":
                    # [D6a] additive + nested pool => the firing set only shrinks
                    if prev_fire is not None:
                        note(not (fire & ~prev_fire).any(),
                             f"D6a firing set grew at pos={pos} {model}/{inj} eps={eps:.0e}")
                    # [D2a] the ceiling rises by exactly (1+a/(N+1))
                    note(abs(r["CEIL"] - (Ncal + a + 1.0) / K) < 1e-6,
                         f"D2a ceiling wrong at eps={eps:.0e}")
                    # [D5a] the feasibility margin improves while firing collapses
                    note(r["margin"] >= base["margin"] - 1e-12,
                         f"D5a margin fell at eps={eps:.0e}")
                    prev_fire = fire
                else:
                    note(abs(r["CEIL"] - base["CEIL"]) < 1e-9,
                         f"D2b replacement changed the ceiling at eps={eps:.0e}")

    # ------------------------------------------------------------------------------
    # [D3a] the per-FLOW sweep: the axis on which the adversarial arm actually moves
    # ------------------------------------------------------------------------------
    print(f"\n  --- per-flow sweep, additive, j mislabelled flows " + "-" * 56)
    print(f"  [D3a] at k = {K} the tolerable adversarial count is k-1 = {K-1}.  j = 1 should")
    print(f"        already hand the threshold to the attacker; eps is the wrong axis.")
    print(f"  {'injection':>12} {'j':>4} {'thresh':>10} {'f_ben':>11} {'f_mal':>9} "
          f"{'recall':>8} {'FDP':>7} {'rejections':>11}")
    for inj, pool in pools.items():
        for j in JSWEEP:
            cal_c = contaminate(cal_clean, pool, j, "additive")
            r, jfire, _ = run_one(cal_c, s_te, y_te, ts[i2:i3], src[i2:i3], dst[i2:i3],
                                  part=part)
            r.update(pos=pos, j=j, model="additive", injection=inj)
            out["jrows"].append(r)
            print(f"  {inj:>12} {j:>4} {r['thresh']:>10.5f} {r['f_benign']:>11.3e} "
                  f"{r['f_malicious']:>9.4f} {r['lond']['recall']:>8.3f} "
                  f"{'   -' if r['lond']['fdp'] is None else format(r['lond']['fdp'], '>7.3f')} "
                  f"{r['lond']['rejections']:>11,}")
    # [D3a] the adversarial step: every eps > 0 gives the SAME threshold as j = 1
    # Filter on a >= 1, NOT eps > 0: at |C| ~ 2e6 the grid point eps = 1e-7 rounds to ZERO
    # injected flows, so it is a clean run wearing a contaminated label.  Comparing it to
    # j = 1 tests nothing and fails spuriously.
    adv = [r for r in out["rows"]
           if r["pos"] == pos and r["model"] == "additive"
           and r["injection"] == "adversarial" and r["a"] >= 1]
    adv1 = [r for r in out["jrows"]
            if r["pos"] == pos and r["injection"] == "adversarial" and r["j"] == 1]
    if adv and adv1:
        same = all(abs(r["thresh"] - adv1[0]["thresh"]) < 1e-12 for r in adv)
        note(same, f"D3a adversarial threshold varied with eps at pos={pos}")
        print(f"  [D3a] adversarial threshold identical for every eps with a >= 1 and "
              f"for j = 1: {same}  ({len(adv)} rows compared)")

    # ------------------------------------------------------------------------------
    # [D3b] MONTE CARLO: the closed form is a probability, so one draw per eps cannot test
    # it.  The threshold-move indicator is cheap (a max, no episode rebuild), so it is run
    # over many permutations and checked against 1-(1-q0)^a with power gating.
    # ------------------------------------------------------------------------------
    print(f"\n  --- [D3b] threshold-move probability, {NPERM_T:,} permutations " + "-" * 44)
    print(f"  {'a':>4} {'measured':>10} {'hypergeom':>12} {'1-(1-q0)^a':>14} "
          f"{'5-sigma':>10} {'verdict':>10}")
    mcrows = []
    rngm = np.random.default_rng(777 + int(pos * 100))
    for a in ACOUNT:
        if a > n_pool:
            continue
        # WITHOUT replacement, matching how the recall-spread arm and any real poisoner
        # draw; the closed form is then hypergeometric, not (1-q0)^a.
        #
        # Sampled by drawing the NUMBER of exceeders directly, not by materialising the
        # sample.  `np.argsort(rng.random((NPERM_T, n_pool)))` is the obvious way to draw
        # `a` of `n_pool` without replacement and it allocates NPERM_T x n_pool floats --
        # 102 GB at position 0.85, where the pool is 639,913 flows.  The count of exceeders
        # in a size-a draw IS hypergeometric, so drawing it is exact and costs nothing.
        Qp = int((pool_all > cal_clean[-1]).sum())
        moved = float((rngm.hypergeometric(Qp, n_pool - Qp, a, size=NPERM_T) > 0).mean())
        want = float(1.0 - hypergeom.pmf(0, n_pool, Qp, a))
        want_wr = 1.0 - (1.0 - q0) ** a
        sig = 5.0 * np.sqrt(max(want * (1.0 - want), 1e-30) / NPERM_T)
        if want <= 0 or sig > 0.25 * want:
            verdict = "no power"
        else:
            ok = abs(moved - want) <= sig
            verdict = "ok" if ok else "MISMATCH"
            note(ok, f"D3b threshold-move probability off at pos={pos} a={a}: "
                     f"{moved:.4f} vs {want:.4f} +- {sig:.4f}")
        mcrows.append(dict(pos=pos, a=a, measured=moved, closed_form=want,
                           closed_form_with_replacement=float(want_wr),
                           five_sigma=float(sig), verdict=verdict))
        print(f"  {a:>4} {moved:>10.4f} {want:>12.6f} {want_wr:>14.6f} {sig:>10.4f} "
              f"{verdict:>10}")
    out.setdefault("d3b_mc", []).extend(mcrows)

    # ------------------------------------------------------------------------------
    # The operational spread: recall under RANDOM mislabelling is a random variable, and
    # a single draw per eps (as the workplan specifies) reports one sample of it.
    # ------------------------------------------------------------------------------
    print(f"\n  --- random mislabelling, {NPERM_R} draws per a, full pipeline " + "-" * 36)
    print(f"  {'a':>4} {'recall med':>11} {'recall min':>11} {'recall max':>11} "
          f"{'P(rec=0)':>8} {'95% Wilson':>15} {'FDP max':>9} {'f_mal med':>10}")
    rngr = np.random.default_rng(999 + int(pos * 100))
    for a in ACOUNT:
        if a > n_pool:
            continue
        recs = []; fdps = []; fms = []
        for _ in range(NPERM_R):
            sel = pool_all[rngr.choice(n_pool, size=a, replace=False)]
            r, _, _ = run_one(np.concatenate([cal_clean, sel]), s_te, y_te,
                              ts[i2:i3], src[i2:i3], dst[i2:i3], part=part)
            recs.append(r["lond"]["recall"]); fdps.append(r["lond"]["fdp"])
            fms.append(r["f_malicious"])
        recs = np.array(recs)
        out.setdefault("spread", []).append(dict(
            pos=pos, a=a, n_draws=NPERM_R, recall_median=float(np.median(recs)),
            recall_min=float(recs.min()), recall_max=float(recs.max()),
            recall_q10=float(np.quantile(recs, 0.10)),
            recall_q90=float(np.quantile(recs, 0.90)),
            p_recall_zero=float((recs == 0).mean()),
            p_recall_zero_ci=list(wilson(int((recs == 0).sum()), NPERM_R)),
            fdp_max=(None if all(f is None for f in fdps)
                     else float(max(f for f in fdps if f is not None))),
            n_zero_rejection_draws=int(sum(1 for f in fdps if f is None)),
            f_mal_median=float(np.median(fms)), recall_clean=base["lond"]["recall"]))
        lo, hi = wilson(int((recs == 0).sum()), NPERM_R)
        fdm = [f for f in fdps if f is not None]
        print(f"  {a:>4} {np.median(recs):>11.3f} {recs.min():>11.3f} {recs.max():>11.3f} "
              f"{(recs==0).mean():>8.3f} [{lo:.3f},{hi:.3f}] "
              f"{('    -' if not fdm else format(max(fdm), '>9.3f'))} "
              f"{np.median(fms):>10.4f}")
        # (the tautological `max(fdps) <= 1` check that used to sit here tested nothing)

    # ------------------------------------------------------------------------------
    # [D4'] THE VALIDITY CHANNEL, measured rather than asserted.
    # D4a-c prove the FULL conformal p-value only rises under contamination.  The pipeline
    # uses the THRESHOLDED e-value, whose p-value carries M in the denominator, so a
    # contaminating flow that does NOT clear the threshold inflates every firing flow's
    # evidence by exactly 1 + eps and LOWERS its p-value.  That is anti-conservative and it
    # is a validity effect, not a power one.  It is driven here deliberately, by injecting
    # flows chosen to score BELOW the clean maximum -- the stealth poisoner of D4'd.
    # ------------------------------------------------------------------------------
    # Flows that do NOT move the threshold are those at or BELOW the clean maximum -- `<=`,
    # not `<`: a tie at the maximum leaves the maximum where it is.  And they must be SORTED
    # to be "highest-below first"; `below[::-1]` merely reverses calibration-window order,
    # which is not an ordering at all.  Neither correction moves a number here (there are no
    # ties at the maximum, and the ceiling channel depends on the COUNT injected rather than
    # on which flows), but the comment was describing something the code did not do.
    below = np.sort(pool_all[pool_all <= cal_clean[-1]])[::-1]
    print(f"\n  --- [D4'] the ceiling channel: injection BELOW the clean maximum " + "-" * 32)
    print(f"  {len(below):,} of {n_pool:,} pool flows score below the clean calibration max, "
          f"so a stealth")
    print(f"  poisoner has {len(below):,} usable flows; a random draw hits one with "
          f"probability {1-q0:.4f}.")
    print(f"  {'a':>8} {'|C|':>12} {'CEIL':>12} {'thresh':>10} {'p per firing flow':>19} "
          f"{'ratio to clean':>15} {'1+eps':>10} {'recall':>8}")
    d4rows = []
    for a in (0, 1, 10, 100, 1000, 10000, len(below)):
        if a > len(below):
            continue
        cal_c = contaminate(cal_clean, below, a, "additive")   # highest-below-max first
        r, fire, _ = run_one(cal_c, s_te, y_te, ts[i2:i3], src[i2:i3], dst[i2:i3], part=part)
        ratio = r["p_per_firing_flow"] / base["p_per_firing_flow"]
        one_eps = 1.0 + a / (Ncal + 1.0)
        d4rows.append(dict(pos=pos, a=a, NC=r["NC"], CEIL=r["CEIL"], thresh=r["thresh"],
                           p_per_firing_flow=r["p_per_firing_flow"], ratio=float(ratio),
                           one_plus_eps=float(one_eps), recall=r["lond"]["recall"],
                           rejections=r["lond"]["rejections"], fdp=r["lond"]["fdp"],
                           effective_q=float(A * one_eps)))
        print(f"  {a:>8,} {r['NC']:>12,} {r['CEIL']:>12,.0f} {r['thresh']:>10.5f} "
              f"{r['p_per_firing_flow']:>19.6e} {ratio:>15.9f} {one_eps:>10.7f} "
              f"{r['lond']['recall']:>8.3f}")
        if a:
            # [D4'b] the threshold must NOT move, and the p-value must fall by exactly 1+eps
            note(abs(r["thresh"] - base["thresh"]) < 1e-12,
                 f"D4'b threshold moved under below-max injection at pos={pos} a={a}")
            note(abs(ratio * one_eps - 1.0) < 1e-9,
                 f"D4'b p-value ratio {ratio:.9f} is not 1/(1+eps) = {1/one_eps:.9f} "
                 f"at pos={pos} a={a}")
    out.setdefault("d4prime", []).extend(d4rows)
    worst = max(d4rows, key=lambda d: d["one_plus_eps"])
    print(f"  -> worst validity degradation on this arm: q = {A} becomes at most "
          f"{worst['effective_q']:.6f} at a = {worst['a']:,} ({worst['a']/Ncal:.2e} of |C|),")
    print(f"     while ONE adversarial flow above the maximum takes recall to 0.  The "
          f"validity channel is bounded by 1+eps; the power channel is not bounded at all.")

    out.setdefault("baseline", {})[str(pos)] = dict(
        base, eps_star=float(eps_star), q0=float(q0), n_pool=int(n_pool),
        Ncal=int(Ncal), pool_max=float(pool_all.max()), clean_max=float(cal_clean[-1]),
        n_pool_would_fire=int((pool_all > cal_clean[-1]).sum()),
        f_mal_test_window=float(fM0))

# =======================================================================================
# The JSON is written BEFORE the summary is printed.  An earlier version printed first and
# lost a completed twenty-minute run to a format string that met a None -- the summary is
# presentation, and presentation must not be able to destroy measurement.
out["assertions_failed"] = FAIL
json.dump(out, open(OUT / "t38_E4.json", "w"), indent=1)
print(f"\n  wrote out/t38_E4.json  ({len(out['rows'])} eps rows, {len(out['jrows'])} j rows, "
      f"{len(out.get('spread', []))} spread rows, {len(out.get('d4prime', []))} D4' rows)")

print("\n" + "=" * 118)
print("SUMMARY -- THE TOLERANCE, IN THE UNITS THAT ACTUALLY GOVERN IT")
print("=" * 118)
for pos in POS:
    b = out["baseline"][str(pos)]
    jr = [r for r in out["jrows"] if r["pos"] == pos and r["injection"] == "adversarial"]
    j0 = next(r for r in jr if r["j"] == 0); j1 = next(r for r in jr if r["j"] == 1)
    rr = [r for r in out["rows"] if r["pos"] == pos and r["model"] == "additive"
          and r["injection"] == "random"]
    print(f"\n  position {pos}:  pool exceedance q0 = {b['q0']:.4f}  ->  "
          f"eps* = {b['eps_star']:.2e} ({b['eps_star']*b['Ncal']:.2f} flows)")
    sp = [r for r in out.get("spread", []) if r["pos"] == pos]
    for r in sp:
        print(f"    random a={r['a']:>3} over {r['n_draws']} draws: recall median "
              f"{r['recall_median']:.3f} (clean {r['recall_clean']:.3f}), range "
              f"[{r['recall_min']:.3f}, {r['recall_max']:.3f}], P(recall=0) = "
              f"{r['p_recall_zero']:.3f} "
              f"[{r['p_recall_zero_ci'][0]:.3f}, {r['p_recall_zero_ci'][1]:.3f}], "
              f"{r['n_zero_rejection_draws']} of {r['n_draws']} draws made no rejection at all")
    fdp = lambda v: "  -  " if v is None else f"{v:.3f}"
    print(f"    adversarial, j=0 -> j=1 :  recall {j0['lond']['recall']:.3f} -> "
          f"{j1['lond']['recall']:.3f}   FDP {fdp(j0['lond']['fdp'])} -> "
          f"{fdp(j1['lond']['fdp'])}   f_mal {j0['f_malicious']:.4f} -> "
          f"{j1['f_malicious']:.4f}   rejections {j0['lond']['rejections']} -> "
          f"{j1['lond']['rejections']}")
    for r in rr:
        print(f"    random  eps={r['eps']:>8.0e} (a={r['a']:>7,}) :  recall "
              f"{r['lond']['recall']:.3f}  FDP {fdp(r['lond']['fdp'])}  "
              f"f_mal {r['f_malicious']:.4f}  margin {r['margin']:.6f}  "
              f"rejections {r['lond']['rejections']}")

print(f"\n  [{time.time()-t0:.0f}s]  all measurement complete")
if FAIL:
    print("  ASSERTIONS FAILED:")
    for m in FAIL:
        print("   -", m)
    raise SystemExit(1)
print("  all derivation assertions held")
