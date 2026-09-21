import json
import math
import statistics
from pathlib import Path

if not __debug__:
    raise SystemExit(f"{__file__} must not run under `python -O`: assertions are its checks")

RES = Path(__file__).resolve().parent / "out"            
OUTDIR = Path(__file__).resolve().parents[1] / "tables" 
_WRITTEN = []


def load(name):
    with open(RES / f"{name}.json") as f:
        return json.load(f)


# --- formatting helpers ----------------------------------------------------------------
def ci(n):
    """Integer with comma thousands separator, TEXT mode (e.g. 1,813,113)."""
    return f"{int(round(n)):,}"


def cm(n):
    """Integer with {,} thousands separator, MATH mode (e.g. 1{,}813{,}113)."""
    return f"{int(round(n)):,}".replace(",", "{,}")


def f3(x):
    """Rate/recall/FDP: 3 decimals."""
    if x is None:
        return "--"
    return f"{x:.3f}"


def f2(x):
    """Ratio: 2 decimals."""
    if x is None:
        return "--"
    return f"{x:.2f}"


def signed3(x):
    """Signed margin in math mode, 3 decimals: $+0.067$ / $-0.637$."""
    if x is None:
        return "--"
    return f"${'+' if x >= 0 else '-'}{abs(x):.3f}$"


def pct1(x):
    """Fraction -> percent, 1 decimal, with \\% (e.g. 0.901 -> 90.1\\%)."""
    if x is None:
        return "--"
    return f"{x*100:.1f}\\%"


def num_or(x, formatter, dash="--"):
    return dash if x is None else formatter(x)


def half_up(x):
    """Round half up to nearest integer (int(x+0.5)); pass through None."""
    return None if x is None else int(x + 0.5)


def med_int(vals):
    """Median of a list; render as int if whole, else 1 decimal."""
    m = statistics.median(vals)
    return str(int(m)) if abs(m - round(m)) < 1e-9 else f"{m:.1f}"


def sci(x, sig=2):
    """Scientific notation in math mode: 4.4e-07 -> 4.4\\times10^{-7}."""
    if x is None or x == 0:
        return "0"
    exp = int(math.floor(math.log10(abs(x))))
    mant = x / (10 ** exp)
    return f"{mant:.{sig-1}f}\\times10^{{{exp}}}"


def human_bytes(b):
    """Bytes -> short human string with unit (B/KB/MB/GB), for table cells."""
    if b is None:
        return "--"
    for unit, div in (("GB", 1e9), ("MB", 1e6), ("KB", 1e3)):
        if b >= div:
            return f"{b/div:.1f}\\,{unit}"
    return f"{int(round(b))}\\,B"


def human_rate(bps):
    """bit/s -> bit/s or Mbit/s depending on magnitude."""
    if bps is None:
        return "--"
    if bps >= 1e6:
        return f"{bps/1e6:.1f}\\,Mbit/s"
    return f"{bps:.1f}\\,bit/s"


FF_LABEL = (
    r"All counts here use the \textbf{first-flow} within-bucket order, the optimistic upper "
    r"bound over the orders we audit, not the canonical metadata-hash order \cref{tab:main} "
    r"reports (\cref{apptab:ordering}); the order shifts detections and the level an alert "
    r"fires at, and shifts nothing else."
)


def write(key, body):
    out = Path(OUTDIR)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{key}.tex"
    path.write_text(body if body.endswith("\n") else body + "\n")
    _WRITTEN.append(path)
    print(f"  wrote {path.name}  ({len(body)} bytes)")


def write_prose(key, body):
    """ROUND 26.  A prose companion to a table: the definitions and the reading that used to sit in a
    300--550-word caption, written as ordinary appendix text and \\input by satml.tex immediately
    before the table's own \\input.  The numbers stay artefact-derived because the prose is generated
    here, next to the table it explains.  Not a table: it carries no caption and no label of the
    (app)tab kind, so the t61 order registry does not (and must not) list it."""
    write(key, body)


# =======================================================================================
# 1. detection  [table*]  src=t21c_H6_positions.json
#    Filter e-LOND, gamma=poly; all 10 (pos x seed) rows.  |C| == NC.  silent as %.
# =======================================================================================
def t_detection():
    d = load("t21c_H6_positions")
    rows = [r for r in d["rows"] if r["proc"] == "e-LOND" and r["gamma"] == "poly"]
    rows.sort(key=lambda r: (r["pos"], r["seed"]))
    lines = []
    for r in rows:
        lines.append(
            f"{r['pos']:.2f} & {r['seed']} & {f3(r['auroc'])} & {ci(r['T'])} & "
            f"{ci(r['NC'])} & {signed3(r['margin'])} & {r['rejections']} & "
            f"{f3(r['recall'])} & {pct1(r['silent'])} \\\\"
        )
    body = r"""\begin{table*}[t]
\centering
\caption{e-LOND ($\gamma\propto j^{-1.6}$) across five window positions and two detector
seeds, two-hour host-pair grouping. The margin is seed-independent by construction;
$\lvert C\rvert$ is the calibration size $\nCal$. ``silent'' is the fraction of steps at which the
controller is \emph{structurally infeasible} --- the offered level $\alpha_t$ has fallen below
$1/\ceil$, so no rejection is possible even at the maximal admissible evidence $\ceil$ (it is
\emph{not} the fraction of steps without a rejection). All counts here use the \textbf{first-flow} within-bucket order, the optimistic upper bound over the orders we audit, not the canonical metadata-hash order \cref{tab:main} reports (\cref{apptab:ordering}); the order shifts detections and the level an alert fires at, and shifts nothing else.}
\label{apptab:detection}
\begin{tabular}{rrrrrrrrr}
\toprule
Position & Seed & AUROC & $T$ & $\lvert C\rvert$ & margin & rejections & recall & silent \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table*}"""
    write("detection", body)


# =======================================================================================
# 2. procmatrix  [table*]  src=t21c_H6_positions.json
# =======================================================================================
def t_procmatrix():
    d = load("t21c_H6_positions")
    procs = ["LOND", "e-LOND", "LORD++", "SAFFRON", "ADDIS", "online e-BH"]
    gammas = [("poly", r"$\propto j^{-1.6}$"), ("uniform", "uniform")]
    lines = []
    for proc in procs:
        for gk, gl in gammas:
            sub = [r for r in d["rows"] if r["proc"] == proc and r["gamma"] == gk]
            rej = [r["rejections"] for r in sub]
            rec = [r["recall"] for r in sub]
            lines.append(
                f"{proc} & {gl} & {min(rej)} & {med_int(rej)} & {max(rej)} & "
                f"{f3(min(rec))} & {f3(statistics.median(rec))} & {f3(max(rec))} \\\\"
            )
    body = r"""\begin{table*}[t]
\centering
\caption{Procedure power over five positions $\times$ two seeds (min / median / max),
two-hour grouping. All counts here use the \textbf{first-flow} within-bucket order, the optimistic upper bound over the orders we audit, not the canonical metadata-hash order \cref{tab:main} reports (\cref{apptab:ordering}); the order shifts detections and the level an alert fires at, and shifts nothing else. The \emph{uniform} rows are the horizon-uniform $\gamma$, an \oracle{} that must know $T$ in advance (\cref{tab:terms}).}
\label{apptab:procmatrix}
\begin{tabular}{llrrrrrr}
\toprule
 & & \multicolumn{3}{c}{rejections} & \multicolumn{3}{c}{recall} \\
\cmidrule(lr){3-5}\cmidrule(lr){6-8}
Procedure & $\gamma$ & min & med & max & min & med & max \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table*}"""
    write("procmatrix", body)


# =======================================================================================
# 3. grouping  [table]  src=t26_H4_5pos.json
# =======================================================================================
def t_grouping():
    d = load("t26_H4_5pos")
    fam_order = ["src-dst", "src", "dst", "subnet24", "src-dport"]
    buckets = [(300, "300\\,s (5\\,m)"), (7200, "7200\\,s (2\\,h)"), (None, "none")]
    idx = {(r["family"], r["bucket_s"]): r for r in d["rows"]
           if r["seed"] == 0 and r["pos"] == 0.55}
    lines = []
    for fam in fam_order:
        for bk, bl in buckets:
            r = idx.get((fam, bk))
            if r is None:
                continue
            # dagger goes INSIDE the math group to avoid a "$$" (display-math) adjacency
            m = r["margin"]
            mark = "" if r["feasible"] else r"^{\dagger}"
            margin_cell = f"${'+' if m >= 0 else '-'}{abs(m):.3f}{mark}$"
            lines.append(
                f"{fam} & {bl} & {margin_cell} & "
                f"{f3(r['elond_recall'])} & {f3(r['flow_cov_elond'])} \\\\"
            )
    body = r"""\begin{table}[t]
\centering
\caption{Grouping families at the primary window (0.55, seed 0); flow coverage is
window-specific. The margin column is the \emph{level-$w_0$} feasibility margin (\cref{eq:margin});
the recall and coverage columns are e-LOND under the horizon-uniform \oracle\ $\gamma$, whose
cold-start coefficient is $\alpha = 2w_0$. $^{\dagger}$ marks a \emph{negative level-$w_0$ margin};
e-LOND can still fire there when that margin exceeds $-\tfrac12$ (its own $\alpha = 2w_0$
cold-start bound), which is why some daggered rows carry non-zero recall/coverage --- a row is $0$
only when e-LOND is itself infeasible. Feasibility and detection are thus not the same condition
(cf.\ \cref{tab:main}). All counts here use the \textbf{first-flow} within-bucket order, the optimistic upper bound over the orders we audit, not the canonical metadata-hash order \cref{tab:main} reports (\cref{apptab:ordering}).}
\label{apptab:grouping}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{llrrr}
\toprule
Family & bucket & margin & episode recall & flow coverage \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}}
\end{table}"""
    write("grouping", body)


# =======================================================================================
# 4. qsweep  [table]  src=t24_H3.json
#    lever[q] = {poly:[min,med,max], uniform:[min,med,max]} of e-LOND recall.
#    margin_scaling[q] gives ratio (margin+1)/base and predicted (q/0.05).
# =======================================================================================
def t_qsweep():
    d = load("t24_H3")
    lever = {row["q"]: row for row in d["lever"]}
    scale = {row["q"]: row for row in d["margin_scaling"]}
    qs = [0.01, 0.05, 0.10, 0.20]
    lines = []
    for q in qs:
        lv = lever[q]
        sc = scale.get(q, {})
        lines.append(
            f"{q:.2f} & {f3(lv['poly'][1])} & {f3(lv['uniform'][1])} & "
            f"{f2(sc.get('ratio'))} & {f2(sc.get('predicted'))} \\\\"
        )
    body = r"""\begin{table}[t]
\centering
\caption{Error target $q$ vs the spending sequence (median episode recall). Feasibility
scales linearly in $q$: the measured $(\text{margin}+1)/\text{base}$ ratio tracks the
prediction $q/0.05$. All counts here use the \textbf{first-flow} within-bucket order, the optimistic upper bound over the orders we audit, not the canonical metadata-hash order \cref{tab:main} reports (\cref{apptab:ordering}); the order shifts detections and the level an alert fires at, and shifts nothing else. The \emph{uniform} column are the horizon-uniform $\gamma$, an \oracle{} that must know $T$ in advance (\cref{tab:terms}).}
\label{apptab:qsweep}
\begin{tabular}{rrrrr}
\toprule
 & \multicolumn{2}{c}{median recall} & \multicolumn{2}{c}{$(\text{margin}+1)$ ratio} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}
$q$ & poly & uniform & measured & predicted \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}"""
    write("qsweep", body)


# =======================================================================================
# 5. transfer  [table]  src=t39_E6.json
#    Per-ordered-pair E6a (previous-window) normalised regret rho for the cap axis and the
#    grouping axis, seed 0 (the JSON has per-fold data).  rho = (oracle-achieved)/spread in
#    [0,1]; a flat fold has rho undefined (transfer_defined=false) and is shown as ``--''.
#    Summary rows give the worst rho for E6a and for E6b (leave-one-out).  The oracle
#    window-to-window variation reproduced by the task (~0.676) is max-min of the grouping
#    axis oracle across windows (t39_E6_transfer.py's [D2a] line); cap's is much smaller.
# =======================================================================================
def t_transfer():
    d = load("t39_E6")

    def rho_by_pair(node):
        out = {}
        for e in node["E6a"]:
            key = (e["select_pos"], e["eval_pos"])
            out[key] = e["rho"] if e.get("transfer_defined", True) else None
        return out

    cap = d["cap"]["0"]
    grp = d["grouping"]["0"]
    cap_pairs = rho_by_pair(cap)
    grp_pairs = rho_by_pair(grp)
    pairs = sorted(cap_pairs.keys())

    def worst(node, mode):
        rs = [e["rho"] for e in node[mode]
              if e["rho"] is not None and e.get("transfer_defined", True)]
        return max(rs) if rs else None

    def variation(node):
        ov = [w["oracle"] for w in node["per_window"]]
        return max(ov) - min(ov)

    # rho is a normalised regret in [0,1]; show 3 decimals to preserve the headline
    # precision the task asks to reproduce (cap 0.070, grouping 0.991, variation 0.676).
    lines = []
    for (sp, ep) in pairs:
        lines.append(
            f"${sp:.2f} \\to {ep:.2f}$ & {f3(cap_pairs[(sp, ep)])} & "
            f"{f3(grp_pairs[(sp, ep)])} \\\\"
        )
    body = r"""\begin{table}[t]
\centering
\caption{Cross-window configuration transfer: the cap transfers, the grouping does not.
Each cell is the previous-window normalised regret $\rho\in[0,1]$ (0 = oracle,
1 = worst feasible config) on the evaluation window, seed 0; ``--'' is a flat selection
window where transfer is undefined. The grouping axis is not flat --- its oracle flow
coverage varies by """ + f3(variation(grp)) + r""" across windows (cap: """ + f3(variation(cap)) + r""") ---
yet the frozen grouping still fails to transfer. All counts here use the \textbf{first-flow} within-bucket order, the optimistic upper bound over the orders we audit, not the canonical metadata-hash order \cref{tab:main} reports (\cref{apptab:ordering}).}
\label{apptab:transfer}
\begin{tabular}{lrr}
\toprule
 & \multicolumn{2}{c}{normalised regret $\rho$} \\
\cmidrule(lr){2-3}
Transfer fold (select $\to$ eval) & cap axis & grouping axis \\
\midrule
""" + "\n".join(lines) + r"""
\midrule
worst (previous-window sel.)  & \textbf{""" + f3(worst(cap, "E6a")) + r"""} & \textbf{""" + f3(worst(grp, "E6a")) + r"""} \\
worst (leave-one-out)         & """ + f3(worst(cap, "E6b")) + r""" & """ + f3(worst(grp, "E6b")) + r""" \\
\bottomrule
\end{tabular}
\end{table}"""
    write("transfer", body)


# =======================================================================================
# 6. smoothing  [table]  src=t34_E1_smoothed.json
#    pos 0.55, dseed 0, proc LOND, gamma poly.  Baseline = discrete mean-e (18.0).
#    Smoothed route (smoothA) merges {simes, hommel, bonf-p} (mean-e is not defined on the
#    smoothed route in the JSON, only on discrete).  Rejections: mean +- sd when n_seeds>1.
#    Reliable = pdet_mal.n_ge_090; any-detected = pdet_mal.n_gt_000.
# =======================================================================================
def t_smoothing():
    d = load("t34_E1_smoothed")
    base = [r for r in d["rows"] if r["pos"] == 0.55 and r["dseed"] == 0
            and r["proc"] == "LOND" and r["gamma"] == "poly"]
    # desired display order: discrete mean-e baseline, then smoothed simes/hommel/bonf-p
    order = [("discrete", "mean-e"), ("smoothA", "simes"),
             ("smoothA", "hommel"), ("smoothA", "bonf-p")]
    idx = {(r["route"], r["merge"]): r for r in base}
    route_label = {"discrete": "discrete", "smoothA": "smoothed"}
    lines = []
    for route, merge in order:
        r = idx.get((route, merge))
        if r is None:
            continue
        rj, pd = r["rejections"], r["pdet_mal"]
        if r["n_seeds"] > 1:
            rejcell = f"${rj['mean']:.1f}\\pm{rj['sd']:.1f}$"
        else:
            rejcell = f"{rj['mean']:.1f}"
        lines.append(
            f"{merge} & {route_label[route]} & {rejcell} & "
            f"{pd['n_ge_090']} & {pd['n_gt_000']} \\\\"
        )
    body = r"""\begin{table}[t]
\centering
\caption{Randomised smoothing at the primary window (LOND, $\gamma\propto j^{-1.6}$,
position 0.55, seed 0): removing the floor adds no reliable detection that survives the
merge choice. Rejections are mean $\pm$ SD over 100 randomisation draws where applicable;
``reliable'' is the number of malicious episodes detected with probability $\ge 0.9$,
``any'' with probability $>0$. """ + FF_LABEL + r"""}
\label{apptab:smoothing}
\begin{tabular}{llrrr}
\toprule
merge & route & rejections & reliable & any \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}"""
    write("smoothing", body)


# =======================================================================================
# 7. restart  [table]  src=t35_E2_restart.json
#    W1 guarantee, LOND.  E2b == index reset under a pre-committed allocation summing to q
#    (alloc uniform/geometric, alpha_total=q); E2c == budget reset (alloc per-epoch,
#    alpha_total = n*q).  Grouping width is matched to the epoch (grp_h == epoch_h) for the
#    restart arms.  Rows are deduplicated (the raw JSON repeats some configs).  The oracle
#    uninterrupted comparison uses the horizon-uniform gamma (uniform[ORACLE], no restart).
# =======================================================================================
def t_restart():
    d = load("t35_E2_restart")
    rows = [r for r in d["rows"] if r["window"].startswith("W1") and r["proc"] == "LOND"]

    def get(gamma, epoch_h, grp_h, alloc):
        seen = {}
        for r in rows:
            if (r["gamma"] == gamma and r["epoch_h"] == epoch_h
                    and r["grouping_h"] == grp_h and r["alloc"] == alloc):
                seen[r["dseed"]] = r
        return seen  # {seed: row}

    def line(label, gamma, epoch_h, grp_h, alloc, epoch_txt):
        s = get(gamma, epoch_h, grp_h, alloc)
        if 0 not in s or 1 not in s:
            return None
        r0, r1 = s[0], s[1]
        rec = statistics.mean([r0["recall"], r1["recall"]])
        fdp = statistics.mean([r0["fdp"], r1["fdp"]])
        return (f"{label} & {epoch_txt} & {r0['alpha_total']:.3f} & "
                f"{r0['rejections']}\\,/\\,{r1['rejections']} & {f3(rec)} & {f3(fdp)} \\\\")

    lines = []
    # uninterrupted baseline (poly, no restart, 2h grouping)
    lines.append(line("uninterrupted (baseline)", "poly", None, 2, "per-epoch", "--"))
    # E2c: budget reset, per-epoch, 2h and 1h
    lines.append(line("restart 2\\,h, budget reset (E2c)", "poly", 2, 2, "per-epoch", "2"))
    lines.append(line("restart 1\\,h, budget reset (E2c)", "poly", 1, 1, "per-epoch", "1"))
    # E2b: index reset, pre-committed allocation summing to q
    lines.append(line("restart 2\\,h, index reset, uniform (E2b)", "poly", 2, 2, "uniform", "2"))
    lines.append(line("restart 2\\,h, index reset, geometric (E2b)", "poly", 2, 2, "geometric", "2"))
    # oracle uninterrupted comparison
    lines.append(line(r"\oracle\ uninterrupted", "uniform[ORACLE]", None, 2, "per-epoch", "--"))
    lines = [x for x in lines if x is not None]
    body = r"""\begin{table}[t]
\centering
\caption{Periodic restart at the primary window (e-LOND, seed pair 0/1 --- decision-identical to
LOND here, since the group p-value is $\min(1,1/\Ev)$ so $p\le\alphat\Leftrightarrow\Ev\ge1/\alphat$):
detection restored
at the cost of a per-epoch guarantee (total spend $n\cdot q$). Budget reset (E2c) spends
$\alpha_{\text{tot}}=n\cdot q$; index reset (E2b) keeps $\alpha_{\text{tot}}=q$ via a
pre-committed allocation. Rejections are shown per seed (0\,/\,1); recall and $\FDP$ are the
two-seed mean. """ + FF_LABEL + r"""}
\label{apptab:restart}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{llrrrr}
\toprule
arm & epoch (h) & $\alpha_{\text{tot}}$ & rej.\ (s0/s1) & recall & $\FDP$ \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}}
\end{table}"""
    write("restart", body)


