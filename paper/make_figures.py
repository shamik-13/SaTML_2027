"""Build main.tex's figures from the artifact results in ../src/lib/out/.

main.tex is the superseded draft; satml.tex is the submission, and its figures are built by
make_figures_satml.py over ../src/lib/figures.py.  fig2_envelope is shared between the two papers
and therefore lives in ../src/lib/figures.py -- it is re-exported here so this script keeps working.

Usage:  python make_figures.py        ->  figures/fig1, fig3, fig4 .pdf (and .png previews)
"""
import json, math
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

OUT = Path(__file__).resolve().parent / "figures"
RES = Path(__file__).resolve().parent.parent / "src" / "lib" / "out"
OUT.mkdir(exist_ok=True)

COL, WIDE = 3.45, 7.10                      # IEEEtran conference column and text widths, inches
INK, MUTE, ACC, WARN = "#1a1a1a", "#6b6b6b", "#0b6fa4", "#b3272d"
PALETTE = ["#0b6fa4", "#b3272d", "#1b7837", "#d95f02", "#7570b3"]

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 6.5,
    "axes.linewidth": 0.6, "grid.linewidth": 0.4, "lines.linewidth": 1.2,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "axes.edgecolor": INK, "text.color": INK, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK,
    "legend.frameon": False, "figure.dpi": 200,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
})

def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{name}.{ext}")
    plt.close(fig)
    print(f"  figures/{name}.pdf")


# Shared with satml.tex, so there is exactly one implementation (../src/lib/figures.py).
import sys as _sys                                                            # noqa: E402
_sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "lib"))
import figures as _figures                                                    # noqa: E402
_figures.OUTDIR = OUT


def fig2_envelope():
    return _figures.fig2_envelope()


def fig1_system():
    """The pipeline, with the two attack surfaces marked where they attach."""
    fig, ax = plt.subplots(figsize=(WIDE, 1.26))
    ax.set_xlim(0, 100); ax.set_ylim(0, 40); ax.axis("off")

    stages = [("network\nflows", 2), ("ML\ndetector", 17.5), ("conformal\nevidence", 33),
              ("group\naggregation", 49.5), ("online error\ncontroller", 66), ("SOC\nalert", 84)]
    w, h, y = 13.0, 9.5, 20.0
    edges = []
    for label, x in stages:
        emph = label.startswith(("group", "online"))
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.35,rounding_size=1.2",
                                    linewidth=1.1 if emph else 0.7,
                                    edgecolor=WARN if emph else INK,
                                    facecolor="#fdf1f1" if emph else "white", zorder=2))
        ax.text(x + w/2, y + h/2, label, ha="center", va="center", fontsize=7.6, zorder=3)
        edges.append((x, x + w))
    for (_, x1), (x0, _) in zip(edges, edges[1:]):
        ax.add_patch(FancyArrowPatch((x1 + 0.4, y + h/2), (x0 - 0.4, y + h/2),
                                     arrowstyle="-|>", mutation_scale=8,
                                     linewidth=0.8, color=MUTE, zorder=1))

    # the ceiling annotation attaches to the conformal-evidence stage
    cx = 33 + w/2
    ax.plot([cx, cx], [y + h + 0.5, y + h + 3.2], color=MUTE, lw=0.6)
    ax.text(cx, y + h + 4.0, r"bounded evidence  $M=(|\mathcal{C}|+1)/k$",
            ha="center", va="bottom", fontsize=7, color=MUTE)

    # the two attack surfaces: captions on separate rows, arrows routed clear of each other
    for x, tag, head, sub, ty in [
            (49.5, "A", "within-hypothesis padding",
             "dilute the merged evidence", 13.0),
            (66.0, "B", "controller-state manipulation",
             "advance the spending index", 3.0)]:
        bx = x + w/2
        ax.add_patch(FancyArrowPatch((bx, ty + 5.2), (bx, y - 0.5), arrowstyle="-|>",
                                     mutation_scale=8, linewidth=1.0, color=WARN, zorder=1))
        ax.text(bx, ty + 2.4, f"{tag}   {head}", ha="center", va="center",
                fontsize=7.2, color=WARN)
        ax.text(bx, ty - 1.4, sub, ha="center", va="center", fontsize=6.6, color=WARN,
                style="italic")

    save(fig, "fig1_system")




