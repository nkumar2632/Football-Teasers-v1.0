# NFL Teaser v1.0 — 2026 Week 3

🟢 **PLACED** · 🔴 **DISCARD — REBUILD**

|                     |                                                          |
|---------------------|----------------------------------------------------------|
| **Sportsbook**      | SYNTHETIC_BOOK                                           |
| **Graded**          | `2026-09-19T10:00:00-04:00`                              |
| **Re-check**        | DISCARD — REBUILD REQUIRED · `2026-09-20T12:40:00-04:00` |
| **Games scanned**   | 7                                                        |
| **Qualifying legs** | 5                                                        |

> Frozen Teaser Model v1.0. Nothing in this system places a wager.

## Qualifying legs

| Rank | Team | Original → Teased | Total | P_est |
|------|------|-------------------|-------|-------|
| 1    | MIA  | +2.5 → +8.5       | 40.5  | 75.9% |
| 2    | NE   | +1.5 → +7.5       | 42.5  | 75.1% |
| 3    | PHI  | -7.5 → -1.5       | 43.5  | 74.7% |
| 4    | CHI  | +2.5 → +8.5       | 45.5  | 74.0% |
| 5    | SEA  | -8.5 → -2.5       | 46.5  | 73.6% |

Top four retained: **MIA, NE, PHI, CHI**

P_est is a *model-estimated hit probability*, shown to one decimal place. Full precision is preserved in the stored record and listed under Audit.

## Proposed card

**Every ticket below is POSITIVE EV at the offered price.** The frozen selection admits nothing else — a negative-EV ticket can never reach this table.

| Ticket      | Price | P_ticket | Break-even | EV%      | Status            | Stake |
|-------------|-------|----------|------------|----------|-------------------|-------|
| **MIA+NE**  | -120  | 57.0%    | 54.5%      | **4.5%** | 🟢 **POSITIVE_EV** | 1u    |
| **MIA+PHI** | -120  | 56.7%    | 54.5%      | **4.0%** | 🟢 **POSITIVE_EV** | 1u    |
| **NE+PHI**  | -120  | 56.1%    | 54.5%      | **2.9%** | 🟢 **POSITIVE_EV** | 1u    |

Leg exposure: **MIA 2u** · **NE 2u** · **PHI 2u**

Card `card_2026w03_3edca218c507` — **PROPOSED ONLY. This is not a wager.**

## Full ticket board

| Ticket      | Price | P_ticket | Break-even | EV%      | Status        |
|-------------|-------|----------|------------|----------|---------------|
| **MIA+NE**  | -120  | 57.0%    | 54.5%      | **4.5%** | 🟢 POSITIVE_EV |
| **MIA+PHI** | -120  | 56.7%    | 54.5%      | **4.0%** | 🟢 POSITIVE_EV |
| MIA+CHI     | -120  | 56.2%    | 54.5%      | **3.0%** | 🟢 POSITIVE_EV |
| **NE+PHI**  | -120  | 56.1%    | 54.5%      | **2.9%** | 🟢 POSITIVE_EV |
| MIA+NE+PHI  | +140  | 42.6%    | 41.7%      | **2.3%** | 🟢 POSITIVE_EV |
| NE+CHI      | -120  | 55.6%    | 54.5%      | **1.9%** | 🟢 POSITIVE_EV |
| PHI+CHI     | -120  | 55.3%    | 54.5%      | **1.4%** | 🟢 POSITIVE_EV |
| MIA+NE+CHI  | +140  | 42.2%    | 41.7%      | **1.3%** | 🟢 POSITIVE_EV |
| MIA+PHI+CHI | +140  | 42.0%    | 41.7%      | **0.7%** | 🟢 POSITIVE_EV |
| NE+PHI+CHI  | +140  | 41.5%    | 41.7%      | -0.4%    | ⚪ NEGATIVE_EV |

Every constructible ticket is shown, including negative-EV ones. **"Best available" does not mean positive EV.** Bold ticket = on the proposed card.

## Re-check

🔴 **DISCARD — REBUILD** — re-checked `2026-09-20T12:40:00-04:00`

