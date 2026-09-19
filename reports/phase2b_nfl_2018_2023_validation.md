# Phase 2B — NFL 2018-2023 out-of-sample validation of frozen Teaser Model v1.0

**Validation only.** Frozen Teaser Model v1.0 is unchanged by this phase. Nothing below is a recommendation to alter it.

- Lines are **archived reference lines** (`archived_reference_line`). The source documents no capture time. They are **not** closing lines and support no CLV claim.
- No historical teaser menu prices exist in this source and none have been invented. No EV, break-even, payout or ROI figure appears in this phase.
- **Three source regimes.** 2018-2023 and 2024 sit on the pre-2025 line feed; 2025 sits on a different feed. Blocks are never silently pooled; see `reports/nfl_line_composition_investigation.md`.

Hypotheses H1-H3 were declared before these seasons' outcomes were examined. 2018-2023 is the validation sample; 2024-2025 generated the hypotheses and is shown separately, never merged into the validation block.

## 0. Data-quality gate, run independently per season

The existing frozen audit gate was applied unchanged to each season on its own. No threshold was altered and no check was relaxed.

|   season | verdict   |   missing_spreads |   missing_totals |   spreads_off_grid |   totals_off_grid |   spread_half_point_share |   total_half_point_share |   duplicates | warnings               |
|---------:|:----------|------------------:|-----------------:|-------------------:|------------------:|--------------------------:|-------------------------:|-------------:|:-----------------------|
|     2018 | PASS      |                 0 |                0 |                  0 |                 0 |                    0.4906 |                   0.4644 |            0 | none                   |
|     2019 | PASS      |                 0 |                0 |                  0 |                 0 |                    0.4644 |                   0.3783 |            0 | total_half_point_share |
|     2020 | PASS      |                 0 |                0 |                  0 |                 0 |                    0.4721 |                   0.4275 |            0 | none                   |
|     2021 | PASS      |                 0 |                0 |                  0 |                 0 |                    0.5053 |                   0.4281 |            0 | none                   |
|     2022 | PASS      |                 0 |                0 |                  0 |                 0 |                    0.4894 |                   0.4718 |            0 | none                   |
|     2023 | PASS      |                 0 |                0 |                  0 |                 0 |                    0.5158 |                   0.5474 |            0 | none                   |

**All six seasons PASS.** No season was excluded.

### Primary-geometry leg counts per season (before the total guardrail)

|   season |   +1.5 |   +2.5 |   -7.5 |   -8.5 |   total |
|---------:|-------:|-------:|-------:|-------:|--------:|
|     2018 |      7 |     23 |     18 |      8 |      56 |
|     2019 |      7 |     15 |     10 |      1 |      33 |
|     2020 |      7 |     19 |     22 |      4 |      52 |
|     2021 |      2 |     26 |     18 |      6 |      52 |
|     2022 |      5 |     35 |     11 |      6 |      57 |
|     2023 |     14 |     37 |     13 |      3 |      67 |

**2020 is retained.** It passes the gate on its own. It is flagged here as the COVID-era season — no crowds for most games, compressed protocols — and that flag was set before its outcomes were examined. It is not excluded on the basis of results.

## 1. Per-season results (H1)

|   season |   games |   primary_before_guardrail |   qualifying |   mean_p_est |   predicted_wins |   actual_wins |   actual_hit_rate |   calibration_gap |   brier_frozen |   brier_constant |   delta_brier |   logloss_frozen |   logloss_constant |   delta_logloss |   zero_qualifier_weeks |
|---------:|--------:|---------------------------:|-------------:|-------------:|-----------------:|--------------:|------------------:|------------------:|---------------:|-----------------:|--------------:|-----------------:|-------------------:|----------------:|-----------------------:|
|     2018 |     267 |                         56 |           37 |       0.7489 |            27.71 |            25 |            0.6757 |         -0.07318  |         0.2259 |           0.2245 |     0.001375  |           0.6475 |             0.6435 |       0.003912  |                      5 |
|     2019 |     267 |                         33 |           23 |       0.7476 |            17.19 |            17 |            0.7391 |         -0.008441 |         0.191  |           0.1929 |    -0.001847  |           0.5691 |             0.5742 |      -0.00503   |                      9 |
|     2020 |     269 |                         52 |           25 |       0.7424 |            18.56 |            22 |            0.88   |          0.1376   |         0.1246 |           0.1245 |     3.858e-05 |           0.4249 |             0.4249 |       3.026e-05 |                      7 |
|     2021 |     285 |                         52 |           31 |       0.7432 |            23.04 |            25 |            0.8065 |          0.06328  |         0.1602 |           0.1601 |     0.0001121 |           0.5027 |             0.5025 |       0.0002604 |                      7 |
|     2022 |     284 |                         57 |           41 |       0.7533 |            30.89 |            26 |            0.6341 |         -0.1192   |         0.2435 |           0.2462 |    -0.002712  |           0.6845 |             0.6917 |      -0.007233  |                      5 |
|     2023 |     285 |                         67 |           54 |       0.7552 |            40.78 |            40 |            0.7407 |         -0.01451  |         0.1911 |           0.1923 |    -0.001196  |           0.5693 |             0.5728 |      -0.003543  |                      2 |