def fig3_granularity():
    """Per-window granularity: coarsening buys feasibility (top, t26) and costs resolution ---
    measured as the alert blur against a FIXED 5-min atomic evaluation reference (middle, t47/W7),
    which
    is denominator- and gamma-invariant, unlike episode recall.  Malicious-flow coverage (bottom,
    t26) is a window-specific, detector-set quantity.  Source-dest pair family, five windows, seed
    0.  The middle panel uses the blur rather than episode recall because recall's direction is an
    artifact of the moving denominator and the oracle spending sequence (see sec 4.44)."""
    d = json.load(open(RES / "t26_H4_5pos.json"))
    rows = [r for r in d["rows"] if r["family"] == "src-dst" and r["seed"] == 0]
    w7 = json.load(open(RES / "t47_W7.json"))
    blur = [r for r in w7["rows"] if r["family"] == "src-dst"]
    POS = [0.55, 0.62, 0.70, 0.77, 0.85]

    fig, axes = plt.subplots(3, 1, figsize=(COL, 2.55), sharex=True)

    def plot_panel(ax, src, key, pos_key=lambda r: r["pos"]):
        for i, pos in enumerate(POS):
            pts = sorted(((r["bucket_s"] or 86400, r[key]) for r in src
                          if abs(pos_key(r) - pos) < 1e-9 and r[key] is not None),
                         key=lambda p: p[0])
            if not pts: continue
            ax.plot([p[0] for p in pts], [p[1] for p in pts], marker="o", ms=2.6,
                    color=PALETTE[i], label=f"window {pos}")
        ax.set_xscale("log"); ax.grid(True, color=MUTE, alpha=0.22)

    plot_panel(axes[0], rows, "margin")
    axes[0].set_ylabel("feasibility margin")
    plot_panel(axes[1], blur, "blur_mal_atoms_per_alert", pos_key=lambda r: float(r["pos"]))
    axes[1].set_ylabel("alert blur")
    axes[1].set_yscale("log"); axes[1].set_ylim(0.8, 60)
    plot_panel(axes[2], rows, "flow_cov_elond")
    axes[2].set_ylabel("flow coverage"); axes[2].set_ylim(-0.05, 1.08)

    axes[0].set_yscale("symlog", linthresh=1)
    axes[0].axhline(0, color=INK, lw=0.9)
    axes[0].set_ylim(-2, 4)
    axes[0].text(8e4, -0.55, "margin $=0$ (level $w_0$)", fontsize=6.2, color=INK,
                 va="top", ha="right")
    axes[1].axhline(1, color=INK, lw=0.7, ls=":")
    axes[0].legend(loc="upper left", ncol=2, handlelength=1.4, columnspacing=0.9,
                   borderaxespad=0.4, labelspacing=0.25, fontsize=6.3)

    axes[2].set_xlabel("time-bucket width")
    axes[2].set_xticks([300, 1800, 3600, 7200, 21600, 86400])
    axes[2].set_xticklabels(["5 m", "30 m", "1 h", "2 h", "6 h", "1 d"])
    axes[2].minorticks_off()
    fig.align_ylabels(axes)
    save(fig, "fig3_granularity")


