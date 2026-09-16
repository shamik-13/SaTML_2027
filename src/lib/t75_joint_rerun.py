"""Joint attacked-trajectory rerun: does the attack survive when the controller is re-run under it?

WHY THIS EXISTS.  Every suppression number the paper reports is PER-ALERT: each detected episode is
padded on its own and judged against the controller level it received on the UNPERTURBED trajectory
(t48, t74).  The paper says so, and a reviewer read the abstract's "suppresses all 212" as one
simultaneous end-to-end attack run anyway, then named a joint rerun as "the single highest-value
additional experiment".  This is that experiment: pad, then RE-RUN e-LOND over the whole padded
stream, so the controller's own state (its rejection count R, hence every later level) responds to
the attack.

WHAT CHANGES UNDER A JOINT RERUN, AND WHAT CANNOT.  e-LOND offers alpha_t = alpha * gamma_t * (R_{t-1}+1).
Suppressing an earlier alert lowers R_{t-1} for every later step, so every later level is LOWER and
every later threshold 1/alpha_t HIGHER.  Two consequences, both measured here rather than argued:
  * a pad sized on the unperturbed level still suppresses on the attacked trajectory (the threshold
    only rose), so the per-alert set is jointly suppressible and Table I's per-alert TOTAL is an
    upper bound on the joint cost -- the paper states this as a caption remark; the run checks it;
  * an attacker who pads SEQUENTIALLY, sizing each pad against the level the attacked trajectory
    actually offers, pays LESS than the per-alert sum.  The gap is the price of ignoring controller
    state, and it is what a "joint minimum" means here.

THE STREAM PERMUTATION IS CHECKED, NOT ASSUMED.  Every attacker below is applied to the ordered episode
vector (evidence overwritten in place), which is only legitimate if appending the pads to the FLOW
stream and regrouping reproduces the same episode order with the same evidence.  Under the canonical
order that is a theorem (the order hashes the group's OWN (src, dst, bucket) key, which an append does
not change, and arity enters nowhere); under first-flow it holds only if every pad arrives after its
target's first flow, so that the (first_ts, first_pos) pair of every group keeps its RELATIVE order
(absolute positions of later rows shift; the sort compares them, not their values).  So for the STATIC and ADAPTIVE pads, and for the integer state-free multiplier,
`check_padded_stream` constructs the padded flow stream as the pipeline would receive it online: one
row per pad flow, carrying the target's (src, dst) -- by definition of the attack the pad IS traffic
from the attacker's host to the victim -- the timestamp of the target's LAST flow (any instant after
the attacker's own first flow and inside the bucket would do; this one is convenient), label 0 and
zero evidence (the pool is asserted firing-free, so this is the evidence a pool flow carries); the
whole stream is then re-sorted by time with a STABLE sort, so every pad sits after every original
flow of its target and the stream stays chronological.  It then calls
h_stream.build_episodes on that stream under the SAME order and asserts (i) the episode count is
unchanged, (ii) the (src, dst, bucket) key at every stream position is unchanged, (iii) the arities
are m + r, (iv) no label changed and (v) the evidence vector equals the one the attacker was run on.
It is run on the STATIC pads (the largest vector), the ADAPTIVE pads and the integer multiplier; the
capped and other multiplier vectors are sub- or super-sets of those with the same keys, and the
invariance is a property of the keys, not of the pad sizes.  A failed check is a bug in this file,
not a result.

THREE ATTACKERS, kept apart because they know different things:
  STATIC   oracle per-alert pads r*_j = floor(S_j/tau_j) - m_j + 1 from the unperturbed trajectory,
           applied to every true detection at once, then the controller is re-run.  The pad evidence is
           drawn from the black-box pool's e-values (N_DRAWS draws, as t74), but because that pool
           contains no firing flow -- measured on the shipped detector by t48/t74 and asserted again
           here -- every draw is zero and the arm is a ZERO-EVIDENCE rerun; the draws are kept only so
           that a pool that did fire would be exercised rather than assumed away.  The end-to-end
           real-flow replay (pool flows through the detector) is t48/t74's, not this file's.
           Question: does the per-alert set stay suppressed when the controller re-runs?
  ADAPTIVE oracle attacker that walks the stream, and at each of its own episodes that WOULD be
           rejected at the live (attacked-trajectory) level pads it minimally.  Question: what is the
           joint minimum, and how far below Table I's total is it?
  STATE-FREE multiplier c on EVERY malicious episode (the attacker does not know which of its
           episodes will alert, so it pads all of them), c in MULTIPLIERS.  Question: how many true
           detections survive a joint rerun, against the per-alert prediction from t66's rule
           c >= 1 + r*/m?
For every attacker the run also records what happens to the FALSE discoveries, which the attacker
does not touch: with lower levels they can only disappear, and the queue that remains is the
defender's view of the attacked stream.

TWO FURTHER MEASUREMENTS the joint setting makes possible and the per-alert one cannot:
  CAPPED ADAPTIVE  Sec. V-D prices the per-host-pair volume cap on the PER-ALERT pads: an alert is
           "suppressible under the cap" iff m + r* <= n.  Jointly the question is sharper, because an
           alert the attacker cannot hide under the cap FIRES, raises R, and makes every later pad
           dearer.  So the adaptive attacker is re-run under each cap in CAPS: it pads an episode only
           if the padded arity stays within the cap, and otherwise lets it fire.  Reported per cap:
           true detections that survive, the share of benign episodes above the cap (t74's price; nothing is truncated), and a
           MEASURED cascade account: each surviving alert is classified as STRUCTURAL (its pad would
           not fit under the cap even at the cold-start level, R = 0) or a CASCADE VICTIM (it would
           have fitted at R = 0 and fires only because earlier alerts had already raised R).  The
           caps are the sampled grid; nothing is claimed between grid points.
  CRITICAL MULTIPLIER  With R = 0 throughout, e-LOND's cold-start threshold at step t is
           1/(alpha*gamma_t), rejection is INCLUSIVE (Ev >= 1/alpha_t), and the largest evidence any
           episode can carry is CEIL.  Treat the multiplier c as a real number (evidence Ev/c, the
           continuous relaxation of appending (c-1)*m flows).  Then c_crit = max_j Ev_j*alpha*gamma_{t_j}
           is the BOUNDARY: in exact arithmetic every c > c_crit silences every malicious episode from
           cold start and every c <= c_crit leaves the maximising episode rejected (at c = c_crit it
           sits exactly on the inclusive threshold).  Under the horizon-uniform allocation
           c_crit <= CEIL*alpha/T = rho, the paper's feasibility ratio (eq. rho), with equality iff
           some malicious episode attains the ceiling: the feasibility margin the defender buys by
           grouping is the dilution factor that erases it.
           What is ASSERTED, and on what: c_crit*(1 + 1e-3) silences everything and c_crit*(1 - 1e-3)
           leaves >= 1 alert (relaxation, evidence overwritten); the REALISABLE attack is the integer
           multiplier c_int = floor(c_crit) + 1, i.e. (c_int - 1)*m appended flows per episode, which
           is asserted to silence everything AND is checked at the flow-stream level, while c_int - 1
           (when it still pads, i.e. >= 2) is asserted to leave >= 1 alert.  The silence assertions
           hold while no false discovery survives to raise R, recorded as `exact`.  c = c_crit itself is
           rerun and RECORDED as a numerical-boundary observation: floating-point division may land on
           either side of >=, so no claim rests on it.

CONTROL.  The unperturbed canonical arms must reproduce t73's shipped cells exactly (0.55: 3 true
detections at r* = 23, 24, 33, total 80, 0 FD; horizon-aware 105 / total 627,495 / 0 FD; 0.62: 11 /
median 6 / total 926 / 0 FD; horizon-aware 107 / total 977,567 / 1 FD).  Without that the rerun
compares against the wrong baseline, so it is asserted.  The black-box pool must contain NO flow that
reaches the conformal tail (t74 found none at either window over the full pool); this is asserted
because the STATIC subset check below is a theorem only for evidence-non-increasing pads.  The
rejection set of every attacked run must then be a SUBSET of the unperturbed rejection set; a
violation would be a harness bug and stops the run.

    LSPR_DIR=... python t75_joint_rerun.py
"""
import json
import time
from pathlib import Path