# =======================================================================================
# 8. padpools  [table]  src=t28b_reallevel.json
#    (a) per (pos,seed) from table1: detected, median pad real, median pad static.
#    (b) 5-pool medians from pools at 0.62_0 and 0.85_0 (real) + static.
#    Pad medians rounded half-up (int(x+0.5)); null (no detections) shown as ``--''.
# =======================================================================================
def t_padpools():
    d = load("t28b_reallevel")
    # part (a): BOTH within-bucket orders.  `table1` is deliberately the first-flow record (it is
    # what the pre-R3 numbers were transcribed from), so reading it alone would silently report the
    # optimistic arm as if it were the paper's primary one.
    tbo = d["table1_by_order"]
    a_lines = []
    for key in sorted(tbo["keyhash"].keys(),
                      key=lambda k: (float(k.split("_")[0]), int(k.split("_")[1]))):
        kh, ff = tbo["keyhash"][key], tbo["first-flow"][key]
        assert ff["detected_elond"] == d["table1"][key]["detected_elond"]
        cells = []
        for t in (kh, ff):
            real = half_up(t["med_pad_real"]); static = half_up(t["med_pad_static"])
            cells += [str(t["detected_elond"]),
                      ci(real) if real is not None else "--",
                      ci(static) if static is not None else "--"]
        a_lines.append(f"{kh['pos']:.2f} & {kh['seed']} & " + " & ".join(cells) + " \\\\")
    # part (b)
    pool_order = ["generic", "attacker-origin", "protocol-matched", "service-matched", "black-box"]
    pool_label = {"generic": "generic benign", "attacker-origin": "attacker-origin",
                  "protocol-matched": "protocol-matched", "service-matched": "service-matched",
                  "black-box": "black-box"}
    p62 = d["pools"]["0.62_0"]
    p85 = d["pools"]["0.85_0"]
    b_lines = []
    for pool in pool_order:
        r62 = half_up(p62["real"][pool]["med"])
        r85 = half_up(p85["real"][pool]["med"])
        st85 = half_up(p85["static"][pool])
        b_lines.append(
            f"{pool_label[pool]} & {ci(r62)} & {ci(r85)} & {ci(st85)} \\\\"
        )
    body = r"""\begin{table}[t]
\centering
\caption{Padding suppression cost priced against the running controller level $1/\alphat$
(real) vs the static $T/w_0$ threshold. Part (a) gives \emph{both} within-bucket orders at both
detector seeds: the \textbf{canonical} metadata-hash order the paper reports, and the first-flow
arrival order retained as an optimistic upper bound over the orders we audit (\cref{apptab:ordering}).
Detections and the level an alert fires at both move with the order; $T$, $\nCal$, AUROC and the
margin do not. Part (b)'s pool comparison is on the first-flow detected set, the larger of the two;
\cref{tab:pools} gives the same comparison under \emph{both} orders.
Four pools coincide; service-matched is dearer. Medians are rounded to the nearest integer; ``--''
marks a window/seed/order with no detections.}
\label{apptab:padpools}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{rr rrr rrr}
\toprule
\multicolumn{8}{c}{(a) per window $\times$ seed $\times$ order (e-LOND poly, two-hour grouping)} \\
\midrule
& & \multicolumn{3}{c}{\textbf{canonical key-hash}} & \multicolumn{3}{c}{first-flow (upper bd.)} \\
\cmidrule(lr){3-5}\cmidrule(lr){6-8}
pos & seed & det. & pad (real) & pad (static) & det. & pad (real) & pad (static) \\
\midrule
""" + "\n".join(a_lines) + r"""
\bottomrule
\end{tabular}}

\vspace{4pt}
\begin{tabular}{lrrr}
\toprule
\multicolumn{4}{c}{(b) five padding pools, seed 0 (median suppression cost $r$)} \\
\midrule
padding pool & real (0.62) & real (0.85) & static (0.85) \\
\midrule
""" + "\n".join(b_lines) + r"""
\bottomrule
\end{tabular}
\end{table}"""
    write("padpools", body)


# =======================================================================================
# 8b. pools  [table]  src=t28b_reallevel.json
#     Five padding pools priced against the RUNNING e-LOND level 1/alpha_t, seed 0, at the
#     secondary window (0.62) and the stress window (0.85), under BOTH within-bucket
#     orders.  Was hand-written in main.tex, where it went stale when the headline moved to
#     the canonical order; it is generated here so it cannot again.
# =======================================================================================
def t_pools():
    d = load("t28b_reallevel")
    CANON = d["config"]["canonical_order"]
    if CANON != "keyhash":
        # not `assert`: python -O strips those, and this one guards the block HEADINGS
        raise SystemExit(f"t28b's canonical order is {CANON!r}, not 'keyhash'; this table heads a "
                         f"block 'canonical metadata-hash order' and would mislabel that arm")
    POOLS = ["generic", "attacker-origin", "protocol-matched", "service-matched", "black-box"]
    NAMES = {"generic": "generic benign", "attacker-origin": "attacker-origin",
             "protocol-matched": "protocol-matched", "service-matched": "service-matched",
             "black-box": "black-box"}

    def med(order, cell, pool):
        return d["pools_by_order"][order][cell]["real"][pool]["med"]

    def ndet(order, cell):
        return d["pools_by_order"][order][cell]["n_det"]

    def mu(pool):
        # the pool-level mean e-value is a property of the POOL, not of the stream order;
        # assert that rather than quietly taking one arm's copy.
        vals = {d["pools_by_order"][o]["0.85_0"]["real"][pool]["mu"]
                for o in d["pools_by_order"] if "0.85_0" in d["pools_by_order"][o]}
        if len(vals) != 1:
            raise SystemExit(f"mu for {pool} differs across within-bucket orders: {vals}. The "
                             f"caption states mu is a property of the pool, not of the order.")
        return vals.pop()

    def mcell(v):
        # half-UP, not Python's banker's rounding: 98.5 -> 99 and 5246.5 -> 5247, which is
        # what the hand-written predecessor of this table reported and what the body quotes.
        if v is None:
            return "--"
        return cm(int(math.floor(float(v) + 0.5)))

    blocks = []
    for order, head in ((CANON, r"\emph{canonical metadata-hash order (headline)}"),
                        ("first-flow", r"\emph{first-flow arrival (optimistic upper bound)}")):
        blocks.append(r"\multicolumn{4}{l}{" + head + " --- "
                      + f"${ndet(order, '0.62_0')}$ detected at $0.62$, "
                      + f"${ndet(order, '0.85_0')}$ at $0.85$" + r"} \\")
        for pool in POOLS:
            m = mu(pool)
            mus = "---" if m is None else f"{m:.1f}"
            if pool == "black-box":
                mus = r"\textbf{" + mus + "}"
            c85 = f"${mcell(med(order, '0.85_0', pool))}$"
            if pool == "black-box":
                c85 = r"\textbf{" + c85 + "}"
            blocks.append(f"{NAMES[pool]} & {mus} & ${mcell(med(order, '0.62_0', pool))}$ "
                          f"& {c85} \\\\")
        blocks.append(r"\midrule")
    body = r"""\begin{table}[t]
\centering
\caption{Five padding pools priced against the \emph{running} e-LOND level $1/\alphat$, detector
seed 0, two-hour grouping, at the secondary window (0.62) and the stress-test window (0.85), under
\textbf{both} within-bucket orders --- the canonical metadata hash \cref{tab:main} reports and the
first-flow arrival order kept as the optimistic upper bound. Entries are the median suppression cost
$r$ per detected episode, over the detected set that order produces (counts in the block headings);
the order changes \emph{which} episodes must be paid for and how deep into the level sequence they
sit, which is why the two blocks differ by more than a constant. Four pools coincide within each
block; service-matched is dearer, both from a larger mean e-value and from being defined on a
costlier episode subset (\cref{sec:paddingcost}). $\mu$ is the pool-level mean e-value at 0.85 where
defined, a property of the pool and not of the order. Protocol- and service-matched use the episode's
modal protocol/port. Costs are lower bounds.}
\label{tab:pools}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lrrr}
\toprule
Padding pool & $\mu$ (0.85) & median $r$ (0.62) & median $r$ (0.85) \\
\midrule
""" + "\n".join(blocks[:-1]) + r"""
\bottomrule
\end{tabular}}
\end{table}"""
    write("pools", body)


# =======================================================================================
# 9. caps  [table]  src=t25_H5.json
#    summary[cap] holds [min,med,max] over the 10 (pos,seed) configs; we take the median.
#    Columns: n0 (median group-size cap), % groups with m>n0 (viol_frac), detections raw,
#    detections truncated, front-load defeat cost.  'max' cap has no front-load value.
# =======================================================================================
def t_caps():
    d = load("t25_H5")
    cap_order = ["mean", "p50", "p90", "p99", "p999", "max"]
    by = {s["cap"]: s for s in d["summary"]}
    lines = []
    for cap in cap_order:
        s = by[cap]
        n0 = s["n0"][1]
        violpct = s["viol_frac"][1] * 100.0
        # medians over the 10 configs can be x.5 -> show the .5 rather than truncate
        def half(x):
            return str(int(x)) if abs(x - round(x)) < 1e-9 else f"{x:.1f}"
        det_raw = half(s["det_raw"][1])
        det_tr = half(s["det_trunc"][1])
        front = s["frontload"][1] if s["frontload"] is not None else None
        lines.append(
            f"{cap} & {ci(n0)} & {violpct:.2f} & {det_raw} & {det_tr} & "
            f"{ci(front) if front is not None else '--'} \\\\"
        )
    body = r"""\begin{table}[t]
\centering
\caption{Aggregation-cap sweep (median over five positions $\times$ two seeds): the frozen
$n_0=p_{99}$ is chosen for validity and attack cost, not power. ``\% groups $m>n_0$'' is the
share of groups whose size exceeds the cap; ``front-load cost'' is the number of appended
flows needed to defeat the front-loading defence. """ + FF_LABEL + r"""}
\label{apptab:caps}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lrrrrr}
\toprule
cap & $n_0$ & \% groups $m>n_0$ & det.\ raw & det.\ trunc.\ & front-load cost \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}}
\end{table}"""
    write("caps", body)


# =======================================================================================
# 10. addisstate  [table]  src=t32_B1.json   (key/value summary)
#     B* from bstar[R=0]; per-precursor cost = precursor_cost.n_min (= lambda(|C|+1)/k);
#     total = sensitivity[lam=0.25].total; coincidence counts; break_even from surfaces;
#     grey-box landing band from knowledge.grey (cal_estimate_ratio that lands in window).
# =======================================================================================
def t_addisstate():
    d = load("t32_B1")
    bstar = next(x["bstar"] for x in d["bstar"] if x["R"] == 0)
    per_prec = d["precursor_cost"]["n_min"]
    total = next(x["total"] for x in d["sensitivity"]["lam_tau"]
                 if x["lam"] == 0.25 and x["tau"] == 0.5)
    coin = d["coincidence"]
    surf = d["surfaces"]
    grey = [g for g in d["knowledge"]["grey"] if g["lands_in_window"]]
    lo = min(g["cal_estimate_ratio"] for g in grey)
    hi = max(g["cal_estimate_ratio"] for g in grey)
    rows = [
        (r"$B^{\ast}$ (precursor episodes, $R=0$)", f"${bstar}$"),
        (r"per-precursor cost $\lfloor\lambda(\lvert C\rvert+1)/k\rfloor+1$", f"${cm(per_prec)}$ flows"),
        (r"total attack flows", f"${cm(total)}$ ($\\approx {sci(total)}$)"),
        (r"level-saturated coincidence", f"${coin['n_level_saturated']}$ of ${coin['n_detected']}$"),
        (r"minimal pad lands in window", f"${coin['n_minimal_pad_lands_in_window']}$ of ${coin['n_detected']}$"),
        (r"median pad per episode (alternative)", f"${cm(surf['median_pad_per_episode'])}$ flows"),
        (r"break-even vs padding", f"${surf['break_even_episodes']:.2f}$ episodes"),
        (r"grey-box landing band ($\hat{\lvert C\rvert}/\lvert C\rvert$)", f"$[{lo:.2f},\\,{hi:.2f}]$"),
    ]
    lines = [f"{k} & {v} \\\\" for k, v in rows]
    body = r"""\begin{table}[t]
\centering
\caption{ADDIS controller-state attack: $B^\ast=""" + str(bstar) + r"""$ precursor episodes
permanently silence the controller at position 0.85 --- the \textbf{known-invalid} stress window,
which is where the real-stream demonstration must sit, since ADDIS's horizon escape and its
guarantee-invalidity are the same property on two-point conformal evidence
(\cref{apptab:addissynth} reproduces the mechanism where the guarantee does hold). The break-even is
the number of detected episodes whose per-episode padding cost equals the whole one-off state
attack. """ + FF_LABEL + r"""}
\label{apptab:addisstate}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{ll}
\toprule
quantity & value \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}}
\end{table}"""
    write("addisstate", body)


# =======================================================================================
# 11. units  [table]  src=t41_E8.json
#     Position 0.85, black-box pool.  Both attacks in operational units: flows, wire bytes
#     (median), rate, x window flow count, x dataset.  Ratios from volume_ratio[0.85].
# =======================================================================================
def t_units():
    d = load("t41_E8")
    POOL = "black-box (most common benign service)"
    priced = {b["budget"]: b for b in d["budgets_priced"]
              if b["pos"] == 0.85 and b["pool"] == POOL}
    vr = d["volume_ratio"]["0.85"]["ratios"]
    order = [
        ("padding, one e-LOND episode at the RUNNING level (median, 0.85, canonical)",
         r"\textbf{e-LOND, \emph{running} $1/\alphat$: one alert (median), \emph{canonical}}"),
        ("padding, one e-LOND episode at the RUNNING level (median, 0.85)",
         r"\quad same, \emph{first-flow} (optimistic upper bd.)"),
        ("padding, one episode (median)",
         r"level-$w_0$ \emph{static} $\tau{=}T/w_0$: one alert (median)"),
        ("padding, one episode (p90)",
         r"level-$w_0$ \emph{static} $\tau{=}T/w_0$: one alert (p90)"),
        ("padding, all 147 ADDIS detections",
         r"static median $\times$ ADDIS's 147 detections \emph{(mixed)}"),
        ("padding at ADDIS's own level, one episode",
         r"ADDIS, \emph{running} $1/\alphat$: one episode (median)"),
        ("ADDIS spending-state attack", r"ADDIS spending-state attack ($B^\ast$ precursors)"),
    ]

    def ratio_cell(x):
        # large -> N.NNx ; tiny -> sci
        if x >= 1.0:
            return f"${x:.2f}\\times$"
        return f"${sci(x)}$"

    lines = []
    for jkey, label in order:
        b = priced[jkey]
        wire = b.get("wire_bytes", {}).get("0.5")
        r = vr[jkey]
        lines.append(
            f"{label} & ${cm(b['flows'])}$ & {human_bytes(wire)} & "
            f"{human_rate(b['bits_per_s'])} & {ratio_cell(r['vs_window'])} & "
            f"{ratio_cell(r['vs_dataset'])} \\\\"
        )
    body = r"""\begin{table}[t]
\centering
\caption{Both attacks in operational units (position 0.85 --- the \textbf{known-invalid} stress
window; these are attack \emph{costs}, which are measured against the controller's level and do not
rest on the evidence being a valid e-value --- black-box padding pool). Wire
bytes are the per-flow median; rate is priced over the relevant span (7200\,s window for
padding, the position's own deployment span for the state attack). ``$\times$ window'' and
``$\times$ dataset'' are flow-count ratios. \textbf{Each padding row names the procedure whose
level it is priced against, whether that level is the \emph{running} $1/\alphat$ at the episode's own
step or the \emph{static} cold-start $\tau$, and the detected set it is summed over}, because these
differ by two orders of magnitude and are easily confused, \textbf{and the within-bucket order the
detected set was produced under}. Row 1 is the headline cost: the median over e-LOND's own $34$
detections at $0.85$ under the \textbf{canonical} order, priced at the running level --- the value
\cref{tab:main} quotes. Row 2 is the same quantity over the $72$ detections of the
\textbf{first-flow} arrival order, the optimistic upper bound over the orders we audit; it is
$45\times$ dearer because that order detects more episodes and detects them deeper into the level
sequence, where $1/\alphat$ is larger. Both appear in \cref{apptab:padpools}. Rows 3--4 are the \emph{cheap extreme}: $r_{90}$ over the
$257$ episodes of positions $0.62$ and $0.85$ (two seeds) at which all five pools are defined, priced
against the static level-$w_0$ threshold $T/w_0$, first-flow. Row 5 multiplies that static median by
\emph{ADDIS's} $147$-episode detected set (\cref{apptab:addisstate}), so it mixes an e-LOND-scale
per-episode cost with an ADDIS-scale count; it is the cheapest reading of ``suppress everything'' and
is reported only for contrast with the last two rows. Every row below the first is under first-flow
arrival.}
\label{apptab:units}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lrrrrr}
\toprule
attack budget & flows & wire bytes & rate & $\times$ window & $\times$ dataset \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}}
\end{table}"""
    write("units", body)


# =======================================================================================
# 12. feedback  [table]  src=t40_E7_controller.json
#     Guarantee window: delay in {0,0.25,1,4,8}h; FDP for P/PI/AQT (mean over seeds),
#     % alerts open-loop and % steps at actuator limit (reported for the P controller;
#     open-loop is identical for PI).  Final row: long-span at 24h delay (P/PI/AQT FDP),
#     with the no-feedback open-loop baseline named in the caption.
# =======================================================================================
def t_feedback():
    d = load("t40_E7_controller")
    gw = [x for x in d["rows"] if x["window"].startswith("guarantee")]
    ls = [x for x in d["rows"] if x["window"].startswith("long")]

    def mean_fdp(rows, ctrl, delay, window_rows):
        rs = [x for x in window_rows if x["controller"] == ctrl and x["delay_h"] == delay]
        return statistics.mean(x["fdp"] for x in rs) if rs else None

    def mean_field(rows, ctrl, delay, field, window_rows):
        rs = [x for x in window_rows if x["controller"] == ctrl and x["delay_h"] == delay]
        return statistics.mean(x[field] for x in rs) if rs else None

    lines = []
    for delay in [0.0, 0.25, 1.0, 4.0, 8.0]:
        p = mean_fdp(None, "P", delay, gw)
        pi = mean_fdp(None, "PI", delay, gw)
        aqt = mean_fdp(None, "AQT", delay, gw)
        ol = mean_field(None, "P", delay, "frac_open_loop", gw)
        cl = mean_field(None, "P", delay, "frac_steps_clamped", gw)
        dlabel = f"{delay:g}"
        lines.append(
            f"{dlabel} & {f3(p)} & {f3(pi)} & {f3(aqt)} & {pct1(ol)} & {pct1(cl)} \\\\"
        )
    # long-span, 24h
    lp = mean_fdp(None, "P", 24.0, ls)
    lpi = mean_fdp(None, "PI", 24.0, ls)
    laqt = mean_fdp(None, "AQT", 24.0, ls)
    # no-feedback open-loop baseline for long-span (delay None, controller 'none')
    nf = statistics.mean(x["fdp"] for x in ls if x["controller"].startswith("none"))
    long_row = (f"long-span, 24\\,h & {f3(lp)} & {f3(lpi)} & {f3(laqt)} & "
                f"\\multicolumn{{2}}{{c}}{{no-feedback $\\FDP={f3(nf)}$}} \\\\")
    body = r"""\begin{table}[t]
\centering
\caption{Analyst-feedback controllers under wall-clock disposition delay ($q=0.05$) at the
\textbf{primary analysis window} (0.55); $\FDP$ is the two-seed mean. ``open-loop'' and ``at limit''
are for the P controller (open-loop is identical for PI). The final row is the long-span window at a
24\,h delay, where feedback collapses to the no-feedback open-loop baseline. """ + FF_LABEL + r"""}
\label{apptab:feedback}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lrrrrr}
\toprule
delay (h) & $\FDP$ (P) & $\FDP$ (PI) & $\FDP$ (AQT) & \% open-loop & \% at limit \\
\midrule
""" + "\n".join(lines) + r"""
\midrule
""" + long_row + r"""
\bottomrule
\end{tabular}}
\end{table}"""
    write("feedback", body)


