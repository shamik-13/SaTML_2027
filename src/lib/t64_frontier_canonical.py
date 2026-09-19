import numpy as np


ORDERS = ("first-flow", "keyhash", "keyed")
FEEDBACK = [(0, "feedback controller (L=0)"), (20, "feedback controller (L=20 alerts)"),
            (50, "feedback controller (L=50 alerts)"), (None, "fixed threshold (no feedback)")]


def elond_mean_rule(Ev, CEIL, alpha=0.05, gamma_exp=1.6):
    """e-LOND at k=1 on the group mean-e rule: alpha_t = alpha * gamma_t * (R_{t-1}+1)."""
    from scipy.special import zeta
    T = len(Ev)
    gam = np.arange(1, T + 1, dtype=float) ** -gamma_exp / float(zeta(gamma_exp, 1))
    fired = np.zeros(T, bool); R = 0
    for t in range(1, T + 1):
        lvl = alpha * gam[t - 1] * (R + 1)
        if lvl > 0 and CEIL >= 1.0 / lvl and Ev[t - 1] >= 1.0 / lvl:
            fired[t - 1] = True; R += 1
    return fired


def feedback_controller(smax, ismal, cal, NC, L, q=0.05, eta=0.02, u0=0.999, win=200):
    """t20's threshold controller: move the calibration quantile on realised FDP, L alerts late."""
    u = u0; T = len(smax); f = np.zeros(T, bool); pend = []; hist = []; na = 0
    for i in range(T):
        arr = 0
        if L is not None:
            while pend and pend[0][0] <= na - L:
                hist.append(pend.pop(0)[1]); arr += 1
        if arr and len(hist) >= 10:
            u = float(np.clip(u + eta * (np.mean(hist[-win:]) - q), 0.5, 1.0))
        if smax[i] > cal[int(np.clip(u * (NC - 1), 0, NC - 1))]:
            f[i] = True; na += 1
            if L is not None:
                pend.append((na, 0.0 if ismal[i] else 1.0))
    return f


def slot_rule(fire_ct, nsz, ismal, CEIL, thr):
    """Policy D: a randomised per-slot rule; its alert count is an expectation, not a count."""
    pD = (1.0 if CEIL >= thr else 0.0) * fire_ct / np.maximum(nsz, 1)
    tot = float(pD.sum())
    return dict(method="online FDR (policy D, slot)", alerts=tot,
                fdp=(float(pD[~ismal].sum() / tot) if tot else None),
                recall=float(pD[ismal].sum() / int(ismal.sum())),
                note="randomised rule; alerts and FDP are E[R] and E[V]/E[R], not E[V/R]")


def _methods_for_order(ep, smax_g, fire_ct_g, cal, NC, CEIL, thr, hs):
    ismal, Ev, nsz = ep["ismal"], ep["Ev"], ep["nsz"]
    NM = int(ismal.sum())
    out = []

    def add(nm, fired, note=""):
        R = int(fired.sum()); V = int((fired & ~ismal).sum())
        out.append(dict(method=nm, alerts=R, fdp=(float(V / R) if R else None),
                        recall=float((fired & ismal).sum() / NM), note=note))

    elond = elond_mean_rule(Ev, CEIL)
    add("online FDR (e-LOND, mean rule)", elond, "self-selected budget")
    out.append(slot_rule(fire_ct_g, nsz, ismal, CEIL, thr))
    for L, nm in FEEDBACK:
        add(nm, feedback_controller(smax_g, ismal, cal, NC, L))

    fr = hs.frontier(smax_g, ismal)
    for m in out:
        r, _ = hs.frontier_at_budget(fr, m["alerts"])
        m["frontier_recall_at_budget"] = r
        m["gap"] = r - m["recall"]
    fr_rows = []
    for q in (0.00, 0.01, 0.05, 0.10, 0.20):
        r, f_, k_ = hs.frontier_at_fdp(fr, q)
        if r is None:
            continue
        fr_rows.append(dict(q=q, recall=r, fdp=f_, alerts=k_))
    return out, fr_rows, int(elond.sum()), int((elond & ismal).sum())


