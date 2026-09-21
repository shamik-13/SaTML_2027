


def main(smoke=False):
    import numpy as np, json, time, sys, gc
    from pathlib import Path
    from sklearn.metrics import roc_auc_score

    import h_stream as H

    Path("out").mkdir(exist_ok=True)
    SMOKE = smoke
    t0 = time.time()

    BH = 2
    Q = 0.05
    DSEEDS = [0, 1]
    HOUR = 3600 * 1_000_000
    DELAYS_H = [0.0, 0.25, 1.0, 4.0, 8.0]
    DELAYS_H_LONG = [0.0, 1.0, 6.0, 24.0]
    UNMEASURABLE = [72.0]
    if SMOKE:
        DSEEDS = [0]


    def run_controller(kind, smax, ismal, first_ts, cal, delay_us, q=Q,
                       eta_p=0.02, eta_i=0.002, u0=0.999, window=200, step=None):
        """Threshold controller on the episode max score, with WALL-CLOCK disposition delay."""
        NC = len(cal)
        T = len(smax)
        u = float(u0)
        integral = 0.0
        step = eta_p if step is None else float(step)
        fired = np.zeros(T, bool)
        n_updates = 0
        n_clamped = 0
        first_update_t = None
        pending = []
        ptr = 0
        hist = []
        u_trace = np.empty(T)
        for t in range(T):
            now = first_ts[t]
            while ptr < len(pending) and pending[ptr][0] <= now:
                _, was_false = pending[ptr]; ptr += 1
                hist.append(was_false)
                n_updates += 1
                if first_update_t is None:
                    first_update_t = t
                if kind == "AQT":
                    u = u + step * ((1.0 - q) if was_false else -q)
                else:
                    w = hist[-window:]
                    fdp_hat = float(np.mean(w)) if w else 0.0
                    err = fdp_hat - q
                    if kind == "P":
                        u = u + eta_p * err
                    elif kind == "PI":
                        if 0.0 < u < 1.0 or err * (0.5 - u) > 0:
                            integral += err
                        u = u + eta_p * err + eta_i * integral
                    else:
                        raise ValueError(kind)
            if u >= 1.0 or u <= 0.0:
                n_clamped += 1
            u = float(np.clip(u, 0.0, 1.0))
            u_trace[t] = u
            thr = cal[int(np.clip(np.floor(u * (NC - 1)), 0, NC - 1))]
            if smax[t] > thr:
                fired[t] = True
                pending.append((now + delay_us, not bool(ismal[t])))
        rej = int(fired.sum()); tp = int((fired & ismal).sum())
        alert_idx = np.flatnonzero(fired)
        burn = (int((alert_idx < first_update_t).sum()) if first_update_t is not None
                else int(fired.sum()))
        return dict(rejections=rej, tp=tp, fp=rej - tp,
                    fdp=float((rej - tp) / max(rej, 1)),
                    recall=float(tp / max(int(ismal.sum()), 1)),
                    n_updates=n_updates, burn_in_alerts=burn,
                    frac_steps_clamped=float(n_clamped / max(T, 1)),
                    u_final=float(u), u_min=float(u_trace.min()), u_max=float(u_trace.max()),
                    fired=fired)


    X, y, ts, src, dst = H.load()
    N = len(y)
    rows, per_cfg, notes = [], [], []

    WINDOWS = [("guarantee (0.55)", 0.55, "block", DELAYS_H),
               ("long-span (0.10) [WEAK-CAL]", 0.10, "toend", DELAYS_H_LONG)]

    for wname, pos, mode, delays in WINDOWS:
        i2 = int(pos * N)
        i1 = i2 - int(0.15 * N) if i2 - int(0.15 * N) > 0 else i2 // 2
        i3 = min(N, i2 + int(0.15 * N)) if mode == "block" else N
        ts_w, y_te = ts[i2:i3], y[i2:i3]
        span_h = float((ts_w.max() - ts_w.min()) / 3.6e9)
        for dseed in DSEEDS:
            sc = H.fit_detector(X, y, i1, dseed, kind="hgb")
            s_cal, s_te = H.score_windows(sc, X, i1, i2, i3)
            y_cal = y[i1:i2]
            cal = np.sort(s_cal[y_cal == 0]); NC = len(cal)
            auroc = float(roc_auc_score(y_te, s_te))
            ep = H.build_episodes(np.zeros(len(y_te)), y_te, ts_w, src[i2:i3], dst[i2:i3],
                                  bucket_s=BH * 3600)
            gid, order, T, ismal, NMAL = ep["gid"], ep["order"], ep["T"], ep["ismal"], ep["n_mal"]
            smax = np.full(T, -np.inf); np.maximum.at(smax, gid, s_te); smax = smax[order]
            fts = np.full(T, np.iinfo(np.int64).max); np.minimum.at(fts, gid, ts_w); fts = fts[order]
            fr = H.frontier(smax, ismal)
            print(f"\n  {wname} seed {dseed}: span {span_h:.2f} h, T={T:,}, {NMAL} malicious "
                  f"episodes ({100*NMAL/T:.2f}%), |C|={NC:,}, AUROC={auroc:.4f} "
                  f"[{time.time()-t0:.0f}s]")
            for dh in delays:
                if dh > span_h:
                    notes.append(f"{wname}: a {dh:g} h delay exceeds the {span_h:.2f} h window -- "
                                 f"every alert would be open-loop; not run")
                    continue
                for kind in ("P", "PI", "AQT"):
                    if kind == "AQT":
                        grid = [dict(step=st, u0=uu, eta_p=0.02, window=200)
                                for st in (1e-4, 1e-3, 5e-3, 0.02) for uu in (0.99, 0.999)]
                        fixed = dict(step=1e-3, u0=0.999, eta_p=0.02, window=200)
                    else:
                        grid = [dict(eta_p=et, window=wn, u0=uu, step=None)
                                for et in (0.005, 0.02, 0.05, 0.2)
                                for wn in (50, 200) for uu in (0.99, 0.999)]
                        fixed = dict(eta_p=0.02, window=200, u0=0.999, step=None)
                    best, bestkey, best_cfg = None, None, fixed
                    for cfg in grid:
                        cand = run_controller(kind, smax, ismal, fts, cal, int(dh * HOUR),
                                              eta_p=cfg["eta_p"], eta_i=cfg["eta_p"] / 10.0,
                                              u0=cfg["u0"], window=cfg["window"],
                                              step=cfg["step"])
                        if cand["rejections"] == 0:
                            continue
                        key = (abs(cand["fdp"] - Q), -cand["recall"])
                        if best is None or key < bestkey:
                            best, bestkey, best_cfg = cand, key, cfg
                    rfix = run_controller(kind, smax, ismal, fts, cal, int(dh * HOUR),
                                          eta_p=fixed["eta_p"], eta_i=fixed["eta_p"] / 10.0,
                                          u0=fixed["u0"], window=fixed["window"],
                                          step=fixed["step"])
                    r = best if best is not None else rfix
                    orec, ofdp = H.frontier_at_budget(fr, r["rejections"])
                    rows.append(dict(window=wname, pos=pos, dseed=dseed, span_h=span_h,
                                     delay_h=dh, controller=kind, T=int(T), NC=int(NC),
                                     NMAL=int(NMAL), auroc=auroc,
                                     prevalence=float(NMAL / T),
                                     rejections=r["rejections"], tp=r["tp"], fdp=r["fdp"],
                                     recall=r["recall"], n_updates=r["n_updates"],
                                     burn_in_alerts=r["burn_in_alerts"],
                                     frac_open_loop=float(r["burn_in_alerts"] /
                                                          max(r["rejections"], 1)),
                                     alerts_per_day=float(r["rejections"] / (span_h / 24.0)),
                                     oracle_recall_at_budget=float(orec),
                                     u_final=r["u_final"], u_min=r["u_min"], u_max=r["u_max"],
                                     best_cfg={k: v for k, v in best_cfg.items()},
                                     frac_steps_clamped=r["frac_steps_clamped"],
                                     saturated=bool(r["frac_steps_clamped"] > 0.5),
                                     fixed_rejections=rfix["rejections"], fixed_fdp=rfix["fdp"],
                                     fixed_recall=rfix["recall"],
                                     fixed_frac_clamped=rfix["frac_steps_clamped"]))
            rno = run_controller("P", smax, ismal, fts, cal, int(1e18))
            orec, _ = H.frontier_at_budget(fr, rno["rejections"])
            rows.append(dict(window=wname, pos=pos, dseed=dseed, span_h=span_h, delay_h=None,
                             controller="none (open loop)", T=int(T), NC=int(NC), NMAL=int(NMAL),
                             auroc=auroc, prevalence=float(NMAL / T),
                             rejections=rno["rejections"], tp=rno["tp"], fdp=rno["fdp"],
                             recall=rno["recall"], n_updates=0,
                             burn_in_alerts=rno["rejections"], frac_open_loop=1.0,
                             alerts_per_day=float(rno["rejections"] / (span_h / 24.0)),
                             oracle_recall_at_budget=float(orec),
                             u_final=rno["u_final"], u_min=rno["u_min"], u_max=rno["u_max"]))
            per_cfg.append(dict(window=wname, dseed=dseed, span_h=span_h, T=int(T),
                                NMAL=int(NMAL), NC=int(NC), auroc=auroc,
                                prevalence=float(NMAL / T)))
            del s_cal, s_te, cal, ep
            gc.collect()

    for d in UNMEASURABLE:
        notes.append(f"a {d:g} h disposition delay is UNMEASURABLE on LSPR23: the longest "
                     f"deployment window that leaves room for training and calibration spans "
                     f"26.98 h (section 4.35)")

    def agg(v):
        v = [x for x in v if x is not None]
        return (float(np.mean(v)), float(np.std(v, ddof=1)) if len(v) > 1 else 0.0) if v else (None, None)


    for wname, _, _, _ in WINDOWS:
        sub = [r for r in rows if r["window"] == wname]
        if not sub: continue
        c = [c for c in per_cfg if c["window"] == wname][0]
        print("\n" + "=" * 128)
        print(f"{wname}   span {c['span_h']:.2f} h · T={c['T']:,} · {c['NMAL']} malicious "
              f"episodes ({100*c['prevalence']:.2f}%) · target q = {Q}")
        print("=" * 128)
        tagw = "GUARANTEE" if "guarantee" in wname else "WEAK-CAL"
        print(f"  {'window':>10} {'delay':>8} {'ctrl':>5} {'alerts':>8} {'FDP (tuned)':>14} "
              f"{'recall':>14} {'oracle@bud':>10} {'updates':>7} {'open-loop':>9} "
              f"{'clamped':>9} {'FDP fixed':>9} {'knob':>8}")
        for dh in sorted({r["delay_h"] for r in sub if r["delay_h"] is not None}):
            for kind in ("P", "PI", "AQT"):
                rr = [r for r in sub if r["delay_h"] == dh and r["controller"] == kind]
                if not rr: continue
                rj, _ = agg([r["rejections"] for r in rr]); fd, fs = agg([r["fdp"] for r in rr])
                rc, rs = agg([r["recall"] for r in rr]); nu, _ = agg([r["n_updates"] for r in rr])
                ol, _ = agg([r["frac_open_loop"] for r in rr])
                orc, _ = agg([r["oracle_recall_at_budget"] for r in rr])
                apd, _ = agg([r["alerts_per_day"] for r in rr])
                flag = "  <-- above q" if fd > Q else ""
                cfgs = {json.dumps(r.get("best_cfg", {}), sort_keys=True) for r in rr}
                bc = "mixed" if len(cfgs) > 1 else str(
                    rr[0].get("best_cfg", {}).get("step")
                    if kind == "AQT" else rr[0].get("best_cfg", {}).get("eta_p"))
                ff, _ = agg([r["fixed_fdp"] for r in rr])
                cl, _ = agg([r["frac_steps_clamped"] for r in rr])
                print(f"  {tagw:>10} {dh:>7.2f}h {kind:>5} {rj:>8.1f} {fd:>7.3f}±{fs:<6.3f} "
                      f"{rc:>7.3f}±{rs:<6.3f} {orc:>10.3f} {nu:>7.0f} {100*ol:>8.1f}% "
                      f"{100*cl:>8.1f}% {ff:>9.3f} {bc:>8}{flag}")
        rr = [r for r in sub if r["controller"] == "none (open loop)"]
        if rr:
            rj, _ = agg([r["rejections"] for r in rr]); fd, _ = agg([r["fdp"] for r in rr])
            rc, _ = agg([r["recall"] for r in rr]); apd, _ = agg([r["alerts_per_day"] for r in rr])
            print(f"  {tagw:>10} {'--':>8} {'none':>5} {rj:>8.1f} {fd:>14.3f} {rc:>14.3f} "
                  f"{'':>10} {0:>7} {100.0:>8.1f}% {'':>9} {'':>9} {'':>8}")

    print("\n" + "=" * 128)
    print("SCOPE")
    print("=" * 128)
    for n in sorted(set(notes)):
        print("  " + n)

    json.dump(dict(config=dict(bucket_h=BH, q=Q, dseeds=DSEEDS, delays_h=DELAYS_H,
                               delays_h_long=DELAYS_H_LONG, unmeasurable_h=UNMEASURABLE,
                               smoke=SMOKE),
                   rows=rows, per_cfg=per_cfg, notes=sorted(set(notes))),
              open("out/t40_E7_controller.json", "w"), indent=1, allow_nan=True)
    print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t40_E7_controller.json")


if __name__ == "__main__":
    import sys
    main(smoke="--smoke" in sys.argv)
