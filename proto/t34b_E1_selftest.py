"""
Unit tests for the E1 machinery (t34_E1_smoothed.py, t34a_E1_derivation.py).  No data files:
everything is synthetic and runs in a couple of seconds, so it can be re-run after any edit.

Module-level functions are pulled OUT of t34_E1_smoothed.py by AST and executed here, so the
tests exercise the real code rather than a copy of it.  The two helpers that are nested
inside the per-configuration loop (`simes_hommel` and `dev_check`) cannot be imported that
way because they close over loop variables, so their algebra is checked against brute force
AND the exact source expressions are asserted to still be present -- a later edit to one
without the other fails here rather than silently in the record.

What it pins down:
  1  the group-id order <-> episode order round trip.  An array in group-id order indexed as
     if it were in episode order pairs each episode's evidence with a DIFFERENT episode's
     malicious label; it is the highest-impact silent bug available in this script
  2  np.minimum.reduceat groupby-min against a brute-force per-group loop
  3  the Simes within-episode rank algebra (lexsort blocks, rank_k, m/k) against brute force
  4  Hommel's H_m against the exact harmonic number
  5  discrete Simes against the record's mean-e + Markov rule m/(M*r)
  6  run_lond_p against h6_procs.run_lond away from float boundaries, and AT one
  7  dev_check's ability to reject deliberately wrong closed forms
  8  the smoothed conformal p-value's exact conditional rejection probability [D2a]
  9  the Route-B calibrator inversion [D3d]
"""
import numpy as np, ast, sys, re
from pathlib import Path
from scipy.special import digamma

import h_stream as hs
from h6_procs import Ctx, make_gamma, run_lond, run_online_ebh

SRC_PATH = Path(__file__).with_name("t34_E1_smoothed.py")
SRC = SRC_PATH.read_text()
fails = []


def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"   {detail}" if detail else ""))
    if not cond:
        fails.append(name)


def load_module_level(*names):
    """Execute named module-level functions out of t34_E1_smoothed.py without running it."""
    tree = ast.parse(SRC)
    want = {n.name: n for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name in names}
    missing = set(names) - set(want)
    if missing:
        raise AssertionError(f"not module-level in {SRC_PATH.name}: {sorted(missing)}")
    from scipy.stats import norm
    from itertools import combinations
    from scipy.special import digamma as _digamma
    ns = {"np": np, "norm": norm, "combinations": combinations, "digamma": _digamma,
          "online_ebh_kstar": __import__("h6_procs").online_ebh_kstar}
    mod = ast.Module(body=[want[n] for n in names], type_ignores=[])
    exec(compile(ast.fix_missing_locations(mod), str(SRC_PATH), "exec"), ns)
    return [ns[n] for n in names]


(run_lond_p, ebh_mask, metrics, jaccard, simes_index, simes_hommel_merge,
 dev_check, ebh_entry_ts, conformal_ranks, smoothed_p, calibrate,
 episode_pvalues) = load_module_level(
    "run_lond_p", "ebh_mask", "metrics", "jaccard", "simes_index",
    "simes_hommel_merge", "dev_check", "ebh_entry_ts", "conformal_ranks",
    "smoothed_p", "calibrate", "episode_pvalues")

# ======================================================================================
print("=" * 100)
print("1. group-id order <-> episode order round trip")
print("=" * 100)
rng = np.random.default_rng(0)
n, T = 400, 37
gid = rng.integers(0, T, n)
gid = np.unique(gid, return_inverse=True)[1]          # dense, as build_episodes guarantees
T = int(gid.max() + 1)
ts_w = rng.integers(0, 10_000, n).astype(np.int64)
y_te = (rng.random(n) < 0.2).astype(np.int8)
e_te = np.where(rng.random(n) < 0.1, 100.0, 0.0)
src_w = gid.astype(np.int32); dst_w = np.zeros(n, np.int32)
ep = hs.build_episodes(e_te, y_te, ts_w, src_w, dst_w, bucket_s=None,
                       keys=[gid])
