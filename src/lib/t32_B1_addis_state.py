def main():
    import numpy as np, json, time
    from fractions import Fraction
    from pathlib import Path
    from scipy.special import zeta
    from scipy.stats import hypergeom, binom

    import h_stream as hs
    from h6_procs import Ctx, make_gamma, run_addis, run_lond

    Path("out").mkdir(exist_ok=True)
    t0 = time.time()

    POS = 0.85; K = 1; A = 0.05; W0 = 0.025; BUCKET = 2 * 3600
    LAM, TAU = 0.25, 0.5
    N_TARGETS = 200
    out = {"config": dict(pos=POS, k=K, alpha=A, w0=W0, bucket_s=BUCKET, lam=LAM, tau=TAU)}

    X, y, ts, src, dst = hs.load()
    N = len(y)
    i1, i2, i3 = hs.split_indices(N, POS)
    score = hs.fit_detector(X, y, i1, seed=0, kind="hgb", verbose=False)
    s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
    y_te = y[i2:i3]
    e_te, cal, NC, CEIL = hs.evalues(s_cal, y[i1:i2], s_te, k=K)
    ep = hs.build_episodes(e_te, y_te, ts[i2:i3], src[i2:i3], dst[i2:i3], BUCKET, "src-dst")
    T = ep["T"]; Ev = ep["Ev"]; ismal = ep["ismal"]
    ctx = Ctx(Ev, ismal, CEIL, alpha=A, w0=W0)
    FLOOR = 1.0 / CEIL
    print(f"  stream: T={T:,} episodes, {ep['n_mal']} malicious, |C|={NC:,}, CEIL={CEIL:,.0f}, "
          f"conformal floor 1/CEIL={FLOOR:.4e}  [{time.time()-t0:.0f}s]")

    g1p, g0p = make_gamma("poly", T)
    base_fired = np.zeros(T, bool)
    base_lvl = np.zeros(T)
    b_rej, b_tp, b_sil, b_first = run_addis(ctx, g0p, lam=LAM, tau_=TAU, fired=base_fired,
                                            levels=base_lvl)
    D_final = int(((ctx.Pv > LAM) & (ctx.Pv <= TAU)).sum())
    print(f"  ADDIS baseline (gamma ∝ j^-1.6): {b_rej} rejections, {b_tp} true, "
          f"silent {100*b_sil/T:.1f}%,  D_T = {D_final}")
    out["baseline"] = dict(rejections=int(b_rej), tp=int(b_tp), silent=float(b_sil / T),
                           recall=float(b_tp / ep["n_mal"]), D_final=D_final,
                           T=int(T), n_mal=int(ep["n_mal"]), NC=int(NC), CEIL=float(CEIL))

    print("\n" + "=" * 112)
    print("=" * 112)
    Z = float(zeta(1.6, 1))


    def addis_level(D, R, gam0, lag_indices=None):
        """The ADDIS level at index D with R prior rejections."""
        if lag_indices is None:
            lag_indices = [0] * R
        ah = W0 * gam0[min(D, len(gam0) - 1)]
        if R >= 1:
            i_ = D - lag_indices[0]
            if i_ >= 0: ah += (A - W0) * gam0[min(i_, len(gam0) - 1)]
        if R >= 2:
            for Dj in lag_indices[1:]:
                i_ = D - Dj
                if i_ >= 0: ah += A * gam0[min(i_, len(gam0) - 1)]
        return min(LAM, (TAU - LAM) * ah)


    def bstar(R, gam0):
        """Smallest D at which the level drops below the conformal floor, given R rejections"""
        D = 0
        while D < 10_000_000:
            if addis_level(D, R, gam0) < FLOOR:
                return D
            D += 1
        return None


    def bstar_closed(R):
        W = W0 if R == 0 else (W0 + (A - W0) + A * max(R - 1, 0))
        Q = ((TAU - LAM) * W * CEIL / Z) ** (1.0 / 1.6)
        return int(np.floor(Q - 1.0)) + 1


    gam0_big = np.concatenate([g0p, ((np.arange(len(g0p), 2_000_000) + 1.0) ** -1.6) / Z])
    rows = []
    print(f"  {'prior rejections R':>20} {'B* (numeric)':>14} {'B* (closed form)':>18} "
          f"{'level at B*-1':>15} {'floor':>12}")
    for R in (0, 1, 2, 10, 50, 152):
        bs = bstar(R, gam0_big); cf = bstar_closed(R)
        lv = addis_level(bs - 1, R, gam0_big) if bs else float('nan')
        rows.append(dict(R=R, bstar=bs, bstar_closed=cf, level_before=float(lv), floor=float(FLOOR)))
        print(f"  {R:>20} {bs:>14,} {cf:>18,} {lv:>15.4e} {FLOOR:>12.4e}")
    out["bstar"] = rows

    print("\n" + "=" * 112)
    print("B1b -- WHAT ONE PRECURSOR EPISODE COSTS")
    print("=" * 112)
    print("  An episode of n flows containing m ceiling-reaching flows has Ev = CEIL*m/n and")
    print("  p = min(1, 1/Ev), so  p in (lam, tau]  <=>  n in (lam*CEIL*m, tau*CEIL*m].")
    print("  The cheapest precursor uses m = 1.")
    n_lo = int(np.floor(LAM * CEIL)) + 1
    n_hi = int(np.floor(TAU * CEIL))
    print(f"\n  m = 1:  n in ({int(LAM*CEIL):,}, {n_hi:,}]  -> minimum {n_lo:,} flows per precursor")
    lvl0 = addis_level(0, 0, gam0_big)
    n_sup = int(np.floor(lvl0 * CEIL)) + 1
    print(f"\n  For contrast, the section 4.16 padding attack on the SAME episode: suppression")
    print(f"  needs only Ev < 1/alpha_t, i.e. n > alpha_t*CEIL*m.  At ADDIS's own opening level")
    print(f"  alpha_1 = {lvl0:.4e} that is n > {n_sup-1:,} flows for m = 1.")
    print(f"  Ratio of the two padding budgets = lambda/alpha_1 = {LAM/lvl0:,.1f}x.")
    out["precursor_cost"] = dict(n_min=n_lo, n_max=n_hi, window_width_ratio=TAU / LAM,
                                 addis_level_0=float(lvl0),
                                 n_suppress_one_episode=n_sup,
                                 last_size_still_rejected=n_sup - 1,
                                 ratio_state_to_suppress=float(LAM / lvl0))

    print("\n" + "=" * 112)
    print("B1c -- FRONT-LOADED ATTACK ON THE REAL STREAM (precursors before episode 1)")
    print("=" * 112)
    P_PRE = (LAM + TAU) / 2.0
    EV_PRE = 1.0 / P_PRE
    det0 = base_fired & ismal


    def run_attacked(B, inject_at=0):
        """Insert B precursor episodes (benign, p = P_PRE) at position `inject_at` in the"""
        Ev2 = np.concatenate([Ev[:inject_at], np.full(B, EV_PRE), Ev[inject_at:]])
        im2 = np.concatenate([ismal[:inject_at], np.zeros(B, bool), ismal[inject_at:]])
        c2 = Ctx(Ev2, im2, CEIL, alpha=A, w0=W0)
        _, g0 = make_gamma("poly", len(Ev2))
        f2 = np.zeros(len(Ev2), bool)
        rej, tp, sil, first = run_addis(c2, g0, lam=LAM, tau_=TAU, fired=f2)
        keep = np.ones(len(Ev2), bool); keep[inject_at:inject_at + B] = False
        return f2[keep], dict(rejections=int(rej), tp=int(tp), silent=float(sil / len(Ev2)),
                              first_infeasible=(int(first) if first else None))


    GRID = [0, 4, 8, 16, 32, 64, 128, 180, 200, 202, 203, 204, 208, 256, 512]
    sweep = []
    print(f"  {'B':>6} {'flows spent':>16} {'rejections':>11} {'true pos':>9} {'FDP':>7} "
          f"{'recall':>7} {'P(target found)':>16} {'silent':>8} {'first true det.':>16}")
    for B in GRID:
        fired, st = run_attacked(B)
        tp = int((fired & ismal).sum()); rej = int(fired.sum())
        keep_rate = float((fired & det0).sum() / max(det0.sum(), 1))
        ftd = int(np.argmax(fired & ismal) + 1) if (fired & ismal).any() else None
        sweep.append(dict(B=B, flows=B * n_lo, rejections=rej, tp=tp,
                          fdp=(float(1 - tp / rej) if rej else None),
                          recall=float(tp / ep["n_mal"]),
                          p_target_detected=keep_rate, silent=st["silent"],
                          first_true_detection_rank=ftd))
        print(f"  {B:>6} {B*n_lo:>16,} {rej:>11} {tp:>9} "
              f"{(('%.3f' % (1-tp/rej)) if rej else '  -  '):>7} {tp/ep['n_mal']:>7.3f} "
              f"{keep_rate:>16.3f} {100*st['silent']:>7.1f}% "
              f"{(format(ftd, ',') if ftd else 'never'):>16}")
    out["front_load_sweep"] = sweep
    b_kill = next((r["B"] for r in sweep if r["rejections"] == 0), None)
    print(f"\n  smallest B on the grid that silences ADDIS completely: "
          f"{b_kill if b_kill is not None else 'not reached'}  "
          f"(analytic B* = {out['bstar'][0]['bstar']:,})")

    print("\n" + "=" * 112)
    print("B1d -- PER-TARGET ATTACK: precursors injected immediately before the target episode")
    print("=" * 112)
    tgt_all = np.flatnonzero(det0)
    stride = max(1, len(tgt_all) // N_TARGETS)
    targets = tgt_all[::stride][:N_TARGETS]
    print(f"  {len(tgt_all)} episodes are detected without the attack; "
          f"{len(targets)} sampled by stride {stride}")


    def detected(B, tgt):
        fired, _ = run_attacked(B, inject_at=int(tgt))
        return bool(fired[tgt])


    per_target = []
    HI = 65536
    for tgt in targets:
        if not detected(0, tgt):
            continue
        lo, hi = 0, 1
        while hi <= HI and detected(hi, tgt):
            lo, hi = hi, hi * 4
        if hi > HI:
            per_target.append(dict(target=int(tgt), bstar=None)); continue
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if detected(mid, tgt): lo = mid
            else: hi = mid
        per_target.append(dict(target=int(tgt), bstar=int(hi),
                               rank_fraction=float(tgt / T),
                               flows=int(hi) * n_lo))
        print(f"    target rank {int(tgt):>6,} ({100*tgt/T:>5.1f}% into the stream): "
              f"B* = {hi:>5,}  = {hi*n_lo:>14,} flows")
    bs_vals = [r["bstar"] for r in per_target if r["bstar"] is not None]
    if bs_vals:
        print(f"\n  per-target B*: min {min(bs_vals):,}  median {int(np.median(bs_vals)):,}  "
              f"max {max(bs_vals):,}   over {len(bs_vals)} targets")
        print(f"  in flows:      min {min(bs_vals)*n_lo:,}  median "
              f"{int(np.median(bs_vals))*n_lo:,}  max {max(bs_vals)*n_lo:,}")
    out["per_target"] = dict(n_detected=int(len(tgt_all)), n_sampled=int(len(targets)),
                             stride=int(stride), results=per_target,
                             bstar_min=(min(bs_vals) if bs_vals else None),
                             bstar_median=(float(np.median(bs_vals)) if bs_vals else None),
                             bstar_max=(max(bs_vals) if bs_vals else None))

    print("\n" + "=" * 112)
    print("B1e -- ATTACKER KNOWLEDGE: white-box, grey-box, black-box")
    print("=" * 112)
    print("  WHITE-BOX -- knows lambda, tau, k, |C| and the controller state.")
    print(f"    Sets n = {n_lo:,} and m = 1.  Every precursor lands in (lambda, tau].")
    print(f"    Cost to permanent silence before the first rejection: "
          f"{out['bstar'][0]['bstar']:,} x {n_lo:,} = "
          f"{out['bstar'][0]['bstar']*n_lo:,} flows.")

    print("\n  GREY-BOX -- knows the procedure and its parameters, not |C| and not the state.")
    print("    The admissible group size is an interval (lam*CEIL, tau*CEIL], so aiming at its")
    print(f"    midpoint succeeds whenever the estimate of |C| is within a factor")
    print(f"    [{2*LAM/(LAM+TAU):.3f}, {2*TAU/(LAM+TAU):.3f}] of the truth "
          f"(a +/-{100*(2*TAU/(LAM+TAU)-1):.0f}% tolerance; the interval is tau/lam = "
          f"{TAU/LAM:.0f}x wide).")
    grey = []
    for rho in (0.5, 0.67, 0.8, 1.0, 1.25, 1.33, 2.0):
        n_try = int((LAM + TAU) / 2 * CEIL * rho)
        hit = bool(LAM * CEIL < n_try <= TAU * CEIL)
        grey.append(dict(cal_estimate_ratio=rho, n=n_try, lands_in_window=hit))
        print(f"      |C| estimated at {rho:>4.2f}x truth -> n = {n_try:>12,}  "
              f"{'lands in (lam,tau]' if hit else 'MISSES'}")
    print("    Not knowing the state R costs only over-provisioning: B*(R=152) = "
          f"{out['bstar'][-1]['bstar']:,} against B*(R=0) = {out['bstar'][0]['bstar']:,}, so a "
          f"grey-box attacker budgets {out['bstar'][-1]['bstar']/out['bstar'][0]['bstar']:.0f}x.")

    print("\n  BLACK-BOX -- no detector access; sends ordinary traffic of a chosen volume and")
    print("  takes whatever m the detector gives it.  m is then random, and the precursor works")
    print("  only if CEIL*m/n happens to land in [1/tau, 1/lam).")
    half = len(y_te) // 2
    ben_a = np.flatnonzero((y_te[:half] == 0))
    ben_b = np.flatnonzero((y_te[half:] == 0)) + half
    f_est = float((e_te[ben_a] > 0).mean())
    Nb = int(len(ben_b)); Mf = int((e_te[ben_b] > 0).sum())
    f_meas = Mf / Nb
    f_nom = K / (NC + 1.0)
    print(f"    benign flows: {len(ben_a):,} used to estimate the firing rate "
          f"({f_est:.3e}), {Nb:,} held out and used to price the attack "
          f"(rate {f_meas:.3e}, nominal {f_nom:.3e}, ratio {f_meas/f_nom:.1f}x)")
    bb = []
    print(f"\n    {'n':>12} {'P(hit) held-out':>17} {'P(hit) nominal':>16} "
          f"{'groups needed':>15} {'flows needed':>16}")
    for n_try in (n_lo, int(0.375 * CEIL), n_hi, 2 * n_hi, 10 * n_hi):
        m_lo = int(np.ceil(n_try / (TAU * CEIL)))
        m_hi_ = int(np.ceil(n_try / (LAM * CEIL))) - 1
        p_nom = (float(binom.cdf(m_hi_, n_try, f_nom) - binom.cdf(m_lo - 1, n_try, f_nom))
                 if m_hi_ >= m_lo else 0.0)
        if n_try > Nb:
            p_meas = float("nan")
        elif m_hi_ < m_lo:
            p_meas = 0.0
        else:
            p_meas = float(hypergeom.cdf(m_hi_, Nb, Mf, n_try)
                           - hypergeom.cdf(m_lo - 1, Nb, Mf, n_try))
        need = (out["bstar"][0]["bstar"] / p_meas) if (p_meas == p_meas and p_meas > 0) \
            else float("inf")
        bb.append(dict(n=n_try, m_range=[m_lo, m_hi_], p_hit_heldout=p_meas,
                       p_hit_nominal=p_nom, groups_needed=need,
                       flows_needed=(need * n_try if np.isfinite(need) else None),
                       pool_too_small=bool(n_try > Nb)))
        pm = "  pool < n" if n_try > Nb else (f"{p_meas:.3e}" if p_meas < 1e-4 else f"{p_meas:.4f}")
        gn = "infeasible" if not np.isfinite(need) else (f"{need:.3e}" if need > 1e6 else f"{need:,.0f}")
        fn = "-" if not np.isfinite(need) else (f"{need*n_try:.3e}" if need * n_try > 1e6
                                                else f"{need*n_try:,.0f}")
        print(f"    {n_try:>12,} {pm:>17} {p_nom:>16.4f} {gn:>15} {fn:>16}")
    out["knowledge"] = dict(grey=grey, black=bb, n_benign_heldout=Nb, n_fire_heldout=Mf,
                            f_estimated_first_half=f_est, f_heldout=float(f_meas),
                            f_nominal=float(f_nom))
    print("\n    The black-box attacker is priced by the SAME anti-conservatism that section 4.31")
    print("    diagnoses: at the measured firing rate the expected evidence of a large benign")
    print(f"    group is CEIL*f = {CEIL*f_meas:.1f}, far above 1/lambda = {1/LAM:.1f}, so an")
    print("    ordinary-looking group of the required size lands past the window, not inside it.")

    print("\n" + "=" * 112)
    print("B1f -- THE TWO ATTACK SURFACES, PRICED IN THE SAME UNITS")
    print("=" * 112)
    n_mal_ep = int(ep["n_mal"])
    mfire = ep["sum_e"] / CEIL
    det_m = mfire[det0]
    lv = base_lvl[det0]
    X_int = np.rint(CEIL * det_m).astype(np.int64)
    assert np.abs(CEIL * det_m - X_int).max() < 1e-6, "M*m is not integral"


    def least_n_gt(alpha_t, x):
        """Least integer n with n/x > alpha_t, in EXACT rational arithmetic."""
        q = Fraction.from_float(float(alpha_t)) * int(x)
        return q.numerator // q.denominator + 1


    n_need = np.array([least_n_gt(a, x) for a, x in zip(lv, X_int)], dtype=np.int64)
    _naive = (np.floor(lv * CEIL * det_m) + 1.0).astype(np.int64)
    _over = int((_naive != n_need).sum())
    if _over:
        print(f"    [exact n_need] {_over} of {len(n_need)} values differ from the float form "
              f"by rounding of alpha_t*M*m; the exact value is used.")
    pad_each = n_need - ep["nsz"][det0].astype(np.int64)
    if (pad_each < 1).any():
        raise RuntimeError(f"minimal pad below 1 (min {pad_each.min()}) -- level/stream desync; "
                           "D3a says a rejected episode always needs at least one pad flow")
    pad_each = pad_each.astype(float)
    per_ep_pad = float(np.median(pad_each)) if pad_each.size else 0.0
    total_pad = float(pad_each.sum())
    state_cost = out["bstar"][0]["bstar"] * n_lo
    print(f"  within-hypothesis padding (section 4.16/4.30), priced at ADDIS's own traced level")
    print(f"  (levels run {lv.min():.3e} .. {lv.max():.3e}, saturating at lambda = {LAM}):")
    print(f"    median additional flows to suppress one detected episode : {per_ep_pad:,.0f}")
    print(f"    total to suppress all {len(det_m)} detected episodes             : "
          f"{total_pad:,.0f} flows")
    print(f"  across-hypothesis state manipulation (this section):")
    print(f"    flows to silence the controller permanently             : {state_cost:,}")
    print(f"  break-even: state manipulation is cheaper once the attacker must hide more than")
    print(f"    {state_cost/max(per_ep_pad,1):,.0f} episodes.  This window contains {n_mal_ep}.")

    assert det_m.size and det_m.min() >= 1.0, "detected episode with no firing flow"
    sat = lv >= LAM
    p_after = n_need / X_int
    lands = (p_after > LAM) & (p_after <= TAU)
    print(f"\n  ADDIS caps its level at lambda = {LAM}, and the state window STARTS at lambda:")
    print(f"    detected episodes where the cap binds (alpha_t = lambda)      : "
          f"{int(sat.sum())} of {len(lv)}")
    print(f"    detected episodes whose CHEAPEST suppressing pad lands in (lam, tau]: "
          f"{int(lands.sum())} of {len(lv)}")
    print(f"    -> for those, suppressing the alert ALSO advances the spending index, so the")
    print(f"       two attack surfaces are one operation and the state attack is free.")

    rank_det = np.flatnonzero(det0).astype(np.int64)
    nsz_det = ep["nsz"][det0].astype(float)
    p_pre = ctx.Pv[det0]
    _X = CEIL * det_m
    assert len(rank_det) == len(lv) == len(det_m) == len(nsz_det) == len(p_after)

    assert np.allclose(det_m, np.round(det_m), rtol=0.0, atol=1e-6), \
        "m_fire not integral"
    assert det_m.min() >= 1.0, "detected episode with no firing flow"
    assert np.allclose(ep["Ev"][det0], _X / nsz_det, rtol=1e-12, atol=0.0), \
        "Ev identity broken"
    assert np.allclose(p_pre, np.minimum(1.0, nsz_det / _X), rtol=1e-12, atol=0.0), \
        "Pv identity broken"
    assert (p_pre <= lv + 1e-15).all(), "exported episode was not rejectable at its own level"
    _bad5 = [(int(x), float(a), int(n)) for a, x, n in zip(lv, X_int, n_need)
             if not (Fraction(int(n), int(x)) > Fraction.from_float(float(a))
                     and Fraction(int(n) - 1, int(x)) <= Fraction.from_float(float(a)))]
    assert not _bad5, f"n_need is not the least suppressing size: {_bad5[:3]}"
    pad_raw = n_need - nsz_det.astype(np.int64)
    assert (pad_raw >= 1).all(), f"minimal pad below 1 ({pad_raw.min()}) -- level/stream desync"
    assert np.array_equal(pad_each.astype(np.int64), pad_raw), "pad_each drifted from n_need-nsz"
    assert (p_after > lv).all(), "padded p did not clear the level"
    assert (p_after <= lv + 1.0 / _X + 1e-15).all(), "padded p outside the D4a bracket"
    _unsat_land = int(((~sat) & lands).sum())
    assert _unsat_land == 0, (f"{_unsat_land} unsaturated landers: D5b allows them, but the D7a "
                              f"median split and the sat==lands reading both need zero")
    assert (_X >= 1.0 / (TAU - LAM)).all(), "D5a precondition M*m >= 1/(tau-lam) fails"
    assert not (sat & ~lands).any(), "saturated episode failed to land -- D5a violated"

    agg_sat = int(sat.sum()); agg_lands = int(lands.sum()); agg_med = float(np.median(p_after))
    per_ep = [dict(rank=int(r), m_fire=int(round(mf)), nsz=int(nz), alpha_t=float(a),
                   p_pre=float(pp), n_need=int(nn), pad=int(pd), p_after=float(pa),
                   saturated=bool(sa), lands_in_window=bool(ld))
              for r, mf, nz, a, pp, nn, pd, pa, sa, ld
              in zip(rank_det, det_m, nsz_det, lv, p_pre, n_need, pad_each, p_after, sat, lands)]
    assert sum(d["saturated"] for d in per_ep) == agg_sat
    assert sum(d["lands_in_window"] for d in per_ep) == agg_lands
    assert float(np.median([d["p_after"] for d in per_ep])) == agg_med
    _pa = np.asarray([d["p_after"] for d in per_ep])
    _sa = np.asarray([d["saturated"] for d in per_ep])
    assert (_pa[~_sa] <= LAM).all() and (_pa[_sa] > LAM).all(), "D5 split of p_after broken"
    _exc = np.sort(_pa[_sa] - LAM)
    _n = len(_pa); _u = int((~_sa).sum()); _h = _n // 2
    if _n % 2 == 1:
        _want_med = LAM + _exc[_h - _u]
    else:
        _want_med = LAM + 0.5 * (_exc[_h - 1 - _u] + _exc[_h - _u])
    assert agg_med == _want_med, "median does not match the D7a order statistic"

    out["coincidence"] = dict(n_detected=int(len(lv)), n_level_saturated=agg_sat,
                              n_minimal_pad_lands_in_window=agg_lands,
                              median_p_after_minimal_pad=agg_med,
                              population="true detections (base_fired & ismal)",
                              n_rejections_all=int(base_fired.sum()),
                              n_false_positive_alerts=int((base_fired & ~ismal).sum()),
                              M=float(CEIL), lam=LAM, tau=TAU,
                              floor_width=float(1.0 / CEIL),
                              d5a_threshold=float(1.0 / (TAU - LAM)),
                              min_M_times_m=float(_X.min()),
                              median_m_fire=float(np.median(det_m)),
                              median_excess_over_lam=float(agg_med - LAM),
                              n_unsaturated_landing=int((~sat & lands).sum()),
                              per_episode=per_ep)
    print(f"\n  E11 export: {len(per_ep)} per-episode rows "
          f"(rank, m_fire, nsz, alpha_t, p_pre, n_need, pad, p_after, saturated, lands).")
    print(f"    all ten D6 identities asserted;  min M*m = {_X.min():,.0f} against the D5a")
    print(f"    threshold 1/(tau-lam) = {1.0/(TAU-LAM):.0f}, a margin of "
          f"{_X.min()*(TAU-LAM):,.0f}x -- so saturated => lands is FORCED, not observed.")
    print(f"    unsaturated episodes that land: {int((~sat & lands).sum())} "
          f"(D5b allows these only within 1/M = {1.0/CEIL:.3e} of lam)")
    out["surfaces"] = dict(median_pad_per_episode=per_ep_pad,
                           level_min=float(lv.min()), level_max=float(lv.max()),
                           n_detected=int(len(det_m)), total_pad_all=float(total_pad),
                           state_attack_flows=int(state_cost),
                           break_even_episodes=float(state_cost / max(per_ep_pad, 1)),
                           episodes_in_window=n_mal_ep)

    print("\n" + "=" * 112)
    print("B1g -- SENSITIVITY: which parameters price the attack")
    print("=" * 112)
    sens = []
    print(f"  {'lambda':>8} {'tau':>6} {'B*':>8} {'n per precursor':>17} {'total flows':>16} "
          f"{'window width':>13}")
    for lam_, tau_ in ((0.05, 0.5), (0.10, 0.5), (0.25, 0.5), (0.25, 0.9), (0.4, 0.5)):
        W = W0
        bs = int(np.floor(((tau_ - lam_) * W * CEIL / Z) ** (1.0 / 1.6) - 1.0)) + 1
        npc = int(np.floor(lam_ * CEIL)) + 1
        sens.append(dict(lam=lam_, tau=tau_, bstar=bs, n_per=npc, total=bs * npc,
                         width=tau_ / lam_))
        print(f"  {lam_:>8.2f} {tau_:>6.2f} {bs:>8,} {npc:>17,} {bs*npc:>16,} "
              f"{tau_/lam_:>12.1f}x")
    print("\n  Total cost scales as  lambda * |C| * [(tau-lam) w0 |C|]^0.625 / k^1.625, so it is")
    print("  super-linear in the calibration size and falls fast in k -- but every k > 1 is")
    print("  already infeasible (F14), so the attacker cannot reach the cheap regime.")
    scal = []
    for c in (1e4, 1e5, 1e6, CEIL, 1e7):
        bs = int(np.floor(((TAU - LAM) * W0 * c / Z) ** (1.0 / 1.6) - 1.0)) + 1
        npc = int(np.floor(LAM * c)) + 1
        scal.append(dict(CEIL=float(c), bstar=bs, n_per=npc, total=bs * npc))
        print(f"    |C|+1 = {c:>12,.0f}:  B* = {bs:>6,}   n = {npc:>12,}   total = {bs*npc:>16,}")
    out["sensitivity"] = dict(lam_tau=sens, ceiling=scal)

    json.dump(out, open("out/t32_B1.json", "w"), indent=1, allow_nan=True, default=str)
    print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t32_B1.json")

    return out


if __name__ == "__main__":
    main()
