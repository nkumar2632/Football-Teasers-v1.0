# Phase 2 — NFL 2024 vs 2025 comparison

**Calibration only.** No price, no EV, no ROI.

- **2024 and 2025 run on different upstream line feeds.** Opportunity counts are not comparable across the two seasons, and differences in leg volume are a property of the data source, not of the model. See `reports/nfl_line_composition_investigation.md`.
- Lines are **archived reference lines** (`archived_reference_line`). The source documents no capture time; commit-history inspection shows the value is whatever a periodic scrape caught last before the final score landed. It is **not** a closing line and supports no CLV claim.
- No historical teaser menu prices exist in this source and none have been invented. No EV, break-even or ROI figure appears in this phase.

## A. Season summaries, side by side

| metric                           |    2024 |    2025 |
|:---------------------------------|--------:|--------:|
| games_in_source                  | 285     | 285     |
| legs_in_source                   | 570     | 570     |
| primary_legs_before_total_filter |  61     |  99     |
| qualifying_primary_legs          |  41     |  63     |
| dropped_by_guardrail             |  20     |  36     |
| weeks                            |  22     |  22     |
| zero_qualifier_weeks             |   5     |   3     |
| mean_qualifying_legs_per_week    |   1.864 |   2.864 |
| median_qualifying_legs_per_week  |   2     |   3     |
| max_qualifying_legs_in_a_week    |   8     |   7     |

> Do **not** read the difference in opportunity count as model performance. The 2025 feed places far more lines on ±1.5 and ±8.5 than the 2024 feed did, for reasons documented in the line-composition investigation.

## B. Shape-level calibration, by season

### 2024

| shape   | geometry     |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:--------|:-------------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| +1.5    | +1.5 -> +7.5 |   8 |       0.7454 |            0.75   |          0.004558 |     0.3491 |      0.9681 | True         |
| +2.5    | +2.5 -> +8.5 |  20 |       0.7545 |            0.85   |          0.09552  |     0.6211 |      0.9679 | False        |
| -7.5    | -7.5 -> -1.5 |  13 |       0.7516 |            0.6154 |         -0.1362   |     0.3158 |      0.8614 | True         |
| -8.5    | -8.5 -> -2.5 |   0 |     nan      |          nan      |        nan        |   nan      |    nan      | True         |

### 2025

| shape   | geometry     |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:--------|:-------------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| +1.5    | +1.5 -> +7.5 |  24 |       0.7508 |             0.875 |         0.1242    |     0.6764 |      0.9734 | False        |
| +2.5    | +2.5 -> +8.5 |  24 |       0.7493 |             0.75  |         0.0006522 |     0.5329 |      0.9023 | False        |
| -7.5    | -7.5 -> -1.5 |  10 |       0.758  |             0.7   |        -0.05796   |     0.3475 |      0.9333 | True         |
| -8.5    | -8.5 -> -2.5 |   5 |       0.7498 |             0.6   |        -0.1498    |     0.1466 |      0.9473 | True         |

### Supplementary: 2024+2025 pooled

> **Supplementary descriptive statistic only. Spans two source regimes.** This row is not the primary conclusion of Phase 2 and must not be quoted as though it were a single homogeneous sample.

| shape   | geometry     |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:--------|:-------------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| +1.5    | +1.5 -> +7.5 |  32 |       0.7494 |            0.8438 |           0.09433 |     0.6721 |      0.9472 | False        |
| +2.5    | +2.5 -> +8.5 |  44 |       0.7517 |            0.7955 |           0.04378 |     0.647  |      0.902  | False        |
| -7.5    | -7.5 -> -1.5 |  23 |       0.7543 |            0.6522 |          -0.1022  |     0.4273 |      0.8362 | False        |
| -8.5    | -8.5 -> -2.5 |   5 |       0.7498 |            0.6    |          -0.1498  |     0.1466 |      0.9473 | True         |

## C. Total-bucket calibration, by season

### 2024

