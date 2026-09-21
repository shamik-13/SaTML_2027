import json
import time
from pathlib import Path

import numpy as np

import h_stream as hs
from h6_procs import Ctx, make_gamma, run_lond

A = 0.05; W0 = 0.025; K = 1; BUCKET = 2 * 3600
POS = [0.55, 0.62]
SEED = 0
ORDERS = ["keyhash", "first-flow"]          # canonical carries the paper; first-flow as a check
GAMMAS = ["poly", "uniform"]

# The shipped canonical numbers this must reproduce on the poly arm.
CONTROL = {0.55: (3, [23, 24, 33]), 0.62: (11, 6.0)}


def elond_levels(ctx, T, gamma_kind):
    """e-LOND fired mask and tau_t = 1/alpha_t, with alpha_t = A*gamma_t*(R_{t-1}+1).
    """
    g1, _ = make_gamma(gamma_kind, T)
    fired = np.zeros(T, dtype=bool)
    run_lond(ctx, g1, fired=fired)
    R_before = np.concatenate([[0], np.cumsum(fired)[:-1]]).astype(float)
    alpha_t = A * g1[np.arange(1, T + 1)] * (R_before + 1.0)
    with np.errstate(divide="ignore"):
        tau_t = np.where(alpha_t > 0, 1.0 / alpha_t, np.inf)
    return fired, tau_t


def zero_pad(S, n, tau):
    """Minimum zero-evidence additions r with S/(n+r) < tau. t28b's definition, verbatim."""
    x = S / tau - n
    return int(np.floor(x)) + 1 if x >= 0 else 0


def main():
    t0 = time.time()
    Path("out").mkdir(exist_ok=True)
    X, y, ts, src, dst = hs.load()
    N = len(y)
    out = {"config": dict(alpha=A, w0=W0, k=K, bucket_s=BUCKET, positions=POS, seed=SEED,
                          orders=ORDERS, gammas=GAMMAS,
                          canonical_order="keyhash"), "cells": {}}

    for pos in POS:
        i1, i2, i3 = hs.split_indices(N, pos)
        y_cal, y_te = y[i1:i2], y[i2:i3]
        ts_w, src_w, dst_w = ts[i2:i3], src[i2:i3], dst[i2:i3]
        score = hs.fit_detector(X, y, i1, seed=SEED, kind="hgb", verbose=False)
        s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
        e_te, cal, NC, CEIL = hs.evalues(s_cal, y_cal, s_te, k=K)
        for order in ORDERS:
            ep = hs.build_episodes(e_te, y_te, ts_w, src_w, dst_w, BUCKET, "src-dst", order=order)
            T = ep["T"]
            rho = (NC + 1) * (2 * W0) / T          # controller-aligned feasibility ratio, e-LOND
            for gk in GAMMAS:
                ctx = Ctx(ep["Ev"], ep["ismal"], CEIL, alpha=A, w0=W0)
                fired, tau_t = elond_levels(ctx, T, gk)
                det = np.nonzero(fired & ep["ismal"])[0]
                fp = int((fired & ~ep["ismal"]).sum())
                S, n = ep["sum_e"], ep["nsz"]
                pads = [zero_pad(float(S[j]), int(n[j]), float(tau_t[j])) for j in det]
                lvls = [float(tau_t[j]) for j in det]          # 1/alpha_t where each alert fired

                # --- conspicuity -------------------------------------------------------------
                # "Is a pad of this size noticeable?" was marked UNANSWERED by two mock reviewers,
                # and it matters much more now that the horizon-aware arm needs ~10^3 flows rather
                # than ~10^1. Two measurements, both from the deployment stream itself:
                #   (a) where the PADDED episode sits in the deployment arity distribution;
                #   (b) the tradeoff curve for the defence a practitioner reaches for first, a
                #       per-host-pair per-bucket cap: it blocks the pad iff m + r* > cap, and it
                #       costs the defender every BENIGN episode above the cap.
                arity = np.asarray(n, dtype=float)
                benign_arity = arity[~ep["ismal"]]
                padded = np.array([int(n[j]) + p_ for j, p_ in zip(det, pads)], dtype=float)
                exceed = [float((arity >= a).mean()) for a in padded]   # share at least as large
                caps = [10, 30, 100, 300, 1000, 3000, 10000]
                curve = [dict(cap=c,
                              pads_blocked=float((padded > c).mean()) if len(padded) else None,
                              benign_truncated=float((benign_arity > c).mean()))
                         for c in caps]
                rec = dict(
                    pos=pos, seed=SEED, order=order, gamma=gk, T=int(T), NC=int(NC),
                    rho_elond=float(rho), n_malicious=int(ep["ismal"].sum()),
                    detections=int(len(det)), false_positives=fp,
                    recall=float(len(det) / max(1, int(ep["ismal"].sum()))),
                    pads=sorted(int(v) for v in pads),
                    median_pad=(float(np.median(pads)) if pads else None),
                    total_pad=int(sum(pads)),
                    median_level=(float(np.median(lvls)) if lvls else None),
                    first_det_step=int(det[0]) if len(det) else None,
                    median_padded_arity=(float(np.median(padded)) if len(padded) else None),
                    median_deployment_exceedance=(float(np.median(exceed)) if exceed else None),
                    deployment_arity_p50=float(np.percentile(arity, 50)),
                    deployment_arity_p99=float(np.percentile(arity, 99)),
                    deployment_arity_max=float(arity.max()),
                    ratelimit_curve=curve)
                out["cells"][f"{pos}_{order}_{gk}"] = rec
                print(f"  pos={pos} {order:<10} gamma={gk:<8} rho={rho:5.2f} "
                      f"det={rec['detections']:>4} recall={rec['recall']:.3f} "
                      f"median r*={rec['median_pad']} total={rec['total_pad']:>8} "
                      f"median 1/alpha={rec['median_level']:.3g}" if lvls else
                      f"  pos={pos} {order:<10} gamma={gk:<8} rho={rho:5.2f} det=0")

    # --- CONTROL: the poly x canonical arm must reproduce the shipped numbers ------------------
    c55 = out["cells"]["0.55_keyhash_poly"]; c62 = out["cells"]["0.62_keyhash_poly"]
    assert (c55["detections"], c55["pads"]) == CONTROL[0.55], \
        f"CONTROL FAILED at 0.55: got {c55['detections']} dets, pads {c55['pads']}"
    assert (c62["detections"], c62["median_pad"]) == CONTROL[0.62], \
        f"CONTROL FAILED at 0.62: got {c62['detections']} dets, median {c62['median_pad']}"
    out["control_reproduced"] = True
    print("\n  CONTROL OK: the poly x canonical arm reproduces the shipped 3/[23,24,33] and 11/6")

    json.dump(out, open("out/t73_uniform_padding.json", "w"), indent=1)
    print(f"  wrote out/t73_uniform_padding.json  [{time.time()-t0:.0f}s]")


if __name__ == "__main__":
    main()
