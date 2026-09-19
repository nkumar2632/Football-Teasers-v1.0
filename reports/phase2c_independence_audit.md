# Phase 2C — independence audit of ticket probability

**Teaser Model v1.0 is unchanged by this audit.** `P_ticket` remains the product of leg `P_est` values. Nothing here fits a probability, applies a correlation correction, or proposes a new formula.

- No teaser prices exist in this source and none have been invented. No EV, ROI or payout figure appears anywhere in this phase.
- **Three source regimes.** 2018-2023 and 2024 sit on the pre-2025 archived line feed; 2025 sits on a different feed. Blocks are reported separately; the all-years row is supplementary. See `reports/nfl_line_composition_investigation.md`.
- Lines are archived reference lines with no documented capture time. They are not closing lines.

The question: can the Phase 2B ticket-level excess arise from (1) sampling variation, (2) overlapping ticket construction, (3) leg-level miscalibration — or does it require (4) genuine positive dependence among qualifying legs in the same NFL week?

> Tickets are **not independent observations**. Within a week they share legs, and shared legs are exactly the mechanism under test. Every interval below that concerns a ticket statistic is either a simulation interval over the whole board or a week-clustered bootstrap; no standard error treats tickets as independent draws.

## 1. The anomaly, reproduced

### Per season

|   block |   qualifying_legs |   mean_leg_p_est |   actual_leg_hit_rate |   leg_gap_pp |   n_2team |   mean_product_p_2team |   realized_2team |   gap_pp_2team |   n_3team |   mean_product_p_3team |   realized_3team |   gap_pp_3team |
|--------:|------------------:|-----------------:|----------------------:|-------------:|----------:|-----------------------:|-----------------:|---------------:|----------:|-----------------------:|-----------------:|---------------:|
|    2018 |                37 |           0.7489 |                0.6757 |      -7.318  |        32 |                 0.5624 |           0.5938 |          3.133 |        15 |                 0.4246 |           0.6667 |         24.2   |
|    2019 |                23 |           0.7476 |                0.7391 |      -0.8441 |        14 |                 0.5581 |           0.5    |         -5.81  |         3 |                 0.4163 |           0.3333 |         -8.298 |
|    2020 |                25 |           0.7424 |                0.88   |      13.76   |        16 |                 0.5496 |           0.9375 |         38.79  |         5 |                 0.4071 |           1      |         59.29  |
|    2021 |                31 |           0.7432 |                0.8065 |       6.328  |        24 |                 0.5536 |           0.6667 |         11.3   |        10 |                 0.4114 |           0.6    |         18.86  |
|    2022 |                41 |           0.7533 |                0.6341 |     -11.92   |        36 |                 0.5696 |           0.5833 |          1.371 |        14 |                 0.4314 |           0.7143 |         28.28  |
|    2023 |                54 |           0.7552 |                0.7407 |      -1.451  |        52 |                 0.574  |           0.5    |         -7.403 |        26 |                 0.4356 |           0.3462 |         -8.942 |
|    2024 |                41 |           0.7518 |                0.7561 |       0.4309 |        29 |                 0.5674 |           0.5172 |         -5.017 |        10 |                 0.4339 |           0.3    |        -13.39  |
|    2025 |                63 |           0.7513 |                0.7778 |       2.649  |        63 |                 0.568  |           0.619  |          5.106 |        36 |                 0.428  |           0.5278 |          9.982 |

### By block

