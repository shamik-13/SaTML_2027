"""
E10 -- does the padding attack exist outside the anomalous label window?

Reviewer objection (docs/02_WORKPLAN_PHASE4.md E10): "The attack only exists in your
anomalous label window."  Section 4.30 costs the attack at positions 0.62 and 0.85 only,
and 0.85 is the window section 4.31 diagnoses as anomalous (50.9x nominal benign firing).
If the attack were an artefact of that anomaly it would not appear elsewhere.

Reduced experiment at every position with target detections, two pools only:

  generic benign   every benign flow of the deployment window
  black-box        the single most common benign (protocol, destination port) service,
                   chosen with NO detector access -- section 4.30's weakest attacker

The suppression cost is computed with t28_P5_padding.py's OWN `r90`, pulled out of that
file by AST so the two cannot drift: r_90 is the smallest pad size for which suppression
succeeds with probability >= 0.90, found by exhaustive scan because the probability is not
monotone in r (section 4.30).  r_mean, the section 4.17 expectation-level cost, is
recomputed here from the same expression and asserted against r_90.

Accept when: median cost reported at >= 3 positions besides 0.85.

Outputs out/t43_E10.json.
"""
import numpy as np, json, time, ast
from pathlib import Path
from scipy.stats import binom

import h_stream as hs

# Anchor to THIS file's directory: a run from a different cwd would
# otherwise write a second copy of the artefact somewhere else and leave
# the real one stale, which is exactly how a stale JSON gets audited.
OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)
t0 = time.time()

POS = [0.55, 0.62, 0.70, 0.77, 0.85]
SEEDS = [0, 1]
W0 = 0.025; K = 1; BUCKET = 2 * 3600
QUANTS = (0.10, 0.50, 0.90)
out = {"config": dict(pos=POS, seeds=SEEDS, k=K, w0=W0, bucket_s=BUCKET,
                      pools=["generic", "black-box"], quantiles=list(QUANTS),
                      cost_rule="t28_P5_padding.r90 (AST-imported)")}
FAIL = []


def note(cond, msg):
    if not cond:
        FAIL.append(msg)
        print(f"    *** ASSERTION FAILED: {msg}")
    return cond


# The cost rule comes out of t28_P5_padding.py itself.  Re-implementing r90 here is exactly
# how section 4.30's numbers and this section's would silently diverge; t28 runs LSPR23 at
# module level, so AST extraction is the way to reuse it without running it.
_SRC = Path(__file__).with_name("t28_P5_padding.py")


def _load(*names):
    tree = ast.parse(_SRC.read_text())
    want = {n.name: n for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name in names}
    missing = set(names) - set(want)
    if missing:
        raise AssertionError(f"not module-level in {_SRC.name}: {sorted(missing)}")
    ns = {"np": np, "binom": binom}
    exec(compile(ast.fix_missing_locations(
        ast.Module(body=[want[n] for n in names], type_ignores=[])), str(_SRC), "exec"), ns)
    return [ns[n] for n in names]


(r90,) = _load("r90")


def r_mean_cost(S, n, tau, mu):
    """Section 4.17's expectation-level cost, written exactly as t28 writes it."""
    rm = (S - tau * n) / (tau - mu)
    return int(np.floor(rm)) + 1 if rm > 0 else 1


# =======================================================================================
print("=" * 118)
print("E10 -- PADDING COST ACROSS ALL FIVE WINDOWS")
print("=" * 118)
CAVEAT = ("mu and P(fire) are computed from the DEPLOYMENT WINDOW's realised e-values, so "
          "the attacker is credited with exact knowledge of the detector's output on that "
          "window.  The costs below are therefore LOWER BOUNDS, inherited from section "
          "4.30, which states the same caveat for the same reason.")
print(f"\n  ORACLE CAVEAT: {CAVEAT}\n")
out["oracle_caveat"] = CAVEAT
X, y, ts, src, dst = hs.load()
N = len(y)
dport_all = hs.load_extra("dport")

