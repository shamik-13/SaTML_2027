"""
TEST 6: is the silence result an artefact of the gamma sequence?
A practitioner who knows the horizon T can use UNIFORM gamma_j = 1/T (valid: sum=1),
giving a CONSTANT test level alpha_t = w0/T.  That is the best possible case.
Does event-level survive under the BEST valid gamma?
"""
import numpy as np
alpha, w0 = 0.05, 0.025
print("="*104)
print("Minimum calibration-set size needed to be ABLE to reject, under the BEST-CASE")
print("valid gamma (uniform over a known horizon T):  alpha_t = w0/T,  need |C| >= T/w0 - 1")
print("NOTE: uniform gamma is max-min optimal -- it maximises min_{t<=T} alpha_t, i.e. it is")
print("      optimal for 'able to reject at EVERY t <= T', not for 'ever rejects anything'.")
print("="*104)
print(f"{'scenario':>34} {'T (hypotheses)':>16} {'alpha_t':>11} {'min |C| (k=1)':>18} {'feasible?':>11}")
print("-"*104)
def row(name,T):
    a=w0/T; need=1.0/a - 1.0          # exact: n+1 >= 1/alpha_t
    feas = "yes" if need<=5e7 else ("borderline" if need<=5e8 else "NO")
    print(f"{name:>34} {T:>16,} {a:>11.2e} {need:>18,.0f} {feas:>11}")
row("LSPR23 event-level",          16_000_000)
row("LSPR23 incident-level (288)",        288)
row("CIC-IDS2018 event-level (~18M)", 18_000_000)
row("1 day @ 10k flows/s",          864_000_000)
row("1 hour @ 10k flows/s",          36_000_000)
row("AIT wilson event-level",           417_672)
row("incident-level, 5k incidents",       5_000)
row("incident-level, 50k incidents",     50_000)
print()
print("="*104)
print("Comparison of gamma choices at the two operating points (min |C| needed, k=1)")
print("="*104)
def poly_need(T,expo=1.6):
    j=np.arange(1,T+1,dtype=float); g=(T**-expo)/np.sum(j**-expo)
    return 1.0/(g*w0) - 1.0
print(f"{'':>26} {'uniform 1/T':>16} {'gamma ~ j^-1.6':>20}")
for name,T in [("event-level (16M)",16_000_000),("incident-level (288)",288),
               ("incident-level (5k)",5_000)]:
    print(f"{name:>26} {1.0/(w0/T)-1.0:>16,.0f} {poly_need(T):>20,.0f}")
print()
print("VERDICT: even under the most favourable valid gamma, event-level online control")
print("         needs ~10^8-10^9 benign calibration flows. Incident-level needs ~10^4-10^6.")
