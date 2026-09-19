# Data-Quality Audit — NFL 2024, 2025 — nflverse/nfldata

This audit runs **before** any strategy calculation. Its purpose is to decide whether the dataset preserves enough half-point fidelity to test Teaser Model v1.0 at all. It contains no model-performance results of any kind.

**Seasons audited:** 2024, 2025

## Verdict

### PASS

The dataset preserves half-point fidelity and is safe to use for v1.0 historical testing, subject to the limitations listed below.

## Checks

| check                                 | status   | critical   | detail                                                                                                                                                                                                                                                                                                                                                                                                                               |
|:--------------------------------------|:---------|:-----------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| final_scores_present                  | PASS     | yes        | 0 of 570 games have no final score.                                                                                                                                                                                                                                                                                                                                                                                                  |
| missing_spreads                       | PASS     | yes        | 0 of 570 games missing spread_line (0.000%); gate is <= 1.0%.                                                                                                                                                                                                                                                                                                                                                                        |
| missing_totals                        | PASS     | yes        | 0 of 570 games missing total_line (0.000%); gate is <= 1.0%.                                                                                                                                                                                                                                                                                                                                                                         |
| duplicate_games                       | PASS     | yes        | 0 duplicated game_id values; 0 rows duplicating season/week/home/away.                                                                                                                                                                                                                                                                                                                                                               |
| spreads_on_half_point_grid            | PASS     | yes        | 0 spread values are not multiples of 0.5.                                                                                                                                                                                                                                                                                                                                                                                            |
| spread_half_point_share               | PASS     | yes        | 363 of 570 spreads end in .5 (63.68%); gate is >= 40%. A source that rounded half-points away would sit near 0%.                                                                                                                                                                                                                                                                                                                     |
| spread_half_point_share_every_season  | PASS     | yes        | Lowest single-season half-point share is 52.28% in 2024; gate is >= 40%.                                                                                                                                                                                                                                                                                                                                                             |
| season_composition_consistency        | WARN     | no         | spread half-point share varies by 22.8% across seasons ({2024: 0.523, 2025: 0.751}). total half-point share varies by 41.8% across seasons ({2024: 0.582, 2025: 1.0}). This is consistent with a change in the upstream line source or book between seasons. It does not round half-points away (the fidelity gates still pass), but it means leg counts are not directly comparable across seasons and must be reported per season. |
| primary_geometry_present              | PASS     | yes        | All four primary shapes appear in the data.                                                                                                                                                                                                                                                                                                                                                                                          |
| primary_geometry_present_every_season | PASS     | no         | Every primary shape appears in every season.                                                                                                                                                                                                                                                                                                                                                                                         |
| key_numbers_not_collapsed             | PASS     | yes        | Every whole number present in the data still has its adjacent half-point represented.                                                                                                                                                                                                                                                                                                                                                |
| total_half_point_share                | PASS     | no         | 451 of 570 totals end in .5 (79.12%). Totals do not gate the model the way spreads do, but a near-zero share would still indicate rounding.                                                                                                                                                                                                                                                                                          |
| totals_on_half_point_grid             | PASS     | yes        | 0 total values are not multiples of 0.5.                                                                                                                                                                                                                                                                                                                                                                                             |
| suspicious_rounding_patterns          | PASS     | no         | No suspicious rounding patterns detected.                                                                                                                                                                                                                                                                                                                                                                                            |
| impossible_values                     | PASS     | yes        | No impossible values found.                                                                                                                                                                                                                                                                                                                                                                                                          |
| line_provenance_is_honest             | PASS     | no         | Lines are labelled 'archived_reference_line'. 'true_timestamped_close' is only permitted when the source documents a capture time before kickoff.                                                                                                                                                                                                                                                                                    |

### Warnings (non-blocking)

- `season_composition_consistency` — spread half-point share varies by 22.8% across seasons ({2024: 0.523, 2025: 0.751}). total half-point share varies by 41.8% across seasons ({2024: 0.582, 2025: 1.0}). This is consistent with a change in the upstream line source or book between seasons. It does not round half-points away (the fidelity gates still pass), but it means leg counts are not directly comparable across seasons and must be reported per season.

## Tables

### Games by season

|   season |   games |
|---------:|--------:|
|     2024 |     285 |
|     2025 |     285 |

### Games by season and type

