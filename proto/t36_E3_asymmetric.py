"""
E3 -- deterministic precommitted weights and the ordering attack, on LSPR23.  Section 4.36.

Answers reviewer question 8 of 02_WORKPLAN_PHASE4.md section 9: "can asymmetric aggregation
stop the padding attack?".

WHAT IS ALREADY SETTLED AND IS NOT REDONE ------------------------------------------------
Section 4.16's theorem (no SYMMETRIC e-merging family attaining tau is tau-padding-robust)
and its corollary (the single precommitted slot IS valid and padding-invariant) stand, and
section 4.12 policy D already prices that slot rule.  The record already names the true
condition: *the adversary must not be able to choose which slot its events occupy.*  E3 tests
that condition and nothing else.

Closed forms are derived and verified in t36a_E3_derivation.py; run that FIRST.  A
disagreement between the two is a bug, not a finding.  Tags [D1b], [D3a] etc. are its labels.

THE CLASS UNDER TEST ---------------------------------------------------------------------
A PRECOMMITTED WEIGHT SEQUENCE w_1, w_2, ... >= 0 with sum_i w_i <= 1, fixed before any score
is observed and indexed by position within the episode; the merged evidence is
F(e) = sum_i w_i e_i.  By linearity F is a valid e-merging function under ARBITRARY
dependence [D1a] and is invariant to zero-padding APPENDED after the counted positions [D1b].
The single-slot rule of section 4.16's corollary is w = (1, 0, 0, ...).

Two attacker models, which is the whole experiment:
  (i)  the attacker CANNOT influence order -- padding is appended, F is invariant, and the
       scheme's genuine benefit is whatever it detects.
  (ii) the attacker CAN influence order -- it prepends benign flows, pushing the attack past
       the weighted positions.  The cost is L*(w, beta) = min{L : sum_{i>L} w_i < beta} with
       beta = 1/(alpha_t * M) [D3a], which is FINITE for every summable w [D3b].

Runtime ~6 min.  Run from proto/.
"""
import numpy as np, json, time, sys, gc
from pathlib import Path
from sklearn.metrics import roc_auc_score

import h_stream as H
from h6_procs import Ctx, make_gamma, run_lond, run_lordpp

Path("out").mkdir(exist_ok=True)
SMOKE = "--smoke" in sys.argv
t0 = time.time()

POS = [0.55, 0.85]
DSEEDS = [0, 1]
BH = 2
K = 1
A, W0 = 0.05, 0.025
ZETA16 = 2.2857878790884776
# The weight sequence is PRECOMMITTED, so its support must be too.  Taking it from
# rank.max() would read the largest realised episode size off the evaluation split and cap
# L* at that value for schemes whose tail is meant to be unbounded (standing mistake 4).
# 4,000,000 exceeds the whole deployment window (2,453,026 flows), so no episode reaches it.
N_SUPPORT = 4_000_000
# A-priori high-risk destination ports.  Fixed security knowledge, NOT derived from the
# evaluation split or from any score: SMB, RPC/NetBIOS, RDP, LDAP, SSH, telnet, MSSQL, WinRM.
HIGH_RISK_DPORTS = np.array([22, 23, 135, 137, 138, 139, 389, 445, 636, 1433, 3389,
                             5985, 5986], dtype=np.int64)
if SMOKE:
    POS, DSEEDS = [0.55], [0]


# ---------------------------------------------------------------------------------------
def weight_sequence(scheme, N, **kw):
    """A precommitted weight sequence over positions 1..N, non-negative, summing to <= 1."""
    w = np.zeros(N, dtype=float)
    if scheme == "first-only":
        w[0] = 1.0
    elif scheme == "uniform-m0":
        m0 = int(kw["m0"])
        w[:min(m0, N)] = 1.0 / m0
    elif scheme == "exp-decay":
        rho = float(kw["rho"])
        w[:] = (1.0 - rho) * rho ** np.arange(N, dtype=float)
    else:
        raise ValueError(scheme)
    return w