order, T2 = ep["order"], ep["T"]
check("build_episodes reproduces the supplied partition", T2 == T, f"T={T} T2={T2}")
nsz_raw = np.bincount(ep["gid"], minlength=T2).astype(float)
check("nsz_raw[order] equals build_episodes' nsz (group-id -> episode order)",
      np.array_equal(nsz_raw[order], ep["nsz"].astype(float)))
mal_raw = np.bincount(ep["gid"], weights=y_te.astype(float), minlength=T2) > 0
check("ismal is the malicious flag in EPISODE order",
      np.array_equal(mal_raw[order], ep["ismal"]))
sum_e_raw = np.bincount(ep["gid"], weights=e_te, minlength=T2)
check("Ev = (sum_e/nsz)[order] reproduces build_episodes' Ev",
      np.allclose((sum_e_raw / np.maximum(nsz_raw, 1))[order], ep["Ev"]))
# the failure mode this pins down: `order` is not an involution, so applying it twice (or
# forgetting it) silently pairs each episode's evidence with a different episode's label
check("`order` is not an involution: applying it twice differs from applying it once",
      not np.array_equal(nsz_raw[order][order], nsz_raw[order]))
check("forgetting `order` entirely differs from applying it",
      not np.array_equal(nsz_raw, nsz_raw[order]))
check("ismal[order-less] would mis-pair labels for at least one episode",
      not np.array_equal(mal_raw, ep["ismal"]))

# ======================================================================================
print("\n" + "=" * 100)
print("2. reduceat groupby-min against brute force")
print("=" * 100)
g = ep["gid"]
srt = np.argsort(g, kind='stable')
starts = np.concatenate(([0], np.flatnonzero(np.diff(g[srt])) + 1))
check("starts has one entry per episode", len(starts) == T2, f"{len(starts)} vs {T2}")
pv = rng.random(n)
got = np.minimum.reduceat(pv[srt], starts)
want = np.array([pv[g == t].min() for t in range(T2)])
check("reduceat min == per-group brute-force min", np.allclose(got, want))
check("the LAST group is reduced correctly (reduceat's tail case)",
      np.isclose(got[-1], pv[g == T2 - 1].min()))
sing = np.flatnonzero(nsz_raw == 1)
check("groups of size 1 are handled",
      sing.size == 0 or np.allclose(got[sing], [pv[g == t][0] for t in sing]),
      f"{sing.size} singleton groups")

# ======================================================================================
print("\n" + "=" * 100)
print("3. Simes within-episode rank algebra against brute force")
print("=" * 100)
# These call the SHIPPED simes_index / simes_hommel_merge.  An earlier version of this
# test checked copied algebra plus "does the source still contain this string", and a
# mutation audit defeated it by moving the searched text into a comment.
srt2, starts2, flow_m, rank_k, m_over_k, H_m = simes_index(g, nsz_raw, n)
check("simes_index reproduces the group starts", np.array_equal(starts2, starts))
check("rank_k starts at 1 in every episode",
      np.array_equal(rank_k[starts2], np.ones(T2, dtype=np.int64)))
check("rank_k ends at m in every episode",
      np.array_equal(rank_k[np.append(starts2[1:], n) - 1], nsz_raw.astype(np.int64)))
check("lexsort blocks coincide positionally with argsort(gid) blocks",
      np.array_equal(g[np.lexsort((pv, g))], g[srt2]))
sim, hom = simes_hommel_merge(pv, g, starts2, m_over_k, H_m)
brute = np.array([np.min(np.sort(pv[g == t]) * (nsz_raw[t] / np.arange(1, int(nsz_raw[t]) + 1)))
                  for t in range(T2)])
check("simes_hommel_merge Simes == brute-force min_k (m/k) p_(k), every episode",
      np.allclose(sim, np.minimum(1.0, brute)),
      f"max dev {np.max(np.abs(sim - np.minimum(1.0, brute))):.3e}")
brute_h = np.minimum(1.0, np.array([digamma(nsz_raw[t] + 1.0) + np.euler_gamma
                                    for t in range(T2)]) * brute)
check("simes_hommel_merge Hommel == H_m * Simes, every episode (NOT raw Simes)",
      np.allclose(hom, brute_h), f"max dev {np.max(np.abs(hom - brute_h)):.3e}")
