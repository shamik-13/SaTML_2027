"""
Online multiple-testing procedures for H6, isolated from any data loading so they can be
unit-tested (see t21b_h6_selftest.py).

Every procedure takes a Ctx and returns (rejections, true_positives, silent_count,
first_infeasible_t).  "silent" counts times t at which no rejection is possible even if
the evidence took its ceiling value -- the section 4.13 feasibility condition.

Sources, verbatim:
  SAFFRON     Ramdas, Zrnic, Wainwright, Jordan, ICML 2018, arXiv 1802.09098, section 2.3
  ADDIS*      Tian & Ramdas, NeurIPS 2019, arXiv 1905.11465, Algorithm 1
  online e-BH Fischer, Xu & Ramdas, arXiv 2407.20683, section 2
  e-GAI       Zhang, Wei, Ren & Zou, ICML 2025, arXiv 2506.01452, Algorithms 1 and 2
"""
import numpy as np
from scipy.special import zeta


class Ctx:
    """Episode stream.  Ev = aggregated e-value per episode (arithmetic-mean rule,
    section 2.3).  Pv = min(1, 1/Ev), the Markov p-value of section 2.2."""

    def __init__(self, Ev, ismal, CEIL, alpha=0.05, w0=0.025):
        self.Ev = np.asarray(Ev, dtype=float)
        self.ismal = np.asarray(ismal, dtype=bool)
        self.T = len(self.Ev)
        self.CEIL = float(CEIL)
        self.A = float(alpha)
        self.W0 = float(w0)
        self.NMAL = int(self.ismal.sum())
        with np.errstate(divide='ignore'):
            self.Pv = np.where(self.Ev > 0,
                               np.minimum(1.0, 1.0 / np.maximum(self.Ev, 1e-300)), 1.0)

    def infeasible(self, lvl):
        """No rejection possible at level lvl even at the evidence ceiling.
        Written exactly as in t19_T5_T6.py so the section 4.17 rows reproduce."""
        return lvl <= 0 or self.CEIL < 1.0 / lvl


def make_gamma(kind, T):
    """gam1 is 1-indexed (LOND, LORD++, SAFFRON, online e-BH).
       gam0 is 0-indexed (ADDIS, whose paper specifies {gamma_j} from j = 0)."""
    if kind == "poly":                       # gamma_j prop j^-1.6, the section 4.17 choice
        z = float(zeta(1.6, 1))
        g1 = np.zeros(T + 2); g1[1:] = np.arange(1, T + 2, dtype=float) ** -1.6 / z
        g0 = (np.arange(0, T + 2, dtype=float) + 1.0) ** -1.6 / z
    elif kind == "uniform":                  # horizon-uniform, max-min optimal (section 4.5)
        g1 = np.zeros(T + 2); g1[1:T + 1] = 1.0 / T
        g0 = np.zeros(T + 2); g0[0:T] = 1.0 / T
    else:
        raise ValueError(kind)
    return g1, g0


# ----------------------------------------------------------------------------------
# Family I / II baselines (reproduce section 4.17)
# ----------------------------------------------------------------------------------
def run_lond(ctx, gam1, fired=None):
    """LOND / e-LOND: alpha_t = alpha * gamma_t * (R_{t-1} + 1).
    If `fired` is a boolean array of length T it is filled with the rejection mask."""
    R = rej = tp = silent = 0; first = None
    if fired is not None: fired[...] = False
    for t in range(1, ctx.T + 1):
        lvl = ctx.A * gam1[t] * (R + 1)
        if ctx.infeasible(lvl):
            silent += 1
            if first is None: first = t
            continue
        if ctx.Ev[t - 1] >= 1.0 / lvl:
            R += 1; rej += 1
            if fired is not None: fired[t - 1] = True
            if ctx.ismal[t - 1]: tp += 1
    return rej, tp, silent, first


def run_lordpp(ctx, gam1, fired=None):
    """LORD++: alpha_t = gamma_t w0 + (alpha-w0) gamma_{t-tau_1} + alpha sum_{j>=2} gamma_{t-tau_j}.
    If `fired` is a boolean array of length T it is filled with the rejection mask; it is a
    pure output and does not affect the computation."""
    rej = tp = silent = 0; first = None
    if fired is not None: fired[...] = False
    tau = np.empty(ctx.T + 1, dtype=np.int64); nt = 0
    for t in range(1, ctx.T + 1):
        lvl = gam1[t] * ctx.W0
        if nt >= 1 and t > tau[0]:
            lvl += (ctx.A - ctx.W0) * gam1[t - tau[0]]
        if nt >= 2:
            idx = t - tau[1:nt]
            idx = idx[idx >= 1]
            if idx.size: lvl += ctx.A * gam1[idx].sum()
        if ctx.infeasible(lvl):
            silent += 1
            if first is None: first = t
            continue
        if ctx.Ev[t - 1] >= 1.0 / lvl:
            rej += 1; tau[nt] = t; nt += 1
            if fired is not None: fired[t - 1] = True
            if ctx.ismal[t - 1]: tp += 1
    return rej, tp, silent, first


