"""
CROSS-CHECK of F8 (the detection floor) against a REAL detector and REAL episodes.
F8 was derived assuming every attack flow contributes the maximum e-value (P_fire = 1)
and that T = N/n0 exactly. Both are false on real data. This tests how far off it is.

Analytic floor (idealised):   n_att_min = N*k / (w0*(|C|+1))
Analytic floor (real P_fire): n_att_min = N*k / (w0*(|C|+1)*P_fire)
Measured floor              : smallest n_att whose episode actually clears the robust rule
"""
import numpy as np, pandas as pd, json
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

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
cal=np.sort(s_cal[y_cal==0]); NC=len(cal); CEIL=NC+1.0; W0=0.025; K=1
Kr=1+(NC-np.searchsorted(cal,s_te,side='left')); e_te=np.where(Kr<=K,CEIL,0.0)
P_FIRE=(e_te[y_te==1]>0).mean(); N_TEST=len(s_te)
print("="*98)
print("CROSS-CHECK OF THE DETECTION FLOOR (F8) AGAINST REAL SCORES")
print("="*98)
print(f"  detector AUROC={roc_auc_score(y_te,s_te):.4f}   |C|={NC:,}   ceiling={CEIL:,.0f}")
print(f"  test-stream flows N={N_TEST:,}   measured P_fire (attack, k=1) = {P_FIRE:.4f}")

meta=df.iloc[i2:].reset_index(drop=True)
out=[]
for BH in (1,2,6):
    gid=(meta["src"].astype(str)+"|"+meta["dst"].astype(str)+"|"+(meta["ts"]//(BH*3600*1_000_000)).astype(str))
    g=pd.DataFrame({"gid":gid,"e":e_te,"y":y_te})
    agg=g.groupby("gid",observed=True).agg(n=("e","size"),sum_e=("e","sum"),mal=("y","sum"))
    T=len(agg); mean_sz=agg["n"].mean(); thr=T/W0
    att=agg[agg["mal"]>0].copy()
    n0=int(np.ceil(agg["n"].quantile(0.99)))      # pre-committed cap = 99th pct group size
    # robust rule: E = sum_e / n0 ; valid only for groups with n <= n0 (cap enforced)
    att["E_rob"]=att["sum_e"]/n0
    det_rob=att["E_rob"]>=thr
    f_ideal = N_TEST*K/(W0*CEIL)
    f_real  = N_TEST*K/(W0*CEIL*max(P_FIRE,1e-12))
    f_exact = n0*T/(W0*P_FIRE*CEIL)               # without assuming T = N/n0
    meas = att.loc[det_rob,"mal"].min() if det_rob.any() else np.nan
    print("\n"+"-"*98)
    print(f"  {BH}h grouping: T={T:,}  mean group size={mean_sz:.1f}  T*mean={T*mean_sz:,.0f} (N={N_TEST:,})")
    print(f"    pre-committed cap n0 (p99 group size) = {n0:,}   threshold = {thr:,.0f}")
    print(f"    floor, idealised  (P_fire=1, T=N/n0) : {f_ideal:>12,.0f}")
    print(f"    floor, P_fire-corrected             : {f_real:>12,.0f}   (x{f_real/f_ideal:.2f})")
    print(f"    floor, exact (measured T and n0)     : {f_exact:>12,.0f}")
    print(f"    MEASURED smallest detected episode   : {meas if np.isnan(meas) else int(meas):>12}")
    print(f"    episodes detected under robust rule  : {int(det_rob.sum()):,} / {len(att):,}")
    # agreement between analytic prediction and reality
    pred = att["mal"]>=f_exact
    tp=int((pred&det_rob).sum()); fp=int((pred&~det_rob).sum())
    fn=int((~pred&det_rob).sum()); tn=int((~pred&~det_rob).sum())
    print(f"    analytic-vs-actual agreement: {100*(tp+tn)/len(att):.1f}%  "
          f"(TP={tp} FP={fp} FN={fn} TN={tn})")
    # how many real episodes clear each floor
    for lbl,f in [("idealised",f_ideal),("P_fire-corrected",f_real),("exact",f_exact)]:
        above=int((att["mal"]>=f).sum())
        print(f"    episodes >= {lbl:>17} floor: {above:>5,} / {len(att):,} ({100*above/len(att):>5.1f}%)")
    out.append(dict(bucket_h=BH,T=int(T),n0=int(n0),thr=float(thr),f_ideal=float(f_ideal),
                    f_real=float(f_real),f_exact=float(f_exact),
                    measured_min=(None if np.isnan(meas) else int(meas)),
                    det=int(det_rob.sum()),n_ep=int(len(att)),
                    agree=float((tp+tn)/len(att))))
json.dump({"P_fire":float(P_FIRE),"NC":int(NC),"N_test":int(N_TEST),"per_bucket":out},
          open("out/t13_floor_crosscheck.json","w"),indent=1)
print("\nwrote out/t13_floor_crosscheck.json")
