# Phase 3 — hypothetical price sensitivity

**HYPOTHETICAL HISTORICAL SENSITIVITY** — assumes this teaser price was available for every qualifying historical ticket. **Actual historical teaser prices are unknown.** This is not a backtested sportsbook return and not a realized ROI.

**Frozen Teaser Model v1.0 is unchanged.** `P_ticket` is the product of leg `P_est` values, with no correlation adjustment: Phase 2C found only weak evidence against independence, which is not grounds for altering a frozen model.

- **Three source regimes.** 2018-2023 and 2024 sit on the pre-2025 archived line feed; 2025 sits on a different feed. The all-years row is supplementary only.
- Lines are archived reference lines with no documented capture time. They are not closing lines.

> Tickets share legs within a week. No interval anywhere in this phase treats tickets as independent observations; every reported interval is a week-cluster bootstrap.

The grid points below are **analytical only**. They are not described as historically common, historically available, or typical of any book. At each price the frozen procedure is reproduced exactly — top-four construction, break-even and EV from the frozen `P_ticket`, positive-EV filter, descending precise-EV greedy walk, 1 unit per ticket, 2-unit aggregate cap per leg — with only the price replaced by the hypothetical value.

Week-cluster bootstrap: 50,000 resamples, seed `20260919`. Intervals are refused where too few weeks carry a bet.

## 2-team only

### 2018-2023 validation — 2-team only

|   american_2team |   american_3team |   eligible_positive_ev_tickets |   tickets_selected |   betting_weeks |   zero_bet_weeks |   units_staked |   wins |   losses |   outcome_hit_rate |   hypothetical_profit_loss |   hypothetical_roi |   roi_ci_low |   roi_ci_high |
|-----------------:|-----------------:|-------------------------------:|-------------------:|----------------:|-----------------:|---------------:|-------:|---------:|-------------------:|---------------------------:|-------------------:|-------------:|--------------:|
|             -100 |              nan |                            174 |                138 |              64 |               30 |            138 |     77 |       61 |             0.558  |                    16      |            0.1159  |      -0.1159 |        0.3385 |
|             -110 |              nan |                            174 |                138 |              64 |               30 |            138 |     77 |       61 |             0.558  |                     9      |            0.06522 |      -0.1561 |        0.2776 |
|             -120 |              nan |                            158 |                124 |              61 |               33 |            124 |     66 |       58 |             0.5323 |                    -3      |           -0.02419 |      -0.2507 |        0.197  |
|             -130 |              nan |                             74 |                 63 |              30 |               64 |             63 |     38 |       25 |             0.6032 |                     4.231  |            0.06716 |      -0.2203 |        0.3342 |
|             -140 |              nan |                             21 |                 19 |              11 |               83 |             19 |     10 |        9 |             0.5263 |                    -1.857  |           -0.09774 |      -0.5714 |        0.3878 |
|             -150 |              nan |                              4 |                  4 |               3 |               91 |              4 |      2 |        2 |             0.5    |                    -0.6667 |           -0.1667  |     nan      |      nan      |

### 2024 — 2-team only

|   american_2team |   american_3team |   eligible_positive_ev_tickets |   tickets_selected |   betting_weeks |   zero_bet_weeks |   units_staked |   wins |   losses |   outcome_hit_rate |   hypothetical_profit_loss |   hypothetical_roi |   roi_ci_low |   roi_ci_high |
|-----------------:|-----------------:|-------------------------------:|-------------------:|----------------:|-----------------:|---------------:|-------:|---------:|-------------------:|---------------------------:|-------------------:|-------------:|--------------:|
|             -100 |              nan |                             29 |                 26 |              12 |                5 |             26 |     13 |       13 |             0.5    |                     0      |            0       |      -0.3846 |        0.4167 |
|             -110 |              nan |                             29 |                 26 |              12 |                5 |             26 |     13 |       13 |             0.5    |                    -1.182  |           -0.04545 |      -0.4126 |        0.3523 |
|             -120 |              nan |                             28 |                 25 |              12 |                5 |             25 |     12 |       13 |             0.48   |                    -3      |           -0.12    |      -0.5175 |        0.2901 |
|             -130 |              nan |                             11 |                  8 |               4 |               13 |              8 |      3 |        5 |             0.375  |                    -2.692  |           -0.3365  |     nan      |      nan      |
|             -140 |              nan |                              9 |                  7 |               3 |               14 |              7 |      2 |        5 |             0.2857 |                    -3.571  |           -0.5102  |     nan      |      nan      |
|             -150 |              nan |                              1 |                  1 |               1 |               16 |              1 |      1 |        0 |             1      |                     0.6667 |            0.6667  |     nan      |      nan      |

### 2025 — 2-team only

|   american_2team |   american_3team |   eligible_positive_ev_tickets |   tickets_selected |   betting_weeks |   zero_bet_weeks |   units_staked |   wins |   losses |   outcome_hit_rate |   hypothetical_profit_loss |   hypothetical_roi |   roi_ci_low |   roi_ci_high |
|-----------------:|-----------------:|-------------------------------:|-------------------:|----------------:|-----------------:|---------------:|-------:|---------:|-------------------:|---------------------------:|-------------------:|-------------:|--------------:|
|             -100 |              nan |                             63 |                 39 |              15 |                4 |             39 |     25 |       14 |              0.641 |                    11      |             0.2821 |      -0.2    |        0.7297 |
|             -110 |              nan |                             63 |                 39 |              15 |                4 |             39 |     25 |       14 |              0.641 |                     8.727  |             0.2238 |      -0.2364 |        0.6511 |
|             -120 |              nan |                             63 |                 39 |              15 |                4 |             39 |     25 |       14 |              0.641 |                     6.833  |             0.1752 |      -0.2667 |        0.5856 |
|             -130 |              nan |                             33 |                 25 |              11 |                8 |             25 |     13 |       12 |              0.52  |                    -2      |            -0.08   |      -0.5788 |        0.4615 |
|             -140 |              nan |                              7 |                  6 |               4 |               15 |              6 |      3 |        3 |              0.5   |                    -0.8571 |            -0.1429 |     nan      |      nan      |
|             -150 |              nan |                              2 |                  2 |               1 |               18 |              2 |      0 |        2 |              0     |                    -2      |            -1      |     nan      |      nan      |

### SUPPLEMENTARY 2018-2025 all years — 2-team only

|   american_2team |   american_3team |   eligible_positive_ev_tickets |   tickets_selected |   betting_weeks |   zero_bet_weeks |   units_staked |   wins |   losses |   outcome_hit_rate |   hypothetical_profit_loss |   hypothetical_roi |   roi_ci_low |   roi_ci_high |
|-----------------:|-----------------:|-------------------------------:|-------------------:|----------------:|-----------------:|---------------:|-------:|---------:|-------------------:|---------------------------:|-------------------:|-------------:|--------------:|
|             -100 |              nan |                            266 |                203 |              91 |               39 |            203 |    115 |       88 |             0.5665 |                    27      |           0.133    |     -0.05584 |        0.3175 |
|             -110 |              nan |                            266 |                203 |              91 |               39 |            203 |    115 |       88 |             0.5665 |                    16.55   |           0.0815   |     -0.09875 |        0.2576 |
|             -120 |              nan |                            249 |                188 |              88 |               42 |            188 |    103 |       85 |             0.5479 |                     0.8333 |           0.004433 |     -0.1755  |        0.1813 |
|             -130 |              nan |                            118 |                 96 |              45 |               85 |             96 |     54 |       42 |             0.5625 |                    -0.4615 |          -0.004808 |     -0.239   |        0.2291 |
|             -140 |              nan |                             37 |                 32 |              18 |              112 |             32 |     15 |       17 |             0.4688 |                    -6.286  |          -0.1964   |     -0.5023  |        0.1429 |
|             -150 |              nan |                              7 |                  7 |               5 |              125 |              7 |      3 |        4 |             0.4286 |                    -2      |          -0.2857   |    nan       |      nan      |

