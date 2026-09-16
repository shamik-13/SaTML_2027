"""R7-AIT-suppression -- the FULL Surface A pipeline on the benign-inclusive AIT testbed, with
REAL ordinary-to-victim padding flows REPLAYED against the running controller level (no graft).

Motivation (reviewer item 5).  t51 shows the pad-SCORING premise transfers to a benign-inclusive
host-conditioned setting.  This stage runs, per organisation, the complete chain:

    flow (or host-conditioned) detector, leave-one-org-out, features chosen PER FOLD from the
    training orgs only -> chronological in-org benign conformal calibration (calibration flows
    strictly PRECEDE deployment) -> episodes (src-dst 2h) -> e-LOND detections -> suppress each
    detected malicious episode by REPLAYING real ordinary-to-victim benign flows until the group's
    mean evidence falls below 1/level -> empirical min/median suppression cost r* and success rate.

The two arms replay pads differently, because the two detectors read different things:

  FLOW-ONLY arm -- flow features carry no context, so a pad's evidence does not depend on how many
    pads preceded it.  Pads are drawn with replacement from the pool's OBSERVED 0-or-M evidence
    (empirical_rstar).  A firing pad contributes the maximum e-value M and RAISES the cost, which is
    exactly what the zero-pad closed form misses.

  HOST-CONDITIONED arm -- the six host features ARE causal (prior-flow counts, distinct peers,
    failure fractions), so appending pads changes the context every later pad is scored in.  Holding
    them fixed would be a static-context diagnostic, not a replay (review 5, item 9).  We therefore
    port t49's accumulation model: the k-th appended pad sees the attacked pair's real causal state
    at episode end with counts raised by (k-1), distinct-peer counts PINNED (the attacker pads from a
    host already talking to the victim, so no new peer appears -- this models a SINGLE attacker-victim
    pair and excludes botnet / new-host padding), and failure fractions moved toward the pool's
    measured rate.  Scoring the whole pool under that context gives a fire curve p_k, and the replay
    draws the k-th pad as firing with probability p_k (empirical_rstar_causal).

  A success is only reported over the accumulation range the curve was actually EVALUATED at; an
  episode whose cost exceeds that reach is returned unvalidated rather than given the closed form.

Writes out/t54_ait_suppression.json.
"""
import numpy as np, json, time, glob, os, hashlib
from pathlib import Path
from sklearn.metrics import roc_auc_score

import h_stream as hs
from h6_procs import Ctx, make_gamma, run_lond
import t51_R7_ait as t51
import t49_R7_host_detector as t49

BUCKET_US = 2 * 3600 * 1_000_000     # 2-hour bucket; AIT ts is in microseconds
K = 1; A = 0.05; W0 = 0.025
D_REPLAY = 200                       # random pad-replay draws per detected episode
# Host-conditioned chain runs on EVERY organisation by default (reviewer round 31): restricting it to a
# chosen pair leaves the arm open to the reading that the folds were selected for their outcome.
# ORGS_HOST=a,b in the environment narrows it, for a partial re-run only.
_OH = os.environ.get("ORGS_HOST", "").strip()
ORGS_HOST = [x for x in _OH.split(",") if x] or None   # None -> all organisations
N_CTX_LEVELS = 60                    # geometric accumulation levels at which the causal context is scored
CTX_MARGIN = 2                       # evaluate the context curve out to this multiple of the needed cost
SIM_CAP = 3_000_000                  # memory bound on a single simulated draw (not a claim boundary)


def build_evalues(s_cal, s_te, k=K):
    """Threshold conformal e-value: e = CEIL * 1{score strictly above the k-th largest cal score}."""
    cal = np.sort(s_cal); NC = len(cal)
    CEIL = (NC + 1.0) / k
    Kr = 1 + (NC - np.searchsorted(cal, s_te, side='left'))
    e = np.where(Kr <= k, CEIL, 0.0)
    return e, NC, CEIL


