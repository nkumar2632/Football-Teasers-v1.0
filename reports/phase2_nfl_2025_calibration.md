# Phase 2 — NFL 2025 calibration of frozen Teaser Model v1.0

**Calibration only.** No price, no EV, no ROI. Every probability below is a **model-estimated hit probability**, never an objective or true probability.

- Lines are **archived reference lines** (`archived_reference_line`). The source documents no capture time; commit-history inspection shows the value is whatever a periodic scrape caught last before the final score landed. It is **not** a closing line and supports no CLV claim.
- No historical teaser menu prices exist in this source and none have been invented. No EV, break-even or ROI figure appears in this phase.
- **2024 and 2025 run on different upstream line feeds.** Opportunity counts are not comparable across the two seasons, and differences in leg volume are a property of the data source, not of the model. See `reports/nfl_line_composition_investigation.md`.

## A. Season summary

| metric                           |   value |
|:---------------------------------|--------:|
| games_in_source                  | 285     |
| legs_in_source                   | 570     |
| primary_legs_before_total_filter |  99     |
| qualifying_primary_legs          |  63     |
| dropped_by_guardrail             |  36     |
| weeks                            |  22     |
| zero_qualifier_weeks             |   3     |
| mean_qualifying_legs_per_week    |   2.864 |
| median_qualifying_legs_per_week  |   3     |
| max_qualifying_legs_in_a_week    |   7     |

## B. Results by exact primary shape

Calibration gap = actual hit rate − mean P_est. Positive means the legs won more
often than the frozen model expected. Intervals are exact (Clopper–Pearson) 95%.

| shape   | geometry     |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:--------|:-------------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| +1.5    | +1.5 -> +7.5 |  24 |       0.7508 |             0.875 |         0.1242    |     0.6764 |      0.9734 | False        |
| +2.5    | +2.5 -> +8.5 |  24 |       0.7493 |             0.75  |         0.0006522 |     0.5329 |      0.9023 | False        |
| -7.5    | -7.5 -> -1.5 |  10 |       0.758  |             0.7   |        -0.05796   |     0.3475 |      0.9333 | True         |
| -8.5    | -8.5 -> -2.5 |   5 |       0.7498 |             0.6   |        -0.1498    |     0.1466 |      0.9473 | True         |

Rows with N < 20 are marked `low_sample` and are reported as-is; no
bucket was merged after seeing outcomes.

## C. Results by game-total bucket

| bucket   |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:---------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| <=40     |  10 |       0.77   |            0.7    |          -0.06996 |     0.3475 |      0.9333 | True         |
| 40.5-43  |  21 |       0.7549 |            0.6667 |          -0.08824 |     0.4303 |      0.8541 | False        |
| 43.5-45  |  20 |       0.7459 |            0.9    |           0.1541  |     0.683  |      0.9877 | False        |
| 45.5-47  |  12 |       0.7384 |            0.8333 |           0.09489 |     0.5159 |      0.9791 | True         |

## D. Results by predeclared P_est bucket

Buckets were fixed before any outcome was observed. Empty buckets are left empty.

| bucket   |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:---------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| <70%     |   0 |     nan      |          nan      |         nan       |   nan      |    nan      | True         |
| 70-71.9% |   0 |     nan      |          nan      |         nan       |   nan      |    nan      | True         |
| 72-73.9% |  12 |       0.7384 |            0.8333 |           0.09489 |     0.5159 |      0.9791 | True         |
| >=74%    |  51 |       0.7543 |            0.7647 |           0.0104  |     0.6251 |      0.8721 | False        |

## E. Proper scoring

| metric                     |   value |
|:---------------------------|--------:|
| qualifying primary legs    | 63      |
| mean P_est                 |  0.7513 |
| expected wins = sum(P_est) | 47.33   |
| actual wins                | 49      |
| actual − expected          |  1.669  |
| actual hit rate            |  0.7778 |
| Brier score                |  0.1754 |

**Calibration intercept/slope omitted.** N = 63 is below the 500 needed for a stable logistic fit; p_est spans only 0.0525 (0.7364-0.7889), below the 0.10 needed to identify a slope. Reporting a slope here would be noise presented as a finding, so it is left out rather than caveated.

## F. Weekly top-four construction

Legs ranked within each week by full-precision P_est; top four retained.
No EV or pricing is attached in Phase 2.

| qualifying_legs_in_week   |   weeks |
|:--------------------------|--------:|
| 0                         |       3 |
| 1                         |       4 |
| 2                         |       3 |
| 3                         |       4 |
| >=4                       |       8 |