check("Hommel is strictly larger than Simes wherever m > 1 and Simes < 1",
      bool(np.all(hom[(nsz_raw > 1) & (sim < 1.0)] > sim[(nsz_raw > 1) & (sim < 1.0)])),
      f"{int(((nsz_raw > 1) & (sim < 1.0)).sum())} such episodes")

# ======================================================================================
print("\n" + "=" * 100)
print("3b. episode_pvalues: all four merges, in EPISODE order, against brute force")
print("=" * 100)
# This is the function the round-4 mutation audit reached by editing the driver inline:
# dropping an [order], dropping Bonferroni's m, dropping mean-p's 2, or dividing by
# nsz_raw[order].  All four now live here and are checked against a brute-force reference
# computed independently, per episode, in episode order.
EPv = episode_pvalues(pv, g, order, nsz_raw, starts2, srt2, m_over_k, H_m, T2)
bf_simes, bf_bonf, bf_meanp, bf_hom = [], [], [], []
for t in range(T2):
    q = np.sort(pv[g == t]); mm = len(q)
    bf_simes.append(min(1.0, float(np.min((mm / np.arange(1, mm + 1)) * q))))
    bf_bonf.append(min(1.0, mm * float(q.min())))
    bf_meanp.append(min(1.0, 2.0 * float(q.mean())))
    bf_hom.append(min(1.0, (digamma(mm + 1.0) + np.euler_gamma)
                      * float(np.min((mm / np.arange(1, mm + 1)) * q))))
inv = np.argsort(order)          # episode-order position of each group id
for nm, bf in (("simes", bf_simes), ("bonf", bf_bonf),
               ("meanp", bf_meanp), ("hommel", bf_hom)):
    got_ep = EPv[nm]
    want_ep = np.asarray(bf)[order]
    check(f"episode_pvalues['{nm}'] == brute force, in EPISODE order",
          np.allclose(got_ep, want_ep), f"max dev {np.max(np.abs(got_ep-want_ep)):.3e}")
    check(f"episode_pvalues['{nm}'] is NOT in group-id order (the [order] is applied)",
          T2 < 2 or not np.allclose(got_ep, np.asarray(bf)))
check("Bonferroni carries the factor m (dropping it would equal min(p))",
      not np.allclose(EPv["bonf"], np.array([pv[g == t].min() for t in range(T2)])[order]))
check("mean-p carries the factor 2 (dropping it would halve every value)",
      not np.allclose(EPv["meanp"],
                      np.array([pv[g == t].mean() for t in range(T2)])[order]))
check("dividing by nsz_raw[order] instead of nsz_raw would change mean-p",
      T2 < 2 or not np.allclose(
          np.minimum(1.0, 2.0 * np.bincount(g, weights=pv, minlength=T2) / nsz_raw[order])[order],
          EPv["meanp"]))

# ======================================================================================
print("\n" + "=" * 100)
print("3c. conformal_ranks / smoothed_p / calibrate")
print("=" * 100)
cal_t = np.array([-3.0, -1.0, -1.0, 0.0, 2.0, 2.0, 2.0])
sc_t = np.array([-4.0, -3.0, -1.0, 1.0, 2.0, 3.0])
Gt, Et, lot = conformal_ranks(cal_t, sc_t, len(cal_t))
check("conformal_ranks G == #{c > s} exactly",
      np.array_equal(Gt, np.array([(cal_t > x).sum() for x in sc_t], float)),
      f"{Gt.tolist()}")
check("conformal_ranks Etie == #{c == s} exactly",
      np.array_equal(Et, np.array([(cal_t == x).sum() for x in sc_t], float)),
      f"{Et.tolist()}")
check("swapping the searchsorted sides would change G (so the sides matter)",
      not np.array_equal(Gt, (len(cal_t) - np.searchsorted(cal_t, sc_t, side='left'))
                         .astype(float)))
check("1+G+E reproduces h_stream.evalues' rank K",
      np.array_equal(1 + Gt + Et, 1 + (len(cal_t) - lot)))
