# Report notes (working file; the final report is report.tex)

Judge: `gpt-6.1-terra`, chat completions, `reasoning_effort=none`, flex tier.
Not the course's Qwen3-VL-30B; all numbers below are for this judge.

## Part 1 — baseline on 110 seed runs

`output/baseline_predictions.json`, 402 calls, ~3.34M prompt tokens, ~$1.71 (flex).

| family | MCC | TP | TN | FP | FN | support +/- |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| execution_failure | 0.5945 | 8 | 93 | 5 | 4 | 12/98 |
| wrong_data | 0.2363 | 22 | 27 | 46 | 3 | 25/73 |
| wrong_chart | 0.6286 | 66 | 18 | 9 | 5 | 71/27 |
| hard_to_read | 0.6345 | 29 | 52 | 7 | 10 | 39/59 |
| **macro** | **0.5235** | | | | | |

Seed fact: the 12 runs labelled `execution_failure` are exactly the 12 runs with
no `figure.png`.

### Error type A — execution judged from the trajectory's story, not the artifact

- FP (figure exists, judge says crash): 026, 047, 081, 191, 205. Evidence cites
  "exhausted its limits", "repeated format errors", "final script has a syntax
  error", even though a PNG was saved. Because the baseline short-circuits on
  execution_failure, these 5 runs also lose 3 wrong_data, 5 wrong_chart and 3
  hard_to_read true positives (11 downstream FNs).
- FN (no figure, judge says fine): 001, 145, 171 judged acceptable; 103 judged
  wrong_data/wrong_chart/hard_to_read about a figure that does not exist.
- Observable evidence: `run.figure is None` for every FN; a decodable PNG for
  every FP; trajectory exit status LimitsExceeded / RepeatedFormatError on FPs.
- Proposed change: decide execution_failure deterministically from the artifact
  (missing / non-PNG / undecodable), never from the narrative, and always run
  the other judges when a valid figure exists.

### Error type B — per-family YES/NO questions conflate families

- wrong_data FPs (46 of 73 negatives flagged). The judge answers "does the data
  differ in any way?" with YES for design problems, often saying the data is
  fine in the same breath: 021 and 090 ("data … match the request, but the
  chart is missing an x-axis label"), 013/106/130 (colormap), 009/059 (tick
  rotation), 131/143 (subplot grid), 080 (missing value labels), 034 (ticks).
- wrong_chart FPs that are really data errors: 077, 204, 216 (two values
  swapped), 008 and 069 (rows filtered out); or readability: 070, 141, 209.
- hard_to_read FNs where the problem was seen but filed elsewhere or skipped:
  173 (annotation hides curve), 175 (legend covers bars), 129 (white labels on
  white), 086 (invisible pale bars), 209 (points hidden by same-colour boxes),
  213 (colliding captions), 074 (ylabel half outside the image).
- Proposed change: one structured call that enumerates the instruction's
  requirements, tags each `data` or `design` with the official definitions and
  marks met/violated/unclear; a family fires only if a requirement of that kind
  is violated. Readability gets its own image-first call against the official
  hard_to_read checklist, told that missing/wrong elements are not legibility.

## Part 2 — implemented in validator/solution.py

1. Artifact-gated execution check (no model call).
2. Requirement checklist (data vs design) + separate readability call with
   severity; only `major` readability issues count. Image facts (pixel size,
   DPI metadata, blank) are measured and given to the judge.

### Part 2 results on the 110 seed runs (`output/pre_iteration_seed_predictions.json`)

Two passes were run; the committed file is the second.

| family | baseline MCC | Part 2 MCC (pass 2) | TP | TN | FP | FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| execution_failure | 0.5945 | 1.0000 | 12 | 98 | 0 | 0 |
| wrong_data | 0.2363 | 0.7406 | 23 | 64 | 9 | 2 |
| wrong_chart | 0.6286 | 0.9284 | 68 | 27 | 0 | 3 |
| hard_to_read | 0.6345 | 0.8297 | 33 | 57 | 2 | 6 |
| **macro** | **0.5235** | **0.8747** | | | | |

