"""Every figure in the submission, drawn from the cached results in ``out/``.
    import figures; figures.OUTDIR = "somewhere"; figures.build_all()
"""
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

RES = Path(__file__).resolve().parent / "out"
OUTDIR = None                      # set by the paper build; None => return the figure, write nothing

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
    "pdf.fonttype": 42, "ps.fonttype": 42,
})


def save(fig, name):
    """Write the figure if OUTDIR is set, otherwise hand it back for inline display."""
    if OUTDIR is None:
        return fig
    out = Path(OUTDIR)
    out.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(out / f"{name}.{ext}")
    plt.close(fig)
    print(f"  figures/{name}.pdf")
    return fig


def fig2_envelope():
    k, alpha, w0, zeta = 1, 0.05, 0.025, 2.2857744
    T = np.logspace(3, 9.2, 400)
    fig, ax = plt.subplots(figsize=(COL, 1.9))

    ax.loglog(T, k*T/w0 - 1, color=PALETTE[0],
              label=r"$c_0=w_0$ (LORD++), horizon-aware $\gamma_t=1/T$")
    ax.loglog(T, k*T/alpha - 1, color=PALETTE[0], ls=":", lw=1.1,
              label=r"$c_0=\alpha$ (LOND/e-LOND), horizon-aware $\gamma_t=1/T$")
    ax.loglog(T, k*zeta*T**1.6/w0, color=PALETTE[1], ls="--",
              label=r"covered families, $\gamma_j\propto j^{-1.6}$")

    ax.axhspan(1.81e6, 2.45e6, color=MUTE, alpha=0.22, lw=0)
    ax.text(2.2e9, 1.35e6, "available corpus, 1.8–2.4M flows",
            fontsize=6.3, color="#3a3a3a", va="top", ha="right")

    tmax = 2.449031e6 * w0 / k
    ax.plot([tmax], [2.449031e6], "v", ms=4.2, color=PALETTE[0], zorder=6)

    for x in (16.35e6, 8.64e8):
        ax.plot([x], [k*x/w0 - 1], "o", ms=3.6, color=PALETTE[0], zorder=5)
    ax.annotate("LSPR23 stream:\n$6.5\\times10^{8}$ needed", (16.35e6, k*16.35e6/w0 - 1),
                textcoords="offset points", xytext=(8, -2), ha="left", va="top",
                fontsize=6.3, color=PALETTE[0], linespacing=1.25)

    ax.set_xlabel(r"deployment horizon $T$ (hypotheses)")
    ax.set_ylabel(r"required calibration size $|\mathcal{C}|$")
    ax.set_ylim(1e3, 1e15)
    ax.grid(True, which="major", color=MUTE, alpha=0.25)
    ax.legend(loc="upper left", handlelength=1.7, borderaxespad=0.3, labelspacing=0.25)
    save(fig, "fig2_envelope")


