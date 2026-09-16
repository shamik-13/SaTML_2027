"""E1 -- smoothed and continuous conformal evidence, on LSPR23.  Section 4.34."""


def main(smoke=False):
    import numpy as np, json, time, sys, gc
    from pathlib import Path
    from itertools import combinations
    from sklearn.metrics import roc_auc_score
    from scipy.stats import norm
    from scipy.special import digamma

    import h_stream as H
    from h6_procs import (Ctx, make_gamma, run_lond, run_lordpp, run_saffron, run_addis,
                          run_online_ebh, run_egai, online_ebh_kstar)

    Path("out").mkdir(exist_ok=True)
    SMOKE = smoke
    t0 = time.time()

    POS = [0.55, 0.85]
    DSEEDS = [0, 1]
    NRAND = 12 if SMOKE else 100
    BH = 2
    K = 1
    A, W0 = 0.05, 0.025
    LAMS = [0.1, 0.25, 0.5, 0.75]
    SAF_LAM, ADD_LAM, ADD_TAU = 0.5, 0.25, 0.5
    TINY = np.finfo(np.float64).tiny
    VALID_LEVELS = [1.0, 10.0, 100.0]
    VALID_ABS = [1e-5, 3e-5, 5e-5, 1e-4, 2e-4, 5e-4, 1e-3, 1e-2, 1e-1]
    CHECK_LEVELS = [1e-7, 1e-6, 1e-5, 1e-4]
    CHECK_RANKS = [0, 3, 30, 300, 3000]

    REGRESSION = {
        ("poly", "LOND"): (72, 72), ("poly", "LORD++"): (72, 72),
        ("poly", "SAFFRON"): (70, 70), ("poly", "ADDIS"): (152, 147),
        ("poly", "online e-BH"): (72, 72),
        ("uniform[ORACLE]", "LOND"): (151, 147), ("uniform[ORACLE]", "LORD++"): (151, 147),
        ("uniform[ORACLE]", "SAFFRON"): (0, 0), ("uniform[ORACLE]", "ADDIS"): (0, 0),
        ("uniform[ORACLE]", "online e-BH"): (152, 147),
    }


    def dev_check(pred, obs, n):
        pred = np.asarray(pred, float); obs = np.asarray(obs, float)
        nz = pred > 0
        max_dev = float(np.max(np.abs(obs / n - pred))) if pred.size else 0.0
        var = n * pred * (1.0 - pred)
        sel = var >= 5.0
        z = np.zeros_like(pred)
        z[sel] = (obs[sel] - n * pred[sel]) / np.sqrt(var[sel])
        maxz = float(np.max(np.abs(z))) if sel.any() else 0.0
        tot_var = float(var[nz].sum())
        pooled = float((obs[nz] - n * pred[nz]).sum() / np.sqrt(tot_var)) \
            if tot_var > 0 else 0.0
        ncheck = int(sel.sum())
        zcrit = float(norm.isf(0.0025 / max(ncheck, 1))) if ncheck else 6.0
        det_bad = int((((pred == 0.0) & (obs > 0)) |
                       ((pred == 1.0) & (obs < n))).sum())
        low = (var < 5.0) & (pred > 0.0) & (pred < 1.0)
        low_bad = 0; low_pooled = 0.0; low_chi_z = 0.0
        if low.any():
            from scipy.stats import binom as _binom
            pl, ol = pred[low], obs[low]
            tail = 2.0 * np.minimum(_binom.cdf(ol, n, pl), _binom.sf(ol - 1, n, pl))
            low_bad = int((tail < 0.005 / max(int(low.sum()), 1)).sum())
            lv = n * pl * (1.0 - pl)
            low_pooled = float((ol - n * pl).sum() / np.sqrt(lv.sum())) \
                if lv.sum() > 0 else 0.0
            pear = float((((ol - n * pl) ** 2) / np.maximum(lv, 1e-12)).sum())
            dfl = float(low.sum())
            pear_var = float(np.sum(2.0 + (1.0 - 6.0 * pl * (1.0 - pl)) / np.maximum(lv, 1e-12)))
            low_chi_z = (pear - dfl) / np.sqrt(pear_var) if pear_var > 0 else 0.0
        return dict(n_checked=ncheck, n_nonzero=int(nz.sum()), max_abs_dev=max_dev,
                    max_z=maxz, z_crit=zcrit, pooled_z=pooled,
                    n_deterministic_bad=det_bad, n_lowpower=int(low.sum()),
                    n_lowpower_bad=low_bad, lowpower_pooled_z=low_pooled,
                    lowpower_chi_z=low_chi_z,
                    ok=bool(det_bad == 0 and low_bad == 0 and maxz <= zcrit
                            and abs(pooled) <= 5.0 and abs(low_pooled) <= 5.0
                            and low_chi_z <= 5.0))


    def conformal_ranks(cal, s_te, NC):
        """(G, Etie, lo) = (#{c > s}, #{c == s}, searchsorted-left) against the sorted benign"""
        hi = np.searchsorted(cal, s_te, side='right')
        lo = np.searchsorted(cal, s_te, side='left')
        return (NC - hi).astype(np.float64), (hi - lo).astype(np.float64), lo


    def smoothed_p(G, Etie, U, M):
        """The smoothed conformal p-value p_u = (G + U*(1+E))/M.  The (1+E), not E: the test"""
        return (G + U * (1.0 + Etie)) / M


    def calibrate(pu, lam):
        """The p-to-e calibrator lam*p^(lam-1).  The exponent is lam-1, NOT 1-lam: it must be"""
        return lam * pu ** (lam - 1.0)


    def episode_pvalues(pv, gid, order, nsz_raw, starts, srt, m_over_k, H_m, T):
        """All four episode-level merges of a per-flow p-value array, in EPISODE order."""
        pmin = np.minimum.reduceat(pv[srt], starts)
        sim, hom = simes_hommel_merge(pv, gid, starts, m_over_k, H_m)
        bonf = np.minimum(1.0, nsz_raw * pmin)
        meanp = np.minimum(1.0, 2.0 * np.bincount(gid, weights=pv, minlength=T) / nsz_raw)
        return dict(simes=sim[order], hommel=hom[order], bonf=bonf[order],
                    meanp=meanp[order], pmin=pmin)


    def simes_index(gid, nsz_raw, n):
        """Per-flow within-episode rank machinery for the Simes merge, in GROUP-ID order."""
        srt = np.argsort(gid, kind='stable')
        starts = np.concatenate(([0], np.flatnonzero(np.diff(gid[srt])) + 1))
        flow_start = np.repeat(starts, nsz_raw.astype(np.int64))
        flow_m = np.repeat(nsz_raw, nsz_raw.astype(np.int64))
        rank_k = np.arange(n, dtype=np.int64) - flow_start + 1
        m_over_k = flow_m / rank_k
        H_m = digamma(nsz_raw + 1.0) + np.euler_gamma
        return srt, starts, flow_m, rank_k, m_over_k, H_m


    def simes_hommel_merge(pv, gid, starts, m_over_k, H_m):
        """(P_simes, P_hommel) per episode, in GROUP-ID order."""
        o = np.lexsort((pv, gid))
        raw = np.minimum.reduceat(m_over_k * pv[o], starts)
        return np.minimum(1.0, raw), np.minimum(1.0, H_m * raw)


    def run_lond_p(ctx, gam1, P, fired=None):
        """LOND tested directly on the episode p-value."""
        R = rej = tp = silent = 0; first = None
        for t in range(1, ctx.T + 1):
            lvl = ctx.A * gam1[t] * (R + 1)
            if ctx.infeasible(lvl):
                silent += 1
                if first is None: first = t
                continue
            if P[t - 1] <= lvl:
                R += 1; rej += 1
                if fired is not None: fired[t - 1] = True
                if ctx.ismal[t - 1]: tp += 1
        return rej, tp, silent, first


    def ebh_mask(Ev, gam1, alpha, T):
        """The online e-BH rejection mask, built from the SHARED k* routine so it cannot drift"""
        ks, m = online_ebh_kstar(Ev, gam1, alpha, T)
        kfin = int(ks[T])
        return (np.isfinite(m) & (m <= kfin)), kfin, ks, m


    def ebh_entry_ts(ks, m, first_ts_h, T):
        """Wall-clock time at which each online e-BH rejection actually becomes an alert."""
        entry = np.searchsorted(ks, m, side='left')
        entry = np.maximum(entry, np.arange(1, T + 1))
        out = np.full(T, np.nan)
        ok = np.isfinite(m) & (entry <= T)
        out[ok] = first_ts_h[entry[ok] - 1]
        return out


    def metrics(rej, tp, silent, first_inf, fired, ismal, first_ts_h, T, NMAL,
                alert_ts_h=None):
        """`alert_ts_h`, if given, replaces first_ts_h for the LATENCY fields only."""
        d = dict(rejections=int(rej), tp=int(tp), fp=int(rej - tp),
                 fdp=float((rej - tp) / max(rej, 1)),
                 fdp_cond=(float((rej - tp) / rej) if rej else None),
                 recall=float(tp / NMAL) if NMAL else None,
                 silent=float(silent / T),
                 first_infeasible=(int(first_inf) if first_inf else None))
        if fired is not None:
            idx = np.flatnonzero(fired)
            d["alerts"] = idx
            lat = first_ts_h if alert_ts_h is None else alert_ts_h
            d["first_rej_h"] = float(np.min(lat[idx])) if idx.size else None
            tpidx = idx[ismal[idx]]
            d["first_tp_h"] = float(np.min(lat[tpidx])) if tpidx.size else None
            d["alert_time_is_entry"] = alert_ts_h is not None
        return d


    def agg(vals):
        v = np.asarray([x for x in vals if x is not None], dtype=float)
        if not v.size:
            return dict(n=0, mean=None, sd=None, min=None, med=None, max=None)
        return dict(n=int(v.size), mean=float(v.mean()), sd=float(v.std(ddof=1)) if v.size > 1
                    else 0.0, min=float(v.min()), med=float(np.median(v)), max=float(v.max()))


    def jaccard(sets, max_pairs=4950, rng=None):
        """Mean pairwise Jaccard over seed pairs.  This is a MEAN OF RATIOS; the analytic"""
        n = len(sets)
        if n < 2: return None, None, 0
        pairs = list(combinations(range(n), 2))
        if len(pairs) > max_pairs:
            pairs = [pairs[i] for i in rng.choice(len(pairs), max_pairs, replace=False)]
        js, n_empty = [], 0
        for i, j in pairs:
            u = len(sets[i] | sets[j])
            if u == 0:
                n_empty += 1
                continue
            js.append(len(sets[i] & sets[j]) / u)
        if not js:
            return None, None, n_empty
        js = np.asarray(js)
        return (float(js.mean()), float(js.std(ddof=1)) if js.size > 1 else 0.0, n_empty)


    X, y, ts, src, dst = H.load()
    N = len(y)
    rows, per_cfg, failures, lond_disagree = [], [], [], []

    for pos in POS:
        i1, i2, i3 = H.split_indices(N, pos)
        ts_w, src_w, dst_w, y_te = ts[i2:i3], src[i2:i3], dst[i2:i3], y[i2:i3]
        n_te = i3 - i2
        ben_te = (y_te == 0)

        for dseed in DSEEDS:
            tag = f"pos={pos} dseed={dseed}"
            sc = H.fit_detector(X, y, i1, dseed, kind="hgb")
            s_cal, s_te = H.score_windows(sc, X, i1, i2, i3)
            y_cal = y[i1:i2]
            auroc = float(roc_auc_score(y_te, s_te))

            e_te, cal, NC, CEIL = H.evalues(s_cal, y_cal, s_te, k=K)
            M = NC + 1.0
            G, Etie, lo = conformal_ranks(cal, s_te, NC)
            assert np.array_equal(1 + (NC - lo), (1 + G + Etie).astype(np.int64)), "G/E vs K"
            assert np.array_equal(e_te, np.where((1 + G + Etie) <= K, CEIL, 0.0)), \
                "G/E vs evalues() full e-values (magnitude, not just the firing mask)"
            del lo

            ep = H.build_episodes(e_te, y_te, ts_w, src_w, dst_w, bucket_s=BH * 3600)
            gid, order, T = ep["gid"], ep["order"], ep["T"]
            ismal, NMAL = ep["ismal"], ep["n_mal"]
            nsz_raw = np.bincount(gid, minlength=T).astype(np.float64)
            first_ts = np.full(T, np.iinfo(np.int64).max)
            np.minimum.at(first_ts, gid, ts_w)
            first_ts_h = (first_ts[order] - ts_w.min()) / 3.6e9
            srt, starts, flow_m, rank_k, m_over_k, H_m = simes_index(gid, nsz_raw, n_te)
            assert len(starts) == T

            g1p, g0p = make_gamma("poly", T)
            g1u, g0u = make_gamma("uniform", T)
            GAMS = (("poly", g1p, g0p), ("uniform[ORACLE]", g1u, g0u))
            margin = M * W0 / T - 1.0

            lv = [(f"{int(c)}/M", c / M) for c in VALID_LEVELS] + \
                 [(f"{a:g}", a) for a in VALID_ABS]
            nben = int(ben_te.sum())
            Gb, Eb = G[ben_te], Etie[ben_te]
            valid = {}
            for nm, a in lv:
                qb = np.clip((a * M - Gb) / (1.0 + Eb), 0.0, 1.0)
                meas = float(qb.mean())
                valid[nm] = dict(level=a, measured=meas, ratio=meas / a,
                                 expected_count=float(qb.sum()), nominal_count=a * nben,
                                 sd_randomisation=float(np.sqrt((qb * (1.0 - qb)).sum())),
                                 sd_sampling=float(np.sqrt(nben * meas * (1.0 - meas))))
            disc_fire_n = int((e_te[ben_te] > 0).sum())
            valid["discrete_benign_firing_ratio"] = dict(
                level=1.0 / M, measured=disc_fire_n / nben, ratio=(disc_fire_n / nben) * M,
                expected_count=float(disc_fire_n), nominal_count=nben / M,
                sd_randomisation=0.0,
                sd_sampling=float(np.sqrt(nben * (disc_fire_n / nben) * (1 - disc_fire_n / nben))))
            del Gb, Eb

            arms = {}

            def add(route, merge, proc, gname, res, lam=None):
                key = (route, merge, proc, gname, lam)
                arms.setdefault(key, []).append(res)

            CEIL_BONF = M
            CEIL_MEANP = M / 2.0
            CEIL_SIMES = M
            CEIL_HOMMEL = M

            def run_p_procs(route, merge, P_ep, seedtag):
                """LOND / LORD++ / SAFFRON / ADDIS on an episode p-value array (ordered)."""
                Ev = 1.0 / np.maximum(P_ep, TINY)
                if route != "discrete":
                    ceil = np.inf
                else:
                    ceil = {"bonf-p": CEIL_BONF, "mean-p": CEIL_MEANP,
                            "simes": CEIL_SIMES, "hommel": CEIL_HOMMEL}[merge]
                for gname, g1, g0 in GAMS:
                    ctx = Ctx(Ev, ismal, ceil, alpha=A, w0=W0)
                    f = np.zeros(T, bool)
                    Pc = np.minimum(1.0, P_ep)
                    r = run_lond_p(ctx, g1, Pc, fired=f)
                    fe = np.zeros(T, bool)
                    run_lond(ctx, g1, fired=fe)
                    nd = int((f != fe).sum())
                    if nd:
                        lond_disagree.append(dict(pos=pos, dseed=dseed, route=route,
                                                  merge=merge, gamma=gname, n=nd))
                    add(route, merge, "LOND", gname,
                        metrics(*r, f, ismal, first_ts_h, T, NMAL))
                    fl = np.zeros(T, bool)
                    add(route, merge, "LORD++", gname,
                        metrics(*run_lordpp(ctx, g1, fired=fl), fl, ismal, first_ts_h, T, NMAL))
                    f = np.zeros(T, bool)
                    r = run_saffron(ctx, g1, lam=SAF_LAM, fired=f)
                    add(route, merge, "SAFFRON", gname,
                        metrics(*r, f, ismal, first_ts_h, T, NMAL))
                    f = np.zeros(T, bool)
                    r = run_addis(ctx, g0, lam=ADD_LAM, tau_=ADD_TAU, fired=f)
                    add(route, merge, "ADDIS", gname,
                        metrics(*r, f, ismal, first_ts_h, T, NMAL))
                return dict(frac_P_le_addis_tau=float((np.minimum(1, P_ep) <= ADD_TAU).mean()),
                            frac_P_le_addis_lam=float((np.minimum(1, P_ep) <= ADD_LAM).mean()),
                            frac_P_le_saffron_lam=float((np.minimum(1, P_ep) <= SAF_LAM).mean()))

            def run_e_procs(route, merge, Ev, lam, ceil):
                for gname, g1, g0 in GAMS:
                    ctx = Ctx(Ev, ismal, ceil, alpha=A, w0=W0)
                    f = np.zeros(T, bool)
                    r = run_lond(ctx, g1, fired=f)
                    add(route, merge, "e-LOND", gname,
                        metrics(*r, f, ismal, first_ts_h, T, NMAL), lam)
                    mask, kfin, ks, mm = ebh_mask(Ev, g1, A, T)
                    rj = int(mask.sum()); tp = int((mask & ismal).sum())
                    chk = run_online_ebh(ctx, g1)
                    if (chk[0], chk[1]) != (rj, tp):
                        failures.append(f"{tag} ebh_mask != run_online_ebh "
                                        f"{route}/{merge}/{gname}/{lam}: {(rj,tp)} vs {chk[:2]}")
                    add(route, merge, "online e-BH", gname,
                        metrics(rj, tp, chk[2], chk[3], mask, ismal, first_ts_h, T, NMAL,
                                alert_ts_h=ebh_entry_ts(ks, mm, first_ts_h, T)), lam)
                ctx = Ctx(Ev, ismal, ceil, alpha=A, w0=W0)
                fg = np.zeros(T, bool)
                add(route, merge, "e-LORD", "egai(w1=1/T)[ORACLE]",
                    metrics(*run_egai(ctx, "e-LORD", 1.0 / T, fired=fg), fg, ismal,
                            first_ts_h, T, NMAL), lam)

            P_rec = np.minimum(1.0, 1.0 / np.maximum(Ev_rec_pre := ep["Ev"], TINY))
            idx_mean_e = dict(
                frac_P_le_addis_tau=float((P_rec <= ADD_TAU).mean()),
                frac_P_le_addis_lam=float((P_rec <= ADD_LAM).mean()),
                frac_P_le_saffron_lam=float((P_rec <= SAF_LAM).mean()))
            del P_rec

            Ev_rec = ep["Ev"]
            for gname, g1, g0 in GAMS:
                ctx = Ctx(Ev_rec, ismal, CEIL, alpha=A, w0=W0)
                for proc, fn, gg in (("LOND", run_lond, g1), ("LORD++", run_lordpp, g1),
                                     ("SAFFRON", run_saffron, g1), ("ADDIS", run_addis, g0)):
                    f = np.zeros(T, bool)
                    kw = dict(fired=f)
                    if proc == "SAFFRON": kw = dict(lam=SAF_LAM, fired=f)
                    elif proc == "ADDIS": kw = dict(lam=ADD_LAM, tau_=ADD_TAU, fired=f)
                    r = fn(ctx, gg, **kw)
                    add("discrete", "mean-e", proc, gname,
                        metrics(*r, f, ismal, first_ts_h, T, NMAL))
                mask, kfin, _, _ = ebh_mask(Ev_rec, g1, A, T)
                chk = run_online_ebh(ctx, g1)
                rj = int(mask.sum()); tp = int((mask & ismal).sum())
                if (chk[0], chk[1]) != (rj, tp):
                    failures.append(f"{tag} baseline ebh_mask mismatch {(rj,tp)} vs {chk[:2]}")
                add("discrete", "mean-e", "online e-BH", gname,
                    metrics(rj, tp, chk[2], chk[3], mask, ismal, first_ts_h, T, NMAL))

            if pos == 0.85 and dseed == 0:
                for (gname, proc), (wr, wt) in REGRESSION.items():
                    got = arms[("discrete", "mean-e", proc, gname, None)][0]
                    if (got["rejections"], got["tp"]) != (wr, wt):
                        failures.append(f"REGRESSION section 4.20 {gname}/{proc}: got "
                                        f"{(got['rejections'], got['tp'])} want {(wr, wt)}")
                for nm, want in (("T", 31568), ("NC", 1813113), ("NMAL", 255)):
                    got = {"T": T, "NC": NC, "NMAL": NMAL}[nm]
                    if got != want:
                        failures.append(f"REGRESSION {nm}: got {got} want {want}")

            p_d = (1.0 + G + Etie) / M
            EPD = episode_pvalues(p_d, gid, order, nsz_raw, starts, srt, m_over_k, H_m, T)
            sim_d = EPD["simes"]
            P_rec_chk = np.minimum(1.0, 1.0 / np.maximum(ep["Ev"], TINY))
            sim_ep = sim_d
            if not np.all(sim_ep <= P_rec_chk * (1.0 + 1e-12)):
                failures.append(f"{tag} discrete Simes is NOT <= the record's mean-e p-value")
            fired_rec = P_rec_chk < 1.0
            n_strict = int((sim_ep[fired_rec] < P_rec_chk[fired_rec] * (1.0 - 1e-12)).sum()) \
                if fired_rec.any() else 0
            simes_vs_meane = dict(
                n_firing=int(fired_rec.sum()), n_strictly_smaller=n_strict,
                median_ratio=(float(np.median(sim_ep[fired_rec] / P_rec_chk[fired_rec]))
                              if fired_rec.any() else None))
            print(f"    [note] {tag}: discrete Simes strictly below the record's mean-e rule on "
                  f"{n_strict}/{int(fired_rec.sum())} firing episodes "
                  f"(median ratio {simes_vs_meane['median_ratio']})")
            del P_rec_chk, sim_ep, fired_rec
            idx_ctl = {"mean-e": idx_mean_e}
            idx_ctl["simes"] = run_p_procs("discrete", "simes", EPD["simes"], None)
            idx_ctl["hommel"] = run_p_procs("discrete", "hommel", EPD["hommel"], None)
            idx_ctl["bonf-p"] = run_p_procs("discrete", "bonf-p", EPD["bonf"], None)
            idx_ctl["mean-p"] = run_p_procs("discrete", "mean-p", EPD["meanp"], None)
            del p_d, sim_d, EPD

            m_flow = nsz_raw[gid]
            qA_pred, qB_pred, obsA, obsB = {}, {}, {}, {}
            for a in CHECK_LEVELS:
                w = np.clip((a * M / m_flow - G) / (1.0 + Etie), 0.0, 1.0)
                with np.errstate(divide='ignore'):
                    lg = np.log1p(-w)
                qA_pred[a] = 1.0 - np.exp(np.bincount(gid, weights=lg, minlength=T))
                obsA[a] = np.zeros(T, dtype=np.int64)
                del w, lg
            PSTARS = [(r + 0.5) / M for r in CHECK_RANKS]
            selB = np.flatnonzero(G <= max(CHECK_RANKS) + 2)
            qflow, obsAflow = {}, {}
            for pstar in PSTARS:
                q = np.clip((pstar * M - G[selB]) / (1.0 + Etie[selB]), 0.0, 1.0)
                qflow[pstar] = q
                obsAflow[pstar] = np.zeros(len(selB), dtype=np.int64)
                for lam in LAMS:
                    qB_pred[(pstar, lam)] = q
                    obsB[(pstar, lam)] = np.zeros(len(selB), dtype=np.int64)

            idx_traj = {}
            for rs in range(NRAND):
                rng = np.random.default_rng(1_000_000 + 10_000 * rs + int(pos * 100) + dseed)
                U = np.maximum(rng.random(n_te), TINY)
                pu = smoothed_p(G, Etie, U, M)
                EPS_ = episode_pvalues(pu, gid, order, nsz_raw, starts, srt, m_over_k, H_m, T)
                pmin = EPS_["pmin"]
                tr = run_p_procs("smoothA", "simes", EPS_["simes"], rs)
                idx_traj.setdefault("simes", []).append(tr)
                run_p_procs("smoothA", "hommel", EPS_["hommel"], rs)
                run_p_procs("smoothA", "bonf-p", EPS_["bonf"], rs)
                run_p_procs("smoothA", "mean-p", EPS_["meanp"], rs)
                for a in CHECK_LEVELS:
                    obsA[a] += (nsz_raw * pmin <= a)
                puB = pu[selB]
                for pstar in PSTARS:
                    obsAflow[pstar] += (puB <= pstar)
                    for lam in LAMS:
                        a_eq = pstar ** (1.0 - lam) / lam
                        obsB[(pstar, lam)] += (calibrate(puB, lam) >= 1.0 / a_eq)
                del puB
                for lam in LAMS:
                    e = calibrate(pu, lam)
                    Evb = (np.bincount(gid, weights=e, minlength=T) / nsz_raw)[order]
                    run_e_procs("smoothB", "mean-e", Evb, lam, np.inf)
                    del e, Evb
                del U, pu, pmin, EPS_
                if rs == 0 or (rs + 1) % 25 == 0:
                    print(f"  {tag}  randomisation seed {rs+1}/{NRAND}  "
                          f"[{time.time()-t0:.0f}s]")

            dcheck = {}
            for a in CHECK_LEVELS:
                dcheck[f"RouteA bonf-p  a={a:g}  [D4a/D4b]"] = dev_check(qA_pred[a], obsA[a], NRAND)
            for r, pstar in zip(CHECK_RANKS, PSTARS):
                dcheck[f"RouteA flow rank {r}+1/2 [D2a]"] = dev_check(
                    qflow[pstar], obsAflow[pstar], NRAND)
                for lam in LAMS:
                    dcheck[f"RouteB flow rank {r}+1/2 lam={lam} [D3d]"] = dev_check(
                        qB_pred[(pstar, lam)], obsB[(pstar, lam)], NRAND)
            for k, v in dcheck.items():
                if not v["ok"]:
                    failures.append(f"{tag} DERIVATION MISMATCH {k}: max_z={v['max_z']:.2f} "
                                    f"(crit {v['z_crit']:.2f}) pooled_z={v['pooled_z']:.2f} "
                                    f"max|obs-pred|={v['max_abs_dev']:.4f} "
                                    f"n_checked={v['n_checked']} "
                                    f"det-bad={v['n_deterministic_bad']} "
                                    f"lowpower-bad={v['n_lowpower_bad']}/{v['n_lowpower']} "
                                    f"lowpower-pooled-z={v['lowpower_pooled_z']:+.2f} "
                                    f"lowpower-chi-z={v['lowpower_chi_z']:+.2f}")

            rng_j = np.random.default_rng(4242)
            for (route, merge, proc, gname, lam), reslist in arms.items():
                has_mask = all("alerts" in r for r in reslist)
                sets = [set(r["alerts"].tolist()) for r in reslist if "alerts" in r] \
                    if has_mask else []
                jm, jsd, jne = jaccard(sets, rng=rng_j) if len(sets) > 1 else (None, None, 0)
                malidx = np.flatnonzero(ismal)
                if sets:
                    cnt = np.zeros(T)
                    for s in sets: cnt[list(s)] += 1
                    pdet = cnt[malidx] / len(sets)
                else:
                    pdet = np.array([])
                if sets:
                    q = cnt / len(sets)
                    den = float((2 * q - q ** 2).sum())
                    j_roe = float((q ** 2).sum() / den) if den > 0 else None
                else:
                    j_roe = None
                rows.append(dict(
                    pos=pos, dseed=dseed, route=route, merge=merge, proc=proc, gamma=gname,
                    lam=lam, n_seeds=len(reslist), T=int(T), NC=int(NC), NMAL=int(NMAL),
                    auroc=auroc, margin=float(margin), CEIL=float(CEIL),
                    rejections=agg([r["rejections"] for r in reslist]),
                    fdp=agg([r["fdp"] for r in reslist]),
                    fdp_cond=agg([r["fdp_cond"] for r in reslist]),
                    recall=agg([r["recall"] for r in reslist]),
                    silent=agg([r["silent"] for r in reslist]),
                    first_rej_h=agg([r.get("first_rej_h") for r in reslist]),
                    first_tp_h=agg([r.get("first_tp_h") for r in reslist]),
                    var_R=(float(np.var([r["rejections"] for r in reslist], ddof=1))
                           if len(reslist) > 1 else 0.0),
                    var_FDP=(float(np.var([r["fdp"] for r in reslist], ddof=1))
                             if len(reslist) > 1 else 0.0),
                    jaccard_mean=jm, jaccard_sd=jsd, jaccard_ratio_of_exp=j_roe,
                    n_pairs_both_empty=int(jne),
                    n_configs_fdp_over_q=int(sum(1 for r in reslist
                                                 if r["fdp_cond"] is not None
                                                 and r["fdp_cond"] > A)),
                    pdet_mal=dict(n=int(pdet.size),
                                  mean=float(pdet.mean()) if pdet.size else None,
                                  n_ge_090=int((pdet >= 0.9).sum()),
                                  n_ge_050=int((pdet >= 0.5).sum()),
                                  n_gt_000=int((pdet > 0).sum())),
                ))
            per_cfg.append(dict(pos=pos, dseed=dseed, T=int(T), NC=int(NC), NMAL=int(NMAL),
                                auroc=auroc, margin=float(margin), CEIL=float(CEIL),
                                n_test_flows=int(n_te), n_benign_test=int(ben_te.sum()),
                                validity=valid, discrete_index=idx_ctl,
                                derivation_check=dcheck,
                                simes_vs_meane=simes_vs_meane,
                                smoothed_index=(
                                    {k: float(np.mean([d[k] for d in idx_traj["simes"]]))
                                     for k in idx_traj["simes"][0]}
                                    if idx_traj.get("simes") else None)))
            print(f"  {tag} done  AUROC={auroc:.4f} T={T:,} |C|={NC:,} margin={margin:+.3f} "
                  f"mal={NMAL}  [{time.time()-t0:.0f}s]")
            del s_cal, s_te, e_te, cal, G, Etie, ep, arms
            gc.collect()

    def line(r):
        rj, fd, rc = r["rejections"], r["fdp"], r["recall"]
        f = lambda d, p=3: "   --   " if d["mean"] is None else f"{d['mean']:.{p}f}+-{d['sd']:.{p}f}"
        jv = "  --  " if r["jaccard_mean"] is None else f"{r['jaccard_mean']:.3f}"
        ne = r.get("n_pairs_both_empty") or 0
        if ne and r["jaccard_mean"] is not None:
            jv += "*"
        lam = "" if r["lam"] is None else f" lam={r['lam']}"
        return (f"  {r['route']+'/'+r['merge']:>16} {r['proc']:>12}{lam:>9} {r['gamma']:>7} "
                f"{f(rj,1):>16} {f(fd):>15} {f(rc):>15} "
                f"{100*r['silent']['mean']:>6.1f}% {jv:>8} "
                f"{r['pdet_mal']['n_gt_000']:>5}/{r['pdet_mal']['n_ge_090']:>4}")


    HDR = (f"  {'route/merge':>16} {'procedure':>12} {'':>9} {'gamma':>7} "
           f"{'rejections':>16} {'FDP':>15} {'recall':>15} {'silent':>7} {'Jacc':>8} "
           f"{'det>0/>=.9':>10}")
    for pos in POS:
        for dseed in DSEEDS:
            sub = [r for r in rows if r["pos"] == pos and r["dseed"] == dseed]
            if not sub: continue
            c = next(c for c in per_cfg if c["pos"] == pos and c["dseed"] == dseed)
            print("\n" + "=" * 130)
            print(f"position {pos}  detector seed {dseed}   T={c['T']:,}  |C|={c['NC']:,}  "
                  f"malicious episodes={c['NMAL']}  AUROC={c['auroc']:.4f}  "
                  f"margin={c['margin']:+.3f}"
                  + ("   [stress window -- evidence is NOT a valid e-value, section 4.31]"
                     if pos == 0.85 else "   [guarantee window]"))
            print("=" * 130); print(HDR)
            keyf = lambda r: (r["route"], r["merge"], r["proc"], str(r["lam"]), r["gamma"])
            for r in sorted(sub, key=keyf):
                print(line(r))
            print("\n  benign tail validity  (measured / nominal; nominal P(p_u<=a) = a exactly [D2c])")
            for nm, d in c["validity"].items():
                print(f"    {nm:>34}  level={d['level']:.3e}  ratio={d['ratio']:>7.2f}x   "
                      f"benign flows {d['expected_count']:>9.1f} "
                      f"(+-{d['sd_randomisation']:.1f} rand, +-{d['sd_sampling']:.1f} sampling)"
                      f"  vs {d['nominal_count']:>9.1f} nominal")
            si = c["smoothed_index"]; di = c["discrete_index"]
            if si:
                print("\n  ADDIS / SAFFRON index mechanics.  ADDIS escapes the section 4.13 template")
                print("  because its index counts TESTED hypotheses and the two-point p-value never")
                print("  produces one; these fractions are that index's growth rate per step.")
                for k, lbl in (("frac_P_le_addis_tau", "<= ADDIS tau=0.5 "),
                               ("frac_P_le_addis_lam", "<= ADDIS lam=0.25"),
                               ("frac_P_le_saffron_lam", "<= SAFFRON lam=0.5")):
                    print(f"    fraction of episode p-values {lbl} :  discrete mean-e (the record) "
                          f"{di['mean-e'][k]:.4f}   discrete simes {di['simes'][k]:.4f}   "
                          f"smoothed simes {si[k]:.4f}")
            dc = c.get("derivation_check")
            if dc:
                print("\n  DERIVATION AGREEMENT -- measured randomisation frequency vs the t34a closed")
                print("  form, on this window's real scores.  A disagreement is a bug, not a finding.")
                for k, v in dc.items():
                    print(f"    {k:>44}  episodes checked={v['n_checked']:>6}  "
                          f"max|obs-pred|={v['max_abs_dev']:.4f}  max z={v['max_z']:+.2f}  "
                          f"pooled z={v['pooled_z']:+.2f}  det-bad={v['n_deterministic_bad']:>4}  "
                          f"lowpwr {v['n_lowpower_bad']:>3}/{v['n_lowpower']:<6} "
                          f"z={v['lowpower_pooled_z']:+.2f} chi={v['lowpower_chi_z']:+.2f} "
                          f"{'OK' if v['ok'] else 'MISMATCH'}")

    print("\n  Jaccard is the MEAN OF PAIRWISE RATIOS over seed pairs, CONDITIONAL on at least")
    print("  one of the pair alerting; pairs in which both alert sets are empty are excluded")
    print("  rather than scored 1, and a '*' marks a row where some pairs were excluded (the")
    print("  count is n_pairs_both_empty in the JSON).  The analytic reference [D5c] is a ratio")
    print("  of expectations, reported separately as jaccard_ratio_of_exp; the two differ.")
    if lond_disagree:
        tot = sum(d["n"] for d in lond_disagree)
        print(f"\n  LOND p-form vs e-form disagreed on {tot} episode-decisions across "
              f"{len(lond_disagree)} arms (float reciprocal boundary; p-form is authoritative)")
    else:
        print("\n  LOND p-form and e-form agreed on every episode-decision in every arm, so the")
        print("  reciprocal-boundary hazard is confirmed immaterial at these settings.")
    print("\n" + "=" * 130)
    if failures:
        print("FAILURES:")
        for f in failures: print("  " + f)
    else:
        print("all regression and internal consistency checks passed")
    print("=" * 130)

    json.dump(dict(config=dict(POS=POS, DSEEDS=DSEEDS, NRAND=NRAND, bucket_h=BH, k=K,
                               alpha=A, w0=W0, lams=LAMS, saffron_lam=SAF_LAM,
                               addis_lam=ADD_LAM, addis_tau=ADD_TAU, smoke=SMOKE),
                   rows=[{k: (v if k != "alerts" else None) for k, v in r.items()}
                         for r in rows],
                   per_cfg=per_cfg, failures=failures, lond_disagree=lond_disagree),
              open("out/t34_E1_smoothed.json", "w"), indent=1, allow_nan=True)
    print(f"  [{time.time()-t0:.0f}s]  wrote out/t34_E1_smoothed.json")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    import sys
    main(smoke="--smoke" in sys.argv)
