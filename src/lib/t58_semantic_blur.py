"""R4 -- an EXTERNAL semantic anchor for the resolution (alert-blur) claim.

The granularity result prices coarsening in resolution: each issued alert blurs more of the attack
together.  t47_W7_coverage measures that as `blur_mal_atoms_per_alert` -- distinct 5-minute
(SrcIP,DstIP) MALICIOUS episodes merged into one alert.  The reviewer's objection is exact: the
5-minute atom is OUR OWN proxy for "one attack action", so the exchange rate could be an artefact of
a denominator we chose.  A denominator nobody on this project chose would settle it.

LSPR23 ships one: the red team's own task record (`data/lspr23_attacknarratives.json`, 288 tasks /
576 steps, of which 295 carry a submission timestamp spanning 2023-03-09 07:03-15:08 UTC).  t31 uses
only the step TIMES and the compromise IPs; the task identity, Category, Phase and Segments are
unused.  This stage uses them to count, per issued alert, how many DISTINCT RED-TEAM STEPS and
DISTINCT RED-TEAM TASKS it merges -- a semantic unit defined by the attacker, before the dataset was
published, with no reference to our grouping, our detector or our labels.

THE LINK IS THE SEGMENT VOCABULARY, AND IT IS VERIFIED RATHER THAN ASSUMED.  Each task carries
`Segments` like `bt_baf_int`; the dataset's own per-flow forensic columns carry `seg_src`/`seg_dst`
like `baf_int`.  Stripping the constant `bt_` prefix maps one onto the other, and the mapping is
CHECKED against a channel that does not use it: for every machine-readable compromise report (83 of
them, 39 IPv4, 36 of which appear as a flow endpoint), the dataset segment of that IP's flows is
compared with its parent task's declared Segments.  `seg_agree`/`seg_disagree` below report the
result; the stage refuses to proceed if they disagree.

ATTRIBUTION RULE (pre-committed; both conjuncts required).  A timed red-team step s of task k is
attributed to an issued alert a iff

  (T)  s's submission time lies inside a's bucket span [b*w, (b+1)*w), and
  (S)  k's segment set intersects the segments of a's flows, OR one of k's compromise-report IPs is
       one of a's two endpoints.

WHAT IS MEASURED, against bucket width -- the same x-axis as the granularity figure:
  1. steps and tasks merged per issued alert  (the external analogue of t47's atom blur, recomputed
     here on the SAME fired set so the two curves are comparable rather than merely adjacent)
  2. temporal localisation error |alert bucket midpoint - nearest attributed submission|
  3. task-level coverage: how many red-team tasks any alert touches at all

FOUR CONFOUNDS, MEASURED AND NOT MERELY DECLARED:
  (a) A PERMUTATION NULL.  Segments are coarse -- `beg_dmz` alone carries 5.5M flows -- so a merge
      count could be pure density: every alert overlaps some segment, and some step lands in every
      bucket.  We permute which task each submission time belongs to (holding the times and the task
      attributes fixed, breaking only their pairing) and recompute.  Anything the null reproduces is
      not evidence.  THIS IS THE LOAD-BEARING GUARD, and R4 did not ask for it.
  (b) REPORTING LAG.  A submission time is when the red team REPORTED, not when it acted, so (2) is
      an upper bound with unknown lag.  The compromise reports carry their OWN `Time` field, so the
      lag is estimable: `report_lag_s` below is that distribution.
  (c) CIRCULARITY.  99 of t31's 152 verdicts already rest on label-generating identities.  If every
      attributed alert sits on a labelled-malicious episode, the reference partly re-derives the
      labels rather than testing against them.  `frac_attributed_on_benign` measures it.
  (d) COVERAGE OF THE REFERENCE ITSELF: only 295 of 576 steps are timed, and only 126 of the 155
      tasks with a timed step are attributable at all (the rest declare no segment and file no
      compromise report).  Denominators are reported, never assumed.

Both within-bucket orders are run (review-7 item R3): "keyhash" is the canonical order the paper
reports, "first-flow" the optimistic upper bound.  Writes out/t58_semantic_blur.json.
"""
import numpy as np, json, time, re, math, datetime as dt
from pathlib import Path

import h_stream as hs
import h_meta as hm
from h6_procs import Ctx, make_gamma, run_lond

A = 0.05; W0 = 0.025; K = 1
POS = [0.55, 0.62, 0.70, 0.77, 0.85]
SEED = 0
BUCKETS = [300, 1800, 3600, 7200, 21600, 86400]   # the fig:granularity x-axis
ORDERS = ["keyhash", "first-flow"]                # canonical first (item R3)
ATOMIC_BUCKET = 300                               # t47's proxy unit, recomputed here for comparison
N_NULL = 200
NARR = Path(__file__).resolve().parent / "data" / "lspr23_attacknarratives.json"
UTC = dt.timezone.utc
IPV4 = re.compile(r"\d+\.\d+\.\d+\.\d+")