> **HYPOTHETICAL HISTORICAL SENSITIVITY** — assumes this teaser price was available for every qualifying historical ticket. **Actual historical teaser prices are unknown.** This is not a backtested sportsbook return and not a realized ROI.

## 3-team only

### 2018-2023 validation — 3-team only

|   american_2team |   american_3team |   eligible_positive_ev_tickets |   tickets_selected |   betting_weeks |   zero_bet_weeks |   units_staked |   wins |   losses |   outcome_hit_rate |   hypothetical_profit_loss |   hypothetical_roi |   roi_ci_low |   roi_ci_high |
|-----------------:|-----------------:|-------------------------------:|-------------------:|----------------:|-----------------:|---------------:|-------:|---------:|-------------------:|---------------------------:|-------------------:|-------------:|--------------:|
|              nan |              100 |                              0 |                  0 |               0 |               94 |              0 |      0 |        0 |           nan      |                        0   |           nan      |    nan       |      nan      |
|              nan |              110 |                              0 |                  0 |               0 |               94 |              0 |      0 |        0 |           nan      |                        0   |           nan      |    nan       |      nan      |
|              nan |              120 |                              2 |                  2 |               2 |               92 |              2 |      1 |        1 |             0.5    |                        0.2 |             0.1    |    nan       |      nan      |
|              nan |              130 |                             20 |                 16 |              11 |               83 |             16 |      6 |       10 |             0.375  |                       -2.2 |            -0.1375 |     -0.7125  |        0.5333 |
|              nan |              140 |                             53 |                 36 |              26 |               68 |             36 |     19 |       17 |             0.5278 |                        9.6 |             0.2667 |     -0.2     |        0.7333 |
|              nan |              150 |                             72 |                 48 |              36 |               58 |             48 |     25 |       23 |             0.5208 |                       14.5 |             0.3021 |     -0.1176  |        0.7188 |
|              nan |              160 |                             73 |                 49 |              37 |               57 |             49 |     26 |       23 |             0.5306 |                       18.6 |             0.3796 |     -0.05455 |        0.8041 |
|              nan |              170 |                             73 |                 49 |              37 |               57 |             49 |     26 |       23 |             0.5306 |                       21.2 |             0.4327 |     -0.01818 |        0.8735 |
|              nan |              180 |                             73 |                 49 |              37 |               57 |             49 |     26 |       23 |             0.5306 |                       23.8 |             0.4857 |      0.01818 |        0.9429 |

### 2024 — 3-team only

|   american_2team |   american_3team |   eligible_positive_ev_tickets |   tickets_selected |   betting_weeks |   zero_bet_weeks |   units_staked |   wins |   losses |   outcome_hit_rate |   hypothetical_profit_loss |   hypothetical_roi |   roi_ci_low |   roi_ci_high |
|-----------------:|-----------------:|-------------------------------:|-------------------:|----------------:|-----------------:|---------------:|-------:|---------:|-------------------:|---------------------------:|-------------------:|-------------:|--------------:|
|              nan |              100 |                              0 |                  0 |               0 |               17 |              0 |      0 |        0 |           nan      |                        0   |           nan      |          nan |           nan |
|              nan |              110 |                              0 |                  0 |               0 |               17 |              0 |      0 |        0 |           nan      |                        0   |           nan      |          nan |           nan |
|              nan |              120 |                              3 |                  3 |               2 |               15 |              3 |      1 |        2 |             0.3333 |                       -0.8 |            -0.2667 |          nan |           nan |
|              nan |              130 |                              5 |                  3 |               2 |               15 |              3 |      1 |        2 |             0.3333 |                       -0.7 |            -0.2333 |          nan |           nan |
|              nan |              140 |                              6 |                  4 |               3 |               14 |              4 |      2 |        2 |             0.5    |                        0.8 |             0.2    |          nan |           nan |
|              nan |              150 |                             10 |                  8 |               7 |               10 |              8 |      3 |        5 |             0.375  |                       -0.5 |            -0.0625 |          nan |           nan |
|              nan |              160 |                             10 |                  8 |               7 |               10 |              8 |      3 |        5 |             0.375  |                       -0.2 |            -0.025  |          nan |           nan |
|              nan |              170 |                             10 |                  8 |               7 |               10 |              8 |      3 |        5 |             0.375  |                        0.1 |             0.0125 |          nan |           nan |
|              nan |              180 |                             10 |                  8 |               7 |               10 |              8 |      3 |        5 |             0.375  |                        0.4 |             0.05   |          nan |           nan |

### 2025 — 3-team only

|   american_2team |   american_3team |   eligible_positive_ev_tickets |   tickets_selected |   betting_weeks |   zero_bet_weeks |   units_staked |   wins |   losses |   outcome_hit_rate |   hypothetical_profit_loss |   hypothetical_roi |   roi_ci_low |   roi_ci_high |
|-----------------:|-----------------:|-------------------------------:|-------------------:|----------------:|-----------------:|---------------:|-------:|---------:|-------------------:|---------------------------:|-------------------:|-------------:|--------------:|
|              nan |              100 |                              0 |                  0 |               0 |               19 |              0 |      0 |        0 |           nan      |                        0   |           nan      |     nan      |      nan      |
|              nan |              110 |                              0 |                  0 |               0 |               19 |              0 |      0 |        0 |           nan      |                        0   |           nan      |     nan      |      nan      |
|              nan |              120 |                              1 |                  1 |               1 |               18 |              1 |      0 |        1 |             0      |                       -1   |            -1      |     nan      |      nan      |
|              nan |              130 |                              7 |                  5 |               4 |               15 |              5 |      2 |        3 |             0.4    |                       -0.4 |            -0.08   |     nan      |      nan      |
|              nan |              140 |                             32 |                 19 |              12 |                7 |             19 |     10 |        9 |             0.5263 |                        5   |             0.2632 |      -0.4286 |        0.9765 |
|              nan |              150 |                             36 |                 20 |              12 |                7 |             20 |     11 |        9 |             0.55   |                        7.5 |             0.375  |      -0.3478 |        1.105  |
|              nan |              160 |                             36 |                 20 |              12 |                7 |             20 |     11 |        9 |             0.55   |                        8.6 |             0.43   |      -0.3217 |        1.189  |
|              nan |              170 |                             36 |                 20 |              12 |                7 |             20 |     11 |        9 |             0.55   |                        9.7 |             0.485  |      -0.2957 |        1.274  |
|              nan |              180 |                             36 |                 20 |              12 |                7 |             20 |     11 |        9 |             0.55   |                       10.8 |             0.54   |      -0.2696 |        1.358  |

### SUPPLEMENTARY 2018-2025 all years — 3-team only

