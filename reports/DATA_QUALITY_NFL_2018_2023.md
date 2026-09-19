# Data-Quality Audit — NFL 2018, 2019, 2020, 2021, 2022, 2023 — nflverse/nfldata

This audit runs **before** any strategy calculation. Its purpose is to decide whether the dataset preserves enough half-point fidelity to test Teaser Model v1.0 at all. It contains no model-performance results of any kind.

**Seasons audited:** 2018, 2019, 2020, 2021, 2022, 2023

## Verdict

### PASS

The dataset preserves half-point fidelity and is safe to use for v1.0 historical testing, subject to the limitations listed below.

## Checks

| check                                 | status   | critical   | detail                                                                                                                                            |
|:--------------------------------------|:---------|:-----------|:--------------------------------------------------------------------------------------------------------------------------------------------------|
| final_scores_present                  | PASS     | yes        | 0 of 1657 games have no final score.                                                                                                              |
| missing_spreads                       | PASS     | yes        | 0 of 1657 games missing spread_line (0.000%); gate is <= 1.0%.                                                                                    |
| missing_totals                        | PASS     | yes        | 0 of 1657 games missing total_line (0.000%); gate is <= 1.0%.                                                                                     |
| duplicate_games                       | PASS     | yes        | 0 duplicated game_id values; 0 rows duplicating season/week/home/away.                                                                            |
| spreads_on_half_point_grid            | PASS     | yes        | 0 spread values are not multiples of 0.5.                                                                                                         |
| spread_half_point_share               | PASS     | yes        | 812 of 1657 spreads end in .5 (49.00%); gate is >= 40%. A source that rounded half-points away would sit near 0%.                                 |
| spread_half_point_share_every_season  | PASS     | yes        | Lowest single-season half-point share is 46.44% in 2019; gate is >= 40%.                                                                          |
| season_composition_consistency        | PASS     | no         | Half-point composition is consistent across seasons.                                                                                              |
| primary_geometry_present              | PASS     | yes        | All four primary shapes appear in the data.                                                                                                       |
| primary_geometry_present_every_season | PASS     | no         | Every primary shape appears in every season.                                                                                                      |
| key_numbers_not_collapsed             | PASS     | yes        | Every whole number present in the data still has its adjacent half-point represented.                                                             |
| total_half_point_share                | PASS     | no         | 752 of 1657 totals end in .5 (45.38%). Totals do not gate the model the way spreads do, but a near-zero share would still indicate rounding.      |
| totals_on_half_point_grid             | PASS     | yes        | 0 total values are not multiples of 0.5.                                                                                                          |
| suspicious_rounding_patterns          | PASS     | no         | No suspicious rounding patterns detected.                                                                                                         |
| impossible_values                     | PASS     | yes        | No impossible values found.                                                                                                                       |
| line_provenance_is_honest             | PASS     | no         | Lines are labelled 'archived_reference_line'. 'true_timestamped_close' is only permitted when the source documents a capture time before kickoff. |

## Tables

### Games by season

|   season |   games |
|---------:|--------:|
|     2018 |     267 |
|     2019 |     267 |
|     2020 |     269 |
|     2021 |     285 |
|     2022 |     284 |
|     2023 |     285 |

### Games by season and type

|   season | game_type   |   games |
|---------:|:------------|--------:|
|     2018 | CON         |       2 |
|     2018 | DIV         |       4 |
|     2018 | REG         |     256 |
|     2018 | SB          |       1 |
|     2018 | WC          |       4 |
|     2019 | CON         |       2 |
|     2019 | DIV         |       4 |
|     2019 | REG         |     256 |
|     2019 | SB          |       1 |
|     2019 | WC          |       4 |
|     2020 | CON         |       2 |
|     2020 | DIV         |       4 |
|     2020 | REG         |     256 |
|     2020 | SB          |       1 |
|     2020 | WC          |       6 |
|     2021 | CON         |       2 |
|     2021 | DIV         |       4 |
|     2021 | REG         |     272 |
|     2021 | SB          |       1 |
|     2021 | WC          |       6 |
|     2022 | CON         |       2 |
|     2022 | DIV         |       4 |
|     2022 | REG         |     271 |
|     2022 | SB          |       1 |
|     2022 | WC          |       6 |
|     2023 | CON         |       2 |
|     2023 | DIV         |       4 |
|     2023 | REG         |     272 |
|     2023 | SB          |       1 |
|     2023 | WC          |       6 |

### Half-point share by season

