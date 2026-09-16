"""R7 -- a host-conditioned detector and the padding-transfer boundary (review sec:5.1/sec:15).

The paper's padding attack (Surface A / sec:paddingcost) works because the shipped detector uses
FLOW-ONLY features carrying no endpoint identity: ordinary victim-service traffic scores like
ordinary traffic (fires ~0 of the time, experiment W3 / t48) and so dilutes the merged episode
e-value.  The paper scopes this to flow-level detectors and conjectures that a HOST-CONDITIONED
detector "would break the argument" but "needs a testbed".  R7 supplies that measurement, honestly.

Design (mirrors t48 at the primary guarantee window 0.55 and the stress window 0.85, seed 0):

  Part A -- causal, non-leaking host-context features.  Six per-flow features from STRICTLY
    EARLIER-TIMESTAMP traffic only (ts < ts(flow); timestamp ties excluded, not ordered by arbitrary
    row index -- ~1.03M adjacent flows share a timestamp): src_cnt, src_ddst, src_failfrac, dst_cnt,
    dst_dsrc, dst_failfrac.  NO endpoint ground-truth (label_src/label_dst/ext_src/ext_dst) and no y
    are ever used -- those leak (label_src=1 -> attack-rate 1.0).  Validated against a strict-ts
    brute-force reference on both sides; the augmented matrix width is asserted (33 flow + 6 host).

  Part B -- a COMPETENT host-conditioned detector on X_aug = [X | host features]: report AUROC, tail
    reach, and e-LOND detections vs the flow-only detector (all e-values via the shared hs.evalues).

  Part C -- the padding-transfer boundary, with a CAUSAL ACCUMULATION REPLAY (not a static graft).
    Episodes key on (src,dst,bucket), so a pad diluting a detected episode (src*,dst*) must carry
    src=src*,dst=dst*.  We compute the pair's real causal state at episode end from the global
    arrays, then REPLAY the append: the k-th appended pad sees src_cnt/dst_cnt raised by (k-1) prior
    pads, src_ddst/dst_dsrc PINNED (padding one victim adds no new peer), and fail fractions updated
    by the pool's measured fail rate.  We densely sweep 120 accumulation levels k=1..min(r*,cap) and
    take the max fire rate.  A pad fires iff its score STRICTLY beats the k-th largest benign
    calibration score (matching hs.evalues, side='left').  The SUPPRESSION COST is reported only where
    it is exact: when the max fire rate is a measured 0, mu_pad=0 (no Bernoulli variance), so the cost
    is the identical flow-level closed form r*=floor(S*alpha_t)-m+1 (unchanged, no HGB extrapolation).
    Where pads fire (mu_pad>0) the cost is NOT computed -- HGB is non-monotone in the host features so
    a mean-mu proxy would be neither exact nor a bound -- and that regime is reported inconclusive.
    The black-box pad pool is selected on NETWORK-OBSERVABLE FREQUENCY ALONE: the most common
    (proto,dport) over the TRAINING PREFIX [0, i1), which precedes both calibration and deployment --
    no y labels and no detector output, the strictly weakest attacker (review 5, item 3).  Its benign
    fraction is AUDITED (1.00 at both windows) but never used to select it.  Two non-black-box rules
    are kept as a recorded pool_sensitivity; the earlier 0.43 stress-window graft firing came from one
    of them, which at 0.85 selects a pool that is only ~12% benign.

  Premise -- a well-powered estimate independent of how many episodes e-LOND flags: over a large
    sample of malicious episodes, score ordinary pool pads under each episode's causal at-end context
    and report the aggregate fire rate (the host analogue of t48's "20,000 pool flows fire 0").

Produces out/t49_R7.json.
"""
import numpy as np, json, time
from pathlib import Path
from sklearn.metrics import roc_auc_score
from sklearn.ensemble import HistGradientBoostingClassifier
import h_stream as hs
import h_meta as hm
from h6_procs import Ctx, make_gamma, run_lond