def frontload_cost(w, beta):
    """L*(w, beta) = min{L >= 0 : sum_{i>L} w_i < beta}  [D3a].

    w is 0-indexed and positions are 1-indexed, so sum_{i>L} w_i over 1-indexed positions is
    w[L:].sum(); tail[L] is already that quantity and must NOT be shifted.

    beta must be positive; at beta > sum(w) the answer is 0, because the required mass
    exceeds the whole budget and detection is impossible with no padding at all."""
    if beta <= 0:
        raise ValueError("beta must be positive")
    tail = np.concatenate([np.cumsum(w[::-1])[::-1], [0.0]])
    idx = np.flatnonzero(tail < beta)
    return int(idx[0]) if idx.size else len(w)


def frontload_cost_analytic(scheme, kw, beta):
    """L* from the INFINITE-tail closed form [D3d/D3e/D3f], so that no truncation of the
    represented weight array can cap it.  max(0, .) because beta > 1 means the required mass
    exceeds the whole budget."""
    if beta <= 0:
        raise ValueError("beta must be positive")
    if beta > 1.0:
        return 0
    if scheme == "first-only":
        return 1
    if scheme == "uniform-m0":
        return max(0, int(np.floor(int(kw["m0"]) * (1.0 - beta))) + 1)
    if scheme == "exp-decay":
        return max(0, int(np.floor(np.log(beta) / np.log(float(kw["rho"])))) + 1)
    return None


def within_episode_rank(gid, n):
    """1-based arrival rank of each flow inside its own episode, and the episode size seen by
    each flow.  Flows arrive in stream order, and a stable sort by gid preserves that order
    inside every group, so the rank is the offset from the group's first row."""
    srt = np.argsort(gid, kind='stable')
    T = int(gid.max()) + 1
    nsz = np.bincount(gid, minlength=T)
    starts = np.concatenate(([0], np.cumsum(nsz)[:-1]))
    rank_sorted = np.arange(n, dtype=np.int64) - np.repeat(starts, nsz) + 1
    rank = np.empty(n, dtype=np.int64)
    rank[srt] = rank_sorted
    return rank, nsz


def merged_evidence(scheme, e_te, gid, rank, nsz, T, hi_rank=None, **kw):
    """F = sum_i w_i e_i per episode, in GROUP-ID order, plus the weight each flow carried.

    `first-only`, `uniform-m0`, `exp-decay` weight by absolute arrival position and are
    padding-invariant [D1b].  `last-only` weights by position from the END and is NOT
    padding-invariant -- one appended zero moves the counted slot onto the pad [D1c]; it is
    run as the control that fails, not as a candidate.  `prior-port` weights the first
    `n_hi` flows whose destination port is in an a-priori high-risk set.  NOTE: that last one
    is OUT OF CLASS and is reported as a diagnostic, not as a candidate.  Its weights are not
    a precommitted position sequence -- they select slots using an evaluation-time covariate
    (the destination port) -- so `sum w <= 1` does NOT establish validity unless the per-flow
    e-values are conditionally valid given that covariate, which is not shown here.  It is
    included because "weight by a security prior" is the obvious thing a practitioner would
    try, and it is worth showing what it does.
    """
    if scheme == "last-only":
        wf = (rank == nsz[gid]).astype(float)
    elif scheme == "prior-port":
        n_hi = int(kw["n_hi"])
        wf = np.where((hi_rank > 0) & (hi_rank <= n_hi), 1.0 / n_hi, 0.0)
    else:
        if int(rank.max()) > N_SUPPORT:
            raise AssertionError(f"episode longer than the precommitted weight support "
                                 f"({int(rank.max())} > {N_SUPPORT})")
        w = weight_sequence(scheme, N_SUPPORT, **kw)
        wf = w[rank - 1]
    F = np.bincount(gid, weights=wf * e_te, minlength=T)
    return F, wf


