import ast
import math
from pathlib import Path

import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import h_stream as hs


ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "t38_E4_contamination.py").read_text()


def load_module_level(*names):
    tree = ast.parse(SRC)
    want = {n.name: n for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name in names}
    ns = {"np": np, "math": math, "hs": hs, "K": 1, "W0": 0.025, "A": 0.05}
    exec(compile(ast.fix_missing_locations(
        ast.Module(body=[want[n] for n in names], type_ignores=[])), str(ROOT / "t38_E4_contamination.py"), "exec"), ns)
    return [ns[n] for n in names]


contaminate, fire_mask, margin, fdp_recall, wilson, episode_evidence = load_module_level(
    "contaminate", "fire_mask", "margin", "fdp_recall", "wilson", "episode_evidence")

rng = np.random.default_rng(31337)
c0 = np.sort(rng.normal(size=200))
pool = rng.normal(loc=2.0, size=50)
ism = np.array([True, False, True, False])
n = 4000
ts_w = np.sort(rng.integers(0, 5_000_000_000, n))
src_w = rng.integers(0, 40, n)
dst_w = rng.integers(0, 20, n)
y_w = (rng.random(n) < 0.05).astype(np.int64)
for trial in range(5):
    e_te = np.where(rng.random(n) < 0.02, 1e6, 0.0)
    full = hs.build_episodes(e_te, y_w, ts_w, src_w, dst_w, 7200, "src-dst")
    part = hs.build_episodes(np.zeros(n), y_w, ts_w, src_w, dst_w, 7200, "src-dst")


def conds(contaminate=contaminate, fire_mask=fire_mask, fdp_recall=fdp_recall,
          wilson=wilson, margin=margin, episode_evidence=episode_evidence):
    return {
        "drop_highest": (not np.isin(c0[-1], contaminate(c0, pool, 10, "replacement")) is False),
        "random_slice": (set(np.round(contaminate(c0, pool, 3, "additive"), 12))
                         <= set(np.round(contaminate(c0, pool, 7, "additive"), 12))),
        "fire_ge": (not fire_mask(np.array([1.0, 2.0, 3.0]), np.array([3.0]), 1)[0]),
        "side_right": np.array_equal(
            fire_mask(np.array([1.0, 2.0, 3.0]), np.array([2.0, 3.0, 4.0]), 1),
            np.array([False, False, True])),
        "fdp_zero": fdp_recall(np.zeros(4, bool), ism, 2)["fdp"] is None,
        "fdp_div_nmal": fdp_recall(np.array([True, True, False, False]), ism, 2)["fdp"] == 0.5,
        "wilson_normal": wilson(40, 40)[0] < 0.99,
        "margin_k_twice": abs(margin(1_000_000, k=1) - margin(1_000_000)) < 1e-15,
        "episode_no_order": np.allclose(episode_evidence(part, e_te), full["Ev"]),
        "episode_div_T": abs(episode_evidence(part, e_te).sum() - full["Ev"].sum()) < 1e-9,
    }


def contaminate_drop_highest(cal_clean, pool, a, model):
    cal_clean = np.sort(np.asarray(cal_clean, dtype=float))
    a = int(a)
    if a <= 0:
        return np.asarray(cal_clean)
    inj = np.asarray(pool[:a])
    if model == "additive":
        return np.concatenate([cal_clean, inj])
    if model == "replacement":
        return np.concatenate([cal_clean[:-a], inj])
    raise ValueError(model)


def fdp_div_nmal(fired, ismal, n_mal):
    r = int(fired.sum())
    tp = int((fired & ismal).sum())
    return dict(rejections=r, tp=tp, fp=r - tp,
                fdp=(float((r - tp) / n_mal) if r else None),
                fdp_conv=float((r - tp) / n_mal) if r else 0.0,
                recall=float(tp / n_mal) if n_mal else 0.0)


def margin_k_twice(NC, k=1, lvl=0.025):
    CEIL = (NC + 1.0) / (k * k)
    return (CEIL - 1.0 / lvl) / CEIL


def episode_no_order(part, e_te):
    sum_e = np.bincount(part["gid"], weights=e_te, minlength=part["T"])
    return sum_e / np.maximum(part["nsz"], 1)


def episode_div_T(part, e_te):
    sum_e = np.bincount(part["gid"], weights=e_te, minlength=part["T"])[part["order"]]
    return sum_e / part["T"]


base = conds()
mutants = {
    "drop_highest": conds(contaminate=contaminate_drop_highest)["drop_highest"],
    "fdp_div_nmal": conds(fdp_recall=fdp_div_nmal)["fdp_div_nmal"],
    "margin_k_twice": conds(margin=margin_k_twice)["margin_k_twice"],
    "episode_no_order": conds(episode_evidence=episode_no_order)["episode_no_order"],
    "episode_div_T": conds(episode_evidence=episode_div_T)["episode_div_T"],
}

print("base", base)
print("mutant condition values (False means caught by the current assertion)")
for k, v in mutants.items():
    print(k, v)
print("order_is_identity", np.array_equal(part["order"], np.arange(part["T"])))
print("T", part["T"], "nsz_minmax", int(part["nsz"].min()), int(part["nsz"].max()))
