import numpy as np
from scipy.special import zeta


class Ctx:
    """Episode stream.  Ev = aggregated e-value per episode (arithmetic-mean rule,"""

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
        """No rejection possible at level lvl even at the evidence ceiling."""
        return lvl <= 0 or self.CEIL < 1.0 / lvl


def make_gamma(kind, T):
    """gam1 is 1-indexed (LOND, LORD++, SAFFRON, online e-BH)."""
    if kind == "poly":
        z = float(zeta(1.6, 1))
        g1 = np.zeros(T + 2); g1[1:] = np.arange(1, T + 2, dtype=float) ** -1.6 / z
        g0 = (np.arange(0, T + 2, dtype=float) + 1.0) ** -1.6 / z
    elif kind == "uniform":
        g1 = np.zeros(T + 2); g1[1:T + 1] = 1.0 / T
        g0 = np.zeros(T + 2); g0[0:T] = 1.0 / T
    else:
        raise ValueError(kind)
    return g1, g0


def run_lond(ctx, gam1, fired=None):
    """LOND / e-LOND: alpha_t = alpha * gamma_t * (R_{t-1} + 1)."""
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
    """LORD++: alpha_t = gamma_t w0 + (alpha-w0) gamma_{t-tau_1} + alpha sum_{j>=2} gamma_{t-tau_j}."""
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


def run_saffron(ctx, gam1, lam=0.5, fired=None):
    rej = tp = silent = 0; first = None
    if fired is not None: fired[...] = False
    B = np.empty(ctx.T + 1, dtype=np.int64); nt = 0
    cumC = 0
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
            A_j = cumC + (1 if cand else 0)
            B[nt] = t - A_j; nt += 1
            if ctx.ismal[t - 1]: tp += 1
        if cand: cumC += 1
    return rej, tp, silent, first


def run_addis(ctx, gam0, lam=0.25, tau_=0.5, fired=None, levels=None):
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


def online_ebh_kstar(Ev, gam1, alpha, T):
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
        entry = np.searchsorted(ks, m[idx], side='left')
        entry = np.maximum(entry, idx + 1)
        lag = float(np.median(entry - (idx + 1)))
    return rej, tp, silent, first, kfin, lag, never_rejectable


def _rai_omega(w1, phi, psi, nacc, nrej):
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
    R = 0; Rd = 0.0; rej = tp = silent = 0; first = None
    if fired is not None: fired[...] = False
    budget = ctx.A * (1.0 - lam) if kind == "e-SAFFRON" else ctx.A
    cand_thr = (1.0 / lam) if lam > 0 else np.inf
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
    n = nsteps or ctx.T
    g = np.empty(n); prod = 1.0; w = w1
    for t in range(1, n + 1):
        g[t - 1] = w * prod
        prod *= (1.0 - w)
        w = _rai_omega(w1, phi, psi, t, 0)
    return g


def _check_source_assumptions(ctx, gam1, name):
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
    w = 0.0
    for i in rej_idx:
        w += g[i] * min(E[i - 1] - 1.0 / (d * g[i] * Rn), 1.0)
    return w


def run_donation_elond(ctx, gam1, fired=None, diag=None):
    _check_source_assumptions(ctx, gam1, "donation e-LOND")
    T = ctx.T; d = ctx.A; E = ctx.Ev; g = gam1
    rej = tp = silent = 0; first = None
    if fired is not None: fired[...] = False
    unrej = 0.0
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
            lvl = 0.0
        elif den <= 0.0:
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
    L = len(v)
    prev = np.empty(L + 1); prev[:L] = v; prev[L] = -np.inf
    cand = np.empty(L + 1); cand[0] = -np.inf
    cand[1:] = v + (ci - d * Rn * Ei * g[1:L + 1])
    return np.maximum(prev, cand)


def _closed_build(E, g, rejmask, upto, d, Rn):
    v = np.zeros(1)
    for i in range(1, upto + 1):
        v = _closed_extend(v, E[i - 1], 1.0 if rejmask[i - 1] else 0.0, g, d, Rn)
    return v


