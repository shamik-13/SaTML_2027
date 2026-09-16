"""Re-run with a properly regularised detector and a split that lets it see attacks.
Conformal evidence depends only on RANKS, so the question is whether the tail RANKING
changes once the leaf-value explosion is removed."""
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
i1,i2=int(0.60*n),int(0.75*n)          # let training see the ramp-up
print(f"split train={i1:,} ({y[:i1].mean():.4f}) cal={i2-i1:,} ({y[i1:i2].mean():.4f}) test={n-i2:,} ({y[i2:].mean():.4f})")

for tag,kw in [("UNREGULARISED", dict(l2_regularization=0.0, min_samples_leaf=20)),
               ("REGULARISED",   dict(l2_regularization=1.0, min_samples_leaf=200))]:
    clf=HistGradientBoostingClassifier(max_iter=200,learning_rate=0.1,random_state=0,
                                       early_stopping=False,**kw).fit(X[:i1],y[:i1])
    s_cal=clf.decision_function(X[i1:i2]); s_te=clf.decision_function(X[i2:])
    y_cal,y_te=y[i1:i2],y[i2:]
    cal=np.sort(s_cal[y_cal==0]); NC=len(cal)
    sa=s_te[y_te==1]
    Kr=1+(NC-np.searchsorted(cal,sa,side='left'))
    print("\n"+"="*90); print(f"{tag}   |C|={NC:,}"); print("="*90)
    print(f"  score range: [{s_te.min():.3g}, {s_te.max():.3g}]")
    print(f"  test AUROC={roc_auc_score(y_te,s_te):.4f}  AUPRC={average_precision_score(y_te,s_te):.4f}")
    print(f"  attack-flow rank among |C| benign: min={Kr.min():,}  p1={np.percentile(Kr,1):,.0f}  "
          f"p10={np.percentile(Kr,10):,.0f}  median={np.median(Kr):,.0f}")
    print(f"  {'k':>9} {'ceiling':>12} {'% attack flows firing':>22}")
    for k in (1,10,100,1_000,10_000,100_000):
        print(f"  {k:>9,} {(NC+1)/k:>12,.0f} {100*(Kr<=k).mean():>21.2f}%")
    # what the online procedure needs
    meta=df.iloc[i2:].reset_index(drop=True)
    gid=(meta["src"].astype(str)+"|"+meta["dst"].astype(str)+"|"+(meta["ts"]//(3600*1_000_000)).astype(str))
    T=gid.nunique(); need=T/0.025
    print(f"  test-stream hypotheses T={T:,}  -> online procedure needs evidence >= {need:,.0f}")
    print(f"  best attainable ceiling with >=1% of attack flows firing: "
          f"{max([(NC+1)/k for k in (1,10,100,1_000,10_000,100_000) if (Kr<=k).mean()>=0.01], default=0):,.0f}")
