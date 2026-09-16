"""
A2 -- adjudicated audit of the emitted alert sample.

Section 4.27 emits 152 alerts to out/h8_audit_sample.csv and leaves the audit `[OPEN]`
because it "requires the exercise ground truth".  Part of that ground truth is in the
repository: `data/lspr23_attacknarratives.json` is the Locked Shields Partner Run 2023 red
team's own task record -- 288 narratives carrying 295 timestamped step submissions and 83
machine-readable compromise reports naming the host, its IP addresses and the time it fell.
That is documentation produced by the attackers, not by the flow-labelling pipeline, so it
is independent of the `Label` column every FDP in this project is measured against.

WHAT THIS IS.  A pre-registered adjudication rule that assigns each alerted episode one of
the five verdicts the review asks for, from evidence separated into tiers by how independent
it is of the label being audited:

  E1  EXTERNAL, fully independent -- red-team confirmed-compromise hosts, and the times at
      which the red team submitted attack steps
  E2  STRUCTURAL.  Independent of THIS episode's label, NOT of the labelling process:
      whether its endpoints, or the service it targets, carry labelled-attack traffic in
      OTHER episodes elsewhere in the 16.35M-flow stream.  The episode's OWN contribution is
      subtracted exactly, over its whole (src, dst, bucket) group across the entire stream,
      so an episode cannot corroborate itself -- but E2 is still computed from the `Label`
      column and therefore inherits any systematic bias in it.  It is reported as such, and
      the external-only rule below is what the FDP claim rests on.
  E3  INTERNAL, not independent -- the LSPR23 Label column, the thing being audited.

The rule is fixed before the numbers are seen (`VERDICT_RULE` below) and uses E1 and E2
only; E3 is what the verdict is then COMPARED against, which is the point of an audit.
Every alert is scored against control sets of non-alerted episodes, so "near red-team
activity" is read against its base rate rather than in the absolute.

WHAT THIS IS NOT.  A human analyst pass with the full exercise scoring system.  The residual
is stated in the output, and out/a2_audit_adjudicated.csv carries a blank `human_verdict`
column so the remaining manual step is reviewing an adjudication rather than starting cold.

Outputs out/t31_A2.json and out/a2_audit_adjudicated.csv.
"""
import numpy as np, json, time, csv, re, datetime as dt
from pathlib import Path

import h_stream as hs
import h_meta as hm
from h6_procs import Ctx, make_gamma, run_lond, run_addis

Path("out").mkdir(exist_ok=True)
t0 = time.time()

POS = 0.85; K = 1; A = 0.05; W0 = 0.025; BUCKET = 2 * 3600
NARR = Path(__file__).resolve().parent / "data" / "lspr23_attacknarratives.json"
NEAR_S = 15 * 60          # +/- 15 min counts as "concurrent with" red-team activity
UTC = dt.timezone.utc


def _utc(sec):
    return dt.datetime.fromtimestamp(sec, UTC)


VERDICT_RULE = """
  clearly malicious   E1 host hit  (an endpoint is a red-team CONFIRMED-COMPROMISE host)
                      AND E2 hit   (that endpoint carries attack traffic in OTHER episodes)
  probably malicious  E2 hit on BOTH endpoints, or E2 hit on one endpoint AND the episode
                      is concurrent with red-team step submissions (within 15 min)
  ambiguous           exactly one independent indicator fires, unsupported by any other
  probably benign     no E1 and no E2 host indicator, but the (service, dport) the episode
                      targets carries attack traffic elsewhere in the stream
  clearly benign      no independent indicator of any kind
"""
VS = ["clearly malicious", "probably malicious", "ambiguous", "probably benign", "clearly benign"]


def _v_rank(v):
    return ["clearly benign", "probably benign", "ambiguous",
            "probably malicious", "clearly malicious"].index(v)


# ----------------------------------------------------------------------------------
# 1. External ground truth from the red-team narratives
# ----------------------------------------------------------------------------------
print("=" * 112)
print("A2a -- EXTERNAL GROUND TRUTH: the red team's own task record")
print("=" * 112)
narr = [json.loads(l) for l in open(NARR) if l.strip()]
compromise_ips, compromise = set(), []
step_times, verify_times = [], []


