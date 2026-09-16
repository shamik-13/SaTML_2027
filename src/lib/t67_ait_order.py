"""t67 -- the AIT transfer result under the CANONICAL within-bucket order.

The abstract's external-validation number ("84 of 85 detected episodes suppressible on a second,
benign-inclusive dataset") is measured under FIRST-FLOW arrival, and AIT's order sensitivity was
never audited -- the one conspicuous qualification still attached to a headline abstract figure.
On LSPR23 the canonical metadata-hash order is the reported one precisely because first-flow is
attacker-influenceable and is the detection-favourable end of the order ensemble, so leaving AIT on
first-flow is an inconsistency a reader can see.

This stage removes it, and it is a RESEQUENCING, not a new experiment.  Everything expensive in the
AIT chain -- the leave-one-org-out feature selection, the per-fold detector fit, the scores, the
chronological in-org calibration and the e-values -- is computed BEFORE episodes are ordered and is
therefore order-free.  Only the episode permutation, the controller run over it and the replay
pricing depend on the order.  We call t54's own `run_org` with `order="keyhash"` rather than
reimplementing the chain, so the two arms cannot drift; `episodes()` in turn calls h_stream's
`key_hash`/`hashed_order`, so "canonical" means the same thing on AIT as on LSPR23.

Scope: FLOW-ONLY folds, which is what the 84/85 figure covers.  The host-conditioned arm is two orgs
and is left on first-flow, as the paper says.  No new dataset, detector or FDR procedure.

Writes out/t67_ait_order.json.
"""
import numpy as np, json, time, glob
from pathlib import Path

import t51_R7_ait as t51
import t54_ait_suppression as t54

ORDERS = ["first-flow", "keyhash"]


def _agg(rows):
    det = [o for o in rows if o.get("n_detected", 0) > 0]
    n_det = sum(o["n_detected"] for o in det)
    n_sup = sum(o.get("n_suppressible", 0) for o in det)
    succ = [o["mean_success_rate"] for o in det if o.get("mean_success_rate") is not None]
    meds = {o["org"]: o["median_rstar_empirical"] for o in det
            if o.get("median_rstar_empirical") is not None}
    return dict(orgs_with_detections=[o["org"] for o in det], n_detected=n_det,
                n_suppressible=n_sup, median_rstar_by_org=meds,
                per_draw_success_min=min(succ) if succ else None,
                per_draw_success_max=max(succ) if succ else None)


def main():
    t0 = time.time()
    Path("out").mkdir(exist_ok=True)
    t51.ensure_extracted()
    paths = sorted(glob.glob(f"{t51.AIT_DIR}/*/tcp_complete.csv"))
    names = [Path(p).parent.name for p in paths]
    scen = {n: t51.load_scenario(p) for n, p in zip(names, paths)}
    common = {test: sorted(set.intersection(*[scen[n]["good"] & set(scen[n]["Xnum"].columns)
                                              for n in names if n != test]))
              for test in names}
    print(f"  {len(names)} orgs loaded  [{time.time()-t0:.0f}s]")

    arms = {}
    for order in ORDERS:
        # ROUND 31: t54.run_org now seeds itself from (org, arm, order), so each arm's draws are a
        # function of the arm alone rather than of how many folds ran before it.  The arms are still
        # NOT paired -- the two orders detect different episode sets, so a given draw attaches to
        # different episodes -- and the replay success rates remain independent Monte Carlo
        # estimates.  What the keying buys is that this stage's first-flow arm reproduces t54's
        # stored rows by construction rather than by coincidence of RNG position.
        print(f"\n  == flow-only folds, order = {order} ==")
        rows = [r for test in names if (r := t54.run_org(test, scen, names, common, False,
                                                         order=order))]
        arms[order] = dict(rows=rows, summary=_agg(rows))
        s = arms[order]["summary"]
        print(f"  -> {s['n_suppressible']} of {s['n_detected']} suppressible across "
              f"{len(s['orgs_with_detections'])} orgs  [{time.time()-t0:.0f}s]")

    ff, kh = arms["first-flow"]["summary"], arms["keyhash"]["summary"]
    # the stored first-flow arm is the one the paper quotes; reproducing it here is the check that
    # this stage runs the same chain, not merely a similar one.
    try:
        stored = json.load(open("out/t54_ait_suppression.json"))
        st = _agg(stored["flow"])
        # Aggregate equality is too weak to support the "same chain" claim: per-organisation costs
        # or success rates could differ while the totals agree.  Compare the rows field by field.
        FIELDS = ("n_detected", "n_suppressible", "n_mal_ep", "T", "NC",
                  "median_rstar_empirical", "median_rstar_closedform", "auroc")
        by_org = {o["org"]: o for o in stored["flow"]}
        repro = set(by_org) == {o["org"] for o in arms["first-flow"]["rows"]} and all(
            by_org[o["org"]].get(f) == o.get(f)
            for o in arms["first-flow"]["rows"] for f in FIELDS)
    except FileNotFoundError:
        st, repro = None, None

    out = dict(
        config=dict(orders=ORDERS, canonical_order="keyhash", arm="flow-only",
                    reanalysis="resequencing only: the detector fit, scores, calibration and "
                               "e-values are computed before ordering and are identical across arms",
                    sources=["t54_ait_suppression", "h_stream.key_hash/hashed_order"]),
        arms=arms,
        summary=dict(
            first_flow=ff, canonical=kh,
            reproduces_stored_first_flow=repro,
            readback_fields=["n_detected", "n_suppressible", "n_mal_ep", "T", "NC",
                             "median_rstar_empirical", "median_rstar_closedform", "auroc"],
            stored_first_flow=st,
            detections_first_flow=ff["n_detected"], detections_canonical=kh["n_detected"],
            suppressible_first_flow=ff["n_suppressible"],
            suppressible_canonical=kh["n_suppressible"]))
    json.dump(out, open("out/t67_ait_order.json", "w"), indent=1, allow_nan=False)
    print(f"\n  first-flow : {ff['n_suppressible']}/{ff['n_detected']} suppressible")
    print(f"  canonical  : {kh['n_suppressible']}/{kh['n_detected']} suppressible")
    print(f"  reproduces the stored first-flow arm: {repro}")
    print(f"  [{time.time()-t0:.0f}s]  wrote out/t67_ait_order.json")
    return out


if __name__ == "__main__":
    main()
