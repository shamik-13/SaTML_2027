"""R2d/non-claim-21 -- pricing the GROUP-CREATION attack that padding-robustness does not cover.

`thm:padding` and the suppression cost of sec:paddingcost are both about APPENDING flows to a fixed
hypothesis.  Two results in this paper leave a different lever unpriced and say so:

  * non-claim 21: under group-level calibration with the MAX statistic, appending cannot lower a
    maximum, so padding does not bite -- but "an adversary who CREATES groups can emit distinct keys
    ahead of a target and push it past a cold-start prefix only tens of groups wide.  We do not price
    that attack."
  * non-claim 25(i): the canonical key-hash order makes a group's slot a function of its own
    metadata, so padding moves no other group -- but a group's ABSOLUTE rank still depends on which
    other keys are present, so an adversary that creates keys does move ranks.

This stage prices it.  The lever is the same in both cases and it is the cold-start prefix: only the
first w_cold steps can reject anything before the first rejection, so an adversary that inserts
enough hypotheses AHEAD of its own pushes itself out of the only window in which it could have been
rejected.  Nothing is appended to the attacked episode, so `thm:padding` is irrelevant and the max
statistic's append-invariance buys nothing.

WHAT IT COSTS TO GET AHEAD OF THE TARGET, which is where the two orders differ and where an earlier
draft of this file was WRONG.  It is tempting to say no grinding is needed because both orders emit
in bucket-close order and an adversary can always send in an earlier bucket.  On this data that is
false: every detection lands in the FIRST bucket of its deployment window, so there is no earlier
bucket to occupy and the within-bucket tie-break is exactly what the attacker must beat.

  under FIRST-FLOW arrival   free: send the flows earlier inside the same bucket.  This is the
                             timing lever sec:transfer identifies, used to move OTHER hypotheses
                             rather than one's own.
  under the KEY-HASH order   an offline search: the inserted key must hash below the target's.  A
                             uniformly drawn candidate qualifies with probability h_target/2^63, so
                             G insertions need about G*2^63/h_target trials -- computation, not
                             traffic, reported per target as `expected_key_trials`.
  under the KEYED order      the seed is not public, so the ranking cannot be computed offline at
                             all.  Run here as a third arm; what it costs an adversary who cannot
                             rank keys is a different question we do not answer.

So the canonical order does not remove this attack; it converts a free timing manipulation into a
keyspace search.  THREE CONDITIONS the trial count assumes, none of them free:
  (i)   the hash seed is public (the keyed arm is exactly the case where it is not);
  (ii)  the adversary can realise G DISTINCT qualifying keys -- it needs that many endpoint pairs it
        can actually send between, not merely that many candidate integers;
  (iii) the target's hash is stable under the insertion.  IN THIS ARTEFACT IT IS NOT, strictly: the
        cache encodes IPs as pandas category codes over the addresses OBSERVED, so introducing new
        addresses would renumber them and change every hash.  A deployment would hash the raw
        address, for which the value is stable; the trial counts here are therefore indicative of
        the search's SIZE, not an exact operational figure.  Stated rather than hidden.

WHAT IS MEASURED.  For each e-LOND true detection, the minimal number G* of inserted hypotheses that
stops it being rejected, obtained by REPLAY rather than by a closed form: for each G we prepend G
synthetic groups, re-run e-LOND on the T+G stream, and record which of the original detections still
fire.  One run per G yields the answer for every target at once.  Two insertion kinds:

  "zero"    inserted groups carry no evidence.  The cheapest lever and the cleanest: they can never
            fire, so they only consume positions.
  "benign"  inserted groups carry evidence resampled from the window's own benign episodes.  This is
            what real traffic would look like, and it can BACKFIRE: an inserted group that fires is a
            rejection, which raises R, which widens the feasible window and can let the target back
            in.  Measured rather than assumed.

Monotonicity is NOT assumed.  A larger G can in principle restore a detection (through exactly the
bootstrap channel above), so we record both the first G at which a target stops firing and the LAST G
at which it still fires, and report where the two disagree.

The comparison that matters is against the padding cost of the same detections (`t28b`), in the same
unit: flows.  An inserted group needs at least one flow, so G* is a LOWER bound on the attack's flow
cost, on the same oracle footing as every other attack cost in the paper.

Writes out/t60_positional.json.
"""
import numpy as np, json, time
from pathlib import Path
from scipy.special import zeta

