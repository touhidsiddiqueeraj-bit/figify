#!/usr/bin/env python3
"""
IEEE high-quality samples — uses figtweak.fix(enforce) so you can see the difference.

Generates:
  ieee_sample_line_single.svg / .png   — 3.45" single, Times 8pt, legend outside
  ieee_sample_bar_single.svg/.png      — bar + error
  ieee_sample_scatter_double.svg/.png  — 7.16" double, scatter + colorbar
  ieee_sample_comparison.png           — side-by-side bad vs good (for README)

Run: python examples/ieee_samples.py
Then drag any .svg onto http://localhost:8765 (or open gallery.html)
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import figtweak
import matplotlib.pyplot as plt
import numpy as np

# ensure Times available, fallback to DejaVu Serif
plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "Times", "DejaVu Serif"]

OUT = pathlib.Path(__file__).parent
np.random.seed(0)

# 1 — Line, single column, 2 series, legend outside, grid
fig, ax = plt.subplots(figsize=figtweak.ieee_single())
x = np.linspace(0, 6, 80)
ax.plot(x, np.sin(x), label="Signal A", lw=1.5)
ax.plot(x, np.cos(x)*0.8, label="Signal B", lw=1.5, ls="--")
ax.set_title("IEEE Access single — line")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Amplitude (a.u.)")
ax.grid(True, alpha=0.3)
ax.legend(frameon=True)
# lint before fix
print("line lint before:", figtweak.lint(fig))
figtweak.fix(fig, template="ieee-access-single")
print("line lint after:", figtweak.lint(fig))
figtweak.save(fig, str(OUT / "ieee_sample_line_single.svg"), template="ieee-access-single")
# also PNG @300dpi for paper
fig.savefig(str(OUT / "ieee_sample_line_single.png"), dpi=300)
print("wrote ieee_sample_line_single.svg/png")
plt.close(fig)

# 2 — Bar, single, with error bars
fig, ax = plt.subplots(figsize=figtweak.ieee_single())
cats = ["Ctrl", "A", "B", "C"]
vals = [3.2, 5.1, 4.3, 6.0]
err = [0.3, 0.4, 0.35, 0.5]
ax.bar(cats, vals, yerr=err, capsize=4, color="#4f6ef7", edgecolor="black", linewidth=0.6)
ax.set_title("Single — bar + error")
ax.set_ylabel("Score")
ax.set_ylim(0, 7)
print("bar lint:", figtweak.lint(fig))
figtweak.fix(fig, template="ieee-access-single")
figtweak.save(fig, str(OUT / "ieee_sample_bar_single.svg"), template="ieee-access-single")
fig.savefig(str(OUT / "ieee_sample_bar_single.png"), dpi=300)
print("wrote ieee_sample_bar_single.svg/png")
plt.close(fig)

# 3 — Scatter double column, with colorbar
fig, ax = plt.subplots(figsize=figtweak.ieee_double())
n=120
x = np.random.randn(n)
y = np.random.randn(n) + 0.5*x
c = np.hypot(x, y)
sc = ax.scatter(x, y, c=c, s=18, cmap="viridis", edgecolor="k", linewidth=0.3, alpha=0.85)
ax.set_title("IEEE double — scatter + colorbar")
ax.set_xlabel("Feature 1")
ax.set_ylabel("Feature 2")
cb = fig.colorbar(sc, ax=ax, shrink=0.85)
cb.set_label("Distance")
figtweak.fix(fig, template="ieee-access-double")
figtweak.save(fig, str(OUT / "ieee_sample_scatter_double.svg"), template="ieee-access-double")
fig.savefig(str(OUT / "ieee_sample_scatter_double.png"), dpi=300)
print("wrote ieee_sample_scatter_double.svg/png")
plt.close(fig)

# 4 — Comparison: bad (6.4") vs good (3.45") side-by-side for docs
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.16, 2.8), sharey=True)
x = np.linspace(0, 4, 60)
for ax, title in [(ax1, "Bad: 6.4\" default\n(5.8pt when scaled)"), (ax2, "Good: IEEE 3.45\" enforced\n(8pt Times, legend outside)")]:
    ax.plot(x, np.sin(x), label="sin")
    ax.plot(x, np.cos(x), label="cos")
    ax.set_title(title, fontsize=8)
    ax.set_xlabel("x")
    ax.legend(fontsize=6)
    ax.grid(True, alpha=0.3)
# left is bad (no fix), right will be fixed via SVG template? For PNG we fix the whole fig
figtweak.fix(fig, template="ieee-access-double")
fig.savefig(str(OUT / "ieee_comparison.png"), dpi=300)
fig.savefig(str(OUT / "ieee_comparison.svg"))
print("wrote ieee_comparison.png/svg")

print("\nAll IEEE samples done. Open examples/gallery.html or drag SVGs into Figify.")
