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

VARIANTS = ["resampled", "removed"]


def keep_count(T, M, pi):

    if pi is None:
        return int(M)
    if pi <= 0.0:
        return 0
    k = pi * (T - M) / (1.0 - pi)
    return int(min(M, max(1, round(k))))


def cold_start(CEIL, T, R=0):

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

                deterministic = (keep == M) or (keep == 0)
                n_rep = 1 if deterministic else N_REP
                res = {v: dict(el=[], eb=[], tdd=[]) for v in VARIANTS}
                for rep in range(n_rep):

                    rng = np.random.default_rng(
                        (20260902 + 1000 * rep + int(pos * 100)) ^ (0x9E37 * (1 + ORDERS.index(order))))
                    perm = rng.permutation(mal_idx)
                    drop = perm[keep:]
                    for variant in VARIANTS:
                        if variant == "removed":

                            mask = np.ones(T, bool); mask[drop] = False
                            Ev2 = Ev[mask]; im2 = ismal[mask]; bk2 = bucket_ord[mask]
                        else:

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

        max_abs_margin_shift_to_1e4=max((abs(x["margin_shift_fixed_T"]) for x in obs_vs_thin),
                                        default=None),
        max_margin_shift_removed=max((x["margin_shift_removed"] for x in obs_vs_thin), default=None),
        max_T_shrink_frac=max((x["T_shrink_frac_removed"] for x in obs_vs_thin), default=None),

        elond_p_bootstrap_at_1e4=[x["elond_p_boot_1e4"] for x in obs_vs_thin],
        elond_p_bootstrap_at_1e4_removed=[x["elond_p_boot_1e4_removed"] for x in obs_vs_thin],
        ebh_p_bootstrap_at_1e4=[x["ebh_p_boot_1e4"] for x in obs_vs_thin],
        etoad_p_bootstrap_at_1e4=[x["etoad_p_boot_1e4"] for x in obs_vs_thin],

        max_abs_variant_gap_at_1e4=max((abs(x["elond_p_boot_1e4"] - x["elond_p_boot_1e4_removed"])
                                        for x in obs_vs_thin), default=None),

        null_elond_p_reject=[r["elond"]["p_bootstrap"] for r in null_rows],
        null_ebh_p_reject=[r["online_ebh"]["p_bootstrap"] for r in null_rows],
        n_pure_null_rows=n_null_streams,
        n_pure_null_effective_streams=len(POS),
        n_pure_null_rows_with_any_rejection=n_null_rejecting,
        n_pure_null_rows_with_any_rejection_ebh=n_null_rejecting_ebh,
        prob_zero_if_true_rate_045=float(0.955 ** len(POS)),
        prob_zero_if_true_rate_045_over_rows=float(0.955 ** n_null_streams),
        null_arm_can_test_the_simulated_rate=False,

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

    return out


if __name__ == "__main__":
    main()
