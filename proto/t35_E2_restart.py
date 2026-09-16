"""
E2 -- periodic controller restart and batching, on LSPR23.  Section 4.35.

Answers reviewer questions 3 and 4 of 02_WORKPLAN_PHASE4.md section 9: "why not reset the
FDR controller every day?" and "why not batch hypotheses?".

Closed forms are derived and verified in t35a_E2_derivation.py; run that FIRST.  A
disagreement between the two is a bug, not a finding (docs/01_HANDOFF_PHASE4.md section 6).
Tags [D1b], [D2a] etc. refer to its derivation labels.

WHAT RESTART MEANS HERE ------------------------------------------------------------------
At each epoch boundary the controller's wealth, its rejection count and its spending index
`t` are reset; the DETECTOR and the CALIBRATION SET are not.  An episode is assigned to the
epoch containing its FIRST timestamp, which is the online-consistent choice: the controller
meets the episode when it starts.  For a grouping bucket no wider than the epoch this
assignment is exact.

THE SCOPING DECISION, WHICH HAS TO BE MADE EXPLICITLY -------------------------------------
LSPR23 spans 161.5 h but 90% of its flows fall in the final 25.6 h, so a deployment window
that leaves room for training and calibration is SHORT IN TIME however it is placed:

    split at 0.55 (the record's guarantee window)   deployment block spans   8.52 h
    split at 0.55, deploying to the end of stream                           13.29 h
    split at 0.10, deploying to the end of stream                           25.87 h
    split at 0.05, deploying to the end of stream                           26.98 h  (max)

**A 48 h epoch is unmeasurable on this dataset**: no deployment window is that long. A 24 h
epoch is measurable only at an early split, which costs a 3x smaller calibration set. Three
windows are therefore run and reported separately rather than pooled:

    W1  "guarantee"  split 0.55, deployment block  [i2, i3)   8.52 h   |C| = 2,448,993
    W2  "extended"   split 0.55, deployment        [i2, N)   13.29 h   |C| = 2,448,993
    W3  "long-span"  split 0.10, deployment        [i2, N)   25.87 h   |C| ~  813,683

W3 is the only configuration in which a 24 h restart is a restart rather than a no-op, and it
is NOT the guarantee window: its calibration set is a third of the size and its detector sees
a third of the training flows. Every W3 number is labelled.

An epoch that contains the whole window is a no-op and is reported as such rather than as a
restart result.

Runtime ~45 min.  Run from proto/.
"""
import numpy as np, json, time, sys, gc
from pathlib import Path
from sklearn.metrics import roc_auc_score

import h_stream as H
from h6_procs import (Ctx, make_gamma, run_lond, run_lordpp, run_saffron, run_addis,
                      run_online_ebh, online_ebh_kstar)

Path("out").mkdir(exist_ok=True)
SMOKE = "--smoke" in sys.argv
t0 = time.time()

DSEEDS = [0, 1]
BH = 2                               # two-hour grouping, matching sections 4.17/4.19/4.20
K = 1
A, W0 = 0.05, 0.025
SAF_LAM, ADD_LAM, ADD_TAU = 0.5, 0.25, 0.5
EBH_MAX_T = 200_000                  # online e-BH's k* scan is O(T^2); skip above this
HOUR = 3600 * 1_000_000              # microseconds

# Section 4.20, position 0.55 seed 0, two-hour grouping, uninterrupted.  Asserted.
REGRESSION_W1 = {("poly", "LOND"): (18, 18), ("poly", "LORD++"): (19, 19),
                 ("poly", "SAFFRON"): (0, 0), ("poly", "ADDIS"): (110, 109),
                 ("poly", "online e-BH"): (18, 18),
                 ("uniform[ORACLE]", "LOND"): (104, 104),
                 ("uniform[ORACLE]", "LORD++"): (104, 104),
                 ("uniform[ORACLE]", "SAFFRON"): (0, 0),
                 ("uniform[ORACLE]", "ADDIS"): (0, 0),
                 ("uniform[ORACLE]", "online e-BH"): (108, 107)}


# ---------------------------------------------------------------------------------------
def deadline(M, w, ze=2.2857878790884776):
    """Largest t with w*gamma_t >= 1/M for gamma_t = t^-1.6/zeta(1.6); 0 if none. [D2a/D2b]

    Binary search in log space.  A closed-form seed plus a linear repair loop walks over a
    million steps for very large M, and t**-1.6 raises at t = 0."""
    import math
    if M <= 0 or w <= 0:
        return 0
    logb = math.log(w) + math.log(M) - math.log(ze)

    def feasible(t):
        return t >= 1 and logb - 1.6 * math.log(t) >= 0.0

    if not feasible(1):
        return 0
    hi = max(2, int(math.exp(logb / 1.6)) + 2)
    while feasible(hi):
        hi *= 2
    lo = 1
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if feasible(mid):
            lo = mid
        else:
            hi = mid
    return lo


