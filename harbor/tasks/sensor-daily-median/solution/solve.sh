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

df = pd.read_csv("sensors.csv", parse_dates=["timestamp"])
df = df[df["sensor"].isin(["S1", "S2"])].dropna(subset=["temp_c"])
df["day"] = df["timestamp"].dt.normalize()
daily = df.groupby(["sensor", "day"])["temp_c"].agg(["median", "min", "max"])
s1, s2 = daily.loc["S1"], daily.loc["S2"]
days = s1.index

fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(days, s1["median"], "o-", color="tab:blue", label="S1 median")
ax.plot(days, s2["median"], "o-", color="tab:red", label="S2 median")
ax.fill_between(days, s2["min"], s2["max"], color="tab:red", alpha=0.15, label="S2 daily range")
ax.set_xticks(days, [d.strftime("%m-%d") for d in days], rotation=45)
ax.set_ylabel("Temperature (°C)")
ax.set_title("Daily median temperature, S1 vs S2")
ax.legend()
fig.tight_layout()
fig.savefig("figure.png")
with open("plotted_values.json", "w") as handle:
    json.dump({
        "dates": [d.strftime("%m-%d") for d in days],
        "S1_median": [round(float(v), 4) for v in s1["median"]],
        "S2_median": [round(float(v), 4) for v in s2["median"]],
        "S2_min": [round(float(v), 4) for v in s2["min"]],
        "S2_max": [round(float(v), 4) for v in s2["max"]],
    }, handle, indent=2)
PLOT_EOF
python plot.py
