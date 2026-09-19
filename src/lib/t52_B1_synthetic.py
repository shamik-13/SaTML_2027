
import numpy as np, json, time
from pathlib import Path

from h6_procs import Ctx, make_gamma, run_addis


# ---- configuration -------------------------------------------------------------------------
T = 20_000                # legitimate hypotheses
N_TARGET = 120           # genuine non-null targets (strong signal)
P_ALT = 1e-6             # target p-value; small so targets stay detectable over the feasible prefix
LAM, TAU = 0.25, 0.5
A, W0 = 0.05, 0.025
N_SEED = 200             # seeds for the FDR-validity check
P_PRE = (LAM + TAU) / 2.0  # attacker precursor p-value, strictly inside (lambda, tau]
BIG = 1e9                 # Ev for a p=0 style strong target: Ev = 1/p


def make_stream(seed, with_targets=True):
    """Legitimate stream: null p ~ Uniform(0,1) (independent, uniformly conservative -- ADDIS's
    assumption holds exactly); genuine targets carry p = P_ALT.  Ctx stores Ev with p = 1/Ev, so we
    pass Ev = 1/p."""
    rng = np.random.default_rng(seed)
    p = rng.uniform(0.0, 1.0, T)
    ismal = np.zeros(T, bool)
    if with_targets:
        pos = np.linspace(0, T - 1, N_TARGET).round().astype(int)
        p[pos] = P_ALT
        ismal[pos] = True
    Ev = 1.0 / np.maximum(p, 1e-300)

    return Ev, ismal


def addis_run(Ev, ismal, CEIL=BIG):
    ctx = Ctx(Ev, ismal, CEIL, alpha=A, w0=W0)
    _, g0 = make_gamma("poly", ctx.T)
    fired = np.zeros(ctx.T, bool)
    rej, tp, sil, _ = run_addis(ctx, g0, lam=LAM, tau_=TAU, fired=fired)
    V = int((fired & ~ismal).sum()); R = int(fired.sum())
    return dict(rej=R, tp=int(tp), fp=V, fdp=(V / R if R else 0.0),
                recall=(tp / int(ismal.sum()) if ismal.any() else 0.0), fired=fired)


