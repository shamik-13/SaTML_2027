"""
E1 -- smoothed and continuous conformal evidence, on LSPR23.  Section 4.34.

Answers reviewer questions 1 and 2 of 02_WORKPLAN_PHASE4.md section 9: "why not
randomise/smooth the conformal p-values?" and "why not use continuous e-values?".

The closed forms this script asserts against are derived and numerically verified in
t34a_E1_derivation.py; run that FIRST.  A disagreement between the two is a bug, not a
finding (docs/01_HANDOFF_PHASE4.md section 6).  Tags: [D2b], [D3e] etc. refer to its
derivation labels.

WHAT IS COMPARED ------------------------------------------------------------------------
Per-flow evidence, three constructions of it:

  DISCRETE   p_d = (1+G+E)/M,  e = M*1{K<=1}     -- the record's construction, M = |C|+1
  ROUTE A    p_u = (G + U*(1+E))/M               -- smoothed, straight into a p-value proc
  ROUTE B    p_u -> e = lam*p_u^(lam-1)          -- smoothed, calibrated, into an e-proc

Episode-level merges.  The record aggregates per-flow e-values by the arithmetic mean and
takes min(1, 1/Ev) for the p-value procedures (sections 2.2, 2.3).  With the two-point
e-value, if r of m flows fire then min(1,1/Ev) = m/(M*r).  Four p-space merges are run, and
the choice of merge turns out to matter more than smoothing does:

  SIMES    min_k (m/k) p_(k)   -- the p-space analogue of the record's rule.  With the
           discrete two-point evidence it equals m/(M*r) whenever the minimum is attained at
           k = r, and is otherwise STRICTLY SMALLER, because it may pick k > r: with one
           flow at 1/M and five at 2/M the record's rule gives 6/M and Simes gives 2/M.  So
           the relation is Simes <= mean-e+Markov, asserted below in that direction, and the
           discrete Simes control can be strictly more powerful than the record's own rule.
           Valid under independence/PRDS, NOT under arbitrary dependence.  This is the
           primary Route-A merge, because testing Route A under a weaker merge would make
           E1 a strawman.
  HOMMEL   H_m * Simes, H_m the m-th harmonic number -- Simes made valid under ARBITRARY
           dependence, which is the assumption the record's mean-e rule satisfies for free
           by linearity.  The gap between the Simes and Hommel rows is the price of that
           assumption, and H_m ~ ln m + 0.577 is 12-13 for this stream's largest episodes.
  BONF     min(1, m*min_i p_i) -- valid under arbitrary dependence; equals Simes at r = 1.
  MEAN-P   min(1, 2*mean_i p_i) (Ruschendorf / Vovk-Wang) -- valid under arbitrary
           dependence, carried as a sensitivity.  It is destroyed by a single inert flow.

Route B keeps the arithmetic mean of calibrated e-values, unchanged from the record.

Every smoothed arm has a DISCRETE CONTROL UNDER THE SAME MERGE, so that any difference is
attributable to smoothing rather than to the change of merge.

WHY THERE IS NO BOOSTED ROUTE-B ARM ------------------------------------------------------
Boosting (section 4.28, F15) is exactly vacuous for the discrete two-point e-value but NOT
for the calibrated continuous one: t34a derives b* = (tau/lam)^lam, which at lam = 1/2 is
sqrt(2*tau) -- section 4.28's own closed form, recovered independently.  The boosted
rejection region is exactly p_u <= lam*alpha_t [D3j], i.e. Route A run at a level lam times
smaller.  Route A is measured here at the true level, so it dominates every boosted Route-B
arm by construction and no separate run is needed.  The result is recorded as [EXACT].

MEASURED --------------------------------------------------------------------------------
Over NRAND randomisation seeds at positions 0.55 and 0.85 x 2 detector seeds:
empirical FDP, episode recall, alert count, structural-silence fraction, alert-set Jaccard
between seed pairs, per-attack-episode detection probability, Var(R_T), Var(FDP_T),
detection-latency variance, and the benign tail-validity ratio at six levels.

Position 0.55 is the guarantee window; position 0.85 is the instrumented stress window and
its evidence is NOT a valid e-value (section 4.31, 50.9x).  Numbers from 0.85 are reported
separately and never as guarantees (settled decision, 01 section 5.1).

Runtime ~25 min.  Run from proto/.
"""
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
SMOKE = "--smoke" in sys.argv
t0 = time.time()

