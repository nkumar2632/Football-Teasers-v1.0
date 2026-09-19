# Phase 3 — historical outcome price frontier

## B: HISTORICAL OUTCOME BREAK-EVEN PRICE

The payout at which **realized historical profit equals zero**, using the actual outcomes of the tickets the frozen procedure would have selected. This is derived from results, not from `P_est`.

**This is a different object from A: MODEL-IMPLIED FAIR PRICE** (`reports/phase3_fair_price_distribution.md`), which is derived from the model's own probabilities. A gap between A and B is a statement about how the realized sample differed from the model, on a sample of this size. Neither is a price any book offered.

**Frozen Teaser Model v1.0 is unchanged.** `P_ticket` is the product of leg `P_est` values, with no correlation adjustment: Phase 2C found only weak evidence against independence, which is not grounds for altering a frozen model.

- **Three source regimes.** 2018-2023 and 2024 sit on the pre-2025 archived line feed; 2025 sits on a different feed. The all-years row is supplementary only.
- Lines are archived reference lines with no documented capture time. They are not closing lines.

> Tickets share legs within a week. No interval anywhere in this phase treats tickets as independent observations; every reported interval is a week-cluster bootstrap.

Selection depends on price — a better payout makes more tickets positive-EV and reorders the greedy walk — so the frontier cannot be inverted from a hit rate. The whole frozen procedure is re-run at every price on a fine scan, and the crossing is then located by bisection.

## Crossing points

| block                             | ticket_size   |   breakeven_net_profit |   breakeven_american |   tickets_selected_at_crossing | note                                                                                                                          |
|:----------------------------------|:--------------|-----------------------:|---------------------:|-------------------------------:|:------------------------------------------------------------------------------------------------------------------------------|
| 2018-2023 validation              | 2-team        |                 0.8438 |               -118.5 |                            133 | Crossing located by scan then bisection; the frozen procedure is re-run at every price, so selection changes along the curve. |
| 2018-2023 validation              | 3-team        |                 1.333  |                133.3 |                             22 | Crossing located by scan then bisection; the frozen procedure is re-run at every price, so selection changes along the curve. |
| 2024                              | 2-team        |                 1      |                100   |                             26 | Crossing located by scan then bisection; the frozen procedure is re-run at every price, so selection changes along the curve. |
| 2024                              | 3-team        |                 1.667  |                166.7 |                              8 | Crossing located by scan then bisection; the frozen procedure is re-run at every price, so selection changes along the curve. |
| 2025                              | 2-team        |                 0.7821 |               -127.9 |                             32 | Crossing located by scan then bisection; the frozen procedure is re-run at every price, so selection changes along the curve. |
| 2025                              | 3-team        |                 1.383  |                138.3 |                             16 | Crossing located by scan then bisection; the frozen procedure is re-run at every price, so selection changes along the curve. |
| SUPPLEMENTARY 2018-2025 all years | 2-team        |                 0.7774 |               -128.6 |                            106 | Crossing located by scan then bisection; the frozen procedure is re-run at every price, so selection changes along the curve. |
| SUPPLEMENTARY 2018-2025 all years | 3-team        |                 1.333  |                133.3 |                             36 | Crossing located by scan then bisection; the frozen procedure is re-run at every price, so selection changes along the curve. |

## Sensitivity around the threshold

Hypothetical P/L and ROI at prices bracketing each crossing. A shallow curve means the conclusion is fragile to the price assumption.

### 2018-2023 validation — 2-team