# =======================================================================================
# 13. tail  [table]  src=t30_A1.json
#     firing_rates seed 0, all 5 positions: AUROC, n_fired_benign, measured rate, ratio to
#     nominal ('ratio').  rank_depth adds k=1,10,100,1000 firing-rate ratios (seed 0).
# =======================================================================================
def t_tail():
    d = load("t30_A1")
    fr = {r["pos"]: r for r in d["firing_rates"] if r["seed"] == 0}
    rd = {r["pos"]: r for r in d["rank_depth"] if r["seed"] == 0}
    ci = {r["pos"]: r for r in load("t50_calib_ci")["rows"] if r["seed"] == 0}
    lines = []
    for pos in [0.55, 0.62, 0.70, 0.77, 0.85]:
        r = fr[pos]
        k = rd[pos]
        c = ci[pos]
        ci_cell = f"$[{c['ci_lo']:.2f},\\,{c['ci_hi']:.2f}]$"
        lines.append(
            f"{pos:.2f} & {f3(r['auroc'])} & {r['n_fired_benign']} & "
            f"{f2(r['ratio'])} & {ci_cell} & "
            f"{f2(k['k1'])} & {f2(k['k10'])} & {f2(k['k100'])} & {f2(k['k1000'])} \\\\"
        )
    body = r"""\begin{table}[t]
\centering
\caption{Benign firing rate vs nominal by window (seed 0). ``ratio'' is the measured/nominal benign
firing rate at $k=1$, and ``95\% CI'' is its exact Clopper--Pearson binomial interval given the
observed firing count out of the benign flows.
The interval separates the theoretical guarantee from the empirical diagnostic: at the four
non-stress windows only $0$--$3$ benign flows fire (expectation $\approx\!1$), so the interval is
wide and \textbf{includes 1} --- the diagnostic cannot \emph{prove} validity, only fail to reject
it; at position 0.85 the interval \textbf{excludes 1} by orders of magnitude, a clear violation. The
last four columns are the ratio at rank depth $k\in\{1,10,100,1000\}$. This diagnostic is
\textbf{order-invariant}: it scores benign \emph{flows} against the calibration threshold, with no
controller and so no stream sequence to permute.}
\label{apptab:tail}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lrrrrrrrr}
\toprule
 & & & & & \multicolumn{4}{c}{ratio at rank depth $k$} \\
\cmidrule(lr){6-9}
position & AUROC & fired benign & ratio & 95\% CI & $k{=}1$ & $k{=}10$ & $k{=}100$ & $k{=}1000$ \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}}
\end{table}"""
    write("tail", body)


# =======================================================================================
# 14. audit  [table]  src=t31_A2.json
#     (a) verdict_table counts (n, labelled malicious, labelled benign);
#     (b) fdp rows per method: R, fdp_label, fdp_audit_lo (pre-registered), fdp_strict_lo,
#         fdp_strict_hi.
# =======================================================================================
def t_audit():
    d = load("t31_A2")
    vt = d["verdict_table"]
    cats = ["clearly malicious", "probably malicious", "ambiguous",
            "probably benign", "clearly benign"]
    a_lines = []
    for c in cats:
        v = vt[c]
        a_lines.append(f"{c} & {v['n']} & {v['label_mal']} & {v['label_ben']} \\\\")
    b_lines = []
    for f in d["fdp"]:
        b_lines.append(
            f"{f['method']} & {f['R']} & {f3(f['fdp_label'])} & {f3(f['fdp_audit_lo'])} & "
            f"{f3(f['fdp_strict_lo'])} & {f3(f['fdp_strict_hi'])} \\\\"
        )
    body = r"""\begin{table}[t]
\centering
\caption{Adjudicated alert audit against the red-team task record (position 0.85, the
\textbf{known-invalid} stress window). \Cref{apptab:tail} is what establishes that invalidity, from
the benign firing rate; this is a \emph{follow-up label-quality audit} at the same window, not a
guarantee-bearing result and not the diagnostic that made the call. Panel (a):
adjudicated verdict counts with their label split. Panel (b): false-discovery proportion by
method under the label, the pre-registered audit lower bound, and the strict lower/upper bounds.
""" + FF_LABEL + r"""}
\label{apptab:audit}
\begin{tabular}{lrrr}
\toprule
\multicolumn{4}{c}{(a) adjudicated verdicts} \\
\midrule
verdict & $n$ & labelled mal.\ & labelled ben.\ \\
\midrule
""" + "\n".join(a_lines) + r"""
\bottomrule
\end{tabular}

\vspace{4pt}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lrrrrr}
\toprule
\multicolumn{6}{c}{(b) false-discovery proportion} \\
\midrule
method & $R$ & $\FDP_{\text{label}}$ & $\FDP_{\text{audit}}^{\text{lo}}$ & $\FDP_{\text{strict}}^{\text{lo}}$ & $\FDP_{\text{strict}}^{\text{hi}}$ \\
\midrule
""" + "\n".join(b_lines) + r"""
\bottomrule
\end{tabular}}
\end{table}"""
    write("audit", body)


# =======================================================================================
# 15. bates  [table]  src=t23_H7_bates.json
#     Calibration-conditional (Bates) adjustment.  empirical_validity at n_cal=1000 gives,
#     per k, the analytic predicted / measured nominal / beta-adjusted conditional exceedance;
#     summary gives the e-LOND detection cost (median rejections, nominal vs beta).  The
#     beta bound needs beta_ratio of |C| (analytic, delta 0.01..0.2), noted in the caption.
# =======================================================================================
def t_bates():
    d = load("t23_H7_bates")
    NCAL = 1000
    ev = {(e["k"]): e for e in d["empirical_validity"] if e["n_cal"] == NCAL}
    summ = {(s["k"], s["mode"]): s for s in d["summary"]}
    ks = [1, 10, 100]
    lines = []
    for k in ks:
        e = ev[k]
        nom_rej = summ[(k, "nominal")]["elond_rej"][1]
        beta_rej = summ[(k, "beta")]["elond_rej"][1]

        def rejfmt(x):
            return str(int(x)) if abs(x - round(x)) < 1e-9 else f"{x:.1f}"
        lines.append(
            f"{k} & {f3(e['analytic'])} & {f3(e['nominal_exceed'])} & "
            f"{f3(e['adjusted_exceed'])} & {rejfmt(nom_rej)} & {rejfmt(beta_rej)} \\\\"
        )
    # beta_ratio band across delta at k=1 (fraction of |C| the beta bound needs)
    br = [a["beta_ratio"] for a in d["analytic"] if a["k"] == 1]
    body = r"""\begin{table}[t]
\centering
\caption{Bates calibration-conditional adjustment ($n_{\text{cal}}=1000$): it fixes conditional
validity at a power cost set by the same quantity. The first three columns are the conditional
exceedance probability --- analytic prediction, measured nominal, and $\beta$-adjusted; the last
two are the e-LOND detection cost (median rejections, nominal vs $\beta$-adjusted). """ + FF_LABEL + r""" The
$\beta$-bound requires """ + f"{min(br):.2f}" + r"""--""" + f"{max(br):.2f}" + r""" of $\lvert C\rvert$
across error targets $\delta\in[0.01,0.2]$.}
\label{apptab:bates}
\begin{tabular}{lrrrrr}
\toprule
 & \multicolumn{3}{c}{conditional exceedance} & \multicolumn{2}{c}{e-LOND rej.\ (med)} \\
\cmidrule(lr){2-4}\cmidrule(lr){5-6}
$k$ & predicted & nominal & $\beta$-adj.\ & nominal & $\beta$-adj.\ \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}"""
    write("bates", body)


# =======================================================================================
# 16. frontier85  [table]  src=t20_T8.json  (per_pos['0.85'])
#     The stress-test-window matched-operating-points table; the primary (0.55) version is
#     tab:frontier in the body.  Method labels are shortened to match the body table.
# =======================================================================================
def t_frontier85():
    # R8/R5a: canonical order primary (as tab:main), first-flow beneath for the rows it moves.
    d = load("t64_frontier_canonical")
    p = d["per_pos"]["0.85"]["per_order"]["keyhash"]
    pf = d["per_pos"]["0.85"]["per_order"]["first-flow"]
    label = {"online FDR (e-LOND, mean rule)": "online FDR (mean rule)",
             "online FDR (policy D, slot)": "online FDR (slot rule)",
             "feedback controller (L=0)": "feedback, $L{=}0$",
             "feedback controller (L=20 alerts)": "feedback, $L{=}20$",
             "feedback controller (L=50 alerts)": "feedback, $L{=}50$",
             "fixed threshold (no feedback)": "fixed threshold"}

    def alerts_cell(a):
        return f"{a:,.1f}".replace(",", "{,}") if abs(a - round(a)) > 1e-9 else cm(a)

    def row(m):
        return (f"{label[m['method']]} & {alerts_cell(m['alerts'])} & {f3(m['fdp'])} & "
                f"{f3(m['recall'])} & {signed3(m['gap'])} \\\\")

    lines = [row(m) for m in p["methods"]]
    base = {m["method"]: m for m in p["methods"]}
    moved = [m for m in pf["methods"]
             if abs(m["alerts"] - base[m["method"]]["alerts"]) > 1e-9
             or abs(m["recall"] - base[m["method"]]["recall"]) > 1e-12]
    ff_lines = [row(m) for m in moved]
    fr = {round(r["q"], 3): r for r in p["frontier"]}
    for q in (0.0, 0.05):
        r = fr[q]
        lines.append(
            f"\\emph{{frontier, $\\FDP{{=}}{q:.3f}$}} & {cm(r['alerts'])} & {f3(r['fdp'])} & "
            f"\\emph{{{f3(r['recall'])}}} & --- \\\\"
        )
        if q == 0.0:
            lines[-1] = lines[-1].replace("\\midrule\n", "")
    body = r"""\begin{table}[t]
\centering
\caption{Matched operating points at the \textbf{stress-test window} (position 0.85, two-hour
grouping, $T = """ + cm(p["T"]) + r"""$ episodes of which """ + str(p["NM"]) + r""" are malicious).
$\FDP$ is measured against labels at a window where the evidence is \emph{not} a valid e-value
(\cref{sec:tail}). Rows are under the \textbf{canonical} within-bucket order, with the first-flow
arm beneath for the """ + str(len(moved)) + r""" rows the order moves; the frontier is measured
order-invariant and quoted once. The companion primary-window table is \cref{apptab:frontier}.}
\label{apptab:frontier85}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lrrrr}
\toprule
Method & alerts & $\FDP$ & recall & gap \\
\midrule
\multicolumn{5}{l}{\emph{canonical metadata-hash order}} \\
""" + "\n".join(lines[:6]) + r"""
\midrule
\multicolumn{5}{l}{\emph{first-flow arrival (optimistic upper bound; unmoved rows omitted)}} \\
""" + "\n".join(ff_lines) + r"""
\midrule
""" + "\n".join(lines[6:]) + r"""
\bottomrule
\end{tabular}}
\end{table}"""
    write("frontier85", body)


# =======================================================================================
# 17. w7coverage  [table]  src=t47_W7.json
#     Fixed-denominator (5-min src-dst atomic malicious unit) coverage vs the moving-denominator
#     episode recall, and the resolution blur (distinct atomic units per issued alert), for the
#     src-dst family across buckets at the primary (0.55) and stress-test (0.85) windows.
# =======================================================================================
def t_w7coverage():
    d = load("t47_W7")
    denom = d["denom"]
    blabel = {300: "5\\,m", 1800: "30\\,m", 3600: "1\\,h", 7200: "2\\,h",
              21600: "6\\,h", 86400: "1\\,d"}

    def block(pos):
        rows = sorted([r for r in d["rows"] if str(r["pos"]) == pos and r["family"] == "src-dst"],
                      key=lambda r: r["bucket_s"])
        lines = []
        for r in rows:
            feas = "" if r["feasible"] else r"$^{\dagger}$"
            blur = r["blur_mal_atoms_per_alert"]
            lines.append(
                f"{blabel[r['bucket_s']]}{feas} & {f3(r['cov_fixed'])} & "
                f"{(f'{blur:.1f}' if blur is not None else '--')} & "
                f"{f3(r['recall_moving'])} & {f3(r['flow_cov'])} \\\\")
        return lines

    body = r"""\begin{table}[t]
\centering
\caption{Grouping-independent resolution cost (src-dst family, e-LOND $\gamma\propto j^{-1.6}$,
seed 0). The \emph{atomic evaluation reference} is the set of 5-minute src-dst \emph{malicious}
episodes --- a fixed fine-grained denominator we choose, not externally validated incident truth, since
LSPR23 carries no campaign identifier ---
""" + str(denom["0.55"]) + r""" at the primary window, """ + str(denom["0.85"]) + r""" at the
stress-test window --- and its size is \textbf{fixed} across every alerting bucket. ``cov (fixed)''
is the fraction of those atomic units covered by $\ge\!1$ issued alert; ``blur'' is the mean number
of distinct atomic malicious units an issued alert lumps together (the resolution lost); ``recall
(moving)'' is the ordinary episode recall, whose denominator changes with the bucket. As the unit
coarsens the fixed coverage \emph{rises} while the blur climbs from $1$ to $\sim\!20$--$40$: that
climb, not the moving recall, is the denominator-invariant resolution cost. $^{\dagger}$ marks a
\emph{negative level-$w_0$ feasibility margin}; e-LOND can still fire there when that margin exceeds
$-\tfrac12$ (its own $\alpha=2w_0$ cold-start coefficient), which is why some daggered rows carry
non-zero coverage/recall --- a daggered row reads $0$ only when e-LOND is itself infeasible
(cf.\ \cref{apptab:grouping,tab:main}). All counts here use the \textbf{first-flow} within-bucket order, the optimistic upper bound over the orders we audit, not the canonical metadata-hash order \cref{tab:main} reports (\cref{apptab:ordering}).}
\label{apptab:w7coverage}
\begin{tabular}{lrrrr}
\toprule
bucket & cov (fixed) & blur & recall (moving) & flow cov. \\
\midrule
\multicolumn{5}{l}{\emph{primary analysis window (0.55)}} \\
""" + "\n".join(block("0.55")) + r"""
\midrule
\multicolumn{5}{l}{\emph{stress-test window (0.85)}} \\
""" + "\n".join(block("0.85")) + r"""
\bottomrule
\end{tabular}
\end{table}"""
    write("w7coverage", body)


# =======================================================================================
# 18. w3dilution  [table]  src=t48_W3.json
#     Controlled padding-dilution on the real detector: measured pad-flow firing rate (the
#     structural premise, now measured), and measured-vs-closed-form suppression agreement.
# =======================================================================================
def t_w3dilution():
    d = load("t48_W3")
    lines = []
    for pos, tag in (("0.55", "primary (0.55)"), ("0.85", "stress-test (0.85)")):
        p = d["premise"][pos]; e = d["episodes"][pos]; k = d["episodes_keyhash"][pos]
        lines.append(
            f"{tag} & first-flow \\emph{{(upper bd.)}} & {ci(p['pool_size'])} & "
            f"{p['pad_fire_count']}/{ci(p['n_sampled'])} & "
            f"${sci(p['pad_fire_ci95_upper'])}$ & {e['n_detected']} & "
            f"{e['n_match']}/{e['n_detected']} & {cm(e['median_r_closed'])} \\\\")
        lines.append(
            f" & \\textbf{{key-hash (canonical)}} & {ci(p['pool_size'])} & "
            f"{p['pad_fire_count']}/{ci(p['n_sampled'])} & "
            f"${sci(p['pad_fire_ci95_upper'])}$ & {k['n_detected']} & "
            f"{k['n_match']}/{k['n_detected']} & {cm(k['median_r_closed'])} \\\\")
    k55_s = ", ".join(str(v) for v in d["episodes_keyhash"]["0.55"]["r_closed_sorted"])
    pr55 = d["premise"]["0.55"]
    svc = pr55["bb_service_code"]
    svc_s = f"proto {svc//100000}/port {svc%100000}"
    same = all(d["premise"][q]["bb_matches_labelled_choice"] for q in ("0.55", "0.85"))
    atk = max(d["premise"][q]["pool_attack_labelled_frac"] for q in ("0.55", "0.85"))
    naive = d["premise"]["0.85"]["bb_variant_attack_frac"]["window frequency, all flows"]
    same_s = (r", the same service the label-using rule would" if same else "")
    body = r"""\begin{table}[t]
\centering
\caption{Controlled padding-dilution replay on the shipped detector: real flows of the black-box pool
appended to every detected episode under both within-bucket orders (\textbf{canonical} key-hash and
\textbf{first-flow}); src--dst two-hour unit, e-LOND $\gamma\propto j^{-1.6}$, seed 0. Design and
reading: \cref{app:pools}.}
\label{apptab:w3dilution}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{llrrrrrr}
\toprule
window & within-bucket order & pool flows & pad fires & $95\%$ upper & detected & measured $=$ c.f.\ & median $r^{\star}_t$ \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}}
\par\vspace{3pt}
{\footnotesize\raggedright \emph{Notes.} ``pool flows'': the black-box pool's size in the window;
``pad fires'': how many of $n$ sampled pad flows fire when run through the detector, with the exact
one-sided $95\%$ Clopper--Pearson upper bound on the firing probability in the next column;
``measured $=$ c.f.'': detected episodes whose padded group e-value $S_t/(m_t+r)$ crosses the firing
threshold at exactly the predicted $r^{\star}_t=\lfloor S_t\alphat\rfloor-m_t+1$; ``median
$r^{\star}_t$'': over the detected episodes of the row, priced at the running level.\par}
\end{table}"""
    write("w3dilution", body)
    write_prose("w3dilutionprose", r"""\emph{The black-box pool and the dilution replay.} The pad flows of \cref{apptab:w3dilution} are real
flows of the black-box pool, selected on network-observable frequency alone: the most common
$(\text{proto},\text{port})$ over the training prefix, which precedes both calibration and deployment
--- no labels, no detector output, no knowledge of the attacker's own traffic. It picks """ + svc_s + r""" at
both windows""" + same_s + r""", and the resulting pool is measured to be """ + f"{100*atk:.4f}" + r"""\% attack-labelled
(an audit, not a selection criterion). The selection rule matters: taking the mode over \emph{all}
window traffic instead picks the attacker's own flood at the stress window, a pool """ + f"{100*naive:.0f}" + r"""\%
attack-labelled that does not dilute. Zero pad fires out of the sampled flows at both windows is
evidence for the structural premise (ordinary victim-service traffic scores like ordinary traffic),
not proof that the firing probability is zero; the Clopper--Pearson bound in the table says how much
that observation leaves open. Both within-bucket orders are attacked. The key-hash rows are the
canonical order the paper reports, under which a pad provably moves no other hypothesis's spending
weight, so the \cref{assump:groupval} argument is clean; the first-flow rows re-run the identical chain
--- same detector, same pool, same pricing --- on the detected set the initial first-flow order
produces, which \cref{apptab:ordering} shows is the largest over the orders we audit. Every detection is
suppressible under both, and the canonical medians reproduce \cref{tab:main}. The canonical
primary-window set is small, so read it as three individually-priced episodes (costs """ + k55_s + r""" flows)
rather than as a rate; the canonical costs are lower than the first-flow ones because the two orders
detect different episodes at different steps of the level sequence, not because the canonical order is
weaker.
""")


# =======================================================================================
# 19. r7host  [table]  src=t49_R7.json
#     Host-conditioned detector and the padding-transfer boundary. A competent detector that
#     also reads six causal host-context features (higher AUROC than the flow-only arm) is still
#     silenced by padding: ordinary victim-service pads, grafted with the attacker's own causal
#     host context, fire at rate 0 over millions of trials, so dilution survives unchanged.
# =======================================================================================
def _r7verdict(s):
    if s.startswith("holds"): return "holds"
    if s.startswith("inconclusive"): return "OOD (testbed)"
    if s.startswith("fails"): return "fails"
    if s.startswith("partial"): return "partial"
    return "--"


