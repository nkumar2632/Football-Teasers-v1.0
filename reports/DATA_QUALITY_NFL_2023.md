# Data-Quality Audit — NFL 2023 — nflverse/nfldata

This audit runs **before** any strategy calculation. Its purpose is to decide whether the dataset preserves enough half-point fidelity to test Teaser Model v1.0 at all. It contains no model-performance results of any kind.

**Seasons audited:** 2023

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
| spread_half_point_share               | PASS     | yes        | 147 of 285 spreads end in .5 (51.58%); gate is >= 40%. A source that rounded half-points away would sit near 0%.                                  |
| spread_half_point_share_every_season  | PASS     | yes        | Lowest single-season half-point share is 51.58% in 2023; gate is >= 40%.                                                                          |
| season_composition_consistency        | PASS     | no         | Half-point composition is consistent across seasons.                                                                                              |
| primary_geometry_present              | PASS     | yes        | All four primary shapes appear in the data.                                                                                                       |
| primary_geometry_present_every_season | PASS     | no         | Every primary shape appears in every season.                                                                                                      |
| key_numbers_not_collapsed             | PASS     | yes        | Every whole number present in the data still has its adjacent half-point represented.                                                             |
| total_half_point_share                | PASS     | no         | 156 of 285 totals end in .5 (54.74%). Totals do not gate the model the way spreads do, but a near-zero share would still indicate rounding.       |
| totals_on_half_point_grid             | PASS     | yes        | 0 total values are not multiples of 0.5.                                                                                                          |
| suspicious_rounding_patterns          | PASS     | no         | No suspicious rounding patterns detected.                                                                                                         |
| impossible_values                     | PASS     | yes        | No impossible values found.                                                                                                                       |
| line_provenance_is_honest             | PASS     | no         | Lines are labelled 'archived_reference_line'. 'true_timestamped_close' is only permitted when the source documents a capture time before kickoff. |

## Tables

### Games by season

|   season |   games |
|---------:|--------:|
|     2023 |     285 |

### Games by season and type

|   season | game_type   |   games |
|---------:|:------------|--------:|
|     2023 | CON         |       2 |
|     2023 | DIV         |       4 |
|     2023 | REG         |     272 |
|     2023 | SB          |       1 |
|     2023 | WC          |       6 |

### Half-point share by season

|   season |   spreads |   half_point |   half_point_share |   integer |
|---------:|----------:|-------------:|-------------------:|----------:|
|     2023 |       285 |          147 |             0.5158 |       138 |

### Composition by season

|   season |   spread_half_point_share |   total_half_point_share |
|---------:|--------------------------:|-------------------------:|
|     2023 |                    0.5158 |                   0.5474 |

### Integer vs half-point spreads

| kind            |   count |   share |
|:----------------|--------:|--------:|
| half-point (.5) |     147 |  0.5158 |
| integer (.0)    |     138 |  0.4842 |

### Spread fractional parts

|   fractional_part |   count |
|------------------:|--------:|
|               0   |     138 |
|               0.5 |     147 |

### Primary-geometry leg counts

|   leg_spread |   legs_total |   legs_2023 |
|-------------:|-------------:|------------:|
|          1.5 |           14 |          14 |
|          2.5 |           37 |          37 |
|         -7.5 |           13 |          13 |
|         -8.5 |            3 |           3 |

### Key-number pairs (whole vs half)

|   whole |   count_whole |   adjacent_half |   count_half |
|--------:|--------------:|----------------:|-------------:|
|       2 |            11 |             1.5 |           14 |
|       2 |            11 |             2.5 |           37 |
|       3 |            48 |             2.5 |           37 |
|       3 |            48 |             3.5 |           31 |
|       7 |            10 |             6.5 |            7 |
|       7 |            10 |             7.5 |           13 |
|       8 |             2 |             7.5 |           13 |
|       8 |             2 |             8.5 |            3 |
|       9 |             2 |             8.5 |            3 |

### Total line summary

