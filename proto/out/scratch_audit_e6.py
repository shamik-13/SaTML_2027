import json
import numpy as np

POS = [0.55, 0.62, 0.70, 0.77, 0.85]
SEEDS = [0, 1]
FAMILY_ORDER = ["src-dst", "src", "dst", "subnet24", "src-dport"]
BUCKET_ORDER = [7200, 3600, 1800, 300, 21600, 86400, None]
GRID = [(f, b) for f in FAMILY_ORDER for b in BUCKET_ORDER]
CAP_ORDER = ["p99", "max", "p999", "p90", "p50", "mean"]


def positive_gaps(v):
    x = sorted(set(float(a) for a in v if np.isfinite(a)))
    return [b - a for a, b in zip(x, x[1:]) if b > a]


print("== E6 saved summary flat rows")
d = json.load(open("proto/out/t39_E6.json"))
for label, res in (("grouping", d["grouping"]), ("cap", d["cap"]),
                   ("grouping[ORACLE]", {"0": d["grouping_oracle_control"]})):
    for seed, rr0 in res.items():
        for mode in ("E6a", "E6b"):
            rr = rr0[mode]
            ok = [r for r in rr if r["transfer_defined"]]
            deg = [r for r in rr if not r["transfer_defined"]]
            print(label, seed, mode, len(ok), len(rr),
                  "worst_ok", max((r["regret"] for r in ok), default=None),
                  "deg", [(r.get("select_pos"), r.get("eval_pos"), r["regret"]) for r in deg])

print("\n== objective grid min positive gaps")
grows = json.load(open("proto/out/t26_H4_5pos.json"))["rows"]
for key in ("flow_cov_addis", "flow_cov_elond"):
    gaps = []
    for seed in SEEDS:
        lut = {(r["pos"], r["family"], r["bucket_s"]): r for r in grows if r["seed"] == seed}
        for p in POS:
            vals = []
            for c in GRID:
                r = lut.get((p,) + c)
                if r is not None and r.get(key) is not None and r["feasible"]:
                    vals.append(r[key])
            gaps.extend(positive_gaps(vals))
    print(key, "min_gap", min(gaps), "n_gaps", len(gaps))

crows = json.load(open("proto/out/t25_H5.json"))["rows"]
gaps = []
for seed in SEEDS:
    lut = {(r["pos"], r["cap"]): r for r in crows if r["seed"] == seed}
    for p in POS:
        vals = []
        for cap in CAP_ORDER:
            r = lut.get((p, cap))
            if r is not None:
                vals.append(r["det_trunc"] / r["n_att_ep"])
        gaps.extend(positive_gaps(vals))
print("cap det_trunc/n_att_ep", "min_gap", min(gaps), "n_gaps", len(gaps))

print("\n== is_worst mutation witness")
ev = np.array([1.0, 0.0004, 0.0, 0.5])
achieved = ev[1]
rho = (ev.max() - achieved) / (ev.max() - ev.min())
print("rho", rho, "formatted", format(rho, ".3f"),
      "exact_is_worst", abs(achieved - ev.min()) <= 1e-12,
      "rounded_rho_is_worst", float(format(rho, ".3f")) >= 1.0)

print("\n== self-test feasibility witness")
sel = np.array([0.1, 0.9, 0.5, 0.2])
sel_feas = np.array([True, True, False, True])
print("current line-138 fixture winner without selection mask",
      int(np.nanargmax(sel)), "passes winner != c even without the mask")
sel2 = np.array([0.1, 0.9, 0.95, 0.2])
masked = np.where(sel_feas, sel2, np.nan)
print("stronger fixture unmasked winner", int(np.nanargmax(sel2)),
      "masked winner", int(np.nanargmax(masked)))