def fig4_attacks():
    """Three panels: Surface A padding at a GUARANTEE window (primary), the real ADDIS state attack,
    and the state attack on a synthetic stream where ADDIS's guarantee genuinely holds."""
    full = json.load(open(RES / "t28b_reallevel.json"))
    # 0.62 = the REPLICATION window; the artefact key predates the round-7 rename and stays.
    # These cost vectors are the FIRST-FLOW arm (13 detections); t28b's canonical arm detects 11
    # at a median of 6 flows, reported in tab:pools.
    guar = full.get("fig4a_guarantee") or full["fig4a_pools"]
    stress = full["fig4a_pools"]                                # 0.85 stress window
    pools = ["generic", "attacker-origin", "protocol-matched", "service-matched", "black-box"]
    nice = {"generic": "generic benign", "attacker-origin": "attacker-origin",
            "protocol-matched": "protocol-matched", "service-matched": "service-matched",
            "black-box": "black-box (no detector access)"}

    fig, axes = plt.subplots(1, 3, figsize=(WIDE, 1.52))
    grid = np.unique(np.concatenate([[1], np.logspace(0, 8.2, 400)]))

    # --- A: padding at the guarantee window 0.62 (primary), 0.85 as a light stress overlay ---
    ax = axes[0]
    for i, p in enumerate(pools):
        costs = np.array(guar["pools"].get(p, []), float)
        if not len(costs):
            continue
        frac = [(costs <= g).mean() for g in grid]
        ax.plot(grid, frac, color=PALETTE[i], label=nice[p], lw=2.8 - 0.5*i, alpha=0.9)
    bb85 = np.array(stress["pools"].get("black-box", []), float)
    if len(bb85):
        ax.plot(grid, [(bb85 <= g).mean() for g in grid], color=MUTE, lw=1.0, ls="--",
                alpha=0.85, label="black-box (0.85 stress)")
    ax.axvline(72, color=INK, lw=0.7, ls=":")
    ax.annotate("median\n$\\approx$72 flows", (72, 0.86),
                textcoords="offset points", xytext=(-7, 0), fontsize=6.0, color=INK,
                linespacing=1.2, va="center", ha="right")
    ax.set_xscale("log")
    ax.set_xlabel("padding flows added to own episode")
    ax.set_ylabel("episodes suppressed")
    ax.set_ylim(0, 1.04); ax.grid(True, color=MUTE, alpha=0.22)
    ax.legend(loc="lower right", handlelength=1.4, borderaxespad=0.3, labelspacing=0.15,
              fontsize=5.2)
    ax.set_title("A  padding at the secondary window (0.62), first-flow order",
                 fontsize=6.8, loc="left", pad=3)

    # --- B: real ADDIS state attack (0.85 stress) ---
    t = json.load(open(RES / "t32_B1.json"))
    sw = sorted(t["front_load_sweep"], key=lambda r: r["B"])
    B = [r["B"] for r in sw]; P = [r["p_target_detected"] for r in sw]
    ax = axes[1]
    ax.step(B, P, where="post", color=PALETTE[1], lw=1.4)
    ax.plot(B, P, "o", ms=2.8, color=PALETTE[1])
    bstar = t["bstar"][0]["bstar"]
    ax.axvline(bstar, color=INK, lw=0.7, ls=":")
    ax.annotate("$B^{*}=203$:\nsilent, $9.2{\\times}10^{7}$\nflows (36 GB)",
                (bstar, 0.62), textcoords="offset points", xytext=(-6, 0),
                fontsize=6.0, color=INK, linespacing=1.2, va="center", ha="right")
    ax.set_xscale("symlog", linthresh=1)
    ax.set_xlabel("precursor episodes $B$ before target")
    ax.set_ylabel("target detected")
    ax.set_ylim(-0.10, 1.22); ax.set_xlim(-0.4, 20000)
    ax.grid(True, color=MUTE, alpha=0.22)
    ax.set_title("B  state attack, real stream (0.85)", fontsize=6.8, loc="left", pad=3)

    # --- C: the same state attack where ADDIS's guarantee genuinely holds (synthetic) ---
    ax = axes[2]
    try:
        syn = json.load(open(RES / "t52_B1_synthetic.json"))
        a = syn["attack"]; w = a["witness_seed7"]; sweep = sorted(w["sweep"], key=lambda r: r["B"])
        Bs = [r["B"] for r in sweep]; K = [r["kept_frac"] for r in sweep]
        bs = w["b_star"]; bmed = int(round(a["bstar_distribution"]["median"]))
        ax.step(Bs, K, where="post", color=PALETTE[2], lw=1.4)
        ax.plot(Bs, K, "o", ms=2.8, color=PALETTE[2])
        ax.axvline(bs, color=INK, lw=0.7, ls=":")
        mfdp = json.load(open(RES / "t52_B1_synthetic.json"))["validity"]["mixed"]["mean_fdp"]
        ax.annotate(f"$B^*={bmed}$ (median):\nall {a['n_det_clean']} silenced;\n"
                    f"mean FDP $={mfdp:.3f}\\leq q$",
                    (bs, 0.60), textcoords="offset points", xytext=(7, 0),
                    fontsize=6.0, color=INK, linespacing=1.2, va="center", ha="left")
        ax.set_xlim(-0.4, 2 * bs)
    except (FileNotFoundError, KeyError):
        ax.text(0.5, 0.5, "t52 synthetic result missing", ha="center", va="center",
                transform=ax.transAxes, color=WARN)
    ax.set_xlabel("precursor episodes $B$ (synthetic)")
    ax.set_ylabel("targets kept")
    ax.set_ylim(-0.10, 1.22)
    ax.grid(True, color=MUTE, alpha=0.22)
    ax.set_title("C  guarantee-valid stream (synthetic)", fontsize=6.8, loc="left", pad=3)

    fig.tight_layout(w_pad=1.6)
    save(fig, "fig4_attacks")


if __name__ == "__main__":
    print("building figures from", RES)
    fig1_system(); fig2_envelope(); fig3_granularity(); fig4_attacks()