import numpy as np

import h_stream as hs
from h6_procs import Ctx, make_gamma, run_lond

A = 0.05; W0 = 0.025; K = 1; BUCKET = 2 * 3600
POS = [0.55, 0.62]
SEED = 0
ORDERS = ["keyhash", "first-flow"]          # canonical carries the result; first-flow is a sensitivity
GAMMAS = ["poly", "uniform"]
MULTIPLIERS = [2, 3, 5, 10, 100]            # t66's state-free multipliers
N_DRAWS = 200                               # real-flow draws for the STATIC attacker, as t74
CAPS = [30, 100, 300, 1000, 3000, 10000]    # t74's per-host-pair volume caps

# t73's shipped canonical cells: (true detections, false discoveries, total per-alert pad).
CONTROL = {("0.55", "poly"): (3, 0, 80), ("0.55", "uniform"): (105, 0, 627495),
           ("0.62", "poly"): (11, 0, 926), ("0.62", "uniform"): (107, 1, 977567)}


def zero_pad(S, n, tau):
    """Minimum zero-evidence additions r with S/(n+r) < tau.  t28b/t73's definition, verbatim."""
    x = S / tau - n
    return int(np.floor(x)) + 1 if x >= 0 else 0


def trajectory(Ev, ismal, CEIL, g1):
    """Run e-LOND and return (fired, tau_t) with tau_t = 1/alpha_t on THIS stream's own trajectory.

    Identical to t73.elond_levels, but takes the (possibly padded) evidence vector directly so the
    attacked stream is run by the very same procedure code as the unperturbed one.
    """
    T = len(Ev)
    ctx = Ctx(Ev, ismal, CEIL, alpha=A, w0=W0)
    fired = np.zeros(T, dtype=bool)
    run_lond(ctx, g1, fired=fired)
    R_before = np.concatenate([[0], np.cumsum(fired)[:-1]]).astype(float)
    alpha_t = A * g1[np.arange(1, T + 1)] * (R_before + 1.0)
    with np.errstate(divide="ignore"):
        tau_t = np.where(alpha_t > 0, 1.0 / alpha_t, np.inf)
    return fired, tau_t