|   season | game_type   |   games |
|---------:|:------------|--------:|
|     2024 | CON         |       2 |
|     2024 | DIV         |       4 |
|     2024 | REG         |     272 |
|     2024 | SB          |       1 |
|     2024 | WC          |       6 |
|     2025 | CON         |       2 |
|     2025 | DIV         |       4 |
|     2025 | REG         |     272 |
|     2025 | SB          |       1 |
|     2025 | WC          |       6 |

### Half-point share by season

|   season |   spreads |   half_point |   half_point_share |   integer |
|---------:|----------:|-------------:|-------------------:|----------:|
|     2024 |       285 |          149 |             0.5228 |       136 |
|     2025 |       285 |          214 |             0.7509 |        71 |

### Composition by season

|   season |   spread_half_point_share |   total_half_point_share |
|---------:|--------------------------:|-------------------------:|
|     2024 |                    0.5228 |                   0.5825 |
|     2025 |                    0.7509 |                   1      |

### Integer vs half-point spreads

| kind            |   count |   share |
|:----------------|--------:|--------:|
| half-point (.5) |     363 |  0.6368 |
| integer (.0)    |     207 |  0.3632 |

### Spread fractional parts

|   fractional_part |   count |
|------------------:|--------:|
|               0   |     207 |
|               0.5 |     363 |

### Primary-geometry leg counts

|   leg_spread |   legs_total |   legs_2024 |   legs_2025 |
|-------------:|-------------:|------------:|------------:|
|          1.5 |           48 |          13 |          35 |
|          2.5 |           70 |          31 |          39 |
|         -7.5 |           32 |          16 |          16 |
|         -8.5 |           10 |           1 |           9 |

### Key-number pairs (whole vs half)

|   whole |   count_whole |   adjacent_half |   count_half |
|--------:|--------------:|----------------:|-------------:|
|       2 |             8 |             1.5 |           48 |
|       2 |             8 |             2.5 |           70 |
|       3 |            75 |             2.5 |           70 |
|       3 |            75 |             3.5 |           64 |
|       7 |            34 |             6.5 |           32 |
|       7 |            34 |             7.5 |           32 |
|       8 |             6 |             7.5 |           32 |
|       8 |             6 |             8.5 |           10 |
|       9 |             4 |             8.5 |           10 |

### Total line summary

|   season |   n |   min |   p25 |   median |   p75 |   max |   mean |   half_point_share |   at_or_below_47 |
|---------:|----:|------:|------:|---------:|------:|------:|-------:|-------------------:|-----------------:|
|     2024 | 285 |  32.5 |  41.5 |     44.5 |  47.5 |  56.5 |  44.48 |             0.5825 |              212 |
|     2025 | 285 |  33.5 |  42.5 |     44.5 |  47.5 |  55.5 |  44.88 |             1      |              197 |

### Spread increment distribution (source field)

|   spread_line (home-favoured-by) |   count |    share |
|---------------------------------:|--------:|---------:|
|                            -16.5 |       1 | 0.001754 |
|                            -13.5 |       1 | 0.001754 |
|                            -12.5 |       2 | 0.003509 |
|                            -11   |       1 | 0.001754 |
|                            -10.5 |       2 | 0.003509 |
|                            -10   |       3 | 0.005263 |
|                             -9.5 |       1 | 0.001754 |
|                             -9   |       1 | 0.001754 |
|                             -8.5 |       5 | 0.008772 |
|                             -7.5 |      13 | 0.02281  |
|                             -7   |      15 | 0.02632  |
|                             -6.5 |      10 | 0.01754  |
|                             -6   |      12 | 0.02105  |
|                             -5.5 |      14 | 0.02456  |
|                             -5   |       2 | 0.003509 |
|                             -4.5 |      15 | 0.02632  |
|                             -4   |       3 | 0.005263 |
|                             -3.5 |      31 | 0.05439  |
|                             -3   |      36 | 0.06316  |
|                             -2.5 |      30 | 0.05263  |
|                             -2   |       6 | 0.01053  |
|                             -1.5 |      21 | 0.03684  |
|                             -1   |      10 | 0.01754  |
|                              1   |       4 | 0.007018 |
|                              1.5 |      27 | 0.04737  |
|                              2   |       2 | 0.003509 |
|                              2.5 |      40 | 0.07018  |
|                              3   |      39 | 0.06842  |
|                              3.5 |      33 | 0.05789  |
|                              4   |       9 | 0.01579  |
|                              4.5 |      14 | 0.02456  |
|                              5   |       3 | 0.005263 |
|                              5.5 |      20 | 0.03509  |
|                              6   |      17 | 0.02982  |
|                              6.5 |      22 | 0.0386   |
|                              7   |      19 | 0.03333  |
|                              7.5 |      19 | 0.03333  |
|                              8   |       6 | 0.01053  |
|                              8.5 |       5 | 0.008772 |
|                              9   |       3 | 0.005263 |
|                              9.5 |      10 | 0.01754  |
|                             10   |       6 | 0.01053  |
|                             10.5 |       5 | 0.008772 |
|                             12.5 |      11 | 0.0193   |
|                             13   |       1 | 0.001754 |
|                             13.5 |       4 | 0.007018 |
|                             14   |       9 | 0.01579  |
|                             14.5 |       4 | 0.007018 |
|                             15.5 |       2 | 0.003509 |
|                             19.5 |       1 | 0.001754 |

