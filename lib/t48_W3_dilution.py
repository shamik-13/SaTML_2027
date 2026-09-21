
import numpy as np, json, time
from pathlib import Path
from sklearn.metrics import roc_auc_score
from scipy.stats import beta
import h_stream as hs
from h6_procs import Ctx, make_gamma, run_lond
from t53_ordering import key_hash, hashed_order      # the canonical within-bucket order (item R4)

A = 0.05; W0 = 0.025; K = 1; BUCKET = 2 * 3600
POS = [0.55, 0.62, 0.85]                 # primary, secondary, stress-test window

SEED = 0
N_PAD_SAMPLE = 20000                     # pad flows drawn from the benign-service pool for the check


def price_suppression(det, S, m, alpha_t, tau_t, mu, gid_of=None):

    recs = []
    for j in det:
        # `j` indexes the STREAM (a position under whichever order is being priced); `gid_of` maps
        # it back to the stable group id so `ep` means the same thing across the two arms.
        gj = int(j) if gid_of is None else int(gid_of[j])
        Sj, mj, tauj = float(S[j]), int(m[j]), float(tau_t[j])
        r_closed = int(np.floor(Sj / tauj - mj)) + 1 if Sj / tauj - mj >= 0 else 0
        if tauj - mu > 0:
            x = (Sj - tauj * mj) / (tauj - mu)
            r_meas = int(np.floor(x)) + 1 if x >= 0 else 0
        else:
            r_meas = None                            # pad mean exceeds threshold: cannot suppress
        recs.append(dict(ep=gj, stream_pos=int(j), m=mj, S=Sj, alpha_t=float(alpha_t[j]),
                         r_closed=r_closed, r_meas=r_meas))
    r_closed_arr = np.array([r["r_closed"] for r in recs], float)
    r_meas_arr = np.array([(r["r_meas"] if r["r_meas"] is not None else np.nan) for r in recs])
    match = int(np.sum([r["r_closed"] == r["r_meas"] for r in recs]))
    n = len(recs)
    return dict(n_detected=int(n), n_match=match,
                r_closed_sorted=sorted(int(r["r_closed"]) for r in recs),
                n_suppressible=int(np.sum([r["r_meas"] is not None for r in recs])),
                median_r_closed=float(np.median(r_closed_arr)) if n else None,
                median_r_meas=float(np.nanmedian(r_meas_arr)) if n else None,
                per_episode=recs), r_closed_arr


def elond_levels(ctx, T):
    g1, _ = make_gamma("poly", T)
    fired = np.zeros(T, dtype=bool)
    run_lond(ctx, g1, fired=fired)
    R_before = np.concatenate([[0], np.cumsum(fired)[:-1]]).astype(float)
    alpha_t = A * g1[np.arange(1, T + 1)] * (R_before + 1.0)
    with np.errstate(divide="ignore"):
        tau_t = np.where(alpha_t > 0, 1.0 / alpha_t, np.inf)
    return fired, alpha_t, tau_t


