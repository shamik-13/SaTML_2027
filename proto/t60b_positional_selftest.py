"""Unit tests for t60_positional.py (the group-creation / cold-start-exhaustion attack).

Same discipline as t56b-t59b: the tests drive the SHIPPED functions, AST-lifted from
`src/lib/t60_positional.py`, never a restatement of them.

The claim most worth attacking is that G* is a REAL minimum obtained by replay rather than a closed
form dressed up as a measurement -- so the central test constructs streams whose answer is known by
hand and checks the shipped replay finds exactly it.

Run:  proto/.venv/bin/python proto/t60b_positional_selftest.py
"""
import ast, json, sys, types, pathlib
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parent / "src" / "lib" / "t60_positional.py"
OUT = HERE.parent / "src" / "lib" / "out" / "t60_positional.json"
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
    sys.path.insert(0, str(HERE.parent / "src" / "lib"))
    from h6_procs import Ctx, make_gamma, run_lond
    from scipy.special import zeta
    mod = types.ModuleType("t60_lifted")
    mod.__dict__.update(np=np, Ctx=Ctx, make_gamma=make_gamma, run_lond=run_lond, zeta=zeta)
    exec(compile(ast.fix_missing_locations(want), "<lifted>", "exec"), mod.__dict__)
    return mod


M = lift(["cold_start", "survival_curve", "targeted_gstar", "A", "W0", "K", "KINDS",
          "ORDERS", "POS", "G_HEADROOM"])
sys.path.insert(0, str(HERE.parent / "src" / "lib"))
from h6_procs import Ctx, make_gamma, run_lond                     # noqa: E402

print("=" * 100)
print("1. G* on a stream whose answer is known by hand")
print("=" * 100)
# One malicious episode at index p carrying exactly the ceiling; nothing else carries anything.
# With R = 0 the level at step t is A*gamma_t, so the episode fires iff CEIL >= 1/(A*gamma_{p+1}),
# i.e. iff its step is within the cold-start window.  Inserting G ahead of it moves it to step
# p+1+G, so the minimal suppressing G is exactly w_cold - p, and nothing else can matter.
T = 3_000
g1, _ = make_gamma("poly", T)
# The expected answers must be LARGE and DISTINCT.  An earlier version set CEIL so the episode
# cleared exactly at its own step, which made every hand case collapse to G* = 1 -- an
# implementation that suppressed everything at any G > 0 would have passed it (the blind audit
# caught this).  Here the episode clears out to step `last`, so G* = last - p varies by construction.
for p, last in ((10, 500), (100, 700), (400, 1200), (5, 40)):
    CEIL = 1.0 / (M.A * g1[last])                  # clears through step `last`, not beyond
    w, closed = M.cold_start(CEIL, T)
    Ev = np.zeros(T); ismal = np.zeros(T, bool)
    Ev[p] = CEIL; ismal[p] = True
    fb, ins = M.survival_curve(Ev, ismal, CEIL, np.array([p]), last + 20, "zero",
                               np.zeros(1), np.random.default_rng(0))
    off = np.flatnonzero(~fb[:, 0])
    gstar = int(off[0]) if off.size else None
    ck(f"p={p}, clears to {last}: replayed G* == {last - p} (large and case-specific)",
       gstar == last - p, f"got {gstar}, w_cold={w}")
    ck(f"p={p}: it fires at every G < G* and at none >= G*",
       bool(fb[:gstar, 0].all()) and not bool(fb[gstar:, 0].any()))
ck("the hand cases do not all collapse to the same answer (which would test nothing)",
   len({500 - 10, 700 - 100, 1200 - 400, 40 - 5}) == 4)

print()
print("=" * 100)
print("2. the replay is a replay: it agrees with running e-LOND directly")
print("=" * 100)
rng = np.random.default_rng(7)
bad = 0
for trial in range(12):
    T = 1_500
    Ev = np.where(rng.random(T) < 0.01, 8e4, 0.0)
    ismal = rng.random(T) < 0.02
    CEIL = 8e4
    tg = np.flatnonzero(np.zeros(T, bool))
    ctx = Ctx(Ev, ismal, CEIL, alpha=M.A, w0=M.W0)
    f0 = np.zeros(T, bool); run_lond(ctx, make_gamma("poly", T)[0], fired=f0)
    tg = np.flatnonzero(f0 & ismal)
    if tg.size == 0:
        continue
    gmax = 40
    fb, ins = M.survival_curve(Ev, ismal, CEIL, tg, gmax, "zero", np.zeros(1),
                               np.random.default_rng(1))
    for g in (0, 1, 7, 23, gmax):
        Ev2 = np.concatenate([np.zeros(g), Ev]); im2 = np.concatenate([np.zeros(g, bool), ismal])
        f2 = np.zeros(T + g, bool)
        run_lond(Ctx(Ev2, im2, CEIL, alpha=M.A, w0=M.W0), make_gamma("poly", T + g)[0], fired=f2)
        if not np.array_equal(fb[g], f2[g + tg]):
            bad += 1
