# Data-Quality Audit — NFL 2022 — nflverse/nfldata

This audit runs **before** any strategy calculation. Its purpose is to decide whether the dataset preserves enough half-point fidelity to test Teaser Model v1.0 at all. It contains no model-performance results of any kind.

**Seasons audited:** 2022

## Verdict

### PASS

The dataset preserves half-point fidelity and is safe to use for v1.0 historical testing, subject to the limitations listed below.

## Checks

| check                                 | status   | critical   | detail                                                                                                                                            |
|:--------------------------------------|:---------|:-----------|:--------------------------------------------------------------------------------------------------------------------------------------------------|
| final_scores_present                  | PASS     | yes        | 0 of 284 games have no final score.                                                                                                               |
| missing_spreads                       | PASS     | yes        | 0 of 284 games missing spread_line (0.000%); gate is <= 1.0%.                                                                                     |
| missing_totals                        | PASS     | yes        | 0 of 284 games missing total_line (0.000%); gate is <= 1.0%.                                                                                      |
| duplicate_games                       | PASS     | yes        | 0 duplicated game_id values; 0 rows duplicating season/week/home/away.                                                                            |
| spreads_on_half_point_grid            | PASS     | yes        | 0 spread values are not multiples of 0.5.                                                                                                         |
| spread_half_point_share               | PASS     | yes        | 139 of 284 spreads end in .5 (48.94%); gate is >= 40%. A source that rounded half-points away would sit near 0%.                                  |
| spread_half_point_share_every_season  | PASS     | yes        | Lowest single-season half-point share is 48.94% in 2022; gate is >= 40%.                                                                          |
| season_composition_consistency        | PASS     | no         | Half-point composition is consistent across seasons.                                                                                              |
| primary_geometry_present              | PASS     | yes        | All four primary shapes appear in the data.                                                                                                       |
| primary_geometry_present_every_season | PASS     | no         | Every primary shape appears in every season.                                                                                                      |
| key_numbers_not_collapsed             | PASS     | yes        | Every whole number present in the data still has its adjacent half-point represented.                                                             |
| total_half_point_share                | PASS     | no         | 134 of 284 totals end in .5 (47.18%). Totals do not gate the model the way spreads do, but a near-zero share would still indicate rounding.       |
| totals_on_half_point_grid             | PASS     | yes        | 0 total values are not multiples of 0.5.                                                                                                          |
| suspicious_rounding_patterns          | PASS     | no         | No suspicious rounding patterns detected.                                                                                                         |
| impossible_values                     | PASS     | yes        | No impossible values found.                                                                                                                       |
| line_provenance_is_honest             | PASS     | no         | Lines are labelled 'archived_reference_line'. 'true_timestamped_close' is only permitted when the source documents a capture time before kickoff. |

## Tables

### Games by season

|   season |   games |
|---------:|--------:|
|     2022 |     284 |

### Games by season and type

|   season | game_type   |   games |
|---------:|:------------|--------:|
|     2022 | CON         |       2 |
|     2022 | DIV         |       4 |
|     2022 | REG         |     271 |
|     2022 | SB          |       1 |
|     2022 | WC          |       6 |

### Half-point share by season

|   season |   spreads |   half_point |   half_point_share |   integer |
|---------:|----------:|-------------:|-------------------:|----------:|
|     2022 |       284 |          139 |             0.4894 |       145 |

### Composition by season

|   season |   spread_half_point_share |   total_half_point_share |
|---------:|--------------------------:|-------------------------:|
|     2022 |                    0.4894 |                   0.4718 |

### Integer vs half-point spreads

| kind            |   count |   share |
|:----------------|--------:|--------:|
| half-point (.5) |     139 |  0.4894 |
| integer (.0)    |     145 |  0.5106 |

### Spread fractional parts

|   fractional_part |   count |
|------------------:|--------:|
|               0   |     145 |
|               0.5 |     139 |

### Primary-geometry leg counts

|   leg_spread |   legs_total |   legs_2022 |
|-------------:|-------------:|------------:|
|          1.5 |            5 |           5 |
|          2.5 |           35 |          35 |
|         -7.5 |           11 |          11 |
|         -8.5 |            6 |           6 |