| block                             |   qualifying_legs |   mean_leg_p_est |   actual_leg_hit_rate |   leg_gap_pp |   n_2team |   mean_product_p_2team |   realized_2team |   gap_pp_2team |   n_3team |   mean_product_p_3team |   realized_3team |   gap_pp_3team |
|:----------------------------------|------------------:|-----------------:|----------------------:|-------------:|----------:|-----------------------:|-----------------:|---------------:|----------:|-----------------------:|-----------------:|---------------:|
| 2018-2023 validation              |               211 |           0.7496 |                0.7346 |      -1.502  |       174 |                 0.5646 |           0.5977 |          3.306 |        73 |                 0.4265 |           0.5616 |         13.52  |
| 2024                              |                41 |           0.7518 |                0.7561 |       0.4309 |        29 |                 0.5674 |           0.5172 |         -5.017 |        10 |                 0.4339 |           0.3    |        -13.39  |
| 2025                              |                63 |           0.7513 |                0.7778 |       2.649  |        63 |                 0.568  |           0.619  |          5.106 |        36 |                 0.428  |           0.5278 |          9.982 |
| SUPPLEMENTARY 2018-2025 all years |               315 |           0.7502 |                0.746  |      -0.4202 |       266 |                 0.5657 |           0.594  |          2.825 |       119 |                 0.4275 |           0.5294 |         10.19  |

The pattern to explain: leg-level gaps are small and mostly negative, while ticket-level gaps — especially 3-team — are positive. If legs were independent, a negative leg gap could not produce a positive ticket gap.

## 2. Same-week residual dependence

For every qualifying leg, `residual = outcome - P_est`. For every unordered pair of qualifying legs in the same (season, week) and different games:

- `mean_resid_product` estimates the average within-week covariance of outcomes. Under independence its expectation is zero.
- `mean_pair_correlation` normalises each product by `sqrt(p_a(1-p_a) p_b(1-p_b))`, giving a correlation-scale average.
- The interval is a **week-clustered bootstrap** (10,000 resamples of weeks, not of pairs), because pairs inside a week are the object under test.

| block                             |   n_pairs |   n_weeks |   mean_resid_product |   boot_ci_low |   boot_ci_high |   mean_pair_correlation |   observed_joint_win_rate |   expected_joint_win_rate |   observed_minus_expected |
|:----------------------------------|----------:|----------:|---------------------:|--------------:|---------------:|------------------------:|--------------------------:|--------------------------:|--------------------------:|
| 2018                              |        36 |        11 |              0.0627  |     -0.02407  |       0.2045   |                 0.3371  |                    0.5833 |                    0.5625 |                   0.0208  |
| 2019                              |        14 |         8 |             -0.06405 |     -0.1314   |       0.007751 |                -0.3316  |                    0.5    |                    0.5581 |                  -0.0581  |
| 2020                              |        16 |         6 |              0.05138 |      0.003464 |       0.069    |                 0.267   |                    0.9375 |                    0.5496 |                   0.3879  |
| 2021                              |        24 |        10 |              0.01023 |     -0.06203  |       0.1009   |                 0.05159 |                    0.6667 |                    0.5536 |                   0.113   |
| 2022                              |        36 |        14 |              0.04227 |     -0.008789 |       0.09064  |                 0.231   |                    0.5833 |                    0.5696 |                   0.01371 |
| 2023                              |        65 |        15 |             -0.01479 |     -0.04041  |       0.01619  |                -0.08273 |                    0.5538 |                    0.571  |                  -0.01715 |
| 2024                              |        51 |        12 |             -0.03939 |     -0.09487  |      -0.0113   |                -0.2113  |                    0.5294 |                    0.5691 |                  -0.03967 |
| 2025                              |       104 |        15 |              0.04858 |      0.001244 |       0.1206   |                 0.2622  |                    0.5962 |                    0.5646 |                   0.03156 |
| 2018-2023 validation              |       191 |        64 |              0.01564 |     -0.01012  |       0.04586  |                 0.08348 |                    0.6073 |                    0.5642 |                   0.04311 |
| 2024                              |        51 |        12 |             -0.03939 |     -0.09487  |      -0.0113   |                -0.2113  |                    0.5294 |                    0.5691 |                  -0.03967 |
| 2025                              |       104 |        15 |              0.04858 |      0.001244 |       0.1206   |                 0.2622  |                    0.5962 |                    0.5646 |                   0.03156 |
| SUPPLEMENTARY 2018-2025 all years |       346 |        91 |              0.01743 |     -0.004373 |       0.044    |                 0.09375 |                    0.5925 |                    0.5651 |                   0.02743 |

