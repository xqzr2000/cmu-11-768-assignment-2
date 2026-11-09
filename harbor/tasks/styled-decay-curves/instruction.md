# styled-decay-curves

<!-- Copied from tasks/styled-decay-curves/task.json. This is the prompt the three fixed agents
     were given, so do NOT reword it: check-submission holds both your runs
     and this file to the descriptor's wording. Add what your verifier needs
     under the heading below instead. -->

Using matplotlib and numpy, plot three functions of t sampled on t = np.linspace(0, 10, 201): f1 = exp(-0.5 t), f2 = exp(-t) and f3 = 0.5 exp(-2 t) + 1e-4. Requirements: 1. f1 is drawn in colour '#1b9e77' as a solid line with circle markers ('o') on every 20th point (markevery=20). 2. f2 is drawn in colour '#d95f02' as a dashed line ('--') with square markers ('s') on every 20th point. 3. f3 is drawn in colour '#7570b3' as a dash-dot line ('-.') with upward triangle markers ('^') on every 20th point. 4. All three lines have line width 2. 5. The y axis is logarithmic (base 10) with limits 1e-5 to 2; the x axis limits are 0 to 10. 6. A legend in the lower left corner has the labels exactly 'exp(-0.5t)', 'exp(-t)' and '0.5exp(-2t)+1e-4'. 7. The axis labels are exactly 't (s)' and 'amplitude', and the title is exactly 'Three decays on a log scale'. 8. Major grid lines are shown on both axes as dotted lines (':'). 9. The figure is 8 x 5 inches and is saved at 150 dpi as figure.png.

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
   work in a heredoc or with `python -c`; the script must stay on disk.
   It must render the same image every time it runs.
2. **`/app/figure.png`** - the chart, exactly as saved by `plot.py`.
3. **`/app/plotted_values.json`** - the values shown in the chart, written by
   `plot.py` from the same variables passed to the plotting calls. It must contain one JSON object with exactly four keys, `t`, `f1`,
   `f2` and `f3`, each a list of 201 JSON numbers: the sample points and the three
   functions evaluated at them. For example (shortened):
   `{"t": [0.0, 0.05], "f1": [0.0, 0.0], "f2": [0.0, 0.0], "f3": [0.0, 0.0]}`.

Only matplotlib, numpy, pandas and Pillow are available and there is no
network access; everything you need is already installed.