Ut = np.array([0.0, 0.5, 1.0])
check("smoothed_p uses (1+E), not E",
      np.allclose(smoothed_p(np.array([2.0]), np.array([3.0]), np.array([0.5]), 100.0),
                  (2.0 + 0.5 * 4.0) / 100.0),
      "a (G + U*E)/M form would give a different value")
check("smoothed_p spans exactly (G/M, (G+1+E)/M]",
      np.allclose(smoothed_p(np.full(3, 2.0), np.full(3, 3.0), Ut, 100.0),
                  np.array([2.0, 4.0, 6.0]) / 100.0))
for lam in (0.1, 0.5, 0.75):
    pt = np.array([1e-6, 1e-3, 0.5])
    check(f"calibrate is DECREASING in p [lam={lam}] (a 1-lam exponent would increase)",
          bool(np.all(np.diff(calibrate(pt, lam)) < 0)),
          f"{calibrate(pt, lam).round(3).tolist()}")

# ======================================================================================
print("\n" + "=" * 100)
print("4. Hommel's H_m against the exact harmonic number")
print("=" * 100)
for m in (1, 2, 5, 50, 1000, 100_000):
    exact = float(np.sum(1.0 / np.arange(1, m + 1)))
    got_h = float(digamma(m + 1.0) + np.euler_gamma)
    check(f"H_m at m={m}", abs(exact - got_h) < 1e-9 * max(1.0, exact),
          f"exact={exact:.10f} digamma={got_h:.10f}")
check("H_m is increasing in m, so m*H_m is minimised at the SMALLEST episode",
      bool(np.all(np.diff([digamma(m + 1.0) + np.euler_gamma
                           for m in (1, 2, 3, 10, 100)]) > 0)))

# ======================================================================================
print("\n" + "=" * 100)
print("5. discrete Simes against the record's mean-e + Markov rule")
print("=" * 100)
M = 1_813_114.0
for m, r in ((10, 1), (10, 3), (100, 1), (100, 7), (5, 5), (3, 2)):
    p = np.full(m, 1.0); p[:r] = 1.0 / M
    p = np.sort(p)
    k = np.arange(1, m + 1)
    simes = min(1.0, float(np.min((m / k) * p)))
    mean_e_markov = min(1.0, m / (M * r))
    check(f"Simes == mean-e+Markov at m={m}, r={r}",
          abs(simes - mean_e_markov) <= 1e-15 * mean_e_markov,
          f"{simes:.6e} vs {mean_e_markov:.6e}")
# and the case where Simes is STRICTLY smaller: many flows just below the floor
p = np.full(40, 1.0); p[0] = 1.0 / M; p[1:20] = 2.0 / M
p = np.sort(p); k = np.arange(1, 41)
simes = float(np.min((40 / k) * p)); mem = 40 / (M * 1)
check("Simes can be STRICTLY smaller than mean-e+Markov (it may pick k > r)",
      simes < mem, f"Simes={simes:.6e} < mean-e={mem:.6e}; ratio {simes/mem:.3f}")
check("the script asserts the INEQUALITY Simes <= mean-e, not equality",
      "np.all(sim_ep <= P_rec_chk * (1.0 + 1e-12))" in SRC)
check("the strict-gap comparison is relative-only (np.isclose's default atol=1e-8 would "
      "swamp p-values of order 1e-6 and hide every gap)",
      "P_rec_chk[fired_rec] * (1.0 - 1e-12)" in SRC)
check("no np.isclose/np.allclose with a default atol is used on episode p-values",
      not re.search(r"np\.(is|all)close\([^)]*P_rec", SRC))

# ======================================================================================
print("\n" + "=" * 100)
print("6. run_lond_p against h6_procs.run_lond")
print("=" * 100)
Tp = 2000
rngp = np.random.default_rng(7)
P = rngp.random(Tp) ** 6                       # well away from any float boundary
ismal = rngp.random(Tp) < 0.05
ctx = Ctx(1.0 / np.maximum(P, np.finfo(float).tiny), ismal, np.inf, alpha=0.05, w0=0.025)
g1, _ = make_gamma("poly", Tp)
fa = np.zeros(Tp, bool); ra = run_lond_p(ctx, g1, np.minimum(1.0, P), fired=fa)
fb = np.zeros(Tp, bool); rb = run_lond(ctx, g1, fired=fb)
check("p-form and e-form agree away from boundaries",
      ra == rb and np.array_equal(fa, fb), f"{ra} vs {rb}")
