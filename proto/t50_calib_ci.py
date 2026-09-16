"""R3 -- exact Poisson confidence intervals on the benign-firing ratio.

The calibration-validity diagnostic (t30_A1) reports, per window, the measured/nominal benign
firing ratio.  At the guarantee windows the OBSERVED firing count is tiny (1-3 events with an
expectation near 1), so a ratio near 1 is not statistical proof that exchangeability holds.  This
stage attaches an exact Poisson interval to each ratio so the paper can separate the theoretical
guarantee (holds under the assumption) from the empirical diagnostic (limited resolution): the
guarantee-window intervals are wide and include 1, so they only fail to REJECT validity; the 0.85
interval excludes 1 by orders of magnitude, a clear violation.

Reads out/t30_A1.json (no detector rerun); writes out/t50_calib_ci.json.
"""
import json, time
from pathlib import Path
from scipy.stats import chi2

CONF = 0.95


def poisson_ratio_ci(k, lam0, conf=CONF):
    """Exact (Garwood) Poisson interval on the rate ratio k/lam0, where k is the observed firing
    count and lam0 the expected count under the nominal rate.  Returns (lo, hi) on the RATIO."""
    a = 1.0 - conf
    mu_lo = 0.0 if k == 0 else 0.5 * chi2.ppf(a / 2, 2 * k)
    mu_hi = 0.5 * chi2.ppf(1 - a / 2, 2 * k + 2)
    return mu_lo / lam0, mu_hi / lam0


def main():
    t0 = time.time()
    Path("out").mkdir(exist_ok=True)
    d = json.load(open("out/t30_A1.json"))
    rows = []
    for r in d["firing_rates"]:
        k = int(r["n_fired_benign"])
        ratio = float(r["ratio"])
        lam0 = k / ratio if ratio > 0 else float(r["nominal"]) * int(r["n_benign"])
        lo, hi = poisson_ratio_ci(k, lam0)
        rows.append(dict(
            pos=float(r["pos"]), seed=int(r["seed"]),
            n_fired_benign=k, expected_count=lam0, ratio=ratio,
            ci_lo=float(lo), ci_hi=float(hi), conf=CONF,
            excludes_one=bool(lo > 1.0 or hi < 1.0)))
        print(f"  pos={r['pos']} seed={r['seed']}  k={k:>3d}  E[k]={lam0:.3f}  "
              f"ratio={ratio:.2f}  {int(CONF*100)}% CI=[{lo:.2f}, {hi:.2f}]  "
              f"{'VIOLATION' if (lo>1 or hi<1) else 'compatible with 1'}")
    out = dict(
        config=dict(conf=CONF, method="exact Poisson (Garwood) on ratio k/E[k]",
                    source="t30_A1.json firing_rates"),
        rows=rows,
        note=("Exact Poisson intervals on the benign-firing ratio. At the guarantee windows k is 1-3 "
              "so the interval is wide and includes 1 (the diagnostic cannot prove validity, only "
              "fail to reject it); at 0.85 the interval excludes 1 by orders of magnitude."))
    json.dump(out, open("out/t50_calib_ci.json", "w"), indent=1, allow_nan=False)
    print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t50_calib_ci.json")
    return out


if __name__ == "__main__":
    main()