| bucket   |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:---------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| <=40     |   9 |       0.7709 |            0.6667 |          -0.1042  |     0.2993 |      0.9251 | True         |
| 40.5-43  |  14 |       0.7534 |            0.9286 |           0.1752  |     0.6613 |      0.9982 | True         |
| 43.5-45  |  10 |       0.7444 |            0.7    |          -0.04437 |     0.3475 |      0.9333 | True         |
| 45.5-47  |   8 |       0.7369 |            0.625  |          -0.1119  |     0.2449 |      0.9148 | True         |

### 2025

| bucket   |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:---------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| <=40     |  10 |       0.77   |            0.7    |          -0.06996 |     0.3475 |      0.9333 | True         |
| 40.5-43  |  21 |       0.7549 |            0.6667 |          -0.08824 |     0.4303 |      0.8541 | False        |
| 43.5-45  |  20 |       0.7459 |            0.9    |           0.1541  |     0.683  |      0.9877 | False        |
| 45.5-47  |  12 |       0.7384 |            0.8333 |           0.09489 |     0.5159 |      0.9791 | True         |

## D. P_est-bucket calibration, by season

### 2024

| bucket   |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:---------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| <70%     |   0 |     nan      |          nan      |         nan       |   nan      |    nan      | True         |
| 70-71.9% |   0 |     nan      |          nan      |         nan       |   nan      |    nan      | True         |
| 72-73.9% |   8 |       0.7369 |            0.625  |          -0.1119  |     0.2449 |      0.9148 | True         |
| >=74%    |  33 |       0.7554 |            0.7879 |           0.03247 |     0.6109 |      0.9102 | False        |

### 2025

| bucket   |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:---------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| <70%     |   0 |     nan      |          nan      |         nan       |   nan      |    nan      | True         |
| 70-71.9% |   0 |     nan      |          nan      |         nan       |   nan      |    nan      | True         |
| 72-73.9% |  12 |       0.7384 |            0.8333 |           0.09489 |     0.5159 |      0.9791 | True         |
| >=74%    |  51 |       0.7543 |            0.7647 |           0.0104  |     0.6251 |      0.8721 | False        |

## E. Proper scoring, by season

| season             |   n |   expected_wins |   actual_wins |   actual_minus_expected |   mean_p_est |   actual_hit_rate |   brier_score |
|:-------------------|----:|----------------:|--------------:|------------------------:|-------------:|------------------:|--------------:|
| 2024               |  41 |           30.82 |            31 |                  0.1767 |       0.7518 |            0.7561 |        0.1839 |
| 2025               |  63 |           47.33 |            49 |                  1.669  |       0.7513 |            0.7778 |        0.1754 |
| pooled (2 regimes) | 104 |           78.15 |            80 |                  1.846  |       0.7515 |            0.7692 |        0.1787 |

**Calibration intercept/slope omitted for every cut, pooled included.** N = 104 is below the 500 needed for a stable logistic fit; p_est spans only 0.0542 (0.7348-0.7889), below the 0.10 needed to identify a slope.

The reason is structural, not incidental: every qualifying primary leg crosses both key numbers, so the bump is a constant and P_est is a monotone function of the game total alone. With the guardrail capping totals at 47, P_est occupies a narrow band. A logistic slope fitted across that band would be dominated by noise.

## F. Weekly qualifying-leg distribution, by season

| qualifying_legs_in_week   |   2024 |   2025 |
|:--------------------------|-------:|-------:|
| 0                         |      5 |      3 |
| 1                         |      5 |      4 |
| 2                         |      5 |      3 |
| 3                         |      6 |      4 |
| >=4                       |      1 |      8 |

## G. Ticket diagnostics, by season

> **Descriptive only**, for all the reasons in the season reports: no prices, correlated tickets within a week, repeated legs across combinations.

### 2024

| ticket_size   |   n_tickets |   mean_predicted_p_ticket |   realized_hit_rate |      gap |   ci95_low |   ci95_high |   same_game_tickets |
|:--------------|------------:|--------------------------:|--------------------:|---------:|-----------:|------------:|--------------------:|
| 2-team        |          29 |                    0.5674 |              0.5172 | -0.05017 |    0.3253  |      0.7055 |                   0 |
| 3-team        |          10 |                    0.4339 |              0.3    | -0.1339  |    0.06674 |      0.6525 |                   0 |

### 2025

