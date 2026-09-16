"""Attack-surface-A padding cost priced against the RUNNING controller level 1/alpha_t.

The static price is against the horizon-uniform feasibility threshold tau = T/w0 -- the level a
Family-II procedure offers at its first step (R = 0), i.e. an attacker who suppresses every alert
from the start; it is reported here as med_pad_static.  The main price is each detected
alert against the level e-LOND actually offers at that episode's step, alpha_t = alpha *
gamma_t * (R_{t-1}+1), reconstructed from a real run_lond pass -- the same controller-aware
pricing t32_B1 uses for ADDIS.  Feedback (suppressing one alert lowers later levels) is not
charged, so the costs are a lower bound.

Produces out/t28b_reallevel.json:
  table1 : per (pos,seed) e-LOND detections and median black-box pad, real vs static  (Table I)
           -- under the SHIPPED first-flow within-bucket order, kept byte-identical.
  table1_by_order : the same quantities under each within-bucket order in ORDERS_RUN (review-7
           item R3).  "keyhash" is the CANONICAL order -- a splitmix64 hash of the group's own
           (SrcIP,DstIP,bucket) key -- which is evidence-independent AND not timing-influenceable,
           so it is the order the paper should report as primary; first-flow is an optimistic
           upper bound (t53 measures the whole ensemble).  Detections and the level each alert
           fires at both move with the order; T, NC, AUROC and the margin do not.
  pools  : per (pos,seed) five-pool median r_mean, real vs static, at 0.62 and 0.85     (tab:pools)
  fig4a_pools : per-pool sorted real-level pad arrays at 0.85 seed 0                     (Fig 4A)
"""
import numpy as np, json, time
from pathlib import Path
from sklearn.metrics import roc_auc_score
import h_stream as hs
from h6_procs import Ctx, make_gamma, run_lond

A = 0.05; W0 = 0.025; K = 1; BUCKET = 2 * 3600
POS_ALL = [0.55, 0.62, 0.70, 0.77, 0.85]
POS_POOL = [0.62, 0.85]
SEEDS = [0, 1]
# Within-bucket orders to price (review-7 item R3).  "first-flow" is the shipped order and is
# reported byte-identically in table1; "keyhash" is the canonical order the paper now leads with.
ORDERS_RUN = ["first-flow", "keyhash", "keyed"]


def elond_levels(ctx, T):
    """Run e-LOND (poly gamma) and return (fired mask, tau_t) with tau_t[j] = 1/alpha_t at
    the ordered step j+1, alpha_t = A*gamma_t*(R_{t-1}+1)."""
    g1, _ = make_gamma("poly", T)
    fired = np.zeros(T, dtype=bool)
    run_lond(ctx, g1, fired=fired)
    R_before = np.concatenate([[0], np.cumsum(fired)[:-1]]).astype(float)
    alpha_t = A * g1[np.arange(1, T + 1)] * (R_before + 1.0)
    with np.errstate(divide="ignore"):
        tau_t = np.where(alpha_t > 0, 1.0 / alpha_t, np.inf)
    return fired, tau_t


def zero_pad(S, n, tau):
    """min pads r with S/(n+r) < tau (mu=0 pool): r = floor(S/tau - n)+1, clamped >= 0."""
    x = S / tau - n
    return int(np.floor(x)) + 1 if x >= 0 else 0


