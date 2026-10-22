"""Regenerate all data figures for the EvoRiri paper in one consistent style.

Vector PDF (for LaTeX) + 600-dpi PNG (for preview / Word). Sized for the MDPI
text width (394 pt = 5.46 in) so they are included at 1:1 scale.
Usage (from project root): .venv/bin/python make_figures.py OUT_DIR COMPONENTS_JSON
"""
import csv, json, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter, MaxNLocator, MultipleLocator, PercentFormatter

OUT, COMP = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
B = "experiments/baseline_comparison"

W = 394 / 72  # inches, exact MDPI \textwidth, so figures are placed at 1:1 scale
LEFT, RIGHT = 0.78, 0.12  # fixed margins (inches) so all axes line up across figures
INK, GRID = "#222222", "#D9D9D9"
BLUE, ORANGE, SKY, GREY, GREEN = "#0072B2", "#E69F00", "#56B4E9", "#9A9A9A", "#009E73"  # Okabe-Ito
COND = {"B1": GREY, "B2": SKY, "B4": BLUE}
COND_LABEL = {"B1": "B1 (minimal-structure, short budget)", "B2": "B2 (fixed balanced genome)", "B4": "B4 (GA-optimised)"}

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Palatino", "TeX Gyre Pagella", "Palatino Linotype", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "custom", "mathtext.rm": "Palatino", "mathtext.it": "Palatino:italic",
    "font.size": 8.5, "axes.labelsize": 8.5, "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
    "axes.edgecolor": INK, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK, "text.color": INK,
    "axes.linewidth": 0.7, "xtick.major.width": 0.7, "ytick.major.width": 0.7,
    "xtick.major.size": 3, "ytick.major.size": 3,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.6,
    "legend.frameon": False, "lines.linewidth": 1.6,
    "pdf.fonttype": 42, "ps.fonttype": 42, "grid.alpha": 0.8,
})


def frame(fig, top=0.12, bottom=0.42):
    w, h = fig.get_size_inches()
    fig.subplots_adjust(left=LEFT / w, right=1 - RIGHT / w, top=1 - top / h, bottom=bottom / h)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name + ".pdf"))
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=600)
    plt.close(fig)
    print("saved", name)


def gens_axis(ax):
    ax.set_xlim(0.5, 20.5)
    ax.set_xticks([1, 5, 10, 15, 20])
    ax.set_xlabel("Generation")


# ---- convergence + dispersion (main GA run) ----
log = json.load(open(f"{B}/b4_fitness_log.json"))
g = list(range(1, len(log["best"]) + 1))

fig, ax = plt.subplots(figsize=(W, 2.3))
ax.plot(g, log["best"], color=BLUE, marker="o", ms=3, label="Best individual")
ax.plot(g, log["avg"], color=ORANGE, ls="--", marker="s", ms=2.6, label="Population mean")
for ys, col, dy in ((log["best"], BLUE, 0.018), (log["avg"], ORANGE, -0.03)):
    ax.annotate(f"{ys[-1]:.3f}", (g[-1], ys[-1]), xytext=(0, dy * 300), textcoords="offset points",
                ha="center", fontsize=7.5, color=col)
gens_axis(ax)
ax.set_ylabel("Training fitness")
ax.set_ylim(0.3, 0.75)
ax.set_yticks([0.3, 0.4, 0.5, 0.6, 0.7])
ax.yaxis.set_major_formatter(FormatStrFormatter("%.2f"))
ax.legend(loc="lower right", ncol=2, columnspacing=1.2)
frame(fig)
save(fig, "fitness_curve")

fig, ax = plt.subplots(figsize=(W, 2.3))
ax.plot(g, log["var"], color=GREEN, marker="o", ms=3)
gens_axis(ax)
ax.set_ylabel("Variance of\npopulation fitness")
ax.set_ylim(0, 0.11)
frame(fig)
save(fig, "fitness_dispersion")


# ---- dataset / population size (five seeds each, TOST margin) ----
def read(path):
    return list(csv.DictReader(open(path)))


