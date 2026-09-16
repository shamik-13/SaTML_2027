"""R-ordering -- the grouped-hypothesis stream is emitted at bucket close, and the headline
detection count is MATERIALLY SENSITIVE to the pre-committed within-bucket order (measured here).

Motivation (reviewer items 2-3).  A group's evidence uses every flow in its time bucket, so the
hypothesis cannot be decided until the bucket closes.  The controller therefore (i) orders hypotheses
by bucket-close time and (ii) breaks ties among groups closing in the same bucket by a PRE-COMMITTED,
evidence-independent rule.  There is thus NO causal look-ahead: no group is decided using a flow
outside its own closed bucket.

But the within-bucket tie-break is NOT innocuous, and first-flow arrival -- the order the pipeline
originally shipped -- is a POOR canonical choice for two reasons the second review makes precise:
(a) it gives the LARGEST detection count among evidence-independent orders (so headline numbers built
on it are the generous, detector-favouring end), and (b) it is ATTACKER-INFLUENCEABLE (the adversary
controls when its own episode first appears), so delaying an episode's first flow pushes it to a later,
lower-alpha_t slot -- an ordering/timing evasion lever distinct from padding.

We therefore make a DETERMINISTIC METADATA-HASH order (a splitmix64 hash of the raw
(SrcIP,DstIP,bucket) key itself, collisions broken on the key) the CANONICAL within-bucket order.
Being a function of the group's OWN key it is evidence-independent AND not timing-influenceable, so it
removes lever (b).  Detection POWER is then reported honestly as the median/IQR/range over N_RAND=50
fixed random pre-committed orders (an ensemble of legitimate tie-breaks), with first-flow reported only
as an OPTIMISTIC UPPER BOUND.  We also price the minimal padding suppression r* under every order to
confirm the ATTACK cost (median ~ a few hundred flows) is NOT an artefact of the favourable order.

What review 7 (item R3) adds:

 (iii) ALL FIVE positions and BOTH detector seeds, not just 0.55 and 0.85.  tab:main reports a
       detection count and a median padding cost at every window; until now there was no
       canonical-order number at 0.62, 0.70 or 0.77 at all, so the table could only be built on
       the first-flow order.  The canonical count and its padding costs are now measured at each.

 (iv)  The canonical order is no longer this stage's private construction.  h_stream owns the one
       definition and build_episodes(order="keyhash"|"keyed") ships it; this module re-exports it
       and ASSERTS at run time that its own `canonical`/`keyed` permutations equal what
       build_episodes returns.  The stage that measures order sensitivity and the stages that run
       under the canonical order therefore cannot drift.

Two things this version adds (review 5):

  (i)  A KEY-ONLY hash, not a hash of the group INDEX.  The index is the lexicographic rank of the
       packed key among the keys PRESENT, so it is only a function of the whole key set; hashing the
       key values makes the order a function of each group's own metadata alone.  That is what the
       Assumption-1 argument needs: padding must not move any OTHER group's position (and hence its
       spending weight gamma_j).  Measured directly below by ORDER_PERTURBATION.

  (ii) A KEYED variant (secret seed).  A PUBLIC hash of attacker-selectable (SrcIP,DstIP) fields is
       grindable -- an adversary controlling several source hosts can pick whichever gives a
       favourable slot -- so the public hash is a TIMING-INDEPENDENT CANONICALIZATION, not a security
       mechanism.  A pre-committed keyed hash with a seed the defender keeps secret is the
       adversary-resistant variant (at the cost of a new threat-model assumption); from the
       adversary's view its induced order is an unpredictable draw from exactly the ensemble whose
       spread we report here.

Writes out/t53_ordering.json.
"""
import numpy as np, json, time
from pathlib import Path
from scipy.special import zeta

import h_stream as hs
from h6_procs import Ctx, make_gamma, run_lond

# The hash and the induced order have ONE definition, in h_stream, where build_episodes(order=...)
# also uses them (review-7 item R3a).  They are re-exported here because t48 imports them from this
# module; importing rather than re-implementing is what keeps the order the paper MEASURES and the
# order the pipeline SHIPS from drifting apart.
from h_stream import _mix64, key_hash, hashed_order, KEYED_SEED