# ----------------------------------------------------------------------------------
# SAFFRON and ADDIS
# ----------------------------------------------------------------------------------
def run_saffron(ctx, gam1, lam=0.5, fired=None):
    """SAFFRON, arXiv 1802.09098 section 2.3.

    alpha_1 = min{(1-lam) gamma_1 W0, lam}
    alpha_t = min{lam, (1-lam)[W0 g_{t-C0+} + (a-W0) g_{t-tau_1-C1+} + a sum_{j>=2} g_{t-tau_j-Cj+}]}

    The lag index t - tau_j - C_{j+}(t) is rewritten as D_t - B_j with
    D_t = t - cumC(t), B_j = tau_j - A_j, A_j = #{i <= tau_j : P_i <= lam},
    using C_{j+}(t) = cumC(t) - A_j.  This is an identity, not an approximation.
    """
    rej = tp = silent = 0; first = None
    if fired is not None: fired[...] = False
    B = np.empty(ctx.T + 1, dtype=np.int64); nt = 0
    cumC = 0                                        # #{i < t : P_i <= lam}
    for t in range(1, ctx.T + 1):
        D = t - cumC
        ah = ctx.W0 * gam1[min(D, ctx.T + 1)]
        if nt >= 1:
            i1 = D - B[0]
            if i1 >= 1: ah += (ctx.A - ctx.W0) * gam1[min(i1, ctx.T + 1)]
        if nt >= 2:
            idx = D - B[1:nt]
            idx = idx[idx >= 1]
            if idx.size: ah += ctx.A * gam1[np.minimum(idx, ctx.T + 1)].sum()
        lvl = min(lam, (1.0 - lam) * ah)
        cand = ctx.Pv[t - 1] <= lam
        if ctx.infeasible(lvl):
            silent += 1
            if first is None: first = t
        elif ctx.Pv[t - 1] <= lvl:
            rej += 1
            if fired is not None: fired[t - 1] = True
            A_j = cumC + (1 if cand else 0)         # #{i <= t : P_i <= lam}
            B[nt] = t - A_j; nt += 1
            if ctx.ismal[t - 1]: tp += 1
        if cand: cumC += 1
    return rej, tp, silent, first


def run_addis(ctx, gam0, lam=0.25, tau_=0.5, fired=None, levels=None):
    """ADDIS*, arXiv 1905.11465 Algorithm 1.

    alpha_t = min{lam, (tau-lam)[W0 g_{S^t-C0+} + (a-W0) g_{S^t-k*_1-C1+}
                                 + a sum_{j>=2} g_{S^t-k*_j-Cj+}]}

    Lag index S^t - kap*_j - C_{j+}(t) is rewritten as D_t - B_j with
    D_t = S^t - cumC(t), B_j = kap*_j - A_j.  Both S^t and cumC are counted over i < t.

    `fired` and `levels`, if given, are output arrays of length T: the rejection mask and
    the level alpha_t offered at each step.  Neither affects the computation; `levels` is
    what t32_B1_addis_state.py prices the padding attack against, so that it uses the
    procedure's own levels rather than a re-derivation of them.
    """
    rej = tp = silent = 0; first = None
    if fired is not None: fired[...] = False
    B = np.empty(ctx.T + 1, dtype=np.int64); nt = 0
    S = 0; cumC = 0
    for t in range(1, ctx.T + 1):
        D = S - cumC
        ah = ctx.W0 * gam0[min(D, ctx.T + 1)]
        if nt >= 1:
            i1 = D - B[0]
            if i1 >= 0: ah += (ctx.A - ctx.W0) * gam0[min(i1, ctx.T + 1)]
        if nt >= 2:
            idx = D - B[1:nt]
            idx = idx[idx >= 0]
            if idx.size: ah += ctx.A * gam0[np.minimum(idx, ctx.T + 1)].sum()
        lvl = min(lam, (tau_ - lam) * ah)
        if levels is not None: levels[t - 1] = lvl
        sel = ctx.Pv[t - 1] <= tau_
        cand = ctx.Pv[t - 1] <= lam
        if ctx.infeasible(lvl):
            silent += 1
            if first is None: first = t
        elif ctx.Pv[t - 1] <= lvl:
            rej += 1
            if fired is not None: fired[t - 1] = True
            A_j = cumC + (1 if cand else 0)
            kstar_j = S + (1 if sel else 0)
            B[nt] = kstar_j - A_j; nt += 1
            if ctx.ismal[t - 1]: tp += 1
        if sel: S += 1
        if cand: cumC += 1
    return rej, tp, silent, first


# ----------------------------------------------------------------------------------
# online e-BH
# ----------------------------------------------------------------------------------
def online_ebh_kstar(Ev, gam1, alpha, T):
    """Return (k*_t trajectory of length T+1, m array).

    m_j = 1/(alpha gamma_j E_j) is the smallest k at which hypothesis j clears its own
    bar E_j >= 1/(k alpha gamma_j).  Then
        k*_t = max{k <= t : m_(k) <= k}   over the first t values,
    which is the standard step-up fixed point.  Only finite m_j can ever satisfy
    m_(k) <= k, so infinite ones are never inserted -- they sort to the end and cannot
    affect any order statistic below the count of finite entries.
    """
    with np.errstate(divide='ignore'):
        denom = alpha * gam1[1:T + 1] * Ev
        m = np.where(denom > 0, 1.0 / np.where(denom > 0, denom, 1.0), np.inf)
    buf = np.empty(T + 1); nfin = 0
    ar = np.arange(1, T + 2, dtype=float)
    ks = np.zeros(T + 1, dtype=np.int64); kstar = 0
    for t in range(1, T + 1):
        v = m[t - 1]
        if np.isfinite(v):
            p = int(np.searchsorted(buf[:nfin], v))
            buf[p + 1:nfin + 1] = buf[p:nfin]; buf[p] = v; nfin += 1
            ok = np.nonzero(buf[:nfin] <= ar[:nfin])[0]
            kstar = int(ok[-1]) + 1 if ok.size else 0
        ks[t] = kstar
    return ks, m