| Ticket  | Verdict                      | Reason                                                                                                                     |
|---------|------------------------------|----------------------------------------------------------------------------------------------------------------------------|
| MIA+NE  | 🔴 DISCARD — REBUILD REQUIRED | 2026_03_NYJ_NE-NE: line moved to 3.0, which is not primary geometry; 2026_03_NYJ_NE-NE: leg is no longer on the LIVE track |
| MIA+PHI | 🟢 VALIDATED                  | -                                                                                                                          |
| PHI+NE  | 🔴 DISCARD — REBUILD REQUIRED | 2026_03_NYJ_NE-NE: line moved to 3.0, which is not primary geometry; 2026_03_NYJ_NE-NE: leg is no longer on the LIVE track |

> Discarded tickets are **not** substituted and **not** downgraded. The card was rebuilt from the current board: `card_2026w03_ed0ac031bc53`.

## Placement

🟢 **ACTUALLY PLACED** — as recorded manually by the operator.

| Ticket  | Book           | Odds | Stake | Placed at                 | Designation      |
|---------|----------------|------|-------|---------------------------|------------------|
| MIA+PHI | SYNTHETIC_BOOK | -120 | 1.0   | 2026-09-20T12:45:00-04:00 | MODEL_DESIGNATED |

## Settlement

| Placement                | Model result | Book settlement | P/L (units)        | Agree |
|--------------------------|--------------|-----------------|--------------------|-------|
| plc_2026w03_618e44810ee4 | WIN          | WIN             | 0.8333333333333334 | yes   |

Model grade and sportsbook settlement are recorded separately and are never reconciled by a generic rule.

---

## Audit

| field                 | value                       |
|-----------------------|-----------------------------|
| card id               | `card_2026w03_3edca218c507` |
| market snapshot       | `mkt_2026w03_97e29d3c6643`  |
| teaser price snapshot | `prc_2026w03_1032353df2e1`  |
| sportsbook / source   | SYNTHETIC_BOOK              |
| graded at             | `2026-09-19T10:00:00-04:00` |
| report generated      | `2026-09-19T22:59:22+00:00` |
| card status           | PROPOSED                    |
| games scanned         | 7                           |

Source notes: rehearsal grading

### Full-precision legs

| Leg id                | Opp | Total | P_raw              | Bump | P_est              |
|-----------------------|-----|-------|--------------------|------|--------------------|
| `2026_03_BUF_MIA-MIA` | BUF | 40.5  | 0.6892858751269062 | 0.07 | 0.7592858751269063 |
| `2026_03_NYJ_NE-NE`   | NYJ | 42.5  | 0.6810325947045215 | 0.07 | 0.7510325947045215 |
| `2026_03_DAL_PHI-PHI` | DAL | 43.5  | 0.6771593818727903 | 0.07 | 0.7471593818727904 |
| `2026_03_GB_CHI-CHI`  | GB  | 45.5  | 0.6698722507821999 | 0.07 | 0.7398722507822    |
| `2026_03_SF_SEA-SEA`  | SF  | 46.5  | 0.6664412874896358 | 0.07 | 0.7364412874896358 |

### Full-precision tickets

| Ticket      | P_ticket            | Break-even         | EV%    |
|-------------|---------------------|--------------------|--------|
| MIA+NE      | 0.5702484409190538  | 0.5454545454545454 | 4.55%  |
| MIA+PHI     | 0.56730756512456    | 0.5454545454545454 | 4.01%  |
| MIA+CHI     | 0.5617745494172766  | 0.5454545454545454 | 2.99%  |
| NE+PHI      | 0.5611410492257483  | 0.5454545454545454 | 2.88%  |
| MIA+NE+PHI  | 0.42606647263100267 | 0.4166666666666667 | 2.26%  |
| NE+CHI      | 0.5556681762548301  | 0.5454545454545454 | 1.87%  |
| PHI+CHI     | 0.5528024935592587  | 0.5454545454545454 | 1.35%  |
| MIA+NE+CHI  | 0.42191099748782074 | 0.4166666666666667 | 1.26%  |
| MIA+PHI+CHI | 0.41973512509447775 | 0.4166666666666667 | 0.74%  |
| NE+PHI+CHI  | 0.41517269109693966 | 0.4166666666666667 | -0.36% |

### Exposure by leg id

| Leg id                | Units |
|-----------------------|-------|
| `2026_03_BUF_MIA-MIA` | 2     |
| `2026_03_DAL_PHI-PHI` | 2     |
| `2026_03_NYJ_NE-NE`   | 2     |

Presentation only: this report formats the stored card and derives no model value. Probabilities, EV, selection and exposure are read from `card_2026w03_3edca218c507` exactly as the grading layer wrote them.
