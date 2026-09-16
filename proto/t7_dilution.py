"""
TEST 7: DILUTION ATTACK on incident-level e-value aggregation.
The v2 plan proposed E_j = mean of within-incident conformal e-values, because the mean of
e-values is valid under ARBITRARY dependence (linearity of expectation).
But the attacker controls how many events their campaign emits -- i.e. the DENOMINATOR.
Question: can an attacker suppress detection of their own campaign purely by padding it
with extra benign-looking traffic, without changing the attack itself?
"""
import numpy as np
from t1_silence import gamma_poly, LORDpp

NCAL = 1_000_000
def make_cal(rng): return np.sort(rng.normal(0,1,NCAL))
def e_thr(cal, s, k):
    n=len(cal); K = 1 + (n - np.searchsorted(cal, s, side='left'))
    return np.where(K<=k, (n+1.0)/k, 0.0)

def agg(cal, x, k, rule, n0=None):
    e = e_thr(cal, x, k)
    if rule=="mean":      return e.mean()
    if rule=="sum/n0":    return e.sum()/n0                    # pre-committed denominator
    if rule=="top10mean":
        # RETRACTED: NOT a valid arbitrary-dependence e-merger. top-k selection is
        # data-dependent so linearity does not apply; E[.] = 0.5,1.0,10,1000 at
        # N=50,100,1000,100000. Also divided by 10 twice in the original. Kept only
        # to document the error; never use as a defence.
        return np.sort(e)[-10:].mean()
    raise ValueError(rule)

print("="*100)
print("7a. DILUTION: fixed attack (40 malicious events, mu=4), attacker pads with benign traffic")
print(f"    |C|={NCAL:,}  k=1  ->  e ceiling = {NCAL+1:,}")
print("    incident-level LORD++ at T=288 hypotheses, alpha=0.05  ->  need E_j >= 1/alpha_t")
print("="*100)
rng=np.random.default_rng(11); cal=make_cal(rng)
gam=gamma_poly(300); proc=LORDpp(gam,alpha=0.05)
thresh = 1.0/proc.level(50)     # representative mid-stream requirement
print(f"    representative rejection requirement at t=50:  E_j >= {thresh:,.0f}\n")
print(f"{'pad events':>11} {'group size':>11} {'mean-e':>14} {'reject?':>8} {'sum/n0':>14} {'reject?':>8} {'top10':>12} {'reject?':>8}")
print("-"*100)
N_ATT=40; N0=200
att = rng.normal(4.0,1.0,N_ATT)          # FIXED: draw the attack ONCE, outside the loop
for pad in (0, 40, 200, 1_000, 10_000, 100_000):
    ben = rng.normal(0.0,1.0,pad)
    x = np.concatenate([att,ben])
    m  = agg(cal,x,1,"mean")
    s  = agg(cal,x,1,"sum/n0",n0=N0)
    t10= agg(cal,x,1,"top10mean")
    print(f"{pad:>11,} {len(x):>11,} {m:>14,.1f} {'YES' if m>=thresh else 'no':>8} "
          f"{s:>14,.1f} {'YES' if s>=thresh else 'no':>8} {t10:>12,.1f} {'YES' if t10>=thresh else 'no':>8}")

print("\n" + "="*100)
print("7b. INFLATION: can the attacker force a FALSE discovery on a PURELY BENIGN group")
print("    by padding it (the mirror attack on sum-based rules)?  n0 pre-committed = 200")
print("="*100)
print(f"{'benign events':>14} {'mean-e':>12} {'false rej?':>11} {'sum/n0':>12} {'false rej?':>11}")
print("-"*66)
for nb in (10, 200, 1_000, 10_000, 100_000):
    x = rng.normal(0.0,1.0,nb)
    m = agg(cal,x,1,"mean"); s = agg(cal,x,1,"sum/n0",n0=N0)
    print(f"{nb:>14,} {m:>12,.2f} {'YES' if m>=thresh else 'no':>11} "
          f"{s:>12,.2f} {'YES' if s>=thresh else 'no':>11}")

print("\n" + "="*100)
print("7c. ATTACKER COST: padding needed to suppress, as a function of attack strength")
print("="*100)
print(f"{'mu':>5} {'#att events':>12} {'pad to suppress (mean rule)':>29} {'pad / attack ratio':>20}")
print("-"*70)
for mu in (3.0,4.0,5.0,6.0):
    for natt in (40,):
        # FIXED: report the DISTRIBUTION over draws, not a single draw
        reps=[]
        for r in range(400):
            a=np.random.default_rng(1000+r).normal(mu,1.0,natt)
            reps.append(e_thr(cal,a,1).sum())
        e_att=float(np.median(reps))
        # mean rule: reject iff e_att/(natt+pad) >= thresh  =>  pad <= e_att/thresh - natt
        pad_max = e_att/thresh - natt
        need = int(np.floor(pad_max))+1 if pad_max>0 else 0   # FIXED: floor, not ceil
        print(f"{mu:>5.1f} {natt:>12,} {need:>29,} {need/natt if natt else 0:>20,.1f}x")