def run_online_ebh(ctx, gam1):
    """online e-BH.  Returns (rej, tp, silent, first, k*_T, median lag, silent_arrival).

    Two feasibility notions, because online e-BH is an ARC procedure and the two differ:

      silent (the value returned in the third slot, i.e. the column compared against every
        other procedure) -- hypothesis i cannot be rejected AT ITS OWN ARRIVAL, because
        k*_i <= i forces CEIL < 1/(i alpha gamma_i).  This is the notion the
        immediate-decision procedures are scored on, so it is like-for-like.

      never_rejectable (returned last, reported separately) -- hypothesis i can never be
        rejected at ANY later time and for any realisation, because even the largest
        attainable k (k = T) leaves CEIL < 1/(k alpha gamma_i).  This is the analogue of
        the section 4.13 "is the infeasible state absorbing?" question, and it is weaker.

    The two differ only for ARC procedures.  Quoting never_rejectable in the silence column
    against the other procedures' at-arrival silence would compare unlike quantities, so
    the at-arrival figure is the one carried in the shared column.
    """
    T = ctx.T
    ks, m = online_ebh_kstar(ctx.Ev, gam1, ctx.A, T)
    kfin = int(ks[T])
    rejmask = np.isfinite(m) & (m <= kfin)
    rej = int(rejmask.sum()); tp = int((rejmask & ctx.ismal).sum())
    feas_ever = (ctx.CEIL * ctx.A * gam1[1:T + 1] * T) >= 1.0
    never_rejectable = int((~feas_ever).sum())
    arrivals = np.arange(1, T + 1, dtype=float)
    feas_arr = (ctx.CEIL * ctx.A * gam1[1:T + 1] * arrivals) >= 1.0
    silent = int((~feas_arr).sum())
    first = int(np.argmax(~feas_arr) + 1) if (~feas_arr).any() else None
    lag = None
    if rej:
        idx = np.nonzero(rejmask)[0]
        entry = np.searchsorted(ks, m[idx], side='left')   # first t with k*_t >= m_i
        entry = np.maximum(entry, idx + 1)
        lag = float(np.median(entry - (idx + 1)))
    return rej, tp, silent, first, kfin, lag, never_rejectable


# ----------------------------------------------------------------------------------
# e-GAI family
# ----------------------------------------------------------------------------------
def _rai_omega(w1, phi, psi, nacc, nrej):
    """eq (9): w_{t+1} = w1 [1 + sum_{j=1}^{t-R_t} phi^j - sum_{j=1}^{R_t} psi^j].

    The bracket is evaluated as a + (1 - b) rather than 1 + a - b.  Written the naive way,
    b = psi(1-psi^n)/(1-psi) rounds to exactly 1.0 once psi^n falls below machine epsilon
    (n >= 53 at psi = 0.5), so 1 - b cancels to 0 and the true value w1*psi^n is lost.
    The closed form 1 - b = (1 - 2 psi + psi^{n+1})/(1 - psi) has no cancellation.
    """
    a = phi * (1.0 - phi ** nacc) / (1.0 - phi) if nacc > 0 else 0.0
    if nrej > 0:
        one_minus_b = (1.0 - 2.0 * psi + psi ** (nrej + 1)) / (1.0 - psi)
    else:
        one_minus_b = 1.0
    w = w1 * (a + one_minus_b)
    if not (0.0 < w < 1.0):
        raise FloatingPointError(
            f"omega_t={w!r} outside (0,1) for w1={w1}, phi={phi}, psi={psi}, "
            f"nacc={nacc}, nrej={nrej}; see arXiv 2506.01452 Remark 3.3")
    return w


def run_egai(ctx, kind, w1, phi=0.5, psi=0.5, lam=0.1, d=0.99, omega_seq=None, fired=None):
    """e-LORD / e-SAFFRON / mem-e-LORD from arXiv 2506.01452.

    e-LORD      a_t = w_t (a - sum_{j<t} a_j/(R_{j-1}+1)) (R_{t-1}+1)
    e-SAFFRON   a_t = w_t (a(1-lam) - sum_{j<t} a_j 1{e_j < 1/lam}/(R_{j-1}+1)) (R_{t-1}+1)
    mem-e-LORD  same as e-LORD with R^d_t = sum_{j<=t} d^{t-j} delta_j in place of R_t

    omega_seq, if given, overrides the RAI update with a fixed sequence (used by the
    self-test to verify the paper's e-LORD == e-LOND equivalence).

    `fired`, if given, is a boolean output array of length T filled with the rejection mask.
    It is a pure output and does not affect the computation.
    """
    R = 0; Rd = 0.0; rej = tp = silent = 0; first = None
    if fired is not None: fired[...] = False
    budget = ctx.A * (1.0 - lam) if kind == "e-SAFFRON" else ctx.A
    cand_thr = (1.0 / lam) if lam > 0 else np.inf   # e_t >= 1/lam is a candidate
    spent = 0.0
    w = w1
    for t in range(1, ctx.T + 1):
        if omega_seq is not None:
            w = omega_seq[t - 1]
        den = (d * Rd + 1.0) if kind == "mem-e-LORD" else (R + 1.0)
        lvl = max(0.0, w * (budget - spent) * den)
        fired_t = False
        if ctx.infeasible(lvl):
            silent += 1
            if first is None: first = t
        elif ctx.Ev[t - 1] >= 1.0 / lvl:
            fired_t = True
        # the level offered at time t is charged to the budget whether or not it fired;
        # e-SAFFRON charges only non-candidates (e_t < 1/lam)
        if kind != "e-SAFFRON" or ctx.Ev[t - 1] < cand_thr:
            spent += lvl / den
        if fired_t:
            rej += 1
            if fired is not None: fired[t - 1] = True
            if ctx.ismal[t - 1]: tp += 1
            R += 1; Rd = d * Rd + 1.0
        else:
            Rd = d * Rd
        if omega_seq is None:
            w = _rai_omega(w1, phi, psi, t - R, R)
    return rej, tp, silent, first


def egai_implied_gamma(ctx, w1, phi=0.5, psi=0.5, nsteps=None):
    """The spending sequence e-LORD implies, gamma_t = w_t prod_{j<t}(1-w_j)
    (arXiv 2506.01452 section 3.2).  Returned for the rejection-free trajectory."""
    n = nsteps or ctx.T
    g = np.empty(n); prod = 1.0; w = w1
    for t in range(1, n + 1):
        g[t - 1] = w * prod
        prod *= (1.0 - w)
        w = _rai_omega(w1, phi, psi, t, 0)
    return g


