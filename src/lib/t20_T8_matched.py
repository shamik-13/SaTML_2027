def _run_position(POS, X, y, ts, src, dst, hs):
    import numpy as np, time
    from scipy.special import zeta
    from sklearn.metrics import roc_auc_score
    t0 = time.time()
    N = len(y)
    W0 = 0.025; A = 0.05; K = 1; Q = 0.05
    i1, i2, i3 = hs.split_indices(N, POS)
    score = hs.fit_detector(X, y, i1, seed=0, kind="hgb", verbose=False)
    s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
    y_cal, y_te = y[i1:i2], y[i2:i3]
    e_te, cal, NC, CEIL = hs.evalues(s_cal, y_cal, s_te, k=K)
    BH = 2; b = ts[i2:i3] // (BH * 3600 * 1_000_000)
    key = np.empty(i3 - i2, dtype=[("s", "i4"), ("d", "i4"), ("b", "i8")])
    key["s"] = src[i2:i3]; key["d"] = dst[i2:i3]; key["b"] = b
    _, gid = np.unique(key, return_inverse=True); T = int(gid.max() + 1)
    nsz = np.bincount(gid, minlength=T)
    mal = np.bincount(gid, weights=y_te.astype(float), minlength=T)
    sum_e = np.bincount(gid, weights=e_te, minlength=T)
    smax = np.full(T, -np.inf); np.maximum.at(smax, gid, s_te)
    first = np.full(T, np.iinfo(np.int64).max); np.minimum.at(first, gid, ts[i2:i3])
    o = np.argsort(first, kind="mergesort")
    smax, ismal, nz, se = smax[o], (mal > 0)[o], nsz[o], sum_e[o]
    NM = int(ismal.sum()); thr = T / W0
    auroc = float(roc_auc_score(y_te, s_te))
    print(f"  pos={POS}  AUROC={auroc:.4f} |C|={NC:,} T={T:,} malicious episodes={NM}"
          f"  [{time.time()-t0:.0f}s]")

    ordr = np.lexsort((np.arange(T), -smax)); m = ismal[ordr]
    tp = np.cumsum(m); fp = np.cumsum(~m); kk = np.arange(1, T + 1); fdp = fp / kk; rec = tp / NM

    def frontier_at_budget(nb):
        b = float(np.clip(nb, 0.0, T))
        if b <= 0: return 0.0, 0.0
        k = int(np.floor(b)); frac = b - k
        base = float(tp[k - 1]) if k else 0.0
        extra = float(m[k]) if k < T else 0.0
        r = (base + frac * extra) / NM
        fp_b = (float(fp[k - 1]) if k else 0.0) + frac * (1.0 - extra)
        return float(r), float(fp_b / b)

    def frontier_at_fdp(q):
        ok = np.flatnonzero(fdp <= q)
        if not len(ok): return None, None, None
        best = tp[ok].max(); cand = ok[tp[ok] == best]; i = cand[np.argmin(fdp[cand])]
        return float(rec[i]), float(fdp[i]), int(kk[i])

    methods = []

    def add(nm, fired, note=""):
        R = int(fired.sum()); V = int((fired & ~ismal).sum())
        methods.append(dict(method=nm, alerts=R, fdp=float(V / R) if R else float('nan'),
                            recall=float((fired & ismal).sum() / NM), note=note))

    gam = np.arange(1, T + 1, dtype=float) ** -1.6 / float(zeta(1.6, 1))
    Ev = se / np.maximum(nz, 1); fired = np.zeros(T, bool); R = 0
    for t in range(1, T + 1):
        lvl = A * gam[t - 1] * (R + 1)
        if lvl > 0 and CEIL >= 1.0 / lvl and Ev[t - 1] >= 1.0 / lvl: fired[t - 1] = True; R += 1
    add("online FDR (e-LOND, mean rule)", fired, "self-selected budget")
    fire_ct = np.bincount(gid, weights=(e_te > 0).astype(float), minlength=T)[o]
    pD = (1.0 if CEIL >= thr else 0.0) * fire_ct / np.maximum(nz, 1)
    methods.append(dict(method="online FDR (policy D, slot)", alerts=float(pD.sum()),
        fdp=float(pD[~ismal].sum() / pD.sum()) if pD.sum() else float('nan'),
        recall=float(pD[ismal].sum() / NM),
        note="randomised rule; alerts and FDP are E[R] and E[V]/E[R], not E[V/R]"))

    def feedback(L, eta=0.02, u0=0.999, win=200):
        u = u0; f = np.zeros(T, bool); pend = []; hist = []; na = 0
        for i in range(T):
            arr = 0
            if L is not None:
                while pend and pend[0][0] <= na - L: hist.append(pend.pop(0)[1]); arr += 1
            if arr and len(hist) >= 10:
                u = float(np.clip(u + eta * (np.mean(hist[-win:]) - Q), 0.5, 1.0))
            if smax[i] > cal[int(np.clip(u * (NC - 1), 0, NC - 1))]:
                f[i] = True; na += 1
                if L is not None: pend.append((na, 0.0 if ismal[i] else 1.0))
        return f

    for L, nm in [(0, "feedback controller (L=0)"), (20, "feedback controller (L=20 alerts)"),
                  (50, "feedback controller (L=50 alerts)"), (None, "fixed threshold (no feedback)")]:
        add(nm, feedback(L))
    print("\n" + "=" * 112)
    print(f"T8 -- ALL METHODS, ONE STREAM (position {POS})")
    print("=" * 112)
    print(f"  {'method':>34} {'alerts':>9} {'FDP':>8} {'recall':>8} | {'frontier recall':>15} {'gap':>8}")
    print("  " + "-" * 104)
    for mth in methods:
        fr, _ = frontier_at_budget(mth["alerts"])
        mth["frontier_recall_at_budget"] = fr; mth["gap"] = fr - mth["recall"]
        print(f"  {mth['method']:>34} {mth['alerts']:>9,.1f} {mth['fdp']:>8.3f} {mth['recall']:>8.3f} | "
              f"{fr:>15.3f} {fr-mth['recall']:>+8.3f}")
    print("\n  MATCHED-FDP VIEW (best recall achievable at each error level):")
    print(f"  {'target FDP':>11} {'frontier recall':>16} {'alerts':>9} {'achieved FDP':>13}")
    fr_rows = []
    for q in (0.00, 0.01, 0.05, 0.10, 0.20):
        r, f_, k_ = frontier_at_fdp(q)
        if r is None: continue
        fr_rows.append(dict(q=q, recall=r, fdp=f_, alerts=k_))
        print(f"  {q:>11.3f} {r:>16.3f} {k_:>9,} {f_:>13.3f}")
    return {"methods": methods, "frontier": fr_rows, "T": int(T), "NM": NM,
            "NC": int(NC), "thr": float(thr), "auroc": auroc, "pos": POS}