### Key-number pairs (whole vs half)

|   whole |   count_whole |   adjacent_half |   count_half |
|--------:|--------------:|----------------:|-------------:|
|       2 |             7 |             1.5 |            5 |
|       2 |             7 |             2.5 |           35 |
|       3 |            42 |             2.5 |           35 |
|       3 |            42 |             3.5 |           25 |
|       7 |             8 |             6.5 |           18 |
|       7 |             8 |             7.5 |           11 |
|       8 |             4 |             7.5 |           11 |
|       8 |             4 |             8.5 |            6 |
|       9 |             1 |             8.5 |            6 |

### Total line summary

|   season |   n |   min |   p25 |   median |   p75 |   max |   mean |   half_point_share |   at_or_below_47 |
|---------:|----:|------:|------:|---------:|------:|------:|-------:|-------------------:|-----------------:|
|     2022 | 284 |    32 | 41.38 |       44 |    47 |  54.5 |  44.22 |             0.4718 |              218 |

### Spread increment distribution (source field)

|   spread_line (home-favoured-by) |   count |    share |
|---------------------------------:|--------:|---------:|
|                            -14.5 |       1 | 0.003521 |
|                            -14   |       2 | 0.007042 |
|                            -13   |       1 | 0.003521 |
|                            -11   |       1 | 0.003521 |
|                            -10   |       4 | 0.01408  |
|                             -9   |       1 | 0.003521 |
|                             -8.5 |       2 | 0.007042 |
|                             -8   |       1 | 0.003521 |
|                             -7.5 |       5 | 0.01761  |
|                             -7   |       2 | 0.007042 |
|                             -6.5 |       6 | 0.02113  |
|                             -6   |       6 | 0.02113  |
|                             -5.5 |       4 | 0.01408  |
|                             -4.5 |       1 | 0.003521 |
|                             -4   |       7 | 0.02465  |
|                             -3.5 |      10 | 0.03521  |
|                             -3   |      15 | 0.05282  |
|                             -2.5 |      13 | 0.04577  |
|                             -2   |       4 | 0.01408  |
|                             -1.5 |       2 | 0.007042 |
|                             -1   |      17 | 0.05986  |
|                              1   |      14 | 0.0493   |
|                              1.5 |       3 | 0.01056  |
|                              2   |       3 | 0.01056  |
|                              2.5 |      22 | 0.07746  |
|                              3   |      27 | 0.09507  |
|                              3.5 |      15 | 0.05282  |
|                              4   |       5 | 0.01761  |
|                              4.5 |       9 | 0.03169  |
|                              5   |       3 | 0.01056  |
|                              5.5 |      10 | 0.03521  |
|                              6   |       4 | 0.01408  |
|                              6.5 |      12 | 0.04225  |
|                              7   |       6 | 0.02113  |
|                              7.5 |       6 | 0.02113  |
|                              8   |       3 | 0.01056  |
|                              8.5 |       4 | 0.01408  |
|                              9.5 |       3 | 0.01056  |
|                             10   |       8 | 0.02817  |
|                             10.5 |       8 | 0.02817  |
|                             11   |       4 | 0.01408  |
|                             13   |       1 | 0.003521 |
|                             13.5 |       1 | 0.003521 |
|                             14   |       5 | 0.01761  |
|                             16.5 |       2 | 0.007042 |
|                             17   |       1 | 0.003521 |

### Leg spread distribution (team perspective)

