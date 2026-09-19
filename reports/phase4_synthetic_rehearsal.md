# Phase 4 — synthetic end-to-end rehearsal

**Every number below is FABRICATED.** No real 2026 market data was pulled, no wager was placed or simulated, and the frozen model was not touched. The purpose is to prove the audit trail survives a full week, including a market move and a price move.

Synthetic week: NFL 2026 Week 3, book `SYNTHETIC_BOOK`.

## Step 1 — grading-time market and price snapshots

- market snapshot `mkt_2026w03_97e29d3c6643` captured `2026-09-19T10:00:00-04:00`
- price snapshot `prc_2026w03_1032353df2e1`: 2-team **-120**, 3-team **+140**

Board offered to the model:

| Game | Side | Spread | Total | Note |
|---|---|---|---|---|
| BUF @ MIA | MIA | 2.5 | 40.5 | primary +2.5, low total -> highest P_est |
| NYJ @ NE | NE | 1.5 | 42.5 | primary +1.5 |
| DAL @ PHI | PHI | -7.5 | 43.5 | primary -7.5 |
| GB @ CHI | CHI | 2.5 | 45.5 | primary +2.5 |
| SF @ SEA | SEA | -8.5 | 46.5 | primary -8.5, highest total -> lowest P_est |
| KC @ DEN | DEN | 2.5 | 49.5 | primary shape but total 49.5 FAILS the <=47 cap |
| LV @ LAC | LAC | -3.5 | 44.5 | not primary geometry |

## Step 2 — grading-time card

Card `card_2026w03_3edca218c507` — status **PROPOSED**

- qualifying primary legs: **5** (the 49.5-total game was correctly excluded by the guardrail, and the -3.5 line is not primary geometry)
- top four retained: MIA, NE, PHI, CHI
- tickets constructed: **10** (positive EV: 9, negative EV: 1)
- proposed (model-designated): **3**

| Ticket | Legs | P_ticket | Offered | EV% | Status | On card |
|---|---|---|---|---|---|---|
| MIA+NE | 2 | 57.0% | -120 | 4.55% | POSITIVE_EV | YES |
| MIA+PHI | 2 | 56.7% | -120 | 4.01% | POSITIVE_EV | YES |
| MIA+CHI | 2 | 56.2% | -120 | 2.99% | POSITIVE_EV | no |
| NE+PHI | 2 | 56.1% | -120 | 2.88% | POSITIVE_EV | YES |
| MIA+NE+PHI | 3 | 42.6% | 140 | 2.26% | POSITIVE_EV | no |
| NE+CHI | 2 | 55.6% | -120 | 1.87% | POSITIVE_EV | no |
| PHI+CHI | 2 | 55.3% | -120 | 1.35% | POSITIVE_EV | no |
| MIA+NE+CHI | 3 | 42.2% | 140 | 1.26% | POSITIVE_EV | no |
| MIA+PHI+CHI | 3 | 42.0% | 140 | 0.74% | POSITIVE_EV | no |
| NE+PHI+CHI | 3 | 41.5% | 140 | -0.36% | NEGATIVE_EV | no |

Both positive-EV and negative-EV tickets are displayed. Only positive-EV tickets reach the proposed card, and the 2-unit cap bounds aggregate leg exposure.

Exposure on the proposed card: `2026_03_BUF_MIA-MIA` 2u, `2026_03_DAL_PHI-PHI` 2u, `2026_03_NYJ_NE-NE` 2u

## Step 3 — the board moves before placement

New market snapshot `mkt_2026w03_be2b4033a527` captured `2026-09-20T12:40:00-04:00`.
New price snapshot `prc_2026w03_18835ed5ce4d`: 2-team **-120** (unchanged), 3-team **+140 -> +120**.

Three independent changes, chosen to exercise three different failure paths:

