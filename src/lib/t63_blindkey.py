import json, time
import numpy as np
from pathlib import Path
from scipy.special import zeta

import h_stream as hs
from h6_procs import Ctx, make_gamma, run_lond

POS = (0.55, 0.62, 0.70, 0.77, 0.85)
ORDERS = ("keyhash", "keyed")
SEED = 0
K = 1
A = 0.05
W0 = 0.025
BUCKET = 2 * 3600
N_REP = 400
BUDGETS = tuple(sorted({int(round(10 ** (e / 6.0))) for e in range(6, 37)}))
Z16 = float(zeta(1.6, 1))
HMAX = float(1 << 63)


def _elond_prefix(Ev, CEIL, shift, alpha=A):
    if np.any(np.diff(np.asarray(shift)) < 0):
        raise ValueError("shift must be non-decreasing along the stream order; the early stop is "
                         "unsound otherwise")
    T = len(Ev)
    fired = np.zeros(T, bool)
    R = 0
    for i in range(T):
        step = i + int(shift[i]) + 1
        lvl = alpha * (step ** -1.6 / Z16) * (R + 1)
        if lvl <= 0.0 or CEIL < 1.0 / lvl:
            break
        if Ev[i] >= 1.0 / lvl:
            fired[i] = True
            R += 1
    return fired


def shifts_from_hashes(h63, bucket, b0, draws):

    T = len(h63)
    c = np.zeros(T, np.int64)
    if len(draws) == 0:
        return c
    d = np.sort(np.asarray(draws, dtype=np.float64))
    inb = bucket == b0
    c[inb] = np.searchsorted(d, h63[inb], side="left")
    c[bucket > b0] = len(d)
    return c


def blind_curve(Ev, CEIL, h63, bucket, b0, targets, budgets, n_rep, rng):
    """P(target suppressed) against the number of blindly instantiated keys."""
    n_t = len(targets)
    hit = np.zeros((len(budgets), n_t), np.int64)
    for _ in range(n_rep):
        draws = rng.integers(0, int(HMAX), size=max(budgets), dtype=np.int64)
        for bi, N in enumerate(budgets):
            c = shifts_from_hashes(h63, bucket, b0, draws[:N])
            f = _elond_prefix(Ev, CEIL, c)
            hit[bi] += ~f[targets]
    return hit / float(n_rep)


def _interp_budget(budgets, p, want):
    """Smallest budget reaching `want` success, log-interpolated between grid points."""
    p = np.asarray(p, dtype=float)
    ok = np.flatnonzero(p >= want)
    if not ok.size:
        return None
    j = int(ok[0])
    if j == 0 or p[j] == want:
        return float(budgets[j if p[j] == want else 0])
    b0, b1 = float(budgets[j - 1]), float(budgets[j])
    p0, p1 = p[j - 1], p[j]
    if p1 <= p0:
        return b1
    lam = (want - p0) / (p1 - p0)
    return float(np.exp(np.log(b0) + lam * (np.log(b1) - np.log(b0))))


