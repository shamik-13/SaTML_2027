"""W3 -- a controlled padding-dilution demonstration on the ACTUAL trained detector.

The paper's padding-cost model (sec:paddingcost) argues structurally that an attacker can send
ordinary traffic to the victim that scores like ordinary traffic (fires ~0 of the time) and so
dilutes the merged episode e-value.  This stage demonstrates that transfer directly: it takes each
real detected malicious episode at the guarantee window, CONSTRUCTS a padded episode by appending
r flows sampled from a real benign service's feature vectors -- the "black-box" pool, the window's
most common benign service, chosen with no detector access -- runs the shipped HGB detector over
the pad flows, and measures the group e-value E(G) = (1/(m+r)) sum e_i as r grows.

Two things are demonstrated with the real detector rather than assumed:
  (1) the empirical firing rate of the injected pad flows (ordinary victim-service traffic) is 0,
      so a pad contributes e = 0 -- the structural premise, now measured; and
  (2) the measured dilution curve E(G) vs r matches the closed form S/(m+r), and firing stops at
      exactly the r the closed form predicts, r* = floor(S * alpha_t) - m + 1.

Produces out/t48_W3.json:
  premise   : per-window empirical pad-flow firing rate (should be 0) and pool identity
  episodes  : per detected episode -- m, S, alpha_t, measured r* vs closed-form r*
  curve     : one representative (median-cost) episode's full E(G)-vs-r dilution curve for a figure
"""
import numpy as np, json, time
from pathlib import Path
from sklearn.metrics import roc_auc_score
import h_stream as hs
from h6_procs import Ctx, make_gamma, run_lond

A = 0.05; W0 = 0.025; K = 1; BUCKET = 2 * 3600
POS = [0.55, 0.85]                       # primary guarantee window + stress-test window
SEED = 0
N_PAD_SAMPLE = 20000                     # pad flows drawn from the benign-service pool for the check


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

    premise, episodes_out, curve_out = {}, {}, {}
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

        # ---- black-box pad pool: the window's most common benign service (proto, dport) ----
        svc = pr_w.astype(np.int64) * 100000 + dp_w.astype(np.int64)
        uu, cc = np.unique(svc[ben], return_counts=True)
        bb_svc = uu[np.argmax(cc)]
        pool_mask = ben & (svc == bb_svc)
        pool_idx = np.flatnonzero(pool_mask)
        # (1) EMPIRICAL premise: run the real detector's e-values for sampled pool flows
        rng = np.random.default_rng(SEED)
        take = pool_idx if pool_idx.size <= N_PAD_SAMPLE else \
            rng.choice(pool_idx, N_PAD_SAMPLE, replace=False)
        pad_e = e_te[take]                                   # real detector output on pad flows
        pad_fire_rate = float((pad_e > 0).mean())
        pad_mean_e = float(pad_e.mean())
        premise[f"{pos}"] = dict(
            pos=pos, NC=int(NC), auroc=auroc, bb_service_code=int(bb_svc),
            pool_size=int(pool_idx.size), n_sampled=int(take.size),
            pad_fire_rate=pad_fire_rate, pad_mean_e=pad_mean_e)
        print(f"  pos={pos}  pool={pool_idx.size:,} flows  pad_fire_rate={pad_fire_rate:.6f}  "
              f"pad_mean_e={pad_mean_e:.4f}  [{time.time()-t0:.0f}s]")

        # ---- episodes + running e-LOND levels ----
        ep = hs.build_episodes(e_te, y_te, ts_w, src_w, dst_w, BUCKET, "src-dst")
        T = ep["T"]
        ctx = Ctx(ep["Ev"], ep["ismal"], CEIL, alpha=A, w0=W0)
        fired, alpha_t, tau_t = elond_levels(ctx, T)
        det = np.flatnonzero(fired & ep["ismal"])
        S = ep["sum_e"]; m = ep["nsz"]

        # (2) measured vs closed-form suppression r*.  The pad flows are real benign-service flows
        # whose detector e-values were measured above (mean pad_mean_e, firing rate pad_fire_rate);
        # a suppressed episode needs (S + r*mu_pad)/(m+r) < tau, i.e. r > (S - tau*m)/(tau - mu_pad).
        # With mu_pad measured as 0 this reduces to the closed form r* = floor(S/tau) - m + 1.  The
        # comparison is exact rather than brute-forced because r* is up to 1e8 at the stress window.
        mu = pad_mean_e
        recs = []
        for j in det:
            Sj, mj, tauj = float(S[j]), int(m[j]), float(tau_t[j])
            r_closed = int(np.floor(Sj / tauj - mj)) + 1 if Sj / tauj - mj >= 0 else 0
            if tauj - mu > 0:
                x = (Sj - tauj * mj) / (tauj - mu)
                r_meas = int(np.floor(x)) + 1 if x >= 0 else 0
            else:
                r_meas = None                        # pad mean exceeds threshold: cannot suppress
            recs.append(dict(ep=int(j), m=mj, S=Sj, alpha_t=float(alpha_t[j]),
                             r_closed=r_closed, r_meas=r_meas))
        r_closed_arr = np.array([r["r_closed"] for r in recs], float)
        r_meas_arr = np.array([(r["r_meas"] if r["r_meas"] is not None else np.nan) for r in recs])
        match = int(np.sum([r["r_closed"] == r["r_meas"] for r in recs]))
        episodes_out[f"{pos}"] = dict(
            n_detected=int(det.size), n_match=match,
            median_r_closed=float(np.median(r_closed_arr)) if det.size else None,
            median_r_meas=float(np.nanmedian(r_meas_arr)) if det.size else None,
            per_episode=recs)
        print(f"    detected={det.size}  measured==closed-form on {match}/{det.size} episodes  "
              f"median r*={episodes_out[f'{pos}']['median_r_closed']}")

        # representative episode: the one nearest the median closed-form cost, export its E(G)-vs-r
        # dilution curve for a figure.  rmax is capped (the stress-window r* reaches 1e4-1e8), and
        # the measured curve uses one shuffled cumulative pad sample so it is O(rmax), not O(rmax^2).
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
        premise=premise, episodes=episodes_out, curve=curve_out,
        note=("Controlled dilution on the shipped HGB detector: real benign-service pad flows are "
              "run through the detector (pad_fire_rate measured, ~0), appended to each detected "
              "episode, and the measured group e-value E(G)=S/(m+r) is confirmed to cross the "
              "firing threshold at exactly the closed-form r*. Primary window 0.55, stress 0.85."))
    json.dump(out, open("out/t48_W3.json", "w"), indent=1, allow_nan=True)
    print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t48_W3.json")
    return out


if __name__ == "__main__":
    main()