|   american |   profit |   tickets_selected |   units |   wins |   profit_loss |      roi |
|-----------:|---------:|-------------------:|--------:|-------:|--------------:|---------:|
|     -168.1 |    0.595 |                  1 |       1 |      1 |         0.595 |  0.595   |
|     -157.5 |    0.635 |                  2 |       2 |      2 |         1.27  |  0.635   |
|     -148.1 |    0.675 |                  5 |       5 |      3 |         0.025 |  0.005   |
|     -139.9 |    0.715 |                 19 |      19 |     10 |        -1.85  | -0.09737 |
|     -132.5 |    0.755 |                 50 |      50 |     30 |         2.65  |  0.053   |
|     -125.8 |    0.795 |                 84 |      84 |     49 |         3.955 |  0.04708 |
|     -119.8 |    0.835 |                124 |     124 |     66 |        -2.89  | -0.02331 |
|     -114.3 |    0.875 |                138 |     138 |     77 |         6.375 |  0.0462  |
|     -109.3 |    0.915 |                138 |     138 |     77 |         9.455 |  0.06851 |
|     -104.7 |    0.955 |                138 |     138 |     77 |        12.54  |  0.09083 |
|     -100.5 |    0.995 |                138 |     138 |     77 |        15.62  |  0.1132  |
|      103.5 |    1.035 |                138 |     138 |     77 |        18.7   |  0.1355  |
|      107.5 |    1.075 |                138 |     138 |     77 |        21.78  |  0.1578  |

### 2018-2023 validation — 3-team

|   american |   profit |   tickets_selected |   units |   wins |   profit_loss |       roi |
|-----------:|---------:|-------------------:|--------:|-------:|--------------:|----------:|
|      108.5 |    1.085 |                  0 |       0 |      0 |         0     | nan       |
|      112.5 |    1.125 |                  1 |       1 |      1 |         1.125 |   1.125   |
|      116.5 |    1.165 |                  1 |       1 |      1 |         1.165 |   1.165   |
|      120.5 |    1.205 |                  2 |       2 |      1 |         0.205 |   0.1025  |
|      124.5 |    1.245 |                  8 |       8 |      3 |        -1.265 |  -0.1581  |
|      128.5 |    1.285 |                 15 |      15 |      5 |        -3.575 |  -0.2383  |
|      132.5 |    1.325 |                 20 |      20 |      9 |         0.925 |   0.04625 |
|      136.5 |    1.365 |                 29 |      29 |     16 |         8.84  |   0.3048  |
|      140.5 |    1.405 |                 36 |      36 |     19 |         9.695 |   0.2693  |
|      144.5 |    1.445 |                 41 |      41 |     21 |        10.35  |   0.2523  |
|      148.5 |    1.485 |                 47 |      47 |     24 |        12.64  |   0.2689  |
|      152.5 |    1.525 |                 49 |      49 |     26 |        16.65  |   0.3398  |
|      156.5 |    1.565 |                 49 |      49 |     26 |        17.69  |   0.361   |

### 2024 — 2-team

|   american |   profit |   tickets_selected |   units |   wins |   profit_loss |      roi |
|-----------:|---------:|-------------------:|--------:|-------:|--------------:|---------:|
|     -132.5 |    0.755 |                  7 |       7 |      2 |        -3.49  | -0.4986  |
|     -125.8 |    0.795 |                 13 |      13 |      7 |        -0.435 | -0.03346 |
|     -119.8 |    0.835 |                 25 |      25 |     12 |        -2.98  | -0.1192  |
|     -114.3 |    0.875 |                 26 |      26 |     13 |        -1.625 | -0.0625  |
|     -109.3 |    0.915 |                 26 |      26 |     13 |        -1.105 | -0.0425  |
|     -104.7 |    0.955 |                 26 |      26 |     13 |        -0.585 | -0.0225  |
|     -100.5 |    0.995 |                 26 |      26 |     13 |        -0.065 | -0.0025  |
|      103.5 |    1.035 |                 26 |      26 |     13 |         0.455 |  0.0175  |
|      107.5 |    1.075 |                 26 |      26 |     13 |         0.975 |  0.0375  |
|      111.5 |    1.115 |                 26 |      26 |     13 |         1.495 |  0.0575  |
|      115.5 |    1.155 |                 26 |      26 |     13 |         2.015 |  0.0775  |
|      119.5 |    1.195 |                 26 |      26 |     13 |         2.535 |  0.0975  |
|      123.5 |    1.235 |                 26 |      26 |     13 |         3.055 |  0.1175  |

### 2024 — 3-team