Pass 1 gave macro 0.8657 (wrong_data 0.7045, FP 11): run-to-run variance of the
judge at temperature 0 is about ±0.01 macro, mostly in wrong_data.
Cumulative judge spend after baseline + two Part 2 passes + authored pass: ~$2.66.

## Part 3 — authored runs (15 = 5 tasks x deepseek-flash / gpt-5.6-luna / glm-5.3-flash)

All 15 runs submitted a figure in 3-7 model calls (6 min total, < $1 agent spend).
Labelling method: each run's bash commands were replayed in a scratch directory
under the course's savefig hook (pixel-identical to the delivered figure, so the
manifest is exactly what was drawn); plotted values, order, labels, colours,
styles, scales and limits were checked against the independent answer keys,
then every figure was inspected by eye. Draft labels by Claude, reviewed by Russell.

Agent outcome: every run plotted the correct data with the requested design.
The only failures are legibility:
- dense-department-budgets__glm: rotated labels cut off at the bottom-left edge.
- dense-department-budgets__luna: names wrapped onto 2-4 lines collide.
- sensor-daily-median__{deepseek,glm,luna}: the upper-left legend hides the
  S2 band's upper edge near 06-02 (that day's max, ~32.1 °C). Borderline.

Pre-iteration validator on authored runs (`output/pre_iteration_authored_predictions.json`):
hard_to_read MCC 0.5547 (TP 2, TN 10, FP 0, FN 3); wrong_chart 1 FP (luna: the
judge filed "labels must not overlap" as a design violation); execution_failure,
wrong_data, wrong_chart have no positives (insufficient support, MCC 0 by
convention); macro 0.1387. The agents, not the validator, limit what the
large-input class could test: no agent produced a wrong aggregate, so the
validator's inability to verify sums over a clipped 119 KB CSV was never
exercised (its "acceptable" there is right, but not verified).

## Part 4 — changes (validator/solution.py)

1. `legibility` requirement kind, never counted as wrong_chart (fixes the luna FP).
2. Readability call: mandatory overlay inventory (every legend / annotation /
   text box and what it covers; covering data or text => hard_to_read), plus
   the four quadrants enlarged to ~1600 px (targets the sensor legend FNs and
   seed FNs 175, 213, 129, 086).

### Part 4a measured (`output/part4a_*`)

Seeds: macro 0.8327 (exec 1.0, wrong_data 0.6727, wrong_chart 0.9284,
hard_to_read 0.7296 with FP 12, FN 2). Authored: hard_to_read 1.0, macro 0.25.
The overlay rule fixed the authored FNs and 4 of 6 seed FNs (175, 213, 129,
209) but every intended overlay fired: value labels on their own segment
(016, 142, 183), annotation arrows touching their point (077, 167), a box on a
contour (097), plus 136/164/050/126/047/143. Change 6 adds `hides_information`.

### Part 4b measured (your run, to be kept as `output/part4b_*`)

Seeds: exec 1.0, wrong_data 0.6727 (FP 11 FN 3), wrong_chart 0.9012 (FP 1: 209),
hard_to_read 0.7703 (FP 7: 047 050 097 126 136 143 202; FN 4: 046 086 129 161),
macro 0.8360. Authored: hard_to_read 1.0, macro 0.25. Cumulative judge spend $4.41.

Decision: ship Part 2 + change 4 only (OVERLAY_INVENTORY = False); the seed
set is larger and more representative than the 15 authored runs.

### Final (Part 2 + change 4, OVERLAY_INVENTORY = False)

Seeds: exec 1.0, wrong_data 0.7093, wrong_chart 0.9512, hard_to_read 0.8297, macro 0.8726.
Authored: hard_to_read 0.5547, wrong_chart FP 0, macro 0.1387. Total judge spend $4.84.
check-submission: submission valid; oracles 1.0 x5; sum_units 0.0; unrotated_labels 1.0.
