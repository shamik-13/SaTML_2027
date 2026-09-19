import json, statistics as st
from math import floor, ceil

CS = [2, 3, 5, 10, 100]           # pre-committed multipliers, fixed before looking at the data
QUANTILES = ["p50", "p90", "p99", "p999", "max"]


def _load(name):
    return json.load(open(f"out/{name}.json"))


def _selfcheck(w):
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