import h_stream as hs
from h6_procs import Ctx, make_gamma, run_lond

A = 0.05; W0 = 0.025; K = 1; BUCKET = 2 * 3600
POS = [0.55, 0.62, 0.70, 0.77, 0.85]
SEED = 0
ORDERS = ["keyhash", "keyed", "first-flow"]
KINDS = ["zero", "benign"]
G_STEP = 1                    # exact: every insertion count is replayed
G_HEADROOM = 1.6              # scan to G_HEADROOM * w_cold past the last detection's position


def cold_start(CEIL, T, R=0):
    """Largest step at which e-LOND can reject anything with R rejections so far, spelled exactly as
    Ctx.infeasible spells it, with the closed form beside it."""
    g1, _ = make_gamma("poly", T)
    lvl = A * g1[1:T + 1] * (R + 1.0)
    with np.errstate(divide="ignore"):
        ok = np.flatnonzero(np.where(lvl > 0, CEIL >= 1.0 / np.maximum(lvl, 1e-300), False))
    w = int(ok[-1] + 1) if ok.size else 0
    x = A * CEIL * (R + 1.0) / float(zeta(1.6, 1))
    return w, (int(np.floor(x ** (1.0 / 1.6))) if x > 0 else 0)


def lift_t57(names):
    """Lift t57's own nested calibration rules by AST, so this stage attacks the SAME group
    construction t57 measures rather than a re-implementation of it."""
    import ast, types
    src = (Path(__file__).resolve().parent / "t57_group_calibration.py").read_text()
    tree = ast.parse(src)
    want, got = [], set()
    consts = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name in names:
            want.append(n); got.add(n.name)
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id in ("A", "W0", "K", "ZETA16", "BUCKET"):
                    try:
                        consts[t.id] = ast.literal_eval(n.value)
                    except Exception:
                        pass
    if set(names) - got:
        raise SystemExit(f"cannot lift {set(names) - got} from t57_group_calibration.py")
    mod = types.ModuleType("t57_lifted")
    mod.__dict__.update(np=np, **consts)
    exec(compile(ast.fix_missing_locations(ast.Module(body=want, type_ignores=[])),
                 "<lifted>", "exec"), mod.__dict__)
    return mod


def targeted_gstar(Ev, ismal, CEIL, targets, R_before):
    """Cost of the TARGETED attack: insert G hypotheses immediately before ONE target.

    This is the attack an adversary actually mounts against its own episode, and it is NOT what a
    front-prefix insertion measures.  Inserting zero-evidence hypotheses immediately before index p
    leaves every earlier hypothesis, and therefore the running rejection count R_p, exactly as it
    was -- they cannot fire.  The target simply moves from step p+1 to step p+1+G and faces
    level A*gamma_{p+1+G}*(R_p+1).  So it fires iff

        Ev[p] >= 1 / (A * gamma_{p+1+G} * (R_p + 1)),

    and the minimal suppressing G is (last step at which that holds) - p, in closed form.  A
    front-prefix insertion instead moves EVERY hypothesis, which can kill the earlier detections
    that raised R in the first place -- a channel unavailable to an attacker inserting only ahead of
    its own episode.  Reporting the prefix number as a per-target cost overstates the attack, which
    is exactly what an earlier version of this stage did.
    """
    # ANALYTIC, so nothing is truncated.  gamma_t = t^-1.6 / zeta(1.6), so the target clears at
    # step t iff  A * t^-1.6 / zeta * (R+1) * Ev >= 1  iff  t <= (A (R+1) Ev / zeta)^(1/1.6).
    # An earlier version searched a gamma array of length 2T+4 and silently capped G* at 2T+3 --
    # wrong whenever the clearing step exceeds the stream, which the blind audit demonstrated.
    z = float(zeta(1.6, 1))
    out, closed_last = [], []
    for p in targets:
        x = A * (float(R_before[p]) + 1.0) * float(Ev[p]) / z
        last = int(np.floor(x ** (1.0 / 1.6))) if x > 0 else 0
        closed_last.append(last)
        out.append(int(max(0, last - int(p))))               # p is 0-indexed; step p+1 -> +G
    return out, closed_last


