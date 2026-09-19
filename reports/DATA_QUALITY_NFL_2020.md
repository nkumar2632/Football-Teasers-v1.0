# Data-Quality Audit — NFL 2020 — nflverse/nfldata

This audit runs **before** any strategy calculation. Its purpose is to decide whether the dataset preserves enough half-point fidelity to test Teaser Model v1.0 at all. It contains no model-performance results of any kind.

**Seasons audited:** 2020

## Verdict

### PASS

The dataset preserves half-point fidelity and is safe to use for v1.0 historical testing, subject to the limitations listed below.

## Checks

| check                                 | status   | critical   | detail                                                                                                                                            |
|:--------------------------------------|:---------|:-----------|:--------------------------------------------------------------------------------------------------------------------------------------------------|
| final_scores_present                  | PASS     | yes        | 0 of 269 games have no final score.                                                                                                               |
| missing_spreads                       | PASS     | yes        | 0 of 269 games missing spread_line (0.000%); gate is <= 1.0%.                                                                                     |
| missing_totals                        | PASS     | yes        | 0 of 269 games missing total_line (0.000%); gate is <= 1.0%.                                                                                      |
| duplicate_games                       | PASS     | yes        | 0 duplicated game_id values; 0 rows duplicating season/week/home/away.                                                                            |
| spreads_on_half_point_grid            | PASS     | yes        | 0 spread values are not multiples of 0.5.                                                                                                         |
| spread_half_point_share               | PASS     | yes        | 127 of 269 spreads end in .5 (47.21%); gate is >= 40%. A source that rounded half-points away would sit near 0%.                                  |
| spread_half_point_share_every_season  | PASS     | yes        | Lowest single-season half-point share is 47.21% in 2020; gate is >= 40%.                                                                          |
| season_composition_consistency        | PASS     | no         | Half-point composition is consistent across seasons.                                                                                              |
| primary_geometry_present              | PASS     | yes        | All four primary shapes appear in the data.                                                                                                       |
| primary_geometry_present_every_season | PASS     | no         | Every primary shape appears in every season.                                                                                                      |
| key_numbers_not_collapsed             | PASS     | yes        | Every whole number present in the data still has its adjacent half-point represented.                                                             |
| total_half_point_share                | PASS     | no         | 115 of 269 totals end in .5 (42.75%). Totals do not gate the model the way spreads do, but a near-zero share would still indicate rounding.       |
| totals_on_half_point_grid             | PASS     | yes        | 0 total values are not multiples of 0.5.                                                                                                          |
| suspicious_rounding_patterns          | PASS     | no         | No suspicious rounding patterns detected.                                                                                                         |
| impossible_values                     | PASS     | yes        | No impossible values found.                                                                                                                       |
| line_provenance_is_honest             | PASS     | no         | Lines are labelled 'archived_reference_line'. 'true_timestamped_close' is only permitted when the source documents a capture time before kickoff. |

## Tables

### Games by season

|   season |   games |
|---------:|--------:|
|     2020 |     269 |

### Games by season and type

|   season | game_type   |   games |
|---------:|:------------|--------:|
|     2020 | CON         |       2 |
|     2020 | DIV         |       4 |
|     2020 | REG         |     256 |
|     2020 | SB          |       1 |
|     2020 | WC          |       6 |

### Half-point share by season

|   season |   spreads |   half_point |   half_point_share |   integer |
|---------:|----------:|-------------:|-------------------:|----------:|
|     2020 |       269 |          127 |             0.4721 |       142 |

### Composition by season

|   season |   spread_half_point_share |   total_half_point_share |
|---------:|--------------------------:|-------------------------:|
|     2020 |                    0.4721 |                   0.4275 |

### Integer vs half-point spreads

| kind            |   count |   share |
|:----------------|--------:|--------:|
| half-point (.5) |     127 |  0.4721 |
| integer (.0)    |     142 |  0.5279 |

### Spread fractional parts

|   fractional_part |   count |
|------------------:|--------:|
|               0   |     142 |
|               0.5 |     127 |

### Primary-geometry leg counts

|   leg_spread |   legs_total |   legs_2020 |
|-------------:|-------------:|------------:|
|          1.5 |            7 |           7 |
|          2.5 |           19 |          19 |
|         -7.5 |           22 |          22 |
|         -8.5 |            4 |           4 |

### Key-number pairs (whole vs half)

|   whole |   count_whole |   adjacent_half |   count_half |
|--------:|--------------:|----------------:|-------------:|
|       2 |             7 |             1.5 |            7 |
|       2 |             7 |             2.5 |           19 |
|       3 |            39 |             2.5 |           19 |
|       3 |            39 |             3.5 |           21 |
|       7 |            24 |             6.5 |           12 |
|       7 |            24 |             7.5 |           22 |
|       8 |             2 |             7.5 |           22 |
|       8 |             2 |             8.5 |            4 |
|       9 |             0 |             8.5 |            4 |