|   season |   spreads |   half_point |   half_point_share |   integer |
|---------:|----------:|-------------:|-------------------:|----------:|
|     2018 |       267 |          131 |             0.4906 |       136 |
|     2019 |       267 |          124 |             0.4644 |       143 |
|     2020 |       269 |          127 |             0.4721 |       142 |
|     2021 |       285 |          144 |             0.5053 |       141 |
|     2022 |       284 |          139 |             0.4894 |       145 |
|     2023 |       285 |          147 |             0.5158 |       138 |

### Composition by season

|   season |   spread_half_point_share |   total_half_point_share |
|---------:|--------------------------:|-------------------------:|
|     2018 |                    0.4906 |                   0.4644 |
|     2019 |                    0.4644 |                   0.3783 |
|     2020 |                    0.4721 |                   0.4275 |
|     2021 |                    0.5053 |                   0.4281 |
|     2022 |                    0.4894 |                   0.4718 |
|     2023 |                    0.5158 |                   0.5474 |

### Integer vs half-point spreads

| kind            |   count |   share |
|:----------------|--------:|--------:|
| half-point (.5) |     812 |    0.49 |
| integer (.0)    |     845 |    0.51 |

### Spread fractional parts

|   fractional_part |   count |
|------------------:|--------:|
|               0   |     845 |
|               0.5 |     812 |

### Primary-geometry leg counts

|   leg_spread |   legs_total |   legs_2018 |   legs_2019 |   legs_2020 |   legs_2021 |   legs_2022 |   legs_2023 |
|-------------:|-------------:|------------:|------------:|------------:|------------:|------------:|------------:|
|          1.5 |           42 |           7 |           7 |           7 |           2 |           5 |          14 |
|          2.5 |          155 |          23 |          15 |          19 |          26 |          35 |          37 |
|         -7.5 |           92 |          18 |          10 |          22 |          18 |          11 |          13 |
|         -8.5 |           28 |           8 |           1 |           4 |           6 |           6 |           3 |

### Key-number pairs (whole vs half)

|   whole |   count_whole |   adjacent_half |   count_half |
|--------:|--------------:|----------------:|-------------:|
|       2 |            43 |             1.5 |           42 |
|       2 |            43 |             2.5 |          155 |
|       3 |           235 |             2.5 |          155 |
|       3 |           235 |             3.5 |          160 |
|       7 |            87 |             6.5 |           74 |
|       7 |            87 |             7.5 |           92 |
|       8 |            19 |             7.5 |           92 |
|       8 |            19 |             8.5 |           28 |
|       9 |             7 |             8.5 |           28 |

### Total line summary

|   season |   n |   min |   p25 |   median |   p75 |   max |   mean |   half_point_share |   at_or_below_47 |
|---------:|----:|------:|------:|---------:|------:|------:|-------:|-------------------:|-----------------:|
|     2018 | 267 |  36   | 43    |     46.5 |  50   |  63.5 |  46.65 |             0.4644 |              155 |
|     2019 | 267 |  35   | 42.75 |     45.5 |  48   |  55.5 |  45.22 |             0.3783 |              186 |
|     2020 | 269 |  36.5 | 45    |     48   |  51.5 |  58   |  48.17 |             0.4275 |              122 |
|     2021 | 285 |  36   | 43.5  |     46   |  49   |  57.5 |  46.54 |             0.4281 |              167 |
|     2022 | 284 |  32   | 41.38 |     44   |  47   |  54.5 |  44.22 |             0.4718 |              218 |
|     2023 | 285 |  28.5 | 40    |     43.5 |  46   |  54   |  43.13 |             0.5474 |              228 |

### Spread increment distribution (source field)

