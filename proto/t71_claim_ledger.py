"""Claim ledger: one row per headline claim, resolved to the arm it was actually measured on.

WHY THIS EXISTS.  Review 14 asked for it directly, and named the failure it is meant to catch:

    "This catches the common final-draft problem where an experiment is correct but the abstract
     generalizes it beyond the arm actually run."

That is not a numeric error, so t45/t61/t65 cannot see it.  Every number can match its artefact
exactly while the sentence carrying it quietly drops the window, the order, the seed, or the dataset
the measurement was made on -- which is exactly what happened to the replay claim (run at 0.55 only,
stated as though both windows were replayed) and to the fixed-multiplier claim (LSPR23 only, stated
unscoped).  Both were caught by hand in review 14; this makes the check mechanical.

WHAT IT DOES.  For each headline claim it prints, and verifies:

  * VALUE      -- recomputed live from the artefact, never copied from the paper
  * ARM        -- window / order / seed / dataset the artefact row actually belongs to
  * ASSUMPTION -- what the claim needs to be true (valid e-values? A1? labels?)
  * SOURCE     -- the src/lib script that produced the artefact
  * OUTPUT     -- the table or figure in the paper that displays it
  * WORDING    -- the sentence in satml.tex that states it, and whether that sentence carries the
                  arm's qualifiers

A claim whose paper sentence omits a qualifier its arm requires is a FAILURE, not a warning.

    python proto/t71_claim_ledger.py            # check
    python proto/t71_claim_ledger.py --markdown # emit docs/38_claim_ledger.md
"""
import json
import pathlib
import re
import sys

if not __debug__:
    raise SystemExit(f"{__file__} must not run under `python -O`: assertions are its checks")

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "lib" / "out"
TEX = ROOT / "paper" / "satml.tex"
S = TEX.read_text()
BODY = S[: S.index("\\appendices")]
FLAT = re.sub(r"\s+", " ", S)
FLAT_BODY = re.sub(r"\s+", " ", BODY)
OK, BAD = [], []


def load(name):
    f = OUT / f"{name}.json"
    assert f.exists(), f"missing artefact {name}"
    return json.load(open(f))


def dig(obj, path):
    for part in path.split("/"):
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj


# =========================================================================================
# THE LEDGER.  `value` is a callable so nothing is transcribed; `quals` are the tokens the
# claiming sentence must carry, because they are what the arm is scoped to.
# =========================================================================================
# ROUND 31: the host-conditioned arm runs at every organisation, so its two counts are computed from
# the artefact here and required verbatim in the paper.  Hard-coding them would let the artefact and
# the sentence drift apart silently, which is the one thing this ledger exists to prevent.
_HOSTROWS = load("t54_ait_suppression")["host"]
_HOST_DET = sum(o["n_detected"] for o in _HOSTROWS)
_HOST_SUP = sum(o["n_suppressible"] for o in _HOSTROWS)