def adaptive_attack(S, m, ismal, CEIL, g1, cap=None, diag=None):
    """Walk the stream as e-LOND does; pad each of the attacker's episodes that would be rejected at
    the LIVE level by the minimum that prevents it.  Benign rejections are left alone and advance R.

    With `cap`, the attacker pads only if the padded arity m + r stays within the cap; an episode it
    cannot hide under the cap fires and advances R like any other rejection.

    With `diag` (a dict), the capped run also records, for every MALICIOUS episode that fires because
    its pad would not fit under the cap: the rejection count R at that moment, and whether the pad it
    would have needed at R = 0 (the cold-start level) WOULD have fit.  An alert that fits at R = 0 but
    not at the live R is a cascade victim: it fires only because an earlier alert fired.

    This is run_lond's loop with one insertion -- the pad -- so that the level algebra cannot drift
    from h6_procs.  Returns (pads per stream position, fired mask of the attacked run).
    """
    T = len(S)
    pads = np.zeros(T, dtype=np.int64)
    fired = np.zeros(T, dtype=bool)
    if diag is not None:
        diag["R_at_fire"] = np.full(T, -1, dtype=np.int64)
        diag["fits_at_R0"] = np.zeros(T, dtype=bool)
        diag["r_needed"] = np.zeros(T, dtype=np.int64)
    R = 0
    for t in range(1, T + 1):
        lvl = A * g1[t] * (R + 1)
        if lvl <= 0 or CEIL < 1.0 / lvl:              # Ctx.infeasible, inlined
            continue
        tau = 1.0 / lvl
        Sj, mj = float(S[t - 1]), int(m[t - 1])
        if Sj / mj >= tau:
            r = zero_pad(Sj, mj, tau) if ismal[t - 1] else None
            if r is not None and (cap is None or mj + r <= cap):
                pads[t - 1] = r
                assert Sj / (mj + r) < tau, "adaptive pad did not suppress"
            else:
                fired[t - 1] = True
                if diag is not None and r is not None:
                    diag["R_at_fire"][t - 1] = R
                    diag["r_needed"][t - 1] = r
                    r0 = zero_pad(Sj, mj, 1.0 / (A * g1[t]))       # the pad at R = 0
                    diag["fits_at_R0"][t - 1] = bool(mj + r0 <= cap)
                R += 1
    return pads, fired


