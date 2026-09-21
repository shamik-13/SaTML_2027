import numpy as np, json, time, gc
from pathlib import Path
from scipy.stats import beta, norm

import h_stream as hs

K_GRID = [1, 10, 100, 1000]
POSITIONS = [0.55, 0.62, 0.70, 0.77, 0.85]
PRIMARY = 0.55
SEED = 0
BOOT_SEED = 20260901
B = 1000                   # bootstrap replicates (percentile intervals + 1/(B+1) p-values)
CHUNK = 100                # replicates per chunk, to bound the weight matrix's memory
BUCKET = 2 * 3600
MIN_SUPPORT = 5_000        # a stratum below this many benign flows is pooled into "other"
TOP_N = 8                  # top-N services / hosts by benign support; the rest pool into "other"
ARITY_EDGES = [1, 2, 3, 6, 21, 101]        # bin lower edges: 1, 2, 3-5, 6-20, 21-100, >100
ARITY_NAMES = ["m=1", "m=2", "m=3-5", "m=6-20", "m=21-100", "m>100"]
MIN_EVENTS = 10            # below this many firing flows a cell carries no test (but still counts)
JMAX_MULT = 8              # how far down the calibration tail a resampled k-th largest can land


def cp_interval(x, n, conf=0.95):
    """Exact Clopper-Pearson interval -- valid only under INDEPENDENCE, kept for contrast."""
    if n == 0:
        return (float("nan"), float("nan"))
    a = (1.0 - conf) / 2.0
    lo = 0.0 if x == 0 else float(beta.ppf(a, x, n - x + 1))
    hi = 1.0 if x == n else float(beta.ppf(1.0 - a, x + 1, n - x))
    return lo, hi


def step_up(pvals, q, weight=1.0):
    """Generic step-up: BH when weight=1, Benjamini-Yekutieli when weight=sum_{i<=n} 1/i."""
    p = np.asarray(pvals, float)
    n = len(p)
    if n == 0:
        return np.zeros(0, bool)
    o = np.argsort(p)
    passed = p[o] <= q * (np.arange(1, n + 1) / n) / weight
    out = np.zeros(n, bool)
    if passed.any():
        out[o[:int(np.flatnonzero(passed).max()) + 1]] = True
    return out


def by_reject(pvals, q=0.05):
    """Benjamini-Yekutieli: valid under ARBITRARY dependence, which is what we have here."""
    n = len(pvals)
    return step_up(pvals, q, weight=(float(np.sum(1.0 / np.arange(1, n + 1))) if n else 1.0))


def stratify(labels, names, min_support, top_n=None, other_name="other"):
    u, c = np.unique(labels, return_counts=True)
    keep = u[c >= min_support]
    if top_n is not None and len(keep) > top_n:
        keep = keep[np.argsort(-c[np.isin(u, keep)])[:top_n]]
    keep = set(int(v) for v in keep)
    out_lab = np.where(np.isin(labels, sorted(keep)) if keep else np.zeros(len(labels), bool),
                       labels, -1)
    disp = {int(v): names(int(v)) for v in np.unique(out_lab) if int(v) != -1}
    disp[-1] = other_name
    return out_lab, disp


def bucket_strata(bkt):

    _, code = np.unique(bkt, return_inverse=True)
    return code