|   american_2team |   american_3team |   eligible_positive_ev_tickets |   tickets_selected |   betting_weeks |   zero_bet_weeks |   units_staked |   wins |   losses |   outcome_hit_rate |   hypothetical_profit_loss |   hypothetical_roi |   roi_ci_low |   roi_ci_high |
|-----------------:|-----------------:|-------------------------------:|-------------------:|----------------:|-----------------:|---------------:|-------:|---------:|-------------------:|---------------------------:|-------------------:|-------------:|--------------:|
|              nan |              100 |                              0 |                  0 |               0 |              130 |              0 |      0 |        0 |           nan      |                        0   |           nan      |   nan        |      nan      |
|              nan |              110 |                              0 |                  0 |               0 |              130 |              0 |      0 |        0 |           nan      |                        0   |           nan      |   nan        |      nan      |
|              nan |              120 |                              6 |                  6 |               5 |              125 |              6 |      2 |        4 |             0.3333 |                       -1.6 |            -0.2667 |   nan        |      nan      |
|              nan |              130 |                             32 |                 24 |              17 |              113 |             24 |      9 |       15 |             0.375  |                       -3.3 |            -0.1375 |    -0.6      |        0.38   |
|              nan |              140 |                             91 |                 59 |              41 |               89 |             59 |     31 |       28 |             0.5254 |                       15.4 |             0.261  |    -0.1097   |        0.6271 |
|              nan |              150 |                            118 |                 76 |              55 |               75 |             76 |     39 |       37 |             0.5132 |                       21.5 |             0.2829 |    -0.05488  |        0.6197 |
|              nan |              160 |                            119 |                 77 |              56 |               74 |             77 |     40 |       37 |             0.5195 |                       27   |             0.3506 |     0.005333 |        0.7    |
|              nan |              170 |                            119 |                 77 |              56 |               74 |             77 |     40 |       37 |             0.5195 |                       31   |             0.4026 |     0.044    |        0.7654 |
|              nan |              180 |                            119 |                 77 |              56 |               74 |             77 |     40 |       37 |             0.5195 |                       35   |             0.4545 |     0.08267  |        0.8308 |

> **HYPOTHETICAL HISTORICAL SENSITIVITY** — assumes this teaser price was available for every qualifying historical ticket. **Actual historical teaser prices are unknown.** This is not a backtested sportsbook return and not a realized ROI.

## combined (paired)

Paired grid points: the 2-team and 3-team grids are zipped position by position. The full cross product is in the matrix below.

### 2018-2023 validation — combined (paired)

|   american_2team |   american_3team |   eligible_positive_ev_tickets |   tickets_selected |   betting_weeks |   zero_bet_weeks |   units_staked |   wins |   losses |   outcome_hit_rate |   hypothetical_profit_loss |   hypothetical_roi |   roi_ci_low |   roi_ci_high |
|-----------------:|-----------------:|-------------------------------:|-------------------:|----------------:|-----------------:|---------------:|-------:|---------:|-------------------:|---------------------------:|-------------------:|-------------:|--------------:|
|             -100 |              100 |                            174 |                138 |              64 |               30 |            138 |     77 |       61 |             0.558  |                     16     |            0.1159  |      -0.1159 |        0.3385 |
|             -110 |              110 |                            174 |                138 |              64 |               30 |            138 |     77 |       61 |             0.558  |                      9     |            0.06522 |      -0.1561 |        0.2776 |
|             -120 |              120 |                            160 |                124 |              61 |               33 |            124 |     66 |       58 |             0.5323 |                     -3     |           -0.02419 |      -0.2507 |        0.197  |
|             -130 |              130 |                             94 |                 61 |              30 |               64 |             61 |     37 |       24 |             0.6066 |                      4.992 |            0.08184 |      -0.2025 |        0.3483 |
|             -140 |              140 |                             74 |                 42 |              27 |               67 |             42 |     22 |       20 |             0.5238 |                      8.743 |            0.2082  |      -0.2352 |        0.6442 |
|             -150 |              150 |                             76 |                 50 |              36 |               58 |             50 |     26 |       24 |             0.52   |                     14.17  |            0.2833  |      -0.1327 |        0.6987 |

### 2024 — combined (paired)

|   american_2team |   american_3team |   eligible_positive_ev_tickets |   tickets_selected |   betting_weeks |   zero_bet_weeks |   units_staked |   wins |   losses |   outcome_hit_rate |   hypothetical_profit_loss |   hypothetical_roi |   roi_ci_low |   roi_ci_high |
|-----------------:|-----------------:|-------------------------------:|-------------------:|----------------:|-----------------:|---------------:|-------:|---------:|-------------------:|---------------------------:|-------------------:|-------------:|--------------:|
|             -100 |              100 |                             29 |                 26 |              12 |                5 |             26 |     13 |       13 |              0.5   |                     0      |            0       |      -0.3846 |        0.4167 |
|             -110 |              110 |                             29 |                 26 |              12 |                5 |             26 |     13 |       13 |              0.5   |                    -1.182  |           -0.04545 |      -0.4126 |        0.3523 |
|             -120 |              120 |                             31 |                 25 |              12 |                5 |             25 |     12 |       13 |              0.48  |                    -3      |           -0.12    |      -0.5175 |        0.2901 |
|             -130 |              130 |                             16 |                  8 |               4 |               13 |              8 |      3 |        5 |              0.375 |                    -2.692  |           -0.3365  |     nan      |      nan      |
|             -140 |              140 |                             15 |                  6 |               4 |               13 |              6 |      3 |        3 |              0.5   |                     0.5143 |            0.08571 |     nan      |      nan      |
|             -150 |              150 |                             11 |                  8 |               7 |               10 |              8 |      3 |        5 |              0.375 |                    -0.5    |           -0.0625  |     nan      |      nan      |

### 2025 — combined (paired)

|   american_2team |   american_3team |   eligible_positive_ev_tickets |   tickets_selected |   betting_weeks |   zero_bet_weeks |   units_staked |   wins |   losses |   outcome_hit_rate |   hypothetical_profit_loss |   hypothetical_roi |   roi_ci_low |   roi_ci_high |
|-----------------:|-----------------:|-------------------------------:|-------------------:|----------------:|-----------------:|---------------:|-------:|---------:|-------------------:|---------------------------:|-------------------:|-------------:|--------------:|
|             -100 |              100 |                             63 |                 39 |              15 |                4 |             39 |     25 |       14 |             0.641  |                     11     |            0.2821  |      -0.2    |        0.7297 |
|             -110 |              110 |                             63 |                 39 |              15 |                4 |             39 |     25 |       14 |             0.641  |                      8.727 |            0.2238  |      -0.2364 |        0.6511 |
|             -120 |              120 |                             64 |                 39 |              15 |                4 |             39 |     25 |       14 |             0.641  |                      6.833 |            0.1752  |      -0.2667 |        0.5856 |
|             -130 |              130 |                             40 |                 24 |              11 |                8 |             24 |     12 |       12 |             0.5    |                     -2.238 |           -0.09327 |      -0.5917 |        0.4828 |
|             -140 |              140 |                             39 |                 22 |              12 |                7 |             22 |     12 |       10 |             0.5455 |                      5.429 |            0.2468  |      -0.4078 |        0.8932 |
|             -150 |              150 |                             38 |                 20 |              12 |                7 |             20 |     11 |        9 |             0.55   |                      7.5   |            0.375   |      -0.3478 |        1.105  |

### SUPPLEMENTARY 2018-2025 all years — combined (paired)

