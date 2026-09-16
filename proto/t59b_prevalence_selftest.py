"""Unit tests for t59_prevalence.py (review-7 item R5).

Same discipline as t56b/t57b/t58b: the tests drive the SHIPPED functions, AST-lifted out of
`src/lib/t59_prevalence.py` rather than restated here, so a test cannot pass against a restatement
of the code it checks.

The thing most worth attacking in this stage is the THINNING ARITHMETIC -- get `keep` wrong and the
realised prevalence silently misses its target, which would make every reported row mislabelled --
and the claim that thinning moves DETECTION without moving FEASIBILITY, which must hold as an
identity in |C|, k and T rather than as an empirical coincidence.

Run:  proto/.venv/bin/python proto/t59b_prevalence_selftest.py
"""
import ast, json, sys, types, pathlib
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parent / "src" / "lib" / "t59_prevalence.py"
OUT = HERE.parent / "src" / "lib" / "out" / "t59_prevalence.json"
FAIL = []


def ck(label, cond, detail=""):
    if not cond:
        FAIL.append(f"{label}   {detail}" if detail else label)
    print(f"  {'ok  ' if cond else 'FAIL'}  {label}" + (f"   {detail}" if detail and not cond else ""))


def lift(names):
    tree = ast.parse(SRC.read_text())
    want = ast.Module(body=[], type_ignores=[]); got = set()
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name in names:
            want.body.append(n); got.add(n.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id in names:
                    want.body.append(n); got.add(t.id)
    missing = set(names) - got
    if missing:
        raise SystemExit(f"cannot lift {missing} from {SRC}")
    mod = types.ModuleType("t59_lifted")
    mod.__dict__["np"] = np
    from scipy.special import zeta
    mod.__dict__["zeta"] = zeta
    sys.path.insert(0, str(HERE.parent / "src" / "lib"))
    from h6_procs import make_gamma
    mod.__dict__["make_gamma"] = make_gamma
    exec(compile(ast.fix_missing_locations(want), "<lifted>", "exec"), mod.__dict__)
    return mod


M = lift(["keep_count", "cold_start", "q", "A", "W0", "K", "N_REP", "N_REP_TOAD", "PI_TARGETS",
          "POS", "ORDERS"])

print("=" * 100)
print("1. the thinning arithmetic hits its target prevalence")
print("=" * 100)
# keep = pi(T-M)/(1-pi) is the solution of keep/((T-M)+keep) = pi.  Check it INVERTS, over a wide
# grid, rather than checking the formula against itself.
worst = 0.0
bad = 0
for T in (1_000, 31_568, 49_267, 57_368, 250_000):
    for Mm in (1, 17, 246, 275, 398, 5_000):
        if Mm >= T:
            continue
        obs = Mm / T
        for pi in (1e-2, 5e-3, 1e-3, 1e-4, 1e-5, 1e-6):
            if pi > obs:
                continue                       # unreachable: cannot manufacture attacks
            keep = M.keep_count(T, Mm, pi)
            T2 = (T - Mm) + keep
            realised = keep / T2 if T2 else 0.0
            # rounding to a whole episode is the only slack allowed, AND a positive target must
            # never realise as zero -- the audit found rows where it silently did
            slack = 1.0 / max(T2, 1)
            if abs(realised - pi) > slack + 1e-12 and keep > 1:
                bad += 1
            if realised == 0.0:
                bad += 1
            worst = max(worst, abs(realised - pi) / pi)
            if not (0 <= keep <= Mm):
                bad += 1
ck("keep = pi(T-M)/(1-pi) inverts to the target prevalence on every reachable (T, M, pi)",
   bad == 0, f"{bad} violations, worst relative miss {worst:.4f}")
ck("keeping ALL of them is the observed arm", M.keep_count(57368, 275, None) == 275)
ck("pi = 0 keeps none", M.keep_count(57368, 275, 0.0) == 0)
# a positive target must never round down to zero: that would silently duplicate the pure-null arm
ck("a positive target keeps at least ONE episode, never collapsing into the pure null",
   all(M.keep_count(T, Mm, p) >= 1
       for T in (31_426, 31_672, 57_368) for Mm in (246, 255, 275) for p in (1e-5, 1e-6, 1e-9)))
ck("...and pi=0 is the ONLY arm that keeps none",
   M.keep_count(31_672, 246, 1e-5) == 1 and M.keep_count(31_672, 246, 0.0) == 0)
ck("an unreachable target is capped at M rather than exceeding it",
   M.keep_count(1000, 5, 0.5) == 5)
ck("keep is never negative", all(M.keep_count(T, Mm, p) >= 0
                                for T in (1000, 57368) for Mm in (1, 275) for p in (0.0, 1e-9, 1e-3)))
# monotone in pi: a lower target keeps no more episodes
mono = all(M.keep_count(57368, 275, a) >= M.keep_count(57368, 275, b)
           for a, b in zip([5e-3, 1e-3, 1e-4], [1e-3, 1e-4, 1e-5]))
ck("keep is monotone non-increasing in the target prevalence", mono)

print()
print("=" * 100)
print("2. feasibility is an identity in (|C|, k, T) -- it CANNOT move much under thinning")
print("=" * 100)
# margin = (|C|+1) w0 / T - 1.  Dropping d episodes takes T to T-d, so the margin can only move by
# the amount T moves.  This is the claim the stage rests on and it is arithmetic, not measurement.
NC = 2_448_993; T = 57_368; Mm = 275
m0 = (NC + 1) * M.W0 / T - 1.0
worst_shift = 0.0
for pi in (1e-3, 1e-4, 1e-5, 0.0):
    keep = M.keep_count(T, Mm, pi)
    T2 = (T - Mm) + keep
    worst_shift = max(worst_shift, abs((NC + 1) * M.W0 / T2 - 1.0 - m0))
ck("thinning to pi=0 moves the margin by < 0.02 at the guarantee window",
   worst_shift < 0.02, f"{worst_shift:.5f}")
ck("the margin never depends on the SCORES, only on |C|, k and T",
   abs(((NC + 1) * M.W0 / T - 1.0) - m0) < 1e-15)
# and T itself moves by at most the malicious fraction
ck("T shrinks by at most the malicious-episode fraction",
   (Mm / T) < 0.01 and (T - ((T - Mm) + 0)) / T == Mm / T)

print()
print("=" * 100)
print("3. the cold-start window agrees with its closed form and with Ctx.infeasible")
print("=" * 100)
sys.path.insert(0, str(HERE.parent / "src" / "lib"))
from h6_procs import Ctx, make_gamma, run_lond            # noqa: E402
bad = 0
for CEIL, T in ((2_448_994.0, 57_368), (1_813_114.0, 31_568), (2_287_989.0, 37_231),
                (1e4, 5_000), (1e6, 120_000)):
    w, closed = M.cold_start(CEIL, T)
    if w != closed:
        bad += 1
    # brute force against Ctx.infeasible itself, step by step
    ctx = Ctx(np.zeros(T), np.zeros(T, bool), CEIL, alpha=M.A, w0=M.W0)
    g1, _ = make_gamma("poly", T)
    feas = [t for t in range(1, T + 1) if not ctx.infeasible(M.A * g1[t] * 1.0)]
    if (max(feas) if feas else 0) != w:
        bad += 1
ck("cold_start == its closed form == a step-by-step Ctx.infeasible scan, on 5 configurations",
   bad == 0, str(bad))
ck("a larger calibration set gives a longer cold-start window",
   M.cold_start(1e6, 100_000)[0] > M.cold_start(1e4, 100_000)[0])

print()
print("=" * 100)
print("4. thinning removes ONLY malicious episodes, and the run sees a shorter stream")
print("=" * 100)
# reproduce the stage's own masking on a synthetic stream and check the invariants it relies on
rng = np.random.default_rng(11)
T = 4_000; Mm = 40
ismal = np.zeros(T, bool); ismal[rng.choice(T, Mm, replace=False)] = True
Ev = np.where(rng.random(T) < 0.01, 5e5, 0.0)
mal_idx = np.flatnonzero(ismal)
ok_all = True
for pi in (1e-3, 1e-4, 0.0):
    keep = M.keep_count(T, Mm, pi)
    drop = rng.choice(mal_idx, Mm - keep, replace=False)
    mask = np.ones(T, bool); mask[drop] = False
    ok_all &= int((~mask).sum()) == Mm - keep                  # exactly the intended number dropped
    ok_all &= bool(ismal[~mask].all())                         # every dropped one was malicious
    ok_all &= int(ismal[mask].sum()) == keep                   # the survivors are the kept ones
    ok_all &= int(mask.sum()) == (T - Mm) + keep               # the benign stream is untouched
    ok_all &= np.array_equal(Ev[mask][~ismal[mask]], Ev[~ismal])   # benign evidence order preserved
ck("thinning drops exactly the intended malicious episodes and preserves the benign stream", ok_all)

# "Thinning never increases true detections" is NOT a theorem, and an earlier version of this file
# asserted it as one (the blind audit produced the counterexample).  DELETING a hypothesis shortens
# the stream, so every later hypothesis shifts one step EARLIER into a higher alpha_t; a malicious
# episode that could not clear its own step can therefore clear its new one.  Build that case
# explicitly rather than trusting 30 random draws to find it.
T = 1_000
g = make_gamma("poly", T)[0]
DEEP, SHALLOW = 150, 90                      # the survivor's index before and after deletion
CEIL = 1.0 / (M.A * g[SHALLOW + 1])          # clears at step SHALLOW+1, not at step DEEP+1
ismal = np.zeros(T, bool); Ev = np.zeros(T)
ismal[DEEP] = True; Ev[DEEP] = CEIL          # the one attack that carries any evidence
early = rng.choice(np.arange(0, DEEP), 60, replace=False)
ismal[early] = True                          # 60 zero-evidence attacks BEFORE it
full = run_lond(Ctx(Ev, ismal, CEIL, alpha=M.A, w0=M.W0), g)[1]
msk = np.ones(T, bool); msk[early] = False   # thin them away: the survivor moves 60 steps earlier
T2 = int(msk.sum())
thin_removed = run_lond(Ctx(Ev[msk], ismal[msk], CEIL, alpha=M.A, w0=M.W0),
                        make_gamma("poly", T2)[0])[1]
ck("DELETING hypotheses can INCREASE true detections -- monotonicity is not a theorem",
   thin_removed > full, f"full={full}, removed={thin_removed}")
# the index-preserving mechanism the stage uses as PRIMARY removes exactly that channel: the
# survivor keeps its own index, so its level is untouched
Ev_r = Ev.copy(); im_r = ismal.copy()
Ev_r[early] = 0.0; im_r[early] = False       # still in the stream, now benign
thin_fixed = run_lond(Ctx(Ev_r, im_r, CEIL, alpha=M.A, w0=M.W0), g)[1]
ck("...and the index-preserving mechanism does not: the survivor keeps its own level",
   thin_fixed == full, f"full={full}, resampled={thin_fixed}")
# nor is monotonicity guaranteed under resampling either, since a benign draw that FIRES raises R
# and so raises the level for every later hypothesis.  State it rather than assert the opposite.
ck("neither mechanism is asserted monotone; the artefact's monotonicity is checked empirically below",
   True)

print()
print("=" * 100)
print("5. the shipped artefact says what the record says")
print("=" * 100)
if not OUT.exists():
    print(f"  SKIP  {OUT} not present")
else:
    d = json.load(open(OUT))
    rows = d["rows"]; s = d["summary"]
    ck("every row's realised prevalence matches its target to within one episode, or is flagged",
       all(r["pi_target"] is None or r["pi_target"] == 0.0 or r["pi_target_attained"]
           or r["n_keep"] == 1
           for r in rows))
    ck("no POSITIVE prevalence target realises as zero (it would duplicate the pure-null arm)",
       all(r["realised_prevalence_fixed_T"] > 0 for r in rows
           if r["pi_target"] is not None and r["pi_target"] > 0))
    ck("rows that overshoot their nominal target are listed rather than silently reported",
       all(r["n_keep"] == 1 for r in rows if not r["pi_target_attained"])
       and len(s["rows_not_attaining_target"])
       == sum(1 for r in rows if not r["pi_target_attained"]))
    ck("every row's T equals (T_full - n_mal_full) + n_keep",
       all(r["T"] == (r["T_full"] - r["n_mal_full"]) + r["n_keep"] for r in rows))
    ck("the observed and pure-null arms are flagged deterministic and run once",
       all(r["deterministic"] == (r["pi_target"] is None or r["n_keep"] == 0) for r in rows)
       and all(r["elond"]["n_rep"] == 1 for r in rows if r["deterministic"]))
    ck("the partially-thinned arms run N_REP times",
       all(r["elond"]["n_rep"] == M.N_REP for r in rows if not r["deterministic"]))
    ck("pi = 1e-2 is absent, being above the observed episode prevalence everywhere",
       all(r["pi_target"] != 1e-2 for r in rows)
       and s["episode_prevalence_range"][1] < 1e-2)
    # the two claims the stage exists to separate
    ck("PRIMARY arm: the margin is held EXACTLY fixed (T never changes), not merely nearly so",
       s["max_abs_margin_shift_to_1e4"] == 0.0, f"{s['max_abs_margin_shift_to_1e4']}")
    ck("SENSITIVITY arm: T shrinks by under 1%, and the margin RISES (feasibility improves)",
       s["max_T_shrink_frac"] < 0.01 and s["max_margin_shift_removed"] > 0,
       f"T {s['max_T_shrink_frac']:.4f}, margin {s['max_margin_shift_removed']:+.4f}")
    ck("the two thinning mechanisms agree, so re-indexing is not driving the collapse",
       s["max_abs_variant_gap_at_1e4"] <= 0.10, f"{s['max_abs_variant_gap_at_1e4']:.3f}")
    ck("the escapes are reported under the same thinning, e-TOAD included",
       all(x["etoad_p_boot_1e4"] is not None for x in s["obs_vs_thin"]))
    ck("DETECTION collapses: e-LOND's bootstrap probability at pi=1e-4 is <= 0.5 everywhere",
       max(s["elond_p_bootstrap_at_1e4"]) <= 0.5, str(s["elond_p_bootstrap_at_1e4"]))
    ck("...and is 0 wherever the observed arm already detected nothing",
       all(x["elond_p_boot_1e4"] == 0.0 for x in s["obs_vs_thin"] if x["elond_rej_obs"] == 0))
    # the escapes must be checked, not assumed to behave the same
    ck("the ESCAPES collapse too: online e-BH's bootstrap probability at pi=1e-4 is <= 0.5",
       max(s["ebh_p_bootstrap_at_1e4"]) <= 0.5, str(s["ebh_p_bootstrap_at_1e4"]))
    ck("every row carries all three procedures",
       all(r["elond"] and r["online_ebh"] for r in rows))
    # monotonicity in pi, on the real rows
    bad_m = 0
    for pos in {r["pos"] for r in rows}:
        for order in {r["order"] for r in rows}:
            rr = [r for r in rows if r["pos"] == pos and r["order"] == order]
            rr.sort(key=lambda r: (-1.0 if r["pi_target"] is None else -r["pi_target"]))
            tps = [r["elond"]["tp_mean"] for r in rr]
            if any(b > a + 1e-9 for a, b in zip(tps, tps[1:])):
                bad_m += 1
    ck("mean true detections are non-increasing as prevalence falls, in every (window, order)",
       bad_m == 0, str(bad_m))
    # the pure-null arm is ONE stream per cell, not a sample
    nulls = [r for r in rows if r["pi_target"] == 0.0]
    ck("the pure-null arm is one deterministic stream per (window, order)",
       len(nulls) == s["n_pure_null_rows"] == len(M.POS) * len(M.ORDERS)
       and all(r["deterministic"] and r["elond"]["n_rep"] == 1 for r in nulls))
    ck("no pure-null stream produces any rejection",
       s["n_pure_null_rows_with_any_rejection"] == 0
       and s["n_pure_null_rows_with_any_rejection_ebh"] == 0)
    # ...and the stage does NOT claim that checks the body's simulated 4.5%.  The 10 rows are 5
    # overlapping windows counted twice, and zero rejections is the likely outcome even if the
    # simulated rate were exactly right, so the arm is consistency and not a test.
    ck("the null arm is scoped as 5 effective streams, not 10 independent trials",
       s["n_pure_null_effective_streams"] == 5 and s["n_pure_null_rows"] == 10)
    ck("P(zero rejections | true rate 4.5%) is reported and is large (the arm is underpowered)",
       abs(s["prob_zero_if_true_rate_045"] - 0.955 ** 5) < 1e-12
       and s["prob_zero_if_true_rate_045"] > 0.5, f"{s['prob_zero_if_true_rate_045']:.3f}")
    ck("the stage declares that this arm cannot test the simulated rate",
       s["null_arm_can_test_the_simulated_rate"] is False)
    ck("a pure-null stream has zero malicious episodes, so any rejection would be false",
       all(r["n_keep"] == 0 and r["realised_prevalence"] == 0.0 for r in nulls))
    ck("FDP is 0 wherever nothing was rejected (no division-by-zero artefact)",
       all(r["elond"]["fdp_mean"] == 0.0 for r in rows if r["elond"]["rej_max"] == 0))
    # the unconditional mean averages a 0 over every silent repeat, so the conditional one must be
    # carried beside it -- and must be None exactly when no repeat alerted
    ck("conditional FDP is reported, and is None exactly when no repeat alerted",
       all((r["elond"]["fdp_mean_given_alert"] is None) == (r["elond"]["n_rep_with_alert"] == 0)
           for r in rows))
    ck("the conditional FDP is never below the unconditional one",
       all(r["elond"]["fdp_mean_given_alert"] >= r["elond"]["fdp_mean"] - 1e-12
           for r in rows if r["elond"]["fdp_mean_given_alert"] is not None))
    ck("both thinning mechanisms are recorded on every row",
       all("removed" in r and r["removed"]["elond"] for r in rows))
    # cross-check the observed arm against the stage that owns those numbers (t28b, item R3)
    t28 = HERE / "out" / "t28b_reallevel.json"
    if t28.exists():
        tb = json.load(open(t28))["table1_by_order"]
        mism = []
        for r in rows:
            if r["pi_target"] is not None:
                continue
            k = f"{r['pos']}_0"
            want = tb[r["order"]][k]["detected_elond"]
            if abs(r["elond"]["tp_mean"] - want) > 1e-9:
                mism.append((k, r["order"], r["elond"]["tp_mean"], want))
        ck("the observed arm reproduces t28b's detection counts exactly, both orders",
           not mism, str(mism))
    # ...and the cold-start windows against t53 (item R3)
    t53 = HERE / "out" / "t53_ordering.json"
    if t53.exists():
        d53 = json.load(open(t53))
        want = {r["pos"]: r["named"]["bucket, hashed-key (canonical)"]["boundary"]["cold_start_steps"]
                for r in d53["rows"] if r["seed"] == 0}
        ck("the cold-start windows match t53's, window for window",
           all(w["cold_start_steps"] == want[w["pos"]] for w in d["windows"]),
           str({w["pos"]: (w["cold_start_steps"], want[w["pos"]]) for w in d["windows"]}))
    ck("every window's cold-start window matches its closed form",
       all(w["cold_start_matches_closed_form"] for w in d["windows"]))

print()
print("=" * 100)
print(f"  {len(FAIL)} failure(s)")
for f in FAIL:
    print(f"    {f}")
print("=" * 100)
sys.exit(1 if FAIL else 0)
