# Data-Quality Audit — NFL 2018 — nflverse/nfldata

This audit runs **before** any strategy calculation. Its purpose is to decide whether the dataset preserves enough half-point fidelity to test Teaser Model v1.0 at all. It contains no model-performance results of any kind.

**Seasons audited:** 2018

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
| spread_half_point_share               | PASS     | yes        | 131 of 267 spreads end in .5 (49.06%); gate is >= 40%. A source that rounded half-points away would sit near 0%.                                  |
| spread_half_point_share_every_season  | PASS     | yes        | Lowest single-season half-point share is 49.06% in 2018; gate is >= 40%.                                                                          |
| season_composition_consistency        | PASS     | no         | Half-point composition is consistent across seasons.                                                                                              |
| primary_geometry_present              | PASS     | yes        | All four primary shapes appear in the data.                                                                                                       |
| primary_geometry_present_every_season | PASS     | no         | Every primary shape appears in every season.                                                                                                      |
| key_numbers_not_collapsed             | PASS     | yes        | Every whole number present in the data still has its adjacent half-point represented.                                                             |
| total_half_point_share                | PASS     | no         | 124 of 267 totals end in .5 (46.44%). Totals do not gate the model the way spreads do, but a near-zero share would still indicate rounding.       |
| totals_on_half_point_grid             | PASS     | yes        | 0 total values are not multiples of 0.5.                                                                                                          |
| suspicious_rounding_patterns          | PASS     | no         | No suspicious rounding patterns detected.                                                                                                         |
| impossible_values                     | PASS     | yes        | No impossible values found.                                                                                                                       |
| line_provenance_is_honest             | PASS     | no         | Lines are labelled 'archived_reference_line'. 'true_timestamped_close' is only permitted when the source documents a capture time before kickoff. |

## Tables

### Games by season

|   season |   games |
|---------:|--------:|
|     2018 |     267 |

### Games by season and type

|   season | game_type   |   games |
|---------:|:------------|--------:|
|     2018 | CON         |       2 |
|     2018 | DIV         |       4 |
|     2018 | REG         |     256 |
|     2018 | SB          |       1 |
|     2018 | WC          |       4 |

### Half-point share by season

|   season |   spreads |   half_point |   half_point_share |   integer |
|---------:|----------:|-------------:|-------------------:|----------:|
|     2018 |       267 |          131 |             0.4906 |       136 |

### Composition by season

|   season |   spread_half_point_share |   total_half_point_share |
|---------:|--------------------------:|-------------------------:|
|     2018 |                    0.4906 |                   0.4644 |

### Integer vs half-point spreads

| kind            |   count |   share |
|:----------------|--------:|--------:|
| half-point (.5) |     131 |  0.4906 |
| integer (.0)    |     136 |  0.5094 |

### Spread fractional parts

|   fractional_part |   count |
|------------------:|--------:|
|               0   |     136 |
|               0.5 |     131 |

### Primary-geometry leg counts

|   leg_spread |   legs_total |   legs_2018 |
|-------------:|-------------:|------------:|
|          1.5 |            7 |           7 |
|          2.5 |           23 |          23 |
|         -7.5 |           18 |          18 |
|         -8.5 |            8 |           8 |

### Key-number pairs (whole vs half)

|   whole |   count_whole |   adjacent_half |   count_half |
|--------:|--------------:|----------------:|-------------:|
|       2 |             6 |             1.5 |            7 |
|       2 |             6 |             2.5 |           23 |
|       3 |            39 |             2.5 |           23 |
|       3 |            39 |             3.5 |           27 |
|       7 |            13 |             6.5 |           12 |
|       7 |            13 |             7.5 |           18 |
|       8 |             2 |             7.5 |           18 |
|       8 |             2 |             8.5 |            8 |
|       9 |             2 |             8.5 |            8 |

### Total line summary

