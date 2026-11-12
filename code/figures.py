# -*- coding: utf-8 -*-
"""P3 figures (PDF, Copernicus full width = 160 mm).

fig01  dataset composition and evidence provenance
fig02  forest plot of log ratio, sorted, with documented intervals
fig03  ratio versus prior-dependence score (expanded set)
fig04  same-product contrasts (stage and support)
fig05  distribution of log ratio and evidence-type counts
fig06  three under-reporting mechanisms with dataset examples
"""
import csv
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, Rectangle

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
FIG = os.path.join(BASE, "figures")
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 8.5,
    "axes.labelsize": 8.5,
    "axes.titlesize": 9,
    "legend.fontsize": 7.5,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "axes.linewidth": 0.6,
    "pdf.fonttype": 42,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
})

rows = list(csv.DictReader(open(os.path.join(DATA, "p3_dataset.csv"), encoding="utf-8-sig")))
ledger = list(csv.DictReader(open(os.path.join(DATA, "p3_declared_ledger.csv"), encoding="utf-8-sig")))
stats = json.load(open(os.path.join(DATA, "stats.json")))

FAM_COLOR = {
    "sea ice thickness": "#08306b",
    "sea ice concentration": "#2171b5",
    "surface soil moisture": "#6baed6",
    "aerosol optical depth": "#c51b7d",
    "leaf area index": "#238b45",
    "sea surface temperature": "#d94801",
    "sea surface salinity": "#8c6d31",
    "snow water equivalent": "#7a5195",
    "snow cover": "#a6761d",
    "forest aboveground biomass": "#2ca25f",
    "precipitation": "#1b7837",
    "land surface temperature": "#e31a1c",
    "ocean colour chlorophyll": "#0570b0",
    "sea level anomaly": "#636363",
    "evapotranspiration": "#993404",
    "freeze/thaw state": "#525252",
}


def fam(v):
    return "sea ice thickness" if v.startswith("sea ice thickness") else v


def num(x):
    try:
        return float(x)
    except Exception:
        return None


# ---------------------------------------------------------------- figure 1
fam_total, fam_assess = {}, {}
ev_counts = {}
for r in rows:
    v = fam(r["variable"])
    fam_total[v] = fam_total.get(v, 0) + 1
    if r["assessable"] == "1":
        fam_assess[v] = fam_assess.get(v, 0) + 1
for r in ledger:
    ev_counts[r["evidence_type"]] = ev_counts.get(r["evidence_type"], 0) + 1

fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(6.4, 3.3),
                               gridspec_kw={"width_ratios": [2.0, 1.0]})
fig.subplots_adjust(wspace=0.42)
order = sorted(fam_total, key=lambda k: (fam_total[k], k))
y = np.arange(len(order))
tot = np.array([fam_total[k] for k in order])
ass = np.array([fam_assess.get(k, 0) for k in order])
ax0.barh(y, tot, color="#e3e3e3", edgecolor="#9e9e9e", linewidth=0.4)
ax0.barh(y, ass, color="#2166ac", edgecolor="#053061", linewidth=0.4, label="assessable")
ax0.set_yticks(y)
ax0.set_yticklabels(order, fontsize=6.6)
ax0.set_xlabel("objects (light: catalogued, dark: assessable)", fontsize=7.4)
ax0.set_xlim(0, max(tot) + 1.2)
for i, (t, a) in enumerate(zip(tot, ass)):
    ax0.text(t + 0.15, i, f"{a}/{t}", va="center", fontsize=6.3, color="#333333")
ax0.legend(loc="lower right", frameon=False, fontsize=6.6)
ax0.set_title("(a) coverage by variable", fontsize=8)
ax0.spines[["top", "right"]].set_visible(False)

labels = ["raw file attribute", "product document", "recomputed", "third-party literature"]
keys = ["raw_file_attribute", "product_document_text", "recomputation", "third_party_literature"]
vals = [ev_counts.get(k, 0) for k in keys]
cols = ["#2166ac", "#67a9cf", "#ef8a62", "#b2182b"]
bars = ax1.barh(range(4), vals, color=cols, edgecolor="#222222", linewidth=0.4)
ax1.set_yticks(range(4))
ax1.set_yticklabels(labels, fontsize=6.6)
ax1.invert_yaxis()
ax1.set_xlabel("objects in the 17-row ledger", fontsize=7.4)
ax1.set_xlim(0, max(vals) + 3.4)
for b, v in zip(bars, vals):
    ax1.text(v + 0.15, b.get_y() + b.get_height() / 2, f"{v} ({100*v/sum(vals):.0f}%)",
             va="center", fontsize=6.3)