|   american_2team |   american_3team |   eligible_positive_ev_tickets |   tickets_selected |   betting_weeks |   zero_bet_weeks |   units_staked |   wins |   losses |   outcome_hit_rate |   hypothetical_profit_loss |   hypothetical_roi |   roi_ci_low |   roi_ci_high |
|-----------------:|-----------------:|-------------------------------:|-------------------:|----------------:|-----------------:|---------------:|-------:|---------:|-------------------:|---------------------------:|-------------------:|-------------:|--------------:|
|             -100 |              100 |                            266 |                203 |              91 |               39 |            203 |    115 |       88 |             0.5665 |                   27       |          0.133     |     -0.05584 |        0.3175 |
|             -110 |              110 |                            266 |                203 |              91 |               39 |            203 |    115 |       88 |             0.5665 |                   16.55    |          0.0815    |     -0.09875 |        0.2576 |
|             -120 |              120 |                            255 |                188 |              88 |               42 |            188 |    103 |       85 |             0.5479 |                    0.8333  |          0.004433  |     -0.1755  |        0.1813 |
|             -130 |              130 |                            150 |                 93 |              45 |               85 |             93 |     52 |       41 |             0.5591 |                    0.06154 |          0.0006617 |     -0.2333  |        0.2365 |
|             -140 |              140 |                            128 |                 70 |              43 |               87 |             70 |     37 |       33 |             0.5286 |                   14.69    |          0.2098    |     -0.1304  |        0.5453 |
|             -150 |              150 |                            125 |                 78 |              55 |               75 |             78 |     40 |       38 |             0.5128 |                   21.17    |          0.2714    |     -0.06379 |        0.6042 |

> **HYPOTHETICAL HISTORICAL SENSITIVITY** — assumes this teaser price was available for every qualifying historical ticket. **Actual historical teaser prices are unknown.** This is not a backtested sportsbook return and not a realized ROI.

## Two-dimensional combined-price matrix

The greedy ranks every ticket by EV computed from **its own** offered hypothetical price, so a 3-team ticket can outrank a 2-team ticket or the reverse depending on the pair.

### 2018-2023 validation

|   american_2team |   american_3team |   tickets_selected |   n_2team |   n_3team |   units |   wins |   outcome_hit_rate |   hypothetical_pl |   hypothetical_roi |   roi_ci_low |   roi_ci_high |
|-----------------:|-----------------:|-------------------:|----------:|----------:|--------:|-------:|-------------------:|------------------:|-------------------:|-------------:|--------------:|
|             -110 |              120 |                138 |       138 |         0 |     138 |     77 |             0.558  |             9     |            0.06522 |     -0.1561  |        0.2776 |
|             -110 |              140 |                138 |       138 |         0 |     138 |     77 |             0.558  |             9     |            0.06522 |     -0.1561  |        0.2776 |
|             -110 |              160 |                113 |        64 |        49 |     113 |     58 |             0.5133 |            15.69  |            0.1389  |     -0.1458  |        0.4161 |
|             -110 |              180 |                113 |        64 |        49 |     113 |     58 |             0.5133 |            20.89  |            0.1849  |     -0.1147  |        0.4776 |
|             -120 |              120 |                124 |       124 |         0 |     124 |     66 |             0.5323 |            -3     |           -0.02419 |     -0.2507  |        0.197  |
|             -120 |              140 |                122 |       117 |         5 |     122 |     65 |             0.5328 |            -1.7   |           -0.01393 |     -0.2419  |        0.2098 |
|             -120 |              160 |                109 |        60 |        49 |     109 |     55 |             0.5046 |            11.77  |            0.108   |     -0.1812  |        0.392  |
|             -120 |              180 |                109 |        60 |        49 |     109 |     55 |             0.5046 |            16.97  |            0.1557  |     -0.1485  |        0.4542 |
|             -130 |              120 |                 63 |        63 |         0 |      63 |     38 |             0.6032 |             4.231 |            0.06716 |     -0.2203  |        0.3342 |
|             -130 |              140 |                 56 |        21 |        35 |      56 |     30 |             0.5357 |             9.062 |            0.1618  |     -0.2162  |        0.5341 |
|             -130 |              160 |                 69 |        20 |        49 |      69 |     36 |             0.5217 |            16.29  |            0.2361  |     -0.129   |        0.5993 |
|             -130 |              180 |                 69 |        20 |        49 |      69 |     36 |             0.5217 |            21.49  |            0.3115  |     -0.07767 |        0.6981 |
|             -140 |              120 |                 19 |        19 |         0 |      19 |     10 |             0.5263 |            -1.857 |           -0.09774 |     -0.5714  |        0.3878 |
|             -140 |              140 |                 42 |         6 |        36 |      42 |     22 |             0.5238 |             8.743 |            0.2082  |     -0.2352  |        0.6442 |
|             -140 |              160 |                 55 |         6 |        49 |      55 |     29 |             0.5273 |            17.74  |            0.3226  |     -0.08873 |        0.7319 |
|             -140 |              180 |                 55 |         6 |        49 |      55 |     29 |             0.5273 |            22.94  |            0.4171  |     -0.02556 |        0.8556 |

Hypothetical ROI, 2-team price (rows) against 3-team price (columns):

|   american_2team |     120 |     140 |    160 |    180 |
|-----------------:|--------:|--------:|-------:|-------:|
|             -140 | -0.0977 |  0.2082 | 0.3226 | 0.4171 |
|             -130 |  0.0672 |  0.1618 | 0.2361 | 0.3115 |
|             -120 | -0.0242 | -0.0139 | 0.1080 | 0.1557 |
|             -110 |  0.0652 |  0.0652 | 0.1389 | 0.1849 |

### 2024

|   american_2team |   american_3team |   tickets_selected |   n_2team |   n_3team |   units |   wins |   outcome_hit_rate |   hypothetical_pl |   hypothetical_roi |   roi_ci_low |   roi_ci_high |
|-----------------:|-----------------:|-------------------:|----------:|----------:|--------:|-------:|-------------------:|------------------:|-------------------:|-------------:|--------------:|
|             -110 |              120 |                 26 |        26 |         0 |      26 |     13 |             0.5    |          -1.182   |          -0.04545  |      -0.4126 |        0.3523 |
|             -110 |              140 |                 26 |        26 |         0 |      26 |     13 |             0.5    |          -1.182   |          -0.04545  |      -0.4126 |        0.3523 |
|             -110 |              160 |                 20 |        12 |         8 |      20 |      8 |             0.4    |          -2.655   |          -0.1327   |      -0.6445 |        0.4136 |
|             -110 |              180 |                 20 |        12 |         8 |      20 |      8 |             0.4    |          -2.055   |          -0.1027   |      -0.642  |        0.4636 |
|             -120 |              120 |                 25 |        25 |         0 |      25 |     12 |             0.48   |          -3       |          -0.12     |      -0.5175 |        0.2901 |
|             -120 |              140 |                 24 |        22 |         2 |      24 |     12 |             0.5    |          -2       |          -0.08333  |      -0.4907 |        0.3276 |
|             -120 |              160 |                 20 |        12 |         8 |      20 |      8 |             0.4    |          -3.033   |          -0.1517   |      -0.6562 |        0.3833 |
|             -120 |              180 |                 20 |        12 |         8 |      20 |      8 |             0.4    |          -2.433   |          -0.1217   |      -0.646  |        0.4333 |
|             -130 |              120 |                  8 |         8 |         0 |       8 |      3 |             0.375  |          -2.692   |          -0.3365   |     nan      |      nan      |
|             -130 |              140 |                  8 |         4 |         4 |       8 |      4 |             0.5    |           0.3385  |           0.04231  |     nan      |      nan      |
|             -130 |              160 |                 12 |         4 |         8 |      12 |      5 |             0.4167 |          -0.6615  |          -0.05513  |     nan      |      nan      |
|             -130 |              180 |                 12 |         4 |         8 |      12 |      5 |             0.4167 |          -0.06154 |          -0.005128 |     nan      |      nan      |
|             -140 |              120 |                  7 |         7 |         0 |       7 |      2 |             0.2857 |          -3.571   |          -0.5102   |     nan      |      nan      |
|             -140 |              140 |                  6 |         2 |         4 |       6 |      3 |             0.5    |           0.5143  |           0.08571  |     nan      |      nan      |
|             -140 |              160 |                 10 |         2 |         8 |      10 |      4 |             0.4    |          -0.4857  |          -0.04857  |     nan      |      nan      |
|             -140 |              180 |                 10 |         2 |         8 |      10 |      4 |             0.4    |           0.1143  |           0.01143  |     nan      |      nan      |