BUCKET = 2 * 3600
K = 1; A = 0.05; W0 = 0.025
POSITIONS = [0.55, 0.62, 0.70, 0.77, 0.85]   # every window tab:main reports (item R3c)
SEEDS = [0, 1]                               # both detector seeds (item R3c)
N_RAND = 50                  # fixed random pre-committed within-bucket orders (the ensemble)
INT64MAX = np.iinfo(np.int64).max
SECRET_SEED = KEYED_SEED     # stands in for a seed the defender would keep secret


def group_arrays(gid, e_te, y_te, ts_w, T):
    """Per-group aggregates in group-id order (unordered by time)."""
    sum_e = np.bincount(gid, weights=e_te, minlength=T)
    nsz = np.bincount(gid, minlength=T).astype(np.int64)
    mal = np.bincount(gid, weights=y_te.astype(float), minlength=T)
    first_ts = np.full(T, INT64MAX, dtype=np.int64); np.minimum.at(first_ts, gid, ts_w)
    last_ts = np.full(T, -1, dtype=np.int64); np.maximum.at(last_ts, gid, ts_w)
    first_pos = np.full(T, INT64MAX, dtype=np.int64)
    np.minimum.at(first_pos, gid, np.arange(len(gid), dtype=np.int64))
    Ev = sum_e / np.maximum(nsz, 1)
    ismal = mal > 0
    bucket = first_ts // (BUCKET * 1_000_000)
    return dict(Ev=Ev, ismal=ismal, sum_e=sum_e, nsz=nsz, first_ts=first_ts, last_ts=last_ts,
                first_pos=first_pos, bucket=bucket, T=T)


def run_and_price(g, order, CEIL):
    """Run e-LOND under `order`; return (rej, tp, median r*, sorted r*), where r* is the minimal
    real-flow pads that would push a detected malicious episode's mean evidence below 1/level -- the
    closed-form lower bound r* = floor(S*level) - m + 1, priced at the running level where it fired."""
    Evo = g["Ev"][order]; ismo = g["ismal"][order]
    sumo = g["sum_e"][order]; nszo = g["nsz"][order]
    ctx = Ctx(Evo, ismo, CEIL, alpha=A, w0=W0)
    g1, _ = make_gamma("poly", ctx.T)
    R = 0; rej = tp = 0
    rstars = []
    for t in range(1, ctx.T + 1):
        lvl = A * g1[t] * (R + 1)
        if ctx.infeasible(lvl):
            continue
        if Evo[t - 1] >= 1.0 / lvl:
            R += 1; rej += 1
            if ismo[t - 1]:
                tp += 1
                r = int(np.floor(sumo[t - 1] * lvl)) - int(nszo[t - 1]) + 1
                if r >= 1:
                    rstars.append(r)
    med_r = float(np.median(rstars)) if rstars else None
    return rej, tp, med_r, sorted(int(v) for v in rstars)


def cold_start(CEIL, T, R=0):
    """Largest step t at which e-LOND can reject ANYTHING given R rejections so far.

    Before the first rejection the level is alpha_t = A*gamma_t*(R+1) with R=0, and no rejection
    is possible once CEIL < 1/alpha_t.  gamma is strictly decreasing, so the feasible steps are
    exactly the prefix t <= w_cold.  Returned with the closed form floor((A*CEIL*(R+1)/zeta)^(1/1.6))
    beside it so the two can be checked against each other."""
    g1, _ = make_gamma("poly", T)
    lvl = A * g1[1:T + 1] * (R + 1.0)
    # spelled EXACTLY as Ctx.infeasible spells it (CEIL < 1/lvl), not as the algebraically equal
    # lvl*CEIL >= 1: the two disagree on the last representable step often enough to matter, and
    # this quantity is compared against a realised run below.
    with np.errstate(divide="ignore"):
        ok = np.flatnonzero(np.where(lvl > 0, CEIL >= 1.0 / np.maximum(lvl, 1e-300), False))
    w = int(ok[-1] + 1) if ok.size else 0
    x = A * CEIL * (R + 1.0) / float(zeta(1.6, 1))
    closed = int(np.floor(x ** (1.0 / 1.6))) if x > 0 else 0
    return w, closed


