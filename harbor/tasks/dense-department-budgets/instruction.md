# dense-department-budgets

<!-- Copied from tasks/dense-department-budgets/task.json. This is the prompt the three fixed agents
     were given, so do NOT reword it: check-submission holds both your runs
     and this file to the descriptor's wording. Add what your verifier needs
     under the heading below instead. -->

Using matplotlib, draw a vertical bar chart of this year's IT budget, in thousand dollars, for 30 public-sector departments. The data, in the order it must appear from left to right, is: Department of Transportation and Infrastructure: 114; Ministry of Health and Long-Term Care: 240; Office of the Auditor General: 742; Department of Fisheries and Oceans: 427; Ministry of Education and Child Care: 398; Agency for Environmental Protection: 101; Department of Finance and Treasury Board: 631; Office of Indigenous Relations: 585; Ministry of Labour and Workforce Development: 246; Department of Agriculture and Agri-Food: 769; Office of the Chief Information Officer: 198; Ministry of Housing and Municipal Affairs: 851; Department of Justice and Public Safety: 22; Agency for Statistics and Data Services: 328; Ministry of Energy, Mines and Low Carbon Innovation: 763; Department of Tourism, Arts and Culture: 118; Office of the Ombudsperson: 162; Ministry of Forests and Range Management: 398; Department of Veterans Affairs: 701; Agency for Emergency Management: 584; Ministry of Post-Secondary Education and Skills: 181; Department of Public Works and Procurement: 254; Office of the Information and Privacy Commissioner: 283; Ministry of Citizens' Services: 635; Department of Trade and Investment: 725; Agency for Water Stewardship: 885; Ministry of Social Development and Poverty Reduction: 620; Department of Northern Affairs: 390; Office of the Seniors Advocate: 278; Ministry of Mental Health and Addictions: 475. Requirements: 1. One bar per department, in exactly the order given above. 2. The x tick labels are the full department names, rotated 60 degrees, right-aligned (ha='right'), in font size 8; every tick label must be fully visible inside the saved image and none may overlap another. 3. The y axis label is exactly 'IT budget (thousand $)' and the y axis starts at 0. 4. The title is exactly 'IT budget by department'. 5. Bars are coloured '#2a9d8f'. 6. The figure is 12 x 6 inches and is saved at 100 dpi as figure.png.

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
   `plot.py` from the same variables passed to the plotting calls. It must contain one JSON object with exactly two keys: `departments`,
   the 30 department names as strings in left-to-right order, and `budgets_k`, the
   30 budgets in thousand dollars as JSON numbers in the same order. For example
   (shortened): `{"departments": ["A", "B"], "budgets_k": [0, 0]}`.

Only matplotlib, numpy, pandas and Pillow are available and there is no
network access; everything you need is already installed.
