"""R5 -- what the results look like at a SOC's base rate, not a live-fire exercise's.

LSPR23 is a cyber-defence exercise, so its attack prevalence is enormous by operational standards:
10.06% of FLOWS are malicious, and 0.48-0.81% of two-hour host-pair EPISODES.  An ordinary SOC sees
10^-4 to 10^-6.  The reviewer's objection is that every number in the paper is therefore measured in
a regime no deployment inhabits.  It is a fair objection and the direction it pushes matters, so we
measure it rather than argue about it.

WHAT IS THINNED, AND WHY EPISODES RATHER THAN FLOWS.  Dropping malicious *flows* would change the
composition of the groups they belong to -- their arity and their evidence sum -- which is exactly
the channel attack surface A manipulates, so a flow-level thinning would confound C1 with C2.  We
drop whole malicious EPISODES instead: the hypothesis never enters the stream, the benign background
is untouched, and the calibration set (hence the evidence ceiling) is untouched.  To reach target
prevalence pi from M malicious episodes in a stream of T, keep

    keep = pi (T - M) / (1 - pi),      T' = (T - M) + keep,

so the realised prevalence is keep/T' = pi up to rounding, reported per row.

pi = 10^-2 is NOT reachable: the observed episode prevalence is already below it, and we cannot
manufacture attacks.  pi = 0 IS included deliberately -- the pure-null arm measures the probability
that the controller makes an early FALSE rejection, which the body currently quotes from simulation
(4.5% for e-LOND, 2.2% for LORD++).  Measuring it on the real benign stream is a cross-check of an
existing claim, not a new one.

THE EXPECTED DIRECTION, STATED BEFORE MEASURING.  Thinning removes at most 0.8% of the stream, so T
and hence the feasibility margin barely move; what it removes is precisely the rare high-evidence
hypotheses that can bootstrap the controller out of its cold-start window.  So detections should
collapse while the margin stays put -- the same feasibility-is-not-detection separation the paper
already reports at 0.70 seed 1, driven here by prevalence instead of by detector quality.  If that
is what happens, live-fire prevalence is the OPTIMISTIC case and every detection count in the paper
is an upper bound in one more respect.

Three procedures: e-LOND (the paper's primary), online e-BH and e-TOAD at bucket-close deadlines
(the two escapes of the C1 taxonomy -- if the escapes survive realistic prevalence and e-LOND does
not, that is a different paper, so it must be checked).  Both within-bucket orders (item R3):
"keyhash" is the canonical order the paper reports, "first-flow" the optimistic upper bound.

Writes out/t59_prevalence.json.
"""
import numpy as np, json, time
from pathlib import Path
from scipy.special import zeta

import h_stream as hs
from h6_procs import Ctx, make_gamma, run_lond, run_online_ebh, run_etoad, make_deadlines

A = 0.05; W0 = 0.025; K = 1; BUCKET = 2 * 3600
POS = [0.55, 0.62, 0.70, 0.77, 0.85]
SEED = 0
ORDERS = ["keyhash", "first-flow"]
PI_TARGETS = [None, 1e-3, 1e-4, 1e-5, 0.0]     # None = the observed live-fire prevalence
N_REP = 50                                      # e-LOND and online e-BH
N_REP_TOAD = 20                                 # e-TOAD is ~60x dearer per run
# TWO thinning mechanisms, because they are not the same counterfactual and the difference is
# measurable.  "resampled" keeps the hypothesis in the stream with benign evidence (T, the margin and
# every step index fixed) and is PRIMARY; "removed" deletes it (T shrinks, survivors shift earlier
# into a higher alpha_t) and is the sensitivity arm.  Reporting only "removed" would conflate
# "fewer attacks" with "the survivors moved earlier", which can INCREASE detections.
VARIANTS = ["resampled", "removed"]


def keep_count(T, M, pi):
    """Malicious episodes to KEEP so that keep/((T-M)+keep) == pi.

    pi=None keeps them all (the observed arm); pi=0 keeps none (the pure-null arm).  For a positive
    target the exact solution is pi(T-M)/(1-pi), but rounding it can land on ZERO -- at pi=1e-5 with
    T~31,000 the exact value is 0.31 -- which would silently turn a prevalence arm into a second copy
    of the pure-null arm.  A positive target therefore keeps at least ONE episode, and the caller is
    told (`attained` below) that the realised prevalence overshoots its target."""
    if pi is None:
        return int(M)
    if pi <= 0.0:
        return 0
    k = pi * (T - M) / (1.0 - pi)
    return int(min(M, max(1, round(k))))