# ---------------------------------------------------------------------------------------
POS = [0.55, 0.85]
DSEEDS = [0, 1]
NRAND = 12 if SMOKE else 100          # standing mistake 3: a randomised rule needs >= 100
BH = 2                               # two-hour grouping, matching sections 4.17/4.19/4.20
K = 1                                # F14: the only feasible rank
A, W0 = 0.05, 0.025
LAMS = [0.1, 0.25, 0.5, 0.75]        # lam = 0.5 IS Vovk's (1/2) p^(-1/2)
SAF_LAM, ADD_LAM, ADD_TAU = 0.5, 0.25, 0.5
TINY = np.finfo(np.float64).tiny
VALID_LEVELS = [1.0, 10.0, 100.0]    # multiples of 1/M, plus the absolute levels below
VALID_ABS = [1e-5, 3e-5, 5e-5, 1e-4, 2e-4, 5e-4, 1e-3, 1e-2, 1e-1]
CHECK_LEVELS = [1e-7, 1e-6, 1e-5, 1e-4]   # fixed episode levels for the Route-A merge check
# Per-flow checks are placed at HALF-INTEGER RANKS, p* = (r + 1/2)/M.  A flow's rejection
# probability is clip((p*M - G)/(1+E), 0, 1), which for integer G and no ties is 0 or 1
# unless p*M falls strictly inside (G, G+1) -- so a p* at a round number leaves almost every
# flow deterministic and the check has no power.  At p* = (r+1/2)/M every flow of rank
# exactly r has probability 1/2, which is where the check bites hardest.
# Route B is checked at a chosen p* rather than a chosen level for the same reason: at any
# realistic level its region p <= (a*lam)^(1/(1-lam)) admits only flows above EVERY
# calibration score, so a level-parameterised check would compare 0 against 0.  Solving
# a = p*^(1-lam)/lam instead exercises the calibrator inversion [D3d] where flows live.
CHECK_RANKS = [0, 3, 30, 300, 3000]

