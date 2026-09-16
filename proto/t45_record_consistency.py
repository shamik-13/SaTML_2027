"""
Cross-check the numbers quoted in docs/04_EXPERIMENTS_AND_FINDINGS.md against the JSON they
came from.

The record is written by hand from script output, and a transcription error there is
invisible to every other check in this project: the scripts pass, the self-tests pass, the
audits pass, and the paper quotes a number no artefact contains.  This closes that gap for
the load-bearing figures.  It caught one fabricated table row during E10's write-up.

No data files, no detector: reads out/*.json and the record.  Runtime ~1 s.
"""
import json, pathlib, sys

HERE = pathlib.Path(__file__).parent
REC = (HERE.parent / "docs" / "04_EXPERIMENTS_AND_FINDINGS.md").read_text()
OK, BAD, SKIP = [], [], []


def load(name):
    f = HERE / "out" / name
    if not f.exists():
        SKIP.append(name)
        return None
    return json.load(open(f))


def q(label, cond, detail=""):
    (OK if cond else BAD).append(f"{label}   {detail}" if detail else label)


def quoted(text):
    """A literal string that must appear in the record."""
    q(f"record contains {text!r}", text in REC)


# ---------------------------------------------------------------- E11 (extends 4.33)
d = load("t32_B1.json")
if d:
    c = d["coincidence"]
    q("E11 saturated == landing == 101",
      c["n_level_saturated"] == 101 == c["n_minimal_pad_lands_in_window"])
    q("E11 147 exported rows", len(c["per_episode"]) == 147)
    q("E11 152 alerts of which 5 false",
      c["n_rejections_all"] == 152 and c["n_false_positive_alerts"] == 5)
    q("E11 zero unsaturated landers", c["n_unsaturated_landing"] == 0)
    q("E11 median excess 1.90e-9", abs(c["median_excess_over_lam"] - 1.9019e-9) < 1e-12)
    quoted("**The equality 101 = 101 is forced, not a property of this window**")

# ---------------------------------------------------------------- E4 (4.37)
d = load("t38_E4.json")
if d:
    for pos in ("0.55", "0.85"):
        b = d["baseline"][pos]
        q(f"E4 q0 at {pos} is in (0,1)", 0.0 < b["q0"] < 1.0, f"{b['q0']:.4f}")
        q(f"E4 eps* at {pos} is about one flow",
          0.5 <= b["eps_star"] * b["Ncal"] <= 5.0, f"{b['eps_star']*b['Ncal']:.2f} flows")
    jr = [r for r in d["jrows"] if r["injection"] == "adversarial" and r["j"] == 1]
    q("E4 one adversarial flow takes every window to zero recall",
      all(r["lond"]["recall"] == 0.0 for r in jr), f"{len(jr)} windows")
    q("E4 no row reports fdp 0.0 with zero rejections",
      all(not (r["lond"]["rejections"] == 0 and r["lond"]["fdp"] == 0.0)
          for r in d["rows"] + d["jrows"]))
    d4 = d.get("d4prime", [])
    q("E4 the ceiling channel is exactly 1/(1+eps)",
      all(abs(r["ratio"] * r["one_plus_eps"] - 1.0) < 1e-9 for r in d4 if r["a"]),
      f"{len(d4)} rows")
    q("E4 the stealth arm leaves the threshold unmoved",
      all(abs(r["thresh"] - next(x["thresh"] for x in d4
                                 if x["pos"] == r["pos"] and x["a"] == 0)) < 1e-12
          for r in d4))
    q("E4 the stealth arm leaves recall unchanged",
      all(r["recall"] == next(x["recall"] for x in d4
                              if x["pos"] == r["pos"] and x["a"] == 0) for r in d4))
    for pos, eff in (("0.55", 0.050008), ("0.85", 0.054195)):
        w = max((r for r in d4 if str(r["pos"]) == pos), key=lambda r: r["one_plus_eps"])
        q(f"E4 worst effective q at {pos} = {eff}", abs(w["effective_q"] - eff) < 5e-7,
          f"{w['effective_q']:.6f}")
    marg = {str(r["pos"]): round(r["margin"], 6) for r in d["rows"]}
    q("E4 the margin is constant at 0.999984 / 0.999978",
      all(abs(r["margin"] - (0.999984 if r["pos"] == 0.55 else 0.999978)) < 1e-6
          for r in d["rows"]))
    q("E4 one adversarial flow takes rejections to 0 at both windows",
      all(r["lond"]["rejections"] == 0 for r in d["jrows"]
          if r["injection"] == "adversarial" and r["j"] >= 1))
    for pos, q0 in (("0.55", 0.9043), ("0.85", 0.7623)):
        q(f"E4 q0 at {pos} = {q0}", abs(d["baseline"][pos]["q0"] - q0) < 5e-5,
          f"{d['baseline'][pos]['q0']:.4f}")
    q("E4 every D3b Monte-Carlo row agrees with the hypergeometric",
      all(r["verdict"] in ("ok", "no power") for r in d["d3b_mc"]))
    quoted("**the tolerable number of adversarial mislabels is exactly `k \u2212 1`**")

# ---------------------------------------------------------------- E6 (4.38)
d = load("t39_E6.json")
if d:
    g0 = d["grouping"]["0"]
    w = next(x for x in g0["per_window"] if abs(x["pos"] - 0.70) < 1e-9)
    q("E6 the frozen grouping is the worst feasible config at 0.70", w["frozen_is_worst"])
    q("E6 oracle at 0.70 = 0.5943", abs(w["oracle"] - 0.5943) < 1e-3, f"{w['oracle']:.4f}")
    a0 = [r for r in g0["E6a"] if r["transfer_defined"]]
    q("E6 grouping worst transfer regret 0.579",
      abs(max(r["regret"] for r in a0) - 0.5786) < 1e-3)
    c0 = [r for r in d["cap"]["0"]["E6a"] if r["transfer_defined"]]
    q("E6 cap worst transfer regret 0.012",
      abs(max(r["regret"] for r in c0) - 0.0122) < 1e-3)
    q("E6 objectives disagree at 5 of 5 windows", g0["n_objective_disagreements"] == 5)
    q("E6 30 of 35 configs feasible everywhere", d["feasibility"]["n_always_feasible"] == 30)
    quoted("worst regret **0.579**")
    quoted("worst regret **0.012**")

# ---------------------------------------------------------------- E8 (4.40)
d = load("t41_E8.json")
if d:
    bb = [r for r in d["budgets_priced"]
          if r["pos"] == 0.85 and r["pool"].startswith("black-box (most")]
    one = next(r for r in bb if r["budget"].startswith("padding, one episode (median)"))
    st = next(r for r in bb if r["budget"].startswith("ADDIS spending-state"))
    q("E8 one alert = 13,328 wire bytes", round(one["wire_bytes"]["0.5"]) == 13328)
    q("E8 one alert = 15 bit/s", round(one["bits_per_s"]) == 15)
    q("E8 state attack = 36.1 GB", abs(st["wire_bytes"]["0.5"] / 1e9 - 36.07) < 0.05)
    q("E8 state attack = 33.4 Mbit/s", abs(st["bits_per_s"] / 1e6 - 33.4) < 0.1)
    q("E8 state attack needs 4 hosts at 10 Mbit/s", st["hosts"]["10000000"] == 4)
    q("E8 the state budget uses this window's own span", st["window_is_own_span"])
    vr = d["volume_ratio"]["0.85"]["ratios"]["ADDIS spending-state attack"]
    q("E8 37.5x the window", abs(vr["vs_window"] - 37.5) < 0.05)
    q("E8 5.6x the dataset", abs(vr["vs_dataset"] - 5.63) < 0.05)
    q("E8 duration unit is microseconds",
      all(v["selected"] == "microseconds" for v in d["duration_unit"].values()))
    q("E8 unit margin >= 2 decades",
      all(v["margin_decades"] >= 2.0 for v in d["duration_unit"].values()))
    q("E8 the black-box service is the same on the training window",
      all(v["same"] for v in d["blackbox_service"].values()))
    quoted("33.4 Mbit/s")
    quoted("**15 bit/s**")
    quoted("2.403 h")

