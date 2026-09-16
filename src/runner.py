"""Reproduce every result in the paper.

    python runner.py            everything, from whatever cache exists   (~2-3 h)
    python runner.py --theory   only the scripts that need no data       (~1 min)
    python runner.py --list     show the stages and exit

Results are written to lib/out/*.json. The first data-dependent stage rebuilds the flow
cache if it is absent, which takes about a minute and needs the inputs described in
data/README.md.
"""
import argparse, importlib, pathlib, sys, time

LIB = pathlib.Path(__file__).resolve().parent / "lib"
sys.path.insert(0, str(LIB))

THEORY = [
    ("t15_T3_theorem", {}, "feasibility theorem and e-LOND check"),
    ("t18_T4_padding", {}, "padding theorem and checks"),
    ("t21f_H6_scaling", {}, "what the online e-BH escape costs"),
    ("t32a_E11_derivation", {}, "padding/state coincidence, closed forms"),
    ("t34a_E1_derivation", {}, "smoothed and continuous evidence, closed forms"),
    ("t35a_E2_derivation", {}, "periodic restart, closed forms"),
    ("t36a_E3_derivation", {}, "precommitted weights, closed forms"),
    ("t38a_E4_derivation", {}, "calibration contamination, closed forms"),
    ("t39a_E6_derivation", {}, "parameter transfer, design rules"),
    ("t41a_E8_derivation", {}, "operational units, unit recovery"),
    ("t42a_E9_derivation", {}, "tie-block algebra"),
]

# Order matters only where a stage reads another's output:
#   t25 and t26(five=True) -> t39      t41a -> t41      t49 -> t51 -> t54 -> t67 -> t76 -> t77
#   t18 (theory) reads the shipped t17_T2.json; t50 reads t30; t64 reads t20; t60 and t41 read t28b
EXPERIMENTS = [
    ("t17_T2_fullstream", {}, "full stream, five positions x two seeds"),
    ("t22_H1_H2_matrix", {}, "second detector and rank-k sweep"),
    ("t21c_H6_positions", {}, "procedures over five positions"),
    ("t21d_H6_horizon", {}, "horizon misspecification"),
    ("t23_H7_bates", {}, "Bates calibration-conditional adjustment"),
    ("t24_H3_q_gamma", {}, "joint q and spending-sequence sweep"),
    ("t25_H5_caps", {}, "cap-selection sweep"),
    ("t26_H4_grouping", {"five": True}, "grouping families, five positions"),
    ("t28b_reallevel_padding", {}, "padding cost vs the running controller level"),
    ("t29_compound_e", {}, "boosting and compound e-values"),
    ("t20_T8_matched", {}, "matched operating points and frontier"),
    ("t30_A1_tailforensics", {}, "position-0.85 tail forensics"),
    ("t31_A2_alertaudit", {}, "adjudicated alert audit"),
    ("t32_B1_addis_state", {}, "controller-state attack and coincidence export"),
    ("t34_E1_smoothed", {}, "randomised smoothing and continuous evidence"),
    ("t35_E2_restart", {}, "periodic restart and batching"),
    ("t36_E3_asymmetric", {}, "precommitted weights and ordering"),
    ("t38_E4_contamination", {}, "calibration contamination"),
    ("t39_E6_transfer", {}, "cross-window parameter transfer"),
    ("t40_E7_controller", {}, "second controller and wall-clock delay"),
    ("t41_E8_units", {}, "both attacks in operational units"),
    ("t42_E9_ties", {}, "timestamp-tie sensitivity"),
    ("t46_hostpair_padding", {}, "can pads reach the target host pair"),
    ("t47_W7_coverage", {}, "grouping-independent fixed-unit coverage and resolution blur"),
    ("t48_W3_dilution", {}, "controlled padding-dilution on the real detector"),
    ("t49_R7_host_detector", {}, "host-conditioned detector and the padding-transfer boundary"),
    ("t51_R7_ait", {}, "R7 re-measured on the AIT benign-inclusive testbed (no graft)"),
    ("t54_ait_suppression", {}, "full Surface A suppression pipeline on AIT, real victim pads"),
    ("t50_calib_ci", {}, "Clopper-Pearson intervals on the benign-firing diagnostic"),
    ("t52_B1_synthetic", {}, "ADDIS state attack on a synthetic guarantee-valid stream"),
    ("t53_ordering", {}, "within-bucket order-sensitivity of the headline detections"),
    ("t55_a1_strata", {}, "metadata-stratified interrogation of Assumption 1 at deeper rank depths"),
    ("t56_uai26_procedures", {}, "UAI 2026 e-closure/compound-e procedures against the C1 horizon"),
    ("t57_group_calibration", {}, "group-level calibration: repairing Assumption 1, and its cost"),
    ("t58_semantic_blur", {}, "external semantic anchor for the alert-blur claim (red-team record)"),
    ("t59_prevalence", {}, "realistic-prevalence sensitivity: thinning attacks to a SOC base rate"),
    ("t60_positional", {}, "group-creation attack: suppression by insertion, not by padding"),
    ("t63_blindkey", {}, "what a SECRET canonical-order seed costs the insertion attacker"),
    ("t64_frontier_canonical", {}, "operational evaluation under the canonical (headline) order"),
    ("t66_nonoracle_padding", {}, "padding priced WITHOUT oracle state: multiplier and flat-pad attackers (re-analysis)"),
    ("t67_ait_order", {}, "the AIT transfer under both within-bucket orders (canonical carries the paper)"),
    ("t73_uniform_padding", {}, "padding cost under horizon-free vs horizon-aware spending (Table I)"),
    ("t74_defended_replay", {}, "per-alert real-flow replay under horizon-aware spending; volume cap"),
    ("t75_joint_rerun", {}, "joint attacked-trajectory rerun: static, sequential and state-free attackers"),
    ("t76_joint_ait", {}, "joint attack on the benign-inclusive AIT stream: real pads, live R, causal host context"),
    ("t77_cor2_premise", {}, "Corollary 2's premise measured directly on the t76 streams (max non-attacker evidence vs T/alpha)"),
]


def run(stages):
    import os
    os.chdir(LIB)
    width = max(len(n) for n, _, _ in stages)
    failed, t0 = [], time.time()
    for i, (name, kw, desc) in enumerate(stages, 1):
        tag = name + ("(five=True)" if kw.get("five") else "")
        print(f"[{i:>2}/{len(stages)}] {tag:<{width + 12}} {desc}", flush=True)
        t = time.time()
        try:
            mod = importlib.import_module(name)
            importlib.reload(mod) if kw else None
            mod.main(**kw)
            print(f"         ok  {time.time() - t:6.1f}s", flush=True)
        except SystemExit as e:
            if e.code:
                failed.append(tag)
                print(f"         FAILED (exit {e.code})  {time.time() - t:6.1f}s", flush=True)
            else:
                print(f"         ok  {time.time() - t:6.1f}s", flush=True)
        except Exception as e:
            failed.append(tag)
            print(f"         FAILED  {type(e).__name__}: {e}", flush=True)
    print(f"\n{len(stages) - len(failed)}/{len(stages)} stages ok in "
          f"{(time.time() - t0) / 60:.1f} min")
    if failed:
        print("failed: " + ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--theory", action="store_true", help="only the no-data stages")
    ap.add_argument("--list", action="store_true", help="print the stages and exit")
    a = ap.parse_args()
    stages = THEORY if a.theory else THEORY + EXPERIMENTS
    if a.list:
        for n, kw, d in stages:
            print(f"  {n + ('(five=True)' if kw.get('five') else ''):<32} {d}")
        sys.exit(0)
    sys.exit(run(stages))
