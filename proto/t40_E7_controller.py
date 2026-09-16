"""
E7 -- a second feedback controller, and disposition delay in real time.  Section 4.39.

Answers reviewer questions 11 and 12 of 02_WORKPLAN_PHASE4.md section 9: "does the result
depend on one feedback controller?" and "does realistic feedback delay change it?".

WHAT SECTION 4.14 ALREADY ESTABLISHES ----------------------------------------------------
One proportional controller on the episode max-score threshold, updating an exact calibration
order statistic `u <- u + eta*(FDP_hat - q)` only when a disposition arrives, with latency
measured in ALERTS.  It holds the target to roughly 50 alerts of latency and collapses beyond
it (FDP 0.057 at L=0, 0.378 at L=200, 0.656 with no feedback).  RQ4's conclusion rests on it.

E7a adds ONE alternative controller.  The work plan says: do not invent a control algorithm.
Two textbook ones are run, both standard:
  * PI      u <- u + eta_P*(FDP_hat - q) + eta_I*sum(FDP_hat - q)     (proportional-integral)
  * AQT     direct adaptive quantile targeting: move u by a fixed step in units of the
            calibration order statistic, up on a false discovery and down on a true one, with
            step sizes in the Robbins-Monro ratio q : (1-q) so the stationary point is the
            q-quantile of the disposition process.
E7b replaces alert-counted latency with WALL-CLOCK disposition delay.

THE SCOPING DECISION, MADE EXPLICITLY ----------------------------------------------------
The work plan offers (a) run E7b on the full 161.5 h stream with a coarser alerting unit, or
(b) report only the short delays and say why the rest are unmeasurable.  **Neither is
available as stated, and E2's scoping analysis (section 4.35) says why**: LSPR23 spans 161.5 h
but 90% of its flows fall in the final 25.6 h, so a deployment window that leaves room for
training and calibration spans at most 26.98 h however it is placed.  There is no "full
161.5 h stream" to deploy on.  The decision taken here is therefore:

  * delays of 15 min, 1 h, 4 h and 8 h are measured at the GUARANTEE window (position 0.55,
    8.52 h) -- 8 h is a third of that window and is reported as marginal;
  * a 24 h delay is measured only on E2's LONG-SPAN window (split 0.10, 25.87 h), which has a
    3x smaller calibration set and is labelled [WEAK-CAL];
  * a 72 h delay is UNMEASURABLE on LSPR23 and is reported as such, not silently omitted.

Runtime ~4 min.  Run from proto/.
"""
import numpy as np, json, time, sys, gc
from pathlib import Path
from sklearn.metrics import roc_auc_score

import h_stream as H

Path("out").mkdir(exist_ok=True)
SMOKE = "--smoke" in sys.argv
t0 = time.time()

BH = 2
Q = 0.05
DSEEDS = [0, 1]
HOUR = 3600 * 1_000_000
# wall-clock disposition delays, in hours
DELAYS_H = [0.0, 0.25, 1.0, 4.0, 8.0]
DELAYS_H_LONG = [0.0, 1.0, 6.0, 24.0]
UNMEASURABLE = [72.0]
if SMOKE:
    DSEEDS = [0]


def run_controller(kind, smax, ismal, first_ts, cal, delay_us, q=Q,
                   eta_p=0.02, eta_i=0.002, u0=0.999, window=200, step=None):
    """Threshold controller on the episode max score, with WALL-CLOCK disposition delay.

    The threshold is an exact calibration order statistic `cal[floor(u*(NC-1))]`; section 4.14
    established that a quantile grid quantises the controller into a fixed operating point
    regardless of gain, so the grid is the order statistics themselves.

    A disposition for an alert raised at time t becomes available at t + delay, and the
    controller updates only when one actually arrives -- so at a long delay most alerts are
    issued open-loop, which is the point of the experiment.

    kind='P'   u <- u + eta_p*(FDP_hat - q)                     the section 4.14 rule
    kind='PI'  u <- u + eta_p*(FDP_hat - q) + eta_i*integral    textbook proportional-integral
    kind='AQT' Robbins-Monro adaptive quantile targeting: on each arriving disposition move u
               by +step*(1-q) if the alert was false and -step*q if it was true, whose
               stationary point is the q-quantile of the disposition process.
    """
    NC = len(cal)
    T = len(smax)
    u = float(u0)
    integral = 0.0
    # AQT's Robbins-Monro step.  It must be commensurate with the proportional gain, not with
    # one order statistic: at |C| ~ 2.4e6 a single-order-statistic step moves u by 4e-7 per
    # disposition, so over a whole window the threshold never moves at all and the "controller"
    # is just its own initial condition.
    step = eta_p if step is None else float(step)
    fired = np.zeros(T, bool)
    n_updates = 0
    n_clamped = 0
    first_update_t = None
    pending = []                          # (ready_time, was_false) in arrival order
    ptr = 0
    hist = []                             # dispositions already returned, most recent last
    u_trace = np.empty(T)
    for t in range(T):
        now = first_ts[t]
        # collect every disposition that has become available by now
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
                    # anti-windup: stop accumulating while the actuator is saturated, or the
                    # integral grows without bound and the controller becomes a constant
                    if 0.0 < u < 1.0 or err * (0.5 - u) > 0:
                        integral += err
                    u = u + eta_p * err + eta_i * integral
                else:
                    raise ValueError(kind)
        # Clamping to 1 - 1e-12 made floor(u*(NC-1)) top out one order statistic BELOW the
        # maximum, so the strictest threshold the controller could ever set was more liberal
        # than the strictest valid one.  Clamp u to [0, 1] and the index to [0, NC-1].
        if u >= 1.0 or u <= 0.0:
            n_clamped += 1
        u = float(np.clip(u, 0.0, 1.0))
        u_trace[t] = u
        thr = cal[int(np.clip(np.floor(u * (NC - 1)), 0, NC - 1))]
        if smax[t] > thr:
            fired[t] = True
            pending.append((now + delay_us, not bool(ismal[t])))
    rej = int(fired.sum()); tp = int((fired & ismal).sum())
    # burn-in: alerts issued before ANY disposition had come back and could steer a decision.
    # Counting by timestamp missed the case where every alert is issued and the run ends
    # before the first disposition returns, which at zero delay left burn-in at 0.
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


# ---------------------------------------------------------------------------------------
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
                # Tuning sweep, exactly as section 4.14 does for the proportional rule, and
                # labelled the same way: the gain is selected ON THE EVALUATION STREAM, so
                # each row is a BEST CASE for its controller family rather than a deployable
                # pre-committed setting.  Selecting the best cell for every controller at
                # every delay keeps the comparison between them fair.
                # AQT's knob is its step, not the averaging window (which it does not use),
                # so it gets its own grid; an eta-sized step is enormous in order-statistic
                # units and saturates the actuator immediately.
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
            # no-feedback reference at this window
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

# =======================================================================================
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
