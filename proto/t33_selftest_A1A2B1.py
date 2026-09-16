"""
Unit tests for the A1 / A2 / B1 machinery.  No data files: everything here is synthetic and
runs in a second, so it can be re-run after any edit to h_meta.py, t30, t31 or t32.

What it pins down:
  1  h_meta's permutation direction (a wrong direction silently attributes one host's
     traffic to another and every forensic conclusion inverts)
  2  the ADDIS state-attack arithmetic against the h6_procs implementation, not against a
     re-derivation of it: B*(R) predicted by the closed form must equal the index at which
     run_addis actually reports its first infeasible step
  3  the precursor size window  n in (lam*CEIL*m, tau*CEIL*m]  at both endpoints
  4  the Mondrian conformal e-value against a brute-force reference
  5  the episode index algebra t31 relies on (rank_of_flow, rep_src, first_ts ordering)
"""
import numpy as np, sys
from pathlib import Path
from scipy.special import zeta

import h_stream as hs
from h6_procs import Ctx, make_gamma, run_addis

fails = []


def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"   {detail}" if detail else ""))
    if not cond:
        fails.append(name)


# ----------------------------------------------------------------------------------
print("=" * 100)
print("1. h_meta permutation direction")
print("=" * 100)
# h_stream builds its cache as: perm = argsort(ts_original); sorted = original[perm]
ts_orig = np.array([50, 10, 30, 20, 40], dtype=np.int64)
side_orig = np.array(["a", "b", "c", "d", "e"])
perm = np.argsort(ts_orig, kind="mergesort")
ts_sorted = ts_orig[perm]
side_sorted = side_orig[perm]            # this is what h_meta._build does
check("perm sorts the timestamps", bool((np.diff(ts_sorted) > 0).all()))
check("side column follows its own row",
      list(side_sorted) == [side_orig[i] for i in np.argsort(ts_orig)],
      f"{list(side_sorted)}")
# the inverse permutation would be wrong -- show it, so a regression is unmistakable
inv = np.argsort(perm)
check("the INVERSE permutation is a different array (so the choice matters)",
      not np.array_equal(perm, inv), f"perm={list(perm)} inv={list(inv)}")

# ----------------------------------------------------------------------------------
print("\n" + "=" * 100)
print("2. ADDIS state attack: closed form against the h6_procs implementation")
print("=" * 100)
Z = float(zeta(1.6, 1))
LAM, TAU, W0, A = 0.25, 0.5, 0.025, 0.05


def bstar_closed(CEIL, R):
    W = W0 if R == 0 else (W0 + (A - W0) + A * max(R - 1, 0))
    Q = ((TAU - LAM) * W * CEIL / Z) ** (1.0 / 1.6)
    return int(np.floor(Q - 1.0)) + 1


def first_infeasible(CEIL, R, n_pre=40_000):
    """A stream of R immediately-rejected episodes followed by n_pre precursors with
    p = 0.375 in (lam, tau].  run_addis reports the 1-indexed first infeasible step."""
    Ev = np.concatenate([np.full(R, CEIL), np.full(n_pre, 1.0 / 0.375)])
    im = np.zeros(len(Ev), bool)
    ctx = Ctx(Ev, im, CEIL, alpha=A, w0=W0)
    _, g0 = make_gamma("poly", len(Ev))
    rej, tp, sil, first = run_addis(ctx, g0, lam=LAM, tau_=TAU)
    return rej, first


for CEIL in (1_813_114.0, 1e4, 1e5, 1e6):
    for R in (0, 1, 5, 20):
        rej, first = first_infeasible(CEIL, R)
        pred = bstar_closed(CEIL, R)
        # the first R steps are the rejections (D stays 0), then precursor j sees D = j-1,
        # so the first infeasible step is at 1-indexed position R + pred + 1
        check(f"CEIL={CEIL:>10,.0f} R={R:>2}: first infeasible step",
              first == R + pred + 1 and rej == R,
              f"run_addis={first}, predicted={R + pred + 1}, rejections={rej}/{R}")