|   season |   n |   min |   p25 |   median |   p75 |   max |   mean |   half_point_share |   at_or_below_47 |
|---------:|----:|------:|------:|---------:|------:|------:|-------:|-------------------:|-----------------:|
|     2018 | 267 |    36 |    43 |     46.5 |    50 |  63.5 |  46.65 |             0.4644 |              155 |

### Spread increment distribution (source field)

|   spread_line (home-favoured-by) |   count |    share |
|---------------------------------:|--------:|---------:|
|                            -14.5 |       1 | 0.003745 |
|                            -14   |       1 | 0.003745 |
|                            -13.5 |       1 | 0.003745 |
|                            -13   |       1 | 0.003745 |
|                            -10.5 |       4 | 0.01498  |
|                             -8.5 |       2 | 0.007491 |
|                             -8   |       1 | 0.003745 |
|                             -7.5 |       4 | 0.01498  |
|                             -7   |       5 | 0.01873  |
|                             -6.5 |       1 | 0.003745 |
|                             -6   |       6 | 0.02247  |
|                             -5.5 |       2 | 0.007491 |
|                             -5   |       1 | 0.003745 |
|                             -4   |       4 | 0.01498  |
|                             -3.5 |      12 | 0.04494  |
|                             -3   |      14 | 0.05243  |
|                             -2.5 |      13 | 0.04869  |
|                             -2   |       3 | 0.01124  |
|                             -1.5 |       3 | 0.01124  |
|                             -1   |      11 | 0.0412   |
|                              1   |      11 | 0.0412   |
|                              1.5 |       4 | 0.01498  |
|                              2   |       3 | 0.01124  |
|                              2.5 |      10 | 0.03745  |
|                              3   |      25 | 0.09363  |
|                              3.5 |      15 | 0.05618  |
|                              4   |       8 | 0.02996  |
|                              4.5 |       7 | 0.02622  |
|                              5   |       4 | 0.01498  |
|                              5.5 |       8 | 0.02996  |
|                              6   |      10 | 0.03745  |
|                              6.5 |      11 | 0.0412   |
|                              7   |       8 | 0.02996  |
|                              7.5 |      14 | 0.05243  |
|                              8   |       1 | 0.003745 |
|                              8.5 |       6 | 0.02247  |
|                              9   |       2 | 0.007491 |
|                             10   |      10 | 0.03745  |
|                             10.5 |       4 | 0.01498  |
|                             11.5 |       1 | 0.003745 |
|                             12.5 |       1 | 0.003745 |
|                             13   |       2 | 0.007491 |
|                             13.5 |       3 | 0.01124  |
|                             14   |       4 | 0.01498  |
|                             14.5 |       1 | 0.003745 |
|                             15.5 |       1 | 0.003745 |
|                             16.5 |       2 | 0.007491 |
|                             17   |       1 | 0.003745 |

### Leg spread distribution (team perspective)

