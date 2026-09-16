"""TRACK 2 (corrected): dilution attack vs a REAL, properly-regularised detector on real
LSPR23 traffic. Supersedes t11 (which used an unregularised model whose leaf values
exploded under 0.6% class imbalance, destroying tail ranking)."""
import numpy as np, pandas as pd, json
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score

cols=["ts","src","dst","label","proto"]+[f"f{i}" for i in range(32)]
df=pd.read_csv("/tmp/lspr_feat.csv",header=None,names=cols,
               dtype={"src":"category","dst":"category","label":"int8"},low_memory=False)
df=df.sort_values("ts",kind="mergesort").reset_index(drop=True)
feat=["proto"]+[f"f{i}" for i in range(32)]
X=df[feat].apply(pd.to_numeric,errors="coerce").fillna(0.0).replace([np.inf,-np.inf],0.0).to_numpy(np.float32)
y=df["label"].to_numpy(); n=len(df)
i1,i2=int(0.60*n),int(0.78*n)
clf=HistGradientBoostingClassifier(max_iter=200,learning_rate=0.1,l2_regularization=1.0,
        min_samples_leaf=200,random_state=0,early_stopping=False).fit(X[:i1],y[:i1])
s_cal=clf.decision_function(X[i1:i2]); s_te=clf.decision_function(X[i2:])
y_cal,y_te=y[i1:i2],y[i2:]
cal=np.sort(s_cal[y_cal==0]); NC=len(cal)
print("="*94); print("TRACK 2b -- STRONG detector (more ramp-up in training), REAL LSPR23 traffic, chronological split"); print("="*94)
print(f"  train={i1:,} ({y[:i1].mean():.4f})  cal={i2-i1:,}  test={n-i2:,} ({y[i2:].mean():.4f})")
print(f"  benign calibration |C| = {NC:,}   score range [{s_te.min():.2f},{s_te.max():.2f}]")
print(f"  test AUROC={roc_auc_score(y_te,s_te):.4f}  AUPRC={average_precision_score(y_te,s_te):.4f}")
K=1
def ev(s): 
    Kr=1+(NC-np.searchsorted(cal,s,side='left')); return np.where(Kr<=K,(NC+1.0)/K,0.0)
e_te=ev(s_te)
print(f"  MEASURED P(attack flow fires at k=1) = {(e_te[y_te==1]>0).mean():.4f}  "
      f"(simulations assumed 0.04-0.89)")
print(f"  MEASURED P(benign flow fires)        = {(e_te[y_te==0]>0).mean():.6f}  (nominal {1/(NC+1):.2e})")

meta=df.iloc[i2:].reset_index(drop=True)
for BH in (1,2,6):
    gid=(meta["src"].astype(str)+"|"+meta["dst"].astype(str)+"|"+(meta["ts"]//(BH*3600*1_000_000)).astype(str))
    g=pd.DataFrame({"gid":gid,"e":e_te,"y":y_te})
    agg=g.groupby("gid",observed=True).agg(n=("e","size"),sum_e=("e","sum"),mal=("y","sum"))
    T=len(agg); thr=T/0.025; ceil=NC+1.0
    att=agg[agg["mal"]>0]; mean_e=att["sum_e"]/att["n"]; det=mean_e>=thr
    print("\n"+"-"*94)
    print(f"  {BH}h grouping: T={T:,}  threshold={thr:,.0f}  ceiling={ceil:,.0f}  "
          f"FEASIBLE={ceil>=thr}")
    print(f"  attack episodes={len(att):,}  detected (no adversary)={det.sum():,} ({100*det.mean():.1f}%)")
    if det.sum()==0: continue
    ben_e=e_te[y_te==0]; rng=np.random.default_rng(0); D=att[det]
    print(f"  {'pad':>7} {'still detected':>16} {'% suppressed':>14}")
    rows=[]
    for pad in (0,10,25,50,100,250,500,1000):
        add = np.array([ben_e[rng.integers(0,len(ben_e),pad)].sum() if pad else 0.0
                        for _ in range(len(D))])
        still=int((((D["sum_e"].to_numpy()+add)/(D["n"].to_numpy()+pad))>=thr).sum())
        rows.append((pad,still))
        print(f"  {pad:>7,} {still:>16,} {100*(1-still/len(D)):>13.1f}%")
    med=np.median((D["sum_e"].to_numpy()/thr)-D["n"].to_numpy())
    print(f"  median pad needed to suppress a detected episode: {max(0,int(np.floor(med))+1):,}")
    json.dump({"bucket_h":BH,"T":int(T),"thr":float(thr),"ceiling":float(ceil),
               "n_att_ep":int(len(att)),"detected":int(det.sum()),"dilution":rows},
              open(f"out/t12_track2_{BH}h.json","w"),indent=1)
