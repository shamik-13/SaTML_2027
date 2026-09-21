"""H5 -- cap-selection sweep."""


def main():
    import numpy as np, json, time
    from pathlib import Path
    import h_stream as hs

    Path("out").mkdir(exist_ok=True)
    t0 = time.time()
    W0 = 0.025; K = 1; BUCKET = 2 * 3600
    POS = [0.55, 0.62, 0.70, 0.77, 0.85]
    SEEDS = [0, 1]
    CAPS = ["mean", "p50", "p90", "p99", "p999", "max"]

    X, y, ts, src, dst = hs.load()
    N = len(y)


    def cal_group_sizes(ts_c, src_c, dst_c, bucket_s):
        b = ts_c // (bucket_s * 1_000_000)
        key = np.empty(len(b), dtype=[("s", "i8"), ("d", "i8"), ("b", "i8")])
        key["s"] = src_c; key["d"] = dst_c; key["b"] = b
        _, gid = np.unique(key, return_inverse=True)
        return np.bincount(gid)


    def cap_value(sizes, name):
        if name == "mean": return max(1, int(np.ceil(sizes.mean())))
        if name == "p50":  return max(1, int(np.ceil(np.percentile(sizes, 50))))
        if name == "p90":  return max(1, int(np.ceil(np.percentile(sizes, 90))))
        if name == "p99":  return max(1, int(np.ceil(np.percentile(sizes, 99))))
        if name == "p999": return max(1, int(np.ceil(np.percentile(sizes, 99.9))))
        if name == "max":  return int(sizes.max())
        raise ValueError(name)


    rows = []
    for pos in POS:
        i1, i2, i3 = hs.split_indices(N, pos)
        y_cal, y_te = y[i1:i2], y[i2:i3]
        ts_w = ts[i2:i3]
        csizes = cal_group_sizes(ts[i1:i2], src[i1:i2], dst[i1:i2], BUCKET)
        for seed in SEEDS:
            score = hs.fit_detector(X, y, i1, seed=seed, kind="hgb", verbose=False)
            s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
            e_te, cal, NC, CEIL = hs.evalues(s_cal, y_cal, s_te, k=K)
            ep = hs.build_episodes(e_te, y_te, ts_w, src[i2:i3], dst[i2:i3], BUCKET, "src-dst")
            gid = ep["gid"]; T = ep["T"]; thr = T / W0
            nsz_g = np.bincount(gid, minlength=T)
            mal_g = np.bincount(gid, weights=y_te.astype(float), minlength=T)
            sum_g = np.bincount(gid, weights=e_te, minlength=T)
            fired = (e_te > 0)
            fire_g = np.bincount(gid, weights=fired.astype(float), minlength=T)
            att = mal_g > 0
            ordg = np.argsort(gid, kind="stable")
            gs = gid[ordg]
            starts = np.searchsorted(gs, np.arange(T), side="left")
            rank = np.arange(len(gid)) - starts[gs]
            e_ordg = e_te[ordg]; fired_ordg = fired[ordg]
            for cname in CAPS:
                n0 = cap_value(csizes, cname)
                viol = int((nsz_g > n0).sum())
                viol_flow_share = float(nsz_g[nsz_g > n0].sum() / nsz_g.sum()) if viol else 0.0
                max_infl = float(nsz_g.max() / n0)
                need = int(np.ceil(thr * n0 / CEIL))
                det_raw = (sum_g / n0) >= thr
                trunc_sum = np.bincount(gs, weights=e_ordg * (rank < n0), minlength=T)
                det_tr = (trunc_sum / n0) >= thr
                def floor_of(mask):
                    m = mask & att
                    return int(mal_g[m].min()) if m.any() else None
                costs = []
                det_idx = np.nonzero(det_tr & att)[0]
                if len(det_idx):
                    fr_by_g = {}
                    sel = np.isin(gs, det_idx) & fired_ordg
                    for g_, r_ in zip(gs[sel], rank[sel]):
                        fr_by_g.setdefault(g_, []).append(r_)
                    for g_ in det_idx:
                        js = np.sort(np.array(fr_by_g.get(g_, [])))
                        if len(js) >= need and need >= 1:
                            costs.append(max(1, int(n0 - js[need - 1])))
                        else:
                            costs.append(1)
                rows.append(dict(pos=pos, seed=seed, cap=cname, n0=int(n0), T=int(T),
                                 thr=float(thr), CEIL=float(CEIL), need_flows=need,
                                 viol_groups=viol, viol_frac=float(viol / T),
                                 viol_flow_share=viol_flow_share, max_inflation=max_infl,
                                 det_raw=int((det_raw & att).sum()),
                                 det_trunc=int((det_tr & att).sum()),
                                 n_att_ep=int(att.sum()),
                                 floor_raw=floor_of(det_raw), floor_trunc=floor_of(det_tr),
                                 frontload_med=(float(np.median(costs)) if costs else None)))
            print(f"  pos={pos} seed={seed} T={T:,} thr={thr:,.0f}  [{time.time()-t0:.0f}s]")


    def agg(v):
        v = [x for x in v if x is not None]
        return (float(min(v)), float(np.median(v)), float(max(v))) if v else None


    def f3(a, p=0):
        return "  n/a  " if a is None else f"{a[0]:,.{p}f}/{a[1]:,.{p}f}/{a[2]:,.{p}f}"


    print("\n" + "=" * 120)
    print("H5 -- CAP SWEEP.  min/median/max over 5 positions x 2 seeds, two-hour grouping")
    print("=" * 120)
    print(f"  {'cap':>6} {'n0 med':>9} {'groups m>n0':>12} {'flows in them':>14} "
          f"{'max m/n0':>10} {'flows needed':>13}")
    summ = []
    for c in CAPS:
        sub = [r for r in rows if r["cap"] == c]
        rec = dict(cap=c, n0=agg([r["n0"] for r in sub]),
                   viol_frac=agg([r["viol_frac"] for r in sub]),
                   viol_flow_share=agg([r["viol_flow_share"] for r in sub]),
                   max_infl=agg([r["max_inflation"] for r in sub]),
                   need=agg([r["need_flows"] for r in sub]),
                   det_raw=agg([r["det_raw"] for r in sub]),
                   det_trunc=agg([r["det_trunc"] for r in sub]),
                   n_att=agg([r["n_att_ep"] for r in sub]),
                   floor_raw=agg([r["floor_raw"] for r in sub]),
                   floor_trunc=agg([r["floor_trunc"] for r in sub]),
                   frontload=agg([r["frontload_med"] for r in sub]))
        summ.append(rec)
        print(f"  {c:>6} {rec['n0'][1]:>9,.0f} {100*rec['viol_frac'][1]:>11.2f}% "
              f"{100*rec['viol_flow_share'][1]:>13.1f}% {rec['max_infl'][1]:>10,.0f} "
              f"{rec['need'][1]:>13,.0f}")

    print(f"\n  {'cap':>6} {'det raw (invalid where m>n0)':>30} {'det truncated (valid)':>24} "
          f"{'floor raw':>12} {'floor trunc':>13} {'front-load':>11}")
    for rec in summ:
        print(f"  {rec['cap']:>6} {f3(rec['det_raw']):>30} {f3(rec['det_trunc']):>24} "
              f"{f3(rec['floor_raw']):>12} {f3(rec['floor_trunc']):>13} "
              f"{f3(rec['frontload']):>11}")

    json.dump({"config": dict(POS=POS, SEEDS=SEEDS, CAPS=CAPS, bucket_s=BUCKET, k=K, w0=W0),
               "rows": rows, "summary": summ},
              open("out/t25_H5.json", "w"), indent=1, allow_nan=True)
    print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t25_H5.json")


if __name__ == "__main__":
    main()
