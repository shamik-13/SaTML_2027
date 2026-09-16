"""
H6, part 4 -- consequence of H6 for section 4.19 / F13.

Section 4.19 measures "online FDR (e-LOND, mean rule)" at 72 alerts / recall 0.282 /
FDP 0.000 and contrasts it with the achievable frontier, which offers recall 0.459 on 117
alerts at the same zero error rate.  That row was computed under gamma prop j^-1.6.

H6 shows the same procedure under the horizon-uniform spending sequence reaches a very
different point.  Since F13 is a claim about WHICH point online error control selects,
this script puts every H6 configuration on the same frontier as section 4.19, so F13 can
be restated against measurement rather than against one gamma.

Frontier construction and tie-breaking are taken from t20_T8_matched.py.  The episode
ordering is np.lexsort((first_pos, first_ts)) as in t19/t21 rather than
np.argsort(first_ts): ties in first_ts are broken by first occurrence in the stream, which
is the deterministic convention of standing mistake 5.  The e-LOND row is asserted to
reproduce section 4.19 under gamma prop j^-1.6.
"""
import numpy as np, pandas as pd, json, time, gc
from pathlib import Path
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from h6_procs import Ctx, make_gamma, run_lond, run_lordpp, run_saffron, run_addis, online_ebh_kstar, run_egai

Path("out").mkdir(exist_ok=True); t0 = time.time()
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

POS = 0.85; W0 = 0.025; A = 0.05; K = 1; BH = 2
i2 = int(POS * N); i1 = i2 - int(0.15 * N); i3 = min(N, i2 + int(0.15 * N))
rng = np.random.default_rng(0); tr = np.arange(i1); ben = tr[y[tr] == 0]
tr_idx = np.sort(np.concatenate([tr[y[tr] == 1], ben[rng.random(len(ben)) < 0.5]]))
clf = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1, l2_regularization=1.0,
      min_samples_leaf=200, random_state=0, early_stopping=False).fit(X[tr_idx], y[tr_idx])
s_cal = clf.decision_function(X[i1:i2]); s_te = clf.decision_function(X[i2:i3])
y_cal, y_te = y[i1:i2], y[i2:i3]
cal = np.sort(s_cal[y_cal == 0]); NC = len(cal); CEIL = NC + 1.0
Kr = 1 + (NC - np.searchsorted(cal, s_te, side='left')); e_te = np.where(Kr <= K, CEIL, 0.0)
b = ts[i2:i3] // (BH * 3600 * 1_000_000)
key = np.empty(i3 - i2, dtype=[("s", "i4"), ("d", "i4"), ("b", "i8")])
key["s"] = src[i2:i3]; key["d"] = dst[i2:i3]; key["b"] = b
_, gid = np.unique(key, return_inverse=True); T = int(gid.max() + 1)
nsz = np.bincount(gid, minlength=T); mal = np.bincount(gid, weights=y_te.astype(float), minlength=T)
sum_e = np.bincount(gid, weights=e_te, minlength=T)
smax = np.full(T, -np.inf); np.maximum.at(smax, gid, s_te)
first_ts = np.full(T, np.iinfo(np.int64).max); np.minimum.at(first_ts, gid, ts[i2:i3])
first_pos = np.full(T, np.iinfo(np.int64).max)
np.minimum.at(first_pos, gid, np.arange(len(gid), dtype=np.int64))
o = np.lexsort((first_pos, first_ts))
smax, ismal, nz, se = smax[o], (mal > 0)[o], nsz[o], sum_e[o]
NM = int(ismal.sum()); Ev = se / np.maximum(nz, 1)
ctx = Ctx(Ev, ismal, CEIL, alpha=A, w0=W0)
print(f"AUROC={roc_auc_score(y_te, s_te):.4f} |C|={NC:,} T={T:,} malicious episodes={NM}  [{time.time()-t0:.0f}s]")

# ---------------- oracle Pareto frontier for the score-threshold family ----------------
ordr = np.lexsort((np.arange(T), -smax)); m = ismal[ordr]
tp = np.cumsum(m); fp = np.cumsum(~m); kk = np.arange(1, T + 1); fdp = fp / kk; rec = tp / NM