# ---------------------------------------------------------------- E9 (4.41)
d = load("t42_E9.json")
if d:
    q("E9 zero varying statistics", sum(1 for r in d["rows"] if r["varies"]) == 0)
    q("E9 36 statistics measured", len(d["rows"]) == 36)
    q("E9 exposure 651 / 412 tie-movable episodes",
      d["exposure"]["0.55"]["n_tied"] == 651 and d["exposure"]["0.85"]["n_tied"] == 412)
    q("E9 largest tie block is 3", d["exposure"]["0.55"]["B_max"] == 3)
    q("E9 every randomised order differs from the deterministic one",
      all(v["n_orders_changed"] == v["n_draws"] for v in d["power"].values()))
    q("E9 a draw moves ~324 / ~205 positions",
      abs(d["power"]["0.55"]["mean_positions_moved"] - 324) < 3
      and abs(d["power"]["0.85"]["mean_positions_moved"] - 205) < 3)
    quoted("all 36 statistics")

# ---------------------------------------------------------------- E10 (4.42)
d = load("t43_E10.json")
if d:
    bw = d["xwindow_by_window"]
    for pos, val in (("0.55", 3.0), ("0.62", 4.5), ("0.7", 62.0), ("0.77", 35.0),
                     ("0.85", 35.25)):
        q(f"E10 median r_90 at {pos} = {val}", abs(bw[pos] - val) < 1e-9, f"{bw[pos]}")
    q("E10 measurable at all four other windows",
      d["xwindow"]["n_other_windows_measurable"] == 4)
    q("E10 cheaper at three of the four", d["xwindow"]["n_other_windows_cheaper"] == 3)
    q("E10 the black-box pool never fires at any window",
      all(p["p_fire"] == 0.0 for r in d["rows"] for nm, p in r["pools"].items()
          if nm == "black-box"))
    quoted("| median `r_90` (flows) | 3 | 4.5 | 62 | 35 | **35.25** |")

# ---------------------------------------------------------------- host-pair placement (4.30)
d = load("t46_hostpair.json")
if d:
    sm = d["summary"]
    q("t46 674 detected episodes over 9 cells",
      sm["n_detected"] == 674 and sm["n_cells"] == 9,
      f"{sm['n_detected']} over {sm['n_cells']}")
    q("t46 every attack host pair is 100% malicious",
      sm["n_pairs_all_malicious"] == sm["n_detected"])
    q("t46 no episode has a host-pair-matched pool available",
      sm["n_with_pool_available"] == 0)
    q("t46 the empirical route is closed", sm["empirical_route_closed"])
    fs = d["feature_set"]
    q("t46 33 features, none naming an endpoint identity",
      fs["n_features"] == 33 and fs["identity_features"] == []
      and fs["score_invariant_to_host_pair"])
    quoted("**674 detected episodes** — *every* episode's host pair is **100%")
    quoted("**no IP address, no port, and no endpoint")

# ---------------------------------------------------------------- W2 matched frontier (4.19)
d = load("t20_T8.json")
if d and "per_pos" in d:
    def _mrow(pos, name):
        return next(m for m in d["per_pos"][pos]["methods"] if m["method"] == name)
    def _fr(pos, qv):
        return next(f for f in d["per_pos"][pos]["frontier"] if abs(f["q"] - qv) < 1e-9)
    # primary window 0.55: the numbers the paper's tab:frontier now leads with
    p55 = d["per_pos"]["0.55"]
    q("t20 0.55 primary window shape", p55["T"] == 57368 and p55["NM"] == 275
      and p55["NC"] == 2448993)
    m55 = _mrow("0.55", "online FDR (e-LOND, mean rule)")
    q("t20 0.55 e-LOND mean rule: 18 alerts, recall 0.065",
      m55["alerts"] == 18 and abs(m55["recall"] - 0.0654545) < 1e-4 and m55["fdp"] == 0.0)
    f55 = _fr("0.55", 0.0)
    q("t20 0.55 frontier at FDP=0: recall 0.378 on 104 alerts",
      f55["alerts"] == 104 and abs(f55["recall"] - 0.378182) < 1e-4)
    q("t20 0.55 no method leaves recall on the table (gap <= 0.040)",
      max(m["gap"] for m in p55["methods"]) <= 0.0401)
    # stress window 0.85: must reproduce the original single-window numbers exactly
    m85 = _mrow("0.85", "online FDR (e-LOND, mean rule)")
    q("t20 0.85 e-LOND mean rule unchanged: 72 alerts, recall 0.282",
      m85["alerts"] == 72 and abs(m85["recall"] - 0.282353) < 1e-4)
    f85 = _fr("0.85", 0.0)
    q("t20 0.85 frontier at FDP=0 unchanged: recall 0.459 on 117 alerts",
      f85["alerts"] == 117 and abs(f85["recall"] - 0.458824) < 1e-4)
    # the record must lead with the valid window
    quoted("0.55 (evidence a valid e-value)")
    quoted("nearly 6× the recall at the same zero error")

# ---------------------------------------------------------------- W7 fixed-unit coverage (4.44)
d = load("t47_W7.json")
if d:
    q("t47 fixed atomic denominators 1899 / 1973",
      d["denom"]["0.55"] == 1899 and d["denom"]["0.85"] == 1973)

    def _sd(pos):
        return sorted([r for r in d["rows"] if str(r["pos"]) == pos and r["family"] == "src-dst"],
                      key=lambda r: r["bucket_s"])
    s55 = _sd("0.55")
    # blur climbs monotonically 1 -> ~38 with coarsening (the resolution cost)
    blur55 = [r["blur_mal_atoms_per_alert"] for r in s55]
    q("t47 blur is monotone non-decreasing with coarsening (0.55)",
      all(b is not None for b in blur55) and blur55 == sorted(blur55),
      f"{[round(b,1) for b in blur55]}")
    q("t47 blur runs 1.0 -> ~38 at 0.55",
      abs(blur55[0] - 1.0) < 1e-9 and 35 <= blur55[-1] <= 42, f"{blur55[0]:.1f}->{blur55[-1]:.1f}")
    # fixed coverage RISES with coarsening at 0.55 (the finding that weakens 'recall falls')
    cov55 = [r["cov_fixed"] for r in s55]
    q("t47 fixed coverage rises with coarsening (0.55): 0.020 -> 0.385",
      abs(cov55[0] - 0.020) < 5e-3 and abs(cov55[-1] - 0.385) < 5e-3 and cov55[-1] > cov55[0])
    # poly recall_moving at 2h matches t21c exactly -> not a bug
    r2h = next(r for r in s55 if r["bucket_s"] == 7200)
    q("t47 poly recall_moving at 2h/0.55 matches t21c (0.0655)",
      abs(r2h["recall_moving"] - 0.0654545) < 1e-4)
    quoted("hardened C2 the reviewer asked for")

