# Data-Quality Audit — NFL 2021 — nflverse/nfldata

This audit runs **before** any strategy calculation. Its purpose is to decide whether the dataset preserves enough half-point fidelity to test Teaser Model v1.0 at all. It contains no model-performance results of any kind.

**Seasons audited:** 2021

## Verdict

### PASS

The dataset preserves half-point fidelity and is safe to use for v1.0 historical testing, subject to the limitations listed below.

## Checks

| check                                 | status   | critical   | detail                                                                                                                                            |
|:--------------------------------------|:---------|:-----------|:--------------------------------------------------------------------------------------------------------------------------------------------------|
| final_scores_present                  | PASS     | yes        | 0 of 285 games have no final score.                                                                                                               |
| missing_spreads                       | PASS     | yes        | 0 of 285 games missing spread_line (0.000%); gate is <= 1.0%.                                                                                     |
| missing_totals                        | PASS     | yes        | 0 of 285 games missing total_line (0.000%); gate is <= 1.0%.                                                                                      |
| duplicate_games                       | PASS     | yes        | 0 duplicated game_id values; 0 rows duplicating season/week/home/away.                                                                            |
| spreads_on_half_point_grid            | PASS     | yes        | 0 spread values are not multiples of 0.5.                                                                                                         |
| spread_half_point_share               | PASS     | yes        | 144 of 285 spreads end in .5 (50.53%); gate is >= 40%. A source that rounded half-points away would sit near 0%.                                  |
| spread_half_point_share_every_season  | PASS     | yes        | Lowest single-season half-point share is 50.53% in 2021; gate is >= 40%.                                                                          |
| season_composition_consistency        | PASS     | no         | Half-point composition is consistent across seasons.                                                                                              |
| primary_geometry_present              | PASS     | yes        | All four primary shapes appear in the data.                                                                                                       |
| primary_geometry_present_every_season | PASS     | no         | Every primary shape appears in every season.                                                                                                      |
| key_numbers_not_collapsed             | PASS     | yes        | Every whole number present in the data still has its adjacent half-point represented.                                                             |
| total_half_point_share                | PASS     | no         | 122 of 285 totals end in .5 (42.81%). Totals do not gate the model the way spreads do, but a near-zero share would still indicate rounding.       |
| totals_on_half_point_grid             | PASS     | yes        | 0 total values are not multiples of 0.5.                                                                                                          |
| suspicious_rounding_patterns          | PASS     | no         | No suspicious rounding patterns detected.                                                                                                         |
| impossible_values                     | PASS     | yes        | No impossible values found.                                                                                                                       |
| line_provenance_is_honest             | PASS     | no         | Lines are labelled 'archived_reference_line'. 'true_timestamped_close' is only permitted when the source documents a capture time before kickoff. |

## Tables

### Games by season

|   season |   games |
|---------:|--------:|
|     2021 |     285 |

### Games by season and type

|   season | game_type   |   games |
|---------:|:------------|--------:|
|     2021 | CON         |       2 |
|     2021 | DIV         |       4 |
|     2021 | REG         |     272 |
|     2021 | SB          |       1 |
|     2021 | WC          |       6 |

### Half-point share by season

|   season |   spreads |   half_point |   half_point_share |   integer |
|---------:|----------:|-------------:|-------------------:|----------:|
|     2021 |       285 |          144 |             0.5053 |       141 |

### Composition by season

|   season |   spread_half_point_share |   total_half_point_share |
|---------:|--------------------------:|-------------------------:|
|     2021 |                    0.5053 |                   0.4281 |

### Integer vs half-point spreads

| kind            |   count |   share |
|:----------------|--------:|--------:|
| half-point (.5) |     144 |  0.5053 |
| integer (.0)    |     141 |  0.4947 |

### Spread fractional parts

|   fractional_part |   count |
|------------------:|--------:|
|               0   |     141 |
|               0.5 |     144 |

### Primary-geometry leg counts

|   leg_spread |   legs_total |   legs_2021 |
|-------------:|-------------:|------------:|
|          1.5 |            2 |           2 |
|          2.5 |           26 |          26 |
|         -7.5 |           18 |          18 |
|         -8.5 |            6 |           6 |

### Key-number pairs (whole vs half)