# ----------------------------------------------------------------------------------
# Xu, Fischer & Ramdas, UAI 2026 (arXiv 2603.24792v3, 8 Jul 2026):
#   "Improving online FDR procedures via online analogs of e-closure and compound
#    e-values"
#
# All four procedures below control SupFDR under ARBITRARY dependence and each improves the
# baseline it is named after, so they are the strongest published members of the class C1
# covers.  They are implemented here to CLASSIFY them against thm:family1 / thm:family2, not
# because the paper proposes them.  Equation numbers are theirs.
#
# SCOPE OF "strictly improves".  Their Theorem 2 conditions closed e-LOND's strict improvement
# over e-LOND on a NONINCREASING gamma (source line 245); with an increasing gamma it can be
# strictly worse -- delta = 0.1, gamma = [0.1, 0.9], E = [0, 20] has e-LOND reject H_2 and
# closed e-LOND reject nothing.  Both sequences we run (gamma prop j^-1.6 and horizon-uniform)
# are nonincreasing, so the condition holds throughout, but it must be stated wherever the
# domination is claimed.
#
# One fact drives every implementation and is worth stating once: the step-up index r can
# never exceed the number of hypotheses carrying NONZERO evidence, because the bar
# E_i >= 1/(delta gamma_i r) is unsatisfiable at E_i = 0 for any finite r.  Under two-point
# conformal evidence at security prevalence that count is a small fraction of T, which is
# what makes the deferred-decision escape self-referential -- and what makes these
# procedures cheap to run at T = 57k.
# ----------------------------------------------------------------------------------


def _check_source_assumptions(ctx, gam1, name):
    """The UAI 2026 results, and both propositions we derive from them, hold under the source's
    standing assumptions.  Violating them does not degrade the bounds gracefully -- a gamma
    sequence with total mass above 1 breaks the donation cold-start bound outright -- so they are
    checked rather than assumed."""
    g = np.asarray(gam1)[1:ctx.T + 1]
    if not np.all(np.isfinite(g)) or np.any(g < 0.0):
        raise ValueError(f"{name}: gamma must be finite and nonnegative")
    tot = float(np.sum(g))
    if tot > 1.0 + 1e-9:
        raise ValueError(f"{name}: sum(gamma) = {tot:.6f} > 1 violates the source's budget")
    if not (0.0 < ctx.A <= 1.0):
        raise ValueError(f"{name}: delta = {ctx.A} outside (0, 1]")
    if not np.all(np.isfinite(ctx.Ev)) or np.any(ctx.Ev < 0.0):
        raise ValueError(f"{name}: e-values must be finite and nonnegative")
    if np.any(ctx.Ev > ctx.CEIL * (1.0 + 1e-9)):
        raise ValueError(f"{name}: CEIL = {ctx.CEIL} is not an upper bound on the evidence")


def _donation_wealth_rejected(E, g, rej_idx, d, Rn):
    """Their (26), the already-rejected half of Wbar_t:

        sum_{i in R_{t-1}} gamma_i * ((E_i - 1/(d gamma_i Rn)) ^ 1)

    Rn = |R_{t-1}| + 1 is its only time dependence, so the caller recomputes this only when
    |R| changes rather than at every step.  A summand is NEGATIVE when a past rejection
    cannot sustain itself at the larger discovery count -- that is the formula as written,
    and it is a top-up demand rather than a donation.  The caller counts how often the total
    goes negative, because the paper's claim that the level always dominates e-LOND's
    ((1 - (d Rn Wbar ^ 1))^{-1} >= 1, their note after (28)) needs Wbar >= 0.
    """
    w = 0.0
    for i in rej_idx:
        w += g[i] * min(E[i - 1] - 1.0 / (d * g[i] * Rn), 1.0)
    return w


