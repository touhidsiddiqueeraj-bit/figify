import matplotlib.pyplot as plt
import numpy as np, sys
sys.path.insert(0, "/home/touhid/figtweak")
import figtweak

np.random.seed(0)
x = np.linspace(0, 6, 60)
# 1. line
fig, ax = plt.subplots(figsize=(6,3.5))
ax.plot(x, np.sin(x), label="sin", lw=2)
ax.plot(x, np.cos(x), label="cos", lw=2, ls="--")
ax.set_title("Line — editable")
ax.set_xlabel("x (rad)"); ax.set_ylabel("amplitude")
ax.legend(frameon=True)
figtweak.save(fig, "/home/touhid/figtweak/examples/line.svg")
plt.close(fig)
# 2. bar
fig, ax = plt.subplots(figsize=(6,3.5))
cats = ["A","B","C","D","E"]
vals = [3,5,2,6,4]
ax.bar(cats, vals, color="#4f6ef7", edgecolor="black")
ax.set_title("Bar — editable")
figtweak.save(fig, "/home/touhid/figtweak/examples/bar.svg")
plt.close(fig)
# 3. scatter
fig, ax = plt.subplots(figsize=(5,5))
ax.scatter(np.random.randn(50), np.random.randn(50), s=60, alpha=0.6, edgecolor="k")
ax.set_title("Scatter — editable")
ax.set_xlabel("x"); ax.set_ylabel("y")
figtweak.save(fig, "/home/touhid/figtweak/examples/scatter.svg")
plt.close(fig)
print("wrote line.svg, bar.svg, scatter.svg")

# csv for import test
import csv
with open("/home/touhid/figtweak/examples/sample.csv","w",newline="") as f:
    w=csv.writer(f)
    w.writerow(["time","sensor_A","sensor_B"])
    for i in range(20):
        w.writerow([i, 10+np.sin(i*0.5)*5+np.random.randn()*0.5, 12+np.cos(i*0.4)*4+np.random.randn()*0.5])
print("wrote sample.csv")