|   whole |   count_whole |   adjacent_half |   count_half |
|--------:|--------------:|----------------:|-------------:|
|       2 |             7 |             1.5 |            2 |
|       2 |             7 |             2.5 |           26 |
|       3 |            37 |             2.5 |           26 |
|       3 |            37 |             3.5 |           27 |
|       7 |            17 |             6.5 |           13 |
|       7 |            17 |             7.5 |           18 |
|       8 |             5 |             7.5 |           18 |
|       8 |             5 |             8.5 |            6 |
|       9 |             1 |             8.5 |            6 |

### Total line summary

|   season |   n |   min |   p25 |   median |   p75 |   max |   mean |   half_point_share |   at_or_below_47 |
|---------:|----:|------:|------:|---------:|------:|------:|-------:|-------------------:|-----------------:|
|     2021 | 285 |    36 |  43.5 |       46 |    49 |  57.5 |  46.54 |             0.4281 |              167 |

### Spread increment distribution (source field)

|   spread_line (home-favoured-by) |   count |    share |
|---------------------------------:|--------:|---------:|
|                            -17   |       1 | 0.003509 |
|                            -14.5 |       2 | 0.007018 |
|                            -14   |       1 | 0.003509 |
|                            -13.5 |       1 | 0.003509 |
|                            -13   |       2 | 0.007018 |
|                            -11.5 |       4 | 0.01404  |
|                            -11   |       1 | 0.003509 |
|                            -10.5 |       1 | 0.003509 |
|                            -10   |       3 | 0.01053  |
|                             -9.5 |       2 | 0.007018 |
|                             -8.5 |       1 | 0.003509 |
|                             -8   |       3 | 0.01053  |
|                             -7.5 |       4 | 0.01404  |
|                             -7   |       6 | 0.02105  |
|                             -6.5 |       4 | 0.01404  |
|                             -6   |       8 | 0.02807  |
|                             -5.5 |       3 | 0.01053  |
|                             -5   |       2 | 0.007018 |
|                             -4.5 |       4 | 0.01404  |
|                             -4   |       8 | 0.02807  |
|                             -3.5 |      12 | 0.04211  |
|                             -3   |      14 | 0.04912  |
|                             -2.5 |       7 | 0.02456  |
|                             -2   |       5 | 0.01754  |
|                             -1.5 |       2 | 0.007018 |
|                             -1   |      11 | 0.0386   |
|                              1   |       6 | 0.02105  |
|                              2   |       2 | 0.007018 |
|                              2.5 |      19 | 0.06667  |
|                              3   |      23 | 0.0807   |
|                              3.5 |      15 | 0.05263  |
|                              4   |       8 | 0.02807  |
|                              4.5 |       4 | 0.01404  |
|                              5   |       1 | 0.003509 |
|                              5.5 |       9 | 0.03158  |
|                              6   |       3 | 0.01053  |
|                              6.5 |       9 | 0.03158  |
|                              7   |      11 | 0.0386   |
|                              7.5 |      14 | 0.04912  |
|                              8   |       2 | 0.007018 |
|                              8.5 |       5 | 0.01754  |
|                              9   |       1 | 0.003509 |
|                              9.5 |       3 | 0.01053  |
|                             10   |       4 | 0.01404  |
|                             10.5 |      10 | 0.03509  |
|                             11   |       3 | 0.01053  |
|                             11.5 |       4 | 0.01404  |
|                             12.5 |       1 | 0.003509 |
|                             13   |       4 | 0.01404  |
|                             13.5 |       2 | 0.007018 |
|                             14   |       4 | 0.01404  |
|                             15   |       1 | 0.003509 |
|                             16   |       1 | 0.003509 |
|                             17   |       1 | 0.003509 |
|                             17.5 |       1 | 0.003509 |
|                             19   |       1 | 0.003509 |
|                             20.5 |       1 | 0.003509 |

### Leg spread distribution (team perspective)

