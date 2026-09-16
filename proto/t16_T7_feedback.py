"""
T7 -- analyst-disposition feedback controller (B6) vs online error control.

If analyst dispositions arrive with latency L, a SOC can estimate realised FDP directly and
steer the threshold. No multiplicity theory, no exchangeability, no dependence assumption.
Question: at what label latency does formal online error control become worth its cost?
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
cal=np.sort(s_cal[y_cal==0]); NC=len(cal); CEIL=NC+1.0; W0=0.025; Q=0.05

# ---- episodes in the test stream ----
meta=df.iloc[i2:].reset_index(drop=True)
BH=2; BUCK=BH*3600*1_000_000
gid=(meta["src"].astype(str)+"|"+meta["dst"].astype(str)+"|"+(meta["ts"]//BUCK).astype(str))
ep=pd.DataFrame({"gid":gid,"s":s_te,"y":y_te,"ts":meta["ts"].to_numpy()}) \
     .groupby("gid",observed=True).agg(smax=("s","max"),mal=("y","sum"),
                                       n=("s","size"),t0=("ts","min")).sort_values("t0")
span_h=(ep["t0"].max()-ep["t0"].min())/3.6e9
print("="*100); print("T7 -- ANALYST-FEEDBACK BASELINE"); print("="*100)
print(f"  detector AUROC={roc_auc_score(y_te,s_te):.4f}  |C|={NC:,}")
print(f"  test stream: {len(ep):,} episodes over {span_h:.1f} h  "
      f"({(ep['mal']>0).sum():,} malicious = {100*(ep['mal']>0).mean():.2f}%)")

smax=ep["smax"].to_numpy(); ismal=(ep["mal"]>0).to_numpy(); t0=ep["t0"].to_numpy()
E=len(ep)

def tau_of(u, cal):
    """EXACT order statistic -- full resolution. cal is already sorted ascending.
    (A 20k-point quantile grid addresses ~25 calibration order stats per step in the
    upper tail and quantises the controller; do not use one here.)"""
    return cal[int(np.clip(u*(len(cal)-1), 0, len(cal)-1))]

def run_feedback(L_alerts, eta=0.02, u0=0.999, win=200):
    """Latency in ALERTS: the disposition of alert j is available only after L further
    alerts. L_alerts=None means dispositions never arrive (fixed threshold)."""
    u=u0; fired=np.zeros(E,bool); pending=[]; hist=[]
    n_alert=0; n_updates=0; burnin_alerts=0
    for i in range(E):
        arrived=0
        if L_alerts is not None:
            while pending and pending[0][0] <= n_alert - L_alerts:
                hist.append(pending.pop(0)[1]); arrived+=1
        # update ONLY when new dispositions actually arrived
        if arrived and len(hist)>=10:
            u=float(np.clip(u+eta*(np.mean(hist[-win:])-Q),0.5,1.0)); n_updates+=1
        if smax[i]>tau_of(u,cal):
            fired[i]=True; n_alert+=1
            if len(hist)<10: burnin_alerts+=1
            if L_alerts is not None:
                pending.append((n_alert,0.0 if ismal[i] else 1.0))
    R=fired.sum(); V=(fired&~ismal).sum()
    return dict(alerts=int(R), fdp=float(V/R) if R else float('nan'),
                recall=float((fired&ismal).sum()/ismal.sum()),
                per_day=float(R/(span_h/24)), u_end=float(u),
                updates=int(n_updates), burnin=int(burnin_alerts))

print("\n" + "="*100)
print(f"  B6 FEEDBACK CONTROLLER, target FDP q={Q}")
print("="*100)
print(f"  {'feedback latency':>19} {'alerts':>8} {'realised FDP':>13} {'episode recall':>15} {'alerts/day':>11} {'updates':>8} {'burn-in':>8}")
print("  "+"-"*68)
rows=[]
LATS=[("0 alerts (instant)",0),("5 alerts",5),("20 alerts",20),("50 alerts",50),
      ("200 alerts",200),("inf (no labels)",None)]
for nm,L in LATS:
    r=run_feedback(L); r["L"]=nm; rows.append(r)
    print(f"  {nm:>19} {r['alerts']:>8,} {r['fdp']:>13.3f} {r['recall']:>15.3f} {r['per_day']:>11.1f} "
          f"{r['updates']:>8,} {r['burnin']:>8,}")

# ---- comparison at MATCHED ALERT BUDGET against the best valid online rule (policy D) ----
print("\n" + "="*100)
print("  MATCHED-BUDGET COMPARISON vs online error control (policy D, the only valid")
print("  online rule with meaningful power -- see 4.12)")
print("="*100)
Kk=1
Kr=1+(NC-np.searchsorted(cal,s_te,side='left')); e_te=np.where(Kr<=Kk,CEIL,0.0)
g2=pd.DataFrame({"gid":gid,"e":e_te,"y":y_te}).groupby("gid",observed=True)
fire_ct=g2["e"].apply(lambda v:(v.to_numpy()>0).sum()); nsz=g2.size()
thrD=len(ep)/W0; feas=1.0 if CEIL>=thrD else 0.0
pD=(feas*fire_ct/nsz).reindex(ep.index).to_numpy()
expD_alerts=float(pD.sum()); expD_tp=float(pD[ismal].sum())
expD_fdp=1-expD_tp/expD_alerts if expD_alerts>0 else float('nan')
print(f"  policy D: E[alerts]={expD_alerts:.1f}  E[TP]={expD_tp:.1f}  "
      f"E[FDP]={expD_fdp:.3f}  recall={expD_tp/ismal.sum():.3f}  alerts/day={expD_alerts/(span_h/24):.1f}")
# match B6 to D's alert budget by sweeping u
target=expD_alerts
lo,hi=0.5,1-1e-9
for _ in range(60):
    mid=(lo+hi)/2
    a=(smax>np.quantile(cal,mid)).sum()
    if a>target: lo=mid
    else: hi=mid
tau=np.quantile(cal,(lo+hi)/2); f=smax>tau
Rm=int(f.sum()); fdpm=float((f&~ismal).sum()/Rm) if Rm else float('nan')
print(f"  B6 at matched budget ({Rm} alerts, ORACLE-tuned on the eval stream): "
      f"FDP={fdpm:.3f}  recall={(f&ismal).sum()/ismal.sum():.3f}")
json.dump({"span_h":float(span_h),"episodes":int(E),"mal_ep":int(ismal.sum()),
           "feedback":rows,"policyD":{"alerts":expD_alerts,"fdp":expD_fdp,
           "recall":float(expD_tp/ismal.sum())},
           "matched":{"alerts":Rm,"fdp":fdpm,
                      "recall":float((f&ismal).sum()/ismal.sum())}},
          open("out/t16_T7.json","w"),indent=1)
print("\nwrote out/t16_T7.json")

print("\n" + "="*100)
print("  IS THE OVERSHOOT AT L=0 A TUNING ARTEFACT?  sweep eta and window")
print("="*100)
print(f"  {'eta':>7} {'window':>8} {'alerts':>8} {'realised FDP':>13} {'recall':>9}")
print("  "+"-"*50)
best=None
for eta in (0.005,0.02,0.05,0.2):
    for win in (50,200,1000):
        r=run_feedback(0,eta=eta,win=win)
        print(f"  {eta:>7.3f} {win:>8} {r['alerts']:>8,} {r['fdp']:>13.3f} {r['recall']:>9.3f}")
        if not np.isnan(r['fdp']) and (best is None or abs(r['fdp']-Q)<abs(best[2]-Q)):
            best=(eta,win,r['fdp'],r['recall'],r['alerts'])
print(f"\n  closest to q={Q}: eta={best[0]}, window={best[1]} -> FDP={best[2]:.3f}, "
      f"recall={best[3]:.3f}, alerts={best[4]:,}")
print(f"  episode prevalence is {100*ismal.mean():.2f}%, so a q=0.05 target admits only")
print(f"  ~{int(ismal.sum()/(1-Q))} alerts in total -- the feedback signal is inherently sparse.")
