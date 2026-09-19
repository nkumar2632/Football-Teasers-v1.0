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

### 1.1 Two independent classification dimensions

Every leg is classified along **two dimensions that must never be conflated**:

| Dimension | Values | Determined by |
|---|---|---|
| **Geometry class** | `PRIMARY` / `SECONDARY` | the shape of the line, alone |
| **Operational track** | `LIVE` / `PAPER` | the league, plus the geometry class |

**Primary geometry is the same structural geometry in both leagues** (§3). What differs
between leagues is the track, not the geometry.

| Leg | geometry_class | track |
|---|---|---|
| NFL `+2.5 → +8.5` | PRIMARY | LIVE |
| CFB `+2.5 → +8.5` | PRIMARY | PAPER |
| NFL `+4.5 → +10.5` | SECONDARY | PAPER |
| CFB `+4.5 → +10.5` | SECONDARY | PAPER |

### 1.2 Track contents

| Track | Contents |
|---|---|
| **LIVE** | NFL primary geometry only |
| **PAPER / RESEARCH ONLY** | NFL secondary geometry; all college football — *including CFB primary geometry*; the entire 2026 season |

All college football remains paper-only for the entire 2026 v1.0 season. **CFB primary
geometry must nevertheless remain distinguishable from CFB secondary geometry** for
research purposes. Collapsing the two is an implementation error, not a conservative
choice.

No assumed weekly betting volume. Volume is measured prospectively, not assumed.

## 2. Standard teaser

**6 points only.**

## 3. Primary geometry — half-point lines only

The primary geometry below is a structural property of the line. It is the same in the NFL
and in college football. Only the NFL's primary geometry is on the LIVE track (§1).

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

### 5.1 Key numbers — frozen for v1.0

```
KEY_NUMBERS = {3, 7}
```

Exactly `{3, 7}`, in **both** leagues. This is fixed for v1.0.

A key number is **crossed** when the 6-point teaser turns a margin of that size from a loss
or push into a win. Formally: a bet on a team at line `L` wins when `margin + L > 0`, so
teasing `L` to `L + 6` newly covers exactly the signed margins in the half-open interval
`(-L - 6, -L]`. A key number `k` is crossed when `k` or `-k` lies in that interval.

Worked examples:

| Leg | Newly covered margins | Key numbers crossed | Count |
|---|---|---|---|
| `+2.5 → +8.5` | −8 … −3 | 3 and 7 | **both** |
| `−8.5 → −2.5` | 3 … 8 | 3 and 7 | **both** |
| `+1.5 → +7.5` | −7 … −2 | 3 and 7 | **both** |
| `−7.5 → −1.5` | 2 … 7 | 3 and 7 | **both** |
| `+4.5 → +10.5` | −10 … −5 | 7 only | **one** |

All four primary geometries cross both key numbers. `+4.5 → +10.5` is a **one**-key-number
shape under frozen v1.0: it crosses 7, it does not cross 3, and the 10 it passes through
earns nothing.

**10 is NOT a v1.0 key number**, in either league. Whether college football warrants
separate treatment of 10 is a research question only — see `RESEARCH_QUEUE.md` R-03 — and
must not be implemented before the 2027 preseason review.

### 5.2 Provisional key-number bump

| League | Crosses both key numbers | Crosses one |
|---|---|---|
| NFL | +0.07 | +0.04 |
| CFB | +0.04 | +0.02 |

Provisional does not mean editable. **Do not hard-code any proposed CFB bump correction.**

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

1. Identify eligible primary NFL legs — i.e. legs whose geometry class is PRIMARY *and*
   whose track is LIVE, inside the NFL total guardrail. CFB primary legs are primary
   geometry but are on the paper track and never enter this pool.
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
PRIMARY_SPREADS               = {+1.5, +2.5, -7.5, -8.5}   # same set in BOTH leagues
LIVE_LEAGUES                  = {NFL}                      # only the track is NFL-only
TOTAL_GUARDRAIL[NFL]          = 47
TOTAL_GUARDRAIL[CFB]          = 52
KEY_NUMBERS_V1_0              = {3, 7}     # frozen; 10 is NOT a v1.0 key number
KEY_NUMBERS[NFL]              = (3, 7)
KEY_NUMBERS[CFB]              = (3, 7)
BUMP[NFL]                     = both: 0.07, one: 0.04, none: 0.00
BUMP[CFB]                     = both: 0.04, one: 0.02, none: 0.00
TOP_N_LEGS                    = 4
TICKET_SIZES                  = (2, 3)
MIN_LEGS_FOR_ANY_TICKET       = 2
MAX_UNITS_PER_LEG_PER_WEEK    = 2
UNITS_PER_TICKET              = 1
```

Points of written-specification ambiguity, and the exact reading used, are recorded in
[AMBIGUITIES.md](AMBIGUITIES.md). None of them alters the four primary geometries.

Implementation clarifications made after the specification was frozen — the key-number set
(§5.1) and the two-dimensional classification (§1.1) — are recorded in
[CORRECTIONS_LOG.md](CORRECTIONS_LOG.md).