| ticket_size   |   n_tickets |   mean_predicted_p_ticket |   realized_hit_rate |     gap |   ci95_low |   ci95_high |   same_game_tickets |
|:--------------|------------:|--------------------------:|--------------------:|--------:|-----------:|------------:|--------------------:|
| 2-team        |          63 |                     0.568 |              0.619  | 0.05106 |     0.488  |      0.7385 |                   0 |
| 3-team        |          36 |                     0.428 |              0.5278 | 0.09982 |     0.3549 |      0.6959 |                   0 |

### Supplementary: pooled tickets (two regimes)

| ticket_size   |   n_tickets |   mean_predicted_p_ticket |   realized_hit_rate |     gap |   ci95_low |   ci95_high |   same_game_tickets |
|:--------------|------------:|--------------------------:|--------------------:|--------:|-----------:|------------:|--------------------:|
| 2-team        |          92 |                    0.5678 |              0.587  | 0.01915 |     0.4795 |      0.6887 |                   0 |
| 3-team        |          46 |                    0.4292 |              0.4783 | 0.04902 |     0.3289 |      0.6305 |                   0 |

## H. Independence diagnostic

The frozen ticket formula multiplies leg P_est values, which assumes independence. Comparing the product against the realized rate:

|   season | ticket_size   |   n_tickets |   predicted (product of P_est) |   realized |      gap |   same_game_tickets |
|---------:|:--------------|------------:|-------------------------------:|-----------:|---------:|--------------------:|
|     2024 | 2-team        |          29 |                         0.5674 |     0.5172 | -0.05017 |                   0 |
|     2024 | 3-team        |          10 |                         0.4339 |     0.3    | -0.1339  |                   0 |
|     2025 | 2-team        |          63 |                         0.568  |     0.619  |  0.05106 |                   0 |
|     2025 | 3-team        |          36 |                         0.428  |     0.5278 |  0.09982 |                   0 |

**Tickets containing two legs from the same NFL game: 0.** This is a structural consequence of the frozen geometry, not luck: the primary set {+1.5, +2.5, −7.5, −8.5} contains no complementary pair, so if one side of a game is primary the other side cannot be. Independence is therefore not violated by same-game pairing in any week.

This diagnostic is recorded for later EV work. **No model change follows from it.** The v1.0 ticket formula stays as specified.

## Limitations and anomalies

1. **Sample size.** 2024: 41 qualifying primary legs, 2025: 63 qualifying primary legs (104 across both). At these counts a shape-level hit rate has a confidence interval tens of percentage points wide, which is why every table carries an exact interval. Individual shape gaps are not distinguishable from noise.

2. **Two source regimes.** The seasons are not a homogeneous sample. Pooled rows are supplementary only.

3. **Thin shapes.** Reported as-is, never merged: 2024 +1.5: N=8; 2024 -7.5: N=13; 2024 -8.5: N=0; 2025 -7.5: N=10; 2025 -8.5: N=5. These carry essentially no calibration information on their own.

4. **Postseason weeks contribute almost nothing.** 2024: 0 qualifying legs across 4 postseason weeks; 2025: 3 qualifying legs across 4 postseason weeks. Playoff games rarely combine primary geometry with a total at or below 47, so the weekly distribution is effectively a regular-season distribution with structural zeros appended. This is a property of the frozen filters, not a data defect.

5. **P_est occupies a narrow band by construction.** Every qualifying primary leg crosses both key numbers, so the bump is a constant +0.07 and P_est is a monotone function of the total alone. Combined with the total ≤ 47 guardrail, observed P_est spans 0.7348-0.7889. Two of the four predeclared P_est buckets are therefore structurally unreachable for qualifying legs and are reported empty. No bucket was redesigned.

6. **Ticket rows are not independent observations.** Within a week the same legs recur across combinations, and no historical teaser price exists. Ticket hit rates are descriptive only.

7. **No market-quality measurement is possible from this source.** Lines carry no documented capture time, so CLV and line movement are out of reach. That track requires our own timestamped capture during 2026.

## What Phase 2 does not contain

No price, EV, break-even or ROI figure. No hypothetical-price sensitivity.
No CFB. No secondary NFL shapes. No fitted or recalibrated parameter.
No recommended model change. Teaser Model v1.0 is unchanged by this phase.