All 346 same-week pairs are different-game pairs by construction: the primary set contains no complementary pair, so one game can never contribute two primary legs.

## 3. Week-level all-win analysis

For each week with at least two qualifying primary legs, the independence expectation that **all** of that week's qualifying legs win is `product(P_i)` over all of them — not just the top four.

### 2018-2023 validation

| block                | week_size     |   weeks |   expected_all_win_weeks |   actual_all_win_weeks |   actual_minus_expected |
|:---------------------|:--------------|--------:|-------------------------:|-----------------------:|------------------------:|
| 2018-2023 validation | exactly 2     |      27 |                  15.09   |                      9 |                 -6.086  |
| 2018-2023 validation | exactly 3     |      25 |                  10.57   |                     13 |                  2.429  |
| 2018-2023 validation | exactly 4     |       9 |                   2.876  |                      6 |                  3.124  |
| 2018-2023 validation | >=5           |       3 |                   0.6746 |                      0 |                 -0.6746 |
| 2018-2023 validation | all weeks >=2 |      64 |                  29.21   |                     28 |                 -1.207  |

### 2024

|   block | week_size     |   weeks |   expected_all_win_weeks |   actual_all_win_weeks |   actual_minus_expected |
|--------:|:--------------|--------:|-------------------------:|-----------------------:|------------------------:|
|    2024 | exactly 2     |       5 |                   2.821  |                      2 |                 -0.8214 |
|    2024 | exactly 3     |       6 |                   2.515  |                      2 |                 -0.5146 |
|    2024 | exactly 4     |       0 |                   0      |                      0 |                  0      |
|    2024 | >=5           |       1 |                   0.1098 |                      0 |                 -0.1098 |
|    2024 | all weeks >=2 |      12 |                   5.446  |                      4 |                 -1.446  |

### 2025

|   block | week_size     |   weeks |   expected_all_win_weeks |   actual_all_win_weeks |   actual_minus_expected |
|--------:|:--------------|--------:|-------------------------:|-----------------------:|------------------------:|
|    2025 | exactly 2     |       3 |                   1.676  |                      2 |                 0.3238  |
|    2025 | exactly 3     |       4 |                   1.737  |                      3 |                 1.263   |
|    2025 | exactly 4     |       3 |                   0.9413 |                      3 |                 2.059   |
|    2025 | >=5           |       5 |                   0.9819 |                      1 |                 0.01806 |
|    2025 | all weeks >=2 |      15 |                   5.337  |                      9 |                 3.663   |

### SUPPLEMENTARY 2018-2025 all years

| block                             | week_size     |   weeks |   expected_all_win_weeks |   actual_all_win_weeks |   actual_minus_expected |
|:----------------------------------|:--------------|--------:|-------------------------:|-----------------------:|------------------------:|
| SUPPLEMENTARY 2018-2025 all years | exactly 2     |      35 |                   19.58  |                     13 |                 -6.583  |
| SUPPLEMENTARY 2018-2025 all years | exactly 3     |      35 |                   14.82  |                     18 |                  3.178  |
| SUPPLEMENTARY 2018-2025 all years | exactly 4     |      12 |                    3.817 |                      9 |                  5.183  |
| SUPPLEMENTARY 2018-2025 all years | >=5           |       9 |                    1.766 |                      1 |                 -0.7663 |
| SUPPLEMENTARY 2018-2025 all years | all weeks >=2 |      91 |                   39.99  |                     41 |                  1.011  |

### 3a. A benchmark that uses no P_est at all

