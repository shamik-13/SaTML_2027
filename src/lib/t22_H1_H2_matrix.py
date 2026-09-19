def main():
    import numpy as np, json, time
    from pathlib import Path
    from sklearn.metrics import roc_auc_score
    import h_stream as hs
    from h6_procs import Ctx, make_gamma, run_lond, run_lordpp, run_saffron, run_addis, run_online_ebh

    Path("out").mkdir(exist_ok=True)
    t0 = time.time()
    W0 = 0.025; A = 0.05; BUCKET = 2 * 3600
    POS = [0.55, 0.62, 0.70, 0.77, 0.85]
    SEEDS = [0, 1]
    KS = [1, 10, 100, 1000]
    DETS = ["hgb", "iforest"]

    X, y, ts, src, dst = hs.load()
    N = len(y)
    rows = []

    for pos in POS:
        i1, i2, i3 = hs.split_indices(N, pos)
        if i1 <= 0: continue
        y_cal, y_te = y[i1:i2], y[i2:i3]
        ts_w, src_w, dst_w = ts[i2:i3], src[i2:i3], dst[i2:i3]
        n_att_flows = int(y_te.sum())
        for det in DETS:
            for seed in SEEDS:
                score = hs.fit_detector(X, y, i1, seed=seed, kind=det, verbose=False)
                s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
                auroc = float(roc_auc_score(y_te, s_te))
                for k in KS:
                    e_te, cal, NC, CEIL = hs.evalues(s_cal, y_cal, s_te, k=k)
                    ep = hs.build_episodes(e_te, y_te, ts_w, src_w, dst_w, BUCKET, "src-dst")
                    T = ep["T"]
                    margin = CEIL * W0 / T - 1.0
                    fired = e_te > 0
                    tail_reach = float(fired[y_te == 1].mean()) if n_att_flows else float('nan')
                    ben = y_te == 0
                    p_fire_ben = float(fired[ben].mean())
                    nominal = k / (NC + 1.0)
                    ctx = Ctx(ep["Ev"], ep["ismal"], CEIL, alpha=A, w0=W0)
                    g1p, g0p = make_gamma("poly", T); g1u, _ = make_gamma("uniform", T)

                    def pack(nm, r):
                        rej, tp = r[0], r[1]
                        return dict(proc=nm, rejections=int(rej), tp=int(tp),
                                    fdp=(float(1 - tp / rej) if rej else None),
                                    recall=float(tp / ep["n_mal"]) if ep["n_mal"] else None,
                                    silent=float(r[2] / T))
                    procs = [pack("e-LOND/poly", run_lond(ctx, g1p)),
                             pack("e-LOND/uniform", run_lond(ctx, g1u)),
                             pack("LORD++/poly", run_lordpp(ctx, g1p)),
                             pack("ADDIS/poly", run_addis(ctx, g0p, lam=0.25, tau_=0.5)),
                             pack("online e-BH/uniform", run_online_ebh(ctx, g1u)[:4])]

                    smax = np.full(T, -np.inf); np.maximum.at(smax, ep["gid"], s_te)
                    fr = hs.frontier(smax[ep["order"]], ep["ismal"])
                    for p in procs:
                        if p["rejections"]:
                            frr, _ = hs.frontier_at_budget(fr, p["rejections"])
                            p["frontier_recall"] = frr
                            p["gap"] = frr - (p["recall"] or 0.0)
                        else:
                            p["frontier_recall"] = None; p["gap"] = None
                    fr0 = hs.frontier_at_fdp(fr, 0.0); fr05 = hs.frontier_at_fdp(fr, 0.05)

                    rows.append(dict(detector=det, pos=pos, seed=seed, k=k, auroc=auroc,
                                     NC=int(NC), CEIL=float(CEIL), T=int(T), n_mal=ep["n_mal"],
                                     margin=float(margin), tail_reach=tail_reach,
                                     p_fire_benign=p_fire_ben, nominal_fire=float(nominal),
                                     fire_ratio=float(p_fire_ben / nominal) if nominal else None,
                                     n_att_flows=n_att_flows, procs=procs,
                                     frontier_fdp0=dict(recall=fr0[0], alerts=fr0[2]),
                                     frontier_fdp05=dict(recall=fr05[0], alerts=fr05[2])))
                print(f"  {det:>8} pos={pos} seed={seed} AUROC={auroc:.4f}  [{time.time()-t0:.0f}s]")

    json.dump({"config": dict(POS=POS, SEEDS=SEEDS, KS=KS, DETS=DETS, bucket_s=BUCKET,
                              alpha=A, w0=W0), "rows": rows},
              open("out/t22_H1_H2.json", "w"), indent=1, allow_nan=True)


    def agg(vals):
        v = [x for x in vals if x is not None]
        if not v: return None
        return (float(min(v)), float(np.median(v)), float(max(v)))


    def fmt(a, p=3):
        return "   n/a   " if a is None else f"{a[0]:.{p}f}/{a[1]:.{p}f}/{a[2]:.{p}f}"


    print("\n" + "=" * 118)
    print("H1 -- SECOND DETECTOR.  min/median/max over 5 positions x 2 seeds, k = 1")
    print("=" * 118)
    print(f"  {'detector':>9} {'AUROC':>22} {'feasibility margin':>22} {'tail reach':>22} "
          f"{'benign fire ratio':>20}")
    h1 = {}
    for det in DETS:
        sub = [r for r in rows if r["detector"] == det and r["k"] == 1]
        h1[det] = dict(auroc=agg([r["auroc"] for r in sub]), margin=agg([r["margin"] for r in sub]),
                       tail=agg([r["tail_reach"] for r in sub]),
                       ratio=agg([r["fire_ratio"] for r in sub]))
        print(f"  {det:>9} {fmt(h1[det]['auroc'],4):>22} {fmt(h1[det]['margin']):>22} "
              f"{fmt(h1[det]['tail']):>22} {fmt(h1[det]['ratio'],2):>20}")

    print("\n  per-procedure, k = 1, min/median/max over the 10 configurations:")
    print(f"  {'detector':>9} {'procedure':>20} {'rejections':>18} {'FDP':>20} {'recall':>20} "
          f"{'silent med':>11}")
    h1p = []
    for det in DETS:
        for pname in ("e-LOND/poly", "e-LOND/uniform", "ADDIS/poly", "online e-BH/uniform"):
            sub = [p for r in rows if r["detector"] == det and r["k"] == 1
                   for p in r["procs"] if p["proc"] == pname]
            rj = agg([p["rejections"] for p in sub]); fd = agg([p["fdp"] for p in sub])
            rc = agg([p["recall"] for p in sub]); sl = agg([p["silent"] for p in sub])
            h1p.append(dict(detector=det, proc=pname, rejections=rj, fdp=fd, recall=rc, silent=sl))
            rjs = "n/a" if rj is None else f"{int(rj[0])}/{int(rj[1])}/{int(rj[2])}"
            print(f"  {det:>9} {pname:>20} {rjs:>18} {fmt(fd):>20} {fmt(rc):>20} "
                  f"{(100*sl[1] if sl else 0):>10.1f}%")

    print("\n" + "=" * 118)
    print("=" * 118)
    h2 = []
    for det in DETS:
        print(f"\n  detector = {det}")
        print(f"  {'k':>6} {'ceiling':>14} {'feasibility margin':>22} {'tail reach':>22} "
              f"{'benign fire ratio':>20} {'e-LOND/uniform rej':>20}")
        for k in KS:
            sub = [r for r in rows if r["detector"] == det and r["k"] == k]
            ce = agg([r["CEIL"] for r in sub]); mg = agg([r["margin"] for r in sub])
            tr = agg([r["tail_reach"] for r in sub]); ra = agg([r["fire_ratio"] for r in sub])
            rj = agg([p["rejections"] for r in sub for p in r["procs"]
                      if p["proc"] == "e-LOND/uniform"])
            h2.append(dict(detector=det, k=k, ceiling=ce, margin=mg, tail_reach=tr,
                           fire_ratio=ra, elond_uniform_rej=rj))
            rjs = "n/a" if rj is None else f"{int(rj[0])}/{int(rj[1])}/{int(rj[2])}"
            print(f"  {k:>6} {ce[1]:>14,.0f} {fmt(mg):>22} {fmt(tr):>22} {fmt(ra,2):>20} {rjs:>20}")

    json.dump({"config": dict(POS=POS, SEEDS=SEEDS, KS=KS, DETS=DETS, bucket_s=BUCKET,
                              alpha=A, w0=W0),
               "rows": rows, "h1_summary": h1, "h1_procs": h1p, "h2_summary": h2},
              open("out/t22_H1_H2.json", "w"), indent=1, allow_nan=True)
    print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t22_H1_H2.json")


if __name__ == "__main__":
    main()