- Constructible weeks (≥2 qualifying legs): **15** of 22
- 2-team tickets constructible: **63**
- 3-team tickets constructible: **36**

### Per-week detail

|   season |   week |   n_qualifying_legs |   n_top_legs | constructible   |   n_tickets_2team |   n_tickets_3team |   n_legs_winning |
|---------:|-------:|--------------------:|-------------:|:----------------|------------------:|------------------:|-----------------:|
|     2025 |      1 |                   4 |            4 | True            |                 6 |                 4 |                4 |
|     2025 |      2 |                   4 |            4 | True            |                 6 |                 4 |                4 |
|     2025 |      3 |                   7 |            4 | True            |                 6 |                 4 |                5 |
|     2025 |      4 |                   6 |            4 | True            |                 6 |                 4 |                6 |
|     2025 |      5 |                   5 |            4 | True            |                 6 |                 4 |                1 |
|     2025 |      6 |                   2 |            2 | True            |                 1 |                 0 |                2 |
|     2025 |      7 |                   5 |            4 | True            |                 6 |                 4 |                2 |
|     2025 |      8 |                   2 |            2 | True            |                 1 |                 0 |                0 |
|     2025 |      9 |                   2 |            2 | True            |                 1 |                 0 |                2 |
|     2025 |     10 |                   3 |            3 | True            |                 3 |                 1 |                3 |
|     2025 |     11 |                   3 |            3 | True            |                 3 |                 1 |                3 |
|     2025 |     12 |                   1 |            1 | False           |                 0 |                 0 |                1 |
|     2025 |     13 |                   0 |            0 | False           |                 0 |                 0 |                0 |
|     2025 |     14 |                   6 |            4 | True            |                 6 |                 4 |                4 |
|     2025 |     15 |                   4 |            4 | True            |                 6 |                 4 |                4 |
|     2025 |     16 |                   3 |            3 | True            |                 3 |                 1 |                3 |
|     2025 |     17 |                   3 |            3 | True            |                 3 |                 1 |                2 |
|     2025 |     18 |                   0 |            0 | False           |                 0 |                 0 |                0 |
|     2025 |     19 |                   1 |            1 | False           |                 0 |                 0 |                1 |
|     2025 |     20 |                   1 |            1 | False           |                 0 |                 0 |                1 |
|     2025 |     21 |                   1 |            1 | False           |                 0 |                 0 |                1 |
|     2025 |     22 |                   0 |            0 | False           |                 0 |                 0 |                0 |

## G. Ticket hit rates and independence diagnostic

> **Descriptive only.** These tickets are not independent observations: no historical teaser price exists, tickets within a week are correlated, and the same legs appear in many combinations. Do not read these as a track record.

| ticket_size   |   n_tickets |   mean_predicted_p_ticket |   realized_hit_rate |     gap |   ci95_low |   ci95_high |   same_game_tickets |
|:--------------|------------:|--------------------------:|--------------------:|--------:|-----------:|------------:|--------------------:|
| 2-team        |          63 |                     0.568 |              0.619  | 0.05106 |     0.488  |      0.7385 |                   0 |
| 3-team        |          36 |                     0.428 |              0.5278 | 0.09982 |     0.3549 |      0.6959 |                   0 |

- Tickets combining two legs from the same NFL game: **0**. Zero, as the frozen geometry requires: the primary set contains no complementary pair, so a game can contribute at most one primary leg.

## Limitations

- Sample: **63 qualifying primary legs** in 2025. Confidence intervals in every table above are wide; individual shape and bucket gaps are not distinguishable from noise at this size.
- P_est spans only 0.7364-0.7889 by construction (constant bump, total capped at 47), so two predeclared P_est buckets are structurally unreachable and reported empty.
- Postseason weeks contribute 3 qualifying legs; the weekly distribution is effectively regular-season with structural zeros.
- Ticket rows are correlated and unpriced; see §G.
- No CLV or line-movement measurement is possible from this source.

## Machine-readable outputs

- `data/processed/phase2_legs_all_2025.csv` — every graded leg
- `data/processed/phase2_legs_qualifying_2025.csv` — qualifying primary legs
- `data/processed/phase2_top_legs_2025.csv` — weekly top-four selections
- `data/processed/phase2_tickets_2025.csv` — every constructible ticket
- `data/processed/phase2_weekly_2025.csv` — weekly counts including zeros

