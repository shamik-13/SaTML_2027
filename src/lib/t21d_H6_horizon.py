"""H6, part 3 -- how much of each escape is bought with oracle knowledge of the horizon?"""

import os

# The derived LSPR23 CSV.  Same override pattern as h_stream/h_meta: LSPR_DIR moves the
# inputs off the volatile /tmp default without changing behaviour for the documented recipes.
CSV = os.environ.get("LSPR_CSV", f'{os.environ.get("LSPR_DIR", "/tmp")}/lspr_full.csv')


def main():
    import numpy as np, pandas as pd, json, time, gc
    from pathlib import Path
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.metrics import roc_auc_score
    from h6_procs import Ctx, make_gamma, run_lond, run_lordpp, run_addis, run_online_ebh, run_egai

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

    POS = 0.85; CAL_F = TEST_F = 0.15; W0 = 0.025; A = 0.05; K = 1; BH = 2
    i2 = int(POS * N); i1 = i2 - int(CAL_F * N); i3 = min(N, i2 + int(TEST_F * N))
    rng = np.random.default_rng(0); tr = np.arange(i1); ben = tr[y[tr] == 0]
    tr_idx = np.sort(np.concatenate([tr[y[tr] == 1], ben[rng.random(len(ben)) < 0.5]]))
    clf = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1, l2_regularization=1.0,
          min_samples_leaf=200, random_state=0, early_stopping=False).fit(X[tr_idx], y[tr_idx])
    s_cal = clf.decision_function(X[i1:i2]); s_te = clf.decision_function(X[i2:i3])
    y_cal, y_te = y[i1:i2], y[i2:i3]
    cal = np.sort(s_cal[y_cal == 0]); NC = len(cal); CEIL = NC + 1.0
    Kr = 1 + (NC - np.searchsorted(cal, s_te, side='left')); e_te = np.where(Kr <= K, CEIL, 0.0)
    b = ts[i2:i3] // (BH * 3600 * 1_000_000)
    key = np.empty(i3 - i2, dtype=[("s", "i4"), ("d", "i4"), ("b", "i8")])
    key["s"] = src[i2:i3]; key["d"] = dst[i2:i3]; key["b"] = b
    _, gid = np.unique(key, return_inverse=True); T = int(gid.max() + 1)
    nsz = np.bincount(gid, minlength=T); mal = np.bincount(gid, weights=y_te.astype(float), minlength=T)
    sum_e = np.bincount(gid, weights=e_te, minlength=T)
    first_ts = np.full(T, np.iinfo(np.int64).max); np.minimum.at(first_ts, gid, ts[i2:i3])
    first_pos = np.full(T, np.iinfo(np.int64).max)
    np.minimum.at(first_pos, gid, np.arange(len(gid), dtype=np.int64))
    order = np.lexsort((first_pos, first_ts))
    Ev = (sum_e / np.maximum(nsz, 1))[order]; ismal = (mal > 0)[order]
    ctx = Ctx(Ev, ismal, CEIL, alpha=A, w0=W0)
    print(f"AUROC={roc_auc_score(y_te, s_te):.4f}  T={T:,}  |C|={NC:,}  malicious={ctx.NMAL}  "
          f"margin={(NC+1.0)*W0/T-1:+.3f}  [{time.time()-t0:.0f}s]")


    def gamma_uniform_hat(That, T):
        """gamma_j = 1/That for j <= That, 0 afterwards.  If That < T the procedure has spent"""
        g1 = np.zeros(T + 2); n = min(int(That), T)
        g1[1:n + 1] = 1.0 / float(That)
        return g1


    def line(proc, c, That, r, extra=""):
        rej, tp, sil, fi = r[0], r[1], r[2], r[3]
        fdp = (1 - tp / rej) if rej else float('nan')
        rows.append(dict(proc=proc, c=float(c), T_hat=int(That), rejections=int(rej), tp=int(tp),
                         fdp=(None if rej == 0 else float(fdp)), recall=float(tp / ctx.NMAL),
                         silent=float(sil / T), first_infeasible=(int(fi) if fi else None)))
        print(f"  {proc:>13} c={c:<6g} T_hat={That:<9,} rejections={rej:>4,} tp={tp:>4,} "
              f"FDP={'  -  ' if rej == 0 else f'{fdp:.3f}':>6} recall={tp/ctx.NMAL:>5.3f} "
              f"silent={100*sil/T:>5.1f}% {extra}")


    rows = []
    CS = [0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 100.0]
    print("\n" + "=" * 112)
    print("HORIZON MISSPECIFICATION -- horizon-uniform gamma over a guessed horizon T_hat = c*T")
    print("=" * 112)
    for c in CS:
        That = max(1, int(round(c * T)))
        g1 = gamma_uniform_hat(That, T)
        line("LOND/e-LOND", c, That, run_lond(ctx, g1), "<- c=1 is oracle" if c == 1.0 else "")
    for c in CS:
        That = max(1, int(round(c * T)))
        line("LORD++", c, That, run_lordpp(ctx, gamma_uniform_hat(That, T)))
    for c in CS:
        That = max(1, int(round(c * T)))
        eb = run_online_ebh(ctx, gamma_uniform_hat(That, T))
        line("online e-BH", c, That, eb[:4], f"k*_T={eb[4]:,} never-rejectable={100*eb[6]/T:.1f}%")

    print("\n" + "=" * 112)
    print("HORIZON MISSPECIFICATION -- e-GAI e-LORD with w_1 = 1/T_hat")
    print("=" * 112)
    for c in CS:
        That = max(1, int(round(c * T)))
        line("e-LORD", c, That, run_egai(ctx, "e-LORD", 1.0 / That),
             "<- c=1 is the paper's recommended w_1 = 1/T" if c == 1.0 else "")

    print("\n" + "=" * 112)
    print("CONTROL -- ADDIS under gamma prop j^-1.6, which uses no horizon at all")
    print("=" * 112)
    g1p, g0p = make_gamma("poly", T)
    r = run_addis(ctx, g0p, lam=0.25, tau_=0.5)
    line("ADDIS", float('nan'), 0, r, "<- needs no horizon")
    addis_row = rows[-1]

    json.dump({"config": dict(POS=POS, bucket_h=BH, k=K, alpha=A, w0=W0, T=int(T), NC=int(NC),
                              CEIL=float(CEIL), n_malicious=ctx.NMAL),
               "rows": rows, "cs": CS}, open("out/t21d_H6_horizon.json", "w"), indent=1, allow_nan=True)
    print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t21d_H6_horizon.json")


if __name__ == "__main__":
    main()