# and the state, once infeasible, is absorbing: no later step recovers
Ev = np.concatenate([np.full(50_000, 1.0 / 0.375), np.full(200, 1_813_114.0)])
ctx = Ctx(Ev, np.zeros(len(Ev), bool), 1_813_114.0, alpha=A, w0=W0)
_, g0 = make_gamma("poly", len(Ev))
rej, tp, sil, first = run_addis(ctx, g0, lam=LAM, tau_=TAU)
check("after B* precursors, 200 ceiling-valued episodes still yield no rejection",
      rej == 0, f"rejections={rej}, first infeasible={first}")

# the attack needs the p-value strictly inside (lam, tau]: at p = 1 the index never moves
Ev0 = np.concatenate([np.zeros(50_000), np.full(200, 1_813_114.0)])
ctx0 = Ctx(Ev0, np.zeros(len(Ev0), bool), 1_813_114.0, alpha=A, w0=W0)
_, g00 = make_gamma("poly", len(Ev0))
rej0, _, sil0, first0 = run_addis(ctx0, g00, lam=LAM, tau_=TAU)
check("50,000 DISCARDED episodes (p = 1) do not advance the index",
      rej0 == 200 and first0 is None, f"rejections={rej0}, first infeasible={first0}")

# ----------------------------------------------------------------------------------
print("\n" + "=" * 100)
print("3. precursor size window")
print("=" * 100)
CEIL = 1_813_114.0
for m in (1, 3):
    n_lo = int(np.floor(LAM * CEIL * m)) + 1
    n_hi = int(np.floor(TAU * CEIL * m))
    for n, want in ((n_lo - 1, False), (n_lo, True), (n_hi, True), (n_hi + 1, False)):
        p = min(1.0, n / (CEIL * m))
        check(f"m={m} n={n:,}: p in (lam, tau] is {want}",
              (LAM < p <= TAU) == want, f"p={p:.6f}")

# ----------------------------------------------------------------------------------
print("\n" + "=" * 100)
print("4. Mondrian conformal e-value against a brute-force reference")
print("=" * 100)
sys.path.insert(0, ".")
import importlib.util
spec = importlib.util.spec_from_file_location("_t30", "t30_A1_tailforensics.py")
# t30 executes a full experiment on import, so the function is transcribed here instead and
# checked to be character-identical to the one in the script.
src_txt = (Path(__file__).resolve().parent / "t30_A1_tailforensics.py").read_text()
assert "def mondrian(" in src_txt, "mondrian() has been renamed; update this test"
ns = {"np": np}
body = src_txt[src_txt.index("def mondrian("):src_txt.index("repairs = {}")]
exec(body, ns)
mondrian = ns["mondrian"]

rng = np.random.default_rng(0)
NC_, NT = 4000, 3000
strat_cal = rng.integers(0, 4, NC_)
strat_te = rng.integers(0, 5, NT)          # stratum 4 has no calibration flows
s_cal = rng.normal(size=NC_) + strat_cal
y_cal = (rng.random(NC_) < 0.05).astype(np.int8)
s_te = rng.normal(size=NT) + strat_te
for k in (1, 5):
    e, ceil_of, n_unc = mondrian(s_cal, y_cal, s_te, strat_cal, strat_te, k=k)
    ok = True
    for i in range(0, NT, 37):                 # brute force a sample of test flows
        s_ = strat_te[i]
        seg = np.sort(s_cal[(y_cal == 0) & (strat_cal == s_)])
        if len(seg) == 0:
            ok &= (e[i] == 0.0); continue
        rk = 1 + int((seg >= s_te[i]).sum())
        want = (len(seg) + 1.0) / k if rk <= k else 0.0
        ok &= abs(e[i] - want) < 1e-9
    check(f"k={k}: mondrian matches brute force", ok,
          f"uncalibrated={n_unc} (expected {(strat_te == 4).sum()})")
    check(f"k={k}: strata absent from calibration get e = 0",
          n_unc == int((strat_te == 4).sum()) and float(e[strat_te == 4].max(initial=0.0)) == 0.0)
