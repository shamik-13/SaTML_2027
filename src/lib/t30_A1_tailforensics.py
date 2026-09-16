"""A1 -- forensics of the position-0.85 extreme-tail benign flows."""


def main():
    import numpy as np, json, time, gc, csv, datetime as dt
    from pathlib import Path
    from sklearn.metrics import roc_auc_score

    import h_stream as hs
    import h_meta as hm
    from h6_procs import Ctx, make_gamma, run_lond, run_addis

    NARR = Path(__file__).resolve().parent / "data" / "lspr23_attacknarratives.json"


    def _compromise_ips():
        """IPv4 addresses the Locked Shields red team's own task record names as compromised."""
        import re as _re
        out = set()
        for line in open(NARR):
            if not line.strip():
                continue
            r = json.loads(line)
            for c in (r.get("Content") or []):
                c = c.strip()
                if not c.startswith("{"):
                    continue
                try:
                    d = json.loads(c)
                except Exception:
                    continue
                out.update(i for i in (d.get("IPs") or [])
                           if _re.fullmatch(r"\d+\.\d+\.\d+\.\d+", i))
        return out

    Path("out").mkdir(exist_ok=True)
    t0 = time.time()

    POS_ALL = [0.55, 0.62, 0.70, 0.77, 0.85]
    SEEDS = [0, 1]
    DEEP_POS = 0.85
    K = 1
    A = 0.05
    W0 = 0.025
    BUCKET = 2 * 3600
    CAT_FIELDS = ["service", "conn", "dport", "sport", "l3l4", "seg_src", "seg_dst",
                  "ext_src", "ext_dst", "label_src", "label_dst"]

    out = {"config": dict(positions=POS_ALL, seeds=SEEDS, deep_pos=DEEP_POS, k=K, alpha=A,
                          w0=W0, bucket_s=BUCKET)}

    X, y, ts, src, dst = hs.load()
    N = len(y)
    meta, cats = hm.load()
    hm.verify(meta, src, dst)
    print(f"  [h_meta] alignment verified against h_stream host codes  [{time.time()-t0:.0f}s]")

    _chk = np.random.default_rng(1).choice(N, min(3_000_000, N), replace=False)
    ident = bool(np.array_equal((y[_chk] == 1),
                                (meta["label_src"][_chk] == 1) | (meta["label_dst"][_chk] == 1)))
    print(f"  Label == (Label_src==1 or Label_dst==1) on a 3M-row sample: {ident}")
    out["label_decomposition_identity"] = ident

    def _svc_key(service, dport):
        """Collision-free (service, dport) key.  dport is -1 when the field is empty, so the"""
        d = np.asarray(dport, dtype=np.int64)
        if (d < -1).any() or (d > 65535).any():
            raise ValueError("dport outside [-1, 65535]")
        return np.asarray(service, dtype=np.int64) * 65537 + (d + 1)


    mal = y == 1
    attack_src = np.unique(src[mal])
    attack_dst = np.unique(dst[mal])
    _i2_all = hs.split_indices(N, DEEP_POS)[1]
    _pre = np.zeros(N, bool); _pre[:_i2_all] = True
    attack_src_pre = np.unique(src[mal & _pre])
    attack_dst_pre = np.unique(dst[mal & _pre])
    del _pre
    print(f"  attack sources {len(attack_src):,} ({len(attack_src_pre):,} before the window)  "
          f"attack destinations {len(attack_dst):,} ({len(attack_dst_pre):,})  "
          f"[{time.time()-t0:.0f}s]")


    def _voidkeys(rows_a, rows_b):
        """np.unique codes for the 33-feature vectors of two row sets, computed jointly so the"""
        def _k(r):
            Z = np.ascontiguousarray(np.asarray(X[r], dtype=np.float32)) + 0.0
            return Z.view(np.dtype((np.void, Z.dtype.itemsize * Z.shape[1]))).ravel()
        ka, kb = _k(rows_a), _k(rows_b)
        _, inv = np.unique(np.concatenate([ka, kb]), return_inverse=True)
        return inv[:len(ka)], inv[len(ka):]


    print("\n" + "=" * 112)
    print("A1a -- BENIGN FIRING RATE BY WINDOW POSITION (k = 1); nominal = 1/(|C|+1)")
    print("=" * 112)
    print(f"  {'pos':>5} {'seed':>5} {'AUROC':>7} {'|C|':>12} {'benign te':>12} {'fired':>7} "
          f"{'measured':>11} {'nominal':>11} {'ratio':>8} {'mal fired':>10}")
    KGRID = [1, 10, 100, 1000, 10_000, 100_000]
    rate_rows = []
    depth_rows = []
    deep = {}
    for pos in POS_ALL:
        i1, i2, i3 = hs.split_indices(N, pos)
        for sd in SEEDS:
            score = hs.fit_detector(X, y, i1, seed=sd, kind="hgb", verbose=False)
            s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
            y_cal, y_te_ = y[i1:i2], y[i2:i3]
            e_te, cal, NC, CEIL = hs.evalues(s_cal, y_cal, s_te, k=K)
            ben = y_te_ == 0
            nb = int(ben.sum())
            fired = e_te > 0
            nfb = int((fired & ben).sum())
            nfm = int((fired & ~ben).sum())
            meas = nfb / nb
            nom = K / (NC + 1.0)
            auroc = float(roc_auc_score(y_te_, s_te))
            rate_rows.append(dict(pos=pos, seed=sd, auroc=auroc, NC=int(NC), n_benign=nb,
                                  n_fired_benign=nfb, n_fired_malicious=nfm,
                                  measured=float(meas), nominal=float(nom),
                                  ratio=float(meas / nom), Ee=float(CEIL * meas)))
            print(f"  {pos:>5.2f} {sd:>5} {auroc:>7.4f} {NC:>12,} {nb:>12,} {nfb:>7,} "
                  f"{meas:>11.3e} {nom:>11.3e} {meas/nom:>8.2f} {nfm:>10,}")
            rk = 1 + (NC - np.searchsorted(cal, s_te[ben], side='left'))
            drow = dict(pos=pos, seed=sd)
            for kk in KGRID:
                mm = float((rk <= kk).mean()); nn = kk / (NC + 1.0)
                drow[f"k{kk}"] = mm / nn
            depth_rows.append(drow)
            del rk
            if pos == DEEP_POS:
                deep[sd] = dict(i1=i1, i2=i2, i3=i3, s_cal=s_cal, s_te=s_te, e_te=e_te,
                                cal=cal, NC=NC, CEIL=CEIL, auroc=auroc)
            else:
                del s_cal, s_te, e_te, cal
            gc.collect()
    out["firing_rates"] = rate_rows
    print(f"  [{time.time()-t0:.0f}s]")

    print("\n" + "=" * 112)
    print("A1b -- IS THE EXCESS ONLY AT k = 1?  measured/nominal P(rank <= k), benign test flows")
    print("=" * 112)
    print(f"  {'pos':>5} {'seed':>5} " + " ".join(f"{f'k={kk}':>10}" for kk in KGRID))
    for drow in depth_rows:
        print(f"  {drow['pos']:>5.2f} {drow['seed']:>5} "
              + " ".join(f"{drow[f'k{kk}']:>10.2f}" for kk in KGRID))
    out["rank_depth"] = depth_rows
    print("\n  A ratio that decays towards 1 as k grows means a small number of extreme outliers;")
    print("  a ratio flat in k means the whole benign score distribution has moved.")
    print("  Ranks use side='left', so tied scores are ranked conservatively and the null is")
    print("  P(rank <= k) <= k/(|C|+1).  Every ratio below is therefore a LOWER bound on the")
    print("  anti-conservatism, which is the safe direction for the conclusion drawn from it.")
    print(f"  [{time.time()-t0:.0f}s]")

    i1, i2, i3 = hs.split_indices(N, DEEP_POS)
    w = slice(i2, i3)
    y_te = y[w]; ts_w = ts[w]; src_w = src[w]; dst_w = dst[w]
    meta_w = {c: meta[c][w] for c in hm._COLS}
    ip_src = hm.ip_table(meta, cats, src, "src")
    ip_dst = hm.ip_table(meta, cats, dst, "dst")
    ben_w = y_te == 0
    comp = {}

    for sd in SEEDS:
        d = deep[sd]
        tail = np.flatnonzero((d["e_te"] > 0) & ben_w)
        base = np.flatnonzero(ben_w)
        print("\n" + "=" * 112)
        print(f"A1c -- COMPOSITION OF THE EXTREME TAIL, position {DEEP_POS}, seed {sd}: "
              f"{len(tail):,} benign flows with s(x) > max cal score")
        print("=" * 112)
        c = dict(n_tail=int(len(tail)), n_benign_window=int(len(base)))
        if len(tail) == 0:
            print("  no benign flow fired at this seed; nothing to characterise")
            comp[sd] = c
            continue
        tpath = f"out/a1_extreme_tail_seed{sd}.csv"
        _mts = ts_w[~ben_w]
        with open(tpath, "w", newline="") as fh:
            wr = csv.writer(fh)
            wr.writerow(["row_in_window", "utc", "ts_us", "src", "dst", "sport", "dport",
                         "proto_l3l4", "conn", "service", "seg_src", "seg_dst", "ext_src",
                         "ext_dst", "score", "score_minus_cal_max",
                         "sec_to_nearest_malicious_flow"])
            for j in tail:
                if len(_mts):
                    _p = np.searchsorted(_mts, ts_w[j]); _c = []
                    if _p > 0: _c.append(ts_w[j] - _mts[_p - 1])
                    if _p < len(_mts): _c.append(_mts[_p] - ts_w[j])
                    _n = min(_c) / 1e6
                else:
                    _n = float("nan")
                wr.writerow([int(j),
                             dt.datetime.fromtimestamp(ts_w[j] / 1e6, dt.timezone.utc)
                               .strftime("%Y-%m-%d %H:%M:%S"),
                             int(ts_w[j]), str(ip_src[src_w[j]]), str(ip_dst[dst_w[j]]),
                             int(meta_w["sport"][j]), int(meta_w["dport"][j]),
                             int(meta_w["l3l4"][j]), cats["conn"][meta_w["conn"][j]],
                             cats["service"][meta_w["service"][j]],
                             cats["seg_src"][meta_w["seg_src"][j]],
                             cats["seg_dst"][meta_w["seg_dst"][j]],
                             int(meta_w["ext_src"][j]), int(meta_w["ext_dst"][j]),
                             f"{d['s_te'][j]:.6f}", f"{d['s_te'][j] - d['cal'][-1]:.6f}",
                             f"{_n:.1f}"])
        c["tail_csv"] = tpath
        print(f"  full listing written to {tpath}")

        def _conc(vals_tail, vals_base, name, decode=None, top=6):
            ut, ct = np.unique(vals_tail, return_counts=True)
            o = np.argsort(-ct)
            ub, cb = np.unique(vals_base, return_counts=True)
            bmap = dict(zip(ub.tolist(), cb.tolist()))
            rows = []
            for j in o[:top]:
                v = int(ut[j]); n_t = int(ct[j]); n_b = bmap.get(v, 0)
                rows.append(dict(value=(decode(v) if decode else v), n_tail=n_t,
                                 share_tail=n_t / len(vals_tail),
                                 n_benign=n_b, share_benign=n_b / len(vals_base),
                                 fire_rate=(n_t / n_b if n_b else float('nan')),
                                 enrichment=((n_t / len(vals_tail)) / (n_b / len(vals_base))
                                             if n_b else float('inf'))))
            share = np.sort(ct)[::-1] / len(vals_tail)
            n90 = int(np.searchsorted(np.cumsum(share), 0.90) + 1)
            return dict(field=name, n_distinct_tail=int(len(ut)),
                        n_distinct_benign=int(len(ub)),
                        top1_share=float(share[0]), hhi=float((share ** 2).sum()),
                        n_values_for_90pct=n90, top=rows)

        conc = [_conc(src_w[tail], src_w[base], "srcip", lambda v: str(ip_src[v])),
                _conc(dst_w[tail], dst_w[base], "dstip", lambda v: str(ip_dst[v]))]
        _ND = int(dst_w.max()) + 1
        if (int(src_w.max()) + 1) * _ND > (1 << 62):
            raise OverflowError("src/dst pair key does not fit in int64")
        pair_t = src_w[tail].astype(np.int64) * _ND + dst_w[tail]
        pair_b = src_w[base].astype(np.int64) * _ND + dst_w[base]
        conc.append(_conc(pair_t, pair_b, "src->dst pair",
                          lambda v: f"{ip_src[v // _ND]}->{ip_dst[v % _ND]}"))
        for f in CAT_FIELDS:
            dec = (lambda v, f=f: cats[f][v]) if f in hm._STR else None
            conc.append(_conc(meta_w[f][tail], meta_w[f][base], f, dec))
        c["concentration"] = conc
        for cc in conc:
            print(f"\n  by {cc['field']}: {cc['n_distinct_tail']:,} distinct in the tail "
                  f"(of {cc['n_distinct_benign']:,} in benign traffic), top-1 share "
                  f"{100*cc['top1_share']:.1f}%, HHI {cc['hhi']:.3f}, "
                  f"{cc['n_values_for_90pct']} values cover 90%")
            print(f"    {'value':>34} {'tail':>7} {'%tail':>7} {'benign':>11} {'%benign':>8} "
                  f"{'fire rate':>11} {'enrich':>9}")
            for r in cc["top"]:
                print(f"    {str(r['value'])[:34]:>34} {r['n_tail']:>7,} "
                      f"{100*r['share_tail']:>6.1f}% {r['n_benign']:>11,} "
                      f"{100*r['share_benign']:>7.2f}% {r['fire_rate']:>11.3e} "
                      f"{r['enrichment']:>9.1f}")

        c["attack_host_overlap"] = {}
        print(f"\n  attack-host overlap (host codes seen on a labelled-malicious flow)")
        for scope, a_s, a_d in (("whole stream", attack_src, attack_dst),
                                ("before the window only", attack_src_pre, attack_dst_pre)):
            in_as = np.isin(src_w[tail], a_s); in_ad = np.isin(dst_w[tail], a_d)
            b_as = np.isin(src_w[base], a_s); b_ad = np.isin(dst_w[base], a_d)
            o = dict(tail_src_is_attack_source=float(in_as.mean()),
                     base_src_is_attack_source=float(b_as.mean()),
                     tail_dst_is_attack_target=float(in_ad.mean()),
                     base_dst_is_attack_target=float(b_ad.mean()),
                     tail_either=float((in_as | in_ad).mean()),
                     base_either=float((b_as | b_ad).mean()))
            c["attack_host_overlap"][scope] = o
            print(f"    [{scope}]")
            print(f"      tail src is an attack source : {100*o['tail_src_is_attack_source']:6.2f}%   "
                  f"benign baseline {100*o['base_src_is_attack_source']:6.2f}%")
            print(f"      tail dst is an attack target : {100*o['tail_dst_is_attack_target']:6.2f}%   "
                  f"benign baseline {100*o['base_dst_is_attack_target']:6.2f}%")
            print(f"      tail touches either          : {100*o['tail_either']:6.2f}%   "
                  f"benign baseline {100*o['base_either']:6.2f}%")

        mts = ts_w[~ben_w]
        def _near(idx):
            if not len(mts): return np.full(len(idx), np.nan)
            p = np.searchsorted(mts, ts_w[idx])
            lo = np.where(p > 0, ts_w[idx] - mts[np.maximum(p - 1, 0)], np.iinfo(np.int64).max)
            hi = np.where(p < len(mts), mts[np.minimum(p, len(mts) - 1)] - ts_w[idx],
                          np.iinfo(np.int64).max)
            return np.minimum(lo, hi) / 1e6
        rng = np.random.default_rng(20260826 + sd)
        samp = rng.choice(base, min(200_000, len(base)), replace=False)
        nt, nb_ = _near(tail), _near(samp)
        span = (ts_w[-1] - ts_w[0]) / 1e6
        tfrac = (ts_w[tail] - ts_w[0]) / max(ts_w[-1] - ts_w[0], 1)
        bfrac = (ts_w[samp] - ts_w[0]) / max(ts_w[-1] - ts_w[0], 1)
        c["temporal"] = dict(window_span_s=float(span),
                             tail_sec_to_nearest_malicious=dict(
                                 p10=float(np.percentile(nt, 10)), median=float(np.median(nt)),
                                 p90=float(np.percentile(nt, 90))),
                             benign_sec_to_nearest_malicious=dict(
                                 p10=float(np.percentile(nb_, 10)), median=float(np.median(nb_)),
                                 p90=float(np.percentile(nb_, 90))),
                             tail_decile_counts=np.histogram(tfrac, bins=10, range=(0, 1))[0].tolist(),
                             benign_decile_share=(np.histogram(bfrac, bins=10, range=(0, 1))[0]
                                                  / len(samp)).tolist())
        tt = c["temporal"]
        print(f"\n  temporal (window spans {span/3600:.2f} h)")
        print(f"    seconds to nearest malicious flow -- tail   p10/med/p90 = "
              f"{tt['tail_sec_to_nearest_malicious']['p10']:.1f} / "
              f"{tt['tail_sec_to_nearest_malicious']['median']:.1f} / "
              f"{tt['tail_sec_to_nearest_malicious']['p90']:.1f}")
        print(f"    seconds to nearest malicious flow -- benign p10/med/p90 = "
              f"{tt['benign_sec_to_nearest_malicious']['p10']:.1f} / "
              f"{tt['benign_sec_to_nearest_malicious']['median']:.1f} / "
              f"{tt['benign_sec_to_nearest_malicious']['p90']:.1f}")
        print(f"    tail count by window decile: {tt['tail_decile_counts']}")
        print(f"    benign share by decile:      "
              f"{[round(x,3) for x in tt['benign_decile_share']]}")

        rows_tail = np.arange(i2, i3)[tail]
        mal_rows = np.flatnonzero(mal)
        kt, km = _voidkeys(rows_tail, mal_rows)
        hit_mal = np.isin(kt, km)
        cal_ben = np.arange(i1, i2)[y[i1:i2] == 0]
        if len(cal_ben) > 4_000_000:
            cal_ben = np.sort(np.random.default_rng(7).choice(cal_ben, 4_000_000, replace=False))
        kt2, kc = _voidkeys(rows_tail, cal_ben)
        hit_cal = np.isin(kt2, kc)
        _, dup_cnt = np.unique(kt, return_counts=True)
        c["collisions"] = dict(
            tail_identical_to_a_malicious_flow=float(hit_mal.mean()),
            n_tail_identical_to_malicious=int(hit_mal.sum()),
            tail_identical_to_a_calibration_benign_flow=float(hit_cal.mean()),
            cal_benign_sampled=int(len(cal_ben)),
            distinct_feature_vectors_in_tail=int(len(dup_cnt)),
            largest_repeated_vector=int(dup_cnt.max()) if len(dup_cnt) else 0)
        cc = c["collisions"]
        print(f"\n  exact 33-feature-vector collisions")
        print(f"    tail flows byte-identical to some MALICIOUS flow  : "
              f"{cc['n_tail_identical_to_malicious']:,} "
              f"({100*cc['tail_identical_to_a_malicious_flow']:.2f}%)")
        print(f"    tail flows byte-identical to a CALIBRATION benign : "
              f"{100*cc['tail_identical_to_a_calibration_benign_flow']:.2f}%  "
              f"(of {cc['cal_benign_sampled']:,} sampled)")
        print(f"    distinct vectors in the tail: {cc['distinct_feature_vectors_in_tail']:,}; "
              f"largest repeat {cc['largest_repeated_vector']:,}")

        cal_slice = slice(i1, i2)
        cal_ben_mask = y[cal_slice] == 0
        seen_src = np.unique(src[cal_slice][cal_ben_mask])
        seen_dst = np.unique(dst[cal_slice][cal_ben_mask])
        seen_svc = np.unique(_svc_key(meta["service"][cal_slice][cal_ben_mask],
                                      meta["dport"][cal_slice][cal_ben_mask]))
        t_sv = _svc_key(meta_w["service"][tail], meta_w["dport"][tail])
        b_sv = _svc_key(meta_w["service"][base], meta_w["dport"][base])
        c["novelty"] = dict(
            tail_src_unseen_in_calibration=float((~np.isin(src_w[tail], seen_src)).mean()),
            base_src_unseen_in_calibration=float((~np.isin(src_w[base], seen_src)).mean()),
            tail_dst_unseen_in_calibration=float((~np.isin(dst_w[tail], seen_dst)).mean()),
            base_dst_unseen_in_calibration=float((~np.isin(dst_w[base], seen_dst)).mean()),
            tail_service_port_unseen=float((~np.isin(t_sv, seen_svc)).mean()),
            base_service_port_unseen=float((~np.isin(b_sv, seen_svc)).mean()))
        nv = c["novelty"]
        print(f"\n  novelty relative to the benign calibration window")
        print(f"    src host unseen in calibration      : tail {100*nv['tail_src_unseen_in_calibration']:6.2f}%"
              f"   benign {100*nv['base_src_unseen_in_calibration']:6.2f}%")
        print(f"    dst host unseen in calibration      : tail {100*nv['tail_dst_unseen_in_calibration']:6.2f}%"
              f"   benign {100*nv['base_dst_unseen_in_calibration']:6.2f}%")
        print(f"    (service, dport) unseen             : tail {100*nv['tail_service_port_unseen']:6.2f}%"
              f"   benign {100*nv['base_service_port_unseen']:6.2f}%")

        cal = d["cal"]; s_t = d["s_te"][tail]
        gap = s_t - cal[-1]
        spacing = float(cal[-1] - cal[-2]) if len(cal) >= 2 else float("nan")
        iqr = float(np.percentile(cal, 75) - np.percentile(cal, 25))
        c["score_gap"] = dict(cal_max=float(cal[-1]), top_spacing=spacing, cal_iqr=iqr,
                              gap_median=float(np.median(gap)), gap_p90=float(np.percentile(gap, 90)),
                              gap_median_in_spacings=float(np.median(gap) / spacing) if spacing > 0 else None,
                              gap_median_in_iqr=float(np.median(gap) / iqr) if iqr > 0 else None,
                              frac_gap_below_one_spacing=float((gap <= spacing).mean()))
        sg = c["score_gap"]
        print(f"\n  how far past the ceiling: cal max {sg['cal_max']:.3f}, gap to it median "
              f"{sg['gap_median']:.3f} = {sg['gap_median_in_spacings']:.1f}x the top calibration "
              f"spacing, {sg['gap_median_in_iqr']:.3f}x the calibration IQR")
        print(f"    fraction of tail flows within one top-order-statistic spacing of the ceiling: "
              f"{100*sg['frac_gap_below_one_spacing']:.1f}%")
        comp[sd] = c

    out["composition"] = comp
    print(f"\n  [{time.time()-t0:.0f}s]")

    print("\n" + "=" * 112)
    print("A1e -- EXTERNAL CORROBORATION: are the extreme-tail flows attack traffic?")
    print("=" * 112)
    cips = _compromise_ips()
    comp_s = np.array([ip_src[c] in cips for c in range(len(ip_src))])
    comp_d = np.array([ip_dst[c] in cips for c in range(len(ip_dst))])
    touch_w = comp_s[src_w] | comp_d[dst_w]
    print(f"  red-team confirmed-compromise IPv4 addresses: {len(cips)}")
    print(f"  benign window flows touching one of them: {int((touch_w & ben_w).sum()):,} of "
          f"{int(ben_w.sum()):,} ({100*float((touch_w & ben_w).mean() / ben_w.mean()):.2f}%)")
    ext = {}
    for sd in SEEDS:
        d = deep[sd]
        tail = np.flatnonzero((d["e_te"] > 0) & ben_w)
        if not len(tail):
            continue
        hit = touch_w[tail]
        base_rate = float((d["e_te"][ben_w] > 0).mean())
        clean = ben_w & ~touch_w
        fr_clean = float((d["e_te"][clean] > 0).mean())
        nom = K / (d["NC"] + 1.0)
        ext[sd] = dict(n_tail=int(len(tail)), n_tail_touching_compromise=int(hit.sum()),
                       share=float(hit.mean()),
                       base_share=float((touch_w & ben_w).sum() / ben_w.sum()),
                       fire_rate_all_benign=base_rate, fire_rate_uncompromised=fr_clean,
                       nominal=float(nom), ratio_all=float(base_rate / nom),
                       ratio_uncompromised=float(fr_clean / nom),
                       Ee_all=float(d["e_te"][ben_w].mean()),
                       Ee_uncompromised=float(d["e_te"][clean].mean()))
        e = ext[sd]
        print(f"\n  seed {sd}: {e['n_tail_touching_compromise']} of {e['n_tail']} tail flows "
              f"({100*e['share']:.1f}%) touch a confirmed-compromise host,")
        print(f"          against a {100*e['base_share']:.2f}% base rate among benign window flows "
              f"-- enrichment {e['share']/max(e['base_share'],1e-12):.0f}x")
        print(f"    benign firing rate, all benign flows            : {e['fire_rate_all_benign']:.3e}"
              f"  = {e['ratio_all']:6.2f}x nominal,  E[e|benign] = {e['Ee_all']:7.2f}")
        print(f"    benign firing rate, excluding compromised hosts : {e['fire_rate_uncompromised']:.3e}"
              f"  = {e['ratio_uncompromised']:6.2f}x nominal,  E[e|benign] = {e['Ee_uncompromised']:7.2f}")
    out["external_corroboration"] = dict(n_compromise_ips=len(cips), by_seed=ext)
    print("\n  This exclusion uses the red team's documentation, not the labels being audited and")
    print("  not the test-split scores.  Note it is barely enriched over the base rate: a")
    print("  confirmed-compromise host also sends a great deal of ordinary traffic, so host")
    print("  identity alone does not adjudicate these flows.")

    print("\n  [ORACLE] how much of the inflation lives in how few host pairs:")
    _ND2 = int(dst_w.max()) + 1
    pair_w = src_w.astype(np.int64) * _ND2 + dst_w
    conc_rows = []
    for sd in SEEDS:
        d = deep[sd]
        tail = np.flatnonzero((d["e_te"] > 0) & ben_w)
        if not len(tail):
            continue
        up, cp = np.unique(pair_w[tail], return_counts=True)
        o = np.argsort(-cp)
        nom = K / (d["NC"] + 1.0)
        row = dict(seed=sd, n_tail=int(len(tail)), n_pairs_in_tail=int(len(up)),
                   n_pairs_in_window=int(len(np.unique(pair_w[ben_w]))), steps=[])
        for npair in (1, 2, 3, 5):
            if npair > len(up):
                break
            drop = up[o[:npair]]
            keep = ben_w & ~np.isin(pair_w, drop)
            fr = float((d["e_te"][keep] > 0).mean())
            row["steps"].append(dict(pairs_dropped=npair,
                                     tail_covered=int(cp[o[:npair]].sum()),
                                     benign_flows_left=int(keep.sum()),
                                     fire_rate=fr, ratio=float(fr / nom),
                                     Ee=float(d["e_te"][keep].mean()),
                                     names=[f"{ip_src[int(v)//_ND2]}->{ip_dst[int(v)%_ND2]}"
                                            for v in drop]))
            print(f"    seed {sd}: drop the top {npair} pair(s) "
                  f"({cp[o[:npair]].sum()} of {len(tail)} tail flows, "
                  f"{100*cp[o[:npair]].sum()/len(tail):.0f}%) -> firing rate {fr:.3e} = "
                  f"{fr/nom:5.2f}x nominal, E[e|benign] = {d['e_te'][keep].mean():6.2f}")
            for nmm in row["steps"][-1]["names"][-1:]:
                pass
        print(f"      pairs dropped, in order: "
              + ", ".join(row["steps"][-1]["names"]))
        conc_rows.append(row)
    out["pair_concentration"] = conc_rows
    print(f"\n  For comparison, the other four window positions measure 1.07-3.79x nominal.")
    print("\n  The pair exclusion above is [ORACLE] -- the pairs are chosen from the test-split")
    print("  score tail, so it measures how LOCALISED the cause is and is not a deployable fix.")

    print("\n" + "=" * 112)
    print("A1d -- REPAIRS: what restores E[e] <= 1, and what it costs")
    print("=" * 112)


    def run_stream(e_te_, y_te_, CEIL_, label):
        """Episode stream + e-LOND (horizon-uniform) and ADDIS (poly), as in section 4.20."""
        ep = hs.build_episodes(e_te_, y_te_, ts_w, src_w, dst_w, BUCKET, "src-dst")
        T = ep["T"]
        ctx = Ctx(ep["Ev"], ep["ismal"], CEIL_, alpha=A, w0=W0)
        g1p, g0p = make_gamma("poly", T)
        g1u, _ = make_gamma("uniform", T)
        res = {}
        for nm, fn, gam, kw in (("e-LOND/uniform", run_lond, g1u, {}),
                                ("ADDIS/poly", run_addis, g0p, dict(lam=0.25, tau_=0.5))):
            m = np.zeros(T, bool)
            rej, tp, sil, first = fn(ctx, gam, fired=m, **kw)
            res[nm] = dict(rejections=int(rej), tp=int(tp),
                           fdp=(float(1 - tp / rej) if rej else None),
                           recall=float(tp / ep["n_mal"]) if ep["n_mal"] else 0.0,
                           silent=float(sil / T))
        return dict(label=label, T=int(T), n_mal=int(ep["n_mal"]),
                    margin=float((CEIL_) * W0 / T - 1.0), procedures=res)


    def mondrian(s_cal_, y_cal_, s_te_, strat_cal, strat_te, k=1):
        """Mondrian (stratified) split-conformal: rank each test flow only against calibration"""
        cb = strat_cal[y_cal_ == 0]
        sb = s_cal_[y_cal_ == 0]
        order = np.lexsort((sb, cb))
        cb_s, sb_s = cb[order], sb[order]
        uniq, start = np.unique(cb_s, return_index=True)
        end = np.append(start[1:], len(cb_s))
        e = np.zeros(len(s_te_)); ceil_of = np.zeros(len(s_te_))
        pos = np.searchsorted(uniq, strat_te)
        ok = pos < len(uniq)
        if ok.any():
            ok[ok] &= uniq[pos[ok]] == strat_te[ok]
        n_uncal = int((~ok).sum())
        for j in np.unique(pos[ok]):
            rows = np.flatnonzero(ok & (pos == j))
            if not len(rows): continue
            seg = sb_s[start[j]:end[j]]; ns = len(seg)
            ce = (ns + 1.0) / k
            rk = 1 + (ns - np.searchsorted(seg, s_te_[rows], side='left'))
            e[rows] = np.where(rk <= k, ce, 0.0)
            ceil_of[rows] = ce
        return e, ceil_of, n_uncal


    repairs = {}
    for sd in SEEDS:
        d = deep[sd]
        print(f"\n  --- seed {sd} " + "-" * 90)
        r = {}
        base_rate = float((d["e_te"][ben_w] > 0).mean())
        r["baseline"] = dict(fire_rate=base_rate, Ee=float(d["e_te"][ben_w].mean()),
                             stream=run_stream(d["e_te"], y_te, d["CEIL"], "baseline"))
        print(f"    baseline                       fire rate {base_rate:.3e}  "
              f"E[e|benign] = {r['baseline']['Ee']:8.2f}  "
              f"T={r['baseline']['stream']['T']:,} margin={r['baseline']['stream']['margin']:+.3f}")
        for nm, res in r["baseline"]["stream"]["procedures"].items():
            print(f"      {nm:>16}: {res['rejections']:>4} alerts  FDP "
                  f"{('%.3f' % res['fdp']) if res['fdp'] is not None else '  -  '}  "
                  f"recall {res['recall']:.3f}  silent {100*res['silent']:.1f}%")

        for field in ("service", "conn"):
            st_cal = meta[field][slice(i1, i2)]
            st_te = meta_w[field]
            e_m, ceil_of, n_unc = mondrian(d["s_cal"], y[i1:i2], d["s_te"], st_cal, st_te, k=K)
            fr = float((e_m[ben_w] > 0).mean())
            Ee = float(e_m[ben_w].mean())
            cmax = float(ceil_of.max())
            stream = run_stream(e_m, y_te, cmax, f"mondrian-{field}")
            cap_ep = hs.build_episodes(ceil_of, y_te, ts_w, src_w, dst_w, BUCKET,
                                       "src-dst")["Ev"]
            Tm = stream["T"]
            stream["margin_note"] = ("global-max ceiling; see margin_min / margin_median for "
                                     "the per-episode values")
            stream["margin_min"] = float(cap_ep.min() * W0 / Tm - 1.0)
            stream["margin_median"] = float(np.median(cap_ep) * W0 / Tm - 1.0)
            r[f"mondrian_{field}"] = dict(fire_rate=fr, Ee=Ee, n_uncalibrated=n_unc,
                                          max_ceiling=cmax, min_ceiling=float(ceil_of.min()),
                                          stream=stream)
            print(f"    Mondrian by {field:<18} fire rate {fr:.3e}  E[e|benign] = {Ee:8.2f}  "
                  f"uncalibrated {n_unc:,}  ceiling {ceil_of.min():,.0f}..{cmax:,.0f}  "
                  f"margin/episode {stream['margin_min']:+.3f}..{stream['margin_median']:+.3f}")
            for nm, res in stream["procedures"].items():
                print(f"      {nm:>16}: {res['rejections']:>4} alerts  FDP "
                      f"{('%.3f' % res['fdp']) if res['fdp'] is not None else '  -  '}  "
                      f"recall {res['recall']:.3f}  silent {100*res['silent']:.1f}%")

        cand = []
        tail = np.flatnonzero((d["e_te"] > 0) & ben_w)
        if not len(tail):
            r["oracle_exclusion"] = None
            repairs[sd] = r
            print("    [ORACLE] no tail at this seed; exclusion not defined")
            continue
        for field in ("service", "conn", "dport", "seg_src", "seg_dst"):
            v, cnt = np.unique(meta_w[field][tail], return_counts=True)
            j = int(np.argmax(cnt))
            cand.append((float(cnt[j]) / len(tail), field, int(v[j])))
        cand.sort(key=lambda z: (-z[0], z[1], z[2]))
        share, field, val = cand[0]
        keep_te = meta_w[field] != val
        keep_cal = meta[field][slice(i1, i2)] != val
        s_cal2 = d["s_cal"][keep_cal]; y_cal2 = y[i1:i2][keep_cal]
        e2, cal2, NC2, CEIL2 = hs.evalues(s_cal2, y_cal2, d["s_te"][keep_te], k=K)
        ben2 = y_te[keep_te] == 0
        fr2 = float((e2[ben2] > 0).mean())
        ep2 = hs.build_episodes(e2, y_te[keep_te], ts_w[keep_te], src_w[keep_te],
                                dst_w[keep_te], BUCKET, "src-dst")
        ctx2 = Ctx(ep2["Ev"], ep2["ismal"], CEIL2, alpha=A, w0=W0)
        g1u2, _ = make_gamma("uniform", ep2["T"])
        _, g0p2 = make_gamma("poly", ep2["T"])
        pr = {}
        for nm, fn, gam, kw in (("e-LOND/uniform", run_lond, g1u2, {}),
                                ("ADDIS/poly", run_addis, g0p2, dict(lam=0.25, tau_=0.5))):
            rej, tp, sil, first = fn(ctx2, gam, **kw)
            pr[nm] = dict(rejections=int(rej), tp=int(tp),
                          fdp=(float(1 - tp / rej) if rej else None),
                          recall=float(tp / ep2["n_mal"]) if ep2["n_mal"] else 0.0,
                          silent=float(sil / ep2["T"]))
        r["oracle_exclusion"] = dict(
            field=field, value=(cats[field][val] if field in hm._STR else val),
            share_of_tail=share, fire_rate=fr2, Ee=float(e2[ben2].mean()), NC=int(NC2),
            flows_dropped_test=int((~keep_te).sum()), flows_dropped_cal=int((~keep_cal).sum()),
            stream=dict(T=int(ep2["T"]), n_mal=int(ep2["n_mal"]),
                        margin=float(CEIL2 * W0 / ep2["T"] - 1.0), procedures=pr))
        print(f"    [ORACLE] drop {field}={r['oracle_exclusion']['value']!r} "
              f"({100*share:.1f}% of the tail): fire rate {fr2:.3e}  "
              f"E[e|benign] = {e2[ben2].mean():8.2f}  T={ep2['T']:,} "
              f"margin={r['oracle_exclusion']['stream']['margin']:+.3f}")
        for nm, res in pr.items():
            print(f"      {nm:>16}: {res['rejections']:>4} alerts  FDP "
                  f"{('%.3f' % res['fdp']) if res['fdp'] is not None else '  -  '}  "
                  f"recall {res['recall']:.3f}  silent {100*res['silent']:.1f}%")
        repairs[sd] = r

    out["repairs"] = repairs

    json.dump(out, open("out/t30_A1.json", "w"), indent=1, allow_nan=True, default=str)
    print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t30_A1.json")

    return out


if __name__ == "__main__":
    main()