def fig1_chain():
    fig, ax = plt.subplots(figsize=(WIDE, 1.75))
    ax.set_xlim(0, 100); ax.set_ylim(0, 56); ax.axis("off")

    # --- pipeline -------------------------------------------------------------------------
    stages = [("network\nflows", 1.5), ("ML\ndetector", 16.5), ("conformal\nevidence", 31.5),
              ("group\naggregation", 46.5), ("online error\ncontroller", 61.5), ("SOC\nalert", 79.5)]
    w, h, y = 12.5, 9.0, 41.0
    edges = []
    for label, x in stages:
        emph = label.startswith(("group", "online"))
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.35,rounding_size=1.2",
                                    linewidth=1.1 if emph else 0.7,
                                    edgecolor=WARN if emph else INK,
                                    facecolor="#fdf1f1" if emph else "white", zorder=2))
        ax.text(x + w/2, y + h/2, label, ha="center", va="center", fontsize=7.4, zorder=3)
        edges.append((x, x + w))
    for (_, x1), (x0, _) in zip(edges, edges[1:]):
        ax.add_patch(FancyArrowPatch((x1 + 0.4, y + h/2), (x0 - 0.4, y + h/2),
                                     arrowstyle="-|>", mutation_scale=8,
                                     linewidth=0.8, color=MUTE, zorder=1))
    # the ceiling attaches to the evidence stage
    cx = 31.5 + w/2
    ax.plot([cx, cx], [y + h + 0.4, y + h + 2.6], color=MUTE, lw=0.6)
    ax.text(cx, y + h + 3.2, r"bounded: $e\in\{0,\,M\}$,  $M=(|\mathcal{C}|+1)/k$",
            ha="center", va="bottom", fontsize=6.8, color=MUTE)
    # the level attaches to the controller stage
    kx = 61.5 + w/2
    ax.plot([kx, kx], [y + h + 0.4, y + h + 2.6], color=MUTE, lw=0.6)
    ax.text(kx, y + h + 3.2, r"reject iff  $\mathrm{Ev}(G_t)\ \geq\ 1/\alpha_t$,  $\alpha_t\downarrow$",
            ha="center", va="bottom", fontsize=6.8, color=MUTE)

    bx = 46.5 + w/2
    ax.add_patch(FancyArrowPatch((bx, 32.6), (bx, y - 0.4), arrowstyle="-|>",
                                 mutation_scale=8, linewidth=1.0, color=WARN, zorder=1))
    ax.text(bx + 1.2, 30.4, "attacker-influenceable membership:  zero-evidence padding",
            ha="left", va="center", fontsize=6.9, color=WARN)
    ax.text(bx + 1.2, 26.9, "append ordinary flows to own episode  (Thm. 3)",
            ha="left", va="center", fontsize=6.2, color=WARN, style="italic")
    kx2 = 61.5 + w/2
    ax.add_patch(FancyArrowPatch((kx2, 32.6), (kx2, y - 0.4), arrowstyle="-|>", linestyle="--",
                                 mutation_scale=6, linewidth=0.6, color=MUTE, zorder=1))
    ax.text(kx2 + 1.0, 24.0, "adaptive controller-state extension (App. G)",
            ha="left", va="center", fontsize=5.8, color=MUTE, style="italic")

    chain = [("bounded evidence\n$M<\\infty$", 1.5, INK),
             ("summable spending\n$\\alpha_t\\to 0$", 21.0, INK),
             ("finite discovery horizon\n(Thm. 1\u20132, Cor. 1)", 40.5, ACC),
             ("repair: group flows\n$T\\downarrow$, blur $\\uparrow$  (Sec. IV)", 60.0, ACC),
             ("group membership\nattacker-facing  (Sec. V)", 79.5, WARN)]
    cw, ch, cy = 17.5, 9.0, 4.0
    cedges = []
    for label, x, col in chain:
        ax.add_patch(FancyBboxPatch((x, cy), cw, ch, boxstyle="round,pad=0.3,rounding_size=1.0",
                                    linewidth=0.7, edgecolor=col, facecolor="white", zorder=2))
        ax.text(x + cw/2, cy + ch/2, label, ha="center", va="center", fontsize=6.6, color=col,
                zorder=3, linespacing=1.15)
        cedges.append((x, x + cw))
    for (_, x1), (x0, _) in zip(cedges, cedges[1:]):
        ax.add_patch(FancyArrowPatch((x1 + 0.3, cy + ch/2), (x0 - 0.3, cy + ch/2),
                                     arrowstyle="-|>", mutation_scale=7,
                                     linewidth=0.7, color=MUTE, zorder=1))
    ax.text(0.0, cy + ch + 2.2, "causal chain", fontsize=6.4, color=MUTE, va="bottom",
            style="italic")
    save(fig, "fig1_chain")


