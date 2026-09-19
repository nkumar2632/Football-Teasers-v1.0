# NFL 2026 Week 3 — Teaser Model v1.0 live card

Report generated: `2026-09-19T18:36:56+00:00`

> Frozen Teaser Model v1.0. Nothing in this system places a wager.

## Market snapshot

| field                   | value                     |
|-------------------------|---------------------------|
| sportsbook / source     | SYNTHETIC_BOOK            |
| market snapshot         | mkt_2026w03_97e29d3c6643  |
| teaser price snapshot   | prc_2026w03_1032353df2e1  |
| graded at               | 2026-09-19T10:00:00-04:00 |
| games scanned           | 7                         |
| qualifying primary legs | 5                         |

## Primary legs

| Rank | Team | Opp | Original | Teased | Total | P_est |
|------|------|-----|----------|--------|-------|-------|
| 1    | MIA  | BUF | 2.5      | 8.5    | 40.5  | 76%   |
| 2    | NE   | NYJ | 1.5      | 7.5    | 42.5  | 75%   |
| 3    | PHI  | DAL | -7.5     | -1.5   | 43.5  | 75%   |
| 4    | CHI  | GB  | 2.5      | 8.5    | 45.5  | 74%   |
| 5    | SEA  | SF  | -8.5     | -2.5   | 46.5  | 74%   |

P_est shown as a whole percent: *model-estimated hit probability*.

Top four retained for construction: MIA, NE, PHI, CHI

## Ticket board

| Ticket      | Legs | P_ticket | Offered | Break-even | EV%    | Status      | On card |
|-------------|------|----------|---------|------------|--------|-------------|---------|
| MIA+NE      | 2    | 57.0%    | -120    | 54.5%      | 4.55%  | POSITIVE_EV | YES     |
| MIA+PHI     | 2    | 56.7%    | -120    | 54.5%      | 4.01%  | POSITIVE_EV | YES     |
| MIA+CHI     | 2    | 56.2%    | -120    | 54.5%      | 2.99%  | POSITIVE_EV | no      |
| NE+PHI      | 2    | 56.1%    | -120    | 54.5%      | 2.88%  | POSITIVE_EV | YES     |
| MIA+NE+PHI  | 3    | 42.6%    | 140     | 41.7%      | 2.26%  | POSITIVE_EV | no      |
| NE+CHI      | 2    | 55.6%    | -120    | 54.5%      | 1.87%  | POSITIVE_EV | no      |
| PHI+CHI     | 2    | 55.3%    | -120    | 54.5%      | 1.35%  | POSITIVE_EV | no      |
| MIA+NE+CHI  | 3    | 42.2%    | 140     | 41.7%      | 1.26%  | POSITIVE_EV | no      |
| MIA+PHI+CHI | 3    | 42.0%    | 140     | 41.7%      | 0.74%  | POSITIVE_EV | no      |
| NE+PHI+CHI  | 3    | 41.5%    | 140     | 41.7%      | -0.36% | NEGATIVE_EV | no      |

Every constructible ticket is shown, including negative-EV ones. **"Best available" does not mean positive EV.**

## Proposed live card

| Ticket  | Legs | Stake  | EV%   | Offered |
|---------|------|--------|-------|---------|
| MIA+NE  | 2    | 1 unit | 4.55% | -120    |
| MIA+PHI | 2    | 1 unit | 4.01% | -120    |
| NE+PHI  | 2    | 1 unit | 2.88% | -120    |

Aggregate leg exposure:

| Leg                 | Units |
|---------------------|-------|
| 2026_03_BUF_MIA-MIA | 2     |
| 2026_03_DAL_PHI-PHI | 2     |
| 2026_03_NYJ_NE-NE   | 2     |

Card id: `card_2026w03_3edca218c507` — **PROPOSED ONLY. This is not a wager.**

## Re-check status

**DISCARD — REBUILD REQUIRED** — re-checked at `2026-09-20T12:40:00-04:00`

| Ticket                                  | Verdict                    | Reason                                                                                                                     |
|-----------------------------------------|----------------------------|----------------------------------------------------------------------------------------------------------------------------|
| 2026_03_BUF_MIA-MIA|2026_03_NYJ_NE-NE   | DISCARD — REBUILD REQUIRED | 2026_03_NYJ_NE-NE: line moved to 3.0, which is not primary geometry; 2026_03_NYJ_NE-NE: leg is no longer on the LIVE track |
| 2026_03_BUF_MIA-MIA|2026_03_DAL_PHI-PHI | VALIDATED                  | -                                                                                                                          |
| 2026_03_DAL_PHI-PHI|2026_03_NYJ_NE-NE   | DISCARD — REBUILD REQUIRED | 2026_03_NYJ_NE-NE: line moved to 3.0, which is not primary geometry; 2026_03_NYJ_NE-NE: leg is no longer on the LIVE track |

New market snapshot: `mkt_2026w03_be2b4033a527`
New price snapshot: `prc_2026w03_18835ed5ce4d`

> Discarded tickets are **not** substituted and **not** downgraded. The card was rebuilt from the current board: `card_2026w03_ed0ac031bc53`.

## Placement status

| Placement                | Ticket                                  | Book           | Odds | Stake | Placed at                 | Designation      |
|--------------------------|-----------------------------------------|----------------|------|-------|---------------------------|------------------|
| plc_2026w03_618e44810ee4 | 2026_03_BUF_MIA-MIA|2026_03_DAL_PHI-PHI | SYNTHETIC_BOOK | -120 | 1.0   | 2026-09-20T12:45:00-04:00 | MODEL_DESIGNATED |

**ACTUALLY PLACED** — as recorded manually by the operator.

## Settlement

| Placement                | Model result | Book settlement | P/L (units)        | Agree |
|--------------------------|--------------|-----------------|--------------------|-------|
| plc_2026w03_618e44810ee4 | WIN          | WIN             | 0.8333333333333334 | yes   |

Model grade and sportsbook settlement are recorded separately and are never reconciled by a generic rule.