# ---------------------------------------------------------------- W3 controlled dilution (4.45)
d = load("t48_W3.json")
if d:
    for pos in ("0.55", "0.85"):
        pr = d["premise"][pos]; ep = d["episodes"][pos]
        q(f"t48 pad fire rate is exactly 0 at {pos} (premise measured)",
          pr["pad_fire_rate"] == 0.0 and pr["pad_mean_e"] == 0.0)
        q(f"t48 measured == closed-form on every detected episode at {pos}",
          ep["n_match"] == ep["n_detected"] and ep["n_detected"] > 0,
          f"{ep['n_match']}/{ep['n_detected']}")
    q("t48 18/18 at guarantee window, 72/72 at stress window",
      d["episodes"]["0.55"]["n_match"] == 18 and d["episodes"]["0.85"]["n_match"] == 72)
    q("t48 median r* reproduces Table I (118 at 0.55, 5202 at 0.85)",
      d["episodes"]["0.55"]["median_r_closed"] == 118.0
      and abs(d["episodes"]["0.85"]["median_r_closed"] - 5201.5) < 1.0)
    quoted("confirmed by a controlled experiment")
    # ---- R4 (4.55): the same attack under the CANONICAL key-hash within-bucket order ----
    kh = d.get("episodes_keyhash")
    q("t48 carries the canonical key-hash arm (review 6, R4)", bool(kh))
    if kh:
        for pos in ("0.55", "0.85"):
            e = kh[pos]
            q(f"t48 key-hash order: every detection suppressible at {pos}",
              e["n_suppressible"] == e["n_detected"] == e["n_match"] and e["n_detected"] > 0,
              f"{e['n_suppressible']}/{e['n_detected']}")
        q("t48 key-hash detections are 3 and 34 (matching t53's independent count)",
          kh["0.55"]["n_detected"] == 3 and kh["0.85"]["n_detected"] == 34)
        q("t48 key-hash median r* is 24 and 115.5 (matching t53's independent pricing)",
          kh["0.55"]["median_r_closed"] == 24.0
          and abs(kh["0.85"]["median_r_closed"] - 115.5) < 1e-6)
        q("t48 key-hash primary costs are 23, 24, 33",
          kh["0.55"]["r_closed_sorted"] == [23, 24, 33],
          str(kh["0.55"]["r_closed_sorted"]))
    e53 = load("t53_ordering.json")
    if e53:
        for pp in e53["positions"]:
            k = f"{pp['pos']}"
            if kh and k in kh:
                c = pp["named"]["bucket, hashed-key (canonical)"]
                q(f"t48 and t53 agree on the canonical order at {k} (independent implementations)",
                  c["tp"] == kh[k]["n_detected"]
                  and abs(c["median_rstar"] - kh[k]["median_r_closed"]) < 1e-6,
                  f"t53 {c['tp']}/{c['median_rstar']} vs t48 {kh[k]['n_detected']}/"
                  f"{kh[k]['median_r_closed']}")

# ------------------------------------------- R3: the canonical within-bucket order (4.58)
d53 = load("t53_ordering.json")
d28 = load("t28b_reallevel.json")
if d53 and d28:
    tbo = d28.get("table1_by_order")
    q("t28b carries the per-order arms (review 7, R3)", bool(tbo))
    q("t53 covers all five windows and both seeds",
      len(d53["rows"]) == 10 and sorted({r["pos"] for r in d53["rows"]}) ==
      [0.55, 0.62, 0.70, 0.77, 0.85],
      f"{len(d53['rows'])} rows")
    # (1) the shipped first-flow record is UNCHANGED by the refactor: t28b's table1 is what the
    #     paper transcribed before item R3, and t53 recomputes it through a different code path
    if tbo:
        for k, r in d28["table1"].items():
            q(f"t28b first-flow arm unchanged at {k}",
              tbo["first-flow"][k]["detected_elond"] == r["detected_elond"]
              and tbo["first-flow"][k]["med_pad_real"] == r["med_pad_real"])
    for r in d53["rows"]:
        k = f"{r['pos']}_{r['seed']}"
        q(f"t53 and t28b agree on first-flow at {k} (independent pricing)",
          r["first_flow_tp"] == d28["table1"][k]["detected_elond"]
          and r["first_flow_median_rstar"] == d28["table1"][k]["med_pad_real"],
          f"t53 {r['first_flow_tp']}/{r['first_flow_median_rstar']} vs "
          f"t28b {d28['table1'][k]['detected_elond']}/{d28['table1'][k]['med_pad_real']}")
        if tbo:
            q(f"t53 and t28b agree on the CANONICAL order at {k}",
              r["canonical_tp"] == tbo["keyhash"][k]["detected_elond"]
              and r["canonical_median_rstar"] == tbo["keyhash"][k]["med_pad_real"],
              f"t53 {r['canonical_tp']}/{r['canonical_median_rstar']} vs "
              f"t28b {tbo['keyhash'][k]['detected_elond']}/{tbo['keyhash'][k]['med_pad_real']}")
    # (2) first-flow really is the optimistic end, at every window AND seed
    q("t53: first-flow is an upper bound on detection at every window and seed",
      d53["first_flow_is_upper_bound_everywhere"] and d53["canonical_never_exceeds_first_flow"])
    # strict exceedance wherever ANY order detects anything; at 0.70 seed 1 nothing detects under
    # any order, so first-flow ties the ensemble at 0 -- a degenerate tie, not a counterexample
    q("t53: first-flow strictly exceeds the 50-order ensemble maximum wherever anything detects",
      all(r["first_flow_tp"] > r["ensemble"]["tp_max"]
          for r in d53["rows"] if r["ensemble"]["tp_max"] > 0 or r["first_flow_tp"] > 0),
      str([(r["pos"], r["seed"]) for r in d53["rows"]
           if r["ensemble"]["tp_max"] == 0 and r["first_flow_tp"] == 0]))
    # (3) the ZERO results are the feasibility boundary, not a bug.  Before the first rejection
    #     e-LOND offers exactly A*gamma_t, so the run rejects nothing IFF no episode in the
    #     feasible prefix clears -- an exact characterisation the stage asserts per arm.
    bs = [nr["boundary"] for r in d53["rows"] for nr in r["named"].values()]
    q("t53: zero rejections IFF nothing clears inside the feasible prefix (all arms)",
      all(b["zero_iff_empty_prefix"] for b in bs), f"{len(bs)} arms")
    q("t53: the cold-start window matches its closed form on every arm",
      all(b["cold_start_matches_closed_form"] for b in bs))
    q("t53: nothing outside the feasible prefix can ever clear (evidence ceiling holds)",
      all(b["n_clearing_in_prefix"] == b["n_clearing_anywhere"] for b in bs))
    cs = {r["pos"]: r["named"]["bucket, hashed-key (canonical)"]["boundary"]["cold_start_steps"]
          for r in d53["rows"] if r["seed"] == 0}
    q("t53 cold-start windows are 902/902/865/824/748 steps",
      [cs[x] for x in (0.55, 0.62, 0.70, 0.77, 0.85)] == [902, 902, 865, 824, 748], str(cs))
    canon = {r["pos"]: r["canonical_tp"] for r in d53["rows"] if r["seed"] == 0}
    q("t53 canonical detections are 3/11/0/0/34 at seed 0",
      [canon[x] for x in (0.55, 0.62, 0.70, 0.77, 0.85)] == [3, 11, 0, 0, 34], str(canon))
    zero = [r["pos"] for r in d53["rows"] if r["seed"] == 0
            and r["named"]["bucket, hashed-key (canonical)"]["boundary"]["n_clearing_anywhere"] == 0]
    q("t53: at 0.70 and 0.77 NO episode clears its own step anywhere under the canonical order",
      zero == [0.70, 0.77], str(zero))
    # (4) padding is invariant under the canonical order, at every window and seed
    q("t53: a pad moves 0 other hypotheses under the key-hash at every window and seed",
      all(r["perturbation"]["others_moved_hashed_key"] == 0 for r in d53["rows"]))
    q("t53: a pad moves 373 other hypotheses under first-flow at 0.55",
      [r for r in d53["rows"] if r["pos"] == 0.55 and r["seed"] == 0][0]
      ["perturbation"]["others_moved_first_flow"] == 373)

