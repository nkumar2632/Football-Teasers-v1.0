# Phase 2 — NFL 2024 calibration of frozen Teaser Model v1.0

**Calibration only.** No price, no EV, no ROI. Every probability below is a **model-estimated hit probability**, never an objective or true probability.

- Lines are **archived reference lines** (`archived_reference_line`). The source documents no capture time; commit-history inspection shows the value is whatever a periodic scrape caught last before the final score landed. It is **not** a closing line and supports no CLV claim.
- No historical teaser menu prices exist in this source and none have been invented. No EV, break-even or ROI figure appears in this phase.
- **2024 and 2025 run on different upstream line feeds.** Opportunity counts are not comparable across the two seasons, and differences in leg volume are a property of the data source, not of the model. See `reports/nfl_line_composition_investigation.md`.

## A. Season summary

| metric                           |   value |
|:---------------------------------|--------:|
| games_in_source                  | 285     |
| legs_in_source                   | 570     |
| primary_legs_before_total_filter |  61     |
| qualifying_primary_legs          |  41     |
| dropped_by_guardrail             |  20     |
| weeks                            |  22     |
| zero_qualifier_weeks             |   5     |
| mean_qualifying_legs_per_week    |   1.864 |
| median_qualifying_legs_per_week  |   2     |
| max_qualifying_legs_in_a_week    |   8     |

## B. Results by exact primary shape

Calibration gap = actual hit rate − mean P_est. Positive means the legs won more
often than the frozen model expected. Intervals are exact (Clopper–Pearson) 95%.

| shape   | geometry     |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:--------|:-------------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| +1.5    | +1.5 -> +7.5 |   8 |       0.7454 |            0.75   |          0.004558 |     0.3491 |      0.9681 | True         |
| +2.5    | +2.5 -> +8.5 |  20 |       0.7545 |            0.85   |          0.09552  |     0.6211 |      0.9679 | False        |
| -7.5    | -7.5 -> -1.5 |  13 |       0.7516 |            0.6154 |         -0.1362   |     0.3158 |      0.8614 | True         |
| -8.5    | -8.5 -> -2.5 |   0 |     nan      |          nan      |        nan        |   nan      |    nan      | True         |

Rows with N < 20 are marked `low_sample` and are reported as-is; no
bucket was merged after seeing outcomes.

## C. Results by game-total bucket

| bucket   |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:---------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| <=40     |   9 |       0.7709 |            0.6667 |          -0.1042  |     0.2993 |      0.9251 | True         |
| 40.5-43  |  14 |       0.7534 |            0.9286 |           0.1752  |     0.6613 |      0.9982 | True         |
| 43.5-45  |  10 |       0.7444 |            0.7    |          -0.04437 |     0.3475 |      0.9333 | True         |
| 45.5-47  |   8 |       0.7369 |            0.625  |          -0.1119  |     0.2449 |      0.9148 | True         |

## D. Results by predeclared P_est bucket

Buckets were fixed before any outcome was observed. Empty buckets are left empty.

| bucket   |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:---------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| <70%     |   0 |     nan      |          nan      |         nan       |   nan      |    nan      | True         |
| 70-71.9% |   0 |     nan      |          nan      |         nan       |   nan      |    nan      | True         |
| 72-73.9% |   8 |       0.7369 |            0.625  |          -0.1119  |     0.2449 |      0.9148 | True         |
| >=74%    |  33 |       0.7554 |            0.7879 |           0.03247 |     0.6109 |      0.9102 | False        |

## E. Proper scoring

| metric                     |   value |
|:---------------------------|--------:|
| qualifying primary legs    | 41      |
| mean P_est                 |  0.7518 |
| expected wins = sum(P_est) | 30.82   |
| actual wins                | 31      |
| actual − expected          |  0.1767 |
| actual hit rate            |  0.7561 |
| Brier score                |  0.1839 |

**Calibration intercept/slope omitted.** N = 41 is below the 500 needed for a stable logistic fit; p_est spans only 0.0434 (0.7348-0.7781), below the 0.10 needed to identify a slope. Reporting a slope here would be noise presented as a finding, so it is left out rather than caveated.

## F. Weekly top-four construction

Legs ranked within each week by full-precision P_est; top four retained.
No EV or pricing is attached in Phase 2.

| qualifying_legs_in_week   |   weeks |
|:--------------------------|--------:|
| 0                         |       5 |
| 1                         |       5 |
| 2                         |       5 |
| 3                         |       6 |
| >=4                       |       1 |