def run_donation_elond(ctx, gam1, fired=None, diag=None):
    """Donation e-LOND, their (26)-(28):

        Wbar_t  = sum_{i in R_{t-1}}   gamma_i ((E_i - 1/(d gamma_i Rn)) ^ 1)
                + sum_{i notin R_{t-1}} gamma_i (E_i ^ 1)
        alpha_t = d gamma_t Rn / (1 - (d Rn Wbar_t ^ 1)),      Rn = |R_{t-1}| + 1

    WHY THIS IS IN thm:family1, AND EXACTLY HOW FAR.  Every summand of Wbar_t is gamma_i
    times a quantity capped at 1, so Wbar_t <= sum_i gamma_i <= 1 -- the donation budget IS
    the spending budget, which is why redistributing wealth cannot manufacture more of it.
    Hence the denominator is at least 1 - d*Rn and

        alpha_t <= d gamma_t Rn / (1 - d Rn)       whenever  d Rn < 1,

    a BOUNDED multiplicative boost, so the procedure satisfies the hypothesis of thm:family1
    with c = 1/(1 - d Rn) and degree 1.  Two scopes must be kept apart:

      COLD START (Rn = 1, no rejection yet) -- alpha_t <= d gamma_t / (1 - d).  This is the
        case cor:budget needs, because c_0 is by definition the constant multiplying gamma_T
        in the level offered BEFORE the first rejection.  So c_0 moves from alpha to
        alpha/(1-alpha) and the required |C| shrinks by a factor (1-alpha) -- 5% at
        alpha = 0.05.  `diag["max_boost_coldstart"]` checks this against the ceiling.

      AFTER Rn >= 1/d REJECTIONS the bound is vacuous: d*Rn*Wbar can saturate at 1, the
        denominator can reach 0, and the level becomes unbounded (their line 341 says any
        nonnegative e-value then satisfies the constraint).  Such a run has already made
        1/d = 20 discoveries, so it is not the regime C1 asks about -- C1 asks whether ANY
        discovery is possible -- but the bound must not be quoted as an all-time statement.
        `diag["max_boost"]` is the all-time figure and `diag["n_unbounded_level"]` counts the
        saturated steps, so the two are never conflated.
    """
    _check_source_assumptions(ctx, gam1, "donation e-LOND")
    T = ctx.T; d = ctx.A; E = ctx.Ev; g = gam1
    rej = tp = silent = 0; first = None
    if fired is not None: fired[...] = False
    unrej = 0.0                       # running sum_{i not in R} gamma_i (E_i ^ 1)
    rej_idx = []; R = 0
    wr = 0.0; wr_stale = True
    max_boost = 1.0; max_boost_cold = 1.0
    n_neg_wealth = 0; n_unbounded = 0; max_wealth = 0.0
    for t in range(1, T + 1):
        Rn = R + 1
        if wr_stale:
            wr = _donation_wealth_rejected(E, g, rej_idx, d, Rn); wr_stale = False
        W = unrej + wr
        if W < 0.0: n_neg_wealth += 1
        max_wealth = max(max_wealth, W)
        den = 1.0 - min(d * Rn * W, 1.0)
        if g[t] <= 0.0:
            # self-consistency needs gamma_t * Etilde_t >= 1/(d |R_t|), which is unsatisfiable
            # at gamma_t = 0 for any finite compound e-value, however much wealth is donated
            lvl = 0.0
        elif den <= 0.0:
            # the wealth saturates the denominator: the level is unbounded, so the realised
            # boost is too and must be reported as such rather than as its last finite value
            lvl = np.inf; n_unbounded += 1; max_boost = np.inf
            if R == 0: max_boost_cold = np.inf
        else:
            lvl = d * g[t] * Rn / den
            max_boost = max(max_boost, 1.0 / den)
            if R == 0: max_boost_cold = max(max_boost_cold, 1.0 / den)
        hit = False
        if ctx.infeasible(lvl):
            silent += 1
            if first is None: first = t
        elif np.isinf(lvl) or E[t - 1] >= 1.0 / lvl:
            hit = True
        if hit:
            rej += 1; rej_idx.append(t); R += 1; wr_stale = True
            if fired is not None: fired[t - 1] = True
            if ctx.ismal[t - 1]: tp += 1
        else:
            unrej += g[t] * min(E[t - 1], 1.0)
    if diag is not None:
        diag.update(max_boost=float(max_boost),
                    max_boost_coldstart=float(max_boost_cold),
                    boost_ceiling=(1.0 / (1.0 - d)) if d < 1.0 else float("inf"),
                    max_wealth=float(max_wealth), n_neg_wealth=int(n_neg_wealth),
                    n_unbounded_level=int(n_unbounded))
    return rej, tp, silent, first


def _closed_extend(v, Ei, ci, g, d, Rn):
    """One index of their dynamic program (21)-(22).

        v_t(i, k) = max{ v_t(i-1, k),  v_t(i-1, k-1) + 1{i in R_{t-1}} - d gamma_k E_i Rn }

    `v` holds v_t(i-1, .) for k = 0 .. len(v)-1; the return holds v_t(i, .) for k = 0 .. len(v).
    """
    L = len(v)
    prev = np.empty(L + 1); prev[:L] = v; prev[L] = -np.inf
    cand = np.empty(L + 1); cand[0] = -np.inf
    cand[1:] = v + (ci - d * Rn * Ei * g[1:L + 1])
    return np.maximum(prev, cand)


def _closed_build(E, g, rejmask, upto, d, Rn):
    """v_t(upto, .) from scratch, O(upto^2).  Needed whenever |R| changes, because Rn
    rescales every evidence term in (22) and so invalidates the whole table."""
    v = np.zeros(1)
    for i in range(1, upto + 1):
        v = _closed_extend(v, E[i - 1], 1.0 if rejmask[i - 1] else 0.0, g, d, Rn)
    return v


def run_closed_elond(ctx, gam1, fired=None, max_t=None, diag=None):
    """Closed e-LOND (their e-LOND-bar), test level (15)-(16) via the DP (19)-(22):

        alpha_t = min over k with 1 + v_t(t-1,k) > 0  of  d gamma_{k+1} Rn / (1 + v_t(t-1,k))

    WHY THIS NEEDS A SEPARATE ARGUMENT.  Unlike donation e-LOND this is NOT covered by the
    letter of thm:family1: the candidate at k = 0 (i.e. S empty) is d gamma_1 Rn, which does
    not decay in t, so the level is not gamma_t times a bounded factor.  It is covered by an
    argument specific to two-point conformal evidence.  Let

        Z_t = #{i < t : E_i = 0}.

    A zero-evidence hypothesis can never be rejected -- the rejection bar 1/alpha_t is strictly
    positive whenever alpha_t is finite, and E_i = 0 does not reach it (the bar need not exceed
    1; positivity is all the argument uses) -- so the set S of all Z_t zero-evidence indices
    satisfies |S ∩ R_{t-1}| = 0 and E_S = 0, hence
    D_t(S) = 1 > 0 and S is admissible in the minimum.  Therefore

        alpha_t <= d gamma_{Z_t + 1} Rn,

    the e-LOND decay with the time index rescaled by the non-firing fraction.  At security
    prevalence Z_t / t -> 1, so the horizon is finite and absorbing with T -> T(1 - p) for the
    firing rate p.  The closure draws its power from ACCUMULATED evidence, and a security
    stream supplies almost none.  `diag["worst_lvl_over_zero_bound"]` reports the largest
    realised alpha_t / (d gamma_{Z_t+1} Rn), which the bound requires to be <= 1.

    `max_t` truncates the run; the DP costs O(t) per step plus a full O(t^2) rebuild on each
    rejection, so a long stream with many rejections is the expensive case.
    """
    _check_source_assumptions(ctx, gam1, "closed e-LOND")
    T = ctx.T if max_t is None else min(ctx.T, int(max_t))
    d = ctx.A; E = ctx.Ev; g = gam1
    rej = tp = silent = 0; first = None
    if fired is not None: fired[...] = False
    rejmask = np.zeros(T, dtype=bool)
    R = 0; Rn = 1
    v = np.zeros(1)                          # v_t(0, .), before any index is folded in
    nzero = 0; worst_ratio = 0.0
    for t in range(1, T + 1):
        if t > 1:
            v = _closed_extend(v, E[t - 2], 1.0 if rejmask[t - 2] else 0.0, g, d, Rn)
        D = 1.0 + v
        ok = D > 0.0
        if ok.any():
            kk = np.flatnonzero(ok)
            lvl = float(np.min(d * g[kk + 1] * Rn / D[kk]))
        else:
            lvl = 0.0
        if nzero > 0:
            bnd = d * g[nzero + 1] * Rn
            if bnd > 0.0: worst_ratio = max(worst_ratio, lvl / bnd)
        hit = False
        if ctx.infeasible(lvl):
            silent += 1
            if first is None: first = t
        elif E[t - 1] >= 1.0 / lvl:
            hit = True
        if hit:
            rej += 1; rejmask[t - 1] = True; R += 1; Rn = R + 1
            if fired is not None: fired[t - 1] = True
            if ctx.ismal[t - 1]: tp += 1
            v = _closed_build(E, g, rejmask, t - 1, d, Rn)      # Rn changed: rebuild
        elif E[t - 1] == 0.0:
            nzero += 1
    if diag is not None:
        diag.update(n_zero_evidence=int(nzero), ran_to=int(T),
                    worst_lvl_over_zero_bound=float(worst_ratio),
                    truncated=bool(max_t is not None and ctx.T > T))
    return rej, tp, silent, first