1. **NE +1.5 -> +3.0** — the leg leaves primary geometry entirely.
2. **CHI total 45.5 -> 47.5** — the leg breaches the total guardrail.
3. **The 3-team teaser price worsens, +140 -> +120** — enough to turn a 3-team ticket negative EV on price alone, while the 2-team menu is unchanged so a validated ticket survives to be placed.

> The earlier snapshots are **not** modified. Both remain on disk under their own ids; a later capture is always a new record.

## Step 4 — placement-time re-check

Re-check `rck_2026w03_d6fd890a4caf` — overall verdict: **DISCARD — REBUILD REQUIRED**

| Ticket | Verdict | Reason |
|---|---|---|
| 2026_03_BUF_MIA-MIA|2026_03_NYJ_NE-NE | DISCARD — REBUILD REQUIRED | 2026_03_NYJ_NE-NE: line moved to 3.0, which is not primary geometry; 2026_03_NYJ_NE-NE: leg is no longer on the LIVE track |
| 2026_03_BUF_MIA-MIA|2026_03_DAL_PHI-PHI | VALIDATED | - |
| 2026_03_DAL_PHI-PHI|2026_03_NYJ_NE-NE | DISCARD — REBUILD REQUIRED | 2026_03_NYJ_NE-NE: line moved to 3.0, which is not primary geometry; 2026_03_NYJ_NE-NE: leg is no longer on the LIVE track |

Discarded tickets were **not** substituted with another team and **not** downgraded from 3-team to 2-team. The word used is *discard*; "void" is reserved for a sportsbook settling a wager that was actually placed.

## Step 5 — rebuild from the current board

Rebuilt card `card_2026w03_ed0ac031bc53` from snapshot `mkt_2026w03_be2b4033a527`.

- qualifying primary legs now: **3** (MIA, PHI, SEA)
- tickets constructed: **4**, positive EV: **3**
- proposed: **3**

| Ticket | Legs | P_ticket | Offered | EV% | Status | On card |
|---|---|---|---|---|---|---|
| MIA+PHI | 2 | 56.7% | -120 | 4.01% | POSITIVE_EV | YES |
| MIA+SEA | 2 | 55.9% | -120 | 2.51% | POSITIVE_EV | YES |
| PHI+SEA | 2 | 55.0% | -120 | 0.88% | POSITIVE_EV | YES |
| MIA+PHI+SEA | 3 | 41.8% | 120 | -8.09% | NEGATIVE_EV | no |

The worsened 3-team price is visible here: every 3-team ticket is re-evaluated at +120 instead of +140, and only tickets still positive EV reach the rebuilt card.

## Step 6 — explicit placement recording

Tickets that survived the re-check: `2026_03_BUF_MIA-MIA|2026_03_DAL_PHI-PHI`

Guard rails exercised before any successful record:

- a ticket DISCARDED at re-check is refused: `ticket 2026_03_BUF_MIA-MIA|2026_03_NYJ_NE-NE was DISCARDED at re-check rck_2026w03_d6fd890a4caf: 2026_03_NYJ_NE-NE: line moved to 3.0, which is not primary geometry. A discarded ticket is never reused, substituted or downgraded — rebuild from the current board.`
- recorded placement `plc_2026w03_ff9ca5d6c62c` for ticket `2026_03_BUF_MIA-MIA|2026_03_DAL_PHI-PHI` at SYNTHETIC_BOOK -120, stake 1.0u
- the 2-unit exposure cap refuses a further placement: `this placement would exceed the frozen 2-unit weekly cap on 2026_03_BUF_MIA-MIA (3.0 units), 2026_03_DAL_PHI-PHI (3.0 units). Record it as EXTERNAL_NON_MODEL if you placed it outside the model.`

> **PROPOSED is never PLACED.** Every row above exists only because an operator explicitly recorded it. This software submitted nothing to any sportsbook.

## Step 7 — market-quality trail