def boundary_check(g, order, CEIL, n_rej):
    """Is a zero-rejection run the FEASIBILITY BOUNDARY or a bug?

    Before its first rejection e-LOND offers alpha_t = A*gamma_t exactly, so the run rejects
    nothing IF AND ONLY IF no episode in the feasible prefix t <= w_cold carries Ev[t] >= 1/alpha_t.
    That is an exact characterisation, not a necessary condition, so comparing it against the
    realised rejection count is a hard check: a wrong threshold direction, a scoring/ordering
    mismatch or an off-by-one in the rank would break the equivalence, whereas the boundary
    reproduces it.  Also reports where the first CLEARING episode sits, so a zero can be read as
    "the earliest episode that could have fired arrived at step N, and the prefix ended at w_cold"."""
    T = len(order)
    w, closed = cold_start(CEIL, T)
    Evo = g["Ev"][order]
    g1, _ = make_gamma("poly", T)
    lvl = A * g1[1:T + 1]
    # likewise spelled as run_and_price spells it (Ev >= 1/lvl)
    with np.errstate(divide="ignore"):
        thr = np.where(lvl > 0, 1.0 / np.maximum(lvl, 1e-300), np.inf)
    clears = np.flatnonzero(Evo >= thr)                # would fire at R=0, at its own step
    first_clear = int(clears[0] + 1) if clears.size else None
    in_prefix = int((clears < w).sum())
    return dict(cold_start_steps=w, cold_start_closed_form=closed,
                cold_start_matches_closed_form=bool(w == closed),
                first_clearing_step=first_clear, n_clearing_in_prefix=in_prefix,
                n_clearing_anywhere=int(clears.size), n_rej=int(n_rej),
                zero_iff_empty_prefix=bool((n_rej == 0) == (in_prefix == 0)))


