"""Diagnose the degenerate result in t11: detector quality vs tail separation."""
import numpy as np, pandas as pd, time
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score

cols=["ts","src","dst","label","proto"]+[f"f{i}" for i in range(32)]
df=pd.read_csv("/tmp/lspr_feat.csv",header=None,names=cols,
               dtype={"src":"category","dst":"category","label":"int8"},low_memory=False)
df=df.sort_values("ts",kind="mergesort").reset_index(drop=True)
feat=["proto"]+[f"f{i}" for i in range(32)]
X=df[feat].apply(pd.to_numeric,errors="coerce").fillna(0.0).replace([np.inf,-np.inf],0.0).to_numpy(np.float32)
y=df["label"].to_numpy()
n=len(df)

print("="*92); print("ATTACK ARRIVAL OVER THE STREAM (why the chronological split is pathological)")
print("="*92)
for i in range(10):
    a,b=int(i*n/10),int((i+1)*n/10)
    print(f"  decile {i+1:>2}: prevalence {y[a:b].mean():.4f}")

i1,i2=int(0.40*n),int(0.70*n)
clf=HistGradientBoostingClassifier(max_iter=150,random_state=0,early_stopping=False).fit(X[:i1],y[:i1])
s_cal=clf.decision_function(X[i1:i2]); s_te=clf.decision_function(X[i2:])
y_cal,y_te=y[i1:i2],y[i2:]
cal=np.sort(s_cal[y_cal==0]); NC=len(cal)

print("\n"+"="*92); print("IS THE DETECTOR ANY GOOD?"); print("="*92)
print(f"  test AUROC = {roc_auc_score(y_te,s_te):.4f}   AUPRC = {average_precision_score(y_te,s_te):.4f}")
print(f"  test prevalence = {y_te.mean():.4f}")

print("\n"+"="*92); print("TAIL SEPARATION: where do attack scores rank among benign calibration?")
print("="*92)
sa=s_te[y_te==1]; sb=s_te[y_te==0]
print(f"  benign calibration |C| = {NC:,}")
for q,lbl in [(50,'p50'),(90,'p90'),(99,'p99'),(99.9,'p99.9'),(99.99,'p99.99'),(99.999,'p99.999'),(100,'MAX')]:
    thr=np.percentile(cal,q)
    print(f"  benign cal {lbl:>8} = {thr:>9.3f}   attack flows above: {100*(sa>thr).mean():>6.2f}%"
          f"   benign TEST flows above: {100*(sb>thr).mean():>6.3f}%")

print("\n"+"="*92); print("WHAT k IS ATTAINABLE?  (e-value ceiling = (|C|+1)/k)")
print("="*92)
Kr = 1 + (NC - np.searchsorted(cal, sa, side='left'))     # rank of each attack flow
print(f"  attack-flow rank among calibration: min={Kr.min():,} p1={np.percentile(Kr,1):,.0f} "
      f"p10={np.percentile(Kr,10):,.0f} median={np.median(Kr):,.0f}")
print("  -> k must be >= the rank for the e-value to fire.")
for k in (1,10,100,1000,10_000,100_000):
    frac=(Kr<=k).mean(); ceil=(NC+1)/k
    print(f"  k={k:>7,}  ceiling={ceil:>12,.0f}   attack flows firing: {100*frac:>6.2f}%")