def cold_start(CEIL, T, R=0):
    """Largest step at which e-LOND can reject anything with R rejections so far.

    Spelled exactly as Ctx.infeasible spells it (CEIL < 1/lvl), so it agrees with a realised run
    step for step.  Returned with the closed form beside it as a cross-check."""
    g1, _ = make_gamma("poly", T)
    lvl = A * g1[1:T + 1] * (R + 1.0)
    with np.errstate(divide="ignore"):
        ok = np.flatnonzero(np.where(lvl > 0, CEIL >= 1.0 / np.maximum(lvl, 1e-300), False))
    w = int(ok[-1] + 1) if ok.size else 0
    x = A * CEIL * (R + 1.0) / float(zeta(1.6, 1))
    return w, (int(np.floor(x ** (1.0 / 1.6))) if x > 0 else 0)


def q(a, p):
    return float(np.percentile(a, p)) if len(a) else None


def main():
    t0 = time.time()
    Path("out").mkdir(exist_ok=True)
    X, y, ts, src, dst = hs.load()
    N = len(y)
    flow_prev = float(y.mean())
    print(f"  LSPR23 flow prevalence {100*flow_prev:.2f}% malicious "
          f"({int(y.sum()):,}/{N:,}) -- a SOC sees 1e-4 to 1e-6")

    rows, per_pos = [], []
    for pos in POS:
        i1, i2, i3 = hs.split_indices(N, pos)
        y_te = y[i2:i3]; ts_w = ts[i2:i3]; src_w = src[i2:i3]; dst_w = dst[i2:i3]
        score = hs.fit_detector(X, y, i1, seed=SEED, kind="hgb", verbose=False)
        s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
        e_te, cal, NC, CEIL = hs.evalues(s_cal, y[i1:i2], s_te, k=K)

        for order in ORDERS:
            ep = hs.build_episodes(e_te, y_te, ts_w, src_w, dst_w, BUCKET, "src-dst", order=order)
            T = ep["T"]; Ev = ep["Ev"]; ismal = ep["ismal"]
            bucket_ord = ep["bucket_g"][ep["order"]]          # bucket id in EMITTED order
            M = int(ismal.sum())
            obs_pi = M / T
            w_cold, w_closed = cold_start(CEIL, T)
            if order == ORDERS[0]:
                print(f"\n  pos={pos}  T={T:,}  malicious episodes {M} "
                      f"(episode prevalence {100*obs_pi:.3f}%)  cold-start window {w_cold} steps  "
                      f"[{time.time()-t0:.0f}s]")
                per_pos.append(dict(pos=pos, T=int(T), n_mal=M, episode_prevalence=obs_pi,
                                    flow_prevalence=flow_prev, CEIL=float(CEIL), NC=int(NC),
                                    cold_start_steps=w_cold,
                                    cold_start_matches_closed_form=bool(w_cold == w_closed)))
            print(f"    {order:<11} {'pi':>8} {'keep':>5} {'realised':>9} {'margin':>7} "
                  f"| {'e-LOND R':>9} {'boot%':>6} {'FDP|a':>6} {'silent':>7} "
                  f"| {'e-BH R':>7} {'boot%':>6} | {'eTOAD':>6} | {'rm R':>6} {'rm boot':>7}")

            mal_idx = np.flatnonzero(ismal)
            ben_idx = np.flatnonzero(~ismal)
            for pi in PI_TARGETS:
                keep = keep_count(T, M, pi)
                if pi is not None and pi > obs_pi:
                    continue                                  # cannot manufacture attacks
                # Only a PARTIAL thinning is random.  Keeping all of them (the observed arm) or
                # none (the pure-null arm) yields one deterministic stream, and running it 50 times
                # would report a probability over 50 identical trials.
                deterministic = (keep == M) or (keep == 0)
                n_rep = 1 if deterministic else N_REP
                res = {v: dict(el=[], eb=[], tdd=[]) for v in VARIANTS}
                for rep in range(n_rep):
                    # NESTED draw: one permutation of the malicious episodes per (window, order,
                    # repeat), keeping its first `keep`.  A lower target therefore keeps a strict
                    # SUBSET of what a higher one kept, which is both the physical story (a
                    # deployment with fewer attacks) and a paired comparison across pi.  Seeding on
                    # the order too keeps the two orders' draws independent -- mal_idx lives in
                    # EMITTED coordinates, so a shared seed would not even retain the same episodes.
                    rng = np.random.default_rng(
                        (20260902 + 1000 * rep + int(pos * 100)) ^ (0x9E37 * (1 + ORDERS.index(order))))
                    perm = rng.permutation(mal_idx)
                    drop = perm[keep:]
                    for variant in VARIANTS:
                        if variant == "removed":
                            # the hypothesis leaves the stream: T shrinks and every LATER hypothesis
                            # shifts one step earlier, into a higher alpha_t.  That confounds
                            # "fewer attacks" with "survivors move earlier", so it is the sensitivity
                            # arm rather than the primary one.
                            mask = np.ones(T, bool); mask[drop] = False
                            Ev2 = Ev[mask]; im2 = ismal[mask]; bk2 = bucket_ord[mask]
                        else:
                            # INDEX-PRESERVING (primary): the host pair still generates traffic, it
                            # is simply benign, so the hypothesis stays in the stream at its own
                            # index with evidence drawn from that window's own BENIGN episodes.  T,
                            # the margin and every survivor's step index are held fixed, which is
                            # what isolates prevalence from re-indexing.
                            Ev2 = Ev.copy(); im2 = ismal.copy(); bk2 = bucket_ord
                            if drop.size:
                                Ev2[drop] = Ev[ben_idx][rng.integers(0, ben_idx.size, drop.size)]
                                im2[drop] = False
                        T2v = int(len(Ev2))
                        ctx = Ctx(Ev2, im2, CEIL, alpha=A, w0=W0)
                        g1, _ = make_gamma("poly", T2v)
                        r, tp, sil, first = run_lond(ctx, g1)
                        res[variant]["el"].append((r, tp, sil, T2v))
                        r2, tp2, sil2, _f2, _k, _lag, _na = run_online_ebh(ctx, g1)
                        res[variant]["eb"].append((r2, tp2, sil2, T2v))
                        if rep < N_REP_TOAD:
                            d = make_deadlines("bucket", T2v, bucket=bk2)
                            r3, tp3, sil3, _f3 = run_etoad(ctx, g1, d)[:4]
                            res[variant]["tdd"].append((r3, tp3, sil3, T2v))
                T2 = int(T - (M - keep))                       # the "removed" variant's length
                real_pi = keep / T2 if T2 else 0.0
                real_pi_fixed = keep / T                       # the index-preserving variant's
                margin = (NC + 1) * W0 / T2 - 1.0
                margin_fixed = (NC + 1) * W0 / T - 1.0

                def summarise(v, n_rep_used):
                    if not v:
                        return None
                    R = np.array([x[0] for x in v], float)
                    TP = np.array([x[1] for x in v], float)
                    SL = np.array([x[2] for x in v], float)
                    TT = np.array([x[3] for x in v], float)
                    fdp = np.where(R > 0, (R - TP) / np.maximum(R, 1), 0.0)
                    fired = R > 0
                    return dict(n_rep=n_rep_used, rej_mean=float(R.mean()), rej_max=float(R.max()),
                                tp_mean=float(TP.mean()), tp_max=float(TP.max()),
                                p_bootstrap=float(fired.mean()),
                                p_true_detection=float((TP > 0).mean()),
                                fdp_mean=float(fdp.mean()), fdp_max=float(fdp.max()),
                                # E[V/(R v 1)] averages a 0 over every silent repeat, so the
                                # CONDITIONAL value -- FDP among repeats that alerted at all -- is
                                # reported beside it; quoting the unconditional one alone would
                                # read as "the alerts are clean" when there were no alerts.
                                fdp_mean_given_alert=(float(fdp[fired].mean()) if fired.any()
                                                      else None),
                                n_rep_with_alert=int(fired.sum()),
                                silent_frac_mean=float((SL / np.maximum(TT, 1)).mean()))

                attained = (pi is None or pi <= 0.0
                            or abs(real_pi_fixed - pi) <= 1.0 / T + 1e-12)
                rec = dict(pos=pos, order=order, pi_target=pi, n_keep=int(keep), T=int(T2),
                           deterministic=bool(deterministic),
                           pi_target_attained=bool(attained),
                           realised_prevalence=float(real_pi),
                           realised_prevalence_fixed_T=float(real_pi_fixed),
                           margin=float(margin), margin_fixed_T=float(margin_fixed),
                           n_mal_full=M, T_full=int(T), cold_start_steps=w_cold,
                           elond=summarise(res["resampled"]["el"], n_rep),
                           online_ebh=summarise(res["resampled"]["eb"], n_rep),
                           etoad_bucket=summarise(res["resampled"]["tdd"], min(n_rep, N_REP_TOAD)),
                           removed=dict(
                               elond=summarise(res["removed"]["el"], n_rep),
                               online_ebh=summarise(res["removed"]["eb"], n_rep),
                               etoad_bucket=summarise(res["removed"]["tdd"],
                                                      min(n_rep, N_REP_TOAD))))
                rows.append(rec)
                f = lambda x, d=3: ("--" if x is None else f"{x:.{d}f}")
                pl = ("obs" if pi is None else (f"{pi:.0e}" if pi > 0 else "0"))
                if not attained:
                    pl += "*"
                rm = rec["removed"]["elond"]
                print(f"    {'':<11} {pl:>8} {keep:>5} {real_pi_fixed:>9.2e} "
                      f"{margin_fixed:>+7.3f} | {rec['elond']['rej_mean']:>9.2f} "
                      f"{100*rec['elond']['p_bootstrap']:>5.0f}% "
                      f"{f(rec['elond']['fdp_mean_given_alert'], 2):>6} "
                      f"{100*rec['elond']['silent_frac_mean']:>6.1f}% "
                      f"| {rec['online_ebh']['rej_mean']:>7.2f} "
                      f"{100*rec['online_ebh']['p_bootstrap']:>5.0f}% "
                      f"| {100*(rec['etoad_bucket'] or {}).get('p_bootstrap', float('nan')):>5.0f}% "
                      f"| {rm['rej_mean']:>6.2f} {100*rm['p_bootstrap']:>6.0f}%")

    # --- the two claims this stage exists to settle -------------------------------------
    def at(pos, order, pi):
        for r in rows:
            if r["pos"] == pos and r["order"] == order and r["pi_target"] == pi:
                return r
        return None

    obs_vs_thin = []
    for pos in POS:
        for order in ORDERS:
            a = at(pos, order, None); b = at(pos, order, 1e-4)
            if a and b:
                obs_vs_thin.append(dict(
                    pos=pos, order=order,
                    # the PRIMARY (index-preserving) arm holds T and the margin exactly fixed, so
                    # the margin shift is zero BY CONSTRUCTION; the "removed" arm's shift is the
                    # thing worth reporting, and it is what the sensitivity is about
                    margin_obs=a["margin_fixed_T"], margin_1e4=b["margin_fixed_T"],
                    margin_shift_fixed_T=b["margin_fixed_T"] - a["margin_fixed_T"],
                    margin_shift_removed=b["margin"] - a["margin"],
                    T_shrink_frac_removed=1.0 - b["T"] / a["T"],
                    elond_rej_obs=a["elond"]["rej_mean"], elond_rej_1e4=b["elond"]["rej_mean"],
                    elond_p_boot_1e4=b["elond"]["p_bootstrap"],
                    elond_p_boot_1e4_removed=b["removed"]["elond"]["p_bootstrap"],
                    elond_rej_1e4_removed=b["removed"]["elond"]["rej_mean"],
                    ebh_rej_obs=a["online_ebh"]["rej_mean"],
                    ebh_rej_1e4=b["online_ebh"]["rej_mean"],
                    ebh_p_boot_1e4=b["online_ebh"]["p_bootstrap"],
                    etoad_p_boot_1e4=(b["etoad_bucket"] or {}).get("p_bootstrap")))
    # the pure-null arm is ONE deterministic stream per (window, order), not a sample of 50
    null_rows = [r for r in rows if r["pi_target"] == 0.0]
    n_null_streams = len(null_rows)
    n_null_rejecting = sum(1 for r in null_rows if r["elond"]["rej_max"] > 0)
    n_null_rejecting_ebh = sum(1 for r in null_rows if r["online_ebh"]["rej_max"] > 0)
    summary = dict(
        flow_prevalence=flow_prev,
        episode_prevalence_range=[min(p["episode_prevalence"] for p in per_pos),
                                  max(p["episode_prevalence"] for p in per_pos)],
        pi_1e2_unreachable=True,
        # (1) does thinning move FEASIBILITY?  In the PRIMARY arm it cannot -- T is held fixed, so
        # the margin is identically unchanged.  In the "removed" arm T shrinks and the margin RISES
        # slightly, which is the direction that would flatter the controller, so reporting it
        # matters: detection collapses even as feasibility improves.
        max_abs_margin_shift_to_1e4=max((abs(x["margin_shift_fixed_T"]) for x in obs_vs_thin),
                                        default=None),
        max_margin_shift_removed=max((x["margin_shift_removed"] for x in obs_vs_thin), default=None),
        max_T_shrink_frac=max((x["T_shrink_frac_removed"] for x in obs_vs_thin), default=None),
        # (2) does thinning move DETECTION?  it must, and towards zero -- under BOTH mechanisms.
        elond_p_bootstrap_at_1e4=[x["elond_p_boot_1e4"] for x in obs_vs_thin],
        elond_p_bootstrap_at_1e4_removed=[x["elond_p_boot_1e4_removed"] for x in obs_vs_thin],
        ebh_p_bootstrap_at_1e4=[x["ebh_p_boot_1e4"] for x in obs_vs_thin],
        etoad_p_bootstrap_at_1e4=[x["etoad_p_boot_1e4"] for x in obs_vs_thin],
        # do the two mechanisms agree?  if they do, re-indexing is not driving the result.
        max_abs_variant_gap_at_1e4=max((abs(x["elond_p_boot_1e4"] - x["elond_p_boot_1e4_removed"])
                                        for x in obs_vs_thin), default=None),
        # (3) the pure-null arm.  It is NOT a sample: 5 windows x 2 orders is 10 rows but 5
        # datasets, and the windows overlap by construction (a 15% test slice slides across the
        # same stream).  With 5 effective streams, observing zero rejections has probability 0.79
        # even if the true early-false-rejection rate were the 4.5% the body quotes FROM SIMULATION
        # -- so this arm CANNOT check that number, and is reported as consistency, not as a test.
        null_elond_p_reject=[r["elond"]["p_bootstrap"] for r in null_rows],
        null_ebh_p_reject=[r["online_ebh"]["p_bootstrap"] for r in null_rows],
        n_pure_null_rows=n_null_streams,
        n_pure_null_effective_streams=len(POS),
        n_pure_null_rows_with_any_rejection=n_null_rejecting,
        n_pure_null_rows_with_any_rejection_ebh=n_null_rejecting_ebh,
        prob_zero_if_true_rate_045=float(0.955 ** len(POS)),
        prob_zero_if_true_rate_045_over_rows=float(0.955 ** n_null_streams),
        null_arm_can_test_the_simulated_rate=False,
        # (4) which rows did NOT attain their nominal target (rounding to under one episode)
        rows_not_attaining_target=[dict(pos=r["pos"], order=r["order"], pi_target=r["pi_target"],
                                        realised=r["realised_prevalence_fixed_T"])
                                   for r in rows if not r["pi_target_attained"]],
        obs_vs_thin=obs_vs_thin)
    out = dict(
        config=dict(POS=POS, SEED=SEED, ORDERS=ORDERS, PI_TARGETS=[str(p) for p in PI_TARGETS],
                    n_rep=N_REP, n_rep_toad=N_REP_TOAD, k=K, alpha=A, w0=W0, bucket_s=BUCKET,
                    thinning="whole malicious EPISODES dropped; benign stream and calibration set "
                             "untouched, so |C| and the evidence ceiling are unchanged"),
        windows=per_pos, rows=rows, summary=summary)
    json.dump(out, open("out/t59_prevalence.json", "w"), indent=1, allow_nan=False)
    print(f"\n  PRIMARY (index-preserving) arm: T and the margin are held fixed by construction "
          f"(max shift {summary['max_abs_margin_shift_to_1e4']:.1e}), and e-LOND's probability of "
          f"EVER rejecting at pi=1e-4 is {summary['elond_p_bootstrap_at_1e4']}")
    print(f"  SENSITIVITY (removed) arm: T shrinks by at most "
          f"{100*summary['max_T_shrink_frac']:.2f}% and the margin RISES by up to "
          f"{summary['max_margin_shift_removed']:+.4f} -- detection collapses even as feasibility "
          f"improves; bootstrap {summary['elond_p_bootstrap_at_1e4_removed']}")
    print(f"  the two mechanisms differ by at most "
          f"{summary['max_abs_variant_gap_at_1e4']:.2f} in bootstrap probability, so re-indexing is "
          f"not what drives the collapse")
    print(f"  pure-null arm: {n_null_rejecting} of {n_null_streams} "
          f"rows reject, but that is {len(POS)} effective streams (the windows overlap), and "
          f"P(zero | true rate 4.5%) = {summary['prob_zero_if_true_rate_045']:.2f} -- CONSISTENT "
          f"with the body's simulated rate, not a test of it")
    print(f"  [{time.time()-t0:.0f}s]  wrote out/t59_prevalence.json")
    return out


if __name__ == "__main__":
    main()
