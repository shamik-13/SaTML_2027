"""
TEST 8 (REBUILT after blind review). Original version was confounded:
  - gamma was renormalised inside the G loop, so cross-G comparison was invalid
  - printed "mean-e per grp" was the LAST group's value leaking from the loop
  - "threshold at T=G" was actually the j=1 threshold
  - and the premise was weak: for a pure-attack group, mean-e ~ P(hit)*(n+1) is
    INDEPENDENT of group size, so splitting cannot reduce per-group evidence at all.
This version separates the two effects explicitly.
"""
import numpy as np
from t1_silence import gamma_poly, LORDpp

NCAL=1_000_000; K=1; ALPHA=0.05; W0=ALPHA/2
CEIL=(NCAL+1.0)/K
rng=np.random.default_rng(21); cal=np.sort(rng.normal(0,1,NCAL))
def e_thr(cal,s,k):
    n=len(cal); Kr=1+(n-np.searchsorted(cal,s,side='left'))
    return np.where(Kr<=k,(n+1.0)/k,0.0)

print("="*100)
print("8a. Is per-group evidence reduced by splitting?  (the original premise)")
print("    400 malicious events at mu=4, split across G groups. 200 replicates each.")
print("="*100)
print(f"{'G':>5} {'events/grp':>11} {'median mean-e':>15} {'p10':>13} {'p90':>13}")
print("-"*62)
for G in (1,2,5,20,100,400):
    per=400//G
    vals=[e_thr(cal,rng.normal(4.0,1.0,per),K).mean() for _ in range(200)]
    v=np.array(vals)
    print(f"{G:>5} {per:>11} {np.median(v):>15,.0f} {np.percentile(v,10):>13,.0f} "
          f"{np.percentile(v,90):>13,.0f}")
print("\n  -> per-group evidence is FLAT in group size (it is ~P(hit)*(n+1)); only the")
print("     variance grows as groups shrink. Splitting does NOT dilute evidence.")

print("\n" + "="*100)
print("8b. The only real effect of splitting: a LONGER hypothesis stream.")
print("    Common gamma horizon (10,000) for ALL G so the comparison is valid.")
print("="*100)
GAM=gamma_poly(10_000)          # FIXED: one common horizon
print(f"{'G':>5} {'thr at j=1':>13} {'thr at j=G':>15} {'ceiling':>12} {'can reject at j=G?':>20}")
print("-"*72)
for G in (1,2,5,20,100,400,2000):
    p=LORDpp(GAM,alpha=ALPHA)
    t1=1.0/p.level(1); tG=1.0/p.level(min(G,len(GAM)))
    print(f"{G:>5} {t1:>13,.0f} {tG:>15,.0f} {CEIL:>12,.0f} {str(CEIL>=tG):>20}")

print("\n" + "="*100)
print("8c. Net effect on the attacker: does splitting help them?  (end-to-end)")
print("    Common gamma horizon; 400 malicious events at mu=4 spread over G groups in a")
print("    stream of G groups; count how many groups get rejected.")
print("="*100)
print(f"{'G':>5} {'groups rejected':>17} {'attacker outcome':>20}")
print("-"*46)
for G in (1,2,5,20,100,400):
    per=400//G; p=LORDpp(GAM,alpha=ALPHA); rej=0
    for j in range(1,G+1):
        E=e_thr(cal,rng.normal(4.0,1.0,per),K).mean()
        a=p.level(j)
        if a>0 and CEIL>=1.0/a and E>=1.0/a: rej+=1; p.record(j)
    print(f"{G:>5} {rej:>17} {('WORSE for attacker' if rej>=1 else 'evades'):>20}")
print("\n  CONCLUSION: splitting is a poor attack. Evidence per group does not fall, and")
print("  more groups means more rejection opportunities and more earned wealth.")
print("  The effective attack is DILUTION WITHIN a group (t7), not fragmentation.")