def size_plot(rows, eq, key, ref, xlabel, name):
    xs = [int(r[key]) for r in rows]
    m = [float(r["mean_fitness"]) for r in rows]
    sd = [float(r["std_fitness"]) for r in rows]
    eqmap = {int(r[key]): r["is_equivalent"] == "True" for r in eq}
    ref_m = m[xs.index(ref)]
    fig, ax = plt.subplots(figsize=(W, 2.5))
    ax.axhspan(ref_m - 0.01, ref_m + 0.01, color=SKY, alpha=0.18, lw=0, label=r"Equivalence margin ($\pm$0.01)")
    ax.axhline(ref_m, color=SKY, lw=0.8)
    ax.errorbar(xs, m, yerr=sd, color=BLUE, lw=1.2, capsize=3, capthick=0.9, zorder=3)
    for x, y in zip(xs, m):
        if x == ref:
            ax.plot(x, y, "D", color=BLUE, ms=5, zorder=4)
        elif eqmap.get(x, False):
            ax.plot(x, y, "o", color=BLUE, ms=5, zorder=4)
        else:
            ax.plot(x, y, "o", mfc="white", mec=BLUE, mew=1.2, ms=5, zorder=4)
    ax.plot([], [], "D", color=BLUE, ms=5, label="Reference condition")
    ax.plot([], [], "o", color=BLUE, ms=5, label="Equivalent to reference (TOST)")
    if not all(eqmap.values()):
        ax.plot([], [], "o", mfc="white", mec=BLUE, mew=1.2, ms=5, label="Not equivalent at margin")
    ax.set_xscale("log")
    ax.set_xticks(xs)
    ax.set_xticklabels([str(x) for x in xs])
    ax.minorticks_off()
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Validation fitness\n(mean $\\pm$ SD)")
    ax.set_ylim(ref_m - 0.016, ref_m + 0.016)
    ax.yaxis.set_major_locator(MultipleLocator(0.005))
    ax.yaxis.set_major_formatter(FormatStrFormatter("%.3f"))
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, columnspacing=1.2, handletextpad=0.4)
    frame(fig, top=0.5)
    save(fig, name)


size_plot(read(f"{B}/dataset_size_corrected.csv"), read(f"{B}/dataset_size_equivalence.csv"),
          "dataset_size", 2297, "Optimisation-set size (nested subsets)", "dataset_size")
size_plot(read(f"{B}/population_size_corrected.csv"), read(f"{B}/population_size_equivalence.csv"),
          "population_size", 100, "Population size", "population_size")


# ---- redesigned: structure components and escalation by risk ----
comp = json.load(open(COMP))
conds = ["B1", "B2", "B4"]


def grouped(ax, groups, getter, ylabel):
    n = len(conds)
    width = 0.26
    for i, c in enumerate(conds):
        vals = [getter(c, k) for k in groups]
        xs = [j + (i - (n - 1) / 2) * width for j in range(len(groups))]
        ax.bar(xs, vals, width * 0.92, color=COND[c], label=COND_LABEL[c], zorder=3, edgecolor="white", linewidth=0.4)
        for x, v in zip(xs, vals):
            ax.text(x, v + 0.015, f"{100 * v:.0f}%", ha="center", va="bottom", fontsize=6.5, color=INK)
    ax.set_ylim(0, 1.12)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", length=0)


fig, ax = plt.subplots(figsize=(W, 2.6))
groups = ["grounding", "action", "question", "all_three"]
grouped(ax, groups, lambda c, k: comp[c]["component_rate"][k], "Responses containing component")
ax.set_xticks(range(len(groups)))
ax.set_xticklabels(["Grounding", "Action", "Question", "All three"])
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, columnspacing=1.0, handlelength=1.0)
frame(fig, top=0.32, bottom=0.32)
save(fig, "structure_components")

fig, ax = plt.subplots(figsize=(W, 2.6))
risks = ["low", "mid", "high"]
grouped(ax, risks, lambda c, k: comp[c]["esc_rate_by_risk"].get(k, 0.0), "Responses with escalation content")
ax.set_xticks(range(3))
n = comp["B4"]["n_by_risk"]
ax.set_xticklabels([f"Low risk ($n$={n.get('low', 0)})", f"Mid risk ($n$={n.get('mid', 0)})", f"High risk ($n$={n.get('high', 0)})"])
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, columnspacing=1.0, handlelength=1.0)
frame(fig, top=0.32, bottom=0.32)
save(fig, "escalation_by_risk")
print(json.dumps({c: {"esc": comp[c]["esc_rate_by_risk"], "comp": comp[c]["component_rate"]} for c in conds}, indent=1))