# Section 4.20, position 0.85 seed 0, two-hour grouping.  Asserted, not trusted: if the
# stream construction has moved, every number below moves with it.
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
    sel = var >= 5.0                        # where the normal approximation holds
    z = np.zeros_like(pred)
    z[sel] = (obs[sel] - n * pred[sel]) / np.sqrt(var[sel])
    maxz = float(np.max(np.abs(z))) if sel.any() else 0.0
    tot_var = float(var[nz].sum())
    pooled = float((obs[nz] - n * pred[nz]).sum() / np.sqrt(tot_var)) \
        if tot_var > 0 else 0.0
    ncheck = int(sel.sum())
    # Bonferroni-corrected two-sided 0.5% critical value over the checked episodes
    zcrit = float(norm.isf(0.0025 / max(ncheck, 1))) if ncheck else 6.0
    # A prediction of exactly 0 or exactly 1 has zero variance, so it never enters
    # the z statistics and a badly wrong one would pass unnoticed: predicting 0 when
    # the observed rate is 0.5 gives max_z = 0.  Check those cells directly.
    det_bad = int((((pred == 0.0) & (obs > 0)) |
                   ((pred == 1.0) & (obs < n))).sum())
    # Cells with 0 < pred < 1 but n*pred*(1-pred) < 5 enter neither max_z (gated out)
    # nor det_bad (not deterministic), so an error there is invisible and can also
    # cancel inside pooled_z: pred=[.04,.04], obs=[0,8], n=100 passes every other
    # test.  Check them EXACTLY, with a Bonferroni-corrected two-sided binomial tail.
    low = (var < 5.0) & (pred > 0.0) & (pred < 1.0)
    low_bad = 0; low_pooled = 0.0; low_chi_z = 0.0
    if low.any():
        from scipy.stats import binom as _binom
        pl, ol = pred[low], obs[low]
        # (a) any single low-power cell that is decisively wrong on its own
        tail = 2.0 * np.minimum(_binom.cdf(ol, n, pl), _binom.sf(ol - 1, n, pl))
        low_bad = int((tail < 0.005 / max(int(low.sum()), 1)).sum())
        # (b) SYSTEMATIC bias across the low-power cells, which no single-cell test
        # sees and which cancels inside the global pooled_z once the high-power
        # cells are added.  Pool the low-power cells on their own.
        lv = n * pl * (1.0 - pl)
        low_pooled = float((ol - n * pl).sum() / np.sqrt(lv.sum())) \
            if lv.sum() > 0 else 0.0
        # (c) an OMNIBUS term.  The signed pool above cancels when errors alternate in
        # sign: pred = [0.02, 0.05]*200 against obs = [4, 3]*200 is wrong in EVERY cell
        # yet gives pooled z = 0.  A Pearson statistic cannot cancel; it is standardised
        # to a z by its own null mean (df) and variance (2*df).
        pear = float((((ol - n * pl) ** 2) / np.maximum(lv, 1e-12)).sum())
        dfl = float(low.sum())
        # Var(Z^2) for a BINOMIAL Z is 2 + (1 - 6p(1-p))/(np(1-p)), not 2.  When n*p < 1 the
        # correction dominates, and standardising by sqrt(2*df) fires on a CORRECT closed
        # form -- blocking a true result, which is worse than missing a bug.
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
    """(G, Etie, lo) = (#{c > s}, #{c == s}, searchsorted-left) against the sorted benign
    calibration scores.  The searchsorted sides are the whole content of this function and a
    swapped side is a silent off-by-one in every downstream p-value, so it lives here where
    the self-test can reach it rather than inline in the driver."""
    hi = np.searchsorted(cal, s_te, side='right')
    lo = np.searchsorted(cal, s_te, side='left')
    return (NC - hi).astype(np.float64), (hi - lo).astype(np.float64), lo


def smoothed_p(G, Etie, U, M):
    """The smoothed conformal p-value p_u = (G + U*(1+E))/M.  The (1+E), not E: the test
    point is a member of its own tie group."""
    return (G + U * (1.0 + Etie)) / M


def calibrate(pu, lam):
    """The p-to-e calibrator lam*p^(lam-1).  The exponent is lam-1, NOT 1-lam: it must be
    negative so that a small p maps to large evidence."""
    return lam * pu ** (lam - 1.0)


def episode_pvalues(pv, gid, order, nsz_raw, starts, srt, m_over_k, H_m, T):
    """All four episode-level merges of a per-flow p-value array, in EPISODE order.

    Returns dict(simes, hommel, bonf, meanp, pmin).  Every merge is built AND permuted by
    `order` here, so a dropped or doubled `[order]`, a missing Bonferroni factor m, or a
    missing mean-p factor 2 is a change to THIS function, which the self-test checks against
    a brute-force reference.
    """
    pmin = np.minimum.reduceat(pv[srt], starts)
    sim, hom = simes_hommel_merge(pv, gid, starts, m_over_k, H_m)
    bonf = np.minimum(1.0, nsz_raw * pmin)
    meanp = np.minimum(1.0, 2.0 * np.bincount(gid, weights=pv, minlength=T) / nsz_raw)
    return dict(simes=sim[order], hommel=hom[order], bonf=bonf[order],
                meanp=meanp[order], pmin=pmin)


