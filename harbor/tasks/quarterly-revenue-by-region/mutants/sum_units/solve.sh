#!/bin/bash
# MUTANT: Sums units per region and quarter instead of revenue (units * unit_price).
# Expected reward 0: test_s5_sidecar_matches_key and
# test_s2_sixteen_vertical_bars_with_the_right_heights reject it.
set -euo pipefail
cd /app
cat > plot.py <<'PLOT_EOF'
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

df = pd.read_csv("transactions.csv", parse_dates=["date"])
df["revenue"] = df["units"] * 1000  # BUG: units, not dollars
df["quarter"] = "Q" + df["date"].dt.quarter.astype(str)
quarters = ["Q1", "Q2", "Q3", "Q4"]
regions = ["East", "North", "South", "West"]
table = (df.pivot_table(index="quarter", columns="region", values="revenue", aggfunc="sum")
           .reindex(index=quarters, columns=regions) / 1000)

fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(len(quarters))
width = 0.2
for i, region in enumerate(regions):
    ax.bar(x + (i - 1.5) * width, table[region].values, width, label=region)
ax.set_xticks(x, quarters)
ax.set_xlabel("Quarter of 2025")
ax.set_ylabel("Revenue (thousand USD)")
ax.set_title("Quarterly revenue by region, 2025")
ax.set_ylim(bottom=0)
ax.legend(title="Region")
fig.savefig("figure.png", dpi=100)
with open("plotted_values.json", "w") as handle:
    json.dump({r: [round(float(v), 4) for v in table[r].values] for r in regions}, handle, indent=2)
PLOT_EOF
python plot.py
