# Phase 3 — model-implied fair price distribution

## A: MODEL-IMPLIED FAIR PRICE

Derived from the frozen `P_ticket`:  `fair net profit per unit = (1 - P) / P`. This states what the **model** thinks a ticket is worth. It is **not** a price any sportsbook offered, and it is **not** a historical outcome. The distinct object derived from realized results is the historical outcome break-even price in `reports/phase3_historical_price_frontier.md`; the two must never be conflated.

**Frozen Teaser Model v1.0 is unchanged.** `P_ticket` is the product of leg `P_est` values, with no correlation adjustment: Phase 2C found only weak evidence against independence, which is not grounds for altering a frozen model.

- **Three source regimes.** 2018-2023 and 2024 sit on the pre-2025 archived line feed; 2025 sits on a different feed. The all-years row is supplementary only.
- Lines are archived reference lines with no documented capture time. They are not closing lines.

At the fair price the break-even probability equals `P_ticket` exactly, by construction. Full precision is retained internally; the tables round for display.

## Calibration base

| block                             |   n |   mean_p_est |   expected_wins |   actual_wins |   actual_hit_rate |   calibration_gap |   brier_score |
|:----------------------------------|----:|-------------:|----------------:|--------------:|------------------:|------------------:|--------------:|
| 2018-2023 validation              | 211 |       0.7496 |          158.2  |           155 |            0.7346 |         -0.01502  |        0.1949 |
| 2024                              |  41 |       0.7518 |           30.82 |            31 |            0.7561 |          0.004309 |        0.1839 |
| 2025                              |  63 |       0.7513 |           47.33 |            49 |            0.7778 |          0.02649  |        0.1754 |
| SUPPLEMENTARY 2018-2025 all years | 315 |       0.7502 |          236.3  |           235 |            0.746  |         -0.004202 |        0.1896 |

> The all-years row is supplementary and spans three source regimes.

## Fair-price distribution, by block and ticket size

### 2018-2023 validation

| ticket_size   |   n_tickets |   p_ticket_min |   p_ticket_median |   p_ticket_max |   fair_american_min |   fair_american_p25 |   fair_american_median |   fair_american_p75 |   fair_american_max |
|:--------------|------------:|---------------:|------------------:|---------------:|--------------------:|--------------------:|-----------------------:|--------------------:|--------------------:|
| 2-team        |         174 |         0.5399 |            0.5628 |         0.6426 |              -179.8 |              -134.6 |                 -128.7 |              -123.7 |              -117.3 |
| 3-team        |          73 |         0.3976 |            0.4262 |         0.4755 |               110.3 |               128.8 |                  134.6 |               140.9 |               151.5 |

Decimal-odds and net-profit views of the same distribution:

| ticket_size   |   fair_profit_min |   fair_profit_p25 |   fair_profit_median |   fair_profit_p75 |   fair_profit_max |   fair_decimal_min |   fair_decimal_median |   fair_decimal_max |
|:--------------|------------------:|------------------:|---------------------:|------------------:|------------------:|-------------------:|----------------------:|-------------------:|
| 2-team        |            0.5561 |            0.7427 |               0.7769 |            0.8086 |            0.8522 |              1.556 |                 1.777 |              1.852 |
| 3-team        |            1.103  |            1.288  |               1.346  |            1.409  |            1.515  |              2.103 |                 2.346 |              2.515 |

### 2024

| ticket_size   |   n_tickets |   p_ticket_min |   p_ticket_median |   p_ticket_max |   fair_american_min |   fair_american_p25 |   fair_american_median |   fair_american_p75 |   fair_american_max |
|:--------------|------------:|---------------:|------------------:|---------------:|--------------------:|--------------------:|-----------------------:|--------------------:|--------------------:|
| 2-team        |          29 |         0.5411 |            0.5598 |         0.6035 |              -152.2 |              -142.1 |                 -127.2 |              -123.7 |              -117.9 |
| 3-team        |          10 |         0.4023 |            0.4352 |         0.4609 |               117   |               119.5 |                  130.1 |               142.3 |               148.6 |

