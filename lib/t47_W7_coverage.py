import numpy as np, json, time
from pathlib import Path
from sklearn.metrics import roc_auc_score
import h_stream as hs
from h6_procs import Ctx, make_gamma, run_lond

A = 0.05; W0 = 0.025; K = 1
ATOMIC_BUCKET = 300                      # 5-minute host-pair episodes = the fixed ground truth
POS = [0.55, 0.62, 0.70, 0.77, 0.85]     # all five windows (fig3 plots the blur across them)
SEED = 0
BUCKETS = [300, 1800, 3600, 7200, 21600, 86400]
FAMILIES = ["src-dst", "src", "dst", "subnet24", "src-dport"]


def _fired_flow_mask(ep, fired_ordered):

    fired_original = ep["order"][fired_ordered]
    return np.isin(ep["gid"], fired_original)


def main():
    t0 = time.time()
    Path("out").mkdir(exist_ok=True)
    X, y, ts, src, dst = hs.load()
    N = len(y)
    src24 = hs.load_extra("src24"); dst24 = hs.load_extra("dst24")
    dport = hs.load_extra("dport")

    denom = {}
    rows = []
    for pos in POS:
        i1, i2, i3 = hs.split_indices(N, pos)
        y_cal, y_te = y[i1:i2], y[i2:i3]
        ts_w = ts[i2:i3]
        mal_flow = y_te == 1
        fams = {"src-dst": [src[i2:i3], dst[i2:i3]],
                "src": [src[i2:i3]],
                "dst": [dst[i2:i3]],
                "subnet24": [src24[i2:i3], dst24[i2:i3]],
                "src-dport": [src[i2:i3], dport[i2:i3]]}

        score = hs.fit_detector(X, y, i1, seed=SEED, kind="hgb", verbose=False)
        s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
        e_te, cal, NC, CEIL = hs.evalues(s_cal, y_cal, s_te, k=K)
        auroc = float(roc_auc_score(y_te, s_te)) if np.unique(y_te).size == 2 else None

        # ---- fixed atomic ground truth: malicious 5-minute src-dst episodes ----
        atom = hs.build_episodes(e_te, y_te, ts_w, bucket_s=ATOMIC_BUCKET,
                                 keys=[src[i2:i3], dst[i2:i3]])
        atomic_gid = atom["gid"]                       # per-flow atomic episode id
        Ta = atom["T"]
        atom_mal = np.bincount(atomic_gid, weights=y_te.astype(float), minlength=Ta) > 0
        mal_atomic_ids = np.flatnonzero(atom_mal)      # the FIXED set of atomic malicious units
        D = int(mal_atomic_ids.size)
        denom[f"{pos}"] = D
        print(f"  pos={pos}  atomic malicious units (5-min src-dst) = {D}  "
              f"|C|={NC:,} AUROC={auroc:.4f}  [{time.time()-t0:.0f}s]")

        for fam, keys in fams.items():
            for b in BUCKETS:
                ep = hs.build_episodes(e_te, y_te, ts_w, bucket_s=b, keys=keys)
                T = ep["T"]
                margin = CEIL * W0 / T - 1.0
                ctx = Ctx(ep["Ev"], ep["ismal"], CEIL, alpha=A, w0=W0)
                g1p, _ = make_gamma("poly", T)
                fired = np.zeros(T, bool)
                rej, tp, silent, first = run_lond(ctx, g1p, fired=fired)

                # moving-denominator episode recall (denominator = this grouping's malicious eps)
                n_mal_ep = ctx.NMAL
                recall_moving = float(tp / n_mal_ep) if n_mal_ep else None

                # malicious-flow coverage (mass of malicious flows in fired episodes)
                mal_per_ep = np.bincount(ep["gid"], weights=y_te.astype(float),
                                         minlength=T)[ep["order"]]
                tot_mal = float(mal_per_ep.sum())
                flow_cov = float(mal_per_ep[fired].sum() / tot_mal) if tot_mal else None


                in_fired = _fired_flow_mask(ep, fired)
                sel = in_fired & mal_flow
                covered_ids = np.unique(atomic_gid[sel])
                covered_mal = np.intersect1d(covered_ids, mal_atomic_ids, assume_unique=False)
                cov_fixed = float(covered_mal.size / D) if D else None

                blur = None
                if sel.any():
                    coarse_of_flow = ep["gid"][sel]        # original coarse id per selected flow
                    atom_of_flow = atomic_gid[sel]
                    pair = np.unique(np.stack([coarse_of_flow, atom_of_flow], 1), axis=0)
                    per_alert = np.bincount(
                        np.unique(pair[:, 0], return_inverse=True)[1])
                    blur = float(per_alert.mean())

                rows.append(dict(
                    pos=pos, family=fam, bucket_s=b, T=int(T), n_mal_ep=int(n_mal_ep),
                    margin=float(margin), feasible=bool(margin >= 0.0),
                    elond_rej=int(rej), elond_tp=int(tp),
                    cov_fixed=cov_fixed, recall_moving=recall_moving, flow_cov=flow_cov,
                    blur_mal_atoms_per_alert=blur, covered_atomic=int(covered_mal.size)))
                print(f"    {fam:>9} b={b:>6}s  T={T:>7,}  feas={margin>=0!s:>5}  "
                      f"cov_fixed={cov_fixed:.3f}  recall_moving="
                      f"{('%.3f'%recall_moving) if recall_moving is not None else 'na':>6}  "
                      f"blur={('%.2f'%blur) if blur is not None else 'na':>6}  "
                      f"flow_cov={('%.3f'%flow_cov) if flow_cov is not None else 'na'}")

    out = dict(
        config=dict(POS=POS, SEED=SEED, FAMILIES=FAMILIES, BUCKETS=BUCKETS,
                    atomic_family="src-dst", atomic_bucket_s=ATOMIC_BUCKET, k=K, w0=W0, alpha=A,
                    proc="e-LOND", gamma="poly"),
        denom=denom, rows=rows,
        note=("cov_fixed = fraction of the FIXED 5-min src-dst malicious atomic units covered by "
              ">=1 issued e-LOND alert; the denominator (denom) does not change with the alerting "
              "grouping. recall_moving is the ordinary episode recall whose denominator DOES change "
              "with the grouping. Primary window 0.55, stress-test window 0.85; seed 0."))
    json.dump(out, open("out/t47_W7.json", "w"), indent=1, allow_nan=True)
    print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t47_W7.json")
    return out


if __name__ == "__main__":
    main()