The Monte Carlo null assumes `P_est` is calibrated. A benchmark free of that assumption: let `r` be the realized hit rate of the legs that actually appear on tickets. If those same wins were arranged independently across the board, a k-leg ticket would hit at `r^k`. Comparing the observed rate to `r^k` isolates **arrangement** from **calibration**.

| block                             | ticket_size   |   ticket_leg_hit_rate_r |   independence_benchmark_r_pow_k |   product_of_P_est |   observed |   observed_minus_r_pow_k_pp |
|:----------------------------------|:--------------|------------------------:|---------------------------------:|-------------------:|-----------:|----------------------------:|
| 2018-2023 validation              | 2-team        |                  0.7288 |                           0.5312 |             0.5646 |     0.5977 |                       6.653 |
| 2018-2023 validation              | 3-team        |                  0.7288 |                           0.3871 |             0.4265 |     0.5616 |                      17.45  |
| 2024                              | 2-team        |                  0.75   |                           0.5625 |             0.5674 |     0.5172 |                      -4.526 |
| 2024                              | 3-team        |                  0.75   |                           0.4219 |             0.4339 |     0.3    |                     -12.19  |
| 2025                              | 2-team        |                  0.74   |                           0.5476 |             0.568  |     0.619  |                       7.145 |
| 2025                              | 3-team        |                  0.74   |                           0.4052 |             0.428  |     0.5278 |                      12.26  |
| SUPPLEMENTARY 2018-2025 all years | 2-team        |                  0.7336 |                           0.5382 |             0.5657 |     0.594  |                       5.583 |
| SUPPLEMENTARY 2018-2025 all years | 3-team        |                  0.7336 |                           0.3948 |             0.4275 |     0.5294 |                      13.46  |

Note that `r` is *below* the mean `P_est` in most blocks: the legs that reach tickets did not out-perform. So the top-four selection cannot be what lifts the ticket rates. These `r^k` values are also, to three decimals, where the permutation distributions in `reports/phase2c_permutation.md` centre — which is the expected behaviour and a useful cross-check on that test.

### 3b. Where the excess sits, by week size

This matters for how much the ticket statistics can bear. A week with four qualifying legs contributes ten tickets; a week with two contributes one. The ticket-level statistics are therefore dominated by large weeks, while the all-win-week statistic counts every week once.

**2018-2023 validation**

|   week_size |   weeks |   expected_all_win_weeks |   actual_all_win_weeks |   n_2team |   rate_2team |   n_3team |   rate_3team |
|------------:|--------:|-------------------------:|-----------------------:|----------:|-------------:|----------:|-------------:|
|           2 |      27 |                  15.09   |                      9 |        27 |       0.3333 |         0 |     nan      |
|           3 |      25 |                  10.57   |                     13 |        75 |       0.6    |        25 |       0.52   |
|           4 |       9 |                   2.876  |                      6 |        54 |       0.7963 |        36 |       0.7222 |
|           5 |       2 |                   0.4949 |                      0 |        12 |       0.3333 |         8 |       0.125  |
|           6 |       1 |                   0.1796 |                      0 |         6 |       0.5    |         4 |       0.25   |

**2024**

|   week_size |   weeks |   expected_all_win_weeks |   actual_all_win_weeks |   n_2team |   rate_2team |   n_3team |   rate_3team |
|------------:|--------:|-------------------------:|-----------------------:|----------:|-------------:|----------:|-------------:|
|           2 |       5 |                   2.821  |                      2 |         5 |       0.4    |         0 |     nan      |
|           3 |       6 |                   2.515  |                      2 |        18 |       0.5556 |         6 |       0.3333 |
|           8 |       1 |                   0.1098 |                      0 |         6 |       0.5    |         4 |       0.25   |

**2025**

