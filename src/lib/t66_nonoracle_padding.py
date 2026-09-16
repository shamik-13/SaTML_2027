"""t66 -- what Surface A costs an attacker who does NOT have oracle state.

Every per-alert padding cost the paper reports is r* = floor(S*alpha_t) - m + 1, which uses the
realised group evidence sum S and the LIVE controller level alpha_t.  Both are oracle quantities, and
the paper says so at every use.  A reviewer's objection to that framing is fair and sharp: the oracle
caveat is honest, but sizing IS the hard part of the attack, and the paper never measures what a
non-oracle attacker actually has to spend.  Surface B already answers the same question for itself
(a +/-33% estimate of |C| suffices; unknown controller state costs ~36x over-provisioning); Surface A
did not.  This stage closes that asymmetry.

It is a RE-ANALYSIS, not a new experiment: t48_W3 already stores per-episode m, S, alpha_t and
r_closed, and t25_H5 already stores calibration-slice group-size quantiles (NOT benign-filtered --
see the CONSPICUITY note below, which is where that mattered).  Nothing is re-simulated, so nothing
here can disagree with the runs that produced those artefacts -- and the first thing main() does is
assert that r_closed is reproduced from the stored (S, m, alpha_t), which is the check that this
module is reading the fields it thinks it is.

TWO attacker strategies, both strictly weaker than the oracle:

  MULTIPLIER (needs m only).  Append (c-1)*m flows -- i.e. multiply your own episode's flow count by
  c.  Defeats the alert iff (c-1)*m >= r*, i.e. iff c >= 1 + r*/m.  The attacker needs NO estimate of
  S, alpha_t, |C| or T; it needs the size of its own episode.  On LSPR23 that is free, because every
  host pair carrying attack traffic is 100% malicious (paper Sec. V-D), so m IS the attacker's own
  flow count.  On a benign-inclusive stream m also contains benign flows the attacker cannot see, so
  there it knows only a LOWER bound on m and this strategy under-pads -- recorded as a scope limit,
  not silently ignored.

  ABSOLUTE.  Append a fixed N flows to every episode you create.  Defeats iff N >= r*.  Executing it
  needs no knowledge, but CHOOSING N does: the N reported here is read off the realised r*
  distribution, so it measures how large a flat pad must BE, and is not a rule an uninformed attacker
  could derive.  Because it is defined without m it is measured on the canonical and first-flow cells
  of every window and seed t28b carries (the `keyed` arm t28b also holds is out of scope here), not
  only the two windows for which t48 stores per-episode arities.

WHY BOTH.  The multiplier arm is the operationally natural strategy and is measurable on two windows;
the absolute arm is the strictly-zero-knowledge floor and is measurable on all five.  Reporting only
the first would overstate coverage; reporting only the second would understate the attacker.

Also measured: CONSPICUITY.  A pad that defeats the mean is useless to an attacker if a trivial
volume monitor catches it, so the padded arity c*m is bracketed against the arity distribution.
CAREFUL WITH THE POPULATION -- an earlier version of this module got it wrong.  t25_H5's n0 is a
quantile of source-destination-bucket group sizes over the CALIBRATION slice and is NOT filtered to
benign (`csizes = cal_group_sizes(ts[i1:i2], ...)` at t25_H5_caps.py:43, while only the e-value
calibration takes y_cal), so it is neither "the benign arity distribution" nor a deployment quantity.
What t25 DOES give per window, and what a claim about being noticed should rest on, is
`viol_frac`: the fraction of DEPLOYMENT groups whose arity exceeds each n0.  We therefore report the
padded arity together with the two n0 values that bracket it and their deployment exceedance
fractions, which supports a statement of the form "the padded arity lies between the 90th and 99th
percentile of deployment episode arity" -- unremarkable, but not invisible, which is the honest
reading.

Writes out/t66_nonoracle.json.
"""
import json, statistics as st
from math import floor, ceil