ax1.set_title("(b) provenance of the declaration", fontsize=8)
ax1.spines[["top", "right"]].set_visible(False)
fig.savefig(os.path.join(FIG, "fig01_composition.pdf"))
fig.savefig(os.path.join(FIG, "fig01_composition.png"), dpi=170)
plt.close(fig)

# ---------------------------------------------------------------- figure 2
ass_rows = [r for r in rows if r["assessable"] == "1" and num(r["ratio"])]
ass_rows.sort(key=lambda r: math.log10(float(r["ratio"])))
fig, ax = plt.subplots(figsize=(5.6, 4.9))
ax.axvspan(0.05, 1.0, color="#fdd0d0", alpha=0.45, lw=0)
ax.axvspan(1.0, 20.0, color="#d9e8f5", alpha=0.45, lw=0)
for i, r in enumerate(ass_rows):
    gid = r["group_id"]
    v = float(r["ratio"])
    col = FAM_COLOR.get(fam(r["variable"]), "#444444")
    marker = "o" if r["ratio_relation"] == "point" else ("s" if r["ratio_relation"] == "upper_bound" else "D")
    ax.plot([v], [i], marker=marker, ms=5.2, color=col, mec="#222222", mew=0.5, zorder=5)
    lo, hi = num(r["ci_low"]), num(r["ci_high"])
    if lo and hi:
        ax.plot([lo, hi], [i, i], color="#222222", lw=1.2, zorder=4)
    elif hi:
        ax.annotate("", xy=(hi, i), xytext=(hi * 0.62, i),
                    arrowprops=dict(arrowstyle="-|>", color="#222222", lw=1.1))
    elif lo:
        ax.annotate("", xy=(lo, i), xytext=(lo * 1.55, i),
                    arrowprops=dict(arrowstyle="-|>", color="#222222", lw=1.1))
ax.set_xscale("log")
ax.set_xlim(0.05, 20)
ax.axvline(1.0, color="#111111", ls="--", lw=0.9)
ax.set_yticks(range(len(ass_rows)))
LABEL = {
    "G01": "sea ice thickness (freeboard)", "G02": "sea ice thickness", "G03": "sea ice thickness (CS2SMOS)",
    "G04": "surface soil moisture", "G05": "surface soil moisture", "G06": "aerosol optical depth",
    "G07": "leaf area index", "G08": "sea surface temperature", "G15": "surface soil moisture",
    "G16": "surface soil moisture", "G17": "soil moisture (pixel)", "G18": "soil moisture (areal)",
    "G19": "surface soil moisture", "G20": "land surface temperature",
}
ax.set_yticklabels([f"{r['group_id']}  {LABEL.get(r['group_id'], r['variable'])}" for r in ass_rows])
ax.set_xlabel("declared uncertainty / independently measured error  (log scale)")
ax.text(0.055, 2.0, "declared too small", fontsize=7.0, color="#a50f15", rotation=0)
ax.text(2.2, 2.0, "declared too large", fontsize=7.0, color="#08519c")
for i, r in enumerate(ass_rows):
    v = float(r["ratio"])
    f = max(v, 1 / v)
    ax.text(19.2, i, f"{f:.2f}x", ha="right", va="center", fontsize=6.6, color="#444444")
ax.set_title("Unified ratio (declared/actual); whiskers only where the source reports a range", fontsize=8)
ax.spines[["top", "right"]].set_visible(False)
ax.set_ylim(-0.8, len(ass_rows) - 0.2)
ax.grid(axis="x", which="major", color="#cccccc", lw=0.4, alpha=0.7)
fig.savefig(os.path.join(FIG, "fig02_forest.pdf"))
fig.savefig(os.path.join(FIG, "fig02_forest.png"), dpi=170)
plt.close(fig)