### 2018-2023 aggregate (validation block)

| metric                          |      value |
|:--------------------------------|-----------:|
| qualifying primary legs         | 211        |
| mean P_est                      |   0.7496   |
| predicted wins = sum(P_est)     | 158.2      |
| actual wins                     | 155        |
| actual - predicted              |  -3.169    |
| actual hit rate                 |   0.7346   |
| calibration gap                 |  -0.01502  |
| Brier (frozen)                  |   0.1949   |
| Brier (constant mean P_est)     |   0.1952   |
| delta Brier (frozen - constant) |  -0.000252 |

## 2. Weekly qualifying-leg distribution, including zeros

|   season |   weeks |   0 |   1 |   2 |   3 |   >=4 |
|---------:|--------:|----:|----:|----:|----:|------:|
|     2018 |      21 |   5 |   5 |   5 |   3 |     3 |
|     2019 |      21 |   9 |   4 |   5 |   3 |     0 |
|     2020 |      21 |   7 |   8 |   1 |   5 |     0 |
|     2021 |      22 |   7 |   5 |   6 |   2 |     2 |
|     2022 |      22 |   5 |   3 |   6 |   6 |     2 |
|     2023 |      22 |   2 |   5 |   4 |   6 |     5 |

## 3. Geometry results (H1, by exact shape)

### 2018

| shape   | geometry     |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:--------|:-------------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| +1.5    | +1.5 -> +7.5 |   5 |       0.7431 |            0.8    |           0.05687 |     0.2836 |      0.9949 | True         |
| +2.5    | +2.5 -> +8.5 |  17 |       0.7482 |            0.7059 |          -0.04228 |     0.4404 |      0.8969 | True         |
| -7.5    | -7.5 -> -1.5 |  12 |       0.7528 |            0.5    |          -0.2528  |     0.2109 |      0.7891 | True         |
| -8.5    | -8.5 -> -2.5 |   3 |       0.7466 |            1      |           0.2534  |     0.2924 |      1      | True         |

### 2019

| shape   | geometry     |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:--------|:-------------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| +1.5    | +1.5 -> +7.5 |   4 |       0.7552 |            1      |           0.2448  |    0.3976  |      1      | True         |
| +2.5    | +2.5 -> +8.5 |  13 |       0.748  |            0.7692 |           0.02122 |    0.4619  |      0.9496 | True         |
| -7.5    | -7.5 -> -1.5 |   5 |       0.74   |            0.4    |          -0.34    |    0.05274 |      0.8534 | True         |
| -8.5    | -8.5 -> -2.5 |   1 |       0.7491 |            1      |           0.2509  |    0.025   |      1      | True         |

### 2020

| shape   | geometry     |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:--------|:-------------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| +1.5    | +1.5 -> +7.5 |   3 |       0.7471 |            1      |           0.2529  |     0.2924 |      1      | True         |
| +2.5    | +2.5 -> +8.5 |   8 |       0.7417 |            1      |           0.2583  |     0.6306 |      1      | True         |
| -7.5    | -7.5 -> -1.5 |  11 |       0.743  |            0.8182 |           0.07518 |     0.4822 |      0.9772 | True         |
| -8.5    | -8.5 -> -2.5 |   3 |       0.7376 |            0.6667 |          -0.07093 |     0.0943 |      0.9916 | True         |

### 2021

| shape   | geometry     |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:--------|:-------------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| +1.5    | +1.5 -> +7.5 |   1 |       0.7381 |            1      |           0.2619  |     0.025  |      1      | True         |
| +2.5    | +2.5 -> +8.5 |  13 |       0.7446 |            0.7692 |           0.02465 |     0.4619 |      0.9496 | True         |
| -7.5    | -7.5 -> -1.5 |  12 |       0.7427 |            0.9167 |           0.1739  |     0.6152 |      0.9979 | True         |
| -8.5    | -8.5 -> -2.5 |   5 |       0.7416 |            0.6    |          -0.1416  |     0.1466 |      0.9473 | True         |

### 2022