# Validity on exchangeable data.  The firing rate must average k/(n_s+1) over the
# CALIBRATION DRAW, not within one draw: with a single calibration set the conditional rate
# is P(x > max C_s), which is Beta(1, n_s) and has standard deviation equal to its mean --
# this is F10 measured, and it is why the test below averages over many independent strata
# rather than three.  A three-stratum version of this test saw conditional counts of
# 123 / 1,727 / 2,251 against a nominal 497 and could not have detected a rank bug.
NS, NCAL_S, NTE = 2000, 50, 300_000
strat = np.repeat(np.arange(NS), NCAL_S)
sc = rng.normal(size=NS * NCAL_S)
ycal = np.zeros(NS * NCAL_S, np.int8)
st_te = rng.integers(0, NS, NTE)
ste = rng.normal(size=NTE)
e, ceil_of, _ = mondrian(sc, ycal, ste, strat, st_te, k=1)
n_fire = int((e > 0).sum())
c_ = NCAL_S
EU = 1.0 / (c_ + 1.0); VU = c_ / ((c_ + 1.0) ** 2 * (c_ + 2.0))
nps = NTE / NS
var = NS * (nps * (EU - (VU + EU ** 2)) + nps ** 2 * VU)     # E[Var|U] + Var[E|U]
sd = float(np.sqrt(var)); exp = NTE * EU
check("exchangeable synthetic data: firing count matches nominal within 4 s.d.",
      abs(n_fire - exp) < 4 * sd,
      f"fired={n_fire}, expected={exp:.0f} +/- {sd:.0f} "
      f"(rate {n_fire/NTE:.4e} vs nominal {EU:.4e})")
check("exchangeable synthetic data: E[e] = 1 within 4 s.d.",
      abs(float(e.mean()) - 1.0) < 4 * (c_ + 1.0) * sd / NTE,
      f"E[e]={e.mean():.4f}  (position 0.85 measures ~51 for exactly this quantity)")