def episodes(e_te, y_te, ts_te, src_te, dst_te, order="first-flow"):
    """Group deployment flows into (src,dst,2h-bucket) episodes.

    `order` is the pre-committed within-bucket sequence: "first-flow" arrival (the default, and what
    every previously reported AIT number uses) or "keyhash", the canonical metadata hash the LSPR23
    results report.  The canonical branch calls h_stream's key_hash/hashed_order directly rather than
    reimplementing them, so the two datasets cannot drift apart in what "canonical" means."""
    bucket = ts_te // BUCKET_US
    key = np.stack([src_te, dst_te, bucket], axis=1)
    _, gid = np.unique(key, axis=0, return_inverse=True)
    T = int(gid.max() + 1)
    sum_e = np.bincount(gid, weights=e_te, minlength=T)
    nsz = np.bincount(gid, minlength=T).astype(np.int64)
    mal = np.bincount(gid, weights=y_te.astype(float), minlength=T)
    first_ts = np.full(T, np.iinfo(np.int64).max); np.minimum.at(first_ts, gid, ts_te)
    first_pos = np.full(T, np.iinfo(np.int64).max)
    np.minimum.at(first_pos, gid, np.arange(len(gid), dtype=np.int64))
    last_ts = np.full(T, -1, dtype=np.int64); np.maximum.at(last_ts, gid, ts_te)
    gsrc = np.zeros(T, dtype=np.int64); gsrc[gid] = src_te     # every flow of a group shares the key
    gdst = np.zeros(T, dtype=np.int64); gdst[gid] = dst_te
    gbucket = np.zeros(T, dtype=np.int64); gbucket[gid] = bucket
    if order == "first-flow":
        ordr = np.lexsort((first_pos, first_ts))
    elif order == "keyhash":
        ordr = hs.hashed_order(hs.key_hash(gsrc, gdst, gbucket, seed=0), gsrc, gdst, gbucket)
    else:
        raise ValueError(f"unknown order {order!r}")
    return dict(Ev=(sum_e / np.maximum(nsz, 1))[ordr], ismal=(mal > 0)[ordr],
                nsz=nsz[ordr].astype(np.int64), sum_e=sum_e[ordr], T=T,
                src=gsrc[ordr], dst=gdst[ordr], last_ts=last_ts[ordr], order_kind=order)


def empirical_rstar(S, m, lvl, pad_e, rng, D=D_REPLAY):
    """Minimal number r of REAL replayed pads (each carrying its true 0-or-M evidence, sampled with
    replacement from the observed ordinary-to-victim pool pad_e) that pushes (S + sum pad_e)/(m+r)
    below 1/lvl.  Returns the empirical min/median r* and the success rate over D draws.  With a
    zero-firing pool this collapses to the closed form floor(S*lvl)-m+1; a firing pad ADDS M and so
    raises the cost, which is exactly what the closed form misses."""
    thr = 1.0 / lvl
    closed = int(np.floor(S * lvl)) - m + 1
    if S / max(m, 1) < thr:                    # already suppressed (should not happen for a detection)
        return dict(median=0.0, min=0, success=1.0, closed=closed, pad_fire=0.0)
    pfire = float((pad_e > 0).mean()) if len(pad_e) else 0.0
    if pfire == 0.0:                           # no firing pad observed -> deterministic zero-pad cost
        r = max(closed, 1)
        return dict(median=float(r), min=int(r), success=1.0, closed=closed, pad_fire=0.0)
    cap = max(closed * 6, 1000)                # generous per-draw budget
    rr = np.arange(1, cap + 1)
    rs = []
    for _ in range(D):
        seq = rng.choice(pad_e, size=cap, replace=True)   # replay real ordinary-to-victim flows
        mean_after = (S + np.cumsum(seq)) / (m + rr)
        hit = np.flatnonzero(mean_after < thr)
        if hit.size:
            rs.append(int(hit[0] + 1))
    if not rs:
        return dict(median=None, min=None, success=0.0, closed=closed, pad_fire=pfire)
    return dict(median=float(np.median(rs)), min=int(min(rs)),
                success=float(len(rs) / D), closed=closed, pad_fire=pfire)