|   american |   profit |   tickets_selected |   units |   wins |   profit_loss |      roi |
|-----------:|---------:|-------------------:|--------:|-------:|--------------:|---------:|
|        142 |     1.42 |                  5 |       5 |      3 |          2.26 |  0.452   |
|        146 |     1.46 |                  7 |       7 |      3 |          0.38 |  0.05429 |
|        150 |     1.5  |                  8 |       8 |      3 |         -0.5  | -0.0625  |
|        154 |     1.54 |                  8 |       8 |      3 |         -0.38 | -0.0475  |
|        158 |     1.58 |                  8 |       8 |      3 |         -0.26 | -0.0325  |
|        162 |     1.62 |                  8 |       8 |      3 |         -0.14 | -0.0175  |
|        166 |     1.66 |                  8 |       8 |      3 |         -0.02 | -0.0025  |
|        170 |     1.7  |                  8 |       8 |      3 |          0.1  |  0.0125  |
|        174 |     1.74 |                  8 |       8 |      3 |          0.22 |  0.0275  |
|        178 |     1.78 |                  8 |       8 |      3 |          0.34 |  0.0425  |
|        182 |     1.82 |                  8 |       8 |      3 |          0.46 |  0.0575  |
|        186 |     1.86 |                  8 |       8 |      3 |          0.58 |  0.0725  |
|        190 |     1.9  |                  8 |       8 |      3 |          0.7  |  0.0875  |

### 2025 — 2-team

|   american |   profit |   tickets_selected |   units |   wins |   profit_loss |       roi |
|-----------:|---------:|-------------------:|--------:|-------:|--------------:|----------:|
|     -186.9 |    0.535 |                  0 |       0 |      0 |         0     | nan       |
|     -173.9 |    0.575 |                  0 |       0 |      0 |         0     | nan       |
|     -162.6 |    0.615 |                  0 |       0 |      0 |         0     | nan       |
|     -152.7 |    0.655 |                  0 |       0 |      0 |         0     | nan       |
|     -143.9 |    0.695 |                  3 |       3 |      1 |        -1.305 |  -0.435   |
|     -136.1 |    0.735 |                 11 |      11 |      6 |        -0.59  |  -0.05364 |
|     -129   |    0.775 |                 28 |      28 |     15 |        -1.375 |  -0.04911 |
|     -122.7 |    0.815 |                 38 |      38 |     24 |         5.56  |   0.1463  |
|     -117   |    0.855 |                 39 |      39 |     25 |         7.375 |   0.1891  |
|     -111.7 |    0.895 |                 39 |      39 |     25 |         8.375 |   0.2147  |
|     -107   |    0.935 |                 39 |      39 |     25 |         9.375 |   0.2404  |
|     -102.6 |    0.975 |                 39 |      39 |     25 |        10.38  |   0.266   |
|      101.5 |    1.015 |                 39 |      39 |     25 |        11.38  |   0.2917  |

### 2025 — 3-team

|   american |   profit |   tickets_selected |   units |   wins |   profit_loss |       roi |
|-----------:|---------:|-------------------:|--------:|-------:|--------------:|----------:|
|      113.5 |    1.135 |                  0 |       0 |      0 |         0     | nan       |
|      117.5 |    1.175 |                  1 |       1 |      0 |        -1     |  -1       |
|      121.5 |    1.215 |                  1 |       1 |      0 |        -1     |  -1       |
|      125.5 |    1.255 |                  3 |       3 |      0 |        -3     |  -1       |
|      129.5 |    1.295 |                  4 |       4 |      1 |        -1.705 |  -0.4262  |
|      133.5 |    1.335 |                 11 |      11 |      5 |         0.675 |   0.06136 |
|      137.5 |    1.375 |                 15 |      15 |      6 |        -0.75  |  -0.05    |
|      141.5 |    1.415 |                 19 |      19 |     10 |         5.15  |   0.2711  |
|      145.5 |    1.455 |                 20 |      20 |     11 |         7.005 |   0.3503  |
|      149.5 |    1.495 |                 20 |      20 |     11 |         7.445 |   0.3723  |
|      153.5 |    1.535 |                 20 |      20 |     11 |         7.885 |   0.3943  |
|      157.5 |    1.575 |                 20 |      20 |     11 |         8.325 |   0.4163  |
|      161.5 |    1.615 |                 20 |      20 |     11 |         8.765 |   0.4383  |