| shape   | geometry     |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:--------|:-------------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| +1.5    | +1.5 -> +7.5 |   3 |       0.7629 |            0.6667 |          -0.09619 |     0.0943 |      0.9916 | True         |
| +2.5    | +2.5 -> +8.5 |  24 |       0.7535 |            0.625  |          -0.1285  |     0.4059 |      0.812  | False        |
| -7.5    | -7.5 -> -1.5 |   9 |       0.7486 |            0.5556 |          -0.193   |     0.212  |      0.863  | True         |
| -8.5    | -8.5 -> -2.5 |   5 |       0.7552 |            0.8    |           0.04481 |     0.2836 |      0.9949 | True         |

### 2023

| shape   | geometry     |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:--------|:-------------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| +1.5    | +1.5 -> +7.5 |  10 |       0.7521 |            0.6    |          -0.1521  |    0.2624  |      0.8784 | True         |
| +2.5    | +2.5 -> +8.5 |  31 |       0.7575 |            0.8387 |           0.08124 |    0.6627  |      0.9455 | False        |
| -7.5    | -7.5 -> -1.5 |  11 |       0.7525 |            0.6364 |          -0.1162  |    0.3079  |      0.8907 | True         |
| -8.5    | -8.5 -> -2.5 |   2 |       0.7515 |            0.5    |          -0.2515  |    0.01258 |      0.9874 | True         |

### 2018-2023 aggregate

| shape   | geometry     |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:--------|:-------------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| +1.5    | +1.5 -> +7.5 |  26 |       0.751  |            0.7692 |          0.01824  |     0.5635 |      0.9103 | False        |
| +2.5    | +2.5 -> +8.5 | 106 |       0.7511 |            0.7642 |          0.01301  |     0.6718 |      0.8412 | False        |
| -7.5    | -7.5 -> -1.5 |  60 |       0.7472 |            0.6667 |         -0.08057  |     0.5331 |      0.7831 | False        |
| -8.5    | -8.5 -> -2.5 |  19 |       0.7468 |            0.7368 |         -0.009919 |     0.488  |      0.9085 | True         |

Rows with N < 20 are marked `low_sample` and reported as-is.

## 4. H3 — does total-driven P_est variation add predictive information?

Comparator **B** is a constant forecast equal to that season's mean frozen P_est. It is derived from model inputs only: no realized outcome enters it. A negative delta means the frozen per-leg variation helped; a positive delta means the constant did better.

|   season |   qualifying |   brier_frozen |   brier_constant |   delta_brier |   logloss_frozen |   logloss_constant |   delta_logloss |
|---------:|-------------:|---------------:|-----------------:|--------------:|-----------------:|-------------------:|----------------:|
|     2018 |           37 |         0.2259 |           0.2245 |     0.001375  |           0.6475 |             0.6435 |       0.003912  |
|     2019 |           23 |         0.191  |           0.1929 |    -0.001847  |           0.5691 |             0.5742 |      -0.00503   |
|     2020 |           25 |         0.1246 |           0.1245 |     3.858e-05 |           0.4249 |             0.4249 |       3.026e-05 |
|     2021 |           31 |         0.1602 |           0.1601 |     0.0001121 |           0.5027 |             0.5025 |       0.0002604 |
|     2022 |           41 |         0.2435 |           0.2462 |    -0.002712  |           0.6845 |             0.6917 |      -0.007233  |
|     2023 |           54 |         0.1911 |           0.1923 |    -0.001196  |           0.5693 |             0.5728 |      -0.003543  |

| block               |   n |   constant_p |   brier_frozen |   brier_constant |   delta_brier |   logloss_frozen |   logloss_constant |   delta_logloss |   p_est_variance |
|:--------------------|----:|-------------:|---------------:|-----------------:|--------------:|-----------------:|-------------------:|----------------:|-----------------:|
| 2018-2023 aggregate | 211 |       0.7496 |         0.1949 |           0.1952 |     -0.000252 |           0.5785 |             0.5792 |      -0.0007522 |         0.000177 |

See `reports/phase2b_total_dependence.md` for the bucket-level ordering check that accompanies this. **This is a diagnostic of the total-based variation. It is not permission to alter sigma.**

## 5. Ticket construction (descriptive only)

> Ticket rows are **correlated and overlapping**: within a week the same legs recur across combinations, and no historical teaser price exists. These are not independent observations and are not a track record.