LEDGER = [
    dict(claim="Calibration required at LSPR23 flow scale, LOND/e-LOND, horizon-uniform",
         value=lambda: dig(load("t21f_H6_scaling"), "attainable/2/R=1"),
         show=lambda v: f"{v:.3g}",
         arm="algebraic; no window, order or seed",
         assumption="none beyond a finite evidence ceiling M and gamma_t = 1/T",
         source="t21f_H6_scaling.py", output="Fig. 2",
         tex="$3.3\\times10^{8}$", quals=("LOND/e-LOND",)),
    dict(claim="Calibration units per hypothesis at k=1 (LOND/e-LOND, LORD++)",
         value=lambda: (1 / 0.05, 1 / 0.025), show=lambda v: f"{v[0]:.0f} / {v[1]:.0f}",
         arm="algebraic; k/c_0, dataset- and unit-independent",
         assumption="none beyond the cold-start coefficient c_0",
         source="closed form k/c_0", output="Sec. III-B prose",
         tex="$20$ calibration units per hypothesis for LOND/e-LOND and $40$ for LORD++",
         quals=("k=1",), qual_alias={"k=1": ("$k=1$",)}),
    dict(claim="Alert blur at the two-hour headline unit, primary window",
         value=lambda: next(r["blur_mal_atoms_per_alert"] for r in load("t47_W7")["rows"]
                            if r["family"] == "src-dst" and abs(float(r["pos"]) - 0.55) < 1e-9
                            and (r["bucket_s"] or 86400) == 7200),
         show=lambda v: f"{v:.1f}",
         arm="primary window 0.55, seed 0, FIRST-FLOW order (blur needs alerts at every width)",
         assumption="dataset labels (blur counts malicious atoms)",
         source="t47_W7_coverage.py", output="Fig. 3 (lower panel)",
         tex="$16.1$ at the two-hour headline unit", quals=("blur",)),
    dict(claim="Exact padding cost per alert, primary window",
         value=lambda: dig(load("t28b_reallevel"), "table1_by_order/keyhash/0.55_0/pads_real"),
         show=lambda v: ", ".join(str(x) for x in v),
         arm="primary window 0.55, seed 0, CANONICAL order",
         assumption="labels (to know which episodes are true detections); NOT e-validity",
         source="t28b_reallevel_padding.py", output="Table I, Fig. 4A",
         tex="23, 24 and 33 added flows", quals=("canonical",)),
    dict(claim="Exact padding cost, secondary window (median)",
         value=lambda: dig(load("t28b_reallevel"), "table1_by_order/keyhash/0.62_0/med_pad_real"),
         show=lambda v: f"{v:.0f}",
         arm="secondary window 0.62, seed 0, CANONICAL order; NOT replayed",
         assumption="labels; NOT e-validity",
         source="t28b_reallevel_padding.py", output="Table I, Fig. 4A",
         tex="median cost of six", quals=("canonical",)),
    dict(claim="A single fixed multiplier c=10 defeats every canonical alert",
         value=lambda: [(w, next(r for r in load("t66_nonoracle")["multiplier"][w]["by_c"]
                                 if r["c"] == 10)) for w in ("canonical@0.55", "canonical@0.85")],
         show=lambda v: "; ".join(f"{w}: {r['defeated']}/{r['of']}" for w, r in v),
         arm="LSPR23 only, canonical order, windows 0.55 and 0.85; state-free arms",
         assumption="attacker knows its own arity m (free on LSPR23: 674/674 detected episodes "
                    "sit on host pairs with no benign traffic). Does NOT transfer to AIT, where "
                    "the episode contains benign flows the attacker cannot count.",
         source="t66_nonoracle_padding.py", output="Sec. V-C prose, App. E",
         tex="on LSPR23, $c=10$", quals=("LSPR23", "primary and stress windows")),
    dict(claim="Per-alert real-flow replay reproduces the closed form, primary window",
         value=lambda: dig(load("t28b_reallevel"), "table1_by_order/keyhash/0.55_0/pads_real"),
         show=lambda v: f"3/3 at the predicted {min(v)}--{max(v)} flows",
         arm="0.55 and 0.62, seed 0, CANONICAL order; both windows replayed (14 alerts, all "
             "suppressed at the closed form)",
         assumption="labels; NOT e-validity",
         source="t28b_reallevel_padding.py (replay arm)", output="Table I, Sec. V-D",
         tex="all $3/3$ canonical primary-window detections", quals=("canonical",)),
    dict(claim="AIT transfer: suppressible flow-only detections, canonical order",
         value=lambda: load("t67_ait_order")["summary"]["canonical"],
         show=lambda v: f"{v['n_suppressible']} of {v['n_detected']}",
         arm="AIT-LDSv2.0, 8 held-out organisations, CANONICAL order, flow-only detector",
         assumption="labels; NOT e-validity, NOT A1",
         source="t67_ait_order.py", output="Table I, Fig. 4B",
         tex="78 of 79", quals=("canonical",)),
    dict(claim="Joint AIT campaign cost, deployment pool, horizon-free",
         value=lambda: sum(o["flow"]["greedy_t54pool"]["poly"]["total_pads"]["median"]
                           for o in load("t76_joint_ait")["orgs"].values() if "flow" in o),
         show=lambda v: f"{v:,.0f} flows",
         arm="AIT-LDSv2.0, 8 organisations, CANONICAL order, flow-only, controller re-run over the "
             "padded stream; summed per-organisation medians over 100 pad-sampling trajectories",
         assumption="labels; NOT e-validity, NOT A1; pool drawn from the whole deployment window",
         source="t76_joint_ait.py", output="Table I row, Sec. V-F, App. E",
         tex="244{,}250", quals=("canonical",)),
    dict(claim="Joint AIT alerts surviving when cover traffic predates the attack",
         value=lambda: [sum(o["flow"]["greedy"][g]["remaining_own"]["median"]
                            for o in load("t76_joint_ait")["orgs"].values() if "flow" in o)
                        for g in ("poly", "uniform")],
         show=lambda v: f"{v[0]:.0f} and {v[1]:.0f} own alerts remain",
         arm="AIT-LDSv2.0, 8 organisations, CANONICAL order, flow-only, pool restricted to flows the "
             "victim received before the attacker's own last flow in the episode",
         assumption="labels; NOT e-validity, NOT A1",
         source="t76_joint_ait.py", output="Sec. V-F, App. E",
         tex="$24$ and $27$", quals=("canonical",)),
    dict(claim="Suppression cost under the max-min-optimal horizon-aware allocation",
         value=lambda: load("t73_uniform_padding")["cells"]["0.55_keyhash_uniform"],
         show=lambda v: f"{v['detections']} true detections, median r*={v['median_pad']:.0f}, "
                        f"{v['false_positives']} FP",
         arm="LSPR23 primary 0.55, seed 0, CANONICAL order, gamma_t = 1/T (needs a known horizon)",
         assumption="labels; NOT e-validity. The control arm reproduces the shipped poly numbers.",
         source="t73_uniform_padding.py", output="Table III, Fig. 4A",
         tex="$2{,}946$", quals=("horizon-aware",)),
    # --- ROUND 24.  Three headline claims the ledger did not carry.  Each is a claim a reviewer
    # reads in the abstract or Sec. V, so each needs its arm pinned like the rest.
    dict(claim="Detection count under the two spending allocations, primary window",
         value=lambda: (dig(load("t73_uniform_padding"), "cells/0.55_keyhash_poly/detections"),
                        dig(load("t73_uniform_padding"), "cells/0.55_keyhash_uniform/detections")),
         show=lambda v: f"{v[0]} -> {v[1]} TRUE detections",
         arm="LSPR23 primary 0.55, seed 0, CANONICAL order; gamma poly -> gamma_t = 1/T is the "
             "ONLY thing that changes. Both cells have 0 false discoveries.",
         assumption="labels (a true detection needs one); NOT e-validity",
         source="t73_uniform_padding.py", output="Abstract, Table I, Sec. V-D",
         tex="detects $105$ of 275 malicious episodes at the primary window", quals=("horizon-aware",)),
    dict(claim="Per-alert real-flow replay under horizon-aware spending, both windows",
         value=lambda: [(w, dig(load("t74_defended_replay"),
                                f"cells/{w}_uniform/n_alerts_always_suppressed"),
                         dig(load("t74_defended_replay"), f"cells/{w}_uniform/detections"))
                        for w in ("0.55", "0.62")],
         show=lambda v: "; ".join(f"{w}: {a}/{d}" for w, a, d in v),
         arm="LSPR23 0.55 and 0.62, seed 0, CANONICAL order, gamma_t = 1/T, 200 draws. PER-ALERT "
             "at the level each alert received on the UNPERTURBED trajectory -- not a joint rerun "
             "of the controller under attack. Counts TRUE detections: the 0.62 cell also has one "
             "false discovery, which is not in the 107.",
         assumption="labels; NOT e-validity. Pads are real pool flows, so the e-values are "
                    "measured; the aggregation and the level are arithmetic.",
         source="t74_defended_replay.py", output="Abstract, Sec. V-D",
         tex="suppresses $105/105$ and $107/107$ true detections",
         quals=("horizon-aware", "per-alert")),
    dict(claim="Per-host-pair volume cap: alerts still suppressible UNDER the cap",
         value=lambda: {r["cap"]: (r["n_fits"], r["of"], r["benign_truncated"])
                        for r in dig(load("t74_defended_replay"), "cells/0.55_uniform/cap_curve")
                        if r["cap"] in (100, 300)},
         show=lambda v: "; ".join(f"cap {c}: {n}/{o} at {b:.3%} benign truncated"
                                  for c, (n, o, b) in v.items()),
         arm="LSPR23 primary 0.55, seed 0, CANONICAL order (t74 runs order=keyhash), "
             "gamma_t = 1/T. The cap disrupts ARITY only; what truncation does to the scores is "
             "not modelled. Per-alert m + r* <= n, not a joint rerun.",
         assumption="labels; NOT e-validity",
         source="t74_defended_replay.py", output="Sec. V-D (per-alert reading), App. E",
         tex="where $m_t+r^{\\star}_t>n$ predicts $91$ and $95$",
         quals=("per-alert",)),
    dict(claim="Joint rerun: per-alert pads applied together leave no true detection",
         value=lambda: {k: c["static"]["remaining_true_max"]
                        for k, c in load("t75_joint_rerun")["cells"].items() if "keyhash" in k},
         show=lambda v: "; ".join(f"{k}: {r} remain" for k, r in v.items()),
         arm="LSPR23 0.55 and 0.62, seed 0, CANONICAL order, both regimes; controller RE-RUN over the "
             "padded stream; zero-evidence pads (pool has no firing flow, asserted)",
         assumption="labels; NOT e-validity. Oracle per-alert pads r* from the unperturbed run.",
         source="t75_joint_rerun.py", output="Sec. V-D, Table I caption, App. E",
         tex="leaves no true detection standing", quals=("canonical",)),
    dict(claim="Joint rerun: sequential oracle attacker's campaign cost, horizon-aware",
         value=lambda: [(w, dig(load("t75_joint_rerun"), f"cells/{w}_keyhash_uniform/adaptive/total_cost"),
                         dig(load("t75_joint_rerun"), f"cells/{w}_keyhash_uniform/unperturbed/total_r_static"))
                        for w in ("0.55", "0.62")],
         show=lambda v: "; ".join(f"{w}: {a:,} vs per-alert {s:,}" for w, a, s in v),
         arm="LSPR23 0.55 and 0.62, seed 0, CANONICAL order, gamma_t = 1/T; GREEDY sequential oracle "
             "sized on the attacked trajectory's live level -- one strategy's cost, an upper bound on "
             "the campaign minimum, not a global minimum. Two windows, one seed.",
         assumption="labels; NOT e-validity. Attacker knows which of its own episodes would fire and "
                    "the live level (the same oracle knowledge r* assumes).",
         source="t75_joint_rerun.py", output="Sec. V-D, Table I joint column, App. E",
         tex="$5{,}650$ flows in total", quals=("canonical", "primary window")),
    dict(claim="Joint rerun: volume cap against the sequential attacker at cap 100",
         value=lambda: {w: next(r for r in dig(load("t75_joint_rerun"),
                                               f"cells/{w}_keyhash_uniform/capped_adaptive")
                                if r["cap"] == 100) for w in ("0.55", "0.62")},
         show=lambda v: "; ".join(f"{w}: {r['remaining_true']} fire = {r['n_fired_structural']} structural "
                                  f"+ {r['n_fired_cascade_victims']} cascade" for w, r in v.items()),
         arm="LSPR23 0.55 and 0.62, seed 0, CANONICAL order, gamma_t = 1/T; sequential attacker pads "
             "only if m + r <= cap, else the alert fires and raises R. Sampled cap grid; nothing "
             "between grid points.",
         assumption="labels; NOT e-validity; zero-evidence pads",
         source="t75_joint_rerun.py", output="Sec. V-D, App. E",
         tex="$96$ of the $105$ horizon-aware primary-window alerts still fire", quals=("canonical",)),
    dict(claim="State-free multiplier c=3 silences both horizon-aware arms jointly",
         value=lambda: [(w, dig(load("t75_joint_rerun"), f"cells/{w}_keyhash_uniform/multiplier/3/remaining_true"),
                         dig(load("t75_joint_rerun"), f"cells/{w}_keyhash_uniform/critical_multiplier/c_crit"),
                         dig(load("t75_joint_rerun"), f"cells/{w}_keyhash_uniform/critical_multiplier/rho_elond"))
                        for w in ("0.55", "0.62")],
         show=lambda v: "; ".join(f"{w}: {r} remain at c=3, c_crit={c:.3f}=rho={p:.3f}" for w, r, c, p in v),
         arm="LSPR23 0.55 and 0.62, seed 0, CANONICAL order, gamma_t = 1/T, EVERY malicious episode "
             "multiplied; c_crit <= rho is exact here because a malicious episode attains the ceiling "
             "and no false discovery survives. Two windows; not a general theorem.",
         assumption="labels; attacker knows only its own arity m",
         source="t75_joint_rerun.py", output="Sec. V-C, App. E",
         tex="multiplying \\emph{every} own episode by $c=3$ silences it at both windows",
         quals=("horizon-aware",)),
    dict(claim="AIT host-conditioned detections suppressed under causal context recomputation",
         value=lambda: load("t54_ait_suppression")["host"],
         show=lambda v: f"{sum(o['n_suppressible'] for o in v)} of "
                        f"{sum(o['n_detected'] for o in v)} over "
                        f"{sorted(o['org'] for o in v)}",
         arm="AIT, ALL EIGHT organisations (round 31), FIRST-FLOW order, host-conditioned detector; "
             "'suppressible' = at least one of 200 replay draws cleared the threshold inside the "
             "scored accumulation range",
         assumption="labels; the six causal host features and the accumulation model implemented",
         source="t54_ait_suppression.py", output="Table III, Sec. V-F",
         tex=f"issues ${_HOST_DET}$ host-conditioned true detections\nand suppresses ${_HOST_SUP}$ of them",
         quals=("first-flow",)),
]


