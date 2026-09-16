"""
TEST 1 - Proposition 1: structural silence.
Does the conformal p-value floor 1/(|C|+1) collide with alpha-wealth decay
so that online FDR procedures become UNABLE to reject any input?

Implements LORD++ and LOND exactly. Pure simulation, no data needed.
"""
import numpy as np, math, json
from collections import deque

# ---------- gamma sequences (must be nonneg, sum to 1) ----------
def gamma_poly(n, expo=1.6):
    j = np.arange(1, n+1, dtype=float)
    g = j**(-expo)
    return g / np.sum(j**(-expo))   # normalise over horizon (standard practice)

def gamma_jm(n):
    # Javanmard-Montanari style: log(max(j,2)) / (j * exp(sqrt(log j)))
    j = np.arange(1, n+1, dtype=float)
    lj = np.log(np.maximum(j, 2.0))
    g = lj / (j * np.exp(np.sqrt(np.log(np.maximum(j, 2.0)))))
    return g / g.sum()

# ---------- analytic: correct feasibility quantities ----------
# CORRECTED after blind review. The previous `max_drought` computed
# max{t : gamma_t*w0 >= floor} but was LABELLED as drought tolerance. Those differ by
# up to 4 orders of magnitude. The three distinct quantities are separated below.
# NOTE: gamma here is normalised over a finite horizon, so these numbers characterise
# THIS gamma family, not "all summable gamma" (see absorbing_delta for the general bound).

def first_rejection_deadline(gam, floor, w0):
    """Before ANY rejection, alpha_t = gamma_t*w0. Largest t at which that still clears
    the evidence floor => the procedure must make its FIRST rejection by then or it is
    permanently silent."""
    ok = np.nonzero(gam*w0 >= floor)[0]
    return (ok[-1]+1) if len(ok) else 0

def drought_tolerance(gam, floor, alpha, w0, D):
    """Longest rejection-free run survivable given D prior rejections, in the most
    FAVOURABLE arrangement (all D immediately before the drought). Then
    alpha_t ~ gamma_Delta * (alpha - w0 + alpha*(D-1))."""
    if D <= 0: return first_rejection_deadline(gam, floor, w0)
    coef = (alpha - w0) + alpha*max(D-1, 0)
    ok = np.nonzero(gam*coef >= floor)[0]
    return (ok[-1]+1) if len(ok) else 0

def absorbing_delta(gam, floor, alpha, w0):
    """General bound valid for ANY nonnegative summable gamma, monotone or not.
    With S(D) = sum_{d>=D} gamma_d, during a rejection-free run of length Delta every
    index t-tau_j is distinct and >= Delta, and gamma_t <= S(t) <= S(Delta), so
        alpha_t <= (w0 + alpha) * S(Delta),
    which is non-increasing in Delta. Delta* = min{Delta : (w0+alpha)S(Delta) < floor}
    is finite and the state is ABSORBING once reached (Delta only grows)."""
    S = np.cumsum(gam[::-1])[::-1]           # S[i] = sum_{d>=i+1} gamma_d
    bad = np.nonzero((w0+alpha)*S < floor)[0]
    return (bad[0]+1) if len(bad) else None

def report_drought_table():
    print("="*100)
    print("A. FEASIBILITY QUANTITIES (LORD++, alpha=0.05, w0=alpha/2).  Three DISTINCT things:")
    print("   [1] first-rejection deadline : before any rejection alpha_t = gamma_t*w0, so the")
    print("       procedure must make its FIRST rejection within this many hypotheses or it is")
    print("       permanently silent.  <-- this is what the simulation in part B exhibits")
    print("   [2] drought tolerance | D    : longest rejection-free run survivable given D prior")
    print("       rejections, best-case arrangement")
    print("   [3] absorbing Delta*        : general bound, ANY summable gamma, provably absorbing")
    print("="*100)
    H = 10**7
    for name, gam in [("gamma ~ j^-1.6", gamma_poly(H)), ("gamma ~ JM", gamma_jm(H))]:
        print(f"\n  {name}")
        print(f"  {'|C|':>12} {'p-floor':>10} {'[1] 1st-rej':>13} {'[2] D=1':>10} "
              f"{'[2] D=1000':>12} {'[3] Delta*':>13}")
        for nc in [10**3, 10**4, 10**5, 10**6, 10**7]:
            floor = 1.0/(nc+1); alpha, w0 = 0.05, 0.025
            d1  = first_rejection_deadline(gam, floor, w0)
            t1_ = drought_tolerance(gam, floor, alpha, w0, 1)
            t2_ = drought_tolerance(gam, floor, alpha, w0, 1000)
            ad  = absorbing_delta(gam, floor, alpha, w0)
            print(f"  {nc:>12,} {floor:>10.2e} {d1:>13,} {t1_:>10,} {t2_:>12,} "
                  f"{(f'{ad:,}' if ad else '>1e7'):>13}")
    print()