# ---------------------------------------------------------------- figure 3
fig, ax = plt.subplots(figsize=(4.6, 3.5))
rng = np.random.default_rng(0)
for r in ass_rows:
    x = float(r["prior_score"]); v = float(r["ratio"])
    j = rng.uniform(-0.10, 0.10)
    col = FAM_COLOR.get(fam(r["variable"]), "#444444")
    ax.plot([x + j], [v], "o", ms=5.5, color=col, mec="#222222", mew=0.5)
    ax.annotate(r["group_id"], (x + j, v), xytext=(4, 4), textcoords="offset points", fontsize=6.2, color="#333333")
ax.set_yscale("log")
ax.axhline(1.0, color="#111111", ls="--", lw=0.9)
ax.set_xlabel("prior-dependence score (0-4)")
ax.set_ylabel("declared / actual  (log scale)")
ax.set_xticks([1, 2, 3])
ax.set_xlim(0.6, 3.4)
C = stats["sets"]["C_all_assessable"]
ax.set_title(f"n = {C['n']}, Spearman rho = {C['rho_prior']:.2f} (p = {C['p_prior']:.2f})")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(alpha=0.2)
fig.savefig(os.path.join(FIG, "fig03_ratio_prior.pdf"))
fig.savefig(os.path.join(FIG, "fig03_ratio_prior.png"), dpi=170)
plt.close(fig)

# ---------------------------------------------------------------- figure 4
pairs = [
    ("G01", "G02", "same product, different stage\nfreeboard vs thickness (CCI SIT v4.0)"),
    ("G17", "G18", "same product and period, different support\npixel vs areal (SMOS L3, Pernambuco)"),
    ("G03", "G02", "same product, different reference\nCS2SMOS bound vs airborne EM"),
]
fig, ax = plt.subplots(figsize=(5.6, 2.35))
ylab, xpos = [], 1
for left, right, label in pairs:
    rl = next(r for r in rows if r["group_id"] == left)
    rr = next(r for r in rows if r["group_id"] == right)
    vel = float(rl["ratio"]); ver = float(rr["ratio"])
    ax.plot([vel, ver], [xpos, xpos], color="#999999", lw=0.7, zorder=1)
    ax.plot([vel], [xpos], "o", ms=6, color="#08306b", mew=0.4, mec="#222222", zorder=3)
    ax.plot([ver], [xpos], "o", ms=6, color="#6baed6", mew=0.4, mec="#222222", zorder=3)
    if abs(math.log10(vel / ver)) > 0.12:
        ax.annotate(f"{left}: {vel:.3f}", (vel, xpos), xytext=(-4, 9), textcoords="offset points",
                    ha="right", fontsize=6.4)
        ax.annotate(f"{right}: {ver:.3f}", (ver, xpos), xytext=(4, 9), textcoords="offset points",
                    ha="left", fontsize=6.4)
    else:
        ax.annotate(f"{left}: {vel:.3f}", (vel, xpos), xytext=(0, 9), textcoords="offset points",
                    ha="center", fontsize=6.4)
        ax.annotate(f"{right}: {ver:.3f}", (ver, xpos), xytext=(0, -13), textcoords="offset points",
                    ha="center", fontsize=6.4)
    ylab.append(label)
    xpos += 1
ax.set_yticks(range(1, xpos))
ax.set_yticklabels(ylab, fontsize=6.2)
ax.set_xscale("log")
ax.set_xlim(0.34, 1.45)
ax.axvline(1.0, color="#111111", ls="--", lw=0.9)
ax.set_xlabel("declared / actual  (log scale)")
ax.set_title("Contrasts inside a single product", fontsize=8)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="x", alpha=0.2)
ax.set_ylim(0.15, xpos + 0.05)
ax.invert_yaxis()
fig.savefig(os.path.join(FIG, "fig04_pairs.pdf"))
fig.savefig(os.path.join(FIG, "fig04_pairs.png"), dpi=170)
plt.close(fig)

# ---------------------------------------------------------------- figure 5
fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(6.3, 2.9),
                               gridspec_kw={"width_ratios": [1.35, 1.0]})
logs = np.array([math.log10(float(r["ratio"])) for r in ass_rows])
ax0.hist(logs, bins=np.arange(-1.2, 0.4, 0.15), color="#9ecae1", edgecolor="#222222", lw=0.4)
ax0.axvline(0, color="#111111", ls="--", lw=0.9)
for r in ass_rows:
    ax0.plot([math.log10(float(r["ratio"]))], [-0.35], "|", color="#08306b", ms=6, mew=0.8)