def main():
    t0 = time.time()
    Path("out").mkdir(exist_ok=True)
    X, y, ts, src, dst = hs.load()
    N = len(y)
    rows, fails = [], []

    for pos in POS:
        i1, i2, i3 = hs.split_indices(N, pos)
        y_te = y[i2:i3]; ts_w = ts[i2:i3]; src_w = src[i2:i3]; dst_w = dst[i2:i3]
        score = hs.fit_detector(X, y, i1, seed=SEED, kind="hgb", verbose=False)
        s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
        e_te, cal, NC, CEIL = hs.evalues(s_cal, y[i1:i2], s_te, k=K)

        for order in ORDERS:
            ep = hs.build_episodes(e_te, y_te, ts_w, src_w, dst_w, BUCKET, "src-dst", order=order)
            T, Ev, ismal = ep["T"], ep["Ev"], ep["ismal"]

            f_ref = np.zeros(T, bool)
            run_lond(Ctx(Ev, ismal, CEIL, alpha=A, w0=W0), make_gamma("poly", T)[0], fired=f_ref)
            f_mine = _elond_prefix(Ev, CEIL, np.zeros(T, np.int64))
            if not np.array_equal(f_ref, f_mine):
                fails.append(f"_elond_prefix disagrees with run_lond at pos={pos} order={order}")
            targets = np.flatnonzero(f_ref & ismal)
            print(f"\n  pos={pos} {order:<8} T={T:,}  true detections {targets.size}"
                  f"  [{time.time()-t0:.0f}s]")
            if targets.size == 0:
                rows.append(dict(pos=pos, order=order, T=int(T), n_targets=0,
                                 note="nothing detected here; no target to suppress"))
                continue

            hseed = 0 if order == "keyhash" else hs.KEYED_SEED
            gsrc = np.zeros(T, np.int64); gsrc[ep["gid"]] = src_w
            gdst = np.zeros(T, np.int64); gdst[ep["gid"]] = dst_w
            h63 = (hs.key_hash(gsrc, gdst, ep["bucket_g"], seed=hseed)
                   & np.uint64((1 << 63) - 1)).astype(np.int64)[ep["order"]]
            bucket = ep["bucket_g"][ep["order"]]
            b0 = int(bucket[targets[0]])
            same_bucket = bool(all(int(bucket[t]) == b0 for t in targets))
            n_earlier_bucket_eps = int((bucket < b0).sum())
            if not same_bucket:
                fails.append(f"targets span several buckets at pos={pos} order={order}; the "
                             f"single-bucket insertion model does not apply")
            if n_earlier_bucket_eps:
                fails.append(f"an EARLIER bucket exists at pos={pos} order={order} "
                             f"({n_earlier_bucket_eps} episodes): insertion there precedes the "
                             f"target with probability 1 and this cost model is far too high")
            u = h63[targets] / HMAX                       # the target's hash quantile

            def _front(G, t):

                c = np.zeros(T, np.int64)
                c[bucket >= b0] = G
                return c

            def _targeted(G, t):
                c = np.zeros(T, np.int64)
                c[int(t):] = G                 # only the target and everything after it moves
                return c

            def _min_G(place, t):
                lo, hi = 0, int(2 * T)
                if _elond_prefix(Ev, CEIL, place(hi, t))[t]:
                    return None                # not suppressible within the search range
                while lo < hi:
                    mid = (lo + hi) // 2
                    if not _elond_prefix(Ev, CEIL, place(mid, t))[t]:
                        hi = mid
                    else:
                        lo = mid + 1
                return int(lo)

            gstar, gstar_tgt, pub_ok = [], [], []
            for t in targets:
                gf = _min_G(_front, t)
                gt_ = _min_G(_targeted, t)
                gstar.append(gf)
                gstar_tgt.append(gt_)
                pub_ok.append(bool(gf is not None and gt_ is not None
                                   and not _elond_prefix(Ev, CEIL, _front(gf, t))[t]
                                   and not _elond_prefix(Ev, CEIL, _targeted(gt_, t))[t]))

            # ---- the BLIND attacker ---------------------------------------------------------
            rng = np.random.default_rng(20260902 + int(pos * 100) + (1 if order == "keyed" else 0))
            budgets = [b for b in BUDGETS]
            psucc = blind_curve(Ev, CEIL, h63, bucket, b0, targets, budgets, N_REP, rng)
            n50 = [_interp_budget(budgets, psucc[:, j], 0.50) for j in range(len(targets))]
            n90 = [_interp_budget(budgets, psucc[:, j], 0.90) for j in range(len(targets))]
            n99 = [_interp_budget(budgets, psucc[:, j], 0.99) for j in range(len(targets))]

            def bracket(col, want):
                """The two GRID points the answer lies between -- the measured precision."""
                ok = np.flatnonzero(np.asarray(col) >= want)
                if not ok.size:
                    return [budgets[-1], None]          # not reached inside the grid
                j = int(ok[0])
                return [budgets[j - 1] if j else None, budgets[j]]

            br50 = [bracket(psucc[:, j], 0.50) for j in range(len(targets))]
            br90 = [bracket(psucc[:, j], 0.90) for j in range(len(targets))]
            br99 = [bracket(psucc[:, j], 0.99) for j in range(len(targets))]
            # binomial LOWER BOUND: the target's own displacement at fixed R, i.e. the targeted
            # placement.  The replay may only do better, because it also drops R.
            from scipy.stats import binom
            pbin = np.array([[(float(binom.sf(gstar_tgt[j] - 1, Nb, u[j]))
                               if gstar_tgt[j] is not None else np.nan)
                              for j in range(len(targets))] for Nb in budgets])
            with np.errstate(invalid="ignore"):
                fin_bin = np.isfinite(pbin)
                viol = float(np.max((pbin - psucc)[fin_bin])) if fin_bin.any() else 0.0
                slack = float(np.max((psucc - pbin)[fin_bin])) if fin_bin.any() else 0.0
            if viol > 0.05:
                fails.append(f"replay fell below its binomial lower bound by {viol:.3f} at "
                             f"pos={pos} order={order}")


            p_at_max = [float(psucc[-1, j]) for j in range(len(targets))]
            n_certain_at_max = int(sum(1 for x in p_at_max if x >= 1.0))


            def _ratio(nn):
                return [(nn[j] / gstar[j]) if (nn[j] and gstar[j]) else None
                        for j in range(len(targets))]

            ratio = _ratio(n99)
            ratio50 = _ratio(n50)
            rr = [r for r in ratio if r is not None]
            rec = dict(pos=pos, order=order, T=int(T), NC=int(NC), CEIL=float(CEIL),
                       n_targets=int(targets.size),
                       all_targets_in_one_bucket=same_bucket,
                       n_episodes_in_earlier_buckets=n_earlier_bucket_eps,
                       target_bucket_is_first_of_window=bool(n_earlier_bucket_eps == 0),
                       target_positions=[int(x) + 1 for x in targets],
                       target_hash_quantile=[float(x) for x in u],
                       public_gstar_front=gstar,
                       public_gstar_targeted=gstar_tgt,
                       public_gstar_verified=bool(all(pub_ok)),
                       budgets=budgets,
                       p_success=[[float(x) for x in psucc[bi]] for bi in range(len(budgets))],
                       p_success_binomial=[[float(x) for x in pbin[bi]]
                                           for bi in range(len(budgets))],
                       binomial_lower_bound_violation=viol,
                       replay_slack_over_binomial_lower_bound=slack,
                       N50=n50, N90=n90, N99=n99,
                       N50_bracket=br50, N90_bracket=br90, N99_bracket=br99,

                       N50_median=(float(np.median([x for x in n50 if x is not None]))
                                   if any(x is not None for x in n50) else None),
                       N90_median=(float(np.median([x for x in n90 if x is not None]))
                                   if any(x is not None for x in n90) else None),
                       N99_median=(float(np.median([x for x in n99 if x is not None]))
                                   if any(x is not None for x in n99) else None),
                       blind_over_public_ratio_median=(
                           float(np.median([x for x in ratio if x is not None]))
                           if any(x is not None for x in ratio) else None),

                       bracket_width_max=max(
                           [(hi / lo) for b in (br50 + br90 + br99)
                            for lo, hi in [b] if lo and hi] or [float("nan")]),
                       p_success_at_max_budget=p_at_max,
                       n_targets_certain_at_max_budget=n_certain_at_max,
                       min_p_success_at_max_budget=float(min(p_at_max)),
                       blind_over_public_ratio=ratio,
                       blind_over_public_ratio_at_50pct=ratio50,
                       blind_over_targeted_ratio=[
                           (n99[j] / gstar_tgt[j]) if (n99[j] and gstar_tgt[j]) else None
                           for j in range(len(targets))],
                       blind_over_public_median=(float(np.median(rr)) if rr else None),
                       blind_over_public_min=(float(min(rr)) if rr else None),
                       blind_over_public_max=(float(max(rr)) if rr else None),
                       n_targets_unreachable_at_max_budget=int(sum(1 for x in n50 if x is None)),
                       n_rep=N_REP)
            rows.append(rec)
            fin = [x for x in n50 if x is not None]
            gt_fin = [g for g in gstar_tgt if g is not None]
            print(f"    public G* front {min(gstar):>6,}-{max(gstar):>6,}  targeted "
                  f"{min(gt_fin):>6,}-{max(gt_fin):>6,}   blind N50 "
                  f"{(f'{min(fin):,.0f}-{max(fin):,.0f}' if fin else 'unreached'):>15}"
                  f"  x{rec['blind_over_public_median'] or float('nan'):>6.1f} median"
                  f"  (lb violation {viol:+.3f}, slack {slack:.3f})")

    live = [r for r in rows if r.get("n_targets")]
    all_ratios = [x for r in live for x in r["blind_over_public_ratio"] if x is not None]
    all_n50 = [x for r in live for x in r["N50"] if x is not None]
    all_u = [x for r in live for x in r["target_hash_quantile"]]
    n_unreach = sum(r["n_targets_unreachable_at_max_budget"] for r in live)
    summary = dict(
        n_cells=len(rows), n_cells_with_targets=len(live),
        n_targets_total=sum(r["n_targets"] for r in live),
        n_targets_unreachable_at_max_budget=int(n_unreach),
        n_targets_certain_at_max_budget=sum(r["n_targets_certain_at_max_budget"] for r in live),
        min_p_success_at_max_budget=min(r["min_p_success_at_max_budget"] for r in live),
        every_target_certain_at_max_budget=all(r["min_p_success_at_max_budget"] >= 1.0
                                               for r in live),
        target_bucket_is_first_of_window_everywhere=all(r["target_bucket_is_first_of_window"]
                                                        for r in live),
        max_budget=max(BUDGETS), n_rep=N_REP,
        public_gstar_verified_everywhere=all(r["public_gstar_verified"] for r in live),
        public_gstar_front_min=min(g for r in live for g in r["public_gstar_front"]),
        public_gstar_front_max=max(g for r in live for g in r["public_gstar_front"]),
        public_gstar_targeted_min=min(g for r in live for g in r["public_gstar_targeted"]
                                      if g is not None),
        public_gstar_targeted_max=max(g for r in live for g in r["public_gstar_targeted"]
                                      if g is not None),
        blind_N50_min=(min(all_n50) if all_n50 else None),
        blind_N50_max=(max(all_n50) if all_n50 else None),
        ratio_basis="N99 / G*_front: blind budget for 99% success over the public budget for "
                    "certain suppression, i.e. matched reliability",
        blind_over_public_median=(float(np.median(all_ratios)) if all_ratios else None),
        blind_over_public_min=(float(min(all_ratios)) if all_ratios else None),
        blind_over_public_max=(float(max(all_ratios)) if all_ratios else None),
        bracket_width_max=max(r["bracket_width_max"] for r in live),
        target_hash_quantile_min=(float(min(all_u)) if all_u else None),
        target_hash_quantile_max=(float(max(all_u)) if all_u else None),
        max_binomial_lower_bound_violation=max(r["binomial_lower_bound_violation"]
                                               for r in live),
        max_replay_slack_over_binomial=max(r["replay_slack_over_binomial_lower_bound"]
                                           for r in live),
        assertions_failed=fails)
    out = dict(config=dict(POS=list(POS), ORDERS=list(ORDERS), SEED=SEED, k=K, alpha=A, w0=W0,
                           bucket_s=BUCKET, n_rep=N_REP, budgets=list(BUDGETS),
                           cost_unit="distinct (SrcIP,DstIP) pairs the adversary must instantiate "
                                     "and send traffic between",
                           model="secret seed: every inserted key hashes uniformly, so the "
                                 "adversary cannot choose keys that precede the target"),
               rows=rows, summary=summary)
    json.dump(out, open("out/t63_blindkey.json", "w"), indent=1, allow_nan=False)
    print("\n" + "=" * 100)
    print(f"  targets {summary['n_targets_total']}, of which "
          f"{summary['n_targets_certain_at_max_budget']} fall in EVERY draw at "
          f"{summary['max_budget']:,} blindly instantiated keys "
          f"(worst per-target success {summary['min_p_success_at_max_budget']:.3f})")
    print(f"  the target bucket is the first of its window everywhere: "
          f"{summary['target_bucket_is_first_of_window_everywhere']} -- if it were not, insertion "
          f"into an earlier bucket would precede the target with probability 1")
    print(f"  public hash needs G* = {summary['public_gstar_front_min']:,}-"
          f"{summary['public_gstar_front_max']:,} keys (front placement; "
          f"{summary['public_gstar_targeted_min']:,}-"
          f"{summary['public_gstar_targeted_max']:,} targeted) plus a FREE offline search")
    print(f"  at MATCHED reliability (blind 99% vs public certain) a secret seed multiplies the "
          f"instantiated-key cost by {summary['blind_over_public_min']:.1f}-"
          f"{summary['blind_over_public_max']:.1f}x (median "
          f"{summary['blind_over_public_median']:.1f}x)")
    print(f"  every N50/N90/N99 is bracketed by grid points at most "
          f"{summary['bracket_width_max']:.2f}x apart, which is its real precision")
    se = 0.5 / (N_REP ** 0.5)
    print(f"  worst shortfall against the binomial lower bound "
          f"{summary['max_binomial_lower_bound_violation']:+.4f}, against a Monte-Carlo standard "
          f"error of {se:.4f} at n_rep={N_REP} ({summary['max_binomial_lower_bound_violation']/se:.1f} "
          f"SE, i.e. sampling noise, not a model error); the coupling through R buys the attacker up "
          f"to {summary['max_replay_slack_over_binomial']:.3f} in success probability")
    if fails:
        print("  *** ASSERTIONS FAILED: " + "; ".join(fails))
    print(f"  [{time.time()-t0:.0f}s]  wrote out/t63_blindkey.json")
    return out


if __name__ == "__main__":
    main()
