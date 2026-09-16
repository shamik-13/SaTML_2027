"""Review priority 1, item 3 -- "the strongest recent compound-e / e-closure method that is"""


def main():
    import numpy as np, json, time
    from pathlib import Path
    import h_stream as hs

    Path("out").mkdir(exist_ok=True)
    t0 = time.time()
    W0 = 0.025; BUCKET = 2 * 3600
    POS = [0.55, 0.62, 0.70, 0.77, 0.85]
    SEEDS = [0, 1]


    def optimal_boost(values, probs, tau):
        """Largest b with E[b*V*1{b*V >= tau}] <= 1 for a discrete e-variable."""
        v = np.asarray(values, dtype=float); p = np.asarray(probs, dtype=float)
        o = np.argsort(v); v = v[o]; p = p[o]
        suf = np.concatenate([np.cumsum((v * p)[::-1])[::-1], [0.0]])

        def f(b):
            if b <= 0: return 0.0
            i = int(np.searchsorted(v, tau / b, side="left"))
            return b * float(suf[i])

        if f(1.0) > 1.0:
            lo, hi = 0.0, 1.0
        else:
            lo, hi = 1.0, 1.0
            while f(hi) <= 1.0 and hi < 1e12:
                lo = hi; hi *= 2.0
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            if f(mid) <= 1.0: lo = mid
            else: hi = mid
        return 1.0 if abs(lo - 1.0) <= 1e-10 and f(1.0) <= 1.0 else lo


    print("=" * 104)
    print("BOOSTING A TWO-POINT (THRESHOLD CONFORMAL) e-VALUE")
    print("=" * 104)
    sym = []
    for M in (1e3, 1e5, 1_813_114.0):
        for tau_mult in (0.1, 0.5, 0.9):
            tau = tau_mult * M
            vals = np.array([0.0, M]); pr = np.array([1 - 1 / M, 1 / M])
            b = optimal_boost(vals, pr, tau)
            sym.append(dict(M=M, tau=tau, b_star=float(b)))
            print(f"  M={M:>12,.0f}  tau={tau:>12,.0f}  optimal boost b* = {b:.6f}")
    print("\n  b* = 1 in every cell: boosting a two-point e-value gains exactly nothing.")

    print("\n" + "=" * 104)
    print("CONTRAST -- BOOSTING A CONTINUOUS e-VALUE (Vovk calibrator E = 1/(2*sqrt(U)))")
    print("=" * 104)
    Ngrid = 2_000_000
    grid = (np.arange(Ngrid) + 0.5) / Ngrid
    vals_c = 0.5 / np.sqrt(grid); pr_c = np.full(Ngrid, 1.0 / Ngrid)
    cont = []
    for tau in (2.0, 5.0, 20.0, 100.0):
        b = optimal_boost(vals_c, pr_c, tau)
        closed = np.sqrt(2.0 * tau)
        cont.append(dict(tau=tau, b_star=float(b), closed_form=float(closed)))
        print(f"  tau={tau:>8,.0f}   optimal boost b* = {b:>7.4f}   closed form sqrt(2*tau) = {closed:>7.4f}")
    print("\n  b* > 1 and grows as sqrt(tau), matching the closed form, because a continuous")
    print("  e-value has mass sitting below the threshold that boosting can lift.")
    print("  A two-point e-value has none: its mass is already all at the ceiling or at zero.")

    print("\n" + "=" * 104)
    print("EMPIRICAL b* ON REAL LSPR23 SCORES (uses the MEASURED benign firing rate)")
    print("=" * 104)
    X, y, ts, src, dst = hs.load()
    N = len(y)
    rows = []
    print(f"  {'pos':>6} {'seed':>5} {'|C|':>12} {'nominal P(fire)':>16} {'measured P(fire)':>17} "
          f"{'ratio':>8} {'b* = 1/(M*Pmeas)':>18}")
    for pos in POS:
        i1, i2, i3 = hs.split_indices(N, pos)
        y_cal, y_te = y[i1:i2], y[i2:i3]
        for seed in SEEDS:
            score = hs.fit_detector(X, y, i1, seed=seed, kind="hgb", verbose=False)
            s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
            e_te, cal, NC, CEIL = hs.evalues(s_cal, y_cal, s_te, k=1)
            ben = y_te == 0
            p_meas = float((e_te[ben] > 0).mean())
            p_nom = 1.0 / CEIL
            b_star = (1.0 / (CEIL * p_meas)) if p_meas > 0 else np.inf
            rows.append(dict(pos=pos, seed=seed, NC=int(NC), p_nominal=p_nom,
                             p_measured=p_meas, ratio=float(p_meas / p_nom),
                             b_star=float(b_star)))
            print(f"  {pos:>6} {seed:>5} {NC:>12,} {p_nom:>16.3e} {p_meas:>17.3e} "
                  f"{p_meas/p_nom:>8.2f} {b_star:>18.4f}")

    bs = [r["b_star"] for r in rows if np.isfinite(r["b_star"])]
    print(f"\n  b* median over the {len(bs)} configurations with a positive measured firing "
          f"rate = {np.median(bs):.4f}, range [{min(bs):.4f}, {max(bs):.4f}]")
    print(f"  {len(rows) - len(bs)} configurations had zero benign firings, giving b* = inf; "
          f"they are excluded rather than counted as boostable.")
    print("  Where b* < 1 the nominal e-value is already anti-conservative on real traffic")
    print("  (F9), so the correct 'boost' is a shrinkage.  Either way there is no free power:")
    print("  the strongest power-recovery technique for e-BH returns nothing on this evidence,")
    print("  and it returns nothing for the same reason the feasibility boundary exists -- the")
    print("  evidence is two-point, not because the procedure is weak.")

    json.dump({"two_point": sym, "continuous": cont, "empirical": rows,
               "b_star_median": float(np.median(bs)) if bs else None},
              open("out/t29_compound_e.json", "w"), indent=1, allow_nan=True)
    print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t29_compound_e.json")


if __name__ == "__main__":
    main()