def main():
    t0 = time.time()
    Path("out").mkdir(exist_ok=True)
    X, y, ts, src, dst = hs.load()
    N = len(y)
    out = {"config": dict(bucket_s=BUCKET, k=K, alpha=A, w0=W0, positions=POSITIONS,
                          seeds=SEEDS, n_rand=N_RAND,
                          canonical="deterministic metadata-hash within-bucket order (not "
                                    "timing-influenceable); power reported as median/IQR/range over "
                                    f"{N_RAND} random pre-committed orders; first-flow = upper bound",
                          note="within-bucket order robustness; evidence-independent keys only")}
    rows = []
    for POS in POSITIONS:
        i1, i2, i3 = hs.split_indices(N, POS)
        y_te = y[i2:i3]
        ts_w, src_w, dst_w = ts[i2:i3], src[i2:i3], dst[i2:i3]
        for SEED in SEEDS:
            score = hs.fit_detector(X, y, i1, seed=SEED, kind="hgb", verbose=False)
            s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
            e_te, cal, NC, CEIL = hs.evalues(s_cal, y[i1:i2], s_te, k=K)
            ep = hs.build_episodes(e_te, y_te, ts_w, src_w, dst_w, BUCKET, "src-dst")
            gid = ep["gid"]; T = ep["T"]
            g = group_arrays(gid, e_te, y_te, ts_w, T)

            # per-group key values (every flow of a group shares them, so scatter-assign is exact)
            gsrc = np.zeros(T, dtype=np.int64); gsrc[gid] = src_w
            gdst = np.zeros(T, dtype=np.int64); gdst[gid] = dst_w
            gbkt = g["bucket"]

            # deterministic metadata-hash of the group's OWN (SrcIP,DstIP,bucket) key -> CANONICAL
            # order; a function of that group's metadata alone, so neither its own nor any other
            # group's slot moves when the attacker changes arrival times or pads its episode.
            hkey = key_hash(gsrc, gdst, gbkt, seed=0)
            canonical = hashed_order(hkey, gsrc, gdst, gbkt)
            keyed = hashed_order(key_hash(gsrc, gdst, gbkt, seed=SECRET_SEED), gsrc, gdst, gbkt)
            # the SAME order build_episodes now ships (item R3a).  Asserting equality here is what
            # keeps the stage that MEASURES order sensitivity and the stages that RUN under the
            # canonical order from drifting apart -- they are one definition, checked at run time.
            for kind, ref in (("keyhash", canonical), ("keyed", keyed)):
                shipped = hs.build_episodes(e_te, y_te, ts_w, src_w, dst_w, BUCKET, "src-dst",
                                            order=kind)["order"]
                assert np.array_equal(shipped, ref), f"build_episodes(order={kind!r}) != t53's"

            # five illustrative NAMED orders (for the appendix spread table)
            rng0 = np.random.default_rng(20260831)
            perm = rng0.permutation(T)
            named = {
                "shipped (bucket, first-flow)":  np.lexsort((g["first_pos"], g["first_ts"])),
                "bucket, group-id":              np.lexsort((np.arange(T), g["bucket"])),
                "bucket, last-flow":             np.lexsort((g["last_ts"], g["bucket"])),
                "bucket, fixed-random":          np.lexsort((perm, g["bucket"])),
                "bucket, hashed-key (canonical)": canonical,
                "bucket, keyed hash (secret seed)": keyed,
            }
            print(f"\n  pos={POS} seed={SEED}: T={T:,} episodes, {int(g['ismal'].sum())} malicious, "
                  f"CEIL={CEIL:,.0f}  [{time.time()-t0:.0f}s]")
            print(f"    {'within-bucket order':<32} {'rej':>5} {'true det':>9} {'med r*':>8}")
            named_rows = {}
            for name, order in named.items():
                assert np.array_equal(np.sort(order), np.arange(T)), f"{name} not a permutation"
                assert np.all(np.diff(g["bucket"][order]) >= 0), f"{name} breaks bucket-close order"
                rej, tp, med_r, rs = run_and_price(g, order, CEIL)
                bc = boundary_check(g, order, CEIL, rej)
                assert bc["zero_iff_empty_prefix"], (
                    f"{name} @ pos={POS} seed={SEED}: rejections={rej} but "
                    f"{bc['n_clearing_in_prefix']} episodes clear inside the feasible prefix "
                    f"of {bc['cold_start_steps']} steps -- the two must agree exactly")
                assert bc["cold_start_matches_closed_form"], bc
                named_rows[name] = dict(rej=int(rej), tp=int(tp), median_rstar=med_r,
                                        rstar_sorted=rs, boundary=bc,
                                        recall=float(tp / max(int(g["ismal"].sum()), 1)))
                print(f"    {name:<32} {rej:>5} {tp:>9} {str(med_r):>8}")

            # ---- the ensemble: N_RAND fixed random pre-committed within-bucket orders ----
            tps, rstar_meds = [], []
            for sd in range(N_RAND):
                rs_ = np.random.default_rng(1000 + sd).random(T)     # one random key per group
                order = np.lexsort((rs_, g["bucket"]))               # random within-bucket, batched
                _, tp, med_r, _ = run_and_price(g, order, CEIL)
                tps.append(tp)
                if med_r is not None:
                    rstar_meds.append(med_r)
            tps = np.array(tps)
            q = lambda a, pq: float(np.percentile(a, pq)) if len(a) else None
            ff_row = named_rows["shipped (bucket, first-flow)"]
            cn_row = named_rows["bucket, hashed-key (canonical)"]
            ky_row = named_rows["bucket, keyed hash (secret seed)"]
            ff = ff_row["tp"]; canon_tp = cn_row["tp"]
            ens = dict(tp_min=int(tps.min()), tp_q25=q(tps, 25), tp_median=float(np.median(tps)),
                       tp_q75=q(tps, 75), tp_max=int(tps.max()),
                       rstar_median_over_orders=(q(rstar_meds, 50) if rstar_meds else None),
                       rstar_iqr=[q(rstar_meds, 25), q(rstar_meds, 75)] if rstar_meds else None,
                       n_orders_with_detection=int((tps > 0).sum()))
            # ---- ORDER PERTURBATION: how many OTHER groups can the attacker's timing move? ----
            # Assumption 1 is stated per hypothesis against a group-specific metadata sigma-field
            # M_j.  Padding must therefore leave every OTHER (true-null) group's position -- hence
            # its spending weight gamma_j -- untouched.  We inject one pad flow on an attacked
            # episode's own key, timed at the earliest instant of its own bucket, and count how many
            # other groups change index.
            att = np.flatnonzero(g["ismal"])
            pert = {}
            if att.size:
                j = int(att[np.argmin(g["first_ts"][att])])       # earliest malicious episode
                ft2 = g["first_ts"].copy(); fp2 = g["first_pos"].copy()
                ft2[j] = int(gbkt[j]) * BUCKET * 1_000_000         # first instant of its own bucket
                fp2[j] = -1                                        # and first in stream order
                base_ff = np.empty(T, np.int64)
                base_ff[named["shipped (bucket, first-flow)"]] = np.arange(T)
                new_ff = np.empty(T, np.int64); new_ff[np.lexsort((fp2, ft2))] = np.arange(T)
                moved_ff = int((base_ff != new_ff).sum()) - int(base_ff[j] != new_ff[j])
                # the hashed key does not read first_ts at all (the bucket is part of the group KEY
                # and a pad in the same bucket cannot change it), so the order is bit-identical
                new_canon = hashed_order(key_hash(gsrc, gdst, gbkt, seed=0), gsrc, gdst, gbkt)
                moved_hash = int((new_canon != canonical).sum())
                pert = dict(perturbed_group=j, others_moved_first_flow=moved_ff,
                            others_moved_hashed_key=moved_hash,
                            frac_moved_first_flow=float(moved_ff / max(T - 1, 1)))
                print(f"    order perturbation (one pad, earliest slot of its own bucket): "
                      f"first-flow order moves {moved_ff:,} other groups "
                      f"({100*moved_ff/max(T-1,1):.1f}% of the stream); hashed moves {moved_hash}")

            rows.append(dict(pos=POS, seed=SEED, T=int(T), n_mal=int(g["ismal"].sum()),
                             CEIL=float(CEIL), named=named_rows, ensemble=ens,
                             first_flow_tp=int(ff), canonical_tp=int(canon_tp),
                             canonical_median_rstar=cn_row["median_rstar"],
                             canonical_rstar_sorted=cn_row["rstar_sorted"],
                             keyed_tp=int(ky_row["tp"]),
                             keyed_median_rstar=ky_row["median_rstar"],
                             first_flow_median_rstar=ff_row["median_rstar"],
                             perturbation=pert,
                             first_flow_is_upper=bool(ff >= tps.max())))
            print(f"    ensemble over {N_RAND} random orders: true det median={np.median(tps):.1f} "
                  f"IQR[{ens['tp_q25']:.0f},{ens['tp_q75']:.0f}] range[{tps.min()},{tps.max()}]; "
                  f"canonical(hash)={canon_tp}; first-flow={ff} (upper: {ff >= tps.max()})")
            print(f"    padding cost median r* over orders: {ens['rstar_median_over_orders']} "
                  f"IQR {ens['rstar_iqr']}  (attack cost robust to order)")
    out["rows"] = rows
    # `positions` keeps its pre-R3c shape (seed 0 only) so the transcribed record stays checkable
    out["positions"] = [r for r in rows if r["seed"] == SEEDS[0]]
    out["first_flow_is_upper_bound_everywhere"] = all(r["first_flow_is_upper"] for r in rows)
    out["canonical_never_exceeds_first_flow"] = all(r["canonical_tp"] <= r["first_flow_tp"]
                                                    for r in rows)
    json.dump(out, open("out/t53_ordering.json", "w"), indent=1, allow_nan=False)
    print(f"\n  first-flow is an upper bound on detection power at every window and seed: "
          f"{out['first_flow_is_upper_bound_everywhere']}")
    print(f"  [{time.time()-t0:.0f}s]  wrote out/t53_ordering.json")
    return out


if __name__ == "__main__":
    main()
