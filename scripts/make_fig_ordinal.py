"""Draw the ordinal-synthesis figure of the review (Fig. 7) from the data-extraction sheet.

Every marker is one primary study, placed at its energy score S_E or throughput/PDR score S_T
(rubric table of the manuscript) and labeled with its reference number (column ref_no).
Hollow markers: the decision mechanism is stated to run at the BS or offline (dagger flag).

Usage:  python scripts/make_fig_ordinal.py [extraction csv] [output pdf]
Defaults: data/extraction/data_extraction.csv  ->  output/fig_ordinal.pdf
Requires: matplotlib.
"""
import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "extraction" / "data_extraction.csv"
out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "output" / "fig_ordinal.pdf"
if not src.is_file():
    sys.exit(f"missing input file: {src}")

FAMILIES = ["Heuristic", "Metaheuristic", "Reinforcement-learning", "Neural-network", "Hierarchical", "Game-theoretic"]
SHORT = {"Heuristic": "Heur.", "Metaheuristic": "Meta-\nheur.", "Reinforcement-learning": "RL",
         "Neural-network": "NN", "Hierarchical": "Hier.", "Game-theoretic": "GT"}

rows = list(csv.DictReader(open(src, encoding="utf-8-sig")))
for r in rows:
    r["ref_no"] = int(r["ref_no"])
    for k in ("S_E", "S_T"):
        r[k] = int(r[k]) if r[k].strip() else None
    r["dagger"] = r["dagger_cost_excluded"].strip() == "True"
assert {r["family"] for r in rows} <= set(FAMILIES), {r["family"] for r in rows}

plt.rcParams.update({"font.size": 9, "font.family": "serif", "mathtext.fontset": "dejavuserif", "axes.linewidth": 0.6, "pdf.fonttype": 42})
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.6), sharey=True)
for ax, key, title in zip(axes, ["S_E", "S_T"],
                          ["Energy score $S_E$\n(vs. own strongest baseline)",
                           "Throughput / PDR score $S_T$\n(vs. own strongest baseline)"]):
    for i, fam in enumerate(FAMILIES):
        fam_rows = [r for r in rows if r["family"] == fam]
        scored = sorted((r for r in fam_rows if r[key] is not None), key=lambda r: r["ref_no"])
        for score in sorted({r[key] for r in scored}):
            level = [r for r in scored if r[key] == score]       # spread only the studies with the same score
            for j, r in enumerate(level):
                off = (j - (len(level) - 1) / 2) * 0.22
                face = "white" if r["dagger"] else "C0"
                ax.scatter(i + off, r[key], s=38, marker="o", facecolors=face, edgecolors="C0", linewidths=0.9, zorder=3)
                ax.annotate(str(r["ref_no"]), (i + off, r[key]), textcoords="offset points",
                            xytext=(0, 6 + 7 * (j % 2)), ha="center", fontsize=7.5, color="0.2")
        ax.text(i, 0.45, f"n={len(scored)}/{len(fam_rows)}", ha="center", va="center", fontsize=8, color="0.3")
    ax.set_xticks(range(len(FAMILIES)))
    ax.set_xticklabels([SHORT[f] for f in FAMILIES], fontsize=9)
    ax.set_xlim(-0.6, len(FAMILIES) - 0.4)
    ax.set_ylim(0.2, 6.0)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(["1\n$\\geq$30% worse", "2\n10–30% worse", "3\n±10%", "4\n10–30% better",
                        "5\n$\\geq$30% better"], fontsize=8)
    ax.set_title(title, fontsize=9)
    ax.grid(axis="y", color="0.9", linewidth=0.6, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
axes[0].set_ylabel("Ordinal score")
fig.tight_layout()
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, bbox_inches="tight", metadata={"Creator": None, "Producer": None, "CreationDate": None})
print("written:", out)