### Leg spread distribution (team perspective)

|   leg spread (team perspective) |   count |     share |
|--------------------------------:|--------:|----------:|
|                           -19.5 |       1 | 0.0008772 |
|                           -16.5 |       1 | 0.0008772 |
|                           -15.5 |       2 | 0.001754  |
|                           -14.5 |       4 | 0.003509  |
|                           -14   |       9 | 0.007895  |
|                           -13.5 |       5 | 0.004386  |
|                           -13   |       1 | 0.0008772 |
|                           -12.5 |      13 | 0.0114    |
|                           -11   |       1 | 0.0008772 |
|                           -10.5 |       7 | 0.00614   |
|                           -10   |       9 | 0.007895  |
|                            -9.5 |      11 | 0.009649  |
|                            -9   |       4 | 0.003509  |
|                            -8.5 |      10 | 0.008772  |
|                            -8   |       6 | 0.005263  |
|                            -7.5 |      32 | 0.02807   |
|                            -7   |      34 | 0.02982   |
|                            -6.5 |      32 | 0.02807   |
|                            -6   |      29 | 0.02544   |
|                            -5.5 |      34 | 0.02982   |
|                            -5   |       5 | 0.004386  |
|                            -4.5 |      29 | 0.02544   |
|                            -4   |      12 | 0.01053   |
|                            -3.5 |      64 | 0.05614   |
|                            -3   |      75 | 0.06579   |
|                            -2.5 |      70 | 0.0614    |
|                            -2   |       8 | 0.007018  |
|                            -1.5 |      48 | 0.04211   |
|                            -1   |      14 | 0.01228   |
|                             1   |      14 | 0.01228   |
|                             1.5 |      48 | 0.04211   |
|                             2   |       8 | 0.007018  |
|                             2.5 |      70 | 0.0614    |
|                             3   |      75 | 0.06579   |
|                             3.5 |      64 | 0.05614   |
|                             4   |      12 | 0.01053   |
|                             4.5 |      29 | 0.02544   |
|                             5   |       5 | 0.004386  |
|                             5.5 |      34 | 0.02982   |
|                             6   |      29 | 0.02544   |
|                             6.5 |      32 | 0.02807   |
|                             7   |      34 | 0.02982   |
|                             7.5 |      32 | 0.02807   |
|                             8   |       6 | 0.005263  |
|                             8.5 |      10 | 0.008772  |
|                             9   |       4 | 0.003509  |
|                             9.5 |      11 | 0.009649  |
|                            10   |       9 | 0.007895  |
|                            10.5 |       7 | 0.00614   |
|                            11   |       1 | 0.0008772 |
|                            12.5 |      13 | 0.0114    |
|                            13   |       1 | 0.0008772 |
|                            13.5 |       5 | 0.004386  |
|                            14   |       9 | 0.007895  |
|                            14.5 |       4 | 0.003509  |
|                            15.5 |       2 | 0.001754  |
|                            16.5 |       1 | 0.0008772 |
|                            19.5 |       1 | 0.0008772 |

### Total line distribution