def run_closed_elond(ctx, gam1, fired=None, max_t=None, diag=None):
    _check_source_assumptions(ctx, gam1, "closed e-LOND")
    T = ctx.T if max_t is None else min(ctx.T, int(max_t))
    d = ctx.A; E = ctx.Ev; g = gam1
    rej = tp = silent = 0; first = None
    if fired is not None: fired[...] = False
    rejmask = np.zeros(T, dtype=bool)
    R = 0; Rn = 1
    v = np.zeros(1)
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
            v = _closed_build(E, g, rejmask, t - 1, d, Rn)
        elif E[t - 1] == 0.0:
            nzero += 1
    if diag is not None:
        diag.update(n_zero_evidence=int(nzero), ran_to=int(T),
                    worst_lvl_over_zero_bound=float(worst_ratio),
                    truncated=bool(max_t is not None and ctx.T > T))
    return rej, tp, silent, first


def make_deadlines(kind, T, bucket=None, ts=None, horizon_s=None):
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
    _check_source_assumptions(ctx, gam1, "e-TOAD")
    T = ctx.T; d = ctx.A; E = ctx.Ev
    g = gam1[1:T + 1]
    u = g * E
    dl = np.asarray(deadline, dtype=float)
    if dl.shape != (T,): raise ValueError(f"deadline must have shape ({T},)")
    if np.any(dl < np.arange(1, T + 1)): raise ValueError("deadline requires d_i >= i")
    expires = {}
    for i in range(1, T + 1):
        if np.isfinite(dl[i - 1]):
            expires.setdefault(int(dl[i - 1]), []).append(i)
    rej_mask = np.zeros(T, dtype=bool)
    act_pos_u = np.empty(0); act_pos_i = np.empty(0, dtype=np.int64)
    m_t = 0; locked = 0
    silent = 0; first = None
    prev_r = 0; n_regress = 0; max_r = 0; n_cap_differs = 0
    for t in range(1, T + 1):
        for i in expires.pop(t - 1, ()):
            m_t -= 1
            if rej_mask[i - 1]: locked += 1
            k = np.flatnonzero(act_pos_i == i)
            if k.size:
                act_pos_u = np.delete(act_pos_u, k[0]); act_pos_i = np.delete(act_pos_i, k[0])
        m_t += 1
        if u[t - 1] > 0.0:
            p = int(np.searchsorted(-act_pos_u, -u[t - 1]))
            act_pos_u = np.insert(act_pos_u, p, u[t - 1])
            act_pos_i = np.insert(act_pos_i, p, t)
        npos = len(act_pos_u)
        u_cf = g[t - 1] * ctx.CEIL
        if u_cf <= 0.0:
            rejectable = False
        else:
            cf = act_pos_u
            if u[t - 1] > 0.0:
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
        smax = min(m_t, npos)
        s = 0
        if smax > 0:
            ss = np.arange(1, smax + 1, dtype=float)
            ok = act_pos_u[:smax] * (d * (ss + locked)) >= 1.0
            if ok.any(): s = int(ss[np.flatnonzero(ok)[-1]])
        smax_lit = max(min(m_t - locked, npos), 0)
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
    head = float(np.minimum(us[:r] - 1.0 / (d * r), gs[:r]).sum())
    return head + float(tail[r]) + extra


def _donation_rmax(npos, d, n):
    if not d < 0.25:
        return n
    return int(min(n, 2 * max(npos, 1) + 2))


def _donation_ebh_r(us, gs, tail, d, n, rmax):
    best = 0
    hi = int(min(n, rmax))
    for r in range(1, hi + 1):
        if float(np.minimum(us[:r] - 1.0 / (d * r), gs[:r]).sum()) + float(tail[r]) >= 0.0:
            best = r
    return best


def run_donation_ebh(ctx, gam1, fired=None, diag=None, exact=False, history="snapshot"):
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