def _run_position(POS, X, y, ts, src, dst, hs, bucket_s=7200, seed=0, k=1, w0=0.025):
    import time
    from sklearn.metrics import roc_auc_score
    t0 = time.time()
    N = len(y)
    i1, i2, i3 = hs.split_indices(N, POS)
    score = hs.fit_detector(X, y, i1, seed=seed, kind="hgb", verbose=False)
    s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
    y_cal, y_te = y[i1:i2], y[i2:i3]
    e_te, cal, NC, CEIL = hs.evalues(s_cal, y_cal, s_te, k=k)
    ts_w, src_w, dst_w = ts[i2:i3], src[i2:i3], dst[i2:i3]
    auroc = float(roc_auc_score(y_te, s_te))

    per_order = {}
    tie_note = None
    for order in ORDERS:
        ep = hs.build_episodes(e_te, y_te, ts_w, src_w, dst_w, bucket_s=bucket_s, order=order)
        T, gid, o = ep["T"], ep["gid"], ep["order"]
        smax = np.full(T, -np.inf); np.maximum.at(smax, gid, s_te)
        fire_ct = np.bincount(gid, weights=(e_te > 0).astype(float), minlength=T)
        thr = T / w0
        meth, fr_rows, n_rej, n_tp = _methods_for_order(
            ep, smax[o], fire_ct[o], cal, NC, CEIL, thr, hs)
        per_order[order] = dict(methods=meth, frontier=fr_rows, T=int(T),
                                NM=ep["n_mal"], elond_rej=n_rej, elond_tp=n_tp,
                                elond_recall=float(n_tp / ep["n_mal"]))
        if order == "first-flow":
            # (2) the two tie-break conventions, measured rather than assumed
            first_ts = np.full(T, np.iinfo(np.int64).max); np.minimum.at(first_ts, gid, ts_w)
            o_t20 = np.argsort(first_ts, kind="mergesort")
            n_tied = int(T - len(np.unique(first_ts)))
            per_order[order]["t20_tiebreak_identical"] = bool(np.array_equal(o, o_t20))
            per_order[order]["n_episodes_sharing_a_first_timestamp"] = n_tied
            tie_note = (n_tied, bool(np.array_equal(o, o_t20)))

    # (1) is the frontier order-invariant?
    base = per_order["first-flow"]["frontier"]
    inv = all(all(abs(a["recall"] - b["recall"]) < 1e-12 and a["alerts"] == b["alerts"]
                  for a, b in zip(base, per_order[od]["frontier"]))
              for od in ORDERS)
    print(f"  pos={POS}  AUROC={auroc:.4f}  |C|={NC:,}  T={per_order['first-flow']['T']:,}  "
          f"malicious={per_order['first-flow']['NM']}   [{time.time()-t0:.0f}s]")
    print(f"    frontier order-invariant: {inv}   "
          f"({tie_note[0]:,} episodes share a first timestamp; "
          f"first-flow == t20 tie-break: {tie_note[1]})")
    for od in ORDERS:
        p = per_order[od]
        print(f"    {od:<11} e-LOND {p['elond_rej']:>4} alerts  recall {p['elond_recall']:.3f}")
    return dict(pos=POS, auroc=auroc, NC=int(NC), CEIL=float(CEIL),
                frontier_order_invariant=bool(inv), per_order=per_order)