def make_deadlines(kind, T, bucket=None, ts=None, horizon_s=None):
    """Deadline vector d_i >= i for e-TOAD, 1-indexed hypotheses, returned 0-indexed.

    The deadline is the paper's interpolation parameter between the two ends of our escape
    taxonomy, and operationally it is the SOC's ALERTING-LATENCY budget: how long a
    hypothesis may sit undecided before it must be accepted for good.

      "immediate"  d_i = i          -> e-LOND (their App. D.2)
      "arc"        d_i = infinity   -> online e-BH (their App. D.2)
      "bucket"     d_i = last hypothesis index sharing i's time bucket -> the BATCHED
                   architecture: the SOC receives a batch when the bucket closes and decides
                   it jointly, which is also order-free within the bucket
      "time"       d_i = last index whose episode starts within horizon_s of i's start
    """
    if kind == "immediate":
        return np.arange(1, T + 1, dtype=float)
    if kind == "arc":
        return np.full(T, np.inf)
    if kind == "bucket":
        b = np.asarray(bucket)
        if b.shape != (T,): raise ValueError(f"bucket must have shape ({T},)")
        if np.any(np.diff(b) < 0): raise ValueError("bucket ids must be non-decreasing")
        last = np.zeros(T, dtype=float)
        idx = np.arange(1, T + 1, dtype=float)
        _, start = np.unique(b, return_index=True)
        ends = np.append(start[1:], T)
        for s, e in zip(start, ends):
            last[s:e] = idx[e - 1]
        return last
    if kind == "time":
        t0 = np.asarray(ts, dtype=float)
        if t0.shape != (T,): raise ValueError(f"ts must have shape ({T},)")
        j = np.searchsorted(t0, t0 + float(horizon_s), side="right") - 1
        return np.maximum(j + 1, np.arange(1, T + 1)).astype(float)
    raise ValueError(kind)