def t_r7host():
    d = load("t49_R7")
    lines = []
    for pos, tag in (("0.55", "primary (0.55)"), ("0.85", "stress-test (0.85)")):
        b = d["partB"][pos]; pr = d["premise"][pos]; c = d["partC"][pos]; o = d["ood"][pos]
        real_bf = f"{o['host_real_benign_fires']}/{cm(o['n_benign'])}"
        graft = f"{c['max_pad_fire']:.3f}" if c["max_pad_fire"] is not None else "--"
        lines.append(
            f"{tag} & {b['host']['auroc']:.3f}/{b['flow_only']['auroc']:.3f} & "
            f"{b['host']['tail_reach']:.3f}/{b['flow_only']['tail_reach']:.3f} & "
            f"{b['host']['elond_detections']}/{b['flow_only']['elond_detections']} & "
            f"${real_bf}$ & ${graft}$ & "
            f"{cm(c['median_r_suppress_host'])}/{cm(c['median_r_star_flowlevel'])} & "
            f"{_r7verdict(c['transfer_verdict'])} \\\\")
    corr = d["features"]["corr_with_y"]
    costs = "; ".join(
        f"{tag} $r^{{\\star}}_t={cm(d['partC'][pos]['median_r_suppress_host'])}$ host vs "
        f"{cm(d['partC'][pos]['median_r_star_flowlevel'])} flow"
        for pos, tag in (("0.55", "0.55"), ("0.85", "0.85")))
    _sen = d["partC"]["0.85"]["pool_sensitivity"]
    _k = "detector-non-firing modal [uses detector output]"
    # ROUND 26 (fidelity audit): the scored accumulation range and the sensitivity pool's service,
    # from the artefact rather than typed
    _cap = d["partC"]["0.85"]["pad_feasible_cap"]
    _trials = d["premise"]["0.55"]["n_pad_scorings"]
    _nhost = len(d["config"]["features"])
    _svc = _sen[_k]["service_code"] if _k in _sen else None
    _svc_s = (f"proto {_svc // 100000}/port {_svc % 100000}" if _svc is not None else "the modal service")
    sens = (f"${100*_sen[_k]['pool_benign_frac']:.0f}\\%$ benign and fires ${_sen[_k]['max_pad_fire']:.2f}$"
            if _k in _sen else "attack-dominated")
    body = r"""\begin{table}[t]
\centering
\caption{Host-conditioned detector and the padding-transfer boundary on LSPR23 (src--dst two-hour
unit, e-LOND $\gamma\propto j^{-1.6}$, seed 0; \textbf{first-flow} within-bucket order on both legs,
the optimistic upper bound over the orders we audit, not the canonical order \cref{tab:main} reports).
``h/f'': host-conditioned / flow-only detector. Design and reading: \cref{app:ait}.}
\label{apptab:r7host}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lcccrrrc}
\toprule
window & AUROC h/f & tail reach h/f & det.\ h/f & real benign fires & graft fire & median cost h/f & transfer \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}}
\par\vspace{3pt}
{\footnotesize\raggedright \emph{Notes.} ``AUROC'': area under the ROC curve on the window's flows;
``tail reach'': the fraction of attack flows scoring above every benign calibration score; ``det.'': e-LOND detections; ``real benign fires'': host-detector firings among
the window's benign flows; ``graft fire'': the grafted-pad firing rate on detected episodes across
accumulation; ``median cost h/f'': the median suppression cost over detected episodes under the causally
recomputed host context / the flow-level closed form $r^{\star}_t$; ``transfer'': whether the flow-level closed form still prices the suppression. """ + FF_LABEL + r"""\par}
\end{table}"""
    write("r7host", body)
    write_prose("r7hostprose", r"""\emph{Host-conditioned detector on LSPR23.} The detector of \cref{apptab:r7host} reads the 33 flow
features plus """ + str(_nhost) + r""" strictly causal ($\mathrm{ts}<\mathrm{ts}(\text{flow})$) host-context features ---
per-host prior counts, distinct-peer counts and failed-connection fractions --- and no endpoint ground
truth (\texttt{label\_src} and \texttt{label\_dst} both have attack rate $1.0$ and are excluded). It has
higher AUROC than the flow-only detector at both windows, yet lower tail reach and fewer e-LOND
detections ($2$ against $18$ at the primary window): higher ranking quality buying fewer, not more,
operational alerts, the detector-quality-versus-feasibility gap of \cref{sec:feasnotdet}. To test the
padding boundary we graft each attacked pair's real causal context (strongest feature src-distinct-dst,
$\rho=""" + f"{corr['src_ddst']:+.2f}" + r"""$; padding one victim cannot raise it) onto ordinary black-box pads ---
the most common $(\text{proto},\text{port})$ on the training prefix, which precedes both calibration
and deployment, so the pool is chosen on network-observable frequency alone with no labels and no
detector output --- and replay the append causally. The pads fire zero across the scored accumulation
range at both windows --- up to """ + cm(_cap) + r""" appended flows per episode, """ + f"{_trials:,}".replace(",", "{,}") + r""" pad scorings at the
primary window --- and the suppression cost is the identical flow-level closed form (""" + costs + r"""),
so within that range the transfer holds at both; costs above the cap are closed-form values, not
replayed. A non-black-box pool rule does fire: selecting the modal service among detector-non-firing
flows picks """ + _svc_s + r""" at $0.85$, a pool that is only """ + sens + r""". Grafting the attacker's own flood onto attack context and
observing the detector fire is not evidence of a defence, so that rule is reported only as a
sensitivity. What LSPR23 cannot settle is the benign-inclusive question: its attacked pairs are $100\%$
malicious, so no real ordinary-to-victim traffic exists there, which is what the AIT testbed supplies.
""")


# =======================================================================================
# 20. r7ait  [table]  src=t51_R7_ait.json
#     R7 re-measured on a benign-inclusive testbed (AIT-LDSv2.0, 8 orgs, no graft): a competent
#     cross-scenario host-conditioned detector fires on REAL ordinary-to-victim traffic far below the
#     LSPR23 graft, confirming the grafted stress-window firing was out-of-distribution.
# =======================================================================================
def t_r7ait():
    d = load("t51_R7_ait")
    lines = []
    for n in d["config"]["scenarios"]:
        f = d["per_fold"][n]; h, fl = f["host"], f["flow"]
        lines.append(
            f"\\texttt{{{n[:10]}}} & {h['auroc']:.3f}/{fl['auroc']:.3f} & {h['attack_fire']:.2f} & "
            f"{100*(h['benign_to_victim_fire'] or 0):.2f}/{100*(fl['benign_to_victim_fire'] or 0):.2f} \\\\")
    dl = d["summary"]["host_minus_flow_delta"]; g = d["summary"]["lspr23_grafted_fire"]
    mx = d["summary"]["host_benign_to_victim"]["max"]
    body = r"""\begin{table}[t]
\centering
\caption{The padding-transfer boundary re-measured on a \emph{benign-inclusive} testbed
(AIT-LDSv2.0, \textbf{8} organisations,
\textbf{""" + f"{d['config']['n_malicious_flows']:,}".replace(",", "{,}") + r"""} attack flows), where victims serve
heavy real benign traffic while attacked, so the padding question is answered on \emph{real}
ordinary-to-victim flows --- \textbf{no graft}. Leave-one-organisation-out (train 7, test 1; a
``deploy on a new network'' test), in-organisation benign conformal calibration, flow features
selected per fold from the training orgs with all identity and \emph{absolute-time} fields excluded.
``benign$\to$victim'' is the fire rate of real benign flows to an attacked host (the pad analogue),
host\,/\,flow-only. Host conditioning adds little and inconsistently (median host$-$flow delta
$""" + f"{dl['median']:+.4f}" + r"$; host higher on $" + f"{dl['n_folds_host_higher']}" + r"/8$ orgs, max $" + f"{100*mx:.1f}" + r"""\%$),
with \texttt{shaw} the one organisation where it is materially higher.
\textbf{That per-organisation exception is real but does not survive as a defence.} A raised
ordinary-to-victim fire rate is measured here \emph{in each flow's own context}; the pads an attacker
actually sends carry the \emph{attacked} pair's context, and replaying the whole Surface~A chain under
that context suppresses every detected Shaw episode (\cref{apptab:aitsupp}). So the honest reading is
that host conditioning is usually negligible here and can look decisive on an individual organisation,
but replaying the chain end-to-end at all eight organisations it does not stop the attack on most
episodes once the pad's own context is modelled, and where it does the binding constraint is the
number of pads required (\cref{apptab:aitsupp}). This also settles the LSPR23 side: the $""" + f"{g}" + r"""$ grafted firing at the
stress window comes from a non-black-box pad pool that is mostly the attacker's own flood
(\cref{apptab:r7host}). AIT has no high-volume flood, which remains open. The flow-only folds are audited under \textbf{both} within-bucket orders in
\cref{apptab:aitorder}: the canonical order detects fewer episodes and its alerts are cheaper to
suppress, as on LSPR23. Rows sequenced by \textbf{first-flow} arrival are conditional on the detected
set that order produces on this testbed.}
\label{apptab:r7ait}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lccc}
\toprule
organisation & AUROC h/f & atk.\ recall & benign$\to$victim \% (h/f) \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}}
\end{table}"""
    write("r7ait", body)


# =======================================================================================
# 21. ordering  [table]  src=t53_ordering.json
#     e-LOND true detections under alternative pre-committed, evidence-independent within-bucket
#     orders, at the primary window (0.55) and the stress-test window (0.85).
# =======================================================================================
def t_ordering():
    d = load("t53_ordering")
    POS = [0.55, 0.62, 0.70, 0.77, 0.85]
    pos = {p["pos"]: p for p in d["positions"]}
    label = {
        "shipped (bucket, first-flow)":    r"first-flow arrival \textbf{(upper bound)}",
        "bucket, group-id":                "group-id (packed key)",
        "bucket, last-flow":               "last-flow arrival",
        "bucket, fixed-random":            "fixed random permutation (one instance)",
        "bucket, hashed-key (canonical)":  r"key-hash \textbf{(canonical, reported)}",
        "bucket, keyed hash (secret seed)": r"keyed key-hash (secret seed)",
    }
    fmt = lambda x: (f"{x:.0f}" if float(x).is_integer() else f"{x:.1f}")
    lines = []
    for name, disp in label.items():
        cells = " & ".join(str(pos[q]["named"][name]["tp"]) for q in POS)
        lines.append(f"{disp} & {cells} \\\\")
    ens = {q: pos[q]["ensemble"] for q in POS}
    med = " & ".join(f"\\emph{{{fmt(ens[q]['tp_median'])}}}" for q in POS)
    rng = " & ".join(f"\\emph{{{ens[q]['tp_min']}--{ens[q]['tp_max']}}}" for q in POS)
    # every window and BOTH seeds, not only the seed-0 rows this table shows
    assert d["first_flow_is_upper_bound_everywhere"], "first-flow is no longer the upper bound"
    assert all(r["perturbation"]["others_moved_hashed_key"] == 0 for r in d["rows"])
    pert = " / ".join(f"{pos[q]['perturbation']['others_moved_first_flow']:,}" for q in POS)
    cold = " / ".join(str(pos[q]["named"]["bucket, hashed-key (canonical)"]
                          ["boundary"]["cold_start_steps"]) for q in POS)
    Ts = " / ".join(f"{pos[q]['T']:,}" for q in POS)
    zero = [q for q in POS
            if pos[q]["named"]["bucket, hashed-key (canonical)"]["boundary"]
            ["n_clearing_anywhere"] == 0]
    zstr = " and ".join(f"{q:.2f}" for q in zero)
    cost = " / ".join(fmt(ens[q]["rstar_median_over_orders"]) for q in POS)
    by = {}
    for r in d["rows"]:
        by.setdefault(r["pos"], {})[r["seed"]] = r
    dmax = lambda key: max(abs(v[0][key] - v[1][key]) for v in by.values() if len(v) == 2)
    seeddelta = str(dmax("canonical_tp")); ffdelta = str(dmax("first_flow_tp"))
    body = r"""\begin{table}[t]
\centering
\caption{e-LOND true detections under \textbf{pre-committed, evidence-independent} within-bucket orders,
all five windows, detector seed 0. All orders emit hypotheses at
bucket close and differ only in how groups closing in the same bucket are sequenced. The count is
\textbf{materially order-sensitive}, and first-flow arrival is the \emph{largest} over every order and
seed we audit --- which is why the paper reports the \textbf{key-hash} row, a deterministic hash of the
group's \emph{own} $(\mathrm{SrcIP},\mathrm{DstIP},\text{bucket})$ key (collisions broken on the key),
and carries first-flow only as a labelled upper bound. The mechanism is \cref{thm:family1}: before the
first rejection only a prefix of """ + cold + r""" steps out of """ + Ts + r""" can reject at all, so a
detection needs a near-ceiling episode to land inside it. Under the canonical order at """ + zstr + r"""
\emph{no} episode clears its own step anywhere in the stream, which is why those entries are $0$.
The key-hash is a timing-independent canonicalization, not a security mechanism: a public hash of
attacker-selectable fields can be ground, and the keyed row is the grinding-resistant variant, itself an
unpredictable draw from the random ensemble below. Conditioned on there being detected episodes, the
per-order median padding cost is """ + cost + r""" flows --- a survivorship-conditioned estimand.
Because the key-hash reads no arrival time, it is also what makes the padding attack leave
\cref{assump:groupval} intact for every other hypothesis: injecting one pad at the earliest instant of
its own bucket moves """ + pert + r""" other hypotheses under first-flow arrival, against \textbf{0}
under the key-hash at every window and seed. The canonical order is also the more
\emph{seed}-stable of the two: across detector seeds its count moves by at most """ + seeddelta + r""",
against """ + ffdelta + r""" for first-flow arrival. Feasibility (C1) is order-invariant. See
\cref{sec:transfer}.}
\label{apptab:ordering}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lrrrrr}
\toprule
within-bucket order & 0.55 & 0.62 & 0.70 & 0.77 & 0.85 \\
\midrule
""" + "\n".join(lines) + r"""
\midrule
\emph{median over 50 orders} & """ + med + r""" \\
\emph{range over 50 orders} & """ + rng + r""" \\
\bottomrule
\end{tabular}}
\end{table}"""
    write("ordering", body)


# =======================================================================================
# 22. addissynth  [table]  src=t52_B1_synthetic.json
#     synthetic guarantee-valid ADDIS: FDR control under conservative vs anti-conservative nulls,
#     and the state attack silencing the target at exactly B*.
# =======================================================================================
def t_addissynth():
    d = load("t52_B1_synthetic")
    v = d["validity"]; a = d["attack"]; cf = d["config"]
    bd = a["bstar_distribution"]
    bmed = str(int(round(bd["median"]))); bmin = str(int(bd["min"])); bmax = str(int(bd["max"]))
    nst = str(bd["n_streams"])
    an = v["all_null"]; mx = v["mixed"]; nt = str(cf["n_target"])
    fdp_an = f"{an['mean_fdp']:.3f}"; fdp_mx = f"{mx['mean_fdp']:.3f}"; rec = f"{mx['mean_recall']:.2f}"
    body = r"""\begin{table}[t]
\centering
\caption{The ADDIS state attack on a \textbf{synthetic stream where ADDIS's guarantee genuinely
holds}, isolating the mechanism from the real-window validity failure. The two-point conformal
evidence used elsewhere cannot supply this: its ADDIS horizon-escape (the spending index never
advances) is the \emph{same} property that makes its null p-values non-conservative, so no two-point
stream is both escape-feasible and guarantee-valid. We therefore use genuinely uniformly-conservative
null p-values ($\mathrm{Unif}(0,1)$, independent, the assumption ADDIS needs). The stream is
synthetic, so LSPR23's grouping plays no part and the result is \textbf{order-invariant} by
construction. \emph{Top:} ADDIS
controls $\FDR$ --- an expectation, not a per-realisation bound (the mixed arm's worst single
realisation is $\FDP=0.104$, above $q$, which the guarantee permits) --- on this
stream: the honest \emph{all-null} test (every rejection false) gives mean $\FDP=""" + fdp_an + r"""\le q{=}0.05$, and with """ + nt + r"""
strong targets present mean $\FDP=""" + fdp_mx + r"""$ at recall
""" + rec + r""" (200 seeds each). \emph{Bottom:} the attack is adversarial state \emph{poisoning} ---
prepending $B$ attacker-generated \emph{alternative} (non-null) precursor episodes with
$p\in(\lambda,\tau]$. ADDIS constrains only \emph{true-null} p-values, so alternatives may take any
value: the legitimate nulls stay $\mathrm{Unif}(0,1)$ and ADDIS's guarantee holds on the \emph{attacked}
stream, not merely the clean one. These selected non-candidates advance the spending index and silence
every rejection at a median $B^{\star}=""" + bmed + r"""$ over """ + nst + r""" guarantee-valid streams
(range """ + bmin + r"""--""" + bmax + r"""; the tail from a rare null false positive that transiently
restores wealth). So even where ADDIS's guarantee holds \emph{after} the attack, an adversary who only
adds traffic drives the controller to silence --- a property of the mechanism, not an artefact of the
dataset already violating the assumption.}
\label{apptab:addissynth}
\begin{tabular}{lrr}
\toprule
 & mean $\FDP$ & $\le q{=}0.05$? \\
\midrule
all-null (every rejection false) & """ + fdp_an + r""" & yes \\
mixed (""" + nt + r""" targets, recall """ + rec + r""") & """ + fdp_mx + r""" & yes \\
\midrule
\multicolumn{3}{l}{\emph{state poisoning: median $B^{\star}{=}""" + bmed + r"""$ (range """ + bmin + r"""--""" + bmax + r""") silences all}} \\
\bottomrule
\end{tabular}
\end{table}"""
    write("addissynth", body)


# =======================================================================================
# 23. aitsupp  [table]  src=t54_ait_suppression.json
#     full Surface A suppression pipeline on the AIT benign-inclusive testbed, real victim pads.
# =======================================================================================
def t_aitsupp():
    d = load("t54_ait_suppression")

    def row(o):
        pf = o.get("real_pad_fire_rate")
        pf_s = "--" if pf is None or pf != pf else f"{pf:.1e}"
        me, mc, sr = o.get("median_rstar_empirical"), o.get("median_rstar_closedform"), o.get("mean_success_rate")
        # a median over an even number of detections is a half-integer; int(round()) is
        # round-half-to-EVEN in Python, so 364.5 printed as "364" -- a number in no artefact.
        def med(v):
            i, frac = int(v), abs(v - int(v))
            return cm(i) if frac < 1e-9 else f"{cm(i)}.{round(frac * 10)}"
        emp = r"\emph{none}" if me is None else med(me)
        clo = "--" if mc is None else med(mc)
        srs = "--" if sr is None else f"{sr:.2f}"
        supp = f"{o.get('n_suppressible', '--')}/{o['n_detected']}"
        return (f"{o['org']} & {o['n_detected']}/{o['n_mal_ep']} & {pf_s} & "
                f"{emp} & {clo} & {supp} & {srs} \\\\")

    flow = [row(o) for o in d["flow"] if o.get("n_detected")]
    host = [row(o) for o in d.get("host", []) if o.get("n_detected")]
    det_f = sum(o["n_detected"] for o in d["flow"] if o.get("n_detected"))
    sup_f = sum(o["n_suppressible"] for o in d["flow"] if o.get("n_detected"))
    hostrows = [o for o in d.get("host", []) if o.get("n_detected")]
    # ROUND 31: the host arm now runs at ALL EIGHT organisations, and some episodes are NOT
    # suppressible within the accumulation range the context curve was scored over.  That used to be
    # an assertion (it held on the two-organisation arm); it is now a reported quantity, because the
    # failures are the informative part -- suppressing it would be the selective reporting the
    # eight-fold run exists to remove.
    hf = {o["org"]: o for o in hostrows}
    shaw_static = hf["shaw"]["real_pad_fire_rate"]; shaw_causal = hf["shaw"]["causal_pad_fire_max"]
    # ROUND 26 (fidelity audit): scope and provenance for the prose companion
    succ_lo = min(o["mean_success_rate"] for o in d["flow"] if o.get("n_detected"))
    succ_hi = max(o["mean_success_rate"] for o in d["flow"] if o.get("n_detected"))
    host_orgs = ", ".join(r"\texttt{" + o["org"] + "}" for o in hostrows)
    host_det = sum(o["n_detected"] for o in hostrows)
    host_sup = sum(o["n_suppressible"] for o in hostrows)
    host_fail = sorted((o["org"], o["n_detected"] - o["n_suppressible"]) for o in hostrows
                       if o["n_suppressible"] < o["n_detected"])
    host_fail_s = ", ".join(r"\texttt{" + o + "}" for o, _ in host_fail)
    host_succ_lo = min(o["mean_success_rate"] for o in hostrows)
    n_draw = d["config"]["d_replay"]
    body = r"""\begin{table}[t]
\centering
\caption{Full suppression pipeline on the benign-inclusive AIT testbed: per organisation, a
leave-one-organisation-out detector, in-organisation benign calibration preceding the first attack,
two-hour host-pair episodes, e-LOND, and each detected malicious episode suppressed by replaying real
ordinary-to-victim flows against the running controller level (200 draws). Rows are sequenced by
\textbf{first-flow} arrival and are conditional on the detected set that order produces; the flow-only
folds under both orders are \cref{apptab:aitorder}. Design and reading: \cref{app:ait}.}
\label{apptab:aitsupp}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lrrrrrr}
\toprule
org & det. & pad fire & $r^{\star}_{t,\mathrm{emp}}$ & $r^{\star}_t$ (closed) & suppr. & succ. \\
\midrule
\multicolumn{7}{l}{\emph{flow-only detector}} \\
""" + "\n".join(flow) + r"""
\midrule
\multicolumn{7}{l}{\emph{host-conditioned detector, end-to-end}} \\
""" + "\n".join(host) + r"""
\bottomrule
\end{tabular}}
\par\vspace{3pt}
{\footnotesize\raggedright \emph{Notes.} ``det.'': e-LOND true detections over malicious episodes; ``pad
fire'': the real ordinary-to-victim firing rate as observed; ``$r^{\star}_{t,\mathrm{emp}}$'': the empirical median
replay cost over suppressible episodes; ``$r^{\star}_t$ (closed)'': the zero-pad closed-form lower bound over
the same episodes ($\le$ empirical by construction); ``suppr.'': detected episodes for which at least
one of the """ + str(n_draw) + r""" draws brought the group below threshold inside the scored range --- a
possibility count, not a reliability one; ``succ.'': the mean per-draw success, which is the
reliability the count does not carry. An episode outside ``suppr.'' had no successful draw within that
budget, which does not establish that it cannot be padded.\par}
\end{table}"""
    write("aitsupp", body)
    write_prose("aitsuppprose", r"""\emph{Design of the AIT replay.} Per organisation, \cref{apptab:aitsupp} trains a
leave-one-organisation-out detector whose flow features are chosen per fold from the training
organisations only, calibrates on in-organisation benign flows strictly preceding the first attack,
forms $(\mathrm{SrcIP},\mathrm{DstIP},\text{2\,h})$ episodes, runs e-LOND, and suppresses each detected
malicious episode by replaying real benign flows to an attacked victim of the organisation (""" + str(n_draw) + r"""
draws). A firing pad contributes the maximum e-value and raises the cost, which the zero-pad closed form
misses. The two arms replay differently because the two detectors read different things. Flow-only:
flow features carry no context, so pads are drawn with replacement from the pool's observed
$0$-or-$\ceil$ evidence, an empirical i.i.d.\ generator, so a modelled cost may exceed the finite
observed pool. Host-conditioned: the six host features are causal, so appending pads changes the
context every later pad is scored in, and holding them fixed would be a static-context diagnostic
rather than a replay; we therefore recompute the victim's context as pads accumulate (counts raised,
distinct-peer counts pinned, failure fractions moved to the pool's rate), score the whole pool under
it, and report a success only over the accumulation range actually scored. The chain runs end-to-end
at all eight organisations, in both arms: under first-flow order """ + f"{sup_f}" + r""" of """ + f"{det_f}" + r""" flow-only detections are
suppressible, per-draw success $""" + f"{succ_lo:.2f}" + r"""$--$""" + f"{succ_hi:.2f}" + r"""$, and """ + str(host_sup) + r""" of """ + str(host_det) + r""" host-conditioned
detections are, per-draw success $""" + f"{host_succ_lo:.2f}" + r"""$--$1.00$. Host conditioning therefore blunts the attack
without stopping it. The causal replay is what shows both halves. It is why most episodes still
suppress: \texttt{shaw}'s ordinary-to-victim flows fire """ + f"{100*shaw_static:.0f}" + r"""\% in
their own contexts, which under a static-context replay made no episode suppressible, but a pad's
context is the attacked pair's, and under that context the same pool fires at most
""" + f"{shaw_causal:.1%}".replace("%", r"\%") + r""" across accumulation, so all three episodes suppress. It is also why the
remaining """ + str(host_det - host_sup) + r""" do not (""" + host_fail_s + r"""): under the accumulated context a pad can
itself fire, and a firing pad adds the ceiling to the group's evidence instead of diluting it, so on
those episodes no draw brings the group mean below threshold in any of the """ + str(n_draw) + r""" draws, within twice
the zero-pad cost (at least $1{,}000$ pads), which is the range the context curve is scored over. What
decides the outcome is the pad count an episode needs against the rate at which pads fire along that
accumulation path. These are censored simulations rather than proof that the episodes cannot be
padded: a budget or a draw count large enough might still find a route. The pinning
models a single already-active attacker--victim pair; padding from new hosts would move the
distinct-peer counts and is not covered.
""")



