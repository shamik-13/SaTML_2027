"""E8, part 1 -- the ANALYTIC derivation of the flows -> operational-units conversion, and the"""
import math
import numpy as np



def recover_duration_scale(duration, total_bytes, bytes_per_s, min_dur=0.0,
                           min_bytes=0.0):
    """Recover the unit of `Flow Duration` from internal consistency.  [D1a]"""
    d = np.asarray(duration, float); b = np.asarray(total_bytes, float)
    r = np.asarray(bytes_per_s, float)
    m = (d > min_dur) & (b > min_bytes) & (r > 0) & np.isfinite(d) & np.isfinite(b) & np.isfinite(r)
    if not m.any():
        raise ValueError("no usable flows for unit recovery")
    tbl = {}
    for name, S in SCALES.items():
        implied = b[m] / (d[m] / S)
        tbl[name] = float(np.median(np.abs(np.log10(implied / r[m]))))
    best = min(tbl, key=tbl.get)
    return best, tbl, dict(n_used=int(m.sum()), frac_used=float(m.mean()))


def per_flow_cost(X, rows, header_bytes_per_packet=0.0):
    """Packets and bytes for a set of flows.  [D3a]"""
    pk = X[rows, COL["fwd_pkts"]].astype(float) + X[rows, COL["bwd_pkts"]].astype(float)
    by = X[rows, COL["fwd_bytes"]].astype(float) + X[rows, COL["bwd_bytes"]].astype(float)
    return pk, by + header_bytes_per_packet * pk


def budget_cost(pkts, bytes_, n_flows, quantiles=(0.0, 0.5, 1.0)):
    """Cost of n_flows drawn from a pool, under EXPLICIT attacker models.  [D2a]"""
    out = {}
    for q in quantiles:
        out[q] = dict(packets=float(n_flows * np.quantile(pkts, q)),
                      bytes=float(n_flows * np.quantile(bytes_, q)))
    out["mean"] = dict(packets=float(n_flows * pkts.mean()),
                       bytes=float(n_flows * bytes_.mean()))
    out["iid_expected"] = out["mean"]
    out["typical"] = dict(packets=float(n_flows * np.median(pkts)),
                          bytes=float(n_flows * np.median(bytes_)))
    out["chosen_min"] = dict(packets=float(n_flows * pkts.min()),
                             bytes=float(n_flows * bytes_.min()))
    if n_flows <= len(bytes_):
        srt = np.sort(bytes_)[:int(n_flows)]
        idx = np.argsort(bytes_)[:int(n_flows)]
        out["chosen_sum"] = dict(packets=float(pkts[idx].sum()), bytes=float(srt.sum()))
    else:
        out["chosen_sum"] = None
    return out


def rate_and_hosts(total_bytes, window_s, host_rates_bps=(1e6, 1e7, 1e8, 1e9)):
    """Required sustained rate over a window, and hosts needed at given per-host rates."""
    bps = 8.0 * total_bytes / window_s
    return dict(bytes_per_s=float(total_bytes / window_s), bits_per_s=float(bps),
                hosts={f"{int(r):d}": math.ceil(bps / r) for r in host_rates_bps})


COL = dict(duration=1, bytes_per_s=2, pkts_per_s=3, fwd_pkts=4, bwd_pkts=5,
           fwd_bytes=6, bwd_bytes=7)


SCALES = {"seconds": 1.0, "milliseconds": 1e3, "microseconds": 1e6, "nanoseconds": 1e9}


