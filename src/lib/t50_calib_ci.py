"""R3 -- exact binomial (Clopper-Pearson) confidence intervals on the benign-firing ratio.

The calibration-validity diagnostic (t30_A1) reports, per window, the measured/nominal benign
firing ratio.  At the guarantee windows the OBSERVED firing count is tiny (1-3 events with an
expectation near 1), so a ratio near 1 is not statistical proof that exchangeability holds.  This
stage attaches an exact interval to each ratio so the paper can separate the theoretical guarantee
(holds under the assumption) from the empirical diagnostic (limited resolution): the
guarantee-window intervals are wide and include 1, so they only fail to REJECT validity; the 0.85
interval excludes 1 by orders of magnitude, a clear violation.

The underlying experiment is a BINOMIAL count -- x benign flows fire out of n_benign, each firing
with the nominal per-flow probability p0 = k/(|C|+1) under exchangeability -- so the exact interval
is the Clopper-Pearson binomial interval on p0, not a Poisson interval.  Because p0 is tiny and
n_benign is large the Poisson approximation is numerically almost identical, but the binomial
interval is exact under the model that actually generated the count.

Reads out/t30_A1.json (no detector rerun); writes out/t50_calib_ci.json.
"""
import json, time
from pathlib import Path
from scipy.stats import beta

CONF = 0.95


def clopper_pearson(x, n, conf=CONF):
    """Exact Clopper-Pearson binomial interval (lo, hi) on the success probability p, given x
    successes in n trials.  Uses the Beta-quantile form; lo=0 when x=0, hi=1 when x=n."""
    a = 1.0 - conf
    lo = 0.0 if x == 0 else beta.ppf(a / 2, x, n - x + 1)
    hi = 1.0 if x == n else beta.ppf(1 - a / 2, x + 1, n - x)
    return float(lo), float(hi)


def cp_ratio_ci(x, n, p0, conf=CONF):
    """Clopper-Pearson interval mapped onto the ratio p/p0, where x/n estimates p and p0 is the
    nominal per-flow firing probability.  Returns (lo, hi) on the RATIO."""
    lo, hi = clopper_pearson(x, n, conf)
    return lo / p0, hi / p0


def main():
    t0 = time.time()
    Path("out").mkdir(exist_ok=True)
    d = json.load(open("out/t30_A1.json"))
    rows = []
    for r in d["firing_rates"]:
        x = int(r["n_fired_benign"])
        n = int(r["n_benign"])
        ratio = float(r["ratio"])
        p0 = float(r["nominal"])
        lo, hi = cp_ratio_ci(x, n, p0)
        # expected count under the nominal rate, reported for continuity with the earlier diagnostic
        lam0 = n * p0
        rows.append(dict(
            pos=float(r["pos"]), seed=int(r["seed"]),
            n_fired_benign=x, n_benign=n, expected_count=lam0, ratio=ratio,
            ci_lo=float(lo), ci_hi=float(hi), conf=CONF,
            excludes_one=bool(lo > 1.0 or hi < 1.0)))
        print(f"  pos={r['pos']} seed={r['seed']}  x={x:>3d}/{n:,}  E[x]={lam0:.3f}  "
              f"ratio={ratio:.2f}  {int(CONF*100)}% CI=[{lo:.2f}, {hi:.2f}]  "
              f"{'VIOLATION' if (lo>1 or hi<1) else 'compatible with 1'}")
    out = dict(
        config=dict(conf=CONF, method="exact binomial (Clopper-Pearson) on the ratio p/p0",
                    source="t30_A1.json firing_rates"),
        rows=rows,
        note=("Exact Clopper-Pearson binomial intervals on the benign-firing ratio. At the "
              "guarantee windows x is 1-3 so the interval is wide and includes 1 (the diagnostic "
              "cannot prove validity, only fail to reject it); at 0.85 the interval excludes 1 by "
              "orders of magnitude. The count is binomial (x fires out of n_benign), so this is the "
              "exact interval; the Poisson approximation is numerically almost identical here "
              "because p0 is tiny and n_benign large."))
    json.dump(out, open("out/t50_calib_ci.json", "w"), indent=1, allow_nan=False)
    print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t50_calib_ci.json")
    return out


if __name__ == "__main__":
    main()