# =======================================================================================
# 24. a1strata  [table]  src=t55_a1_strata.json
#     Metadata-stratified interrogation of Assumption 1 at rank depths k in {1,10,100,1000}
#     (review 6, item R5).  Every sentence of the caption is derived from the artefact, so
#     the table cannot drift from the numbers or overstate which windows carry a finding.
# =======================================================================================
def t_a1strata():
    d = load("t55_a1_strata")
    m = d["multiplicity"]
    K = d["config"]["k_grid"]

    def fmt(v):
        return f"{v['ratio']:.2f} $[{v['ci'][0]:.2f},{v['ci'][1]:.2f}]$"

    def wins(flags):
        w = sorted({f["pos"] for f in flags})
        return ", ".join(f"{v:.2f}" for v in w) if w else "none"

    lines = []
    for pp in d["per_position"]:
        rows = [r for r in d["rows"] if r["pos"] == pp["pos"]]
        ncell = len(rows) * len(K)
        untest = sum(1 for r in rows for k in K if not r[f"k{k}"]["estimable"])
        lines.append(
            f"{pp['pos']:.2f} & {pp['n_strata']} & {ncell} & {untest} & "
            f"{pp['n_flag_by']} & {pp['n_flag_by_k1']} & {pp['n_flag_contrast']} & "
            + " & ".join(fmt(pp["marginal"][f"k{k}"]) for k in (1, 1000)) + r" \\")

    by, con = m["flagged_by"], m["flagged_contrast"]
    k1 = [f for f in by if f["k"] == 1]
    guar = [f for f in k1 if f["pos"] != 0.85]
    k1_claim = (r"\textbf{none at $k{=}1$ rejects at the primary or secondary window}" if not guar
                else r"\textbf{" + str(len(guar)) + r" at $k{=}1$ reject at the primary or secondary window}")
    k1_where = (r" --- all " + str(len(k1)) + r" $k{=}1$ rejections sit at " + wins(k1) +
                r", already an unambiguous violation" if k1 and not guar else "")
    arity = [f for f in con if f["family"] == "arity"]
    best = max(con, key=lambda f: f["contrast_ci"][0]) if con else None
    bigp = max(con, key=lambda f: f["contrast"]) if con else None
    if best is None:
        con_txt = (r"no stratum contrast survives correction at any window, so the conditional "
                   r"statement is not contradicted either")
    else:
        a_txt = ""
        if arity:
            ba = max(arity, key=lambda f: f["contrast_ci"][0])
            a_txt = (r" The \emph{arity} family --- the component of $\mathcal{M}_j$ the padding "
                     r"attack moves --- carries " + str(len(arity)) + r" of them, the strongest being "
                     + ba["stratum"] + r" at window " + f"{ba['pos']:.2f}" + r", $k{=}" + str(ba["k"])
                     + r"$, firing " + f"{ba['contrast']:.1f}" + r"$\times$ $["
                     + f"{ba['contrast_ci'][0]:.1f},{ba['contrast_ci'][1]:.1f}" + r"]$ its own "
                     r"window's rate.")
        con_txt = (str(len(con)) + r" stratum contrasts survive correction, at windows " + wins(con)
                   + r". The largest lower bound is " + best["stratum"] + r" at "
                   + f"{best['pos']:.2f}" + r", $k{=}" + str(best["k"]) + r"$ ("
                   + f"{best['contrast']:.1f}" + r"$\times$ $["
                   + f"{best['contrast_ci'][0]:.1f},{best['contrast_ci'][1]:.1f}" + r"]$); the "
                   r"largest point estimate is " + bigp["stratum"] + r" at " + f"{bigp['pos']:.2f}"
                   + r", $k{=}" + str(bigp["k"]) + r"$ (" + f"{bigp['contrast']:.1f}"
                   + r"$\times$)." + a_txt)

    body = r"""\begin{table}[t]
\centering
\caption{Metadata-stratified interrogation of \cref{assump:groupval} (seed 0; \textbf{order-invariant}:
per-flow firings against a fixed threshold, not controller decisions). Rows are windows; cells are
(stratum, depth) pairs read at $k\in\{1,10,100,1000\}$; ``surviving BY'' counts Benjamini--Yekutieli
rejections over all cells, at $k{=}1$, and of stratum contrasts. Design and reading: \cref{sec:tail}.}
\label{apptab:a1strata}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lrrrrrrrr}
\toprule
 & & \multicolumn{2}{c}{cells} & \multicolumn{3}{c}{surviving BY} & \multicolumn{2}{c}{marginal ratio [95\% CI]} \\
\cmidrule(lr){3-4}\cmidrule(lr){5-7}\cmidrule(lr){8-9}
position & strata & total & untested & ratio & at $k{=}1$ & contrast & $k{=}1$ & $k{=}1000$ \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}}
\par\vspace{3pt}
{\footnotesize\raggedright \emph{Notes.} ``untested'': cells firing fewer than ten times, which carry no
test but enter the Benjamini--Yekutieli family at $p=1$. Ranks break ties conservatively, so each
marginal ratio is a \emph{lower} bound on the anti-conservatism; the interval is a 95\% percentile
interval from the joint resampling. ``contrast'': strata departing from their \emph{own} window's
marginal on the same replicates.\par}
\end{table}"""
    write("a1strata", body)
    write_prose("a1strataprose", r"""\emph{Stratified design.} \Cref{assump:groupval} constrains benign flows of \emph{true-null} groups
conditionally on that group's metadata, whereas the marginal diagnostic (\cref{apptab:tail}) reads the
marginal rate at the shipped depth $k{=}1$, where the four non-stress windows fire $0$--$3$ benign
flows. \Cref{apptab:a1strata} stratifies those flows on the observable components of $\mathcal{M}_j$
--- episode \textbf{arity} (the quantity padding manipulates), \textbf{service}
$(\text{proto},\text{port})$, the two-hour \textbf{bucket} that fixes a group's position, and
high-support destination \textbf{host}, all fixed by an outcome-blind support rule --- and reads them
at $k\in\{1,10,100,1000\}$. Both sources of uncertainty are resampled jointly, and both are clustered:
a window's whole diagnostic depends on the calibration set only through its $k$-th largest score, which
every stratum shares, so the calibration tail is resampled over calibration \emph{host pairs}; the test
side is a Poisson-multiplier bootstrap over deployment host pairs. Multiplicity is corrected with
Benjamini--Yekutieli, valid under the arbitrary dependence this design has, over \emph{every} cell: a
cell firing fewer than ten times carries no test, but still enters the family at $p=1$, since dropping
it would shrink the denominator using the same tail count that drives significance. A \emph{contrast}
is a stratum departing from its \emph{own} window's marginal on the same replicates --- the quantity
that speaks to the conditional statement, since the shared calibration draw largely cancels in a ratio
of two rates read at one threshold.

\emph{Reading, in both directions.} """ + str(m["n_untestable"]) + r""" of the """ + str(m["n_cells"]) + r""" cells carry no test at all
(""" + str(m["n_low_events"]) + r""" of them fire fewer than ten times), which is itself the point: at the depth the pipeline
uses, the data mostly cannot speak. Of the """ + str(m["n_flag_by"]) + r""" cells that do reject, """ + k1_claim + k1_where + r""",
which is an \emph{inconclusive non-rejection} and not evidence for \cref{assump:groupval}: at
$k{=}1$ most cells are simply uninformative. Deeper in the tail the conditional statement is
another matter: """ + con_txt + r""" One dependence remains unresampled: host-pair clustering does not
absorb a shock shared across many pairs at once, and a window's calibration tail concentrates in its
two to four buckets, so these counts may be optimistic --- dropping the one stratum family aligned
with that confounder leaves """ + str(m["n_flag_contrast_excl_bucket"]) + r""" contrasts at windows """ + ", ".join(f"{v:.2f}" for v in m["windows_contrast_excl_bucket"]) + r""". A departure at
$k{=}1000$ is nonetheless compatible with a valid rank-1 rate --- the excess may sit entirely in
ranks $2..1000$ --- so this tests a \emph{necessary implication} where it is estimable, not the
assumption itself. Every guarantee-bearing conclusion in this paper is therefore stated \emph{under}
\cref{assump:groupval}, and this diagnostic is not offered as support for it.
""")


# =======================================================================================
# 25. uai26  [table*]  src=t56_uai26.json
#     The UAI 2026 e-closure / compound-e procedures against the C1 horizon, gamma=poly,
#     seed 0 (seed 1 differs only at 0.62/0.70 and is in the record).  "silent" is the EXACT
#     at-arrival figure for every arm, including the step-up ones.
# =======================================================================================
def t_uai26():
    d = load("t56_uai26")
    # e-TOAD at d_t = infinity IS online e-BH (mask-identical at every row, checked in
    # t56's summary), so it is listed once, carrying the exact silence figure.
    arms = ["e-LOND", "donation e-LOND", "closed e-LOND", "donation e-BH (snapshot)",
            "e-TOAD(bucket)", "e-TOAD(arc)"]
    label = {"e-LOND": r"e-LOND \emph{(baseline)}, $d_t=t$",
             "donation e-LOND": "donation e-LOND",
             "closed e-LOND": r"closed e-LOND ($\overline{\text{e-LOND}}$)",
             "donation e-BH (snapshot)": "donation e-BH",
             "e-TOAD(bucket)": "e-TOAD, bucket-close deadline",
             "e-TOAD(arc)": r"e-TOAD, $d_t=\infty$ ($=$ online e-BH)"}
    # R8/R5c: t56 now carries two orders, and keying this dict on pos alone silently took
    # whichever came last.  Select the CANONICAL order explicitly, as tab:main does.
    ORD = "keyhash"
    rows = {r["pos"]: r for r in d["rows"]
            if r["gamma"] == "poly" and r["seed"] == 0 and r.get("order", "first-flow") == ORD}
    assert len(rows) == 5, f"expected 5 canonical rows, got {len(rows)}"
    positions = sorted(rows)
    lines = []
    for a in arms:
        cells = []
        for pos in positions:
            r = rows[pos]; x = r["arms"][a]
            sil = x["silent"]
            cells.append(f"{x['tp']}" if sil is None
                         else f"{x['tp']} & {pct1(sil / r['T'])}")
        # arms without a silence figure span the column with a dash
        row = " & ".join(c if "&" in c else f"{c} & --" for c in cells)
        lines.append(f"{label[a]} & {row} \\\\")
    hdr = " & ".join(rf"\multicolumn{{2}}{{c}}{{{p:.2f}}}" for p in positions)
    cmid = "".join(rf"\cmidrule(lr){{{2*i+2}-{2*i+3}}}" for i in range(len(positions)))
    sub = " & ".join(["det.\\ & silent"] * len(positions))
    body = r"""\begin{table*}[t]
\centering
\caption{The UAI 2026 procedures~\cite{xu2026eclosure} against the feasibility horizon
($\gamma\propto j^{-1.6}$, seed 0, two-hour grouping; \cref{sec:escapes}). ``det.'' is true
detections, ``silent'' the fraction of hypotheses that cannot be rejected \emph{at their own
arrival} even at the evidence ceiling. For the step-up procedures that fraction is computed
\emph{exactly}, by re-running the step-up on the counterfactual in which the arriving hypothesis
carries $\ceil$; the cheaper test --- does $\ceil$ clear $1/(\alpha\gamma_t r)$ at the largest
conceivable $r$ --- is only \emph{necessary}, since reaching $r$ needs $r$ hypotheses to clear the
bar at once, and it reports $0.0\%$ at every window here. All counts and silence fractions are under
the \textbf{canonical} within-bucket order, as \cref{tab:main} is. \textbf{Deferring the decision
leaves at-arrival feasibility essentially unchanged} --- identical to $d_t=t$ at three of the five windows
--- \textbf{and buys power only by revisiting}, which is why its price is alerting latency. The
last row is online e-BH, reached as the $d_t=\infty$ limit and verified rejection-identical to it at
every row. Donation e-BH is the literal reading of its source's Eq.~(102); a second
reading of that equation gives one more detection at 0.85 and is reported here as a sensitivity
analysis, and neither is quoted as a power comparison (\cref{sec:escapes}).}
\label{apptab:uai26}
\begin{tabular}{l""" + "rr" * len(positions) + r"""}
\toprule
 & """ + hdr + r""" \\
""" + cmid + r"""
Procedure & """ + sub + r""" \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table*}"""
    write("uai26", body)


# =======================================================================================
# 26. groupcal  [table]  src=t57_group_calibration.json
#     Seed 0.  What calibrating the grouped unit costs, against the shipped flow calibration.
# =======================================================================================
def t_groupcal():
    d = load("t57_group_calibration")
    rows = [r for r in d["rows"] if r["seed"] == 0]
    rows.sort(key=lambda r: r["pos"])
    lines = []
    for r in rows:
        g = r["group"]; mx = r["stats"]["max"]; mn = r["stats"]["mean"]
        lines.append(
            f"{r['pos']:.2f} & {ci(r['flow']['nCal'])} & {signed3(r['flow']['margin'])} & "
            f"{r['flow']['tp']} & {ci(g['nCal'])} & {signed3(g['margin'])} & "
            f"{mx['tp']} & {mn['tp']} & {mx['coldstart_window_closed_form']} & "
            f"{num_or(mx['first_fire_position'], ci)} & "
            f"{mx['arity']['spearman_arity_vs_statistic']:+.2f} & "
            f"{mn['arity']['spearman_arity_vs_statistic']:+.2f} \\\\")
    body = r"""\begin{table*}[t]
\centering
\caption{What calibrating the \emph{grouped unit} costs (seed 0; \cref{sec:groupcal}). Left: the
shipped construction, calibrated on benign \emph{flows}. Right: split conformal on the group, same
key and protocol, which would need only calibration/test \emph{group} exchangeability. The evidence
ceiling falls by the flows-per-group ratio ($40$--$49\times$) with $T$ unchanged, so the margin
collapses and detection at the primary and secondary windows goes to zero. That is the feasibility boundary, not
a weak statistic: the cold-start window is tens of hypotheses and the first \emph{firing} group
arrives hundreds of positions later (at $0.55$, $110$ groups fire and none lands inside the window);
feasible-step counts match $\lfloor(\alpha\ceil(R{+}1)/\zeta(1.6))^{1/1.6}\rfloor$ at every
configuration. The last two columns qualify the repair without refuting it: the \emph{max} statistic --- the
padding-robust one --- is strongly arity-dependent, and arity is what the adversary controls, so
group exchangeability may be fragile under group-formation shift, though the correlation alone
neither refutes it nor shows that it fails; the \emph{mean} is arity-invariant to within noise and is exactly the rule
\cref{thm:padding} defeats. Position $0.85$ is the stress window and
its detections are not guarantee-bearing (\cref{sec:tail}). The flow-calibration columns use the \textbf{first-flow} within-bucket order (the optimistic upper bound), not the canonical order of \cref{tab:main}; the group arm matches its tie-break to the same order, so the two remain comparable (\cref{apptab:ordering}).}
\label{apptab:groupcal}
\resizebox{\textwidth}{!}{%
\begin{tabular}{lrrrrrrrrrrr}
\toprule
 & \multicolumn{3}{c}{flow calibration} & \multicolumn{6}{c}{group calibration} &
 \multicolumn{2}{c}{arity corr.} \\
\cmidrule(lr){2-4}\cmidrule(lr){5-10}\cmidrule(lr){11-12}
Position & $\lvert C\rvert$ & margin & det. & $\lvert C\rvert$ & margin & det.\ max &
det.\ mean & cold start & 1st fire & max & mean \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}}
\end{table*}"""
    write("groupcal", body)



