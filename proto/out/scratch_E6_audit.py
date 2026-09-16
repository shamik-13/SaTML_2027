import ast
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
sys.path.insert(0, str(ROOT))

POS = [0.55, 0.62, 0.70, 0.77, 0.85]
SEEDS = [0, 1]
FAMILY_ORDER = ["src-dst", "src", "dst", "subnet24", "src-dport"]
BUCKET_ORDER = [7200, 3600, 1800, 300, 21600, 86400, None]
CAP_ORDER = ["p99", "max", "p999", "p90", "p50", "mean"]
GRID = [(f, b) for f in FAMILY_ORDER for b in BUCKET_ORDER]


def load_t39_functions(*names):
    src = (ROOT / "t39_E6_transfer.py").read_text()
    tree = ast.parse(src)
    want = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names}
    ns = {"np": np}
    mod = ast.Module(body=[want[n] for n in names], type_ignores=[])
    exec(compile(ast.fix_missing_locations(mod), str(ROOT / "t39_E6_transfer.py"), "exec"), ns)
    return [ns[n] for n in names]


select, normalised_regret, transfer_table = load_t39_functions(
    "select", "normalised_regret", "transfer_table"
)


def clean_bucket(v):
    return None if v is None else int(v)


def grid_values(rows, key, seed):
    lut = {(r["pos"], r["family"], clean_bucket(r["bucket_s"])): r for r in rows if r["seed"] == seed}
    V = np.full((len(POS), len(GRID)), np.nan)
    for w, p in enumerate(POS):
        for c, cfg in enumerate(GRID):
            r = lut.get((p,) + cfg)
            if r is not None and r.get(key) is not None:
                V[w, c] = r[key]
    return V


def cap_values(rows, key, seed):
    lut = {(r["pos"], r["cap"]): r for r in rows if r["seed"] == seed}
    V = np.full((len(POS), len(CAP_ORDER)), np.nan)
    for w, p in enumerate(POS):
        for c, cap in enumerate(CAP_ORDER):
            r = lut.get((p, cap))
            if r is not None and r.get(key) is not None:
                V[w, c] = r[key]
    return V


def report(name, value):
    print(f"{name}: {value}")


g5 = json.load(open(OUT / "t26_H4_5pos.json"))
g2 = json.load(open(OUT / "t26_H4.json"))
c5 = json.load(open(OUT / "t25_H5.json"))
t39 = json.load(open(OUT / "t39_E6.json"))

report("rows five/default/cap", (len(g5["rows"]), len(g2["rows"]), len(c5["rows"])))

for key in ("flow_cov_addis", "flow_cov_elond", "addis_recall"):
    for seed in SEEDS:
        V = grid_values(g5["rows"], key, seed)
        report(f"missing {key} seed {seed}", int(np.isnan(V).sum()))
        report(f"finite support counts {key} seed {seed}", np.isfinite(V).sum(axis=1).tolist())

for seed in SEEDS:
    V = grid_values(g5["rows"], "flow_cov_addis", seed)
    spreads = []
    frozen_rhos = []
    for w, p in enumerate(POS):
        ev = V[w]
        fin = np.isfinite(ev)
        spreads.append(float(ev[fin].max() - ev[fin].min()))
        frozen = ev[GRID.index(("src-dst", 7200))]
        frozen_rhos.append(normalised_regret(ev, frozen))
    report(f"grouping spreads seed {seed}", spreads)
    report(f"grouping frozen rhos seed {seed}", frozen_rhos)

for seed in SEEDS:
    D = cap_values(c5["rows"], "det_trunc", seed)
    NA = cap_values(c5["rows"], "n_att_ep", seed)
    V = D / NA
    report(f"missing cap V seed {seed}", int(np.isnan(V).sum()))
    report(f"n_att_ep unique per window seed {seed}", [sorted(set(NA[w])) for w in range(len(POS))])
    report(f"cap spreads seed {seed}", [float(np.nanmax(V[w]) - np.nanmin(V[w])) for w in range(len(POS))])