|   spread_line (home-favoured-by) |   count |     share |
|---------------------------------:|--------:|----------:|
|                            -18   |       1 | 0.0006035 |
|                            -17   |       2 | 0.001207  |
|                            -15.5 |       1 | 0.0006035 |
|                            -15   |       1 | 0.0006035 |
|                            -14.5 |       6 | 0.003621  |
|                            -14   |       6 | 0.003621  |
|                            -13.5 |       5 | 0.003018  |
|                            -13   |       7 | 0.004225  |
|                            -12.5 |       1 | 0.0006035 |
|                            -12   |       1 | 0.0006035 |
|                            -11.5 |       5 | 0.003018  |
|                            -11   |       4 | 0.002414  |
|                            -10.5 |      10 | 0.006035  |
|                            -10   |      11 | 0.006639  |
|                             -9.5 |      12 | 0.007242  |
|                             -9   |       2 | 0.001207  |
|                             -8.5 |       7 | 0.004225  |
|                             -8   |       5 | 0.003018  |
|                             -7.5 |      27 | 0.01629   |
|                             -7   |      35 | 0.02112   |
|                             -6.5 |      22 | 0.01328   |
|                             -6   |      34 | 0.02052   |
|                             -5.5 |      25 | 0.01509   |
|                             -5   |      11 | 0.006639  |
|                             -4.5 |      16 | 0.009656  |
|                             -4   |      32 | 0.01931   |
|                             -3.5 |      64 | 0.03862   |
|                             -3   |      99 | 0.05975   |
|                             -2.5 |      65 | 0.03923   |
|                             -2   |      26 | 0.01569   |
|                             -1.5 |      20 | 0.01207   |
|                             -1   |      64 | 0.03862   |
|                              1   |      66 | 0.03983   |
|                              1.5 |      22 | 0.01328   |
|                              2   |      17 | 0.01026   |
|                              2.5 |      90 | 0.05432   |
|                              3   |     136 | 0.08208   |
|                              3.5 |      96 | 0.05794   |
|                              4   |      50 | 0.03018   |
|                              4.5 |      36 | 0.02173   |
|                              5   |      23 | 0.01388   |
|                              5.5 |      49 | 0.02957   |
|                              6   |      39 | 0.02354   |
|                              6.5 |      52 | 0.03138   |
|                              7   |      52 | 0.03138   |
|                              7.5 |      65 | 0.03923   |
|                              8   |      14 | 0.008449  |
|                              8.5 |      21 | 0.01267   |
|                              9   |       5 | 0.003018  |
|                              9.5 |      21 | 0.01267   |
|                             10   |      37 | 0.02233   |
|                             10.5 |      35 | 0.02112   |
|                             11   |      14 | 0.008449  |
|                             11.5 |       6 | 0.003621  |
|                             12   |       3 | 0.001811  |
|                             12.5 |       6 | 0.003621  |
|                             13   |      16 | 0.009656  |
|                             13.5 |       9 | 0.005432  |
|                             14   |      20 | 0.01207   |
|                             14.5 |       2 | 0.001207  |
|                             15   |       3 | 0.001811  |
|                             15.5 |       3 | 0.001811  |
|                             16   |       1 | 0.0006035 |
|                             16.5 |       7 | 0.004225  |
|                             17   |       5 | 0.003018  |
|                             17.5 |       4 | 0.002414  |
|                             19   |       1 | 0.0006035 |
|                             20   |       1 | 0.0006035 |
|                             20.5 |       2 | 0.001207  |
|                             22   |       1 | 0.0006035 |

### Leg spread distribution (team perspective)

|   leg spread (team perspective) |   count |     share |
|--------------------------------:|--------:|----------:|
|                           -22   |       1 | 0.0003018 |
|                           -20.5 |       2 | 0.0006035 |
|                           -20   |       1 | 0.0003018 |
|                           -19   |       1 | 0.0003018 |
|                           -18   |       1 | 0.0003018 |
|                           -17.5 |       4 | 0.001207  |
|                           -17   |       7 | 0.002112  |
|                           -16.5 |       7 | 0.002112  |
|                           -16   |       1 | 0.0003018 |
|                           -15.5 |       4 | 0.001207  |
|                           -15   |       4 | 0.001207  |
|                           -14.5 |       8 | 0.002414  |
|                           -14   |      26 | 0.007846  |
|                           -13.5 |      14 | 0.004225  |
|                           -13   |      23 | 0.00694   |
|                           -12.5 |       7 | 0.002112  |
|                           -12   |       4 | 0.001207  |
|                           -11.5 |      11 | 0.003319  |
|                           -11   |      18 | 0.005432  |
|                           -10.5 |      45 | 0.01358   |
|                           -10   |      48 | 0.01448   |
|                            -9.5 |      33 | 0.009958  |
|                            -9   |       7 | 0.002112  |
|                            -8.5 |      28 | 0.008449  |
|                            -8   |      19 | 0.005733  |
|                            -7.5 |      92 | 0.02776   |
|                            -7   |      87 | 0.02625   |
|                            -6.5 |      74 | 0.02233   |
|                            -6   |      73 | 0.02203   |
|                            -5.5 |      74 | 0.02233   |
|                            -5   |      34 | 0.01026   |
|                            -4.5 |      52 | 0.01569   |
|                            -4   |      82 | 0.02474   |
|                            -3.5 |     160 | 0.04828   |
|                            -3   |     235 | 0.07091   |
|                            -2.5 |     155 | 0.04677   |
|                            -2   |      43 | 0.01298   |
|                            -1.5 |      42 | 0.01267   |
|                            -1   |     130 | 0.03923   |
|                             1   |     130 | 0.03923   |
|                             1.5 |      42 | 0.01267   |
|                             2   |      43 | 0.01298   |
|                             2.5 |     155 | 0.04677   |
|                             3   |     235 | 0.07091   |
|                             3.5 |     160 | 0.04828   |
|                             4   |      82 | 0.02474   |
|                             4.5 |      52 | 0.01569   |
|                             5   |      34 | 0.01026   |
|                             5.5 |      74 | 0.02233   |
|                             6   |      73 | 0.02203   |
|                             6.5 |      74 | 0.02233   |
|                             7   |      87 | 0.02625   |
|                             7.5 |      92 | 0.02776   |
|                             8   |      19 | 0.005733  |
|                             8.5 |      28 | 0.008449  |
|                             9   |       7 | 0.002112  |
|                             9.5 |      33 | 0.009958  |
|                            10   |      48 | 0.01448   |
|                            10.5 |      45 | 0.01358   |
|                            11   |      18 | 0.005432  |
|                            11.5 |      11 | 0.003319  |
|                            12   |       4 | 0.001207  |
|                            12.5 |       7 | 0.002112  |
|                            13   |      23 | 0.00694   |
|                            13.5 |      14 | 0.004225  |
|                            14   |      26 | 0.007846  |
|                            14.5 |       8 | 0.002414  |
|                            15   |       4 | 0.001207  |
|                            15.5 |       4 | 0.001207  |
|                            16   |       1 | 0.0003018 |
|                            16.5 |       7 | 0.002112  |
|                            17   |       7 | 0.002112  |
|                            17.5 |       4 | 0.001207  |
|                            18   |       1 | 0.0003018 |
|                            19   |       1 | 0.0003018 |
|                            20   |       1 | 0.0003018 |
|                            20.5 |       2 | 0.0006035 |
|                            22   |       1 | 0.0003018 |