def survival_curve(Ev, ismal, CEIL, targets, g_max, kind, ben_pool, rng):
    """Replay e-LOND with G inserted hypotheses at the front, for G = 0..g_max.

    Returns (fired_by_G, n_inserted_firing) where fired_by_G[g] is a boolean array over `targets`
    saying whether that original detection is still rejected when G = g.  Inserting at the front
    shifts EVERY hypothesis by g, so one run answers for all targets at once."""
    T = len(Ev)
    fired_by_G = np.zeros((g_max + 1, len(targets)), bool)
    n_ins_fire = np.zeros(g_max + 1, int)
    # The head is drawn ONCE and used in prefixes.  Re-drawing it at each g would make "insert one
    # more" a fresh experiment rather than an extension, and the curve would wobble for a purely
    # sampling reason -- which is exactly what an earlier version of this file reported as
    # non-monotonicity.
    full_head = (np.zeros(max(g_max, 1)) if kind == "zero"
                 else ben_pool[rng.integers(0, ben_pool.size, max(g_max, 1))])
    for g in range(g_max + 1):
        if g == 0:
            Ev2 = Ev; im2 = ismal
        else:
            head = full_head[:g]
            Ev2 = np.concatenate([head, Ev])
            im2 = np.concatenate([np.zeros(g, bool), ismal])
        ctx = Ctx(Ev2, im2, CEIL, alpha=A, w0=W0)
        g1, _ = make_gamma("poly", T + g)
        fired = np.zeros(T + g, bool)
        run_lond(ctx, g1, fired=fired)
        fired_by_G[g] = fired[g + targets]
        n_ins_fire[g] = int(fired[:g].sum())
    return fired_by_G, n_ins_fire