Hypothetical ROI, 2-team price (rows) against 3-team price (columns):

|   american_2team |     120 |     140 |     160 |     180 |
|-----------------:|--------:|--------:|--------:|--------:|
|             -140 | -0.5102 |  0.0857 | -0.0486 |  0.0114 |
|             -130 | -0.3365 |  0.0423 | -0.0551 | -0.0051 |
|             -120 | -0.1200 | -0.0833 | -0.1517 | -0.1217 |
|             -110 | -0.0455 | -0.0455 | -0.1327 | -0.1027 |

### 2025

|   american_2team |   american_3team |   tickets_selected |   n_2team |   n_3team |   units |   wins |   outcome_hit_rate |   hypothetical_pl |   hypothetical_roi |   roi_ci_low |   roi_ci_high |
|-----------------:|-----------------:|-------------------:|----------:|----------:|--------:|-------:|-------------------:|------------------:|-------------------:|-------------:|--------------:|
|             -110 |              120 |                 39 |        39 |         0 |      39 |     25 |             0.641  |            8.727  |             0.2238 |      -0.2364 |        0.6511 |
|             -110 |              140 |                 39 |        39 |         0 |      39 |     25 |             0.641  |            8.727  |             0.2238 |      -0.2364 |        0.6511 |
|             -110 |              160 |                 35 |        15 |        20 |      35 |     20 |             0.5714 |           10.78   |             0.3081 |      -0.3015 |        0.9172 |
|             -110 |              180 |                 35 |        15 |        20 |      35 |     20 |             0.5714 |           12.98   |             0.3709 |      -0.2727 |        1.012  |
|             -120 |              120 |                 39 |        39 |         0 |      39 |     25 |             0.641  |            6.833  |             0.1752 |      -0.2667 |        0.5856 |
|             -120 |              140 |                 38 |        37 |         1 |      38 |     24 |             0.6316 |            6.567  |             0.1728 |      -0.2713 |        0.6    |
|             -120 |              160 |                 35 |        15 |        20 |      35 |     20 |             0.5714 |           10.1    |             0.2886 |      -0.3143 |        0.8898 |
|             -120 |              180 |                 35 |        15 |        20 |      35 |     20 |             0.5714 |           12.3    |             0.3514 |      -0.2857 |        0.9843 |
|             -130 |              120 |                 25 |        25 |         0 |      25 |     13 |             0.52   |           -2      |            -0.08   |      -0.5788 |        0.4615 |
|             -130 |              140 |                 26 |         8 |        18 |      26 |     14 |             0.5385 |            4.446  |             0.171  |      -0.4225 |        0.8181 |
|             -130 |              160 |                 27 |         7 |        20 |      27 |     15 |             0.5556 |            8.677  |             0.3214 |      -0.3308 |        1.018  |
|             -130 |              180 |                 27 |         7 |        20 |      27 |     15 |             0.5556 |           10.88   |             0.4028 |      -0.2877 |        1.146  |
|             -140 |              120 |                  6 |         6 |         0 |       6 |      3 |             0.5    |           -0.8571 |            -0.1429 |     nan      |      nan      |
|             -140 |              140 |                 22 |         3 |        19 |      22 |     12 |             0.5455 |            5.429  |             0.2468 |      -0.4078 |        0.8932 |
|             -140 |              160 |                 23 |         3 |        20 |      23 |     13 |             0.5652 |            9.029  |             0.3925 |      -0.2909 |        1.071  |
|             -140 |              180 |                 23 |         3 |        20 |      23 |     13 |             0.5652 |           11.23   |             0.4882 |      -0.2476 |        1.219  |

Hypothetical ROI, 2-team price (rows) against 3-team price (columns):

|   american_2team |     120 |    140 |    160 |    180 |
|-----------------:|--------:|-------:|-------:|-------:|
|             -140 | -0.1429 | 0.2468 | 0.3925 | 0.4882 |
|             -130 | -0.0800 | 0.1710 | 0.3214 | 0.4028 |
|             -120 |  0.1752 | 0.1728 | 0.2886 | 0.3514 |
|             -110 |  0.2238 | 0.2238 | 0.3081 | 0.3709 |

### SUPPLEMENTARY 2018-2025 all years

|   american_2team |   american_3team |   tickets_selected |   n_2team |   n_3team |   units |   wins |   outcome_hit_rate |   hypothetical_pl |   hypothetical_roi |   roi_ci_low |   roi_ci_high |
|-----------------:|-----------------:|-------------------:|----------:|----------:|--------:|-------:|-------------------:|------------------:|-------------------:|-------------:|--------------:|
|             -110 |              120 |                203 |       203 |         0 |     203 |    115 |             0.5665 |           16.55   |           0.0815   |     -0.09875 |        0.2576 |
|             -110 |              140 |                203 |       203 |         0 |     203 |    115 |             0.5665 |           16.55   |           0.0815   |     -0.09875 |        0.2576 |
|             -110 |              160 |                168 |        91 |        77 |     168 |     86 |             0.5119 |           23.82   |           0.1418   |     -0.09575 |        0.3762 |
|             -110 |              180 |                168 |        91 |        77 |     168 |     86 |             0.5119 |           31.82   |           0.1894   |     -0.06146 |        0.436  |
|             -120 |              120 |                188 |       188 |         0 |     188 |    103 |             0.5479 |            0.8333 |           0.004433 |     -0.1755  |        0.1813 |
|             -120 |              140 |                184 |       176 |         8 |     184 |    101 |             0.5489 |            2.867  |           0.01558  |     -0.1659  |        0.1936 |
|             -120 |              160 |                164 |        87 |        77 |     164 |     83 |             0.5061 |           18.83   |           0.1148   |     -0.1266  |        0.3545 |
|             -120 |              180 |                164 |        87 |        77 |     164 |     83 |             0.5061 |           26.83   |           0.1636   |     -0.09082 |        0.4152 |
|             -130 |              120 |                 96 |        96 |         0 |      96 |     54 |             0.5625 |           -0.4615 |          -0.004808 |     -0.239   |        0.2291 |
|             -130 |              140 |                 90 |        33 |        57 |      90 |     48 |             0.5333 |           13.85   |           0.1538   |     -0.1401  |        0.4528 |
|             -130 |              160 |                108 |        31 |        77 |     108 |     56 |             0.5185 |           24.31   |           0.2251   |     -0.06585 |        0.5239 |
|             -130 |              180 |                108 |        31 |        77 |     108 |     56 |             0.5185 |           32.31   |           0.2991   |     -0.01119 |        0.6184 |
|             -140 |              120 |                 32 |        32 |         0 |      32 |     15 |             0.4688 |           -6.286  |          -0.1964   |     -0.5023  |        0.1429 |
|             -140 |              140 |                 70 |        11 |        59 |      70 |     37 |             0.5286 |           14.69   |           0.2098   |     -0.1304  |        0.5453 |
|             -140 |              160 |                 88 |        11 |        77 |      88 |     46 |             0.5227 |           26.29   |           0.2987   |     -0.02459 |        0.6216 |
|             -140 |              180 |                 88 |        11 |        77 |      88 |     46 |             0.5227 |           34.29   |           0.3896   |      0.04375 |        0.7359 |