|   leg spread (team perspective) |   count |    share |
|--------------------------------:|--------:|---------:|
|                           -17   |       1 | 0.001873 |
|                           -16.5 |       2 | 0.003745 |
|                           -15.5 |       1 | 0.001873 |
|                           -14.5 |       2 | 0.003745 |
|                           -14   |       5 | 0.009363 |
|                           -13.5 |       4 | 0.007491 |
|                           -13   |       3 | 0.005618 |
|                           -12.5 |       1 | 0.001873 |
|                           -11.5 |       1 | 0.001873 |
|                           -10.5 |       8 | 0.01498  |
|                           -10   |      10 | 0.01873  |
|                            -9   |       2 | 0.003745 |
|                            -8.5 |       8 | 0.01498  |
|                            -8   |       2 | 0.003745 |
|                            -7.5 |      18 | 0.03371  |
|                            -7   |      13 | 0.02434  |
|                            -6.5 |      12 | 0.02247  |
|                            -6   |      16 | 0.02996  |
|                            -5.5 |      10 | 0.01873  |
|                            -5   |       5 | 0.009363 |
|                            -4.5 |       7 | 0.01311  |
|                            -4   |      12 | 0.02247  |
|                            -3.5 |      27 | 0.05056  |
|                            -3   |      39 | 0.07303  |
|                            -2.5 |      23 | 0.04307  |
|                            -2   |       6 | 0.01124  |
|                            -1.5 |       7 | 0.01311  |
|                            -1   |      22 | 0.0412   |
|                             1   |      22 | 0.0412   |
|                             1.5 |       7 | 0.01311  |
|                             2   |       6 | 0.01124  |
|                             2.5 |      23 | 0.04307  |
|                             3   |      39 | 0.07303  |
|                             3.5 |      27 | 0.05056  |
|                             4   |      12 | 0.02247  |
|                             4.5 |       7 | 0.01311  |
|                             5   |       5 | 0.009363 |
|                             5.5 |      10 | 0.01873  |
|                             6   |      16 | 0.02996  |
|                             6.5 |      12 | 0.02247  |
|                             7   |      13 | 0.02434  |
|                             7.5 |      18 | 0.03371  |
|                             8   |       2 | 0.003745 |
|                             8.5 |       8 | 0.01498  |
|                             9   |       2 | 0.003745 |
|                            10   |      10 | 0.01873  |
|                            10.5 |       8 | 0.01498  |
|                            11.5 |       1 | 0.001873 |
|                            12.5 |       1 | 0.001873 |
|                            13   |       3 | 0.005618 |
|                            13.5 |       4 | 0.007491 |
|                            14   |       5 | 0.009363 |
|                            14.5 |       2 | 0.003745 |
|                            15.5 |       1 | 0.001873 |
|                            16.5 |       2 | 0.003745 |
|                            17   |       1 | 0.001873 |

### Total line distribution

|   total_line |   count |    share |
|-------------:|--------:|---------:|
|         36   |       1 | 0.003745 |
|         36.5 |       2 | 0.007491 |
|         37   |       1 | 0.003745 |
|         38   |       4 | 0.01498  |
|         38.5 |       1 | 0.003745 |
|         39   |       3 | 0.01124  |
|         39.5 |       6 | 0.02247  |
|         40   |       8 | 0.02996  |
|         40.5 |       8 | 0.02996  |
|         41   |       7 | 0.02622  |
|         41.5 |       3 | 0.01124  |
|         42   |       5 | 0.01873  |
|         42.5 |      10 | 0.03745  |
|         43   |      10 | 0.03745  |
|         43.5 |      11 | 0.0412   |
|         44   |      16 | 0.05993  |
|         44.5 |      10 | 0.03745  |
|         45   |      10 | 0.03745  |
|         45.5 |       8 | 0.02996  |
|         46   |       8 | 0.02996  |
|         46.5 |      12 | 0.04494  |
|         47   |      11 | 0.0412   |
|         47.5 |      11 | 0.0412   |
|         48   |      10 | 0.03745  |
|         48.5 |       8 | 0.02996  |
|         49   |       6 | 0.02247  |
|         49.5 |       7 | 0.02622  |
|         50   |       7 | 0.02622  |
|         50.5 |       5 | 0.01873  |
|         51   |       9 | 0.03371  |
|         51.5 |       3 | 0.01124  |
|         52   |       8 | 0.02996  |
|         52.5 |       3 | 0.01124  |
|         53   |       4 | 0.01498  |
|         53.5 |       4 | 0.01498  |
|         54   |       5 | 0.01873  |
|         54.5 |       3 | 0.01124  |
|         55   |       5 | 0.01873  |
|         55.5 |       3 | 0.01124  |
|         56   |       2 | 0.007491 |
|         56.5 |       2 | 0.007491 |
|         57   |       2 | 0.007491 |
|         57.5 |       2 | 0.007491 |
|         59.5 |       1 | 0.003745 |
|         61   |       1 | 0.003745 |
|         63.5 |       1 | 0.003745 |

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