# now engineer the boundary the audit found and show the p-form is the correct one
lvl1 = 0.05 * g1[1] * 1
Pb = np.full(Tp, 0.9); Pb[0] = np.nextafter(lvl1, np.inf)
ctxb = Ctx(1.0 / Pb, np.zeros(Tp, bool), np.inf, alpha=0.05, w0=0.025)
f1 = np.zeros(Tp, bool); run_lond_p(ctxb, g1, np.minimum(1.0, Pb), fired=f1)
f2 = np.zeros(Tp, bool); run_lond(ctxb, g1, fired=f2)
check("p-form does NOT reject when P is one ulp ABOVE the level (correct)", not f1[0],
      f"P={Pb[0]!r} lvl={lvl1!r}")
# search for a level at which the two forms genuinely disagree, rather than asserting a
# tautology.  If none exists in float64 the hazard is nil and this records that fact.
found = None
for t_idx in range(1, 4000):
    lv = 0.05 * g1[t_idx] * 1
    if lv <= 0: continue
    Pn = np.nextafter(lv, np.inf)             # strictly ABOVE the level: must NOT reject
    if (1.0 / Pn) >= (1.0 / lv):              # but the reciprocal form says it does
        found = (t_idx, lv, Pn); break
check("a level exists where the e-form rejects a p-value strictly ABOVE it",
      found is not None,
      f"t={found[0]}, lvl={found[1]!r}, P={found[2]!r}" if found
      else "none found in the first 4000 levels")
if found:
    t_b, lv, Pn = found
    check("p-form is the correct one there (P > lvl, so no rejection)", not (Pn <= lv))
    check("e-form would wrongly reject there", (1.0 / Pn) >= (1.0 / lv))
    # feed it back through the SHIPPED run_lond_p: an earlier version of this test found
    # the boundary but never exercised the function on it, so reverting run_lond_p to the
    # reciprocal comparison still passed
    Pb2 = np.full(Tp, 0.9); Pb2[t_b - 1] = Pn
    fb2 = np.zeros(Tp, bool)
    run_lond_p(Ctx(1.0 / Pb2, np.zeros(Tp, bool), np.inf, alpha=0.05, w0=0.025),
               g1, np.minimum(1.0, Pb2), fired=fb2)
    check("run_lond_p does NOT reject at the found boundary (it compares p, not 1/p)",
          not fb2[t_b - 1], f"step {t_b}")
    fe2 = np.zeros(Tp, bool)
    run_lond(Ctx(1.0 / Pb2, np.zeros(Tp, bool), np.inf, alpha=0.05, w0=0.025), g1, fired=fe2)
    check("the reciprocal e-form DOES reject there, so this test has teeth",
          fe2[t_b - 1], f"step {t_b}")

# ======================================================================================
print("\n" + "=" * 100)
print("7. dev_check rejects deliberately wrong closed forms")
print("=" * 100)
# dev_check below is the SHIPPED module-level function, not a copy.

NN = 100
truth = np.concatenate([np.full(300, 0.5), np.full(300, 0.0), np.full(300, 1.0)])
rngd = np.random.default_rng(3)
obs_true = rngd.binomial(NN, truth)
check("the CORRECT closed form passes", dev_check(truth, obs_true, NN)["ok"])
bad_hi = np.minimum(1.0, truth * 1.2)
check("a closed form 20% too high FAILS", not dev_check(bad_hi, obs_true, NN)["ok"],
      f"pooled_z={dev_check(bad_hi, obs_true, NN)['pooled_z']:+.1f}")
bad_zero = truth.copy(); bad_zero[:300] = 0.0
check("predicting 0 where the true rate is 0.5 FAILS (the deterministic-cell trap)",
      not dev_check(bad_zero, obs_true, NN)["ok"],
      f"det_bad={dev_check(bad_zero, obs_true, NN)['n_deterministic_bad']}")
