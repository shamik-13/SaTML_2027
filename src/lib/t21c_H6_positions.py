import os
CSV = os.environ.get("LSPR_CSV", f'{os.environ.get("LSPR_DIR", "/tmp")}/lspr_full.csv')


def main():
    import numpy as np, pandas as pd, json, time, gc
    from pathlib import Path
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.metrics import roc_auc_score
    from h6_procs import (Ctx, make_gamma, run_lond, run_lordpp, run_saffron, run_addis,
                          run_online_ebh, run_egai)

    Path("out").mkdir(exist_ok=True)
    t0 = time.time()
    cols = ["ts", "src", "dst", "label", "proto"] + [f"f{i}" for i in range(32)]
    dt = {"ts": "int64", "src": "category", "dst": "category", "label": "int8", "proto": "float32"}
    dt.update({f"f{i}": "float32" for i in range(32)})
    df = pd.read_csv(CSV, header=None, names=cols, dtype=dt, low_memory=False)
    df = df.sort_values("ts", kind="mergesort").reset_index(drop=True)
    feat = ["proto"] + [f"f{i}" for i in range(32)]
    X = df[feat].to_numpy(dtype=np.float32, copy=True)
    np.nan_to_num(X, copy=False, nan=0.0, posinf=0.0, neginf=0.0)
    y = df["label"].to_numpy(copy=True); ts = df["ts"].to_numpy(copy=True)
    src = df["src"].cat.codes.to_numpy(dtype=np.int32, copy=True)
    dst = df["dst"].cat.codes.to_numpy(dtype=np.int32, copy=True)
    del df; gc.collect(); N = len(y)
    print(f"loaded+sorted N={N:,}  [{time.time()-t0:.0f}s]")

    W0 = 0.025; A = 0.05; K = 1; BH = 2
    CAL_F = TEST_F = 0.15
    POS = [0.55, 0.62, 0.70, 0.77, 0.85]
    SEEDS = [0, 1]

    rows = []
    for pos in POS:
        i2 = int(pos * N); i1 = i2 - int(CAL_F * N); i3 = min(N, i2 + int(TEST_F * N))
        if i1 <= 0: continue
        b = ts[i2:i3] // (BH * 3600 * 1_000_000)
        key = np.empty(i3 - i2, dtype=[("s", "i4"), ("d", "i4"), ("b", "i8")])
        key["s"] = src[i2:i3]; key["d"] = dst[i2:i3]; key["b"] = b
        _, gid = np.unique(key, return_inverse=True); T = int(gid.max() + 1)
        nsz = np.bincount(gid, minlength=T)
        mal = np.bincount(gid, weights=y[i2:i3].astype(float), minlength=T)
        first_ts = np.full(T, np.iinfo(np.int64).max); np.minimum.at(first_ts, gid, ts[i2:i3])
        first_pos = np.full(T, np.iinfo(np.int64).max)
        np.minimum.at(first_pos, gid, np.arange(len(gid), dtype=np.int64))
        order = np.lexsort((first_pos, first_ts))
        g1p, g0p = make_gamma("poly", T); g1u, g0u = make_gamma("uniform", T)

        for seed in SEEDS:
            rng = np.random.default_rng(seed)
            tr = np.arange(i1); ben = tr[y[tr] == 0]
            tr_idx = np.sort(np.concatenate([tr[y[tr] == 1], ben[rng.random(len(ben)) < 0.5]]))
            clf = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1,
                  l2_regularization=1.0, min_samples_leaf=200, random_state=seed,
                  early_stopping=False).fit(X[tr_idx], y[tr_idx])
            s_cal = clf.decision_function(X[i1:i2]); s_te = clf.decision_function(X[i2:i3])
            y_cal, y_te = y[i1:i2], y[i2:i3]
            cal = np.sort(s_cal[y_cal == 0]); NC = len(cal); CEIL = NC + 1.0
            Kr = 1 + (NC - np.searchsorted(cal, s_te, side='left'))
            e_te = np.where(Kr <= K, CEIL, 0.0)
            auroc = float(roc_auc_score(y_te, s_te))
            sum_e = np.bincount(gid, weights=e_te, minlength=T)
            Ev = (sum_e / np.maximum(nsz, 1))[order]; ismal = (mal > 0)[order]
            ctx = Ctx(Ev, ismal, CEIL, alpha=A, w0=W0)
            margin = (NC + 1.0) * W0 / T - 1.0

            def rec(proc, gk, r, note=""):
                rej, tp, sil, fi = r[0], r[1], r[2], r[3]
                rows.append(dict(pos=pos, seed=seed, gamma=gk, proc=proc, T=int(T), NC=int(NC),
                                 auroc=auroc, margin=float(margin), n_mal=ctx.NMAL,
                                 rejections=int(rej), tp=int(tp),
                                 fdp=(float(1 - tp / rej) if rej else None),
                                 recall=float(tp / ctx.NMAL) if ctx.NMAL else None,
                                 silent=float(sil / T),
                                 first_infeasible=(int(fi) if fi else None), note=note))

            for gk, g1, g0 in (("poly", g1p, g0p), ("uniform", g1u, g0u)):
                r = run_lond(ctx, g1)
                rec("LOND", gk, r); rec("e-LOND", gk, r)
                rec("LORD++", gk, run_lordpp(ctx, g1))
                rec("SAFFRON", gk, run_saffron(ctx, g1, lam=0.5))
                rec("ADDIS", gk, run_addis(ctx, g0, lam=0.25, tau_=0.5))
                eb = run_online_ebh(ctx, g1)
                rec("online e-BH", gk, eb[:4], note=f"k*_T={eb[4]}; never-rejectable={eb[6]/T:.4f}")
            for nm, kw in (("e-LORD", {}), ("e-SAFFRON", dict(lam=0.1)),
                           ("mem-e-LORD", dict(d=0.99))):
                rec(nm, "egai(w1=1/T)", run_egai(ctx, nm, 1.0 / T, **kw))
            print(f"  pos={pos} seed={seed} AUROC={auroc:.4f} T={T:,} |C|={NC:,} "
                  f"margin={margin:+.3f} mal={ctx.NMAL}  [{time.time()-t0:.0f}s]")

    PROCS = ["LOND", "e-LOND", "LORD++", "SAFFRON", "ADDIS", "online e-BH",
             "e-LORD", "e-SAFFRON", "mem-e-LORD"]


    def agg(vals):
        v = [x for x in vals if x is not None]
        if not v: return None, None, None
        return float(min(v)), float(np.median(v)), float(max(v))


    def block(gk, title):
        print("\n" + "=" * 118); print(title); print("=" * 118)
        print(f"  {'procedure':>14} {'rejections min/med/max':>24} {'FDP min/med/max':>24} "
              f"{'recall min/med/max':>22} {'silent med':>11} {'FDP>q':>6}")
        out = []
        for pr in PROCS:
            sub = [r for r in rows if r['proc'] == pr and r['gamma'] == gk]
            if not sub: continue
            rj = agg([r['rejections'] for r in sub])
            fd = agg([r['fdp'] for r in sub])
            rc = agg([r['recall'] for r in sub])
            sl = agg([r['silent'] for r in sub])
            nfdp = [r['fdp'] for r in sub if r['fdp'] is not None]
            over = sum(1 for f in nfdp if f > 0.05)
            meanfdp = float(np.mean(nfdp)) if nfdp else None
            out.append(dict(proc=pr, gamma=gk, n_cfg=len(sub),
                            rejections=rj, fdp=fd, recall=rc, silent=sl,
                            mean_fdp=meanfdp, n_fdp_over_q=over, n_with_rejections=len(nfdp)))
            f = lambda a, p=3: "  n/a  " if a[0] is None else f"{a[0]:.{p}f}/{a[1]:.{p}f}/{a[2]:.{p}f}"
            rjs = "0/0/0" if rj[0] is None else f"{int(rj[0])}/{int(rj[1])}/{int(rj[2])}"
            print(f"  {pr:>14} {rjs:>24} {f(fd):>24} {f(rc):>22} "
                  f"{(100*sl[1] if sl[1] is not None else 0):>10.1f}% {over:>3}/{len(nfdp):<3}")
        return out


    summary = {}
    summary["poly"] = block("poly", "H6 over 5 positions x 2 seeds -- gamma prop j^-1.6 (the section 4.17 choice)")
    summary["uniform"] = block("uniform", "H6 over 5 positions x 2 seeds -- horizon-uniform gamma = 1/T (max-min optimal)")
    summary["egai"] = block("egai(w1=1/T)", "H6 over 5 positions x 2 seeds -- e-GAI family (w1 = 1/T)")

    print("\n  'FDP>q' counts configurations whose realised FDP exceeded q = 0.05, out of those")
    print("  that made at least one rejection.  Mean FDP is the empirical estimate of FDR.")
    for gk in summary:
        for r in summary[gk]:
            if r['mean_fdp'] is not None:
                print(f"    {r['gamma']:>14} {r['proc']:>14}  mean FDP = {r['mean_fdp']:.4f}  "
                      f"over {r['n_with_rejections']} configs with rejections")

    json.dump({"config": dict(POS=POS, SEEDS=SEEDS, bucket_h=BH, k=K, alpha=A, w0=W0),
               "rows": rows, "summary": summary},
              open("out/t21c_H6_positions.json", "w"), indent=1, allow_nan=True)
    print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t21c_H6_positions.json")


if __name__ == "__main__":
    main()
