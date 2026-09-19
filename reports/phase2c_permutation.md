# Phase 2C — calibration-neutral permutation test

**Teaser Model v1.0 is unchanged by this audit.** `P_ticket` remains the product of leg `P_est` values. Nothing here fits a probability, applies a correlation correction, or proposes a new formula.

## Permutation schemes, declared before the results were computed

Both schemes below were fixed in `src/teaser_model_v1/analysis/dependence.py` before either was run, and **both are reported regardless of what they show.** Neither was chosen after seeing which produced significance.

**P1 — season-level free permutation (primary).** Within each season, permute the observed WIN/LOSS labels among all qualifying primary legs. Each season's marginal win count is preserved exactly. The permutation is not confined within a week, so the association between a leg's week and its outcome is destroyed.

**P2 — season x side_class stratified permutation (secondary).** As P1, but permuting within (season, DOG/FAVORITE) strata, so week-level dog/favorite composition cannot manufacture clustering. Strata with fewer than 5 legs are held fixed; the count of held-fixed legs is reported.

**Why not a finer stratification.** The preferred stratification by shape and total bucket is not defensible at this sample size: seasons carry 23-63 qualifying legs, so a 16-cell scheme would leave most cells with 0-2 legs and the permutation would be close to the identity. Per the Phase 2C instruction, the simplest defensible scheme is used and the limitation stated here rather than worked around.

100,000 permutations per block per scheme, seed `20260919`, fixed. The one-sided probability is `(1 + #{permuted >= observed}) / (1 + n_sims)`.

**What this test does and does not assume.** It does **not** assume `P_est` is calibrated: it conditions on the realized number of wins and asks only whether those wins are more clustered within weeks than a random reallocation of the same wins would produce. That makes it the right instrument for separating dependence from leg-level miscalibration.

> Tickets are **not independent observations**. Within a week they share legs, and shared legs are exactly the mechanism under test. Every interval below that concerns a ticket statistic is either a simulation interval over the whole board or a week-clustered bootstrap; no standard error treats tickets as independent draws.

## Scheme P1

| block                             |   n_legs |   strata |   permutable_strata |   legs_held_fixed |
|:----------------------------------|---------:|---------:|--------------------:|------------------:|
| 2018-2023 validation              |      211 |        6 |                   6 |                 0 |
| 2024                              |       41 |        1 |                   1 |                 0 |
| 2025                              |       63 |        1 |                   1 |                 0 |
| SUPPLEMENTARY 2018-2025 all years |      315 |        8 |                   8 |                 0 |

### P1 — 2-team tickets

| block                             |   n_tickets |   observed_hit_rate |   perm_mean |   perm_ci_low |   perm_ci_high |   p_value_one_sided |
|:----------------------------------|------------:|--------------------:|------------:|--------------:|---------------:|--------------------:|
| 2018-2023 validation              |         174 |              0.5977 |      0.5309 |        0.477  |         0.592  |             0.01993 |
| 2024                              |          29 |              0.5172 |      0.5673 |        0.4138 |         0.7241 |             0.8041  |
| 2025                              |          63 |              0.619  |      0.6019 |        0.5079 |         0.7143 |             0.4197  |
| SUPPLEMENTARY 2018-2025 all years |         266 |              0.594  |      0.5517 |        0.5038 |         0.6015 |             0.05507 |

### P1 — 3-team tickets

| block                             |   n_tickets |   observed_hit_rate |   perm_mean |   perm_ci_low |   perm_ci_high |   p_value_one_sided |
|:----------------------------------|------------:|--------------------:|------------:|--------------:|---------------:|--------------------:|
| 2018-2023 validation              |          73 |              0.5616 |      0.3814 |        0.2603 |         0.5068 |             0.00513 |
| 2024                              |          10 |              0.3    |      0.4218 |        0.2    |         0.8    |             0.8503  |
| 2025                              |          36 |              0.5278 |      0.4633 |        0.2778 |         0.6667 |             0.2861  |
| SUPPLEMENTARY 2018-2025 all years |         119 |              0.5294 |      0.4097 |        0.3109 |         0.5126 |             0.01319 |

### P1 — all-win weeks