def main():
    t0 = time.time()
    Path("out").mkdir(exist_ok=True)
    X, y, ts, src, dst = hs.load()
    N = len(y)
    rows, notes = [], []

    for pos in POS:
        i1, i2, i3 = hs.split_indices(N, pos)
        y_te = y[i2:i3]; ts_w = ts[i2:i3]; src_w = src[i2:i3]; dst_w = dst[i2:i3]
        score = hs.fit_detector(X, y, i1, seed=SEED, kind="hgb", verbose=False)
        s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
        e_te, cal, NC, CEIL = hs.evalues(s_cal, y[i1:i2], s_te, k=K)

        for order in ORDERS:
            ep = hs.build_episodes(e_te, y_te, ts_w, src_w, dst_w, BUCKET, "src-dst", order=order)
            T = ep["T"]; Ev = ep["Ev"]; ismal = ep["ismal"]; nsz = ep["nsz"]
            w_cold, w_closed = cold_start(CEIL, T)
            ctx0 = Ctx(Ev, ismal, CEIL, alpha=A, w0=W0)
            g1, _ = make_gamma("poly", T)
            fired0 = np.zeros(T, bool)
            run_lond(ctx0, g1, fired=fired0)
            targets = np.flatnonzero(fired0 & ismal)       # the true detections to suppress
            R_before = np.concatenate([[0], np.cumsum(fired0)[:-1]]).astype(int)
            print(f"\n  pos={pos} {order:<11} T={T:,}  w_cold={w_cold}  "
                  f"true detections {targets.size}"
                  f"{' (nothing to attack)' if targets.size == 0 else ''}  [{time.time()-t0:.0f}s]")
            if targets.size == 0:
                rows.append(dict(pos=pos, order=order, T=int(T), cold_start_steps=w_cold,
                                 n_targets=0, note="controller detects nothing here; "
                                                   "no target to suppress"))
                continue
            # scan far enough that the LAST detection is pushed well past the feasible prefix
            g_max = int(G_HEADROOM * w_cold) + int(targets.max())
            g_max = min(g_max, 4000)
            ben_pool = Ev[~ismal]
            # the TARGETED cost, in closed form, verified against a replay below
            gt, gt_last = targeted_gstar(Ev, ismal, CEIL, targets, R_before)
            # Where does the target sit, and what does getting ahead of it cost?  Both orders emit
            # by bucket first, so an attacker can only precede a target by occupying an EARLIER
            # bucket or by beating it inside its own.  Measure which is available.
            bk = ep["bucket_g"][ep["order"]]
            gsrc = np.zeros(T, np.int64); gsrc[ep["gid"]] = src_w
            gdst = np.zeros(T, np.int64); gdst[ep["gid"]] = dst_w
            # the hash must be the one that BUILT this order, or the fractions are meaningless
            hseed = 0 if order == "keyhash" else (hs.KEYED_SEED if order == "keyed" else 0)
            h63 = (hs.key_hash(gsrc, gdst, ep["bucket_g"], seed=hseed)
                   & np.uint64((1 << 63) - 1)).astype(float)[ep["order"]]
            tb = bk[targets]
            n_before_bucket = [int((bk < b).sum()) for b in tb]
            in_bucket = [int((bk == b).sum()) for b in tb]
            rank_in_bucket = [int(((bk == b) & (np.arange(T) < int(t))).sum())
                              for b, t in zip(tb, targets)]
            # THE RIGHT EVENT.  The targeted attack needs its insertions to land between the LAST
            # REJECTION before the target and the target itself -- land them earlier and they shift
            # that rejection too, which changes R and turns this into the prefix attack.  So the
            # qualifying hash interval is (h_lastrej, h_target), not the whole space below the
            # target.  Pricing the wider event understates the search by orders of magnitude, which
            # is what an earlier version did.
            rej_idx = np.flatnonzero(fired0)
            frac_below, frac_gap = [], []
            for t in targets:
                frac_below.append(float(h63[t] / float(1 << 63)))
                prev = rej_idx[rej_idx < t]
                lo = float(h63[prev[-1]]) if prev.size else 0.0
                frac_gap.append(max(0.0, float(h63[t]) - lo) / float(1 << 63))
            rec = dict(pos=pos, order=order, T=int(T), NC=int(NC), CEIL=float(CEIL),
                       cold_start_steps=w_cold,
                       cold_start_matches_closed_form=bool(w_cold == w_closed),
                       n_targets=int(targets.size), g_max=int(g_max),
                       target_positions=[int(x) + 1 for x in targets],
                       target_group_sizes=[int(nsz[x]) for x in targets],
                       median_target_group_size=int(np.median(nsz[targets])),
                       target_evidence=[float(Ev[x]) for x in targets],
                       target_R_before=[int(R_before[x]) for x in targets],
                       # TARGETED attack: insert only ahead of this one episode.  This is the
                       # per-episode cost; the prefix numbers below are a DIFFERENT attack.
                       targeted_gstar=gt,
                       targeted_gstar_median=float(np.median(gt)) if gt else None,
                       targeted_gstar_min=int(min(gt)) if gt else None,
                       targeted_gstar_max=int(max(gt)) if gt else None,
                       # the last step at which THIS episode's own evidence clears at R=0.  w_cold
                       # is the same quantity for an episode carrying the full ceiling, so it is an
                       # upper bound; a sub-ceiling episode falls out of the window sooner, and that
                       # is why G* can be smaller than the naive w_cold - position + 1.
                       target_last_clearing_step=[
                           int(np.searchsorted(-(A * g1[1:T + 1] * float(Ev[x])), -1.0,
                                               side="right"))
                           for x in targets],
                       margin_at_0=float((NC + 1) * W0 / T - 1.0),
                       margin_at_gmax=float((NC + 1) * W0 / (T + g_max) - 1.0),
                       # the access question: can the attacker simply use an earlier bucket?
                       n_episodes_in_earlier_buckets=n_before_bucket,
                       n_episodes_in_target_bucket=in_bucket,
                       target_rank_within_bucket=rank_in_bucket,
                       all_targets_in_first_bucket=bool(all(x == 0 for x in n_before_bucket)),
                       hash_fraction_below_target=frac_below,
                       hash_fraction_in_targeted_gap=frac_gap)
            # VERIFY the closed form by replaying the targeted insertion on a sample of targets
            ver_bad, ver_n = 0, 0
            for jj in list(range(min(40, targets.size))):
                pp = int(targets[jj]); G = int(gt[jj])
                for Gtest, want_fire in ((max(G - 1, 0), G > 0), (G, False)):
                    ins = np.zeros(Gtest)
                    Ev2 = np.concatenate([Ev[:pp], ins, Ev[pp:]])
                    im2 = np.concatenate([ismal[:pp], np.zeros(Gtest, bool), ismal[pp:]])
                    f2 = np.zeros(len(Ev2), bool)
                    run_lond(Ctx(Ev2, im2, CEIL, alpha=A, w0=W0),
                             make_gamma("poly", len(Ev2))[0], fired=f2)
                    ver_n += 1
                    if bool(f2[pp + Gtest]) != bool(want_fire):
                        ver_bad += 1
            rec["targeted_closed_form_replay_checks"] = int(ver_n)
            rec["targeted_closed_form_replay_failures"] = int(ver_bad)
            print(f"    targeted (insert only ahead of the target): G* median "
                  f"{rec['targeted_gstar_median']} [{rec['targeted_gstar_min']}, "
                  f"{rec['targeted_gstar_max']}]  closed form verified by replay "
                  f"{ver_n - ver_bad}/{ver_n}")

            for kind in KINDS:
                rng = np.random.default_rng(20260902 + int(pos * 100) + ORDERS.index(order))
                fb, ins_fire = survival_curve(Ev, ismal, CEIL, targets, g_max, kind, ben_pool, rng)
                gstar, glast, never = [], [], 0
                for j in range(targets.size):
                    col = fb[:, j]
                    off = np.flatnonzero(~col)
                    gstar.append(int(off[0]) if off.size else None)
                    on = np.flatnonzero(col)
                    glast.append(int(on[-1]) if on.size else None)
                    if not off.size:
                        never += 1
                # non-monotone iff a target fires again after it first stopped
                nonmono = int(sum(1 for a, b in zip(gstar, glast)
                                  if a is not None and b is not None and b > a))
                gs = [x for x in gstar if x is not None]
                rec[kind] = dict(
                    # aligned with `target_positions`, so the mechanism can be checked per target
                    # rather than by pairing two independently sorted lists
                    gstar_by_target=[None if x is None else int(x) for x in gstar],
                    attack="prefix: insert ahead of EVERY hypothesis (silences the window); "
                           "these are NOT per-episode costs -- see targeted_gstar for those",
                    n_suppressible=len(gs), n_never_suppressed=never,
                    gstar_median=(float(np.median(gs)) if gs else None),
                    gstar_min=(int(min(gs)) if gs else None),
                    gstar_max=(int(max(gs)) if gs else None),
                    gstar_sorted=sorted(gs),
                    n_nonmonotone=nonmono,
                    glast_max=(max([x for x in glast if x is not None], default=None)),
                    n_inserted_that_fire_at_gmax=int(ins_fire[g_max]),
                    inserted_ever_fire=bool(ins_fire.max() > 0),
                    # every detection gone at once: the attacker silences the window outright
                    g_all_suppressed=(int(np.flatnonzero(~fb.any(axis=1))[0])
                                      if (~fb.any(axis=1)).any() else None))
                # the KEY-HASH order's price: an offline search, sized per target
                if order == "keyhash":
                    # PUBLIC seed only.  Under "keyed" the adversary cannot rank keys offline at
                    # all, so no trial count is defined -- emitting one there (as an earlier version
                    # did, and with the WRONG seed) would contradict the very point of that arm.
                    # Two events are priced because they are different attacks:
                    #   prefix   : land anywhere below the target      -> fraction h/2^63
                    #   targeted : land inside the last-rejection gap  -> fraction gap/2^63
                    tp = [g / f for g, f in zip(gt, frac_gap) if f > 0]
                    pf = [g / f for g, f in zip(gstar, frac_below)
                          if g is not None and f > 0]
                    rec[kind]["key_trials_prefix_median"] = (float(np.median(pf)) if pf else None)
                    rec[kind]["key_trials_targeted_median"] = (float(np.median(tp)) if tp else None)
                    rec[kind]["key_trials_targeted_max"] = (float(max(tp)) if tp else None)
                    rec[kind]["n_targets_with_zero_gap"] = int(sum(1 for f in frac_gap if f <= 0))
                else:
                    rec[kind]["key_trials_note"] = (
                        "first-flow needs no search (send earlier in the bucket); keyed cannot be "
                        "ranked offline at all, so no trial count is defined")
                print(f"    {kind:<7} suppressible {len(gs)}/{targets.size}  "
                      f"G* median {rec[kind]['gstar_median']} "
                      f"[{rec[kind]['gstar_min']}, {rec[kind]['gstar_max']}]  "
                      f"all-silent at G={rec[kind]['g_all_suppressed']}  "
                      f"inserted-that-fire {rec[kind]['n_inserted_that_fire_at_gmax']}  "
                      f"non-monotone {nonmono}")
            rows.append(rec)

    # =====================================================================================
    # The GROUP-CALIBRATED MAX pipeline -- the construction non-claim 21 is actually about.
    # Padding provably cannot suppress it (appending cannot lower a maximum, t57 verifies
    # 110/110 ... 152/152 still firing after pads).  Insertion does not append anything, so the
    # append-invariance buys nothing; this is where that has to be shown rather than argued.
    # =====================================================================================
    T57 = lift_t57(["group_by_key", "group_fires"])
    grp_rows = []
    for pos in POS:
        i1, i2, i3 = hs.split_indices(N, pos)
        score = hs.fit_detector(X, y, i1, seed=SEED, kind="hgb", verbose=False)
        s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
        gcal = T57.group_by_key(src[i1:i2], dst[i1:i2], ts[i1:i2], y[i1:i2], s_cal, BUCKET)
        gte = T57.group_by_key(src[i2:i3], dst[i2:i3], ts[i2:i3], y[i2:i3], s_te, BUCKET)
        keep = ~gcal["ismal"]                       # benign calibration GROUPS
        cal = np.sort(gcal["max"][keep]); NCg = int(cal.size)
        CEILg = (NCg + 1.0) / K
        stat = gte["max"]
        fires = T57.group_fires(cal, stat)
        Ev_g = np.where(fires, CEILg, 0.0)
        order = np.lexsort((gte["first_pos"], gte["first_ts"]))
        Ev = Ev_g[order]; ismal = gte["ismal"][order]
        G = int(gte["G"])
        ctx = Ctx(Ev, ismal, CEILg, alpha=A, w0=W0)
        g1, _ = make_gamma("poly", G)
        f0 = np.zeros(G, bool)
        run_lond(ctx, g1, fired=f0)
        tg = np.flatnonzero(f0 & ismal)
        R_before = np.concatenate([[0], np.cumsum(f0)[:-1]]).astype(int)
        w_cold, _ = cold_start(CEILg, G)
        rr = dict(pos=pos, pipeline="group-max", G=int(G), NC_groups=NCg, CEIL=float(CEILg),
                  cold_start_steps=w_cold, n_firing_groups=int(fires.sum()),
                  n_targets=int(tg.size),
                  target_positions=[int(x) + 1 for x in tg])
        if tg.size:
            gt, _gtl = targeted_gstar(Ev, ismal, CEILg, tg, R_before)
            rr.update(targeted_gstar=gt, targeted_gstar_median=float(np.median(gt)),
                      targeted_gstar_min=int(min(gt)), targeted_gstar_max=int(max(gt)),
                      # prefix attack: push the earliest target out and nothing bootstraps
                      prefix_g_all=int(w_cold - min(int(x) + 1 for x in tg) + 1))
            print(f"  group-MAX pos={pos}: G={G:,} groups, {int(fires.sum())} firing, "
                  f"{tg.size} true detections, w_cold={w_cold}; targeted G* median "
                  f"{rr['targeted_gstar_median']}, prefix bound {rr['prefix_g_all']}")
        else:
            rr["note"] = "group-MAX controller detects nothing here"
            print(f"  group-MAX pos={pos}: G={G:,} groups, {int(fires.sum())} firing, "
                  f"0 true detections (nothing to attack)")
        grp_rows.append(rr)

    # --- the comparison that decides whether this lever matters -----------------------------
    try:
        t28 = json.load(open("out/t28b_reallevel.json"))["table1_by_order"]
    except Exception:
        t28 = None
    cmp_rows = []
    for r in rows:
        if not r.get("n_targets"):
            continue
        pad = pad_total = None
        if t28:
            cell = t28[r["order"]][f"{r['pos']}_0"]
            pad = cell["med_pad_real"]
            # to silence the WHOLE window by padding, every detected episode must be padded
            # separately, so the comparable total is the SUM of the individual costs -- not the
            # median.  Insertion silences all of them at once, which is the asymmetry that matters.
            # UPPER bound: padding every detection separately.  It is not the joint cost --
            # suppressing an early rejection lowers R and can make later ones vanish or cost less,
            # so the true joint cost is somewhere between the cheapest single pad and this sum.
            pad_total = int(sum(cell["pads_real"])) if cell.get("pads_real") else None
            pad_min = int(min(cell["pads_real"])) if cell.get("pads_real") else None
            pr = sorted(cell.get("pads_real") or [], reverse=True)
            tail_share = (float(sum(pr[:10]) / sum(pr)) if pr and sum(pr) else None)
        g_all = r["zero"]["g_all_suppressed"]
        g_tgt = r["targeted_gstar_median"]
        # An inserted hypothesis costs at least ONE flow, but a group a defender would actually
        # form may need more; the comparison is therefore reported at several flows-per-group
        # rather than asserted at the floor.  f=1 is a lower bound, not a measurement.
        fpg = {}
        for f_ in (1, 2, int(r["median_target_group_size"])):
            fpg[str(f_)] = dict(
                targeted_flows=(g_tgt * f_ if g_tgt is not None else None),
                window_flows=(g_all * f_ if g_all is not None else None),
                cheaper_per_episode=(bool(g_tgt is not None and pad is not None
                                          and g_tgt * f_ < pad)),
                cheaper_per_window=(bool(g_all is not None and pad_total is not None
                                         and g_all * f_ < pad_total)))
        cmp_rows.append(dict(pos=r["pos"], order=r["order"], n_targets=r["n_targets"],
                             median_targeted_gstar=g_tgt,
                             prefix_gstar_median=r["zero"]["gstar_median"],
                             median_pad_flows=pad,
                             g_all_suppressed=g_all,
                             total_pad_flows_to_silence_window_UPPER=pad_total,
                             cheapest_single_pad_LOWER=pad_min,
                             pad_sum_top10_share=tail_share,
                             by_flows_per_group=fpg,
                             cheaper_per_episode_at_1_flow_per_group=fpg["1"]["cheaper_per_episode"],
                             cheaper_per_window_at_1_flow_per_group=fpg["1"]["cheaper_per_window"],
                             cheaper_per_window_at_2_flows_per_group=fpg["2"]["cheaper_per_window"],
                             window_silencing_ratio_UPPER=(
                                 float(pad_total / g_all) if (pad_total and g_all) else None)))
    n_cheaper = sum(1 for c in cmp_rows if c["cheaper_per_episode_at_1_flow_per_group"])
    n_cheaper_win = sum(1 for c in cmp_rows if c["cheaper_per_window_at_1_flow_per_group"])
    summary = dict(
        n_rows=len(rows),
        n_rows_with_targets=sum(1 for r in rows if r.get("n_targets")),
        n_rows_no_target=sum(1 for r in rows if not r.get("n_targets")),
        all_targets_suppressible=all(r[k]["n_never_suppressed"] == 0
                                     for r in rows if r.get("n_targets") for k in KINDS),
        any_nonmonotone=any(r[k]["n_nonmonotone"] > 0
                            for r in rows if r.get("n_targets") for k in KINDS),
        inserted_ever_fire_zero=any(r["zero"]["inserted_ever_fire"]
                                    for r in rows if r.get("n_targets")),
        inserted_ever_fire_benign=any(r["benign"]["inserted_ever_fire"]
                                      for r in rows if r.get("n_targets")),
        group_max_targets=sum(r["n_targets"] for r in grp_rows),
        group_max_all_suppressible=all(all(g < r["G"] for g in r.get("targeted_gstar", []))
                                       for r in grp_rows),
        comparison=cmp_rows, n_cells_positional_cheaper=n_cheaper,
        n_cells_positional_cheaper_per_window=n_cheaper_win,
        n_cells_cheaper_per_window_at_2_flows=sum(
            1 for c in cmp_rows if c["cheaper_per_window_at_2_flows_per_group"]),
        max_window_silencing_ratio_UPPER=max(
            (c["window_silencing_ratio_UPPER"] for c in cmp_rows
             if c["window_silencing_ratio_UPPER"] is not None), default=None),
        median_window_silencing_ratio_UPPER=float(np.median(
            [c["window_silencing_ratio_UPPER"] for c in cmp_rows
             if c["window_silencing_ratio_UPPER"] is not None])),
        max_pad_sum_top10_share=max((c["pad_sum_top10_share"] for c in cmp_rows
                                     if c["pad_sum_top10_share"] is not None), default=None),
        n_cells_compared=sum(1 for c in cmp_rows if c["median_pad_flows"] is not None))
    out = dict(
        config=dict(POS=POS, SEED=SEED, ORDERS=ORDERS, KINDS=KINDS, k=K, alpha=A, w0=W0,
                    bucket_s=BUCKET, g_step=G_STEP, g_headroom=G_HEADROOM,
                    attack=("insert G hypotheses AHEAD of the target by sending traffic in an "
                            "earlier bucket; nothing is appended to the target, so thm:padding "
                            "and the max statistic's append-invariance are both irrelevant"),
                    cost_unit="inserted hypotheses; >= 1 flow each, so a LOWER bound in flows"),
        rows=rows, group_max_rows=grp_rows, summary=summary)
    json.dump(out, open("out/t60_positional.json", "w"), indent=1, allow_nan=False)
    print(f"\n  every true detection is suppressible by insertion alone: "
          f"{summary['all_targets_suppressible']}")
    print(f"  per EPISODE, insertion is cheaper than padding at "
          f"{n_cheaper}/{summary['n_cells_compared']} cells")
    print(f"  per WINDOW (silence everything), insertion is cheaper at "
          f"{n_cheaper_win}/{summary['n_cells_compared']} cells at 1 flow per inserted group, "
          f"{summary['n_cells_cheaper_per_window_at_2_flows']}/{summary['n_cells_compared']} at 2; "
          f"ratio median {summary['median_window_silencing_ratio_UPPER']:.0f}x, max "
          f"{summary['max_window_silencing_ratio_UPPER']:.0f}x (UPPER bounds; the padding total is "
          f"a sum of independent costs, and its top 10 entries carry up to "
          f"{100*summary['max_pad_sum_top10_share']:.1f}% of it)")
    for c in cmp_rows:
        print(f"    pos={c['pos']} {c['order']:<11} targeted G* {c['median_targeted_gstar']:>7.0f} "
              f"vs padding {c['median_pad_flows']:>8} flows  |  window: insert "
              f"{c['g_all_suppressed']:>4} vs pad {c['total_pad_flows_to_silence_window_UPPER']:>11,}"
              f"{'   <-- insertion cheaper' if c['cheaper_per_window_at_1_flow_per_group'] else ''}")
    print(f"  [{time.time()-t0:.0f}s]  wrote out/t60_positional.json")
    return out


if __name__ == "__main__":
    main()