Hypothetical ROI, 2-team price (rows) against 3-team price (columns):

|   american_2team |     120 |    140 |    160 |    180 |
|-----------------:|--------:|-------:|-------:|-------:|
|             -140 | -0.1964 | 0.2098 | 0.2987 | 0.3896 |
|             -130 | -0.0048 | 0.1538 | 0.2251 | 0.2991 |
|             -120 |  0.0044 | 0.0156 | 0.1148 | 0.1636 |
|             -110 |  0.0815 | 0.0815 | 0.1418 | 0.1894 |

> **HYPOTHETICAL HISTORICAL SENSITIVITY** — assumes this teaser price was available for every qualifying historical ticket. **Actual historical teaser prices are unknown.** This is not a backtested sportsbook return and not a realized ROI.

## Flat-eligibility control

Control: include **every** positive-EV ticket, with no EV ranking and no exposure cap. Its purpose is to show whether any apparent result comes materially from the exposure algorithm rather than from the underlying ticket set. **Neither procedure is optimized**, and the control is not a proposal.

### 2-team only

| block                             |   american_2team |   american_3team |   hypothetical_roi_flat |   hypothetical_roi_frozen |   tickets_selected_flat |   tickets_selected_frozen |
|:----------------------------------|-----------------:|-----------------:|------------------------:|--------------------------:|------------------------:|--------------------------:|
| 2018-2023 validation              |             -150 |              nan |                -0.1667  |                 -0.1667   |                       4 |                         4 |
| 2018-2023 validation              |             -140 |              nan |                -0.102   |                 -0.09774  |                      21 |                        19 |
| 2018-2023 validation              |             -130 |              nan |                 0.09979 |                  0.06716  |                      74 |                        63 |
| 2018-2023 validation              |             -120 |              nan |                 0.05591 |                 -0.02419  |                     158 |                       124 |
| 2018-2023 validation              |             -110 |              nan |                 0.1411  |                  0.06522  |                     174 |                       138 |
| 2018-2023 validation              |             -100 |              nan |                 0.1954  |                  0.1159   |                     174 |                       138 |
| 2024                              |             -150 |              nan |                 0.6667  |                  0.6667   |                       1 |                         1 |
| 2024                              |             -140 |              nan |                -0.2381  |                 -0.5102   |                       9 |                         7 |
| 2024                              |             -130 |              nan |                -0.1958  |                 -0.3365   |                      11 |                         8 |
| 2024                              |             -120 |              nan |                -0.08333 |                 -0.12     |                      28 |                        25 |
| 2024                              |             -110 |              nan |                -0.01254 |                 -0.04545  |                      29 |                        26 |
| 2024                              |             -100 |              nan |                 0.03448 |                  0        |                      29 |                        26 |
| 2025                              |             -150 |              nan |                -1       |                 -1        |                       2 |                         2 |
| 2025                              |             -140 |              nan |                -0.2653  |                 -0.1429   |                       7 |                         6 |
| 2025                              |             -130 |              nan |                -0.08858 |                 -0.08     |                      33 |                        25 |
| 2025                              |             -120 |              nan |                 0.1349  |                  0.1752   |                      63 |                        39 |
| 2025                              |             -110 |              nan |                 0.1818  |                  0.2238   |                      63 |                        39 |
| 2025                              |             -100 |              nan |                 0.2381  |                  0.2821   |                      63 |                        39 |
| SUPPLEMENTARY 2018-2025 all years |             -150 |              nan |                -0.2857  |                 -0.2857   |                       7 |                         7 |
| SUPPLEMENTARY 2018-2025 all years |             -140 |              nan |                -0.166   |                 -0.1964   |                      37 |                        32 |
| SUPPLEMENTARY 2018-2025 all years |             -130 |              nan |                 0.01956 |                 -0.004808 |                     118 |                        96 |
| SUPPLEMENTARY 2018-2025 all years |             -120 |              nan |                 0.06024 |                  0.004433 |                     249 |                       188 |
| SUPPLEMENTARY 2018-2025 all years |             -110 |              nan |                 0.134   |                  0.0815   |                     266 |                       203 |
| SUPPLEMENTARY 2018-2025 all years |             -100 |              nan |                 0.188   |                  0.133    |                     266 |                       203 |

### 3-team only

| block                             |   american_2team |   american_3team |   hypothetical_roi_flat |   hypothetical_roi_frozen |   tickets_selected_flat |   tickets_selected_frozen |
|:----------------------------------|-----------------:|-----------------:|------------------------:|--------------------------:|------------------------:|--------------------------:|
| 2018-2023 validation              |              nan |              100 |                nan      |                  nan      |                       0 |                         0 |
| 2018-2023 validation              |              nan |              110 |                nan      |                  nan      |                       0 |                         0 |
| 2018-2023 validation              |              nan |              120 |                  0.1    |                    0.1    |                       2 |                         2 |
| 2018-2023 validation              |              nan |              130 |                 -0.08   |                   -0.1375 |                      20 |                        16 |
| 2018-2023 validation              |              nan |              140 |                  0.2679 |                    0.2667 |                      53 |                        36 |
| 2018-2023 validation              |              nan |              150 |                  0.3889 |                    0.3021 |                      72 |                        48 |
| 2018-2023 validation              |              nan |              160 |                  0.4603 |                    0.3796 |                      73 |                        49 |
| 2018-2023 validation              |              nan |              170 |                  0.5164 |                    0.4327 |                      73 |                        49 |
| 2018-2023 validation              |              nan |              180 |                  0.5726 |                    0.4857 |                      73 |                        49 |
| 2024                              |              nan |              100 |                nan      |                  nan      |                       0 |                         0 |
| 2024                              |              nan |              110 |                nan      |                  nan      |                       0 |                         0 |
| 2024                              |              nan |              120 |                 -0.2667 |                   -0.2667 |                       3 |                         3 |
| 2024                              |              nan |              130 |                 -0.54   |                   -0.2333 |                       5 |                         3 |
| 2024                              |              nan |              140 |                 -0.2    |                    0.2    |                       6 |                         4 |
| 2024                              |              nan |              150 |                 -0.25   |                   -0.0625 |                      10 |                         8 |
| 2024                              |              nan |              160 |                 -0.22   |                   -0.025  |                      10 |                         8 |
| 2024                              |              nan |              170 |                 -0.19   |                    0.0125 |                      10 |                         8 |
| 2024                              |              nan |              180 |                 -0.16   |                    0.05   |                      10 |                         8 |
| 2025                              |              nan |              100 |                nan      |                  nan      |                       0 |                         0 |
| 2025                              |              nan |              110 |                nan      |                  nan      |                       0 |                         0 |
| 2025                              |              nan |              120 |                 -1      |                   -1      |                       1 |                         1 |
| 2025                              |              nan |              130 |                 -0.3429 |                   -0.08   |                       7 |                         5 |
| 2025                              |              nan |              140 |                  0.125  |                    0.2632 |                      32 |                        19 |
| 2025                              |              nan |              150 |                  0.3194 |                    0.375  |                      36 |                        20 |
| 2025                              |              nan |              160 |                  0.3722 |                    0.43   |                      36 |                        20 |
| 2025                              |              nan |              170 |                  0.425  |                    0.485  |                      36 |                        20 |
| 2025                              |              nan |              180 |                  0.4778 |                    0.54   |                      36 |                        20 |
| SUPPLEMENTARY 2018-2025 all years |              nan |              100 |                nan      |                  nan      |                       0 |                         0 |
| SUPPLEMENTARY 2018-2025 all years |              nan |              110 |                nan      |                  nan      |                       0 |                         0 |
| SUPPLEMENTARY 2018-2025 all years |              nan |              120 |                 -0.2667 |                   -0.2667 |                       6 |                         6 |
| SUPPLEMENTARY 2018-2025 all years |              nan |              130 |                 -0.2094 |                   -0.1375 |                      32 |                        24 |
| SUPPLEMENTARY 2018-2025 all years |              nan |              140 |                  0.1868 |                    0.261  |                      91 |                        59 |
| SUPPLEMENTARY 2018-2025 all years |              nan |              150 |                  0.3136 |                    0.2829 |                     118 |                        76 |
| SUPPLEMENTARY 2018-2025 all years |              nan |              160 |                  0.3765 |                    0.3506 |                     119 |                        77 |
| SUPPLEMENTARY 2018-2025 all years |              nan |              170 |                  0.4294 |                    0.4026 |                     119 |                        77 |
| SUPPLEMENTARY 2018-2025 all years |              nan |              180 |                  0.4824 |                    0.4545 |                     119 |                        77 |