### Total line distribution

|   total_line |   count |     share |
|-------------:|--------:|----------:|
|         28.5 |       1 | 0.0006035 |
|         30   |       1 | 0.0006035 |
|         32   |       2 | 0.001207  |
|         33   |       1 | 0.0006035 |
|         33.5 |       2 | 0.001207  |
|         34   |       3 | 0.001811  |
|         35   |       5 | 0.003018  |
|         35.5 |       3 | 0.001811  |
|         36   |       7 | 0.004225  |
|         36.5 |      14 | 0.008449  |
|         37   |      14 | 0.008449  |
|         37.5 |      13 | 0.007846  |
|         38   |      22 | 0.01328   |
|         38.5 |      21 | 0.01267   |
|         39   |      15 | 0.009053  |
|         39.5 |      33 | 0.01992   |
|         40   |      42 | 0.02535   |
|         40.5 |      28 | 0.0169    |
|         41   |      56 | 0.0338    |
|         41.5 |      50 | 0.03018   |
|         42   |      50 | 0.03018   |
|         42.5 |      49 | 0.02957   |
|         43   |      79 | 0.04768   |
|         43.5 |      66 | 0.03983   |
|         44   |      94 | 0.05673   |
|         44.5 |      67 | 0.04043   |
|         45   |      68 | 0.04104   |
|         45.5 |      61 | 0.03681   |
|         46   |      80 | 0.04828   |
|         46.5 |      53 | 0.03199   |
|         47   |      76 | 0.04587   |
|         47.5 |      54 | 0.03259   |
|         48   |      71 | 0.04285   |
|         48.5 |      58 | 0.035     |
|         49   |      53 | 0.03199   |
|         49.5 |      49 | 0.02957   |
|         50   |      31 | 0.01871   |
|         50.5 |      24 | 0.01448   |
|         51   |      40 | 0.02414   |
|         51.5 |      24 | 0.01448   |
|         52   |      26 | 0.01569   |
|         52.5 |      28 | 0.0169    |
|         53   |      23 | 0.01388   |
|         53.5 |      18 | 0.01086   |
|         54   |      19 | 0.01147   |
|         54.5 |      13 | 0.007846  |
|         55   |      18 | 0.01086   |
|         55.5 |      12 | 0.007242  |
|         56   |       4 | 0.002414  |
|         56.5 |       6 | 0.003621  |
|         57   |       3 | 0.001811  |
|         57.5 |       3 | 0.001811  |
|         58   |       1 | 0.0006035 |
|         59.5 |       1 | 0.0006035 |
|         61   |       1 | 0.0006035 |
|         63.5 |       1 | 0.0006035 |

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