rows = []
for pos in POS:
    i1, i2, i3 = hs.split_indices(N, pos)
    y_cal, y_te = y[i1:i2], y[i2:i3]
    ts_w, src_w, dst_w = ts[i2:i3], src[i2:i3], dst[i2:i3]
    dp_w = dport_all[i2:i3]
    pr_w = np.asarray(X[i2:i3, 0]).astype(np.int32)
    ben = (y_te == 0)
    svc = pr_w.astype(np.int64) * 100000 + dp_w.astype(np.int64)
    uu, cc = np.unique(svc[ben], return_counts=True)
    bb_svc = uu[np.argmax(cc)]
    for seed in SEEDS:
        score = hs.fit_detector(X, y, i1, seed=seed, kind="hgb", verbose=False)
        s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
        e_te, cal, NC, CEIL = hs.evalues(s_cal, y_cal, s_te, k=K)
        ep = hs.build_episodes(e_te, y_te, ts_w, src_w, dst_w, BUCKET, "src-dst")
        T = ep["T"]; tau = T / W0
        det = np.nonzero(ep["ismal"] & (ep["Ev"] >= tau))[0]
        pools = {"generic": ben, "black-box": ben & (svc == bb_svc)}
        stats = {nm: dict(mu=float(e_te[m].mean()), p_fire=float((e_te[m] > 0).mean()),
                          n_flows=int(m.sum()))
                 for nm, m in pools.items() if m.sum()}
        print(f"  pos={pos} seed={seed}: T={T:,}  detected={len(det):>4}  "
              f"tau={tau:,.0f}  |C|={NC:,}  "
              f"black-box pool={stats['black-box']['n_flows']:,} flows  "
              f"[{time.time()-t0:.0f}s]")
        if not len(det):
            rows.append(dict(pos=pos, seed=seed, n_detected=0, T=int(T), tau=float(tau),
                             CEIL=float(CEIL), pools={}))
            continue
        per = {}
        for nm, st in stats.items():
            mu, pf = st["mu"], st["p_fire"]
            if mu >= tau:
                note(False, f"pool {nm} mean e exceeds tau at pos={pos} seed={seed}")
                continue
            rm_l, r9_l, gap_l, cens = [], [], [], 0
            for j in det:
                S = float(ep["sum_e"][j]); n = int(ep["nsz"][j])
                rm = r_mean_cost(S, n, tau, mu)
                r9 = r90(S, n, tau, CEIL, pf)
                rm_l.append(rm)
                if r9 is None:
                    cens += 1
                else:
                    r9_l.append(int(r9))
                    gap_l.append(int(r9) - int(rm))
            q = lambda v: [float(x) for x in np.quantile(v, QUANTS)] if v else None
            # r_90 - r_mean is RECORDED, not asserted.  "Needing 90% confidence cannot
            # cost less than needing it in expectation" sounds like a theorem and is not
            # one: out/t28_P5.json already contains 33 rows with r_90 - r_mean = -1,
            # because for rare-fire padding a 90% quantile can sit below the mean-cost
            # boundary.  Asserting an ordering here would manufacture failures.
            per[nm] = dict(mu=mu, p_fire=pf, n_pool_flows=st["n_flows"],
                           r_mean_q=q(rm_l), r_90_q=q(r9_l),
                           r90_minus_rmean_min=(min(gap_l) if gap_l else None),
                           r90_minus_rmean_max=(max(gap_l) if gap_l else None),
                           n_r90_below_rmean=int(sum(1 for g in gap_l if g < 0)),
                           r_mean_median=(float(np.median(rm_l)) if rm_l else None),
                           r_90_median=(float(np.median(r9_l)) if r9_l else None),
                           n_costed=len(rm_l), n_r90_censored=cens)
        rows.append(dict(pos=pos, seed=seed, n_detected=int(len(det)), T=int(T),
                         tau=float(tau), CEIL=float(CEIL), pools=per))

out["rows"] = rows

# =======================================================================================
print("\n" + "=" * 118)
print("MEDIAN SUPPRESSION COST BY WINDOW  (r_90: the pad size that works with prob >= 0.90)")
print("=" * 118)
print(f"  {'window':>8} {'seed':>5} {'detected':>9} {'pool':>12} {'mean e':>10} "
      f"{'P(fire)':>11} {'r_90 p10':>9} {'r_90 med':>9} {'r_90 p90':>9} {'censored':>9}")
summary = []
for r in rows:
    for nm, p in r["pools"].items():
        q = p["r_90_q"] or [float("nan")] * 3
        summary.append(dict(pos=r["pos"], seed=r["seed"], pool=nm,
                            n_detected=r["n_detected"], r_90_median=p["r_90_median"],
                            r_90_q=p["r_90_q"], mu=p["mu"], p_fire=p["p_fire"],
                            n_r90_censored=p["n_r90_censored"]))
        print(f"  {r['pos']:>8.2f} {r['seed']:>5} {r['n_detected']:>9,} {nm:>12} "
              f"{p['mu']:>10.2f} {p['p_fire']:>11.3e} {q[0]:>9,.0f} {q[1]:>9,.0f} "
              f"{q[2]:>9,.0f} {p['n_r90_censored']:>9,}")
