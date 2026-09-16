"""
T5 -- feasibility boundary per online procedure, measured on the real episode stream.
T6 -- attacker-origin padding: does traffic from an attacker-controlled host score as low
      as generic benign traffic?
"""
import numpy as np, pandas as pd, json, time, gc
from pathlib import Path
from scipy.special import zeta
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
Path("out").mkdir(exist_ok=True)
t0=time.time()
cols=["ts","src","dst","label","proto"]+[f"f{i}" for i in range(32)]
dt={"ts":"int64","src":"category","dst":"category","label":"int8","proto":"float32"}
dt.update({f"f{i}":"float32" for i in range(32)})
df=pd.read_csv("/tmp/lspr_full.csv",header=None,names=cols,dtype=dt,low_memory=False)
df=df.sort_values("ts",kind="mergesort").reset_index(drop=True)
feat=["proto"]+[f"f{i}" for i in range(32)]
X=df[feat].to_numpy(dtype=np.float32,copy=True)
np.nan_to_num(X,copy=False,nan=0.0,posinf=0.0,neginf=0.0)
y=df["label"].to_numpy(copy=True); ts=df["ts"].to_numpy(copy=True)
src=df["src"].cat.codes.to_numpy(dtype=np.int32,copy=True)
dst=df["dst"].cat.codes.to_numpy(dtype=np.int32,copy=True)
del df; gc.collect(); N=len(y)

POS=0.85; CAL_F=TEST_F=0.15; W0=0.025; A=0.05; K=1
i2=int(POS*N); i1=i2-int(CAL_F*N); i3=min(N,i2+int(TEST_F*N))
rng=np.random.default_rng(0); tr=np.arange(i1); ben=tr[y[tr]==0]
tr_idx=np.sort(np.concatenate([tr[y[tr]==1],ben[rng.random(len(ben))<0.5]]))
clf=HistGradientBoostingClassifier(max_iter=200,learning_rate=0.1,l2_regularization=1.0,
      min_samples_leaf=200,random_state=0,early_stopping=False).fit(X[tr_idx],y[tr_idx])
s_cal=clf.decision_function(X[i1:i2]); s_te=clf.decision_function(X[i2:i3])
y_cal,y_te=y[i1:i2],y[i2:i3]
cal=np.sort(s_cal[y_cal==0]); NC=len(cal); CEIL=NC+1.0
Kr=1+(NC-np.searchsorted(cal,s_te,side='left')); e_te=np.where(Kr<=K,CEIL,0.0)
print(f"detector AUROC={roc_auc_score(y_te,s_te):.4f}  |C|={NC:,}  ceiling={CEIL:,.0f}  [{time.time()-t0:.0f}s]")

BH=2; b=ts[i2:i3]//(BH*3600*1_000_000)
key=np.empty(i3-i2,dtype=[("s","i4"),("d","i4"),("b","i8")])
key["s"]=src[i2:i3]; key["d"]=dst[i2:i3]; key["b"]=b
_,gid=np.unique(key,return_inverse=True); T=int(gid.max()+1)
nsz=np.bincount(gid,minlength=T); mal=np.bincount(gid,weights=y_te.astype(float),minlength=T)
sum_e=np.bincount(gid,weights=e_te,minlength=T)
first_ts=np.full(T,np.iinfo(np.int64).max)
np.minimum.at(first_ts,gid,ts[i2:i3])
first_pos=np.full(T,np.iinfo(np.int64).max)
np.minimum.at(first_pos,gid,np.arange(len(gid),dtype=np.int64))
order=np.lexsort((first_pos,first_ts))   # ties broken by first stream occurrence
Ev=(sum_e/np.maximum(nsz,1))[order]; ismal=(mal>0)[order]
print(f"episodes T={T:,}  malicious={int(ismal.sum()):,}")