class Bootstrapper:


    def __init__(self, cal_scores, cal_cl, scores, cl, n_clusters, rng,
                 k_grid=K_GRID, b=B, chunk=CHUNK, top_m=None):
        self.scores = scores
        self.cl = cl
        self.G = int(n_clusters)
        self.b, self.chunk, self.k_grid = b, chunk, k_grid
        self._chunks = [(x, min(x + chunk, b)) for x in range(0, b, chunk)]

        top_m = top_m or (max(k_grid) * JMAX_MULT + 1024)
        o = np.argsort(cal_scores)[::-1][:top_m]
        self.cal_top = cal_scores[o]                       # descending
        cal_top_cl = cal_cl[o]
        _, self.cal_top_cl = np.unique(cal_top_cl, return_inverse=True)
        self.n_cal_cl = int(self.cal_top_cl.max()) + 1
        self.top_m = len(o)
        self._cal_rng = rng
        self.P = self._draw_calibration()                  # {k: array of positions into cal_top}

    def _draw_calibration(self):
        """Per replicate and depth, the position in the descending calibration tail that the
        resample's k-th largest score lands on."""
        out = {k: np.empty(self.b, np.int64) for k in self.k_grid}
        for lo, hi in self._chunks:
            Wc = self._cal_rng.poisson(1.0, size=(hi - lo, self.n_cal_cl))
            mult = Wc[:, self.cal_top_cl]                  # multiplicity of each tail score
            cs = np.cumsum(mult, axis=1)
            for k in self.k_grid:
                hit = cs >= k
                assert hit.any(axis=1).all(), (
                    f"calibration tail of {self.top_m} scores too short for k={k}")
                out[k][lo:hi] = np.argmax(hit, axis=1)
            del Wc, mult, cs
        return out

    def _weights(self, lo, hi):

        return np.random.default_rng(BOOT_SEED + 977 * lo).poisson(
            1.0, size=(hi - lo, self.G)).astype(np.float64)

    def _prep(self, sel):
        s = self.scores[sel]; c = self.cl[sel]
        o = np.argsort(s, kind="stable")
        n_g = np.bincount(c, minlength=self.G).astype(np.float64)
        return s[o], c[o], n_g

    def _point_index(self, k):
        return k - 1

    def run(self, sel, k):
        s_sorted, cl_sorted, n_g = self._prep(sel)
        n = len(s_sorted)
        fires = {}
        for P in np.unique(self.P[k]):
            cnt = n - int(np.searchsorted(s_sorted, self.cal_top[int(P)], side="right"))
            fires[int(P)] = cl_sorted[n - cnt:] if cnt else cl_sorted[:0]
        rate = np.empty(self.b)
        for lo, hi in self._chunks:
            W = self._weights(lo, hi)
            den = W @ n_g
            Pc = self.P[k][lo:hi]
            num = np.zeros(hi - lo)
            for P in np.unique(Pc):
                rows = np.flatnonzero(Pc == P)
                f = fires[int(P)]
                if f.size:
                    num[rows] = W[np.ix_(rows, f)].sum(axis=1)
            rate[lo:hi] = np.divide(num, den, out=np.zeros_like(num), where=den > 0)
            del W
        tau0 = self.cal_top[self._point_index(k)]
        x = n - int(np.searchsorted(s_sorted, tau0, side="right"))
        return rate, x, n

    def test_only(self, sel, k):
        s_sorted, cl_sorted, n_g = self._prep(sel)
        n = len(s_sorted)
        cnt = n - int(np.searchsorted(s_sorted, self.cal_top[self._point_index(k)], side="right"))
        x_g = (np.bincount(cl_sorted[n - cnt:], minlength=self.G).astype(np.float64)
               if cnt else np.zeros(self.G))
        rate = np.empty(self.b)
        for lo, hi in self._chunks:
            W = self._weights(lo, hi)                       # SAME weights as run()
            den = W @ n_g
            num = W @ x_g
            rate[lo:hi] = np.divide(num, den, out=np.zeros_like(num), where=den > 0)
            del W
        return rate


def boot_pvalue(reps, null_value, x, point):
    if x < MIN_EVENTS or point <= 0 or null_value <= 0:
        return 1.0, False
    with np.errstate(divide="ignore", invalid="ignore"):
        lg = np.log(reps[reps > 0])
    if lg.size < 0.9 * len(reps) or not np.isfinite(lg).all():
        return 1.0, False                       # too many degenerate replicates to approximate
    sd = float(lg.std(ddof=1))
    if not np.isfinite(sd) or sd <= 0:
        return 1.0, False
    return float(norm.sf((np.log(point) - np.log(null_value)) / sd)), True