### combined (paired)

| block                             |   american_2team |   american_3team |   hypothetical_roi_flat |   hypothetical_roi_frozen |   tickets_selected_flat |   tickets_selected_frozen |
|:----------------------------------|-----------------:|-----------------:|------------------------:|--------------------------:|------------------------:|--------------------------:|
| 2018-2023 validation              |             -150 |              100 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -150 |              110 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -150 |              120 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -150 |              130 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -150 |              140 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -150 |              150 |                 0.3596  |                 0.2833    |                      76 |                        50 |
| 2018-2023 validation              |             -140 |              100 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -140 |              110 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -140 |              120 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -140 |              130 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -140 |              140 |                 0.1629  |                 0.2082    |                      74 |                        42 |
| 2018-2023 validation              |             -140 |              150 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -130 |              100 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -130 |              110 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -130 |              120 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -130 |              130 |                 0.06154 |                 0.08184   |                      94 |                        61 |
| 2018-2023 validation              |             -130 |              140 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -130 |              150 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -120 |              100 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -120 |              110 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -120 |              120 |                 0.05646 |                -0.02419   |                     160 |                       124 |
| 2018-2023 validation              |             -120 |              130 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -120 |              140 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -120 |              150 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -110 |              100 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -110 |              110 |                 0.1411  |                 0.06522   |                     174 |                       138 |
| 2018-2023 validation              |             -110 |              120 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -110 |              130 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -110 |              140 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -110 |              150 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -100 |              100 |                 0.1954  |                 0.1159    |                     174 |                       138 |
| 2018-2023 validation              |             -100 |              110 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -100 |              120 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -100 |              130 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -100 |              140 |               nan       |               nan         |                     nan |                       nan |
| 2018-2023 validation              |             -100 |              150 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -150 |              100 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -150 |              110 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -150 |              120 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -150 |              130 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -150 |              140 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -150 |              150 |                -0.1667  |                -0.0625    |                      11 |                         8 |
| 2024                              |             -140 |              100 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -140 |              110 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -140 |              120 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -140 |              130 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -140 |              140 |                -0.2229  |                 0.08571   |                      15 |                         6 |
| 2024                              |             -140 |              150 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -130 |              100 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -130 |              110 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -130 |              120 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -130 |              130 |                -0.3034  |                -0.3365    |                      16 |                         8 |
| 2024                              |             -130 |              140 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -130 |              150 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -120 |              100 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -120 |              110 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -120 |              120 |                -0.1011  |                -0.12      |                      31 |                        25 |
| 2024                              |             -120 |              130 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -120 |              140 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -120 |              150 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -110 |              100 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -110 |              110 |                -0.01254 |                -0.04545   |                      29 |                        26 |
| 2024                              |             -110 |              120 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -110 |              130 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -110 |              140 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -110 |              150 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -100 |              100 |                 0.03448 |                 0         |                      29 |                        26 |
| 2024                              |             -100 |              110 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -100 |              120 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -100 |              130 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -100 |              140 |               nan       |               nan         |                     nan |                       nan |
| 2024                              |             -100 |              150 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -150 |              100 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -150 |              110 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -150 |              120 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -150 |              130 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -150 |              140 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -150 |              150 |                 0.25    |                 0.375     |                      38 |                        20 |
| 2025                              |             -140 |              100 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -140 |              110 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -140 |              120 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -140 |              130 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -140 |              140 |                 0.05495 |                 0.2468    |                      39 |                        22 |
| 2025                              |             -140 |              150 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -130 |              100 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -130 |              110 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -130 |              120 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -130 |              130 |                -0.1331  |                -0.09327   |                      40 |                        24 |
| 2025                              |             -130 |              140 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -130 |              150 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -120 |              100 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -120 |              110 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -120 |              120 |                 0.1172  |                 0.1752    |                      64 |                        39 |
| 2025                              |             -120 |              130 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -120 |              140 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -120 |              150 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -110 |              100 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -110 |              110 |                 0.1818  |                 0.2238    |                      63 |                        39 |
| 2025                              |             -110 |              120 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -110 |              130 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -110 |              140 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -110 |              150 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -100 |              100 |                 0.2381  |                 0.2821    |                      63 |                        39 |
| 2025                              |             -100 |              110 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -100 |              120 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -100 |              130 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -100 |              140 |               nan       |               nan         |                     nan |                       nan |
| 2025                              |             -100 |              150 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -150 |              100 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -150 |              110 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -150 |              120 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -150 |              130 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -150 |              140 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -150 |              150 |                 0.28    |                 0.2714    |                     125 |                        78 |
| SUPPLEMENTARY 2018-2025 all years |             -140 |              100 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -140 |              110 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -140 |              120 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -140 |              130 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -140 |              140 |                 0.08482 |                 0.2098    |                     128 |                        70 |
| SUPPLEMENTARY 2018-2025 all years |             -140 |              150 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -130 |              100 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -130 |              110 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -130 |              120 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -130 |              130 |                -0.02928 |                 0.0006617 |                     150 |                        93 |
| SUPPLEMENTARY 2018-2025 all years |             -130 |              140 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -130 |              150 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -120 |              100 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -120 |              110 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -120 |              120 |                 0.05255 |                 0.004433  |                     255 |                       188 |
| SUPPLEMENTARY 2018-2025 all years |             -120 |              130 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -120 |              140 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -120 |              150 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -110 |              100 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -110 |              110 |                 0.134   |                 0.0815    |                     266 |                       203 |
| SUPPLEMENTARY 2018-2025 all years |             -110 |              120 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -110 |              130 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -110 |              140 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -110 |              150 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -100 |              100 |                 0.188   |                 0.133     |                     266 |                       203 |
| SUPPLEMENTARY 2018-2025 all years |             -100 |              110 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -100 |              120 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -100 |              130 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -100 |              140 |               nan       |               nan         |                     nan |                       nan |
| SUPPLEMENTARY 2018-2025 all years |             -100 |              150 |               nan       |               nan         |                     nan |                       nan |