A = 0.05; W0 = 0.025; K = 1; BUCKET = 2 * 3600
POS = [0.55, 0.85]
SEED = 0
N_PAD_SAMPLE = 20000
N_PREMISE_EPISODES = 200          # malicious episodes for the well-powered fire-rate premise
PAD_FEASIBLE_CAP = 100000         # accumulation levels are swept up to min(r*, this): pads must fit
#                                   the 2h bucket, so testing beyond a feasible count is not required
FAIL_CONN = {"S0", "REJ", "RSTO", "RSTR", "RSTRH", "SH", "SHR"}   # failed / aborted handshakes
FORBIDDEN = ["label_src", "label_dst", "ext_src", "ext_dst"]      # endpoint ground-truth -> leakage
FEAT_NAMES = ["src_cnt", "src_ddst", "src_failfrac", "dst_cnt", "dst_dsrc", "dst_failfrac"]
N_FLOW_FEATS = 33                 # proto + 32 flow stats (h_stream _FEAT); X_aug must be 33+6


# --------------------------------------------- strict-timestamp causal host features --------------
def _sum_before_ts(group, ts, val):
    """For each i: sum of val over rows sharing `group` with STRICTLY smaller ts (ties excluded).

    The global arrays are ts-sorted, so a stable argsort by group keeps ts non-decreasing within each
    group.  Rows sharing a (group, ts) form a block; every row in a block gets the cumulative sum as
    of the block's start, minus the group's base -- i.e. only strictly-earlier-ts same-group rows.
    """
    order = np.argsort(group, kind="stable")
    g = group[order]; t = ts[order]; v = val[order].astype(np.float64)
    cs = np.cumsum(v)
    prevcs = np.concatenate([[0.0], cs[:-1]])                 # inclusive sum up to the previous row
    newblock = np.ones(len(g), bool)
    newblock[1:] = (g[1:] != g[:-1]) | (t[1:] != t[:-1])      # new (group,ts) block
    blkid = np.cumsum(newblock) - 1
    strict_incl = prevcs[newblock][blkid]                     # sum of everything before this block
    firstgrp = np.ones(len(g), bool); firstgrp[1:] = g[1:] != g[:-1]
    grp_base = prevcs[firstgrp][np.cumsum(firstgrp) - 1]      # sum before this group began
    before = strict_incl - grp_base                           # same-group, strictly-earlier-ts
    out = np.empty(len(val), np.float64); out[order] = before
    return out


def _count_before_ts(group, ts):
    return _sum_before_ts(group, ts, np.ones(len(group), np.float64))


def _distinct_before_ts(g, other, ts):
    """Distinct `other` values among same-`g` rows with strictly-earlier ts."""
    Bo = int(other.max()) + 1
    pair = g.astype(np.int64) * Bo + other.astype(np.int64)
    _, fi = np.unique(pair, return_index=True)                # first occurrence of each pair (by idx)
    fo = np.zeros(len(g), np.float64); fo[fi] = 1.0
    return _sum_before_ts(g, ts, fo)                          # ties excluded -> strict-ts distinct


def build_host_features(src, dst, ts, is_fail):
    """Six strict-ts-causal per-flow host-context features; float32, row-aligned to the flow arrays."""
    src_cnt = _count_before_ts(src, ts)
    dst_cnt = _count_before_ts(dst, ts)
    F = {
        "src_cnt": src_cnt,
        "src_ddst": _distinct_before_ts(src, dst, ts),
        "src_failfrac": _sum_before_ts(src, ts, is_fail) / np.maximum(src_cnt, 1.0),
        "dst_cnt": dst_cnt,
        "dst_dsrc": _distinct_before_ts(dst, src, ts),
        "dst_failfrac": _sum_before_ts(dst, ts, is_fail) / np.maximum(dst_cnt, 1.0),
    }
    return np.column_stack([F[n] for n in FEAT_NAMES]).astype(np.float32)


def _validate_features(H, src, dst, ts, is_fail, n_hosts=6, per=250):
    """Strict-ts brute-force check on BOTH sides, biased to hosts with tied timestamps."""
    ci = {n: i for i, n in enumerate(FEAT_NAMES)}
    bad = 0
    rng = np.random.default_rng(0)
    tied = np.flatnonzero(np.diff(ts) == 0)
    for host_arr, other_arr, cnt, ddist, ff in (
            (src, dst, "src_cnt", "src_ddst", "src_failfrac"),
            (dst, src, "dst_cnt", "dst_dsrc", "dst_failfrac")):
        pool = np.unique(host_arr[tied]) if tied.size else np.unique(host_arr)
        for h in rng.choice(pool, min(n_hosts, len(pool)), replace=False):
            rows = np.flatnonzero(host_arr == h)[:per]
            for i in rows:
                e = rows[ts[rows] < ts[i]]                    # STRICTLY earlier ts, same host
                bad += int(H[i, ci[cnt]] != len(e))
                bad += int(abs(H[i, ci[ddist]] - len(set(other_arr[e].tolist()))) > 1e-4)
                bad += int(abs(H[i, ci[ff]] - (is_fail[e].sum() / max(len(e), 1))) > 1e-4)
    return bad


