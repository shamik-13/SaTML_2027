"""T3 -- general feasibility theorem, numerical verification."""


def main():
    import json
    import numpy as np
    from pathlib import Path

    OUT = Path(__file__).resolve().parent / "out"
    OUT.mkdir(exist_ok=True)
    res = {"config": dict(alpha=0.05, w0=0.025, horizon=10 ** 7)}

    A,W0 = 0.05, 0.025
    from scipy.special import zeta as _zeta
    def g_poly(n,e=1.6):
        """normalise by the INFINITE sum zeta(e), not the truncated one, so the sequence is"""
        j=np.arange(1,n+1,dtype=float); return j**-e/_zeta(e,1)
    def g_jm(n):
        j=np.arange(1,n+1,dtype=float); l=np.log(np.maximum(j,2.0))
        x=l/(j*np.exp(np.sqrt(np.log(np.maximum(j,2.0)))))
        return x/x.sum()

    H=10**7
    GAMS={"gamma ~ j^-1.6":g_poly(H), "gamma ~ JM":g_jm(H)}

    print("="*100)
    print("PART 1 -- does the sharp condition gamma_t * t^d -> 0 hold for our gamma families?")
    print("="*100)
    print(f"  {'gamma':>16} {'d=1: max t^1*g_t':>20} {'argmax':>10} {'limit t^1*g_t':>16} {'d=2 diverges?':>15}")
    res["sharp_condition"] = []
    for nm,gam in GAMS.items():
        t=np.arange(1,H+1,dtype=float)
        v1=gam*t; v2=gam*t**2
        res["sharp_condition"].append(dict(gamma=nm, max_t_gamma=float(v1.max()),
                                           argmax=int(np.argmax(v1))+1,
                                           limit_t_gamma=float(v1[-1]),
                                           d2_diverges=bool(v2[-1]>v2[len(v2)//2])))
        print(f"  {nm:>16} {v1.max():>20.4f} {int(np.argmax(v1))+1:>10,} {v1[-1]:>16.2e} "
              f"{str(v2[-1]>v2[len(v2)//2]):>15}")
    print("  -> d=1 (LOND, e-LOND, LORD++ , SAFFRON, ADDIS): gamma_t*t -> 0, condition HOLDS.")
    print("  -> d=2 would NOT hold for gamma~j^-1.6. The degree of g matters and must be checked.")

    print("\n" + "="*100)
    print("PART 2 -- feasibility horizon per procedure (family I, multiplicative)")
    print("   largest t at which rejection is possible, given R rejections so far")
    print("="*100)
    def horizon_mult(gam,M,c=1.0,d=1,R=0):
        """largest t at which rejection is possible GIVEN exactly R prior rejections."""
        t=np.arange(1,len(gam)+1)
        lvl=A*gam*c*float(R+1)**d
        lvl=np.where(t>=R+1, lvl, 0.0)
        ok=np.nonzero(lvl>=1.0/M)[0]
        return int(ok[-1]+1) if len(ok) else 0
    print(f"  {'procedure':>28} {'|C|':>10} {'R=0':>10} {'R=10':>10} {'R=1000':>12} {'R=t (all rej)':>14}")
    for nm,gam in GAMS.items():
        print(f"  --- {nm}")
        for nc in (10**4,10**6):
            M=nc+1.0
            r0=horizon_mult(gam,M,R=0); r10=horizon_mult(gam,M,R=10)
            r1k=horizon_mult(gam,M,R=1000)
            t=np.arange(1,len(gam)+1); lvl=A*gam*t
            rall=int(np.nonzero(lvl>=1.0/M)[0][-1]+1) if (lvl>=1.0/M).any() else 0
            res.setdefault("horizon_multiplicative", []).append(
                dict(gamma=nm, NC=nc, R0=r0, R10=r10, R1000=r1k, R_all=rall))
            print(f"  {'LOND / e-LOND':>28} {nc:>10,} {r0:>10,} {r10:>10,} {r1k:>12,} {rall:>14,}")

    print("\n" + "="*100)
    print("PART 3 -- absorbing Delta* per procedure (family II, lag-sum: LORD++/SAFFRON/ADDIS)")
    print("="*100)
    def absorbing_delta(gam,M):
        S=np.cumsum(gam[::-1])[::-1]
        bad=np.nonzero((W0+A)*S < 1.0/M)[0]
        return int(bad[0]+1) if len(bad) else None
    print(f"  {'gamma':>16} {'|C|=1e4':>12} {'|C|=1e6':>12} {'|C|=1e8':>14}")
    for nm,gam in GAMS.items():
        row=[absorbing_delta(gam,nc+1.0) for nc in (10**4,10**6,10**8)]
        res.setdefault("absorbing_delta", []).append(
            dict(gamma=nm, **{f"NC_1e{int(np.log10(nc))}": x for nc,x in zip((10**4,10**6,10**8), row)}))
        print(f"  {nm:>16} " + " ".join(f"{(f'{x:,}' if x else '>1e7'):>12}" for x in row))

    print("\n" + "="*100)
    print("PART 4 -- empirical check: e-LOND fed MAXIMUM evidence at the true attack rate")
    print("   (best case for the procedure: every attack flow fires at the ceiling)")
    print("="*100)
    def run_elond(T,pi,M,gam,seed=0,p_ben_fire=2e-6):
        """Faithful e-LOND: R increments on ANY rejection, including false ones."""
        rng=np.random.default_rng(seed)
        is_att=np.zeros(T,bool); is_att[rng.choice(T,max(1,int(T*pi)),replace=False)]=True
        ben_fire=rng.random(T)<p_ben_fire
        R=0; rej=0; false_rej=0; silent=0; first=None
        for t in range(1,T+1):
            lvl=A*gam[t-1]*(R+1)
            if M < 1.0/lvl:
                silent+=1
                if first is None: first=t
                continue
            fires = is_att[t-1] or ben_fire[t-1]
            if fires:
                R+=1
                if is_att[t-1]: rej+=1
                else: false_rej+=1
        return rej,int(is_att.sum()),silent/T,first,false_rej
    print(f"  {'|C|':>10} {'pi':>8} {'attacks':>9} {'rejected':>10} {'silent%':>9} {'1st infeasible t':>18} {'false rej':>10}")
    T=500_000; gam=g_poly(T+10)
    for nc in (10**4,10**6,10**8):
        for pi in (1e-4,1e-2):
            rej,na,sil,first,fr=run_elond(T,pi,nc+1.0,gam)
            res.setdefault("elond_max_evidence", []).append(
                dict(NC=nc, pi=pi, attacks=int(na), rejected=int(rej),
                     silent_frac=float(sil), first_infeasible=first, false_rej=int(fr)))
            print(f"  {nc:>10,} {pi:>8.0e} {na:>9,} {rej:>10,} {100*sil:>8.1f}% "
                  f"{(f'{first:,}' if first else '-'):>18} {fr:>10,}")

    print("\n" + "="*100)
    print("PART 5 -- is the JM horizon contaminated by finite-horizon normalisation?")
    print("="*100)
    for H2 in (10**7, 10**8):
        gj=g_jm(H2)
        S=np.cumsum(gj[::-1])[::-1]
        d=[int(np.nonzero((W0+A)*S < 1.0/(nc+1.0))[0][0]+1) if ((W0+A)*S < 1.0/(nc+1.0)).any() else None
           for nc in (10**4,10**6)]
        res.setdefault("jm_normalisation", []).append(
            dict(H=H2, **{f"NC_1e{int(np.log10(nc))}": x for nc,x in zip((10**4,10**6), d)}))
        print(f"  JM normalised over H={H2:>12,}: absorbing Delta* = "
              + ", ".join(f"|C|=1e{int(np.log10(nc))}: {(f'{x:,}' if x else '>H')}"
                          for nc,x in zip((10**4,10**6),d)))
    tail = float(np.sum(np.arange(10**7+1,10**8+1,dtype=float)**-1.6)/_zeta(1.6,1))
    res["poly_normaliser"] = dict(zeta_1_6=float(_zeta(1.6,1)), tail_beyond_1e7=tail)
    print(f"  poly j^-1.6 uses the exact infinite normaliser zeta(1.6)={float(_zeta(1.6,1)):.4f}; "
          f"tail beyond 1e7 = {tail:.2e}")

    json.dump(res, open(OUT / "t15_T3.json", "w"), indent=1)
    print(f"\n  wrote out/t15_T3.json")
    return res


if __name__ == "__main__":
    main()
