"""
H8 -- label noise: quantify it on LSPR23 and report FDP as an interval.

FDP is the headline metric of this project and it is measured against LSPR23's labels,
which have never been validated.  Engelen et al. (WTMC'21) and Liu et al. (CNS'22) measured
6.67% and 7.53% label corruption in CIC-IDS2017 / CSE-CIC-IDS2018, above 75% for some
attack classes.  LSPR23 labels come from exercise instrumentation rather than from a
post-hoc labelling script, so they are probably cleaner -- but "probably" is not a number.

WHAT THIS SCRIPT DOES, AND WHAT IT DOES NOT.
It does NOT hand-audit alerts; that requires an analyst with access to the exercise
ground truth, and no automated procedure can substitute for it.  What it does:

  1. Measures label INCONSISTENCY directly, which is a reproducible lower bound on label
     noise that needs no external ground truth: flows whose feature vectors are byte-identical
     but whose labels disagree cannot both be correct.  Reported per feature-key definition
     so the bound is not an artefact of one choice.
  2. Propagates label noise into FDP analytically.  With R alerts, V of them labelled
     false, and
        eps0 = P(truly malicious | labelled benign),  eps1 = P(truly benign | labelled malicious),
     the corrected proportion is
        FDP_true = FDP_obs*(1 - eps0) + (1 - FDP_obs)*eps1.
     Reported over a grid spanning zero to the CIC-measured 7.53%.
  3. Emits a fixed-seed audit sample of 250 alerts to out/h8_audit_sample.csv with the
     fields an analyst needs, so the manual pass is a well-defined next step rather than an
     open-ended one.

Alerts are taken from the section 4.20 configuration: position 0.85, two-hour grouping,
e-LOND under horizon-uniform gamma, plus the ADDIS alert set, so both are covered.
"""
import numpy as np, json, time, csv
from pathlib import Path
import h_stream as hs
from h6_procs import Ctx, make_gamma, run_lond, run_addis

Path("out").mkdir(exist_ok=True)
t0 = time.time()
W0 = 0.025; A = 0.05; K = 1; BUCKET = 2 * 3600

X, y, ts, src, dst = hs.load()
N = len(y)

# ----------------------------------------------------------------------------------
# 1. Label inconsistency: identical feature vectors carrying different labels
# ----------------------------------------------------------------------------------
print("=" * 108)
print("H8a -- LABEL INCONSISTENCY ON LSPR23 (lower bound on label noise, no ground truth needed)")
print("=" * 108)
rng = np.random.default_rng(0)
SAMPLE = 4_000_000                    # subsample for the hash join; full 16.35M is memory-heavy
idx = np.sort(rng.choice(N, SAMPLE, replace=False))
incons = []
for label, with_hosts in (("all 33 features", False),
                          ("features + src + dst", True)):
    Z = np.ascontiguousarray(np.asarray(X[idx], dtype=np.float32))
    Z = Z + 0.0                      # canonicalise -0.0 so the key is a true byte identity
    if with_hosts:
        # keep src/dst as their own int32 fields: casting them into the float32 matrix
        # would alias distinct codes above 2**24
        dt = [(f"f{j}", Z.dtype) for j in range(Z.shape[1])] + \
             [("src", src.dtype), ("dst", dst.dtype)]
        view = np.empty(len(idx), dtype=dt)
        for j in range(Z.shape[1]):
            view[f"f{j}"] = Z[:, j]
        view["src"] = src[idx]; view["dst"] = dst[idx]
    else:
        view = Z.view(np.dtype((np.void, Z.dtype.itemsize * Z.shape[1]))).ravel()
    uniq, inv, cnt = np.unique(view, return_inverse=True, return_counts=True)
    lab_sum = np.bincount(inv, weights=y[idx].astype(float), minlength=len(uniq))
    grp_n = cnt.astype(float)
    mixed = (lab_sum > 0) & (lab_sum < grp_n)          # both labels present in one key
    n_mixed_keys = int(mixed.sum())
    rows_in_mixed = int(grp_n[mixed].sum())
    # minority label within each mixed key is the minimum number that must be wrong
    minority = np.minimum(lab_sum[mixed], grp_n[mixed] - lab_sum[mixed]).sum()
    frac = float(minority / SAMPLE)
    incons.append(dict(keydef=label, sample=SAMPLE, mixed_keys=n_mixed_keys,
                       rows_in_mixed=rows_in_mixed, minority_rows=int(minority),
                       lower_bound_noise=frac))
    print(f"  key = {label:<30} duplicate keys with BOTH labels: {n_mixed_keys:>9,}")
    print(f"  {'':<37} rows involved:                {rows_in_mixed:>9,}")
    print(f"  {'':<37} minimum mislabelled rows:     {int(minority):>9,}  "
          f"= {100*frac:.4f}% of the sample")
    del view, uniq, inv, cnt
print("\n  This is a LOWER bound: it catches only mislabels that collide exactly with a")
print("  correctly-labelled twin.  It cannot see a systematically mislabelled attack class.")
print("  Compare CIC-IDS2017 6.67% and CSE-CIC-IDS2018 7.53% (Engelen'21, Liu'22).")