|   week_size |   weeks |   expected_all_win_weeks |   actual_all_win_weeks |   n_2team |   rate_2team |   n_3team |   rate_3team |
|------------:|--------:|-------------------------:|-----------------------:|----------:|-------------:|----------:|-------------:|
|           2 |       3 |                   1.676  |                      2 |         3 |      0.6667  |         0 |       nan    |
|           3 |       4 |                   1.737  |                      3 |        12 |      0.8333  |         4 |         0.75 |
|           4 |       3 |                   0.9413 |                      3 |        18 |      1       |        12 |         1    |
|           5 |       2 |                   0.4923 |                      0 |        12 |      0.08333 |         8 |         0    |
|           6 |       2 |                   0.3595 |                      1 |        12 |      0.5833  |         8 |         0.5  |
|           7 |       1 |                   0.1302 |                      0 |         6 |      0.1667  |         4 |         0    |

**SUPPLEMENTARY 2018-2025 all years**

|   week_size |   weeks |   expected_all_win_weeks |   actual_all_win_weeks |   n_2team |   rate_2team |   n_3team |   rate_3team |
|------------:|--------:|-------------------------:|-----------------------:|----------:|-------------:|----------:|-------------:|
|           2 |      35 |                  19.58   |                     13 |        35 |       0.3714 |         0 |     nan      |
|           3 |      35 |                  14.82   |                     18 |       105 |       0.619  |        35 |       0.5143 |
|           4 |      12 |                   3.817  |                      9 |        72 |       0.8472 |        48 |       0.7917 |
|           5 |       4 |                   0.9872 |                      0 |        24 |       0.2083 |        16 |       0.0625 |
|           6 |       3 |                   0.5391 |                      1 |        18 |       0.5556 |        12 |       0.4167 |
|           7 |       1 |                   0.1302 |                      0 |         6 |       0.1667 |         4 |       0      |
|           8 |       1 |                   0.1098 |                      0 |         6 |       0.5    |         4 |       0.25   |

## 4. Ticket overlap and effective sample size

The nominal ticket count overstates how much independent information the tickets carry, because each selected leg appears in several of them.

| block                             |   unique_qualifying_legs |   n_tickets_2team |   n_tickets_3team |   weeks_contributing_tickets |   legs_used_on_tickets |   mean_tickets_per_used_leg |   max_tickets_containing_one_leg |
|:----------------------------------|-------------------------:|------------------:|------------------:|-----------------------------:|-----------------------:|----------------------------:|---------------------------------:|
| 2018-2023 validation              |                      211 |               174 |                73 |                           64 |                    177 |                       3.203 |                                6 |
| 2024                              |                       41 |                29 |                10 |                           12 |                     32 |                       2.75  |                                6 |
| 2025                              |                       63 |                63 |                36 |                           15 |                     50 |                       4.68  |                                6 |
| SUPPLEMENTARY 2018-2025 all years |                      315 |               266 |               119 |                           91 |                    259 |                       3.432 |                                6 |

### Week-clustered bootstrap intervals for the ticket hit rates

Resampling unit is the **week**, with replacement, 10,000 draws. A naive interval treating each ticket as an independent observation would be narrower and wrong.

| block                             | ticket_size   |   n_tickets |   n_weeks |   observed_hit_rate |   boot_ci_low |   boot_ci_high |
|:----------------------------------|:--------------|------------:|----------:|--------------------:|--------------:|---------------:|
| 2018-2023 validation              | 2-team        |         174 |        64 |              0.5977 |        0.4815 |         0.7041 |
| 2018-2023 validation              | 3-team        |          73 |        37 |              0.5616 |        0.3836 |         0.7317 |
| 2024                              | 2-team        |          29 |        12 |              0.5172 |        0.3448 |         0.7083 |
| 2024                              | 3-team        |          10 |         7 |              0.3    |        0.1    |         0.5714 |
| 2025                              | 2-team        |          63 |        15 |              0.619  |        0.3788 |         0.8628 |
| 2025                              | 3-team        |          36 |        12 |              0.5278 |        0.2143 |         0.8485 |
| SUPPLEMENTARY 2018-2025 all years | 2-team        |         266 |        91 |              0.594  |        0.4983 |         0.6889 |
| SUPPLEMENTARY 2018-2025 all years | 3-team        |         119 |        56 |              0.5294 |        0.384  |         0.6788 |