Decimal-odds and net-profit views of the same distribution:

| ticket_size   |   fair_profit_min |   fair_profit_p25 |   fair_profit_median |   fair_profit_p75 |   fair_profit_max |   fair_decimal_min |   fair_decimal_median |   fair_decimal_max |
|:--------------|------------------:|------------------:|---------------------:|------------------:|------------------:|-------------------:|----------------------:|-------------------:|
| 2-team        |             0.657 |            0.7036 |               0.7862 |            0.8086 |             0.848 |              1.657 |                 1.786 |              1.848 |
| 3-team        |             1.17  |            1.195  |               1.301  |            1.423  |             1.486 |              2.17  |                 2.301 |              2.486 |

### 2025

| ticket_size   |   n_tickets |   p_ticket_min |   p_ticket_median |   p_ticket_max |   fair_american_min |   fair_american_p25 |   fair_american_median |   fair_american_p75 |   fair_american_max |
|:--------------|------------:|---------------:|------------------:|---------------:|--------------------:|--------------------:|-----------------------:|--------------------:|--------------------:|
| 2-team        |          63 |         0.5502 |            0.5671 |         0.6025 |              -151.6 |              -133.6 |                 -131   |              -126.6 |              -122.3 |
| 3-team        |          36 |         0.4111 |            0.426  |         0.4601 |               117.3 |               131   |                  134.8 |               138.4 |               143.2 |

Decimal-odds and net-profit views of the same distribution:

| ticket_size   |   fair_profit_min |   fair_profit_p25 |   fair_profit_median |   fair_profit_p75 |   fair_profit_max |   fair_decimal_min |   fair_decimal_median |   fair_decimal_max |
|:--------------|------------------:|------------------:|---------------------:|------------------:|------------------:|-------------------:|----------------------:|-------------------:|
| 2-team        |            0.6597 |            0.7483 |               0.7634 |             0.79  |            0.8174 |              1.66  |                 1.763 |              1.817 |
| 3-team        |            1.173  |            1.31   |               1.348  |             1.384 |            1.432  |              2.173 |                 2.348 |              2.432 |

### SUPPLEMENTARY 2018-2025 all years

| ticket_size   |   n_tickets |   p_ticket_min |   p_ticket_median |   p_ticket_max |   fair_american_min |   fair_american_p25 |   fair_american_median |   fair_american_p75 |   fair_american_max |
|:--------------|------------:|---------------:|------------------:|---------------:|--------------------:|--------------------:|-----------------------:|--------------------:|--------------------:|
| 2-team        |         266 |         0.5399 |            0.5642 |         0.6426 |              -179.8 |              -134.6 |                 -129.4 |              -124.4 |              -117.3 |
| 3-team        |         119 |         0.3976 |            0.4261 |         0.4755 |               110.3 |               129.3 |                  134.7 |               139.6 |               151.5 |

Decimal-odds and net-profit views of the same distribution:

| ticket_size   |   fair_profit_min |   fair_profit_p25 |   fair_profit_median |   fair_profit_p75 |   fair_profit_max |   fair_decimal_min |   fair_decimal_median |   fair_decimal_max |
|:--------------|------------------:|------------------:|---------------------:|------------------:|------------------:|-------------------:|----------------------:|-------------------:|
| 2-team        |            0.5561 |            0.7432 |               0.7726 |            0.8039 |            0.8522 |              1.556 |                 1.773 |              1.852 |
| 3-team        |            1.103  |            1.293  |               1.347  |            1.396  |            1.515  |              2.103 |                 2.347 |              2.515 |

## Reading these numbers

A 2-team fair price of, say, -129 means the frozen model considers a 2-team 6-point teaser a break-even proposition at -129, so a book charging more juice than that is charging more than the model's own valuation. Whether the model's valuation is correct is the calibration question answered in Phase 2/2B, not here.

Machine-readable: `data/processed/phase3_ticket_fair_prices.csv`.