|   total_line |   count |    share |
|-------------:|--------:|---------:|
|         32.5 |       1 | 0.001754 |
|         33.5 |       1 | 0.001754 |
|         34.5 |       1 | 0.001754 |
|         35.5 |       4 | 0.007018 |
|         36   |       2 | 0.003509 |
|         36.5 |       8 | 0.01404  |
|         37   |       5 | 0.008772 |
|         37.5 |      16 | 0.02807  |
|         38   |       2 | 0.003509 |
|         38.5 |       9 | 0.01579  |
|         39   |       4 | 0.007018 |
|         39.5 |      10 | 0.01754  |
|         40   |       8 | 0.01404  |
|         40.5 |      20 | 0.03509  |
|         41   |       6 | 0.01053  |
|         41.5 |      47 | 0.08246  |
|         42   |      15 | 0.02632  |
|         42.5 |      27 | 0.04737  |
|         43   |      11 | 0.0193   |
|         43.5 |      46 | 0.0807   |
|         44   |       8 | 0.01404  |
|         44.5 |      56 | 0.09825  |
|         45   |      10 | 0.01754  |
|         45.5 |      32 | 0.05614  |
|         46   |      11 | 0.0193   |
|         46.5 |      39 | 0.06842  |
|         47   |      10 | 0.01754  |
|         47.5 |      37 | 0.06491  |
|         48   |       8 | 0.01404  |
|         48.5 |      30 | 0.05263  |
|         49   |      10 | 0.01754  |
|         49.5 |      22 | 0.0386   |
|         50   |       1 | 0.001754 |
|         50.5 |      14 | 0.02456  |
|         51   |       4 | 0.007018 |
|         51.5 |      15 | 0.02632  |
|         52   |       1 | 0.001754 |
|         52.5 |       4 | 0.007018 |
|         53   |       2 | 0.003509 |
|         53.5 |       4 | 0.007018 |
|         54   |       1 | 0.001754 |
|         54.5 |       4 | 0.007018 |
|         55.5 |       3 | 0.005263 |
|         56.5 |       1 | 0.001754 |

## Thresholds used

These are **pre-registered data-quality gates, not model parameters.** They describe what a dataset must look like to be usable, were fixed before any strategy result was computed, and must never be tuned to make a dataset pass.

|   min_half_point_share |   max_missing_share |   max_season_composition_gap |   max_abs_spread |   min_total |   max_total |
|-----------------------:|--------------------:|-----------------------------:|-----------------:|------------:|------------:|
|                    0.4 |                0.01 |                          0.2 |               30 |          20 |          80 |

## Source and provenance notes

- Source: nflverse/nfldata games.csv (Lee Sharpe) — https://github.com/nflverse/nfldata/blob/master/data/games.csv
- Upstream commit: 4a7ebfde2a7c784255f95c457d8c638a7ca188fa
- Retrieved (UTC): 2026-09-19T14:17:56+00:00
- Raw snapshot: `data/raw/nflverse_nfldata_games.csv` (sha256 `35bc182c6e810955404f8e035228fc6535cce3c39c8ecc0dc8af96715b1cd30f`)
- Line provenance label: **archived_reference_line**. nfldata DATASETS.md documents spread_line/total_line only as 'the spread line for the game' / 'the total line for the game'. It makes no claim about capture time, so the fields cannot be called a close of any kind.
- Documented meaning of `spread_line`: The spread line for the game. A positive number means the home team was favored by that many points, a negative number means the away team was favored by that many points. No capture time is documented.
- Documented meaning of `total_line`: The total line for the game. No capture time is documented.
- Caveat: spread_line/total_line have no documented capture timestamp. They are archived reference lines, NOT a close of any kind.
- Caveat: The source aggregates lines historically; the exact sportsbook is not recorded per game.
- Caveat: No teaser menu prices are present in this source. None have been invented.

## Limitations

- The source provides one spread and one total per game. It does not provide an opening line, a line-movement history, a per-book line, or a capture timestamp, so CLV and line-movement measurement (spec §11, market-quality track) cannot be computed from this source at all.
- No teaser menu prices exist in this source. Per spec §7, none have been invented: historical work must test hit rate and calibration directly, report fair break-even pricing, and run sensitivity analysis at explicitly hypothetical prices.
- The sportsbook behind each archived line is not identified.
- Because the lines are archived reference lines rather than a documented close, they are suitable as a *grading* line for backtesting geometry and calibration, and are NOT suitable for any CLV claim.