# ------------------------------------------- R4: external semantic anchor (4.59)
d = load("t58_semantic_blur.json")
if d:
    sm = d["segment_map_check"]; rt = d["redteam"]; sm2 = d["summary"]
    q("t58 the bt_ segment map is corroborated, 83 agree / 0 disagree",
      sm["seg_agree"] == 83 and sm["seg_disagree"] == 0, str(sm))
    q("t58 39 compromise IPv4, 36 appearing as a flow endpoint",
      sm["n_compromise_ipv4"] == 39 and sm["n_present_as_endpoint"] == 36)
    q("t58 the record is 288 tasks / 295 timed steps / 155 with a timed step / 126 attributable",
      rt["n_tasks"] == 288 and rt["n_timed_steps"] == 295
      and rt["n_tasks_with_timed_step"] == 155 and rt["n_attributable"] == 126, str(rt))
    q("t58 the reference is usable at 3 of 10 (window, order) cells",
      sm2["n_windows_usable"] == 3 and sm2["n_window_order_cells"] == 10)
    q("t58 attribution beats its permutation null at 6 of 19 cells",
      sm2["n_beating_null_p975"] == 6 and sm2["n_compared_to_null"] == 19)
    # the load-bearing tracking result, and the two ways it fails elsewhere
    tw = d["summary"]["tracking"]
    q("t58 0.70 first-flow: steps/alert tracks the 5-minute proxy at Spearman +1.000 over 6 buckets",
      abs(tw["first-flow"]["per_window"]["0.7"]["steps_vs_atoms"] - 1.0) < 1e-9
      and tw["first-flow"]["per_window"]["0.7"]["n"] == 6)
    q("t58 0.70 key-hash: +0.800 over 4 buckets",
      abs(tw["keyhash"]["per_window"]["0.7"]["steps_vs_atoms"] - 0.8) < 1e-9)
    # average-rank Spearman: the tied 0.77 series reads +0.816, NOT the +1.000 that
    # argsort(argsort(.)) reported before the blind audit caught it
    q("t58 0.77 first-flow: +0.816 over 4 buckets (ties averaged, not +1.000)",
      abs(tw["first-flow"]["per_window"]["0.77"]["steps_vs_atoms"] - 0.8164965809277259) < 1e-6,
      str(tw["first-flow"]["per_window"]["0.77"]["steps_vs_atoms"]))
    # the SHIFT null is what decides how this result may be reported
    rws = [r for r in d["rows"] if r["steps_per_alert"] is not None]
    n_shift = sum(1 for r in rws if r["steps_per_alert"] > r["steps_per_alert_shiftnull_p975"])
    q("t58 the timeline-shift null is beaten at only 1 of 19 cells",
      n_shift == 1 and len(rws) == 19, f"{n_shift}/{len(rws)}")
    cj = sm2["conjuncts"]
    q("t58 the compromise-IP conjunct adds no alert the segment conjunct did not",
      cj["ip_adds_nothing_over_seg"] is True and cj["attributed_alerts"] == 215
      and cj["seg_only_alerts"] == 215 and cj["ip_only_alerts"] == 28
      and cj["temporal_only_alerts"] == 1617, str(cj))
    q("t58 0 compromise IPs appear only as a destination", d["n_compromise_ips_destination_only"] == 0)
    q("t58 the flow-span sensitivity is carried on every row",
      all("flow_span" in r for r in d["rows"]))
    us = sm2["usability"]
    q("t58 at 0.55/0.62 the failure is TEMPORAL: <=9% of alerts overlap the exercise in time",
      all(us[k]["frac_alerts_temporally_overlapping"] <= 0.10
          for k in ("0.55_keyhash", "0.62_keyhash", "0.62_first-flow")),
      str({k: round(us[k]["frac_alerts_temporally_overlapping"], 3)
           for k in ("0.55_keyhash", "0.62_keyhash", "0.62_first-flow")}))
    q("t58 at 0.85 the failure is SPATIAL: alerts overlap in time but nothing attributes",
      all(us[k]["n_alerts_temporally_overlapping"] > 0 and us[k]["n_alerts_attributed"] == 0
          for k in ("0.85_keyhash", "0.85_first-flow")))
    q("t58 only 2 of the 17 tasks with a timed step at 0.85 are attributable at all",
      [w for w in d["windows"] if w["pos"] == 0.85][0]["n_tasks_attributable"] == 2
      and [w for w in d["windows"] if w["pos"] == 0.85][0]["n_tasks_in_window"] == 17)
    # confounds
    lg = d["reporting_lag"]
    q("t58 reporting lag median 170 s (IQR 115-279)",
      abs(lg["median_s"] - 170.455) < 0.5 and abs(lg["q25_s"] - 115.24) < 0.5
      and abs(lg["q75_s"] - 278.69) < 0.5, str(lg["median_s"]))
    q("t58 CIRCULARITY recorded: every attributed alert sits on a labelled-malicious episode",
      sm2["any_attributed_on_benign"] is False)
    rows = d["rows"]
    q("t58 at the 24 h bucket the observation ties its null in every case (spatial conjunct vacuous)",
      all(abs(r["steps_per_alert"] - r["steps_per_alert_null"]) < 1e-9 for r in rows
          if r["bucket_s"] == 86400 and r["steps_per_alert"] is not None))
    q("t58 attributed <= temporally overlapping <= issued, on every row",
      all(r["n_alerts_with_step"] <= r["temporal_only"]["n_alerts"] <= r["n_alerts"] for r in rows))
    q("t58 every reported localisation error is within half its bucket",
      all(r["loc_err_median_s"] is None or r["loc_err_median_s"] <= r["bucket_s"] / 2 + 1e-9
          for r in rows))