### SUPPLEMENTARY 2018-2025 all years — 2-team

|   american |   profit |   tickets_selected |   units |   wins |   profit_loss |        roi |
|-----------:|---------:|-------------------:|--------:|-------:|--------------:|-----------:|
|     -188.7 |     0.53 |                  0 |       0 |      0 |          0    | nan        |
|     -175.4 |     0.57 |                  1 |       1 |      1 |          0.57 |   0.57     |
|     -163.9 |     0.61 |                  1 |       1 |      1 |          0.61 |   0.61     |
|     -153.8 |     0.65 |                  3 |       3 |      2 |          0.3  |   0.1      |
|     -144.9 |     0.69 |                 17 |      17 |      7 |         -5.17 |  -0.3041   |
|     -137   |     0.73 |                 45 |      45 |     22 |         -6.94 |  -0.1542   |
|     -129.9 |     0.77 |                 96 |      96 |     54 |         -0.42 |  -0.004375 |
|     -123.5 |     0.81 |                160 |     160 |     92 |          6.52 |   0.04075  |
|     -117.6 |     0.85 |                201 |     201 |    114 |          9.9  |   0.04925  |
|     -112.4 |     0.89 |                203 |     203 |    115 |         14.35 |   0.07069  |
|     -107.5 |     0.93 |                203 |     203 |    115 |         18.95 |   0.09335  |
|     -103.1 |     0.97 |                203 |     203 |    115 |         23.55 |   0.116    |
|      101   |     1.01 |                203 |     203 |    115 |         28.15 |   0.1387   |

### SUPPLEMENTARY 2018-2025 all years — 3-team

|   american |   profit |   tickets_selected |   units |   wins |   profit_loss |       roi |
|-----------:|---------:|-------------------:|--------:|-------:|--------------:|----------:|
|      108.5 |    1.085 |                  0 |       0 |      0 |         0     | nan       |
|      112.5 |    1.125 |                  1 |       1 |      1 |         1.125 |   1.125   |
|      116.5 |    1.165 |                  1 |       1 |      1 |         1.165 |   1.165   |
|      120.5 |    1.205 |                  6 |       6 |      2 |        -1.59  |  -0.265   |
|      124.5 |    1.245 |                 14 |      14 |      4 |        -5.02  |  -0.3586  |
|      128.5 |    1.285 |                 22 |      22 |      7 |        -6.005 |  -0.273   |
|      132.5 |    1.325 |                 33 |      33 |     14 |        -0.45  |  -0.01364 |
|      136.5 |    1.365 |                 47 |      47 |     23 |         7.395 |   0.1573  |
|      140.5 |    1.405 |                 59 |      59 |     31 |        15.56  |   0.2636  |
|      144.5 |    1.445 |                 68 |      68 |     35 |        17.58  |   0.2585  |
|      148.5 |    1.485 |                 74 |      74 |     38 |        20.43  |   0.2761  |
|      152.5 |    1.525 |                 77 |      77 |     40 |        24     |   0.3117  |
|      156.5 |    1.565 |                 77 |      77 |     40 |        25.6   |   0.3325  |

## A versus B, side by side

Model-implied fair price against historical outcome break-even, for the same block and ticket size. **These are different objects.** A is what the model says the ticket is worth; B is what this particular realized sample would have needed.

Where B is a *worse* price than A (more juice tolerable), the selected tickets out-performed the frozen `P_ticket` in that sample. Where B is *better* than A, they under-performed. Neither is evidence about future prices or future outcomes.

> **HYPOTHETICAL HISTORICAL SENSITIVITY** — assumes this teaser price was available for every qualifying historical ticket. **Actual historical teaser prices are unknown.** This is not a backtested sportsbook return and not a realized ROI.

Machine-readable curves: `data/processed/phase3_frontier_curves.csv`.

