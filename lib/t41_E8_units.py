


def main():
    import numpy as np, json, time, math
    from pathlib import Path

    import ast, subprocess, sys
    import h_stream as hs

    _DERIV = Path(__file__).with_name("t41a_E8_derivation.py")


    def _load_from_derivation(*names):
        tree = ast.parse(_DERIV.read_text())
        want = {n.name: n for n in tree.body
                if isinstance(n, ast.FunctionDef) and n.name in names}
        consts = {n.targets[0].id: n for n in tree.body
                  if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
                  and n.targets[0].id in names}
        missing = set(names) - set(want) - set(consts)
        if missing:
            raise AssertionError(f"not module-level in {_DERIV.name}: {sorted(missing)}")
        ns = {"np": np, "math": math}
        body = [consts[n] if n in consts else want[n] for n in names]
        exec(compile(ast.fix_missing_locations(ast.Module(body=body, type_ignores=[])),
                     str(_DERIV), "exec"), ns)
        return [ns[n] for n in names]


    (COL, SCALES, recover_duration_scale, per_flow_cost, budget_cost,
     rate_and_hosts) = _load_from_derivation(
        "COL", "SCALES", "recover_duration_scale", "per_flow_cost", "budget_cost",
        "rate_and_hosts")

    print("  running t41a_E8_derivation.py before using its primitives ...")
    _p = subprocess.run([sys.executable, str(_DERIV)], cwd=str(_DERIV.parent),
                        capture_output=True, text=True)
    if _p.returncode != 0:
        print(_p.stdout[-3000:]); print(_p.stderr[-2000:])
        raise SystemExit("t41a_E8_derivation.py FAILED; refusing to convert units with it")
    print(f"    {[l for l in _p.stdout.splitlines() if 'PASSED' in l][-1].strip()}")

    OUT = Path(__file__).resolve().parent / "out"
    OUT.mkdir(exist_ok=True)
    t0 = time.time()

    POS = [0.62, 0.85]
    BUCKET = 2 * 3600
    HEADER_B = 40.0
    HOST_RATES = (1e6, 1e7, 1e8, 1e9)
    QUANTS = (0.10, 0.50, 0.90)

    _T28B = Path(__file__).resolve().parent / "out" / "t28b_reallevel.json"
    if not _T28B.exists():
        raise SystemExit("t28b_reallevel.json is required: it carries the running-level "
                         "medians this stage prices, under both within-bucket orders")
    _t28b_all = json.load(open(_T28B))
    _CANON = _t28b_all["config"]["canonical_order"]
    if _CANON != "keyhash":
        raise SystemExit(f"t28b's canonical order is {_CANON!r}, not 'keyhash'; the budget "
                         "labels below name the order explicitly and must be updated with it")

    def _runlevel(order):

        c = _t28b_all["table1_by_order"][order]["0.85_0"]
        if c.get("order") != order:
            raise SystemExit(f"t28b record filed under table1_by_order[{order!r}] declares "
                             f"order={c.get('order')!r}; the arms are mislabelled and every "
                             f"order claim downstream of this stage would be wrong")
        if c["pos"] != 0.85 or c["seed"] != 0:
            raise SystemExit(f"t28b record at ['{order}']['0.85_0'] is pos={c['pos']} "
                             f"seed={c['seed']}, not 0.85/0")
        if c["med_pad_real"] is None:
            raise SystemExit(f"t28b has no running-level median at 0.85 seed 0 under {order!r}")
        return int(round(float(c["med_pad_real"]))), int(c["detected_elond"])

    RUNLEVEL_085_CANON, NDET_085_CANON = _runlevel(_CANON)
    RUNLEVEL_085_FF, NDET_085_FF = _runlevel("first-flow")
    print(f"  [order] running-level median pad at 0.85 seed 0: "
          f"canonical({_CANON}) {RUNLEVEL_085_CANON:,} over {NDET_085_CANON} detections; "
          f"first-flow {RUNLEVEL_085_FF:,} over {NDET_085_FF} detections")

    BUDGETS = [
        dict(name="padding, one e-LOND episode at the RUNNING level (median, 0.85, canonical)",
             flows=RUNLEVEL_085_CANON, window_s=BUCKET,
             source=f"t28b_reallevel table1_by_order['{_CANON}']['0.85_0'].med_pad_real -- "
                    f"e-LOND running level 1/alpha_t at each of ITS OWN {NDET_085_CANON} "
                    f"detections under the CANONICAL within-bucket order, position 0.85 seed 0; "
                    f"this is the arm tab:main reports"),
        dict(name="padding, one e-LOND episode at the RUNNING level (median, 0.85)",
             flows=RUNLEVEL_085_FF, window_s=BUCKET,
             source=f"t28b_reallevel table1_by_order['first-flow']['0.85_0'].med_pad_real -- "
                    f"e-LOND running level 1/alpha_t at each of ITS OWN {NDET_085_FF} detections "
                    f"under FIRST-FLOW arrival, the optimistic upper bound, position 0.85 seed 0"),
        dict(name="padding, one episode (median)", flows=34, window_s=BUCKET,
             source="section 4.30, r_90 median over the 257 like-for-like episodes of positions "
                    "0.62+0.85 x 2 seeds, priced against the STATIC level-w0 threshold tau=T/w0"),
        dict(name="padding, one episode (p90)", flows=227, window_s=BUCKET,
             source="section 4.30, r_90 p90, same static level-w0 threshold and episode set"),
        dict(name="padding, all 147 ADDIS detections", flows=34 * 147, window_s=BUCKET,
             source="section 4.30's STATIC-threshold median x section 4.33's ADDIS detected-set "
                    "size (147) -- a mixed quantity, labelled as such in the table"),
        dict(name="padding at ADDIS's own level, one episode", flows=34_465_311,
             window_s=BUCKET, source="section 4.33 median_pad_per_episode"),
        dict(name="ADDIS spending-state attack", flows=92_015_637, window_s=None,
             source="section 4.33: B* = 203 precursors x 453,279 flows at |C|+1 = 1,813,114; "
                    "priced over this position's OWN deployment span"),
    ]

    for _b in BUDGETS:
        _b["order"] = (_CANON if _b["name"].endswith("canonical)") else
                       "first-flow" if "RUNNING level" in _b["name"] else None)
    out = {"config": dict(pos=POS, bucket_s=BUCKET, header_bytes_per_packet=HEADER_B,
                          host_rates_bps=list(HOST_RATES), quantiles=list(QUANTS),
                          orders=["first-flow", _CANON], canonical_order=_CANON,
                          budgets=[{k: v for k, v in b.items()} for b in BUDGETS],
                          derivation="t41a_E8_derivation.py")}
    FAIL = []


    def note(cond, msg):
        if not cond:
            FAIL.append(msg)
            print(f"    *** ASSERTION FAILED: {msg}")
        return cond



    note(abs(float(_t28b_all["table1"]["0.85_0"]["med_pad_real"]) - RUNLEVEL_085_FF) <= 0.5,
         f"t28b's default table1 at 0.85 seed 0 is {_t28b_all['table1']['0.85_0']['med_pad_real']}, "
         f"which is not its first-flow arm ({RUNLEVEL_085_FF}); the default arm changed")
    note(RUNLEVEL_085_CANON < RUNLEVEL_085_FF,
         f"canonical running-level cost {RUNLEVEL_085_CANON} is not below the first-flow upper "
         f"bound {RUNLEVEL_085_FF}; the 'optimistic order' framing would be wrong")
    print(f"  [xcheck] t28b default arm == first-flow arm at 0.85 seed 0 "
          f"({RUNLEVEL_085_FF:,} flows over {NDET_085_FF} detections)")
    X, y, ts, src, dst = hs.load()
    N = len(y)
    dport_all = hs.load_extra("dport")

    pool_rows, budget_rows = [], []
    for pos in POS:
        i1, i2, i3 = hs.split_indices(N, pos)
        y_te = y[i2:i3]
        Xw = np.asarray(X[i2:i3])
        dp_w = dport_all[i2:i3]
        pr_w = Xw[:, 0].astype(np.int32)

        dur = Xw[:, COL["duration"]].astype(float)
        tot_b = (Xw[:, COL["fwd_bytes"]].astype(float) + Xw[:, COL["bwd_bytes"]].astype(float))
        bps = Xw[:, COL["bytes_per_s"]].astype(float)
        scale_name, tbl, cov = recover_duration_scale(dur, tot_b, bps)
        ranked = sorted(tbl.items(), key=lambda kv: kv[1])
        print(f"\n  [D1a] duration-unit recovery at position {pos}:")
        for nm, v in ranked:
            print(f"        {nm:>14}: median |log10 ratio| = {v:.4f}"
                  + ("   <- selected" if nm == scale_name else ""))
        print(f"        recovered on {cov['n_used']:,} of {i3-i2:,} flows "
              f"({100*cov['frac_used']:.1f}% with positive duration, bytes and rate)")
        note(ranked[1][1] - ranked[0][1] >= 2.0,
             f"duration unit is ambiguous at pos={pos}: best {ranked[0]} vs {ranked[1]}")
        note(cov["frac_used"] >= 0.5,
             f"duration unit recovered on only {100*cov['frac_used']:.1f}% of flows at pos={pos}")
        S = SCALES[scale_name]
        dur_s = dur / S

        att_src = np.unique(src[i2:i3][y_te == 1])
        is_att_src = np.isin(src[i2:i3], att_src)
        ben = (y_te == 0)
        svc = pr_w.astype(np.int64) * 100000 + dp_w.astype(np.int64)
        uu, cc = np.unique(svc[ben], return_counts=True)
        bb_svc = uu[np.argmax(cc)]
        svc_ref = (np.asarray(X[:i1, 0]).astype(np.int64) * 100000
                   + dport_all[:i1].astype(np.int64))
        ref_ben = (y[:i1] == 0)
        uu_r, cc_r = np.unique(svc_ref[ref_ben], return_counts=True)
        bb_ref = uu_r[np.argmax(cc_r)]
        pools = {"generic benign": ben,
                 "attacker-origin": ben & is_att_src,
                 "black-box (most common benign service)": ben & (svc == bb_svc),
                 "black-box [service chosen on the TRAINING window]": ben & (svc == bb_ref)}
        print(f"  black-box service: proto {bb_svc//100000}/port {bb_svc%100000} chosen on the "
              f"deployment window, proto {bb_ref//100000}/port {bb_ref%100000} on the training "
              f"window -- {'SAME' if bb_svc == bb_ref else 'DIFFERENT'}")
        out.setdefault("blackbox_service", {})[str(pos)] = dict(
            deployment=int(bb_svc), training=int(bb_ref), same=bool(bb_svc == bb_ref))

        print(f"\n  position {pos}: per-flow cost of each padding pool  [{time.time()-t0:.0f}s]")
        print(f"  {'pool':>40} {'flows':>12} {'packets p10/med/p90':>24} "
              f"{'payload bytes p10/med/p90':>30} {'mean B':>10} {'dur med (s)':>12}")
        per_pos = {}
        for nm, mask in pools.items():
            rows_i = np.flatnonzero(mask)
            pk, by_pay = per_flow_cost(Xw, rows_i, 0.0)
            _, by_wire = per_flow_cost(Xw, rows_i, HEADER_B)
            qp = np.quantile(pk, QUANTS); qb = np.quantile(by_pay, QUANTS)
            per_pos[nm] = dict(pkts=pk, pay=by_pay, wire=by_wire)
            pool_rows.append(dict(pos=pos, pool=nm, n_flows=int(mask.sum()),
                                  pkts_q=[float(v) for v in qp],
                                  payload_q=[float(v) for v in qb],
                                  wire_q=[float(v) for v in np.quantile(by_wire, QUANTS)],
                                  pkts_mean=float(pk.mean()),
                                  payload_mean=float(by_pay.mean()),
                                  wire_mean=float(by_wire.mean()),
                                  duration_s_median=float(np.median(dur_s[rows_i])),
                                  duration_unit=scale_name))
            print(f"  {nm:>40} {mask.sum():>12,} "
                  f"{qp[0]:>6.0f}/{qp[1]:>6.0f}/{qp[2]:>7.0f} "
                  f"{qb[0]:>8.0f}/{qb[1]:>9.0f}/{qb[2]:>10.0f} {by_pay.mean():>10,.0f} "
                  f"{np.median(dur_s[rows_i]):>12.3f}")
        for nm in pools:
            r = [p for p in pool_rows if p["pos"] == pos and p["pool"] == nm][0]
            note(r["payload_mean"] > 0, f"empty pool {nm} at pos={pos}")

        span_s = (float(ts[i3 - 1]) - float(ts[i2])) / 1e6
        print(f"\n  position {pos}: deployment window spans {span_s:,.0f} s "
              f"({span_s/3600:.3f} h) and carries {i3-i2:,} flows")
        print(f"  position {pos}: the budgets, priced against each pool")
        for bud in BUDGETS:
            w = bud["window_s"] if bud["window_s"] is not None else span_s
            print(f"\n    {bud['name']}  --  {bud['flows']:,} flows"
                  + (f", over {w/3600:.2f} h" if w else ", window not bounded"))
            print(f"      {'pool':>40} {'packets (median flow)':>22} "
                  f"{'payload bytes':>16} {'wire bytes':>16} {'rate (bit/s)':>14} "
                  f"{'hosts @10 Mbit/s':>17}")
            for nm in pools:
                pk = per_pos[nm]["pkts"]; wire = per_pos[nm]["wire"]; pay = per_pos[nm]["pay"]
                bc_pay = budget_cost(pk, pay, bud["flows"], QUANTS)
                bc_wire = budget_cost(pk, wire, bud["flows"], QUANTS)
                row = dict(pos=pos, budget=bud["name"], flows=bud["flows"], pool=nm,
                           window_s=w, window_is_own_span=(bud["window_s"] is None),
                           iid_expected_bytes=bc_wire["iid_expected"]["bytes"],
                           typical_bytes=bc_wire["typical"]["bytes"],
                           chosen_min_bytes=bc_wire["chosen_min"]["bytes"],
                           chosen_sum_bytes=(None if bc_wire["chosen_sum"] is None
                                             else bc_wire["chosen_sum"]["bytes"]),
                           packets={str(q): bc_pay[q]["packets"] for q in QUANTS},
                           packets_mean=bc_pay["mean"]["packets"],
                           payload_bytes={str(q): bc_pay[q]["bytes"] for q in QUANTS},
                           payload_bytes_mean=bc_pay["mean"]["bytes"],
                           wire_bytes={str(q): bc_wire[q]["bytes"] for q in QUANTS},
                           wire_bytes_mean=bc_wire["mean"]["bytes"])
                if w:
                    rh = rate_and_hosts(bc_wire["typical"]["bytes"], w, HOST_RATES)
                    row.update(bits_per_s=rh["bits_per_s"], hosts=rh["hosts"])
                    note(abs(bc_pay[0.5]["bytes"]
                             - bud["flows"] * float(np.quantile(pay, 0.5))) < 1e-6,
                         f"budget_cost is not n * quantile at pos={pos} {bud['name']} {nm}")
                    print(f"      {nm:>40} {bc_pay[0.5]['packets']:>22,.0f} "
                          f"{bc_pay[0.5]['bytes']:>16,.0f} {bc_wire[0.5]['bytes']:>16,.0f} "
                          f"{rh['bits_per_s']:>14,.0f} {rh['hosts']['10000000']:>17,}")
                else:
                    print(f"      {nm:>40} {bc_pay[0.5]['packets']:>22,.0f} "
                          f"{bc_pay[0.5]['bytes']:>16,.0f} {bc_wire[0.5]['bytes']:>16,.0f} "
                          f"{'n/a':>14} {'n/a':>17}")
                budget_rows.append(row)
        n_window_flows = int(i3 - i2)
        print(f"\n  position {pos}: attack volume against the monitored population")
        print(f"      deployment window carries {n_window_flows:,} flows "
              f"({len(y):,} in the whole dataset)")
        for bud in BUDGETS:
            print(f"      {bud['name']:>44}: {bud['flows']:>14,} flows = "
                  f"{bud['flows']/n_window_flows:>12,.4f}x the window, "
                  f"{bud['flows']/len(y):>10,.4f}x the dataset")
        out.setdefault("volume_ratio", {})[str(pos)] = dict(
            n_window_flows=n_window_flows, n_dataset_flows=int(len(y)),
            ratios={b["name"]: dict(vs_window=b["flows"] / n_window_flows,
                                    vs_dataset=b["flows"] / len(y)) for b in BUDGETS})

        out.setdefault("duration_unit", {})[str(pos)] = dict(
            selected=scale_name, table=tbl, coverage=cov,
            margin_decades=float(ranked[1][1] - ranked[0][1]))
        out.setdefault("window_span_s", {})[str(pos)] = float(span_s)

    out["pools"] = pool_rows
    out["budgets_priced"] = budget_rows

    print("\n" + "=" * 118)
    print("THE SENTENCE E8 EXISTS TO PRODUCE")
    print("=" * 118)
    gb = [r for r in budget_rows if r["pool"] == "black-box (most common benign service)"
          and r["pos"] == 0.85]
    one = next(r for r in gb if r["budget"].startswith("padding, one episode (median)"))
    allep = next(r for r in gb if r["budget"].startswith("padding, all 147"))
    state = next(r for r in gb if r["budget"].startswith("ADDIS spending-state"))
    addis_pad = next(r for r in gb if r["budget"].startswith("padding at ADDIS's own level"))

    out["assertions_failed"] = FAIL
    json.dump(out, open(OUT / "t41_E8.json", "w"), indent=1, allow_nan=True)
    print(f"  [{time.time()-t0:.0f}s]  wrote out/t41_E8.json")
    if FAIL:
        print("  ASSERTIONS FAILED:")
        for m in FAIL:
            print("   -", m)
        raise SystemExit(1)
    print("  all derivation assertions held")

    return out


if __name__ == "__main__":
    main()