def causal_fire_curve(clf, pad_flowstats, raw, pool_fail, thr, kmax):
    """p_k: the fraction of the real ordinary-to-victim pool that FIRES when appended as the k-th pad,
    under the victim's CAUSALLY UPDATED host context.

    This is what makes the host-conditioned arm a real replay rather than a static-context diagnostic:
    appending pads raises the victim's prior-flow count (and the attacker host's), moves both failure
    fractions toward the pool's rate, and leaves the distinct-peer counts pinned (padding one victim
    from a host already talking to it adds no new peer) -- exactly t49's accumulation model, applied
    here to AIT.  Evaluated on a geometric grid and held piecewise-constant between grid points."""
    levels = np.unique(np.clip(np.round(np.geomspace(1, max(kmax, 1), N_CTX_LEVELS)).astype(np.int64),
                               1, max(kmax, 1)))
    p = np.array([t49._fire_rate(clf, pad_flowstats,
                                 t49._replay_ctx(raw, int(k), pool_fail), thr, 1.0)[0]
                  for k in levels])
    return levels, p


def empirical_rstar_causal(S, m, lvl, levels, p_curve, CEIL, rng, D=D_REPLAY, cap=None):
    """Replay with a CAUSAL context: the k-th pad fires with probability p_k read off `p_curve`.
    Otherwise identical to empirical_rstar -- a firing pad contributes the maximum e-value M and
    RAISES the cost.  With a flat curve this reduces exactly to the static replay.

    A suppression is only ever reported as successful over the accumulation range the context curve
    was actually EVALUATED on: `levels[-1]` is the largest k at which the pool was scored, and any
    outcome requiring more pads than that is returned as unvalidated (median None, success 0) with
    `validated_to` recording the reach.  Reporting the deterministic closed form past that point
    would assume the context stays benign at accumulation levels never scored."""
    thr = 1.0 / lvl
    closed = int(np.floor(S * lvl)) - m + 1
    reach = int(levels[-1])
    meta = dict(closed=closed, validated_to=reach,
                pad_fire_k1=float(p_curve[0]), pad_fire_max=float(p_curve.max()))
    if S / max(m, 1) < thr:
        return dict(median=0.0, min=0, success=1.0, capped=False, **meta)
    cap = int(min(cap or max(closed * 6, 1000), reach))     # never simulate past the evaluated reach
    rr = np.arange(1, cap + 1)
    pk = p_curve[np.searchsorted(levels, rr, side="right") - 1]   # piecewise-constant in k
    if pk.max() == 0.0:                                # no firing pad anywhere in the scored range
        r = max(closed, 1)
        if r > reach:                                  # cost lies beyond what we scored -> unvalidated
            return dict(median=None, min=None, success=0.0, capped=True, **meta)
        return dict(median=float(r), min=int(r), success=1.0, capped=False, **meta)
    rs = []
    for _ in range(D):
        seq = np.where(rng.random(cap) < pk, CEIL, 0.0)
        mean_after = (S + np.cumsum(seq)) / (m + rr)
        hit = np.flatnonzero(mean_after < thr)
        if hit.size:
            rs.append(int(hit[0] + 1))
    if not rs:
        return dict(median=None, min=None, success=0.0, capped=True, **meta)
    return dict(median=float(np.median(rs)), min=int(min(rs)), success=float(len(rs) / D),
                capped=bool(len(rs) < D), **meta)


def fold_rng(test, use_host, order):
    """A generator keyed to (organisation, arm, order), not to position in the run.

    ROUND 31: the host arm was extended from a hard-coded pair to all eight organisations.  With one
    mutable generator threaded through every fold, the pool subsampling and replay draws a fold sees
    depend on which folds ran before it, so adding organisations silently perturbs the ones already
    reported and no subset can be re-run on its own.  Keying the seed to the fold makes each row a
    function of its own organisation, arm and order alone, which is what lets the eight-fold run
    reproduce the pair exactly, lets any subset be re-run for checking, and makes t67's
    order-resequencing arms reproduce this stage's first-flow rows by construction."""
    h = hashlib.sha256(f"t54|{test}|{'host' if use_host else 'flow'}|{order}".encode()).digest()
    return np.random.default_rng(int.from_bytes(h[:8], "big"))