|   leg spread (team perspective) |   count |    share |
|--------------------------------:|--------:|---------:|
|                           -17   |       1 | 0.001761 |
|                           -16.5 |       2 | 0.003521 |
|                           -14.5 |       1 | 0.001761 |
|                           -14   |       7 | 0.01232  |
|                           -13.5 |       1 | 0.001761 |
|                           -13   |       2 | 0.003521 |
|                           -11   |       5 | 0.008803 |
|                           -10.5 |       8 | 0.01408  |
|                           -10   |      12 | 0.02113  |
|                            -9.5 |       3 | 0.005282 |
|                            -9   |       1 | 0.001761 |
|                            -8.5 |       6 | 0.01056  |
|                            -8   |       4 | 0.007042 |
|                            -7.5 |      11 | 0.01937  |
|                            -7   |       8 | 0.01408  |
|                            -6.5 |      18 | 0.03169  |
|                            -6   |      10 | 0.01761  |
|                            -5.5 |      14 | 0.02465  |
|                            -5   |       3 | 0.005282 |
|                            -4.5 |      10 | 0.01761  |
|                            -4   |      12 | 0.02113  |
|                            -3.5 |      25 | 0.04401  |
|                            -3   |      42 | 0.07394  |
|                            -2.5 |      35 | 0.06162  |
|                            -2   |       7 | 0.01232  |
|                            -1.5 |       5 | 0.008803 |
|                            -1   |      31 | 0.05458  |
|                             1   |      31 | 0.05458  |
|                             1.5 |       5 | 0.008803 |
|                             2   |       7 | 0.01232  |
|                             2.5 |      35 | 0.06162  |
|                             3   |      42 | 0.07394  |
|                             3.5 |      25 | 0.04401  |
|                             4   |      12 | 0.02113  |
|                             4.5 |      10 | 0.01761  |
|                             5   |       3 | 0.005282 |
|                             5.5 |      14 | 0.02465  |
|                             6   |      10 | 0.01761  |
|                             6.5 |      18 | 0.03169  |
|                             7   |       8 | 0.01408  |
|                             7.5 |      11 | 0.01937  |
|                             8   |       4 | 0.007042 |
|                             8.5 |       6 | 0.01056  |
|                             9   |       1 | 0.001761 |
|                             9.5 |       3 | 0.005282 |
|                            10   |      12 | 0.02113  |
|                            10.5 |       8 | 0.01408  |
|                            11   |       5 | 0.008803 |
|                            13   |       2 | 0.003521 |
|                            13.5 |       1 | 0.001761 |
|                            14   |       7 | 0.01232  |
|                            14.5 |       1 | 0.001761 |
|                            16.5 |       2 | 0.003521 |
|                            17   |       1 | 0.001761 |

### Total line distribution

|   total_line |   count |    share |
|-------------:|--------:|---------:|
|         32   |       1 | 0.003521 |
|         34   |       1 | 0.003521 |
|         35   |       1 | 0.003521 |
|         35.5 |       1 | 0.003521 |
|         36.5 |       5 | 0.01761  |
|         37   |       2 | 0.007042 |
|         37.5 |       3 | 0.01056  |
|         38   |       5 | 0.01761  |
|         38.5 |       7 | 0.02465  |
|         39   |       4 | 0.01408  |
|         39.5 |       6 | 0.02113  |
|         40   |      14 | 0.0493   |
|         40.5 |      10 | 0.03521  |
|         41   |      11 | 0.03873  |
|         41.5 |      14 | 0.0493   |
|         42   |      14 | 0.0493   |
|         42.5 |       7 | 0.02465  |
|         43   |      16 | 0.05634  |
|         43.5 |      10 | 0.03521  |
|         44   |      21 | 0.07394  |
|         44.5 |      12 | 0.04225  |
|         45   |       8 | 0.02817  |
|         45.5 |      10 | 0.03521  |
|         46   |      17 | 0.05986  |
|         46.5 |       7 | 0.02465  |
|         47   |      11 | 0.03873  |
|         47.5 |       6 | 0.02113  |
|         48   |       6 | 0.02113  |
|         48.5 |      14 | 0.0493   |
|         49   |       7 | 0.02465  |
|         49.5 |       6 | 0.02113  |
|         50   |       2 | 0.007042 |
|         50.5 |       2 | 0.007042 |
|         51   |       2 | 0.007042 |
|         51.5 |       8 | 0.02817  |
|         52   |       2 | 0.007042 |
|         52.5 |       5 | 0.01761  |
|         53   |       1 | 0.003521 |
|         54   |       4 | 0.01408  |
|         54.5 |       1 | 0.003521 |

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

