# Phase 2B — total dependence and P_est monotonicity (H3)

**Frozen Teaser Model v1.0 is unchanged by this phase. Nothing below is a recommendation to alter it.**

Within qualifying primary legs the frozen P_est varies only over a narrow range: every primary leg receives the same +0.07 NFL bump and the total is capped at 47, so all remaining variation comes from `sigma = 0.30 x total`. This report asks whether that variation carries information. **It is a diagnostic, not permission to alter sigma.**

- Lines are **archived reference lines** (`archived_reference_line`). The source documents no capture time. They are **not** closing lines and support no CLV claim.
- No historical teaser menu prices exist in this source and none have been invented. No EV, break-even, payout or ROI figure appears in this phase.
- **Three source regimes.** 2018-2023 and 2024 sit on the pre-2025 line feed; 2025 sits on a different feed. Blocks are never silently pooled; see `reports/nfl_line_composition_investigation.md`.

Buckets are the frozen Phase 2 buckets, unchanged: `<=40`, `40.5-43`, `43.5-45`, `45.5-47`. None was redesigned after seeing results. The frozen model predicts hit rates should **fall** as the total rises.

## 1. 2018-2023 aggregate (validation block)

| bucket   |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:---------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| <=40     |  39 |       0.7715 |            0.7692 |         -0.002227 |     0.6067 |      0.8887 | False        |
| 40.5-43  |  59 |       0.7531 |            0.7288 |         -0.02431  |     0.5973 |      0.8364 | False        |
| 43.5-45  |  47 |       0.7442 |            0.7021 |         -0.04208  |     0.5511 |      0.8266 | False        |
| 45.5-47  |  66 |       0.7374 |            0.7424 |          0.004988 |     0.6199 |      0.8422 | False        |

**Monotonicity: Realized hit rates are NOT monotone in the predicted direction: 2/3 adjacent pairs ordered as predicted. Inversions at: 43.5-45 -> 45.5-47.**

Spearman rank correlation between bucket mean P_est and realized hit rate: rho = 0.400 (p = 0.600), across 4 buckets. Reported as a descriptive rank statistic; **no trend is fitted**, and with four points it carries very little weight.

## 2. Each validation season separately

### 2018

| bucket   |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:---------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| <=40     |   6 |       0.7666 |            0.5    |          -0.2666  |     0.1181 |      0.8819 | True         |
| 40.5-43  |  10 |       0.7537 |            0.8    |           0.04628 |     0.4439 |      0.9748 | True         |
| 43.5-45  |  13 |       0.7443 |            0.7692 |           0.02493 |     0.4619 |      0.9496 | True         |
| 45.5-47  |   8 |       0.7369 |            0.5    |          -0.2369  |     0.157  |      0.843  | True         |

Monotonicity: Realized hit rates are NOT monotone in the predicted direction: 2/3 adjacent pairs ordered as predicted. Inversions at: <=40 -> 40.5-43.

### 2019

| bucket   |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:---------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| <=40     |   3 |       0.7739 |            1      |           0.2261  |    0.2924  |      1      | True         |
| 40.5-43  |   7 |       0.7514 |            0.7143 |          -0.03708 |    0.2904  |      0.9633 | True         |
| 43.5-45  |   4 |       0.7453 |            0.5    |          -0.2453  |    0.06759 |      0.9324 | True         |
| 45.5-47  |   9 |       0.7368 |            0.7778 |           0.04094 |    0.3999  |      0.9719 | True         |

Monotonicity: Realized hit rates are NOT monotone in the predicted direction: 2/3 adjacent pairs ordered as predicted. Inversions at: 43.5-45 -> 45.5-47.

### 2020

| bucket   |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:---------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| <=40     |   1 |       0.7615 |            1      |           0.2385  |     0.025  |      1      | True         |
| 40.5-43  |   5 |       0.7523 |            0.8    |           0.04774 |     0.2836 |      0.9949 | True         |
| 43.5-45  |   4 |       0.7439 |            1      |           0.2561  |     0.3976 |      1      | True         |
| 45.5-47  |  15 |       0.7375 |            0.8667 |           0.1292  |     0.5954 |      0.9834 | True         |

Monotonicity: Realized hit rates are NOT monotone in the predicted direction: 2/3 adjacent pairs ordered as predicted. Inversions at: 40.5-43 -> 43.5-45.

### 2021

| bucket   |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:---------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| <=40     |   0 |     nan      |          nan      |         nan       |   nan      |    nan      | True         |
| 40.5-43  |  10 |       0.7519 |            0.8    |           0.04813 |     0.4439 |      0.9748 | True         |
| 43.5-45  |   4 |       0.7449 |            0.75   |           0.00515 |     0.1941 |      0.9937 | True         |
| 45.5-47  |  17 |       0.7377 |            0.8235 |           0.08588 |     0.5657 |      0.962  | True         |

Monotonicity: Realized hit rates are NOT monotone in the predicted direction: 1/2 adjacent pairs ordered as predicted. Inversions at: 43.5-45 -> 45.5-47.

### 2022