def check_padded_stream(flows, ep, pads, Ev_expect, order):
    """Append the pads as FLOWS, regroup with h_stream.build_episodes under the same order, and assert
    the stream is the same permutation carrying the expected evidence.  `pads` is per stream position.

    Each pad flow carries its target's (src, dst) and the timestamp of the target's LAST flow (same
    bucket by construction).  The padded stream is re-sorted by time with a stable sort, so a pad sits
    after every original flow carrying the same timestamp, hence after every flow of its target: the
    target's first flow (timestamp AND position) is unchanged, which is what an online APPEND means
    under both orders, and the stream the grouper sees is chronological.
    """
    e_te, y_te, ts_w, src_w, dst_w = flows
    assert np.all(np.diff(ts_w) >= 0), "the deployment window must be chronological"
    T = ep["T"]; gid = ep["gid"]; ordr = ep["order"]
    gsrc = np.zeros(T, dtype=np.int64); gsrc[gid] = src_w
    gdst = np.zeros(T, dtype=np.int64); gdst[gid] = dst_w
    last_ts = np.full(T, np.iinfo(np.int64).min, dtype=np.int64); np.maximum.at(last_ts, gid, ts_w)
    pos = np.flatnonzero(pads > 0)
    g_of_pos = ordr[pos]                                      # stream position -> group id
    rep = np.repeat(g_of_pos, pads[pos])
    assert np.all(last_ts[rep] >= ep["first_ts_g"][rep]), "a pad would precede its target"
    ts2 = np.concatenate([ts_w, last_ts[rep]])
    perm = np.argsort(ts2, kind="mergesort")                  # stable: originals before pads at ties
    padded = tuple(a[perm] for a in (np.concatenate([e_te, np.zeros(len(rep))]),
                                     np.concatenate([y_te, np.zeros(len(rep), dtype=y_te.dtype)]),
                                     ts2,
                                     np.concatenate([src_w, gsrc[rep]]),
                                     np.concatenate([dst_w, gdst[rep]])))
    assert np.all(np.diff(padded[2]) >= 0), "padded stream is not chronological"
    ep2 = hs.build_episodes(*padded, BUCKET, "src-dst", order=order)
    assert np.array_equal(ep2["first_ts_g"][ep2["order"]], ep["first_ts_g"][ordr]), \
        "a pad changed some group's first timestamp: not an append"
    assert ep2["T"] == T, f"padding created or merged episodes: {ep2['T']} vs {T}"
    k1 = np.stack([gsrc[ordr], gdst[ordr], ep["bucket_g"][ordr]])
    gsrc2 = np.zeros(T, dtype=np.int64); gsrc2[ep2["gid"]] = padded[3]
    gdst2 = np.zeros(T, dtype=np.int64); gdst2[ep2["gid"]] = padded[4]
    k2 = np.stack([gsrc2[ep2["order"]], gdst2[ep2["order"]], ep2["bucket_g"][ep2["order"]]])
    assert np.array_equal(k1, k2), "padding changed the episode order"
    assert np.array_equal(ep2["nsz"], ep["nsz"] + pads), "padded arities are not m + r"
    assert np.array_equal(ep2["ismal"], ep["ismal"]), "padding changed a group's label"
    assert np.allclose(ep2["Ev"], Ev_expect, rtol=0, atol=1e-9 * float(np.max(Ev_expect))), \
        "regrouped evidence differs from the vector the attacker was run on"
    return int(len(rep))


