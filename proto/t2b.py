"""
TEST 2 (corrected).
2a: separate the DEPENDENCE question from the CALIBRATION-CONDITIONAL question.
2b: sweep the e-value ceiling k -- does ANY config escape silence WITH power?
"""
import numpy as np, math, json
from t1_silence import gamma_poly, LORDpp

def K_rank(cal_sorted, s):
    n=len(cal_sorted); return 1 + (n - np.searchsorted(cal_sorted, s, side='left'))
def e_thr(cal_sorted, s, k):
    n=len(cal_sorted); return np.where(K_rank(cal_sorted,s)<=k, (n+1.0)/k, 0.0)

def dep_draw(rng, n, rho):
    if rho>=1.0: return np.full(n, rng.normal(0,1))
    if rho<=0.0: return rng.normal(0,1,n)
    z=rng.normal(0,1,n); x=np.empty(n); x[0]=z[0]
    c=math.sqrt(1-rho**2)
    for i in range(1,n): x[i]=rho*x[i-1]+c*z[i]
    return x

def test_2a(ncal=10_000, n_ev=100, reps=8000, seed=0):
    rng=np.random.default_rng(seed)
    print("="*94)
    print("2a. E[ mean-of-e-values ] under within-incident dependence.  Valid needs <= 1.0")
    print(f"    |C|={ncal:,}  events/incident={n_ev}  reps={reps:,}")
    print("    FIXED cal = one calibration set reused (what you deploy)")
    print("    REDRAWN  = fresh calibration set per incident (the marginal guarantee)")
    print("    NOTE: validity under dependence is a THEOREM (linearity of expectation).")
    print("    Cells marked UNINFORMATIVE have MC standard error > 25% of the estimate")
    print("    and cannot distinguish E=1 from E=0 or E=3. They are not evidence.")
    print("="*94)
    print(f"{'k (e ceiling)':>16} {'mode':>9} " + " ".join(f"{n:>13}" for n in
          ["indep","AR(1) .9","AR(1) .99","identical"]))
    print("-"*94)
    out=[]
    for k in (1, 10, 100, 1000):
        for mode in ("FIXED","REDRAWN"):
            row=[]
            for rho in (0.0,0.9,0.99,1.0):
                # FIXED: independent calibration draw per (k,mode,rho) cell so columns
                # are not perfectly correlated; and report MC standard error, because at
                # small k the estimator variance EXCEEDS the quantity being estimated.
                cal_fixed=np.sort(rng.normal(0,1,ncal))
                vals=np.empty(reps)
                for r in range(reps):
                    cal = cal_fixed if mode=="FIXED" else np.sort(rng.normal(0,1,ncal))
                    vals[r]=e_thr(cal, dep_draw(rng,n_ev,rho), k).mean()
                se = vals.std(ddof=1)/np.sqrt(reps)
                row.append((vals.mean(), se))
            ceil=(ncal+1)/k
            print(f"{k:>6} (max e={ceil:>6.0f}) {mode:>9} " +
                  " ".join((f"{m:>7.3f}+-{se:<5.3f}" if se<0.25*max(m,1e-9) else f"{'UNINFORMATIVE':>13}")
                           for m,se in row))
            out.append(dict(k=k,mode=mode,ceiling=ceil,means=[m for m,_ in row],
                            mc_se=[se for _,se in row]))
    json.dump(out, open("out/t2a.json","w"), indent=1)
    print()

def run_inc(T_events, pi_inc, mu, ncal, inc_size, k, alpha=0.05, seed=0):
    rng=np.random.default_rng(seed)
    cal=np.sort(rng.normal(0,1,ncal))
    n_inc=T_events//inc_size
    n_att=max(1,int(round(n_inc*pi_inc)))
    att=np.zeros(n_inc,bool); att[rng.choice(n_inc,n_att,replace=False)]=True
    gam=gamma_poly(n_inc+10); proc=LORDpp(gam,alpha=alpha)
    ceil=(ncal+1.0)/k
    R=V=0; silent=0; first=None
    for j in range(1,n_inc+1):
        x=rng.normal(mu if att[j-1] else 0.0,1.0,inc_size)
        E=e_thr(cal,x,k).mean()
        a=proc.level(j)
        if a<=0 or ceil < 1.0/a:
            silent+=1
            if first is None: first=j
            continue
        if E>=1.0/a:
            R+=1
            if not att[j-1]: V+=1
            proc.record(j)
    return dict(n_inc=n_inc,inc_size=inc_size,ncal=ncal,k=k,n_att=int(n_att),R=R,V=V,
                FDP=(V/R if R else float('nan')),recall=(R-V)/n_att,
                silence=silent/n_inc,first=first)

def test_2b():
    print("="*100)
    print("2b. Does INCIDENT-LEVEL aggregation escape structural silence *with power*?")
    print("    500,000-event stream, 1% of incidents malicious, mu=5, alpha=0.05, gamma~j^-1.6")
    print("="*100)
    hdr=(f"{'inc_size':>9} {'#hyp':>8} {'|C|':>10} {'k':>5} {'max e':>9} {'#att':>5} "
         f"{'R':>5} {'FDP':>7} {'recall':>7} {'silent%':>8}")
    print(hdr); print("-"*len(hdr)); rows=[]
    for inc_size in (1,100,1000):
        for ncal in (10_000,1_000_000):
            for k in (1,10):
                r=run_inc(500_000,0.01,5.0,ncal,inc_size,k,seed=3); rows.append(r)
                print(f"{inc_size:>9} {r['n_inc']:>8,} {ncal:>10,} {k:>5} "
                      f"{(ncal+1)/k:>9.0f} {r['n_att']:>5} {r['R']:>5} {r['FDP']:>7.3f} "
                      f"{r['recall']:>7.3f} {100*r['silence']:>7.1f}%")
    json.dump(rows,open("out/t2b.json","w"),indent=1)
    print("\nwrote out/t2a.json out/t2b.json")

if __name__=="__main__":
    test_2a(); test_2b()
