# Data-Quality Audit — NFL 2019 — nflverse/nfldata

This audit runs **before** any strategy calculation. Its purpose is to decide whether the dataset preserves enough half-point fidelity to test Teaser Model v1.0 at all. It contains no model-performance results of any kind.

**Seasons audited:** 2019

## Verdict

### PASS

The dataset preserves half-point fidelity and is safe to use for v1.0 historical testing, subject to the limitations listed below.

## Checks

| check                                 | status   | critical   | detail                                                                                                                                            |
|:--------------------------------------|:---------|:-----------|:--------------------------------------------------------------------------------------------------------------------------------------------------|
| final_scores_present                  | PASS     | yes        | 0 of 267 games have no final score.                                                                                                               |
| missing_spreads                       | PASS     | yes        | 0 of 267 games missing spread_line (0.000%); gate is <= 1.0%.                                                                                     |
| missing_totals                        | PASS     | yes        | 0 of 267 games missing total_line (0.000%); gate is <= 1.0%.                                                                                      |
| duplicate_games                       | PASS     | yes        | 0 duplicated game_id values; 0 rows duplicating season/week/home/away.                                                                            |
| spreads_on_half_point_grid            | PASS     | yes        | 0 spread values are not multiples of 0.5.                                                                                                         |
| spread_half_point_share               | PASS     | yes        | 124 of 267 spreads end in .5 (46.44%); gate is >= 40%. A source that rounded half-points away would sit near 0%.                                  |
| spread_half_point_share_every_season  | PASS     | yes        | Lowest single-season half-point share is 46.44% in 2019; gate is >= 40%.                                                                          |
| season_composition_consistency        | PASS     | no         | Half-point composition is consistent across seasons.                                                                                              |
| primary_geometry_present              | PASS     | yes        | All four primary shapes appear in the data.                                                                                                       |
| primary_geometry_present_every_season | PASS     | no         | Every primary shape appears in every season.                                                                                                      |
| key_numbers_not_collapsed             | PASS     | yes        | Every whole number present in the data still has its adjacent half-point represented.                                                             |
| total_half_point_share                | WARN     | no         | 101 of 267 totals end in .5 (37.83%). Totals do not gate the model the way spreads do, but a near-zero share would still indicate rounding.       |
| totals_on_half_point_grid             | PASS     | yes        | 0 total values are not multiples of 0.5.                                                                                                          |
| suspicious_rounding_patterns          | PASS     | no         | No suspicious rounding patterns detected.                                                                                                         |
| impossible_values                     | PASS     | yes        | No impossible values found.                                                                                                                       |
| line_provenance_is_honest             | PASS     | no         | Lines are labelled 'archived_reference_line'. 'true_timestamped_close' is only permitted when the source documents a capture time before kickoff. |

### Warnings (non-blocking)

- `total_half_point_share` — 101 of 267 totals end in .5 (37.83%). Totals do not gate the model the way spreads do, but a near-zero share would still indicate rounding.

## Tables

### Games by season

|   season |   games |
|---------:|--------:|
|     2019 |     267 |

### Games by season and type

|   season | game_type   |   games |
|---------:|:------------|--------:|
|     2019 | CON         |       2 |
|     2019 | DIV         |       4 |
|     2019 | REG         |     256 |
|     2019 | SB          |       1 |
|     2019 | WC          |       4 |

### Half-point share by season

|   season |   spreads |   half_point |   half_point_share |   integer |
|---------:|----------:|-------------:|-------------------:|----------:|
|     2019 |       267 |          124 |             0.4644 |       143 |

### Composition by season

|   season |   spread_half_point_share |   total_half_point_share |
|---------:|--------------------------:|-------------------------:|
|     2019 |                    0.4644 |                   0.3783 |

### Integer vs half-point spreads

| kind            |   count |   share |
|:----------------|--------:|--------:|
| half-point (.5) |     124 |  0.4644 |
| integer (.0)    |     143 |  0.5356 |

### Spread fractional parts

|   fractional_part |   count |
|------------------:|--------:|
|               0   |     143 |
|               0.5 |     124 |

### Primary-geometry leg counts

|   leg_spread |   legs_total |   legs_2019 |
|-------------:|-------------:|------------:|
|          1.5 |            7 |           7 |
|          2.5 |           15 |          15 |
|         -7.5 |           10 |          10 |
|         -8.5 |            1 |           1 |

### Key-number pairs (whole vs half)