# --------------------------------------------- e-LOND levels --------------------------------------
def elond_levels(ctx, T):
    g1, _ = make_gamma("poly", T)
    fired = np.zeros(T, dtype=bool)
    run_lond(ctx, g1, fired=fired)
    R_before = np.concatenate([[0], np.cumsum(fired)[:-1]]).astype(float)
    alpha_t = A * g1[np.arange(1, T + 1)] * (R_before + 1.0)
    with np.errstate(divide="ignore"):
        tau_t = np.where(alpha_t > 0, 1.0 / alpha_t, np.inf)
    return fired, alpha_t, tau_t


def fit_host_detector(Xaug, y, i1, seed):
    """HGB on the augmented matrix, same hyperparameters as h_stream.fit_detector('hgb')."""
    tr = hs.train_index(y, i1, seed)
    return HistGradientBoostingClassifier(
        max_iter=200, learning_rate=0.1, l2_regularization=1.0, min_samples_leaf=200,
        random_state=seed, early_stopping=False).fit(Xaug[tr], y[tr])


def _score_chunked(clf, Xaug, a, b, chunk=2_000_000):
    out = np.empty(b - a)
    for s in range(a, b, chunk):
        e = min(s + chunk, b); out[s - a:e - a] = clf.decision_function(Xaug[s:e])
    return out


def _fire_rate(clf, pad_flowstats, ctx_vec, thr, CEIL):
    """Fire rate of ordinary pad flow-stats all grafted with a single context vector (strict >)."""
    padH = np.tile(np.asarray(ctx_vec, np.float32), (pad_flowstats.shape[0], 1))
    s = clf.decision_function(np.concatenate([pad_flowstats, padH], axis=1).astype(np.float32))
    fired = s > thr
    return float(fired.mean()), float(np.where(fired, CEIL, 0.0).mean())


def _episode_base_state(src, dst, ts, is_fail, s_star, d_star, t_end):
    """Real causal state of the (s_star, d_star) pair at episode end (ts <= t_end), from the global
    arrays.  Returns [src_cnt, src_ddst, src_failfrac, dst_cnt, dst_dsrc, dst_failfrac] and the raw
    counts/fails needed to replay pad accumulation."""
    sm = (src == s_star) & (ts <= t_end)
    dm = (dst == d_star) & (ts <= t_end)
    src_cnt = int(sm.sum()); dst_cnt = int(dm.sum())
    src_fail = int((sm & is_fail).sum()); dst_fail = int((dm & is_fail).sum())
    src_ddst = int(np.unique(dst[sm]).size); dst_dsrc = int(np.unique(src[dm]).size)
    base = [src_cnt, src_ddst, src_fail / max(src_cnt, 1),
            dst_cnt, dst_dsrc, dst_fail / max(dst_cnt, 1)]
    return np.array(base, np.float32), dict(src_cnt=src_cnt, src_fail=src_fail, src_ddst=src_ddst,
                                            dst_cnt=dst_cnt, dst_fail=dst_fail, dst_dsrc=dst_dsrc)


def _replay_ctx(raw, k, pad_fail_frac):
    """Context an appended k-th pad (src*->dst*) sees: counts += (k-1) prior pads, ddst/dsrc PINNED
    (no new peer), fail fractions updated by the pool's pad fail rate.  k>=1."""
    add = k - 1
    sc = raw["src_cnt"] + add; dc = raw["dst_cnt"] + add
    sf = raw["src_fail"] + pad_fail_frac * add; df = raw["dst_fail"] + pad_fail_frac * add
    return np.array([sc, raw["src_ddst"], sf / max(sc, 1),
                     dc, raw["dst_dsrc"], df / max(dc, 1)], np.float32)


