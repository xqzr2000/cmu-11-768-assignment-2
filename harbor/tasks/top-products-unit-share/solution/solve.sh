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
import pandas as pd

df = pd.read_csv("transactions.csv")
units = df.groupby("product")["units"].sum()
share = units / units.sum() * 100
top = share.sort_values(ascending=False).head(8)

fig, ax = plt.subplots(figsize=(8, 5))
order = top.index[::-1]  # barh draws bottom-up, so the largest ends on top
bars = ax.barh(order, top[order].values, color="#4C72B0")
for bar, value in zip(bars, top[order].values):
    ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2, f"{value:.1f}%", va="center")
ax.set_xlabel("Share of all units sold (%)")
ax.set_title("Top 8 products by unit share")
ax.set_xlim(0, top.max() * 1.15)
fig.tight_layout()
fig.savefig("figure.png")
with open("plotted_values.json", "w") as handle:
    json.dump({"products": list(top.index),
               "share_pct": [round(float(v), 4) for v in top.values]}, handle, indent=2)
PLOT_EOF
python plot.py