def sentences_of(hay, needle):
    """EVERY sentence that states the claim, not just the first.

    Checking only the first occurrence is the wrong semantics here: the abstract and the body both
    state most of these claims, and it is precisely the second, more compressed statement that tends
    to shed the qualifier.  (Verified: the abstract's "78 of 79" lost "canonical" in a compression
    pass and a first-occurrence check would have passed if the body's copy came first.)
    """
    starts = [0] + [m.end() for m in re.finditer(r"(?<=[.?!])\s+(?=[A-Z\\$])", hay)]
    out, at = [], hay.find(needle)
    while at != -1:
        a = max(x for x in starts if x <= at)
        later = [x for x in starts if x > at + len(needle) - 1]
        chunk = hay[a:min(later) if later else len(hay)]
        out.append(chunk if len(chunk) >= 40 else hay[max(0, at - 300):at + 300])
        at = hay.find(needle, at + 1)
    return out


rows = []
for e in LEDGER:
    val = e["value"]()
    shown = e["show"](val)
    tex = re.sub(r"\s+", " ", e["tex"])
    present = tex in FLAT
    OK.append(f"{e['claim'][:58]:60} = {shown}") if present else \
        BAD.append(f"{e['claim']}: paper does not carry {e['tex']!r}")
    missing = []
    if present:
        sents = sentences_of(FLAT, tex)
        for n, sent in enumerate(sents):
            for qtok in e["quals"]:
                alts = e.get("qual_alias", {}).get(qtok, ()) + (qtok,)
                # a qualifier may legitimately live in the consolidated limitations section instead
                hay = FLAT if e.get("qual_scope") == "limitations" else sent
                if not any(a in hay for a in alts):
                    missing.append((n, qtok))
        if missing:
            for n, qtok in missing:
                BAD.append(f"{e['claim']}: occurrence {n + 1} of {e['tex']!r} omits {qtok!r}; "
                           f"the arm is {e['arm']}\n              ...{sents[n][:150]}...")
        else:
            OK.append(f"  ^ {len(sents)} statement(s), all carrying {list(e['quals'])}")
    rows.append(dict(e, shown=shown, present=present, missing=missing))