# =======================================================================================
# 27. semblur  [table]  src=t58_semantic_blur.json
#     The EXTERNAL semantic anchor for the alert-blur claim (review-7 item R4): distinct
#     red-team steps merged per issued alert, against the 5-minute proxy, by bucket width.
# =======================================================================================
def t_semblur():
    d = load("t58_semantic_blur")
    sm = d["summary"]; us = sm["usability"]; sg = d["segment_map_check"]
    lg = d["reporting_lag"]; rt = d["redteam"]
    f = lambda x, n=2: ("--" if x is None else f"{x:.{n}f}")
    lines = []
    for pos in d["config"]["POS"]:
        for order in d["config"]["ORDERS"]:
            rr = [r for r in d["rows"] if r["pos"] == pos and r["order"] == order]
            rr.sort(key=lambda r: r["bucket_s"])
            if not any(r["steps_per_alert"] is not None for r in rr):
                continue
            tag = "key-hash" if order == "keyhash" else "first-flow"
            for r in rr:
                if r["steps_per_alert"] is None:
                    continue
                bl = ("$\\checkmark$" if r["steps_per_alert"] > r["steps_per_alert_null_p975"]
                      else "--")
                bs = ("$\\checkmark$" if r["steps_per_alert"] > r["steps_per_alert_shiftnull_p975"]
                      else "--")
                lines.append(
                    f"{pos:.2f} & {tag} & {r['bucket_s']} & {r['n_alerts_with_step']} & "
                    f"{f(r['steps_per_alert'])} & {f(r['flow_span']['steps_per_alert'])} & "
                    f"{f(r['steps_per_alert_null'])} & {bl} & "
                    f"{f(r['steps_per_alert_shiftnull'])} & {bs} & "
                    f"{f(r['blur_mal_atoms_per_alert'])} \\\\")
    tw = sm["tracking"]
    trk = []
    for order in d["config"]["ORDERS"]:
        for pos, w in tw[order]["per_window"].items():
            tag = "key-hash" if order == "keyhash" else "first-flow"
            trk.append(f"{pos} & {tag} & {w['n']} & {w['steps_vs_atoms']:+.3f} & "
                       f"{w['steps_vs_bucket']:+.3f} & {w['atoms_vs_bucket']:+.3f} \\\\")
    temporal = [k for k, v in us.items() if v["verdict"].startswith("temporal")]
    spatial = [k for k, v in us.items() if v["verdict"].startswith("spatial")]
    # ROUND 26: the old caption said "under 10% of them overlap it in time" for the temporal cells,
    # which was true of those cells but was read against 0.55/first-flow (13.1%), a "thin" cell the
    # sentence did not name.  Name the cells with their order and compute the bound.
    _cell = lambda k: k.split("_")[0] + (" (canonical)" if k.endswith("keyhash") else " (first-flow)")
    _by_window = lambda k: (float(k.split("_")[0]), 0 if k.endswith("keyhash") else 1)
    temporal_cells = ", ".join(_cell(k) for k in sorted(temporal, key=_by_window))
    spatial_cells = ", ".join(_cell(k) for k in sorted(spatial, key=_by_window))
    temporal_max_overlap = max(us[k]["frac_alerts_temporally_overlapping"] for k in temporal)
    body = r"""\begin{table}[t]
\centering
\caption{An external denominator for the resolution cost: distinct red-team steps of LSPR23's task
record merged per issued alert, under both within-bucket orders (\textbf{canonical} key-hash and
\textbf{first-flow}). (a) steps per alert against the label and shift nulls; (b) within-window rank
agreement across bucket widths. Design and reading: \cref{app:granularity}.}
\label{apptab:semblur}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{rlrrrrrcrcr}
\toprule
 & & & & \multicolumn{2}{c}{steps/alert} & \multicolumn{2}{c}{label null} & \multicolumn{2}{c}{shift null} & 5-min \\
\cmidrule(lr){5-6}\cmidrule(lr){7-8}\cmidrule(lr){9-10}
pos & order & bucket (s) & attrib. & bucket & flow & mean & $>$ & mean & $>$ & atoms/alert \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}}

\vspace{4pt}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{rlrrrr}
\toprule
\multicolumn{6}{c}{(b) within-window rank agreement across bucket widths} \\
\midrule
pos & order & widths & steps vs.\ atoms & steps vs.\ bucket & atoms vs.\ bucket \\
\midrule
""" + "\n".join(trk) + r"""
\bottomrule
\end{tabular}}
\par\vspace{3pt}
{\footnotesize\raggedright \emph{Notes.} ``pos'': the window's chronological position; ``attrib.'': alerts
with at least one attributed step.
``bucket''/``flow'': the same attribution rule priced against the alert's bucket span or its actual
first-to-last flow span. ``mean'': the null's mean steps per alert; $\checkmark$ marks an observed count
exceeding that null's $97.5$th percentile. At the $86{,}400$\,s bucket both nulls tie the observation
exactly, so only sub-daily widths inform. Panel (b): Spearman rank agreement across bucket widths
within one window.\par}
\end{table}"""
    write("semblur", body)
    write_prose("semblurprose", r"""\emph{Attribution rule and nulls.} The 5-minute atom is \emph{our} proxy for one attack action, so
\cref{apptab:semblur} counts instead how many distinct red-team steps each issued alert merges, using
LSPR23's own task record (""" + str(rt["n_tasks"]) + r""" tasks, """ + str(rt["n_timed_steps"]) + r""" timestamped submissions,
2023-03-09 07:03--15:08 UTC), an attacker-defined decomposition fixed before the dataset was
published. A step is attributed to an alert when its submission falls in the alert's bucket span
\emph{and} its task's declared network segments meet the alert's, or one of its compromise-report IPs
is an alert endpoint. The link is the segment vocabulary --- the task record's \texttt{bt\_baf\_int}
is the dataset's own per-flow \texttt{baf\_int} --- corroborated against the machine-readable
compromise reports (""" + str(sg["n_present_as_endpoint"]) + r"""/""" + str(sg["n_compromise_ipv4"]) + r""" IPv4 appear as a flow endpoint;
""" + str(sg["seg_agree"]) + r""" agree, """ + str(sg["seg_disagree"]) + r""" disagree). Two nulls are run. The \textbf{label} null permutes which
task each submission belongs to, holding the times fixed: it asks whether \emph{which} task acted is
informative, and goes degenerate at the daily bucket where every submission shares one bucket. The
\textbf{shift} null rotates the whole red-team timeline against the stream, preserving task identity,
ordering, attributes and inter-arrival structure: it asks the sharper question, whether the alignment
\emph{in time} is informative, and does not degenerate.

\emph{Reading.} The result is agreement in direction without discrimination. The external count and
the proxy rise together (panel (b) of \cref{apptab:semblur}), so the resolution cost survives
substituting an attacker-defined unit for ours; but the count clears the label null at only $6$ of
$19$ cells and the shift null at only $1$, so the rise is driven by a wider bucket capturing more
submissions rather than by alert-level correspondence, and we report it as agreement rather than as
confirmation. The record also sees the alerts at only """ + str(sm["n_windows_usable"]) + r""" of """ + str(sm["n_window_order_cells"]) + r""" window--order
cells: at """ + temporal_cells + r""" the issued alerts sit in the \emph{feasible prefix} --- the first
minutes of a deployment window --- which predates the exercise's first submission, so at most
$""" + f"{100 * temporal_max_overlap:.0f}" + r"""\%$ of them overlap it in time at all; at """ + spatial_cells + r""" they do overlap but only $2$ of $17$ tasks with a
timed step declare a segment or file a compromise report. Four further limits. \emph{(i)} At the
$86{,}400$\,s bucket both nulls tie the observation exactly: every submission shares one daily bucket,
so no permutation and no rotation can move a step between alerts (the spatial filter is \emph{not}
vacuous there --- at $0.70$/first-flow it admits $12$ of $30$ temporally overlapping alerts --- it is
the nulls that lose their power); only sub-daily widths inform. \emph{(ii)} The whole positive result
rests on six coarse segment labels: across every row the compromise-IP conjunct adds \emph{no} alert
the segment conjunct did not already admit. \emph{(iii)} Every attributed alert sits on a
labelled-malicious episode and the labels came from this same exercise, so nothing here is
label-independent evidence that an alert is a true positive. \emph{(iv)} A submission is when the red
team \emph{reported}: the lag, estimable from the compromise reports' own timestamps, has median
""" + f"{lg['median_s']:.0f}" + r"""\,s (IQR """ + f"{lg['q25_s']:.0f}--{lg['q75_s']:.0f}" + r"""\,s), small against every bucket width.
""")



# =======================================================================================
# 28. prevalence  [table]  src=t59_prevalence.json
#     Realistic-prevalence sensitivity (review-7 item R5): thinning malicious EPISODES to a SOC
#     base rate collapses detection while leaving (or improving) feasibility.
# =======================================================================================
def t_prevalence():
    d = load("t59_prevalence")
    s = d["summary"]
    f = lambda x, n=2: ("--" if x is None else f"{x:.{n}f}")
    lines = []
    for w in d["windows"]:
        for order in d["config"]["ORDERS"]:
            tag = "key-hash" if order == "keyhash" else "first-flow"
            rr = [r for r in d["rows"] if r["pos"] == w["pos"] and r["order"] == order]
            rr.sort(key=lambda r: (-1.0 if r["pi_target"] is None else -r["pi_target"]))
            cells = []
            for r in rr:
                cells.append(f"{r['elond']['rej_mean']:.2f}")
                cells.append(f"{100*r['elond']['p_bootstrap']:.0f}")
            lines.append(f"{w['pos']:.2f} & {tag} & " + " & ".join(cells) + " \\\\")
    esc = []
    for x in s["obs_vs_thin"]:
        tag = "key-hash" if x["order"] == "keyhash" else "first-flow"
        esc.append(f"{x['pos']:.2f} & {tag} & {100*x['elond_p_boot_1e4']:.0f} & "
                   f"{100*x['ebh_p_boot_1e4']:.0f} & "
                   f"{100*(x['etoad_p_boot_1e4'] or 0):.0f} & "
                   f"{100*x['elond_p_boot_1e4_removed']:.0f} \\\\")
    import math as _m
    _pis = [float(x) for x in d["config"]["PI_TARGETS"] if x not in ("None", "0.0")]
    _orders_lo = _m.log10(s["episode_prevalence_range"][0] / max(_pis))
    _orders_hi = _m.log10(s["episode_prevalence_range"][0] / min(_pis))
    body = r"""\begin{table}[t]
\centering
\caption{Detection at lower base rates (item R5): malicious episodes thinned to a target prevalence
$\pi$ with benign replacement; e-LOND, seed 0, both within-bucket orders (\textbf{canonical} key-hash
and \textbf{first-flow}). Upper panel: mean rejections $R$ and the bootstrap probability that the
controller ever rejects; lower panel: that probability at $\pi=10^{-4}$ for the escape procedures and
for the deletion mechanism. Design and reading: \cref{app:feasnotpower}.}
\label{apptab:prevalence}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{rl rr rr rr rr rr}
\toprule
 & & \multicolumn{2}{c}{observed} & \multicolumn{2}{c}{$\pi=10^{-3}$} & \multicolumn{2}{c}{$\pi=10^{-4}$} & \multicolumn{2}{c}{$\pi=10^{-5}$} & \multicolumn{2}{c}{$\pi=0$} \\
\cmidrule(lr){3-4}\cmidrule(lr){5-6}\cmidrule(lr){7-8}\cmidrule(lr){9-10}\cmidrule(lr){11-12}
pos & order & $R$ & boot & $R$ & boot & $R$ & boot & $R$ & boot & $R$ & boot \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}}

\vspace{4pt}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{rlrrrr}
\toprule
\multicolumn{6}{c}{bootstrap probability (\%) at $\pi = 10^{-4}$: the escapes collapse too} \\
\midrule
pos & order & e-LOND & online e-BH & e-TOAD & e-LOND (deletion) \\
\midrule
""" + "\n".join(esc) + r"""
\bottomrule
\end{tabular}}
\par\vspace{3pt}
{\footnotesize\raggedright \emph{Notes.} ``pos'': the window's chronological position; ``observed'': the
unthinned stream; ``$R$'': mean rejections over """ + str(d["config"]["n_rep"]) + r""" draws; ``boot'': the percentage of draws in
which the controller \emph{ever} rejects; the observed and $\pi=0$ arms are single deterministic
streams. Lower panel: online e-BH and e-TOAD are the escape procedures of \cref{app:taxonomy}; ``e-LOND
(deletion)'' removes thinned episodes instead of replacing them. $\pi=10^{-2}$ is unreachable: it is above the observed episode rate, and
we cannot manufacture attacks. The $0.85$ rows are the stress window, whose evidence is not a valid
e-value.\par}
\end{table}"""
    write("prevalence", body)
    write_prose("prevalenceprose", r"""\emph{Prevalence as a swept parameter.} LSPR23 is a live-fire exercise: $""" + f"{100*s['flow_prevalence']:.2f}" + r"""\%$ of flows and
""" + f"{100*s['episode_prevalence_range'][0]:.2f}" + r"""--""" + f"{100*s['episode_prevalence_range'][1]:.2f}" + r"""\% of episodes are
malicious, the optimistic case, so \cref{apptab:prevalence} treats prevalence as a swept parameter rather
than asserting a figure for a typical SOC: the targets run from """ + f"{_orders_lo:.1f}" + r""" to """ + f"{_orders_hi:.1f}" + r""" orders of
magnitude below the exercise's episode rate, a sensitivity range, not a claim about any deployment. We thin malicious
episodes --- not flows, which would change group arity and evidence sums and so confound the
feasibility question with the padding cost --- to each target $\pi$, keeping a nested random subset so
a lower target keeps a strict subset of a higher one. The primary mechanism replaces each thinned
episode with benign evidence drawn from the same window, so the hypothesis stays at its own index and
$T$, the margin and every survivor's level are held exactly fixed; the deletion mechanism removes it
instead, which shrinks $T$ by up to """ + f"{100*s['max_T_shrink_frac']:.2f}" + r"""\% and raises the margin by up to
""" + f"{s['max_margin_shift_removed']:+.4f}" + r""". The two agree to within """ + f"{s['max_abs_variant_gap_at_1e4']:.2f}" + r""" in
bootstrap probability, so it is prevalence and not re-indexing that drives the collapse. Feasibility is
untouched while detection collapses: the feasibility-is-not-detection separation, driven by base rate
alone. The $\pi=0$ arm produces no rejection on any stream, but that is """ + str(s["n_pure_null_effective_streams"]) + r"""
effective (overlapping) windows, and zero would be the likely outcome even at the $4.5\%$ early-false
rate quoted from simulation in \cref{app:taxonomy} ($P=""" + f"{s['prob_zero_if_true_rate_045']:.2f}" + r"""$): it is
consistency, not a test of that number.
""")



# =======================================================================================
# 29. insertion  [table]  src=t60_positional.json
#     Suppression by INSERTION: creating hypotheses ahead of a target pushes it out of the
#     cold-start window.  Nothing is appended, so thm:padding and the group-MAX statistic's
#     append-invariance are both irrelevant to it.
# =======================================================================================
def t_insertion():
    d = load("t60_positional")
    s = d["summary"]
    f = lambda x, n=0: ("--" if x is None else f"{x:,.{n}f}")
    lines = []
    for c in s["comparison"]:
        tag = {"keyhash": "key-hash", "keyed": "keyed", "first-flow": "first-flow"}[c["order"]]
        lines.append(
            f"{c['pos']:.2f} & {tag} & {c['n_targets']} & "
            f"{f(c['median_targeted_gstar'])} & {f(c['median_pad_flows'], 1)} & "
            f"{f(c['g_all_suppressed'])} & {f(c['total_pad_flows_to_silence_window_UPPER'])} & "
            f"{'$\\checkmark$' if c['cheaper_per_window_at_1_flow_per_group'] else '--'} \\\\")
    gl = []
    for r in d["group_max_rows"]:
        n = r["n_targets"]
        gl.append(f"{r['pos']:.2f} & {r['G']:,} & {r['n_firing_groups']} & {n} & "
                  f"{r['cold_start_steps']} & "
                  f"{f(r.get('targeted_gstar_median'), 1) if n else '--'} & "
                  f"{f(r.get('prefix_g_all')) if n else '--'} \\\\")
    body = r"""\begin{table}[t]
\centering
\caption{\textbf{Suppression by insertion, not by padding.} \Cref{thm:padding} and every cost in
\cref{sec:paddingcost} concern \emph{appending} flows to a fixed hypothesis. This attack appends
nothing: it \emph{creates} hypotheses ahead of the target, pushing it out of the cold-start window
past which no rejection is possible. Two models are kept apart because they are different attacks.
\textbf{Targeted} inserts only immediately ahead of one episode, which leaves every earlier
hypothesis and hence $R$ untouched, so its cost is closed-form
$G^\star=\lfloor(\alpha(R{+}1)E/\zeta(1.6))^{1/1.6}\rfloor-p$ (replay-verified).
\textbf{Window} inserts ahead of everything and silences the controller outright --- that is
\emph{not} a per-episode cost, since it also deletes the earlier detections that raised $R$.
\textbf{The split verdict is the result:} insertion does \emph{not} beat padding for one alert
(""" + f"{s['n_cells_positional_cheaper']}" + r"""/""" + f"{s['n_cells_compared']}" + r""" cells),
but silences the whole window for a few hundred hypotheses
(""" + f"{s['n_cells_positional_cheaper_per_window']}" + r"""/""" + f"{s['n_cells_compared']}" + r"""
cells at one flow per inserted group, """ + f"{s['n_cells_cheaper_per_window_at_2_flows']}" + r"""/""" + f"{s['n_cells_compared']}" + r""" at two). Padding totals are \textbf{upper} bounds --- the
joint cost is lower, because suppressing an early rejection lowers $R$ --- and the largest ratio is
heavy-tail driven. Panel (b) is the construction of \cref{sec:groupcal}, which padding provably
cannot suppress: calibrating on \emph{groups} shrinks the ceiling, so its cold-start window collapses
to """ + f"{min(r['cold_start_steps'] for r in d['group_max_rows'])}" + r"""--""" + f"{max(r['cold_start_steps'] for r in d['group_max_rows'])}" + r""" and every detection
falls to a few dozen insertions. \emph{Group validity by design plus padding robustness does not buy
attack resistance.} Getting ahead of a target is free under first-flow arrival (send earlier in the
bucket), costs an offline keyspace search under a public hash, and cannot be ranked offline at all
under a keyed one --- which removes the \emph{search}, not the attack. Both within-bucket orders are reported: the \textbf{canonical} metadata key-hash
\cref{tab:main} uses, and \textbf{first-flow} arrival, the optimistic upper bound over the orders we
audit (\cref{apptab:ordering}).}
\label{apptab:insertion}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{rlr rr rr c}
\toprule
\multicolumn{8}{c}{(a) the shipped flow-level pipeline} \\
\midrule
 & & & \multicolumn{2}{c}{per episode} & \multicolumn{2}{c}{silence the window} & \\
\cmidrule(lr){4-5}\cmidrule(lr){6-7}
pos & order & det. & insert & pad (flows) & insert & pad (upper) & cheaper \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}}

\vspace{4pt}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{rrrrrrr}
\toprule
\multicolumn{7}{c}{(b) the group-calibrated \textsc{max} pipeline --- padding cannot suppress it at all} \\
\midrule
pos & groups & firing & detections & cold start & targeted $G^\star$ & window $G$ \\
\midrule
""" + "\n".join(gl) + r"""
\bottomrule
\end{tabular}}
\end{table}"""
    write("insertion", body)


# =======================================================================================
# 30. blindkey  [table]  src=t63_blindkey.json
#     What a SECRET canonical-order seed costs the insertion attacker: the public-hash cost is
#     G* USEFUL keys plus a free offline search; the keyed cost is N INSTANTIATED keys, because
#     the adversary cannot tell which of them landed ahead of the target.
# =======================================================================================
def t_blindkey():
    d = load("t63_blindkey")
    s = d["summary"]
    lines = []
    for r in d["rows"]:
        pos = f"{r['pos']:.2f}"
        od = {"keyhash": "public", "keyed": "keyed"}[r["order"]]
        if not r.get("n_targets"):
            lines.append(f"{pos} & {od} & 0 & --- & --- & --- & --- & --- & --- \\\\")
            continue
        g = r["public_gstar_front"]
        u = r["target_hash_quantile"]
        # medians come from the artefact, never from arithmetic here: a number computed while
        # typesetting is one no artefact gate can check.
        lines.append(
            f"{pos} & {od} & {r['n_targets']} & {min(u):.3f}--{max(u):.3f} & "
            f"{cm(min(g))}--{cm(max(g))} & {cm(round(r['N50_median']))} & "
            f"{cm(round(r['N90_median']))} & {cm(round(r['N99_median']))} & "
            f"{r['blind_over_public_ratio_median']:.1f}$\\times$ \\\\")
    body = r"""\begin{table}[t]
\centering
\caption{What a secret seed for the \textbf{canonical} key-hash order costs the insertion attacker
(e-LOND, seed 0): the public-hash cost $G^{\star}$ against the keyed-hash budgets $N_{50/90/99}$ over
""" + str(s["n_rep"]) + r""" draws, and their ratio ($N_{99}$ against the certain public suppression). Design and
reading: \cref{sec:transfer}.}
\label{apptab:blindkey}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{llrrrrrrr}
\toprule
 & & & & public & \multicolumn{3}{c}{keyed: instantiated keys} & blind \\
\cmidrule(lr){6-8}
pos & order & targets & $u$ & $G^{\star}$ & $N_{50}$ & $N_{90}$ & $N_{99}$ & $N_{99}/G^{\star}$ \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}}
\par\vspace{3pt}
{\footnotesize\raggedright \emph{Notes.} ``pos'': the window's chronological position; ``targets'':
detected episodes under that order; ``$u$'': the target's own hash quantile, unknown to a blind adversary; ``$G^{\star}$'': hypotheses an adversary who
knows the ranking must instantiate ahead of the target on that same stream; ``$N_{p}$'': distinct
$(\mathrm{SrcIP},\mathrm{DstIP})$ pairs a blind adversary must send traffic between to suppress the
target with probability $p$, located on a six-points-per-decade grid and so exact to within
$""" + f"{s['bracket_width_max']:.2f}" + r"""\times$ and no further; the $N_{p}$ cells are medians over the row's targets;
last column: $N_{99}$ against the certain public $G^{\star}$, the nearest matched-reliability comparison
the grid offers ($99\%$ against $100\%$), a reliability budget rather than a lower bound. Rows with no
detection carry no cost claim.\par}
\end{table}"""
    write("blindkey", body)
    write_prose("blindkeyprose", r"""\emph{How the keyed-hash budget is measured.} Under a public hash the adversary ranks candidate keys
offline for free and instantiates only the $G^{\star}$ that land ahead of the target; under a keyed
hash it cannot rank at all and must instantiate blind, and the cost scales as $G^{\star}/u$ with the
target's own hash quantile $u$, which is why the spread in \cref{apptab:blindkey} is wide and
heavy-tailed. Every one of the """ + str(s["n_targets_total"]) + r""" targets falls in every draw at a budget of
""" + cm(s["max_budget"]) + r""" keys, so the seed does not stop the attack; at the nearest matched reliability,
$N_{99}$ against the certain public $G^{\star}$, it multiplies the instantiated-key cost by a median
$""" + f"{s['blind_over_public_median']:.1f}" + r"""\times$ (range $""" + f"{s['blind_over_public_min']:.1f}" + r"""$--$""" + f"{s['blind_over_public_max']:.1f}" + r"""\times$). Suppression is
verified by replay at every $G^{\star}$, not asserted from a closed form, and the replayed success
probability is compared with the binomial lower bound $P(\mathrm{Bin}(N,u)\ge G^{\star}_{\text{targeted}})$:
it falls short of that bound by at most """ + f"{s['max_binomial_lower_bound_violation']:.3f}" + r""" in probability, the Monte Carlo
tolerance of """ + str(s["n_rep"]) + r""" draws. None of this touches Surface~A padding (\cref{thm:padding}), which
needs no key.
""")