# ------------------------------------------- R5: realistic prevalence (4.60)
d = load("t59_prevalence.json")
if d:
    sm = d["summary"]; rows = d["rows"]
    q("t59 flow prevalence 10.06%, episode prevalence 0.48-0.81%",
      abs(100 * sm["flow_prevalence"] - 10.06) < 0.01
      and abs(100 * sm["episode_prevalence_range"][0] - 0.479) < 0.01
      and abs(100 * sm["episode_prevalence_range"][1] - 0.808) < 0.01,
      f"{100*sm['flow_prevalence']:.2f}%, {[round(100*x,3) for x in sm['episode_prevalence_range']]}")
    # the separation this stage exists to show
    q("t59 the PRIMARY arm holds the margin exactly fixed",
      sm["max_abs_margin_shift_to_1e4"] == 0.0)
    q("t59 the deletion arm shrinks T by at most 0.80% and RAISES the margin by up to +0.0129",
      abs(100 * sm["max_T_shrink_frac"] - 0.80) < 0.02
      and abs(sm["max_margin_shift_removed"] - 0.0129) < 5e-4,
      f"{100*sm['max_T_shrink_frac']:.2f}%, {sm['max_margin_shift_removed']:+.4f}")
    q("t59 the two thinning mechanisms agree to within 0.02 in bootstrap probability",
      sm["max_abs_variant_gap_at_1e4"] <= 0.0201, str(sm["max_abs_variant_gap_at_1e4"]))
    q("t59 e-LOND's bootstrap probability at pi=1e-4 is 0-40%",
      min(sm["elond_p_bootstrap_at_1e4"]) == 0.0 and max(sm["elond_p_bootstrap_at_1e4"]) <= 0.40,
      str(sm["elond_p_bootstrap_at_1e4"]))
    q("t59 the escapes collapse too (online e-BH and e-TOAD <= 40% at pi=1e-4)",
      max(sm["ebh_p_bootstrap_at_1e4"]) <= 0.40
      and max(x or 0 for x in sm["etoad_p_bootstrap_at_1e4"]) <= 0.40)
    # the pure-null arm, correctly scoped
    q("t59 no pure-null stream rejects, under either procedure",
      sm["n_pure_null_rows_with_any_rejection"] == 0
      and sm["n_pure_null_rows_with_any_rejection_ebh"] == 0)
    q("t59 the null arm is 5 effective streams, not 10, and P(zero | 4.5%) = 0.79",
      sm["n_pure_null_effective_streams"] == 5 and sm["n_pure_null_rows"] == 10
      and abs(sm["prob_zero_if_true_rate_045"] - 0.79) < 0.005
      and sm["null_arm_can_test_the_simulated_rate"] is False,
      f"{sm['prob_zero_if_true_rate_045']:.3f}")
    # no positive target may silently realise as the pure null (the audit's MAJOR)
    q("t59 every positive prevalence target realises above zero",
      all(r["realised_prevalence_fixed_T"] > 0 for r in rows
          if r["pi_target"] is not None and r["pi_target"] > 0))
    q("t59 pi=1e-2 is absent, being above the observed episode prevalence",
      all(r["pi_target"] != 1e-2 for r in rows))
    # the observed arm must reproduce the stage that owns those numbers
    d28 = load("t28b_reallevel.json")
    if d28:
        tb = d28.get("table1_by_order")
        bad = [(r["pos"], r["order"]) for r in rows if r["pi_target"] is None and tb
               and abs(r["elond"]["tp_mean"] - tb[r["order"]][f"{r['pos']}_0"]["detected_elond"]) > 1e-9]
        q("t59's observed arm reproduces t28b's detection counts under both orders", not bad, str(bad))
    d53 = load("t53_ordering.json")
    if d53:
        want = {r["pos"]: r["named"]["bucket, hashed-key (canonical)"]["boundary"]["cold_start_steps"]
                for r in d53["rows"] if r["seed"] == 0}
        q("t59's cold-start windows match t53's, window for window",
          all(w["cold_start_steps"] == want[w["pos"]] for w in d["windows"]))

# ------------------------------------------- t60: suppression by insertion (4.61)
d = load("t60_positional.json")
if d:
    sm = d["summary"]; rows = d["rows"]; gm = d.get("group_max_rows", [])
    live = [r for r in rows if r.get("n_targets")]
    q("t60 every true detection is suppressible by insertion alone",
      sm["all_targets_suppressible"] is True)
    q("t60 per EPISODE padding is cheaper at every cell (insertion does not beat it for one alert)",
      sm["n_cells_positional_cheaper"] == 0 and sm["n_cells_compared"] == 12,
      f"{sm['n_cells_positional_cheaper']}/{sm['n_cells_compared']}")
    q("t60 per WINDOW insertion is cheaper at 10 of 12 cells (7 at two flows per group)",
      sm["n_cells_positional_cheaper_per_window"] == 10
      and sm["n_cells_cheaper_per_window_at_2_flows"] == 7,
      f"{sm['n_cells_positional_cheaper_per_window']}, {sm['n_cells_cheaper_per_window_at_2_flows']}")
    q("t60 the window-silencing ratio is an UPPER bound with a heavy tail, and says so",
      sm["max_pad_sum_top10_share"] > 0.9 and sm["median_window_silencing_ratio_UPPER"] < 100,
      f"top10 share {sm['max_pad_sum_top10_share']:.3f}, "
      f"median ratio {sm['median_window_silencing_ratio_UPPER']:.1f}")
    q("t60 targeted G* is never cheaper than the prefix cost",
      all(r["targeted_gstar_median"] >= r["zero"]["gstar_median"] for r in live))
    q("t60 the targeted closed form is replay-verified with zero failures",
      all(r["targeted_closed_form_replay_failures"] == 0 for r in live)
      and all(r["targeted_closed_form_replay_checks"] > 0 for r in live))
    # the group-MAX arm: the construction non-claim 21 is about
    q("t60 prices the group-calibrated MAX pipeline, reproducing t57's firing counts",
      bool(gm) and sm["group_max_all_suppressible"] is True)
    d57 = load("t57_group_calibration.json")
    if d57 and gm:
        want = {r["pos"]: r["stats"]["max"]["n_firing"] for r in d57["rows"] if r["seed"] == 0}
        q("t60's group-MAX firing counts equal t57's exactly",
          all(r["n_firing_groups"] == want[r["pos"]] for r in gm),
          str({r["pos"]: (r["n_firing_groups"], want[r["pos"]]) for r in gm}))
    q("t60 group-MAX has 42 true detections at 0.85 and a cold-start window of only 65 groups",
      any(r["pos"] == 0.85 and r["n_targets"] == 42 and r["cold_start_steps"] == 65 for r in gm))
    q("t60 group-MAX cold-start windows are 65-86 groups, far below the flow pipeline's 748-902",
      all(65 <= r["cold_start_steps"] <= 86 for r in gm if r["n_targets"]))
    q("t60 every group-MAX detection is suppressible by 62-207 insertions",
      all(r["targeted_gstar_max"] <= 300 for r in gm if r["n_targets"]))
    # the keyspace search is priced for the RIGHT event, and only where it exists
    kh = [r for r in live if r["order"] == "keyhash"]
    q("t60 the targeted keyspace search is dearer than the prefix one (a narrower interval)",
      all(r["zero"]["key_trials_targeted_median"] >= r["zero"]["key_trials_prefix_median"]
          for r in kh))
    q("t60 no trial count is emitted for the keyed order (it cannot be ranked offline)",
      all(r["zero"].get("key_trials_targeted_median") is None
          for r in live if r["order"] != "keyhash"))
    q("t60 the keyed order does NOT stop the attack, only the offline search",
      any(r["order"] == "keyed" and r["n_targets"] > 0 for r in rows))
    q("t60 every target sits in the first bucket, so no earlier bucket is available",
      all(r["all_targets_in_first_bucket"] for r in live))

