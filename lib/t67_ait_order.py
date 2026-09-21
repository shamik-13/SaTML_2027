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

        print(f"\n  == flow-only folds, order = {order} ==")
        rows = [r for test in names if (r := t54.run_org(test, scen, names, common, False,
                                                         order=order))]
        arms[order] = dict(rows=rows, summary=_agg(rows))
        s = arms[order]["summary"]
        print(f"  -> {s['n_suppressible']} of {s['n_detected']} suppressible across "
              f"{len(s['orgs_with_detections'])} orgs  [{time.time()-t0:.0f}s]")

    ff, kh = arms["first-flow"]["summary"], arms["keyhash"]["summary"]
    try:
        stored = json.load(open("out/t54_ait_suppression.json"))
        st = _agg(stored["flow"])
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