def lond_levels(ctx, gam1):
    """LOND, recording the level alpha_t offered at each step.  A literal transcription of
    h6_procs.run_lond with a `levels` output added; asserted identical to run_lond."""
    R = rej = tp = silent = 0
    lv = np.zeros(ctx.T)
    fired = np.zeros(ctx.T, bool)
    for t in range(1, ctx.T + 1):
        lvl = ctx.A * gam1[t] * (R + 1)
        lv[t - 1] = lvl
        if ctx.infeasible(lvl):
            silent += 1
            continue
        if ctx.Ev[t - 1] >= 1.0 / lvl:
            R += 1; rej += 1; fired[t - 1] = True
            if ctx.ismal[t - 1]: tp += 1
    return rej, tp, silent, lv, fired


# ---------------------------------------------------------------------------------------
X, y, ts, src, dst = H.load()
N = len(y)
try:
    DPORT = H.load_extra("dport")
except FileNotFoundError:
    DPORT = None
    print("  [warn] dport cache missing; the prior-port scheme will be skipped")

SCHEMES = [("first-only", {}), ("uniform-m0", dict(m0=10)), ("uniform-m0", dict(m0=100)),
           ("exp-decay", dict(rho=0.5)), ("exp-decay", dict(rho=0.99)),
           ("last-only", {}), ("prior-port", dict(n_hi=10))]
rows, per_cfg, failures, notes = [], [], [], []

