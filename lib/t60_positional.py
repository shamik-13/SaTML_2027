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

    g1, _ = make_gamma("poly", T)
    lvl = A * g1[1:T + 1] * (R + 1.0)
    with np.errstate(divide="ignore"):
        ok = np.flatnonzero(np.where(lvl > 0, CEIL >= 1.0 / np.maximum(lvl, 1e-300), False))
    w = int(ok[-1] + 1) if ok.size else 0
    x = A * CEIL * (R + 1.0) / float(zeta(1.6, 1))
    return w, (int(np.floor(x ** (1.0 / 1.6))) if x > 0 else 0)


def lift_t57(names):

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

    z = float(zeta(1.6, 1))
    out, closed_last = [], []
    for p in targets:
        x = A * (float(R_before[p]) + 1.0) * float(Ev[p]) / z
        last = int(np.floor(x ** (1.0 / 1.6))) if x > 0 else 0
        closed_last.append(last)
        out.append(int(max(0, last - int(p))))               # p is 0-indexed; step p+1 -> +G
    return out, closed_last


def survival_curve(Ev, ismal, CEIL, targets, g_max, kind, ben_pool, rng):

    T = len(Ev)
    fired_by_G = np.zeros((g_max + 1, len(targets)), bool)
    n_ins_fire = np.zeros(g_max + 1, int)

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

            gt, gt_last = targeted_gstar(Ev, ismal, CEIL, targets, R_before)

            bk = ep["bucket_g"][ep["order"]]
            gsrc = np.zeros(T, np.int64); gsrc[ep["gid"]] = src_w
            gdst = np.zeros(T, np.int64); gdst[ep["gid"]] = dst_w
            hseed = 0 if order == "keyhash" else (hs.KEYED_SEED if order == "keyed" else 0)
            h63 = (hs.key_hash(gsrc, gdst, ep["bucket_g"], seed=hseed)
                   & np.uint64((1 << 63) - 1)).astype(float)[ep["order"]]
            tb = bk[targets]
            n_before_bucket = [int((bk < b).sum()) for b in tb]
            in_bucket = [int((bk == b).sum()) for b in tb]
            rank_in_bucket = [int(((bk == b) & (np.arange(T) < int(t))).sum())
                              for b, t in zip(tb, targets)]

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

                       targeted_gstar=gt,
                       targeted_gstar_median=float(np.median(gt)) if gt else None,
                       targeted_gstar_min=int(min(gt)) if gt else None,
                       targeted_gstar_max=int(max(gt)) if gt else None,

                       target_last_clearing_step=[
                           int(np.searchsorted(-(A * g1[1:T + 1] * float(Ev[x])), -1.0,
                                               side="right"))
                           for x in targets],
                       margin_at_0=float((NC + 1) * W0 / T - 1.0),
                       margin_at_gmax=float((NC + 1) * W0 / (T + g_max) - 1.0),

                       n_episodes_in_earlier_buckets=n_before_bucket,
                       n_episodes_in_target_bucket=in_bucket,
                       target_rank_within_bucket=rank_in_bucket,
                       all_targets_in_first_bucket=bool(all(x == 0 for x in n_before_bucket)),
                       hash_fraction_below_target=frac_below,
                       hash_fraction_in_targeted_gap=frac_gap)
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

                nonmono = int(sum(1 for a, b in zip(gstar, glast)
                                  if a is not None and b is not None and b > a))
                gs = [x for x in gstar if x is not None]
                rec[kind] = dict(

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

                    g_all_suppressed=(int(np.flatnonzero(~fb.any(axis=1))[0])
                                      if (~fb.any(axis=1)).any() else None))

                if order == "keyhash":

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

            pad_total = int(sum(cell["pads_real"])) if cell.get("pads_real") else None
            pad_min = int(min(cell["pads_real"])) if cell.get("pads_real") else None
            pr = sorted(cell.get("pads_real") or [], reverse=True)
            tail_share = (float(sum(pr[:10]) / sum(pr)) if pr and sum(pr) else None)
        g_all = r["zero"]["g_all_suppressed"]
        g_tgt = r["targeted_gstar_median"]
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