|   leg spread (team perspective) |   count |    share |
|--------------------------------:|--------:|---------:|
|                           -20.5 |       1 | 0.001754 |
|                           -19   |       1 | 0.001754 |
|                           -17.5 |       1 | 0.001754 |
|                           -17   |       2 | 0.003509 |
|                           -16   |       1 | 0.001754 |
|                           -15   |       1 | 0.001754 |
|                           -14.5 |       2 | 0.003509 |
|                           -14   |       5 | 0.008772 |
|                           -13.5 |       3 | 0.005263 |
|                           -13   |       6 | 0.01053  |
|                           -12.5 |       1 | 0.001754 |
|                           -11.5 |       8 | 0.01404  |
|                           -11   |       4 | 0.007018 |
|                           -10.5 |      11 | 0.0193   |
|                           -10   |       7 | 0.01228  |
|                            -9.5 |       5 | 0.008772 |
|                            -9   |       1 | 0.001754 |
|                            -8.5 |       6 | 0.01053  |
|                            -8   |       5 | 0.008772 |
|                            -7.5 |      18 | 0.03158  |
|                            -7   |      17 | 0.02982  |
|                            -6.5 |      13 | 0.02281  |
|                            -6   |      11 | 0.0193   |
|                            -5.5 |      12 | 0.02105  |
|                            -5   |       3 | 0.005263 |
|                            -4.5 |       8 | 0.01404  |
|                            -4   |      16 | 0.02807  |
|                            -3.5 |      27 | 0.04737  |
|                            -3   |      37 | 0.06491  |
|                            -2.5 |      26 | 0.04561  |
|                            -2   |       7 | 0.01228  |
|                            -1.5 |       2 | 0.003509 |
|                            -1   |      17 | 0.02982  |
|                             1   |      17 | 0.02982  |
|                             1.5 |       2 | 0.003509 |
|                             2   |       7 | 0.01228  |
|                             2.5 |      26 | 0.04561  |
|                             3   |      37 | 0.06491  |
|                             3.5 |      27 | 0.04737  |
|                             4   |      16 | 0.02807  |
|                             4.5 |       8 | 0.01404  |
|                             5   |       3 | 0.005263 |
|                             5.5 |      12 | 0.02105  |
|                             6   |      11 | 0.0193   |
|                             6.5 |      13 | 0.02281  |
|                             7   |      17 | 0.02982  |
|                             7.5 |      18 | 0.03158  |
|                             8   |       5 | 0.008772 |
|                             8.5 |       6 | 0.01053  |
|                             9   |       1 | 0.001754 |
|                             9.5 |       5 | 0.008772 |
|                            10   |       7 | 0.01228  |
|                            10.5 |      11 | 0.0193   |
|                            11   |       4 | 0.007018 |
|                            11.5 |       8 | 0.01404  |
|                            12.5 |       1 | 0.001754 |
|                            13   |       6 | 0.01053  |
|                            13.5 |       3 | 0.005263 |
|                            14   |       5 | 0.008772 |
|                            14.5 |       2 | 0.003509 |
|                            15   |       1 | 0.001754 |
|                            16   |       1 | 0.001754 |
|                            17   |       2 | 0.003509 |
|                            17.5 |       1 | 0.001754 |
|                            19   |       1 | 0.001754 |
|                            20.5 |       1 | 0.001754 |

### Total line distribution

|   total_line |   count |    share |
|-------------:|--------:|---------:|
|         36   |       1 | 0.003509 |
|         36.5 |       1 | 0.003509 |
|         37   |       1 | 0.003509 |
|         37.5 |       1 | 0.003509 |
|         38   |       1 | 0.003509 |
|         39.5 |       2 | 0.007018 |
|         40   |       7 | 0.02456  |
|         40.5 |       2 | 0.007018 |
|         41   |       8 | 0.02807  |
|         41.5 |       6 | 0.02105  |
|         42   |      11 | 0.0386   |
|         42.5 |       6 | 0.02105  |
|         43   |      20 | 0.07018  |
|         43.5 |       8 | 0.02807  |
|         44   |      12 | 0.04211  |
|         44.5 |      13 | 0.04561  |
|         45   |      12 | 0.04211  |
|         45.5 |      18 | 0.06316  |
|         46   |      13 | 0.04561  |
|         46.5 |      10 | 0.03509  |
|         47   |      14 | 0.04912  |
|         47.5 |      10 | 0.03509  |
|         48   |      22 | 0.07719  |
|         48.5 |      10 | 0.03509  |
|         49   |       7 | 0.02456  |
|         49.5 |      11 | 0.0386   |
|         50   |       3 | 0.01053  |
|         50.5 |       6 | 0.02105  |
|         51   |      12 | 0.04211  |
|         51.5 |       3 | 0.01053  |
|         52   |       4 | 0.01404  |
|         52.5 |       2 | 0.007018 |
|         53   |       5 | 0.01754  |
|         53.5 |      10 | 0.03509  |
|         54   |       4 | 0.01404  |
|         54.5 |       2 | 0.007018 |
|         55   |       4 | 0.01404  |
|         56   |       1 | 0.003509 |
|         57   |       1 | 0.003509 |
|         57.5 |       1 | 0.003509 |

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