def fig3_granularity_body():
    d = json.load(open(RES / "t26_H4_5pos.json"))
    rows = [r for r in d["rows"] if r["family"] == "src-dst" and r["seed"] == 0]
    C0_ELOND = 0.05                       # c_0 = alpha = 2*w_0 for LOND/e-LOND
    for r in rows:
        r["rho"] = (r["NC"] + 1) * C0_ELOND / r["T"]
    w7 = json.load(open(RES / "t47_W7.json"))
    blur = [r for r in w7["rows"] if r["family"] == "src-dst"]
    POS = [0.55, 0.62, 0.70, 0.77, 0.85]

    fig, axes = plt.subplots(2, 1, figsize=(COL, 1.95), sharex=True)

    STYLE = {0.55: dict(color=PALETTE[0], lw=1.9, ms=3.4, zorder=5, label="0.55 primary"),
             0.62: dict(color=PALETTE[1], lw=1.2, ms=2.8, zorder=4, label="0.62 secondary")}

    def plot_panel(ax, src, key, pos_key=lambda r: r["pos"]):
        env = {}
        for pos in POS:
            pts = sorted(((r["bucket_s"] or 86400, r[key]) for r in src
                          if abs(pos_key(r) - pos) < 1e-9 and r[key] is not None),
                         key=lambda p: p[0])
            if not pts:
                continue
            if pos in STYLE:
                ax.plot([p[0] for p in pts], [p[1] for p in pts], marker="o", **STYLE[pos])
            else:
                for x, y in pts:
                    env.setdefault(x, []).append(y)
        if env:
            xs = sorted(env)
            ax.fill_between(xs, [min(env[x]) for x in xs], [max(env[x]) for x in xs],
                            color=MUTE, alpha=0.20, lw=0, zorder=1,
                            label="0.70/0.77/0.85 (range)")
        ax.set_xscale("log"); ax.grid(True, color=MUTE, alpha=0.22)

    plot_panel(axes[0], rows, "rho")
    axes[0].set_ylabel(r"feasibility ratio $\rho$")
    axes[0].set_yscale("log")
    axes[0].axhline(1, color=INK, lw=0.9)
    axes[0].set_ylim(0.02, 20)
    axes[0].text(8e4, 0.78, r"$\rho=1$: e-LOND cold-start feasible", fontsize=6.2, color=INK,
                 va="top", ha="right")
    axes[0].legend(loc="upper left", ncol=3, handlelength=1.4, columnspacing=0.8,
                   borderaxespad=0.4, labelspacing=0.25, fontsize=6.0)

    plot_panel(axes[1], blur, "blur_mal_atoms_per_alert", pos_key=lambda r: float(r["pos"]))
    axes[1].set_ylabel("alert blur")
    axes[1].set_yscale("log"); axes[1].set_ylim(0.8, 60)
    axes[1].axhline(1, color=INK, lw=0.7, ls=":")

    # the two-hour headline unit
    for ax in axes:
        ax.axvline(7200, color=MUTE, lw=0.7, ls="--", alpha=0.8)
    axes[1].text(7200 * 1.12, 0.92, "headline unit (2 h)", fontsize=5.8, color=MUTE, ha="left",
                 va="bottom")

    axes[1].set_xlabel("time-bucket width")
    axes[1].set_xticks([300, 1800, 3600, 7200, 21600, 86400])
    axes[1].set_xticklabels(["5 m", "30 m", "1 h", "2 h", "6 h", "1 d"])
    axes[1].minorticks_off()
    fig.align_ylabels(axes)
    save(fig, "fig3_granularity_body")


def fig4_padding_body():
    full = json.load(open(RES / "t28b_reallevel.json"))
    by_order = full["table1_by_order"]
    prim = np.array(by_order["keyhash"]["0.55_0"]["pads_real"], float)     # 23, 24, 33
    sec = np.array(by_order["keyhash"]["0.62_0"]["pads_real"], float)      # 11 detections
    t67 = json.load(open(RES / "t67_ait_order.json"))
    c = t67["summary"]["canonical"]
    org_med = c["median_rstar_by_org"]
    unif = np.array(json.load(open(RES / "t73_uniform_padding.json"))
                    ["cells"]["0.55_keyhash_uniform"]["pads"], float)
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(WIDE, 2.35),
                                 gridspec_kw=dict(width_ratios=[1.35, 1.0]))
    print(f"    fig4: primary {sorted(prim.astype(int))}, secondary median {np.median(sec):.0f} "
          f"({len(sec)} alerts), AIT {c['n_suppressible']}/{c['n_detected']} over {len(org_med)} orgs")

    grid = np.unique(np.concatenate([[1], np.logspace(0, 5.5, 400)]))
    ax.plot(grid, [(sec <= g).mean() for g in grid], color=ACC, lw=2.4, zorder=4,
            label=f"0.62 secondary ({len(sec)} alerts,\nmedian {np.median(sec):.0f})")
    for n, v in enumerate(sorted(prim)):
        ax.plot([v], [(n + 1) / len(prim)], marker="o", ms=6.0, color=WARN, zorder=6,
                label="0.55 primary (3 alerts,\nall replayed)" if n == 0 else None)
    ax.plot(sorted(prim), [(n + 1) / len(prim) for n in range(len(prim))],
            color=WARN, lw=1.4, zorder=5)
    ax.annotate(f"{int(min(prim))}, {int(sorted(prim)[1])}, {int(max(prim))}",
                (max(prim), 1.0), textcoords="offset points", xytext=(5, -1),
                fontsize=7.2, color=WARN, va="center", ha="left")
    ax.plot(grid, [(unif <= g).mean() for g in grid], color=PALETTE[2], lw=1.6, ls=(0, (4, 1.5)),
            zorder=3,
            label=f"0.55, horizon-aware ({len(unif)} alerts,\nmedian {np.median(unif):,.0f})")
    ax.set_xscale("log"); ax.set_xlim(0.85, 3e5)
    ax.set_ylim(0, 1.52)                       # head-room for the legend, clear of every curve
    ax.set_yticks(np.arange(0, 1.01, 0.2))
    ax.set_xlabel("padding flows added")
    ax.set_ylabel("alerts suppressed")
    ax.grid(True, color=MUTE, alpha=0.22)
    ax.legend(loc="upper center", ncol=3, handlelength=1.2, handletextpad=0.4, borderaxespad=0.25,
              labelspacing=0.3, columnspacing=1.0, fontsize=6.4, frameon=True, framealpha=0.95,
              edgecolor=MUTE, facecolor="white", borderpad=0.3)
    ax.set_title("A  LSPR23, canonical order", fontsize=7.6, loc="left", pad=3)

    orgs = sorted(org_med, key=org_med.get)
    bx.barh(range(len(orgs)), [org_med[o] for o in orgs], color=ACC, alpha=0.85, height=0.62)
    bx.set_yticks(range(len(orgs)))
    bx.set_yticklabels(orgs, fontsize=6.6)
    bx.set_xscale("log")
    bx.set_xlabel(r"median empirical replay cost $r^{\star}_{t,\mathrm{emp}}$ (flows)")
    bx.grid(True, axis="x", color=MUTE, alpha=0.22)
    bx.set_title("B  AIT transfer, canonical order", fontsize=7.6, loc="left", pad=3)
    bx.text(0.97, 0.06,
            f"{c['n_suppressible']} of {c['n_detected']} detections\nsuppressible; per draw "
            f"{c['per_draw_success_min']:.2f}–{c['per_draw_success_max']:.2f}",
            transform=bx.transAxes, fontsize=6.6, ha="right", va="bottom", linespacing=1.2,
            color=INK)

    fig.tight_layout(w_pad=0.9)
    save(fig, "fig4_padding_body")