bad_one = truth.copy(); bad_one[:300] = 1.0
check("predicting 1 where the true rate is 0.5 FAILS",
      not dev_check(bad_one, obs_true, NN)["ok"],
      f"det_bad={dev_check(bad_one, obs_true, NN)['n_deterministic_bad']}")
# The low-power hole the second audit found: cells with 0<pred<1 but n*p*(1-p)<5 enter
# neither max_z nor det_bad.  Two distinct failure modes, and both must be caught.
#  (a) one cell decisively wrong on its own
r_a = dev_check(np.array([0.04, 0.04]), np.array([0, 40]), 100)
check("a single decisively-wrong low-power cell FAILS", not r_a["ok"],
      f"lowpower_bad={r_a['n_lowpower_bad']}")
#  (b) a SYSTEMATIC bias spread over many low-power cells, each individually innocuous,
#      which cancels against the high-power cells inside the global pooled_z
nlow = 400
sys_pred = np.concatenate([np.full(nlow, 0.02), np.full(400, 0.5)])
rng_lp = np.random.default_rng(99)
sys_obs = np.concatenate([rng_lp.binomial(100, 0.05, nlow),      # truth is 0.05, not 0.02
                          rng_lp.binomial(100, 0.5, 400)])
r_b = dev_check(sys_pred, sys_obs, 100)
check("a systematic bias across many low-power cells FAILS", not r_b["ok"],
      f"global pooled_z={r_b['pooled_z']:+.1f}, low-power pooled_z="
      f"{r_b['lowpower_pooled_z']:+.1f}, per-cell lowpower_bad={r_b['n_lowpower_bad']}")
#  (b2) errors that ALTERNATE IN SIGN, so every signed pool cancels to zero.  Only the
#       Pearson omnibus term sees these.  This is the round-3 audit's counterexample.
r_alt = dev_check(np.array([0.02, 0.05] * 200), np.array([4, 3] * 200), 100)
check("sign-alternating low-power errors FAIL via the Pearson omnibus", not r_alt["ok"],
      f"pooled_z={r_alt['pooled_z']:+.2f}, low pooled_z={r_alt['lowpower_pooled_z']:+.2f}, "
      f"low chi_z={r_alt['lowpower_chi_z']:+.2f}")
#  (c) and low-power cells that genuinely agree still pass
ok_obs = np.concatenate([rng_lp.binomial(100, 0.02, nlow), rng_lp.binomial(100, 0.5, 400)])
check("low-power cells that AGREE still pass", dev_check(sys_pred, ok_obs, 100)["ok"],
      f"low-power pooled_z={dev_check(sys_pred, ok_obs, 100)['lowpower_pooled_z']:+.2f}")

# ======================================================================================
print("\n" + "=" * 100)
print("8. smoothed conformal p: exact conditional rejection probability [D2a]")
print("=" * 100)
Mt = 1000.0
rng8 = np.random.default_rng(11)
for (Gv, Ev_, a) in ((0, 0, 5e-4), (3, 0, 5e-3), (2, 4, 4e-3), (12, 2, 5e-3)):
    nn = 1_000_000
    U = rng8.random(nn)
    got_p = float(((Gv + U * (1 + Ev_)) / Mt <= a).mean())
    want_p = float(np.clip((a * Mt - Gv) / (1 + Ev_), 0, 1))
    se = np.sqrt(max(want_p * (1 - want_p), 1e-12) / nn)
    check(f"P(reject|G={Gv},E={Ev_},a={a:g}) == clip((aM-G)/(1+E))",
          abs(got_p - want_p) <= max(5 * se, 3.0 / nn),
          f"{got_p:.5f} vs {want_p:.5f}")
# the exact-expectation form used for the benign validity table
Gb = rng8.integers(0, 50, 20_000).astype(float)
Eb = rng8.integers(0, 3, 20_000).astype(float)
a = 0.02
qb = np.clip((a * Mt - Gb) / (1.0 + Eb), 0.0, 1.0)
U = rng8.random((400, 20_000))
emp = float((((Gb + U * (1.0 + Eb)) / Mt) <= a).mean())
check("mean of clip(...) is the exact expectation of the benign firing rate",
      abs(emp - float(qb.mean())) < 5 * float(np.sqrt((qb * (1 - qb)).sum())) / 20_000 / 20,
      f"empirical {emp:.6f} vs exact {float(qb.mean()):.6f}")