CS = [2, 3, 5, 10, 100]           # pre-committed multipliers, fixed before looking at the data
QUANTILES = ["p50", "p90", "p99", "p999", "max"]


def _load(name):
    return json.load(open(f"out/{name}.json"))


def _selfcheck(w):
    """r_closed must be reproduced by the closed form from the stored fields.  If this fails the
    module is reading the wrong keys and every number below is meaningless."""
    n = bad = 0
    for arm in ("episodes", "episodes_keyhash"):
        for pos in w[arm]:
            for e in w[arm][pos]["per_episode"]:
                n += 1
                if floor(e["S"] * e["alpha_t"]) - e["m"] + 1 != e["r_closed"]:
                    bad += 1
    assert n and not bad, f"closed form does not reproduce r_closed on {bad}/{n} episodes"
    return n


def _multiplier_arm(w, arity_q, exceed):
    out = {}
    for arm, label in (("episodes_keyhash", "canonical"), ("episodes", "first-flow")):
        for pos in sorted(w[arm]):
            pe = w[arm][pos]["per_episode"]
            if not pe:
                continue
            need = [1.0 + e["r_closed"] / e["m"] for e in pe]      # c >= 1 + r*/m defeats
            rows = []
            for c in CS:
                hit = [e for e in pe if (c - 1) * e["m"] >= e["r_closed"]]
                if not hit:
                    rows.append(dict(c=c, defeated=0, of=len(pe)))
                    continue
                added = [(c - 1) * e["m"] for e in hit]
                oracle = [e["r_closed"] for e in hit]
                rows.append(dict(
                    c=c, defeated=len(hit), of=len(pe),
                    median_added=float(st.median(added)),
                    median_oracle=float(st.median(oracle)),
                    median_overprovision=float(st.median(a / b for a, b in zip(added, oracle))),
                    max_added=float(max(added)),
                    # conspicuity: where the padded arity sits in the calibration-block arity distribution
                    median_padded_arity=float(st.median(c * e["m"] for e in hit)),
                    max_padded_arity=float(max(c * e["m"] for e in hit))))
            q = arity_q.get((float(pos), 0), {})
            ex = exceed.get((float(pos), 0), {})
            # bracket the padded arity between the two stored quantiles that straddle it
            for r in rows:
                pa = r.get("median_padded_arity")
                if pa is None:
                    continue
                below = [(v, k) for k, v in q.items() if v <= pa]
                above = [(v, k) for k, v in q.items() if v > pa]
                r["arity_bracket"] = dict(
                    lower=max(below)[1] if below else None, lower_n0=max(below)[0] if below else None,
                    upper=min(above)[1] if above else None, upper_n0=min(above)[0] if above else None,
                    lower_deployment_exceedance=ex.get(max(below)[1]) if below else None,
                    upper_deployment_exceedance=ex.get(min(above)[1]) if above else None)
            out[f"{label}@{pos}"] = dict(
                order=label, pos=float(pos), n_alerts=len(pe),
                c_required_median=float(st.median(need)),
                c_required_p90=float(sorted(need)[min(len(need) - 1, int(0.9 * len(need)))]),
                c_required_max=float(max(need)),
                c_min_integer_defeating_all=int(ceil(max(need))),
                calibration_arity_n0=q, deployment_exceedance=ex, by_c=rows)
    return out


def _absolute_arm(b):
    """N >= r* defeats; needs no knowledge at all.  Measurable wherever r* lists exist."""
    out = {}
    for order, label in (("keyhash", "canonical"), ("first-flow", "first-flow")):
        for cell, v in b["table1_by_order"][order].items():
            pads = v.get("pads_real") or []
            if not pads:
                continue
            s = sorted(pads)
            n = len(s)
            def at(p):
                return int(s[min(n - 1, int(p * n) if p < 1 else n - 1)])
            out[f"{label}@{cell}"] = dict(
                order=label, pos=v["pos"], seed=v["seed"], n_alerts=n,
                N_for_50pct=at(0.5), N_for_90pct=at(0.9), N_for_all=int(max(s)))
    return out


