def main():
    import numpy as np, json, time
    from pathlib import Path
    import h_stream as hs
    from h6_procs import (Ctx, make_gamma, make_deadlines, run_lond, run_online_ebh,
                          online_ebh_kstar,
                          run_donation_elond, run_closed_elond, run_donation_ebh, run_etoad)

    Path("out").mkdir(exist_ok=True)
    t0 = time.time()
    POSITIONS = [0.55, 0.62, 0.70, 0.77, 0.85]
    SEEDS = [0, 1]
    K = 1; A = 0.05; W0 = 0.025; BUCKET = 2 * 3600
    GAMMAS = ["poly", "uniform"]

    ORDERS = ["first-flow", "keyhash"]
    DEADLINES = [("immediate", None), ("bucket", None), ("6h", 6 * 3600),
                 ("24h", 24 * 3600), ("arc", None)]

    X, y, ts, src, dst = hs.load()
    N = len(y)
    out = {"config": dict(
        positions=POSITIONS, seeds=SEEDS, k=K, alpha=A, w0=W0, bucket_s=BUCKET,
        gammas=GAMMAS, deadlines=[d[0] for d in DEADLINES],
        source="Xu, Fischer & Ramdas, UAI 2026, arXiv 2603.24792v3",
        note="classification of the newest strict improvements against thm:family1/family2; "
             "e-TOAD deadline = the SOC alerting-latency budget, bucket = the batched "
             "architecture")}

    rows = []
    for POS in POSITIONS:
        i1, i2, i3 = hs.split_indices(N, POS)
        for SEED in SEEDS:
            score = hs.fit_detector(X, y, i1, seed=SEED, kind="hgb", verbose=False)
            s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
            e_te, cal, NC, CEIL = hs.evalues(s_cal, y[i1:i2], s_te, k=K)
            ts_w = ts[i2:i3]
            for ORD in ORDERS:
                ep = hs.build_episodes(e_te, y[i2:i3], ts_w, src[i2:i3], dst[i2:i3],
                                       BUCKET, "src-dst", order=ORD)
                T = ep["T"]; gid = ep["gid"]; order = ep["order"]
                first_ts = np.full(T, np.iinfo(np.int64).max)
                np.minimum.at(first_ts, gid, ts_w)
                first_ts = first_ts[order]                      # stream order, microseconds
                t_sec = (first_ts - first_ts[0]) / 1e6
                bucket_id = first_ts // (BUCKET * 1_000_000)
                ctx = Ctx(ep["Ev"], ep["ismal"], CEIL, alpha=A, w0=W0)
                npos = int((ep["Ev"] > 0).sum())
                print(f"\n  pos {POS} seed {SEED} order {ORD}: T={T:,}  |C|={NC:,}  CEIL={CEIL:,.0f}  "
                      f"malicious={ep['n_mal']}  nonzero-evidence episodes={npos:,} "
                      f"({100*npos/T:.2f}%)  span={t_sec[-1]/3600:.1f}h")

                for GK in GAMMAS:
                    g1, _ = make_gamma(GK, T)
                    arms = {}

                    m_lond = np.zeros(T, bool)
                    r = run_lond(ctx, g1, fired=m_lond)
                    arms["e-LOND"] = dict(rej=r[0], tp=r[1], silent=r[2], first_silent=r[3])
                    m_ebh = np.zeros(T, bool)
                    ks, mv = online_ebh_kstar(ctx.Ev, g1, ctx.A, T)
                    m_ebh[:] = np.isfinite(mv) & (mv <= int(ks[T]))

                    dg = {}
                    r = run_donation_elond(ctx, g1, diag=dg)
                    arms["donation e-LOND"] = dict(rej=r[0], tp=r[1], silent=r[2],
                                                   first_silent=r[3], **dg)

                    dg = {}
                    r = run_closed_elond(ctx, g1, diag=dg)
                    arms["closed e-LOND"] = dict(rej=r[0], tp=r[1], silent=r[2],
                                                 first_silent=r[3], **dg)

                    r = run_online_ebh(ctx, g1)
                    arms["online e-BH"] = dict(rej=r[0], tp=r[1], silent=r[2], first_silent=r[3],
                                               kstar_T=r[4], never_rejectable=r[6])

                    for hist in ("snapshot", "union"):
                        dg = {}
                        r = run_donation_ebh(ctx, g1, diag=dg, history=hist)
                        arms[f"donation e-BH ({hist})"] = dict(rej=r[0], tp=r[1], silent=None,
                                                               first_silent=None, **dg)

                    for dname, horizon in DEADLINES:
                        if dname == "immediate":
                            dl = make_deadlines("immediate", T)
                        elif dname == "arc":
                            dl = make_deadlines("arc", T)
                        elif dname == "bucket":
                            dl = make_deadlines("bucket", T, bucket=bucket_id)
                        else:
                            dl = make_deadlines("time", T, ts=t_sec, horizon_s=horizon)
                        wait = np.where(np.isfinite(dl), dl, T) - np.arange(1, T + 1)
                        dg = {}
                        m_td = np.zeros(T, bool)
                        r = run_etoad(ctx, g1, dl, fired=m_td, diag=dg)
                        # the paper's claim is that the two limiting deadlines reproduce the two
                        # baselines EXACTLY, so compare masks, not counts
                        if dname == "immediate":
                            eq = bool(np.array_equal(m_td, m_lond))
                        elif dname == "arc":
                            eq = bool(np.array_equal(m_td, m_ebh))
                        else:
                            eq = None
                        arms[f"e-TOAD({dname})"] = dict(
                            rej=r[0], tp=r[1], silent=r[2], first_silent=r[3],
                            mask_equals_baseline=eq,
                            median_hypotheses_waited=float(np.median(wait)),
                            max_hypotheses_waited=int(wait.max()), **dg)

                    need_elond = K * T / A - 1.0
                    need_don = K * T / (A / (1.0 - A)) - 1.0
                    n_flow = int(i3 - i2)

                    exact_silence = {"e-LOND", "donation e-LOND", "closed e-LOND"} | {
                        f"e-TOAD({d[0]})" for d in DEADLINES}
                    base_fs = arms["e-LOND"]["first_silent"]
                    base_fs = T if base_fs is None else base_fs
                    gained = {}
                    for nm, a in arms.items():
                        meth = ("exact" if nm in exact_silence
                                else None if a["silent"] is None else "necessary-only")
                        fsa = a["first_silent"]
                        if fsa is None and a["silent"] is None:
                            gained[nm] = dict(first_silent_shift=None, first_silent_censored=None,
                                              silent_fraction=None, silence_method=meth,
                                              extra_true_detections=int(a["tp"] - arms["e-LOND"]["tp"]))
                            continue

                        cens = fsa is None
                        fsa = T if cens else fsa
                        gained[nm] = dict(first_silent_shift=int(fsa - base_fs),
                                          first_silent_censored=bool(cens),
                                          silent_fraction=float((a["silent"] or 0) / T),
                                          silence_method=meth,
                                          extra_true_detections=int(a["tp"] - arms["e-LOND"]["tp"]))
                    cls = dict(

                        required_C_elond=need_elond,
                        required_C_donation_elond=need_don,
                        donation_relaxation=need_don / need_elond,
                        C_available=int(NC),
                        required_over_available_elond=need_elond / NC,
                        required_over_available_donation=need_don / NC,
                        horizon_uniform_feasible=bool(need_elond <= NC),
                        T_flows=n_flow,
                        required_C_elond_flowgrain=K * n_flow / A - 1.0,
                        required_over_available_flowgrain=(K * n_flow / A - 1.0) / NC,
                        realised_coldstart_boost=arms["donation e-LOND"]["max_boost_coldstart"],
                        realised_boost_any_R=arms["donation e-LOND"]["max_boost"],
                        boost_ceiling=arms["donation e-LOND"]["boost_ceiling"],
                        realised_max_wealth=arms["donation e-LOND"]["max_wealth"],
                        wealth_budget=1.0,
                        wealth_used_fraction=arms["donation e-LOND"]["max_wealth"],
                        closed_level_over_zero_bound=arms["closed e-LOND"]["worst_lvl_over_zero_bound"],
                        zero_evidence_fraction=arms["closed e-LOND"]["n_zero_evidence"] / T,
                        ebh_silent_necessary_only=arms["online e-BH"]["silent"],
                        ebh_silent_exact=arms["e-TOAD(arc)"]["silent"],
                        donation_ebh_snapshot=arms["donation e-BH (snapshot)"]["tp"],
                        donation_ebh_union=arms["donation e-BH (union)"]["tp"],
                        donation_ebh_sets_nested=arms["donation e-BH (snapshot)"]["sets_are_nested"],
                        gained=gained)

                    rows.append(dict(pos=POS, seed=SEED, order=ORD, gamma=GK, T=int(T), nCal=int(NC),
                                     CEIL=float(CEIL), n_mal=int(ep["n_mal"]),
                                     n_positive_evidence=npos, span_h=float(t_sec[-1] / 3600),
                                     arms=arms, classification=cls))

                    print(f"    gamma={GK}")
                    print(f"      {'arm':<26} {'rej':>5} {'true':>5} {'silent':>9} {'1st silent':>11}")
                    for nm, a in arms.items():
                        fs = a["first_silent"]; sl = a["silent"]
                        print(f"      {nm:<26} {a['rej']:>5} {a['tp']:>5} "
                              f"{('n/a' if sl is None else f'{sl:,}'):>9} "
                              f"{('-' if fs is None else f'{fs:,}'):>11}")
                    print(f"      donation boost at cold start {cls['realised_coldstart_boost']:.6f} "
                          f"(ceiling {cls['boost_ceiling']:.6f}); wealth "
                          f"{cls['realised_max_wealth']:.2e} of a budget of 1")
                    print(f"      closed e-LOND level / zero-evidence bound = "
                          f"{cls['closed_level_over_zero_bound']:.6f}  "
                          f"(zero-evidence episodes {100*cls['zero_evidence_fraction']:.2f}%)")
                    print(f"      required |C| at this granularity: e-LOND {need_elond:,.0f}, "
                          f"donation e-LOND {need_don:,.0f} ({cls['donation_relaxation']:.4f}x); "
                          f"available {NC:,} -> horizon-uniform feasible: "
                          f"{cls['horizon_uniform_feasible']}")
                    print(f"      same requirement at FLOW granularity (T={n_flow:,}): "
                          f"{cls['required_C_elond_flowgrain']:,.0f} -> "
                          f"{cls['required_over_available_flowgrain']:.1f}x what is available")
                    print(f"      first silence moves by: donation "
                          f"{gained['donation e-LOND']['first_silent_shift']:+,}, closed "
                          f"{gained['closed e-LOND']['first_silent_shift']:+,}, e-TOAD(bucket) "
                          f"{gained['e-TOAD(bucket)']['first_silent_shift']:+,} of {T:,} steps")
                    print(f"      extra true detections: donation "
                          f"{gained['donation e-LOND']['extra_true_detections']:+d}, closed "
                          f"{gained['closed e-LOND']['extra_true_detections']:+d}, e-TOAD(bucket) "
                          f"{gained['e-TOAD(bucket)']['extra_true_detections']:+d}, arc "
                          f"{gained['e-TOAD(arc)']['extra_true_detections']:+d}, donation e-BH "
                          f"{gained['donation e-BH (snapshot)']['extra_true_detections']:+d} "
                          f"(snapshot) / "
                          f"{gained['donation e-BH (union)']['extra_true_detections']:+d} (union)")
                    print(f"      online e-BH silence: {cls['ebh_silent_necessary_only']:,} by the "
                          f"necessary condition, {cls['ebh_silent_exact']:,} exact")

    out["rows"] = rows
    ff = lambda r: r["order"] == "first-flow"
    ca = lambda r: r["order"] == "keyhash"

    def col(f, where=lambda r: True):
        return [f(r) for r in rows if ff(r) and where(r)]

    def anyr(f):
        return any(f(r) for r in rows if ff(r))

    def allr(f):
        return all(f(r) for r in rows if ff(r))

    def _converts(pred):
        """(pos, seed) cells at which deferral to bucket close buys a true detection."""
        return sorted({(r["pos"], r["seed"]) for r in rows
                       if pred(r) and r["gamma"] == "poly"
                       and r["arms"]["e-TOAD(bucket)"]["tp"] > r["arms"]["e-LOND"]["tp"]})

    poly = lambda r: r["gamma"] == "poly"
    summary = dict(
        n_rows=len(rows),
        n_rows_first_flow=sum(1 for r in rows if ff(r)),
        orders=list(ORDERS),
        max_coldstart_boost=max(col(lambda r: r["classification"]["realised_coldstart_boost"])),
        boost_ceiling=1.0 / (1.0 - A),
        max_wealth_used=max(col(lambda r: r["classification"]["realised_max_wealth"])),
        # "attained", not "tight": the bound is an upper bound that happens to be met here
        closed_bound_attained_everywhere=all(
            abs(r["classification"]["closed_level_over_zero_bound"] - 1.0) < 1e-9
            or r["classification"]["closed_level_over_zero_bound"] == 0.0
            for r in rows if ff(r)),
        max_closed_bound_ratio=max(
            col(lambda r: r["classification"]["closed_level_over_zero_bound"])),
        donation_elond_ever_beats_elond=anyr(
            lambda r: r["arms"]["donation e-LOND"]["tp"] > r["arms"]["e-LOND"]["tp"]),
        closed_elond_ever_beats_elond=anyr(
            lambda r: r["arms"]["closed e-LOND"]["tp"] > r["arms"]["e-LOND"]["tp"]),
        donation_ebh_ever_beats_ebh=anyr(
            lambda r: r["arms"]["donation e-BH (snapshot)"]["tp"]
            > r["arms"]["online e-BH"]["tp"]),
        donation_ebh_readings_ever_differ=anyr(
            lambda r: not r["arms"]["donation e-BH (snapshot)"]["sets_are_nested"]),
        etoad_immediate_equals_elond=allr(
            lambda r: r["arms"]["e-TOAD(immediate)"]["mask_equals_baseline"]),
        etoad_arc_equals_online_ebh=allr(
            lambda r: r["arms"]["e-TOAD(arc)"]["mask_equals_baseline"]),
        max_ebh_silence_understated=max(
            (r["classification"]["ebh_silent_exact"] or 0)
            - (r["classification"]["ebh_silent_necessary_only"] or 0)
            for r in rows if ff(r)),
        max_positive_evidence_fraction=max(
            col(lambda r: r["n_positive_evidence"] / r["T"])),
        min_required_over_available_flowgrain=min(
            col(lambda r: r["classification"]["required_over_available_flowgrain"])),
        max_first_silent_shift_donation=max(
            col(lambda r: r["classification"]["gained"]["donation e-LOND"]["first_silent_shift"])),
        max_first_silent_shift_closed=max(
            col(lambda r: r["classification"]["gained"]["closed e-LOND"]["first_silent_shift"])),
        max_extra_detections_donation=max(
            col(lambda r: r["classification"]["gained"]["donation e-LOND"]["extra_true_detections"])),
        max_extra_detections_closed=max(
            col(lambda r: r["classification"]["gained"]["closed e-LOND"]["extra_true_detections"])),
        max_extra_detections_arc=max(
            col(lambda r: r["classification"]["gained"]["e-TOAD(arc)"]["extra_true_detections"])),
        max_extra_detections_bucket=max(
            col(lambda r: r["classification"]["gained"]["e-TOAD(bucket)"]["extra_true_detections"])),
        deferral_converts_cells_first_flow=[list(c) for c in _converts(ff)],
        deferral_converts_cells_canonical=[list(c) for c in _converts(ca)],
        deferral_converts_windows_first_flow=sorted({c[0] for c in _converts(ff)}),
        deferral_converts_windows_canonical=sorted({c[0] for c in _converts(ca)}),
        n_deferral_converting_cells_first_flow=len(_converts(ff)),
        n_deferral_converting_cells_canonical=len(_converts(ca)),
        n_cells_per_order=sum(1 for r in rows if ff(r) and r["gamma"] == "poly"),
        elond_tp_canonical={f"{r['pos']}/{r['seed']}": r["arms"]["e-LOND"]["tp"]
                            for r in rows if ca(r) and r["gamma"] == "poly"},
        etoad_bucket_tp_canonical={f"{r['pos']}/{r['seed']}": r["arms"]["e-TOAD(bucket)"]["tp"]
                                   for r in rows if ca(r) and r["gamma"] == "poly"},
        max_positive_evidence_fraction_canonical=max(
            r["n_positive_evidence"] / r["T"] for r in rows if ca(r)))
    out["summary"] = summary

    print("\n" + "=" * 100)
    print("CLASSIFICATION SUMMARY")
    print("=" * 100)
    print(f"  rows                                         : {summary['n_rows']}")
    print(f"  e-TOAD(immediate) == e-LOND everywhere       : "
          f"{summary['etoad_immediate_equals_elond']}")
    print(f"  e-TOAD(arc) == online e-BH everywhere        : "
          f"{summary['etoad_arc_equals_online_ebh']}")
    print(f"  largest cold-start donation boost            : "
          f"{summary['max_coldstart_boost']:.6f}  (ceiling {summary['boost_ceiling']:.6f})")
    print(f"  largest donated wealth used                  : "
          f"{summary['max_wealth_used']:.3e}  of a budget of 1")
    print(f"  closed e-LOND level / zero-evidence bound    : "
          f"max {summary['max_closed_bound_ratio']:.6f} (bound holds iff <= 1)")
    print(f"  required/available |C| at FLOW granularity   : "
          f"at least {summary['min_required_over_available_flowgrain']:.1f}x")
    print(f"  furthest the improvements move 1st silence   : donation "
          f"{summary['max_first_silent_shift_donation']:+,}, closed "
          f"{summary['max_first_silent_shift_closed']:+,} (NOT a prefix length)")
    print(f"  online e-BH silence understated by up to     : "
          f"{summary['max_ebh_silence_understated']:,} steps "
          f"(necessary-condition vs exact)")
    print(f"  donation e-BH readings ever differ           : "
          f"{summary['donation_ebh_readings_ever_differ']}")
    print(f"  most extra true detections they buy          : donation "
          f"{summary['max_extra_detections_donation']:+d}, closed "
          f"{summary['max_extra_detections_closed']:+d}, e-TOAD(bucket) "
          f"{summary['max_extra_detections_bucket']:+d}, arc "
          f"{summary['max_extra_detections_arc']:+d}")
    print(f"  largest nonzero-evidence fraction of a stream: "
          f"{100*summary['max_positive_evidence_fraction']:.2f}%")

    json.dump(out, open("out/t56_uai26.json", "w"), indent=1, allow_nan=False)
    print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t56_uai26.json")
    return out


if __name__ == "__main__":
    main()
