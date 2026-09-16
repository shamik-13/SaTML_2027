"""
T4 -- formalisation of padding-robustness, with numerical checks of each step.

Route A (essential domination). Vovk & Wang Prop 3.1: M_K essentially dominates any
symmetric e-merging function, i.e. M_K >= F wherever F > 1. Hence for every symmetric
e-merging function of arity N,
        F_N(x) <= max(1, mean(x)).                                            (1)
Padding x in [0,inf)^m with r zeros drives mean(x,0^r) = (sum x)/(m+r) -> 0, so
        F_{m+r}(x, 0^r) <= max(1, (sum x)/(m+r)),                             (2)
and for any tau > 1 the right-hand side falls below tau once
        r > (sum x)/tau - m.                                                  (3)

Route B (direct, no domination result needed). For a uniformly random size-m subset S of
[N], set e_i = (N/m)*1{i in S}. Then E[e_i] = 1 so each is an e-variable, and they are
perfectly negatively dependent. Symmetry makes F_N(e) a deterministic constant, and an
e-variable that is constant is <= 1, giving
        F_N((N/m)*1_m, 0^{N-m}) <= 1  for all N >= m.                         (4)
"""
import numpy as np, json

print("="*100)
print("CHECK 1 -- route B: is e_i = (N/m)*1{i in S} a valid e-variable?")
print("="*100)
rng=np.random.default_rng(0)
for N,m in [(10,3),(100,5),(1000,40)]:
    E=[]
    for _ in range(200_000):
        S=rng.choice(N,m,replace=False)
        v=np.zeros(N); v[S]=N/m
        E.append(v[0])                      # marginal of a single coordinate
    se=np.std(E,ddof=1)/np.sqrt(len(E))
    print(f"  N={N:>5} m={m:>4}: E[e_1] = {np.mean(E):.4f} +- {se:.4f} (SE); exact value is 1")
print("  -> valid; and the vector is a permutation of ((N/m)*1_m, 0^(N-m)), so a symmetric")
print("     F_N maps every realisation to the SAME constant, which must therefore be <= 1.")

print("\n" + "="*100)
print("CHECK 2 -- the bound (3) reproduces the measured dilution costs exactly")
print("="*100)
from pathlib import Path
res=json.load(open(Path(__file__).resolve().parent/"out"/"t17_T2.json"))
print(f"  {'pos':>5} {'seed':>5} {'BH':>3} {'threshold tau':>15} {'measured median pad':>21}")
print("  "+"-"*54)
for r in res:
    if r["BH"]==2 and r["med_pad"] is not None:
        print(f"  {r['pos']:>5} {r['seed']:>5} {r['BH']:>3} {r['thr']:>15,.0f} {r['med_pad']:>21.1f}")
print("  NOTE: this is a consistency check, not independent evidence -- t17 computes")
print("  max(0, floor(sum_e/tau - n) + 1), which IS formula (3).")
print("  So the measured costs are the theorem's bound evaluated on real episodes.")

print("\n" + "="*100)
print("CHECK 3 -- is (1) tight? compare candidate symmetric rules against max(1, mean)")
print("="*100)
def mean_rule(x): return x.mean()
def convex(x,lam=0.3): return lam + (1-lam)*x.mean()      # admissible per VW Thm 3.2
def sum_n0(x,n0): return x.sum()/n0                        # valid only while len(x) <= n0
print(f"  {'rule':>28} {'x=(1e6,0,...,0), m=40':>24} {'max(1,mean)':>13} {'<= bound?':>10}")
x=np.zeros(40); x[0]=1e6
for nm,f in [("arithmetic mean",mean_rule),("0.3 + 0.7*mean",convex),
             ("sum/n0 (n0=40)",lambda v: sum_n0(v,40)),("sum/n0 (n0=200)",lambda v: sum_n0(v,200))]:
    v=f(x); b=max(1.0,x.mean())
    print(f"  {nm:>28} {v:>24,.1f} {b:>13,.1f} {str(v<=b+1e-9):>10}")
print("  (sum/n0 with n0 > m is dominated by the mean -- valid but inadmissible, which is")
print("   exactly the price of padding-robustness within a committed cap.)")

print("\n" + "="*100)
print("CHECK 4 -- the asymmetric escape, and why tau > 1 is required")
print("="*100)
print("  pre-committed slot F_N(e) = e_1 :")
for r in (0,10,1000,100000):
    x=np.concatenate([[1e6],np.zeros(r)])
    print(f"    padded with {r:>7,} zeros -> F = {x[0]:>12,.0f}   (invariant)")
print("  constant rule F == 1 : symmetric, valid, padding-invariant -- but it can never")
print("  reject, since rejection needs evidence >= 1/alpha_t > 1. Hence tau > 1 in the")
print("  definition is exactly the requirement that the rule can fire at all.")
