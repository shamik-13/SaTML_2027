import json
import time
from pathlib import Path

import numpy as np

import h_stream as hs
from h6_procs import Ctx, make_gamma, run_lond

A = 0.05; W0 = 0.025; K = 1; BUCKET = 2 * 3600
POS = [0.55, 0.62]
SEED = 0
ORDER = "keyhash"
GAMMAS = ["poly", "uniform"]
N_POOL_SAMPLE = 20000            # pool flows scored to measure the firing rate, as t48 does
N_DRAWS = 200                    # stochastic replay draws per alert, as the AIT arm uses
CAPS = [30, 100, 300, 1000, 3000, 10000]
FAMILIES = ["src-dst", "src", "dst"]
CONTROL = (3, [23, 24, 33])


def elond_levels(ctx, T, gamma_kind):
    g1, _ = make_gamma(gamma_kind, T)
    fired = np.zeros(T, dtype=bool)
    run_lond(ctx, g1, fired=fired)
    R_before = np.concatenate([[0], np.cumsum(fired)[:-1]]).astype(float)
    alpha_t = A * g1[np.arange(1, T + 1)] * (R_before + 1.0)
    with np.errstate(divide="ignore"):
        tau_t = np.where(alpha_t > 0, 1.0 / alpha_t, np.inf)
    return fired, tau_t