for pos in POS:
    i1, i2, i3 = H.split_indices(N, pos)
    ts_w, y_te = ts[i2:i3], y[i2:i3]
    n_te = i3 - i2
    for dseed in DSEEDS:
        tag = f"pos={pos} seed={dseed}"
        sc = H.fit_detector(X, y, i1, dseed, kind="hgb")
        s_cal, s_te = H.score_windows(sc, X, i1, i2, i3)
        e_te, cal, NC, CEIL = H.evalues(s_cal, y[i1:i2], s_te, k=K)
        M = float(CEIL)
        auroc = float(roc_auc_score(y_te, s_te))
        ep = H.build_episodes(e_te, y_te, ts_w, src[i2:i3], dst[i2:i3], bucket_s=BH * 3600)
        gid, order, T, ismal, NMAL = ep["gid"], ep["order"], ep["T"], ep["ismal"], ep["n_mal"]
        nsz_raw = np.bincount(gid, minlength=T)
        rank, nsz_chk = within_episode_rank(gid, n_te)
        assert np.array_equal(nsz_raw, nsz_chk)
        # the record's symmetric baseline, for comparison on the same episodes
        Ev_mean = ep["Ev"]
        smax = np.full(T, -np.inf); np.maximum.at(smax, gid, s_te)
        fr = H.frontier(smax[order], ismal)
        # a-priori high-risk rank: the k-th high-risk flow of the episode, 0 if not high risk
        if DPORT is not None:
            dp = DPORT[i2:i3]
            is_hi = np.isin(dp, HIGH_RISK_DPORTS)
            srt = np.argsort(gid, kind='stable')
            hi_sorted = is_hi[srt].astype(np.int64)
            starts = np.concatenate(([0], np.cumsum(nsz_raw)[:-1]))
            csum = np.cumsum(hi_sorted)
            base = np.repeat(csum[starts] - hi_sorted[starts], nsz_raw)
            hr_sorted = np.where(hi_sorted > 0, csum - base, 0)
            hi_rank = np.empty(n_te, dtype=np.int64); hi_rank[srt] = hr_sorted
            frac_hi = float(is_hi.mean())
        else:
            hi_rank, frac_hi = None, None
        g1p, _ = make_gamma("poly", T)
        g1u, _ = make_gamma("uniform", T)
        print(f"  {tag}: T={T:,} |C|={NC:,} AUROC={auroc:.4f} malicious episodes {NMAL} "
              f"mean m={nsz_raw.mean():.0f} max m={nsz_raw.max():,} "
              f"high-risk flows {100*frac_hi if frac_hi is not None else float('nan'):.2f}% "
              f"[{time.time()-t0:.0f}s]")

        mean_det = {}
        arms = [("mean (the record, SYMMETRIC)", "mean", {}, Ev_mean, None)]
        for scheme, kw in SCHEMES:
            if scheme == "prior-port" and DPORT is None:
                continue
            F, wf = merged_evidence(scheme, e_te, gid, rank, nsz_raw, T,
                                    hi_rank=hi_rank, **kw)
            arms.append((scheme + (str(kw) if kw else ""), scheme, kw, F[order], wf))

        for label, scheme, kw, Ev, wf in arms:
            # ---- validity, on EVERY group (standing rule 6) ---------------------------
            if scheme == "mean":
                sumw, ceil_arm = 1.0, M
            elif scheme == "last-only":
                sumw, ceil_arm = 1.0, M
            elif scheme == "prior-port":
                sumw, ceil_arm = 1.0, M
            else:
                sumw = float(weight_sequence(scheme, N_SUPPORT, **kw).sum())
                ceil_arm = M * sumw
            if sumw > 1.0 + 1e-12:
                failures.append(f"{tag} {label}: sum of weights {sumw} > 1 -- not valid")
            benign_ep = ~ismal
            max_benign_F = float(Ev[benign_ep].max()) if benign_ep.any() else 0.0
            benign_fire = float((Ev[benign_ep] >= 1.0).mean()) if benign_ep.any() else 0.0

            # ---- padding-invariance [D1b], asserted at r = 0, 10, 1e3, 1e5 -------------
            pad_inv = None
            if scheme not in ("mean",):
                probe = np.zeros(200); probe[[0, 5, 37, 199]] = M
                if scheme == "last-only":
                    base = probe[-1]
                    pad_inv = all(np.concatenate([probe, np.zeros(r)])[-1] == base
                                  for r in (10, 1000, 100_000))
                elif scheme == "prior-port":
                    pad_inv = True     # appended non-high-risk flows never enter the sum
                else:
                    ww = weight_sequence(scheme, N_SUPPORT, **kw)
                    base = float(probe @ ww[:200])
                    pad_inv = all(abs(float(np.concatenate([probe, np.zeros(r)])
                                            @ ww[:200 + r]) - base) <= 1e-9 * max(1.0, base)
                                  for r in (0, 10, 1000, 100_000))
                if scheme == "last-only" and pad_inv:
                    failures.append(f"{tag}: last-only reported padding-invariant, but [D1c] "
                                    f"says one appended zero must destroy it")

            # Per-episode realised ceiling.  `ceil_arm = M*sum(w)` is a stream-wide bound;
            # an episode shorter than the weighted prefix, or with no high-risk flow, has a
            # strictly smaller maximum attainable F, so one scalar UNDER-counts silence.
            # Rejections are unaffected (Ev cannot cross the threshold either way).
            ceil_ep = (np.full(T, M) if wf is None
                       else (M * np.bincount(gid, weights=wf, minlength=T))[order])

            for gk, g1 in (("poly", g1p), ("uniform[ORACLE]", g1u)):
                ctx = Ctx(Ev, ismal, ceil_arm, alpha=A, w0=W0)
                rej, tp, silent, lv, fired = lond_levels(ctx, g1)
                chk = run_lond(Ctx(Ev, ismal, ceil_arm, alpha=A, w0=W0), g1)
                if (chk[0], chk[1], chk[2]) != (rej, tp, silent):
                    failures.append(f"{tag} {label} {gk}: lond_levels != run_lond "
                                    f"{(rej,tp,silent)} vs {chk[:3]}")
                fl = np.zeros(T, bool)
                r2 = run_lordpp(Ctx(Ev, ismal, ceil_arm, alpha=A, w0=W0), g1, fired=fl)

                with np.errstate(divide='ignore'):
                    silent_ep = int(((lv <= 0) |
                                     (ceil_ep < 1.0 / np.maximum(lv, 1e-300))).sum())
                det = np.flatnonzero(fired)
                orec, ofdp = H.frontier_at_budget(fr, rej)
                # ---- attacker model (ii): the front-load cost per DETECTED episode ------
                Lstar, pad_sym = [], []
                if det.size and scheme != "mean":
                    analytic = scheme in ("first-only", "uniform-m0", "exp-decay")
                    wseq = weight_sequence(scheme, N_SUPPORT, **kw) if analytic else None
                    for t_idx in det:
                        beta = 1.0 / (lv[t_idx] * M) if lv[t_idx] > 0 else np.inf
                        if analytic:
                            La = frontload_cost_analytic(scheme, kw, beta)
                            Lw = frontload_cost(wseq, beta)     # cross-check the closed form
                            if La != Lw and Lw < N_SUPPORT:
                                failures.append(f"{tag} {label}: analytic L*={La} != array "
                                                f"L*={Lw} at beta={beta:.6g}")
                            Lstar.append(La)
                        elif scheme == "prior-port":
                            # the budget is exhausted by n_hi leading high-risk benign flows
                            Lstar.append(int(kw["n_hi"]))
                        # last-only has NO front-load cost to report: it is defeated by a
                        # single APPENDED flow, a different attack, recorded separately
                # PAIRED comparison: on the episodes this arm AND the symmetric mean arm both
                # detect, what does it cost to suppress each under each rule?  An arm's L*
                # against the symmetric pad on that arm's own (different) detections would not
                # be like-for-like.
                sum_e = np.bincount(gid, weights=e_te, minlength=T)[order]
                m_ep = nsz_raw[order]
                if det.size:
                    common = np.intersect1d(det, mean_det.get(gk, np.array([], dtype=np.int64)))
                    for t_idx in common:
                        tau = 1.0 / lv[t_idx] if lv[t_idx] > 0 else np.inf
                        pad_sym.append(max(0, int(np.floor(sum_e[t_idx] / tau - m_ep[t_idx])) + 1)
                                       if np.isfinite(tau) else 0)
                if scheme == "mean":
                    mean_det[gk] = det

                rows.append(dict(
                    pos=pos, dseed=dseed, arm=label, scheme=scheme, kw=str(kw), gamma=gk,
                    T=int(T), NC=int(NC), NMAL=int(NMAL), auroc=auroc, sum_w=sumw,
                    ceil_arm=float(ceil_arm), padding_invariant=pad_inv,
                    rejections=int(rej), tp=int(tp),
                    fdp=float((rej - tp) / max(rej, 1)),
                    recall=float(tp / NMAL) if NMAL else None,
                    oracle_recall_at_budget=float(orec),
                    silent=float(silent / T),
                    silent_realised=float(silent_ep / T),
                    n_common_with_mean=int(len(pad_sym)),
                    lordpp_rejections=int(r2[0]), lordpp_tp=int(r2[1]),
                    max_benign_F=max_benign_F, benign_fire_rate=benign_fire,
                    median_frontload_L=(float(np.median(Lstar)) if Lstar else None),
                    min_frontload_L=(int(np.min(Lstar)) if Lstar else None),
                    max_frontload_L=(int(np.max(Lstar)) if Lstar else None),
                    median_symmetric_pad_paired=(float(np.median(pad_sym)) if pad_sym else None),
                    alpha_t_M_at_first_det=(float(lv[det[0]] * M) if det.size else None),
                ))
        del s_cal, s_te, e_te, cal, ep, rank
        gc.collect()
        per_cfg.append(dict(pos=pos, dseed=dseed, T=int(T), NC=int(NC), NMAL=int(NMAL),
                            auroc=auroc, M=M, frac_high_risk_flows=frac_hi))