| block                             |   weeks |   observed |   perm_mean |   perm_ci_low |   perm_ci_high |   p_value_one_sided |
|:----------------------------------|--------:|-----------:|------------:|--------------:|---------------:|--------------------:|
| 2018-2023 validation              |      64 |         28 |      27.23  |            23 |             32 |             0.4531  |
| 2024                              |      12 |          4 |       5.453 |             3 |              8 |             0.9683  |
| 2025                              |      15 |          9 |       5.843 |             4 |              8 |             0.01159 |
| SUPPLEMENTARY 2018-2025 all years |      91 |         41 |      38.52  |            33 |             44 |             0.2493  |

## Scheme P2

| block                             |   n_legs |   strata |   permutable_strata |   legs_held_fixed |
|:----------------------------------|---------:|---------:|--------------------:|------------------:|
| 2018-2023 validation              |      211 |       12 |                  12 |                 0 |
| 2024                              |       41 |        2 |                   2 |                 0 |
| 2025                              |       63 |        2 |                   2 |                 0 |
| SUPPLEMENTARY 2018-2025 all years |      315 |       16 |                  16 |                 0 |

### P2 — 2-team tickets

| block                             |   n_tickets |   observed_hit_rate |   perm_mean |   perm_ci_low |   perm_ci_high |   p_value_one_sided |
|:----------------------------------|------------:|--------------------:|------------:|--------------:|---------------:|--------------------:|
| 2018-2023 validation              |         174 |              0.5977 |      0.5259 |        0.4713 |         0.5862 |             0.01207 |
| 2024                              |          29 |              0.5172 |      0.5637 |        0.4138 |         0.7241 |             0.7935  |
| 2025                              |          63 |              0.619  |      0.5912 |        0.4921 |         0.6984 |             0.3405  |
| SUPPLEMENTARY 2018-2025 all years |         266 |              0.594  |      0.5455 |        0.5    |         0.594  |             0.0301  |

### P2 — 3-team tickets

| block                             |   n_tickets |   observed_hit_rate |   perm_mean |   perm_ci_low |   perm_ci_high |   p_value_one_sided |
|:----------------------------------|------------:|--------------------:|------------:|--------------:|---------------:|--------------------:|
| 2018-2023 validation              |          73 |              0.5616 |      0.3723 |        0.2603 |         0.5068 |             0.00307 |
| 2024                              |          10 |              0.3    |      0.4271 |        0.2    |         0.8    |             0.8542  |
| 2025                              |          36 |              0.5278 |      0.4482 |        0.2778 |         0.6389 |             0.232   |
| SUPPLEMENTARY 2018-2025 all years |         119 |              0.5294 |      0.3999 |        0.3025 |         0.5042 |             0.00747 |

### P2 — all-win weeks

| block                             |   weeks |   observed |   perm_mean |   perm_ci_low |   perm_ci_high |   p_value_one_sided |
|:----------------------------------|--------:|-----------:|------------:|--------------:|---------------:|--------------------:|
| 2018-2023 validation              |      64 |         28 |      27.2   |            23 |             32 |             0.4475  |
| 2024                              |      12 |          4 |       5.293 |             3 |              7 |             0.9596  |
| 2025                              |      15 |          9 |       5.816 |             4 |              8 |             0.01125 |
| SUPPLEMENTARY 2018-2025 all years |      91 |         41 |      38.31  |            33 |             44 |             0.2258  |

## Limitations

- P1 reallocates outcomes across legs with different `P_est` values, so it preserves the season's win total but not its composition by total or shape.
- P2 removes the dog/favorite channel but is coarser than the shape x total scheme the instruction prefers, for the sample-size reason stated above.
- Permuting within a season means a season with an unusual win total is treated as given. That is the intent — the test is about arrangement, not level — but it means the test says nothing about leg-level calibration.
- Ticket statistics remain overlapping; the permutation distribution accounts for that overlap because it rebuilds the same fixed ticket set each time.

## What follows from this

Nothing, operationally. This is a diagnostic recorded in `RESEARCH_QUEUE.md` R-08. No correlation correction is applied, no ticket probability is altered, and no new live formula is proposed.

