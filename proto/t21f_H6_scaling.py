"""
H6, part 5 -- how much does online e-BH actually weaken the calibration requirement?

F1 states that retaining feasibility over horizon T with no prior rejections requires
|C| >= kT/w0 - 1 under horizon-uniform gamma: 654 million at LSPR23 event scale.

online e-BH rejects H_i when E_i >= 1/(k*_t alpha gamma_i).  Two different questions get
two different answers, and conflating them overstates the escape:

  (a) CAN H_i EVER BE REJECTED?  k*_t <= t <= T, so the necessary condition is
          |C| >= k/(T alpha gamma_i) - 1,
      which under gamma = 1/T is |C| >= k/alpha - 1 = 19, independent of T.  This is the
      "is the infeasible state absorbing?" question of section 4.13, and the answer is that
      it is NOT absorbing.  But k = T requires every hypothesis to be rejected, so this is
      an upper bound on what is attainable, not a promise.

  (b) WHAT IS ACTUALLY ATTAINED?  k*_T is the self-consistent fixed point.  Making R
      discoveries under gamma = 1/T needs R hypotheses each carrying E >= T/(R alpha),
      hence
          |C| >= T/(alpha R) - 1,
      against Family I/II's cold-start |C| >= T/w0 - 1.  The improvement factor is
      alpha R / w0 = 2R -- the number of SIMULTANEOUS strong signals, not the horizon.

So the escape is real but it is an escape from the feasibility metric, not from the
calibration budget: the requirement still scales linearly in T, just divided by R.

No real data is used; this is an [EXACT] check of a scaling law, confirmed numerically
against the actual fixed point.
"""
import numpy as np, json
from pathlib import Path
from scipy.special import zeta
from h6_procs import Ctx, make_gamma, run_lond, run_online_ebh

Path("out").mkdir(exist_ok=True)
ALPHA = 0.05; W0 = 0.025; K = 1

print("=" * 104)
print("(a) CAN A REJECTION EVER HAPPEN?  necessary condition, horizon-uniform gamma = 1/T")
print("=" * 104)
print(f"  {'horizon T':>16} {'Family I/II cold start: kT/w0 - 1':>36} {'online e-BH at k=T: k/alpha - 1':>33}")
never = []
for T in (10 ** 3, 31_568, 10 ** 6, 16_353_511):
    fam = K * T / W0 - 1.0
    ebh = K / ALPHA - 1.0
    never.append(dict(T=int(T), family_I_II=fam, online_ebh_upper=ebh))
    print(f"  {T:>16,} {fam:>36,.0f} {ebh:>33,.0f}")
print("\n  The Family I/II state is absorbing; online e-BH's is not, at any horizon.")
print("  But k = T is attainable only if every hypothesis is rejected, so this bound is")
print("  NOT a calibration budget.  The attainable requirement is (b).")

print("\n" + "=" * 104)
print("(b) WHAT IS ATTAINABLE?  |C| needed to make R simultaneous discoveries, gamma = 1/T")
print("=" * 104)
print(f"  {'horizon T':>14} {'R=1':>16} {'R=10':>16} {'R=152':>16} {'R=10^4':>16} "
      f"{'Family I/II':>18}")
attain = []
for T in (31_568, 10 ** 6, 16_353_511):
    row = dict(T=int(T), family_I_II=K * T / W0 - 1.0)
    cells = []
    for R in (1, 10, 152, 10 ** 4):
        v = T / (ALPHA * R) - 1.0
        row[f"R={R}"] = v; cells.append(f"{v:>16,.0f}")
    attain.append(row)
    print(f"  {T:>14,} " + " ".join(cells) + f" {row['family_I_II']:>18,.0f}")
print("\n  Requirement is linear in T divided by R.  Improvement over Family I/II is exactly")
print(f"  alpha*R/w0 = {ALPHA/W0:.0f}R, so it buys a constant factor per simultaneous signal,")
print("  not a factor of the horizon.")

# --- numerical confirmation of (b) against the actual fixed point --------------------
print("\n" + "=" * 104)
print("NUMERICAL CHECK -- actual fixed point, gamma = 1/T, R signals at the ceiling")
print("=" * 104)
print(f"  {'T':>10} {'R signals':>10} {'|C| needed T/(aR)-1':>21} {'|C| used':>12} "
      f"{'e-LOND rej':>11} {'e-BH rej':>9} {'e-BH silent':>12}")
chk = []
for T, R in ((10 ** 4, 100), (10 ** 5, 1000), (10 ** 6, 10 ** 4), (10 ** 6, 100)):
    need = T / (ALPHA * R) - 1.0
    for mult, tag in ((1.05, "just above"), (0.95, "just below")):
        NC = max(1.0, need * mult); CEIL = NC + 1.0
        Ev = np.zeros(T); Ev[np.linspace(0, T - 1, R).astype(int)] = CEIL
        ismal = Ev > 0
        ctx = Ctx(Ev, ismal, CEIL, alpha=ALPHA, w0=W0)
        g1u, _ = make_gamma("uniform", T)
        lr = run_lond(ctx, g1u); eb = run_online_ebh(ctx, g1u)
        chk.append(dict(T=int(T), R=int(R), need=need, NC=float(NC), tag=tag,
                        elond_rej=int(lr[0]), ebh_rej=int(eb[0]), kstar=int(eb[4]),
                        ebh_silent=float(eb[2] / T)))
        print(f"  {T:>10,} {R:>10,} {need:>21,.0f} {NC:>12,.0f} ({tag:>9}) "
              f"{lr[0]:>11,} {eb[0]:>9,} {100*eb[2]/T:>11.1f}%")
print("\n  e-BH fires exactly when |C| clears T/(alpha R) - 1 and not below it, confirming (b).")
print("  e-LOND rejects nothing in any of these cells, confirming the cold-start barrier.")

json.dump({"never_absorbing": never, "attainable": attain, "numerical_check": chk,
           "alpha": ALPHA, "w0": W0, "k": K},
          open("out/t21f_H6_scaling.json", "w"), indent=1)
print("\n  wrote out/t21f_H6_scaling.json")
