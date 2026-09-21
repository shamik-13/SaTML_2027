def main():
    import numpy as np, json, time
    from pathlib import Path
    import h_stream as hs
    from h6_procs import Ctx, make_gamma, run_lond, run_lordpp, run_addis, run_online_ebh

    Path("out").mkdir(exist_ok=True)
    t0 = time.time()
    QS = [0.01, 0.05, 0.10, 0.20]
    GAMMAS = ["poly", "uniform"]
    POS = [0.55, 0.62, 0.70, 0.77, 0.85]
    SEEDS = [0, 1]
    BUCKET = 2 * 3600; K = 1

    X, y, ts, src, dst = hs.load()
    N = len(y)
    rows = []
    for pos in POS:
        i1, i2, i3 = hs.split_indices(N, pos)
        if i1 <= 0: continue
        y_cal, y_te = y[i1:i2], y[i2:i3]
        for seed in SEEDS:
            score = hs.fit_detector(X, y, i1, seed=seed, kind="hgb", verbose=False)
            s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
            e_te, cal, NC, CEIL = hs.evalues(s_cal, y_cal, s_te, k=K)
            ep = hs.build_episodes(e_te, y_te, ts[i2:i3], src[i2:i3], dst[i2:i3], BUCKET, "src-dst")
            T = ep["T"]
            g1p, g0p = make_gamma("poly", T); g1u, g0u = make_gamma("uniform", T)
            for q in QS:
                w0 = q / 2.0
                ctx = Ctx(ep["Ev"], ep["ismal"], CEIL, alpha=q, w0=w0)
                margin = CEIL * w0 / T - 1.0
                for gk, g1, g0 in (("poly", g1p, g0p), ("uniform", g1u, g0u)):
                    def pack(nm, r):
                        rej, tp = r[0], r[1]
                        return dict(proc=nm, rejections=int(rej), tp=int(tp),
                                    fdp=(float(1 - tp / rej) if rej else None),
                                    recall=float(tp / ep["n_mal"]) if ep["n_mal"] else None,
                                    silent=float(r[2] / T),
                                    first_infeasible=(int(r[3]) if r[3] else None))
                    procs = [pack("e-LOND", run_lond(ctx, g1)),
                             pack("LORD++", run_lordpp(ctx, g1)),
                             pack("ADDIS", run_addis(ctx, g0, lam=0.25, tau_=0.5)),
                             pack("online e-BH", run_online_ebh(ctx, g1)[:4])]
                    rows.append(dict(pos=pos, seed=seed, q=q, w0=w0, gamma=gk, T=int(T),
                                     NC=int(NC), CEIL=float(CEIL), n_mal=ep["n_mal"],
                                     margin=float(margin), procs=procs))
            print(f"  pos={pos} seed={seed} T={T:,} |C|={NC:,}  [{time.time()-t0:.0f}s]")


    def agg(v):
        v = [x for x in v if x is not None]
        return (float(min(v)), float(np.median(v)), float(max(v))) if v else None


    def fmt(a, p=3):
        return "   n/a   " if a is None else f"{a[0]:.{p}f}/{a[1]:.{p}f}/{a[2]:.{p}f}"


    print("\n" + "=" * 112)
    print("H3a -- FEASIBILITY MARGIN vs q.  corollary predicts (margin+1) proportional to q")
    print("=" * 112)
    print(f"  {'q':>6} {'w0':>7} {'margin min/med/max':>26} {'(margin+1) median':>19} "
          f"{'ratio to q=0.05':>17} {'predicted':>10}")
    scal = []
    BASE_Q = 0.05
    if BASE_Q not in QS:
        raise ValueError(f"QS must contain BASE_Q={BASE_Q} for the ratio column")
    base = agg([r["margin"] for r in rows if r["q"] == BASE_Q and r["gamma"] == "poly"])[1] + 1.0
    for q in QS:
        sub = [r for r in rows if r["q"] == q and r["gamma"] == "poly"]
        mg = agg([r["margin"] for r in sub]); mp1 = mg[1] + 1.0
        scal.append(dict(q=q, margin=mg, margin_plus1=mp1, ratio=mp1 / base, predicted=q / 0.05))
        print(f"  {q:>6.2f} {q/2:>7.3f} {fmt(mg):>26} {mp1:>19.3f} {mp1/base:>17.3f} "
              f"{q/0.05:>10.1f}")

    for gk in GAMMAS:
        print("\n" + "=" * 112)
        print(f"H3b -- OPERATING POINT vs q,  gamma = {gk}   (min/median/max over 10 configs)")
        print("=" * 112)
        print(f"  {'q':>6} {'procedure':>13} {'rejections':>18} {'FDP':>22} {'recall':>22} "
              f"{'silent med':>11}")
        for q in QS:
            for pname in ("e-LOND", "ADDIS", "online e-BH"):
                sub = [p for r in rows if r["q"] == q and r["gamma"] == gk
                       for p in r["procs"] if p["proc"] == pname]
                rj = agg([p["rejections"] for p in sub]); fd = agg([p["fdp"] for p in sub])
                rc = agg([p["recall"] for p in sub]); sl = agg([p["silent"] for p in sub])
                rjs = "n/a" if rj is None else f"{int(rj[0])}/{int(rj[1])}/{int(rj[2])}"
                print(f"  {q:>6.2f} {pname:>13} {rjs:>18} {fmt(fd):>22} {fmt(rc):>22} "
                      f"{(100*sl[1] if sl else 0):>10.1f}%")

    print("\n" + "=" * 112)
    print("=" * 112)
    print(f"  {'q':>6} {'recall @ poly':>15} {'recall @ uniform':>18} {'gamma effect':>14}")
    lever = []
    for q in QS:
        r_poly = agg([p["recall"] for r in rows if r["q"] == q and r["gamma"] == "poly"
                      for p in r["procs"] if p["proc"] == "e-LOND"])
        r_uni = agg([p["recall"] for r in rows if r["q"] == q and r["gamma"] == "uniform"
                     for p in r["procs"] if p["proc"] == "e-LOND"])
        lever.append(dict(q=q, poly=r_poly, uniform=r_uni))
        d = (r_uni[1] - r_poly[1]) if (r_poly and r_uni) else float('nan')
        print(f"  {q:>6.2f} {r_poly[1]:>15.3f} {r_uni[1]:>18.3f} {d:>+14.3f}")
    qspan = max(l["poly"][1] for l in lever) - min(l["poly"][1] for l in lever)
    gspan = max(abs(l["uniform"][1] - l["poly"][1]) for l in lever)
    print(f"\n  spread in median recall from sweeping q 0.01->0.20 at fixed gamma: {qspan:.3f}")
    print(f"  largest shift from switching gamma at fixed q:                     {gspan:.3f}")

    json.dump({"config": dict(QS=QS, GAMMAS=GAMMAS, POS=POS, SEEDS=SEEDS, k=K, bucket_s=BUCKET),
               "rows": rows, "margin_scaling": scal, "lever": lever,
               "q_span_recall": float(qspan), "gamma_span_recall": float(gspan)},
              open("out/t24_H3.json", "w"), indent=1, allow_nan=True)
    print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t24_H3.json")


if __name__ == "__main__":
    main()