### What the exposure cap removes, and how those tickets fared

At a single price within one ticket size, EV order is the same as `P_ticket` order, so the greedy exhausts the highest-`P_est` legs first. In a four-leg week it takes the three pairings among the top three legs, at which point all three sit at the 2-unit cap and **every remaining ticket containing the fourth leg is skipped**. The cap therefore removes the lowest-`P_est` leg of large weeks almost by construction.

| block                             | reference_price            |   all_positive_ev |   selected_by_cap |   skipped_by_cap |   hit_rate_selected |   hit_rate_skipped |   mean_p_ticket_selected |   mean_p_ticket_skipped |
|:----------------------------------|:---------------------------|------------------:|------------------:|-----------------:|--------------------:|-------------------:|-------------------------:|------------------------:|
| 2018-2023 validation              | 2-team -110 (hypothetical) |               174 |               138 |               36 |              0.558  |             0.75   |                   0.5652 |                  0.5626 |
| 2018-2023 validation              | 3-team +160 (hypothetical) |                73 |                49 |               24 |              0.5306 |             0.625  |                   0.4278 |                  0.4237 |
| 2024                              | 2-team -110 (hypothetical) |                29 |                26 |                3 |              0.5    |             0.6667 |                   0.565  |                  0.5882 |
| 2024                              | 3-team +160 (hypothetical) |                10 |                 8 |                2 |              0.375  |             0      |                   0.4294 |                  0.4518 |
| 2025                              | 2-team -110 (hypothetical) |                63 |                39 |               24 |              0.641  |             0.5833 |                   0.571  |                  0.5631 |
| 2025                              | 3-team +160 (hypothetical) |                36 |                20 |               16 |              0.55   |             0.5    |                   0.4308 |                  0.4245 |
| SUPPLEMENTARY 2018-2025 all years | 2-team -110 (hypothetical) |               266 |               203 |               63 |              0.5665 |             0.6825 |                   0.5663 |                  0.564  |
| SUPPLEMENTARY 2018-2025 all years | 3-team +160 (hypothetical) |               119 |                77 |               42 |              0.5195 |             0.5476 |                   0.4287 |                  0.4253 |

In the 2018-2023 block and in the all-years row the skipped tickets won **more** often than the ones the cap kept, which is why the flat control shows a higher hypothetical ROI at most grid points there. **2025 reverses this** — the kept tickets out-performed the skipped ones — so the effect is not a stable property.

Crucially, the mean `P_ticket` of kept and skipped tickets is nearly identical (0.5663 against 0.5640 at 2-team -110, all years). The cap is therefore **not** discarding tickets the model rates materially worse; essentially the whole hit-rate gap is realized-outcome variation on a small sample, not a difference in model-rated quality.

**The exposure cap is a risk rule, not an EV rule.** It exists to bound single-leg exposure, and it does that exactly — no leg ever exceeds 2 units. Nothing here is a recommendation to change it, and no wager-sizing change is proposed.

## Dog/favorite composition of selected tickets

Descriptive only. This does **not** modify selection, and the frozen model treats all four primary shapes identically.

| block                             | composition   |   selected_ticket_rows |   wins |   outcome_hit_rate |   mean_p_ticket |
|:----------------------------------|:--------------|-----------------------:|-------:|-------------------:|----------------:|
| 2018-2023 validation              | all-dog       |                    435 |    242 |             0.5563 |          0.5508 |
| 2018-2023 validation              | all-favorite  |                     99 |     53 |             0.5354 |          0.5507 |
| 2018-2023 validation              | mixed         |                    754 |    409 |             0.5424 |          0.5204 |
| 2024                              | all-dog       |                     83 |     68 |             0.8193 |          0.5451 |
| 2024                              | all-favorite  |                     16 |      6 |             0.375  |          0.5763 |
| 2024                              | mixed         |                    135 |     33 |             0.2444 |          0.5286 |
| 2025                              | all-dog       |                    185 |    127 |             0.6865 |          0.5399 |
| 2025                              | all-favorite  |                     32 |     16 |             0.5    |          0.5715 |
| 2025                              | mixed         |                    221 |    114 |             0.5158 |          0.5082 |
| SUPPLEMENTARY 2018-2025 all years | all-dog       |                    703 |    437 |             0.6216 |          0.5472 |
| SUPPLEMENTARY 2018-2025 all years | all-favorite  |                    147 |     75 |             0.5102 |          0.558  |
| SUPPLEMENTARY 2018-2025 all years | mixed         |                   1110 |    556 |             0.5009 |          0.519  |

Note that composition counts are pooled across every grid price, so a ticket selected at several prices is counted once per price. They describe the shape of the selected card, not a sample of independent tickets.

## Overlap and effective sample

| block                             | reference_scenario                       |   nominal_tickets_selected |   unique_weeks_with_a_bet |   unique_constituent_legs |   max_aggregate_leg_exposure |   week_pl_min |   week_pl_median |   week_pl_max |
|:----------------------------------|:-----------------------------------------|---------------------------:|--------------------------:|--------------------------:|-----------------------------:|--------------:|-----------------:|--------------:|
| 2018-2023 validation              | 2-team -120 / 3-team +140 (hypothetical) |                        122 |                        61 |                       160 |                            2 |            -3 |                0 |         3.067 |
| 2024                              | 2-team -120 / 3-team +140 (hypothetical) |                         24 |                        12 |                        32 |                            2 |            -2 |                0 |         2.5   |
| 2025                              | 2-team -120 / 3-team +140 (hypothetical) |                         38 |                        15 |                        42 |                            2 |            -3 |                0 |         2.5   |
| SUPPLEMENTARY 2018-2025 all years | 2-team -120 / 3-team +140 (hypothetical) |                        184 |                        88 |                       234 |                            2 |            -3 |                0 |         3.067 |

The maximum aggregate leg exposure confirms the frozen 2-unit cap binds: no leg ever carries more than 2 units in a week.

## Machine-readable outputs

- `data/processed/phase3_price_grid.csv` — every grid point, both procedures
- `data/processed/phase3_price_matrix.csv` — the 2-D combined matrix
- `data/processed/phase3_selected_tickets.csv` — ticket-level, every scenario
- `data/processed/phase3_weekly_cards.csv` — weekly card, every scenario
- `data/processed/phase3_ticket_fair_prices.csv` — model-implied fair prices
- `data/processed/phase3_frontier_curves.csv` — price/PL curves
- `data/processed/phase3_cap_mechanism.csv` — what the exposure cap removes

> **HYPOTHETICAL HISTORICAL SENSITIVITY** — assumes this teaser price was available for every qualifying historical ticket. **Actual historical teaser prices are unknown.** This is not a backtested sportsbook return and not a realized ROI.