keys = [
    "T",
    "n_mal",
    "NC",
    "margin",
    "required_C",
    "feasible",
    "tail_reach",
    "flow_cov_elond",
    "flow_cov_addis",
    "mean_size",
    "p99_size",
    "max_size",
    "elond_rej",
    "elond_tp",
    "elond_recall",
    "elond_silent",
    "addis_rej",
    "addis_tp",
    "addis_recall",
    "ebh_rej",
    "ebh_tp",
    "ebh_recall",
]
five_lut = {
    (r["pos"], r["seed"], r["family"], clean_bucket(r["bucket_s"])): r
    for r in g5["rows"]
}
mismatches = []
for r in g2["rows"]:
    k = (r["pos"], r["seed"], r["family"], clean_bucket(r["bucket_s"]))
    rr = five_lut.get(k)
    if rr is None:
        mismatches.append((k, "missing in five"))
        continue
    for key in keys:
        a = r[key]
        b = rr[key]
        if isinstance(a, float) or isinstance(b, float):
            if not (math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=0.0) or (math.isnan(float(a)) and math.isnan(float(b)))):
                mismatches.append((k, key, a, b, float(b) - float(a)))
        elif a != b:
            mismatches.append((k, key, a, b))
report("default-vs-five mismatches", len(mismatches))
for m in mismatches[:10]:
    report(" mismatch", m)

# Select edge cases.
edge_cases = [
    ("nan ignored", [np.nan, 2.0, 1.0], [0, 2, 1]),
    ("-inf ignored", [-np.inf, -2.0, -3.0], [0, 1, 2]),
    ("all nan", [np.nan, np.nan], [1, 0]),
    ("all -inf", [-np.inf, -np.inf], [1, 0]),
    ("positive inf", [1.0, np.inf], [0, 1]),
]
for name, vals, order in edge_cases:
    try:
        idx, nt = select(vals, order)
        report(f"select {name}", (idx, nt, vals[idx]))
    except Exception as e:
        report(f"select {name} raised", repr(e))

for vals, achieved in [
    ([1.0, 1.0 + 1e-15], 1.0),
    ([1.0, 1.0 + 1e-15], 1.0 - 1e-12),
    ([np.nan, np.nan], np.nan),
]:
    report(f"normalised_regret {vals} achieved={achieved}", normalised_regret(vals, achieved))

# Synthetic proof of the t26 flow-coverage indexing direction.
from h_stream import build_episodes

e_te = np.ones(6)
y_te = np.ones(6, dtype=int)
ts_w = np.array([20, 30, 31, 10, 11, 12], dtype=np.int64) * 1_000_000
src = np.array([1, 2, 2, 3, 3, 3])
ep = build_episodes(e_te, y_te, ts_w, keys=[src], bucket_s=None)
mal_rank = np.bincount(ep["gid"], weights=y_te.astype(float), minlength=ep["T"])[ep["order"]]
gid_rank = np.bincount(ep["gid"], weights=y_te.astype(float), minlength=ep["T"])
wrong_rank = np.empty_like(gid_rank)
wrong_rank[ep["order"]] = gid_rank
manual = []
for g in ep["order"]:
    manual.append(float(y_te[ep["gid"] == g].sum()))
report("flow coverage rank-order expected", manual)
report("flow coverage rank-order code", mal_rank.tolist())
report("flow coverage reversed-permutation", wrong_rank.tolist())

# Missing-data selection bias example.
cfgs = ["complete", "one-good-window", "low"]
order = np.array([0, 1, 2])
value = np.array([
    [0.7, np.nan, 0.1],
    [0.7, 1.0, 0.1],
    [0.7, 0.0, 0.1],
])
r = transfer_table(cfgs, order, value, [0, 1], 2, 0)
report("nanmean mixed-support winner", (r["winner"], r["value_on_selection"], r["value_on_eval"]))

for axis in ("grouping", "cap"):
    for seed in ("0", "1"):
        for mode in ("E6a", "E6b"):
            rows = t39[axis][seed][mode]
            report(f"t39 {axis} seed {seed} {mode} max rho/regret",
                   (max((r["rho"] for r in rows if r["rho"] is not None), default=None),
                    max(r["regret"] for r in rows)))
