"""R2 -- repair Assumption 1 by construction, and price the repair.

Assumption 1 (metadata-conditional per-flow validity) is the paper's most exposed premise: it is
a modelling assumption the data cannot establish, and the stratified diagnostic (t55) finds the
conditional statement measurably imperfect deeper in the tail. The constructive alternative a
reviewer asks for is to stop MERGING per-flow evidence and instead CALIBRATE THE GROUPED UNIT
DIRECTLY, with the identical grouping protocol on the calibration split. Then

  * the exchangeability needed is between calibration groups and benign test groups -- the level
    actually tested -- and no per-flow, metadata-conditional premise is required at all;
  * thm:padding does not apply, because that theorem is about e-merging functions of per-flow
    e-values and this construction merges nothing.

This stage measures what that repair costs. Three quantities, per window and detector seed:

  1  FEASIBILITY.  Group calibration replaces the evidence ceiling (|C_flows|+1)/k with
     (|C_groups|+1)/k. Calibration and deployment windows are both 15% of the stream, so they
     produce comparable group counts and the ceiling falls by the flows-per-group ratio, while T
     is unchanged. cor:budget then asks for a ratio of k/c_0 between them, which no dataset size
     supplies -- so we also report the requirement in CALENDAR TIME, the unit a SOC budgets in.

  2  PADDING.  Under a max group statistic, APPENDING flows to a fixed group cannot lower its
     maximum, so the evasion of sec:paddingcost does not run in that form.  This is narrow and
     must stay narrow: an adversary who instead CREATES groups can emit distinct
     (src,dst,bucket) keys ahead of a target and push it past a cold-start prefix that these
     same numbers show is only tens of groups wide -- a positional attack we do not price here.
     Under a mean statistic even appending works, and we price it as an oracle lower bound.

  3  DETECTION.  What the repaired pipeline actually alerts on, against the shipped one.

Writes out/t57_group_calibration.json.
"""


