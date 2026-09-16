"""
TRACK 2: the dilution attack against a REAL detector on REAL LSPR23 traffic.
Replaces the assumed Gaussian separation mu with measured score separation.
"""
import numpy as np, pandas as pd, json, time
from sklearn.ensemble import HistGradientBoostingClassifier

t0=time.time()
cols = ["ts","src","dst","label","proto"] + [f"f{i}" for i in range(32)]
df = pd.read_csv("/tmp/lspr_feat.csv", header=None, names=cols,
                 dtype={"src":"category","dst":"category","label":"int8"},
                 low_memory=False)
print(f"loaded {len(df):,} rows in {time.time()-t0:.0f}s")
df = df.sort_values("ts", kind="mergesort").reset_index(drop=True)   # FIX: file is unordered
feat = ["proto"]+[f"f{i}" for i in range(32)]
X = df[feat].apply(pd.to_numeric, errors="coerce").fillna(0.0)
X = X.replace([np.inf,-np.inf],0.0).to_numpy(dtype=np.float32)
y = df["label"].to_numpy()
n=len(df); i1,i2 = int(0.40*n), int(0.70*n)
print(f"chronological split: train={i1:,} cal={i2-i1:,} test={n-i2:,}")
print(f"  attack prevalence  train={y[:i1].mean():.4f} cal={y[i1:i2].mean():.4f} test={y[i2:].mean():.4f}")

print("training HistGradientBoosting on TRAIN ...")
clf = HistGradientBoostingClassifier(max_iter=150, learning_rate=0.1,
                                     early_stopping=False, random_state=0)
clf.fit(X[:i1], y[:i1]); print(f"  done {time.time()-t0:.0f}s")

s_cal_all = clf.decision_function(X[i1:i2]); y_cal = y[i1:i2]
s_te      = clf.decision_function(X[i2:]);   y_te  = y[i2:]
cal = np.sort(s_cal_all[y_cal==0])          # BENIGN calibration only
NC = len(cal); print(f"benign calibration |C| = {NC:,}")

# ---- MEASURED separation: the real analogue of mu ----
print("\n"+"="*92); print("A. MEASURED SEPARATION (replaces the assumed mu)"); print("="*92)
cmax = cal[-1]
p_hit_att = (s_te[y_te==1] > cmax).mean()
p_hit_ben = (s_te[y_te==0] > cmax).mean()
print(f"  P(test ATTACK flow exceeds calibration max) = {p_hit_att:.4f}")
print(f"  P(test BENIGN flow exceeds calibration max) = {p_hit_ben:.6f}   (nominal 1/(|C|+1) = {1/(NC+1):.2e})")
from scipy.stats import norm
mu_equiv = norm.ppf(1-1/(NC+1.0)) - norm.ppf(max(1e-12,1-p_hit_att)) if p_hit_att<1 else np.inf
print(f"  => Gaussian-equivalent mu ~ {mu_equiv:.2f}   (simulations assumed mu = 3-6)")

def e_val(s, k=1):
    Kr = 1 + (NC - np.searchsorted(cal, s, side='left'))
    return np.where(Kr<=k, (NC+1.0)/k, 0.0)

# ---- episodes in the TEST stream ----
meta = df.iloc[i2:].reset_index(drop=True)
BUCKET = 3600*1_000_000
gid = (meta["src"].astype(str)+"|"+meta["dst"].astype(str)+"|"+(meta["ts"]//BUCKET).astype(str))
e_te = e_val(s_te, 1)
g = pd.DataFrame({"gid":gid,"e":e_te,"y":y_te})
agg = g.groupby("gid",observed=True).agg(n=("e","size"), sum_e=("e","sum"), mal=("y","sum"))
T = len(agg); W0=0.025; thr = T/W0
att_ep = agg[agg["mal"]>0]
print("\n"+"="*92); print("B. TEST-STREAM EPISODES"); print("="*92)
print(f"  hypotheses T = {T:,}   attack episodes = {len(att_ep):,}   threshold 1/alpha_T = {thr:,.0f}")
print(f"  evidence ceiling (|C|+1)/k = {NC+1:,}   feasible at t=T? {NC+1 >= thr}")

mean_e = att_ep["sum_e"]/att_ep["n"]
det = (mean_e >= thr)
print(f"  episodes detected (mean rule, no adversary) = {det.sum():,} / {len(att_ep):,} ({100*det.mean():.1f}%)")

# ---- DILUTION ATTACK with REAL benign padding ----
print("\n"+"="*92); print("C. DILUTION ATTACK (padding with REAL benign test flows)"); print("="*92)
ben_e = e_te[y_te==0]
rng=np.random.default_rng(0)
detected = att_ep[det]
print(f"  attacking the {len(detected):,} episodes that ARE detected without an adversary")
print(f"  {'pad events':>11} {'episodes still detected':>25} {'% suppressed':>14}")
print("  "+"-"*54)
rows=[]
for pad in (0,10,50,100,500,1000,5000):
    still=0
    for _,r in detected.iterrows():
        add = ben_e[rng.integers(0,len(ben_e),pad)].sum() if pad else 0.0
        if (r["sum_e"]+add)/(r["n"]+pad) >= thr: still+=1
    rows.append((pad,still))
    print(f"  {pad:>11,} {still:>25,} {100*(1-still/max(len(detected),1)):>13.1f}%")
json.dump({"p_hit_att":float(p_hit_att),"p_hit_ben":float(p_hit_ben),"NC":int(NC),"T":int(T),
           "thr":float(thr),"n_att_ep":int(len(att_ep)),"det":int(det.sum()),
           "dilution":rows}, open("out/t11_real_attack.json","w"), indent=1)
print(f"\nwrote out/t11_real_attack.json   ({time.time()-t0:.0f}s total)")