def epoch_index(ts_us, epoch_h):
    """Epoch id from an ABSOLUTE-CLOCK floor, the same grid h_stream.build_episodes uses for
    its time buckets (`ts // (bucket_s * 1e6)`).

    An earlier version floored `(ts - t_start)`, i.e. a grid offset from the bucket grid, so
    an episode could straddle a restart even when the bucket was no wider than the epoch.
    That matters: a straddling episode averages evidence from a LATER epoch into a
    hypothesis tested by the EARLIER epoch's freshly-reset controller, which can inflate
    restart's apparent power.  With both grids absolute and the epoch an integer multiple of
    the bucket, containment is exact -- and it is asserted, not assumed."""
    if epoch_h is None:
        return np.zeros(len(ts_us), dtype=np.int64)
    return (ts_us // int(round(epoch_h * HOUR))).astype(np.int64)


def epoch_ids_and_schedule(fts, lts, epoch_h):
    """(epoch id per episode, number of SCHEDULED epochs, contained?).

    The schedule counts every wall-clock epoch the window spans, INCLUDING empty ones: a
    precommitted alpha allocation cannot know in advance which hours will carry traffic, and
    dividing q over only the non-empty epochs would hand each of them more budget than a
    deployment could."""
    if epoch_h is None:
        return np.zeros(len(fts), dtype=np.int64), 1, True
    e_first = epoch_index(fts, epoch_h)
    e_last = epoch_index(lts, epoch_h)
    contained = bool(np.array_equal(e_first, e_last))
    lo, hi = int(e_first.min()), int(e_last.max())
    return (e_first - lo).astype(np.int64), int(hi - lo + 1), contained


def alpha_allocation(kind, n_epochs, q=A):
    """Per-epoch error target.
    'per-epoch'  every epoch spends the full q -- the naive restart, and the only one that
                 buys feasibility [D4b]; the pooled guarantee is then lost [D5b].
    'uniform'    q/n to each epoch, so the deployment spends q in total.
    'geometric'  a front-loaded precommitted split summing to q."""
    if kind == "per-epoch":
        return np.full(n_epochs, q)
    if kind == "uniform":
        return np.full(n_epochs, q / n_epochs)
    if kind == "geometric":
        w = 0.5 ** np.arange(n_epochs, dtype=float)
        return q * w / w.sum()
    raise ValueError(kind)


def run_procedure(proc, Ev, ismal, CEIL, alpha, w0, gamma_kind):
    """One procedure on one contiguous block, returning (rej, tp, silent, fired)."""
    T = len(Ev)
    if T == 0:
        return 0, 0, 0, np.zeros(0, bool)
    ctx = Ctx(Ev, ismal, CEIL, alpha=alpha, w0=w0)
    g1, g0 = make_gamma("poly" if gamma_kind == "poly" else "uniform", T)
    fired = np.zeros(T, bool)
    if proc == "LOND":
        r = run_lond(ctx, g1, fired=fired)
    elif proc == "LORD++":
        r = run_lordpp(ctx, g1, fired=fired)
    elif proc == "SAFFRON":
        r = run_saffron(ctx, g1, lam=SAF_LAM, fired=fired)
    elif proc == "ADDIS":
        r = run_addis(ctx, g0, lam=ADD_LAM, tau_=ADD_TAU, fired=fired)
    elif proc == "online e-BH":
        ks, m = online_ebh_kstar(Ev, g1, alpha, T)
        mask = np.isfinite(m) & (m <= int(ks[T]))
        chk = run_online_ebh(ctx, g1)
        rej, tp = int(mask.sum()), int((mask & ismal).sum())
        if (chk[0], chk[1]) != (rej, tp):
            raise AssertionError(f"ebh mask != run_online_ebh {(rej,tp)} vs {chk[:2]}")
        return rej, tp, chk[2], mask
    else:
        raise ValueError(proc)
    return r[0], r[1], r[2], fired


def run_restarted(proc, Ev, ismal, CEIL, ep_id, gamma_kind, alloc="per-epoch",
                  n_scheduled=None):
    """Run `proc` independently on each epoch, resetting wealth, rejection count and the
    spending index at every boundary.  Returns the pooled result plus per-epoch detail.

    The alpha allocation is spread over `n_scheduled` wall-clock epochs, not over the
    non-empty ones: an empty hour still consumes its share of a precommitted budget."""
    T = len(Ev)
    uniq = np.unique(ep_id)
    n_ep = len(uniq)
    n_sched = n_ep if n_scheduled is None else max(n_scheduled, n_ep)
    alphas_all = alpha_allocation(alloc, n_sched)
    alphas = alphas_all[np.asarray(uniq, dtype=np.int64)] \
        if alloc != "per-epoch" else np.full(n_ep, A)
    fired = np.zeros(T, bool)
    per = []
    silent_tot = 0
    for j, e in enumerate(uniq):
        sel = np.flatnonzero(ep_id == e)
        a_j = float(alphas[j]); w_j = a_j / 2.0
        rej, tp, sil, f = run_procedure(proc, Ev[sel], ismal[sel], CEIL, a_j, w_j, gamma_kind)
        fired[sel] = f
        silent_tot += sil
        per.append(dict(epoch=int(e), n=len(sel), n_mal=int(ismal[sel].sum()),
                        alpha=a_j, rejections=int(rej), tp=int(tp), silent_count=int(sil),
                        fdp=float((rej - tp) / max(rej, 1)), silent=float(sil / max(len(sel), 1)),
                        margin=float(CEIL * w_j / max(len(sel), 1) - 1.0),
                        deadline=int(deadline(CEIL, a_j if proc != "LORD++" else w_j))))
    rej = int(fired.sum()); tp = int((fired & ismal).sum())
    # The epochs must PARTITION the stream: every episode tested exactly once, and the
    # pooled rejection count equal to the sum of the per-epoch counts.  A mutation that made
    # the per-epoch `fired` writes overlap would otherwise go unnoticed.
    if sum(p["n"] for p in per) != T:
        raise AssertionError(f"epochs do not partition the stream: "
                             f"{sum(p['n'] for p in per)} != {T}")
    if rej != sum(p["rejections"] for p in per):
        raise AssertionError(f"pooled rejections {rej} != sum of per-epoch "
                             f"{sum(p['rejections'] for p in per)}: epoch masks overlap")
    if tp != sum(p["tp"] for p in per):
        raise AssertionError("pooled true positives != sum of per-epoch")
    return dict(alloc=alloc, n_scheduled=n_sched, alpha_total=float(np.sum(alphas_all)),
                rejections=rej, tp=tp, fp=rej - tp,
                fdp=float((rej - tp) / max(rej, 1)),
                fdp_cond=(float((rej - tp) / rej) if rej else None),
                silent=float(silent_tot / max(T, 1)),
                n_epochs=n_ep,
                n_epochs_zero_disc=int(sum(1 for p in per if p["rejections"] == 0)),
                frac_epochs_zero_disc=float(sum(1 for p in per if p["rejections"] == 0) / n_ep),
                per_epoch=per), fired


def coverage(fired, gid_of_flow, order, y_te):
    """Malicious-FLOW coverage: the fraction of malicious flows inside alerted episodes."""
    alerted_groups = order[np.flatnonzero(fired)]
    mask = np.isin(gid_of_flow, alerted_groups)
    nm = int(y_te.sum())
    return float(((y_te == 1) & mask).sum() / nm) if nm else None


# ---------------------------------------------------------------------------------------
X, y, ts, src, dst = H.load()
N = len(y)
rows, per_cfg, failures, notes = [], [], [], []

WINDOWS = [("W1 guarantee", 0.55, "block"), ("W2 extended", 0.55, "toend"),
           ("W3 long-span[WEAK-CAL]", 0.10, "toend")]
EPOCHS_BY_WINDOW = {"W1 guarantee": [None, 1, 2, 4],
                    "W2 extended": [None, 1, 2, 4, 6, 12],
                    "W3 long-span[WEAK-CAL]": [None, 1, 6, 12, 24]}
PROCS = ["LOND", "LORD++", "SAFFRON", "ADDIS", "online e-BH"]
GAMMAS = ["poly", "uniform[ORACLE]"]
if SMOKE:
    DSEEDS = [0]
    EPOCHS_BY_WINDOW = {k: v[:3] for k, v in EPOCHS_BY_WINDOW.items()}
    PROCS = ["LOND", "LORD++"]

for wname, pos, mode in WINDOWS:
    i2 = int(pos * N)
    i1 = i2 - int(0.15 * N) if i2 - int(0.15 * N) > 0 else i2 // 2
    i3 = min(N, i2 + int(0.15 * N)) if mode == "block" else N
    ts_w, y_te = ts[i2:i3], y[i2:i3]
    span_h = float((ts_w.max() - ts_w.min()) / 3.6e9)
    t_start = int(ts_w.min())

    for dseed in DSEEDS:
        tag = f"{wname} seed={dseed}"
        sc = H.fit_detector(X, y, i1, dseed, kind="hgb")
        s_cal, s_te = H.score_windows(sc, X, i1, i2, i3)
        y_cal = y[i1:i2]
        e_te, cal, NC, CEIL = H.evalues(s_cal, y_cal, s_te, k=K)
        auroc = float(roc_auc_score(y_te, s_te))
        ep = H.build_episodes(e_te, y_te, ts_w, src[i2:i3], dst[i2:i3], bucket_s=BH * 3600)
        Ev, ismal, T, order, gid = ep["Ev"], ep["ismal"], ep["T"], ep["order"], ep["gid"]
        NMAL = ep["n_mal"]
        first_ts = np.full(T, np.iinfo(np.int64).max)
        last_ts = np.zeros(T, dtype=np.int64)
        np.minimum.at(first_ts, gid, ts_w)
        np.maximum.at(last_ts, gid, ts_w)
        fts, lts = first_ts[order], last_ts[order]
        margin_unint = CEIL * W0 / T - 1.0
        D_LOND, D_LORD = deadline(CEIL, A), deadline(CEIL, W0)
        pi = NMAL / T

        print(f"  {tag}: span {span_h:.2f} h  T={T:,}  |C|={NC:,}  AUROC={auroc:.4f}  "
              f"margin(w0)={margin_unint:+.3f} margin(LOND,alpha)={CEIL*A/T-1:+.3f}  "
              f"malicious episodes {NMAL}  deadlines LOND {D_LOND} / LORD++ {D_LORD}  "
              f"[{time.time()-t0:.0f}s]")

        for epoch_h in EPOCHS_BY_WINDOW[wname]:
            if epoch_h is not None and epoch_h < BH:
                notes.append(f"{tag}: a {epoch_h}h epoch is NARROWER than the {BH}h grouping "
                             f"bucket, so an episode would straddle a restart -- skipped in "
                             f"E2a. The coherent hourly-restart configuration is 1h grouping "
                             f"x 1h epoch, measured in E2c")
                continue
            ep_id, n_sched, contained = epoch_ids_and_schedule(fts, lts, epoch_h)
            if epoch_h is not None and not contained:
                failures.append(f"{tag}: episodes straddle a {epoch_h}h epoch boundary at "
                                f"{BH}h grouping -- the restart semantics would be wrong")
                continue
            n_ep = len(np.unique(ep_id))
            if epoch_h is not None and n_ep == 1:
                notes.append(f"{tag}: a {epoch_h}h epoch contains the whole {span_h:.2f} h "
                             f"window -- a no-op, not a restart")
                continue
            T_ep_mean = T / n_ep
            for proc in PROCS:
                if proc == "online e-BH" and epoch_h is None and T > EBH_MAX_T:
                    notes.append(f"{tag}: online e-BH skipped uninterrupted at T={T:,} "
                                 f"(its k* scan is O(T^2)); it escapes the horizon anyway (F1)")
                    for gk in GAMMAS:
                        rows.append(dict(window=wname, pos=pos, dseed=dseed, span_h=span_h,
                                         epoch_h=None, n_scheduled=1, alloc="per-epoch",
                                         grouping_h=BH, proc=proc, gamma=gk, T=int(T),
                                         NC=int(NC), NMAL=int(NMAL), auroc=auroc,
                                         skipped=True,
                                         skip_reason=f"T={T} > EBH_MAX_T={EBH_MAX_T}"))
                    continue
                for gk in GAMMAS:
                    res, fired = run_restarted(proc, Ev, ismal, CEIL, ep_id, gk,
                                               n_scheduled=n_sched)
                    det = np.flatnonzero(fired)
                    rows.append(dict(
                        window=wname, pos=pos, dseed=dseed, span_h=span_h, epoch_h=epoch_h,
                        n_scheduled=n_sched, alpha_total=res["alpha_total"],
                        alloc="per-epoch", grouping_h=BH, proc=proc, gamma=gk,
                        T=int(T), NC=int(NC), NMAL=int(NMAL), auroc=auroc,
                        margin_uninterrupted=float(margin_unint),
                        margin_epoch=float(CEIL * W0 / T_ep_mean - 1.0),
                        # the cold-start coefficient is alpha for LOND and w0 for LORD++
                        # [D1]; the record's margin convention is the Family-II (w0) one,
                        # so LOND's own margin is reported separately rather than implied
                        margin_epoch_proc=float(
                            CEIL * (A if proc == "LOND" else W0) / T_ep_mean - 1.0),
                        margin_epoch_worst=float(
                            CEIL * (A if proc == "LOND" else W0)
                            / max(1, max(p["n"] for p in res["per_epoch"])) - 1.0),
                        n_epochs=res["n_epochs"], T_ep_mean=float(T_ep_mean),
                        rejections=res["rejections"], tp=res["tp"], fdp=res["fdp"],
                        fdp_cond=res["fdp_cond"],
                        recall=float(res["tp"] / NMAL) if NMAL else None,
                        flow_coverage=coverage(fired, gid, order, y_te),
                        silent=res["silent"],
                        frac_epochs_zero_disc=res["frac_epochs_zero_disc"],
                        n_epochs_zero_disc=res["n_epochs_zero_disc"],
                        alerts_per_day=float(res["rejections"] / (span_h / 24.0)),
                        first_det_h=(float((fts[det[0]] - t_start) / 3.6e9) if det.size else None),
                        median_det_h=(float(np.median((fts[det] - t_start) / 3.6e9))
                                      if det.size else None),
                        per_epoch_fdp=[p["fdp"] for p in res["per_epoch"]],
                        per_epoch_rej=[p["rejections"] for p in res["per_epoch"]],
                        per_epoch_margin=[p["margin"] for p in res["per_epoch"]],
                        per_epoch_n=[p["n"] for p in res["per_epoch"]],
                        per_epoch_silent=[p["silent_count"] for p in res["per_epoch"]],
                        per_epoch_alpha=[p["alpha"] for p in res["per_epoch"]],
                        epoch_ids=[p["epoch"] for p in res["per_epoch"]],
                    ))

        # ---- regression against section 4.20, uninterrupted, W1 seed 0 -----------------
        if wname == "W1 guarantee" and dseed == 0 and not SMOKE:
            for (gk, proc), (wr, wt) in REGRESSION_W1.items():
                got = [r for r in rows if r["window"] == wname and r["dseed"] == 0
                       and r["epoch_h"] is None and r["proc"] == proc and r["gamma"] == gk]
                if got and (got[0]["rejections"], got[0]["tp"]) != (wr, wt):
                    failures.append(f"REGRESSION 4.20 {gk}/{proc}: got "
                                    f"{(got[0]['rejections'], got[0]['tp'])} want {(wr, wt)}")

        # ================= E2b: alpha-budgeted restarts ==================================
        if wname == "W1 guarantee":
            EB_EPOCH = BH          # the coherent choice: restart epoch = grouping bucket
            ep_id, n_sched_b, contained_b = epoch_ids_and_schedule(fts, lts, EB_EPOCH)
            if not contained_b:
                failures.append(f"{tag}: E2b episodes straddle a {EB_EPOCH}h epoch")
            for alloc in ("per-epoch", "uniform", "geometric"):
                for proc in ("LOND", "LORD++"):
                    for gk in GAMMAS:
                        res, fired = run_restarted(proc, Ev, ismal, CEIL, ep_id, gk, alloc,
                                                   n_scheduled=n_sched_b)
                        det = np.flatnonzero(fired)
                        rows.append(dict(
                            window=wname + " [E2b]", pos=pos, dseed=dseed, span_h=span_h,
                            epoch_h=EB_EPOCH, n_scheduled=n_sched_b,
                            alpha_total=res["alpha_total"], alloc=alloc,
                            grouping_h=BH, proc=proc, gamma=gk,
                            T=int(T), NC=int(NC), NMAL=int(NMAL), auroc=auroc,
                            margin_uninterrupted=float(margin_unint),
                            margin_epoch=float(np.mean([p["margin"] for p in res["per_epoch"]])),
                            n_epochs=res["n_epochs"], T_ep_mean=float(T / res["n_epochs"]),
                            rejections=res["rejections"], tp=res["tp"], fdp=res["fdp"],
                            fdp_cond=res["fdp_cond"],
                            recall=float(res["tp"] / NMAL) if NMAL else None,
                            flow_coverage=coverage(fired, gid, order, y_te),
                            silent=res["silent"],
                            frac_epochs_zero_disc=res["frac_epochs_zero_disc"],
                            n_epochs_zero_disc=res["n_epochs_zero_disc"],
                            alerts_per_day=float(res["rejections"] / (span_h / 24.0)),
                            first_det_h=(float((fts[det[0]] - t_start) / 3.6e9)
                                         if det.size else None),
                            median_det_h=None,
                            per_epoch_fdp=[p["fdp"] for p in res["per_epoch"]],
                            per_epoch_rej=[p["rejections"] for p in res["per_epoch"]],
                            per_epoch_margin=[p["margin"] for p in res["per_epoch"]],
                            per_epoch_n=[p["n"] for p in res["per_epoch"]],
                            per_epoch_silent=[p["silent_count"] for p in res["per_epoch"]],
                            per_epoch_alpha=[p["alpha"] for p in res["per_epoch"]],
                            epoch_ids=[p["epoch"] for p in res["per_epoch"]]))

        # ================= E2c: restart x grouping =======================================
        if wname == "W1 guarantee":
            for gh in (1, 2, 6):
                ep_g = H.build_episodes(e_te, y_te, ts_w, src[i2:i3], dst[i2:i3],
                                        bucket_s=gh * 3600)
                Evg, ismalg, Tg, orderg, gidg = (ep_g["Ev"], ep_g["ismal"], ep_g["T"],
                                                 ep_g["order"], ep_g["gid"])
                NMALg = ep_g["n_mal"]
                ftsg = np.full(Tg, np.iinfo(np.int64).max)
                ltsg = np.zeros(Tg, dtype=np.int64)
                np.minimum.at(ftsg, gidg, ts_w)
                np.maximum.at(ltsg, gidg, ts_w)
                ftsg, ltsg = ftsg[orderg], ltsg[orderg]
                # oracle achievable frontier for this grouping, so that a "beats" comparison
                # can be made at a MATCHED alert budget (standing rule 2, section 4.19)
                smax_g = np.full(Tg, -np.inf)
                np.maximum.at(smax_g, gidg, s_te)
                fr_g = H.frontier(smax_g[orderg], ismalg)
                for eh in (None, 1, 2, 6):
                    if eh is not None and eh < gh:
                        continue                      # would straddle: skip, see E2a note
                    ep_idg, n_sched_g, contained_g = epoch_ids_and_schedule(ftsg, ltsg, eh)
                    if eh is not None and not contained_g:
                        failures.append(f"{tag}: E2c episodes straddle a {eh}h epoch at "
                                        f"{gh}h grouping")
                        continue
                    if eh is not None and len(np.unique(ep_idg)) == 1:
                        continue
                    for proc in ("LOND", "LORD++"):
                        for gk in GAMMAS:
                            res, fired = run_restarted(proc, Evg, ismalg, CEIL, ep_idg, gk,
                                                       n_scheduled=n_sched_g)
                            det = np.flatnonzero(fired)
                            orec, ofdp = H.frontier_at_budget(fr_g, res["rejections"])
                            rows.append(dict(
                                window=wname + " [E2c]", pos=pos, dseed=dseed, span_h=span_h,
                                epoch_h=eh, n_scheduled=n_sched_g,
                                alpha_total=res["alpha_total"],
                                oracle_recall_at_budget=float(orec),
                                oracle_fdp_at_budget=float(ofdp),
                                alloc="per-epoch", grouping_h=gh, proc=proc,
                                gamma=gk, T=int(Tg), NC=int(NC),
                                NMAL=int(NMALg), auroc=auroc,
                                margin_uninterrupted=float(CEIL * W0 / Tg - 1.0),
                                margin_epoch=float(np.mean([p["margin"]
                                                            for p in res["per_epoch"]])),
                                n_epochs=res["n_epochs"],
                                T_ep_mean=float(Tg / res["n_epochs"]),
                                rejections=res["rejections"], tp=res["tp"], fdp=res["fdp"],
                                fdp_cond=res["fdp_cond"],
                                recall=float(res["tp"] / NMALg) if NMALg else None,
                                flow_coverage=coverage(fired, gidg, orderg, y_te),
                                silent=res["silent"],
                                frac_epochs_zero_disc=res["frac_epochs_zero_disc"],
                                n_epochs_zero_disc=res["n_epochs_zero_disc"],
                                alerts_per_day=float(res["rejections"] / (span_h / 24.0)),
                                first_det_h=(float((ftsg[det[0]] - t_start) / 3.6e9)
                                             if det.size else None),
                                median_det_h=None,
                                per_epoch_fdp=[p["fdp"] for p in res["per_epoch"]],
                                per_epoch_rej=[p["rejections"] for p in res["per_epoch"]],
                                per_epoch_margin=[p["margin"] for p in res["per_epoch"]],
                                per_epoch_n=[p["n"] for p in res["per_epoch"]],
                                per_epoch_silent=[p["silent_count"] for p in res["per_epoch"]],
                                per_epoch_alpha=[p["alpha"] for p in res["per_epoch"]],
                            epoch_ids=[p["epoch"] for p in res["per_epoch"]]))
                del ep_g, Evg, ismalg
                gc.collect()

        # ---- per-configuration record ---------------------------------------------------
        # the measured per-episode firing rate phi, which D3b needs
        phi = float((Ev[ismal] >= 1.0).mean()) if NMAL else 0.0
        per_cfg.append(dict(window=wname, dseed=dseed, pos=pos, span_h=span_h, T=int(T),
                            NC=int(NC), CEIL=float(CEIL), NMAL=int(NMAL), auroc=auroc,
                            margin_uninterrupted=float(margin_unint),
                            deadline_LOND=D_LOND, deadline_LORDpp=D_LORD,
                            pi=float(pi), phi_evidence_positive=phi,
                            episodes_per_hour=float(T / span_h),
                            required_C_uninterrupted=float(K * T / W0 - 1.0)))
        del s_cal, s_te, e_te, cal, ep
        gc.collect()

# =======================================================================================
def cold_margin(proc, M, n_ep_size, alpha=A, w0=W0):
    """Cold-start feasibility margin with the PROCEDURE'S OWN coefficient [D1].
    LOND's level at R = 0 is alpha*gamma_t; LORD++'s leading term is gamma_t*w0.  SAFFRON,
    ADDIS and online e-BH index their levels by counts of tested hypotheses, or by a fixed
    point over the whole history, so a single scalar cold-start margin is not defined for
    them and None is reported rather than the Family-II number."""
    if proc == "LOND":
        return M * alpha / n_ep_size - 1.0
    if proc == "LORD++":
        return M * w0 / n_ep_size - 1.0
    return None


def agg(v):
    v = [x for x in v if x is not None]
    return (float(np.mean(v)), float(np.std(v, ddof=1)) if len(v) > 1 else 0.0) if v else (None, None)


print("\n" + "=" * 132)
print("E2a — RESTART, per-epoch full q.  Mean over detector seeds.")
print("=" * 132)
for wname, _, _ in WINDOWS:
    sub = [r for r in rows if r["window"] == wname]
    if not sub: continue
    c = [c for c in per_cfg if c["window"] == wname][0]
    print(f"\n{wname}   span {c['span_h']:.2f} h · T={c['T']:,} · |C|={c['NC']:,} · "
          f"{c['episodes_per_hour']:,.0f} episodes/h · uninterrupted margin "
          f"{c['margin_uninterrupted']:+.3f} · LOND deadline {c['deadline_LOND']}")
    print(f"  {'proc':>12} {'gamma':>17} {'epoch':>7} {'n_ep':>5} {'margin':>9} "
          f"{'rejections':>12} {'FDP':>12} {'recall':>12} {'flow cov':>10} "
          f"{'silent':>8} {'zero-disc epochs':>17}")
    for proc in PROCS:
        for gk in GAMMAS:
            for eh in EPOCHS_BY_WINDOW[wname]:
                rr = [r for r in sub if r["proc"] == proc and r["gamma"] == gk
                      and r["epoch_h"] == eh and not r.get("skipped")]
                if not rr:
                    sk = [r for r in sub if r["proc"] == proc and r["gamma"] == gk
                          and r["epoch_h"] == eh and r.get("skipped")]
                    if sk:
                        print(f"  {proc:>12} {gk:>17} {'none':>7} {'--':>5} {'n/a':>9} "
                              f"{'NOT RUN':>12}   {sk[0]['skip_reason']}")
                    continue
                rj, rjs = agg([r["rejections"] for r in rr])
                fd, _ = agg([r["fdp"] for r in rr])
                rc, _ = agg([r["recall"] for r in rr])
                fc, _ = agg([r["flow_coverage"] for r in rr])
                sl, _ = agg([r["silent"] for r in rr])
                zd, _ = agg([r["frac_epochs_zero_disc"] for r in rr])
                cm = cold_margin(proc, rr[0]["NC"] + 1.0,
                                  rr[0]["T"] / max(rr[0]["n_epochs"], 1))
                mgs = f"{cm:>+9.3f}" if cm is not None else f"{'n/a':>9}"
                print(f"  {proc:>12} {gk:>17} {str(eh)+'h' if eh else 'none':>7} "
                      f"{rr[0]['n_epochs']:>5} {mgs} {rj:>7.1f}±{rjs:<4.1f} "
                      f"{fd:>12.3f} {rc:>12.3f} {(fc if fc is not None else float('nan')):>10.3f} "
                      f"{100*sl:>7.1f}% {100*zd:>16.1f}%")

print("\n" + "=" * 132)
print("E2b — ALPHA-BUDGETED RESTART (1 h epochs, W1).  [D4b] predicts the uniform budget")
print("      reproduces the UNINTERRUPTED margin exactly, i.e. buys no feasibility at all.")
print("=" * 132)
print(f"  {'proc':>12} {'gamma':>17} {'allocation':>12} {'mean margin':>12} {'rejections':>12} "
      f"{'FDP':>10} {'recall':>10} {'zero-disc':>10}")
for proc in ("LOND", "LORD++"):
    for gk in GAMMAS:
        for alloc in ("per-epoch", "uniform", "geometric"):
            rr = [r for r in rows if r["window"].endswith("[E2b]") and r["proc"] == proc
                  and r["gamma"] == gk and r["alloc"] == alloc and not r.get("skipped")]
            if not rr: continue
            rj, _ = agg([r["rejections"] for r in rr]); fd, _ = agg([r["fdp"] for r in rr])
            rc, _ = agg([r["recall"] for r in rr]); mg, _ = agg([r["margin_epoch"] for r in rr])
            zd, _ = agg([r["frac_epochs_zero_disc"] for r in rr])
            print(f"  {proc:>12} {gk:>17} {alloc:>12} {mg:>+12.3f} {rj:>12.1f} {fd:>10.3f} "
                  f"{rc:>10.3f} {100*zd:>9.1f}%")

print("\n" + "=" * 132)
print("E2c — RESTART x GROUPING (W1).  Does restart preserve episode resolution where")
print("      coarsening cannot?  [D1c]: both are the same feasibility lever.")
print("=" * 132)
print("      Comparisons are NOT at a matched alert budget, so 'oracle@budget' gives the")
print("      achievable episode recall at each arm's OWN alert count (section 4.19's")
print("      frontier).  Recall must be read against it, not against another arm's recall.")
print(f"  {'proc':>10} {'gamma':>17} {'grouping':>9} {'epoch':>7} {'T':>8} {'margin':>9} "
      f"{'alerts':>8} {'FDP':>8} {'ep recall':>10} {'oracle@budget':>14} {'flow cov':>10}")
for proc in ("LOND", "LORD++"):
    for gk in GAMMAS:
        for gh in (1, 2, 6):
            for eh in (None, 1, 2):
                rr = [r for r in rows if r["window"].endswith("[E2c]") and r["proc"] == proc
                      and r["gamma"] == gk and r["grouping_h"] == gh and r["epoch_h"] == eh
                      and not r.get("skipped")]
                if not rr: continue
                rj, _ = agg([r["rejections"] for r in rr]); fd, _ = agg([r["fdp"] for r in rr])
                rc, _ = agg([r["recall"] for r in rr])
                fc, _ = agg([r["flow_coverage"] for r in rr])
                orc, _ = agg([r.get("oracle_recall_at_budget") for r in rr])
                cm = cold_margin(proc, rr[0]["NC"] + 1.0,
                                 rr[0]["T"] / max(rr[0]["n_epochs"], 1))
                mgs = f"{cm:>+9.3f}" if cm is not None else f"{'n/a':>9}"
                print(f"  {proc:>10} {gk:>17} {str(gh)+'h':>9} {str(eh)+'h' if eh else 'none':>7} "
                      f"{rr[0]['T']:>8,} {mgs} {rj:>8.1f} {fd:>8.3f} {rc:>10.3f} "
                      f"{(orc if orc is not None else float('nan')):>14.3f} "
                      f"{(fc if fc is not None else float('nan')):>10.3f}")

print("\n" + "=" * 132)
print("DERIVATION AGREEMENT")
print("=" * 132)
dchk = []
ZETA16 = 2.2857878790884776
for c in per_cfg:
    M = c["CEIL"]
    for r in rows:
        if r.get("skipped"): continue
        if r["window"].split(" [")[0] != c["window"] or r["dseed"] != c["dseed"]:
            continue
        if r["proc"] not in ("LOND", "LORD++") or not r.get("per_epoch_n"):
            continue
        # [D2a/D2b] In an epoch with ZERO rejections the level never grows, so the number of
        # structurally silent steps is EXACTLY max(0, T_i - D) with D the closed-form
        # deadline at that epoch's own alpha.  With rejections the horizon extends, so the
        # silent count must be strictly smaller.  This tests the closed form against the
        # procedure's own bookkeeping, which computing the same expression twice would not.
        for n_i, sil_i, rej_i, a_i in zip(r["per_epoch_n"], r["per_epoch_silent"],
                                          r["per_epoch_rej"], r["per_epoch_alpha"]):
            w_i = a_i if r["proc"] == "LOND" else a_i / 2.0
            if r["gamma"] == "poly":
                D_i = deadline(M, w_i, ZETA16)
                want = max(0, n_i - D_i)
            else:
                # [D2c] uniform gamma is a cliff: with no rejections the level is w_i/n_i at
                # every step -- alpha_i for LOND, whose level is alpha*gamma_t*(R+1), and
                # w0_i = alpha_i/2 for LORD++, whose leading term is gamma_t*w0.
                want = n_i if (M * w_i / max(n_i, 1)) < 1.0 else 0
            if rej_i == 0:
                ok = (sil_i == want)
                dchk.append((f"D2 silent count == max(0,T_i-D) with no rejections "
                             f"[{r['gamma']}]", ok, sil_i, want))
                if not ok:
                    failures.append(f"D2 silent mismatch {r['window']} {r['proc']} "
                                    f"{r['gamma']} epoch n={n_i}: got {sil_i} want {want}")
            else:
                ok = (sil_i <= want)
                dchk.append((f"D2 rejections strictly extend the horizon [{r['gamma']}]",
                             ok, sil_i, want))
                if not ok:
                    failures.append(f"D2 silent-with-rejections {r['window']} {r['proc']} "
                                    f"{r['gamma']}: got {sil_i} > bound {want}")

# [D4] EVERY row that claims an allocation must spend what it claims, over the SCHEDULED
# epochs.  An earlier version broke out after the first row and never examined the uniform
# or geometric arms at all, so a bug in either would have gone unnoticed.
for r in rows:
    if not r.get("per_epoch_alpha") or r.get("skipped"):
        continue
    tot_obs = float(np.sum(r["per_epoch_alpha"]))
    n_sched = r.get("n_scheduled", r["n_epochs"])
    if r["alloc"] == "per-epoch":
        want, nm = r["n_epochs"] * A, "per-epoch (q per epoch)"
    elif r["alloc"] == "uniform":
        want, nm = A * r["n_epochs"] / n_sched, "uniform (q/n_scheduled per epoch)"
    else:
        want, nm = None, "geometric"
    if want is not None:
        ok = abs(tot_obs - want) <= 1e-9 * max(1.0, want)
        dchk.append((f"D4 alpha spent by the {nm} allocation", ok, tot_obs, want))
        if not ok:
            failures.append(f"D4 {r['alloc']} at {r['window']} {r['proc']} {r['gamma']}: "
                            f"non-empty epochs hold {tot_obs:.6g}, want {want:.6g}")
    else:
        ok = tot_obs <= A + 1e-9
        dchk.append(("D4 geometric allocation never exceeds q in total", ok, tot_obs, A))
        if not ok:
            failures.append(f"D4 geometric spends {tot_obs} > q at {r['window']}")
    # The SUM alone cannot tell a per-epoch-id lookup from a positional one when an epoch in
    # the middle is empty.  Check the VALUES against the schedule.
    if r["alloc"] != "per-epoch" and r.get("epoch_ids"):
        want_vals = alpha_allocation(r["alloc"], n_sched)[np.asarray(r["epoch_ids"])]
        okv = bool(np.allclose(r["per_epoch_alpha"], want_vals, rtol=0, atol=1e-15))
        dchk.append((f"D4 per-epoch alpha VALUES match the {r['alloc']} schedule position",
                     okv, float(np.sum(r["per_epoch_alpha"])), float(np.sum(want_vals))))
        if not okv:
            failures.append(f"D4 {r['alloc']} values at {r['window']} {r['proc']}: "
                            f"{r['per_epoch_alpha']} vs schedule {list(want_vals)}")

nok = sum(1 for _, o, _, _ in dchk if o)
print(f"  {nok}/{len(dchk)} derivation checks passed")
for nm in sorted(set(n for n, _, _, _ in dchk)):
    sub = [d for d in dchk if d[0] == nm]
    print(f"    {nm:<48} {sum(1 for d in sub if d[1])}/{len(sub)}")

if notes:
    print("\n" + "=" * 132)
    print("SCOPE NOTES (epochs that are no-ops, and what is unmeasurable on this dataset)")
    print("=" * 132)
    for n in sorted(set(notes)):
        print("  " + n)
    print("  48 h epochs are unmeasurable on LSPR23: the longest deployment window that")
    print("  leaves room for training and calibration spans 26.98 h.")

print("\n" + "=" * 132)
if failures:
    print("FAILURES:")
    for f in failures: print("  " + f)
else:
    print("all regression and derivation checks passed")
print("=" * 132)

json.dump(dict(config=dict(DSEEDS=DSEEDS, bucket_h=BH, k=K, alpha=A, w0=W0,
                           windows=[w[0] for w in WINDOWS],
                           epochs_by_window={k: [str(x) for x in v]
                                             for k, v in EPOCHS_BY_WINDOW.items()},
                           smoke=SMOKE),
               rows=rows, per_cfg=per_cfg, notes=sorted(set(notes)), failures=failures),
          open("out/t35_E2_restart.json", "w"), indent=1, allow_nan=True)
print(f"  [{time.time()-t0:.0f}s]  wrote out/t35_E2_restart.json")
if failures:
    raise SystemExit(1)
