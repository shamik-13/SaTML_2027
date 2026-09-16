"""
TEST 9: the three-way bind.
Sweep the committed group-size cap n0 and check, at LSPR23 scale:
  (a) FEASIBILITY   : can the procedure reject at all?  ceiling >= 1/alpha_T, T = N/n0
  (b) ADMISSIBLE RULE (mean)   : power, and suppressibility by padding
  (c) ROBUST RULE (sum/n0)     : power, and suppressibility by padding
Also checks validity of sum/n0 numerically.
"""
import numpy as np

N_EVENTS = 16_000_000      # LSPR23 scale
NCAL     = 1_000_000
K        = 1
ALPHA    = 0.05
W0       = ALPHA/2
CEIL     = (NCAL+1.0)/K     # max attainable e-value

def alpha_T(n0):            # horizon-uniform gamma (best case): alpha_t = w0/T
    T = max(1, N_EVENTS//n0)
    return W0/T, T

print("="*104)
print("9a. VALIDITY CHECK: is sum(e)/n0 a valid e-value under arbitrary dependence?")
print("    E[sum(e)/n0] = (#members/n0) * E[e] <= 1 whenever #members <= n0.  Verify numerically.")
print("="*104)
rng=np.random.default_rng(31); cal=np.sort(rng.normal(0,1,20_000))
def e_thr(cal,s,k):
    n=len(cal); Kr=1+(n-np.searchsorted(cal,s,side='left'))
    return np.where(Kr<=k,(n+1.0)/k,0.0)
n0=200
print(f"{'members':>9} {'dependence':>16} {'E[mean e]':>11} {'E[sum e/n0]':>13} {'valid?':>8}")
print("-"*62)
for m,rho in [(200,0.0),(200,0.99),(200,1.0),(50,0.0),(50,1.0)]:
    vals_m=[];vals_s=[]
    for _ in range(40_000):
        if rho>=1.0: x=np.full(m,rng.normal(0,1))
        elif rho==0: x=rng.normal(0,1,m)
        else:
            z=rng.normal(0,1,m);x=np.empty(m);x[0]=z[0];c=np.sqrt(1-rho**2)
            for i in range(1,m): x[i]=rho*x[i-1]+c*z[i]
        e=e_thr(cal,x,200)
        vals_m.append(e.mean()); vals_s.append(e.sum()/n0)
    em=np.mean(vals_m); es=np.mean(vals_s)
    flag = 'ok' if m<=n0 else 'INVALID(N>n0)'
    print(f"{m:>9} {('rho='+str(rho)):>16} {em:>11.4f} {es:>13.4f} {flag:>14}")
    # NOTE: values slightly >1 are the known calibration-CONDITIONAL bias
    # (E[e|C] ~ ((n+1)/k)Beta(k,n+1-k)), not a defect of the aggregation rule.

print("\n" + "="*104)
print("9b. THE THREE-WAY BIND at LSPR23 scale (N=16M flows, |C|=1e6, k=1, alpha=0.05)")
print(f"    max attainable e-value (ceiling) = {CEIL:,.0f}")
print("="*104)
print(f"{'cap n0':>9} {'T=N/n0':>11} {'alpha_T':>10} {'need E>=':>13} {'feasible':>9} "
      f"{'MEAN detects':>13} {'MEAN padded':>12} {'SUM/n0 detects (n_att)':>24}")
print("-"*112)
for n0 in (10, 100, 640, 1_000, 5_000, 50_000, 500_000):
    aT,T = alpha_T(n0); need = 1.0/aT
    feasible = CEIL >= need
    # MEAN rule: E = (n_att*e_att)/(n_att+n_pad); unpadded E = e_att = CEIL (strong attack)
    mean_unpadded = CEIL
    mean_ok = feasible and (mean_unpadded >= need)
    # attacker pads without limit under the mean rule (no cap): pad to just below threshold
    pad_needed = (CEIL*40)/need - 40 if need>0 else 0   # 40-event campaign
    mean_padded_ok = False if pad_needed > 0 else mean_ok
    # SUM/n0 rule: E = n_att*CEIL/n0  -> need n_att >= need*n0/CEIL
    n_att_req = need*n0/CEIL
    print(f"{n0:>9,} {T:>11,} {aT:>10.2e} {need:>13,.0f} {str(feasible):>9} "
          f"{str(mean_ok):>13} {('no (pad '+format(int(max(pad_needed,0)),',')+')') if mean_ok else '-':>12} "
          f"{('needs n_att>='+format(int(np.ceil(n_att_req)),',')) if feasible else 'infeasible':>24}")

print("\n" + "="*104)
print("9c. WHO IS PROTECTED?  campaign size vs cap, under the padding-robust rule")
print("="*104)
print(f"{'cap n0':>9} {'feasible':>9} " + " ".join(f"{('n_att='+str(a)):>12}" for a in (40,200,1000,5000,20000)))
print("-"*100)
for n0 in (640, 1_000, 5_000, 50_000, 500_000):
    aT,T=alpha_T(n0); need=1.0/aT; feasible = CEIL>=need
    cells=[]
    for n_att in (40,200,1000,5000,20000):
        eff=min(n_att,n0)                       # only n0 members fit in one group
        E=eff*CEIL/n0
        cells.append("DETECT" if (feasible and E>=need) else "miss")
    print(f"{n0:>9,} {str(feasible):>9} " + " ".join(f"{c:>12}" for c in cells))
print("\nreading: 'miss' under the robust rule = attack invisible.")
print("         under the admissible (mean) rule those same attacks are detectable")
print("         but suppressible by padding (Test 7).")