# =======================================================================================
#  apptab:nonoracle -- what Surface A costs an attacker WITHOUT the oracle state.
#  Pure re-analysis (t66), so nothing here can disagree with the runs it reads.
# =======================================================================================
def _bracket(r):
    """the padded arity's position in the DEPLOYMENT arity distribution, as an exceedance range."""
    b = r.get("arity_bracket") or {}
    lo, hi = b.get("upper_deployment_exceedance"), b.get("lower_deployment_exceedance")
    if lo is None or hi is None:
        return "---"
    return f"{100*lo:.1f}--{100*hi:.1f}\\%"


def t_nonoracle():
    d = load("t66_nonoracle")
    CS_TBL = d["config"]["multipliers"]
    mult, absol = d["multiplier"], d["absolute"]

    def mrow(key):
        v = mult[key]
        c = v["c_min_integer_defeating_all"]
        r = next((x for x in v["by_c"]
                  if x["c"] >= c and x.get("defeated") == x.get("of")), None)
        if r is None:
            # No pre-committed multiplier defeats every alert in this cell.  Emit the row saying so
            # rather than dropping it: a silently missing row reads as "not measured".
            return (f"{v['order']} & {v['pos']:.2f} & {v['n_alerts']} & "
                    f"{v['c_required_median']:.2f} & {v['c_required_max']:.2f} & "
                    f"\\emph{{none $\\le$ {max(CS_TBL)}}} & --- & --- & --- & --- \\\\")
        return (f"{v['order']} & {v['pos']:.2f} & {v['n_alerts']} & "
                f"{v['c_required_median']:.2f} & {v['c_required_max']:.2f} & {r['c']} & "
                f"{cm(r['median_added'])} & {r['median_overprovision']:.1f}$\\times$ & "
                f"{cm(r['median_padded_arity'])} & {_bracket(r)} \\\\")

    mlines = [x for x in (mrow(k) for k in sorted(mult)) if x]
    alines = [(f"{absol[k]['order']} & {absol[k]['pos']:.2f} & {absol[k]['seed']} & "
               f"{absol[k]['n_alerts']} & {cm(absol[k]['N_for_50pct'])} & "
               f"{cm(absol[k]['N_for_90pct'])} & {cm(absol[k]['N_for_all'])} \\\\")
              for k in sorted(absol)]
    nchk = d["summary"]["closed_form_selfcheck_episodes"]

    body = (r"""\begin{table}[t]
\centering
\caption{Surface~A priced \textbf{without oracle state}: a re-analysis of the same per-episode
$(m,S,\alphat)$ the oracle costs come from, with no re-simulation --- the closed form """
            + r"\eqref{eq:rstar}" + r""" is re-derived from the stored fields on all """ + str(nchk) + r"""
episodes as a read-back check. \emph{Multiplier}: append $(c-1)m$ flows, that is, multiply your own
episode by $c$. It defeats the alert iff $c\ge1+r^{\star}_t/m_t$ and needs \textbf{no} estimate of $S_t$,
$\alphat$ or $\nCal$ --- only $m$, which on LSPR23 is the attacker's own flow count, since every host
pair carrying attack traffic is 100\% malicious. ``padded arity'' is $cm$, and the column beside it answers
the deployment-side question --- would a volume monitor see the pad --- as the fraction of
\emph{deployment} episodes larger than the padded one, bracketed by the two stored group-size quantiles
that straddle it. Those quantiles are \emph{not} shown and are \emph{not} benign deployment values:
they are quantiles of source--destination group size over the \emph{calibration} slice, unfiltered by
label, which is why the deployment exceedance and not the quantile is what the claim rests on. Rows are given under \textbf{both}
within-bucket orders --- the \textbf{canonical} metadata hash the paper reports and \textbf{first-flow}
arrival, retained as the optimistic upper bound. \emph{Absolute}: append a
pre-committed flat $N$ flows, which needs nothing at all; $N$ is reported at the fraction of that
cell's alerts it suppresses. The multiplier arm covers the two windows for which per-episode arities
are stored; the secondary window appears in the absolute arm only. Both strategies are upper bounds
on the oracle cost, and both are optimistic on a benign-inclusive stream, where $m$ also contains
benign flows the attacker cannot see.}
\label{apptab:nonoracle}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{llrrrrrrrr}
\toprule
\multicolumn{10}{l}{\emph{multiplier --- needs the attacker's own arity $m$ and nothing else}} \\
order & pos & alerts & med.\ $c$ & max $c$ & $c$ used & med.\ added & vs oracle & padded arity & \% deployment larger \\
\midrule
""" + "\n".join(mlines) + r"""
\bottomrule
\end{tabular}}

\vspace{3pt}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{llrrrrr}
\toprule
\multicolumn{7}{l}{\emph{absolute --- a flat pad: executing it needs no state, but the $N$ below is read off the realised $r^{\star}_t$ distribution}} \\
order & pos & seed & alerts & $N$ for 50\% & $N$ for 90\% & $N$ for all \\
\midrule
""" + "\n".join(alines) + r"""
\bottomrule
\end{tabular}}
\end{table}""")
    write("nonoracle", body)

# =======================================================================================
#  apptab:aitorder -- the AIT transfer under BOTH within-bucket orders (t67).
#  Resequencing only: the per-fold fit, scores, calibration and e-values are order-free, so the
#  two arms differ by the permutation alone.  t67 re-derives the stored first-flow arm as a
#  read-back check that it runs the same chain.
# =======================================================================================
def t_aitorder():
    d = load("t67_ait_order")
    arms, summ = d["arms"], d["summary"]
    order_label = {"first-flow": "first-flow", "keyhash": "canonical"}
    _rej = {k: sum(r["elond_rej"] for r in arms[k]["rows"]) for k in arms}
    _tru = {k: sum(r["elond_true"] for r in arms[k]["rows"]) for k in arms}
    _fdp = {k: (_rej[k] - _tru[k]) / _rej[k] for k in arms}
    lines = []
    for key in ("keyhash", "first-flow"):
        a = arms[key]["summary"]
        rows = {o["org"]: o for o in arms[key]["rows"] if o.get("n_detected")}
        lines.append(r"\multicolumn{5}{l}{\emph{" + order_label[key] +
                     r" order} --- " + f"{a['n_suppressible']}" + r"/" + f"{a['n_detected']}" +
                     r" suppressible} \\")
        for org in sorted(rows):
            o = rows[org]
            med = o.get("median_rstar_empirical")
            med_s = "--" if med is None else (cm(int(med)) if float(med).is_integer()
                                              else f"{med:.1f}")
            lines.append(f"\\texttt{{{org}}} & {o['n_detected']}/{o['n_mal_ep']} & {med_s} & "
                         f"{o.get('n_suppressible', '--')}/{o['n_detected']} & "
                         f"{o['mean_success_rate']:.2f} \\\\")
        if key == "keyhash":
            lines.append(r"\midrule")

    body = (r"""\begin{table}[t]
\centering
\caption{The AIT transfer under \textbf{both} within-bucket orders, flow-only folds. This is a
\emph{resequencing}: the leave-one-organisation-out feature selection, the per-fold detector fit, the
scores, the chronological in-organisation calibration and the e-values are all computed before
episodes are ordered, so the two arms differ by the permutation alone; the canonical arm uses the same
key-hash rule as the LSPR23 results. The stored first-flow arm is re-derived here as a read-back
check that this is the same chain and not merely a similar one (it reproduces """
            + f"{summ['suppressible_first_flow']}/{summ['detections_first_flow']}" + r"""). The
canonical order detects fewer episodes, as on LSPR23, and the alerts it does issue are
\emph{cheaper} to suppress --- per-organisation median $r^{\star}_{t,\mathrm{emp}}$ falls from """
            + f"{min(summ['first_flow']['median_rstar_by_org'].values()):g}--"
              f"{max(summ['first_flow']['median_rstar_by_org'].values()):g}" + r""" to """
            + f"{min(summ['canonical']['median_rstar_by_org'].values()):g}--"
              f"{max(summ['canonical']['median_rstar_by_org'].values()):g}" + r""" flows. The
host-conditioned arm runs at all eight organisations and is left on first-flow
(\cref{apptab:r7ait}). ``det./mal.'' counts \emph{true} detections against malicious episodes;
the eight per-organisation runs issue """
            + f"{_rej['keyhash']}" + r""" rejections under the canonical order and """
            + f"{_rej['first-flow']}" + r""" under first-flow, carrying """
            + f"{_rej['keyhash'] - _tru['keyhash']}" + r""" and """
            + f"{_rej['first-flow'] - _tru['first-flow']}" + r""" false discoveries
respectively (pooled realised $\FDP$ """
            + f"{_fdp['keyhash']:.3f}" + r""" and """
            + f"{_fdp['first-flow']:.3f}" + r"""); costs are empirical replay medians
$r^{\star}_{t,\mathrm{emp}}$, at or above the zero-pad lower bound $r^{\star}_t$ (\cref{apptab:aitsupp}
lists both for the first-flow arm).}
\label{apptab:aitorder}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lrrrr}
\toprule
organisation & det./mal. & median $r^{\star}_{t,\mathrm{emp}}$ & suppressible & per-draw succ. \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}}
\end{table}""")
    write("aitorder", body)


# =======================================================================================
#  apptab:joint -- the joint attacked-trajectory rerun (t75).  The controller is RE-RUN over the
#  padded stream, so its rejection count responds to the attack; every other cost in the paper is
#  per-alert at the unperturbed level.  Zero-evidence pads (the pool has no firing flow, asserted).
# =======================================================================================
# =======================================================================================
# 41. joint76  [table + prose]  src=t76_joint_ait.json
#     the joint attack on the benign-inclusive AIT stream: real pads, live controller state,
#     causal host-context recomputation, and the two template pools.
# =======================================================================================
def t_joint76():
    d = load("t76_joint_ait")
    cfg = d["config"]; orgs = d["orgs"]
    def cell(o, arm, slot, g, key="remaining_own"):
        return orgs[o][arm][slot][g][key]["median"]
    flow = [o for o in orgs if "flow" in orgs[o]]
    host = [o for o in orgs if "host" in orgs[o]]

    def tot(arm, slot, g, key):
        src = flow if arm == "flow" else host
        return sum(orgs[o][arm][slot][g][key]["median"] for o in src)

    rows = []
    for o in flow:
        r = orgs[o]["flow"]; b = r["baseline"]
        line = [o, f"{b['poly']['own_alerts']}/{b['uniform']['own_alerts']}",
                f"{b['poly']['nonown_alerts']}/{b['uniform']['nonown_alerts']}",
                f"{r['greedy']['n_unavailable'] if False else r['greedy']['poly']['n_unavailable']}/{r['n_own']}"]
        for g in ("poly", "uniform"):
            line.append(f"{cell(o,'flow','greedy_t54pool',g):.0f}")
            line.append(f"{cm(int(round(cell(o,'flow','greedy_t54pool',g,'total_pads'))))}")
            line.append(f"{cell(o,'flow','greedy',g):.0f}")
            line.append(f"{cm(int(round(cell(o,'flow','greedy',g,'total_pads'))))}")
        rows.append(" & ".join(line) + r" \\")
    body_rows = "\n".join(rows)

    # totals used by the body text, recomputed here so the prose cannot drift from the artefact
    t_pool = {g: tot("flow", "greedy_t54pool", g, "total_pads") for g in ("poly", "uniform")}
    t_caus = {g: tot("flow", "greedy", g, "total_pads") for g in ("poly", "uniform")}
    rem_pool = {g: tot("flow", "greedy_t54pool", g, "remaining_own") for g in ("poly", "uniform")}
    rem_caus = {g: tot("flow", "greedy", g, "remaining_own") for g in ("poly", "uniform")}
    base = {g: sum(orgs[o]["flow"]["baseline"][g]["own_alerts"] for o in flow) for g in ("poly", "uniform")}
    rstar = {g: sum(orgs[o]["flow"]["baseline"][g]["rstar_sum"] for o in flow) for g in ("poly", "uniform")}
    eps = [e for o in flow for e in orgs[o]["flow"]["own_episodes"]]
    n_un = sum(1 for e in eps if e["pool_unavailable"])
    n_zero = sum(1 for e in eps if e["n_templates"] == 0)
    mk = {g: sum(orgs[o]["flow"]["multiplier"]["c_int/k0_m_atk"][g]["remaining_own"]["median"] for o in flow)
          for g in ("poly", "uniform")}
    mo = {g: sum(orgs[o]["flow"]["multiplier"]["c_int/oracle_m_total"][g]["remaining_own"]["median"] for o in flow)
          for g in ("poly", "uniform")}
    mo_pool = {g: sum(orgs[o]["flow"]["multiplier"]["c_int/oracle_m_total/t54pool"][g]["remaining_own"]["median"]
                      for o in flow) for g in ("poly", "uniform")}
    mk_pool = {g: sum(orgs[o]["flow"]["multiplier"]["c_int/k0_m_atk/t54pool"][g]["remaining_own"]["median"]
                      for o in flow) for g in ("poly", "uniform")}
    hostrow = []
    for o in host:
        r = orgs[o]["host"]; b = r["baseline"]
        hostrow.append(f"\\texttt{{{o}}} issues {b['poly']['own_alerts']} and {b['uniform']['own_alerts']} "
                       f"own alerts and {b['poly']['nonown_alerts']} and {b['uniform']['nonown_alerts']} "
                       f"non-attacker alerts; the deployment pool clears all of them for "
                       f"{cm(int(round(cell(o,'host','greedy_t54pool','poly','total_pads'))))} and "
                       f"{cm(int(round(cell(o,'host','greedy_t54pool','uniform','total_pads'))))} flows, "
                       f"the victim's prior traffic leaves {cell(o,'host','greedy','poly'):.0f} and "
                       f"{cell(o,'host','greedy','uniform'):.0f}")
    prose = r"""\emph{The joint attack on AIT.} \Cref{apptab:joint76} re-runs e-LOND over the padded stream for
each organisation, so the controller's rejection count responds to the attack and, on the
host-conditioned arm, every later flow on the attacked pair is re-scored as the pads arrive. Each figure
is the median over """ + str(cfg["d_traj"]) + r""" pad-sampling trajectories; the totals below sum those medians over the eight
organisations and are not counts from a single run. Two template pools are separated throughout: the
\emph{deployment} pool is the benign-to-victim traffic the per-alert arms of \cref{apptab:aitsupp} use,
and the \emph{prior} pool is restricted to flows the victim had received before the attacker's own last
flow in the episode. An episode whose prior pool holds fewer than """ + str(cfg["n_min"]) + r""" flows is never padded.

With the deployment pool the campaign costs """ + cm(int(round(t_pool['poly']))) + r""" and """ + cm(int(round(t_pool['uniform']))) + r""" flows against per-alert sums of
""" + cm(rstar['poly']) + r""" and """ + cm(rstar['uniform']) + r""", leaving """ + f"{rem_pool['poly']:.0f}" + r""" and """ + f"{rem_pool['uniform']:.0f}" + r""" of the """ + str(base['poly']) + r""" and """ + str(base['uniform']) + r""" own alerts. With the prior pool
""" + f"{rem_caus['poly']:.0f}" + r""" and """ + f"{rem_caus['uniform']:.0f}" + r""" remain and no organisation is cleared, at """ + cm(int(round(t_caus['poly']))) + r""" and """ + cm(int(round(t_caus['uniform']))) + r""" flows: """ + str(n_un) + r""" of the
""" + str(len(eps)) + r""" attacker-owned episodes have too little prior traffic to imitate and """ + str(n_zero) + r""" have none at all, and those
episodes carry most of what survives. On the host-conditioned arm, """ + "; ".join(hostrow) + r""".

The state-free multiplier $c=\lfloor\rho\rfloor+1$ of \cref{cor:dilution} leaves """ + f"{mk['poly']:.0f}" + r""" and """ + f"{mk['uniform']:.0f}" + r""" alerts standing
with the prior pool. Sizing it on the episode's full arity rather than the attacker's own flow count
changes nothing there (""" + f"{mo['poly']:.0f}" + r""" and """ + f"{mo['uniform']:.0f}" + r"""), and changes the outcome only with the deployment pool
(""" + f"{mo_pool['poly']:.0f}" + r""" and """ + f"{mo_pool['uniform']:.0f}" + r""" against """ + f"{mk_pool['poly']:.0f}" + r""" and """ + f"{mk_pool['uniform']:.0f}" + r"""): what the attacker does not know about co-resident benign
flows costs it nothing while cover traffic is the binding constraint."""
    write_prose("joint76prose", prose)

    body = r"""\begin{table*}[t]
\centering
\caption{Joint attack on the benign-inclusive AIT stream, flow-only detector, canonical order, seed 0,
medians over """ + str(cfg["d_traj"]) + r""" pad-sampling trajectories. ``own'' and ``other'' are the baseline alerts on
attacker-owned and other episodes, horizon-free/horizon-aware. ``no pool'' counts own episodes whose
prior traffic to the victim is under """ + str(cfg["n_min"]) + r""" flows. For each spending rule the attacker is run twice: from the
\emph{deployment} pool the per-alert arms use, and from the victim's \emph{prior} traffic only; each pair
of columns gives the alerts still standing and the flows spent. Reading and the host-conditioned arm:
\cref{app:ait}.}
\label{apptab:joint76}
\footnotesize
\setlength{\tabcolsep}{4pt}
\begin{tabular}{lcccrrrrrrrr}
\toprule
& & & & \multicolumn{4}{c}{horizon-free} & \multicolumn{4}{c}{horizon-aware} \\
\cmidrule(lr){5-8}\cmidrule(lr){9-12}
& & & & \multicolumn{2}{c}{deployment} & \multicolumn{2}{c}{prior} & \multicolumn{2}{c}{deployment} & \multicolumn{2}{c}{prior} \\
\cmidrule(lr){5-6}\cmidrule(lr){7-8}\cmidrule(lr){9-10}\cmidrule(lr){11-12}
org & own & other & no pool & left & flows & left & flows & left & flows & left & flows \\
\midrule
""" + body_rows + r"""
\bottomrule
\end{tabular}
\end{table*}"""
    write("joint76", body)


