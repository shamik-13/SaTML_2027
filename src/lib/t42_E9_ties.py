


def main():
    import numpy as np, json, time
    from pathlib import Path

    import h_stream as hs
    from h6_procs import Ctx, make_gamma, run_lond, run_lordpp, run_addis

    OUT = Path(__file__).resolve().parent / "out"
    OUT.mkdir(exist_ok=True)
    t0 = time.time()

    POS_EXPOSURE = [0.55, 0.62, 0.70, 0.77, 0.85]
    POS_FULL = [0.55, 0.85]
    K = 1; A = 0.05; W0 = 0.025; BUCKET = 2 * 3600; SEED = 0
    NSEED = 50
    LAM, TAU = 0.25, 0.5
    out = {"config": dict(pos_exposure=POS_EXPOSURE, pos_full=POS_FULL, k=K, alpha=A, w0=W0,
                          bucket_s=BUCKET, detector_seed=SEED, n_tie_seeds=NSEED,
                          derivation="t42a_E9_derivation.py")}
    FAIL = []


    def note(cond, msg):
        if not cond:
            FAIL.append(msg)
            print(f"    *** ASSERTION FAILED: {msg}")
        return cond


    def tie_exposure(first_ts):
        """The movable population, from timestamps alone.  [D2a]"""
        ts = np.asarray(first_ts)
        _, counts = np.unique(ts, return_counts=True)
        return dict(n_episodes=int(len(ts)), n_blocks=int(len(counts)),
                    n_tied=int(counts[counts >= 2].sum()),
                    n_nontrivial_blocks=int((counts >= 2).sum()),
                    B_max=int(counts.max()) if len(counts) else 0,
                    tied_fraction=float(counts[counts >= 2].sum() / max(len(ts), 1)))


    def first_ts_by_group(ts_w, gid, T):
        """Each episode's first flow timestamp, indexed by GROUP ID (build_episodes' internal"""
        first = np.full(T, np.iinfo(np.int64).max)
        np.minimum.at(first, gid, np.asarray(ts_w))
        return first


    def stats(fired, ismal, n_mal):
        """Discoveries, true positives, FDP, recall, first-detection rank."""
        r = int(fired.sum()); tp = int((fired & ismal).sum())
        idx = np.flatnonzero(fired)
        return dict(rejections=r, tp=tp, fp=r - tp,
                    fdp=(float((r - tp) / r) if r else None),
                    recall=float(tp / n_mal) if n_mal else 0.0,
                    first_rank=(int(idx[0]) + 1 if r else None),
                    first_tp_rank=(int(np.flatnonzero(fired & ismal)[0]) + 1
                                   if tp else None))


    def percentile_of(value, sample):
        """Where the deterministic value sits inside the randomised distribution, as the"""
        s = np.asarray([x for x in sample if x is not None], dtype=float)
        if value is None or s.size == 0:
            return None
        return float(((s < value).sum() + 0.5 * (s == value).sum()) / s.size)


    def run_procs(ep, CEIL):
        """LOND, LORD++ and ADDIS on one episode ordering, through the shared module."""
        T = ep["T"]
        ctx = Ctx(ep["Ev"], ep["ismal"], CEIL, alpha=A, w0=W0)
        g1, g0 = make_gamma("poly", T)
        res = {}
        for nm in ("lond", "lordpp", "addis"):
            fired = np.zeros(T, bool)
            if nm == "lond":
                run_lond(ctx, g1, fired=fired)
            elif nm == "lordpp":
                run_lordpp(ctx, g1, fired=fired)
            else:
                run_addis(ctx, g0, lam=LAM, tau_=TAU, fired=fired)
            res[nm] = stats(fired, ep["ismal"], ep["n_mal"])
        return res


    print("=" * 118)
    print("E9 -- TIMESTAMP-TIE SENSITIVITY")
    print("=" * 118)
    X, y, ts, src, dst = hs.load()
    N = len(y)

    print("\n" + "=" * 118)
    print("[D2a] EXPOSURE -- computed from timestamps alone, no detector and no labels")
    print("=" * 118)
    print(f"  {'window':>8} {'episodes':>10} {'distinct ts':>12} {'tied blocks':>12} "
          f"{'episodes tied':>14} {'fraction':>10} {'B_max':>7}")
    exposure = {}
    for pos in POS_EXPOSURE:
        i1, i2, i3 = hs.split_indices(N, pos)
        ep0 = hs.build_episodes(np.zeros(i3 - i2), y[i2:i3], ts[i2:i3], src[i2:i3], dst[i2:i3],
                                BUCKET, "src-dst")
        fts = first_ts_by_group(ts[i2:i3], ep0["gid"], ep0["T"])
        e = tie_exposure(fts)
        exposure[str(pos)] = e
        print(f"  {pos:>8.2f} {e['n_episodes']:>10,} {e['n_blocks']:>12,} "
              f"{e['n_nontrivial_blocks']:>12,} {e['n_tied']:>14,} "
              f"{e['tied_fraction']:>10.4f} {e['B_max']:>7,}")
    out["exposure"] = exposure
    max_frac = max(e["tied_fraction"] for e in exposure.values())
    print(f"\n  largest tied fraction over the five windows: {max_frac:.4f}")
    if max_frac == 0.0:
        print("  -> zero exposure: the deterministic tie-break is INERT and E9 is a one-line "
              "appendix note.")
    else:
        print(f"  -> non-zero exposure, so the seeds below can move something.  [D2a] bounds "
              f"the movable population at {max(e['n_tied'] for e in exposure.values()):,} "
              f"episodes and the first-detection rank shift at "
              f"{max(e['B_max'] for e in exposure.values())-1} ranks.")

    rows = []
    for pos in POS_FULL:
        print("\n" + "=" * 118)
        print(f"POSITION {pos} -- {NSEED} randomised tie orders against the deterministic one")
        print("=" * 118)
        i1, i2, i3 = hs.split_indices(N, pos)
        score = hs.fit_detector(X, y, i1, seed=SEED, kind="hgb", verbose=False)
        s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
        e_te, cal, NC, CEIL = hs.evalues(s_cal, y[i1:i2], s_te, k=K)

        det_ep = hs.build_episodes(e_te, y[i2:i3], ts[i2:i3], src[i2:i3], dst[i2:i3],
                                   BUCKET, "src-dst")
        det = run_procs(det_ep, CEIL)
        T = det_ep["T"]
        fts = first_ts_by_group(ts[i2:i3], det_ep["gid"], T)
        e = exposure[str(pos)]
        print(f"  T = {T:,} episodes, {det_ep['n_mal']} malicious, |C| = {NC:,}; "
              f"{e['n_tied']:,} episodes ({100*e['tied_fraction']:.1f}%) are tie-movable, "
              f"B_max = {e['B_max']}  [{time.time()-t0:.0f}s]")

        draws = {nm: [] for nm in ("lond", "lordpp", "addis")}
        rng = np.random.default_rng(20260827 + int(pos * 100))
        n_order_changed = 0
        n_moved_total = 0
        rng_seed_orders = []
        for sd in range(NSEED):
            tie_key = rng.permutation(T)
            rep = hs.build_episodes(e_te, y[i2:i3], ts[i2:i3], src[i2:i3], dst[i2:i3],
                                    BUCKET, "src-dst", tie_key=tie_key)
            nmoved = int((rep["order"] != det_ep["order"]).sum())
            n_moved_total += nmoved
            n_order_changed += int(nmoved > 0)
            rng_seed_orders.append(nmoved)
            if sd == 0:
                note(np.array_equal(np.sort(fts[det_ep["order"]]), fts[rep["order"]]),
                     f"tie randomisation moved the timestamp sequence at pos={pos}")
                note(np.array_equal(np.sort(det_ep["nsz"]), np.sort(rep["nsz"])),
                     f"tie randomisation changed the episode partition at pos={pos}")
            for nm, st in run_procs(rep, CEIL).items():
                draws[nm].append(st)

        note(n_order_changed == NSEED,
             f"only {n_order_changed} of {NSEED} tie orders differ from the deterministic one "
             f"at pos={pos}: an sd of 0 below would then be an artefact")
        print(f"\n  [power] {n_order_changed} of {NSEED} randomised orders differ from the "
              f"deterministic one; a draw moves {np.mean(rng_seed_orders):.0f} episode positions "
              f"on average (min {min(rng_seed_orders)}, max {max(rng_seed_orders)}) out of "
              f"{e['n_tied']:,} movable.")
        out.setdefault("power", {})[str(pos)] = dict(
            n_orders_changed=n_order_changed, n_draws=NSEED,
            mean_positions_moved=float(np.mean(rng_seed_orders)),
            min_positions_moved=int(min(rng_seed_orders)),
            max_positions_moved=int(max(rng_seed_orders)),
            n_movable=int(e["n_tied"]))
        print(f"\n  {'proc':>8} {'stat':>12} {'deterministic':>14} {'mean':>10} {'sd':>10} "
              f"{'min':>10} {'max':>10} {'pctile of det':>14}")
        for nm in ("lond", "lordpp", "addis"):
            for stat_name in ("rejections", "tp", "fdp", "recall", "first_rank",
                              "first_tp_rank"):
                vals = [d[stat_name] for d in draws[nm]]
                fin = np.asarray([v for v in vals if v is not None], dtype=float)
                dv = det[nm][stat_name]
                pct = percentile_of(dv, vals)
                n_none = sum(1 for v in vals if v is None)
                key = lambda v: None if v is None else float(v)
                support = {key(v) for v in vals}
                n_distinct = len(support)
                varies = bool(len(support | {key(dv)}) > 1)
                row = dict(pos=pos, proc=nm, stat=stat_name,
                           deterministic=dv, n_distinct=n_distinct, varies=varies,
                           undefined_fraction=float(n_none / NSEED),
                           deterministic_undefined=bool(dv is None),
                           mean=(float(fin.mean()) if fin.size else None),
                           sd=(float(fin.std(ddof=1)) if fin.size > 1 else None),
                           min=(float(fin.min()) if fin.size else None),
                           max=(float(fin.max()) if fin.size else None),
                           n_undefined=n_none, n_draws=NSEED, pctile_of_det=pct)
                rows.append(row)
                fmt = lambda v: "     -" if v is None else (f"{v:>10.4f}" if isinstance(v, float)
                                                            else f"{v:>10}")
                print(f"  {nm:>8} {stat_name:>12} "
                      f"{'         -' if dv is None else (format(dv,'>14.4f') if isinstance(dv,float) else format(dv,'>14,'))}"
                      f" {fmt(row['mean'])} {fmt(row['sd'])} {fmt(row['min'])} {fmt(row['max'])}"
                      f" {'      -' if pct is None else format(pct,'>14.3f')}"
                      + (f"   ({n_none} undefined)" if n_none else ""))
        out.setdefault("deterministic", {})[str(pos)] = det

    out["rows"] = rows

    for pos in POS_FULL:
        sub = [r for r in rows if r["pos"] == pos]
        moved = [r for r in sub if r["varies"]]
        extreme = [r for r in sub if r["pctile_of_det"] is not None
                   and r["undefined_fraction"] == 0.0 and not r["deterministic_undefined"]
                   and (r["pctile_of_det"] <= 0.05 or r["pctile_of_det"] >= 0.95)]
        undef = [r for r in sub if r["undefined_fraction"] > 0 or r["deterministic_undefined"]]
        print(f"\n  position {pos}: {len(moved)} of {len(sub)} statistics take more than one "
              f"value across {NSEED} tie orders;")
        print(f"    {len(extreme)} sit in an extreme 5% tail of their randomised distribution "
              f"(over the {len(sub)-len(undef)} that are defined in every draw; "
              f"{len(undef)} are not).")
        for r in moved:
            rel = (r["sd"] / abs(r["mean"])) if r["mean"] else float("nan")
            print(f"      {r['proc']:>7} {r['stat']:<13} det={r['deterministic']!s:>10} "
                  f"{r['n_distinct']} distinct values, mean={r['mean']:>10.4f} "
                  f"sd={r['sd']:>9.4g} ({100*rel:.2f}% of mean)  "
                  f"range [{r['min']:.6g}, {r['max']:.6g}]  pctile {r['pctile_of_det']:.3f}")
        if not moved:
            print("      none -- every statistic takes a single value across all "
                  f"{NSEED} randomised tie orders, and it equals the deterministic one.")

    out["assertions_failed"] = FAIL
    json.dump(out, open(OUT / "t42_E9.json", "w"), indent=1, allow_nan=True)
    print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t42_E9.json")
    if FAIL:
        print("  ASSERTIONS FAILED:")
        for m in FAIL:
            print("   -", m)
        raise SystemExit(1)
    print("  all derivation assertions held")

    return out


if __name__ == "__main__":
    main()