def run_etoad(ctx, gam1, deadline, fired=None, diag=None):
    """e-TOAD (Fisher 2022) as stated in their App. D.2, (103)-(104):

        r_t = max{ r in {|R_{t-1} \\ A_t|, ..., m_t} :
                     #{i in A_t : E_i >= 1/(d gamma_i r)} >= r - |R_{t-1} \\ A_t| }
        R_t = R_{t-1} u {i in A_t : E_i >= 1/(d gamma_i r_t)}

    ACTIVE SET.  A_t = {i <= t : d_i >= t}, the hypotheses whose deadline has NOT yet passed.
    Their displayed definition reads "d_i <= t", which contradicts both the words around it
    ("whose deadlines have not yet passed") and the two limiting cases they state; we take the
    words.  The self-test pins the reading: d_i = i must reproduce e-LOND exactly and
    d_i = infinity must reproduce online e-BH exactly, which is their own claim, and only this
    reading does so.  It also makes the |R_{t-1} \\ A_t| term meaningful rather than vacuous.

    WHY THIS MATTERS FOR C1.  e-TOAD interpolates between the two ends of the escape
    taxonomy, so "advance the spending index on every hypothesis" (bound) and "defer the
    decision" (escape) are not a dichotomy but a one-parameter family indexed by the decision
    deadline.  With d_i = bucket close it is also the BATCHED architecture, valid under
    arbitrary dependence -- which BatchBH and BatchSt-BH are not.  The escape is
    self-referential: the bar E_i >= 1/(d gamma_i r) is unsatisfiable at E_i = 0, so r can
    never exceed the number of active hypotheses carrying nonzero evidence, and at security
    prevalence the batch does not supply the simultaneity the escape needs.

    `silent` is the at-arrival notion used by every other runner, computed EXACTLY: hypothesis
    t is counted silent when, even carrying the largest evidence the ceiling permits
    (E_t = CEIL) and with nothing else in the stream perturbed, the step-up at time t would not
    reject it.  The cheaper test -- does CEIL clear 1/(d gamma_t r) at the largest conceivable
    r -- is only NECESSARY, because reaching r needs r hypotheses to clear the bar at once and
    the realised active set may not supply them; it would under-count silence.
    """
    _check_source_assumptions(ctx, gam1, "e-TOAD")
    T = ctx.T; d = ctx.A; E = ctx.Ev
    g = gam1[1:T + 1]
    u = g * E                                   # bar E_i >= 1/(d gam_i r)  <=>  u_i >= 1/(d r)
    dl = np.asarray(deadline, dtype=float)
    if dl.shape != (T,): raise ValueError(f"deadline must have shape ({T},)")
    if np.any(dl < np.arange(1, T + 1)): raise ValueError("deadline requires d_i >= i")
    expires = {}
    for i in range(1, T + 1):
        if np.isfinite(dl[i - 1]):
            expires.setdefault(int(dl[i - 1]), []).append(i)
    rej_mask = np.zeros(T, dtype=bool)
    act_pos_u = np.empty(0); act_pos_i = np.empty(0, dtype=np.int64)   # sorted desc by u
    m_t = 0; locked = 0
    silent = 0; first = None
    prev_r = 0; n_regress = 0; max_r = 0; n_cap_differs = 0
    for t in range(1, T + 1):
        for i in expires.pop(t - 1, ()):                      # d_i = t-1 < t: leaves A_t
            m_t -= 1
            if rej_mask[i - 1]: locked += 1
            k = np.flatnonzero(act_pos_i == i)
            if k.size:
                act_pos_u = np.delete(act_pos_u, k[0]); act_pos_i = np.delete(act_pos_i, k[0])
        m_t += 1                                              # hypothesis t enters A_t
        if u[t - 1] > 0.0:
            p = int(np.searchsorted(-act_pos_u, -u[t - 1]))
            act_pos_u = np.insert(act_pos_u, p, u[t - 1])
            act_pos_i = np.insert(act_pos_i, p, t)
        npos = len(act_pos_u)
        # EXACT at-arrival feasibility, not the necessary condition alone.  Asking only whether
        # CEIL clears 1/(d gamma_t r) at the largest conceivable r is too generous: reaching r
        # requires r hypotheses to clear the bar simultaneously, and the realised active set may
        # not supply them.  So we run the actual step-up on the counterfactual stream in which
        # THIS hypothesis carries the largest evidence it could (E_t = CEIL), and ask whether it
        # would then be rejected.  Nothing else is perturbed.
        u_cf = g[t - 1] * ctx.CEIL
        if u_cf <= 0.0:
            rejectable = False
        else:
            cf = act_pos_u
            if u[t - 1] > 0.0:                      # replace t's own entry with the bumped one
                k_t = np.flatnonzero(act_pos_i == t)
                cf = np.delete(act_pos_u, k_t[0]) if k_t.size else act_pos_u
            p_cf = int(np.searchsorted(-cf, -u_cf))
            cf = np.insert(cf, p_cf, u_cf)
            smax_cf = min(m_t, len(cf))
            s_cf = 0
            if smax_cf > 0:
                ss_cf = np.arange(1, smax_cf + 1, dtype=float)
                ok_cf = cf[:smax_cf] * (d * (ss_cf + locked)) >= 1.0
                if ok_cf.any(): s_cf = int(ss_cf[np.flatnonzero(ok_cf)[-1]])
            r_cf = s_cf + locked
            rejectable = bool(r_cf > 0 and u_cf >= 1.0 / (d * r_cf))
        if not rejectable:
            silent += 1
            if first is None: first = t
        # s = r - |R_{t-1} \ A_t| is the number of discoveries drawn from the active set, so
        # r ranges over {locked, ..., locked + m_t}.  Their (103) writes the upper limit as
        # m_t, which cannot be meant: with d_i = i it gives the EMPTY range {R, ..., 1} once
        # R >= 2, and the procedure would stop rejecting.  The reading below is forced by
        # their own limiting case (d_i = i must be e-LOND); the self-test verifies it, and
        # n_steps_mt_cap_binds counts how often the literal limit would have differed.
        smax = min(m_t, npos)
        s = 0
        if smax > 0:
            ss = np.arange(1, smax + 1, dtype=float)
            ok = act_pos_u[:smax] * (d * (ss + locked)) >= 1.0
            if ok.any(): s = int(ss[np.flatnonzero(ok)[-1]])
        smax_lit = max(min(m_t - locked, npos), 0)            # their literal upper limit
        s_lit = 0
        if smax_lit > 0:
            ssl = np.arange(1, smax_lit + 1, dtype=float)
            okl = act_pos_u[:smax_lit] * (d * (ssl + locked)) >= 1.0
            if okl.any(): s_lit = int(ssl[np.flatnonzero(okl)[-1]])
        if s_lit != s: n_cap_differs += 1
        r = s + locked
        max_r = max(max_r, r)
        if r < prev_r: n_regress += 1
        prev_r = r
        if r > 0 and npos:
            thr = 1.0 / (d * r)
            hit = act_pos_i[act_pos_u >= thr]
            if hit.size: rej_mask[hit - 1] = True
    rej = int(rej_mask.sum()); tp = int((rej_mask & ctx.ismal).sum())
    if fired is not None: fired[...] = rej_mask
    if diag is not None:
        diag.update(max_r=int(max_r), n_r_regress=int(n_regress),
                    n_steps_mt_cap_binds=int(n_cap_differs))
    return rej, tp, silent, first


def _donation_balance(us, gs, cap, tail, d, r, extra=0.0):
    """The donation balance of their (102)/(106) at a candidate discovery count r:

        sum_{i<=r} (gamma_(i) E_(i) - 1/(d r)) ^ gamma_(i)  +  sum_{i>r} gamma_(i)(E_(i) ^ 1)

    Non-negative exactly when a valid gamma-weighted donation exists that keeps all r
    discoveries self-consistent.  `extra` carries the locked-hypothesis term Wbar(r)."""
    head = float(np.minimum(us[:r] - 1.0 / (d * r), gs[:r]).sum())
    return head + float(tail[r]) + extra


def _donation_rmax(npos, d, n):
    """A rigorous cap on the search over r.  For r > npos every added head term is
    -1/(d r) (a zero-evidence hypothesis has nothing to donate and needs a full top-up), so

        balance(r) <= sum(gamma) + sum(gamma) - (r - npos)/(d r) <= 2 - (1 - npos/r)/d,

    using sum(gamma) <= 1 twice.  At r >= 2 npos that is at most 2 - 1/(2d) < 0 whenever
    d < 1/4, so no r beyond 2 npos can qualify."""
    if not d < 0.25:
        return n
    return int(min(n, 2 * max(npos, 1) + 2))