def t_joint():
    d = load("t75_joint_rerun")
    cells = d["cells"]
    regime = {"poly": "horizon-free", "uniform": "horizon-aware"}

    def row(pos, gk):
        c = cells[f"{pos}_keyhash_{gk}"]
        u, st, a, cr = c["unperturbed"], c["static"], c["adaptive"], c["critical_multiplier"]
        share = a["deployment_share_at_least_median_padded_only"]
        return (f"{pos} & {regime[gk]} & {u['true_detections']} ({u['false_discoveries']}) & "
                f"{cm(u['median_r_static'])} / {cm(u['total_r_static'])} & "
                f"{st['remaining_true_max']} & "
                f"{cm(a['total_cost'])} ({a['joint_over_static']:.3f}) & "
                f"{a['median_r_adaptive_padded_only']:g} & {a['n_spared_by_lower_level']} & "
                f"{a['median_padded_arity_padded_only']:g} ({cm(a['median_padded_arity_static'])}) & "
                f"{100*share:.1f}\\% & {cr['c_int']} \\\\")

    def caprow(n):
        out = [f"{cm(n)}"]
        for pos in ("0.55", "0.62"):
            c = cells[f"{pos}_keyhash_uniform"]
            r = next(x for x in c["capped_adaptive"] if x["cap"] == n)
            pa = c["unperturbed"]["true_detections"] - r["per_alert_suppressible_under_cap"]
            out.append(f"{r['remaining_true']} ({r['n_fired_structural']}+{r['n_fired_cascade_victims']})")
            out.append(f"{pa}")
            out.append(f"{100*r['benign_truncated']:.2f}\\%")
        return " & ".join(out) + " \\\\"

    rows = [row(p, g) for p in ("0.55", "0.62") for g in ("poly", "uniform")]
    caps = [caprow(n) for n in (30, 100, 300, 1000, 3000)]
    c55 = cells["0.55_keyhash_uniform"]; c62 = cells["0.62_keyhash_uniform"]
    body = (r"""\begin{table}[t]
\centering
\caption{Joint zero-evidence controller-state rerun: LSPR23, detector seed 0, \textbf{canonical}
order, two-hour host-pair episodes, e-LOND, both windows and both spending regimes. Upper panel: the
static, sequential and state-free attackers of \cref{sec:costcurve}; lower panel: the per-host-pair
volume cap against the sequential attacker. Design and reading: \cref{app:joint}.}
\label{apptab:joint}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{llrrrrrrrrr}
\toprule
window & regime & true det.\ (FD) & median $r^{\star}_t$ / $\sum_{t\in\mathcal D} r^{\star}_t$ & static: remain & $J_{\mathrm{seq}}$ ($\div$ $\sum_{t\in\mathcal D} r^{\star}_t$) & med.\ pad (padded) & spared & padded arity (per-alert) & \% episodes $\ge$ & $c_{\mathrm{int}}$ \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}}

\vspace{3pt}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{rrrrrrr}
\toprule
& \multicolumn{3}{c}{0.55 horizon-aware (""" + str(c55["unperturbed"]["true_detections"]) + r""" true det.)} & \multicolumn{3}{c}{0.62 horizon-aware (""" + str(c62["unperturbed"]["true_detections"]) + r""" true det.)} \\
cap $n$ & fire (struct.+casc.) & per-alert fire & benign $>n$ & fire (struct.+casc.) & per-alert fire & benign $>n$ \\
\midrule
""" + "\n".join(caps) + r"""
\bottomrule
\end{tabular}}
\par\vspace{3pt}
{\footnotesize\raggedright \emph{Notes.} ``true det.\ (FD)'': true detections and false discoveries on
the unperturbed run; ``median $r^{\star}_t$ / $\sum_{t\in\mathcal D} r^{\star}_t$'': the per-alert oracle cost and the
per-alert sum of \cref{tab:costcurve}. ``remain'': true detections still rejected after the rerun (the
one 0.62 horizon-aware false discovery also disappears). ``padded'' statistics are over the alerts the
sequential attacker actually padded; ``spared'' alerts fire only at a level raised by earlier rejections
and need no pad once those are gone. ``padded arity (per-alert)'': the sequential attacker's median
padded arity, with the per-alert reading of \cref{sec:costcurve} in parentheses; ``\% episodes $\ge$'':
the share of deployment episodes at least that large. $c_{\mathrm{int}}=\lfloor\rho\rfloor+1$
(\cref{cor:dilution}). Lower panel: ``fire (struct.+casc.)'' splits the surviving alerts into structural
(the pad would not fit even at $R=0$) and cascade victims (it would have fitted at $R=0$); ``per-alert
fire'' is $m_t+r^{\star}_t>n$ on the unperturbed pads; ``benign $>n$'': the share of benign deployment
episodes whose arity exceeds the cap, i.e.\ the episodes an implemented admission policy would alter;
no baseline episode is truncated or rescored in this experiment. Caps are the sampled grid; nothing is
claimed between grid points.\par}
\end{table}""")
    write("joint", body)
    cr55, cr62 = c55["critical_multiplier"], c62["critical_multiplier"]
    write_prose("jointprose", r"""\subsection{The joint controller-state rerun}\label{app:joint}

The per-alert costs of \cref{sec:costcurve} price each alert at the level it received on the
unperturbed trajectory. \Cref{apptab:joint} instead propagates the zero-evidence pads that the
real-flow replay of \cref{sec:replay} validates through the controller, which is re-run over the
padded stream, so that its rejection count --- and with it every later level
$\alphat=\alpha\gamma_t(R_{t-1}{+}1)$ --- responds to the attack. The black-box pool contains no flow
that reaches the conformal tail at either window, so this is the zero-evidence limit of the real-flow
replay, not a second replay. Three attackers are run. \emph{Static}: the per-alert oracle pads of
\cref{tab:costcurve}, applied to every true detection at once. \emph{Sequential}: a greedy oracle
that pads each of its own episodes that would fire at the \emph{live} level by the minimum; its total
$J_{\mathrm{seq}}$ is one strategy's cost on this stream, an upper bound on the minimum joint cost
over all attacker-controlled episodes in the window. \emph{State-free}: every own episode is
multiplied by the integer $c_{\mathrm{int}}=\lfloor\rho\rfloor+1$ of \cref{cor:dilution}, which is
$""" + str(cr55["c_int"]) + r"""$ at the primary and $""" + str(cr62["c_int"]) + r"""$ at the secondary
window, and silences the arm with no controller state. With $R=0$ throughout, the stream-specific
boundary is $c_{\mathrm{crit}}=\max_j \Ev_j\,\alpha\gamma_{t_j}\le\ceil\alpha/T=\rho$, with equality
when a malicious episode attains the ceiling, as one does at each window ($c_{\mathrm{crit}}=\rho=""" + f"{cr55['c_crit']:.3f}" + r"""$
and $""" + f"{cr62['c_crit']:.3f}" + r"""$); rejection is inclusive, so the boundary must be strictly
exceeded, the real-valued checks just above and below $c_{\mathrm{crit}}$ are a continuous relaxation,
and only the integer $c_{\mathrm{int}}$ is a realisable prescription. The lower panel re-runs the sequential attacker under a per-host-pair volume cap $n$:
it pads only if $m_t+r\le n$ and otherwise lets the alert fire and raise $R$, and each surviving alert
is classified as structural or as a cascade victim by whether its pad would have fitted at $R=0$.
Every padded stream was regrouped from flows and asserted against the unperturbed stream on what an
append must leave unchanged --- the episode count, the (source, destination, bucket) key of every
controller position and hence the permutation, each group's first timestamp and its label --- and
asserted to carry arities $m_t+r_t$ and exactly the padded group means $S_t/(m_t+r_t)$ that the
attacker was priced on; the padded means differ from the unperturbed ones by construction.
""")


# =======================================================================================
# 42. joint76rel  [table* + prose]  src=t76_joint_ait.json           (round 32, review point 4)
#     reliability of the joint AIT attack over the 100 pad-sampling trajectories: P(every own
#     alert silenced), median and 95th percentile of the residual count and of the flows spent.
#     The stage stores median/p5/p95/min/max/mean per cell, not the trajectories, so the upper
#     quantile reported is the 95th; a 90th percentile cannot be recovered without re-running.
# =======================================================================================
def t_joint76rel():
    d = load("t76_joint_ait")
    orgs = d["orgs"]; cfg = d["config"]
    flow = [o for o in orgs if "flow" in orgs[o]]
    host = [o for o in orgs if "host" in orgs[o]]
    ARMS = (("greedy_t54pool", None), ("greedy", None), ("multiplier", "c_int/k0_m_atk"))

    def stats(rec, slot, sub, g):
        r = rec[slot][sub][g] if sub else rec[slot][g]
        return r["p_all_silenced"], r["remaining_own"], r["total_pads"]

    def g_(x):
        return f"{x:g}"

    rows = []
    varying = 0; cells = 0; spread = []
    p_all_dep = []; dep_survivor_cells = []
    for arm, names in (("flow", flow), ("host", host)):
        for o in names:
            rec = orgs[o][arm]
            for g in ("poly", "uniform"):
                line = [(r"\texttt{%s}" % o) + (r" \emph{(host)}" if arm == "host" else ""),
                        "horizon-free" if g == "poly" else "horizon-aware"]
                for slot, sub in ARMS:
                    p_all, rem, pads = stats(rec, slot, sub, g)
                    line += [f"{p_all:.2f}", f"{g_(rem['median'])}/{g_(rem['p95'])}",
                             f"{cm(pads['median'])}/{cm(pads['p95'])}"]
                    cells += 1
                    if rem["p5"] != rem["p95"]:
                        varying += 1
                    if pads["median"] > 0:
                        spread.append(pads["p95"] / pads["median"])
                    if slot == "greedy_t54pool" and arm == "flow":
                        p_all_dep.append(p_all)
                        if rem["median"] > 0:
                            dep_survivor_cells.append((o, g, rem, p_all))
                rows.append(" & ".join(line) + r" \\")
    n_dep = len(p_all_dep); n_dep_certain = sum(1 for p in p_all_dep if p == 1.0)
    assert len(dep_survivor_cells) == n_dep - n_dep_certain - sum(1 for p in p_all_dep if 0 < p < 1)
    def _rng(rem):
        return (f"exactly {g_(rem['min'])}" if rem["min"] == rem["max"]
                else f"{g_(rem['min'])}--{g_(rem['max'])}")
    surv_txt = "; ".join(f"\\texttt{{{o}}} under {'horizon-free' if g == 'poly' else 'horizon-aware'} spending, "
                         f"where {_rng(rem)} alert{'s' if rem['max'] != 1 else ''} "
                         f"survive{'s' if rem['max'] == 1 else ''} in every trajectory ($P=%.2f$)" % p_all
                         for o, g, rem, p_all in dep_survivor_cells)
    body = r"""\begin{table*}[t]
\centering
\caption{Reliability of the joint AIT attack over the """ + str(cfg["d_traj"]) + r""" pad-sampling trajectories,
\textbf{canonical} order, seed 0. For each organisation and spending rule, and for each attacker arm of
\cref{tab:aitboundary}: $P(\text{all})$, the fraction of trajectories in which every attacker-owned
alert is silenced; ``left'', the median and 95th percentile of the residual own-alert count; ``flows'',
the median and 95th percentile of the flows spent. The 95th percentile is the upper quantile the stage
stores (linearly interpolated, so a count can be fractional); the trajectories themselves were not
retained, so no 90th percentile is available. Flow-only
detector on all eight organisations; the two host-conditioned rows are the joint host arm.}
\label{apptab:joint76rel}
\footnotesize
\setlength{\tabcolsep}{2.4pt}
\begin{tabular}{llrrrrrrrrr}
\toprule
& & \multicolumn{3}{c}{sequential oracle, deployment pool} & \multicolumn{3}{c}{sequential oracle, prior pool} & \multicolumn{3}{c}{state-free $c=\lfloor\rho\rfloor+1$, prior pool} \\
\cmidrule(lr){3-5}\cmidrule(lr){6-8}\cmidrule(lr){9-11}
org & spending & $P(\text{all})$ & left med/p95 & flows med/p95 & $P(\text{all})$ & left med/p95 & flows med/p95 & $P(\text{all})$ & left med/p95 & flows med/p95 \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table*}"""
    write("joint76rel", body)
    write_prose("joint76relprose", r"""\emph{Reliability over trajectories.} A summed median can hide a bimodal outcome (a median of
zero survivors is compatible with many trajectories having some), so \cref{apptab:joint76rel} reports,
per organisation, spending rule and attacker arm, the probability that every attacker-owned alert is
silenced and the 95th percentile of the residual count and of the cost alongside the median. The
residual count is essentially not a sampling quantity here: in """ + str(cells - varying) + r""" of the
""" + str(cells) + r""" cells its 5th and 95th percentiles coincide, and in the remaining """ + str(varying) + r""" they
differ by one alert. With the deployment pool the sequential oracle silences every own alert in
every trajectory in """ + str(n_dep_certain) + r""" of the """ + str(n_dep) + r""" flow-only cells; the exception is
""" + surv_txt + r""". What pad sampling does move is the cost: the 95th percentile exceeds the median by
up to a factor of """ + f"{max(spread):.2f}" + r""" (median ratio """ + f"{sorted(spread)[len(spread)//2]:.2f}" + r""" across cells). The
variation that matters is therefore across organisations, not across pad draws, and the sums of
medians in \cref{tab:aitboundary} should be read as eight nearly deterministic per-organisation
outcomes added together, not as one typical campaign.""")


# =======================================================================================
# 43. cor2diag  [table* + prose]  src=t77_cor2_premise.json + t76_joint_ait.json   (round 32, point 2)
#     Corollary 2's premise measured directly on the attacked AIT streams: the largest
#     non-attacker evidence relative to the cold-start threshold T/alpha, the non-attacker
#     alerts that clear the R = 0 level at their own position versus those that fire only at a
#     raised level, the own episodes without a usable prior pool, the firing behaviour of the
#     admitted pads and the residual own alerts (the last three from t76).
# =======================================================================================
def t_cor2diag():
    d77 = load("t77_cor2_premise")
    d76 = load("t76_joint_ait")
    assert d77["control_reproduced"] and d77["n_cells"] == len(d77["rows"])
    orgs = d76["orgs"]

    def pct(fired, total):
        return "--" if total["median"] == 0 else f"{100 * fired['median'] / total['median']:.2f}\\%"

    rows = []; fails = []; at_r0 = 0; nonown_total = 0; raised = 0; nonown_any = 0
    for rec in d77["rows"]:
        o, arm = rec["org"], rec["arm"]; r76 = orgs[o][arm]
        b = rec["baseline"]
        mult = r76["multiplier"]["c_int/k0_m_atk"]
        gp, gu = r76["greedy"]["poly"], r76["greedy"]["uniform"]
        line = [(r"\texttt{%s}" % o) + (r" \emph{(host)}" if arm == "host" else ""),
                f"{rec['rho']:.2f}",
                f"{rec['max_nonown_ratio']:.3f}" if rec["max_nonown_ev"] > 0 else "0",
                str(rec["n_nonown_at_cold_start"]),
                f"{b['poly']['nonown_alerts']} ({b['poly']['nonown_alerts_at_R0']}) / "
                f"{b['uniform']['nonown_alerts']} ({b['uniform']['nonown_alerts_at_R0']})",
                f"{gp['n_unavailable']}/{r76['n_own']}",
                pct(mult["poly"]["pads_fired"], mult["poly"]["total_pads"]),
                f"{pct(gp['pads_fired'], gp['total_pads'])} / {pct(gu['pads_fired'], gu['total_pads'])}",
                f"{mult['poly']['remaining_own']['median']:g}/{mult['uniform']['remaining_own']['median']:g}",
                f"{gp['remaining_own']['median']:g}/{gu['remaining_own']['median']:g}"]
        rows.append(" & ".join(line) + r" \\")
        if rec["premise_fails_cold_start"]:
            fails.append((o, arm, rec["max_nonown_ratio"], rec["n_nonown_at_cold_start"]))
        for g in ("poly", "uniform"):
            nonown_total += b[g]["nonown_alerts"]; at_r0 += b[g]["nonown_alerts_at_R0"]
            raised += b[g]["nonown_alerts_level_raised"]
        nonown_any += int(rec["n_nonown_firing"] > 0)
        # the multiplier stream is regime-independent: its pads fire identically under both rules
        assert mult["poly"]["pads_fired"] == mult["uniform"]["pads_fired"]
    assert at_r0 + raised == nonown_total
    n_cells = len(d77["rows"])
    ceil_all = all(r["own_attains_ceiling"] for r in d77["rows"])
    below = [r for r in d77["rows"] if not r["own_attains_ceiling"]]
    _names = ", ".join(f"\\texttt{{{r['org']}}}" + (" (host)" if r["arm"] == "host" else "") for r in below)
    if below and len({(round(r["c_crit"], 2), round(r["rho"], 2)) for r in below}) == 1:
        below_txt = (_names + f", where the largest attacker evidence gives "
                     f"$c_{{\\mathrm{{crit}}}}={below[0]['c_crit']:.2f}<\\rho={below[0]['rho']:.2f}$"
                     + (" in each" if len(below) > 1 else ""))
    else:
        below_txt = "; ".join(f"\\texttt{{{r['org']}}}" + (" (host)" if r["arm"] == "host" else "") +
                              f", where the largest attacker evidence gives $c_{{\\mathrm{{crit}}}}={r['c_crit']:.2f}<\\rho={r['rho']:.2f}$"
                              for r in below)
    fail_txt = ("; ".join(f"\\texttt{{{o}}}" + (" (host)" if arm == "host" else "") +
                          f" at {ratio:.2f} with {n} episode{'s' if n != 1 else ''} at or above it"
                          for o, arm, ratio, n in fails)) if fails else "none"
    body = r"""\begin{table*}[t]
\centering
\caption{\Cref{cor:dilution}'s premise tested on the joint-attack AIT cells, \textbf{canonical} order,
seed 0. ``max other $\div T/\alpha$'': the largest non-attacker group evidence divided by the
horizon-uniform cold-start threshold ($\ge1$ means the premise fails on that stream); ``$n\ge T/\alpha$'':
non-attacker episodes at or above it. ``other alerts (at $R{=}0$)'': baseline non-attacker alerts under
horizon-free / horizon-aware spending, with the number that clear the $R=0$ level at their own position
in parentheses; the rest fire only at a level raised by earlier rejections. ``no pool'': own episodes with
fewer than 20 prior templates, never padded. ``pads fired'': median share of admitted pads that carry the
ceiling rather than zero, for the state-free multiplier (regime-independent stream) and the sequential
oracle (horizon-free / horizon-aware), both from the prior pool. ``left'': median residual own alerts,
horizon-free / horizon-aware. Under horizon-free spending the multiplier is a heuristic transfer of a
result proved for horizon-uniform spending.}
\label{apptab:cor2diag}
\footnotesize
\setlength{\tabcolsep}{3.5pt}
\begin{tabular}{lrrrrrrrrr}
\toprule
& & \multicolumn{3}{c}{premise: other hypotheses} & own & \multicolumn{2}{c}{pads fired (prior pool)} & \multicolumn{2}{c}{left (prior pool)} \\
\cmidrule(lr){3-5}\cmidrule(lr){7-8}\cmidrule(lr){9-10}
org & $\rho$ & max other $\div T/\alpha$ & $n\ge T/\alpha$ & other alerts (at $R{=}0$) & no pool & $c_{\mathrm{int}}$ & sequential & $c_{\mathrm{int}}$ & sequential \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table*}"""
    write("cor2diag", body)
    write_prose("cor2diagprose", r"""\emph{Testing the premise of \cref{cor:dilution} rather than a proxy.} The corollary needs one thing of
the rest of the stream: no non-attacker hypothesis carries evidence at or above the cold-start
threshold $T/\alpha$. A baseline non-attacker alert does not by itself show that this fails, because
under either spending rule an alert can fire only after earlier rejections have raised the level.
\Cref{apptab:cor2diag} therefore measures the premise directly on the """ + str(n_cells) + r""" streams the joint
attack ran on, rebuilt with the same chain and asserted to reproduce every stored baseline. The
cold-start premise fails on """ + (str(len(fails)) if fails else "none") + r""" of them (""" + fail_txt + r"""); on the others
the largest non-attacker evidence is below $T/\alpha$, and in """ + str(n_cells - nonown_any) + r""" streams no
non-attacker episode carries any evidence at all. Of the """ + str(nonown_total) + r""" baseline non-attacker
alerts over both spending rules, """ + str(at_r0) + r""" clear the $R=0$ level at their own position and
""" + str(raised) + r""" fire only at a raised level. """ + (r"Some attacker episode attains the ceiling in every cell, so $c_{\mathrm{crit}}=\rho$ throughout." if ceil_all else ("An attacker episode attains the ceiling in every cell but " + below_txt + r", so the stream-specific integer $\lfloor c_{\mathrm{crit}}\rfloor+1$ can be smaller than $c_{\mathrm{int}}$ there.")) + r"""
The other three conditions the corollary rests on are read from the joint run itself: own episodes
without a usable prior pool are never padded and account for most of what survives; admitted pads
from the prior pool are not zero-evidence, and where they fire the multiplier's dilution is partly
undone; and the residual counts are the observed outcome. The corollary is stated for horizon-uniform
spending, so its multiplier under horizon-free spending is a heuristic transfer, reported as such.""")

# --- main ------------------------------------------------------------------------------
TABLES = (t_detection, t_procmatrix, t_grouping, t_qsweep, t_transfer,
               t_smoothing, t_restart, t_padpools, t_pools, t_caps, t_addisstate,
               t_units, t_feedback, t_tail, t_audit, t_bates, t_frontier85,
               t_w7coverage, t_w3dilution, t_r7host, t_r7ait, t_ordering, t_addissynth,
               t_aitsupp, t_a1strata, t_uai26, t_groupcal, t_semblur, t_prevalence,
               t_insertion, t_blindkey, t_nonoracle, t_aitorder, t_joint, t_joint76,
               t_joint76rel, t_cor2diag)


def build_all(verbose=True):
    """Write every table (and prose companion) into OUTDIR; returns the list of paths written."""
    _WRITTEN.clear()
    if verbose:
        print(f"Reading JSONs from {RES}")
        print(f"Writing tables to  {Path(OUTDIR)}\n")
    for fn in TABLES:
        fn()
    if verbose:
        print(f"\nDone: {len(TABLES)} table builders, {len(_WRITTEN)} files.")
    return list(_WRITTEN)


def main():
    build_all()


if __name__ == "__main__":
    main()