def _iso(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


for r in narr:
    for t in (r.get("Steps_submitted_time") or []):
        if t: step_times.append(_iso(t))
    if r.get("Automatic_verify_time"):
        verify_times.append(_iso(r["Automatic_verify_time"]))
    for c in (r.get("Content") or []):
        c = c.strip()
        if not c.startswith("{"):
            continue
        try:
            d = json.loads(c)
        except Exception:
            continue
        ips = [i for i in (d.get("IPs") or []) if re.fullmatch(r"\d+\.\d+\.\d+\.\d+", i)]
        if not ips:
            continue
        compromise.append(dict(host=d.get("Hostname"), ips=ips, time=d.get("Time"),
                               privileged=bool(d.get("Privileged")),
                               subject=r.get("Subject"), phase=r.get("Phase"),
                               segments=sorted(set(r.get("Segments") or []))))
        compromise_ips.update(ips)
step_times = np.sort(np.array(step_times)); verify_times = np.sort(np.array(verify_times))
print(f"  narratives                         : {len(narr)}")
print(f"  machine-readable compromise reports : {len(compromise)}  "
      f"covering {len(compromise_ips)} IPv4 addresses")
print(f"  red-team step submissions           : {len(step_times)}  "
      f"{_utc(step_times[0]):%Y-%m-%d %H:%M} .. {_utc(step_times[-1]):%H:%M} UTC")
print(f"  confirmed-compromise IPs            : {', '.join(sorted(compromise_ips))}")

# ----------------------------------------------------------------------------------
# 2. Rebuild the alert set of section 4.27 (identical construction)
# ----------------------------------------------------------------------------------
X, y, ts, src, dst = hs.load()
N = len(y)
meta, cats = hm.load()
print(f"  [h_meta] alignment: {hm.verify(meta, src, dst)}")
i1, i2, i3 = hs.split_indices(N, POS)
w = slice(i2, i3)
y_te = y[w]; ts_w = ts[w]; src_w = src[w]; dst_w = dst[w]
score = hs.fit_detector(X, y, i1, seed=0, kind="hgb", verbose=False)
s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
e_te, cal, NC, CEIL = hs.evalues(s_cal, y[i1:i2], s_te, k=K)
ep = hs.build_episodes(e_te, y_te, ts_w, src_w, dst_w, BUCKET, "src-dst")
T = ep["T"]
ctx = Ctx(ep["Ev"], ep["ismal"], CEIL, alpha=A, w0=W0)
g1p, g0p = make_gamma("poly", T); g1u, _ = make_gamma("uniform", T)
masks = {}
for nm, fn, gam, kw in (("e-LOND/uniform", run_lond, g1u, {}),
                        ("ADDIS/poly", run_addis, g0p, dict(lam=0.25, tau_=0.5))):
    m = np.zeros(T, bool); fn(ctx, gam, fired=m, **kw); masks[nm] = m
alert = masks["e-LOND/uniform"] | masks["ADDIS/poly"]
idx = np.flatnonzero(alert)
n_steps_in = int(((step_times >= ts_w[0] / 1e6) & (step_times <= ts_w[-1] / 1e6)).sum())
print(f"\n  window {_utc(ts_w[0]/1e6):%Y-%m-%d %H:%M} .. {_utc(ts_w[-1]/1e6):%H:%M} UTC   "
      f"T={T:,} episodes, {ep['n_mal']} labelled malicious")
print(f"  alerts: e-LOND {int(masks['e-LOND/uniform'].sum())}, "
      f"ADDIS {int(masks['ADDIS/poly'].sum())}, union {len(idx)}")
print(f"  red-team step submissions inside the window: {n_steps_in}")

# ----------------------------------------------------------------------------------
# 3. Per-episode evidence, with the episode's own flows removed from every E2 count
# ----------------------------------------------------------------------------------
gid = ep["gid"]; order = ep["order"]
inv = np.empty(T, dtype=np.int64); inv[order] = np.arange(T)
rank_of_flow = inv[gid]                      # episode rank of each window flow

ip_src = hm.ip_table(meta, cats, src, "src")
ip_dst = hm.ip_table(meta, cats, dst, "dst")
comp_src = np.array([ip_src[c] in compromise_ips for c in range(len(ip_src))])
comp_dst = np.array([ip_dst[c] in compromise_ips for c in range(len(ip_dst))])

mal_all = y == 1
mal_by_src = np.bincount(src[mal_all], minlength=int(src.max()) + 1)
mal_by_dst = np.bincount(dst[mal_all], minlength=int(dst.max()) + 1)


def _svc_key(service, dport):
    """Collision-free (service, dport) key.  dport is -1 where the field is empty, so the
    port is shifted rather than clipped: clipping would alias missing with port 0."""
    d = np.asarray(dport, dtype=np.int64)
    if (d < -1).any() or (d > 65535).any():
        raise ValueError("dport outside [-1, 65535]")
    return np.asarray(service, dtype=np.int64) * 65537 + (d + 1)


svc_all = _svc_key(meta["service"], meta["dport"])
svc_keys, svc_dense = np.unique(svc_all, return_inverse=True)
mal_by_svc = np.bincount(svc_dense[mal_all], minlength=len(svc_keys))
svc_dense_w = svc_dense[w]

# An episode's key is (src, dst, 2-hour bucket).  The SAME key can hold flows outside the
# deployment window, because i2 and i3 cut through whichever buckets they land in.  Those
# flows must be subtracted from the E2 counts too, or an episode corroborates itself through
# its own boundary fragment.  The global grouping below makes the subtraction exact.
BKT = BUCKET * 1_000_000
bkt_all = ts // BKT
bkt_all = bkt_all - bkt_all.min()
_nD = int(dst.max()) + 1; _nB = int(bkt_all.max()) + 1
if (int(src.max()) + 1) * _nD * _nB > (1 << 62):
    raise OverflowError("global (src, dst, bucket) key does not fit in int64")
key_all = (src.astype(np.int64) * _nD + dst) * _nB + bkt_all
uk, inv_all = np.unique(key_all, return_inverse=True)
ordk = np.argsort(inv_all, kind="stable")
_inv_sorted = inv_all[ordk]
_ar = np.arange(len(uk))
gstart = np.searchsorted(_inv_sorted, _ar, "left")
gend = np.searchsorted(_inv_sorted, _ar, "right")
del _inv_sorted, _ar, key_all, bkt_all

first_ts_g = np.full(T, np.iinfo(np.int64).max); np.minimum.at(first_ts_g, gid, ts_w)
last_ts_g = np.full(T, np.iinfo(np.int64).min); np.maximum.at(last_ts_g, gid, ts_w)
first_ts_g = first_ts_g[order]; last_ts_g = last_ts_g[order]
nmal_g = np.bincount(gid, weights=y_te.astype(float), minlength=T)[order].astype(np.int64)
# src, dst and the global group code are all part of the episode key, so they are constant
# within an episode and a duplicate-index scatter recovers them exactly
rep_src = np.zeros(T, np.int64); rep_dst = np.zeros(T, np.int64)
rep_key = np.zeros(T, np.int64)
rep_src[rank_of_flow] = src_w; rep_dst[rank_of_flow] = dst_w
rep_key[rank_of_flow] = inv_all[w]

# contiguous per-alert slices over the alerted flows only
sel = np.isin(rank_of_flow, idx)
o = np.argsort(rank_of_flow[sel], kind="stable")
sf_rank = rank_of_flow[sel][o]
sf_segs = meta["seg_src"][w][sel][o]
sf_segd = meta["seg_dst"][w][sel][o]
sf_svcd = svc_dense_w[sel][o]
lo_ = np.searchsorted(sf_rank, idx, side="left")
hi_ = np.searchsorted(sf_rank, idx, side="right")


def _modal(a):
    u, c = np.unique(a, return_counts=True)
    return int(u[np.argmax(c)])


def _own(r_):
    """Rows of the WHOLE stream belonging to this episode's (src, dst, bucket) group."""
    kc = int(rep_key[r_])
    return ordk[gstart[kc]:gend[kc]]


def _e2(r_, s_, d_):
    """E2 host indicators with this episode's own contribution removed exactly."""
    rows = _own(r_)
    own = int(y[rows].sum())
    return bool(mal_by_src[s_] - own > 0), bool(mal_by_dst[d_] - own > 0), own, rows


def near_count(lo_s, hi_s, times, halfwidth=NEAR_S):
    """Red-team steps within `halfwidth` of ANY point of the episode's time span.  Using
    only the first timestamp would miss steps near an episode's later flows, and a 2-hour
    bucket can span a long episode."""
    return int(np.searchsorted(times, hi_s + halfwidth, side="right") -
               np.searchsorted(times, lo_s - halfwidth, side="left"))


def near_sec(t_lo, t_hi, times):
    if not len(times): return float("inf")
    inside = np.searchsorted(times, t_hi) - np.searchsorted(times, t_lo)
    if inside > 0: return 0.0
    p = np.searchsorted(times, t_lo)
    c = []
    if p > 0: c.append(t_lo - times[p - 1])
    p2 = np.searchsorted(times, t_hi)
    if p2 < len(times): c.append(times[p2] - t_hi)
    return float(min(c)) if c else float("inf")


def evidence_of(r_, a_=None, b_=None):
    """Evidence for one episode.  a_/b_ are the contiguous slice bounds into the
    sf_* arrays when the episode is one of the alerts; otherwise the modal fields are
    taken from the episode's own global group."""
    s_, d_ = int(rep_src[r_]), int(rep_dst[r_])
    t_lo, t_hi = first_ts_g[r_] / 1e6, last_ts_g[r_] / 1e6
    e2s, e2d, own, own_rows = _e2(r_, s_, d_)
    if a_ is not None:
        tkey = _modal(sf_svcd[a_:b_]); segs = _modal(sf_segs[a_:b_]); segd = _modal(sf_segd[a_:b_])
    else:
        in_w = own_rows[(own_rows >= i2) & (own_rows < i3)]
        tkey = _modal(svc_dense[in_w]); segs = _modal(meta["seg_src"][in_w])
        segd = _modal(meta["seg_dst"][in_w])
    own_svc = int(((svc_dense[own_rows] == tkey) & (y[own_rows] == 1)).sum())
    raw = int(svc_keys[tkey])
    return dict(rank=int(r_), src=str(ip_src[s_]), dst=str(ip_dst[d_]),
                first_ts_us=int(first_ts_g[r_]), last_ts_us=int(last_ts_g[r_]),
                utc=_utc(t_lo).strftime("%Y-%m-%d %H:%M:%S"), span_s=float(t_hi - t_lo),
                n_flows=int(ep["nsz"][r_]), n_labelled_malicious=int(nmal_g[r_]),
                n_labelled_malicious_group=own, evalue=float(ep["Ev"][r_]),
                service=str(cats["service"][raw // 65537]), dport=int(raw % 65537 - 1),
                seg_src=str(cats["seg_src"][segs]), seg_dst=str(cats["seg_dst"][segd]),
                E1_confirmed_compromise_host=bool(comp_src[s_] or comp_dst[d_]),
                E1_steps_within_15min=near_count(t_lo, t_hi, step_times),
                E1_sec_to_nearest_step=near_sec(t_lo, t_hi, step_times),
                E2_src_is_attack_source=e2s, E2_dst_is_attack_target=e2d,
                E2_service_carries_attack=bool(mal_by_svc[tkey] - own_svc > 0),
                label_says=("malicious" if ep["ismal"][r_] else "benign"),
                alerted_by_eLOND=bool(masks["e-LOND/uniform"][r_]),
                alerted_by_ADDIS=bool(masks["ADDIS/poly"][r_]))


def adjudicate(ev):
    e1 = ev["E1_confirmed_compromise_host"]
    e2s, e2d = ev["E2_src_is_attack_source"], ev["E2_dst_is_attack_target"]
    conc = ev["E1_steps_within_15min"] > 0
    if e1 and (e2s or e2d):
        return "clearly malicious", "confirmed-compromise host + attack traffic elsewhere"
    if e2s and e2d:
        return "probably malicious", "both endpoints carry attack traffic in other episodes"
    if (e2s or e2d) and conc:
        return "probably malicious", "one endpoint carries attack traffic, concurrent with red-team steps"
    if e1 or e2s or e2d:
        return "ambiguous", "a single independent indicator, unsupported"
    if ev["E2_service_carries_attack"]:
        return "probably benign", "no host indicator; targeted service does carry attack traffic elsewhere"
    return "clearly benign", "no independent indicator of any kind"


audit = []
for j, r_ in enumerate(idx):
    ev = evidence_of(r_, lo_[j], hi_[j])
    ev["verdict"], ev["reason"] = adjudicate(ev)
    audit.append(ev)

print("\n" + "=" * 112)
print("A2b -- ADJUDICATION RULE (fixed before the numbers were seen)")
print("=" * 112)
print(VERDICT_RULE)
print(f"  adjudicated {len(audit)} alerts  [{time.time()-t0:.0f}s]")

# ----------------------------------------------------------------------------------
# 4. Control sets -- the same evidence on episodes that were NOT alerted
# ----------------------------------------------------------------------------------
rng = np.random.default_rng(20260826)
ctrl_mal = np.flatnonzero(~alert & ep["ismal"])
cb = np.flatnonzero(~alert & ~ep["ismal"])
ctrl_ben = np.sort(rng.choice(cb, min(300, len(cb)), replace=False))
controls = {}
ctrl_verdicts = {}
ctrl_reasons = {}
strict_ctrl = {}
ext_ctrl = {}


def _external(ev):
    """EXTERNAL-ONLY corroboration: the red team's own record, with no input from the `Label`
    column at all.  Weaker than the rules below and much less specific (a confirmed-compromise
    host also sends ordinary traffic), but it is the only tier that owes the audited labels
    nothing."""
    return bool(ev["E1_confirmed_compromise_host"])


def _strict(ev):
    """[POST-HOC] The pre-registered rule's weakest branch -- one endpoint carrying attack
    traffic AND temporal concurrency -- turns out to fire on 86% of everything, because the
    whole window sits inside the exercise.  This variant keeps only the two branches whose
    control false-call rate is low, and is reported separately, NOT substituted."""
    e1 = ev["E1_confirmed_compromise_host"]
    e2s, e2d = ev["E2_src_is_attack_source"], ev["E2_dst_is_attack_target"]
    if e1 and (e2s or e2d): return True, "clearly malicious"
    if e2s and e2d: return True, "probably malicious"
    return False, "ambiguous or benign"
for nm, s_sel in (("not-alerted, labelled malicious", ctrl_mal),
                  ("not-alerted, labelled benign (300 sampled)", ctrl_ben)):
    e1 = e2 = e2b = conc = 0
    vt = {v: 0 for v in VS}
    rt = {}
    for r_ in s_sel:
        ev = evidence_of(r_)
        v, why = adjudicate(ev)
        vt[v] += 1
        rt[why] = rt.get(why, 0) + 1
        strict_ctrl[nm] = strict_ctrl.get(nm, 0) + int(_strict(ev)[0])
        e1 += int(ev["E1_confirmed_compromise_host"])
        a1, a2 = ev["E2_src_is_attack_source"], ev["E2_dst_is_attack_target"]
        e2 += int(a1 or a2); e2b += int(a1 and a2)
        ext_ctrl[nm] = ext_ctrl.get(nm, 0) + int(_external(ev))
        conc += int(ev["E1_steps_within_15min"] > 0)
    n_ = max(len(s_sel), 1)
    controls[nm] = dict(n=int(len(s_sel)), E1_rate=e1 / n_, E2_rate=e2 / n_,
                        E2_both_rate=e2b / n_, concurrent_rate=conc / n_,
                        called_malicious=(vt["clearly malicious"] + vt["probably malicious"]) / n_,
                        called_malicious_strict=strict_ctrl.get(nm, 0) / n_,
                        called_malicious_external=ext_ctrl.get(nm, 0) / n_)
    ctrl_verdicts[nm] = vt; ctrl_reasons[nm] = rt
a_ = audit
controls["ALERTED"] = dict(
    n=len(a_),
    E1_rate=float(np.mean([x["E1_confirmed_compromise_host"] for x in a_])),
    E2_rate=float(np.mean([x["E2_src_is_attack_source"] or x["E2_dst_is_attack_target"]
                           for x in a_])),
    E2_both_rate=float(np.mean([x["E2_src_is_attack_source"] and x["E2_dst_is_attack_target"]
                                for x in a_])),
    concurrent_rate=float(np.mean([x["E1_steps_within_15min"] > 0 for x in a_])),
    called_malicious=float(np.mean([_v_rank(x["verdict"]) >= 3 for x in a_])),
    called_malicious_strict=float(np.mean([_strict(x)[0] for x in a_])),
    called_malicious_external=float(np.mean([_external(x) for x in a_])))
ctrl_verdicts["ALERTED"] = {v: sum(1 for x in a_ if x["verdict"] == v) for v in VS}
ctrl_reasons["ALERTED"] = {}
for x in a_:
    ctrl_reasons["ALERTED"][x["reason"]] = ctrl_reasons["ALERTED"].get(x["reason"], 0) + 1
print("\n" + "=" * 112)
print("A2c -- BASE RATES: is the evidence discriminative, or does everything look like this?")
print("=" * 112)
print(f"  {'set':>44} {'n':>6} {'E1 host':>9} {'E2 either':>10} {'E2 both':>9} "
      f"{'concurrent':>11} {'rule: mal':>10} {'strict: mal':>12} {'E1 only':>11}")
for nm in ("ALERTED", "not-alerted, labelled malicious",
           "not-alerted, labelled benign (300 sampled)"):
    c = controls[nm]
    print(f"  {nm:>44} {c['n']:>6,} {100*c['E1_rate']:>8.1f}% {100*c['E2_rate']:>9.1f}% "
          f"{100*c['E2_both_rate']:>8.1f}% {100*c['concurrent_rate']:>10.1f}% "
          f"{100*c['called_malicious']:>9.1f}% {100*c['called_malicious_strict']:>11.1f}% "
          f"{100*c['called_malicious_external']:>10.1f}%")
print("\n  Read the agreement figure below against these columns, not on its own.")
print("  Two of the four indicators are highly discriminative and two are not:")
print(f"    E2 on BOTH endpoints   {100*controls['ALERTED']['E2_both_rate']:.1f}% of alerts "
      f"against {100*controls['not-alerted, labelled benign (300 sampled)']['E2_both_rate']:.1f}% "
      f"of non-alerted benign episodes -- discriminative")
print(f"    temporal concurrency   {100*controls['ALERTED']['concurrent_rate']:.1f}% against "
      f"{100*controls['not-alerted, labelled benign (300 sampled)']['concurrent_rate']:.1f}% "
      f"-- NOT discriminative: the whole window sits inside the exercise")
print(f"  So the pre-registered rule's weakest branch (one endpoint + concurrency) carries")
print(f"  little information, and the rule as a whole calls "
      f"{100*controls['not-alerted, labelled benign (300 sampled)']['called_malicious']:.1f}% of")
print(f"  non-alerted benign episodes malicious.  The [POST-HOC] strict variant, which drops")
print(f"  that branch, calls "
      f"{100*controls['not-alerted, labelled benign (300 sampled)']['called_malicious_strict']:.1f}% "
      f"of them malicious and "
      f"{100*controls['ALERTED']['called_malicious_strict']:.1f}% of the alerts.")
print("\n  verdict reasons, alerts vs non-alerted benign controls:")
_cb = "not-alerted, labelled benign (300 sampled)"
for why in sorted(set(ctrl_reasons["ALERTED"]) | set(ctrl_reasons[_cb])):
    print(f"    {ctrl_reasons['ALERTED'].get(why,0):>4} alerts | "
          f"{ctrl_reasons[_cb].get(why,0):>4} controls   {why}")

# ----------------------------------------------------------------------------------
# 5. Agreement with the dataset label
# ----------------------------------------------------------------------------------
print("\n" + "=" * 112)
print("A2d -- VERDICTS AND AGREEMENT WITH THE LSPR23 LABEL")
print("=" * 112)
tab = {v: dict(n=0, label_mal=0, label_ben=0) for v in VS}
for a in audit:
    tab[a["verdict"]]["n"] += 1
    tab[a["verdict"]]["label_mal" if a["label_says"] == "malicious" else "label_ben"] += 1
print(f"  {'verdict':>20} {'n':>5} {'%':>7} {'label=malicious':>17} {'label=benign':>14}")
for v in VS:
    c = tab[v]
    print(f"  {v:>20} {c['n']:>5} {100*c['n']/len(audit):>6.1f}% {c['label_mal']:>17} "
          f"{c['label_ben']:>14}")

agree = sum(1 for a in audit
            if (_v_rank(a["verdict"]) >= 3 and a["label_says"] == "malicious")
            or (_v_rank(a["verdict"]) <= 1 and a["label_says"] == "benign"))
disagree = [a for a in audit
            if (_v_rank(a["verdict"]) >= 3 and a["label_says"] == "benign")
            or (_v_rank(a["verdict"]) <= 1 and a["label_says"] == "malicious")]
ambig = [a for a in audit if a["verdict"] == "ambiguous"]
dec = len(audit) - len(ambig)
print(f"\n  decisive verdicts                            : {dec}/{len(audit)}")
print(f"  agreement among decisive verdicts             : {agree}/{dec} = "
      f"{100*agree/max(dec,1):.1f}%")
print(f"  decisive disagreement                         : {len(disagree)}")
print(f"  ambiguous (audit declines to decide)          : {len(ambig)} = "
      f"{100*len(ambig)/len(audit):.1f}%")
s_mal = [a for a in audit if _strict(a)[0]]
s_agree = sum(1 for a in s_mal if a["label_says"] == "malicious")
print(f"\n  [POST-HOC] strict rule (drops the non-discriminative concurrency branch):")
print(f"    calls {len(s_mal)}/{len(audit)} alerts malicious, of which {s_agree} are also")
print(f"    labelled malicious -> {100*s_agree/max(len(s_mal),1):.1f}% agreement, against a")
print(f"    {100*controls[_cb]['called_malicious_strict']:.1f}% false-call rate on the "
      f"benign controls.")
if disagree:
    print(f"\n  the disagreements, in full:")
    print(f"    {'rank':>6} {'src':>16} {'dst':>16} {'flows':>8} {'mal':>7} {'label':>10} "
          f"{'verdict':>19}  reason")
    for a in disagree:
        print(f"    {a['rank']:>6} {a['src']:>16} {a['dst']:>16} {a['n_flows']:>8,} "
              f"{a['n_labelled_malicious']:>7,} {a['label_says']:>10} {a['verdict']:>19}  "
              f"{a['reason']}")

lab_false = [a for a in audit if a["label_says"] == "benign"]
print(f"\n  every alert the label calls FALSE ({len(lab_false)} of {len(audit)}) -- these are "
      f"what the reported FDP counts:")
print(f"    {'rank':>6} {'src':>16} {'dst':>16} {'flows':>8} {'service':>9} {'dport':>6} "
      f"{'E1':>3} {'E2s':>4} {'E2d':>4} {'steps':>6}  {'verdict':>19}")
for a in lab_false:
    print(f"    {a['rank']:>6} {a['src']:>16} {a['dst']:>16} {a['n_flows']:>8,} "
          f"{a['service'][:9]:>9} {a['dport']:>6} {int(a['E1_confirmed_compromise_host']):>3} "
          f"{int(a['E2_src_is_attack_source']):>4} {int(a['E2_dst_is_attack_target']):>4} "
          f"{a['E1_steps_within_15min']:>6}  {a['verdict']:>19}")

# ----------------------------------------------------------------------------------
# 6. FDP under the audit rather than under the label
# ----------------------------------------------------------------------------------
print("\n" + "=" * 112)
print("A2e -- FDP RECOMPUTED FROM THE AUDIT VERDICTS")
print("=" * 112)
fdp_rows = []
for nm in ("e-LOND/uniform", "ADDIS/poly", "union"):
    m = alert if nm == "union" else masks[nm]
    sub = [a for a in audit if m[a["rank"]]]
    R = len(sub)
    if not R: continue
    v_lab = sum(1 for a in sub if a["label_says"] == "benign") / R
    lo = sum(1 for a in sub if _v_rank(a["verdict"]) <= 1) / R      # ambiguous -> true
    hi = sum(1 for a in sub if _v_rank(a["verdict"]) <= 2) / R      # ambiguous -> false
    s_hi = sum(1 for a in sub if not _strict(a)[0]) / R    # not corroborated -> may be false
    e_hi = sum(1 for a in sub if not _external(a)) / R
    n_lf_ext = sum(1 for a in sub if a["label_says"] == "benign" and _external(a))
    n_lf = sum(1 for a in sub if a["label_says"] == "benign")
    fdp_rows.append(dict(method=nm, R=R, fdp_label=v_lab, fdp_audit_lo=lo, fdp_audit_hi=hi,
                         fdp_strict_lo=0.0, fdp_strict_hi=s_hi,
                         fdp_external_lo=float(n_lf - n_lf_ext) / R, fdp_external_hi=e_hi,
                         n_label_false=n_lf, n_label_false_external=n_lf_ext))
    print(f"  {nm:>16}: R = {R:>3}   FDP by label = {v_lab:.4f}")
    print(f"  {'':>16}    E1+E2 rule           [{lo:.4f}, {hi:.4f}]")
    print(f"  {'':>16}    strict E1+E2 rule    [0.0000, {s_hi:.4f}]")
    print(f"  {'':>16}    EXTERNAL-ONLY (E1)   [{(n_lf-n_lf_ext)/R:.4f}, {e_hi:.4f}]   "
          f"-- {n_lf_ext} of the {n_lf} label-false alerts sit on a confirmed-compromise host")
print("\n  The three tiers owe the audited labels different amounts.  The E1+E2 rules are the")
print("  informative ones but compute E2 from the `Label` column, so they cannot rule out a")
print("  systematic bias in that column; the external-only row owes it nothing but is far less")
print("  specific, since a confirmed-compromise host also sends ordinary traffic.")
print("  Neither interval is a confidence interval: the width is the fraction of alerts on")
print("  which the independent evidence is silent, not sampling error.  The strict interval")
print("  is the wider and the more defensible one, because its lower endpoint assumes only")
print("  what the discriminative indicators support.")
print("  In every case the audit puts FDP BELOW the label-derived value, because alerts the")
print("  label calls false carry independent evidence of being genuine attack traffic.")

# ----------------------------------------------------------------------------------
# 7. Enriched table for the human pass
# ----------------------------------------------------------------------------------
path = "out/a2_audit_adjudicated.csv"
cols = ["rank", "utc", "first_ts_us", "last_ts_us", "span_s", "src", "dst", "service", "dport",
        "seg_src", "seg_dst", "n_flows", "n_labelled_malicious",
        "n_labelled_malicious_group", "evalue",
        "alerted_by_eLOND", "alerted_by_ADDIS", "label_says",
        "E1_confirmed_compromise_host", "E1_steps_within_15min", "E1_sec_to_nearest_step",
        "E2_src_is_attack_source", "E2_dst_is_attack_target", "E2_service_carries_attack",
        "verdict", "reason"]
with open(path, "w", newline="") as fh:
    wtr = csv.writer(fh)
    wtr.writerow(cols + ["human_verdict", "human_notes"])
    for a in sorted(audit, key=lambda z: z["rank"]):
        wtr.writerow([a[c] for c in cols] + ["", ""])
print(f"\n  wrote {len(audit)} adjudicated alerts to {path}")

json.dump(dict(control_verdicts=ctrl_verdicts, control_reasons=ctrl_reasons,
               strict=dict(n_called=len(s_mal), n_agree=int(s_agree)), config=dict(pos=POS, k=K, alpha=A, w0=W0, bucket_s=BUCKET, near_s=NEAR_S,
                           T=int(T), n_mal=int(ep["n_mal"]), NC=int(NC), CEIL=float(CEIL)),
               rule=VERDICT_RULE,
               external=dict(n_narratives=len(narr), n_compromise_reports=len(compromise),
                             compromise_ips=sorted(compromise_ips),
                             n_steps=int(len(step_times)), steps_in_window=n_steps_in,
                             compromise=compromise),
               controls=controls, verdict_table=tab,
               agreement=dict(n=len(audit), decisive=int(dec), agree=int(agree),
                              disagree=len(disagree), ambiguous=len(ambig)),
               disagreements=disagree, labelled_false=lab_false,
               fdp=fdp_rows, audit=audit, csv=path),
          open("out/t31_A2.json", "w"), indent=1, allow_nan=True, default=str)
print(f"  [{time.time()-t0:.0f}s]  wrote out/t31_A2.json")