def summarise(rate, nom, x, n, conf=0.95):
    """Percentile interval and one-sided p-value for a replicate rate vector."""
    a = (1.0 - conf) / 2.0
    lo, hi = np.percentile(rate, [100 * a, 100 * (1 - a)])
    pv, est = boot_pvalue(rate, nom, x, (x / n) if n else 0.0)
    cl_lo, cl_hi = cp_interval(x, n)
    return dict(x=int(x), expected=float(n * nom), ratio=float((x / n) / nom) if n else float("nan"),
                ci=[float(lo / nom), float(hi / nom)],
                ci_iid=[float(cl_lo / nom), float(cl_hi / nom)],
                p_one_sided=float(min(pv, 1.0)), estimable=bool(est),
                ci_excludes_one=bool(lo / nom > 1.0))


def main(smoke=False):
    t0 = time.time()
    Path("out").mkdir(exist_ok=True)
    X, y, ts, src, dst = hs.load()
    N = len(y)
    dport_all = hs.load_extra("dport")
    positions = [PRIMARY] if smoke else POSITIONS

    all_rows, per_pos = [], []
    for pos in positions:
        i1, i2, i3 = hs.split_indices(N, pos)
        y_cal, y_te = y[i1:i2], y[i2:i3]
        ts_w, src_w, dst_w = ts[i2:i3], src[i2:i3], dst[i2:i3]
        dp_w = dport_all[i2:i3]
        pr_w = np.asarray(X[i2:i3, 0]).astype(np.int64)

        score = hs.fit_detector(X, y, i1, seed=SEED, kind="hgb", verbose=False)
        s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)
        cal = np.sort(s_cal[y_cal == 0]); NC = len(cal)

        ep = hs.build_episodes(np.zeros(len(y_te)), y_te, ts_w, src_w, dst_w, BUCKET, "src-dst")
        gid = ep["gid"]; T = ep["T"]
        arity_per_group = np.bincount(gid, minlength=T)
        mal_per_group = np.bincount(gid, weights=y_te.astype(float), minlength=T)
        sel_idx = np.flatnonzero((y_te == 0) & (mal_per_group[gid] == 0))
        n_ben_all = int((y_te == 0).sum())
        s_sel = s_te[sel_idx]

        rk = 1 + (NC - np.searchsorted(cal, s_sel, side="left"))

        for _k in K_GRID:
            assert int((rk <= _k).sum()) == int((s_sel > cal[NC - _k]).sum()), \
                f"rank/threshold mismatch at k={_k}"

        pair = (src_w[sel_idx].astype(np.int64) * (int(dst_w.max()) + 1)
                + dst_w[sel_idx].astype(np.int64))
        _, cl = np.unique(pair, return_inverse=True)
        G = int(cl.max()) + 1

        cben = np.flatnonzero(y_cal == 0)
        cpair = (src[i1:i2][cben].astype(np.int64) * (int(dst_w.max()) + 1)
                 + dst[i1:i2][cben].astype(np.int64))
        _, cal_cl = np.unique(cpair, return_inverse=True)
        boot = Bootstrapper(s_cal[cben], cal_cl, s_sel, cl, G,
                            np.random.default_rng(BOOT_SEED + int(pos * 1000)))
        arity = arity_per_group[gid][sel_idx]
        abin = np.searchsorted(ARITY_EDGES, arity, side="right") - 1
        a_strat, a_disp = stratify(abin, lambda c: ARITY_NAMES[c], min_support=1)
        svc = pr_w[sel_idx] * 100000 + dp_w[sel_idx].astype(np.int64)
        s_strat, s_disp = stratify(svc, lambda c: f"proto {c//100000}/port {c%100000}",
                                   MIN_SUPPORT, TOP_N)
        tcode = bucket_strata(ts_w[sel_idx] // (BUCKET * 1_000_000))
        n_bkt = int(tcode.max()) + 1
        t_strat, t_disp = stratify(tcode, lambda c: f"bucket {c+1}/{n_bkt}", min_support=1)
        h_strat, h_disp = stratify(dst_w[sel_idx], lambda c: f"dst host {c}", MIN_SUPPORT, TOP_N)

        allmask = np.ones(len(sel_idx), bool)
        marg_rate, marg = {}, {}
        for k in K_GRID:
            nom = k / (NC + 1.0)
            r, x, n = boot.run(allmask, k)
            marg_rate[k] = r
            marg[f"k{k}"] = summarise(r, nom, x, n)
            marg[f"k{k}"]["ci_test_only"] = [
                float(v / nom) for v in np.percentile(boot.test_only(allmask, k), [2.5, 97.5])]

        rows = []
        for fam, st, dp in (("arity", a_strat, a_disp), ("service", s_strat, s_disp),
                            ("bucket", t_strat, t_disp), ("host", h_strat, h_disp)):
            for code in sorted(dp, key=lambda c: (c == -1, c)):
                sel = st == code
                if not sel.any():
                    continue
                row = dict(family=fam, pos=pos, stratum=dp[code], code=int(code),
                           n=int(sel.sum()), n_clusters=int(np.unique(cl[sel]).size))
                for k in K_GRID:
                    nom = k / (NC + 1.0)
                    r, x, n = boot.run(sel, k)
                    cell = summarise(r, nom, x, n)
                    cell["ci_test_only"] = [float(v / nom) for v in
                                            np.percentile(boot.test_only(sel, k), [2.5, 97.5])]

                    mr = marg_rate[k]
                    mratio_k = marg[f"k{k}"]["ratio"]
                    ok = mr > 0
                    con = np.divide(r, mr, out=np.zeros_like(r), where=ok)[ok]
                    if con.size:
                        clo, chi = np.percentile(con, [2.5, 97.5])
                        cpv, cest = boot_pvalue(
                            con, 1.0, x,
                            (cell["ratio"] / mratio_k) if mratio_k > 0 else 0.0)
                    else:
                        clo = chi = float("nan"); cpv, cest = 1.0, False
                    cell["contrast"] = (float(cell["ratio"] / mratio_k)
                                        if mratio_k > 0 else float("nan"))
                    cell["contrast_ci"] = [float(clo), float(chi)]
                    cell["contrast_p"] = float(min(cpv, 1.0))
                    cell["contrast_estimable"] = bool(cest)
                    cell["contrast_ci_excludes_one"] = bool(clo > 1.0)
                    row[f"k{k}"] = cell
                rows.append(row)
        all_rows += rows

        pv = np.array([r[f"k{k}"]["p_one_sided"] for r in rows for k in K_GRID])
        ar = {r["stratum"]: {f"k{k}": r[f"k{k}"]["ratio"] for k in K_GRID}
              for r in rows if r["family"] == "arity"}
        per_pos.append(dict(
            pos=pos, NC=int(NC), n_benign_all=n_ben_all, n_benign_truenull=int(len(rk)),
            n_truenull_groups=int((mal_per_group == 0).sum()), n_groups=int(T), n_clusters=G,
            n_strata=len(rows), n_cells=int(len(pv)),
            n_tested=int(sum(1 for r in rows for k in K_GRID if r[f"k{k}"]["estimable"])),
            n_flag_raw=int((pv <= 0.05).sum()), marginal=marg, arity_ratio_by_bin=ar))
        print(f"  pos={pos}  |C|={NC:,}  true-null benign={len(rk):,} of {n_ben_all:,}  "
              f"clusters={G:,}  strata={len(rows)}  [{time.time()-t0:.0f}s]")
        print(f"      {'marginal':<10} n={len(rk):>9,}  " + "  ".join(
            f"k={k}: {marg[f'k{k}']['ratio']:>6.2f} "
            f"[{marg[f'k{k}']['ci'][0]:.2f},{marg[f'k{k}']['ci'][1]:.2f}]" for k in K_GRID))
        for r in rows:
            if r["family"] == "arity":
                print(f"      {r['stratum']:<10} n={r['n']:>9,}  " + "  ".join(
                    f"k={k}: {r[f'k{k}']['ratio']:>6.2f} "
                    f"[{r[f'k{k}']['ci'][0]:.2f},{r[f'k{k}']['ci'][1]:.2f}]"
                    f"(c{r[f'k{k}']['contrast']:.1f})" for k in K_GRID))
        del s_cal, s_te, cal, score, boot
        gc.collect()

    flat = flat_all = [(r, k) for r in all_rows for k in K_GRID]
    n_untestable = sum(1 for r, k in flat_all if not r[f"k{k}"]["estimable"])
    n_low_events = sum(1 for r, k in flat_all if r[f"k{k}"]["x"] < MIN_EVENTS)
    pv_all = np.array([r[f"k{k}"]["p_one_sided"] for r, k in flat])
    cflat = flat_all
    cpv_all = np.array([r[f"k{k}"]["contrast_p"] for r, k in cflat])
    bh_all, by_all = step_up(pv_all, 0.05), by_reject(pv_all, 0.05)
    by_contrast = by_reject(cpv_all, 0.05)

    def pack(mask, use_contrast=False):
        src = cflat if use_contrast else flat
        return [dict(family=r["family"], pos=r["pos"], stratum=r["stratum"], k=k, n=r["n"],
                     ratio=r[f"k{k}"]["ratio"], ci=r[f"k{k}"]["ci"],
                     contrast=r[f"k{k}"]["contrast"], contrast_ci=r[f"k{k}"]["contrast_ci"],
                     p=r[f"k{k}"]["contrast_p" if use_contrast else "p_one_sided"])
                for (r, k), m in zip(src, mask) if m]

    flagged_by, flagged_bh = pack(by_all), pack(bh_all)
    flagged_contrast = pack(by_contrast, use_contrast=True)
    clean = sorted({p["pos"] for p in per_pos} - {f["pos"] for f in flagged_by})
    clean_c = sorted({p["pos"] for p in per_pos} - {f["pos"] for f in flagged_contrast})
    k1 = [f for f in flagged_by if f["k"] == 1]
    k1c = [f for f in flagged_contrast if f["k"] == 1]
    for pp in per_pos:
        pp["n_flag_by"] = sum(1 for f in flagged_by if f["pos"] == pp["pos"])
        pp["n_flag_bh"] = sum(1 for f in flagged_bh if f["pos"] == pp["pos"])
        pp["n_flag_contrast"] = sum(1 for f in flagged_contrast if f["pos"] == pp["pos"])
        pp["n_flag_by_k1"] = sum(1 for f in flagged_by if f["pos"] == pp["pos"] and f["k"] == 1)
        pp["n_flag_contrast_k1"] = sum(1 for f in flagged_contrast
                                       if f["pos"] == pp["pos"] and f["k"] == 1)

    out = dict(
        config=dict(positions=positions, seed=SEED, boot_seed=BOOT_SEED, B=B, k_grid=K_GRID,
                    bucket_s=BUCKET, min_support=MIN_SUPPORT, top_n=TOP_N,
                    arity_edges=ARITY_EDGES, min_events=MIN_EVENTS, tie_rule="side='left' (ranks ties conservatively)",
                    population="benign flows of TRUE-NULL (all-benign) episodes",
                    cluster="src-dst host pair (coarser than the episode)",
                    interval="JOINT bootstrap: calibration tail order statistic (shared across a "
                             "window's strata) x Poisson multiplier over clusters",
                    correction="Benjamini-Yekutieli (arbitrary dependence) as headline; BH as the "
                               "optimistic reading"),
        per_position=per_pos, rows=all_rows,
        multiplicity=dict(
            n_cells=len(flat_all), n_tests=int(len(flat_all) - n_untestable),
            n_untestable=int(n_untestable), n_low_events=int(n_low_events),
            min_events=MIN_EVENTS,
            n_cells_ci_excludes_one=int(sum(r[f"k{k}"]["ci_excludes_one"] for r, k in flat_all)),
            n_flag_raw=int((pv_all <= 0.05).sum()),
            n_contrast_tests=int(len(cpv_all)),
            n_flag_by=int(by_all.sum()), n_flag_bh=int(bh_all.sum()),
            expected_raw_by_chance=float(0.05 * (len(flat_all) - n_untestable)),
            n_flag_by_at_k1=len(k1), flagged_by=flagged_by,
            n_flag_contrast_by=int(by_contrast.sum()), n_flag_contrast_at_k1=len(k1c),
            n_flag_contrast_excl_bucket=int(sum(1 for f in flagged_contrast
                                                if f["family"] != "bucket")),
            windows_contrast_excl_bucket=sorted({f["pos"] for f in flagged_contrast
                                                 if f["family"] != "bucket"}),
            flagged_contrast=flagged_contrast),
        windows_with_no_by_flag=clean, windows_with_no_contrast_flag=clean_c,
        note=("Metadata-stratified interrogation of Assumption 1 (review 6, item R5).  Population: "
              "benign flows of TRUE-NULL episodes.  Estimand per stratum s and depth k: "
              "Pr_hat(K<=k|s)/(k/(|C|+1)).  Intervals come from a JOINT bootstrap of BOTH sources of "
              "uncertainty: the shared calibration tail (Poisson(1) multiplicities on cal's order "
              "statistics, one draw per replicate SHARED across a window's strata, since they really "
              "do share one calibration set) and the test side (Poisson multiplier bootstrap over "
              "src-dst host-pair clusters).  `ci_test_only` and `ci_iid` retain the narrower, wrong "
              "intervals for comparison.  The CONTRAST -- a stratum's rate against its own window's "
              "marginal on the same replicates -- is the quantity that speaks to the CONDITIONAL "
              "statement, because a shared calibration draw largely cancels in it.  Multiplicity is "
              "corrected with BENJAMINI-YEKUTIELI (valid under arbitrary dependence); BH is the "
              "optimistic reading.  Ranks use side='left', so every ratio is a LOWER bound on the "
              "anti-conservatism.  This CANNOT prove conditional exchangeability given M_j, and a "
              "departure at k=1000 is compatible with a valid rank-1 rate (the excess may sit in "
              "ranks 2..1000), so the paper's conclusions remain stated UNDER Assumption 1."))
    json.dump(out, open("out/t55_a1_strata.json", "w"), indent=1, allow_nan=True)
    m = out["multiplicity"]
    print(f"\n  {m['n_cells']} cells, {m['n_untestable']} carrying no test "
          f"({m['n_low_events']} of them firing <{MIN_EVENTS} times); {m['n_tests']} tested: "
          f"{m['n_flag_raw']} raw (chance {m['expected_raw_by_chance']:.1f}), "
          f"{m['n_flag_by']} survive Benjamini-Yekutieli over ALL {m['n_cells']} cells, "
          f"{m['n_flag_bh']} survive BH; {m['n_flag_by_at_k1']} of the BY survivors at k=1")
    print(f"  CONTRAST vs the window's own marginal: {m['n_flag_contrast_by']} survive BY "
          f"({m['n_flag_contrast_at_k1']} at k=1); windows with none: {clean_c}")
    print(f"    sensitivity, excluding the bucket family (the one confounded with a time-block "
          f"shock the host-pair clustering cannot absorb): {m['n_flag_contrast_excl_bucket']} "
          f"at windows {m['windows_contrast_excl_bucket']}")
    print(f"  windows with no BY-surviving stratum (raw ratio): {clean}")
    print(f"  [{time.time()-t0:.0f}s]  wrote out/t55_a1_strata.json")
    return out


if __name__ == "__main__":
    main()