| bucket   |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:---------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| <=40     |  14 |       0.7677 |            0.7857 |           0.01803 |    0.492   |      0.9534 | True         |
| 40.5-43  |  10 |       0.7531 |            0.6    |          -0.1531  |    0.2624  |      0.8784 | True         |
| 43.5-45  |  10 |       0.7438 |            0.6    |          -0.1438  |    0.2624  |      0.8784 | True         |
| 45.5-47  |   7 |       0.7384 |            0.4286 |          -0.3098  |    0.09899 |      0.8159 | True         |

Monotonicity: Realized hit rates are perfectly monotone in the predicted direction across 4 non-empty buckets (3/3 adjacent pairs ordered as predicted).

### 2023

| bucket   |   n |   mean_p_est |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high | low_sample   |
|:---------|----:|-------------:|------------------:|------------------:|-----------:|------------:|:-------------|
| <=40     |  15 |       0.7771 |            0.8    |           0.02289 |     0.5191 |      0.9567 | True         |
| 40.5-43  |  17 |       0.7545 |            0.7059 |          -0.04862 |     0.4404 |      0.8969 | True         |
| 43.5-45  |  12 |       0.7439 |            0.6667 |          -0.07727 |     0.3489 |      0.9008 | True         |
| 45.5-47  |  10 |       0.7373 |            0.8    |           0.06269 |     0.4439 |      0.9748 | True         |

Monotonicity: Realized hit rates are NOT monotone in the predicted direction: 2/3 adjacent pairs ordered as predicted. Inversions at: 43.5-45 -> 45.5-47.

## 3. Monotonicity summary across every block

| block               |   non_empty_buckets |   adjacent_pairs |   ordered_as_predicted | perfectly_monotone   |   spearman_rho |
|:--------------------|--------------------:|-----------------:|-----------------------:|:---------------------|---------------:|
| 2018                |                   4 |                3 |                      2 | False                |         0.1054 |
| 2019                |                   4 |                3 |                      2 | False                |         0.4    |
| 2020                |                   4 |                3 |                      2 | False                |         0.2108 |
| 2021                |                   3 |                2 |                      1 | False                |        -0.5    |
| 2022                |                   4 |                3 |                      3 | True                 |         0.9487 |
| 2023                |                   4 |                3 |                      2 | False                |         0.1054 |
| 2018-2023 aggregate |                   4 |                3 |                      2 | False                |         0.4    |
| 2024                |                   4 |                3 |                      2 | False                |         0.4    |
| 2025                |                   4 |                3 |                      2 | False                |        -0.6    |

## 4. Frozen P_est versus a constant forecast

The comparator is a constant equal to each block's mean frozen P_est — derived from **model inputs only**, never from realized outcomes. Negative delta means the frozen per-leg variation helped.

| block               |   n |   constant_p |   brier_frozen |   brier_constant |   delta_brier |   log_loss_frozen |   log_loss_constant |   delta_log_loss |   p_est_variance |
|:--------------------|----:|-------------:|---------------:|-----------------:|--------------:|------------------:|--------------------:|-----------------:|-----------------:|
| 2018                |  37 |       0.7489 |         0.2259 |           0.2245 |     0.001375  |            0.6475 |              0.6435 |        0.003912  |        0.0001091 |
| 2019                |  23 |       0.7476 |         0.191  |           0.1929 |    -0.001847  |            0.5691 |              0.5742 |       -0.00503   |        0.0001469 |
| 2020                |  25 |       0.7424 |         0.1246 |           0.1245 |     3.858e-05 |            0.4249 |              0.4249 |        3.026e-05 |        5.199e-05 |
| 2021                |  31 |       0.7432 |         0.1602 |           0.1601 |     0.0001121 |            0.5027 |              0.5025 |        0.0002604 |        4.623e-05 |
| 2022                |  41 |       0.7533 |         0.2435 |           0.2462 |    -0.002712  |            0.6845 |              0.6917 |       -0.007233  |        0.0001508 |
| 2023                |  54 |       0.7552 |         0.1911 |           0.1923 |    -0.001196  |            0.5693 |              0.5728 |       -0.003543  |        0.0002971 |
| 2018-2023 aggregate | 211 |       0.7496 |         0.1949 |           0.1952 |    -0.000252  |            0.5785 |              0.5792 |       -0.0007522 |        0.000177  |
| 2024                |  41 |       0.7518 |         0.1839 |           0.1844 |    -0.0005477 |            0.5542 |              0.5556 |       -0.00142   |        0.0001494 |
| 2025                |  63 |       0.7513 |         0.1754 |           0.1735 |     0.001841  |            0.5366 |              0.5316 |        0.004998  |        0.0001127 |

Mechanically, `delta Brier = var(P_est) - 2 x cov(P_est, outcome)`. With `var(P_est)` around 1.77e-04 in the validation block, the frozen variation can only beat the constant by a margin of that order. Whatever the sign, the magnitude is tiny by construction.

## 5. Limitations

- Bucket N is small in every season; per-season ordering is close to noise and is shown for completeness.
- Empty buckets are skipped in the ordering check, never imputed or merged.
- The P_est range is narrow **by construction**, so neither a positive nor a negative delta here can carry much weight. A null result is the expected outcome of a well-posed test at this sample size, not evidence that sigma is wrong.
- No trend is fitted and no parameter is estimated anywhere in this report.