|   season |   n |   min |   p25 |   median |   p75 |   max |   mean |   half_point_share |   at_or_below_47 |
|---------:|----:|------:|------:|---------:|------:|------:|-------:|-------------------:|-----------------:|
|     2023 | 285 |  28.5 |    40 |     43.5 |    46 |    54 |  43.13 |             0.5474 |              228 |

### Spread increment distribution (source field)

|   spread_line (home-favoured-by) |   count |    share |
|---------------------------------:|--------:|---------:|
|                            -14   |       1 | 0.003509 |
|                            -13   |       2 | 0.007018 |
|                            -12.5 |       1 | 0.003509 |
|                            -11.5 |       1 | 0.003509 |
|                            -11   |       1 | 0.003509 |
|                            -10   |       1 | 0.003509 |
|                             -9.5 |       4 | 0.01404  |
|                             -9   |       1 | 0.003509 |
|                             -8.5 |       1 | 0.003509 |
|                             -7.5 |       2 | 0.007018 |
|                             -7   |       4 | 0.01404  |
|                             -6.5 |       1 | 0.003509 |
|                             -6   |       3 | 0.01053  |
|                             -5.5 |       3 | 0.01053  |
|                             -5   |       3 | 0.01053  |
|                             -4.5 |       5 | 0.01754  |
|                             -4   |       3 | 0.01053  |
|                             -3.5 |       9 | 0.03158  |
|                             -3   |      23 | 0.0807   |
|                             -2.5 |      17 | 0.05965  |
|                             -2   |       9 | 0.03158  |
|                             -1.5 |       7 | 0.02456  |
|                             -1   |       7 | 0.02456  |
|                              1   |       6 | 0.02105  |
|                              1.5 |       7 | 0.02456  |
|                              2   |       2 | 0.007018 |
|                              2.5 |      20 | 0.07018  |
|                              3   |      25 | 0.08772  |
|                              3.5 |      22 | 0.07719  |
|                              4   |      11 | 0.0386   |
|                              4.5 |       6 | 0.02105  |
|                              5   |       2 | 0.007018 |
|                              5.5 |       8 | 0.02807  |
|                              6   |      10 | 0.03509  |
|                              6.5 |       6 | 0.02105  |
|                              7   |       6 | 0.02105  |
|                              7.5 |      11 | 0.0386   |
|                              8   |       2 | 0.007018 |
|                              8.5 |       2 | 0.007018 |
|                              9   |       1 | 0.003509 |
|                              9.5 |       6 | 0.02105  |
|                             10   |       4 | 0.01404  |
|                             10.5 |       3 | 0.01053  |
|                             11   |       1 | 0.003509 |
|                             12   |       1 | 0.003509 |
|                             12.5 |       1 | 0.003509 |
|                             13   |       3 | 0.01053  |
|                             13.5 |       1 | 0.003509 |
|                             14   |       4 | 0.01404  |
|                             14.5 |       1 | 0.003509 |
|                             15   |       2 | 0.007018 |
|                             15.5 |       1 | 0.003509 |
|                             17.5 |       1 | 0.003509 |

### Leg spread distribution (team perspective)