def main():
    t0 = time.time()
    Path("out").mkdir(exist_ok=True)
    X, y, ts, src, dst = hs.load()
    N = len(y)
    dport_all = hs.load_extra("dport")
    proto_col = 0                       # h_stream feature order is ["proto"] + f0..f31

    table1, pools_out, fig4a, fig4a_guar = {}, {}, {}, {}
    table1_by_order = {o: {} for o in ORDERS_RUN}
    pools_by_order = {o: {} for o in ORDERS_RUN}
    for pos in POS_ALL:
        i1, i2, i3 = hs.split_indices(N, pos)
        y_cal, y_te = y[i1:i2], y[i2:i3]
        ts_w, src_w, dst_w = ts[i2:i3], src[i2:i3], dst[i2:i3]
        dp_w = dport_all[i2:i3]
        pr_w = np.asarray(X[i2:i3, proto_col]).astype(np.int32)
        att_src = np.unique(src_w[y_te == 1]); is_att_src = np.isin(src_w, att_src)
        ben = (y_te == 0)
        svc = pr_w.astype(np.int64) * 100000 + dp_w.astype(np.int64)
        uu, cc = np.unique(svc[ben], return_counts=True); bb_svc = uu[np.argmax(cc)]
        for seed in SEEDS:
            score = hs.fit_detector(X, y, i1, seed=seed, kind="hgb", verbose=False)
            s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
            e_te, cal, NC, CEIL = hs.evalues(s_cal, y_cal, s_te, k=K)
            auroc = float(roc_auc_score(y_te, s_te)) if np.unique(y_te).size == 2 else None
            for order in ORDERS_RUN:
                ep = hs.build_episodes(e_te, y_te, ts_w, src_w, dst_w, BUCKET, "src-dst",
                                       order=order)
                T = ep["T"]; tau_static = T / W0
                ctx = Ctx(ep["Ev"], ep["ismal"], CEIL, alpha=A, w0=W0)
                fired, tau_t = elond_levels(ctx, T)
                det = np.nonzero(fired & ep["ismal"])[0]        # e-LOND true-positive detections
                S = ep["sum_e"]; n = ep["nsz"]
                pads_real = [zero_pad(float(S[j]), int(n[j]), float(tau_t[j])) for j in det]
                pads_static = [zero_pad(float(S[j]), int(n[j]), tau_static) for j in det]
                rec = dict(
                    pos=pos, seed=seed, T=int(T), NC=int(NC), auroc=auroc, order=order,
                    detected_elond=int(len(det)),
                    med_pad_real=(float(np.median(pads_real)) if pads_real else None),
                    med_pad_static=(float(np.median(pads_static)) if pads_static else None),
                    pads_real=sorted(int(v) for v in pads_real))
                table1_by_order[order][f"{pos}_{seed}"] = rec
                if order == "first-flow":
                    # the shipped record, kept key-for-key as it was before item R3 so the
                    # transcribed numbers in docs/04 and the paper stay checkable
                    table1[f"{pos}_{seed}"] = {kk: rec[kk] for kk in
                                               ("pos", "seed", "T", "NC", "auroc",
                                                "detected_elond", "med_pad_real",
                                                "med_pad_static")}
                print(f"  pos={pos} seed={seed} order={order:<10} det={len(det):>3} "
                      f"med_pad real={rec['med_pad_real']} "
                      f"static={rec['med_pad_static']}  [{time.time()-t0:.0f}s]")

                if pos not in POS_POOL:
                    continue
                # ---- five-pool recompute against real levels (t28 pool logic) ----
                gid = ep["gid"]; inv = np.empty(T, dtype=np.int64); inv[ep["order"]] = np.arange(T)
                ep_of_flow = inv[gid]
                pool_lvl = {"generic": ben, "attacker-origin": ben & is_att_src,
                            "black-box": ben & (svc == bb_svc)}
                stats = {nm: (float(e_te[m].mean()), float((e_te[m] > 0).mean()))
                         for nm, m in pool_lvl.items() if m.sum()}
                _pm, _sm = {}, {}

                def proto_pool(v):
                    if v not in _pm:
                        m = ben & (pr_w == v)
                        _pm[v] = ((float(e_te[m].mean()), float((e_te[m] > 0).mean()))
                                  if m.any() else None)
                    return _pm[v]

                def svc_pool(v):
                    if v not in _sm:
                        m = ben & (dp_w == v)
                        _sm[v] = ((float(e_te[m].mean()), float((e_te[m] > 0).mean()))
                                  if m.any() else None)
                    return _sm[v]

                POOLS = ["generic", "attacker-origin", "protocol-matched",
                         "service-matched", "black-box"]
                per_real = {p: [] for p in POOLS}
                per_static = {p: [] for p in POOLS}
                for j in det:
                    sel = ep_of_flow == j
                    Sj = float(S[j]); nj = int(n[j]); taur = float(tau_t[j])
                    modal_pr = int(np.bincount(pr_w[sel]).argmax())
                    modal_dp = int(np.bincount(dp_w[sel]).argmax())
                    cand = [(nm, stats[nm]) for nm in stats]
                    cand.append(("protocol-matched", proto_pool(modal_pr)))
                    cand.append(("service-matched", svc_pool(modal_dp)))
                    for nm, st in cand:
                        if st is None:
                            continue
                        mu, pf = st
                        for tau, store in ((taur, per_real), (tau_static, per_static)):
                            if mu >= tau:
                                continue
                            rm = (Sj - tau * nj) / (tau - mu)
                            store[nm].append(int(np.floor(rm)) + 1 if rm > 0 else 1)
                prec = dict(
                    pos=pos, seed=seed, n_det=int(len(det)),
                    real={p: dict(mu=(stats.get(p, (None, None))[0]),
                                  med=(float(np.median(v)) if v else None), n=len(v))
                          for p, v in per_real.items()},
                    static={p: (float(np.median(v)) if v else None) for p, v in per_static.items()})
                pools_by_order[order][f"{pos}_{seed}"] = prec
                if order != "first-flow":
                    continue
                pools_out[f"{pos}_{seed}"] = prec
                if pos == 0.85 and seed == 0:
                    fig4a = {"pos": 0.85, "seed": 0, "n_det": int(len(det)),
                             "pools": {p: sorted(v) for p, v in per_real.items()}}
                if pos == 0.62 and seed == 0:
                    fig4a_guar = {"pos": 0.62, "seed": 0, "n_det": int(len(det)),
                                  "pools": {p: sorted(v) for p, v in per_real.items()}}

    out = dict(
        config=dict(POS=POS_ALL, POS_POOL=POS_POOL, SEEDS=SEEDS, k=K, w0=W0, bucket_s=BUCKET,
                    orders=ORDERS_RUN, canonical_order="keyhash"),
        table1=table1, pools=pools_out, fig4a_pools=fig4a, fig4a_guarantee=fig4a_guar,
        table1_by_order=table1_by_order, pools_by_order=pools_by_order,
        note=("pad costs priced against the running e-LOND poly level 1/alpha_t; "
              "static = T/w0 (R=0 lower bound); feedback ignored, so a lower bound"))
    json.dump(out, open("out/t28b_reallevel.json", "w"), indent=1, allow_nan=True)
    print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t28b_reallevel.json")
    return out


if __name__ == "__main__":
    main()