def frontier_at_budget(nb):
    b_ = float(np.clip(nb, 0.0, T))
    if b_ <= 0: return 0.0, 0.0
    k = int(np.floor(b_)); frac = b_ - k
    base = float(tp[k - 1]) if k else 0.0
    extra = float(m[k]) if k < T else 0.0
    r = (base + frac * extra) / NM
    fp_b = (float(fp[k - 1]) if k else 0.0) + frac * (1.0 - extra)
    return float(r), float(fp_b / b_)


def frontier_at_fdp(q):
    ok = np.flatnonzero(fdp <= q)
    if not len(ok): return None, None, None
    best = tp[ok].max(); cand = ok[tp[ok] == best]; i = cand[np.argmin(fdp[cand])]
    return float(rec[i]), float(fdp[i]), int(kk[i])


# ---------------- methods: every H6 configuration ----------------
methods = []


def add_from_mask(nm, fired, note=""):
    R = int(fired.sum()); V = int((fired & ~ismal).sum())
    methods.append(dict(method=nm, alerts=R, fdp=(float(V / R) if R else None),
                        recall=float((fired & ismal).sum() / NM), note=note))


def fired_mask(runner, *a, **kw):
    """Run one of the tested implementations in h6_procs and return its rejection mask,
    so this script never re-implements a procedure."""
    f = np.zeros(T, bool)
    runner(ctx, *a, fired=f, **kw)
    return f


def ebh_mask(gam1):
    ks, mm = online_ebh_kstar(Ev, gam1, A, T)
    return np.isfinite(mm) & (mm <= ks[T])


g1p, g0p = make_gamma("poly", T)
g1u, g0u = make_gamma("uniform", T)

add_from_mask("online FDR (e-LOND), gamma ~ j^-1.6", fired_mask(run_lond, g1p), "section 4.19 row")
add_from_mask("online FDR (e-LOND), horizon-uniform gamma", fired_mask(run_lond, g1u), "oracle horizon")
add_from_mask("ADDIS, gamma ~ j^-1.6", fired_mask(run_addis, g0p), "no horizon needed")
add_from_mask("ADDIS, horizon-uniform gamma", fired_mask(run_addis, g0u), "oracle horizon")
add_from_mask("online e-BH, gamma ~ j^-1.6", ebh_mask(g1p), "ARC")
add_from_mask("online e-BH, horizon-uniform gamma", ebh_mask(g1u), "ARC, oracle horizon")

print("\n" + "=" * 118); print("H6 CONFIGURATIONS AGAINST THE SECTION 4.19 FRONTIER"); print("=" * 118)
print(f"  {'method':>44} {'alerts':>8} {'FDP':>8} {'recall':>8} | {'frontier recall':>15} "
      f"{'gap':>8}  note")
for mth in methods:
    fr, _ = frontier_at_budget(mth["alerts"])
    mth["frontier_recall_at_budget"] = fr; mth["gap"] = fr - mth["recall"]
    fdps = f"{mth['fdp']:.3f}" if mth['fdp'] is not None else "   -  "
    print(f"  {mth['method']:>44} {mth['alerts']:>8,} {fdps:>8} {mth['recall']:>8.3f} | "
          f"{fr:>15.3f} {mth['gap']:>+8.3f}  {mth['note']}")

print("\n  achievable frontier by error level (same score, same stream):")
fr_rows = []
print(f"  {'target FDP':>11} {'frontier recall':>16} {'alerts':>9} {'achieved FDP':>13}")
for q in (0.0, 0.01, 0.05, 0.10, 0.20):
    r, f_, k_ = frontier_at_fdp(q)
    fr_rows.append(dict(target=q, recall=r, alerts=k_, achieved=f_))
    print(f"  {q:>11.3f} {r:>16.3f} {k_:>9,} {f_:>13.3f}")

# section 4.19 regression
e = methods[0]
ok = (e["alerts"] == 72 and abs(e["recall"] - 0.282) < 0.002 and e["fdp"] == 0.0)
print(f"\n  section 4.19 e-LOND row regression: {'REPRODUCED' if ok else 'MISMATCH'} "
      f"(alerts={e['alerts']}, recall={e['recall']:.3f}, FDP={e['fdp']:.3f})")

json.dump({"methods": methods, "frontier": fr_rows, "T": int(T), "NM": NM,
           "NC": int(NC), "CEIL": float(CEIL)},
          open("out/t21e_H6_frontier.json", "w"), indent=1, allow_nan=True)
print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t21e_H6_frontier.json")
