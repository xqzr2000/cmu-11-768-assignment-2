# top-products-unit-share

<!-- Copied from tasks/top-products-unit-share/task.json. This is the prompt the three fixed agents
     were given, so do NOT reword it: check-submission holds both your runs
     and this file to the descriptor's wording. Add what your verifier needs
     under the heading below instead. -->

Using matplotlib, read transactions.csv. It has one row per order with columns order_id, date, region, product, units and unit_price. For every product, compute the total number of units sold across all orders, and that product's share of ALL units sold by all products, as a percentage. Draw a HORIZONTAL bar chart of only the 8 products with the most units sold. Requirements: 1. One bar per product, sorted so the product with the largest share is at the TOP and the smallest of the eight at the bottom. 2. Each bar's length is the product's percentage share of all units sold; the denominator includes all products, so the eight bars do not add up to 100. 3. Write each bar's percentage just past the end of the bar, with one decimal place and a percent sign, for example '14.2%'. 4. The y tick labels are the product names. The x axis label is exactly 'Share of all units sold (%)' and the x axis starts at 0. There is no y axis label. 5. The title is exactly 'Top 8 products by unit share'. 6. All bars use the single colour '#4C72B0'. Save the figure as figure.png.

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
   `plot.py` from the same variables passed to the plotting calls. It must contain one JSON object with exactly two keys: `products`, a list
   of the eight product names as strings ordered from the largest share (top bar) to
   the smallest, and `share_pct`, a list of eight JSON numbers giving each of those
   products' percentage share of all units, in the same order, as plain numbers
   (14.2, not "14.2%"). For example:
   `{"products": ["A", "B", "C", "D", "E", "F", "G", "H"], "share_pct": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}`.

Do not modify `transactions.csv`.

Only matplotlib, numpy, pandas and Pillow are available and there is no
network access; everything you need is already installed.