# ======================================================================================
print("\n" + "=" * 100)
print("9. Route-B calibrator inversion [D3d]")
print("=" * 100)
rng9 = np.random.default_rng(13)
for lam in (0.1, 0.25, 0.5, 0.75):
    for pstar in (1e-6, 1e-4, 1e-2):
        a_eq = pstar ** (1.0 - lam) / lam
        p = rng9.random(200_000) * 3.0 * pstar
        lhs = lam * p ** (lam - 1.0) >= 1.0 / a_eq
        rhs = p <= pstar
        check(f"e >= 1/a  <=>  p <= p*  [lam={lam}, p*={pstar:g}]",
              np.array_equal(lhs, rhs),
              f"{int((lhs != rhs).sum())} disagreements of {len(p)}")

# ======================================================================================
print("\n" + "=" * 100)
print("9b. online e-BH alert times are ENTRY times, not arrival times")
print("=" * 100)
# k* must come from the REAL routine: an earlier version of this test hand-wrote a k*
# trajectory that online_ebh_kstar can never produce, so it proved nothing.
from h6_procs import online_ebh_kstar
Te = 400
rng9b = np.random.default_rng(21)
Ev9 = np.where(rng9b.random(Te) < 0.15, 4000.0, 0.0)
g1e, _ = make_gamma("poly", Te)
ks_t, m_t = online_ebh_kstar(Ev9, g1e, 0.05, Te)
fts = np.cumsum(rng9b.random(Te))                  # strictly increasing arrival times
ent = ebh_entry_ts(ks_t, m_t, fts, Te)
mask9, kfin9, _, _ = ebh_mask(Ev9, g1e, 0.05, Te)
rej_idx = np.flatnonzero(mask9)
check("k* is non-decreasing, as ebh_entry_ts assumes",
      bool(np.all(np.diff(ks_t) >= 0)))
check("every REJECTED hypothesis has a finite entry time",
      bool(np.all(np.isfinite(ent[rej_idx]))), f"{len(rej_idx)} rejections")
check("no rejected hypothesis is alerted before it arrives",
      bool(np.all(ent[rej_idx] >= fts[rej_idx])))
check("entry time is the FIRST step at which k*_t >= m_i, for every rejection",
      all(int(np.searchsorted(ks_t, m_t[i], side='left')) <= Te
          and ent[i] == fts[max(int(np.searchsorted(ks_t, m_t[i], side='left')), i + 1) - 1]
          for i in rej_idx))
check("never-entered hypotheses are NaN, not silently clipped to the last timestamp",
      bool(np.isnan(ent[~np.isfinite(m_t)]).all()) if (~np.isfinite(m_t)).any() else True,
      f"{int((~np.isfinite(m_t)).sum())} hypotheses with infinite m")
check("using arrival times instead would UNDERSTATE latency for the rejections",
      float(np.nansum(ent[rej_idx])) >= float(fts[rej_idx].sum()),
      f"entry {np.nansum(ent[rej_idx]):.1f} vs arrival {fts[rej_idx].sum():.1f}")

# ======================================================================================
print("\n" + "=" * 100)
print("10. metrics / jaccard / ebh_mask")
print("=" * 100)
fired = np.zeros(10, bool); fired[[1, 4, 7]] = True
ismal10 = np.zeros(10, bool); ismal10[[1, 2, 4]] = True
d = metrics(3, 2, 5, 6, fired, ismal10, np.arange(10.0), 10, 3)
check("FDP = V/max(R,1)", abs(d["fdp"] - 1 / 3) < 1e-12, f"{d['fdp']:.4f}")
check("fdp_cond = V/R when R>0", abs(d["fdp_cond"] - 1 / 3) < 1e-12)
d0 = metrics(0, 0, 5, 6, np.zeros(10, bool), ismal10, np.arange(10.0), 10, 3)
check("FDP = 0 and fdp_cond = None when R = 0",
      d0["fdp"] == 0.0 and d0["fdp_cond"] is None)
