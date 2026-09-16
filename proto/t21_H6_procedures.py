"""
H6 -- SAFFRON, ADDIS, online e-BH and e-GAI (e-LORD / e-SAFFRON / mem-e-LORD) on the real
episode stream.  Question: does any of them escape the Family-I / Family-II feasibility
template of section 4.13?

Procedure implementations live in h6_procs.py and are unit-tested by t21b_h6_selftest.py
against literal transcriptions of the published formulas and against four identities the
source papers state.

The stream construction below is copied verbatim from t19_T5_T6.py, so the LOND / e-LOND /
LORD++ rows must reproduce section 4.17 exactly (72 / 72 / 72 rejections, FDP 0.000,
recall 0.282, silent 65.4 / 65.4 / 60.8%, first infeasible 10,929 / 10,929 / 12,383).
That is asserted below and acts as a regression test on the whole pipeline.

Two spending sequences are run for every gamma-parameterised procedure:
  poly     gamma_j prop j^-1.6      -- the section 4.17 choice, so rows are comparable
  uniform  gamma_j = 1/T            -- horizon-uniform, max-min optimal (section 4.5)
Running both is what stops "your procedures failed because you picked a bad gamma".
"""
import numpy as np, pandas as pd, json, time, gc
from pathlib import Path
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from h6_procs import (Ctx, make_gamma, run_lond, run_lordpp, run_saffron, run_addis,
                      run_online_ebh, run_egai, egai_implied_gamma)

Path("out").mkdir(exist_ok=True)
t0 = time.time()

# ----------------------------------------------------------------------------------
# Stream construction -- verbatim from t19_T5_T6.py
# ----------------------------------------------------------------------------------
cols = ["ts", "src", "dst", "label", "proto"] + [f"f{i}" for i in range(32)]
dt = {"ts": "int64", "src": "category", "dst": "category", "label": "int8", "proto": "float32"}
dt.update({f"f{i}": "float32" for i in range(32)})
df = pd.read_csv("/tmp/lspr_full.csv", header=None, names=cols, dtype=dt, low_memory=False)
df = df.sort_values("ts", kind="mergesort").reset_index(drop=True)
feat = ["proto"] + [f"f{i}" for i in range(32)]
X = df[feat].to_numpy(dtype=np.float32, copy=True)
np.nan_to_num(X, copy=False, nan=0.0, posinf=0.0, neginf=0.0)
y = df["label"].to_numpy(copy=True); ts = df["ts"].to_numpy(copy=True)
src = df["src"].cat.codes.to_numpy(dtype=np.int32, copy=True)
dst = df["dst"].cat.codes.to_numpy(dtype=np.int32, copy=True)
del df; gc.collect(); N = len(y)

POS = 0.85; CAL_F = TEST_F = 0.15; W0 = 0.025; A = 0.05; K = 1
i2 = int(POS * N); i1 = i2 - int(CAL_F * N); i3 = min(N, i2 + int(TEST_F * N))
rng = np.random.default_rng(0); tr = np.arange(i1); ben = tr[y[tr] == 0]
tr_idx = np.sort(np.concatenate([tr[y[tr] == 1], ben[rng.random(len(ben)) < 0.5]]))
clf = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1, l2_regularization=1.0,
      min_samples_leaf=200, random_state=0, early_stopping=False).fit(X[tr_idx], y[tr_idx])
s_cal = clf.decision_function(X[i1:i2]); s_te = clf.decision_function(X[i2:i3])
y_cal, y_te = y[i1:i2], y[i2:i3]
cal = np.sort(s_cal[y_cal == 0]); NC = len(cal); CEIL = NC + 1.0
Kr = 1 + (NC - np.searchsorted(cal, s_te, side='left')); e_te = np.where(Kr <= K, CEIL, 0.0)
AUROC = float(roc_auc_score(y_te, s_te))
print(f"detector AUROC={AUROC:.4f}  |C|={NC:,}  ceiling={CEIL:,.0f}  [{time.time()-t0:.0f}s]")

BH = 2; b = ts[i2:i3] // (BH * 3600 * 1_000_000)
key = np.empty(i3 - i2, dtype=[("s", "i4"), ("d", "i4"), ("b", "i8")])
key["s"] = src[i2:i3]; key["d"] = dst[i2:i3]; key["b"] = b
_, gid = np.unique(key, return_inverse=True); T = int(gid.max() + 1)
nsz = np.bincount(gid, minlength=T); mal = np.bincount(gid, weights=y_te.astype(float), minlength=T)
sum_e = np.bincount(gid, weights=e_te, minlength=T)
first_ts = np.full(T, np.iinfo(np.int64).max)
np.minimum.at(first_ts, gid, ts[i2:i3])
first_pos = np.full(T, np.iinfo(np.int64).max)
np.minimum.at(first_pos, gid, np.arange(len(gid), dtype=np.int64))
order = np.lexsort((first_pos, first_ts))
Ev = (sum_e / np.maximum(nsz, 1))[order]; ismal = (mal > 0)[order]