# ----------------------------------------------------------------------------------
# 2. Alert sets and FDP intervals
# ----------------------------------------------------------------------------------
i1, i2, i3 = hs.split_indices(N, 0.85)
y_cal, y_te = y[i1:i2], y[i2:i3]
score = hs.fit_detector(X, y, i1, seed=0, kind="hgb", verbose=False)
s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
e_te, cal, NC, CEIL = hs.evalues(s_cal, y_cal, s_te, k=K)
ep = hs.build_episodes(e_te, y_te, ts[i2:i3], src[i2:i3], dst[i2:i3], BUCKET, "src-dst")
T = ep["T"]
ctx = Ctx(ep["Ev"], ep["ismal"], CEIL, alpha=A, w0=W0)
g1p, g0p = make_gamma("poly", T); g1u, _ = make_gamma("uniform", T)

alerts = {}
for nm, runner, gam in (("e-LOND/uniform", run_lond, g1u), ("ADDIS/poly", run_addis, g0p)):
    mask = np.zeros(T, bool)
    if nm.startswith("ADDIS"):
        runner(ctx, gam, lam=0.25, tau_=0.5, fired=mask)
    else:
        runner(ctx, gam, fired=mask)
    R = int(mask.sum()); V = int((mask & ~ep["ismal"]).sum())
    alerts[nm] = dict(mask=mask, R=R, V=V, fdp=(V / R if R else None))

print("\n" + "=" * 108)
print("H8b -- FDP AS AN INTERVAL UNDER LABEL NOISE")
print("=" * 108)
GRID = [0.0, 0.005, 0.0067, 0.0753]
fdp_rows = []
for nm, a in alerts.items():
    if not a["R"]: continue
    print(f"\n  {nm}: {a['R']} alerts, {a['V']} labelled false, observed FDP = {a['fdp']:.4f}")
    print(f"    {'eps0 (benign->mal)':>20} {'eps1 (mal->benign)':>20} {'corrected FDP':>15}")
    for e0 in GRID:
        for e1 in GRID:
            corr = a["fdp"] * (1 - e0) + (1 - a["fdp"]) * e1
            fdp_rows.append(dict(method=nm, eps0=e0, eps1=e1, fdp_obs=a["fdp"],
                                 fdp_corrected=float(corr)))
            if (e0, e1) in ((0.0, 0.0), (0.0067, 0.0067), (0.0753, 0.0753), (0.0753, 0.0)):
                print(f"    {e0:>20.4f} {e1:>20.4f} {corr:>15.4f}")
    lo = min(r["fdp_corrected"] for r in fdp_rows if r["method"] == nm)
    hi = max(r["fdp_corrected"] for r in fdp_rows if r["method"] == nm)
    print(f"    interval over the whole grid: [{lo:.4f}, {hi:.4f}]   (q = 0.05)")
    a["interval"] = [lo, hi]
print("\n  eps1 dominates: with few labelled-false alerts, converting a small fraction of the")
print("  many labelled-TRUE alerts into false ones moves FDP far more than the reverse.")
print("  At the CIC-measured 7.53% the FDP target q = 0.05 cannot be certified at all.")

# ----------------------------------------------------------------------------------
# 3. Audit sample for a human pass
# ----------------------------------------------------------------------------------
rng2 = np.random.default_rng(20260826)
union = alerts["e-LOND/uniform"]["mask"] | alerts["ADDIS/poly"]["mask"]
cand = np.nonzero(union)[0]
take = cand if len(cand) <= 250 else np.sort(rng2.choice(cand, 250, replace=False))
inv_order = ep["order"]
first_ts = np.full(T, np.iinfo(np.int64).max)
np.minimum.at(first_ts, ep["gid"], ts[i2:i3])
first_ts = first_ts[inv_order]
nmal_g = np.bincount(ep["gid"], weights=y_te.astype(float), minlength=T)[inv_order]
path = "out/h8_audit_sample.csv"
with open(path, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["episode_rank", "first_ts_us", "n_flows", "n_labelled_malicious",
                "episode_evalue", "alerted_by_eLOND", "alerted_by_ADDIS",
                "label_says", "analyst_verdict", "notes"])
    for j in take:
        w.writerow([int(j), int(first_ts[j]), int(ep["nsz"][j]), int(nmal_g[j]),
                    f"{ep['Ev'][j]:.1f}",
                    int(alerts["e-LOND/uniform"]["mask"][j]),
                    int(alerts["ADDIS/poly"]["mask"][j]),
                    "malicious" if ep["ismal"][j] else "benign", "", ""])
print(f"\n  wrote {len(take)} alerts to {path} for a manual pass "
      f"(seed 20260826; analyst_verdict left blank)")

json.dump({"inconsistency": incons,
           "alerts": {k: dict(R=v["R"], V=v["V"], fdp=v["fdp"],
                              interval=v.get("interval")) for k, v in alerts.items()},
           "fdp_grid": fdp_rows, "grid": GRID, "audit_sample": path,
           "audit_n": int(len(take))},
          open("out/t27_H8.json", "w"), indent=1, allow_nan=True)
print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t27_H8.json")