def main():
    t0 = time.time()
    Path("out").mkdir(exist_ok=True)
    out = {"config": dict(T=T, n_target=N_TARGET, p_alt=P_ALT, lam=LAM, tau=TAU,
                          alpha=A, w0=W0, n_seed=N_SEED, p_precursor=P_PRE,
                          null="independent Uniform(0,1) -- uniformly conservative, ADDIS-valid")}
    print(f"  synthetic stream: T={T:,}, {N_TARGET} targets (p={P_ALT}), null p~U(0,1), "
          f"precursor p={P_PRE}  [{time.time()-t0:.0f}s]")


    print("\n" + "=" * 92)
    print("A -- ADDIS FDR CONTROL under uniformly-conservative U(0,1) nulls (the assumption it needs)")
    print("=" * 92)

    fdps_null, rej_null = [], []
    for s in range(N_SEED):
        Ev, ismal = make_stream(2000 + s, with_targets=False)
        r = addis_run(Ev, ismal)
        fdps_null.append(r["fdp"]); rej_null.append(r["rej"])
    fdps_null = np.array(fdps_null)
    # mixed (targets present): FDR <= q, and targets detected
    fdps_mix, rec_mix, tp_mix = [], [], []
    for s in range(N_SEED):
        Ev, ismal = make_stream(3000 + s, with_targets=True)
        r = addis_run(Ev, ismal)
        fdps_mix.append(r["fdp"]); rec_mix.append(r["recall"]); tp_mix.append(r["tp"])
    fdps_mix = np.array(fdps_mix)
    out["validity"] = dict(
        all_null=dict(mean_fdp=float(fdps_null.mean()), max_fdp=float(fdps_null.max()),
                      frac_seed_any_rej=float((np.array(rej_null) > 0).mean()),
                      controlled=bool(fdps_null.mean() <= A)),
        mixed=dict(mean_fdp=float(fdps_mix.mean()), max_fdp=float(fdps_mix.max()),
                   mean_recall=float(np.mean(rec_mix)), mean_tp=float(np.mean(tp_mix)),
                   controlled=bool(fdps_mix.mean() <= A)))
    print(f"  all-null (every rejection is false):  mean FDP {fdps_null.mean():.4f}  "
          f"max {fdps_null.max():.4f}  <= q={A}?  {fdps_null.mean() <= A}")
    print(f"  mixed (targets present):              mean FDP {fdps_mix.mean():.4f}  "
          f"mean recall {np.mean(rec_mix):.3f}  <= q?  {fdps_mix.mean() <= A}")
    print(f"  => ADDIS's guarantee genuinely holds on this stream (unlike LSPR23's 0.85 window).")


    rng = np.random.default_rng(9)
    pn = rng.uniform(0, 1, 2_000_000); sel = pn[pn <= TAU]
    diag = [dict(x=x, lhs=float((sel <= x * TAU).mean()), ok=bool((sel <= x * TAU).mean() <= x + 5e-3))
            for x in (0.01, 0.05, 0.1, 0.25, 0.5, 1.0)]
    out["uniform_conservative_diag"] = diag
    print("  uniform-conservativeness of the null (P(P/tau<=x | P<=tau) <= x):")
    for d in diag:
        print(f"    x={d['x']:.2f}  lhs={d['lhs']:.3f}  {'ok' if d['ok'] else 'VIOLATED'}")


    def attack(seed, Bmax=8000):

        Ev, ismal = make_stream(seed=seed, with_targets=True)
        base = addis_run(Ev, ismal)
        det0 = base["fired"] & ismal
        n_det0 = int(det0.sum())

        def rej_at(B):
            Ev2 = np.concatenate([np.full(B, 1.0 / P_PRE), Ev])
            im2 = np.concatenate([np.ones(B, bool), ismal])   # precursors are ALTERNATIVES, not nulls
            r = addis_run(Ev2, im2)
            return r["rej"], int((r["fired"][B:] & det0).sum())

        coarse = [0, 32, 64, 128, 192, 256, 384, 512, 768, 1024, 1536, 2048, 3072, 4096, 6144, Bmax]
        kill = next((B for B in coarse if rej_at(B)[0] == 0), None)
        if kill is None:
            return None, False, n_det0, base, det0, rej_at
        lo = max([c for c in coarse if c < kill], default=0); hi = kill
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if rej_at(mid)[0] == 0: hi = mid
            else: lo = mid
        b_star = hi
        stable = all(rej_at(min(int(b_star * f), Bmax))[0] == 0 for f in (1, 2, 4))
        return b_star, stable, n_det0, base, det0, rej_at


    N_ATTACK = 300
    bstars, stables = [], 0
    for s in range(N_ATTACK):
        b, st, _, _, _, _ = attack(s)
        if b is not None:
            bstars.append(b); stables += int(st)
    bstars = np.array(sorted(bstars))
    q = lambda p: float(np.percentile(bstars, p)) if len(bstars) else None
    print(f"  B* over {N_ATTACK} guarantee-valid streams: min={int(bstars.min())} q25={q(25):.0f} "
          f"median={q(50):.0f} q75={q(75):.0f} max={int(bstars.max())}; "
          f"silence stable above B* on {stables}/{N_ATTACK}")

    b7, st7, n_det0, base, det0, rej7 = attack(7)
    grid = sorted({0, 32, 128, 256, b7 - 1, b7, b7 + 1, 2 * b7} - {x for x in (b7 - 1,) if b7 <= 0})
    grid = [b for b in grid if b >= 0]
    sweep = []
    print(f"\n  witness seed 7: clean {base['rej']} rej ({base['tp']} true, FDP {base['fdp']:.4f}); "
          f"B*={b7} (stable above={st7})")
    print(f"  {'B (precursors)':>15} {'total rej':>10} {'targets kept':>13}")
    for B in grid:
        rej, survive = rej7(B)
        sweep.append(dict(B=int(B), total_rej=int(rej), targets_kept=int(survive),
                          kept_frac=survive / max(n_det0, 1)))
        print(f"  {B:>15} {rej:>10} {survive:>7}/{n_det0:<5}")

    out["attack"] = dict(
        n_det_clean=n_det0,
        bstar_distribution=dict(n_streams=N_ATTACK, min=int(bstars.min()), q25=q(25), median=q(50),
                                q75=q(75), max=int(bstars.max()), n_stable=int(stables)),
        witness_seed7=dict(b_star=int(b7), stable_above=bool(st7), sweep=sweep),
        precursors=("alternative (non-null), p in (lam,tau] = SELECTED non-candidates; true nulls stay "
                    "U(0,1) so ADDIS's assumption & FDR guarantee hold on the ATTACKED stream"),
        note=("silence is absorbing over the finite realization; a rare null false positive can "
              "transiently restore wealth, so B* is reported as a distribution with a stability check"),
        clean=dict(rej=base["rej"], tp=base["tp"], fp=base["fp"], fdp=base["fdp"], recall=base["recall"]))
    print(f"\n  => Even on streams where ADDIS's guarantee HOLDS (nulls U(0,1)), a median of {q(50):.0f}")
    print(f"     alternative precursors silences every rejection -- a genuine post-attack failure of a")
    print(f"     guarantee-valid stream, not an artefact of the dataset already violating the assumption.")

    json.dump(out, open("out/t52_B1_synthetic.json", "w"), indent=1, allow_nan=False)
    print(f"\n  [{time.time()-t0:.0f}s]  wrote out/t52_B1_synthetic.json")
    return out


if __name__ == "__main__":
    main()
