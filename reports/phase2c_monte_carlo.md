# Phase 2C — Monte Carlo null on the exact historical board

**Teaser Model v1.0 is unchanged by this audit.** `P_ticket` remains the product of leg `P_est` values. Nothing here fits a probability, applies a correlation correction, or proposes a new formula.

**Design.** Each qualifying leg keeps its actual frozen `P_est`. Under the null that leg outcomes are independent `Bernoulli(P_est)` draws, 100,000 complete blocks are simulated. Each leg's week and `P_est` are preserved, and **the frozen top-four ticket set is held fixed**, so the historical overlap is reproduced exactly: where four legs generated six 2-team and four 3-team tickets, the simulation generates those same overlapping tickets from the simulated leg outcomes.

Seed `20260919`, fixed. Re-running reproduces every number; a test asserts it.

The one-sided Monte Carlo probability is `(1 + #{simulated >= observed}) / (1 + n_sims)`.

**What this null assumes.** It takes `P_est` to be correctly calibrated. If the frozen model systematically under-states leg probabilities, this test can register that miscalibration as apparent dependence. The permutation test in `reports/phase2c_permutation.md` drops that assumption.

> Tickets are **not independent observations**. Within a week they share legs, and shared legs are exactly the mechanism under test. Every interval below that concerns a ticket statistic is either a simulation interval over the whole board or a week-clustered bootstrap; no standard error treats tickets as independent draws.

## 2-team tickets

| block                             |   n_tickets |   observed_hit_rate |   sim_mean |   sim_ci_low |   sim_ci_high |   p_value_one_sided |
|:----------------------------------|------------:|--------------------:|-----------:|-------------:|--------------:|--------------------:|
| 2018-2023 validation              |         174 |              0.5977 |     0.5648 |       0.4598 |        0.6724 |              0.2901 |
| 2024                              |          29 |              0.5172 |     0.5669 |       0.3103 |        0.8276 |              0.6972 |
| 2025                              |          63 |              0.619  |     0.5681 |       0.381  |        0.7619 |              0.3302 |
| SUPPLEMENTARY 2018-2025 all years |         266 |              0.594  |     0.5658 |       0.4774 |        0.6541 |              0.2769 |

## 3-team tickets

| block                             |   n_tickets |   observed_hit_rate |   sim_mean |   sim_ci_low |   sim_ci_high |   p_value_one_sided |
|:----------------------------------|------------:|--------------------:|-----------:|-------------:|--------------:|--------------------:|
| 2018-2023 validation              |          73 |              0.5616 |     0.4266 |       0.2603 |        0.589  |             0.06808 |
| 2024                              |          10 |              0.3    |     0.4337 |       0.1    |        0.8    |             0.7994  |
| 2025                              |          36 |              0.5278 |     0.4282 |       0.1944 |        0.6944 |             0.2542  |
| SUPPLEMENTARY 2018-2025 all years |         119 |              0.5294 |     0.4276 |       0.3025 |        0.563  |             0.07623 |

## All-win weeks

A statistic free of ticket overlap: the number of weeks in which every qualifying leg won, against the independence expectation.

| block                             |   weeks |   observed |   sim_mean |   sim_ci_low |   sim_ci_high |   p_value_one_sided |
|:----------------------------------|--------:|-----------:|-----------:|-------------:|--------------:|--------------------:|
| 2018-2023 validation              |      64 |         28 |     29.22  |           22 |            37 |             0.6697  |
| 2024                              |      12 |          4 |      5.435 |            2 |             9 |             0.8778  |
| 2025                              |      15 |          9 |      5.339 |            2 |             9 |             0.04034 |
| SUPPLEMENTARY 2018-2025 all years |      91 |         41 |     39.99  |           31 |            49 |             0.4539  |

## Leg-win totals (sanity check on the null)

The simulated leg-win totals show where the observed leg count sits inside the null. This is the leg-level calibration channel, isolated from any ticket effect.

| block                             |   observed |   sim_mean |   sim_ci_low |   sim_ci_high |
|:----------------------------------|-----------:|-----------:|-------------:|--------------:|
| 2018-2023 validation              |        155 |     158.2  |          146 |           170 |
| 2024                              |         31 |      30.81 |           25 |            36 |
| 2025                              |         49 |      47.33 |           40 |            54 |
| SUPPLEMENTARY 2018-2025 all years |        235 |     236.3  |          221 |           251 |

## Reading these results

The simulation interval is wide because it lets the **total** number of leg wins vary binomially as well as their arrangement. It therefore answers: *could this whole board, overlap included, have come out this way by chance under independence?* It does not isolate clustering. The permutation test conditions on the realized win total and isolates arrangement; the two answer different questions and should be read together.

