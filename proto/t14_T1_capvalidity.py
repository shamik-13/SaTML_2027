"""
T1 -- cap validity. The rule Sum(e)/n0 is a valid e-value only when group occupancy m <= n0.
Setting n0 = p99 group size violates that on ~1% of groups -- the LARGEST ones.
Compare four policies that each guarantee m <= n0, and measure what each costs,
including the attack channel each one opens.
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

def ev(s):
    Kr=1+(NC-np.searchsorted(cal,s,side='left')); return np.where(Kr<=K,CEIL,0.0)

# --- P_fire on CALIBRATION, not test (removes the circularity in the old §4.11) ---
e_cal_att = ev(s_cal[y_cal==1])
P_FIRE_CAL = (e_cal_att>0).mean()
e_te = ev(s_te)
P_FIRE_TE  = (e_te[y_te==1]>0).mean()
print("="*100)
print("T1 -- CAP VALIDITY")
print("="*100)
print(f"  detector AUROC={roc_auc_score(y_te,s_te):.4f}  |C|={NC:,}  ceiling={CEIL:,.0f}")
print(f"  P_fire estimated on CALIBRATION = {P_FIRE_CAL:.4f}   (on test = {P_FIRE_TE:.4f})")

# --- caps derived from CALIBRATION-window group sizes (not from the test set) ---
meta_cal=df.iloc[i1:i2].reset_index(drop=True)
BH=2
gid_cal=(meta_cal["src"].astype(str)+"|"+meta_cal["dst"].astype(str)+"|"
         +(meta_cal["ts"]//(BH*3600*1_000_000)).astype(str))
cal_sizes=gid_cal.value_counts()
N0_P99_CAL=int(np.ceil(cal_sizes.quantile(0.99)))
N0_MAX_CAL=int(cal_sizes.max())
print(f"\n  caps set from CALIBRATION traffic: p99={N0_P99_CAL:,}  max={N0_MAX_CAL:,}")

meta=df.iloc[i2:].reset_index(drop=True)
bucket=(meta["ts"]//(BH*3600*1_000_000)).astype(str)
gid=(meta["src"].astype(str)+"|"+meta["dst"].astype(str)+"|"+bucket)
g=pd.DataFrame({"gid":gid,"e":e_te,"y":y_te,"ts":meta["ts"].to_numpy()})
sizes=g.groupby("gid",observed=True).size()
T0=len(sizes); thr0=T0/W0
print(f"\n  {BH}h grouping: T={T0:,}  base threshold={thr0:,.0f}")
print(f"  group size: mean={sizes.mean():.1f} p99={sizes.quantile(0.99):.0f} max={sizes.max():,}")

# ---- the bug being fixed ----
n0_p99=N0_P99_CAL   # from calibration, not test
viol=(sizes>n0_p99).sum()
print(f"\n  OLD SETTING n0=p99={n0_p99:,}: {viol:,} of {T0:,} groups ({100*viol/T0:.2f}%) have m>n0")
print(f"    -> E[sum(e)/n0] = m/n0 up to {sizes.max()/n0_p99:.1f} > 1 on those groups: rule INVALID there")
print(f"    -> and they hold {100*sizes[sizes>n0_p99].sum()/sizes.sum():.1f}% of all flows")

# ---- policies ----
gsort=g.sort_values(["gid","ts"],kind="mergesort")
grp=gsort.groupby("gid",observed=True)
agg=grp.agg(n=("e","size"), sum_e=("e","sum"), mal=("y","sum"))
first_e={}   # cumulative e over the first n0 events, per candidate n0
print("\n" + "="*100)
print("  POLICY COMPARISON  (all guarantee m <= n0, so all are VALID)")
print("="*100)
print(f"  {'policy':<34} {'n0':>9} {'T':>9} {'threshold':>12} {'episodes det.':>14} {'floor(mal)':>11}")
print("  "+"-"*94)
res=[]
att_idx=agg["mal"]>0
def report(name,n0,T,stat,extra=""):
    thr=T/W0
    det=stat>=thr
    a=agg[att_idx]
    d=det[att_idx]
    floor=int(a.loc[d,"mal"].min()) if d.any() else None
    print(f"  {name:<34} {n0:>9,} {T:>9,} {thr:>12,.0f} {int(d.sum()):>7,}/{len(a):<6,} "
          f"{(floor if floor else '-'):>11}")
    res.append(dict(policy=name,n0=int(n0),T=int(T),thr=float(thr),
                    det=int(d.sum()),n_ep=int(len(a)),floor=floor))

# A: n0 = max group size
n0A=N0_MAX_CAL; report("A. n0 = max group size", n0A, T0, agg["sum_e"]/n0A)
# B: truncate to first n0 events (by time within group)
for n0B in (n0_p99,):
    cum=gsort.groupby("gid",observed=True).cumcount()
    trunc=gsort[cum<n0B].groupby("gid",observed=True)["e"].sum()
    report(f"B. truncate at first n0", n0B, T0, trunc/n0B)
# C: deterministic split of oversized groups
n0C=n0_p99
sub=(gsort.groupby("gid",observed=True).cumcount()//n0C)
sub_id=gsort["gid"].astype(str)+"#"+sub.astype(str)
aggC=pd.DataFrame({"sid":sub_id,"e":gsort["e"].to_numpy(),"y":gsort["y"].to_numpy()}) \
       .groupby("sid",observed=True).agg(n=("e","size"),sum_e=("e","sum"),mal=("y","sum"))
TC=len(aggC); thrC=TC/W0; detC=(aggC["sum_e"]/n0C)>=thrC
# map sub-group -> original episode so the denominator matches A/B/D
orig=pd.Series(aggC.index.str.rsplit("#",n=1).str[0], index=aggC.index)
ep_det=detC.groupby(orig).any()                      # episode detected if ANY sub-group fires
ep_mal=aggC["mal"].groupby(orig).sum()
attC=ep_mal[ep_mal>0]
dC=ep_det.reindex(attC.index).fillna(False)
fC=int(attC[dC].min()) if dC.any() else None
print(f"  {'C. split oversized into sub-groups':<34} {n0C:>9,} {TC:>9,} {thrC:>12,.0f} "
      f"{int(dC.sum()):>7,}/{len(attC):<6,} {(fC if fC else '-'):>11}")
res.append(dict(policy="C. split oversized",n0=int(n0C),T=int(TC),thr=float(thrC),
                det=int(dC.sum()),n_ep=int(len(attC)),floor=fC))
# D: pre-committed slot (single e-value per group, slot chosen by keyed hash)
# D is RANDOMISED: report the exact expectation, not one draw. Feasibility factor included.
fire_ct0=gsort.assign(f=(gsort["e"].to_numpy()>0).astype(int)).groupby("gid",observed=True)["f"].sum()
feas = 1.0 if CEIL>=thr0 else 0.0
p_detD=feas*(fire_ct0/agg["n"])
expD=float(p_detD[att_idx].sum()); aD=agg[att_idx]
mc=[int((np.random.default_rng(1000+r).random(len(aD))<p_detD[att_idx].to_numpy()).sum())
    for r in range(400)]
mc=np.array(mc)
fD=int(aD.loc[p_detD[att_idx]>0,"mal"].min()) if (p_detD[att_idx]>0).any() else None
print(f"  {'D. slot (E[detected], 95% MC CI)':<34} {1:>9,} {T0:>9,} {thr0:>12,.0f} "
      f"{expD:>7.1f}/{len(aD):<6,} {(fD if fD else '-'):>11}   "
      f"CI=[{np.percentile(mc,2.5):.0f},{np.percentile(mc,97.5):.0f}]")
res.append(dict(policy="D. pre-committed slot",n0=1,T=int(T0),thr=float(thr0),
                det=expD,det_ci=[float(np.percentile(mc,2.5)),float(np.percentile(mc,97.5))],
                n_ep=int(len(aD)),floor=fD,feasible=bool(CEIL>=thr0)))
json.dump({"P_fire_cal":float(P_FIRE_CAL),"P_fire_te":float(P_FIRE_TE),"NC":int(NC),
           "n0_p99":int(n0_p99),"viol_groups":int(viol),"T0":int(T0),"policies":res},
          open("out/t14_T1.json","w"),indent=1)
print("\nwrote out/t14_T1.json")

# ================= attack channel per policy =================
print("\n" + "="*100)
print("  ATTACK CHANNEL OPENED BY EACH VALID POLICY")
print("="*100)

# --- B: front-load attack. Attacker emits leading benign flows so the malicious ones
#     fall beyond index n0 and are never counted.
n0B=n0_p99
cum=gsort.groupby("gid",observed=True).cumcount()
gs=gsort.assign(pos=cum.to_numpy())
trunc_e=gs[gs["pos"]<n0B].groupby("gid",observed=True)["e"].sum()
detB=(trunc_e/n0B)>=thr0
detB_ep=detB[att_idx.reindex(detB.index).fillna(False)]
# for each detected episode: how many leading pads push every firing flow past n0?
costs=[]
for gid_,sub_ in gs[gs["gid"].isin(detB_ep[detB_ep].index)].groupby("gid",observed=True):
    fire=sub_["pos"].to_numpy()[sub_["e"].to_numpy()>0]
    if len(fire)==0: continue
    # need pads P such that (first firing position + P) >= n0  -> P = n0 - min_fire_pos
    costs.append(max(0, n0B - int(fire.min())))
costs=np.array(costs) if costs else np.array([0])
print(f"  B (truncate at {n0B}): detected {int(detB_ep.sum())} episodes")
print(f"    front-load pads to suppress: median={int(np.median(costs)):,}  "
      f"min={int(costs.min()):,}  max={int(costs.max()):,}")
print(f"    (upper bound is n0 = {n0B:,} leading benign flows -- fills the counted window)")

# --- D: slot rule. Padding does not break validity, it dilutes the HIT PROBABILITY.
att_g=agg[att_idx].copy()
att_g["p_hit"]=[ (gsort.loc[gsort["gid"]==i,"e"].to_numpy()>0).sum()/att_g.loc[i,"n"]
                 for i in att_g.index[:0] ] if False else np.nan
# vectorised: fraction of firing events per group
fire_ct=gsort.assign(f=(gsort["e"].to_numpy()>0).astype(int)).groupby("gid",observed=True)["f"].sum()
p_hit=(feas*fire_ct/agg["n"])[att_idx]
print(f"\n  D (pre-committed slot): P(detect) = fraction of group that fires")
print(f"    median P(detect) over attack episodes = {p_hit.median():.3f}")
for mult in (1,2,5,10,100):
    print(f"    after padding group x{mult:<4}: median P(detect) = {p_hit.median()/mult:.4f}  "
          f"expected detections = {(p_hit/mult).sum():.1f} / {len(p_hit)}")
print("    -> validity survives padding; POWER decays as 1/m. And the rule is randomised:")
print("       the alert depends on a coin flip, which a SOC cannot audit.")

print("\n" + "="*100)
print("  T1 SUMMARY")
print("="*100)
print("  Every policy that restores validity is either powerless or attackable:")
for r in res:
    d=r["det"]; d=f"{d:.1f}" if isinstance(d,float) else f"{d:,}"
    print(f"    {r['policy']:<34} n0={r['n0']:>8,}  T={r['T']:>8,}  detected {d}/{r['n_ep']:,}")
print(f"    B front-load cost: median {int(np.median(costs)):,} leading pads")