## 5. Dog/favorite composition as a candidate explanation

Phase 2B found primary dogs out-hitting primary favorites. If successful weeks simply contained more dogs, that composition — not dependence — could produce the ticket excess. Weeks are binned by dog fraction; bins were fixed before the results were read.

### 2018-2023 validation

| bin         |   weeks |   legs |   mean_dog_fraction |   mean_week_hit_rate |   expected_all_win_weeks |   actual_all_win_weeks |   actual_minus_expected |
|:------------|--------:|-------:|--------------------:|---------------------:|-------------------------:|-----------------------:|------------------------:|
| <50% dogs   |      14 |     40 |              0.1893 |               0.6976 |                    6.235 |                      6 |                 -0.2346 |
| 50-99% dogs |      34 |    103 |              0.6069 |               0.7294 |                   14.81  |                     16 |                  1.194  |
| 100% dogs   |      16 |     38 |              1      |               0.6771 |                    8.166 |                      6 |                 -2.166  |

### 2024

| bin         |   weeks |   legs |   mean_dog_fraction |   mean_week_hit_rate |   expected_all_win_weeks |   actual_all_win_weeks |   actual_minus_expected |
|:------------|--------:|-------:|--------------------:|---------------------:|-------------------------:|-----------------------:|------------------------:|
| <50% dogs   |       2 |      5 |              0.1667 |                0.75  |                    1.001 |                      1 |               -0.001097 |
| 50-99% dogs |       7 |     24 |              0.631  |                0.631 |                    2.9   |                      0 |               -2.9      |
| 100% dogs   |       3 |      7 |              1      |                1     |                    1.545 |                      3 |                1.455    |

### 2025

| bin         |   weeks |   legs |   mean_dog_fraction |   mean_week_hit_rate |   expected_all_win_weeks |   actual_all_win_weeks |   actual_minus_expected |
|:------------|--------:|-------:|--------------------:|---------------------:|-------------------------:|-----------------------:|------------------------:|
| <50% dogs   |       2 |      5 |              0.1667 |               1      |                   0.9801 |                      2 |                   1.02  |
| 50-99% dogs |       7 |     37 |              0.7068 |               0.7116 |                   1.614  |                      3 |                   1.386 |
| 100% dogs   |       6 |     17 |              1      |               0.7778 |                   2.742  |                      4 |                   1.258 |

### SUPPLEMENTARY 2018-2025 all years

| bin         |   weeks |   legs |   mean_dog_fraction |   mean_week_hit_rate |   expected_all_win_weeks |   actual_all_win_weeks |   actual_minus_expected |
|:------------|--------:|-------:|--------------------:|---------------------:|-------------------------:|-----------------------:|------------------------:|
| <50% dogs   |      18 |     50 |              0.1843 |               0.737  |                    8.216 |                      9 |                  0.7842 |
| 50-99% dogs |      48 |    164 |              0.625  |               0.7125 |                   19.32  |                     19 |                 -0.3206 |
| 100% dogs   |      25 |     62 |              1      |               0.74   |                   12.45  |                     13 |                  0.5473 |

## 6. Evidence assessment

The four candidate explanations from the Phase 2C brief, against what the diagnostics actually show:

| block                             |   mean_resid_product | resid_ci_excludes_zero   |   mc_p_2team |   mc_p_3team |   permP1_p_2team |   permP1_p_3team |   permP2_p_3team |   allwin_perm_p |
|:----------------------------------|---------------------:|:-------------------------|-------------:|-------------:|-----------------:|-----------------:|-----------------:|----------------:|
| 2018-2023 validation              |              0.01564 | no                       |       0.2901 |      0.06808 |          0.01993 |          0.00513 |          0.00307 |         0.4531  |
| 2024                              |             -0.03939 | yes (-)                  |       0.6972 |      0.7994  |          0.8041  |          0.8503  |          0.8542  |         0.9683  |
| 2025                              |              0.04858 | yes (+)                  |       0.3302 |      0.2542  |          0.4197  |          0.2861  |          0.232   |         0.01159 |
| SUPPLEMENTARY 2018-2025 all years |              0.01743 | no                       |       0.2769 |      0.07623 |          0.05507 |          0.01319 |          0.00747 |         0.2493  |