def main():
    import numpy as np, json, math
    from pathlib import Path

    OUT = Path(__file__).resolve().parent / "out"
    OUT.mkdir(exist_ok=True)
    rng = np.random.default_rng(20260827)
    OK, FAIL = [], []


    def check(name, got, want, tol, note=""):
        ok = abs(got - want) <= tol
        (OK if ok else FAIL).append(name)
        print(f"  [{'ok ' if ok else 'FAIL'}] {name:<62} got={got:<15.9g} want={want:<15.9g} "
              f"tol={tol:.3g} {note}")
        return ok


    def check_bool(name, got, note=""):
        (OK if got else FAIL).append(name)
        print(f"  [{'ok ' if got else 'FAIL'}] {name:<62} {'holds' if got else 'VIOLATED':<15} "
              f"{note}")
        return got




    print("=" * 118)
    print("D1.  THE DURATION UNIT IS RECOVERED FROM THE FILE, NOT ASSUMED")
    print("=" * 118)
    print("""
    The file carries the totals AND the rates, which overdetermines the duration unit:

            Flow Bytes/s  ==  (fwd_bytes + bwd_bytes) / (Flow Duration / S)                [D1a]

    Only one S in {1, 1e3, 1e6, 1e9} makes that hold.  Getting S wrong scales every required-
    bandwidth number in E8 by 10^3 or 10^6 -- exactly the class of error the audit procedure
    exists to catch (docs/01_HANDOFF_PHASE4.md section 7 lists three rescaled headline numbers).
    t41 runs the recovery on the real column and ASSERTS that the winning candidate beats the
    runner-up by at least two orders of magnitude, so a near-tie is a failure rather than a
    coin flip.
    """)
    for true_name, S in SCALES.items():
        n = 20000
        dur_s = rng.uniform(1e-4, 30.0, n)
        by = rng.uniform(60, 1e6, n)
        bps = by / dur_s
        dur_col = dur_s * S
        got, tbl, cov = recover_duration_scale(dur_col, by, bps)
        ranked = sorted(tbl.items(), key=lambda kv: kv[1])
        check_bool(f"D1a  recovers '{true_name}' from synthetic columns", got == true_name,
                   note=f"runner-up {ranked[1][0]} at {ranked[1][1]:.2f} decades vs "
                        f"{ranked[0][1]:.2e}")
    dur_s = rng.uniform(1e-4, 30.0, 20000); by = rng.uniform(60, 1e6, 20000)
    _, tbl, cov0 = recover_duration_scale(dur_s * 1e6, by, by / dur_s)
    rk = sorted(tbl.values())
    check_bool("D1a  the runner-up is >= 2 decades worse", rk[1] - rk[0] >= 2.0,
               note=f"best {rk[0]:.2e}, runner-up {rk[1]:.2f}")
    noisy = (by / dur_s) * np.exp(rng.normal(0, 0.2, 20000))
    got_n, _, _ = recover_duration_scale(dur_s * 1e6, by, noisy)
    check_bool("D1a  survives 20% multiplicative noise on the rate column",
               got_n == "microseconds")
    check_bool("D1a  the survivor fraction is reported and near 1 on clean synthetic input",
               cov0["frac_used"] > 0.99, note=f"{cov0['frac_used']:.4f}")

    print("=" * 118)
    print("D2.  A BUDGET IS DRAWN FROM A POOL, SO THE MEAN IS THE WRONG SUMMARY")
    print("=" * 118)
    print("""
    The attack budgets are COUNTS OF FLOWS the attacker must generate, drawn from a pool of
    real benign traffic.  The attacker chooses which pool flows to imitate, so

            cost(n)  =  n * (a quantile of the pool's per-flow cost)                     [D2a]

    and the operationally meaningful figures are the CHEAPEST realisable attack (a low
    quantile), the typical one (the median), and the mean -- which is neither, and which
    heavy-tailed flow-size distributions pull far above the median.  Reporting only n * mean
    overstates a cost the attacker can avoid paying; reporting only n * min understates one
    they may not be able to sustain.  E8 reports the interval.
    """)
    pool = np.concatenate([rng.lognormal(6.0, 1.0, 9000), rng.lognormal(12.0, 0.5, 1000)])
    pk = np.ones_like(pool)
    b = budget_cost(pk, pool, 1_000_000, quantiles=(0.01, 0.5, 0.99))
    check("D2a  iid_expected == n * mean", b["iid_expected"]["bytes"],
          1_000_000 * float(pool.mean()), 1e-3)
    check("D2a  typical == n * median", b["typical"]["bytes"],
          1_000_000 * float(np.median(pool)), 1e-3)
    check("D2a  chosen_min == n * min", b["chosen_min"]["bytes"],
          1_000_000 * float(pool.min()), 1e-6)
    check_bool("D2a  chosen_sum is None when n exceeds the pool",
               b["chosen_sum"] is None, note=f"pool has {len(pool)} flows, budget 1e6")
    b_small = budget_cost(pk, pool, 100, quantiles=(0.5,))
    check("D2a  chosen_sum is the sum of the n cheapest", b_small["chosen_sum"]["bytes"],
          float(np.sort(pool)[:100].sum()), 1e-6)
    check_bool("D2a  and it is below n * min? no -- it is ABOVE, since min repeats",
               b_small["chosen_sum"]["bytes"] >= b_small["chosen_min"]["bytes"])
    check_bool("D2a  mean exceeds median on a heavy-tailed pool",
               b["mean"]["bytes"] > b[0.5]["bytes"],
               note=f"mean {b['mean']['bytes']:.3e} vs median {b[0.5]['bytes']:.3e}, "
                    f"ratio {b['mean']['bytes']/b[0.5]['bytes']:.1f}x")
    check_bool("D2a  the 1%-99% interval spans orders of magnitude",
               b[0.99]["bytes"] / b[0.01]["bytes"] > 100,
               note=f"{b[0.99]['bytes']/b[0.01]['bytes']:.0f}x")
    check("D2a  cost is linear in n", budget_cost(pk, pool, 2_000_000)[0.5]["bytes"],
          2.0 * budget_cost(pk, pool, 1_000_000)[0.5]["bytes"], 1e-6)

    print("=" * 118)
    print("D3.  THE BYTE FIGURE IS PAYLOAD; HEADERS ARE NOT IN THE CACHE")
    print("=" * 118)
    print("""
    `Total Length of Fwd/Bwd Packet` (columns 14-15) are payload lengths.  Header lengths are
    columns 42-43, and h_stream's cache stops at column 40, so a wire-bytes figure cannot be
    computed exactly from what is cached.  Understating it flatters the attacker, so E8 reports
    BOTH the payload figure and a payload + 40 bytes/packet figure (the TCP/IPv4 minimum
    header), and says which is which.                                                     [D3a]

    The gap matters most for the many-small-packets flows a padding attack would prefer: at a
    mean payload of 100 bytes over 2 packets, the 40-byte allowance adds 80%.
    """)
    X = np.zeros((3, 8))
    X[:, COL["fwd_pkts"]] = [1, 2, 10]
    X[:, COL["bwd_pkts"]] = [1, 0, 10]
    X[:, COL["fwd_bytes"]] = [50, 100, 5000]
    X[:, COL["bwd_bytes"]] = [50, 0, 5000]
    pk0, by0 = per_flow_cost(X, np.arange(3), 0.0)
    pk1, by1 = per_flow_cost(X, np.arange(3), 40.0)
    check("D3a  payload bytes of the worked flows", float(by0.sum()), 10200.0, 0)
    check("D3a  packets of the worked flows", float(pk0.sum()), 24.0, 0)
    check("D3a  +40 B/packet adds exactly 40*packets", float(by1.sum() - by0.sum()),
          40.0 * 24.0, 1e-9)
    check("D3a  the small-flow inflation is 80%", float(by1[1] / by1[1]) * (by1[1] / by0[1]),
          1.8, 1e-9, note="2 packets, 100 B payload -> 180 B")

    print("=" * 118)
    print("D4.  RATE AND HOSTS")
    print("=" * 118)
    print("""
            required rate  =  8 * total_bytes / window_seconds     bits per second       [D4a]
            hosts at rate R =  ceil(required rate / R)

    The window is the one the attack must fit inside: for within-episode padding that is the
    BUCKET duration (2 h = 7200 s), because pad flows must land in the same episode; for the
    ADDIS state attack it is the deployment window, because precursors only have to precede the
    target.  Using the wrong window rescales the bandwidth by the ratio of the two, so t41
    states the window with every rate it prints.                                          [D4b]
    """)
    r = rate_and_hosts(7200.0 * 1e6 / 8.0, 7200.0)
    check("D4a  1 Mbit/s round trip", r["bits_per_s"], 1e6, 1e-6)
    check("D4a  hosts at 1 Mbit/s each", r["hosts"]["1000000"], 1, 0)
    check("D4a  hosts at 1 Gbit/s each", r["hosts"]["1000000000"], 1, 0)
    r2 = rate_and_hosts(7200.0 * 1e9 / 8.0, 7200.0)
    check("D4a  hosts at 10 Mbit/s each for a 1 Gbit/s attack", r2["hosts"]["10000000"], 100, 0)
    check("D4b  the same bytes over the 26.98 h window instead of 7200 s",
          rate_and_hosts(7200.0 * 1e6 / 8.0, 26.98 * 3600)["bits_per_s"],
          1e6 * 7200.0 / (26.98 * 3600), 1e-3,
          note="a factor of 13.5 -- which is why the window must be stated")

    print("=" * 118)
    print(f"  PASSED {len(OK)} / {len(OK) + len(FAIL)} checks")
    if FAIL:
        print("  FAILED: " + ", ".join(FAIL))
    print("=" * 118)

    json.dump(dict(
        D1a="the duration unit is RECOVERED from Flow Bytes/s == total_bytes/(duration/S); "
            "the winner must beat the runner-up by >= 2 decades",
        D2a="a budget is n * a POOL QUANTILE, not n * mean; report the interval",
        D3a="Total Length of Fwd/Bwd Packet is PAYLOAD; header columns 42-43 are not cached, "
            "so report payload and payload + 40 B/packet and say which",
        D4a="required rate = 8*bytes/window_s; hosts = ceil(rate / per-host rate)",
        D4b="the window is the BUCKET for within-episode padding and the DEPLOYMENT WINDOW "
            "for the state attack -- a factor of 13.5 apart; state it with every rate",
        column_map=COL, scales=list(SCALES),
        n_passed=len(OK), n_failed=len(FAIL), failed=FAIL),
        open(OUT / "t41a_E8_derivation.json", "w"), indent=1)
    print("  wrote out/t41a_E8_derivation.json")
    if FAIL:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