def simes_index(gid, nsz_raw, n):
    """Per-flow within-episode rank machinery for the Simes merge, in GROUP-ID order.

    Returns (starts, flow_m, rank_k, m_over_k, H_m).  np.lexsort((p, gid)) places the groups
    in the same ascending-gid blocks, at the same positions, as np.argsort(gid), so `starts`
    indexes both orders identically -- that is what makes the reduceat below correct.
    """
    srt = np.argsort(gid, kind='stable')
    starts = np.concatenate(([0], np.flatnonzero(np.diff(gid[srt])) + 1))
    flow_start = np.repeat(starts, nsz_raw.astype(np.int64))
    flow_m = np.repeat(nsz_raw, nsz_raw.astype(np.int64))
    rank_k = np.arange(n, dtype=np.int64) - flow_start + 1
    m_over_k = flow_m / rank_k
    H_m = digamma(nsz_raw + 1.0) + np.euler_gamma        # exact harmonic number
    return srt, starts, flow_m, rank_k, m_over_k, H_m


def simes_hommel_merge(pv, gid, starts, m_over_k, H_m):
    """(P_simes, P_hommel) per episode, in GROUP-ID order.

    Simes  = min_k (m/k) p_(k)                 valid under independence / PRDS
    Hommel = H_m * Simes                       valid under ARBITRARY dependence
    """
    o = np.lexsort((pv, gid))
    raw = np.minimum.reduceat(m_over_k * pv[o], starts)
    return np.minimum(1.0, raw), np.minimum(1.0, H_m * raw)


def run_lond_p(ctx, gam1, P, fired=None):
    """LOND tested directly on the episode p-value.

    h6_procs.run_lond tests `Ev >= 1/lvl`.  Route A supplies Ev = 1/P_ep, and the two
    reciprocals can round to the same float when P_ep sits within one ulp of lvl, so
    `Ev >= 1/lvl` and `P_ep <= lvl` can disagree there (e.g. lvl = 1.5330101557787505e-06,
    P = nextafter(lvl)).  This is a literal transcription of run_lond with that one
    comparison replaced; the number of episodes on which the two forms disagree is counted
    and reported, so the size of the effect is measured rather than assumed negligible."""
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
    """The online e-BH rejection mask, built from the SHARED k* routine so it cannot drift
    from run_online_ebh.  Asserted equal to run_online_ebh's counts on every baseline arm."""
    ks, m = online_ebh_kstar(Ev, gam1, alpha, T)
    kfin = int(ks[T])
    return (np.isfinite(m) & (m <= kfin)), kfin, ks, m


def ebh_entry_ts(ks, m, first_ts_h, T):
    """Wall-clock time at which each online e-BH rejection actually becomes an alert.

    Hypothesis i clears once k*_t >= m_i; the entry step is the first such t, and it is at
    least i+1 (it cannot be alerted before it arrives).  The alert time is the arrival time
    of the episode occupying that step."""
    entry = np.searchsorted(ks, m, side='left')
    entry = np.maximum(entry, np.arange(1, T + 1))
    out = np.full(T, np.nan)
    ok = np.isfinite(m) & (entry <= T)
    out[ok] = first_ts_h[entry[ok] - 1]
    return out