ctx = Ctx(Ev, ismal, CEIL, alpha=A, w0=W0)
print(f"episodes T={T:,}  malicious={ctx.NMAL:,}  [{time.time()-t0:.0f}s]")

# ----------------------------------------------------------------------------------
def summarise(name, rej, tp, silent, first, note=""):
    return dict(proc=name, rejections=int(rej), tp=int(tp),
                fdp=(float(1 - tp / rej) if rej else None),
                recall=float(tp / ctx.NMAL), silent=float(silent / T),
                first_infeasible=(int(first) if first else None), note=note)


def show(rows, title):
    print("\n" + "=" * 112); print(title); print("=" * 112)
    print(f"  {'procedure':>16} {'rejections':>11} {'true pos':>9} {'FDP':>8} {'recall':>8} "
          f"{'silent':>8} {'1st infeas':>11}  note")
    for r in rows:
        fi = format(r['first_infeasible'], ',') if r['first_infeasible'] else '-'
        fdp = f"{r['fdp']:.3f}" if r['fdp'] is not None else "   -  "
        print(f"  {r['proc']:>16} {r['rejections']:>11,} {r['tp']:>9,} {fdp:>8} "
              f"{r['recall']:>8.3f} {100*r['silent']:>7.1f}% {fi:>11}  {r['note']}")


results = {}
for gk in ("poly", "uniform"):
    g1, g0 = make_gamma(gk, T)
    rows = []
    r = run_lond(ctx, g1)
    rows.append(summarise("LOND", *r))
    rows.append(summarise("e-LOND", *r, note="identical level to LOND"))
    rows.append(summarise("LORD++", *run_lordpp(ctx, g1)))
    rows.append(summarise("SAFFRON", *run_saffron(ctx, g1, lam=0.5), note="lam=0.5"))
    rows.append(summarise("ADDIS", *run_addis(ctx, g0, lam=0.25, tau_=0.5),
                          note="lam=0.25 tau=0.5; FDR guarantee NOT applicable, see diagnostics"))
    rj, tp, sl, fi, kfin, lag, never = run_online_ebh(ctx, g1)
    rows.append(summarise("online e-BH", rj, tp, sl, fi,
                          note=f"ARC; k*_T={kfin:,}; lag={'-' if lag is None else int(lag)}; "
                               f"never-rejectable={100*never/T:.1f}%"))
    show(rows, f"H6 -- gamma = {gk}" +
         ("  (j^-1.6, the section 4.17 choice; needs no horizon)" if gk == "poly"
          else "  (horizon-uniform, max-min optimal; ORACLE -- requires T known in advance)"))
    results[gk] = rows
    print(f"  [{time.time()-t0:.0f}s]")

# regression test against section 4.17
p = {r['proc']: r for r in results['poly']}
exp = {"LOND": (72, 72, 10929), "e-LOND": (72, 72, 10929), "LORD++": (72, 72, 12383)}
bad = [k for k, (rj, tp, fi) in exp.items()
       if not (p[k]['rejections'] == rj and p[k]['tp'] == tp and p[k]['first_infeasible'] == fi)]
print(f"\n  section 4.17 regression: {'REPRODUCED' if not bad else 'MISMATCH in ' + str(bad)}")
for k in exp:
    print(f"    {k:>8}: rej={p[k]['rejections']} tp={p[k]['tp']} recall={p[k]['recall']:.3f} "
          f"silent={100*p[k]['silent']:.1f}% first_infeasible={p[k]['first_infeasible']:,}")
assert not bad, f"section 4.17 no longer reproduces: {bad}"

# e-GAI family: generates its own spending sequence from w_1, so it is gamma-free
w1 = 1.0 / T
rows = [summarise("e-LORD", *run_egai(ctx, "e-LORD", w1), note="w1=1/T, phi=psi=0.5"),
        summarise("e-SAFFRON", *run_egai(ctx, "e-SAFFRON", w1, lam=0.1), note="w1=1/T, lam=0.1"),
        summarise("mem-e-LORD", *run_egai(ctx, "mem-e-LORD", w1, d=0.99),
                  note="d=0.99; controls mem-FDR, NOT FDR")]
show(rows, "H6 -- e-GAI family (arXiv 2506.01452); spending sequence generated internally from w_1"
           "\n       w_1 = 1/T is the value the paper recommends, and is ORACLE: T is the number of\n"
           "       evaluation episodes.  t21d_H6_horizon.py sweeps a mis-specified horizon.")
results["egai"] = rows

print("\n  e-GAI sensitivity to w_1 (e-LORD):")
sens = []
for w in (1.0 / T, 1e-4, 5e-3, 5e-2):
    rj, tp, sl, fi = run_egai(ctx, "e-LORD", w)
    sens.append(dict(w1=float(w), rejections=int(rj), tp=int(tp), silent=float(sl / T),
                     first_infeasible=(int(fi) if fi else None)))
    print(f"    w1={w:<11.6g} rejections={rj:>5,}  tp={tp:>5,}  silent={100*sl/T:>5.1f}%  "
          f"first infeasible={(format(fi, ',') if fi else '-')}")