def main():
    import json, time
    from pathlib import Path
    import h_stream as hs
    Path("out").mkdir(exist_ok=True); t0 = time.time()
    X, y, ts, src, dst = hs.load()
    per_pos = {}
    for POS in (0.55, 0.85):
        per_pos[f"{POS}"] = _run_position(POS, X, y, ts, src, dst, hs)

    old = Path("out/t20_T8.json")
    if old.exists():
        prev = json.load(open(old))
        if "methods" in prev:
            new85 = per_pos["0.85"]
            assert prev["T"] == new85["T"] and prev["NM"] == new85["NM"] \
                and prev["NC"] == new85["NC"], "0.85 episode stream changed"
            for a, b in zip(prev["methods"], new85["methods"]):
                assert a["method"] == b["method"] and a["alerts"] == b["alerts"] \
                    and abs(a["recall"] - b["recall"]) < 1e-12, f"0.85 regression: {a['method']}"
            print("\n  regression vs original 0.85 artifact: OK")

    out = {"config": dict(primary_pos=0.55, stress_pos=0.85, seed=0, k=1, w0=0.025,
                          alpha=0.05, q=0.05, bucket_h=2),
           "per_pos": per_pos,
           "note": ("0.55 = primary / guarantee window (evidence a valid e-value); "
                    "0.85 = stress-test window (evidence not a valid e-value, sec:tail); "
                    "FDP at 0.85 is a measurement against labels, not a guarantee")}
    json.dump(out, open("out/t20_T8.json", "w"), indent=1, allow_nan=False)
    print(f"\n  [{time.time()-t0:.0f}s] wrote out/t20_T8.json")
    return out


if __name__ == "__main__":
    main()
