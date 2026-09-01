"""Example .py for FigTweak — drag this file onto the canvas.
Run via CLI too:  python figtweak.py examples/plot_example.py
"""
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 6, 80)
fig, ax = plt.subplots(figsize=(6,3.5))
ax.plot(x, np.sin(x), label="sin", lw=2)
ax.plot(x, np.cos(x)*0.8, label="cos", ls="--", lw=2)
ax.set_title("Drag this .py onto FigTweak")
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.legend()

# second figure — gallery will show Fig 1 / Fig 2 to switch
fig2, ax2 = plt.subplots(figsize=(5,4))
ax2.scatter(np.random.randn(40), np.random.randn(40), s=60, alpha=0.6, edgecolor="k")
ax2.set_title("Second figure — also editable")
ax2.set_xlabel("x"); ax2.set_ylabel("y")