def figE_padding_sensitivity():
    full = json.load(open(RES / "t28b_reallevel.json"))
    guar = full.get("fig4a_guarantee") or full["fig4a_pools"]
    pools = ["generic", "attacker-origin", "protocol-matched", "service-matched", "black-box"]
    by_order = full["table1_by_order"]
    canon62 = np.array(by_order["keyhash"]["0.62_0"]["pads_real"], float)
    canon85 = np.array(by_order["keyhash"]["0.85_0"]["pads_real"], float)
    canon_pool_med = {k: v["med"] for k, v in
                      full["pools_by_order"]["keyhash"]["0.62_0"]["real"].items()}
    cmed, c85med = float(np.median(canon62)), float(np.median(canon85))
    ffmed = float(np.median(np.array(guar["pools"]["black-box"], float)))

    fig, ax = plt.subplots(figsize=(COL, 1.85))
    grid = np.unique(np.concatenate([[1], np.logspace(0, 8.2, 400)]))
    for i, pl in enumerate(pools):
        costs = np.array(guar["pools"].get(pl, []), float)
        if not len(costs):
            continue
        ax.plot(grid, [(costs <= g).mean() for g in grid], color=MUTE, lw=0.7, ls="--",
                alpha=0.8, zorder=2,
                label=f"first-flow arm, 5 pools (median {ffmed:.0f})" if i == 0 else None)
    ax.plot(grid, [(canon62 <= g).mean() for g in grid], color=ACC, lw=2.4, zorder=5,
            label=f"canonical, 0.62 secondary (median {cmed:.0f})")
    ax.plot(grid, [(canon85 <= g).mean() for g in grid], color=INK, lw=1.3, alpha=0.8, zorder=4,
            label=f"canonical, 0.85 stress (median {c85med:.0f}, {len(canon85)} alerts)")
    for v in sorted(set(canon_pool_med.values())):
        ax.plot([v], [0.50], marker="|", ms=9, mew=1.6, color=ACC, zorder=6)
    ax.set_xscale("log"); ax.set_xlim(0.85, 3e5); ax.set_ylim(0, 1.06)
    ax.set_xlabel("padding flows added to own episode")
    ax.set_ylabel("alerts suppressed")
    ax.grid(True, color=MUTE, alpha=0.22)
    ax.legend(loc="lower right", handlelength=1.5, handletextpad=0.4, borderaxespad=0.3,
              labelspacing=0.2, fontsize=5.2, frameon=True, framealpha=0.95, edgecolor=MUTE,
              facecolor="white", borderpad=0.35)
    fig.tight_layout()
    save(fig, "figE_padding_sensitivity")