# =======================================================================================
def agg(v):
    v = [x for x in v if x is not None]
    return (float(np.mean(v)), float(np.std(v, ddof=1)) if len(v) > 1 else 0.0) if v else (None, None)


for pos in POS:
    sub = [r for r in rows if r["pos"] == pos]
    if not sub: continue
    c = [c for c in per_cfg if c["pos"] == pos][0]
    print("\n" + "=" * 140)
    lbl = "GUARANTEE WINDOW" if pos == 0.55 else "STRESS WINDOW (evidence NOT a valid e-value)"
    print(f"POSITION {pos} — {lbl}   T={c['T']:,}  |C|={c['NC']:,}  malicious episodes {c['NMAL']}")
    print("=" * 140)
    print(f"  {'arm':>26} {'gamma':>17} {'sum w':>7} {'pad-inv':>8} {'alerts':>8} {'FDP':>7} "
          f"{'recall':>8} {'oracle@bud':>11} {'silent':>8} {'L* (order attack)':>18} "
          f"{'sym pad (paired)':>17}")
    for label in [a for a in dict.fromkeys(r["arm"] for r in sub)]:
        for gk in ("poly", "uniform[ORACLE]"):
            rr = [r for r in sub if r["arm"] == label and r["gamma"] == gk]
            if not rr: continue
            rj, _ = agg([r["rejections"] for r in rr]); fd, _ = agg([r["fdp"] for r in rr])
            rc, _ = agg([r["recall"] for r in rr])
            orc, _ = agg([r["oracle_recall_at_budget"] for r in rr])
            sl, _ = agg([r["silent_realised"] for r in rr])
            L, _ = agg([r["median_frontload_L"] for r in rr])
            ps, _ = agg([r["median_symmetric_pad_paired"] for r in rr])
            pi = rr[0]["padding_invariant"]
            pis = "n/a" if pi is None else ("YES" if pi else "**NO**")
            print(f"  {label:>26} {gk:>17} {rr[0]['sum_w']:>7.3f} {pis:>8} {rj:>8.1f} "
                  f"{fd:>7.3f} {rc:>8.3f} {orc:>11.3f} {100*sl:>7.1f}% "
                  f"{(L if L is not None else float('nan')):>18,.0f} "
                  f"{(ps if ps is not None else float('nan')):>17,.0f}")