### 1. Sampling variation — NOT excluded

The Monte Carlo null, which lets the board vary as a whole, does not reject independence in any block at conventional levels. The ticket-level excess sits inside its 95% simulation interval everywhere.

### 2. Overlapping ticket construction — EXCLUDED as the sole cause

Both the Monte Carlo and the permutation rebuild the identical fixed ticket set from resampled leg outcomes, so overlap is reproduced exactly in the null distribution. Overlap widens those distributions; it does not shift their centre. It therefore cannot by itself explain an observed value above the centre.

### 3. Leg-level miscalibration — EXCLUDED as the sole cause

The `r^k` benchmark in §3a uses no `P_est` at all, and the permutation test conditions on the realized win count. Both still show the 2018-2023 and 2025 excess. Moreover the legs that reach tickets hit *below* their mean `P_est`, so miscalibration runs against the observed direction, not with it.

### 4. Genuine positive within-week dependence — SUPPORTED, WEAKLY

Under the calibration-neutral permutation the 2018-2023 block shows an excess at p = 0.020 (2-team) and p = 0.005 (3-team), and 2025 shows an all-win-week excess at p = 0.012. The same-week residual product is positive in 2025 with a week-clustered interval excluding zero.

**But the evidence does not hang together, for four reasons:**

1. **The direction reverses by regime.** 2024 runs negative on every statistic, with a same-week residual product whose clustered interval excludes zero on the *negative* side. A common weekly shock does not switch sign between adjacent seasons.
2. **The statistics disagree within a regime.** In 2018-2023 the ticket statistics are significant while the overlap-free all-win-week count is not (28 observed against 27.2 permuted, p = 0.45). In 2025 the reverse holds: all-win weeks are significant while the ticket statistics are not.
3. **The signal is not uniform across week sizes, as a common shock would require.** In 2018-2023, weeks with exactly two qualifying legs went 9 of 27 all-win against 15.1 expected — a large deficit — while weeks with four legs went 6 of 9 against 2.9 expected. Positive dependence should lift both.
4. **Very few independent clusters carry the result.** The 2018-2023 ticket-level excess rests on nine four-leg weeks contributing 90 of that block's 247 tickets. The effective sample is weeks, not tickets, and the decisive weeks number single digits.

**Verdict: WEAK evidence for positive within-week dependence.** It is more than absent — two independent calibration-neutral tests reject the random-arrangement null in two of three regimes, and the two mechanical explanations (overlap, miscalibration) are ruled out as sole causes. It is less than moderate — the sign reverses across regimes, the overlap-free and ticket-weighted statistics contradict each other within regimes, the week-size pattern is inconsistent with a common shock, and a handful of week-clusters drives the result.

No operational consequence follows. This is recorded as a research diagnostic in `RESEARCH_QUEUE.md` R-08. The frozen ticket formula is unchanged.

## 7. Machine-readable outputs

- `data/processed/phase2c_week_diagnostics.csv` — one row per qualifying week, with per-week ticket counts, wins, dog composition and all-win indicator
- `data/processed/phase2c_same_week_pairs.csv` — every same-week leg pair
- `data/processed/phase2c_monte_carlo.csv`, `phase2c_permutation.csv` — every simulated statistic, each row carrying its seed, simulation count and (for the permutation) stratum counts and legs held fixed

See `reports/phase2c_monte_carlo.md` and `reports/phase2c_permutation.md`.

