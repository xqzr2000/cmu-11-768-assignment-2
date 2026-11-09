#!/bin/bash
# MUTANT: Correct values, names, order, colour and size, but the 30 long tick labels
# are left horizontal and centred, so they overprint into an unreadable band,
# and without tight_layout the outer ones run off the canvas. Expected reward
# 1.0: no assertion measures rotation, overlap or clipping.
set -euo pipefail
cd /app
cat > plot.py <<'PLOT_EOF'
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA = """Department of Transportation and Infrastructure: 114; Ministry of Health and Long-Term Care: 240; Office of the Auditor General: 742; Department of Fisheries and Oceans: 427; Ministry of Education and Child Care: 398; Agency for Environmental Protection: 101; Department of Finance and Treasury Board: 631; Office of Indigenous Relations: 585; Ministry of Labour and Workforce Development: 246; Department of Agriculture and Agri-Food: 769; Office of the Chief Information Officer: 198; Ministry of Housing and Municipal Affairs: 851; Department of Justice and Public Safety: 22; Agency for Statistics and Data Services: 328; Ministry of Energy, Mines and Low Carbon Innovation: 763; Department of Tourism, Arts and Culture: 118; Office of the Ombudsperson: 162; Ministry of Forests and Range Management: 398; Department of Veterans Affairs: 701; Agency for Emergency Management: 584; Ministry of Post-Secondary Education and Skills: 181; Department of Public Works and Procurement: 254; Office of the Information and Privacy Commissioner: 283; Ministry of Citizens' Services: 635; Department of Trade and Investment: 725; Agency for Water Stewardship: 885; Ministry of Social Development and Poverty Reduction: 620; Department of Northern Affairs: 390; Office of the Seniors Advocate: 278; Ministry of Mental Health and Addictions: 475"""
pairs = [item.rsplit(": ", 1) for item in DATA.split("; ")]
names = [name for name, _ in pairs]
budgets = [int(value) for _, value in pairs]

fig, ax = plt.subplots(figsize=(12, 6))
ax.bar(range(len(names)), budgets, color="#2a9d8f")
ax.set_xticks(range(len(names)), names, fontsize=8)
ax.set_ylabel("IT budget (thousand $)")
ax.set_title("IT budget by department")
ax.set_ylim(bottom=0)
ax.set_xlim(-0.6, len(names) - 0.4)
fig.savefig("figure.png", dpi=100)
with open("plotted_values.json", "w") as handle:
    json.dump({"departments": names, "budgets_k": budgets}, handle, indent=2)
PLOT_EOF
python plot.py