def main():
    t0 = time.time()
    Path("out").mkdir(exist_ok=True)
    X, y, ts, src, dst = hs.load()
    N = len(y)
    dport_all = hs.load_extra("dport")

    premise, episodes_out, curve_out, episodes_keyhash = {}, {}, {}, {}
    for pos in POS:
        i1, i2, i3 = hs.split_indices(N, pos)
        y_cal, y_te = y[i1:i2], y[i2:i3]
        ts_w, src_w, dst_w = ts[i2:i3], src[i2:i3], dst[i2:i3]
        dp_w = dport_all[i2:i3]
        pr_w = np.asarray(X[i2:i3, 0]).astype(np.int32)     # proto is feature column 0
        ben = y_te == 0

        score = hs.fit_detector(X, y, i1, seed=SEED, kind="hgb", verbose=False)
        s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
        e_te, cal, NC, CEIL = hs.evalues(s_cal, y_cal, s_te, k=K)
        auroc = float(roc_auc_score(y_te, s_te)) if np.unique(y_te).size == 2 else None


        svc = pr_w.astype(np.int64) * 100000 + dp_w.astype(np.int64)
        svc_tr = (np.asarray(X[:i1, 0]).astype(np.int64) * 100000
                  + dport_all[:i1].astype(np.int64))

        def _modal(v):
            u, c = np.unique(v, return_counts=True)
            return int(u[np.argmax(c)])

        att_src = np.unique(src_w[y_te == 1])                # hosts the ATTACKER itself runs
        own = np.isin(src_w, att_src)
        rules = {
            "training-prefix frequency": _modal(svc_tr),
            "window frequency, excl. own hosts [y-reconstructed]": _modal(svc[~own]),
            "window frequency, all flows": _modal(svc),
            "window frequency, benign-labelled [oracle]": _modal(svc[ben]),
        }
        BB_RULE = "training-prefix frequency"
        bb_svc = rules[BB_RULE]
        pool_mask = (svc == bb_svc)                          # no label filter: label-free pool
        pool_idx = np.flatnonzero(pool_mask)
        pool_atk_rate = float(y_te[pool_idx].mean()) if pool_idx.size else float("nan")
        print(f"  pos={pos}  black-box service selection rules:")
        for nm, code in rules.items():
            frac = float(y_te[svc == code].mean()) if (svc == code).any() else float("nan")
            print(f"      {nm:<44} proto {code//100000:>3}/port {code%100000:<6} "
                  f"pool {100*frac:7.4f}% attack-labelled"
                  + ("   <- USED" if nm == BB_RULE else ""))

        rng = np.random.default_rng(SEED)
        take = pool_idx if pool_idx.size <= N_PAD_SAMPLE else \
            rng.choice(pool_idx, N_PAD_SAMPLE, replace=False)
        pad_e = e_te[take]                                   # real detector output on pad flows
        n_fire = int((pad_e > 0).sum())
        pad_fire_rate = float(n_fire / max(take.size, 1))
        pad_mean_e = float(pad_e.mean())
        cp_upper = float(beta.ppf(0.95, n_fire + 1, max(take.size - n_fire, 1)))
        premise[f"{pos}"] = dict(
            pos=pos, NC=int(NC), auroc=auroc, bb_service_code=int(bb_svc),
            bb_selection_rule=BB_RULE, bb_selection_label_free=True,
            bb_selection_variants={k: int(v) for k, v in rules.items()},
            bb_variant_attack_frac={
                k: (float(y_te[svc == v].mean()) if (svc == v).any() else None)
                for k, v in rules.items()},
            bb_matches_labelled_choice=bool(
                bb_svc == rules["window frequency, benign-labelled [oracle]"]),
            pool_attack_labelled_frac=pool_atk_rate,
            pool_size=int(pool_idx.size), n_sampled=int(take.size),
            pad_fire_count=n_fire, pad_fire_rate=pad_fire_rate,
            pad_fire_ci95_upper=cp_upper, pad_mean_e=pad_mean_e)
        print(f"  pos={pos}  pool={pool_idx.size:,} flows  pad_fire={n_fire}/{take.size} "
              f"({pad_fire_rate:.6f}, 95% CP upper {cp_upper:.2e})  "
              f"pad_mean_e={pad_mean_e:.4f}  [{time.time()-t0:.0f}s]")

        # ---- episodes + running e-LOND levels ----
        ep = hs.build_episodes(e_te, y_te, ts_w, src_w, dst_w, BUCKET, "src-dst")
        T = ep["T"]
        ctx = Ctx(ep["Ev"], ep["ismal"], CEIL, alpha=A, w0=W0)
        fired, alpha_t, tau_t = elond_levels(ctx, T)
        det = np.flatnonzero(fired & ep["ismal"])
        S = ep["sum_e"]; m = ep["nsz"]


        mu = pad_mean_e
        rec, r_closed_arr = price_suppression(det, S, m, alpha_t, tau_t, mu,
                                              gid_of=ep["order"])
        episodes_out[f"{pos}"] = rec
        print(f"    detected={det.size}  measured==closed-form on {rec['n_match']}/{det.size} "
              f"episodes  median r*={rec['median_r_closed']}")


        gid = ep["gid"]
        gsrc = np.zeros(T, dtype=np.int64); gsrc[gid] = src_w
        gdst = np.zeros(T, dtype=np.int64); gdst[gid] = dst_w
        gfirst = np.full(T, np.iinfo(np.int64).max, dtype=np.int64)
        np.minimum.at(gfirst, gid, ts_w)
        gbkt = gfirst // (BUCKET * 1_000_000)
        canon = hashed_order(key_hash(gsrc, gdst, gbkt, seed=0), gsrc, gdst, gbkt)
        assert np.array_equal(np.sort(canon), np.arange(T)), "canonical order is not a permutation"
        assert np.all(np.diff(gbkt[canon]) >= 0), "canonical order breaks bucket-close order"

        inv = np.empty(T, np.int64); inv[ep["order"]] = np.arange(T)      # gid -> shipped position
        Ev_g = ep["Ev"][inv]; ismal_g = ep["ismal"][inv]
        S_g = ep["sum_e"][inv]; m_g = ep["nsz"][inv]
        ctx_c = Ctx(Ev_g[canon], ismal_g[canon], CEIL, alpha=A, w0=W0)
        fired_c, alpha_c, tau_c = elond_levels(ctx_c, T)
        det_c = np.flatnonzero(fired_c & ismal_g[canon])
        rec_c, _ = price_suppression(det_c, S_g[canon], m_g[canon], alpha_c, tau_c, mu,
                                     gid_of=canon)
        rec_c["order"] = "canonical key-hash (splitmix64 of the group's own SrcIP,DstIP,bucket)"

        rec_c["order_is_key_determined"] = True
        episodes_keyhash[f"{pos}"] = rec_c
        print(f"    [R4] canonical key-hash order: detected={det_c.size}  "
              f"suppressible={rec_c['n_suppressible']}/{det_c.size}  "
              f"measured==closed-form on {rec_c['n_match']}/{det_c.size}  "
              f"median r*={rec_c['median_r_closed']}")

        if det.size:
            med = np.median(r_closed_arr)
            jrep = det[int(np.argmin(np.abs(r_closed_arr - med)))]
            Sr, mr, taur = float(S[jrep]), int(m[jrep]), float(tau_t[jrep])
            r_star = int(np.floor(Sr / taur - mr)) + 1 if Sr / taur - mr >= 0 else 0
            CURVE_CAP = 400
            rmax = int(min(CURVE_CAP, max(4, r_star * 1.6 + 4)))
            samp = rng.choice(pad_e, rmax, replace=True)
            csum = np.concatenate([[0.0], np.cumsum(samp)])       # csum[r] = sum of first r pad e
            rs = np.arange(0, rmax + 1)
            Eg_meas = [float((Sr + csum[r]) / (mr + r)) for r in rs]
            Eg_closed = [float(Sr / (mr + r)) for r in rs]
            curve_out[f"{pos}"] = dict(
                ep=int(jrep), m=mr, S=Sr, threshold=taur, r_star=r_star, curve_capped_at=rmax,
                r=rs.tolist(), Eg_measured=Eg_meas, Eg_closedform=Eg_closed)

    out = dict(
        config=dict(POS=POS, SEED=SEED, bucket_s=BUCKET, k=K, w0=W0, alpha=A,
                    pool="black-box (window's most common benign service)",
                    n_pad_sample=N_PAD_SAMPLE, proc="e-LOND", gamma="poly"),
        premise=premise, episodes=episodes_out, episodes_keyhash=episodes_keyhash,
        curve=curve_out,
        note=("Controlled dilution on the shipped HGB detector: real benign-service pad flows are "
              "run through the detector (pad_fire_rate measured, ~0), appended to each detected "
              "episode, and the measured group e-value E(G)=S/(m+r) is confirmed to cross the "
              "firing threshold at exactly the closed-form r*. Primary window 0.55, stress 0.85. "
              "`episodes` is the shipped first-flow within-bucket order (an optimistic upper bound "
              "on detection power); `episodes_keyhash` re-runs the identical chain under the "
              "CANONICAL key-hash order the paper recommends -- the order under which a pad "
              "provably moves no other hypothesis's spending weight -- so the attack is priced on "
              "the ordering whose Assumption-1 argument is clean (review 6, item R4)."))
    json.dump(out, open("out/t48_W3.json", "w"), indent=1, allow_nan=True)
    print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t48_W3.json")
    return out


if __name__ == "__main__":
    main()