def figA_addis_state():
    fig, axes = plt.subplots(2, 1, figsize=(COL, 3.15))

    t = json.load(open(RES / "t32_B1.json"))
    sw = sorted(t["front_load_sweep"], key=lambda r: r["B"])
    B = [r["B"] for r in sw]; P = [r["p_target_detected"] for r in sw]
    ax = axes[0]
    ax.set_facecolor("#e9e9e9")
    ax.step(B, P, where="post", color="#7a3a3d", lw=1.3)
    ax.plot(B, P, "o", ms=2.6, color="#7a3a3d")
    bstar = t["bstar"][0]["bstar"]
    ax.axvline(bstar, color=INK, lw=0.7, ls=":")
    ax.annotate(f"$B^{{*}}={bstar}$:\nsilent, $9.2{{\\times}}10^{{7}}$ flows (36 GB)",
                (bstar, 0.62), textcoords="offset points", xytext=(-6, 0),
                fontsize=5.8, color=INK, linespacing=1.2, va="center", ha="right")
    ax.text(0.02, 0.05, "stress window 0.85: evidence not a valid e-value;\nmechanism and cost only",
            transform=ax.transAxes, fontsize=5.6, color="#5a5a5a", ha="left", va="bottom",
            linespacing=1.15, style="italic")
    ax.set_xscale("symlog", linthresh=1)
    ax.set_xlabel("precursor episodes $B$ before target")
    ax.set_ylabel("target detected")
    ax.set_ylim(-0.10, 1.22); ax.set_xlim(-0.4, 20000)
    ax.grid(True, color="white", alpha=0.9)
    ax.set_title("B  state attack, real stream (0.85 stress; mechanism only)",
                 fontsize=6.6, loc="left", pad=3, color="#5a5a5a")

    ax = axes[1]
    syn = json.load(open(RES / "t52_B1_synthetic.json"))
    a = syn["attack"]; w = a["witness_seed7"]; sweep = sorted(w["sweep"], key=lambda r: r["B"])
    Bs = [r["B"] for r in sweep]; K = [r["kept_frac"] for r in sweep]
    bs = w["b_star"]; bmed = int(round(a["bstar_distribution"]["median"]))
    ax.step(Bs, K, where="post", color=PALETTE[2], lw=1.4)
    ax.plot(Bs, K, "o", ms=2.8, color=PALETTE[2])
    ax.axvline(bs, color=INK, lw=0.7, ls=":")
    mfdp = syn["validity"]["mixed"]["mean_fdp"]
    ax.annotate(f"$B^*={bmed}$ (median):\nall {a['n_det_clean']} silenced;\n"
                f"mean FDP $={mfdp:.3f}\\leq q$",
                (bs, 0.60), textcoords="offset points", xytext=(7, 0),
                fontsize=5.8, color=INK, linespacing=1.2, va="center", ha="left")
    ax.set_xlim(-0.4, 2 * bs)
    ax.set_xlabel("precursor episodes $B$ (synthetic)")
    ax.set_ylabel("targets kept")
    ax.set_ylim(-0.10, 1.22)
    ax.grid(True, color=MUTE, alpha=0.22)
    ax.set_title("C  guarantee-valid stream (synthetic)", fontsize=6.6, loc="left", pad=3)

    fig.tight_layout(h_pad=1.1)
    save(fig, "figA_addis_state")

SUBMISSION = [
    ("fig1_chain", "Fig. 1 -- the trust layer and the causal chain"),
    ("fig2_envelope", "Fig. 2 -- calibration required against the horizon"),
    ("fig3_granularity_body", "Fig. 3 -- feasibility ratio and alert blur against bucket width"),
    ("fig4_padding_body", "Fig. 4 -- padding cost per alert, LSPR23 and the AIT transfer"),
    ("figE_padding_sensitivity", "App. E -- stress-window and first-flow sensitivity arms"),
    ("figA_addis_state", "App. G -- the ADDIS state attack"),
]


def build_all(verbose=True):
    """Draw every submission figure. Returns {name: Figure}."""
    figs = {}
    for name, caption in SUBMISSION:
        if verbose and OUTDIR is None:
            print(caption)
        figs[name] = globals()[name]()
    return figs
