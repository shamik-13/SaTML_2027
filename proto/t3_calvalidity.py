"""
TEST 3: is the e-value valid CONDITIONALLY on the one calibration set you deploy?
E[e | cal] = (n+1)/k * (1 - F(cal_{(n+1-k)}))   -- computed EXACTLY (F=Phi known),
so zero Monte Carlo error.  Dependence is irrelevant here: E[mean e]=E[e] by linearity.
"""
import numpy as np
from scipy.stats import norm

print("="*100)
print("3. CALIBRATION-CONDITIONAL validity of the conformal e-value")
print("   marginal guarantee is E[e]=1 (EXACTLY only for continuous scores / no ties;
   with ties and the '>=' convention it is conservative, E[e]<=1).")
print("   deployed reality: you get ONE calibration set. Distribution of E[e|cal]:")
print("="*100)
print(f"{'|C|':>10} {'k':>6} {'max e':>10} {'mean':>7} {'median':>7} {'P(>1)':>7} "
      f"{'p95':>7} {'p99':>7} {'worst/2000':>11}")
print("-"*100)
rng=np.random.default_rng(7); DRAWS=2000
for ncal in (10_000, 100_000, 1_000_000):
    # order statistics: we need cal_{(n+1-k)} = the k-th largest calibration value
    for k in (1,10,100,1000):
        vals=np.empty(DRAWS)
        for d in range(DRAWS):
            # tail prob of k-th largest of n std normals ~ Beta(k, n+1-k) in U-space
            u = rng.beta(k, ncal+1-k)      # 1-F(k-th largest)  exactly
            vals[d] = (ncal+1.0)/k * u
        print(f"{ncal:>10,} {k:>6} {(ncal+1)/k:>10,.0f} {vals.mean():>7.3f} "
              f"{np.median(vals):>7.3f} {(vals>1).mean():>7.3f} "
              f"{np.percentile(vals,95):>7.3f} {np.percentile(vals,99):>7.3f} {vals.max():>11.3f}")
    print()
print("READ: 'P(>1)' = probability your deployed calibration set makes the e-value")
print("      ANTI-conservative. NOTE: this is NOT an invalid procedure -- C is part of")
print("      the probability space, so MARGINAL validity (what e-BH/LORD++ require) holds")
print("      and FDR is controlled. What fails is CONDITIONAL coverage: realised FDP")
print("      tends to a C-dependent limit exceeding alpha with the probability shown.")
print("      Exact law: E[e|C] ~ ((n+1)/k)*Beta(k, n+1-k).")
print("      For k=1, P(E[e|C]>1) = (n/(n+1))^n -> 1/e = 0.3679, independent of n.")
print("      Small k = high evidence ceiling = what Test 1 says you NEED = least reliable.")