| Label | Spread | Total | Observed at | Snapshot |
|---|---|---|---|---|
| grading_line | 2.5 | 40.5 | 2026-09-19T10:00:00-04:00 | `mkt_2026w03_97e29d3c6643` |
| placement_line | 2.5 | 40.5 | 2026-09-20T12:45:00-04:00 | `mkt_2026w03_be2b4033a527` |
| final_observed_market_snapshot | 2.5 | 40.5 | 2026-09-20T12:58:00-04:00 | `mkt_2026w03_be2b4033a527` |

Line movement grading -> final observed: **0.0**.

> CLV is not computed: the later observation is a final_observed_market_snapshot, not a documented close. Computing CLV against it would overstate what the provenance supports.

## Step 8 — settlement

| Leg | Teased | Final margin | Model result |
|---|---|---|---|
| 2026_03_BUF_MIA-MIA | 8.5 | 3 | WIN |
| 2026_03_DAL_PHI-PHI | -1.5 | 3 | WIN |

No leg graded PUSH, as the half-point geometry guarantees; the settlement code raises rather than absorbing one if it ever appears.

Settlement `stl_2026w03_9be25fc3e1b2`:

| Field | Value |
|---|---|
| model_ticket_result | **WIN** |
| book_settlement | **WIN** |
| profit_loss_units | 0.8333333333333334 |
| results_agree | True |

The model grade and the sportsbook settlement are stored in **separate fields** even when they agree, because they are different claims: one is what frozen v1.0 says happened, the other is what the book actually did.

When they disagree — a book voiding or cancelling a wager the model graded a winner — both stand as recorded, the P/L follows the book, and no generic reconciliation rule is invented. `book_settlement` accepts VOID and CANCELLED for exactly that case; a dedicated test covers it.

## Step 9 — append-only season ledger

| Metric | Value |
|---|---|
| season | 2026 |
| weeks_recorded | 2 |
| weeks_with_zero_qualifying_legs | 1 |
| weeks_with_no_constructible_ticket | 1 |
| weeks_with_zero_placements | 1 |
| total_qualifying_legs | 5 |
| total_positive_ev_tickets | 9 |
| total_proposed_tickets | 3 |
| total_placed_tickets | 1 |
| total_units_staked | 1.0 |
| total_wins | 1 |
| total_losses | 0 |
| total_profit_loss_units | 0.8333333333333334 |
| model_expected_wins | 0.56730756512456 |

Week 4 was recorded with **zero** qualifying legs and zero bets. Empty weeks appear in the ledger exactly like active ones — omitting them would build survivorship bias into the prospective record by construction.

## Step 10 — audit trail

Every record written during this rehearsal, none of which overwrote another:

| Kind | Record id |
|---|---|
| market_snapshot | `mkt_2026w03_97e29d3c6643` |
| teaser_price_snapshot | `prc_2026w03_1032353df2e1` |
| market_snapshot | `mkt_2026w03_be2b4033a527` |
| teaser_price_snapshot | `prc_2026w03_18835ed5ce4d` |
| weekly_card | `card_2026w03_3edca218c507` |
| recheck | `rck_2026w03_d6fd890a4caf` |
| weekly_card | `card_2026w03_ed0ac031bc53` |
| settlement | `stl_2026w03_9be25fc3e1b2` |
| placement | `plc_2026w03_ff9ca5d6c62c` |
| placement | `plc_2026w03_736e2b5c3dd8` |

Re-offering the grading snapshot returned **already present (no-op)** — content-addressed ids make duplicate capture idempotent, and differing content can never collide with an earlier record.

## Weekly report

Rendered to `reports/live/nfl_2026_week_03_rehearsal.md`.

---

**Rehearsal complete.** Every transition the live system must handle was exercised against fabricated data: grading, a geometry break, a guardrail breach, a price move, discard, rebuild, explicit placement, a refused over-cap placement, and a settlement where the book disagreed with the model. No real market data was used and no wager was placed.

