"""
AUTHORITATIVE NUMBERS for the paper. Every figure here has survived two independent
blind reviews (Opus + codex). Anything they corrected is stated in its corrected form.
"""
import numpy as np
from t1_silence import gamma_poly, first_rejection_deadline, drought_tolerance, absorbing_delta

A,W0 = 0.05, 0.025
print("="*96)
print("1. FEASIBILITY  (corrected: three distinct quantities, previously conflated)")
print("="*96)
H=10**7; gam=gamma_poly(H)
for nc in (10**4,10**6):
    f=1.0/(nc+1)
    print(f"  |C|={nc:>10,}  floor={f:.2e}   first-rejection deadline={first_rejection_deadline(gam,f,W0):>7,}"
          f"   drought|D=1000={drought_tolerance(gam,f,A,W0,1000):>9,}"
          f"   absorbing Delta*={absorbing_delta(gam,f,A,W0):>10,}")
print("\n  STATEMENT: LORD++ must make its FIRST rejection within 18 (|C|=1e4) / 334 (|C|=1e6)")
print("  hypotheses or it is permanently silent. At prevalence 1e-4 the first attack arrives")
print("  around event 10,000 -- the deadline is missed before any attack appears.")

print("\n" + "="*96)
print("2. SCALE  (corrected: exact bound is n >= T/w0 - 1; uniform gamma is MAX-MIN optimal,")
print("   i.e. optimal for 'able to reject at every t<=T', not for 'ever rejects anything')")
print("="*96)
for name,T in [("LSPR23 event-level",16_000_000),("1 hr @ 10k flows/s",36_000_000),
               ("LSPR23 incident-level (288)",288)]:
    print(f"  {name:>30}  T={T:>12,}  n_min = T/w0 - 1 = {T/W0-1:>16,.0f}")

print("\n" + "="*96)
print("3. CONDITIONAL VALIDITY  (corrected: NOT 'guarantee void'. Marginal validity holds,")
print("   so FDR is controlled; what fails is CONDITIONAL coverage.)")
print("="*96)
print("   Exact law:  E[e|C] ~ ((n+1)/k) * Beta(k, n+1-k)")
for nc in (10**4,10**6):
    p_exact=(nc/(nc+1.0))**nc
    print(f"   k=1, |C|={nc:>10,}:  P(E[e|C]>1) = (n/(n+1))^n = {p_exact:.4f}   (1/e = {1/np.e:.4f})")
print("   -> independent of |C|. More calibration data does NOT help; the fix is Bates et al.")
print("      calibration-conditional p-values.")

print("\n" + "="*96)
print("4. DILUTION  (corrected: attack drawn once; floor not ceil; numerator is not zero --")
print("   padded statistic tends to ~1, not 0, so the claim holds for thresholds > 1)")
print("="*96)
NCAL=1_000_000; CEIL=NCAL+1.0; THR=46_665
cal_max=4.753   # Phi^{-1}(1-1/(NCAL+1))
print(f"  {'mu':>5} {'P(attack event exceeds cal max)':>32} {'E[hits]/40':>12} {'median pad to suppress':>24}")
from scipy.stats import norm
for mu in (3.,4.,5.,6.):
    ph=1-norm.cdf(cal_max-mu); H_=40*ph
    pads=[]
    for r in range(400):
        h=np.random.default_rng(2000+r).binomial(40,ph)
        pm=h*CEIL/THR-40
        pads.append(int(np.floor(pm))+1 if pm>0 else 0)
    print(f"  {mu:>5.1f} {ph:>32.4f} {H_:>12.2f} {int(np.median(pads)):>24,}")
print("  -> 3-18x the attack's own event count. Both reviewers independently reproduced")
print("     medians of ~130-155 (mu=4), ~450-475 (mu=5), ~700-730 (mu=6).")

print("\n" + "="*96)
print("5. DETECTION FLOOR under the padding-robust rule (grouping-independent)")
print("="*96)
N=16_000_000
for k in (1,):
    for ncal in (10**6,10**7,10**8):
        floor_att = N*k/(W0*(ncal+1))
        print(f"  |C|={ncal:>12,}  k={k}  ->  min detectable campaign = {floor_att:>10,.0f} events")
print("  -> n_att_min = N*k / (w0*(|C|+1)); the group-size cap CANCELS.")
print("  -> protecting a 40-event campaign at LSPR23 scale needs |C| ~ 1.6e7.")

print("\n" + "="*96)
print("6. RETRACTED / CORRECTED")
print("="*96)
for line in [
 "top10mean is NOT a valid e-merger (data-dependent selection); E[.]=0.5,1,10,1000 at N=50,100,1e3,1e5.",
 "Trilemma does NOT follow from Vovk-Wang Thm 3.2 alone (Thm 3.2 fixes arity; padding changes it).",
 "  It IS provable via essential domination F_m(x) <= max(1, mean(x)), or directly with",
 "  negatively-dependent e-values. Requires a threshold quantifier tau>1, else F==1 is a counterexample.",
 "Escape from the trilemma is DROPPING SYMMETRY (pre-committed slots), not sum/n0.",
 "sum/n0 is a valid e-merger only for N <= n0; for N > n0 it is invalid.",
 "Attribution: Vovk & Wang 2021 Thm 3.2 = symmetric result. Wang 2025 Biometrika Thm 1 = asymmetric.",
 "'any summable gamma' holds as an ABSORBING-STATE statement via S(Delta), not pointwise in t.",
]: print("  - "+line)
