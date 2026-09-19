# Teaser Model v1.0 — FROZEN SPECIFICATION

**Status:** Frozen for the entire 2026 season.
**Change control:** See [AGENTS.md](AGENTS.md). Only genuine data-entry, source, formula, or
implementation errors may be corrected, and every correction must be logged in
[CORRECTIONS_LOG.md](CORRECTIONS_LOG.md). Research may continue but cannot alter v1.0 until the
2027 preseason review.

This document is the contract. `src/teaser_model_v1/engine/` implements it. Where the two
disagree, the code is wrong.

---

## 1. Scope

One model architecture with league-specific parameters.

| Track | Contents |
|---|---|
| **LIVE** | NFL primary geometry only |
| **PAPER / RESEARCH ONLY** | NFL secondary geometry; all college football; the entire 2026 season |

No assumed weekly betting volume. Volume is measured prospectively, not assumed.

## 2. Standard teaser

**6 points only.**

## 3. Primary NFL geometry — half-point lines only

Eligible underdogs:

| Pre-teaser spread | Teased to |
|---|---|
| +1.5 | +7.5 |
| +2.5 | +8.5 |

Eligible favorites:

| Pre-teaser spread | Teased to |
|---|---|
| -7.5 | -1.5 |
| -8.5 | -2.5 |

Whole-number lines such as `+2` or `-8` are **NOT** primary. They are secondary.

All other shapes are secondary.

## 4. Total guardrails

| League | Guardrail |
|---|---|
| NFL | `total <= 47` |
| CFB | `total <= 52` |

## 5. Probability model

```
sigma  = 0.30 * game_total
P_raw  = standard_normal_CDF(6 / sigma)
```

Provisional key-number bump:

| League | Crosses both key numbers | Crosses one |
|---|---|---|
| NFL | +0.07 | +0.04 |
| CFB | +0.04 | +0.02 |

```
P_est = P_raw + bump
```

Retain full numerical precision internally.

For presentation, round to whole percentages and label the result:

> **model-estimated hit probability**

Do **not** call it an objective or true probability.

## 6. Ticket probability

```
P_ticket = product of constituent leg P_est values
```

## 7. Price / EV

When an actual teaser price is available:

```
profit       = net profit per 1 unit staked
break_even   = 1 / (1 + profit)
EV_per_unit  = P_ticket * profit - (1 - P_ticket)
```

Rank tickets by **internally precise EV**, not by `P_est` alone.

Historical teaser menu prices may be unavailable. **Do NOT invent them.**

If actual historical teaser prices cannot be obtained, historical testing must:

1. test hit rate and calibration directly;
2. calculate fair break-even pricing;
3. provide sensitivity analysis at **explicitly hypothetical** teaser prices.

Hypothetical prices must always be labeled as such.

## 8. Weekly construction

1. Identify eligible primary NFL legs.
2. Rank them by `P_est`.
3. Retain the **top four** eligible primary legs.
4. If fewer than two qualify, **no primary ticket can be constructed.**
5. Display all 2-team and 3-team combinations from those top four.
6. Negative-EV tickets may be displayed/logged, but are **not** model-designated live bets.
7. Live placement eligibility requires **positive EV at the actual offered price**.

## 9. Exposure rule

Flat **1 unit per ticket**.

Maximum aggregate exposure to any individual teaser leg: **2 units per week**.

For live-ticket selection:

- walk positive-EV tickets in descending internally precise EV order;
- add a ticket only if doing so keeps every constituent leg at `<= 2` units aggregate exposure;
- otherwise skip it and continue.

This greedy rule is intentional. **Do NOT replace it with a portfolio optimizer.**

Tie rule:

1. internally precise EV;
2. if truly tied, fewer legs first.

## 10. Placement re-check

Immediately before any real wager, re-check:

- current spread
- teased spread
- geometry
- total
- exact teaser payout

Recalculate `P_est`, break-even, and EV.

If the leg leaves primary geometry, the total exceeds the NFL guardrail, or the ticket becomes
negative EV:

- **discard** the pre-placement ticket;
- **rebuild** from the current board.

Do not automatically substitute another leg.
Do not automatically convert a 3-team ticket into a 2-team ticket.

**"Void"** is reserved for sportsbook settlement after placement.

## 11. Measurement

Keep two tracks separate.

**Market quality:**

- grading line
- placement line
- closing/reference line
- CLV
- line movement
- sportsbook
- exact teaser price obtained

**Model quality:**

- `P_est`
- actual outcome
- calibration by probability bucket
- Brier score
- ROI when a real price exists

**CLV does NOT validate probability calibration.**

Also record every week:

- number of qualifying live-primary NFL legs — **including zero**
- number of positive-EV tickets constructed
- number actually placed

## 12. Historical-data rule

Do not assume a field called `closing_line` is truly the last market price before kickoff.

Track provenance explicitly. Use the terms:

- `archived_reference_line`
- `true_timestamped_close`

only when supported by the source.

**Half-point fidelity is critical.** Any data source that rounds `+2.5` to `+3`, `-7.5` to `-8`,
etc. is unsuitable for this model.

## 13. Constants as implemented

These are the literal values in `src/teaser_model_v1/engine/constants.py`. They are frozen.

```
TEASER_POINTS                 = 6
SIGMA_TOTAL_COEFFICIENT       = 0.30
PRIMARY_NFL_SPREADS           = {+1.5, +2.5, -7.5, -8.5}
TOTAL_GUARDRAIL[NFL]          = 47
TOTAL_GUARDRAIL[CFB]          = 52
KEY_NUMBERS[NFL]              = (3, 7)     # see AMBIGUITIES.md A-1
KEY_NUMBERS[CFB]              = (3, 7)     # see AMBIGUITIES.md A-1
BUMP[NFL]                     = both: 0.07, one: 0.04, none: 0.00
BUMP[CFB]                     = both: 0.04, one: 0.02, none: 0.00
TOP_N_LEGS                    = 4
TICKET_SIZES                  = (2, 3)
MIN_LEGS_FOR_ANY_TICKET       = 2
MAX_UNITS_PER_LEG_PER_WEEK    = 2
UNITS_PER_TICKET              = 1
```

Points of written-specification ambiguity, and the exact reading used, are recorded in
[AMBIGUITIES.md](AMBIGUITIES.md). None of them alters the four primary NFL geometries.
