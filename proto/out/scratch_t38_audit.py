import math
import sys
from pathlib import Path

import numpy as np
from scipy.stats import hypergeom

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import h_stream as hs
from h6_procs import Ctx, make_gamma, run_lond


def threshold_p(cal, s, k=1):
    e, _, _, _ = hs.evalues(np.asarray(cal, float), np.zeros(len(cal), dtype=np.int64),
                            np.asarray([s], float), k=k)
    return 1.0 if e[0] == 0 else 1.0 / e[0]


def lond_rejects(ev):
    ctx = Ctx(np.asarray([ev], float), np.asarray([False]), CEIL=ev, alpha=0.05, w0=0.025)
    g1, _ = make_gamma("poly", 1)
    fired = np.zeros(1, bool)
    run_lond(ctx, g1, fired=fired)
    return bool(fired[0]), float(1.0 / (0.05 * g1[1]))


def additive_ceil_can_increase_rejections():
    cal = np.arange(39.0)
    low_attack = np.full(6, -100.0)
    s = 100.0
    e0, _, _, ceil0 = hs.evalues(cal, np.zeros(len(cal), dtype=np.int64), [s], k=1)
    e1, _, _, ceil1 = hs.evalues(np.r_[cal, low_attack],
                                 np.zeros(len(cal) + len(low_attack), dtype=np.int64), [s], k=1)
    r0, needed = lond_rejects(e0[0])
    r1, _ = lond_rejects(e1[0])
    return dict(clean_ceil=ceil0, contaminated_ceil=ceil1, clean_reject=r0,
                contaminated_reject=r1, needed=needed,
                clean_p=threshold_p(cal, s),
                contaminated_p=threshold_p(np.r_[cal, low_attack], s))


def replacement_bottom_drop_counterexample():
    cal = np.arange(5.0)
    k = 3
    clean = np.sort(cal)[::-1][k - 1]
    kept = np.sort(cal)[3:]
    return dict(clean_ck=clean, kept_after_dropping_3_lowest=kept.tolist(),
                enough_clean_left=len(kept) >= k)


def actual_with_without_gap():
    out = []
    for P, Q in [(4033, 3647), (639913, 487778)]:
        q = Q / P
        for a in (1, 2, 3, 5, 10):
            wr = 1.0 - (1.0 - q) ** a
            wor = 1.0 - hypergeom.pmf(0, P, Q, a)
            out.append((P, a, wr, wor, wor - wr))
    return out


def binomial_precision():
    n = 40
    return [(x, x / n, math.sqrt((x / n) * (1 - x / n) / n)) for x in (0, 10, 22, 30, 34, 40)]


if __name__ == "__main__":
    print("additive ceiling counterexample:", additive_ceil_can_increase_rejections())
    print("replacement bottom-drop edge:", replacement_bottom_drop_counterexample())
    print("with/without gaps:", actual_with_without_gap())
    print("binomial SE:", binomial_precision())