|   leg spread (team perspective) |   count |    share |
|--------------------------------:|--------:|---------:|
|                           -17.5 |       1 | 0.001754 |
|                           -15.5 |       1 | 0.001754 |
|                           -15   |       2 | 0.003509 |
|                           -14.5 |       1 | 0.001754 |
|                           -14   |       5 | 0.008772 |
|                           -13.5 |       1 | 0.001754 |
|                           -13   |       5 | 0.008772 |
|                           -12.5 |       2 | 0.003509 |
|                           -12   |       1 | 0.001754 |
|                           -11.5 |       1 | 0.001754 |
|                           -11   |       2 | 0.003509 |
|                           -10.5 |       3 | 0.005263 |
|                           -10   |       5 | 0.008772 |
|                            -9.5 |      10 | 0.01754  |
|                            -9   |       2 | 0.003509 |
|                            -8.5 |       3 | 0.005263 |
|                            -8   |       2 | 0.003509 |
|                            -7.5 |      13 | 0.02281  |
|                            -7   |      10 | 0.01754  |
|                            -6.5 |       7 | 0.01228  |
|                            -6   |      13 | 0.02281  |
|                            -5.5 |      11 | 0.0193   |
|                            -5   |       5 | 0.008772 |
|                            -4.5 |      11 | 0.0193   |
|                            -4   |      14 | 0.02456  |
|                            -3.5 |      31 | 0.05439  |
|                            -3   |      48 | 0.08421  |
|                            -2.5 |      37 | 0.06491  |
|                            -2   |      11 | 0.0193   |
|                            -1.5 |      14 | 0.02456  |
|                            -1   |      13 | 0.02281  |
|                             1   |      13 | 0.02281  |
|                             1.5 |      14 | 0.02456  |
|                             2   |      11 | 0.0193   |
|                             2.5 |      37 | 0.06491  |
|                             3   |      48 | 0.08421  |
|                             3.5 |      31 | 0.05439  |
|                             4   |      14 | 0.02456  |
|                             4.5 |      11 | 0.0193   |
|                             5   |       5 | 0.008772 |
|                             5.5 |      11 | 0.0193   |
|                             6   |      13 | 0.02281  |
|                             6.5 |       7 | 0.01228  |
|                             7   |      10 | 0.01754  |
|                             7.5 |      13 | 0.02281  |
|                             8   |       2 | 0.003509 |
|                             8.5 |       3 | 0.005263 |
|                             9   |       2 | 0.003509 |
|                             9.5 |      10 | 0.01754  |
|                            10   |       5 | 0.008772 |
|                            10.5 |       3 | 0.005263 |
|                            11   |       2 | 0.003509 |
|                            11.5 |       1 | 0.001754 |
|                            12   |       1 | 0.001754 |
|                            12.5 |       2 | 0.003509 |
|                            13   |       5 | 0.008772 |
|                            13.5 |       1 | 0.001754 |
|                            14   |       5 | 0.008772 |
|                            14.5 |       1 | 0.001754 |
|                            15   |       2 | 0.003509 |
|                            15.5 |       1 | 0.001754 |
|                            17.5 |       1 | 0.001754 |

### Total line distribution

|   total_line |   count |    share |
|-------------:|--------:|---------:|
|         28.5 |       1 | 0.003509 |
|         30   |       1 | 0.003509 |
|         32   |       1 | 0.003509 |
|         33   |       1 | 0.003509 |
|         33.5 |       2 | 0.007018 |
|         34   |       2 | 0.007018 |
|         35   |       3 | 0.01053  |
|         35.5 |       2 | 0.007018 |
|         36   |       5 | 0.01754  |
|         36.5 |       3 | 0.01053  |
|         37   |       4 | 0.01404  |
|         37.5 |       6 | 0.02105  |
|         38   |       8 | 0.02807  |
|         38.5 |      12 | 0.04211  |
|         39   |       4 | 0.01404  |
|         39.5 |      12 | 0.04211  |
|         40   |       8 | 0.02807  |
|         40.5 |       6 | 0.02105  |
|         41   |      12 | 0.04211  |
|         41.5 |      14 | 0.04912  |
|         42   |       9 | 0.03158  |
|         42.5 |      11 | 0.0386   |
|         43   |      10 | 0.03509  |
|         43.5 |      20 | 0.07018  |
|         44   |      13 | 0.04561  |
|         44.5 |      14 | 0.04912  |
|         45   |      14 | 0.04912  |
|         45.5 |      11 | 0.0386   |
|         46   |       6 | 0.02105  |
|         46.5 |       8 | 0.02807  |
|         47   |       5 | 0.01754  |
|         47.5 |      16 | 0.05614  |
|         48   |       9 | 0.03158  |
|         48.5 |       5 | 0.01754  |
|         49   |       6 | 0.02105  |
|         49.5 |       4 | 0.01404  |
|         50   |       1 | 0.003509 |
|         50.5 |       4 | 0.01404  |
|         51   |       2 | 0.007018 |
|         52   |       1 | 0.003509 |
|         52.5 |       5 | 0.01754  |
|         53   |       3 | 0.01053  |
|         54   |       1 | 0.003509 |

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