- Constructible weeks (≥2 qualifying legs): **12** of 22
- 2-team tickets constructible: **29**
- 3-team tickets constructible: **10**

### Per-week detail

|   season |   week |   n_qualifying_legs |   n_top_legs | constructible   |   n_tickets_2team |   n_tickets_3team |   n_legs_winning |
|---------:|-------:|--------------------:|-------------:|:----------------|------------------:|------------------:|-----------------:|
|     2024 |      1 |                   1 |            1 | False           |                 0 |                 0 |                1 |
|     2024 |      2 |                   1 |            1 | False           |                 0 |                 0 |                1 |
|     2024 |      3 |                   2 |            2 | True            |                 1 |                 0 |                1 |
|     2024 |      4 |                   8 |            4 | True            |                 6 |                 4 |                6 |
|     2024 |      5 |                   3 |            3 | True            |                 3 |                 1 |                3 |
|     2024 |      6 |                   2 |            2 | True            |                 1 |                 0 |                2 |
|     2024 |      7 |                   1 |            1 | False           |                 0 |                 0 |                0 |
|     2024 |      8 |                   3 |            3 | True            |                 3 |                 1 |                2 |
|     2024 |      9 |                   3 |            3 | True            |                 3 |                 1 |                2 |
|     2024 |     10 |                   3 |            3 | True            |                 3 |                 1 |                3 |
|     2024 |     11 |                   2 |            2 | True            |                 1 |                 0 |                1 |
|     2024 |     12 |                   1 |            1 | False           |                 0 |                 0 |                1 |
|     2024 |     13 |                   1 |            1 | False           |                 0 |                 0 |                1 |
|     2024 |     14 |                   0 |            0 | False           |                 0 |                 0 |                0 |
|     2024 |     15 |                   3 |            3 | True            |                 3 |                 1 |                2 |
|     2024 |     16 |                   2 |            2 | True            |                 1 |                 0 |                2 |
|     2024 |     17 |                   2 |            2 | True            |                 1 |                 0 |                1 |
|     2024 |     18 |                   3 |            3 | True            |                 3 |                 1 |                2 |
|     2024 |     19 |                   0 |            0 | False           |                 0 |                 0 |                0 |
|     2024 |     20 |                   0 |            0 | False           |                 0 |                 0 |                0 |
|     2024 |     21 |                   0 |            0 | False           |                 0 |                 0 |                0 |
|     2024 |     22 |                   0 |            0 | False           |                 0 |                 0 |                0 |

## G. Ticket hit rates and independence diagnostic

> **Descriptive only.** These tickets are not independent observations: no historical teaser price exists, tickets within a week are correlated, and the same legs appear in many combinations. Do not read these as a track record.

| ticket_size   |   n_tickets |   mean_predicted_p_ticket |   realized_hit_rate |      gap |   ci95_low |   ci95_high |   same_game_tickets |
|:--------------|------------:|--------------------------:|--------------------:|---------:|-----------:|------------:|--------------------:|
| 2-team        |          29 |                    0.5674 |              0.5172 | -0.05017 |    0.3253  |      0.7055 |                   0 |
| 3-team        |          10 |                    0.4339 |              0.3    | -0.1339  |    0.06674 |      0.6525 |                   0 |

- Tickets combining two legs from the same NFL game: **0**. Zero, as the frozen geometry requires: the primary set contains no complementary pair, so a game can contribute at most one primary leg.

## Limitations

- Sample: **41 qualifying primary legs** in 2024. Confidence intervals in every table above are wide; individual shape and bucket gaps are not distinguishable from noise at this size.
- P_est spans only 0.7348-0.7781 by construction (constant bump, total capped at 47), so two predeclared P_est buckets are structurally unreachable and reported empty.
- Postseason weeks contribute 0 qualifying legs; the weekly distribution is effectively regular-season with structural zeros.
- Ticket rows are correlated and unpriced; see §G.
- No CLV or line-movement measurement is possible from this source.

## Machine-readable outputs

- `data/processed/phase2_legs_all_2024.csv` — every graded leg
- `data/processed/phase2_legs_qualifying_2024.csv` — qualifying primary legs
- `data/processed/phase2_top_legs_2024.csv` — weekly top-four selections
- `data/processed/phase2_tickets_2024.csv` — every constructible ticket
- `data/processed/phase2_weekly_2024.csv` — weekly counts including zeros