ax0.set_xlabel("log10 (declared / actual)")
ax0.set_ylabel("objects")
ax0.set_ylim(-0.9, None)
ax0.set_title("(a) asymmetry is mild on the log scale")
ax0.spines[["top", "right"]].set_visible(False)
ax0.annotate("parity", (0.02, ax0.get_ylim()[1] * 0.93), fontsize=6.8)

ev_groups = {}
for r in ledger:
    if r["unified_ratio_declared_over_actual"]:
        ev_groups.setdefault(r["evidence_type"], []).append(abs(math.log10(float(r["unified_ratio_declared_over_actual"]))))
keys = ["raw_file_attribute", "product_document_text", "recomputation", "third_party_literature"]
short = ["file\nattribute", "product\ndocument", "recomputed", "third-party\nliterature"]
pos = []
data = []
for k in keys:
    if k in ev_groups:
        data.append(ev_groups[k])
        pos.append(len(pos))
        ax1.scatter([pos[-1]] * len(ev_groups[k]), ev_groups[k], s=24, color="#08306b", alpha=0.8, zorder=3)
        if len(ev_groups[k]) > 1:
            ax1.plot([pos[-1], pos[-1]], [min(ev_groups[k]), max(ev_groups[k])], color="#888888", lw=0.8, zorder=1)
            ax1.plot([pos[-1] - 0.12, pos[-1] + 0.12],
                     [np.median(ev_groups[k])] * 2, color="#d62728", lw=1.4, zorder=4)
ax1.set_xticks(pos)
ax1.set_xticklabels([short[keys.index(k)] for k in keys if k in ev_groups], fontsize=6.8)
ax1.set_ylabel("|log10 (declared / actual)|")
ax1.set_title("(b) error by evidence provenance")
ax1.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig05_distribution.pdf"))
fig.savefig(os.path.join(FIG, "fig05_distribution.png"), dpi=170)
plt.close(fig)

# ---------------------------------------------------------------- figure 6
fig, ax = plt.subplots(figsize=(6.3, 2.6))
ax.axis("off")
ax.set_xlim(0, 3)
ax.set_ylim(0, 1)
panels = [
    ("1  field semantics", "the declared number is a\ndifferent quantity from\nthe validated one",
     "G01: freeboard sigma\n0.0089 m vs freeboard\nerror 0.0915 m\n-> ratio 0.097",
     "#fdd0d0"),
    ("2  error propagation", "the sigma covers one\nretrieval stage; the user\nreceives a derived product",
     "thickness = f(freeboard,\nsnow depth, density)\ndeclared 0.6163 m\nvs measured 0.701 m\n-> ratio 0.879",
     "#fee8c8"),
    ("3  support confusion", "aggregation level and grid\nlevel carry the same single\n'accuracy' number",
     "G17 pixel 0.071 m3/m3\nG18 areal 0.040 m3/m3\nboth vs 0.040 objective\n-> 0.56 vs 1.00",
     "#e1f5d8"),
]
for i, (title, body, ex, col) in enumerate(panels):
    ax.add_patch(Rectangle((i + 0.04, 0.06), 0.92, 0.86, facecolor=col, edgecolor="#666666", lw=0.6))
    ax.text(i + 0.5, 0.83, title, ha="center", fontsize=7.8, weight="bold")
    ax.text(i + 0.5, 0.615, body, ha="center", va="center", fontsize=6.2, linespacing=1.25)
    ax.text(i + 0.5, 0.27, ex, ha="center", va="center", fontsize=5.9, color="#222222", linespacing=1.3)
    if i < 2:
        ax.add_patch(FancyArrowPatch((i + 0.97, 0.49), (i + 1.03, 0.49),
                                     arrowstyle="-|>", mutation_scale=9, color="#444444"))
fig.savefig(os.path.join(FIG, "fig06_mechanisms.pdf"))
fig.savefig(os.path.join(FIG, "fig06_mechanisms.png"), dpi=170)
plt.close(fig)

print("figures written:", sorted(f for f in os.listdir(FIG) if f.endswith(".pdf")))
