"""
TEST 5: end-to-end at LSPR23's REAL operating point.
16.0M flows total, 1.6M malicious, 288 red-team campaigns (from the narratives file).
=> event-level stream length T = 16,000,000 hypotheses
=> incident-level stream length T = 288 hypotheses
Question: does the escape from structural silence hold at the real scale, and with a
REALISTIC (not idealised) detector?
"""
import numpy as np, json
from t1_silence import gamma_poly, LORDpp

T_EVENTS   = 16_000_000
N_INCIDENT = 288
MAL_FLOWS  = 1_600_000

print("="*96)
print("LSPR23 real structure (from downloaded narratives + published counts)")
print(f"  total flows            {T_EVENTS:>12,}")
print(f"  malicious flows        {MAL_FLOWS:>12,}   ({100*MAL_FLOWS/T_EVENTS:.1f}%)")
print(f"  red-team campaigns     {N_INCIDENT:>12,}")
print(f"  mean flows / campaign  {MAL_FLOWS//N_INCIDENT:>12,}")
print(f"  => hypotheses, event-level    {T_EVENTS:>12,}")
print(f"  => hypotheses, incident-level {N_INCIDENT:>12,}   ({T_EVENTS/N_INCIDENT:,.0f}x fewer)")
print("="*96)

def alpha_floor_check(T, ncal, alpha=0.05, k=1):
    """what test level is available at the END of the stream with NO rejections,
       and is the evidence ceiling enough?"""
    gam = gamma_poly(T+10); w0=alpha/2
    a_end = gam[T-1]*w0
    ceiling = (ncal+1.0)/k
    return a_end, ceiling, (ceiling >= 1.0/a_end if a_end>0 else False)

print(f"\n{'level':>14} {'T (hypoth)':>12} {'|C|':>11} {'k':>3} {'alpha_T':>11} "
      f"{'need ceiling':>14} {'have ceiling':>13} {'CAN ALERT?':>11}")
print("-"*98)
for lvl, T in [("event", T_EVENTS), ("incident", N_INCIDENT)]:
    for ncal in (10_000, 1_000_000):
        for k in (1, 100):
            a,c,ok = alpha_floor_check(T, ncal, k=k)
            print(f"{lvl:>14} {T:>12,} {ncal:>11,} {k:>3} {a:>11.2e} "
                  f"{1/a:>14,.0f} {c:>13,.0f} {'YES' if ok else 'NO':>11}")

# ---- realistic detector: sweep separation, incident level, real T ----
print("\n" + "="*96)
print("Incident-level control at T=288 with a REALISTIC detector")
print("(mu = how many benign-sd the mean attack flow scores above benign; real NIDS")
print(" on NetFlow features is typically mu ~ 1.5-3 for hard families, 4+ for volumetric)")
print("="*96)
def run(mu, ncal, k, inc_size=5555, n_inc=288, n_att=None, alpha=0.05, seed=0, reps=5):
    out=[]
    for rep in range(reps):
        rng=np.random.default_rng(seed+rep)
        cal=np.sort(rng.normal(0,1,ncal))
        na = n_att if n_att else max(1,int(0.5*n_inc))
        att=np.zeros(n_inc,bool); att[rng.choice(n_inc,na,replace=False)]=True
        gam=gamma_poly(n_inc+10); proc=LORDpp(gam,alpha=alpha); ceil=(ncal+1.0)/k
        R=V=0; silent=0
        for j in range(1,n_inc+1):
            x=rng.normal(mu if att[j-1] else 0.0,1.0,inc_size)
            Kr=1+(ncal-np.searchsorted(cal,x,side='left'))
            E=np.where(Kr<=k,(ncal+1.0)/k,0.0).mean()
            a=proc.level(j)
            if a<=0 or ceil<1.0/a: silent+=1; continue
            if E>=1.0/a:
                R+=1
                if not att[j-1]: V+=1
                proc.record(j)
        out.append((R,V,(V/R if R else np.nan),(R-V)/na,silent/n_inc))
    A=np.array(out,dtype=float)
    return A.mean(axis=0)

print(f"{'mu':>5} {'|C|':>10} {'k':>5} {'R':>7} {'FDP':>7} {'incid.recall':>13} {'silent%':>8}")
print("-"*62)
rows=[]
for mu in (1.5, 2.0, 3.0, 5.0):
    for ncal,k in ((1_000_000,1),(1_000_000,100),(10_000,1)):
        R,V,fdp,rec,sil = run(mu,ncal,k)
        rows.append(dict(mu=mu,ncal=ncal,k=k,R=R,FDP=float(fdp),recall=rec,silence=sil))
        print(f"{mu:>5.1f} {ncal:>10,} {k:>5} {R:>7.1f} {fdp:>7.3f} {rec:>13.3f} {100*sil:>7.1f}%")
json.dump(rows,open("out/t5_realscale.json","w"),indent=1)
print("\nwrote out/t5_realscale.json")
