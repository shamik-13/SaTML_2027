"""T2 -- full-stream re-run with genuine repetition."""

import os

# The derived LSPR23 CSV.  Same override pattern as h_stream/h_meta: LSPR_DIR moves the
# inputs off the volatile /tmp default without changing behaviour for the documented recipes.
CSV = os.environ.get("LSPR_CSV", f'{os.environ.get("LSPR_DIR", "/tmp")}/lspr_full.csv')


def main():
    import numpy as np, pandas as pd, json, time, gc
    from pathlib import Path
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.metrics import roc_auc_score
    Path("out").mkdir(exist_ok=True)

    t0=time.time()
    cols=["ts","src","dst","label","proto"]+[f"f{i}" for i in range(32)]
    dt={"ts":"int64","src":"category","dst":"category","label":"int8","proto":"float32"}
    dt.update({f"f{i}":"float32" for i in range(32)})
    df=pd.read_csv(CSV,header=None,names=cols,dtype=dt,low_memory=False)
    df=df.sort_values("ts",kind="mergesort").reset_index(drop=True)
    feat=["proto"]+[f"f{i}" for i in range(32)]
    X=df[feat].to_numpy(dtype=np.float32,copy=True)
    np.nan_to_num(X,copy=False,nan=0.0,posinf=0.0,neginf=0.0)
    y=df["label"].to_numpy(copy=True); ts=df["ts"].to_numpy(copy=True)
    src=df["src"].cat.codes.to_numpy(dtype=np.int32,copy=True)
    dst=df["dst"].cat.codes.to_numpy(dtype=np.int32,copy=True)
    del df; gc.collect()
    N=len(y)
    print(f"loaded+sorted N={N:,}  malicious={y.sum():,} ({100*y.mean():.2f}%)  "
          f"span={(ts[-1]-ts[0])/3.6e9:.1f} h  [{time.time()-t0:.0f}s]")

    W0=0.025; K=1
    CAL_F, TEST_F = 0.15, 0.15
    POS=[0.55,0.62,0.70,0.77,0.85]
    SEEDS=[0,1]
    results=[]
    for pos in POS:
        i2=int(pos*N); i1=i2-int(CAL_F*N); i3=min(N,i2+int(TEST_F*N))
        if i1<=0: continue
        groups={}
        for BH in (1,2,6):
            b=ts[i2:i3]//(BH*3600*1_000_000)
            key=np.empty(i3-i2,dtype=[("s","i4"),("d","i4"),("b","i8")])
            key["s"]=src[i2:i3]; key["d"]=dst[i2:i3]; key["b"]=b
            _,gid=np.unique(key,return_inverse=True)
            T=int(gid.max()+1)
            groups[BH]=(gid,T,np.bincount(gid,minlength=T),
                        np.bincount(gid,weights=y[i2:i3].astype(float),minlength=T))
        for seed in SEEDS:
            rng=np.random.default_rng(seed)
            tr=np.arange(i1)
            ben=tr[y[tr]==0]; keep=rng.random(len(ben))<0.5
            tr_idx=np.sort(np.concatenate([tr[y[tr]==1],ben[keep]]))
            clf=HistGradientBoostingClassifier(max_iter=200,learning_rate=0.1,
                  l2_regularization=1.0,min_samples_leaf=200,random_state=seed,
                  early_stopping=False).fit(X[tr_idx],y[tr_idx])
            s_cal=clf.decision_function(X[i1:i2]); s_te=clf.decision_function(X[i2:i3])
            y_cal,y_te=y[i1:i2],y[i2:i3]
            cal=np.sort(s_cal[y_cal==0]); NC=len(cal); CEIL=NC+1.0
            auc=float(roc_auc_score(y_te,s_te)) if np.unique(y_te).size==2 else None
            ac=s_cal[y_cal==1]
            pf=1+(NC-np.searchsorted(cal,ac,side='left'))<=K
            p_fire_cal=float(pf.mean()) if pf.size else None
            Kr=1+(NC-np.searchsorted(cal,s_te,side='left'))
            e_te=np.where(Kr<=K,CEIL,0.0)
            for BH,(gid,T,nsz,mal) in groups.items():
                sum_e=np.bincount(gid,weights=e_te,minlength=T)
                thr=T/W0; margin=CEIL/thr-1.0
                am=mal>0; det=am&((sum_e/np.maximum(nsz,1))>=thr)
                if det.any():
                    x=sum_e[det]/thr-nsz[det]
                    med_pad=float(np.median(np.floor(x).astype(np.int64)+1))
                else:
                    med_pad=None
                results.append(dict(pos=pos,seed=seed,BH=BH,auc=auc,NC=int(NC),
                    N_test=int(i3-i2),p_fire_cal=p_fire_cal,T=T,thr=float(thr),
                    ceiling=float(CEIL),margin=float(margin),feasible=bool(margin>=0),
                    n_ep=int(am.sum()),det=int(det.sum()),med_pad=med_pad))
                print(f"  pos={pos} seed={seed} {BH}h: AUC={auc if auc is None else round(auc,4)} "
                      f"|C|={NC:,} T={T:,} margin={margin:+.3f} det={int(det.sum())}/{int(am.sum())} "
                      f"medpad={med_pad}  [{time.time()-t0:.0f}s]")
            del clf,s_cal,s_te,e_te; gc.collect()
    with open("out/t17_T2.json","w") as f: json.dump(results,f,indent=1,allow_nan=False)

    R=pd.DataFrame(results)
    print("\n"+"="*108); print("T2 SUMMARY"); print("="*108)
    print(f"  detector AUROC {R['auc'].min():.4f}-{R['auc'].max():.4f}   "
          f"|C| {R['NC'].min():,}-{R['NC'].max():,}   "
          f"P_fire(cal) {R['p_fire_cal'].min():.3f}-{R['p_fire_cal'].max():.3f}")
    print("\n  A. FEASIBILITY MARGIN across the 5 window positions (seed-independent by design)")
    print(f"  {'grouping':>9} {'T range':>21} {'margin values':>44} {'feasible':>10}")
    for BH,g in R.groupby("BH"):
        u=g.drop_duplicates(subset=["pos"])
        vals=", ".join(f"{m:+.3f}" for m in u["margin"])
        print(f"  {BH:>8}h {u['T'].min():>9,}-{u['T'].max():<10,} {vals:>44} "
              f"{int((u['margin']>=0).sum())}/{len(u):>2}")
    print("\n  B. DETECTIONS and DILUTION COST (varies with seed and position)")
    print(f"  {'grouping':>9} {'episodes':>10} {'detected':>16} {'median pad to suppress':>24}")
    for BH,g in R.groupby("BH"):
        mp=g["med_pad"].dropna()
        print(f"  {BH:>8}h {g['n_ep'].min():>4}-{g['n_ep'].max():<5} "
              f"{g['det'].min():>6}-{g['det'].max():<8} "
              f"{(f'{mp.min():.0f}-{mp.max():.0f}' if len(mp) else 'no detections'):>24}")
    print(f"\n  runtime {time.time()-t0:.0f}s")

    return results


if __name__ == "__main__":
    main()
