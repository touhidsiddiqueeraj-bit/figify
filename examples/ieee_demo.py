"""IEEE demo — shows enforce vs default.

Agent usage:
    import figtweak
    fig, ax = plt.subplots(figsize=figtweak.ieee_single())  # 3.45x2.6"
    ax.plot(...)
    figtweak.fix(fig, template="ieee-access-single")  # enforce
    figtweak.save(fig, "fig.svg", template="ieee-access-single")

Or CLI: python figtweak.py examples/ieee_demo.py  (auto uses default, no template)
For enforce, edit this file to call fix() or save with template.
"""
import matplotlib.pyplot as plt
import numpy as np
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import figtweak

# --- Bad: default 6.4x4.8, small fonts when scaled to 3.5" ---
fig, ax = plt.subplots(figsize=(6.4, 4.8))
x = np.linspace(0, 6, 80)
ax.plot(x, np.sin(x), label="sin, overlapping legend demo")
ax.plot(x, np.cos(x), label="cos")
ax.set_title("Default 6.4\" — too small when scaled")
ax.set_xlabel("x (rad)"); ax.set_ylabel("amplitude")
ax.legend()  # will overlap
# don't fix — save as is to show problem
figtweak.save(fig, "ieee_bad.svg")
print("wrote ieee_bad.svg (default, will be tiny at 3.5\")")
print(" lint:", figtweak.lint(fig))
plt.close(fig)

# --- Good: enforce IEEE single ---
fig, ax = plt.subplots(figsize=figtweak.ieee_single())
ax.plot(x, np.sin(x), label="sin")
ax.plot(x, np.cos(x), label="cos")
ax.set_title("IEEE Access single — enforced")
ax.set_xlabel("x (rad)"); ax.set_ylabel("amplitude")
ax.legend()
figtweak.fix(fig, template="ieee-access-single")
print(" lint after fix:", figtweak.lint(fig))
figtweak.save(fig, "ieee_good.svg", template="ieee-access-single")
print("wrote ieee_good.svg (3.45\" Times 8pt, legend outside, tight)")

# --- Double column ---
fig, ax = plt.subplots(figsize=figtweak.ieee_double())
ax.plot(x, np.sin(x))
ax.set_title("IEEE double 7.16\"")
figtweak.fix(fig, template="ieee-access-double")
figtweak.save(fig, "ieee_double.svg", template="ieee-access-double")
print("wrote ieee_double.svg")
