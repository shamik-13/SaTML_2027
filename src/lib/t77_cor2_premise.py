"""t77 -- does Corollary 2's premise hold on the AIT joint-attack cells?  (round 32)

Corollary 2 (cor:dilution) is stated for e-LOND under HORIZON-UNIFORM spending and has one premise about
the rest of the stream: no hypothesis other than the attacker's own episodes carries evidence at or
above the cold-start threshold T/alpha.  The paper previously inferred that the premise "fails" in an
organisation from the existence of a baseline non-attacker alert.  That inference is invalid: a
non-attacker alert can fire only after earlier rejections have raised the level, at which point its
evidence may be well below T/alpha.  This stage measures the premise directly, per organisation and
detector arm, on exactly the episode streams t76_joint_ait attacked:

  max_{j not own} Ev_j / (T/alpha)     >= 1  <=>  the cold-start premise fails on that stream
  n_nonown_at_cold_start                the number of non-attacker episodes at or above T/alpha
  per baseline non-attacker alert       its evidence, the R it fired at, and whether it clears the
                                        R = 0 level at its own position (fires_at_R0) or only the
                                        raised level (level-raised)

together with the own-episode side (max own evidence, c_crit = max_own Ev * alpha / T, whether some
own episode attains the ceiling so that c_crit = rho).  The other three diagnostics the review asked
for -- episodes excluded for insufficient prior templates, the firing behaviour of admitted pads, and
the residual attacker alerts -- are already in out/t76_joint_ait.json and are read from there by the
table generator; this stage does not recompute them.

CONTROL.  The streams are rebuilt with t76.prepare_org (t54's leave-one-organisation-out chain,
canonical order) and the clean e-LOND walk must reproduce t76's stored baselines field by field
(T, NC, CEIL, rho, c_int, rejections, true detections, own and non-attacker alert counts) for every
cell, or the stage fails.  Cells: flow arm on all eight organisations, host arm on the two the joint
host arm covers (t76.ORGS_HOST).

Writes out/t77_cor2_premise.json.    AIT_DIR=... python t77_cor2_premise.py
"""
import glob
import json
import time
from pathlib import Path

import numpy as np

from h6_procs import make_gamma
import t51_R7_ait as t51
import t76_joint_ait as t76

A = t76.A
ORDER = t76.ORDER
GAMMAS = t76.GAMMAS


def diagnose(org, t76_rec):
    ep = org["ep"]; T = ep["T"]; own = ep["ismal"]; Ev = ep["Ev"]
    CEIL = org["CEIL"]; rho = CEIL * A / T; c_int = int(np.floor(rho)) + 1
    tau0 = T / A                                            # horizon-uniform cold-start threshold
    nonown = ~own
    max_nonown = float(Ev[nonown].max()) if nonown.any() else 0.0
    max_own = float(Ev[own].max()) if own.any() else 0.0
    rec = dict(org=org["name"], arm=("host" if org["use_host"] else "flow"), order=ORDER,
               T=int(T), NC=int(org["NC"]), CEIL=float(CEIL), rho=float(rho), c_int=c_int,
               cold_start_threshold=float(tau0),
               n_own=int(own.sum()), n_nonown=int(nonown.sum()),
               max_nonown_ev=max_nonown, max_nonown_ratio=float(max_nonown / tau0),
               premise_fails_cold_start=bool(max_nonown >= tau0),
               n_nonown_at_cold_start=int((Ev[nonown] >= tau0).sum()),
               n_nonown_firing=int((Ev[nonown] > 0).sum()),
               max_nonown_fire_fraction=float(max_nonown / CEIL),
               max_own_ev=max_own, c_crit=float(max_own * A / T),
               own_attains_ceiling=bool(np.isclose(max_own, CEIL)),
               baseline={})
    # control: the stream is the one t76 attacked
    assert t76_rec["T"] == T and t76_rec["NC"] == org["NC"] and np.isclose(t76_rec["CEIL"], CEIL) \
        and np.isclose(t76_rec["rho"], rho) and t76_rec["c_int"] == c_int and t76_rec["n_own"] == int(own.sum()), \
        f"{org['name']}: stream differs from t76's ({t76_rec['T']},{t76_rec['NC']},{t76_rec['rho']:.4f})"
    for k in GAMMAS:
        g1 = make_gamma(k, T)[0]
        fired, lvl, summ = t76.clean_run(org, g1)
        R_before = np.concatenate([[0], np.cumsum(fired)[:-1]]).astype(int)
        b = t76_rec["baseline"][k]
        own_alerts = int((fired & own).sum()); nonown_alerts = int((fired & nonown).sum())
        assert (summ["rejections"], summ["true"], own_alerts, nonown_alerts) == \
               (b["rejections"], b["true"], b["own_alerts"], b["nonown_alerts"]), \
            f"{org['name']}/{k}: clean walk does not reproduce t76's baseline {b}"
        alerts = []
        for j in np.flatnonzero(fired & nonown):
            t = int(j) + 1
            lvl_R0 = A * g1[t]                               # the level at this position with R = 0
            alerts.append(dict(pos=int(j), ev=float(Ev[j]), R_before=int(R_before[j]),
                               level=float(lvl[j]), level_R0=float(lvl_R0),
                               ev_over_cold_start=float(Ev[j] / tau0),
                               fires_at_R0=bool(Ev[j] >= 1.0 / lvl_R0)))
        first_own = np.flatnonzero(fired & own)
        rec["baseline"][k] = dict(
            rejections=summ["rejections"], true=summ["true"], false_discoveries=summ["false_discoveries"],
            own_alerts=own_alerts, nonown_alerts=nonown_alerts,
            nonown_alerts_at_R0=int(sum(a["fires_at_R0"] for a in alerts)),
            nonown_alerts_level_raised=int(sum(not a["fires_at_R0"] for a in alerts)),
            nonown_alerts_at_cold_start=int(sum(a["ev"] >= tau0 for a in alerts)),
            first_own_alert_pos=(int(first_own[0]) if first_own.size else None),
            nonown_alerts_before_first_own=int(sum(a["pos"] < first_own[0] for a in alerts)) if first_own.size else len(alerts),
            nonown_alert_details=alerts)
    return rec