### Total line summary

|   season |   n |   min |   p25 |   median |   p75 |   max |   mean |   half_point_share |   at_or_below_47 |
|---------:|----:|------:|------:|---------:|------:|------:|-------:|-------------------:|-----------------:|
|     2020 | 269 |  36.5 |    45 |       48 |  51.5 |    58 |  48.17 |             0.4275 |              122 |

### Spread increment distribution (source field)

|   spread_line (home-favoured-by) |   count |    share |
|---------------------------------:|--------:|---------:|
|                            -17   |       1 | 0.003717 |
|                            -14.5 |       2 | 0.007435 |
|                            -14   |       1 | 0.003717 |
|                            -13.5 |       1 | 0.003717 |
|                            -13   |       1 | 0.003717 |
|                            -12   |       1 | 0.003717 |
|                            -11   |       1 | 0.003717 |
|                            -10.5 |       1 | 0.003717 |
|                            -10   |       1 | 0.003717 |
|                             -9.5 |       4 | 0.01487  |
|                             -8.5 |       1 | 0.003717 |
|                             -7.5 |       9 | 0.03346  |
|                             -7   |      11 | 0.04089  |
|                             -6.5 |       4 | 0.01487  |
|                             -6   |       8 | 0.02974  |
|                             -5.5 |       5 | 0.01859  |
|                             -4.5 |       4 | 0.01487  |
|                             -4   |       3 | 0.01115  |
|                             -3.5 |      12 | 0.04461  |
|                             -3   |      20 | 0.07435  |
|                             -2.5 |       8 | 0.02974  |
|                             -2   |       2 | 0.007435 |
|                             -1.5 |       2 | 0.007435 |
|                             -1   |       7 | 0.02602  |
|                              1   |      15 | 0.05576  |
|                              1.5 |       5 | 0.01859  |
|                              2   |       5 | 0.01859  |
|                              2.5 |      11 | 0.04089  |
|                              3   |      19 | 0.07063  |
|                              3.5 |       9 | 0.03346  |
|                              4   |       9 | 0.03346  |
|                              4.5 |       5 | 0.01859  |
|                              5   |       5 | 0.01859  |
|                              5.5 |       4 | 0.01487  |
|                              6   |       6 | 0.0223   |
|                              6.5 |       8 | 0.02974  |
|                              7   |      13 | 0.04833  |
|                              7.5 |      13 | 0.04833  |
|                              8   |       2 | 0.007435 |
|                              8.5 |       3 | 0.01115  |
|                              9.5 |       5 | 0.01859  |
|                             10   |       4 | 0.01487  |
|                             10.5 |       4 | 0.01487  |
|                             11   |       4 | 0.01487  |
|                             12.5 |       2 | 0.007435 |
|                             13   |       2 | 0.007435 |
|                             13.5 |       2 | 0.007435 |
|                             15.5 |       1 | 0.003717 |
|                             16.5 |       1 | 0.003717 |
|                             17.5 |       1 | 0.003717 |
|                             20   |       1 | 0.003717 |

### Leg spread distribution (team perspective)

|   leg spread (team perspective) |   count |    share |
|--------------------------------:|--------:|---------:|
|                           -20   |       1 | 0.001859 |
|                           -17.5 |       1 | 0.001859 |
|                           -17   |       1 | 0.001859 |
|                           -16.5 |       1 | 0.001859 |
|                           -15.5 |       1 | 0.001859 |
|                           -14.5 |       2 | 0.003717 |
|                           -14   |       1 | 0.001859 |
|                           -13.5 |       3 | 0.005576 |
|                           -13   |       3 | 0.005576 |
|                           -12.5 |       2 | 0.003717 |
|                           -12   |       1 | 0.001859 |
|                           -11   |       5 | 0.009294 |
|                           -10.5 |       5 | 0.009294 |
|                           -10   |       5 | 0.009294 |
|                            -9.5 |       9 | 0.01673  |
|                            -8.5 |       4 | 0.007435 |
|                            -8   |       2 | 0.003717 |
|                            -7.5 |      22 | 0.04089  |
|                            -7   |      24 | 0.04461  |
|                            -6.5 |      12 | 0.0223   |
|                            -6   |      14 | 0.02602  |
|                            -5.5 |       9 | 0.01673  |
|                            -5   |       5 | 0.009294 |
|                            -4.5 |       9 | 0.01673  |
|                            -4   |      12 | 0.0223   |
|                            -3.5 |      21 | 0.03903  |
|                            -3   |      39 | 0.07249  |
|                            -2.5 |      19 | 0.03532  |
|                            -2   |       7 | 0.01301  |
|                            -1.5 |       7 | 0.01301  |
|                            -1   |      22 | 0.04089  |
|                             1   |      22 | 0.04089  |
|                             1.5 |       7 | 0.01301  |
|                             2   |       7 | 0.01301  |
|                             2.5 |      19 | 0.03532  |
|                             3   |      39 | 0.07249  |
|                             3.5 |      21 | 0.03903  |
|                             4   |      12 | 0.0223   |
|                             4.5 |       9 | 0.01673  |
|                             5   |       5 | 0.009294 |
|                             5.5 |       9 | 0.01673  |
|                             6   |      14 | 0.02602  |
|                             6.5 |      12 | 0.0223   |
|                             7   |      24 | 0.04461  |
|                             7.5 |      22 | 0.04089  |
|                             8   |       2 | 0.003717 |
|                             8.5 |       4 | 0.007435 |
|                             9.5 |       9 | 0.01673  |
|                            10   |       5 | 0.009294 |
|                            10.5 |       5 | 0.009294 |
|                            11   |       5 | 0.009294 |
|                            12   |       1 | 0.001859 |
|                            12.5 |       2 | 0.003717 |
|                            13   |       3 | 0.005576 |
|                            13.5 |       3 | 0.005576 |
|                            14   |       1 | 0.001859 |
|                            14.5 |       2 | 0.003717 |
|                            15.5 |       1 | 0.001859 |
|                            16.5 |       1 | 0.001859 |
|                            17   |       1 | 0.001859 |
|                            17.5 |       1 | 0.001859 |
|                            20   |       1 | 0.001859 |