# ------------------------------------------- A1 metadata strata (4.55, review 6 item R5)
d = load("t55_a1_strata.json")
if d:
    m = d["multiplicity"]
    q("t55 tests only cells with >= 10 firing flows",
      m["min_events"] == 10 and m["n_tests"] + m["n_untestable"] == m["n_cells"],
      f"{m['n_tests']} tested + {m['n_untestable']} untested = {m['n_cells']}")
    q("t55 428 of 536 cells carry no test, 419 of them firing <10 times",
      m["n_cells"] == 536 and m["n_untestable"] == 428 and m["n_low_events"] == 419)
    q("t55 the BY family is EVERY cell, not just the tested ones (no selection on the outcome)",
      m["n_contrast_tests"] == m["n_cells"])
    q("t55 40 strata survive Benjamini-Yekutieli, 55 survive BH",
      m["n_flag_by"] == 40 and m["n_flag_bh"] == 55)
    q("t55 BY is the STRICTER correction (survivors <= BH's)", m["n_flag_by"] <= m["n_flag_bh"])
    q("t55 all 5 k=1 survivors sit at the 0.85 violation window, none at a guarantee window",
      m["n_flag_by_at_k1"] == 5
      and {f["pos"] for f in m["flagged_by"] if f["k"] == 1} == {0.85})
    q("t55 32 stratum-vs-marginal contrasts survive BY, at every window",
      m["n_flag_contrast_by"] == 32
      and len({f["pos"] for f in m["flagged_contrast"]}) == len(d["per_position"]))
    q("t55 the population is benign flows of TRUE-NULL episodes only",
      all(pp["n_benign_truenull"] <= pp["n_benign_all"] for pp in d["per_position"]))
    _best = max(m["flagged_contrast"], key=lambda f: f["contrast_ci"][0])
    q("t55 the largest-lower-bound contrast is arity m=21-100 at 0.77, k=1000, 9.32 [6.48,13.69]",
      _best["stratum"] == "m=21-100" and _best["pos"] == 0.77 and _best["k"] == 1000
      and abs(_best["contrast"] - 9.32) < 0.01 and abs(_best["contrast_ci"][0] - 6.48) < 0.01)
    _bigp = max(m["flagged_contrast"], key=lambda f: f["contrast"])
    q("t55 the largest-point-estimate contrast is a DIFFERENT cell (service, 0.62, 14.38x)",
      _bigp["family"] == "service" and _bigp["pos"] == 0.62
      and abs(_bigp["contrast"] - 14.38) < 0.01)
    q("t55 window 0.70 has no BY-surviving stratum on the raw ratio",
      0.7 in d["windows_with_no_by_flag"])
    q("t55 reports the bucket-family sensitivity on the contrast count",
      "n_flag_contrast_excl_bucket" in m
      and m["n_flag_contrast_excl_bucket"] <= m["n_flag_contrast_by"])
    q("t55 both bootstraps are clustered (calibration AND test side)",
      "host pairs" in d["note"] or "host-pair" in d["config"]["interval"]
      or "calibration" in d["config"]["interval"])

# ---------------------------------------------------------------- R3 firing-count Poisson CIs (4.3)
d = load("t50_calib_ci.json")
if d:
    rows = {(r["pos"], r["seed"]): r for r in d["rows"]}
    # guarantee windows: the interval must INCLUDE 1 (cannot prove validity)
    for pos in (0.55, 0.62, 0.70, 0.77):
        r = rows[(pos, 0)]
        q(f"t50 guarantee window {pos} CI includes 1 (seed 0)",
          r["ci_lo"] <= 1.0 <= r["ci_hi"] and not r["excludes_one"],
          f"[{r['ci_lo']:.2f}, {r['ci_hi']:.2f}]")
    # stress window: the interval must EXCLUDE 1 at both seeds (clear violation)
    for seed in (0, 1):
        r = rows[(0.85, seed)]
        q(f"t50 stress window 0.85 CI excludes 1 (seed {seed})",
          r["ci_lo"] > 1.0 and r["excludes_one"], f"[{r['ci_lo']:.2f}, {r['ci_hi']:.2f}]")
    q("t50 0.55 seed 0: k=1, ratio 1.07, 95% CI [0.03, 5.96]",
      rows[(0.55, 0)]["n_fired_benign"] == 1
      and abs(rows[(0.55, 0)]["ci_lo"] - 0.03) < 0.01
      and abs(rows[(0.55, 0)]["ci_hi"] - 5.96) < 0.05)

# ---------------------------------------------------------------- R7 host-conditioned detector (4.47)
d = load("t49_R7.json")
if d:
    # leakage guard: the forbidden endpoint columns really are perfect predictors (so, excluded)
    q("t49 label_src=1 and label_dst=1 both have attack-rate 1.0 (why they are excluded)",
      d["leakage"]["label_src"]["attack_rate"] == 1.0 and d["leakage"]["label_dst"]["attack_rate"] == 1.0)
    q("t49 causal features validated against brute force (0 mismatches, both sides)",
      d["features"]["n_validation_mismatches"] == 0)
    q("t49 strongest host feature is src_ddst (rho ~ +0.34), no |corr| near 1 (no leakage)",
      abs(d["features"]["corr_with_y"]["src_ddst"] - 0.343) < 0.02
      and max(abs(v) for v in d["features"]["corr_with_y"].values()) < 0.5)
    b55 = d["partB"]["0.55"]; b85 = d["partB"]["0.85"]
    q("t49 host detector is competent: AUROC 0.95 (0.55) / 1.00 (0.85), both above flow-only",
      abs(b55["host"]["auroc"] - 0.954) < 0.01 and b85["host"]["auroc"] > 0.999
      and b55["host"]["auroc"] > b55["flow_only"]["auroc"] and b55["host"]["elond_detections"] > 0)
    # primary window: transfer holds -- grafted pads fire 0 AND detector fires on 0 real benign flows
    c55 = d["partC"]["0.55"]; o55 = d["ood"]["0.55"]
    q("t49 primary window: grafted pads fire 0 over 4M trials and hold",
      d["premise"]["0.55"]["pad_fire_rate"] == 0.0 and c55["max_pad_fire"] == 0.0
      and c55["transfer_verdict"].startswith("holds"))
    q("t49 primary window: host detector fires on 0 real benign flows (consistent, not OOD)",
      o55["host_real_benign_fires"] == 0 and not c55["ood_extrapolation"])
    # stress window: grafted pads fire, but on ~0 real benign flows -> OOD, needs a testbed
    c85 = d["partC"]["0.85"]; o85 = d["ood"]["0.85"]
    q("t49 stress window: grafted pads fire (~0.43) but detector fires on 3 of 1.6M real benign",
      c85["max_pad_fire"] > 0.3 and o85["host_real_benign_fires"] == 3
      and o85["host_real_benign_fire_rate"] < 1e-5)
    q("t49 stress window verdict is inconclusive-OOD (boundary needs a testbed)",
      c85["ood_extrapolation"] and c85["transfer_verdict"].startswith("inconclusive-OOD"))
    q("t49 primary pool is 100% benign; stress pool is only ~12% benign (attack-saturated)",
      d["premise"]["0.55"]["pool_benign_frac"] == 1.0
      and abs(d["premise"]["0.85"]["pool_benign_frac"] - 0.117) < 0.02)
    q("t49 stress-window firing is driven by dst_dsrc (ablation attribution)",
      c85["responsible_feature"] == "dst_dsrc")
    q("t49 primary-window padding cost is unchanged (mu_pad=0): host r* ~108 vs flow-level 118",
      c55["cost_note"].startswith("unchanged")
      and abs(c55["median_r_suppress_host"] - 108) < 3
      and abs(c55["median_r_star_flowlevel"] - 118) < 1)
    quoted("out-of-distribution")

