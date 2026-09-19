# Phase 2B — dog vs favorite validation (H2)

**This validates a hypothesis generated from the 2024-2025 data.** The direction was declared in advance: *primary underdog teaser legs may outperform primary favorite teaser legs*. 2018-2023 is the unseen validation sample.

**Frozen Teaser Model v1.0 is unchanged by this phase. Nothing below is a recommendation to alter it.** The frozen model treats all four primary shapes identically;
`side_class` is a reporting label, not a model dimension.

- Lines are **archived reference lines** (`archived_reference_line`). The source documents no capture time. They are **not** closing lines and support no CLV claim.
- No historical teaser menu prices exist in this source and none have been invented. No EV, break-even, payout or ROI figure appears in this phase.
- **Three source regimes.** 2018-2023 and 2024 sit on the pre-2025 line feed; 2025 sits on a different feed. Blocks are never silently pooled; see `reports/nfl_line_composition_investigation.md`.

## 1. Validation sample: 2018-2023 aggregate

| group                  |   n |   mean_p_est |   wins |   actual_hit_rate |   calibration_gap |   ci95_low |   ci95_high |
|:-----------------------|----:|-------------:|-------:|------------------:|------------------:|-----------:|------------:|
| dogs (+1.5, +2.5)      | 132 |       0.7511 |    101 |            0.7652 |           0.01404 |     0.6835 |      0.8345 |
| favorites (-7.5, -8.5) |  79 |       0.7471 |     54 |            0.6835 |          -0.06358 |     0.5692 |      0.7837 |

### Statistical comparison

| group_a           |   n_a |   wins_a |   hit_rate_a | group_b                |   n_b |   wins_b |   hit_rate_b |   difference_pp |   odds_ratio_a_over_b |   or_ci95_low |   or_ci95_high | or_zero_cell_corrected   |   fisher_exact_p_two_sided |
|:------------------|------:|---------:|-------------:|:-----------------------|------:|---------:|-------------:|----------------:|----------------------:|--------------:|---------------:|:-------------------------|---------------------------:|
| dogs (+1.5, +2.5) |   132 |      101 |       0.7652 | favorites (-7.5, -8.5) |    79 |       54 |       0.6835 |           8.161 |                 1.508 |        0.8099 |          2.809 | False                    |                     0.2017 |

**Direction: the validation sample corroborates the hypothesis.** Dogs hit 76.5% against favorites at 68.4%, a difference of +8.2 percentage points. Fisher exact two-sided p = 0.2017; odds ratio 1.508 (95% CI 0.810-2.809).

Direction and significance are different questions. The p-value above is reported as computed; it is not a decision rule, and **no model change follows from it in either case**.

## 2. Per-season detail within the validation block

|   season |   dogs_n |   dogs_wins |   dogs_rate |   favs_n |   favs_wins |   favs_rate |   difference_pp |
|---------:|---------:|------------:|------------:|---------:|------------:|------------:|----------------:|
|     2018 |       22 |          16 |      0.7273 |       15 |           9 |      0.6    |          12.73  |
|     2019 |       17 |          14 |      0.8235 |        6 |           3 |      0.5    |          32.35  |
|     2020 |       11 |          11 |      1      |       14 |          11 |      0.7857 |          21.43  |
|     2021 |       14 |          11 |      0.7857 |       17 |          14 |      0.8235 |          -3.782 |
|     2022 |       27 |          17 |      0.6296 |       14 |           9 |      0.6429 |          -1.323 |
|     2023 |       41 |          32 |      0.7805 |       13 |           8 |      0.6154 |          16.51  |

Dogs out-hit favorites in **4 of 6** seasons with both groups present. Single-season splits are very small and are shown for transparency, not as evidence.

## 3. Side by side: validation block vs hypothesis-generating block

> The 2024-2025 numbers are **not** independent evidence for this hypothesis — the hypothesis came from them. They are shown to let the reader compare, not to be added together.

| block                                      |   dogs_n |   dogs_wins |   dogs_rate |   dogs_mean_p_est |   favs_n |   favs_wins |   favs_rate |   favs_mean_p_est |   difference_pp |
|:-------------------------------------------|---------:|------------:|------------:|------------------:|---------:|------------:|------------:|------------------:|----------------:|
| 2018-2023 (validation, unseen)             |      132 |         101 |      0.7652 |            0.7511 |       79 |          54 |      0.6835 |            0.7471 |           8.161 |
| 2024 (hypothesis-generating)               |       28 |          23 |      0.8214 |            0.7519 |       13 |           8 |      0.6154 |            0.7516 |          20.6   |
| 2025 (hypothesis-generating, changed feed) |       48 |          39 |      0.8125 |            0.75   |       15 |          10 |      0.6667 |            0.7552 |          14.58  |
| 2024-2025 combined (hypothesis-generating) |       76 |          62 |      0.8158 |            0.7507 |       28 |          18 |      0.6429 |            0.7535 |          17.29  |

Note that **mean P_est is essentially identical for dogs and favorites** in every block: the frozen model assigns them the same probability, because all four primary shapes cross both key numbers and P_est depends only on the total. Any difference in realized hit rate is therefore a difference the frozen model does not predict at all.

## 4. Limitations

- The favorite group is much smaller than the dog group in every block; its interval is correspondingly wide.
- Shape composition differs between blocks, so a dog/favorite difference is partly confounded with which exact shapes were available in a given season.
- Legs within a season are not independent of the market that priced them.
- Multiple hypotheses were examined in Phase 2; this is the one carried forward, and no multiplicity correction is applied to the p-value above.

## What this report does not do

It does not change v1.0, split the model by side, reweight anything, or recommend a parameter change. H2 remains a research question in `RESEARCH_QUEUE.md`.

