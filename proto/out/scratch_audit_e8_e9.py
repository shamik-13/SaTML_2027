import ast
import math
from pathlib import Path

import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import h_stream as hs
from h6_procs import Ctx, make_gamma, run_lond


ROOT = Path(__file__).resolve().parents[1]


def load_deriv(name):
    src = ROOT / "t41a_E8_derivation.py"
    tree = ast.parse(src.read_text())
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id in {"COL", "SCALES"} for t in node.targets):
                nodes.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name == name:
            nodes.append(node)
    ns = {"np": np, "math": math}
    exec(compile(ast.fix_missing_locations(ast.Module(nodes, [])), str(src), "exec"), ns)
    return ns[name]


def show(k, v):
    print(f"{k}: {v}")


recover_duration_scale = load_deriv("recover_duration_scale")
budget_cost = load_deriv("budget_cost")


print("E8 duration filter/dominance")
d = np.array([0, 0.5, 1, 2, 10, 100], dtype=float)
b = np.array([10, 10, 10, 10, 0.5, 100], dtype=float)
r = np.ones_like(d)
mask_default = (d > 1.0) & (b > 1.0) & (r > 0) & np.isfinite(d) & np.isfinite(b) & np.isfinite(r)
mask_doc_positive = (d > 0) & (b > 0) & (r > 0) & np.isfinite(d) & np.isfinite(b) & np.isfinite(r)
show("default_survivors_indices", np.flatnonzero(mask_default).tolist())
show("positive_survivors_indices", np.flatnonzero(mask_doc_positive).tolist())
show("default_survivor_fraction", float(mask_default.mean()))
try:
    show("scale_default", recover_duration_scale(d, b, r))
except Exception as exc:
    show("scale_default_exc", type(exc).__name__ + ":" + str(exc))
show("scale_min0", recover_duration_scale(d, b, r, min_dur=0.0, min_bytes=0.0))


print("\nE8 budget estimator")
pk = np.array([1, 1, 1, 1, 1], dtype=float)
by = np.array([10, 10, 10, 10, 1000000], dtype=float)
bc = budget_cost(pk, by, 100, quantiles=(0.0, 0.5, 0.9))
show("quantile_costs", {str(k): v["bytes"] for k, v in bc.items() if k != "mean"})
show("mean_cost", bc["mean"]["bytes"])
show("exact_cheapest_with_replacement", 100 * by.min())
show("exact_without_replacement_then_reuse_ambiguous", "not identified by n*quantile")


print("\nE9 tie_key group indexing")
e_te = np.array([10, 100, 20, 200, 30, 300], dtype=float)
y_te = np.zeros(6, dtype=int)
ts_w = np.array([1000, 1000, 1000, 1000, 2000, 2000], dtype=np.int64)
src_w = np.array([2, 1, 2, 1, 3, 4], dtype=np.int64)
dst_w = np.array([9, 9, 9, 9, 9, 9], dtype=np.int64)
ep = hs.build_episodes(e_te, y_te, ts_w, src_w, dst_w, bucket_s=None, family="src-dst")
show("det_order_group_ids", ep["order"].tolist())
show("det_Ev", ep["Ev"].tolist())
first_ts = np.full(ep["T"], np.iinfo(np.int64).max)
np.minimum.at(first_ts, ep["gid"], ts_w)
show("first_ts_by_gid", first_ts.tolist())

tk_by_gid = np.arange(ep["T"], dtype=float)
tk_by_gid[ep["order"]] = np.arange(ep["T"] - 1, -1, -1)
ep_gid = hs.build_episodes(e_te, y_te, ts_w, src_w, dst_w, bucket_s=None, family="src-dst", tie_key=tk_by_gid)
show("group_indexed_reverse_order", ep_gid["order"].tolist())
show("group_indexed_reverse_Ev", ep_gid["Ev"].tolist())

tk_wrong_by_rank = np.arange(ep["T"] - 1, -1, -1)
ep_wrong = hs.build_episodes(e_te, y_te, ts_w, src_w, dst_w, bucket_s=None, family="src-dst", tie_key=tk_wrong_by_rank)
show("rank_indexed_key_order", ep_wrong["order"].tolist())
show("rank_indexed_key_Ev", ep_wrong["Ev"].tolist())
show("wrong_matches_intended", bool(np.array_equal(ep_wrong["order"], ep_gid["order"])))
show("timestamp_sequence_unchanged", bool(np.array_equal(first_ts[ep["order"]], first_ts[ep_wrong["order"]])))


print("\nE9 moved-count semantics")
det_order = np.array([10, 11, 12, 20, 21, 30])
rep_order = np.array([11, 10, 12, 21, 20, 30])
show("elementwise_positions_changed", int((rep_order != det_order).sum()))
show("same_episode_set", bool(set(rep_order.tolist()) == set(det_order.tolist())))
show("episode_12_position_unchanged", int(np.where(rep_order == 12)[0][0]) == int(np.where(det_order == 12)[0][0]))


print("\nE9 pipeline consumes permuted Ev")
Ev_a = np.array([1e6, 0.0, 1e6, 0.0, 0.0])
Ev_b = np.array([0.0, 1e6, 1e6, 0.0, 0.0])
ismal = np.zeros(5, dtype=bool)
g1, _ = make_gamma("poly", len(Ev_a))
fa = np.zeros(len(Ev_a), dtype=bool)
fb = np.zeros(len(Ev_b), dtype=bool)
run_lond(Ctx(Ev_a, ismal, 1e6, alpha=0.05, w0=0.025), g1, fired=fa)
run_lond(Ctx(Ev_b, ismal, 1e6, alpha=0.05, w0=0.025), g1, fired=fb)
show("lond_fired_a", fa.tolist())
show("lond_fired_b", fb.tolist())
show("lond_uses_order", bool(not np.array_equal(fa, fb)))


print("\nE9 varies/None bug")
vals = [None, None, 3, 3]
dv = None
fin = np.asarray([v for v in vals if v is not None], dtype=float)
n_distinct_script = len({(None if v is None else float(v)) for v in vals})
varies_script = bool(n_distinct_script > 1 or (fin.size and dv is not None and float(dv) not in {float(x) for x in fin}))
show("script_n_distinct", n_distinct_script)
show("script_varies", varies_script)
vals2 = [None, None, None]
dv2 = 3
fin2 = np.asarray([v for v in vals2 if v is not None], dtype=float)
n_distinct_script2 = len({(None if v is None else float(v)) for v in vals2})
varies_script2 = bool(n_distinct_script2 > 1 or (fin2.size and dv2 is not None and float(dv2) not in {float(x) for x in fin2}))
show("det_number_random_all_none_varies", varies_script2)
