"""Unit tests for t58_semantic_blur.py (review-7 item R4).

The discipline is the one t56b/t57b use and for the same reason: the tests drive the SHIPPED
functions, lifted out of `src/lib/t58_semantic_blur.py` by AST rather than restated here, so a test
cannot pass against a restatement of the code it is meant to check.  Everything the stage claims is
checked against an independent brute force over small synthetic inputs, plus the real record where
the claim is about the record.

Run:  proto/.venv/bin/python proto/t58b_semanticblur_selftest.py
"""
import ast, json, re, sys, types, itertools, subprocess, tempfile, pathlib
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parent / "src" / "lib" / "t58_semantic_blur.py"
NARR = HERE.parent / "src" / "lib" / "data" / "lspr23_attacknarratives.json"
OUT = HERE.parent / "src" / "lib" / "out" / "t58_semantic_blur.json"
FAIL = []


def ck(label, cond, detail=""):
    if not cond:
        FAIL.append(f"{label}   {detail}" if detail else label)
    print(f"  {'ok  ' if cond else 'FAIL'}  {label}" + (f"   {detail}" if detail and not cond else ""))


def lift(names):
    """Import the named top-level functions/constants from the SHIPPED source, with nothing else.

    Parsing rather than importing keeps the heavy module-level imports (sklearn, the flow cache) out
    of the test while still exercising the exact code that ships."""
    tree = ast.parse(SRC.read_text())
    want = ast.Module(body=[], type_ignores=[])
    got = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef,)) and n.name in names:
            want.body.append(n); got.add(n.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id in names:
                    want.body.append(n); got.add(t.id)
    missing = set(names) - got
    if missing:
        raise SystemExit(f"cannot lift {missing} from {SRC}")
    mod = types.ModuleType("t58_lifted")
    mod.__dict__.update(np=np, json=json, re=re, dt=__import__("datetime").datetime,
                        Path=pathlib.Path)
    import datetime as _dt
    mod.__dict__["dt"] = _dt
    mod.__dict__["NARR"] = NARR
    mod.__dict__["IPV4"] = re.compile(r"\d+\.\d+\.\d+\.\d+")
    exec(compile(ast.fix_missing_locations(want), "<lifted>", "exec"), mod.__dict__)
    return mod


M = lift(["_iso", "load_redteam", "attribute", "alert_attributes", "verify_segment_map", "q",
          "ATOMIC_BUCKET", "BUCKETS", "N_NULL"])

print("=" * 100)
print("1. the record parses to what the paper says it does (independent re-parse)")
print("=" * 100)
raw = [json.loads(l) for l in open(NARR) if l.strip()]
tasks, steps = M.load_redteam()
ck("288 tasks", len(tasks) == len(raw) == 288, f"{len(tasks)} vs {len(raw)}")
n_timed_raw = sum(1 for r in raw for t in (r.get("Steps_submitted_time") or []) if t)
ck("295 timed step submissions, matching a direct count",
   len(steps) == n_timed_raw == 295, f"{len(steps)} vs {n_timed_raw}")
n_steps_raw = sum(len(r["Steps_name"]) for r in raw)
ck("576 steps in total, so 295/576 are timed", n_steps_raw == 576, str(n_steps_raw))
# the segment map is EXACTLY a constant-prefix strip, nothing cleverer
raw_segs = {s for r in raw for s in (r.get("Segments") or []) if s}
ck("every declared segment carries the bt_ prefix",
   all(s.startswith("bt_") for s in raw_segs), str(sorted(raw_segs)))
ck("the stripped names are what load_redteam stores",
   {s for t in tasks for s in t["segs"]} == {s[3:] for s in raw_segs})
ck("six distinct segments", len(raw_segs) == 6, str(len(raw_segs)))
# every step index maps back to its own task
by_task = {}
for k, tm in steps:
    by_task.setdefault(k, []).append(tm)
ok = all(sorted(by_task[k]) == sorted(M._iso(t) for t in (raw[k]["Steps_submitted_time"] or []) if t)
         for k in by_task)
ck("each step's time is attached to its own task", ok)
tm = sorted(t for _, t in steps)
import datetime as dt
ck("submissions span 2023-03-09 07:03..15:08 UTC",
   dt.datetime.fromtimestamp(tm[0], dt.timezone.utc).strftime("%Y-%m-%d %H:%M") == "2023-03-09 07:03"
   and dt.datetime.fromtimestamp(tm[-1], dt.timezone.utc).strftime("%H:%M") == "15:08")

print()
print("=" * 100)
print("2. `attribute` against an independent brute force over synthetic inputs")
print("=" * 100)
rng = np.random.default_rng(4)


def brute(step_task, step_time, segc, ipc, segsets, ends, bidx, w, spatial):
    """Independent O(alerts x steps) reference, written from the RULE not from the code."""
    n_a = len(segsets)
    spa = np.zeros(n_a, int); tpa = np.zeros(n_a, int); hits = set()
    gap = np.full(n_a, np.nan)
    for a in range(n_a):
        lo = bidx[a] * w; hi = lo + w
        got = []
        for k, t in zip(step_task, step_time):
            if not (lo <= t < hi):
                continue
            sp_ok = {"none": True,
                     "ip": bool(ipc[k] & {int(ends[a, 0]), int(ends[a, 1])}),
                     "seg": bool(segc[k] & segsets[a]),
                     "both": bool(segc[k] & segsets[a]) or bool(ipc[k] & {int(ends[a, 0]),
                                                                          int(ends[a, 1])})}[spatial]
            if sp_ok:
                got.append((k, t))
        if got:
            spa[a] = len(got); tpa[a] = len({k for k, _ in got}); hits |= {k for k, _ in got}
            mid = (lo + hi) / 2.0
            gap[a] = min(abs(t - mid) for _, t in got)
    return spa, tpa, gap, spa > 0, hits


mismatch = 0
for trial in range(60):
    n_t, n_s, n_a = 6, 25, 7
    segc = [set(rng.choice(5, rng.integers(0, 3), replace=False).tolist()) for _ in range(n_t)]
    ipc = [set(rng.choice(9, rng.integers(0, 2), replace=False).tolist()) for _ in range(n_t)]
    step_task = rng.integers(0, n_t, n_s)
    step_time = np.sort(rng.integers(0, 4000, n_s).astype(float))
    segsets = [set(rng.choice(5, rng.integers(0, 3), replace=False).tolist()) for _ in range(n_a)]
    ends = rng.integers(0, 9, (n_a, 2)).astype(np.int64)
    w = int(rng.choice([300, 900, 1800]))
    bidx = rng.integers(0, 4000 // w + 1, n_a).astype(np.int64)
    for sp in ("none", "seg", "ip", "both"):
        a1 = M.attribute(step_task, step_time, segc, ipc, segsets, ends, bidx, w, spatial=sp)
        a2 = brute(step_task, step_time, segc, ipc, segsets, ends, bidx, w, sp)
        same = (np.array_equal(a1[0], a2[0]) and np.array_equal(a1[1], a2[1])
                and np.allclose(np.nan_to_num(a1[2], nan=-1), np.nan_to_num(a2[2], nan=-1))
                and np.array_equal(a1[3], a2[3]) and a1[4] == a2[4])
        mismatch += 0 if same else 1
ck("shipped `attribute` == brute force on 60 x 4 random cases", mismatch == 0, f"{mismatch} differ")

# the four variants must nest: ip and seg are each subsets of both, and both of none
nest_bad = 0
for trial in range(40):
    n_t, n_s, n_a = 5, 20, 6
    segc = [set(rng.choice(4, rng.integers(0, 3), replace=False).tolist()) for _ in range(n_t)]
    ipc = [set(rng.choice(7, rng.integers(0, 2), replace=False).tolist()) for _ in range(n_t)]
    step_task = rng.integers(0, n_t, n_s)
    step_time = np.sort(rng.integers(0, 3000, n_s).astype(float))
    segsets = [set(rng.choice(4, rng.integers(0, 3), replace=False).tolist()) for _ in range(n_a)]
    ends = rng.integers(0, 7, (n_a, 2)).astype(np.int64)
    w = 600; bidx = rng.integers(0, 6, n_a).astype(np.int64)
    got = {sp: M.attribute(step_task, step_time, segc, ipc, segsets, ends, bidx, w, spatial=sp)
           for sp in ("none", "seg", "ip", "both")}
    if not (np.all(got["seg"][0] <= got["both"][0]) and np.all(got["ip"][0] <= got["both"][0])
            and np.all(got["both"][0] <= got["none"][0])):
        nest_bad += 1
    # `both` is exactly the union of the two conjunct-relaxations, per alert
    for a in range(n_a):
        if got["both"][4] and not (got["seg"][4] | got["ip"][4]) >= got["both"][4]:
            nest_bad += 1
ck("seg, ip <= both <= temporal-only, and both == seg OR ip", nest_bad == 0, str(nest_bad))

# localisation error can never exceed half the bucket, by construction
loc_bad = 0
for trial in range(40):
    n_t, n_s, n_a = 4, 15, 5
    segc = [{0} for _ in range(n_t)]; ipc = [set() for _ in range(n_t)]
    step_task = rng.integers(0, n_t, n_s)
    step_time = np.sort(rng.integers(0, 3000, n_s).astype(float))
    segsets = [{0} for _ in range(n_a)]
    ends = np.zeros((n_a, 2), np.int64)
    w = int(rng.choice([300, 600, 1200])); bidx = rng.integers(0, 3000 // w + 1, n_a).astype(np.int64)
    _, _, gap, hit, _ = M.attribute(step_task, step_time, segc, ipc, segsets, ends, bidx, w)
    g = gap[np.isfinite(gap)]
    if g.size and g.max() > w / 2 + 1e-9:
        loc_bad += 1
ck("localisation error <= bucket/2 always (the step is inside the bucket)", loc_bad == 0, str(loc_bad))

# an empty step list, or no alerts, must return empties rather than raise
e = M.attribute(np.zeros(0, np.int64), np.zeros(0), [], [], [], np.zeros((0, 2), np.int64),
                np.zeros(0, np.int64), 300)
ck("no alerts and no steps -> empty, not an exception", e[0].size == 0 and e[4] == set())

print()
print("=" * 100)
print("3. the permutation null is the right null")
print("=" * 100)
# Permuting which task a submission belongs to must leave the TEMPORAL structure untouched: the
# number of steps in each alert's bucket is unchanged, so any difference between observed and null
# is spatial.  That is the whole claim the null makes.
same_temporal = True
for trial in range(30):
    n_t, n_s, n_a = 5, 30, 8
    segc = [set(rng.choice(4, rng.integers(0, 3), replace=False).tolist()) for _ in range(n_t)]
    ipc = [set() for _ in range(n_t)]
    step_task = rng.integers(0, n_t, n_s)
    step_time = np.sort(rng.integers(0, 3600, n_s).astype(float))
    segsets = [set(rng.choice(4, rng.integers(1, 3), replace=False).tolist()) for _ in range(n_a)]
    ends = np.zeros((n_a, 2), np.int64)
    w = 900; bidx = rng.integers(0, 5, n_a).astype(np.int64)
    base = M.attribute(step_task, step_time, segc, ipc, segsets, ends, bidx, w, spatial="none")[0]
    perm = step_task[rng.permutation(n_s)]
    after = M.attribute(perm, step_time, segc, ipc, segsets, ends, bidx, w, spatial="none")[0]
    same_temporal &= np.array_equal(base, after)
ck("permuting task labels leaves the temporal-only counts identical", same_temporal)

# The 86400 s rows tie their label-null for a specific reason, and the FIRST explanation written
# here was wrong (the blind audit caught it).  It is NOT that the spatial conjunct goes vacuous --
# on the real data at 0.70/first-flow/86400 s the temporal arm sees 30 alerts and the segment arm
# 12, so the filter is still biting.  It is that every submission lands in ONE daily bucket, so
# permuting which task a time belongs to cannot move a step between alerts: the permutation is
# DEGENERATE.  Test that distinction directly -- one bucket ties even with a biting filter, while
# several buckets do not tie.
n_t, n_s = 6, 30
segc = [{i % 3} for i in range(n_t)]                      # a real, biting spatial filter
ipc = [set() for _ in range(n_t)]
step_task = rng.integers(0, n_t, n_s)
step_time = np.sort(rng.integers(0, 3000, n_s).astype(float))
n_a = 5
segsets = [{i % 3} for i in range(n_a)]; ends = np.zeros((n_a, 2), np.int64)


def mean_over_hit(sp, h):
    return float(sp[h].mean()) if h.any() else 0.0


# (i) ONE bucket for everything: every permutation gives the identical per-alert count
one = np.zeros(n_a, np.int64)
base = M.attribute(step_task, step_time, segc, ipc, segsets, ends, one, 86400)
ties = all(np.array_equal(base[0],
                          M.attribute(step_task[rng.permutation(n_s)], step_time, segc, ipc,
                                      segsets, ends, one, 86400)[0]) for _ in range(30))
seg_bites = (M.attribute(step_task, step_time, segc, ipc, segsets, ends, one, 86400,
                         spatial="seg")[0].sum()
             < M.attribute(step_task, step_time, segc, ipc, segsets, ends, one, 86400,
                           spatial="none")[0].sum())
ck("a single shared bucket makes the label-permutation null DEGENERATE (it ties exactly)", ties)
ck("...and it ties even though the spatial filter is still biting (so 'vacuous' is the wrong reason)",
   seg_bites)
# (ii) several buckets: the same permutation now moves counts, so the null is not degenerate
many = np.arange(n_a, dtype=np.int64) % 4
b0 = M.attribute(step_task, step_time, segc, ipc, segsets, ends, many, 600)[0]
moved = any(not np.array_equal(b0, M.attribute(step_task[rng.permutation(n_s)], step_time, segc,
                                               ipc, segsets, ends, many, 600)[0])
            for _ in range(60))
ck("with several buckets the label null is NOT degenerate", moved)

print()
print("=" * 100)
print("4. `alert_attributes`: bucket index and segment sets, against brute force")
print("=" * 100)


class FakeEp(dict):
    pass


bad = 0
for trial in range(40):
    n_flow = 200
    T = 12
    gid = rng.integers(0, T, n_flow)
    order = rng.permutation(T)
    fired = np.zeros(T, bool); fired[rng.choice(T, 4, replace=False)] = True
    seg_s = rng.integers(0, 5, n_flow); seg_d = rng.integers(0, 5, n_flow)
    ip_s = rng.integers(0, 9, n_flow); ip_d = rng.integers(0, 9, n_flow)
    # every flow of a group shares its endpoints, as the real grouping key guarantees
    for g in range(T):
        m = gid == g
        if m.any():
            ip_s[m] = ip_s[m][0]; ip_d[m] = ip_d[m][0]
    first_ts_g = rng.integers(0, 10_000, T).astype(np.int64) * 1_000_000
    ep = FakeEp(order=order, gid=gid, first_ts_g=first_ts_g)
    w = 1800
    orig, segsets, seg_src_only, seg_dst_only, ends, bidx = M.alert_attributes(
        ep, fired, gid, seg_s, seg_d, ip_s, ip_d, first_ts_g, w)
    exp_orig = order[np.flatnonzero(fired)]
    if not np.array_equal(orig, exp_orig):
        bad += 1; continue
    for i, o in enumerate(orig):
        m = gid == o
        exp_seg = set(seg_s[m].tolist()) | set(seg_d[m].tolist())
        if segsets[i] != exp_seg:
            bad += 1
        # the per-side sets, used for the union sensitivity, must be exactly their own sides
        if seg_src_only[i] != set(seg_s[m].tolist()) or seg_dst_only[i] != set(seg_d[m].tolist()):
            bad += 1
        if segsets[i] != seg_src_only[i] | seg_dst_only[i]:
            bad += 1
        if not m.any():
            continue
        if int(ends[i, 0]) != int(ip_s[m][0]) or int(ends[i, 1]) != int(ip_d[m][0]):
            bad += 1
        if int(bidx[i]) != int(first_ts_g[o] // (w * 1_000_000)):
            bad += 1
ck("alert bucket index, per-side and union segment sets, and endpoint pair, match a\n        direct recompute".replace("\n        ", " "), bad == 0, str(bad))

print()
print("=" * 100)
print("5. the shipped artefact is internally consistent")
print("=" * 100)
if not OUT.exists():
    print(f"  SKIP  {OUT} not present")
else:
    d = json.load(open(OUT))
    rows = d["rows"]
    ck("the bt_ segment map is corroborated by a channel that does not use it",
       d["segment_map_check"]["seg_agree"] > 0 and d["segment_map_check"]["seg_disagree"] == 0,
       str(d["segment_map_check"]))
    # nesting must hold on the REAL rows too
    nest = all(r["seg_only"]["n_alerts"] <= r["temporal_only"]["n_alerts"]
               and r["ip_only"]["n_alerts"] <= r["temporal_only"]["n_alerts"]
               and r["n_alerts_with_step"] <= r["temporal_only"]["n_alerts"]
               and r["n_alerts_with_step"] <= r["n_alerts"] for r in rows)
    ck("on the real rows: attributed <= temporally overlapping <= issued", nest)
    loc = all(r["loc_err_median_s"] is None or r["loc_err_median_s"] <= r["bucket_s"] / 2 + 1e-9
              for r in rows)
    ck("every reported localisation error is within half its bucket", loc)
    ck("a row with no temporal overlap attributes nothing",
       all(r["n_alerts_with_step"] == 0 for r in rows if r["temporal_only"]["n_alerts"] == 0))
    ck("every row with an attribution reports a null to compare it against",
       all((r["steps_per_alert"] is None) == (r["steps_per_alert_null"] is None) for r in rows))
    ck("the null never exceeds its own 97.5th percentile",
       all(r["steps_per_alert_null"] <= r["steps_per_alert_null_p975"] + 1e-9
           for r in rows if r["steps_per_alert_null"] is not None))
    sat = [r for r in rows if r["bucket_s"] == 86400 and r["steps_per_alert"] is not None]
    ck("at the 24 h bucket the observation ties its LABEL null (one shared bucket -> degenerate)",
       all(abs(r["steps_per_alert"] - r["steps_per_alert_null"]) < 1e-9 for r in sat),
       f"{len(sat)} rows")
    # ...and the reason is NOT that the spatial filter stops biting: check on the real rows
    bite = [r for r in sat if r["temporal_only"]["n_alerts"] > r["seg_only"]["n_alerts"]]
    ck("...and on the real data the spatial filter is still biting there (>= 1 row)", len(bite) >= 1,
       f"{len(bite)} of {len(sat)}")
    # the SHIFT null is the sharper one and must be reported wherever the label null is
    ck("every row with a label null also carries a timeline-shift null",
       all((r["steps_per_alert_null"] is None) == (r["steps_per_alert_shiftnull"] is None)
           for r in rows))
    # which conjunct carries the result -- the audit's finding, pinned as a regression test
    cj = d["summary"]["conjuncts"]
    ck("RECORDED: the compromise-IP conjunct adds no alert the segment conjunct did not",
       cj["ip_adds_nothing_over_seg"] is True and cj["attributed_alerts"] == cj["seg_only_alerts"],
       str(cj))
    ck("the union of the two segment sides is reported alongside each side alone",
       all("seg_side_src" in r and "seg_side_dst" in r for r in rows))
    ck("the bucket-span result is reported alongside the tighter flow-span one",
       all("flow_span" in r for r in rows))
    # the circularity confound, reported rather than assumed away
    ck("CONFOUND recorded: every attributed alert sits on a labelled-malicious episode",
       d["summary"]["any_attributed_on_benign"] is False)
    # tasks touched can never exceed the attributable tasks in that window
    ck("tasks touched <= attributable tasks in the window",
       all(r["n_tasks_touched"] <= r["n_tasks_attributable_in_window"] for r in rows))
    ck("task coverage is a fraction in [0, 1]",
       all(r["task_coverage"] is None or 0.0 <= r["task_coverage"] <= 1.0 for r in rows))
    # steps/alert and tasks/alert must be consistent: a task can contribute many steps
    ck("steps per alert >= tasks per alert wherever both are defined",
       all(r["steps_per_alert"] >= r["tasks_per_alert"] - 1e-9 for r in rows
           if r["steps_per_alert"] is not None))
    # the two orders must agree on everything that does not depend on the fired set
    by = {}
    for r in rows:
        by.setdefault((r["pos"], r["bucket_s"]), {})[r["order"]] = r
    ck("both within-bucket orders see the same window and the same reference",
       all(v["keyhash"]["n_tasks_attributable_in_window"]
           == v["first-flow"]["n_tasks_attributable_in_window"] for v in by.values() if len(v) == 2))

print()
print("=" * 100)
print("6. Spearman, against an independent implementation")
print("=" * 100)
# spearman and its avg_rank helper are nested inside main(), so lift both by name from anywhere
# in the tree rather than from the module's top level.
tree = ast.parse(SRC.read_text())
picked = {}
for n in ast.walk(tree):
    if isinstance(n, ast.FunctionDef) and n.name in ("spearman", "avg_rank"):
        picked[n.name] = n
if set(picked) != {"spearman", "avg_rank"}:
    raise SystemExit(f"cannot lift spearman/avg_rank from {SRC}: found {sorted(picked)}")
mod = types.ModuleType("sp"); mod.__dict__["np"] = np
exec(compile(ast.fix_missing_locations(
    ast.Module(body=[picked["avg_rank"], picked["spearman"]], type_ignores=[])), "<s>", "exec"),
     mod.__dict__)


def ref_spearman(a, b):
    """Average-rank Spearman, written from the definition.  TIES MATTER: an earlier version of both
    the shipped code and this test ranked with argsort(argsort(.)), which hands tied values
    arbitrary distinct ranks and turns a flat series into a perfectly monotone one."""
    from math import sqrt
    n = len(a)

    def ar(v):
        srt = sorted(v)
        out = []
        for x in v:
            lo = srt.index(x)                       # first position of this value
            hi = len(srt) - 1 - srt[::-1].index(x)  # last position of this value
            out.append((lo + hi) / 2.0)
        return out

    ra, rb = ar(a), ar(b)
    ma = sum(ra) / n; mb = sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return num / den if den else None


bad = 0
for _ in range(50):
    n = int(rng.integers(3, 9))
    a = rng.permutation(n).astype(float) + rng.normal(0, 1e-6, n)   # distinct values, no ties
    b = rng.permutation(n).astype(float) + rng.normal(0, 1e-6, n)
    got = mod.spearman(a.tolist(), b.tolist()); exp = ref_spearman(a.tolist(), b.tolist())
    if got is None or abs(got - exp) > 1e-9:
        bad += 1
ck("shipped spearman == an independent rank-correlation on 50 tie-free cases", bad == 0, str(bad))

# TIES -- the case the blind audit found, which the tie-free test above sails straight past
bad_t = 0
for _ in range(200):
    n = int(rng.integers(4, 9))
    a = rng.integers(0, 3, n).astype(float)        # deliberately many ties
    b = rng.integers(0, 3, n).astype(float)
    got = mod.spearman(a.tolist(), b.tolist()); exp = ref_spearman(a.tolist(), b.tolist())
    if (got is None) != (exp is None) or (got is not None and abs(got - exp) > 1e-9):
        bad_t += 1
ck("shipped spearman == average-rank reference on 200 HEAVILY TIED cases", bad_t == 0, str(bad_t))
# the exact series the audit flagged: a flat leg must NOT read as perfectly monotone
tie_steps = [3.0, 3.1538461538461537, 3.1538461538461537, 3.1538461538461537]
tie_atoms = [9.933333333333334, 19.612903225806452, 21.612903225806452, 21.612903225806452]
got = mod.spearman(tie_steps, tie_atoms)
ck("the 0.77 tied series reads +0.816, not +1.000",
   got is not None and abs(got - 0.8164965809277259) < 1e-6, f"{got}")
ck("a wholly constant series has no rank correlation (returns None, not 1.0)",
   mod.spearman([2.0, 2.0, 2.0, 2.0], [1.0, 2.0, 3.0, 4.0]) is None)
ck("a perfectly increasing pair gives +1", abs(mod.spearman([1, 2, 3, 4], [10, 20, 30, 40]) - 1) < 1e-12)
ck("a perfectly decreasing pair gives -1", abs(mod.spearman([1, 2, 3, 4], [40, 30, 20, 10]) + 1) < 1e-12)
ck("fewer than 3 points returns None", mod.spearman([1, 2], [3, 4]) is None)

print()
print("=" * 100)
print("7. the shipped copy is the copy that ran")
print("=" * 100)
# t58 is authored directly in src/lib (like t52-t57), so there is no proto->src generation to check;
# what must be true is that the artefact was produced by THIS source.  Compare the attribution rule
# recorded in the artefact against the docstring's rule and the constants against the module's.
if OUT.exists():
    d = json.load(open(OUT))
    c = d["config"]
    ck("artefact BUCKETS match the shipped constant", c["BUCKETS"] == M.BUCKETS, str(c["BUCKETS"]))
    ck("artefact atomic bucket matches the shipped constant",
       c["atomic_bucket_s"] == M.ATOMIC_BUCKET)
    ck("artefact n_null matches the shipped constant", c["n_null"] == M.N_NULL)
    ck("artefact records the pre-committed attribution rule",
       "bucket span" in c["attribution_rule"] and "compromise IPs" in c["attribution_rule"])
    ck("artefact records the segment map", "bt_" in c["segment_map"])

print()
print("=" * 100)
print(f"  {len(FAIL)} failure(s)")
for f in FAIL:
    print(f"    {f}")
print("=" * 100)
sys.exit(1 if FAIL else 0)