def main():
    t0 = time.time()
    Path("out").mkdir(exist_ok=True)
    X, y, ts, src, dst = hs.load()
    N = len(y)
    dport_all = hs.load_extra("dport")
    out = {"config": dict(alpha=A, w0=W0, k=K, bucket_s=BUCKET, positions=POS, seed=SEED,
                          orders=ORDERS, canonical_order="keyhash", gammas=GAMMAS,
                          multipliers=MULTIPLIERS, n_draws=N_DRAWS, caps=CAPS,
                          pool="modal training-prefix (proto, dport) service, as t48/t74",
                          stream_permutation_checked=True), "cells": {}}

    for ip, pos in enumerate(POS):
        i1, i2, i3 = hs.split_indices(N, pos)
        y_cal, y_te = y[i1:i2], y[i2:i3]
        ts_w, src_w, dst_w = ts[i2:i3], src[i2:i3], dst[i2:i3]
        dp_w = dport_all[i2:i3]
        pr_w = np.asarray(X[i2:i3, 0]).astype(np.int32)

        score = hs.fit_detector(X, y, i1, seed=SEED, kind="hgb", verbose=False)
        s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
        e_te, cal, NC, CEIL = hs.evalues(s_cal, y_cal, s_te, k=K)
        flows = (e_te, y_te, ts_w, src_w, dst_w)

        # the black-box pool, selected exactly as t48/t74: modal service on the TRAINING prefix
        svc = pr_w.astype(np.int64) * 100000 + dp_w.astype(np.int64)
        svc_tr = (np.asarray(X[:i1, 0]).astype(np.int64) * 100000
                  + dport_all[:i1].astype(np.int64))
        u, c = np.unique(svc_tr, return_counts=True)
        pool_idx = np.nonzero(svc == int(u[np.argmax(c)]))[0]
        pad_e = e_te[pool_idx]
        n_fire = int((pad_e > 0).sum())
        assert n_fire == 0, (f"pool at {pos} has {n_fire} firing flows; the STATIC subset check "
                             "below is a theorem only for evidence-non-increasing pads")
        print(f"  pos={pos}  NC={NC:,}  pool={pool_idx.size:,} flows  firing={n_fire}  "
              f"[{time.time()-t0:.0f}s]")

        for io, order in enumerate(ORDERS):
            ep = hs.build_episodes(e_te, y_te, ts_w, src_w, dst_w, BUCKET, "src-dst", order=order)
            T = ep["T"]
            S, m, ismal = ep["sum_e"].astype(float), ep["nsz"].astype(np.int64), ep["ismal"]
            Ev0 = S / m
            assert np.allclose(Ev0, ep["Ev"]), "S/m must equal the stream's own Ev"
            # does any attacker-owned episode also carry benign flows?  (the attacker then knows
            # only a lower bound on m; the paper says none of the DETECTED ones do on LSPR23)
            mal_cnt = np.bincount(ep["gid"], weights=y_te.astype(float), minlength=T)[ep["order"]]
            mixed = ismal & (mal_cnt < m)
            for ig, gk in enumerate(GAMMAS):
                g1, _ = make_gamma(gk, T)
                rng = np.random.default_rng([SEED, ip, io, ig])   # independent per cell

                # ---- unperturbed trajectory: the baseline every attacker is priced against -----
                fired0, tau0 = trajectory(Ev0, ismal, CEIL, g1)
                det0 = np.flatnonzero(fired0 & ismal)
                fp0 = np.flatnonzero(fired0 & ~ismal)
                r_static = np.array([zero_pad(S[j], m[j], tau0[j]) for j in det0], dtype=np.int64)
                base = dict(true_detections=int(det0.size), false_discoveries=int(fp0.size),
                            r_static_sorted=sorted(int(v) for v in r_static),
                            median_r_static=float(np.median(r_static)) if det0.size else None,
                            total_r_static=int(r_static.sum()),
                            n_malicious_episodes_with_benign_flows=int(mixed.sum()),
                            n_detected_with_benign_flows=int(mixed[det0].sum()))

                # ---- STATIC: per-alert oracle pads applied together, real pool flows, rerun -----
                draws_all_suppressed = 0; remaining_true = []; remaining_fp = []
                pads_s = np.zeros(T, dtype=np.int64); pads_s[det0] = r_static
                for d in range(N_DRAWS):
                    Ev = Ev0.copy()
                    for j, r in zip(det0, r_static):
                        add = rng.choice(pad_e, size=int(r), replace=True).sum() if r > 0 else 0.0
                        Ev[j] = (S[j] + add) / (m[j] + r)
                    fired, _ = trajectory(Ev, ismal, CEIL, g1)
                    assert not np.any(fired & ~fired0), \
                        "STATIC: attacked run rejected a hypothesis the unperturbed run did not"
                    nt = int((fired & ismal).sum()); nf = int((fired & ~ismal).sum())
                    remaining_true.append(nt); remaining_fp.append(nf)
                    draws_all_suppressed += int(nt == 0)
                n_static_flows = check_padded_stream(flows, ep, pads_s, S / (m + pads_s), order)
                static = dict(n_draws=N_DRAWS, pool_firing_count=n_fire,
                              remaining_true_max=int(max(remaining_true)),
                              remaining_true_min=int(min(remaining_true)),
                              remaining_false_discoveries_max=int(max(remaining_fp)),
                              remaining_false_discoveries_min=int(min(remaining_fp)),
                              per_draw_all_true_suppressed=float(draws_all_suppressed / N_DRAWS),
                              total_cost=int(r_static.sum()),
                              padded_stream_checked_flows=n_static_flows,
                              draws_degenerate_zero_evidence=bool(n_fire == 0))

                # ---- ADAPTIVE: sequential oracle, sized on the attacked trajectory --------------
                pads_a, fired_a = adaptive_attack(S, m, ismal, CEIL, g1)
                assert not np.any(fired_a & ~fired0), \
                    "ADAPTIVE: attacked run rejected a hypothesis the unperturbed run did not"
                assert not np.any(fired_a & ismal), "ADAPTIVE: a true detection survived"
                padded_pos = np.flatnonzero(pads_a > 0)
                assert np.all(np.isin(padded_pos, det0)), \
                    "ADAPTIVE: padded an episode the unperturbed run did not reject"
                Ev_a = S / (m + pads_a)
                fired_chk, _ = trajectory(Ev_a, ismal, CEIL, g1)
                assert np.array_equal(fired_chk, fired_a), \
                    "ADAPTIVE: rerunning e-LOND on the padded vector disagrees with the walk"
                n_adapt_flows = check_padded_stream(flows, ep, pads_a, Ev_a, order)
                r_adapt = pads_a[det0]                     # 0 where the lower level already spares it
                per = [dict(pos_in_stream=int(j), m=int(m[j]), S=float(S[j]),
                            r_static=int(rs), r_adaptive=int(ra))
                       for j, rs, ra in zip(det0, r_static, r_adapt)]
                arity_all = m.astype(float)
                padded_a = (m[det0] + r_adapt).astype(float)
                adaptive = dict(remaining_true=int((fired_a & ismal).sum()),
                                remaining_false_discoveries=int((fired_a & ~ismal).sum()),
                                total_cost=int(r_adapt.sum()),
                                median_r_adaptive=float(np.median(r_adapt)) if det0.size else None,
                                median_r_adaptive_padded_only=(
                                    float(np.median(r_adapt[r_adapt > 0]))
                                    if np.any(r_adapt > 0) else None),
                                n_padded=int((r_adapt > 0).sum()),
                                n_spared_by_lower_level=int((r_adapt == 0).sum()),
                                n_cheaper_than_static=int((r_adapt < r_static).sum()),
                                joint_over_static=(float(r_adapt.sum() / r_static.sum())
                                                   if r_static.sum() else None),
                                # over ALL unperturbed detections (spared ones keep arity m) ...
                                median_padded_arity=(float(np.median(padded_a))
                                                     if det0.size else None),
                                # ... and over the episodes the attacker actually padded
                                median_padded_arity_padded_only=(
                                    float(np.median(padded_a[r_adapt > 0]))
                                    if np.any(r_adapt > 0) else None),
                                deployment_share_at_least_median_padded_only=(
                                    float((arity_all >= np.median(padded_a[r_adapt > 0])).mean())
                                    if np.any(r_adapt > 0) else None),
                                median_padded_arity_static=(float(np.median(m[det0] + r_static))
                                                            if det0.size else None),
                                deployment_share_at_least_median_padded=(
                                    float((arity_all >= np.median(padded_a)).mean())
                                    if det0.size else None),
                                padded_stream_checked_flows=n_adapt_flows,
                                per_episode=per)

                # ---- STATE-FREE: multiply every malicious episode by c, rerun -----------------
                mult = {}
                for cm in MULTIPLIERS:
                    Ev = Ev0.copy()
                    Ev[ismal] = Ev0[ismal] / cm            # S/(c m): (c-1)m zero-evidence flows
                    fired, _ = trajectory(Ev, ismal, CEIL, g1)
                    assert not np.any(fired & ~fired0), \
                        "MULTIPLIER: attacked run rejected a hypothesis the unperturbed run did not"
                    # per-alert prediction (t66): an alert survives iff c < 1 + r*/m at the
                    # unperturbed level
                    pred = int(np.sum(cm < 1.0 + r_static / m[det0])) if det0.size else 0
                    mult[str(cm)] = dict(
                        remaining_true=int((fired & ismal).sum()),
                        remaining_false_discoveries=int((fired & ~ismal).sum()),
                        per_alert_predicted_remaining=pred,
                        total_pad_flows=int(((cm - 1) * m[ismal]).sum()),
                        n_malicious_padded=int(ismal.sum()))

                # ---- CAPPED ADAPTIVE: the joint attacker against the per-host-pair volume cap ----
                benign_arity = arity_all[~ismal]
                capped = []
                for n in CAPS:
                    dg = {}
                    pads_c, fired_c = adaptive_attack(S, m, ismal, CEIL, g1, cap=n, diag=dg)
                    assert not np.any(fired_c & ~fired0), \
                        "CAPPED: attacked run rejected a hypothesis the unperturbed run did not"
                    fm = fired_c & ismal                       # malicious alerts the cap let through
                    # cascade accounting: of the alerts that fired, how many would have fitted under
                    # the cap at the cold-start level and fired only because R had already risen?
                    victims = fm & dg["fits_at_R0"]
                    structural = fm & ~dg["fits_at_R0"]        # too large even at R = 0
                    first = int(np.flatnonzero(fm)[0]) if fm.any() else None
                    capped.append(dict(
                        cap=n, remaining_true=int(fm.sum()),
                        remaining_false_discoveries=int((fired_c & ~ismal).sum()),
                        n_padded=int((pads_c > 0).sum()), total_cost=int(pads_c.sum()),
                        benign_truncated=float((benign_arity > n).mean()),
                        # t74's per-alert reading of the same cap, on the unperturbed pads
                        per_alert_suppressible_under_cap=int(np.sum(m[det0] + r_static <= n)),
                        # measured cascade
                        n_fired_structural=int(structural.sum()),
                        n_fired_cascade_victims=int(victims.sum()),
                        first_fired_m=int(m[first]) if first is not None else None,
                        first_fired_R=int(dg["R_at_fire"][first]) if first is not None else None,
                        first_fired_fits_at_R0=(bool(dg["fits_at_R0"][first])
                                                if first is not None else None),
                        max_R_at_fire=int(dg["R_at_fire"].max())))

                # ---- CRITICAL MULTIPLIER: boundary in closed form, then verified by rerun -------
                steps = np.arange(1, T + 1)
                cold_alpha = A * g1[steps]                       # R = 0 throughout
                c_crit = float(np.max(Ev0[ismal] * cold_alpha[ismal])) if ismal.any() else 0.0
                c_int = int(np.floor(c_crit)) + 1
                rho = (NC + 1.0) * A / T                        # eq. rho, e-LOND (c_0 = alpha)
                crit = dict(c_crit=c_crit, c_int=c_int, rho_elond=float(rho),
                            c_crit_le_rho=bool(c_crit <= rho * (1 + 1e-12)),
                            c_crit_equals_rho=bool(abs(c_crit - rho) <= 1e-9 * rho))
                for tag, cm in (("above", c_crit * (1 + 1e-3)), ("at", c_crit),
                                ("below", c_crit * (1 - 1e-3)), ("int", float(c_int)),
                                ("int_below", float(max(c_int - 1, 1)))):
                    Ev = Ev0.copy(); Ev[ismal] = Ev0[ismal] / cm
                    fired, _ = trajectory(Ev, ismal, CEIL, g1)
                    crit[f"remaining_true_{tag}"] = int((fired & ismal).sum())
                    crit[f"remaining_false_discoveries_{tag}"] = int((fired & ~ismal).sum())
                # the boundary is exact while no false discovery survives to raise R
                crit["exact"] = bool(crit["remaining_false_discoveries_above"] == 0)
                if crit["exact"]:
                    assert crit["remaining_true_above"] == 0, "c > c_crit did not silence everything"
                    assert crit["remaining_true_int"] == 0, "c_int did not silence everything"
                assert crit["remaining_true_below"] >= 1, "c < c_crit left nothing standing"
                assert crit["remaining_true_int_below"] >= 1, "c_int - 1 left nothing standing"
                # c == c_crit: the maximising episode sits ON the inclusive threshold in exact
                # arithmetic; floating-point division may land either side, so `at` is recorded only
                crit["at_is_numerical_boundary_observation"] = True
                crit["above_below_are_continuous_relaxation"] = True
                crit["int_is_realisable_attack"] = True
                pads_int = np.where(ismal, (c_int - 1) * m, 0).astype(np.int64)
                crit["padded_stream_checked_flows_int"] = check_padded_stream(
                    flows, ep, pads_int, S / (m + pads_int), order)
                crit["total_pad_flows_int"] = int(pads_int.sum())

                rec = dict(pos=pos, order=order, gamma=gk, T=int(T), NC=int(NC),
                           n_malicious=int(ismal.sum()), unperturbed=base, static=static,
                           adaptive=adaptive, multiplier=mult, capped_adaptive=capped,
                           critical_multiplier=crit)
                out["cells"][f"{pos}_{order}_{gk}"] = rec
                print(f"    {order:<10} gamma={gk:<8} det={base['true_detections']:>4} "
                      f"fd={base['false_discoveries']} mixed={base['n_detected_with_benign_flows']}"
                      f" | static: remaining {static['remaining_true_max']}, cost "
                      f"{static['total_cost']:>7} | adaptive: cost {adaptive['total_cost']:>5} "
                      f"({adaptive['joint_over_static']:.3f}) spared "
                      f"{adaptive['n_spared_by_lower_level']}, med arity "
                      f"{adaptive['median_padded_arity']}"
                      f" | cap100: {capped[1]['remaining_true']} fire (per-alert: "
                      f"{det0.size - capped[1]['per_alert_suppressible_under_cap']})"
                      f" | c_crit={crit['c_crit']:.3f} rho={crit['rho_elond']:.3f} "
                      f"at->{crit['remaining_true_at']} below->{crit['remaining_true_below']} "
                      f"c_int={c_int}->{crit['remaining_true_int']}  [{time.time()-t0:.0f}s]")

    # ---- CONTROL: unperturbed canonical arms reproduce t73 ------------------------------------
    for (p, gk), (d_, f_, tot_) in CONTROL.items():
        b = out["cells"][f"{float(p)}_keyhash_{gk}"]["unperturbed"]
        assert (b["true_detections"], b["false_discoveries"], b["total_r_static"]) == (d_, f_, tot_), \
            f"CONTROL FAILED at {p} {gk}: {b}"
    out["control_reproduced"] = True
    print("\n  CONTROL OK: unperturbed canonical arms reproduce t73 (3/80, 105/627495, 11/926, "
          "107/977567); every padded stream regrouped to the same permutation")
    json.dump(out, open("out/t75_joint_rerun.json", "w"), indent=1)
    print(f"  wrote out/t75_joint_rerun.json  [{time.time()-t0:.0f}s]")
    return out


if __name__ == "__main__":
    main()
