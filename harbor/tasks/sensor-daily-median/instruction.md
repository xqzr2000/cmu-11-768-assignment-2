# sensor-daily-median

<!-- Copied from tasks/sensor-daily-median/task.json. This is the prompt the three fixed agents
     were given, so do NOT reword it: check-submission holds both your runs
     and this file to the descriptor's wording. Add what your verifier needs
     under the heading below instead. -->

Using matplotlib, read sensors.csv. It holds temperature readings taken every 5 minutes, with columns timestamp (YYYY-MM-DD HH:MM), sensor (S1, S2 or S3) and temp_c in degrees Celsius. A blank temp_c is a dropout: ignore it, do not treat it as zero. Using only sensors S1 and S2 (leave S3 out entirely), compute each sensor's daily MEDIAN temperature for each of the 14 calendar days from 2025-06-01 to 2025-06-14. Requirements: 1. Plot the two daily-median series as lines with circle markers against the date on the x axis, S1 in colour 'tab:blue' and S2 in colour 'tab:red'. 2. For S2 only, shade the band between its daily minimum and daily maximum temperature in 'tab:red' with alpha 0.15. 3. The x tick labels show each date as MM-DD and are rotated 45 degrees. 4. The y axis label is exactly 'Temperature (°C)'. 5. The title is exactly 'Daily median temperature, S1 vs S2'. 6. Include a legend with the entries 'S1 median', 'S2 median' and 'S2 daily range'. Save the figure as figure.png.

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
   work in a heredoc or with `python -c`; the script must stay on disk. It must read `sensors.csv` and compute the values rather than hard-code results.
   It must render the same image every time it runs.
2. **`/app/figure.png`** - the chart, exactly as saved by `plot.py`.
3. **`/app/plotted_values.json`** - the values shown in the chart, written by
   `plot.py` from the same variables passed to the plotting calls. It must contain one JSON object with exactly five keys. `dates` is a
   list of the 14 dates as strings in `MM-DD` form, in order; `S1_median`,
   `S2_median`, `S2_min` and `S2_max` are lists of 14 JSON numbers in degrees
   Celsius, aligned with `dates`. For example (shortened to two days):
   `{"dates": ["06-01", "06-02"], "S1_median": [0.0, 0.0], "S2_median": [0.0, 0.0], "S2_min": [0.0, 0.0], "S2_max": [0.0, 0.0]}`.

Do not modify `sensors.csv`.

Only matplotlib, numpy, pandas and Pillow are available and there is no
network access; everything you need is already installed.
