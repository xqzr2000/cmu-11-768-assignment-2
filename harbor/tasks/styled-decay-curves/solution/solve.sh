#!/bin/bash
# Reference solution: writes plot.py, then runs it to make figure.png
# and plotted_values.json in /app.
set -euo pipefail
cd /app
cat > plot.py <<'PLOT_EOF'
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

t = np.linspace(0, 10, 201)
f1 = np.exp(-0.5 * t)
f2 = np.exp(-t)
f3 = 0.5 * np.exp(-2 * t) + 1e-4

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(t, f1, color="#1b9e77", linestyle="-", marker="o", markevery=20, linewidth=2, label="exp(-0.5t)")
ax.plot(t, f2, color="#d95f02", linestyle="--", marker="s", markevery=20, linewidth=2, label="exp(-t)")
ax.plot(t, f3, color="#7570b3", linestyle="-.", marker="^", markevery=20, linewidth=2, label="0.5exp(-2t)+1e-4")
ax.set_yscale("log", base=10)
ax.set_ylim(1e-5, 2)
ax.set_xlim(0, 10)
ax.set_xlabel("t (s)")
ax.set_ylabel("amplitude")
ax.set_title("Three decays on a log scale")
ax.grid(True, which="major", linestyle=":")
ax.legend(loc="lower left")
fig.savefig("figure.png", dpi=150)
with open("plotted_values.json", "w") as handle:
    json.dump({"t": t.tolist(), "f1": f1.tolist(), "f2": f2.tolist(), "f3": f3.tolist()}, handle)
PLOT_EOF
python plot.py