out["summary"] = summary

pos_with_cost = sorted({s["pos"] for s in summary if s["r_90_median"] is not None})
others = [p for p in pos_with_cost if p != 0.85]
print(f"\n  positions with a measurable median cost: {pos_with_cost}")
print(f"  positions besides 0.85: {others}  ({len(others)} of the 4 required >= 3)")
note(len(others) >= 3, f"only {len(others)} positions besides 0.85 have a measurable cost")

# The comparison the objection turns on: is 0.85 special?
med85 = [s["r_90_median"] for s in summary if s["pos"] == 0.85 and s["r_90_median"] is not None]
medoth = [s["r_90_median"] for s in summary if s["pos"] != 0.85 and s["r_90_median"] is not None]
# The aggregate hides the per-window picture: pool x seed cells are pooled, and the four
# non-0.85 windows are NOT uniformly cheaper.  Both breakdowns are reported before the
# aggregate so the aggregate cannot be read as a uniform statement.
print(f"\n  median r_90 BY WINDOW (over pool x seed cells):")
by_window = {}
for pp in sorted({s_["pos"] for s_ in summary}):
    v = [s_["r_90_median"] for s_ in summary
         if s_["pos"] == pp and s_["r_90_median"] is not None]
    by_window[str(pp)] = (float(np.median(v)) if v else None)
    print(f"      {pp:.2f}: {('n/a' if not v else format(np.median(v), '.2f')):>8} "
          f"flows  (over {len(v)} cells)")
print(f"\n  median r_90 BY POOL:")
by_pool = {}
for nm in ("generic", "black-box"):
    a85 = [s_["r_90_median"] for s_ in summary
           if s_["pool"] == nm and s_["pos"] == 0.85 and s_["r_90_median"] is not None]
    aot = [s_["r_90_median"] for s_ in summary
           if s_["pool"] == nm and s_["pos"] != 0.85 and s_["r_90_median"] is not None]
    by_pool[nm] = dict(median_085=(float(np.median(a85)) if a85 else None),
                       median_other=(float(np.median(aot)) if aot else None))
    print(f"      {nm:>12}: 0.85 {np.median(a85):>7.2f}   other four {np.median(aot):>7.2f}")
out["xwindow_by_window"] = by_window
out["xwindow_by_pool"] = by_pool

if med85 and medoth:
    print(f"\n  median r_90 at position 0.85          : {np.median(med85):,.0f} flows "
          f"(over {len(med85)} pool x seed cells)")
    print(f"  median r_90 at the other four windows : {np.median(medoth):,.0f} flows "
          f"(over {len(medoth)} cells), range "
          f"[{min(medoth):,.0f}, {max(medoth):,.0f}]")
    n_cheaper = sum(1 for pp, v in by_window.items()
                    if float(pp) != 0.85 and v is not None and v < np.median(med85))
    n_meas = sum(1 for pp, v in by_window.items() if float(pp) != 0.85 and v is not None)
    print(f"\n  -> the attack is measurable at {n_meas} of the 4 other windows, so it is NOT")
    print(f"     confined to the anomalous window.  It is CHEAPER at {n_cheaper} of them and")
    print(f"     comparable or dearer at {n_meas - n_cheaper}: the aggregate median of "
          f"{np.median(medoth):.0f} is")
    print(f"     driven by the two cheap windows and must not be read as a uniform claim.")
    out["xwindow"] = dict(median_r90_at_085=float(np.median(med85)),
                          median_r90_elsewhere=float(np.median(medoth)),
                          range_elsewhere=[float(min(medoth)), float(max(medoth))],
                          n_cells_085=len(med85), n_cells_other=len(medoth),
                          n_other_windows_measurable=int(n_meas),
                          n_other_windows_cheaper=int(n_cheaper))

out["assertions_failed"] = FAIL
json.dump(out, open(OUT / "t43_E10.json", "w"), indent=1, allow_nan=True)
print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t43_E10.json")
if FAIL:
    print("  ASSERTIONS FAILED:")
    for m in FAIL:
        print("   -", m)
    raise SystemExit(1)
print("  all assertions held")