def metrics(rej, tp, silent, first_inf, fired, ismal, first_ts_h, T, NMAL,
            alert_ts_h=None):
    """`alert_ts_h`, if given, replaces first_ts_h for the LATENCY fields only.

    online e-BH is an ARC procedure: a hypothesis rejected at the end may have arrived much
    earlier, so its alert reaches an analyst at the ENTRY time (the first t with k*_t >= m_i),
    not at the episode's own arrival.  Using arrival times there understates latency."""
    d = dict(rejections=int(rej), tp=int(tp), fp=int(rej - tp),
             fdp=float((rej - tp) / max(rej, 1)),                 # FDP := V/max(R,1)
             fdp_cond=(float((rej - tp) / rej) if rej else None),  # conditional on R > 0
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
    """Mean pairwise Jaccard over seed pairs.  This is a MEAN OF RATIOS; the analytic
    reference [D5c] is a ratio of expectations, and the two differ substantially when the
    per-episode rates are small, so both are reported and neither is asserted equal.

    Pairs in which BOTH alert sets are empty are EXCLUDED, not scored as 1.  Scoring them 1
    makes an arm that never fires report perfect reproducibility, which is the opposite of
    what the number is there to say.  The count of excluded pairs is returned."""
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


# ---------------------------------------------------------------------------------------
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

        # ---- evidence ----------------------------------------------------------------
        e_te, cal, NC, CEIL = H.evalues(s_cal, y_cal, s_te, k=K)
        M = NC + 1.0
        # G = #{c > s}, Etie = #{c == s}.  Consistent with h_stream.evalues, whose
        # K = 1 + #{c >= s} = 1 + G + Etie.
        G, Etie, lo = conformal_ranks(cal, s_te, NC)
        # tie G/Etie to what h_stream.evalues ACTUALLY returned, not merely to an algebraic
        # rearrangement of it: if evalues() drifted, the algebraic form would still pass
        assert np.array_equal(1 + (NC - lo), (1 + G + Etie).astype(np.int64)), "G/E vs K"
        assert np.array_equal(e_te, np.where((1 + G + Etie) <= K, CEIL, 0.0)), \
            "G/E vs evalues() full e-values (magnitude, not just the firing mask)"
        del lo

        # ---- episodes -----------------------------------------------------------------
        ep = H.build_episodes(e_te, y_te, ts_w, src_w, dst_w, bucket_s=BH * 3600)
        gid, order, T = ep["gid"], ep["order"], ep["T"]
        ismal, NMAL = ep["ismal"], ep["n_mal"]
        nsz_raw = np.bincount(gid, minlength=T).astype(np.float64)
        first_ts = np.full(T, np.iinfo(np.int64).max)
        np.minimum.at(first_ts, gid, ts_w)
        first_ts_h = (first_ts[order] - ts_w.min()) / 3.6e9        # hours into the window
        srt, starts, flow_m, rank_k, m_over_k, H_m = simes_index(gid, nsz_raw, n_te)
        assert len(starts) == T

        g1p, g0p = make_gamma("poly", T)
        g1u, g0u = make_gamma("uniform", T)
        # "uniform" is gamma_j = 1/T with T the REALISED episode count of this evaluation
        # window: horizon knowledge, i.e. an ORACLE, exactly as flagged in 03_FROZEN_CLAIMS
        # caveat C1 and labelled in section 4.20.  e-GAI's w1 = 1/T is oracle for the same
        # reason.  The gamma is kept identical to section 4.20 so the regression assertions
        # hold; only the label changes, and it travels with every number.
        GAMS = (("poly", g1p, g0p), ("uniform[ORACLE]", g1u, g0u))
        margin = M * W0 / T - 1.0

        # ---- benign tail validity, EXACTLY --------------------------------------------
        # The smoothed analogue of the section 4.31 benign firing ratio.  Nominal
        # P(p_u <= a) = a for a fixed level [D2c].  This is computed as the EXACT
        # expectation over the randomisation, E[1{p_u <= a}] = clip((a*M - G)/(1+E), 0, 1)
        # averaged over benign test flows [D2a], not from a single U draw: at levels near
        # 1/M the expected benign count is of order one, so a one-draw estimate would be
        # pure noise reported as a result (standing mistake 3).  Divided by the BENIGN
        # count, not by all test flows (standing mistake 10).
        lv = [(f"{int(c)}/M", c / M) for c in VALID_LEVELS] + \
             [(f"{a:g}", a) for a in VALID_ABS]
        nben = int(ben_te.sum())
        Gb, Eb = G[ben_te], Etie[ben_te]
        valid = {}
        for nm, a in lv:
            qb = np.clip((a * M - Gb) / (1.0 + Eb), 0.0, 1.0)
            meas = float(qb.mean())
            # Two very different dispersions.  sd_randomisation is exact but conditional on
            # the realised scores and calibration set -- it is the spread over U alone, and
            # at an integer-rank level it is 0 even though the count would move a great deal
            # under a different benign split.  sd_sampling is the crude binomial scale of
            # that second, much larger source, and is the one to quote when asking whether a
            # ratio is distinguishable from 1.
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

        # ---- arm registry --------------------------------------------------------------
        arms = {}

        def add(route, merge, proc, gname, res, lam=None):
            key = (route, merge, proc, gname, lam)
            arms.setdefault(key, []).append(res)

        # Structural feasibility ceilings for the two merges.  These are properties of the
        # merge and the realised group sizes, NOT of the observed p-values: taking
        # 1/min(P_ep) instead would set a parameter from the evaluation split (standing
        # mistake 4).  Bonferroni floor is min_t(m_t)/M; mean-p x2 floor is 2/M.
        # Split-INDEPENDENT structural ceilings.  Using M/min(nsz) would read the smallest
        # realised episode size off the evaluation window, which is an oracle; m >= 1 holds
        # by construction, so the bound below needs no knowledge of the split at all.
        #   Bonferroni  P >= m/M     >= 1/M   -> ceiling M
        #   Simes       P >= (m/m)/M  = 1/M   -> ceiling M
        #   Hommel      P >= H_m*m/M >= 1/M   -> ceiling M   (H_1 = 1)
        #   mean-p x2   P >= 2/M              -> ceiling M/2
        CEIL_BONF = M
        CEIL_MEANP = M / 2.0
        # Simes floor: an episode of ANY size with every flow at the conformal floor gives
        # min_k (m/k)(1/M) = 1/M, so the ceiling is M regardless of m.  Hommel multiplies
        # that by H_m, and H_m*P_simes is minimised at the SMALLEST episode (H_m is
        # increasing in m), not the largest.
        CEIL_SIMES = M
        CEIL_HOMMEL = M
        # h6_procs.Ctx.infeasible takes ONE scalar ceiling, so these are the most permissive
        # (largest) structural ceilings over the stream.  For Bonferroni and Hommel, whose
        # floor depends on the episode size, that makes the reported `silent` fraction a
        # LOWER BOUND for those two merges.  It is exact for the record's mean-e rule
        # (ceiling M for every episode, independent of m) and for Simes, so the rows
        # compared against section 4.20 are unaffected.  The shared module is not modified.

        def run_p_procs(route, merge, P_ep, seedtag):
            """LOND / LORD++ / SAFFRON / ADDIS on an episode p-value array (ordered)."""
            Ev = 1.0 / np.maximum(P_ep, TINY)
            if route != "discrete":
                ceil = np.inf                      # smoothed p has no floor: inf p_u = 0
            else:
                # structural floors: Bonferroni min_t(m_t)/M, mean-p 2/M, Simes min_t(m_t)/M
                # (attained at k = m), Hommel H_m times that
                ceil = {"bonf-p": CEIL_BONF, "mean-p": CEIL_MEANP,
                        "simes": CEIL_SIMES, "hommel": CEIL_HOMMEL}[merge]
            for gname, g1, g0 in GAMS:
                ctx = Ctx(Ev, ismal, ceil, alpha=A, w0=W0)
                f = np.zeros(T, bool)
                Pc = np.minimum(1.0, P_ep)
                r = run_lond_p(ctx, g1, Pc, fired=f)
                fe = np.zeros(T, bool)
                run_lond(ctx, g1, fired=fe)                # the e-form, for comparison only
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
            # ADDIS/SAFFRON index mechanics: the escape of F1 depends on these staying 0
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

        # ================= deterministic baselines ======================================
        # (1) the record's construction, reproducing section 4.20
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

        # (2) discrete controls under the smoothed merges
        p_d = (1.0 + G + Etie) / M
        EPD = episode_pvalues(p_d, gid, order, nsz_raw, starts, srt, m_over_k, H_m, T)
        sim_d = EPD["simes"]
        # Simes on the discrete two-point evidence is <= the record's mean-e + Markov rule,
        # with equality only where the minimum over k is attained at k = r.  Assert the
        # INEQUALITY and count the strict gaps.  np.isclose's default atol = 1e-8 would
        # swamp p-values of order 1e-6 and hide every strict gap, so the comparison is
        # relative-only.
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

        # ---- derivation-agreement setup -----------------------------------------------
        # The user-facing requirement: a simulation that disagrees with the derivation is a
        # bug.  So for a FIXED level a (no procedure state, hence exact independence across
        # episodes) predict each episode's rejection probability from t34a's closed form and
        # compare it against the measured randomisation frequency on THIS window's scores.
        #   Route A / Bonferroni [D4a,D4b]:  q_t = 1 - prod_i (1 - clip((a*M/m_t - G_i)/(1+E_i)))
        #   Route B / singleton  [D3e]:      q_t = clip((p*(a,lam)*M - G)/(1+E), 0, 1)
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
        # only flows with G < p*M can ever fire, so the check runs on that subset
        selB = np.flatnonzero(G <= max(CHECK_RANKS) + 2)
        qflow, obsAflow = {}, {}
        for pstar in PSTARS:
            q = np.clip((pstar * M - G[selB]) / (1.0 + Etie[selB]), 0.0, 1.0)
            qflow[pstar] = q
            obsAflow[pstar] = np.zeros(len(selB), dtype=np.int64)
            for lam in LAMS:
                qB_pred[(pstar, lam)] = q      # D3d: the two regions coincide at a_eq
                obsB[(pstar, lam)] = np.zeros(len(selB), dtype=np.int64)

        # ================= randomised routes ============================================
        idx_traj = {}
        for rs in range(NRAND):
            rng = np.random.default_rng(1_000_000 + 10_000 * rs + int(pos * 100) + dseed)
            U = np.maximum(rng.random(n_te), TINY)
            pu = smoothed_p(G, Etie, U, M)
            # ---- Route A ---------------------------------------------------------------
            EPS_ = episode_pvalues(pu, gid, order, nsz_raw, starts, srt, m_over_k, H_m, T)
            pmin = EPS_["pmin"]
            tr = run_p_procs("smoothA", "simes", EPS_["simes"], rs)
            idx_traj.setdefault("simes", []).append(tr)
            run_p_procs("smoothA", "hommel", EPS_["hommel"], rs)
            run_p_procs("smoothA", "bonf-p", EPS_["bonf"], rs)
            run_p_procs("smoothA", "mean-p", EPS_["meanp"], rs)
            # ---- derivation agreement, at fixed levels (no procedure state) -----------
            for a in CHECK_LEVELS:
                obsA[a] += (nsz_raw * pmin <= a)
            puB = pu[selB]
            for pstar in PSTARS:
                obsAflow[pstar] += (puB <= pstar)                       # D2a, per flow
                for lam in LAMS:
                    # the level whose Route-B rejection region is exactly p <= pstar
                    a_eq = pstar ** (1.0 - lam) / lam
                    obsB[(pstar, lam)] += (calibrate(puB, lam) >= 1.0 / a_eq)
            del puB
            # ---- Route B ---------------------------------------------------------------
            for lam in LAMS:
                e = calibrate(pu, lam)
                Evb = (np.bincount(gid, weights=e, minlength=T) / nsz_raw)[order]
                run_e_procs("smoothB", "mean-e", Evb, lam, np.inf)
                del e, Evb
            del U, pu, pmin, EPS_
            if rs == 0 or (rs + 1) % 25 == 0:
                print(f"  {tag}  randomisation seed {rs+1}/{NRAND}  "
                      f"[{time.time()-t0:.0f}s]")

        # ---- collapse the derivation-agreement check -----------------------------------
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

        # ---- collapse the arms ---------------------------------------------------------
        rng_j = np.random.default_rng(4242)
        for (route, merge, proc, gname, lam), reslist in arms.items():
            has_mask = all("alerts" in r for r in reslist)
            sets = [set(r["alerts"].tolist()) for r in reslist if "alerts" in r] \
                if has_mask else []
            jm, jsd, jne = jaccard(sets, rng=rng_j) if len(sets) > 1 else (None, None, 0)
            # per-attack-episode detection probability
            malidx = np.flatnonzero(ismal)
            if sets:
                cnt = np.zeros(T)
                for s in sets: cnt[list(s)] += 1
                pdet = cnt[malidx] / len(sets)
            else:
                pdet = np.array([])
            # analytic Jaccard reference [D5c], from the measured per-episode rates
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

# =======================================================================================
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