ck("survival_curve == an independent direct e-LOND run at every sampled G", bad == 0, str(bad))
# G = 0 must reproduce the unattacked run -- checked against a real run, not asserted True
T = 900
rr = np.random.default_rng(21)
Ev = np.where(rr.random(T) < 0.02, 6e4, 0.0); ismal = rr.random(T) < 0.05
f0 = np.zeros(T, bool)
run_lond(Ctx(Ev, ismal, 6e4, alpha=M.A, w0=M.W0), make_gamma("poly", T)[0], fired=f0)
tg0 = np.flatnonzero(f0 & ismal)
if tg0.size:
    fb0, _ = M.survival_curve(Ev, ismal, 6e4, tg0, 3, "zero", np.zeros(1),
                              np.random.default_rng(0))
    ck("G = 0 reproduces the unattacked run exactly", bool(fb0[0].all()))
else:
    ck("G = 0 reproduces the unattacked run exactly (no targets; vacuous)", True)

print()
print("=" * 100)
print("2b. `targeted_gstar` -- the per-episode closed form, driven directly")
print("=" * 100)
# The audit found this was only ever exercised through the artefact, so a broken source could pass.
# Drive it here against a replay, and against the analytic value, including a case whose clearing
# step is FAR beyond the stream length -- the array-search version silently capped that at 2T+3.
z16 = float(__import__("scipy.special", fromlist=["zeta"]).zeta(1.6, 1))
bad_c, bad_r = 0, 0
for T, p, R, mult in ((1_000, 100, 0, 1.0), (1_000, 10, 3, 1.0), (500, 250, 0, 1.0),
                      (100, 5, 0, 400.0)):     # the last one clears far past the stream
    last_target = int(mult * T // 2) or 50
    gg, _ = make_gamma("poly", last_target + 10)
    Ev = np.zeros(T); ismal = np.zeros(T, bool)
    Ev[p] = 1.0 / (M.A * (R + 1) * gg[last_target]); ismal[p] = True
    got, closed = M.targeted_gstar(Ev, ismal, 1e300, np.array([p]), np.full(T, R))
    want_last = int(np.floor((M.A * (R + 1) * Ev[p] / z16) ** (1.0 / 1.6)))
    if got[0] != max(0, want_last - p) or closed[0] != want_last:
        bad_c += 1
    # replay it at R = 0 only (R > 0 needs real earlier rejections, covered by the artefact)
    if R == 0:
        for G, want_fire in ((max(got[0] - 1, 0), got[0] > 0), (got[0], False)):
            Ev2 = np.concatenate([Ev[:p], np.zeros(G), Ev[p:]])
            im2 = np.concatenate([ismal[:p], np.zeros(G, bool), ismal[p:]])
            f2 = np.zeros(len(Ev2), bool)
            run_lond(Ctx(Ev2, im2, 1e300, alpha=M.A, w0=M.W0),
                     make_gamma("poly", len(Ev2))[0], fired=f2)
            if bool(f2[p + G]) != bool(want_fire):
                bad_r += 1
ck("targeted_gstar == its analytic value on 4 cases, incl. one clearing far past the stream",
   bad_c == 0, str(bad_c))
ck("...and a replay fires at G*-1 and not at G*", bad_r == 0, str(bad_r))
# the cap the audit found: a clearing step beyond 2T+3 must NOT be truncated
gg2, _ = make_gamma("poly", 40_000)
T = 100
Ev = np.zeros(T); ismal = np.zeros(T, bool)
Ev[5] = 1.0 / (M.A * gg2[10_000]); ismal[5] = True
got, closed = M.targeted_gstar(Ev, ismal, 1e300, np.array([5]), np.zeros(T, int))
ck("a target clearing through step ~10,000 in a length-100 stream is not capped at 2T+3",
   got[0] > 2 * T + 3, f"G*={got[0]}, closed_last={closed[0]}")

print()
print("=" * 100)
print("3. the inserted head is NESTED, not redrawn per G")
print("=" * 100)
# Re-drawing the head at each g makes 'insert one more' a fresh experiment and manufactures
# non-monotonicity.  An earlier version did exactly that; the artefact reported up to 72 spurious
# non-monotone targets.  Check the property directly: a benign run's head must be a prefix chain.
pool = np.array([0.0, 0.0, 0.0, 9e4])
T = 400
Ev = np.zeros(T); Ev[50] = 9e4
ismal = np.zeros(T, bool); ismal[50] = True
CEIL = 9e4
# with a nested head, the number of inserted groups that FIRE is non-decreasing in g
_, ins = M.survival_curve(Ev, ismal, CEIL, np.array([50]), 60, "benign", pool,
                          np.random.default_rng(3))
ck("the count of firing inserted groups is non-decreasing in G (head is a prefix chain)",
   bool(np.all(np.diff(ins) >= 0)), str(ins[:12].tolist()))
# and the zero head can never fire, at any G
_, ins0 = M.survival_curve(Ev, ismal, CEIL, np.array([50]), 60, "zero", pool,
                           np.random.default_rng(3))
ck("zero-evidence inserted groups never fire, at any G", int(ins0.max()) == 0)

print()
print("=" * 100)
print("4. the attack does not depend on appending anything to the target")
print("=" * 100)
# thm:padding is about appending to a hypothesis.  Here the target's own evidence is untouched, so
# an append-invariant statistic (the group MAX of R2) buys nothing.  Check the target's evidence is
# byte-identical before and after the attack, at the shifted index.
T = 800; p = 120
g1b, _ = make_gamma("poly", T)
CEIL = 1.0 / (M.A * g1b[p + 1])
Ev = np.zeros(T); Ev[p] = CEIL
ismal = np.zeros(T, bool); ismal[p] = True
G = 50
Ev2 = np.concatenate([np.zeros(G), Ev])
ck("the target's evidence is unchanged by the attack (nothing is appended to it)",
   Ev2[G + p] == Ev[p])
ck("only the target's POSITION changes", int(np.flatnonzero(Ev2 > 0)[0]) == G + p)

print()
print("=" * 100)
print("5. the shipped artefact")
print("=" * 100)
if not OUT.exists():
    print(f"  SKIP  {OUT} not present")
else:
    d = json.load(open(OUT)); rows = d["rows"]; s = d["summary"]
    live = [r for r in rows if r.get("n_targets")]
    ck("every window/order pair is present", len(rows) == len(M.POS) * len(M.ORDERS))
    ck("cells with no detection are recorded as having no target, not skipped",
       all("note" in r for r in rows if not r.get("n_targets")))
    ck("every true detection is suppressible by insertion alone",
       all(r[k]["n_never_suppressed"] == 0 for r in live for k in M.KINDS)
       and s["all_targets_suppressible"])
    ck("no target is reported non-monotone (the head is nested)",
       s["any_nonmonotone"] is False
       and all(r[k]["n_nonmonotone"] == 0 for r in live for k in M.KINDS))
    ck("zero-evidence inserted groups never fire in the artefact either",
       s["inserted_ever_fire_zero"] is False)
    ck("G* never exceeds the scan range (no censoring)",
       all(r[k]["gstar_max"] <= r["g_max"] for r in live for k in M.KINDS))
    # THE MECHANISM, stated correctly.  Two naive guesses are WRONG and the artefact refutes both,
    # which is worth pinning as regression tests because the true statement is the more interesting
    # one: the attack works through the BOOTSTRAP CHAIN as well as through position.
    #
    # (i) G*_max is NOT w_cold - p_min + 1.  w_cold is the last step at which an episode carrying the
    #     full CEILING could clear; a sub-ceiling episode drops out sooner.  The identity holds
    #     against each target's OWN last-clearing step, and w_cold gives only an upper bound.
    bad_mech, bad_bound = [], []
    for r in live:
        i0 = int(np.argmin(r["target_positions"]))          # the earliest target: R = 0 up to it
        p0 = r["target_positions"][i0]; wE = r["target_last_clearing_step"][i0]
        for k in M.KINDS:
            if r[k]["gstar_by_target"][i0] != wE - p0 + 1:
                bad_mech.append((r["pos"], r["order"], k,
                                 r[k]["gstar_by_target"][i0], wE - p0 + 1))
            if r[k]["gstar_max"] > r["cold_start_steps"] - p0 + 1:
                bad_bound.append((r["pos"], r["order"], k))
    ck("the EARLIEST target's G* == (its own last clearing step) - position + 1, exactly",
       not bad_mech, str(bad_mech))
    ck("...and w_cold - p_min + 1 is an upper bound on G*_max, never an equality to rely on",
       not bad_bound, str(bad_bound))
    # (ii) G* is NOT monotone in position.  A later target can be cheaper to suppress because it was
    #      only firing thanks to an earlier rejection: break the chain and it dies at a smaller G.
    #      Confirm the artefact really contains such a target, so the claim is evidenced.
    nonmono_cells = []
    for r in live:
        pairs = sorted(zip(r["target_positions"], r["zero"]["gstar_by_target"]))
        gv = [g for _, g in pairs if g is not None]
        if any(b < a for a, b in zip(gv, gv[1:])):
            nonmono_cells.append((r["pos"], r["order"]))
    ck("G* is not monotone in position -- some targets fire only via the bootstrap chain",
       len(nonmono_cells) > 0, f"cells with a cheaper later target: {nonmono_cells}")
    # what IS universal: killing the whole window costs the largest single G*
    ck("every target's G* is at most the all-silent cost",
       all(g <= r[k]["g_all_suppressed"] for r in live for k in M.KINDS
           for g in r[k]["gstar_by_target"] if g is not None))
    ck("silencing EVERY detection costs the largest single G*",
       all(r[k]["g_all_suppressed"] == r[k]["gstar_max"] for r in live for k in M.KINDS))
    # the access premise the docstring rests on
    ck("all targets sit in the FIRST bucket, so no earlier bucket is available",
       all(r["all_targets_in_first_bucket"] for r in live))
    hashed = [r for r in live if r["order"] != "first-flow"]
    ck("the hash orders' keyspace search is priced, and first-flow's is not (it needs none)",
       all(r["zero"].get("key_trials_targeted_median") is not None
           for r in live if r["order"] == "keyhash")
       and all(r["zero"].get("key_trials_targeted_median") is None
               for r in live if r["order"] != "keyhash"))
    ck("the hash fraction below each target is a probability",
       all(0.0 <= f <= 1.0 for r in live for f in r["hash_fraction_below_target"]))
    ck("the targeted keyspace search is DEARER than the prefix one (a narrower interval)",
       all(r["zero"]["key_trials_targeted_median"] >= r["zero"]["key_trials_prefix_median"]
           for r in live if r["order"] == "keyhash"))
    ck("the keyed order is run too -- it is the case where the offline search is unavailable",
       any(r["order"] == "keyed" for r in rows))

    # ---- the TARGETED attack: the per-episode cost, and the distinction the audit forced ----
    ck("every live cell reports a targeted G* verified against a replay, with no failures",
       all(r.get("targeted_closed_form_replay_failures") == 0
           and r.get("targeted_closed_form_replay_checks", 0) > 0 for r in live))
    # the prefix number is NOT a per-episode cost, and must never be smaller than the targeted one
    # for the earliest target -- an attacker inserting only ahead of itself cannot also delete the
    # detections that raised R.  Check the two are reported separately and do not get conflated.
    ck("targeted and prefix costs are reported as separate quantities",
       all("targeted_gstar_median" in r and "gstar_median" in r["zero"] for r in live))
    ck("the targeted cost is never CHEAPER than the prefix cost (the prefix also breaks the chain)",
       all(r["targeted_gstar_median"] >= r["zero"]["gstar_median"] - 1e-9 for r in live),
       str([(r["pos"], r["order"], r["targeted_gstar_median"], r["zero"]["gstar_median"])
            for r in live if r["targeted_gstar_median"] < r["zero"]["gstar_median"]]))
    ck("the per-episode comparison uses the TARGETED cost, not the prefix one",
       all(abs(c["median_targeted_gstar"]
               - [r for r in live if r["pos"] == c["pos"] and r["order"] == c["order"]][0]
               ["targeted_gstar_median"]) < 1e-9 for c in s["comparison"]))
    ck("the flows-per-group sensitivity is reported (G* is in hypotheses, padding in flows)",
       all(set(c["by_flows_per_group"]) >= {"1", "2"} for c in s["comparison"]))

    # ---- the GROUP-MAX pipeline: the construction non-claim 21 is actually about ----
    gm = d.get("group_max_rows")
    ck("the group-calibrated MAX pipeline is priced, not just the shipped flow pipeline", bool(gm))
    if gm:
        live_gm = [r for r in gm if r["n_targets"]]
        ck("it reproduces t57's firing-group counts", all(r["n_firing_groups"] > 0 for r in gm))
        ck("every group-MAX true detection is suppressible by insertion",
           all(g < r["G"] for r in live_gm for g in r["targeted_gstar"])
           and s["group_max_all_suppressible"])
        ck("...at a cost far below the flow pipeline's, because its cold-start window is tiny",
           all(r["cold_start_steps"] < 200 for r in live_gm),
           str([(r["pos"], r["cold_start_steps"]) for r in live_gm]))
        t57p = HERE / "out" / "t57_group_calibration.json"
        if t57p.exists():
            d57 = json.load(open(t57p))
            want = {r["pos"]: r["stats"]["max"]["n_firing"]
                    for r in d57["rows"] if r["seed"] == 0}
            ck("group-MAX firing counts match t57's exactly (same lifted rules)",
               all(r["n_firing_groups"] == want[r["pos"]] for r in gm),
               str({r["pos"]: (r["n_firing_groups"], want[r["pos"]]) for r in gm}))
    # inserting hypotheses grows T and so LOWERS the margin -- it never helps feasibility
    ck("inserting hypotheses lowers the feasibility margin (it cannot flatter the controller)",
       all(r["margin_at_gmax"] < r["margin_at_0"] for r in live))
    # the comparison against padding must be like-for-like: same window, same order, same seed
    ck("the padding comparison is drawn per (window, order)",
       all(c["median_pad_flows"] is not None for c in s["comparison"]))
    ck("the per-episode verdict is the TARGETED cost against padding, and its NAME says at what "
       "flows-per-group it holds",
       all(c["cheaper_per_episode_at_1_flow_per_group"]
           == (c["median_targeted_gstar"] < c["median_pad_flows"]) for c in s["comparison"]))
    ck("the window verdict is reported at 1 AND 2 flows per group, since it changes",
       all("cheaper_per_window_at_2_flows_per_group" in c for c in s["comparison"])
       and s["n_cells_cheaper_per_window_at_2_flows"] <= s["n_cells_positional_cheaper_per_window"])
    ck("the padding window total is labelled an UPPER bound, with the cheapest single pad beside it",
       all("total_pad_flows_to_silence_window_UPPER" in c and "cheapest_single_pad_LOWER" in c
           for c in s["comparison"]))
    ck("the heavy tail behind the largest ratio is reported, not hidden",
       s["max_pad_sum_top10_share"] is not None and s["max_pad_sum_top10_share"] > 0.5)
    ck("keyspace trials are priced for the TARGETED event, not only the wider prefix event",
       all(r["zero"].get("key_trials_targeted_median") is not None
           for r in live if r["order"] == "keyhash"))
    ck("the keyed order carries NO trial count (it cannot be ranked offline)",
       all(r["zero"].get("key_trials_targeted_median") is None
           for r in live if r["order"] == "keyed"))
    ck("per EPISODE, padding is cheaper everywhere -- insertion does not beat it for one alert",
       s["n_cells_positional_cheaper"] == 0, str(s["n_cells_positional_cheaper"]))
    ck("per WINDOW, insertion is cheaper at most cells -- it silences everything at once",
       s["n_cells_positional_cheaper_per_window"] >= s["n_cells_compared"] - 2,
       f"{s['n_cells_positional_cheaper_per_window']}/{s['n_cells_compared']}")
    # cross-check the cold-start windows against the stage that owns them
    t53 = HERE / "out" / "t53_ordering.json"
    if t53.exists():
        d53 = json.load(open(t53))
        want = {r["pos"]: r["named"]["bucket, hashed-key (canonical)"]["boundary"]
                ["cold_start_steps"] for r in d53["rows"] if r["seed"] == 0}
        ck("cold-start windows match t53's, window for window",
           all(r["cold_start_steps"] == want[r["pos"]] for r in rows))
    # ...and the target counts against t28b
    t28 = HERE / "out" / "t28b_reallevel.json"
    if t28.exists():
        tb = json.load(open(t28))["table1_by_order"]
        ck("target counts equal t28b's detection counts, both orders",
           all(r["n_targets"] == tb[r["order"]][f"{r['pos']}_0"]["detected_elond"] for r in rows))

print()
print("=" * 100)
print(f"  {len(FAIL)} failure(s)")
for f in FAIL:
    print(f"    {f}")
print("=" * 100)
sys.exit(1 if FAIL else 0)