|   whole |   count_whole |   adjacent_half |   count_half |
|--------:|--------------:|----------------:|-------------:|
|       2 |             5 |             1.5 |            7 |
|       2 |             5 |             2.5 |           15 |
|       3 |            30 |             2.5 |           15 |
|       3 |            30 |             3.5 |           29 |
|       7 |            15 |             6.5 |           12 |
|       7 |            15 |             7.5 |           10 |
|       8 |             4 |             7.5 |           10 |
|       8 |             4 |             8.5 |            1 |
|       9 |             1 |             8.5 |            1 |

### Total line summary

|   season |   n |   min |   p25 |   median |   p75 |   max |   mean |   half_point_share |   at_or_below_47 |
|---------:|----:|------:|------:|---------:|------:|------:|-------:|-------------------:|-----------------:|
|     2019 | 267 |    35 | 42.75 |     45.5 |    48 |  55.5 |  45.22 |             0.3783 |              186 |

### Spread increment distribution (source field)

|   spread_line (home-favoured-by) |   count |    share |
|---------------------------------:|--------:|---------:|
|                            -18   |       1 | 0.003745 |
|                            -15.5 |       1 | 0.003745 |
|                            -15   |       1 | 0.003745 |
|                            -13.5 |       2 | 0.007491 |
|                            -10.5 |       4 | 0.01498  |
|                            -10   |       2 | 0.007491 |
|                             -9.5 |       2 | 0.007491 |
|                             -7.5 |       3 | 0.01124  |
|                             -7   |       7 | 0.02622  |
|                             -6.5 |       6 | 0.02247  |
|                             -6   |       3 | 0.01124  |
|                             -5.5 |       8 | 0.02996  |
|                             -5   |       5 | 0.01873  |
|                             -4.5 |       2 | 0.007491 |
|                             -4   |       7 | 0.02622  |
|                             -3.5 |       9 | 0.03371  |
|                             -3   |      13 | 0.04869  |
|                             -2.5 |       7 | 0.02622  |
|                             -2   |       3 | 0.01124  |
|                             -1.5 |       4 | 0.01498  |
|                             -1   |      11 | 0.0412   |
|                              1   |      14 | 0.05243  |
|                              1.5 |       3 | 0.01124  |
|                              2   |       2 | 0.007491 |
|                              2.5 |       8 | 0.02996  |
|                              3   |      17 | 0.06367  |
|                              3.5 |      20 | 0.07491  |
|                              4   |       9 | 0.03371  |
|                              4.5 |       5 | 0.01873  |
|                              5   |       8 | 0.02996  |
|                              5.5 |      10 | 0.03745  |
|                              6   |       6 | 0.02247  |
|                              6.5 |       6 | 0.02247  |
|                              7   |       8 | 0.02996  |
|                              7.5 |       7 | 0.02622  |
|                              8   |       4 | 0.01498  |
|                              8.5 |       1 | 0.003745 |
|                              9   |       1 | 0.003745 |
|                              9.5 |       4 | 0.01498  |
|                             10   |       7 | 0.02622  |
|                             10.5 |       6 | 0.02247  |
|                             11   |       2 | 0.007491 |
|                             11.5 |       1 | 0.003745 |
|                             12   |       2 | 0.007491 |
|                             12.5 |       1 | 0.003745 |
|                             13   |       4 | 0.01498  |
|                             14   |       3 | 0.01124  |
|                             16.5 |       2 | 0.007491 |
|                             17   |       2 | 0.007491 |
|                             17.5 |       1 | 0.003745 |
|                             20.5 |       1 | 0.003745 |
|                             22   |       1 | 0.003745 |

### Leg spread distribution (team perspective)

