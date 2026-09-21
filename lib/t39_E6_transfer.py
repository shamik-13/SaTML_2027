
import numpy as np



def select(values, order):

    v = np.asarray(values, dtype=float)
    o = np.asarray(order)
    if np.isinf(v).any():
        raise ValueError("objective contains inf: select() would return a finite value "
                         "and silently not be an argmax")
    finite = np.isfinite(v)
    if not finite.any():
        raise ValueError("no finite objective values: there is nothing to select over")
    best = float(v[finite].max())
    tied = np.flatnonzero(finite & (v == best))
    return int(tied[np.argmin(o[tied])]), int(len(tied))


def normalised_regret(values_on_eval, achieved):
    """(oracle - achieved)/(oracle - worst).  None on a FLAT grid, never 0.        [D2a]"""
    v = np.asarray(values_on_eval, dtype=float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return None
    hi, lo = float(v.max()), float(v.min())
    spread = hi - lo
    if spread <= max(1e-12, 1e-12 * max(abs(hi), abs(lo), 1.0)):
        return None
    return float((hi - float(achieved)) / spread)


def main():
    import numpy as np, json, time
    from pathlib import Path

    OUT = Path(__file__).resolve().parent / "out"
    OUT.mkdir(exist_ok=True)
    t0 = time.time()

    POS = [0.55, 0.62, 0.70, 0.77, 0.85]
    SEEDS = [0, 1]
    W0 = 0.025

    FAMILY_ORDER = ["src-dst", "src", "dst", "subnet24", "src-dport"]
    BUCKET_ORDER = [7200, 3600, 1800, 300, 21600, 86400, None]
    CAP_ORDER = ["p99", "max", "p999", "p90", "p50", "mean"]
    FROZEN_GROUPING = ("src-dst", 7200)
    FROZEN_CAP = "p99"
    OBJ = "flow_cov_addis"
    OBJ_ORACLE = "flow_cov_elond"

    out = {"config": dict(pos=POS, seeds=SEEDS, objective=OBJ, oracle_objective=OBJ_ORACLE,
                          family_order=FAMILY_ORDER, bucket_order=[str(b) for b in BUCKET_ORDER],
                          cap_order=CAP_ORDER, frozen_grouping=list(map(str, FROZEN_GROUPING)),
                          frozen_cap=FROZEN_CAP, derivation="t39a_E6_derivation.py")}
    FAIL = []


    def note(cond, msg):
        if not cond:
            FAIL.append(msg)
            print(f"    *** ASSERTION FAILED: {msg}")
        return cond


    def transfer_table(cfgs, order, value, sel_windows, eval_window, frozen_idx, feas=None):
        """One (select on sel_windows, evaluate on eval_window) result."""
        n = len(cfgs)
        sel_mat = np.asarray([value[w] for w in sel_windows], dtype=float)
        ok = np.isfinite(sel_mat).all(axis=0)
        if feas is not None:
            ok = ok & np.asarray([feas[w] for w in sel_windows], dtype=bool).all(axis=0)
        sel = np.full(n, np.nan)
        if ok.any():
            sel[ok] = sel_mat[:, ok].mean(axis=0)

        ev = np.asarray(value[eval_window], dtype=float)
        ev_ok = np.isfinite(ev)
        if feas is not None:
            ev_ok = ev_ok & np.asarray(feas[eval_window], dtype=bool)
        ev_masked = np.where(ev_ok, ev, np.nan)

        sfin = sel[np.isfinite(sel)]
        sel_spread = float(sfin.max() - sfin.min()) if sfin.size else None
        transfer_defined = bool(sel_spread is not None
                                and sel_spread > max(1e-12, 1e-12 * max(abs(float(sfin.max())), 1.0)))

        w, nt = select(sel, order)
        oi, _ = select(ev_masked, order)
        oracle = float(ev[oi]); worst = float(np.nanmin(ev_masked))
        reg = float(oracle - ev[w])
        freg = float(oracle - ev[frozen_idx])
        return dict(winner=cfgs[w], n_tied=nt, n_eligible=int(ok.sum()),
                    value_on_selection=float(sel[w]), value_on_eval=float(ev[w]),
                    winner_feasible_on_eval=(None if feas is None else bool(feas[eval_window][w])),
                    winners_curse=float(sel[w] - ev[w]),
                    selection_spread=sel_spread, transfer_defined=transfer_defined,
                    oracle=oracle, oracle_config=cfgs[oi], worst=worst,
                    spread=float(oracle - worst),
                    regret=reg, rho=normalised_regret(ev_masked, ev[w]),
                    is_worst=bool(abs(ev[w] - worst) <= 1e-12),
                    frozen=cfgs[frozen_idx], frozen_value=float(ev[frozen_idx]),
                    frozen_regret=freg, frozen_rho=normalised_regret(ev_masked, ev[frozen_idx]),
                    frozen_is_worst=bool(abs(ev[frozen_idx] - worst) <= 1e-12),
                    frozen_feasible_on_eval=(None if feas is None
                                             else bool(feas[eval_window][frozen_idx])),
                    mean_config=float(np.nanmean(ev_masked)),
                    mean_config_rho=normalised_regret(ev_masked,
                                                      float(np.nanmean(ev_masked))))


    def run_axis(name, cfgs, order, value, alt, frozen_cfg, obj_label=OBJ,
                 alt_label="addis_recall", feas=None, extra_print=None):
        """E6a (previous window) and E6b (leave-one-out) over one configuration axis."""
        if alt is value or (isinstance(alt, np.ndarray) and alt is value):
            raise ValueError("alt must differ from value -- see D3a")
        frozen_idx = cfgs.index(frozen_cfg)
        print("\n" + "=" * 118)
        print(f"{name}:  {len(cfgs)} configurations x {len(POS)} windows, "
              f"objective = {obj_label}")
        print("=" * 118)
        print(f"  {'window':>8} {'oracle':>9} {'worst':>9} {'spread':>9} {'frozen':>9} "
              f"{'mean cfg':>9} {'oracle config':>28}     (* = frozen is the worst "
              f"FEASIBLE config on that window)")
        per_window = []
        for w, p in enumerate(POS):
            ev = np.asarray(value[w], dtype=float)
            fin = np.isfinite(ev)
            if feas is not None:
                fin = fin & np.asarray(feas[w], dtype=bool)
            evm = np.where(fin, ev, np.nan)
            bi, bn = select(evm, order)
            fz_worst = bool(abs(ev[frozen_idx] - np.nanmin(evm)) <= 1e-12)
            per_window.append(dict(pos=p, oracle=float(ev[bi]), worst=float(np.nanmin(evm)),
                                   spread=float(ev[bi] - np.nanmin(evm)),
                                   oracle_config=cfgs[bi], oracle_n_tied=bn,
                                   n_feasible=int(fin.sum()),
                                   frozen_value=float(ev[frozen_idx]),
                                   frozen_is_worst=fz_worst,
                                   frozen_rho=normalised_regret(evm, ev[frozen_idx]),
                                   mean_config=float(np.nanmean(evm))))
            print(f"  {p:>8.2f} {ev[bi]:>9.4f} {np.nanmin(evm):>9.4f} "
                  f"{ev[bi]-np.nanmin(evm):>9.4f} {ev[frozen_idx]:>9.4f}"
                  f"{'*' if fz_worst else ' '} "
                  f"{np.nanmean(evm):>9.4f} {str(cfgs[bi]):>28}")
        print(f"\n  [D2a] window-to-window variation of the ORACLE is "
              f"{max(r['oracle'] for r in per_window) - min(r['oracle'] for r in per_window):.4f}; "
              f"the largest within-window spread is "
              f"{max(r['spread'] for r in per_window):.4f}.")

        rows_a, rows_b = [], []
        print(f"\n  E6a -- previous-window selection")
        print(f"  {'select':>7} {'eval':>6} {'winner':>26} {'tied':>5} {'sel val':>9} "
              f"{'eval val':>9} {'curse':>8} {'oracle':>8} {'regret':>8} {'rho':>7} "
              f"{'frozen':>8}")
        for j in range(1, len(POS)):
            r = transfer_table(cfgs, order, value, [j - 1], j, frozen_idx, feas=feas)
            r.update(select_pos=POS[j - 1], eval_pos=POS[j], mode="E6a")
            rows_a.append(r)
            note(r["regret"] >= -1e-12, f"{name} E6a negative regret at {POS[j]}")
            print(f"  {POS[j-1]:>7.2f} {POS[j]:>6.2f} {str(r['winner']):>26} {r['n_tied']:>5} "
                  f"{r['value_on_selection']:>9.4f} {r['value_on_eval']:>9.4f} "
                  f"{r['winners_curse']:>8.4f} {r['oracle']:>8.4f} {r['regret']:>8.4f} "
                  f"{'  n/a' if r['rho'] is None else format(r['rho'], '>7.3f')} "
                  f"{r['frozen_value']:>8.4f}"
                  f"{'' if r['transfer_defined'] else '   [FLAT SELECTION WINDOW: not a transfer result]'}")
        print(f"\n  E6b -- leave-one-window-out selection")
        print(f"  {'held out':>9} {'winner':>26} {'tied':>5} {'sel val':>9} {'eval val':>9} "
              f"{'curse':>8} {'oracle':>8} {'regret':>8} {'rho':>7} {'frozen':>8}")
        for j in range(len(POS)):
            others = [i for i in range(len(POS)) if i != j]
            r = transfer_table(cfgs, order, value, others, j, frozen_idx, feas=feas)
            r.update(eval_pos=POS[j], mode="E6b")
            rows_b.append(r)
            note(r["regret"] >= -1e-12, f"{name} E6b negative regret at {POS[j]}")
            print(f"  {POS[j]:>9.2f} {str(r['winner']):>26} {r['n_tied']:>5} "
                  f"{r['value_on_selection']:>9.4f} {r['value_on_eval']:>9.4f} "
                  f"{r['winners_curse']:>8.4f} {r['oracle']:>8.4f} {r['regret']:>8.4f} "
                  f"{'  n/a' if r['rho'] is None else format(r['rho'], '>7.3f')} "
                  f"{r['frozen_value']:>8.4f}"
                  f"{'' if r['transfer_defined'] else '   [FLAT SELECTION WINDOW: not a transfer result]'}")

        rec_pick = []
        for w, p in enumerate(POS):
            ri, _ = select(np.asarray(alt[w], dtype=float), order)
            vi, _ = select(np.asarray(value[w], dtype=float), order)
            rec_pick.append(dict(pos=p, alt_winner=cfgs[ri], obj_winner=cfgs[vi],
                                 alt_of_alt_winner=float(alt[w][ri]),
                                 obj_of_alt_winner=float(value[w][ri]),
                                 obj_of_obj_winner=float(value[w][vi])))
        print(f"\n  [D3a] what each objective would have selected, per window")
        print(f"  {'window':>8} {'argmax ' + alt_label:>26} {'its ' + obj_label[:9]:>13} "
              f"{'argmax ' + obj_label:>26} {'its ' + obj_label[:9]:>13}")
        for r in rec_pick:
            print(f"  {r['pos']:>8.2f} {str(r['alt_winner']):>26} "
                  f"{r['obj_of_alt_winner']:>13.4f} {str(r['obj_winner']):>26} "
                  f"{r['obj_of_obj_winner']:>13.4f}")
        n_diff = sum(1 for r in rec_pick if r["alt_winner"] != r["obj_winner"])
        print(f"        the two objectives disagree at {n_diff} of {len(POS)} windows")
        if extra_print:
            extra_print()
        return dict(per_window=per_window, E6a=rows_a, E6b=rows_b,
                    objective=obj_label, alt_objective=alt_label,
                    objective_comparison=rec_pick, n_objective_disagreements=n_diff)


    print("=" * 118)
    print("E6 -- CROSS-WINDOW PARAMETER TRANSFER")
    print("=" * 118)
    g5 = json.load(open(OUT / "t26_H4_5pos.json"))
    grows = g5["rows"]
    note(sorted({r["pos"] for r in grows}) == POS,
         f"t26_H4_5pos.json covers {sorted({r['pos'] for r in grows})}, not {POS}")

    GRID = [(f, b) for f in FAMILY_ORDER for b in BUCKET_ORDER]
    gidx = {c: i for i, c in enumerate(GRID)}
    gorder = np.array([gidx[c] for c in GRID])
    note(GRID[0] == FROZEN_GROUPING, "the frozen grouping must be tie-break priority 0")


    def grid_values(rows, key, seed):
        """value[w][c] for one seed, NaN where the row is missing."""
        lut = {(r["pos"], r["family"], r["bucket_s"]): r for r in rows if r["seed"] == seed}
        V = np.full((len(POS), len(GRID)), np.nan)
        for w, p in enumerate(POS):
            for c, (f, b) in enumerate(GRID):
                r = lut.get((p, f, b))
                if r is not None and r.get(key) is not None:
                    V[w, c] = r[key]
        return V


    def grid_feasible(rows, seed):
        """feas[w][c].  Feasibility is CEIL*w0/T - 1 >= 0, a function of |C|, k and T only"""
        lut = {(r["pos"], r["family"], r["bucket_s"]): r for r in rows if r["seed"] == seed}
        F = np.zeros((len(POS), len(GRID)), bool)
        for w, p in enumerate(POS):
            for c, (f, b) in enumerate(GRID):
                r = lut.get((p, f, b))
                F[w, c] = bool(r is not None and r["feasible"])
        return F


    res_grouping = {}
    for seed in SEEDS:
        V = grid_values(grows, OBJ, seed)
        R = grid_values(grows, "addis_recall", seed)
        F = grid_feasible(grows, seed)
        miss = int(np.isnan(V).sum())
        print(f"\n\n{'#'*118}\nGROUPING AXIS, detector seed {seed}   "
              f"({len(GRID)} configs, {miss} missing cells, "
              f"{int(F.sum())}/{F.size} feasible cells)\n{'#'*118}")
        res_grouping[str(seed)] = run_axis(f"grouping (family x bucket), seed {seed}",
                                           GRID, gorder, V, R, FROZEN_GROUPING, obj_label=OBJ,
                                           alt_label="addis_recall", feas=F)

    Vo = grid_values(grows, OBJ_ORACLE, 0)
    Fo = grid_feasible(grows, 0)
    print(f"\n\n{'#'*118}\nGROUPING AXIS under {OBJ_ORACLE} [ORACLE], seed 0\n{'#'*118}")
    res_oracle = run_axis(f"grouping, e-LOND + horizon-uniform gamma [ORACLE], seed 0",
                          GRID, gorder, Vo, grid_values(grows, "elond_recall", 0),
                          FROZEN_GROUPING, obj_label=OBJ_ORACLE, alt_label="elond_recall",
                          feas=Fo)
    out["grouping_oracle_control"] = res_oracle

    print("\n" + "=" * 118)
    print("[D6a] THE FEASIBILITY GATE IS NOT A TUNED PARAMETER -- BUT DOES ITS SET MOVE?")
    print("=" * 118)
    feas = {}
    for seed in SEEDS:
        lut = {(r["pos"], r["family"], r["bucket_s"]): r for r in grows if r["seed"] == seed}
        for w, p in enumerate(POS):
            s = frozenset(c for c in GRID
                          if lut.get((p,) + c) is not None and lut[(p,) + c]["feasible"])
            feas[(seed, p)] = s
    print(f"  {'window':>8} {'seed':>5} {'feasible':>9} {'|C|':>12} {'T of frozen':>12} "
          f"{'margin of frozen':>17}")
    for seed in SEEDS:
        for p in POS:
            lut = {(r["pos"], r["family"], r["bucket_s"]): r for r in grows if r["seed"] == seed}
            fr = lut[(p,) + FROZEN_GROUPING]
            print(f"  {p:>8.2f} {seed:>5} {len(feas[(seed,p)]):>9} {fr['NC']:>12,} "
                  f"{fr['T']:>12,} {fr['margin']:>17.4f}")
    base = feas[(0, POS[0])]
    sym = {p: len(feas[(0, p)] ^ base) for p in POS}
    print(f"\n  symmetric difference of the feasible set against window {POS[0]} (seed 0): "
          f"{ {p: sym[p] for p in POS} }")
    allfeas = frozenset.intersection(*[feas[(s, p)] for s in SEEDS for p in POS])
    neverfeas = [c for c in GRID if not any(c in feas[(s, p)] for s in SEEDS for p in POS)]
    print(f"  feasible at EVERY window and seed: {len(allfeas)} of {len(GRID)} configs")
    print(f"  feasible at NO window: {len(neverfeas)} -- {neverfeas}")
    note(FROZEN_GROUPING in allfeas, "the frozen grouping is not feasible at every window")
    print(f"  the frozen grouping {FROZEN_GROUPING} is feasible everywhere: "
          f"{FROZEN_GROUPING in allfeas}")
    out["feasibility"] = dict(
        n_feasible={f"{s}_{p}": len(feas[(s, p)]) for s in SEEDS for p in POS},
        sym_diff_vs_first={str(p): sym[p] for p in POS},
        n_always_feasible=len(allfeas), n_never_feasible=len(neverfeas),
        never_feasible=[list(map(str, c)) for c in neverfeas],
        frozen_always_feasible=bool(FROZEN_GROUPING in allfeas))

    c5 = json.load(open(OUT / "t25_H5.json"))
    crows = c5["rows"]
    note(sorted({r["pos"] for r in crows}) == POS, "t25_H5.json does not cover the five positions")
    CGRID = list(CAP_ORDER)
    corder = np.arange(len(CGRID))
    note(CGRID[0] == FROZEN_CAP, "the frozen cap must be tie-break priority 0")


    def cap_values(rows, key, seed):
        lut = {(r["pos"], r["cap"]): r for r in rows if r["seed"] == seed}
        V = np.full((len(POS), len(CGRID)), np.nan)
        for w, p in enumerate(POS):
            for c, cap in enumerate(CGRID):
                r = lut.get((p, cap))
                if r is not None and r.get(key) is not None:
                    V[w, c] = r[key]
        return V


    res_cap = {}
    import collections as _c
    _na = _c.defaultdict(set)
    for r in crows:
        _na[(r["pos"], r["seed"])].add(r["n_att_ep"])
    note(all(len(v) == 1 for v in _na.values()),
         "n_att_ep varies across caps -- det_trunc/n_att_ep is then not comparable [D3a]")

    for seed in SEEDS:
        D = cap_values(crows, "det_trunc", seed)
        NA = cap_values(crows, "n_att_ep", seed)
        V = D / NA
        ALT = cap_values(crows, "det_raw", seed) / NA
        print(f"\n\n{'#'*118}\nCAP AXIS, detector seed {seed}   ({len(CGRID)} caps)\n{'#'*118}")

        def _costs(seed=seed):
            vf = cap_values(crows, "viol_frac", seed)
            fl = cap_values(crows, "frontload_med", seed)
            n0 = cap_values(crows, "n0", seed)
            print(f"\n  the two costs a power-only selection ignores")
            print(f"  {'window':>8} " + " ".join(f"{c:>10}" for c in CGRID))
            for lbl, arr, fmt in (("n0", n0, "{:>10,.0f}"),
                                  ("raw-rule violating group share", vf, "{:>10.4f}"),
                                  ("median front-load cost (flows)", fl, "{:>10,.0f}")):
                print(f"  {lbl}")
                for w, p in enumerate(POS):
                    print(f"  {p:>8.2f} " + " ".join(fmt.format(arr[w, c])
                                                     for c in range(len(CGRID))))
            print(f"  -> the record's n0 = {FROZEN_CAP} is the choice of section 4.12, made for "
                  f"raw-rule validity and\n     front-load cost, NOT for power.  A power-only "
                  f"selection picks a much smaller cap and\n     pays for it on both of these "
                  f"axes; the numbers above are what it pays.")

        res_cap[str(seed)] = run_axis(f"cap n0, seed {seed}", CGRID, corder, V, ALT, FROZEN_CAP,
                                      obj_label="det_trunc/n_att_ep",
                                      alt_label="det_raw/n_att_ep", extra_print=_costs)

    out["grouping"] = res_grouping
    out["cap"] = res_cap

    print("\n" + "=" * 118)
    print("SUMMARY -- WORST CASE, NOT MEAN  [D7a]")
    print("=" * 118)
    print("  Rows whose SELECTION window was flat are excluded from the transfer columns: the")
    print("  selection there is a tie-break, not an optimisation, so the resulting regret says")
    print("  nothing about transferability.  They are still counted and reported separately,")
    print("  because an operator would still have had to deploy something.\n")
    for label, res in (("grouping", res_grouping), ("cap", res_cap),
                       ("grouping[ORACLE]", {"0": res_oracle})):
        for seed in (SEEDS if label != "grouping[ORACLE]" else [0]):
            for mode in ("E6a", "E6b"):
                rr = res[str(seed)][mode]
                ok = [r for r in rr if r["transfer_defined"]]
                deg = [r for r in rr if not r["transfer_defined"]]
                wr = max((r["regret"] for r in ok), default=None)
                rhos = [r["rho"] for r in ok if r["rho"] is not None]
                wf = max(r["frozen_regret"] for r in rr)
                frhos = [r["frozen_rho"] for r in rr if r["frozen_rho"] is not None]
                nworst = sum(1 for r in rr if r["frozen_is_worst"])
                print(f"  {label:>16} seed {seed} {mode}:  "
                      f"transfer over {len(ok)}/{len(rr)} usable folds: worst regret "
                      f"{'n/a' if wr is None else format(wr, '.4f')} "
                      f"(rho {max(rhos) if rhos else float('nan'):.3f});  "
                      f"FROZEN worst regret {wf:.4f} "
                      f"(rho {max(frhos) if frhos else float('nan'):.3f}), and the frozen "
                      f"config is the worst FEASIBLE one on {nworst}/{len(rr)} folds;  "
                      f"max tied {max(r['n_tied'] for r in rr)}"
                      + (f";  {len(deg)} fold(s) had a flat selection window" if deg else ""))

    out["assertions_failed"] = FAIL
    json.dump(out, open(OUT / "t39_E6.json", "w"), indent=1, allow_nan=True)
    print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t39_E6.json")
    if FAIL:
        print("  ASSERTIONS FAILED:")
        for m in FAIL:
            print("   -", m)
        raise SystemExit(1)
    print("  all derivation assertions held")

    return out


if __name__ == "__main__":
    main()