# ---------------------------------------------------------------- R7 on AIT testbed, no graft (4.48)
d = load("t51_R7_ait.json")
if d:
    sm = d["summary"]; dl = sm["host_minus_flow_delta"]
    q("t51 AIT: 8 orgs, 45,001 attack flows (2.34% of ~1.9M)",
      len(d["config"]["scenarios"]) == 8 and d["config"]["n_malicious_flows"] == 45001)
    q("t51 AIT: absolute-time fields excluded from features (no schedule leakage)",
      all(c in d["config"]["feature_selection"] for c in ("ABSOLUTE-TIME", "epoch")))
    q("t51 AIT: competent cross-scenario detector (mean host AUROC ~0.97, attack recall ~0.66)",
      sm["mean_auroc_host"] > 0.95 and sm["mean_attack_fire_host"] > 0.5)
    q("t51 AIT: host negligible on 7/8 orgs -- median benign->victim delta ~0, host higher on only 1/8",
      abs(dl["median"]) < 0.002 and dl["n_folds_host_higher"] == 1)
    q("t51 AIT: host mean b2v (~1.1%) driven by one outlier; ~73x flow mean but far below graft",
      abs(sm["host_benign_to_victim"]["mean"] - 0.0114) < 0.003
      and sm["host_benign_to_victim"]["mean"] > 40 * sm["flow_benign_to_victim"]["mean"])
    q("t51 AIT: worst real host benign->victim fire (~8.9%) is ~5x below the LSPR23 grafted 0.43",
      abs(sm["host_benign_to_victim"]["max"] - 0.089) < 0.015
      and sm["host_benign_to_victim"]["max"] < 0.25 * sm["lspr23_grafted_fire"])
    q("t51 AIT verdict: graft was an OOD overestimate, padding substantially transfers",
      "OUT-OF-DISTRIBUTION OVERESTIMATE" in d["verdict"] and "substantially transfers" in d["verdict"])

# ---------------------------------------------------------------- structural checks
import re as _re
_fc = (HERE.parent / "docs" / "03_FROZEN_CLAIMS.md").read_text()
_wp = (HERE.parent / "docs" / "02_WORKPLAN_PHASE4.md").read_text()
_secs = set(_re.findall(r"^## (4\.\d+)", REC, _re.M))
_finds = set(_re.findall(r"^\*\*(F\d+)", REC, _re.M))
# 4.43 was pre-assigned to E12 and deliberately NOT written -- its output is a candidates
# table, which lives in proto/out/E12_triage.md.  02 mentions it only to say so, so it is an
# allowed dangling reference, the same way t44_E12_dataset2.py is an allowed missing script.
_ALLOWED_SECTIONS = {"4.43"}
for _n, _d in (("03", _fc), ("02", _wp)):
    _dang = set(_re.findall(r"§(4\.\d+)", _d)) - _secs - _ALLOWED_SECTIONS
    q(f"{_n}: every §4.N it cites exists in 04", not _dang, str(sorted(_dang)))
    q(f"{_n}: every F-number it cites exists in 04",
      not (set(_re.findall(r"\b(F\d+)\b", _d)) - _finds),
      str(sorted(set(_re.findall(r"\b(F\d+)\b", _d)) - _finds)))
_ids = [int(x) for x in _re.findall(r"^\| S(\d+) \|", _fc, _re.M)]
q("03: S rows are in order and unique",
  _ids == sorted(_ids) and len(set(_ids)) == len(_ids), str(_ids))
for _lab, _mk in (("C", "## C. Caveats"), ("D", "## D. Non-claims")):
    _b = _fc.split(_mk)[1].split("\n---")[0]
    _n2 = [int(x) for x in _re.findall(r"^\s*(\d+)\. \*\*", _b, _re.M)]
    q(f"03: section {_lab} is numbered 1..n", _n2 == list(range(1, len(_n2) + 1)), str(_n2))
_open = _re.findall(r"^## (E\d+) — .*?`\[ \]`", _wp, _re.M)
q("02 and 03 agree that the queue is complete",
  (not _open) == ("ALL TWELVE DONE" in _fc), f"open in 02: {_open}")
_SRCLIB = HERE.parent / "src" / "lib"   # t50+ live in src/lib, not proto/
for _d, _n in ((REC, "04"), (_fc, "03"), (_wp, "02")):
    _miss = [f for f in set(_re.findall(r"`(t\d+[a-z]*_[A-Za-z0-9_]+\.py)`", _d))
             if not ((HERE / f).exists() or (_SRCLIB / f).exists()) and f != "t44_E12_dataset2.py"]
    q(f"{_n}: every script it names exists", not _miss, str(_miss))

