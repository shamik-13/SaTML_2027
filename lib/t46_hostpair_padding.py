

def main():
    import numpy as np, json, time
    from pathlib import Path

    import h_stream as hs

    OUT = Path(__file__).resolve().parent / "out"
    OUT.mkdir(exist_ok=True)
    t0 = time.time()

    POS = [0.55, 0.62, 0.70, 0.77, 0.85]
    SEEDS = [0, 1]
    W0 = 0.025; K = 1; BUCKET = 2 * 3600
    out = {"config": dict(pos=POS, seeds=SEEDS, k=K, w0=W0, bucket_s=BUCKET)}
    FAIL = []


    def note(cond, msg):
        if not cond:
            FAIL.append(msg)
            print(f"    *** ASSERTION FAILED: {msg}")
        return cond


    print("=" * 112)
    print("THE FEATURE SET -- can a score depend on the host pair at all?")
    print("=" * 112)
    FEATURE_NAMES = [
        "Protocol",
        "Flow Duration", "Flow Bytes/s", "Flow Packets/s", "Tot Fwd Pkts", "Tot Bwd Pkts",
        "Total Length of Fwd Packet", "Total Length of Bwd Packet",
        "Fwd Packet Length Min", "Fwd Packet Length Max", "Fwd Packet Length Mean",
        "Fwd Packet Length Std", "Bwd Packet Length Min", "Bwd Packet Length Max",
        "Bwd Packet Length Mean", "Bwd Packet Length Std",
        "Flow IAT Mean", "Flow IAT Min", "Flow IAT Max", "Flow IAT Stddev",
        "Fwd IAT Min", "Fwd IAT Max", "Fwd IAT Mean", "Fwd IAT Std", "Fwd IAT Tot",
        "Bwd IAT Min", "Bwd IAT Max", "Bwd IAT Mean", "Bwd IAT Std", "Bwd IAT Tot",
        "Fwd PSH flags", "Bwd PSH flags", "Fwd URG flags",
    ]
    note(len(FEATURE_NAMES) == len(hs._FEAT),
         f"feature-name list has {len(FEATURE_NAMES)} entries, h_stream._FEAT has {len(hs._FEAT)}")
    IDENTITY = ("ip", "addr", "src", "dst", "port", "host", "mac", "id", "subnet", "prefix")
    offend = [n for n in FEATURE_NAMES
              if any(tok in n.lower().replace("fwd", "").replace("bwd", "") for tok in IDENTITY)]
    print(f"  {len(FEATURE_NAMES)} features, all per-flow timing / volume / protocol statistics")
    print(f"  features naming an endpoint identity: {offend if offend else 'NONE'}")
    note(not offend, f"a feature names an endpoint identity: {offend}")
    src_used_in_fit = "src" in hs._FEAT or "dst" in hs._FEAT
    note(not src_used_in_fit, "src/dst appear in the fitted feature set")
    print(f"  src/dst/ports enter the pipeline only through build_episodes' grouping key, never")
    print(f"  through fit_detector -- so a flow's SCORE is invariant to which host pair it is on.")
    out["feature_set"] = dict(n_features=len(FEATURE_NAMES), names=FEATURE_NAMES,
                              identity_features=offend,
                              score_invariant_to_host_pair=bool(not offend))

    print("\n" + "=" * 112)
    print("IS A HOST-PAIR-MATCHED PADDING POOL AVAILABLE?  (all five windows x two seeds)")
    print("=" * 112)
    X, y, ts, src, dst = hs.load()
    N = len(y)
    print(f"  {'window':>8} {'seed':>5} {'detected':>9} {'pairs 100% malicious':>21} "
          f"{'benign flows on pair: med':>26} {'>= 35 available':>16}")
    rows = []
    for pos in POS:
        i1, i2, i3 = hs.split_indices(N, pos)
        y_te = y[i2:i3]
        sw, dw = src[i2:i3], dst[i2:i3]
        ben = (y_te == 0)
        for seed in SEEDS:
            score = hs.fit_detector(X, y, i1, seed=seed, kind="hgb", verbose=False)
            s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
            e_te, cal, NC, CEIL = hs.evalues(s_cal, y[i1:i2], s_te, k=K)
            ep = hs.build_episodes(e_te, y_te, ts[i2:i3], sw, dw, BUCKET, "src-dst")
            T = ep["T"]; tau = T / W0
            det = np.nonzero(ep["ismal"] & (ep["Ev"] >= tau))[0]
            if not len(det):
                rows.append(dict(pos=pos, seed=seed, n_detected=0))
                print(f"  {pos:>8.2f} {seed:>5} {0:>9} {'—':>21} {'—':>26} {'—':>16}")
                continue
            inv = np.empty(T, dtype=np.int64); inv[ep["order"]] = np.arange(T)
            ep_of_flow = inv[ep["gid"]]
            avail, pure = [], 0
            for j in det:
                k0 = np.flatnonzero(ep_of_flow == j)
                a, b = int(sw[k0[0]]), int(dw[k0[0]])
                if j == det[0]:
                    note(bool((sw[k0] == a).all() and (dw[k0] == b).all()),
                         f"an episode spans more than one host pair at pos={pos} seed={seed}")
                on_pair = (sw == a) & (dw == b)
                avail.append(int((on_pair & ben).sum()))
                if int((on_pair & (y_te == 1)).sum()) == int(on_pair.sum()):
                    pure += 1
            avail = np.array(avail)
            rows.append(dict(pos=pos, seed=seed, n_detected=int(len(det)),
                             n_pairs_all_malicious=int(pure),
                             benign_on_pair_median=float(np.median(avail)),
                             benign_on_pair_max=int(avail.max()),
                             n_with_35_available=int((avail >= 35).sum())))
            print(f"  {pos:>8.2f} {seed:>5} {len(det):>9} {f'{pure} of {len(det)}':>21} "
                  f"{np.median(avail):>26,.0f} {int((avail>=35).sum()):>16}")
    out["rows"] = rows

    done = [r for r in rows if r["n_detected"]]
    tot_det = sum(r["n_detected"] for r in done)
    tot_pure = sum(r["n_pairs_all_malicious"] for r in done)
    tot_avail = sum(r["n_with_35_available"] for r in done)
    print(f"\n  Over {len(done)} (window, seed) cells and {tot_det} detected episodes:")
    print(f"    host pairs that are 100% malicious            : {tot_pure} of {tot_det}")
    print(f"    episodes with >= 35 benign flows on their pair : {tot_avail} of {tot_det}")
    note(tot_pure == tot_det, "some attack host pair carries benign traffic -- a host-pair-matched "
                              "pool IS available and should be priced")
    out["summary"] = dict(n_cells=len(done), n_detected=tot_det,
                          n_pairs_all_malicious=tot_pure,
                          n_with_pool_available=tot_avail,
                          empirical_route_closed=bool(tot_pure == tot_det))


    out["assertions_failed"] = FAIL
    json.dump(out, open(OUT / "t46_hostpair.json", "w"), indent=1)
    print(f"\n  wrote out/t46_hostpair.json")
    if FAIL:
        print("  ASSERTIONS FAILED:")
        for m in FAIL:
            print("   -", m)
        raise SystemExit(1)
    print("  all assertions held")

    return out


if __name__ == "__main__":
    main()