check("recall uses the malicious-EPISODE denominator", abs(d["recall"] - 2 / 3) < 1e-12)
jm, jsd, jne = jaccard([set(), set(), set()], rng=np.random.default_rng(0))
check("all-empty alert sets give Jaccard None, not 1.0", jm is None and jne == 3,
      f"jm={jm} n_both_empty={jne}")
jm2, _, jne2 = jaccard([{1, 2}, {2, 3}], rng=np.random.default_rng(0))
check("Jaccard of {1,2},{2,3} is 1/3", abs(jm2 - 1 / 3) < 1e-12 and jne2 == 0)
jm3, _, jne3 = jaccard([{1, 2}, set()], rng=np.random.default_rng(0))
check("a mixed empty/non-empty pair scores 0 and is NOT excluded",
      jm3 == 0.0 and jne3 == 0)
Ev = np.where(np.random.default_rng(5).random(500) < 0.1, 5000.0, 0.0)
im = np.random.default_rng(6).random(500) < 0.1
g1s, _ = make_gamma("poly", 500)
ctxe = Ctx(Ev, im, 5000.0, alpha=0.05, w0=0.025)
mask, kfin, _, _ = ebh_mask(Ev, g1s, 0.05, 500)
ref = run_online_ebh(ctxe, g1s)
check("ebh_mask reproduces run_online_ebh's rejection count",
      int(mask.sum()) == ref[0], f"{int(mask.sum())} vs {ref[0]}")
check("ebh_mask reproduces run_online_ebh's true-positive count",
      int((mask & im).sum()) == ref[1], f"{int((mask & im).sum())} vs {ref[1]}")

# ======================================================================================
print("\n" + "=" * 100)
print("11. driver-level constants the mutation audit reached")
print("=" * 100)
tree_all = ast.parse(SRC)
consts = {}
for node in ast.walk(tree_all):
    if isinstance(node, ast.Assign) and len(node.targets) == 1 \
            and isinstance(node.targets[0], ast.Name):
        consts.setdefault(node.targets[0].id, []).append(ast.unparse(node.value))
check("CEIL_BONF is M and CEIL_MEANP is M/2 (not swapped)",
      consts.get("CEIL_BONF") == ["M"] and consts.get("CEIL_MEANP") == ["M / 2.0"],
      f"CEIL_BONF={consts.get('CEIL_BONF')} CEIL_MEANP={consts.get('CEIL_MEANP')}")
check("CEIL_SIMES and CEIL_HOMMEL are M",
      consts.get("CEIL_SIMES") == ["M"] and consts.get("CEIL_HOMMEL") == ["M"])
seed_exprs = [e for e in consts.get("rng", []) if "default_rng" in e]
check("the randomisation seed depends on rs, pos AND dseed (standing mistake 7)",
      any("rs" in e and "pos" in e and "dseed" in e for e in seed_exprs),
      f"{seed_exprs}")
check("the benign validity rate divides by the BENIGN flows (qb.mean()), not all flows",
      "meas = float(qb.mean())" in SRC and "qb = np.clip((a * M - Gb) / (1.0 + Eb)" in SRC)
check("first_ts_h is built in EPISODE order (first_ts[order])",
      "first_ts_h = (first_ts[order] - ts_w.min()) / 3.6e9" in SRC)
# a distinct k* plateau: searchsorted must take the FIRST step at which k*_t >= m_i
ks_pl = np.array([0, 0, 1, 1, 2]); m_pl = np.array([1.0, np.inf, np.inf, np.inf])
ent_pl = ebh_entry_ts(ks_pl, m_pl, np.arange(4.0), 4)
check("ebh_entry_ts takes the FIRST step of a k* plateau (side='left'), not the last",
      ent_pl[0] == 1.0, f"entry={ent_pl[0]} (side='right' would give 3.0)")

# ======================================================================================
print("\n" + "=" * 100)
print(f"{len(fails)} failures" if fails else "ALL PASS")
if fails:
    for f in fails: print("  FAILED: " + f)
print("=" * 100)
sys.exit(1 if fails else 0)