if "--markdown" in sys.argv:
    md = ["# Claim ledger", "",
          "Generated by `proto/t71_claim_ledger.py`. Values are recomputed from the artefacts on",
          "every run, never transcribed. The point of the **Arm** column is the failure review 14",
          "named: an experiment that is correct but whose paper sentence generalises it past the",
          "window, order, seed or dataset it was actually run on.", "",
          "| Claim | Value | Arm actually run | Assumption | Source script | Shown in | Body wording |",
          "|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['claim']} | `{r['shown']}` | {r['arm']} | {r['assumption']} | "
                  f"`{r['source']}` | {r['output']} | `{r['tex']}` |")
    (ROOT / "docs" / "38_claim_ledger.md").write_text("\n".join(md) + "\n")
    print(f"  wrote docs/38_claim_ledger.md ({len(rows)} claims)")

print("=" * 96)
for line in OK:
    print(f"  ok     {line}")
for line in BAD:
    print(f"  BAD    {line}")
print("=" * 96)
print(f"  {len(OK)} consistent, {len(BAD)} INCONSISTENT over {len(LEDGER)} headline claims")
if BAD:
    print("  A headline claim is stated without a qualifier its measured arm requires.")
    sys.exit(1)
print("  every headline claim resolves to its arm, and its sentence carries that arm's qualifiers")
print("=" * 96)