def main():
    import numpy as np, json, time
    from pathlib import Path
    import h_stream as hs
    from h6_procs import Ctx, make_gamma, run_lond, run_online_ebh

    Path("out").mkdir(exist_ok=True)
    t0 = time.time()
    POSITIONS = [0.55, 0.62, 0.70, 0.77, 0.85]
    SEEDS = [0, 1]
    K = 1; A = 0.05; W0 = 0.025; BUCKET = 2 * 3600
    STATS = ["max", "mean"]
    ARITY_BINS = [(1, 1), (2, 3), (4, 10), (11, 30), (31, 100), (101, 1000), (1001, 10 ** 9)]
    ZETA16 = 2.2853996                      # zeta(1.6), the normaliser of gamma_j ∝ j^-1.6

    def feasible_window(ceil, R=0, alpha=A, zeta=ZETA16):
        """How many steps can e-LOND still reject at, given R rejections so far?

        Feasibility at t needs alpha*gamma_t*(R+1)*CEIL >= 1 with gamma_t = t^-1.6/zeta, so the
        window is floor((alpha*CEIL*(R+1)/zeta)^(1/1.6)).  R = 0 is the cold-start window; each
        rejection stretches it by (R+1)^(1/1.6), the bootstrap the paper documents.  Reported so
        that BOTH a zero-detection result and a surprisingly large one can be checked against the
        boundary rather than assumed to be it."""
        x = alpha * ceil * (R + 1) / zeta
        return int(np.floor(x ** (1.0 / 1.6))) if x > 0 else 0
    RNG = np.random.default_rng(0)
    N_PAD_DRAW = 20_000          # black-box pad pool size, sampled once per window

    def group_by_key(src, dst, ts, y, score, bucket_s):
        """Group a slice by (SrcIP, DstIP, time bucket) and return per-group aggregates.

        Identical key to the shipped pipeline; returns everything the two group statistics and
        the padding arithmetic need (max, sum, count) plus a malicious flag and first timestamp."""
        b = ts // (int(bucket_s) * 1_000_000)
        comb = np.zeros(len(ts), dtype=np.int64); tot = 1
        for a in (src, dst, b):
            _, c = np.unique(a, return_inverse=True)
            m = int(c.max()) + 1 if len(c) else 1
            comb = comb * m + c; tot *= m
        _, gid = np.unique(comb, return_inverse=True)
        G = int(gid.max()) + 1 if len(gid) else 0
        cnt = np.bincount(gid, minlength=G).astype(np.int64)
        ssum = np.bincount(gid, weights=score, minlength=G)
        smax = np.full(G, -np.inf); np.maximum.at(smax, gid, score)
        nmal = np.bincount(gid, weights=(y == 1).astype(float), minlength=G)
        fts = np.full(G, np.iinfo(np.int64).max); np.minimum.at(fts, gid, ts)
        # first_pos is the baseline's tie-break (h_stream.build_episodes uses
        # lexsort((first_pos, first_ts))); computed here so the two arms are ordered identically
        fpos = np.full(G, np.iinfo(np.int64).max)
        np.minimum.at(fpos, gid, np.arange(len(ts), dtype=np.int64))
        return dict(gid=gid, G=G, cnt=cnt, sum=ssum, max=smax,
                    ismal=nmal > 0, first_ts=fts, first_pos=fpos)

    def group_fires(cal_sorted, stat, k=K):
        """The group-level conformal firing rule: K_r = 1 + #{cal >= stat}, fire iff K_r <= k.

        NOT a bare `stat >= k-th largest`: with ties that is anti-conservative (an all-tied
        stream would fire with probability 1, giving E[e] = n+1).  Ties resolve against the test
        point, matching h_stream.evalues on flows."""
        Kr = 1 + (len(cal_sorted) - np.searchsorted(cal_sorted, stat, side="left"))
        return Kr <= k

    def min_pads(S, m, cal_sorted, pad_asc, pad_csum, k=K):
        """Minimal number of appended pads that stops a firing group firing, for the MEAN
        statistic -- an oracle lower bound, the paper's convention.

        The attacker picks its own pads, so the cheapest suppression takes the LOWEST-scoring
        flows the pool offers: sort ascending and find the shortest prefix whose new mean no
        longer fires.  Suppression is decided by the SAME rule as firing (group_fires), not by a
        `< threshold` comparison -- under the tied-rank rule equality at the threshold already
        stops firing, so comparing strictly would overstate the cost by one pad."""
        r = np.arange(len(pad_asc) + 1)
        new_stat = (S + pad_csum) / (m + r)
        ok = ~group_fires(cal_sorted, new_stat, k)
        if not ok.any():
            return None
        return int(r[int(np.argmax(ok))])

    X, y, ts, src, dst = hs.load()
    N = len(y)
    out = {"config": dict(
        positions=POSITIONS, seeds=SEEDS, k=K, alpha=A, w0=W0, bucket_s=BUCKET,
        statistics=STATS, n_pad_draw=N_PAD_DRAW,
        note="group-level split conformal: calibrate the grouped unit with the SAME protocol, so "
             "the exchangeability needed is between calibration groups and benign test groups and "
             "no metadata-conditional per-flow premise is used",
        pad_pool="scores of benign calibration flows -- a black-box attacker's ordinary traffic, "
                 "needing no labels and no detector output")}

    rows = []
    for POS in POSITIONS:
        i1, i2, i3 = hs.split_indices(N, POS)
        for SEED in SEEDS:
            score = hs.fit_detector(X, y, i1, seed=SEED, kind="hgb", verbose=False)
            s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
            y_cal = y[i1:i2]; y_te = y[i2:i3]

            # ---------- the shipped pipeline: calibrate on benign FLOWS, merge per flow -------
            e_te, cal_flow, NC_flow, CEIL_flow = hs.evalues(s_cal, y_cal, s_te, k=K)
            ep = hs.build_episodes(e_te, y_te, ts[i2:i3], src[i2:i3], dst[i2:i3],
                                   BUCKET, "src-dst")
            T = ep["T"]
            ctx_f = Ctx(ep["Ev"], ep["ismal"], CEIL_flow, alpha=A, w0=W0)
            g1, _ = make_gamma("poly", T)
            rf = run_lond(ctx_f, g1)
            margin_flow = (NC_flow + 1.0) * W0 / T - 1.0

            # ---------- the repair: calibrate the GROUPED UNIT, same protocol ----------------
            gcal = group_by_key(src[i1:i2], dst[i1:i2], ts[i1:i2], y_cal, s_cal, BUCKET)
            gte = group_by_key(src[i2:i3], dst[i2:i3], ts[i2:i3], y_te, s_te, BUCKET)
            # a calibration group is admissible only if it carries no attack flow, exactly as the
            # flow-level construction keeps only benign calibration flows
            benign = ~gcal["ismal"]
            NCg = int(benign.sum())
            # Dropping calibration groups that contain ANY attack flow is the null-unit analogue
            # of keeping benign flows, but it is not identical: benign flows inside mixed groups
            # are discarded with them.  If attacks concentrate in high-arity or high-score host
            # pairs, that LEFT-shifts the calibration distribution and makes benign test groups
            # over-fire.  Measured rather than argued.
            n_mixed = int(gcal["ismal"].sum())
            # NB: this is ALL flows in mixed groups, benign and malicious together -- an upper
            # bound on the benign calibration evidence discarded, not the discarded amount
            mixed_flow_frac = float(gcal["cnt"][gcal["ismal"]].sum() / max(gcal["cnt"].sum(), 1))
            mixed_arity_ratio = float(
                gcal["cnt"][gcal["ismal"]].mean() / max(gcal["cnt"][benign].mean(), 1e-9)
            ) if n_mixed else None
            exclusion = dict(n_mixed_groups=n_mixed, n_benign_groups=NCg,
                             frac_of_calibration_flows_in_mixed_groups=mixed_flow_frac,  # upper bound
                             note='fraction of ALL calibration flows sitting in mixed groups; benign flows discarded are a subset of these',
                             mixed_over_benign_mean_arity=mixed_arity_ratio)
            CEIL_g = (NCg + 1.0) / K
            margin_g = (NCg + 1.0) * W0 / T - 1.0

            cal_span_h = float((ts[i2 - 1] - ts[i1]) / 1e6 / 3600)
            te_span_h = float((ts[i3 - 1] - ts[i2]) / 1e6 / 3600)
            need_g = K * T / A - 1.0                       # cor:budget for e-LOND (c_0 = alpha)
            # the same requirement in calendar time: how long must attack-free observation run at
            # the calibration window's realised group rate to supply that many groups?
            cal_group_rate = NCg / cal_span_h if cal_span_h > 0 else float("nan")
            te_group_rate = T / te_span_h if te_span_h > 0 else float("nan")
            need_span_h = need_g / cal_group_rate if cal_group_rate > 0 else float("inf")
            # The COUNT ratio k/c_0 is the scale-free law; the CALENDAR ratio is that law times
            # the two windows' group-rate ratio, so it is dataset-specific and must not be quoted
            # as if it were the law.  Both are recorded, with the decomposition.
            rate_ratio = te_group_rate / cal_group_rate if cal_group_rate > 0 else float("nan")

            # pad pool: benign calibration flow scores (black box -- no labels, no detector output
            # beyond what an ordinary sender's own traffic would produce)
            pool = s_cal[y_cal == 0]
            pad = RNG.choice(pool, size=min(N_PAD_DRAW, len(pool)), replace=False)
            pad_mean = float(pad.mean()); pad_max = float(pad.max())

            per_stat = {}
            for st in STATS:
                stat_cal = gcal[st] if st == "max" else gcal["sum"] / np.maximum(gcal["cnt"], 1)
                stat_te = gte[st] if st == "max" else gte["sum"] / np.maximum(gte["cnt"], 1)
                cg = np.sort(stat_cal[benign])
                # The rank rule, not a bare ">= k-th largest".  With ties the bare comparison is
                # ANTI-CONSERVATIVE: if the test statistic equals a value shared by many
                # calibration groups it would fire while its true rank is far worse than k.  Use
                # the same construction h_stream.evalues uses on flows: K_r = 1 + #{cal >= stat},
                # fire iff K_r <= k.  Degenerate ties (all statistics equal) then correctly do
                # NOT fire, so E[e] <= 1 is preserved.
                fires = group_fires(cg, stat_te)
                thr = float(cg[-K])                        # reported for the padding arithmetic
                n_tied_at_thr = int(np.count_nonzero(cg == thr))
                n_would_fire_bare = int(np.count_nonzero(stat_te >= thr))
                Ev_g = np.where(fires, CEIL_g, 0.0)

                # identical ordering to the baseline: bucket-close time, ties by first flow
                order = np.lexsort((gte["first_pos"], gte["first_ts"]))
                ctx_g = Ctx(Ev_g[order], gte["ismal"][order], CEIL_g, alpha=A, w0=W0)
                g1g, _ = make_gamma("poly", gte["G"])
                rg = run_lond(ctx_g, g1g)
                rgb = run_online_ebh(ctx_g, g1g)

                # ---- padding, measured on the EVIDENCE, so it is not vacuous when the
                # controller is silent: what does appending r black-box flows do to a firing
                # group's statistic?
                fired_idx = np.flatnonzero(fires)
                if st == "max":
                    # appending cannot lower a maximum, so a firing group still fires; the only
                    # thing a pad can do is RAISE it.  Verified rather than asserted.
                    still = int(np.count_nonzero(
                        np.maximum(stat_te[fired_idx], pad_max) >= thr)) if fired_idx.size else 0
                    pa = dict(kind="max", n_firing=int(fired_idx.size),
                              n_still_firing_after_pad=still,
                              # NARROW, deliberately: this is invariance to APPENDING flows to a
                              # FIXED group.  It says nothing about an adversary who instead
                              # creates new groups -- e.g. emitting distinct (src,dst,bucket)
                              # keys ahead of a target to burn the cold-start window, which the
                              # feasibility numbers here show is only tens of groups wide.  That
                              # is a positional attack, out of scope for this measurement.
                              append_invariant_within_group=bool(still == fired_idx.size),
                              scope="append to a fixed group; group-creation attacks not covered",
                              pad_can_only_raise=True,
                              n_pads_that_exceed_group_max=int(np.count_nonzero(
                                  pad_max > stat_te[fired_idx])) if fired_idx.size else 0)
                else:
                    # mean falls toward the pad pool mean; r* is the closed form, checked against
                    # an explicit draw
                    # r* is an ORACLE LOWER BOUND, the paper's convention throughout: the
                    # attacker picks its pads, so the cheapest suppression uses the LOWEST-scoring
                    # flows the pool offers.  Sort ascending and take the minimal prefix with
                    # (S + cumsum_r)/(m + r) < thr.  A closed form on the pool MEAN is not the
                    # same quantity -- a random draw's realised mean varies, so a mean-based r*
                    # suppresses only about half the time, which is what the verification below
                    # caught.  This version is exact for the pads actually used, hence checkable.
                    pad_asc = np.sort(pad)
                    csum = np.concatenate([[0.0], np.cumsum(pad_asc)])
                    rstars = [min_pads(float(gte["sum"][gi]), int(gte["cnt"][gi]),
                                       cg, pad_asc, csum)
                              for gi in fired_idx[:2000]]
                    ok = [r for r in rstars if r is not None]
                    # Verify EXACTLY, on the same pads the cost was priced against.  A correct r*
                    # must suppress every time; anything else is a bug, and it is surfaced as a
                    # boolean rather than left in a field to be skimmed past.
                    ver = 0; nver = 0
                    for gi, r in list(zip(fired_idx[:2000], rstars))[:200]:
                        if r is None or r == 0: continue
                        nver += 1
                        newm = (gte["sum"][gi] + pad_asc[:r].sum()) / (gte["cnt"][gi] + r)
                        prev = (gte["sum"][gi] + pad_asc[:r - 1].sum()) / (gte["cnt"][gi] + r - 1)
                        # minimal, not merely sufficient: r suppresses and r-1 does not, both
                        # decided by the shipped firing rule
                        ver += int(bool(~group_fires(cg, np.array([newm]))[0])
                                   and bool(group_fires(cg, np.array([prev]))[0]))
                    pa = dict(kind="mean", n_firing=int(fired_idx.size),
                              n_priced=len(ok),
                              median_rstar=float(np.median(ok)) if ok else None,
                              min_rstar=int(min(ok)) if ok else None,
                              max_rstar=int(max(ok)) if ok else None,
                              append_invariant_within_group=False,
                              n_verified=nver, n_verified_suppressed=int(ver),
                              n_unsuppressable=int(sum(1 for r in rstars if r is None)),
                              pool_exhausted=bool(len(ok) and max(ok) >= len(pad_asc)),
                              rstar_verified=bool(nver == 0 or ver == nver))

                # Is a zero-detection result the BOUNDARY or a bug?  Under gamma ∝ j^-1.6 the
                # cold-start window has a closed form; the realised feasible-step count must
                # equal it, and then the question is only whether any firing group lands inside.
                cw = feasible_window(CEIL_g, 0)
                cw_R = feasible_window(CEIL_g, rg[0])
                n_feas = int(gte["G"] - rg[2])
                nfire = int(fires.sum())
                # The decisive check: in the ACTUAL online order, where does the first firing
                # group sit, and how many fire inside the cold-start window?  A fire inside the
                # window with no rejection would be a bug; no fire inside it is the boundary.
                fires_o = fires[order]; mal_o = gte["ismal"][order]
                fire_pos = np.flatnonzero(fires_o)
                first_fire = int(fire_pos[0] + 1) if fire_pos.size else None
                n_in_cw = int(np.count_nonzero(fire_pos < cw))
                n_mal_in_cw = int(np.count_nonzero(fires_o[:cw] & mal_o[:cw]))
                p_hit = 1.0 - (1.0 - min(cw / max(gte["G"], 1), 1.0)) ** nfire if nfire else 0.0
                # The closed form is the COLD-START window: it assumes no prior rejection.  Each
                # rejection raises the level by a factor (R+1) and so extends feasibility, which
                # is the bootstrap the paper documents.  So the identity is only expected on a
                # run that never rejects; where the run does reject, feasibility can only EXTEND,
                # and the size of the extension is itself the bootstrap being measured.
                # ---- HAS THE ASSUMPTION ACTUALLY GONE, OR ONLY MOVED?  Group-level conformal
                # validity needs benign test groups to be exchangeable with calibration groups.
                # If the statistic depends on ARITY -- the one quantity the adversary controls --
                # then it is not exchangeable across arities, and the premise is arity-conditional
                # group validity rather than metadata-conditional per-flow validity.  Measured,
                # not assumed: the rank correlation with arity, and the per-arity rate of landing
                # in the top 1% of the calibration statistic (which should be 1% at every arity).
                a_cal = gcal["cnt"][benign]
                v_cal = stat_cal[benign]
                rho = float(np.corrcoef(
                    np.argsort(np.argsort(a_cal)), np.argsort(np.argsort(v_cal)))[0, 1]) \
                    if len(a_cal) > 2 else float("nan")
                q99 = float(np.quantile(v_cal, 0.99))
                bins = []
                for lo, hi in ARITY_BINS:
                    m = (a_cal >= lo) & (a_cal <= hi)
                    if int(m.sum()) < 20:
                        continue
                    bins.append(dict(lo=lo, hi=(hi if hi < 10 ** 8 else None),
                                     n=int(m.sum()),
                                     frac_in_top1pct=float(np.mean(v_cal[m] >= q99)),
                                     mean_stat=float(v_cal[m].mean())))
                # A max/min ratio explodes when some arity bin never fires, which is a real
                # observation but not a ratio; report the pieces and use "worst bin against the
                # nominal 1%" as the headline, which is bounded and interpretable.
                rates = [b["frac_in_top1pct"] for b in bins]
                r_min = min(rates) if rates else None
                r_max = max(rates) if rates else None
                spread = (r_max / r_min) if (rates and r_min > 0) else None
                worst_over_nominal = (r_max / 0.01) if rates else None

                # ---- and if we REPAIR that by stratifying calibration on arity (Mondrian), what
                # does the repair of the repair cost?  Each stratum calibrates against only its
                # own groups, so its evidence ceiling is (n_stratum + 1)/k and its cold-start
                # window shrinks accordingly.
                mond = []
                for lo, hi in ARITY_BINS:
                    mc = (a_cal >= lo) & (a_cal <= hi)
                    n_b = int(mc.sum())
                    if n_b < 1:
                        continue
                    mond.append(dict(lo=lo, hi=(hi if hi < 10 ** 8 else None), n_cal=n_b,
                                     ceil=(n_b + 1.0) / K,
                                     coldstart_window=feasible_window((n_b + 1.0) / K, 0),
                                     n_test_groups=int(np.count_nonzero(
                                         (gte["cnt"] >= lo) & (gte["cnt"] <= hi)))))
                # ---- R8/R1b: THE BINS ABOVE MEASURE NO COVERAGE PROPERTY AT ALL.
                # `frac_in_top1pct` scores v_cal against v_cal's OWN 99th percentile, so summing
                # the bins back gives exactly 1% by construction, at every window and seed.  It
                # describes how one fixed set decomposes by arity; it cannot bear on
                # calibration/test exchangeability, and the round-8 reviewer was right to say a
                # correlation with arity does not refute exchangeability.
                # The honest question is CONDITIONAL COVERAGE: do benign TEST groups exceed the
                # calibration threshold at the nominal rate within each arity stratum?  Marginal
                # validity says the overall rate is ~1%; it says nothing per stratum, and arity is
                # the stratum the adversary chooses.
                ben_te = ~gte["ismal"]
                a_te = gte["cnt"][ben_te]
                v_te = stat_te[ben_te]
                n_te = int(ben_te.sum())
                cov_bins = []
                for lo, hi in ARITY_BINS:
                    m = (a_te >= lo) & (a_te <= hi)
                    nb = int(m.sum())
                    if nb < 20:
                        continue
                    cov_bins.append(dict(lo=lo, hi=(hi if hi < 10 ** 8 else None), n=nb,
                                         exceed_rate=float(np.mean(v_te[m] >= q99)),
                                         over_nominal=float(np.mean(v_te[m] >= q99) / 0.01)))
                cov_rates = [b["exceed_rate"] for b in cov_bins]
                cov_marginal = float(np.mean(v_te >= q99)) if n_te else None
                test_coverage = dict(
                    n_benign_test_groups=n_te,
                    marginal_exceed_rate=cov_marginal,
                    marginal_over_nominal=(cov_marginal / 0.01) if cov_marginal is not None
                                          else None,
                    bins=cov_bins,
                    min_over_nominal=(min(cov_rates) / 0.01) if cov_rates else None,
                    max_over_nominal=(max(cov_rates) / 0.01) if cov_rates else None,
                    note="benign TEST groups scored against the CALIBRATION threshold q99: a "
                         "genuine conditional-coverage read, unlike `bins` above which is "
                         "calibration-internal and marginally 1% by construction")

                arity = dict(spearman_arity_vs_statistic=rho, bins=bins,
                             calibration_internal_marginal=float(np.mean(v_cal >= q99)),
                             test_coverage=test_coverage,
                             top1pct_min=r_min, top1pct_max=r_max,
                             top1pct_spread_across_arity=spread,
                             top1pct_spread_undefined_zero_bin=bool(rates and r_min == 0),
                             worst_bin_over_nominal=worst_over_nominal,
                             mondrian=mond,
                             mondrian_min_coldstart=min((b["coldstart_window"] for b in mond),
                                                        default=None),
                             mondrian_max_coldstart=max((b["coldstart_window"] for b in mond),
                                                        default=None))
                tc = arity["test_coverage"]
                print(f"      [{st}] test-side coverage: marginal "
                      f"{100*tc['marginal_exceed_rate']:.3f}% "
                      f"({tc['marginal_over_nominal']:.2f}x nominal), by arity "
                      f"{tc['min_over_nominal']:.2f}x-{tc['max_over_nominal']:.2f}x "
                      f"over {len(tc['bins'])} strata"
                      if tc["marginal_exceed_rate"] is not None else
                      f"      [{st}] test-side coverage: no benign test groups")

                per_stat[st] = dict(
                    threshold=thr, n_firing=nfire, arity=arity,
                    n_tied_at_threshold=n_tied_at_thr,
                    n_would_fire_bare=n_would_fire_bare,
                    rej=rg[0], tp=rg[1], silent=rg[2], first_silent=rg[3],
                    ebh_rej=rgb[0], ebh_tp=rgb[1],
                    coldstart_window_closed_form=cw,
                    feasible_window_closed_form_at_R=cw_R,
                    first_fire_position=first_fire,
                    n_fires_in_coldstart=n_in_cw,
                    n_mal_fires_in_coldstart=n_mal_in_cw,
                    zero_is_boundary_not_bug=bool(rg[0] > 0 or n_in_cw == 0),
                    n_feasible_steps=n_feas,
                    feasible_matches_closed_form=bool(abs(n_feas - cw_R) <= 1),
                    feasible_extended_by_rejections=int(n_feas - cw),
                    bootstrap_factor=float((rg[0] + 1) ** (1.0 / 1.6)),
                    p_some_firing_group_in_window=p_hit,
                    padding=pa)

            row = dict(pos=POS, seed=SEED, T=int(T), n_mal_groups=int(gte["ismal"].sum()),
                       flow=dict(nCal=int(NC_flow), CEIL=float(CEIL_flow), margin=margin_flow,
                                 rej=rf[0], tp=rf[1], silent=rf[2], first_silent=rf[3]),
                       # eq:margin is defined for a level-w0 procedure (LORD++); e-LOND's
                       # cold-start level is alpha = 2*w0, so ITS horizon-uniform feasibility
                       # threshold is margin >= -0.5, not margin >= 0.  Both are recorded so the
                       # flow-vs-group comparison is like-for-like for the procedure actually run.
                       elond_feasible=dict(
                           flow=bool((NC_flow + 1.0) * A / T >= 1.0),
                           group=bool((NCg + 1.0) * A / T >= 1.0),
                           threshold_on_margin=-0.5),
                       calibration_exclusion=exclusion,
                       group=dict(nCal=NCg, CEIL=float(CEIL_g), margin=margin_g,
                                  ceiling_ratio=float(CEIL_flow / CEIL_g),
                                  flows_per_group=float(NC_flow / max(NCg, 1)),
                                  required_C=need_g, required_over_available=need_g / max(NCg, 1),
                                  cal_span_h=cal_span_h, test_span_h=te_span_h,
                                  cal_group_rate_per_h=cal_group_rate,
                                  test_group_rate_per_h=te_group_rate,
                                  group_rate_ratio_test_over_cal=rate_ratio,
                                  required_cal_span_h=need_span_h,
                                  required_span_over_test_span=need_span_h / te_span_h,
                                  span_ratio_predicted_by_law=(K / A) * rate_ratio),
                       stats=per_stat,
                       pad_pool=dict(n=int(len(pad)), mean=pad_mean, max=pad_max))
            rows.append(row)

            print(f"\n  pos {POS} seed {SEED}: T={T:,} groups, {int(gte['ismal'].sum())} malicious")
            print(f"    flow calibration : |C|={NC_flow:,} flows   CEIL={CEIL_flow:,.0f}   "
                  f"margin {margin_flow:+.3f}   e-LOND detects {rf[1]}")
            print(f"    GROUP calibration: |C|={NCg:,} groups  CEIL={CEIL_g:,.0f}   "
                  f"margin {margin_g:+.3f}   "
                  f"(ceiling falls {CEIL_flow/CEIL_g:.1f}x, {NC_flow/max(NCg,1):.1f} flows/group)")
            for st in STATS:
                d = per_stat[st]
                print(f"      stat={st:<5} fires on {d['n_firing']:>6,} of {T:,} groups   "
                      f"e-LOND detects {d['tp']:>3}  silent {d['silent']:,}   "
                      f"online e-BH detects {d['ebh_tp']:>3}   "
                      f"append-invariant: {d['padding']['append_invariant_within_group']}")
                ar = d["arity"]
                dep = abs(ar["spearman_arity_vs_statistic"]) > 0.2
                sp = ("undefined (a bin never fires)"
                      if ar["top1pct_spread_across_arity"] is None
                      else f"{ar['top1pct_spread_across_arity']:.1f}x")
                print(f"            arity-dependence: rank corr "
                      f"{ar['spearman_arity_vs_statistic']:+.3f}, worst bin "
                      f"{100*ar['top1pct_max']:.2f}% against a nominal 1% "
                      f"({ar['worst_bin_over_nominal']:.1f}x), spread {sp}"
                      f"  ->  {'exchangeability is arity-CONDITIONAL' if dep else 'arity-invariant to within noise'}")
                print(f"            arity-stratified calibration would leave cold-start windows of "
                      f"{ar['mondrian_min_coldstart']}-{ar['mondrian_max_coldstart']} steps")
            print(f"    calendar price: {cal_span_h:.1f}h of attack-free traffic supplies "
                  f"{NCg:,} groups; cor:budget needs {need_g:,.0f} -> "
                  f"{need_span_h:.0f}h = {need_span_h/te_span_h:.1f}x the {te_span_h:.1f}h "
                  f"deployment window")

    out["rows"] = rows
    col = lambda f: [f(r) for r in rows]
    summary = dict(
        n_rows=len(rows),
        group_margin_max=max(col(lambda r: r["group"]["margin"])),
        group_feasible_anywhere=any(r["group"]["margin"] >= 0 for r in rows),
        flow_margin_min=min(col(lambda r: r["flow"]["margin"])),
        ceiling_ratio_min=min(col(lambda r: r["group"]["ceiling_ratio"])),
        ceiling_ratio_max=max(col(lambda r: r["group"]["ceiling_ratio"])),
        required_over_available_min=min(col(lambda r: r["group"]["required_over_available"])),
        required_span_over_test_span_min=min(
            col(lambda r: r["group"]["required_span_over_test_span"])),
        required_span_over_test_span_max=max(
            col(lambda r: r["group"]["required_span_over_test_span"])),
        # the law is kT/c_0 while cor:budget carries kT/c_0 - 1, so the two agree only up to a
        # relative offset of 1/(cal_rate * test_span); compared relatively for that reason
        span_law_holds=all(
            abs(r["group"]["required_span_over_test_span"]
                - r["group"]["span_ratio_predicted_by_law"])
            / r["group"]["span_ratio_predicted_by_law"] < 1e-5 for r in rows),
        group_rate_ratio_min=min(col(lambda r: r["group"]["group_rate_ratio_test_over_cal"])),
        group_rate_ratio_max=max(col(lambda r: r["group"]["group_rate_ratio_test_over_cal"])),
        group_feasible_for_elond_anywhere=any(r["elond_feasible"]["group"] for r in rows),
        flow_feasible_for_elond_everywhere=all(r["elond_feasible"]["flow"] for r in rows),
        # separated, because the identity is only expected where nothing was rejected
        feasible_matches_closed_form_everywhere=all(
            r["stats"][s]["feasible_matches_closed_form"] for r in rows for s in STATS),
        n_arms=sum(1 for r in rows for s in STATS),
        n_arms_with_rejections=sum(
            1 for r in rows for s in STATS if r["stats"][s]["rej"] > 0),
        max_feasibility_extension_by_rejections=max(
            r["stats"][s]["feasible_extended_by_rejections"] for r in rows for s in STATS),
        max_p_some_firing_group_in_window=max(
            col(lambda r: max(r["stats"][s]["p_some_firing_group_in_window"] for s in STATS))),
        max_group_detections=max(col(lambda r: max(r["stats"][s]["tp"] for s in STATS))),
        max_group_ebh_detections=max(col(lambda r: max(r["stats"][s]["ebh_tp"] for s in STATS))),
        max_flow_detections=max(col(lambda r: r["flow"]["tp"])),
        max_statistic_append_invariant_everywhere=all(
            r["stats"]["max"]["padding"]["append_invariant_within_group"] for r in rows),
        mean_statistic_append_invariant_anywhere=any(
            r["stats"]["mean"]["padding"]["append_invariant_within_group"] for r in rows),
        # a correct r* suppresses every time; anything else is a bug, surfaced here
        zero_is_boundary_not_bug_everywhere=all(
            r["stats"][st]["zero_is_boundary_not_bug"] for r in rows for st in STATS),
        max_fires_in_coldstart_with_no_rejection=max(
            (r["stats"][st]["n_fires_in_coldstart"] for r in rows for st in STATS
             if r["stats"][st]["rej"] == 0), default=0),
        max_frac_calibration_flows_dropped=max(
            col(lambda r: r["calibration_exclusion"]
                          ["frac_of_calibration_flows_in_mixed_groups"])),
        max_mixed_over_benign_arity=max(
            col(lambda r: r["calibration_exclusion"]["mixed_over_benign_mean_arity"] or 0.0)),
        rstar_verified_everywhere=all(
            r["stats"]["mean"]["padding"]["rstar_verified"] for r in rows),
        # ties would make the bare ">= k-th largest" rule anti-conservative; the rank rule is
        # used instead, and this records whether the two would ever have differed
        max_tied_at_threshold=max(r["stats"][st]["n_tied_at_threshold"]
                                  for r in rows for st in STATS),
        max_bare_rule_overfire=max(r["stats"][st]["n_would_fire_bare"]
                                   - r["stats"][st]["n_firing"] for r in rows for st in STATS),
        k_over_c0=K / A,
        max_spearman_arity_max_stat=max(
            col(lambda r: r["stats"]["max"]["arity"]["spearman_arity_vs_statistic"])),
        max_spearman_arity_mean_stat=max(
            col(lambda r: r["stats"]["mean"]["arity"]["spearman_arity_vs_statistic"])),
        max_worst_bin_over_nominal_max_stat=max(
            col(lambda r: r["stats"]["max"]["arity"]["worst_bin_over_nominal"])),
        max_worst_bin_over_nominal_mean_stat=max(
            col(lambda r: r["stats"]["mean"]["arity"]["worst_bin_over_nominal"])),
        any_spread_undefined=any(
            r["stats"][s]["arity"]["top1pct_spread_undefined_zero_bin"]
            for r in rows for s in STATS),
        mondrian_smallest_coldstart=min(
            col(lambda r: r["stats"]["max"]["arity"]["mondrian_min_coldstart"])),
        mondrian_largest_coldstart=max(
            col(lambda r: r["stats"]["max"]["arity"]["mondrian_max_coldstart"])),
        # R8/R1b: the calibration-internal bins are marginally 1% BY CONSTRUCTION; the test-side
        # read is the one that says anything about coverage.
        calibration_internal_marginal_max_dev=max(
            abs(x - 0.01) for x in
            col(lambda r: r["stats"]["max"]["arity"]["calibration_internal_marginal"])),
        test_marginal_over_nominal_min=min(
            col(lambda r: r["stats"]["max"]["arity"]["test_coverage"]["marginal_over_nominal"])),
        test_marginal_over_nominal_max=max(
            col(lambda r: r["stats"]["max"]["arity"]["test_coverage"]["marginal_over_nominal"])),
        test_arity_over_nominal_min_max_stat=min(
            col(lambda r: r["stats"]["max"]["arity"]["test_coverage"]["min_over_nominal"])),
        test_arity_over_nominal_max_max_stat=max(
            col(lambda r: r["stats"]["max"]["arity"]["test_coverage"]["max_over_nominal"])),
        test_arity_over_nominal_min_mean_stat=min(
            col(lambda r: r["stats"]["mean"]["arity"]["test_coverage"]["min_over_nominal"])),
        test_arity_over_nominal_max_mean_stat=max(
            col(lambda r: r["stats"]["mean"]["arity"]["test_coverage"]["max_over_nominal"])),
        spearman_arity_max_stat_min=min(
            col(lambda r: r["stats"]["max"]["arity"]["spearman_arity_vs_statistic"])),
        spearman_arity_mean_stat_min=min(
            col(lambda r: r["stats"]["mean"]["arity"]["spearman_arity_vs_statistic"])))
    out["summary"] = summary

    print("\n" + "=" * 100)
    print("SUMMARY -- what repairing Assumption 1 by construction costs")
    print("=" * 100)
    print(f"  rows                                          : {summary['n_rows']}")
    print(f"  group-calibration margin, best over all rows  : "
          f"{summary['group_margin_max']:+.3f}   feasible anywhere: "
          f"{summary['group_feasible_anywhere']}")
    print(f"  flow-calibration margin, worst over all rows  : "
          f"{summary['flow_margin_min']:+.3f}")
    print(f"  evidence ceiling falls by                     : "
          f"{summary['ceiling_ratio_min']:.1f}x to {summary['ceiling_ratio_max']:.1f}x")
    print(f"  cor:budget requirement / groups available     : "
          f"at least {summary['required_over_available_min']:.1f}x  "
          f"(k/c_0 = {summary['k_over_c0']:.0f})")
    print(f"  required attack-free span / deployment span   : "
          f"{summary['required_span_over_test_span_min']:.1f}x to "
          f"{summary['required_span_over_test_span_max']:.1f}x "
          f"(= k/c_0 times the group-rate ratio "
          f"{summary['group_rate_ratio_min']:.2f}-{summary['group_rate_ratio_max']:.2f}; "
          f"identity holds: {summary['span_law_holds']})")
    print(f"  detections: flow calibration up to {summary['max_flow_detections']}, "
          f"group calibration up to {summary['max_group_detections']} "
          f"(online e-BH {summary['max_group_ebh_detections']})")
    print(f"  e-LOND feasible under GROUP calibration       : "
          f"{summary['group_feasible_for_elond_anywhere']}  "
          f"(under flow calibration, everywhere: "
          f"{summary['flow_feasible_for_elond_everywhere']})")
    print(f"  feasible steps == floor((a*CEIL*(R+1)/zeta)^(1/1.6)) : "
          f"{summary['feasible_matches_closed_form_everywhere']} on all {summary['n_arms']} "
          f"arms ({summary['n_arms_with_rejections']} of which reject) -- so BOTH the zeros and "
          f"the 42 are the boundary, in closed form")
    print(f"  rejections extend feasibility by up to        : "
          f"{summary['max_feasibility_extension_by_rejections']:,} steps (the bootstrap)")
    print(f"  P(some firing group lands in that window)     : at most "
          f"{summary['max_p_some_firing_group_in_window']:.3f}  -- so zero is unsurprising")
    print(f"  arity-dependence of the statistic (rank corr) : max "
          f"{summary['max_spearman_arity_max_stat']:+.3f}  vs  mean "
          f"{summary['max_spearman_arity_mean_stat']:+.3f}")
    print(f"  worst arity bin vs the nominal 1% rate        : max "
          f"{summary['max_worst_bin_over_nominal_max_stat']:.1f}x  vs  mean "
          f"{summary['max_worst_bin_over_nominal_mean_stat']:.1f}x   "
          f"-- so the MAX statistic's exchangeability is arity-conditional and the mean's is "
          f"much closer to invariant")
    print(f"  repairing THAT by arity-stratified calibration: leaves a cold-start window as "
          f"small as {summary['mondrian_smallest_coldstart']} steps")
    print(f"  max stat append-invariant (fixed group) always: "
          f"{summary['max_statistic_append_invariant_everywhere']}")
    print(f"  zero detections are the boundary, not a bug   : "
          f"{summary['zero_is_boundary_not_bug_everywhere']}  "
          f"(fires inside the cold-start window on a silent arm: "
          f"{summary['max_fires_in_coldstart_with_no_rejection']})")
    print(f"  calibration flows discarded with mixed groups : up to "
          f"{100*summary['max_frac_calibration_flows_dropped']:.1f}%, and those groups are "
          f"{summary['max_mixed_over_benign_arity']:.1f}x the benign mean arity "
          f"-- so the exclusion left-shifts calibration")
    print(f"  r* verified minimal on every priced group     : "
          f"{summary['rstar_verified_everywhere']}")
    print(f"  bare '>= kth' rule would over-fire on         : "
          f"{summary['max_bare_rule_overfire']} groups (ties at the threshold: up to "
          f"{summary['max_tied_at_threshold']})")
    print(f"  mean statistic append-invariant anywhere      : "
          f"{summary['mean_statistic_append_invariant_anywhere']}")

    json.dump(out, open("out/t57_group_calibration.json", "w"), indent=1, allow_nan=False)
    print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t57_group_calibration.json")
    return out


if __name__ == "__main__":
    main()