### Total line distribution

|   total_line |   count |    share |
|-------------:|--------:|---------:|
|         36.5 |       1 | 0.003717 |
|         39.5 |       1 | 0.003717 |
|         40   |       1 | 0.003717 |
|         40.5 |       1 | 0.003717 |
|         41   |       7 | 0.02602  |
|         41.5 |       6 | 0.0223   |
|         42   |       2 | 0.007435 |
|         42.5 |       7 | 0.02602  |
|         43   |       6 | 0.0223   |
|         43.5 |       8 | 0.02974  |
|         44   |      15 | 0.05576  |
|         44.5 |      10 | 0.03717  |
|         45   |      13 | 0.04833  |
|         45.5 |       4 | 0.01487  |
|         46   |      17 | 0.0632   |
|         46.5 |       7 | 0.02602  |
|         47   |      16 | 0.05948  |
|         47.5 |       5 | 0.01859  |
|         48   |      10 | 0.03717  |
|         48.5 |      10 | 0.03717  |
|         49   |      13 | 0.04833  |
|         49.5 |      15 | 0.05576  |
|         50   |      12 | 0.04461  |
|         50.5 |       5 | 0.01859  |
|         51   |       9 | 0.03346  |
|         51.5 |       7 | 0.02602  |
|         52   |       8 | 0.02974  |
|         52.5 |       9 | 0.03346  |
|         53   |       9 | 0.03346  |
|         53.5 |       3 | 0.01115  |
|         54   |       5 | 0.01859  |
|         54.5 |       4 | 0.01487  |
|         55   |       9 | 0.03346  |
|         55.5 |       8 | 0.02974  |
|         56   |       1 | 0.003717 |
|         56.5 |       4 | 0.01487  |
|         58   |       1 | 0.003717 |

## Thresholds used

These are **pre-registered data-quality gates, not model parameters.** They describe what a dataset must look like to be usable, were fixed before any strategy result was computed, and must never be tuned to make a dataset pass.

|   min_half_point_share |   max_missing_share |   max_season_composition_gap |   max_abs_spread |   min_total |   max_total |
|-----------------------:|--------------------:|-----------------------------:|-----------------:|------------:|------------:|
|                    0.4 |                0.01 |                          0.2 |               30 |          20 |          80 |

## Source and provenance notes

- Source: nflverse/nfldata games.csv (Lee Sharpe) — https://github.com/nflverse/nfldata/blob/master/data/games.csv
- Upstream commit: 4a7ebfde2a7c784255f95c457d8c638a7ca188fa
- Retrieved (UTC): 2026-09-19T15:26:08+00:00
- Raw snapshot: `data/raw/nflverse_nfldata_games.csv` (sha256 `35bc182c6e810955404f8e035228fc6535cce3c39c8ecc0dc8af96715b1cd30f`)
- Line provenance label: **archived_reference_line**. nfldata DATASETS.md documents spread_line/total_line only as 'the spread line for the game' / 'the total line for the game'. It makes no claim about capture time, so the fields cannot be called a close of any kind. Commit-history inspection (reports/nfl_line_composition_investigation.md §2.4) confirms this: the row is refreshed every few hours through game week and freezes at whatever the last refresh captured when the final score lands. The lag to kickoff is irregular and undocumented, and feed dropouts leaving both fields briefly blank were observed.
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