def main():
    import json, time, pathlib
    import h_stream as hs
    pathlib.Path("out").mkdir(exist_ok=True)
    t0 = time.time()
    X, y, ts, src, dst = hs.load()
    per_pos = {}
    for POS in (0.55, 0.85):
        per_pos[f"{POS}"] = _run_position(POS, X, y, ts, src, dst, hs)

    # ---- regression against t20, whose numbers the paper currently prints --------------------
    reg = {}
    old = pathlib.Path("out/t20_T8.json")
    if old.exists():
        prev = json.load(open(old))
        for pk, blk in prev.get("per_pos", {}).items():
            if pk not in per_pos:
                continue
            mine = per_pos[pk]["per_order"]["first-flow"]["methods"]
            diffs = []
            for a, b in zip(blk["methods"], mine):
                assert a["method"] == b["method"], f"method order changed at {pk}"
                if a["alerts"] != b["alerts"] or abs(a["recall"] - b["recall"]) > 1e-12:
                    diffs.append(dict(method=a["method"], t20_alerts=a["alerts"],
                                      here_alerts=b["alerts"], t20_recall=a["recall"],
                                      here_recall=b["recall"]))
            reg[pk] = dict(n_methods=len(blk["methods"]), n_differing=len(diffs), diffs=diffs)
            print(f"  regression vs t20 at {pk} (first-flow): "
                  f"{len(blk['methods']) - len(diffs)}/{len(blk['methods'])} identical")

    def cell(pk, od, name):
        for m in per_pos[pk]["per_order"][od]["methods"]:
            if m["method"] == name:
                return m
        raise KeyError(name)

    summary = dict(
        n_positions=len(per_pos), orders=list(ORDERS),
        frontier_order_invariant_everywhere=all(v["frontier_order_invariant"]
                                                for v in per_pos.values()),
        max_gap_any_order=max(m["gap"] for v in per_pos.values()
                              for od in ORDERS for m in v["per_order"][od]["methods"]),
        elond_alerts_first_flow_055=cell("0.55", "first-flow",
                                         "online FDR (e-LOND, mean rule)")["alerts"],
        elond_alerts_canonical_055=cell("0.55", "keyhash",
                                        "online FDR (e-LOND, mean rule)")["alerts"],
        elond_recall_first_flow_055=cell("0.55", "first-flow",
                                         "online FDR (e-LOND, mean rule)")["recall"],
        elond_recall_canonical_055=cell("0.55", "keyhash",
                                        "online FDR (e-LOND, mean rule)")["recall"],
        elond_alerts_canonical_085=cell("0.85", "keyhash",
                                        "online FDR (e-LOND, mean rule)")["alerts"],
        elond_recall_canonical_085=cell("0.85", "keyhash",
                                        "online FDR (e-LOND, mean rule)")["recall"],
        regression_vs_t20=reg,
    )
    for pk in per_pos:
        for od in ORDERS:
            blk = per_pos[pk]["per_order"][od]
            z = [f for f in blk["frontier"] if f["q"] == 0.0]
            m = cell(pk, od, "online FDR (e-LOND, mean rule)")
            blk["zero_error_frontier"] = z[0] if z else None
            blk["recall_ratio_vs_zero_error_frontier"] = (
                float(z[0]["recall"] / m["recall"]) if z and m["recall"] > 0 else None)
    summary["recall_ratio_first_flow_055"] = \
        per_pos["0.55"]["per_order"]["first-flow"]["recall_ratio_vs_zero_error_frontier"]
    summary["recall_ratio_canonical_055"] = \
        per_pos["0.55"]["per_order"]["keyhash"]["recall_ratio_vs_zero_error_frontier"]

    out = dict(config=dict(positions=[0.55, 0.85], orders=list(ORDERS), seed=0, k=1,
                           w0=0.025, alpha=0.05, q=0.05, bucket_s=7200,
                           note="t20's method set, recomputed under every audited within-bucket "
                                "order; the frontier is an ex-post oracle (thresholds use labels)"),
               per_pos=per_pos, summary=summary)
    json.dump(out, open("out/t64_frontier_canonical.json", "w"), indent=1, allow_nan=False)
    print(f"\n  0.55  e-LOND first-flow {summary['elond_alerts_first_flow_055']} alerts "
          f"(recall {summary['elond_recall_first_flow_055']:.3f})  ->  canonical "
          f"{summary['elond_alerts_canonical_055']} alerts "
          f"(recall {summary['elond_recall_canonical_055']:.3f})")
    print(f"  the zero-error frontier is {summary['recall_ratio_first_flow_055']:.1f}x the "
          f"controller's recall under first-flow, {summary['recall_ratio_canonical_055']:.1f}x "
          f"under the canonical order")
    print(f"  [{time.time()-t0:.0f}s]  wrote out/t64_frontier_canonical.json")
    return out


if __name__ == "__main__":
    main()