|   leg spread (team perspective) |   count |    share |
|--------------------------------:|--------:|---------:|
|                           -22   |       1 | 0.001873 |
|                           -20.5 |       1 | 0.001873 |
|                           -18   |       1 | 0.001873 |
|                           -17.5 |       1 | 0.001873 |
|                           -17   |       2 | 0.003745 |
|                           -16.5 |       2 | 0.003745 |
|                           -15.5 |       1 | 0.001873 |
|                           -15   |       1 | 0.001873 |
|                           -14   |       3 | 0.005618 |
|                           -13.5 |       2 | 0.003745 |
|                           -13   |       4 | 0.007491 |
|                           -12.5 |       1 | 0.001873 |
|                           -12   |       2 | 0.003745 |
|                           -11.5 |       1 | 0.001873 |
|                           -11   |       2 | 0.003745 |
|                           -10.5 |      10 | 0.01873  |
|                           -10   |       9 | 0.01685  |
|                            -9.5 |       6 | 0.01124  |
|                            -9   |       1 | 0.001873 |
|                            -8.5 |       1 | 0.001873 |
|                            -8   |       4 | 0.007491 |
|                            -7.5 |      10 | 0.01873  |
|                            -7   |      15 | 0.02809  |
|                            -6.5 |      12 | 0.02247  |
|                            -6   |       9 | 0.01685  |
|                            -5.5 |      18 | 0.03371  |
|                            -5   |      13 | 0.02434  |
|                            -4.5 |       7 | 0.01311  |
|                            -4   |      16 | 0.02996  |
|                            -3.5 |      29 | 0.05431  |
|                            -3   |      30 | 0.05618  |
|                            -2.5 |      15 | 0.02809  |
|                            -2   |       5 | 0.009363 |
|                            -1.5 |       7 | 0.01311  |
|                            -1   |      25 | 0.04682  |
|                             1   |      25 | 0.04682  |
|                             1.5 |       7 | 0.01311  |
|                             2   |       5 | 0.009363 |
|                             2.5 |      15 | 0.02809  |
|                             3   |      30 | 0.05618  |
|                             3.5 |      29 | 0.05431  |
|                             4   |      16 | 0.02996  |
|                             4.5 |       7 | 0.01311  |
|                             5   |      13 | 0.02434  |
|                             5.5 |      18 | 0.03371  |
|                             6   |       9 | 0.01685  |
|                             6.5 |      12 | 0.02247  |
|                             7   |      15 | 0.02809  |
|                             7.5 |      10 | 0.01873  |
|                             8   |       4 | 0.007491 |
|                             8.5 |       1 | 0.001873 |
|                             9   |       1 | 0.001873 |
|                             9.5 |       6 | 0.01124  |
|                            10   |       9 | 0.01685  |
|                            10.5 |      10 | 0.01873  |
|                            11   |       2 | 0.003745 |
|                            11.5 |       1 | 0.001873 |
|                            12   |       2 | 0.003745 |
|                            12.5 |       1 | 0.001873 |
|                            13   |       4 | 0.007491 |
|                            13.5 |       2 | 0.003745 |
|                            14   |       3 | 0.005618 |
|                            15   |       1 | 0.001873 |
|                            15.5 |       1 | 0.001873 |
|                            16.5 |       2 | 0.003745 |
|                            17   |       2 | 0.003745 |
|                            17.5 |       1 | 0.001873 |
|                            18   |       1 | 0.001873 |
|                            20.5 |       1 | 0.001873 |
|                            22   |       1 | 0.001873 |

### Total line distribution

|   total_line |   count |    share |
|-------------:|--------:|---------:|
|         35   |       1 | 0.003745 |
|         36.5 |       2 | 0.007491 |
|         37   |       6 | 0.02247  |
|         37.5 |       3 | 0.01124  |
|         38   |       4 | 0.01498  |
|         38.5 |       1 | 0.003745 |
|         39   |       4 | 0.01498  |
|         39.5 |       6 | 0.02247  |
|         40   |       4 | 0.01498  |
|         40.5 |       1 | 0.003745 |
|         41   |      11 | 0.0412   |
|         41.5 |       7 | 0.02622  |
|         42   |       9 | 0.03371  |
|         42.5 |       8 | 0.02996  |
|         43   |      17 | 0.06367  |
|         43.5 |       9 | 0.03371  |
|         44   |      17 | 0.06367  |
|         44.5 |       8 | 0.02996  |
|         45   |      11 | 0.0412   |
|         45.5 |      10 | 0.03745  |
|         46   |      19 | 0.07116  |
|         46.5 |       9 | 0.03371  |
|         47   |      19 | 0.07116  |
|         47.5 |       6 | 0.02247  |
|         48   |      14 | 0.05243  |
|         48.5 |      11 | 0.0412   |
|         49   |      14 | 0.05243  |
|         49.5 |       6 | 0.02247  |
|         50   |       6 | 0.02247  |
|         50.5 |       2 | 0.007491 |
|         51   |       6 | 0.02247  |
|         51.5 |       3 | 0.01124  |
|         52   |       3 | 0.01124  |
|         52.5 |       4 | 0.01498  |
|         53   |       1 | 0.003745 |
|         53.5 |       1 | 0.003745 |
|         54.5 |       3 | 0.01124  |
|         55.5 |       1 | 0.003745 |

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