print("\n" + "=" * 140)
print("READING THIS TABLE")
print("=" * 140)
print("  'pad-inv'      whether the scheme is invariant to zero-padding APPENDED after the")
print("                 counted positions [D1b] -- attacker model (i), who cannot reorder.")
print("  'L*'           attacker model (ii): the number of benign flows that must be placed")
print("                 FIRST to make detection impossible, at the episode's own realised")
print("                 level [D3a].  Finite for every summable weight sequence [D3b].")
print("  'sym pad (paired)' the section 4.16 cost against the record's arithmetic mean, on")
print("                 the episodes THIS ARM AND THE MEAN ARM BOTH detect, at the same")
print("                 levels: floor(sum e/tau - m) + 1, appended anywhere.")
print("  L* is quoted at the UNPERTURBED level.  A sequential attacker that suppresses")
print("  earlier episodes leaves LOND with a smaller R, hence a smaller alpha_t and a weakly")
print("  SMALLER L*, so every L* below is an UPPER BOUND on the real cost.")
print("  Arms are NOT at a matched alert budget, so recall is read against 'oracle@bud',")
print("  the achievable episode recall at each arm's own alert count (section 4.19).")

print("\n" + "=" * 140)
if failures:
    print("FAILURES:")
    for f in failures: print("  " + f)
else:
    print("all validity, padding-invariance and cross-checks passed")
print("=" * 140)

json.dump(dict(config=dict(POS=POS, DSEEDS=DSEEDS, bucket_h=BH, k=K, alpha=A, w0=W0,
                           schemes=[f"{s}{k}" for s, k in SCHEMES],
                           high_risk_dports=HIGH_RISK_DPORTS.tolist(), smoke=SMOKE),
               rows=rows, per_cfg=per_cfg, notes=notes, failures=failures),
          open("out/t36_E3_asymmetric.json", "w"), indent=1, allow_nan=True)
print(f"  [{time.time()-t0:.0f}s]  wrote out/t36_E3_asymmetric.json")
if failures:
    raise SystemExit(1)