def main():
    t0 = time.time()
    Path("out").mkdir(exist_ok=True)
    t76_out = json.load(open("out/t76_joint_ait.json"))
    t51.ensure_extracted()
    paths = sorted(glob.glob(f"{t51.AIT_DIR}/*/tcp_complete.csv"))
    names = [Path(p).parent.name for p in paths]
    print(f"  loading {len(names)} AIT scenarios: {names}", flush=True)
    scen = {}
    for n_, p in zip(names, paths):
        scen[n_] = t51.load_scenario(p); scen[n_]["path"] = p
    common = {test: sorted(set.intersection(*[scen[n_]["good"] & set(scen[n_]["Xnum"].columns)
                                              for n_ in names if n_ != test])) for test in names}
    print(f"  loaded  [{time.time()-t0:.0f}s]", flush=True)
    out = dict(config=dict(stage="t77_cor2_premise", alpha=A, k=t76.K, w0=t76.W0,
                           order=ORDER, orders=[ORDER], canonical_order=ORDER, gammas=list(GAMMAS),
                           orgs=names, orgs_host=list(t76.ORGS_HOST),
                           premise="cor:dilution: no non-attacker hypothesis carries evidence >= T/alpha",
                           control="every cell must reproduce t76_joint_ait's stored baseline",
                           source_t76=t76_out["config"]["stage"]),
               rows=[])
    cells = [(n_, False) for n_ in names] + [(n_, True) for n_ in t76.ORGS_HOST if n_ in scen]
    for test, use_host in cells:
        arm = "host" if use_host else "flow"
        org = t76.prepare_org(test, scen, names, common, use_host=use_host)
        rec = diagnose(org, t76_out["orgs"][test][arm])
        out["rows"].append(rec)
        print(f"  [{test:15s}|{arm}] T={rec['T']} rho={rec['rho']:.3f} max_nonown/(T/a)={rec['max_nonown_ratio']:.3f} "
              f"n>=cold={rec['n_nonown_at_cold_start']} other alerts hf/ha="
              f"{rec['baseline']['poly']['nonown_alerts']}/{rec['baseline']['uniform']['nonown_alerts']} "
              f"(at R0 {rec['baseline']['poly']['nonown_alerts_at_R0']}/{rec['baseline']['uniform']['nonown_alerts_at_R0']}) "
              f"own attains ceiling={rec['own_attains_ceiling']}  [{time.time()-t0:.0f}s]", flush=True)
        json.dump(out, open("out/t77_cor2_premise.json", "w"), indent=1)
    out["control_reproduced"] = True                       # every cell passed the assertions above
    out["n_cells"] = len(out["rows"])
    json.dump(out, open("out/t77_cor2_premise.json", "w"), indent=1)
    print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t77_cor2_premise.json ({len(out['rows'])} cells)")
    return out


if __name__ == "__main__":
    main()