def _iso(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def load_redteam():
    """Parse the red-team record into per-TASK attributes and per-STEP submission times.

    Returns (tasks, steps).  tasks[k] carries the declared segments (with the constant `bt_` prefix
    stripped, which is the whole of the segment mapping), the compromise-report IPv4 addresses and
    their own reported times, and the category/phase.  steps is a list of (task_index, time)."""
    rows = [json.loads(l) for l in open(NARR) if l.strip()]
    tasks, steps = [], []
    for k, r in enumerate(rows):
        segs = {s.replace("bt_", "") for s in (r.get("Segments") or []) if s}
        ips, rep_times = set(), []
        for c in (r.get("Content") or []):
            c = (c or "").strip()
            if not c.startswith("{"):
                continue
            try:
                d = json.loads(c)
            except Exception:
                continue
            got = {x for x in (d.get("IPs") or []) if IPV4.fullmatch(x)}
            if not got:
                continue
            ips |= got
            if d.get("Time"):
                rep_times.append(_iso(d["Time"]))
        tasks.append(dict(idx=k, segs=segs, ips=ips, report_times=rep_times,
                          category=r.get("Category"), phase=r.get("Phase"),
                          subject=(r.get("Subject") or "")[:60]))
        for t in (r.get("Steps_submitted_time") or []):
            if t:
                steps.append((k, _iso(t)))
    return tasks, steps


def verify_segment_map(tasks, meta, cats):
    """Check the `bt_`-stripping segment map against a channel that does not use it.

    For every compromise IPv4 that appears as a flow endpoint, take the dataset's own modal
    seg_src/seg_dst for that address and ask whether it is among its parent task's DECLARED
    segments.  The two come from different places -- the task record and the dataset's forensic
    columns -- so agreement is evidence the map is right, and disagreement would mean it is not."""
    sip = np.asarray(cats["srcip"]); dip = np.asarray(cats["dstip"])
    ssg = np.asarray(cats["seg_src"]); dsg = np.asarray(cats["seg_dst"])
    srcips = sip[meta["srcip"]]; dstips = dip[meta["dstip"]]
    ssegs = ssg[meta["seg_src"]]; dsegs = dsg[meta["seg_dst"]]
    want = {ip for t in tasks for ip in t["ips"]}
    seg_of = {}
    for ip in want:
        c = {}
        for ips_arr, segs_arr in ((srcips, ssegs), (dstips, dsegs)):
            m = ips_arr == ip
            if m.any():
                u, n = np.unique(segs_arr[m], return_counts=True)
                for a, b in zip(u.tolist(), n.tolist()):
                    c[a] = c.get(a, 0) + int(b)
        if c:
            seg_of[ip] = max(c, key=c.get)
    agree = dis = 0
    for t in tasks:
        if not t["segs"]:
            continue
        for ip in t["ips"]:
            if ip in seg_of:
                agree += 1 if seg_of[ip] in t["segs"] else 0
                dis += 0 if seg_of[ip] in t["segs"] else 1
    return dict(n_compromise_ipv4=len(want), n_present_as_endpoint=len(seg_of),
                seg_agree=agree, seg_disagree=dis), seg_of


def alert_attributes(ep, fired, gid, seg_src, seg_dst, srcip_c, dstip_c, first_ts_g, bucket_s):
    """Per issued alert: its bucket span, the SET of segment codes its flows touch, and its two
    endpoint IP codes.  seg is taken as a set over the alert's own flows rather than from the key,
    because seg_src is not a function of the source address alone for every host."""
    orig = ep["order"][np.flatnonzero(fired)]          # original episode ids of the issued alerts
    if orig.size == 0:
        return (orig, [], [], [], np.empty((0, 2), np.int64), np.empty(0, np.int64))
    sel = np.isin(gid, orig)
    g_sel = gid[sel]
    pos_of = {int(o): i for i, o in enumerate(orig)}
    segsets = [set() for _ in orig]
    segsets_s = [set() for _ in orig]                  # source side alone
    segsets_d = [set() for _ in orig]                  # destination side alone
    idx = np.array([pos_of[int(g)] for g in g_sel], dtype=np.int64)
    for arr, store in ((seg_src[sel], segsets_s), (seg_dst[sel], segsets_d)):
        pair = np.unique(np.stack([idx, arr], 1), axis=0)
        for i, sv in pair:
            store[int(i)].add(int(sv)); segsets[int(i)].add(int(sv))
    # the grouping key is (src, dst, bucket), so every flow of an alert shares its endpoints
    ends = np.zeros((orig.size, 2), np.int64)
    ends[idx, 0] = srcip_c[sel]; ends[idx, 1] = dstip_c[sel]
    bidx = first_ts_g[orig] // (int(bucket_s) * 1_000_000)
    return orig, segsets, segsets_s, segsets_d, ends, bidx


def attribute(step_task, step_time, task_segcode, task_ipcode, segsets, ends, bidx, bucket_s,
              spatial="both"):
    """Attribute timed steps to alerts under the pre-committed rule.

    Returns (steps_per_alert, tasks_per_alert, nearest_gap_s, attributed_alert_mask,
             attributed_task_ids).  A step qualifies for an alert when its submission falls inside
    that alert's bucket span AND its task shares a segment with the alert's flows or names one of
    the alert's two endpoints.

    `spatial` selects WHICH conjunct is applied, so a null result can be read:
      "both"    the pre-committed rule (segment OR compromise IP)
      "none"    TEMPORAL ONLY -- does the alert's bucket contain any timed submission at all?
      "ip"      the STRICT variant: the task must name one of the alert's own two endpoints
      "seg"     the LOOSE variant: segment intersection only
    Comparing "none" against "both" separates "the alerts and the red team never coincide in time"
    (a fact about the controller, since only a feasible prefix can fire) from "the reference is too
    sparse to place them in the same segment" (a fact about the record)."""
    n_a = len(segsets)
    if n_a == 0 or step_time.size == 0:
        return (np.zeros(0, int), np.zeros(0, int), np.zeros(0), np.zeros(0, bool), set())
    lo = bidx * int(bucket_s)                       # bucket span in SECONDS
    hi = lo + int(bucket_s)
    order = np.argsort(step_time)
    st = step_time[order]; sk = step_task[order]
    steps_pa = np.zeros(n_a, int); tasks_pa = np.zeros(n_a, int)
    gap = np.full(n_a, np.nan)
    hit_tasks = set()
    for a in range(n_a):
        i0 = int(np.searchsorted(st, lo[a], "left")); i1 = int(np.searchsorted(st, hi[a], "left"))
        if i1 <= i0:
            continue
        segs_a = segsets[a]; e0, e1 = int(ends[a, 0]), int(ends[a, 1])
        ks = sk[i0:i1]; tms = st[i0:i1]
        if spatial == "none":
            keep = np.ones(len(ks), dtype=bool)
        elif spatial == "ip":
            keep = np.array([bool(task_ipcode[k] & {e0, e1}) for k in ks], dtype=bool)
        elif spatial == "seg":
            keep = np.array([bool(task_segcode[k] & segs_a) for k in ks], dtype=bool)
        else:
            keep = np.array([bool(task_segcode[k] & segs_a) or bool(task_ipcode[k] & {e0, e1})
                             for k in ks], dtype=bool)
        if not keep.any():
            continue
        steps_pa[a] = int(keep.sum())
        tk = set(ks[keep].tolist())
        tasks_pa[a] = len(tk); hit_tasks |= tk
        mid = (lo[a] + hi[a]) / 2.0
        gap[a] = float(np.min(np.abs(tms[keep] - mid)))
    return steps_pa, tasks_pa, gap, steps_pa > 0, hit_tasks


def q(a, p):
    return float(np.percentile(a, p)) if len(a) else None


def main():
    t0 = time.time()
    Path("out").mkdir(exist_ok=True)
    tasks, steps = load_redteam()
    X, y, ts, src, dst = hs.load()
    meta, cats = hm.load()
    align = hm.verify(meta, src, dst)
    N = len(y)

    segmap, _seg_of = verify_segment_map(tasks, meta, cats)
    print(f"  segment map check: {segmap['n_present_as_endpoint']}/{segmap['n_compromise_ipv4']} "
          f"compromise IPv4 appear as a flow endpoint; declared-vs-dataset segment "
          f"{segmap['seg_agree']} agree, {segmap['seg_disagree']} disagree")
    if segmap["seg_disagree"] or segmap["seg_agree"] == 0:
        raise SystemExit("the bt_-stripping segment map is not supported by the compromise reports")

    # ONE code space for each attribute.  h_meta factorises seg_src/seg_dst and srcip/dstip
    # SEPARATELY, so the same string can carry different integers in the two columns; every flow
    # attribute below is therefore remapped into the *source* column's space and task attributes are
    # encoded only there.  (Unioning the two spaces instead would put a dst-column integer into a
    # set compared against src-column integers -- silently correct on this data, because the two
    # vocabularies happen to agree on the six segments the red team names, and silently wrong the
    # moment they do not.)
    seg_codes = {v: i for i, v in enumerate(cats["seg_src"])}
    ip_codes = {v: i for i, v in enumerate(cats["srcip"])}
    d2s = np.array([seg_codes.get(v, -1) for v in cats["seg_dst"]], dtype=np.int64)
    d2sip = np.array([ip_codes.get(v, -1) for v in cats["dstip"]], dtype=np.int64)
    task_segcode = [{seg_codes[v] for v in t["segs"] if v in seg_codes} for t in tasks]
    # srcip and dstip are separate factorisations; everything is compared in the srcip space, so a
    # compromise IP that appears ONLY as a destination has no srcip code and would silently never
    # match.  None do here, but silence is exactly the failure mode this stage is prone to.
    dst_only = {v for t in tasks for v in t["ips"]
                if v not in ip_codes and v in set(cats["dstip"])}
    task_ipcode = [{ip_codes[v] for v in t["ips"] if v in ip_codes} for t in tasks]
    n_seg_unmapped = sum(1 for t in tasks for v in t["segs"] if v not in seg_codes)
    if n_seg_unmapped:
        raise SystemExit(f"{n_seg_unmapped} red-team segment names have no dataset counterpart; "
                         "the bt_-stripping map is incomplete")

    n_timed_tasks = len({k for k, _ in steps})
    n_attributable = len({k for k, _ in steps if task_segcode[k] or task_ipcode[k]})
    print(f"  every red-team segment name maps into the dataset's own seg vocabulary; "
          f"{len(dst_only)} compromise IPs appear only as a destination (unmatchable by endpoint)")
    print(f"  red team: {len(tasks)} tasks, {len(steps)} timed step submissions, "
          f"{n_timed_tasks} tasks with a timed step, {n_attributable} of those attributable "
          f"(declare a segment or file a compromise report)")

    # (b) reporting lag: a compromise report's own Time against its task's step submissions
    lags = []
    for t in tasks:
        subs = [tm for k, tm in steps if k == t["idx"]]
        for rt in t["report_times"]:
            if subs:
                lags.append(min(subs) - rt)
    lag = dict(n=len(lags), median_s=q(lags, 50), q25_s=q(lags, 25), q75_s=q(lags, 75),
               min_s=(float(np.min(lags)) if lags else None),
               max_s=(float(np.max(lags)) if lags else None))
    print(f"  reporting lag (first step submission - compromise report time): n={lag['n']}, "
          f"median {None if lag['median_s'] is None else lag['median_s']/3600:.2f} h "
          f"IQR [{lag['q25_s']/3600:.2f}, {lag['q75_s']/3600:.2f}] h")

    rows, per_pos = [], []
    for pos in POS:
        i1, i2, i3 = hs.split_indices(N, pos)
        w = slice(i2, i3)
        y_te = y[w]; ts_w = ts[w]; src_w = src[w]; dst_w = dst[w]
        seg_s = meta["seg_src"][w].astype(np.int64)
        seg_d = d2s[meta["seg_dst"][w]]             # into the seg_src code space
        ip_s = meta["srcip"][w].astype(np.int64)
        ip_d = d2sip[meta["dstip"][w]]              # into the srcip code space

        w_lo, w_hi = ts_w[0] / 1e6, ts_w[-1] / 1e6
        in_win = [(k, tm) for k, tm in steps if w_lo <= tm <= w_hi]
        step_task = np.array([k for k, _ in in_win], dtype=np.int64)
        step_time = np.array([tm for _, tm in in_win], dtype=float)
        tasks_in_win = {k for k, _ in in_win}
        attributable_in_win = {k for k in tasks_in_win if task_segcode[k] or task_ipcode[k]}

        score = hs.fit_detector(X, y, i1, seed=SEED, kind="hgb", verbose=False)
        s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
        e_te, cal, NC, CEIL = hs.evalues(s_cal, y[i1:i2], s_te, k=K)
        mal_flow = y_te.astype(bool)

        # the 5-minute proxy unit, recomputed here so both curves come from ONE fired set
        atom = hs.build_episodes(e_te, y_te, ts_w, bucket_s=ATOMIC_BUCKET, keys=[src_w, dst_w])
        atomic_gid = atom["gid"]

        print(f"\n  pos={pos}  window {dt.datetime.fromtimestamp(w_lo, UTC):%m-%d %H:%M}"
              f"..{dt.datetime.fromtimestamp(w_hi, UTC):%H:%M} UTC   "
              f"{len(in_win)} timed steps inside, {len(tasks_in_win)} tasks "
              f"({len(attributable_in_win)} attributable)   [{time.time()-t0:.0f}s]")
        print(f"    {'order':<11} {'bucket':>7} {'alerts':>7} {'t-ovl':>6} {'w/step':>7} "
              f"{'steps/al':>9} {'tasks/al':>9} {'null':>7} {'atoms/al':>9} {'loc err h':>10} "
              f"{'taskcov':>8}")

        for order in ORDERS:
            for b in BUCKETS:
                ep = hs.build_episodes(e_te, y_te, ts_w, src_w, dst_w, b, "src-dst", order=order)
                T = ep["T"]
                ctx = Ctx(ep["Ev"], ep["ismal"], CEIL, alpha=A, w0=W0)
                g1, _ = make_gamma("poly", T)
                fired = np.zeros(T, bool)
                rej, tp, silent, first = run_lond(ctx, g1, fired=fired)
                orig, segsets, segsets_s, segsets_d, ends, bidx = alert_attributes(
                    ep, fired, ep["gid"], seg_s, seg_d, ip_s, ip_d, ep["first_ts_g"], b)
                last_ts_g = np.full(T, -1, dtype=np.int64)
                np.maximum.at(last_ts_g, ep["gid"], ts_w)

                spa, tpa, gap, hit, hit_tasks = attribute(
                    step_task, step_time, task_segcode, task_ipcode, segsets, ends, bidx, b)
                # SENSITIVITY 1: the alert's segment set unions seg_src and seg_dst.  Does the union
                # do the work?  Re-attribute against each side alone.
                side = {}
                for nm, ss in (("src", segsets_s), ("dst", segsets_d)):
                    sv, _, _, hv, _ = attribute(step_task, step_time, task_segcode, task_ipcode,
                                                ss, ends, bidx, b, spatial="seg")
                    side[nm] = dict(n_alerts=int(hv.sum()),
                                    steps_per_alert=(float(sv[hv].mean()) if hv.any() else None))
                # SENSITIVITY 2: the bucket span is what the HYPOTHESIS covers; the episode's
                # first-to-last FLOW span is when it actually happened.  Same rule, tighter window.
                flow = None
                if orig.size:
                    fs = ep["first_ts_g"][orig] / 1e6
                    ls = last_ts_g[orig] / 1e6
                    sf = np.zeros(orig.size, int); hf = np.zeros(orig.size, bool)
                    so = np.argsort(step_time); stt = step_time[so]; skk = step_task[so]
                    for a2 in range(orig.size):
                        j0 = int(np.searchsorted(stt, fs[a2], "left"))
                        j1 = int(np.searchsorted(stt, ls[a2], "right"))
                        if j1 <= j0:
                            continue
                        kk = skk[j0:j1]
                        kp = np.array([bool(task_segcode[k] & segsets[a2])
                                       or bool(task_ipcode[k] & {int(ends[a2, 0]),
                                                                 int(ends[a2, 1])}) for k in kk],
                                      dtype=bool)
                        sf[a2] = int(kp.sum()); hf[a2] = kp.any()
                    flow = dict(n_alerts=int(hf.sum()),
                                steps_per_alert=(float(sf[hf].mean()) if hf.any() else None))
                # which conjunct binds?  "none" is the temporal condition alone.
                variants = {}
                for nm in ("none", "seg", "ip"):
                    sv, tv, _, hv, tkv = attribute(step_task, step_time, task_segcode, task_ipcode,
                                                   segsets, ends, bidx, b, spatial=nm)
                    variants[nm] = dict(n_alerts=int(hv.sum()),
                                        steps_per_alert=(float(sv[hv].mean()) if hv.any() else None),
                                        n_tasks=len(tkv))
                # WHEN do the alerts actually sit?  Only a feasible prefix can fire, so the issued
                # alerts cluster at the START of a deployment window; if that start predates the
                # exercise's first submission, no attribution is possible at any bucket width.
                a_span = None
                if orig.size:
                    ft = ep["first_ts_g"][orig] / 1e6
                    a_span = [float(ft.min()), float(ft.max())]

                # t47's proxy blur on the SAME fired set: distinct malicious 5-min atoms per alert
                blur_atoms = None
                sel = np.isin(ep["gid"], orig) & mal_flow
                if sel.any():
                    pair = np.unique(np.stack([ep["gid"][sel], atomic_gid[sel]], 1), axis=0)
                    blur_atoms = float(np.bincount(
                        np.unique(pair[:, 0], return_inverse=True)[1]).mean())

                # (a) TWO nulls.  The LABEL null keeps the times and the task attributes and
                # breaks their pairing -- it asks whether WHICH task acted is informative.  It goes
                # degenerate at the daily bucket, where every submission shares one bucket and no
                # permutation can move a step between alerts.  The SHIFT null instead rotates the
                # whole red-team timeline against the stream, preserving task identity, ordering,
                # attributes and inter-arrival structure, and asks the sharper question: is the
                # alignment IN TIME informative?  That one does not degenerate.
                null_mean = null_hi = shift_mean = shift_hi = None
                if hit.any() and step_task.size > 1:
                    rng = np.random.default_rng(20260902 + int(b))
                    vals = np.empty(N_NULL); sv_ = np.empty(N_NULL)
                    span = float(step_time.max() - step_time.min()) or 1.0
                    for s in range(N_NULL):
                        perm_task = step_task[rng.permutation(step_task.size)]
                        sp, _, _, h, _ = attribute(perm_task, step_time, task_segcode, task_ipcode,
                                                   segsets, ends, bidx, b)
                        vals[s] = float(sp[h].mean()) if h.any() else 0.0
                        off = rng.uniform(0.0, span)
                        shifted = step_time.min() + np.mod(step_time - step_time.min() + off, span)
                        sp2, _, _, h2, _ = attribute(step_task, shifted, task_segcode, task_ipcode,
                                                    segsets, ends, bidx, b)
                        sv_[s] = float(sp2[h2].mean()) if h2.any() else 0.0
                    null_mean = float(vals.mean()); null_hi = q(vals, 97.5)
                    shift_mean = float(sv_.mean()); shift_hi = q(sv_, 97.5)

                # (c) circularity: are attributed alerts only ever on labelled-malicious episodes?
                ismal_alert = ep["ismal"][np.flatnonzero(fired)]
                frac_ben = (float((~ismal_alert[hit]).mean()) if hit.any() else None)

                gg = gap[np.isfinite(gap)]
                rec = dict(
                    pos=pos, order=order, bucket_s=b, T=int(T), n_alerts=int(orig.size),
                    n_alerts_with_step=int(hit.sum()),
                    steps_per_alert=(float(spa[hit].mean()) if hit.any() else None),
                    tasks_per_alert=(float(tpa[hit].mean()) if hit.any() else None),
                    steps_per_alert_null=null_mean, steps_per_alert_null_p975=null_hi,
                    steps_per_alert_shiftnull=shift_mean,
                    steps_per_alert_shiftnull_p975=shift_hi,
                    seg_side_src=side["src"], seg_side_dst=side["dst"], flow_span=flow,
                    blur_mal_atoms_per_alert=blur_atoms,
                    loc_err_median_s=q(gg, 50), loc_err_q25_s=q(gg, 25), loc_err_q75_s=q(gg, 75),
                    n_tasks_touched=len(hit_tasks),
                    n_tasks_attributable_in_window=len(attributable_in_win),
                    task_coverage=(len(hit_tasks) / len(attributable_in_win)
                                   if attributable_in_win else None),
                    frac_attributed_on_benign=frac_ben,
                    temporal_only=variants["none"], seg_only=variants["seg"],
                    ip_only=variants["ip"], alert_first_ts_span=a_span,
                    elond_rej=int(rej), elond_tp=int(tp))
                rows.append(rec)
                f = lambda x, d=2: ("--" if x is None else f"{x:.{d}f}")
                print(f"    {order:<11} {b:>7} {orig.size:>7} "
                      f"{variants['none']['n_alerts']:>6} {int(hit.sum()):>7} "
                      f"{f(rec['steps_per_alert']):>9} {f(rec['tasks_per_alert']):>9} "
                      f"{f(null_mean):>7} {f(blur_atoms):>9} "
                      f"{f(None if rec['loc_err_median_s'] is None else rec['loc_err_median_s']/3600):>10} "
                      f"{f(rec['task_coverage'], 3):>8}")

        per_pos.append(dict(pos=pos, window_start_utc=w_lo, window_end_utc=w_hi,
                            n_steps_in_window=len(in_win), n_tasks_in_window=len(tasks_in_win),
                            n_tasks_attributable=len(attributable_in_win)))

    # does the external curve TRACK the 5-minute proxy?  Spearman over the (pos, bucket) grid,
    # per order, on the rows where both are defined.
    def avg_rank(a):
        """Ranks with TIES AVERAGED.  argsort(argsort(x)) hands tied values arbitrary distinct
        ranks, which turns a flat series into a perfectly monotone one: the 0.77 series
        (3.00, 3.15, 3.15, 3.15) would report Spearman +1.000 against (9.9, 19.6, 21.6, 21.6)
        instead of its true +0.816."""
        a = np.asarray(a, float)
        o = np.argsort(a, kind="mergesort")
        r = np.empty(len(a), float); r[o] = np.arange(len(a), dtype=float)
        srt = a[o]; i = 0
        while i < len(srt):
            j = i
            while j + 1 < len(srt) and srt[j + 1] == srt[i]:
                j += 1
            if j > i:
                r[o[i:j + 1]] = (i + j) / 2.0
            i = j + 1
        return r

    def spearman(a, b):
        a = np.asarray(a, float); b = np.asarray(b, float)
        if len(a) < 3:
            return None
        ra = avg_rank(a); rb = avg_rank(b)
        ra = ra - ra.mean(); rb = rb - rb.mean()
        d = float(np.sqrt((ra * ra).sum() * (rb * rb).sum()))
        return float((ra * rb).sum() / d) if d > 0 else None

    # POOLED over windows is the wrong comparison -- windows sit at different levels, which
    # dilutes the very correlation being tested.  The question "does the external count rise with
    # the alerting unit the way the proxy does?" is WITHIN a window, across bucket widths.
    track, usability = {}, {}
    for order in ORDERS:
        ok = [r for r in rows if r["order"] == order
              and r["steps_per_alert"] is not None and r["blur_mal_atoms_per_alert"] is not None]
        per_window = {}
        for pos in POS:
            w = [r for r in ok if r["pos"] == pos]
            allw = [r for r in rows if r["order"] == order and r["pos"] == pos]
            # why is the reference unusable, where it is?  the two conjuncts fail differently, and
            # only one of them is a fact about our controller.
            t_ovl = sum(a["temporal_only"]["n_alerts"] for a in allw)
            n_al = sum(a["n_alerts"] for a in allw)
            hit = sum(a["n_alerts_with_step"] for a in allw)
            frac_t = (t_ovl / n_al) if n_al else 0.0
            # attribution only at the 24 h bucket is not attribution.  At that width EVERY
            # submission falls in the SAME daily bucket, so permuting which task a time belongs to
            # cannot move a step between alerts -- the permutation is degenerate and the null ties
            # the observation exactly.  (The spatial conjunct is NOT vacuous there: at 0.70
            # first-flow/86400 s the temporal-only arm sees 30 alerts against the segment arm's 12.
            # It is the null that loses its power, not the filter.)  Only sub-daily buckets inform.
            fine = [a for a in allw if a["bucket_s"] < 86400 and a["n_alerts_with_step"] > 0]
            why = ("usable" if len(w) >= 3 else
                   "temporal: issued alerts sit in the feasible prefix, which predates the "
                   "exercise's reporting period" if not fine and frac_t < 0.10 else
                   "spatial: alerts coincide with the exercise in time, but too few tasks in this "
                   "window declare a segment or file a compromise report" if hit == 0 else
                   "thin: attribution at too few bucket widths to read a trend")
            usability[f"{pos}_{order}"] = dict(
                n_buckets_defined=len(w), n_alerts=int(n_al),
                n_alerts_temporally_overlapping=int(t_ovl),
                frac_alerts_temporally_overlapping=float(frac_t),
                n_buckets_below_daily_with_attribution=len(fine),
                n_alerts_attributed=int(hit), verdict=why)
            if len(w) >= 3:
                per_window[f"{pos}"] = dict(
                    n=len(w),
                    steps_vs_atoms=spearman([r["steps_per_alert"] for r in w],
                                            [r["blur_mal_atoms_per_alert"] for r in w]),
                    steps_vs_bucket=spearman([r["steps_per_alert"] for r in w],
                                             [r["bucket_s"] for r in w]),
                    atoms_vs_bucket=spearman([r["blur_mal_atoms_per_alert"] for r in w],
                                             [r["bucket_s"] for r in w]),
                    steps_per_alert=[r["steps_per_alert"] for r in w],
                    atoms_per_alert=[r["blur_mal_atoms_per_alert"] for r in w],
                    buckets=[r["bucket_s"] for r in w])
        track[order] = dict(
            n_pooled=len(ok), per_window=per_window,
            pooled_steps_vs_atoms=spearman([r["steps_per_alert"] for r in ok],
                                           [r["blur_mal_atoms_per_alert"] for r in ok]),
            pooled_atoms_vs_bucket=spearman([r["blur_mal_atoms_per_alert"] for r in ok],
                                            [r["bucket_s"] for r in ok]))
    beats = [r for r in rows if r["steps_per_alert"] is not None
             and r["steps_per_alert_null_p975"] is not None]
    # WHICH conjunct carries the result?  If the compromise-IP arm never adds an alert the whole
    # thing rests on six coarse segment labels, and the paper must say so.
    conj = dict(
        temporal_only_alerts=sum(r["temporal_only"]["n_alerts"] for r in rows),
        seg_only_alerts=sum(r["seg_only"]["n_alerts"] for r in rows),
        ip_only_alerts=sum(r["ip_only"]["n_alerts"] for r in rows),
        attributed_alerts=sum(r["n_alerts_with_step"] for r in rows))
    conj["ip_adds_nothing_over_seg"] = bool(
        conj["attributed_alerts"] == conj["seg_only_alerts"])
    # multiplicity: 19 nested cells, so a raw count of 97.5th-percentile wins overstates.  The
    # honest global statistic is the largest null draw ACROSS cells against the largest observed.
    mx = [(r["steps_per_alert"], r["steps_per_alert_null_p975"]) for r in beats]
    conj["n_cells"] = len(mx)
    conj["binomial_tail_if_independent"] = float(
        sum(math.comb(len(mx), i) * 0.025 ** i * 0.975 ** (len(mx) - i)
            for i in range(sum(1 for o, h in mx if o > h), len(mx) + 1))) if mx else None
    summary = dict(
        n_rows=len(rows),
        n_rows_with_attribution=sum(1 for r in rows if r["n_alerts_with_step"] > 0),
        n_beating_null_p975=sum(1 for r in beats
                                if r["steps_per_alert"] > r["steps_per_alert_null_p975"]),
        n_compared_to_null=len(beats),
        tracking=track, usability=usability, conjuncts=conj,
        n_windows_usable=sum(1 for v in usability.values() if v["verdict"] == "usable"),
        n_window_order_cells=len(usability),
        max_task_coverage=max([r["task_coverage"] for r in rows
                               if r["task_coverage"] is not None] or [None]),
        any_attributed_on_benign=any((r["frac_attributed_on_benign"] or 0) > 0 for r in rows))
    out = dict(
        config=dict(POS=POS, SEED=SEED, BUCKETS=BUCKETS, ORDERS=ORDERS, family="src-dst",
                    atomic_bucket_s=ATOMIC_BUCKET, k=K, alpha=A, w0=W0, n_null=N_NULL,
                    attribution_rule=("timed step s of task k -> alert a iff s's submission lies in "
                                      "a's bucket span AND (k's segments meet a's flow segments OR "
                                      "one of k's compromise IPs is an endpoint of a)"),
                    segment_map="red-team `bt_<seg>` -> dataset seg_src/seg_dst `<seg>`"),
        alignment=align, segment_map_check=segmap, reporting_lag=lag,
        n_compromise_ips_destination_only=len(dst_only),
        redteam=dict(n_tasks=len(tasks), n_timed_steps=len(steps),
                     n_tasks_with_timed_step=n_timed_tasks, n_attributable=n_attributable),
        windows=per_pos, rows=rows, summary=summary)
    json.dump(out, open("out/t58_semantic_blur.json", "w"), indent=1, allow_nan=False)
    print(f"\n  attribution beats its permutation null at {summary['n_beating_null_p975']}"
          f"/{summary['n_compared_to_null']} (pos, order, bucket) cells")
    print(f"  the external reference is usable at {summary['n_windows_usable']}"
          f"/{summary['n_window_order_cells']} (window, order) cells:")
    for k, v in usability.items():
        print(f"    {k:<18} {v['verdict']}")
        print(f"    {'':<18}   alerts {v['n_alerts']}, overlapping in time "
              f"{v['n_alerts_temporally_overlapping']} ({100*v['frac_alerts_temporally_overlapping']:.0f}%), "
              f"attributed {v['n_alerts_attributed']}, sub-daily buckets with attribution "
              f"{v['n_buckets_below_daily_with_attribution']}")
    for o in ORDERS:
        t = track[o]
        print(f"  {o}: WITHIN-window Spearman across bucket widths")
        for pos, w in t["per_window"].items():
            print(f"    pos={pos} (n={w['n']} buckets)  steps/alert vs atoms/alert "
                  f"{w['steps_vs_atoms']:+.3f}   steps vs bucket {w['steps_vs_bucket']:+.3f}   "
                  f"atoms vs bucket {w['atoms_vs_bucket']:+.3f}")
            print(f"       buckets {w['buckets']}")
            print(f"       steps/alert {[round(x,2) for x in w['steps_per_alert']]}")
            print(f"       atoms/alert {[round(x,2) for x in w['atoms_per_alert']]}")
    print(f"  [{time.time()-t0:.0f}s]  wrote out/t58_semantic_blur.json")
    return out


if __name__ == "__main__":
    main()