results["egai_w1_sensitivity"] = sens

# ----------------------------------------------------------------------------------
print("\n" + "=" * 112); print("DIAGNOSTICS -- why each procedure lands where it does"); print("=" * 112)
Pv = ctx.Pv
n_sel = int((Pv <= 0.5).sum()); n_cand25 = int((Pv <= 0.25).sum()); n_cand50 = n_sel
print(f"  episodes with Ev > 0                        : {int((Ev>0).sum()):,} / {T:,} "
      f"({100*float((Ev>0).mean()):.3f}%)")
print(f"  ADDIS   selected   P <= tau=0.50            : {n_sel:,}")
print(f"  ADDIS   candidates P <= lam=0.25            : {n_cand25:,}")
print(f"  ADDIS   gamma index S^t - C0+ at t = T      : {n_sel - n_cand25:,}   "
      f"<- the index never advances if this is 0")
print(f"  SAFFRON candidates P <= lam=0.50            : {n_cand50:,}")
print(f"  SAFFRON gamma index t - C0+ at t = T        : {T - n_cand50:,}")
uq = np.unique(Pv)
print(f"  distinct p-values in the stream             : {len(uq):,}  "
      f"(min={uq[0]:.3e}, next={uq[1] if len(uq)>1 else float('nan'):.3e}, max={uq[-1]:.3e})")
g_imp = egai_implied_gamma(ctx, w1)
print(f"  e-LORD implied gamma_t = w_t prod(1-w_j)    : gamma_1={g_imp[0]:.3e}, "
      f"gamma_T={g_imp[-1]:.3e}, sum={g_imp.sum():.4f}")
print(f"  horizon-uniform gamma for comparison        : {1.0/T:.3e}")

# ADDIS Thm 1 needs uniformly conservative null p-values:
#   P(P/tau <= x | P <= tau, F_{t-1}) <= x   for every null t.
# SAFFRON needs a different condition -- (conditional) super-uniformity P(P <= x) <= x --
# so it gets its own check below; the ADDIS test is not a substitute for it.
null_p = Pv[~ismal]
sel_null = null_p[null_p <= 0.5]
print(f"\n  ADDIS Thm 1 assumption -- uniform conservativeness of null p-values (tau=0.5)")
print(f"    null episodes: {int((~ismal).sum()):,}; selected (P <= 0.5): {len(sel_null):,}")
uc = []
for x in (0.001, 0.01, 0.05, 0.1, 0.25, 0.5):
    lhs = float((sel_null <= x * 0.5).mean()) if len(sel_null) else float('nan')
    uc.append(dict(x=float(x), lhs=lhs, violated=bool(lhs == lhs and lhs > x)))
    flag = "   <-- VIOLATED" if lhs == lhs and lhs > x else ""
    print(f"    x={x:<6} P(P/tau <= x | P <= tau) = {lhs:.4f}   required <= {x}{flag}")
results["uniform_conservativeness"] = uc
addis_ok = all(not r["violated"] for r in uc)
print(f"    => ADDIS FDR guarantee {'applies' if addis_ok else 'DOES NOT APPLY'} on this stream; "
      f"its row is empirical-only.")

print(f"\n  SAFFRON assumption -- super-uniformity of null p-values, P(P <= x) <= x")
su = []
for x in (1e-6, 1e-5, 1e-4, 1e-3, 0.01, 0.05, 0.25, 0.5):
    lhs = float((null_p <= x).mean())
    su.append(dict(x=float(x), lhs=lhs, violated=bool(lhs > x)))
    print(f"    x={x:<8g} P(P <= x) = {lhs:.3e}   required <= {x:g}"
          f"{'   <-- VIOLATED' if lhs > x else ''}")
results["super_uniformity"] = su
print(f"    => null p-values are {'super-uniform' if all(not r['violated'] for r in su) else 'NOT super-uniform'}"
      f" at the levels tested; note SAFFRON additionally assumes independence, which"
      f" episode-level conformal e-values do not satisfy.")

json.dump({"config": dict(POS=POS, bucket_h=BH, k=K, alpha=A, w0=W0, T=int(T), NC=int(NC),
                          CEIL=float(CEIL), n_malicious=ctx.NMAL, AUROC=AUROC),
           "results": results,
           "diagnostics": dict(ev_positive=int((Ev > 0).sum()), addis_selected=n_sel,
                               addis_candidates=n_cand25,
                               addis_index_final=int(n_sel - n_cand25),
                               saffron_index_final=int(T - n_cand50),
                               distinct_p=int(len(uq)), pmin=float(1.0 / CEIL),
                               egai_gamma_1=float(g_imp[0]), egai_gamma_T=float(g_imp[-1]),
                               egai_gamma_sum=float(g_imp.sum()),
                               addis_guarantee_applies=bool(addis_ok))},
          open("out/t21_H6.json", "w"), indent=1, allow_nan=True)
print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t21_H6.json")