def _donation_ebh_r(us, gs, tail, d, n, rmax):
    """Their (102): the largest r <= min(n, rmax) whose donation balance is non-negative."""
    best = 0
    hi = int(min(n, rmax))
    for r in range(1, hi + 1):
        if float(np.minimum(us[:r] - 1.0 / (d * r), gs[:r]).sum()) + float(tail[r]) >= 0.0:
            best = r
    return best


def run_donation_ebh(ctx, gam1, fired=None, diag=None, exact=False, history="snapshot"):
    """Online donation e-BH, their (102) -- the strict improvement over online e-BH, which is
    C1's SECOND escape (a history-wide fixed point rather than a spending index).  At each t it
    rejects the r_t largest gamma_i E_i, for the largest r_t whose donation balance is
    non-negative.

    THE SOURCE IS INCONSISTENT HERE, AND WE DO NOT RESOLVE IT.  Two of its own commitments
    collide on real streams, so `history` selects which one to honour and both are reported:

      "snapshot" (default) -- R_t is literally "the r_t largest indices of gamma_i E_i among
        i in [t]", exactly as (102) and the sentence after it define it, and exactly what the
        donation balance certifies.  But these sets are NOT nested: a later arrival can
        displace an earlier index out of the top r_t while r_t itself does not grow, so the
        procedure un-rejects.  Measured instance (d = 0.1, T = 7, gamma_i = 1/7,
        E = [6.899, 78.075, 73.067, 98.354, 66.194, 58.858, 7.758]): {1,...,6} at t = 6 and
        {2,...,7} at t = 7.  Un-rejecting contradicts the ARC premise it is built on, where
        decisions run acceptance-to-rejection only.

      "union" -- the ever-rejected set, which is what an irrevocable-decision deployment would
        actually have emitted.  But the balance does NOT certify it.  Measured instance
        (d = 0.1, T = 20, gamma_i = 1/20, the 20-value stream in the self-test): the snapshot
        at t = T has r = 10, the union has 11, and the (102) balance at r = 11 is -0.0412.

    Both instances are pinned as regression tests.  NOTHING IN OUR CLASSIFICATION RESTS ON THE
    CHOICE: donation e-BH is in the escaping class either way, because it escapes through a
    history-wide fixed point rather than a spending index, and that is the only property C1
    reads.  Its rejection COUNT should therefore not be quoted as a power comparison without
    naming which reading produced it.

    FAST PATH.  Once t > rmax, a hypothesis with gamma_t * (E_t ^ 1) = 0 changes nothing the
    balance reads: it appends to the end of the stable order among the ties at u = 0,
    contributes 0 to every tail sum, and any zero-u slot inside the top r contributes exactly
    -1/(d r) whichever index fills it.  Such steps are skipped.  `exact=True` disables the skip;
    the self-test asserts the two agree on adversarial streams.

    `silent` is NOT reported for this procedure (it is None).  The at-arrival feasibility test
    used by the immediate-decision runners asks whether CEIL clears 1/(d gamma_t r); under
    donation the effective bar is lowered by donated wealth, so that test is not the procedure's
    own feasibility condition and would misreport it in both directions.
    """
    _check_source_assumptions(ctx, gam1, "donation e-BH")
    if history not in ("snapshot", "union"):
        raise ValueError(f"history must be 'snapshot' or 'union', got {history!r}")
    T = ctx.T; d = ctx.A; E = ctx.Ev
    g = gam1[1:T + 1]
    pos_g = g > 0.0
    u = np.where(pos_g, g * E, 0.0)
    capw = np.where(pos_g, g * np.minimum(E, 1.0), 0.0)
    npos_total = int((u > 0.0).sum())
    rmax = _donation_rmax(npos_total, d, T)
    union = np.zeros(T, dtype=bool)
    snapshot = np.zeros(T, dtype=bool)
    n_recompute = 0; max_r = 0; r_regress = 0; prev_r = 0; n_unrejected = 0
    for t in range(1, T + 1):
        if not exact and t > rmax and capw[t - 1] == 0.0 and u[t - 1] == 0.0:
            continue
        n_recompute += 1
        uu = u[:t]
        order = np.argsort(-uu, kind="stable")
        us = uu[order]; gs = g[:t][order]
        cp = capw[:t][order]
        tail = np.concatenate([np.cumsum(cp[::-1])[::-1], [0.0]])
        r = _donation_ebh_r(us, gs, tail, d, t, rmax)
        if r < prev_r: r_regress += 1
        prev_r = r; max_r = max(max_r, r)
        step = np.zeros(T, dtype=bool)
        if r > 0:
            sel = order[:r]
            # gamma_i = 0 leaves the self-consistency bar unsatisfiable at any wealth; drop
            # such indices BEFORE they are counted, so |R_t| and r_t cannot disagree
            sel = sel[pos_g[sel]]
            step[sel] = True
        n_unrejected += int(np.count_nonzero(snapshot & ~step))
        snapshot = step
        union |= step
    rej_mask = snapshot if history == "snapshot" else union
    rej = int(rej_mask.sum()); tp = int((rej_mask & ctx.ismal).sum())
    if fired is not None: fired[...] = rej_mask
    if diag is not None:
        diag.update(history=history, source_faithful=(history == "snapshot"),
                    r_final=int(prev_r), max_r=int(max_r),
                    n_snapshot=int(snapshot.sum()), n_union=int(union.sum()),
                    n_unrejected_events=int(n_unrejected),
                    sets_are_nested=bool(int(union.sum()) == int(snapshot.sum())),
                    n_positive_evidence=int(npos_total), r_search_cap=int(rmax),
                    n_recompute=int(n_recompute), n_r_regress=int(r_regress))
    return rej, tp, None, None