def main():
    t0 = time.time()
    Path("out").mkdir(exist_ok=True)
    X, y, ts, src, dst = hs.load()
    meta, cats = hm.load()
    hm.verify(meta, src, dst, n=2_000_000)                # must not raise
    N = len(y)
    dport_all = hs.load_extra("dport")
    fail_codes = [i for i, c in enumerate(cats["conn"]) if c in FAIL_CONN]
    is_fail = np.isin(meta["conn"], fail_codes)           # global, row-aligned

    t48 = json.load(open("out/t48_W3.json")) if Path("out/t48_W3.json").exists() else None
    def t48_median_r(pos):                                 # flow-level suppression cost, for comparison
        if not t48: return None
        rec = t48["episodes"].get(f"{pos}")
        return float(np.median([r["r_closed"] for r in rec["per_episode"]])) if rec and rec["per_episode"] else None

    # documented leakage guard: the endpoint columns are excluded from features (verified attack-rate)
    leakage = {}
    for c in FORBIDDEN:
        v = meta[c]; pv = 1 if 1 in np.unique(v) else int(np.unique(v)[-1]); m = v == pv
        leakage[c] = dict(value=int(pv), n=int(m.sum()), attack_rate=float(y[m].mean()))

    # Part A: strict-ts causal host features (once, over the whole stream), validated both sides -----
    tf = time.time()
    H = build_host_features(src, dst, ts, is_fail.astype(np.float64))
    n_bad = _validate_features(H, src, dst, ts, is_fail)
    if n_bad:
        raise AssertionError(f"strict-ts feature builder disagrees with brute force on {n_bad} rows")
    if H.shape[1] != len(FEAT_NAMES):
        raise AssertionError("host feature width mismatch")
    corr = {n: float(np.corrcoef(H[:, i], y)[0, 1]) for i, n in enumerate(FEAT_NAMES)}
    print(f"  strict-ts host features built+validated ({n_bad} mismatches, both sides) "
          f"[{time.time()-tf:.0f}s]  max|corr(y)|={max(abs(v) for v in corr.values()):.3f}")

    premise, partB, partC, ood = {}, {}, {}, {}
    for pos in POS:
        i1, i2, i3 = hs.split_indices(N, pos)
        y_cal, y_te = y[i1:i2], y[i2:i3]
        ts_w, src_w, dst_w = ts[i2:i3], src[i2:i3], dst[i2:i3]
        dp_w = dport_all[i2:i3]; pr_w = np.asarray(X[i2:i3, 0]).astype(np.int32)

        # flow-only baseline (competence contrast) --------------------------------------------------
        score0 = hs.fit_detector(X, y, i1, seed=SEED, kind="hgb", verbose=False)
        s0_cal, s0_te = hs.score_windows(score0, X, i1, i2, i3)
        e0_te, _, NC0, CEIL0 = hs.evalues(s0_cal, y_cal, s0_te, k=K)
        auroc0 = float(roc_auc_score(y_te, s0_te)) if np.unique(y_te).size == 2 else None

        # host-conditioned detector on X_aug = [X | H]  (assert width & provenance) ------------------
        Xaug = np.concatenate([np.asarray(X), H], axis=1).astype(np.float32)
        assert Xaug.shape[1] == N_FLOW_FEATS + len(FEAT_NAMES), "X_aug must be 33 flow + 6 host cols"
        clf = fit_host_detector(Xaug, y, i1, SEED)
        sH_cal = _score_chunked(clf, Xaug, i1, i2); sH_te = _score_chunked(clf, Xaug, i2, i3)
        eH_te, calH, NCH, CEILH = hs.evalues(sH_cal, y_cal, sH_te, k=K)
        aurocH = float(roc_auc_score(y_te, sH_te)) if np.unique(y_te).size == 2 else None
        thr = calH[NCH - K] if NCH >= K else np.inf           # fire iff score strictly > this
        del Xaug

        # OOD anchor: on REAL data the detector barely fires on benign flows. Any grafted attack-
        # context pad firing is therefore an out-of-distribution extrapolation -- LSPR23's attacked
        # pairs are 100% malicious, so there is no real ordinary-flow-to-attacked-victim to validate.
        benm = y_te == 0
        nben = int(benm.sum())
        host_bf = int((eH_te[benm] > 0).sum()); flow_bf = int((e0_te[benm] > 0).sum())
        ood[f"{pos}"] = dict(
            pos=pos, n_benign=nben,
            host_real_benign_fires=host_bf, host_real_benign_fire_rate=host_bf / max(nben, 1),
            flow_real_benign_fires=flow_bf, flow_real_benign_fire_rate=flow_bf / max(nben, 1))

        # Part B: competence + e-LOND detections ----------------------------------------------------
        def elond_det(e_te, CEIL):
            ep = hs.build_episodes(e_te, y_te, ts_w, src_w, dst_w, BUCKET, "src-dst")
            ctx = Ctx(ep["Ev"], ep["ismal"], CEIL, alpha=A, w0=W0)
            fired, alpha_t, tau_t = elond_levels(ctx, ep["T"])
            return ep, fired, alpha_t, tau_t, np.flatnonzero(fired & ep["ismal"])
        ep0, _, _, _, det0 = elond_det(e0_te, CEIL0)
        epH, firedH, alpha_tH, tau_tH, detH = elond_det(eH_te, CEILH)
        tailH = float((eH_te[y_te == 1] > 0).mean())
        partB[f"{pos}"] = dict(
            pos=pos, NC_host=int(NCH), CEIL_host=float(CEILH),
            flow_only=dict(auroc=auroc0, tail_reach=float((e0_te[y_te == 1] > 0).mean()),
                           elond_detections=int(det0.size)),
            host=dict(auroc=aurocH, tail_reach=tailH, elond_detections=int(detH.size)),
            competent=bool(detH.size > 0 and aurocH and aurocH > 0.9))
        print(f"  pos={pos} PartB: host AUROC={aurocH:.4f} tail={tailH:.3f} det={detH.size} | "
              f"flow-only AUROC={auroc0:.4f} det={det0.size}  [{time.time()-t0:.0f}s]")

        # BLACK-BOX pad pool (review 5, item 3): selected on NETWORK-OBSERVABLE FREQUENCY ALONE --
        # the most common (proto,dport) over the traffic that PRECEDES deployment.  The previous rule
        # (most common among flows the DETECTOR does not fire on) used detector output, which a
        # black-box attacker does not have; this one uses no labels and no detector, and t48 records
        # that it selects the same service.  Pool membership is likewise unfiltered by detector output.
        svc = pr_w.astype(np.int64) * 100000 + dp_w.astype(np.int64)
        svc_tr = (np.asarray(X[:i1, 0]).astype(np.int64) * 100000
                  + dport_all[:i1].astype(np.int64))
        uu, cc = np.unique(svc_tr, return_counts=True); bb_svc = int(uu[np.argmax(cc)])
        pool_idx = np.flatnonzero(svc == bb_svc)
        rng = np.random.default_rng(SEED)
        take = pool_idx if pool_idx.size <= N_PAD_SAMPLE else rng.choice(pool_idx, N_PAD_SAMPLE, replace=False)
        pad_flowstats = np.asarray(X[i2 + take])
        pool_fail_frac = float(is_fail[i2 + pool_idx].mean())    # measured pad fail rate (replay)
        pool_benign_frac = float((y_te[pool_idx] == 0).mean())  # AUDIT (labels used only to audit,
        #   never as a feature): confirm the black-box pool really is ordinary benign traffic.

        # Alternative selection rules, kept ONLY as a sensitivity: the pool choice is a real degree of
        # freedom and a badly chosen pool can fire under grafted attack context.  Neither is black-box
        # -- (a) reads detector output, (b) reads the window the attacker is flooding -- so neither is
        # the attacker model we claim; they bound how much the conclusion depends on the choice.
        _nf = eH_te == 0
        _u, _c = np.unique(svc[_nf], return_counts=True); alt_nonfire = int(_u[np.argmax(_c)])
        _u, _c = np.unique(svc, return_counts=True); alt_winmode = int(_u[np.argmax(_c)])
        alt_pools = {}
        for _nm, _code, _mask in (("detector-non-firing modal [uses detector output]",
                                   alt_nonfire, _nf & (svc == alt_nonfire)),
                                  ("window-modal, all flows [attacker's own flood]",
                                   alt_winmode, svc == alt_winmode)):
            _idx = np.flatnonzero(_mask)
            if _idx.size == 0 or _code == bb_svc:
                continue
            _tk = _idx if _idx.size <= N_PAD_SAMPLE else rng.choice(_idx, N_PAD_SAMPLE, replace=False)
            alt_pools[_nm] = dict(service_code=_code, n=int(_idx.size),
                                  flowstats=np.asarray(X[i2 + _tk]),
                                  fail_frac=float(is_fail[i2 + _idx].mean()),
                                  benign_frac=float((y_te[_idx] == 0).mean()))
        ben_med_tr = np.median(H[:i1][y[:i1] == 0], axis=0)     # train-prefix benign median (ablation)

        gid = epH["gid"]; order = epH["order"]; S = epH["sum_e"]; m = epH["nsz"]

        # Premise: fire rate over many MALICIOUS episodes, at each pair's causal at-end context ------
        mal_eps = np.flatnonzero(epH["ismal"])
        take_eps = mal_eps if mal_eps.size <= N_PREMISE_EPISODES else \
            rng.choice(mal_eps, N_PREMISE_EPISODES, replace=False)
        fired_any = 0; scored = 0; ctx_examples = []
        for j in take_eps:
            members = np.flatnonzero(gid == order[j])
            s_star = int(src_w[members[0]]); d_star = int(dst_w[members[0]])
            t_end = int(ts_w[members].max())
            base, _ = _episode_base_state(src, dst, ts, is_fail, s_star, d_star, t_end)
            fr, _ = _fire_rate(clf, pad_flowstats, base, thr, CEILH)
            fired_any += int(round(fr * pad_flowstats.shape[0])); scored += pad_flowstats.shape[0]
            if len(ctx_examples) < 3:
                ctx_examples.append([float(z) for z in base])
        premise[f"{pos}"] = dict(
            pos=pos, n_mal_episodes=int(mal_eps.size), n_episodes_sampled=int(take_eps.size),
            n_pad_scorings=int(scored), pad_fire_rate=float(fired_any / max(scored, 1)),
            bb_service_code=int(bb_svc), pool_size=int(pool_idx.size), pool_fail_frac=pool_fail_frac,
            pool_benign_frac=pool_benign_frac, context_examples=ctx_examples)
        print(f"  pos={pos} Premise: {scored:,} scorings over {take_eps.size} mal-episodes "
              f"(at-end context), fire_rate={premise[f'{pos}']['pad_fire_rate']:.6f} "
              f"pool_fail={pool_fail_frac:.3f}  [{time.time()-t0:.0f}s]")

        # Part C: causal accumulation replay.  For each detected episode we densely sweep the append
        # k=1..min(r*,cap) (counts rise, src_ddst/dst_dsrc pinned, fail fractions at the pool's
        # measured rate) and take the max pad fire rate.  The SUPPRESSION COST is reported only where
        # it is exact: when the max fire rate is a measured 0, every pad contributes e=0 so mu_pad=0
        # and r*=floor(S*alpha_t)-m+1 is the identical flow-level closed form (no HGB extrapolation).
        # When pads fire (mu_pad>0) the cost is NOT computed here -- HGB is non-monotone in the host
        # features, so a mean-mu proxy would be neither exact nor a bound; that regime is reported as
        # inconclusive.  At a firing episode we ablate each host feature (neutralise to the train-
        # benign median) to attribute the firing.
        recs = []; abl = {n: [] for n in FEAT_NAMES}
        for j in detH:
            members = np.flatnonzero(gid == order[j])
            s_star = int(src_w[members[0]]); d_star = int(dst_w[members[0]])
            t_end = int(ts_w[members].max())
            base, raw = _episode_base_state(src, dst, ts, is_fail, s_star, d_star, t_end)
            Sj, mj, tauj = float(S[j]), int(m[j]), float(tau_tH[j])
            r_star = int(np.floor(Sj / tauj - mj)) + 1 if Sj / tauj - mj >= 0 else 0
            kmax = max(1, min(r_star, PAD_FEASIBLE_CAP))       # pads must fit the bucket -> feasible cap
            levels = np.unique(np.clip(np.round(np.geomspace(1, kmax, 120)).astype(int), 1, kmax))
            max_fr = 0.0; arg_ctx = _replay_ctx(raw, 1, pool_fail_frac)
            for k in levels:
                cx = _replay_ctx(raw, int(k), pool_fail_frac)
                fr, _ = _fire_rate(clf, pad_flowstats, cx, thr, CEILH)
                if fr > max_fr:
                    max_fr = fr; arg_ctx = cx
            # exact cost only when pads fire a measured 0 (mu_pad=0 -> flow-level closed form); else NA
            r_suppress = r_star if max_fr == 0.0 else None
            if max_fr > 1e-3:                                  # attribute the firing to a feature
                for fi, nm in enumerate(FEAT_NAMES):
                    cc = arg_ctx.copy(); cc[fi] = ben_med_tr[fi]
                    frn, _ = _fire_rate(clf, pad_flowstats, cc, thr, CEILH)
                    abl[nm].append(max_fr - frn)               # drop when this feature is neutralised
            recs.append(dict(ep=int(j), m=mj, r_star_flowlevel=r_star, r_suppress_host=r_suppress,
                             n_levels=int(len(levels)), kmax=int(kmax), max_pad_fire=max_fr,
                             base_ctx=[float(z) for z in base]))

        # pool sensitivity: max graft fire under the non-black-box selection rules, same episodes
        alt_fire = {}
        for _nm, _p in alt_pools.items():
            _mx = 0.0
            for j in detH:
                members = np.flatnonzero(gid == order[j])
                s_star = int(src_w[members[0]]); d_star = int(dst_w[members[0]])
                _, raw = _episode_base_state(src, dst, ts, is_fail,
                                             s_star, d_star, int(ts_w[members].max()))
                Sj, mj, tauj = float(S[j]), int(m[j]), float(tau_tH[j])
                r_star = int(np.floor(Sj / tauj - mj)) + 1 if Sj / tauj - mj >= 0 else 0
                kmax = max(1, min(r_star, PAD_FEASIBLE_CAP))
                for k in np.unique(np.clip(np.round(np.geomspace(1, kmax, 40)).astype(int), 1, kmax)):
                    fr, _ = _fire_rate(clf, _p["flowstats"],
                                       _replay_ctx(raw, int(k), _p["fail_frac"]), thr, CEILH)
                    _mx = max(_mx, fr)
            alt_fire[_nm] = dict(service_code=_p["service_code"], pool_size=_p["n"],
                                 pool_benign_frac=_p["benign_frac"], max_pad_fire=float(_mx))
            print(f"  pos={pos} pool sensitivity: {_nm:<48} proto {_p['service_code']//100000}/"
                  f"port {_p['service_code']%100000} -> max graft fire {_mx:.3f} "
                  f"(pool {100*_p['benign_frac']:.2f}% benign)")

        n_det = int(detH.size)
        fr_arr = np.array([r["max_pad_fire"] for r in recs]) if recs else np.array([])
        max_graft_fire = float(fr_arr.max()) if fr_arr.size else None
        r_ok = [r["r_suppress_host"] for r in recs if r["r_suppress_host"] is not None]
        med_r_host = float(np.median(r_ok)) if r_ok else None          # exact (mu_pad=0) cost, where clean
        med_r_t48 = t48_median_r(pos)                                  # flow-level cost for comparison
        mean_drop = {n: (float(np.mean(abl[n])) if abl[n] else None) for n in FEAT_NAMES}
        responsible = None
        if max_graft_fire and max_graft_fire > 1e-3:
            cand = {n: d for n, d in mean_drop.items() if d is not None and d > 0}
            responsible = max(cand, key=cand.get) if cand else None
        # OOD guard: grafted-pad firing is credible defense only if the detector ALSO fires on REAL
        # benign flows.  Real-benign firing ~0 with grafted firing > 0 => out-of-distribution
        # extrapolation (attacked pairs are 100% malicious), unresolvable on LSPR23 -> needs a testbed.
        real_bf = ood[f"{pos}"]["host_real_benign_fire_rate"]
        graft_fires = bool(max_graft_fire is not None and max_graft_fire > 1e-3)
        ood_extrapolation = bool(graft_fires and real_bf < 1e-4)
        if n_det == 0:
            verdict = "not competent (no detections to attack)"
        elif not graft_fires:
            verdict = "holds (ordinary pads fire ~0 across accumulation; padding still dilutes)"
        elif ood_extrapolation:
            verdict = ("inconclusive-OOD (grafted attack-context pads fire only by extrapolation; "
                       "detector fires on ~0 real benign flows -- boundary needs a testbed)")
        else:
            verdict = "fails (grafted pads fire, and the detector also fires on real benign traffic)"
        # suppression cost: exact where mu_pad=0 (fire=0), else not cleanly computable
        n_cost_clean = len(r_ok)
        cost_note = ("unchanged: mu_pad=0, identical flow-level closed form" if n_cost_clean == n_det and n_det
                     else ("not computable where pads fire (OOD/contaminated)" if n_cost_clean < n_det
                           else None))
        partC[f"{pos}"] = dict(
            pos=pos, n_detected=n_det, pad_feasible_cap=PAD_FEASIBLE_CAP,
            max_pad_fire=max_graft_fire, transfer_verdict=verdict, ood_extrapolation=ood_extrapolation,
            host_real_benign_fire_rate=real_bf,
            n_cost_computable=n_cost_clean, median_r_suppress_host=med_r_host,
            median_r_star_flowlevel=med_r_t48, cost_note=cost_note,
            ablation_mean_fire_drop=mean_drop, responsible_feature=responsible,
            blackbox_service_code=int(bb_svc), blackbox_pool_benign_frac=pool_benign_frac,
            pool_sensitivity=alt_fire, per_episode=recs)
        print(f"  pos={pos} PartC: max graft_fire={max_graft_fire} responsible={responsible} "
              f"| REAL benign fire={ood[f'{pos}']['host_real_benign_fires']}/{ood[f'{pos}']['n_benign']:,} "
              f"({real_bf:.2e}) | cost r*={med_r_host}(host)/{med_r_t48}(flow) [{cost_note}] "
              f"-> {verdict}  [{time.time()-t0:.0f}s]")

    out = dict(
        config=dict(POS=POS, SEED=SEED, bucket_s=BUCKET, k=K, w0=W0, alpha=A,
                    features=FEAT_NAMES, fail_conn=sorted(FAIL_CONN), forbidden=FORBIDDEN,
                    n_pad_sample=N_PAD_SAMPLE, n_premise_episodes=N_PREMISE_EPISODES,
                    pool="black-box: most common (proto,dport) on the traffic PRECEDING deployment "
                 "(network-observable frequency only -- no labels, no detector output)",
                    proc="e-LOND", gamma="poly", causality="strict ts< (ties excluded)",
                    pad_model="causal accumulation replay, 120 log-spaced levels k=1..min(r*,cap); "
                              "counts rise, src_ddst/dst_dsrc pinned, failfrac at pool's measured rate",
                    pad_feasible_cap=PAD_FEASIBLE_CAP,
                    metric="pad fire rate; suppression cost r* reported only where mu_pad=0 (fire=0) is measured",
                    fire_rule="score strictly > k-th largest benign cal score (matches hs.evalues)"),
        leakage=leakage,
        features=dict(names=FEAT_NAMES, n_validation_mismatches=int(n_bad), corr_with_y=corr),
        premise=premise, partB=partB, partC=partC, ood=ood,
        note=("Host-conditioned HGB on X_aug=[33 flow stats | 6 strict-ts-causal host features]; no "
              "endpoint ground-truth columns or y. Episodes group by (src,dst,bucket) so a diluting "
              "pad shares the attacker's (src*,dst*) pair. Pads are replayed causally over accumulation "
              "(appended pads raise src_cnt/dst_cnt, leave src_ddst/dst_dsrc pinned; fail fractions at "
              "the pool's measured rate); a pad fires iff its score strictly beats the k-th largest "
              "benign calibration score. Pool is black-box: the most common (proto,dport) on the "
              "TRAINING PREFIX [0,i1), which precedes both calibration and deployment -- "
              "network-observable frequency only, no labels and no detector output; its benign "
              "fraction is audited (measured 1.00 at both windows) but never used to select it. "
              "With that pool ordinary pads fire 0 across accumulation at BOTH windows and the "
              "suppression cost is the identical flow-level closed form. The earlier "
              "'grafted pads fire 0.43 at the stress window' was an ARTIFACT of a non-black-box pool "
              "rule (modal service among detector-non-firing flows), which at 0.85 selects TCP/80 -- "
              "only ~12% benign, i.e. mostly the attacker's own flood; see pool_sensitivity, kept as "
              "a recorded sensitivity. LSPR23 still cannot settle the benign-inclusive question at "
              "all (attacked pairs are 100% malicious, so no real ordinary-to-victim traffic exists), "
              "which is what the AIT testbed supplies. Windows 0.55, 0.85."))
    json.dump(out, open("out/t49_R7.json", "w"), indent=1, allow_nan=True)
    print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t49_R7.json")
    return out


if __name__ == "__main__":
    main()