# ------------------------------------------- UAI 2026 procedures (4.56, review 7 item R1)
d = load("t56_uai26.json")
if d:
    m = d["summary"]
    rows = {(r["pos"], r["seed"], r["gamma"]): r for r in d["rows"]}
    q("t56 covers 5 positions x 2 seeds x 2 spending sequences", m["n_rows"] == 20)
    q("t56 e-TOAD(d_t=t) reproduces e-LOND by MASK at every row",
      m["etoad_immediate_equals_elond"])
    q("t56 e-TOAD(d_t=inf) reproduces online e-BH by MASK at every row",
      m["etoad_arc_equals_online_ebh"])
    q("t56 the donation cold-start boost never exceeds its 1/(1-alpha) ceiling",
      m["max_coldstart_boost"] <= m["boost_ceiling"] + 1e-12,
      f"{m['max_coldstart_boost']:.6f} <= {m['boost_ceiling']:.6f}")
    q("t56 the closed-e-LOND zero-evidence bound holds (ratio <= 1) and is attained",
      m["max_closed_bound_ratio"] <= 1.0 + 1e-9 and m["closed_bound_attained_everywhere"],
      f"max ratio {m['max_closed_bound_ratio']:.6f}")
    q("t56 the improvements buy +1 (donation) and +0 (closed) true detections",
      m["max_extra_detections_donation"] == 1 and m["max_extra_detections_closed"] == 0)
    q("t56 the deadline family buys +19 detections, at one window only",
      m["max_extra_detections_bucket"] == 19 and m["max_extra_detections_arc"] == 19)
    q("t56 at most 0.48% of episodes in any window carry nonzero evidence",
      abs(m["max_positive_evidence_fraction"] - 0.00481500253421186) < 1e-9,
      f"{100*m['max_positive_evidence_fraction']:.2f}%")
    q("t56 the donation relaxation is (1-alpha) to 1e-6 in every row",
      all(abs(r["classification"]["donation_relaxation"] - 0.95) < 1e-6 for r in d["rows"]))
    q("t56 the level never became unbounded (the cold-start bound is the operative regime)",
      all(r["arms"]["donation e-LOND"]["n_unbounded_level"] == 0 for r in d["rows"]))
    r55 = rows.get((0.55, 0, "poly"))
    if r55:
        a = r55["arms"]
        q("t56 at 0.55 the at-arrival silence is 90.1% at EVERY deadline",
          all(abs(a[k]["silent"] / r55["T"] - 0.9010) < 5e-4
              for k in ("e-LOND", "e-TOAD(bucket)", "e-TOAD(arc)")),
          ", ".join(f"{k}={100*a[k]['silent']/r55['T']:.1f}%"
                    for k in ("e-LOND", "e-TOAD(bucket)", "e-TOAD(arc)")))
        q("t56 online e-BH's necessary-condition silence understates it (0 vs the exact figure)",
          r55["classification"]["ebh_silent_necessary_only"] == 0
          and r55["classification"]["ebh_silent_exact"] == a["e-LOND"]["silent"])
        q("t56 the two Eq.(102) readings differ, and only the snapshot is source-faithful",
          m["donation_ebh_readings_ever_differ"]
          and a["donation e-BH (snapshot)"]["source_faithful"]
          and not a["donation e-BH (union)"]["source_faithful"])
    # cross-artefact: t56 must reproduce t21c on every shared arm
    e21 = load("t21c_H6_positions.json")
    if e21:
        bad = []
        for r21 in e21["rows"]:
            if r21["proc"] not in ("e-LOND", "online e-BH") or r21["gamma"] != "poly":
                continue
            key = (r21["pos"], r21["seed"], "poly")
            if key not in rows:
                continue
            arm = "e-LOND" if r21["proc"] == "e-LOND" else "e-TOAD(arc)"
            if rows[key]["arms"][arm]["tp"] != r21["tp"]:
                bad.append(f"{key} {r21['proc']}: t21c {r21['tp']} vs t56 "
                           f"{rows[key]['arms'][arm]['tp']}")
        q("t56 reproduces t21c on every shared arm (independent stages)", not bad, str(bad))

# ------------------------------------------- group-level calibration (4.57, review 7 item R2)
d = load("t57_group_calibration.json")
if d:
    m = d["summary"]
    rows = {(r["pos"], r["seed"]): r for r in d["rows"]}
    q("t57 covers 5 positions x 2 seeds", m["n_rows"] == 10)
    q("t57 group calibration is infeasible at every window, for e-LOND too",
      not m["group_feasible_anywhere"] and not m["group_feasible_for_elond_anywhere"])
    q("t57 flow calibration IS feasible for e-LOND everywhere",
      m["flow_feasible_for_elond_everywhere"])
    q("t57 the evidence ceiling falls 40.1x-49.1x (the flows-per-group ratio)",
      abs(m["ceiling_ratio_min"] - 40.1) < 0.1 and abs(m["ceiling_ratio_max"] - 49.1) < 0.1,
      f"{m['ceiling_ratio_min']:.1f}x to {m['ceiling_ratio_max']:.1f}x")
    q("t57 feasible steps == the closed form on all 20 arms",
      m["feasible_matches_closed_form_everywhere"])
    q("t57 the zeros are the boundary: no fire inside the cold-start window on a silent arm",
      m["zero_is_boundary_not_bug_everywhere"]
      and m["max_fires_in_coldstart_with_no_rejection"] == 0)
    q("t57 r* is verified MINIMAL on every priced group", m["rstar_verified_everywhere"])
    q("t57 the bare '>= kth largest' rule would have over-fired (tie bug was not latent)",
      m["max_bare_rule_overfire"] > 0, f"{m['max_bare_rule_overfire']} groups")
    q("t57 the max statistic is arity-dependent and the mean is not",
      m["max_spearman_arity_max_stat"] > 0.3 and m["max_spearman_arity_mean_stat"] < 0.15,
      f"max {m['max_spearman_arity_max_stat']:+.3f} vs mean "
      f"{m['max_spearman_arity_mean_stat']:+.3f}")
    q("t57 the max statistic's worst arity bin is >10x the nominal rate, the mean's is ~2x",
      m["max_worst_bin_over_nominal_max_stat"] > 10
      and m["max_worst_bin_over_nominal_mean_stat"] < 3,
      f"{m['max_worst_bin_over_nominal_max_stat']:.1f}x vs "
      f"{m['max_worst_bin_over_nominal_mean_stat']:.1f}x")
    q("t57 arity-stratified calibration leaves a cold-start window of a few steps",
      m["mondrian_smallest_coldstart"] <= 5, f"{m['mondrian_smallest_coldstart']} steps")
    q("t57 the span law is (k/c_0) x the group-rate ratio", m["span_law_holds"])
    q("t57 max is append-invariant within a fixed group; mean is not",
      m["max_statistic_append_invariant_everywhere"]
      and not m["mean_statistic_append_invariant_anywhere"])
    r55 = rows.get((0.55, 0))
    if r55:
        q("t57 0.55: flow calibration detects 18, group calibration 0 at both statistics",
          r55["flow"]["tp"] == 18 and r55["stats"]["max"]["tp"] == 0
          and r55["stats"]["mean"]["tp"] == 0)
        q("t57 0.55: cold-start window 81, first fire at position 401 (110 fire, none inside)",
          r55["stats"]["max"]["coldstart_window_closed_form"] == 81
          and r55["stats"]["max"]["first_fire_position"] == 401
          and r55["stats"]["max"]["n_fires_in_coldstart"] == 0,
          f"window {r55['stats']['max']['coldstart_window_closed_form']}, first fire "
          f"{r55['stats']['max']['first_fire_position']}")
        q("t57 0.55: margin goes +0.067 -> -0.977",
          abs(r55["flow"]["margin"] - 0.067) < 5e-4
          and abs(r55["group"]["margin"] + 0.977) < 5e-4)
    r85 = rows.get((0.85, 0))
    if r85:
        x = r85["stats"]["max"]
        q("t57 0.85: 42 detections are the bootstrap (65-step window stretched to 688)",
          x["tp"] == 42 and x["coldstart_window_closed_form"] == 65
          and x["n_feasible_steps"] == 688 and abs(x["bootstrap_factor"] - 10.49) < 0.01)
    q("t57 dropping mixed calibration groups discards <=26.1% of flows, 45.4x benign arity",
      abs(m["max_frac_calibration_flows_dropped"] - 0.261) < 5e-4
      and abs(m["max_mixed_over_benign_arity"] - 45.4) < 0.1,
      f"{100*m['max_frac_calibration_flows_dropped']:.1f}%, "
      f"{m['max_mixed_over_benign_arity']:.1f}x")

# ---------------------------------------------------------------- report
print("=" * 100)
print(f"  {len(OK)} consistent, {len(BAD)} INCONSISTENT, {len(SKIP)} artefacts missing")
if SKIP:
    print("  missing (run the experiment first): " + ", ".join(SKIP))
if BAD:
    print("=" * 100)
    for b in BAD:
        print("  MISMATCH  " + b)
    print("=" * 100)
    sys.exit(1)
print("  every checked number in the record matches the artefact it came from")
print("=" * 100)