# ---------------- T5: per-procedure feasibility + detections ----------------
gam=np.arange(1,T+1,dtype=float)**-1.6/float(zeta(1.6,1))
def run(proc):
    R=0; rej=0; tp=0; silent=0; first=None; rejt=[]
    w0=A/2
    for t in range(1,T+1):
        if proc=="LOND":      lvl=A*gam[t-1]*(R+1)
        elif proc=="e-LOND":  lvl=A*gam[t-1]*(R+1)
        elif proc=="LORD++":
            lvl=gam[t-1]*w0
            if rejt:
                lvl+= (A-w0)*gam[t-rejt[0]-1] if t>rejt[0] else 0.0
                for tau in rejt[1:]:
                    if t>tau: lvl+=A*gam[t-tau-1]
        if lvl<=0 or CEIL<1.0/lvl:
            silent+=1
            if first is None: first=t
            continue
        if Ev[t-1]>=1.0/lvl:
            R+=1; rej+=1; rejt.append(t)
            if ismal[t-1]: tp+=1
    return dict(proc=proc,rejections=rej,tp=tp,fdp=float(1-tp/rej) if rej else float('nan'),
                recall=float(tp/ismal.sum()),silent=float(silent/T),first_infeasible=first)
print("\n"+"="*96); print("T5 -- FEASIBILITY BOUNDARY PER PROCEDURE (real episode stream)"); print("="*96)
print(f"  {'procedure':>10} {'rejections':>11} {'true pos':>9} {'FDP':>8} {'recall':>8} {'silent':>8} {'1st infeasible':>15}")
t5=[]
for pr in ("LOND","e-LOND","LORD++"):
    r=run(pr); t5.append(r)
    print(f"  {r['proc']:>10} {r['rejections']:>11,} {r['tp']:>9,} "
          f"{r['fdp']:>8.3f} {r['recall']:>8.3f} {100*r['silent']:>7.1f}% "
          f"{(format(r['first_infeasible'],',') if r['first_infeasible'] else '-'):>15}")
print("  All three sit in the Family-I/II template of section 4.13; none escapes it.")
print("  NOT implemented: SAFFRON, ADDIS, e-GAI, compound-e/e-closure.")

# ---------------- T6: attacker-origin padding ----------------
print("\n"+"="*96); print("T6 -- ATTACKER-ORIGIN PADDING"); print("="*96)
src_te=src[i2:i3]
att_src=np.unique(src_te[y_te==1])
is_att_src=np.isin(src_te,att_src)
gen_ben=e_te[(y_te==0)]
ao_ben =e_te[(y_te==0)&is_att_src]
print(f"  attack source IPs in test window: {len(att_src):,}")
print(f"  benign flows overall            : {len(gen_ben):,}   P(fire)={float((gen_ben>0).mean()):.3e}  mean e={gen_ben.mean():.3f}")
print(f"  benign flows from attack sources: {len(ao_ben):,}   P(fire)={float((ao_ben>0).mean()):.3e}  mean e={ao_ben.mean():.3f}")
thr=T/W0
print(f"\n  rejection threshold tau = {thr:,.0f}   evidence ceiling = {CEIL:,.0f}")
print(f"  padding INFLATES instead of diluting once mean(e_pad) >= tau = {thr:,.0f}")
det=np.nonzero(ismal & (Ev>=thr))[0]
print(f"  detected episodes (mean rule) = {len(det):,}")
rows=[]
for nm,pool in [("generic benign",gen_ben),("attacker-origin benign",ao_ben)]:
    mu=float(pool.mean())
    if mu>=thr: print(f"  {nm}: mean e={mu:,.1f} >= tau -> padding cannot suppress"); continue
    pads=[]
    for j in det:
        S=Ev[j]*max(nsz[order][j],1); n=nsz[order][j]
        need=(S-thr*n)/(thr-mu)
        pads.append(int(np.floor(need))+1 if need>0 else 1)
    pads=np.array(pads)
    rows.append(dict(pool=nm,mean_e=mu,p_fire=float((pool>0).mean()),
                     med=float(np.median(pads)),p10=float(np.percentile(pads,10)),
                     p90=float(np.percentile(pads,90))))
    print(f"  {nm:>24}: mean e={mu:>8.2f}  median pad={np.median(pads):>8.0f}  "
          f"p10={np.percentile(pads,10):>7.0f}  p90={np.percentile(pads,90):>8.0f}")
json.dump({"T5":t5,"T6":rows,"T":int(T),"thr":float(thr),"CEIL":float(CEIL),
           "n_att_src":int(len(att_src))},open("out/t19_T5T6.json","w"),indent=1,allow_nan=False)
print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t19_T5T6.json")
