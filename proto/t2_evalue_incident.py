"""
TEST 2a: is mean-of-conformal-e-values valid under ARBITRARY within-incident
         dependence?  (the technical claim C1 rests on)
TEST 2b: does incident-level aggregation escape the structural silence of Test 1?
"""
import numpy as np, math, json
from t1_silence import gamma_poly, LORDpp, LOND

# ---------------- conformal e-values ----------------
def e_threshold(cal_sorted, s, k):
    """e = (n+1)/k * 1{rank(s) <= k};  E[e]=1 under exchangeability. max = (n+1)/k"""
    n = len(cal_sorted)
    K = 1 + (n - np.searchsorted(cal_sorted, s, side='left'))   # 1..n+1
    return np.where(K <= k, (n+1.0)/k, 0.0)

def e_harmonic(cal_sorted, s):
    """e = (n+1)/(K * H_{n+1});  E[e]=1 exactly.  max = (n+1)/H_{n+1}"""
    n = len(cal_sorted)
    K = 1 + (n - np.searchsorted(cal_sorted, s, side='left'))
    H = np.sum(1.0/np.arange(1, n+2))
    return (n+1.0)/(K*H)

def conformal_p(cal_sorted, s):
    n = len(cal_sorted)
    return (1.0 + (n - np.searchsorted(cal_sorted, s, side='left')))/(n+1.0)

# ---------------- 2a: validity under dependence ----------------
def test_validity(ncal=10_000, n_ev=200, reps=20_000, seed=0):
    rng = np.random.default_rng(seed)
    cal = np.sort(rng.normal(0,1,ncal))
    print("="*84)
    print("2a. VALIDITY of aggregated evidence under WITHIN-INCIDENT DEPENDENCE")
    print(f"    {reps:,} replicate null incidents, each {n_ev} benign events, |C|={ncal:,}")
    print("    a valid e-value needs E[.] <= 1 ; a valid p-value needs P(p<=x) <= x")
    print("="*84)
    print(f"{'dependence':>18} {'mean(mean e_thr)':>17} {'mean(mean e_harm)':>18} "
          f"{'P(mean_p<=.05)':>15} {'P(2*mean_p<=.05)':>17}")
    print("-"*88)
    for dep_name, rho in [("independent",0.0),("AR(1) rho=.9",0.9),
                          ("AR(1) rho=.99",0.99),("perfectly identical",1.0)]:
        me_t=[]; me_h=[]; mp=[]
        for _ in range(reps):
            if rho >= 1.0:
                x = np.full(n_ev, rng.normal(0,1))            # worst case: all same
            elif rho == 0.0:
                x = rng.normal(0,1,n_ev)
            else:
                z = rng.normal(0,1,n_ev); x = np.empty(n_ev); x[0]=z[0]
                for i in range(1,n_ev): x[i]=rho*x[i-1]+math.sqrt(1-rho**2)*z[i]
            me_t.append(e_threshold(cal, x, k=max(1,ncal//100)).mean())
            me_h.append(e_harmonic(cal, x).mean())
            mp.append(conformal_p(cal, x).mean())
        me_t=np.array(me_t); me_h=np.array(me_h); mp=np.array(mp)
        print(f"{dep_name:>18} {me_t.mean():>17.4f} {me_h.mean():>18.4f} "
              f"{(mp<=0.05).mean():>15.4f} {(2*mp<=0.05).mean():>17.4f}")
    print("\n  -> e-value columns must stay <= 1.0 in EVERY row (that is the C1 claim)")
    print("  -> mean-p column shows why p-values need the 2x Vovk-Wang correction\n")

# ---------------- 2b: does aggregation escape silence? ----------------
def run_incident_level(T_events, pi, mu, ncal, inc_size, alpha=0.05, seed=0, k_frac=0.01):
    """group the stream into incidents of inc_size events; one hypothesis per incident;
       evidence = mean of conformal e-values; reject when mean_e >= 1/alpha_t"""
    rng = np.random.default_rng(seed)
    cal = np.sort(rng.normal(0,1,ncal))
    n_inc = T_events//inc_size
    n_att_inc = max(1, int(round(n_inc*pi)))
    att = np.zeros(n_inc, bool); att[rng.choice(n_inc, n_att_inc, replace=False)] = True
    gam = gamma_poly(n_inc+10)
    k = max(1, int(ncal*k_frac)); emax = (ncal+1.0)/k
    proc = LORDpp(gam, alpha=alpha)
    R=V=0; silent=0; first_silent=None
    for j in range(1, n_inc+1):
        x = rng.normal(mu if att[j-1] else 0.0, 1.0, inc_size)
        E = e_threshold(cal, x, k).mean()
        a = proc.level(j)
        if a <= 0 or emax < 1.0/a:              # cannot possibly reject
            silent += 1
            if first_silent is None: first_silent=j
            continue
        if E >= 1.0/a:
            R += 1
            if not att[j-1]: V += 1
            proc.record(j)
    return dict(n_inc=n_inc, inc_size=inc_size, ncal=ncal, n_att=int(n_att_inc), R=R, V=V,
                FDP=(V/R if R else float('nan')), recall=(R-V)/n_att_inc,
                silence=silent/n_inc, first_silent=first_silent, emax=emax)

if __name__ == "__main__":
    test_validity()
    print("="*84)
    print("2b. INCIDENT-LEVEL aggregation vs the silence of Test 1")
    print("    same 500,000-event stream, 1% of INCIDENTS malicious, mu=5, alpha=0.05")
    print("="*84)
    hdr=f"{'inc_size':>9} {'#hypoth':>8} {'|C|':>10} {'#att':>5} {'R':>5} {'FDP':>7} {'recall':>7} {'silent%':>8} {'1st sil':>8}"
    print(hdr); print("-"*len(hdr))
    rows=[]
    for inc_size in (1, 10, 100, 1000):
        for ncal in (10_000, 1_000_000):
            r = run_incident_level(500_000, 0.01, 5.0, ncal, inc_size, seed=3)
            rows.append(r); fs=r['first_silent']
            print(f"{inc_size:>9} {r['n_inc']:>8,} {ncal:>10,} {r['n_att']:>5} {r['R']:>5} "
                  f"{r['FDP']:>7.3f} {r['recall']:>7.3f} {100*r['silence']:>7.1f}% {(str(fs) if fs else '-'):>8}")
    json.dump(rows, open("out/t2_incident.json","w"), indent=1)
    print("\nwrote out/t2_incident.json")