| block               | ticket_size   |   n_tickets |   mean_product_p_est |   realized_hit_rate |      gap |   ci95_low |   ci95_high |   same_game_tickets |
|:--------------------|:--------------|------------:|---------------------:|--------------------:|---------:|-----------:|------------:|--------------------:|
| 2018                | 2-team        |          32 |               0.5624 |              0.5938 |  0.03133 |   0.4064   |      0.763  |                   0 |
| 2018                | 3-team        |          15 |               0.4246 |              0.6667 |  0.242   |   0.3838   |      0.8818 |                   0 |
| 2019                | 2-team        |          14 |               0.5581 |              0.5    | -0.0581  |   0.2304   |      0.7696 |                   0 |
| 2019                | 3-team        |           3 |               0.4163 |              0.3333 | -0.08298 |   0.008404 |      0.9057 |                   0 |
| 2020                | 2-team        |          16 |               0.5496 |              0.9375 |  0.3879  |   0.6977   |      0.9984 |                   0 |
| 2020                | 3-team        |           5 |               0.4071 |              1      |  0.5929  |   0.4782   |      1      |                   0 |
| 2021                | 2-team        |          24 |               0.5536 |              0.6667 |  0.113   |   0.4468   |      0.8437 |                   0 |
| 2021                | 3-team        |          10 |               0.4114 |              0.6    |  0.1886  |   0.2624   |      0.8784 |                   0 |
| 2022                | 2-team        |          36 |               0.5696 |              0.5833 |  0.01371 |   0.4076   |      0.7449 |                   0 |
| 2022                | 3-team        |          14 |               0.4314 |              0.7143 |  0.2828  |   0.419    |      0.9161 |                   0 |
| 2023                | 2-team        |          52 |               0.574  |              0.5    | -0.07403 |   0.3581   |      0.6419 |                   0 |
| 2023                | 3-team        |          26 |               0.4356 |              0.3462 | -0.08942 |   0.1721   |      0.5567 |                   0 |
| 2018-2023 aggregate | 2-team        |         174 |               0.5646 |              0.5977 |  0.03306 |   0.5208   |      0.6712 |                   0 |
| 2018-2023 aggregate | 3-team        |          73 |               0.4265 |              0.5616 |  0.1352  |   0.4405   |      0.6776 |                   0 |

Tickets combining two legs from the same NFL game: **0** — structurally impossible under the frozen geometry, since the primary set contains no complementary pair.

### Leg-level control for the ticket gap

The ticket gaps above cannot be read on their own. If the legs that went onto tickets simply out-performed, tickets would beat the product for that reason alone. Controlling for it:

| leg set                              |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |
|:-------------------------------------|----:|-------------:|------------------:|------------------:|
| all qualifying primary legs          | 211 |       0.7496 |            0.7346 |          -0.01502 |
| only the legs that appear on tickets | 177 |       0.7505 |            0.7288 |          -0.02167 |

The legs used on tickets hit **below** their own mean P_est, yet the tickets built from them beat the product of those same P_est values. Those two facts together are the signature of **positive correlation between legs within a week**: outcomes cluster, so all-win weeks occur more often than independence implies even when the per-leg rate is unremarkable.

This is recorded as a diagnostic for later EV work, exactly as the Phase 2 independence check was. **No model change follows from it**, and the ticket numbers remain correlated, overlapping and unpriced.

## 6. Three-block comparison

Blocks are never silently pooled. The all-years row is supplementary and spans source regimes.

| block                                          |   n |   mean_p_est |   predicted_wins |   actual_wins |   actual_hit_rate |   calibration_gap |   brier_frozen |   delta_brier |
|:-----------------------------------------------|----:|-------------:|-----------------:|--------------:|------------------:|------------------:|---------------:|--------------:|
| 1. 2018-2023 validation                        | 211 |       0.7496 |           158.2  |           155 |            0.7346 |         -0.01502  |         0.1949 |    -0.000252  |
| 2. 2024 initial test                           |  41 |       0.7518 |            30.82 |            31 |            0.7561 |          0.004309 |         0.1839 |    -0.0005477 |
| 3. 2025 changed-feed regime                    |  63 |       0.7513 |            47.33 |            49 |            0.7778 |          0.02649  |         0.1754 |     0.001841  |
| SUPPLEMENTARY all years (spans source regimes) | 315 |       0.7502 |           236.3  |           235 |            0.746  |         -0.004202 |         0.1896 |     0.000102  |

> The final row is **supplementary and descriptive**. It mixes three regimes and is not the conclusion of this phase.

## Machine-readable outputs

- `data/processed/phase2b_legs_qualifying_2018_2023.csv` — validation-block legs
- `data/processed/phase2b_legs_qualifying_<season>.csv` — per season
- `data/processed/phase2b_tickets_2018_2023.csv` — validation-block tickets
- `data/processed/phase2b_tickets_<season>.csv`, `phase2b_weekly_<season>.csv`, `phase2b_top_legs_<season>.csv`