def run_org(test, scen, names, common_by_fold, use_host, rng=None, order="first-flow"):
    """Full chain for one held-out org; use_host augments the flow features with causal host context.
    `order` selects the within-bucket sequence; everything before the episode build is order-free."""
    rng = fold_rng(test, use_host, order)  # fold-keyed; the passed-in `rng` is deliberately ignored
    common = common_by_fold[test]          # features chosen from the TRAINING orgs of this fold
    s = scen[test]; y = s["y"]; ts = s["ts"]
    n_mal = int(y.sum())
    if n_mal < 5:
        return None

    def feats(o):
        Xf = scen[o]["Xnum"][common].to_numpy(dtype=np.float32)
        return np.concatenate([Xf, scen[o]["H"]], axis=1).astype(np.float32) if use_host else Xf

    Xtr = np.vstack([feats(o) for o in names if o != test])
    ytr = np.concatenate([scen[o]["y"] for o in names if o != test])
    clf = t51.fit(Xtr, ytr)
    score_all = clf.decision_function(feats(test))
    try:
        auroc = float(roc_auc_score(y, score_all))
    except ValueError:
        auroc = float("nan")

    # chronological split: calibrate on benign flows strictly BEFORE the first attack; deploy after
    atk_ts = ts[y == 1]; t_split = int(atk_ts.min())
    cal_mask = (ts < t_split) & (y == 0); dep_mask = ts >= t_split
    if cal_mask.sum() < 2000 or dep_mask.sum() < 50 or int(y[dep_mask].sum()) < 3:
        return dict(org=test, use_host=use_host, auroc=auroc, skipped="insufficient cal/dep split")
    e_te, NC, CEIL = build_evalues(score_all[cal_mask], score_all[dep_mask])
    y_te = y[dep_mask]; ts_te = ts[dep_mask]
    ep = episodes(e_te, y_te, ts_te, s["src"][dep_mask], s["dst"][dep_mask], order=order)

    ctx = Ctx(ep["Ev"], ep["ismal"], CEIL, alpha=A, w0=W0)
    g1, _ = make_gamma("poly", ctx.T)
    fired = np.zeros(ctx.T, bool)
    rej, tp, sil, _ = run_lond(ctx, g1, fired=fired)
    det = fired & ep["ismal"]; n_det = int(det.sum())

    # real ordinary-to-victim pad pool: benign deployment flows to an attacked victim, same detector
    dep_dst_ip = s["dst_ip"][dep_mask]
    pad_mask = (y_te == 0) & np.isin(dep_dst_ip, list(s["victims"]))
    pad_e = e_te[pad_mask]
    pad_fire = float((pad_e > 0).mean()) if pad_mask.sum() else float("nan")

    tag = "host" if use_host else "flow"
    print(f"  [{test:11s}|{tag}] AUROC={auroc:.3f}  T={ep['T']:,} ep, {int(ep['ismal'].sum())} mal, "
          f"NC={NC:,}, CEIL={CEIL:,.0f} -> e-LOND {rej} rej, {tp} true, {n_det} det; "
          f"pad-pool {int(pad_mask.sum()):,} flows fire {pad_fire:.2e}")

    # price each detected episode by REPLAYING real pads at their true evidence
    base_lvl = np.zeros(ctx.T); R = 0
    for tstep in range(1, ctx.T + 1):
        lvl = A * g1[tstep] * (R + 1); base_lvl[tstep - 1] = lvl
        if not ctx.infeasible(lvl) and ep["Ev"][tstep - 1] >= 1.0 / lvl:
            R += 1
    # For the HOST-CONDITIONED arm the pad's own evidence is not a fixed draw: appending pads changes
    # the victim's causal host context, hence the score of every later pad.  We therefore replay the
    # context causally (t49's accumulation model) rather than holding the host features fixed.
    causal = None
    if use_host:
        thr_score = float(np.sort(score_all[cal_mask])[-K])     # fires iff score STRICTLY exceeds it
        pad_rows = np.flatnonzero(dep_mask)[np.flatnonzero(pad_mask)]
        if pad_rows.size > 5000:
            pad_rows = rng.choice(pad_rows, 5000, replace=False)
        pad_flowstats = scen[test]["Xnum"][common].to_numpy(dtype=np.float32)[pad_rows]
        isf = np.asarray(scen[test]["is_fail"]).astype(bool)   # t49's helpers take a boolean mask
        pool_fail = float(isf[pad_rows].mean()) if pad_rows.size else 0.0
        causal = dict(thr=thr_score, flowstats=pad_flowstats, pool_fail=pool_fail,
                      src=s["src"], dst=s["dst"], ts=ts, is_fail=isf)

    emp_med, emp_min, closed, closed_all, succ = [], [], [], [], []
    fire_k1, fire_max, validated, n_capped = [], [], [], 0
    for j in np.flatnonzero(det):
        Sj, mj, lvlj = ep["sum_e"][j], int(ep["nsz"][j]), base_lvl[j]
        if causal is not None and causal["flowstats"].shape[0]:
            # score the context curve out PAST the cost the episode needs, so a success is never
            # asserted at an accumulation level the pool was not actually scored at
            kcurve = int(max((int(np.floor(Sj * lvlj)) - mj + 1) * CTX_MARGIN, 1000))
            _, raw = t49._episode_base_state(causal["src"], causal["dst"], causal["ts"],
                                             causal["is_fail"], int(ep["src"][j]), int(ep["dst"][j]),
                                             int(ep["last_ts"][j]))
            lv, pc = causal_fire_curve(clf, causal["flowstats"], raw, causal["pool_fail"],
                                       causal["thr"], kcurve)
            r = empirical_rstar_causal(Sj, mj, lvlj, lv, pc, CEIL, rng, cap=SIM_CAP)
            fire_k1.append(r["pad_fire_k1"]); fire_max.append(r["pad_fire_max"])
            validated.append(r["validated_to"]); n_capped += int(r["capped"])
        else:
            r = empirical_rstar(Sj, mj, lvlj, pad_e, rng)
        succ.append(r["success"]); closed_all.append(r["closed"])   # zero-pad lower bound, all detected
        if r["median"] is not None:                                  # suppressible within budget
            emp_med.append(r["median"]); emp_min.append(r["min"]); closed.append(r["closed"])
    row = dict(org=test, use_host=use_host, auroc=auroc,
               replay=("causal host-context accumulation" if use_host else "flow features, context-free"),
               causal_pad_fire_first=(float(np.median(fire_k1)) if fire_k1 else None),
               causal_pad_fire_max=(float(max(fire_max)) if fire_max else None),
               causal_validated_to_min=(int(min(validated)) if validated else None),
               causal_n_capped=(n_capped if use_host else None),
               T=int(ep["T"]),
               n_mal_ep=int(ep["ismal"].sum()), NC=int(NC), CEIL=float(CEIL),
               elond_rej=int(rej), elond_true=int(tp), n_detected=n_det, n_suppressible=len(emp_med),
               real_pad_fire_rate=pad_fire, n_pad_candidates=int(pad_mask.sum()),
               median_rstar_empirical=(float(np.median(emp_med)) if emp_med else None),
               median_rstar_closedform=(float(np.median(closed)) if closed else None),  # suppressible set
               median_rstar_closedform_alldet=(float(np.median(closed_all)) if closed_all else None),
               min_rstar_empirical=(int(min(emp_min)) if emp_min else None),
               mean_success_rate=(float(np.mean(succ)) if succ else None),
               rstar_empirical_values=[float(x) for x in emp_med[:50]])
    if n_det:
        sr = row["mean_success_rate"]
        if emp_med:
            print(f"        empirical median r*={row['median_rstar_empirical']} "
                  f"(closed-form {row['median_rstar_closedform']}), min={row['min_rstar_empirical']}, "
                  f"suppressible {len(emp_med)}/{n_det}, mean success {sr:.3f}")
        else:
            print(f"        SUPPRESSION FAILS: 0/{n_det} episodes suppressible within budget "
                  f"(real pads fire {pad_fire:.2%} -- too often to dilute the mean); mean success {sr:.3f}")
    return row