# ----------------------------------------------------------------------------------
print("\n" + "=" * 100)
print("5. episode index algebra used by t31")
print("=" * 100)
n = 12
ts_w = np.array([5, 1, 5, 2, 9, 9, 1, 3, 3, 7, 7, 7], dtype=np.int64) * 1_000_000
src_w = np.array([1, 2, 1, 2, 3, 3, 2, 1, 1, 4, 4, 4], dtype=np.int64)
dst_w = np.array([9, 8, 9, 8, 7, 7, 8, 6, 6, 5, 5, 5], dtype=np.int64)
y_w = np.array([0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1], dtype=np.int8)
e_w = np.array([0., 0., 100., 0., 100., 0., 0., 0., 0., 0., 0., 100.])
ep = hs.build_episodes(e_w, y_w, ts_w, src_w, dst_w, 3600, "src-dst")
T = ep["T"]
order = ep["order"]; gid = ep["gid"]
inv = np.empty(T, dtype=np.int64); inv[order] = np.arange(T)
rank_of_flow = inv[gid]
first_ts_g = np.full(T, np.iinfo(np.int64).max); np.minimum.at(first_ts_g, gid, ts_w)
first_ts_g = first_ts_g[order]
check("episode first timestamps are non-decreasing in rank order",
      bool((np.diff(first_ts_g) >= 0).all()), str(first_ts_g // 1_000_000))
rep_src = np.zeros(T, np.int64); rep_src[rank_of_flow] = src_w
rep_dst = np.zeros(T, np.int64); rep_dst[rank_of_flow] = dst_w
ok = all((len(set(src_w[rank_of_flow == r])) == 1 and rep_src[r] == src_w[rank_of_flow == r][0])
         for r in range(T))
check("src is constant within an episode and rep_src recovers it", ok)
ok = all((len(set(dst_w[rank_of_flow == r])) == 1 and rep_dst[r] == dst_w[rank_of_flow == r][0])
         for r in range(T))
check("dst is constant within an episode and rep_dst recovers it", ok)
nsz_chk = np.array([int((rank_of_flow == r).sum()) for r in range(T)])
check("ep['nsz'] is in rank order", bool((nsz_chk == ep["nsz"]).all()),
      f"{list(nsz_chk)} vs {list(ep['nsz'])}")
sum_e_chk = np.array([float(e_w[rank_of_flow == r].sum()) for r in range(T)])
check("ep['sum_e'] is in rank order", bool(np.allclose(sum_e_chk, ep["sum_e"])),
      f"{list(sum_e_chk)} vs {list(ep['sum_e'])}")
mal_chk = np.array([bool(y_w[rank_of_flow == r].any()) for r in range(T)])
check("ep['ismal'] is in rank order", bool((mal_chk == ep["ismal"]).all()))
check("ep['Ev'] equals sum_e / nsz in rank order",
      bool(np.allclose(ep["Ev"], ep["sum_e"] / np.maximum(ep["nsz"], 1))))

# ----------------------------------------------------------------------------------
print("\n" + "=" * 100)
print("6. run_addis level trace, and the (service, dport) key")
print("=" * 100)
# the levels out-parameter must not change the result, and must be the level the procedure
# actually offered -- t32 prices the padding attack against it
rng2 = np.random.default_rng(3)
Tt = 4000
Evt = np.zeros(Tt); hit = np.sort(rng2.choice(Tt, 40, replace=False)); Evt[hit] = 5e5
ctx_t = Ctx(Evt, np.zeros(Tt, bool), 5e5, alpha=A, w0=W0)
_, g0t = make_gamma("poly", Tt)
r_a = run_addis(ctx_t, g0t, lam=LAM, tau_=TAU)
lv = np.zeros(Tt)
r_b = run_addis(ctx_t, g0t, lam=LAM, tau_=TAU, levels=lv)
check("levels= does not change the result", r_a == r_b, f"{r_a} vs {r_b}")
check("every traced level is in (0, lam]", bool(((lv > 0) & (lv <= LAM)).all()),
      f"min={lv.min():.3e} max={lv.max():.3e}")
# a rejection happens exactly when Pv <= level and the level is feasible
fired_t = np.zeros(Tt, bool)
run_addis(ctx_t, g0t, lam=LAM, tau_=TAU, fired=fired_t, levels=lv)
pv = np.where(Evt > 0, np.minimum(1.0, 1.0 / np.maximum(Evt, 1e-300)), 1.0)
feas = ctx_t.CEIL >= 1.0 / lv
check("fired == (feasible and Pv <= level)",
      bool((fired_t == (feas & (pv <= lv))).all()))
# suppression boundary: an episode with m ceiling flows is rejected iff n <= level*CEIL*m
CE = 5e5
for m in (1, 4):
    for t_i in (int(hit[0]), int(hit[-1])):
        n_max = int(np.floor(lv[t_i] * CE * m))
        for n, want in ((n_max, True), (n_max + 1, False)):
            Ev_ = CE * m / n
            check(f"m={m} t={t_i} n={n:,}: rejected is {want}",
                  (Ev_ >= 1.0 / lv[t_i]) == want, f"Ev={Ev_:.3f} thr={1/lv[t_i]:.3f}")

# (service, dport) key must not alias a missing port with port 0, nor collide across services
def svc_key(service, dport):
    d = np.asarray(dport, dtype=np.int64)
    return np.asarray(service, dtype=np.int64) * 65537 + (d + 1)


svcs = np.array([0, 0, 1, 1, 2])
dps = np.array([-1, 0, 65535, -1, 1])
k = svc_key(svcs, dps)
check("(service, dport) keys are distinct including the missing port",
      len(np.unique(k)) == 5, str(list(k)))
check("the old clip-based key WOULD have aliased missing with port 0",
      len(np.unique(svcs * 65536 + np.clip(dps, 0, 65535))) == 4)

print("\n" + "=" * 100)
print(f"{'ALL TESTS PASS' if not fails else 'FAILURES: ' + ', '.join(fails)}")
print("=" * 100)
sys.exit(1 if fails else 0)
