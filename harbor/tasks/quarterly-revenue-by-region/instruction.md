# quarterly-revenue-by-region

<!-- Copied from tasks/quarterly-revenue-by-region/task.json. This is the prompt the three fixed agents
     were given, so do NOT reword it: check-submission holds both your runs
     and this file to the descriptor's wording. Add what your verifier needs
     under the heading below instead. -->

Using matplotlib, read transactions.csv. It has one row per order with columns order_id, date (YYYY-MM-DD, all in 2025), region, product, units and unit_price (US dollars). The revenue of an order is units multiplied by unit_price. Draw a GROUPED (side-by-side) vertical bar chart of the total revenue in each calendar quarter of 2025 for each region, where Q1 is January-March, Q2 April-June, Q3 July-September and Q4 October-December. Requirements: 1. The x axis shows the four quarters in the order Q1, Q2, Q3, Q4, with tick labels exactly 'Q1', 'Q2', 'Q3', 'Q4'. 2. Within each quarter there is one bar per region, side by side, in alphabetical order: East, North, South, West. 3. Bar heights are revenue in thousands of US dollars (total revenue divided by 1000). The y axis starts at 0 and its label is exactly 'Revenue (thousand USD)'. 4. The x axis label is exactly 'Quarter of 2025'. 5. The title is exactly 'Quarterly revenue by region, 2025'. 6. Include a legend naming the four regions. 7. The figure is 10 x 6 inches and is saved at 100 dpi as figure.png.

## Required outputs

Leave these behind in `/app`, which is also the working directory. `plot.py` must
refer to every file by bare filename rather than by absolute path: the verifier
re-runs the script in a copied workspace, so an absolute path would point outside
that copy.

Extra images are allowed (for example an exploratory chart), but give them a
different stem: the answer is graded from the figure saved as `figure.png`.

1. **`/app/plot.py`** - the plotting script. Self-contained and re-runnable:
   `python plot.py` from `/app` must reproduce `figure.png` and
   `plotted_values.json` with no arguments and no manual steps. Do not do the
   work in a heredoc or with `python -c`; the script must stay on disk. It must read `transactions.csv` and compute the values rather than hard-code results.
   It must render the same image every time it runs.
2. **`/app/figure.png`** - the chart, exactly as saved by `plot.py`.
3. **`/app/plotted_values.json`** - the values shown in the chart, written by
   `plot.py` from the same variables passed to the plotting calls. It must contain one JSON object with exactly four keys, `East`, `North`,
   `South` and `West`. Each value is a list of four JSON numbers: that region's
   revenue in thousands of US dollars for Q1, Q2, Q3 and Q4, in that order, with no
   unit suffix. For example:
   `{"East": [0.0, 0.0, 0.0, 0.0], "North": [0.0, 0.0, 0.0, 0.0], "South": [0.0, 0.0, 0.0, 0.0], "West": [0.0, 0.0, 0.0, 0.0]}`.

Do not modify `transactions.csv`.

Only matplotlib, numpy, pandas and Pillow are available and there is no
network access; everything you need is already installed.
