def main(five=False):
    import numpy as np, json, time, sys
    from pathlib import Path
    import h_stream as hs
    from h6_procs import Ctx, make_gamma, run_lond, run_addis, run_online_ebh

    Path("out").mkdir(exist_ok=True)
    t0 = time.time()
    W0 = 0.025; A = 0.05; K = 1
    FIVE = five
    POS = [0.55, 0.62, 0.70, 0.77, 0.85] if FIVE else [0.62, 0.85]
    OUTFILE = "out/t26_H4_5pos.json" if FIVE else "out/t26_H4.json"
    SEEDS = [0, 1]
    BUCKETS = [300, 1800, 3600, 7200, 21600, 86400, None]

    X, y, ts, src, dst = hs.load()
    N = len(y)
    src24 = hs.load_extra("src24"); dst24 = hs.load_extra("dst24")
    try:
        dport = hs.load_extra("dport"); HAVE_PORTS = True
    except FileNotFoundError as e:
        dport = None; HAVE_PORTS = False
        print(f"  [warn] destination ports unavailable, skipping the service-based family:\n    {e}")

    rows = []
    for pos in POS:
        i1, i2, i3 = hs.split_indices(N, pos)
        y_cal, y_te = y[i1:i2], y[i2:i3]
        ts_w = ts[i2:i3]
        fams = {"src-dst": [src[i2:i3], dst[i2:i3]],
                "src": [src[i2:i3]],
                "dst": [dst[i2:i3]],
                "subnet24": [src24[i2:i3], dst24[i2:i3]]}
        if HAVE_PORTS:
            fams["src-dport"] = [src[i2:i3], dport[i2:i3]]
        for seed in SEEDS:
            score = hs.fit_detector(X, y, i1, seed=seed, kind="hgb", verbose=False)
            s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
            e_te, cal, NC, CEIL = hs.evalues(s_cal, y_cal, s_te, k=K)
            tail_reach = float((e_te[y_te == 1] > 0).mean())
            for fam, keys in fams.items():
                for b in BUCKETS:
                    ep = hs.build_episodes(e_te, y_te, ts_w, bucket_s=b, keys=keys)
                    T = ep["T"]
                    margin = CEIL * W0 / T - 1.0
                    req_C = K * T / W0 - 1.0
                    ctx = Ctx(ep["Ev"], ep["ismal"], CEIL, alpha=A, w0=W0)
                    g1p, g0p = make_gamma("poly", T); g1u, _ = make_gamma("uniform", T)
                    mal_per_ep = np.bincount(ep["gid"], weights=y_te.astype(float),
                                             minlength=T)[ep["order"]]
                    tot_mal_flows = float(mal_per_ep.sum())
                    fired_lu = np.zeros(T, bool); lu = run_lond(ctx, g1u, fired=fired_lu)
                    fired_ad = np.zeros(T, bool)
                    ad = run_addis(ctx, g0p, lam=0.25, tau_=0.5, fired=fired_ad)
                    eb = run_online_ebh(ctx, g1u)
                    cov_lu = float(mal_per_ep[fired_lu].sum() / tot_mal_flows) if tot_mal_flows else None
                    cov_ad = float(mal_per_ep[fired_ad].sum() / tot_mal_flows) if tot_mal_flows else None
                    nz = ep["nsz"]
                    rows.append(dict(pos=pos, seed=seed, family=fam, bucket_s=b, T=int(T),
                                     n_mal=ep["n_mal"], NC=int(NC), margin=float(margin),
                                     required_C=float(req_C), feasible=bool(margin >= 0),
                                     tail_reach=tail_reach,
                                     flow_cov_elond=cov_lu, flow_cov_addis=cov_ad,
                                     mean_size=float(nz.mean()), p99_size=float(np.percentile(nz, 99)),
                                     max_size=int(nz.max()),
                                     elond_rej=int(lu[0]), elond_tp=int(lu[1]),
                                     elond_recall=float(lu[1] / ep["n_mal"]) if ep["n_mal"] else None,
                                     elond_silent=float(lu[2] / T),
                                     addis_rej=int(ad[0]), addis_tp=int(ad[1]),
                                     addis_recall=float(ad[1] / ep["n_mal"]) if ep["n_mal"] else None,
                                     ebh_rej=int(eb[0]), ebh_tp=int(eb[1]),
                                     ebh_recall=float(eb[1] / ep["n_mal"]) if ep["n_mal"] else None))
            print(f"  pos={pos} seed={seed} |C|={NC:,} tail-reach={tail_reach:.3f}  "
                  f"[{time.time()-t0:.0f}s]")


    def med(vals):
        v = [x for x in vals if x is not None]
        return float(np.median(v)) if v else None


    BLAB = {None: "no time field"}
    print("\n" + "=" * 118)
    print("H4 -- GROUPING FAMILIES.  medians over 2 positions x 2 seeds, k=1, q=0.05")
    print("=" * 118)
    print(f"  {'family':>11} {'bucket':>16} {'T':>10} {'mal ep':>7} {'required |C|':>14} "
          f"{'margin':>9} {'feas':>5} {'e-LOND rec':>11} {'ADDIS rec':>10} {'e-BH rec':>9}")
    summary = []
    for fam in ["src-dst", "src", "dst", "subnet24"] + (["src-dport"] if HAVE_PORTS else []):
        for b in BUCKETS:
            sub = [r for r in rows if r["family"] == fam and r["bucket_s"] == b]
            if not sub: continue
            rec = dict(family=fam, bucket_s=b, T=med([r["T"] for r in sub]),
                       n_mal=med([r["n_mal"] for r in sub]),
                       required_C=med([r["required_C"] for r in sub]),
                       margin=med([r["margin"] for r in sub]),
                       n_feasible=sum(1 for r in sub if r["feasible"]), n_cfg=len(sub),
                       elond_recall=med([r["elond_recall"] for r in sub]),
                       flow_cov_elond=med([r["flow_cov_elond"] for r in sub]),
                       flow_cov_addis=med([r["flow_cov_addis"] for r in sub]),
                       addis_recall=med([r["addis_recall"] for r in sub]),
                       ebh_recall=med([r["ebh_recall"] for r in sub]),
                       mean_size=med([r["mean_size"] for r in sub]),
                       max_size=med([r["max_size"] for r in sub]))
            summary.append(rec)
            lab = BLAB[None] if b is None else f"{b:,} s"
            print(f"  {fam:>11} {lab:>16} {rec['T']:>10,.0f} "
                  f"{rec['n_mal']:>7,.0f} {rec['required_C']:>14,.0f} {rec['margin']:>+9.3f} "
                  f"{rec['n_feasible']}/{rec['n_cfg']:<3} {rec['elond_recall']:>11.3f} "
                  f"{rec['addis_recall']:>10.3f} {rec['ebh_recall']:>9.3f}")


    print("\n  F4 -- FLOW-LEVEL vs EPISODE-LEVEL, same alerts (e-LOND, horizon-uniform gamma):")
    print(f"  {'family':>11} {'bucket':>16} {'episode recall':>15} {'malicious-flow coverage':>24} {'gap':>8}")
    for rec in summary:
        if rec["elond_recall"] is None or rec["flow_cov_elond"] is None: continue
        lab = BLAB[None] if rec["bucket_s"] is None else f"{rec['bucket_s']:,} s"
        gap = rec["flow_cov_elond"] - rec["elond_recall"]
        print(f"  {rec['family']:>11} {lab:>16} {rec['elond_recall']:>15.3f} "
              f"{rec['flow_cov_elond']:>24.3f} {gap:>+8.3f}")

    fc = med([r["tail_reach"] for r in rows])

    json.dump({"config": dict(POS=POS, SEEDS=SEEDS, BUCKETS=[b for b in BUCKETS],
                              k=K, alpha=A, w0=W0, have_ports=HAVE_PORTS),
               "rows": rows, "summary": summary, "flow_coverage_median": fc},
              open(OUTFILE, "w"), indent=1, allow_nan=True)
    print(f"\n  [{time.time()-t0:.0f}s]  wrote {OUTFILE}")


if __name__ == "__main__":
    import sys
    main(five="--five" in sys.argv)