def main():
    t0 = time.time()
    Path("out").mkdir(exist_ok=True)
    t51.ensure_extracted()
    paths = sorted(glob.glob(f"{t51.AIT_DIR}/*/tcp_complete.csv"))
    names = [Path(p).parent.name for p in paths]
    print(f"  loading {len(names)} AIT scenarios: {names}")
    scen = {n: t51.load_scenario(p) for n, p in zip(names, paths)}
    # PER-FOLD feature selection from the TRAINING orgs only, mirroring t51: taking the intersection
    # over every org (the held-out one included) would let the test org's own column availability
    # choose the feature set -- a transductive leak in a leave-one-org-out design.
    common = {test: sorted(set.intersection(*[scen[n]["good"] & set(scen[n]["Xnum"].columns)
                                              for n in names if n != test]))
              for test in names}
    print(f"  per-fold flow features: "
          f"{min(len(v) for v in common.values())}--{max(len(v) for v in common.values())} "
          f"(training orgs only)  [{time.time()-t0:.0f}s]")

    out = {"config": dict(bucket_s=BUCKET_US // 1_000_000, k=K, alpha=A, w0=W0,
                          n_features={k: len(v) for k, v in common.items()}, orgs=names, orgs_host=(ORGS_HOST or names), d_replay=D_REPLAY,
                          calibration="chronological: in-org benign flows strictly BEFORE first attack",
                          pad="REAL ordinary-to-victim benign flows REPLAYED at true 0-or-M evidence")}
    rng = None                             # each fold draws its own generator (fold_rng)

    print("\n  == FLOW-ONLY detector, all orgs ==")
    flow_rows = [r for test in names if (r := run_org(test, scen, names, common, False, rng))]
    orgs_host = ORGS_HOST or names
    print(f"\n  == HOST-CONDITIONED detector, end-to-end, orgs {orgs_host} ==")
    host_rows = [r for test in orgs_host if test in scen
                 and (r := run_org(test, scen, names, common, True, rng))]

    det_flow = [o for o in flow_rows if o.get("n_detected", 0) > 0]
    det_host = [o for o in host_rows if o.get("n_detected", 0) > 0]
    out["flow"] = flow_rows
    out["host"] = host_rows
    out["summary"] = dict(
        n_orgs_with_detection_flow=len(det_flow),
        orgs_detected_flow=[o["org"] for o in det_flow],
        median_rstar_empirical_flow={o["org"]: o["median_rstar_empirical"] for o in det_flow},
        median_rstar_closedform_flow={o["org"]: o["median_rstar_closedform"] for o in det_flow},
        host_end_to_end={o["org"]: dict(detected=o["n_detected"],
                                        median_rstar_empirical=o["median_rstar_empirical"],
                                        real_pad_fire_rate=o["real_pad_fire_rate"],
                                        success=o["mean_success_rate"]) for o in det_host},
        max_real_pad_fire=max((o["real_pad_fire_rate"] for o in flow_rows
                               if o.get("real_pad_fire_rate") == o.get("real_pad_fire_rate")),
                              default=None))
    json.dump(out, open("out/t54_ait_suppression.json", "w"), indent=1, allow_nan=True)
    print(f"\n  flow-only: {len(det_flow)} orgs detect; host end-to-end on "
          f"{', '.join(o['org'] for o in det_host) or 'none'}")
    print(f"  [{time.time()-t0:.0f}s]  wrote out/t54_ait_suppression.json")
    return out


if __name__ == "__main__":
    main()