def main():
    t0 = time.time()
    Path("out").mkdir(exist_ok=True)
    X, y, ts, src, dst = hs.load()
    N = len(y)
    dport_all = hs.load_extra("dport")
    out = {"config": dict(alpha=A, w0=W0, k=K, bucket_s=BUCKET, positions=POS, seed=SEED,
                          order=ORDER, gammas=GAMMAS, n_draws=N_DRAWS, caps=CAPS,
                          families=FAMILIES), "cells": {}, "families": {}}

    for pos in POS:
        i1, i2, i3 = hs.split_indices(N, pos)
        y_cal, y_te = y[i1:i2], y[i2:i3]
        ts_w, src_w, dst_w = ts[i2:i3], src[i2:i3], dst[i2:i3]
        dp_w = dport_all[i2:i3]
        pr_w = np.asarray(X[i2:i3, 0]).astype(np.int32)

        score = hs.fit_detector(X, y, i1, seed=SEED, kind="hgb", verbose=False)
        s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
        e_te, cal, NC, CEIL = hs.evalues(s_cal, y_cal, s_te, k=K)

        svc = pr_w.astype(np.int64) * 100000 + dp_w.astype(np.int64)
        svc_tr = (np.asarray(X[:i1, 0]).astype(np.int64) * 100000
                  + dport_all[:i1].astype(np.int64))
        u, c = np.unique(svc_tr, return_counts=True)
        pool_idx = np.nonzero(svc == int(u[np.argmax(c)]))[0]
        rng = np.random.default_rng(SEED)

        pad_e = e_te[pool_idx]                               # REAL flows, real detector e-values
        n_fire = int((pad_e > 0).sum())
        pad_fire = float(n_fire / pad_e.size)
        # exact one-sided 95% Clopper-Pearson upper bound; at 0 successes it is 1 - 0.05^(1/n)
        p_ub = 1.0 - 0.05 ** (1.0 / pad_e.size) if n_fire == 0 else None
        print(f"  pos={pos}  pool={pool_idx.size:,} flows  firing={n_fire}  "
              f"95% CP upper bound p<={p_ub:.3g}  pad_mean_e={pad_e.mean():.4f}")

        for gk in GAMMAS:
            ep = hs.build_episodes(e_te, y_te, ts_w, src_w, dst_w, BUCKET, "src-dst", order=ORDER)
            T = ep["T"]
            ctx = Ctx(ep["Ev"], ep["ismal"], CEIL, alpha=A, w0=W0)
            fired, tau_t = elond_levels(ctx, T, gk)
            det = np.nonzero(fired & ep["ismal"])[0]
            S, m = ep["sum_e"], ep["nsz"]
            arity = np.asarray(m, float)
            benign_arity = arity[~ep["ismal"]]

            per, closed = [], []
            for j in det:
                Sj, mj, tauj = float(S[j]), int(m[j]), float(tau_t[j])
                x = Sj / tauj - mj
                r_c = int(np.floor(x)) + 1 if x >= 0 else 0
                closed.append(r_c)
                # --- replay: draw r_c REAL pool flows, N_DRAWS times --------------------------
                draws = rng.choice(pad_e, size=(N_DRAWS, max(r_c, 1)), replace=True)
                got = (Sj + draws.sum(axis=1)) / (mj + r_c) < tauj if r_c > 0 else \
                    np.zeros(N_DRAWS, bool)
                succ = float(got.mean())

                hits = (rng.binomial(max(r_c, 1), p_ub, size=N_DRAWS) if p_ub
                        else np.zeros(N_DRAWS, int))
                got_ub = ((Sj + hits * CEIL) / (mj + r_c) < tauj if r_c > 0
                          else np.zeros(N_DRAWS, bool))
                succ_ub = float(got_ub.mean())
                worst = float(draws.sum(axis=1).max())
                x_w = (Sj + worst) / tauj - mj
                r_worst = int(np.floor(x_w)) + 1 if x_w >= 0 else 0
                per.append(dict(ep=int(j), m=mj, S=Sj, tau=tauj, r_closed=r_c,
                                per_draw_success=succ, per_draw_success_at_ub=succ_ub,
                                n_hits_max=int(hits.max()) if p_ub else 0,
                                r_worst_draw=r_worst))
            succs = [p["per_draw_success"] for p in per]
            succs_ub = [p["per_draw_success_at_ub"] for p in per]
            rw = [p["r_worst_draw"] for p in per]
            # --- the cap: can the attacker suppress while staying UNDER it? ------------------
            cap_rows = []
            for n in CAPS:
                fits = [int(p["m"]) + p["r_worst_draw"] <= n for p in per]
                cap_rows.append(dict(cap=n,
                                     suppressible_under_cap=float(np.mean(fits)) if fits else None,
                                     n_fits=int(sum(fits)), of=len(fits),
                                     benign_truncated=float((benign_arity > n).mean())))
            rec = dict(pos=pos, gamma=gk, order=ORDER, T=int(T), NC=int(NC),
                       detections=int(len(det)), pad_fire_rate=pad_fire,
                       pad_mean_e=float(pad_e.mean()),
                       r_closed_sorted=sorted(int(v) for v in closed),
                       median_r_closed=float(np.median(closed)) if closed else None,
                       per_draw_success_min=min(succs) if succs else None,
                       per_draw_success_at_ub_min=min(succs_ub) if succs_ub else None,
                       per_draw_success_at_ub_mean=(float(np.mean(succs_ub)) if succs_ub else None),
                       pool_firing_count=n_fire, pool_firing_upper_bound=p_ub,
                       per_draw_success_max=max(succs) if succs else None,
                       n_alerts_always_suppressed=int(sum(s == 1.0 for s in succs)),
                       median_r_worst_draw=float(np.median(rw)) if rw else None,
                       cap_curve=cap_rows, per_episode=per)
            out["cells"][f"{pos}_{gk}"] = rec
            print(f"    gamma={gk:<8} det={rec['detections']:>4} median r*={rec['median_r_closed']} "
                  f"per-draw {rec['per_draw_success_min']:.3f} "
                  f"at-CP-bound min {rec['per_draw_success_at_ub_min']:.3f} "
                  f"always-suppressed {rec['n_alerts_always_suppressed']}/{rec['detections']}")

        # --- grouping families: is there a key the attacker cannot cheaply co-occupy? ---------
        for fam in FAMILIES:
            for gk in GAMMAS:
                epf = hs.build_episodes(e_te, y_te, ts_w, src_w, dst_w, BUCKET, fam, order=ORDER)
                Tf = epf["T"]
                ctxf = Ctx(epf["Ev"], epf["ismal"], CEIL, alpha=A, w0=W0)
                firedf, tauf = elond_levels(ctxf, Tf, gk)
                detf = np.nonzero(firedf & epf["ismal"])[0]
                Sf, mf = epf["sum_e"], epf["nsz"]
                rr = []
                for j in detf:
                    xx = float(Sf[j]) / float(tauf[j]) - int(mf[j])
                    rr.append(int(np.floor(xx)) + 1 if xx >= 0 else 0)
                out["families"][f"{pos}_{fam}_{gk}"] = dict(
                    pos=pos, family=fam, gamma=gk, T=int(Tf), detections=int(len(detf)),
                    median_r=float(np.median(rr)) if rr else None,
                    total_r=int(sum(rr)))
                print(f"    family={fam:<8} gamma={gk:<8} T={Tf:>7} det={len(detf):>4} "
                      f"median r*={out['families'][f'{pos}_{fam}_{gk}']['median_r']}")

    c = out["cells"]["0.55_poly"]
    assert (c["detections"], c["r_closed_sorted"]) == CONTROL, \
        f"CONTROL FAILED: {c['detections']} dets, {c['r_closed_sorted']}"
    out["control_reproduced"] = True
    print("\n  CONTROL OK: poly x canonical x src-dst reproduces 3 / [23, 24, 33]")
    json.dump(out, open("out/t74_defended_replay.json", "w"), indent=1)
    print(f"  wrote out/t74_defended_replay.json  [{time.time()-t0:.0f}s]")


if __name__ == "__main__":
    main()