def main():
    w, b, h = _load("t48_W3"), _load("t28b_reallevel"), _load("t25_H5")
    n_checked = _selfcheck(w)
    arity_q, exceed = {}, {}
    for r in h["rows"]:
        arity_q.setdefault((r["pos"], r["seed"]), {})[r["cap"]] = r["n0"]
        # viol_frac is the share of DEPLOYMENT groups with arity above this n0 -- the only
        # deployment-side quantity t25 stores, and the one a "would it be noticed" claim needs.
        exceed.setdefault((r["pos"], r["seed"]), {})[r["cap"]] = r["viol_frac"]
    arity_q = {k: {q: v[q] for q in QUANTILES if q in v} for k, v in arity_q.items()}
    exceed = {k: {q: v[q] for q in QUANTILES if q in v} for k, v in exceed.items()}

    mult = _multiplier_arm(w, arity_q, exceed)
    absol = _absolute_arm(b)

    canon = {k: v for k, v in mult.items() if v["order"] == "canonical"}
    summary = dict(
        closed_form_selfcheck_episodes=n_checked,
        canonical_c_min_defeating_all={k: v["c_min_integer_defeating_all"] for k, v in canon.items()},
        note_m_knowledge=("the multiplier strategy needs m, the attacker's own episode arity. On "
                          "LSPR23 every host pair carrying attack traffic is 100% malicious, so m is "
                          "exactly the attacker's own flow count; on a benign-inclusive stream m also "
                          "contains benign flows and the attacker knows only a lower bound"),
        scope=("multiplier arm covers the windows for which t48_W3 stores per-episode arities "
               "(0.55, 0.85, both orders); the absolute arm covers the canonical and first-flow "
               "cells of every window and seed t28b carries, not its `keyed` arm. The replication "
               "window 0.62 has no stored per-episode m, so it appears in the absolute arm only"),
        note_multiplier_selection=("the per-window minimum c is chosen AFTER seeing the realised "
                                   "overshoot factors and is an oracle-informed floor; the "
                                   "pre-committed claim is the single constant c that defeats every "
                                   "canonical alert at both windows, which is c=10"))
    out = dict(
        config=dict(multipliers=CS, arity_quantiles=QUANTILES,
                    # both within-bucket arms are measured; declared structurally so the order
                    # registry can see it rather than having to read the key names
                    orders=["canonical", "first-flow"], canonical_order="canonical",
                    sources=["t48_W3", "t28b_reallevel", "t25_H5"],
                    reanalysis_only=True,
                    strategies=dict(
                        multiplier="append (c-1)*m flows; defeats iff c >= 1 + r*/m; needs m only",
                        absolute="append a fixed N flows; defeats iff N >= r*; needs nothing")),
        multiplier=mult, absolute=absol, summary=summary)
    json.dump(out, open("out/t66_nonoracle.json", "w"), indent=1, allow_nan=False)
    for k, v in sorted(canon.items()):
        row = {r["c"]: r for r in v["by_c"]}
        c = v["c_min_integer_defeating_all"]
        r = row.get(c) or row.get(min(x for x in CS if x >= c), {})
        print(f"  {k:<22} n={v['n_alerts']:>3}  c_req median {v['c_required_median']:.2f} "
              f"max {v['c_required_max']:.2f}  -> c={r.get('c')} defeats "
              f"{r.get('defeated')}/{r.get('of')} at median {r.get('median_added')} added flows "
              f"({r.get('median_overprovision', 0):.1f}x oracle), padded arity "
              f"{r.get('median_padded_arity')} vs calib n0(p99) {v['calibration_arity_n0'].get('p99')}")
    print("  wrote out/t66_nonoracle.json")
    return out


if __name__ == "__main__":
    main()