# ---------- exact online procedures ----------
class LORDpp:
    """Ramdas et al. LORD++:
       alpha_t = gamma_t*w0 + (alpha-w0)*gamma_{t-tau_1} + alpha*sum_{j>=2} gamma_{t-tau_j}"""
    name = "LORD++"
    def __init__(self, gam, alpha=0.05, w0=None, trunc=200000):
        self.gam, self.alpha = gam, alpha
        self.w0 = alpha/2 if w0 is None else w0
        self.rej = deque(); self.first = None; self.trunc = trunc
    def level(self, t):                      # t is 1-indexed
        g = self.gam
        a = g[t-1]*self.w0
        if self.first is not None:
            d = t - self.first
            if 1 <= d <= self.trunc: a += (self.alpha - self.w0)*g[d-1]
        for tau in self.rej:
            d = t - tau
            if 1 <= d <= self.trunc: a += self.alpha*g[d-1]
        return a
    def record(self, t):
        if self.first is None: self.first = t
        else:
            self.rej.append(t)
            while self.rej and (self.rej[0] < t - self.trunc): self.rej.popleft()

class LOND:
    """alpha_t = alpha * gamma_t * (1 + D_{t-1})"""
    name = "LOND"
    def __init__(self, gam, alpha=0.05):
        self.gam, self.alpha, self.D = gam, alpha, 0
    def level(self, t): return self.alpha*self.gam[t-1]*(1+self.D)
    def record(self, t): self.D += 1

# ---------- stream simulation ----------
def run(proc_cls, gam, T, pi, mu, ncal, alpha=0.05, seed=0, agg=1):
    """agg = events per hypothesis (1 = event-level; >1 = incident-level aggregation
       via mean-of-e-values, converted back to a p-value-like test)"""
    rng = np.random.default_rng(seed)
    cal = np.sort(rng.normal(0, 1, ncal))              # benign calibration scores
    n_att = max(1, int(round(T*pi)))
    is_att = np.zeros(T, bool)
    is_att[rng.choice(T, n_att, replace=False)] = True
    s = rng.normal(0, 1, T); s[is_att] = rng.normal(mu, 1, n_att)
    # conformal p-values: p = (1 + #{cal >= s}) / (ncal+1)
    ge = ncal - np.searchsorted(cal, s, side='left')
    p = (1.0 + ge)/(ncal+1.0)
    floor = 1.0/(ncal+1.0)
    proc = proc_cls(gam, alpha=alpha)
    R = V = 0; silent = 0; first_silent = None
    for t in range(1, T+1):
        a = proc.level(t)
        if a < floor:
            silent += 1
            if first_silent is None: first_silent = t
            continue                                    # cannot possibly reject
        if p[t-1] <= a:
            R += 1
            if not is_att[t-1]: V += 1
            proc.record(t)
    return dict(proc=proc.name, T=T, pi=pi, mu=mu, ncal=ncal,
                n_attacks=int(n_att), R=R, V=V,
                FDP=(V/R if R else float('nan')),
                recall=(R-V)/n_att,
                silence_rate=silent/T,
                first_silent_at=first_silent)

if __name__ == "__main__":
    report_drought_table()
    print("="*78)
    print("B. SIMULATION: event-level online FDR on a sparse stream")
    print("   NOTE: 'first silent' below is the FIRST-REJECTION DEADLINE being hit,")
    print("   not a drought bound -- these runs never achieve a first rejection.")
    print("   benign ~ N(0,1), attack ~ N(mu,1), alpha=0.05, gamma ~ j^-1.6")
    print("="*78)
    T = 500_000
    gam = gamma_poly(T+10)
    rows = []
    hdr = f"{'proc':>7} {'pi':>8} {'mu':>4} {'|C|':>9} {'#att':>6} {'R':>6} {'FDP':>7} {'recall':>7} {'silent%':>8} {'1st silent':>11}"
    print(hdr); print("-"*len(hdr))
    for proc in (LORDpp, LOND):
        for pi in (1e-4, 1e-3, 1e-2):
            for ncal in (10_000, 1_000_000):
                r = run(proc, gam, T, pi, 5.0, ncal, seed=1)
                rows.append(r)
                fs = r['first_silent_at']
                print(f"{r['proc']:>7} {pi:>8.0e} {r['mu']:>4.0f} {ncal:>9,} {r['n_attacks']:>6} "
                      f"{r['R']:>6} {r['FDP'] if r['R'] else float('nan'):>7.3f} {r['recall']:>7.3f} "
                      f"{100*r['silence_rate']:>7.1f}% {(f'{fs:,}' if fs else '-'):>11}")
    json.dump(rows, open("out/t1_silence.json","w"), indent=1)
    print("\nwrote out/t1_silence.json")
