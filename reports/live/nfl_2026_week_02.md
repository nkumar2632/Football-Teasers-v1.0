# NFL Teaser v1.0 — 2026 Week 2

🔵 **SHADOW — NOT PLACED** · 🟡 **PENDING RECHECK**

|                     |                             |
|---------------------|-----------------------------|
| **Sportsbook**      | USER_SPORTSBOOK_SCREENSHOT  |
| **Graded**          | `2026-09-19T21:51:41+00:00` |
| **Re-check**        | NOT YET RECHECKED           |
| **Games scanned**   | 15                          |
| **Qualifying legs** | 4                           |

> Frozen Teaser Model v1.0. Nothing in this system places a wager.

## Qualifying legs

| Rank | Team | Original → Teased | Total | P_est |
|------|------|-------------------|-------|-------|
| 1    | TB   | -8.5 → -2.5       | 41.5  | 75.5% |
| 2    | ATL  | +2.5 → +8.5       | 43.5  | 74.7% |
| 3    | CIN  | +2.5 → +8.5       | 45.5  | 74.0% |
| 4    | BAL  | -8.5 → -2.5       | 46    | 73.8% |

Top four retained: **TB, ATL, CIN, BAL**

P_est is a *model-estimated hit probability*, shown to one decimal place. Full precision is preserved in the stored record and listed under Audit.

## Proposed card

**Every ticket below is POSITIVE EV at the offered price.** The frozen selection admits nothing else — a negative-EV ticket can never reach this table.

| Ticket         | Price | P_ticket | Break-even | EV%       | Status            | Stake |
|----------------|-------|----------|------------|-----------|-------------------|-------|
| **TB+ATL+CIN** | +170  | 41.7%    | 37.0%      | **12.7%** | 🟢 **POSITIVE_EV** | 1u    |
| **TB+ATL+BAL** | +170  | 41.6%    | 37.0%      | **12.4%** | 🟢 **POSITIVE_EV** | 1u    |
| **CIN+BAL**    | -110  | 54.6%    | 52.4%      | **4.3%**  | 🟢 **POSITIVE_EV** | 1u    |

Leg exposure: **TB 2u** · **ATL 2u** · **CIN 2u** · **BAL 2u**

Card `card_2026w02_492bb1ded5b3` — **PROPOSED ONLY. This is not a wager.**

## Full ticket board

| Ticket         | Price | P_ticket | Break-even | EV%       | Status        |
|----------------|-------|----------|------------|-----------|---------------|
| **TB+ATL+CIN** | +170  | 41.7%    | 37.0%      | **12.7%** | 🟢 POSITIVE_EV |
| **TB+ATL+BAL** | +170  | 41.6%    | 37.0%      | **12.4%** | 🟢 POSITIVE_EV |
| TB+CIN+BAL     | +170  | 41.2%    | 37.0%      | **11.3%** | 🟢 POSITIVE_EV |
| ATL+CIN+BAL    | +170  | 40.8%    | 37.0%      | **10.2%** | 🟢 POSITIVE_EV |
| TB+ATL         | -110  | 56.4%    | 52.4%      | **7.7%**  | 🟢 POSITIVE_EV |
| TB+CIN         | -110  | 55.9%    | 52.4%      | **6.7%**  | 🟢 POSITIVE_EV |
| TB+BAL         | -110  | 55.7%    | 52.4%      | **6.4%**  | 🟢 POSITIVE_EV |
| ATL+CIN        | -110  | 55.3%    | 52.4%      | **5.5%**  | 🟢 POSITIVE_EV |
| ATL+BAL        | -110  | 55.2%    | 52.4%      | **5.3%**  | 🟢 POSITIVE_EV |
| **CIN+BAL**    | -110  | 54.6%    | 52.4%      | **4.3%**  | 🟢 POSITIVE_EV |

Every constructible ticket is shown, including negative-EV ones. **"Best available" does not mean positive EV.** Bold ticket = on the proposed card.

## Re-check

🟡 **NOT YET RECHECKED**

| Proposed ticket | Verdict   |
|-----------------|-----------|
| TB+ATL+CIN      | 🟡 PENDING |
| TB+ATL+BAL      | 🟡 PENDING |
| CIN+BAL         | 🟡 PENDING |

> The card above was graded against `mkt_2026w02_8ccd64d8fae1` at `2026-09-19T21:51:41+00:00`. **Treat it as stale until re-checked against a current snapshot.**

## Placement

🔵 **NOT PLACED — nothing has been wagered**

A proposed card is never a placement. Nothing counts as wagered until it is explicitly recorded.

---

## All 6-point teaser legs

⚪ **RESEARCH VIEW — NOT AN ELIGIBILITY LIST.** Every side on the board, teased 6 points through the frozen engine. This table feeds nothing: it does not affect the top-four cut, ticket construction, EV, exposure or the proposed card, and **no row here can become live-eligible, whatever its P_est.**

| Team    | Original → Teased | Total | Keys | P_est   | Geometry  | Track   | Exclusion reason                                                    |
|---------|-------------------|-------|------|---------|-----------|---------|---------------------------------------------------------------------|
| **TB**  | -8.5 → -2.5       | 41.5  | 2    | 75.5%   | PRIMARY   | 🟢 LIVE  | —                                                                   |
| **ATL** | +2.5 → +8.5       | 43.5  | 2    | 74.7%   | PRIMARY   | 🟢 LIVE  | —                                                                   |
| **CIN** | +2.5 → +8.5       | 45.5  | 2    | 74.0%   | PRIMARY   | 🟢 LIVE  | —                                                                   |
| **BAL** | -8.5 → -2.5       | 46    | 2    | 73.8%   | PRIMARY   | 🟢 LIVE  | —                                                                   |
| PHI     | -7 → -1           | 39    | 2    | 76.6% ‡ | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (whole-number line)                              |
| NYJ     | +3 → +9           | 44.5  | 2    | 74.3% ‡ | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (whole-number line)                              |
| JAX     | +3 → +9           | 45.5  | 2    | 74.0% ‡ | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (whole-number line)                              |
| TEN     | +7 → +13          | 39    | 1    | 73.6% ‡ | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (whole-number line)                              |
| LA      | -7 → -1           | 48    | 2    | 73.2% ‡ | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (whole-number line) · FAILS TOTAL GUARDRAIL      |
| ARI     | +4 → +10          | 41    | 1    | 72.7% ‡ | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (whole-number line)                              |
| SEA     | -4 → +2           | 41    | 1    | 72.7% ‡ | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (whole-number line)                              |
| NE      | -5 → +1           | 41.5  | 1    | 72.5% ‡ | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (whole-number line)                              |
| PIT     | +5 → +11          | 41.5  | 1    | 72.5% ‡ | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (whole-number line)                              |
| CAR     | -2.5 → +3.5       | 43.5  | 1    | 71.7%   | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (other half-point shape)                         |
| LAC     | -6.5 → -0.5       | 43.5  | 1    | 71.7%   | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (other half-point shape)                         |
| LV      | +6.5 → +12.5      | 43.5  | 1    | 71.7%   | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (other half-point shape)                         |
| GB      | -3 → +3           | 44.5  | 1    | 71.3% ‡ | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (whole-number line)                              |
| DEN     | -3 → +3           | 45.5  | 1    | 71.0% ‡ | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (whole-number line)                              |
| HOU     | -2.5 → +3.5       | 45.5  | 1    | 71.0%   | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (other half-point shape)                         |
| IND     | +6.5 → +12.5      | 46.5  | 1    | 70.6%   | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (other half-point shape)                         |
| KC      | -6.5 → -0.5       | 46.5  | 1    | 70.6%   | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (other half-point shape)                         |
| CHI     | -4.5 → +1.5       | 48    | 1    | 70.2%   | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (other half-point shape) · FAILS TOTAL GUARDRAIL |
| MIN     | +4.5 → +10.5      | 48    | 1    | 70.2%   | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (other half-point shape) · FAILS TOTAL GUARDRAIL |
| NYG     | +7 → +13          | 48    | 1    | 70.2% ‡ | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (whole-number line) · FAILS TOTAL GUARDRAIL      |
| DAL     | -4 → +2           | 50.5  | 1    | 69.4% ‡ | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (whole-number line) · FAILS TOTAL GUARDRAIL      |
| WAS     | +4 → +10          | 50.5  | 1    | 69.4% ‡ | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (whole-number line) · FAILS TOTAL GUARDRAIL      |
| CLE     | +8.5 → +14.5      | 41.5  | 0    | 68.5%   | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (other half-point shape)                         |
| MIA     | +13 → +19         | 45    | 0    | 67.2% ‡ | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (whole-number line)                              |
| SF      | -13 → -7          | 45    | 0    | 67.2% ‡ | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (whole-number line)                              |
| NO      | +8.5 → +14.5      | 46    | 0    | 66.8%   | SECONDARY | ⚪ PAPER | SECONDARY GEOMETRY (other half-point shape)                         |

‡ **RESEARCH P_est — PUSH SETTLEMENT NOT MODELED.** The teased line lands on a whole number, so the leg can push. v1.0 prices no book-specific secondary push rule, so that P_est is a research figure and not a settlement-accurate estimate.

|                             | Leg                | P_est | Classification      |
|-----------------------------|--------------------|-------|---------------------|
| Highest-P_est **primary**   | **TB** -8.5 → -2.5 | 75.5% | 🟢 PRIMARY / LIVE    |
| Highest-P_est **secondary** | PHI -7 → -1 ‡      | 76.6% | ⚪ SECONDARY / PAPER |

**Secondary legs with a higher P_est than a leg on the live board: 3** — PHI 76.6% ‡, NYJ 74.3% ‡, JAX 74.0% ‡.

> This is an observation about two different populations, **not** a finding that the model is mis-specified and **not** a reason to promote anything. A higher P_est on a secondary shape does not make it eligible: eligibility is geometry plus track, never P_est. Most of these sit on a whole number and can push, which v1.0 does not price — so the comparison is not even like for like. If it is worth pursuing it belongs in `RESEARCH_QUEUE.md` for the 2027 preseason review.

---

## Audit

| field                 | value                       |
|-----------------------|-----------------------------|
| card id               | `card_2026w02_492bb1ded5b3` |
| market snapshot       | `mkt_2026w02_8ccd64d8fae1`  |
| teaser price snapshot | `prc_2026w02_d29ff0515315`  |
| sportsbook / source   | USER_SPORTSBOOK_SCREENSHOT  |
| graded at             | `2026-09-19T21:51:41+00:00` |
| report generated      | `2026-09-19T22:58:36+00:00` |
| card status           | PROPOSED                    |
| games scanned         | 15                          |

Source notes: Tonight's grading snapshot from real-book screenshots. NO placement-time recheck performed. Nothing placed.

### Full-precision legs

| Leg id                | Opp | Total | P_raw              | Bump | P_est              |
|-----------------------|-----|-------|--------------------|------|--------------------|
| `2026_02_CLE_TB-TB`   | CLE | 41.5  | 0.6850713499837193 | 0.07 | 0.7550713499837194 |
| `2026_02_CAR_ATL-ATL` | CAR | 43.5  | 0.6771593818727903 | 0.07 | 0.7471593818727904 |
| `2026_02_CIN_HOU-CIN` | HOU | 45.5  | 0.6698722507821999 | 0.07 | 0.7398722507822    |
| `2026_02_NO_BAL-BAL`  | NO  | 46    | 0.6681398851771989 | 0.07 | 0.738139885177199  |

### Full-precision tickets

| Ticket      | P_ticket            | Break-even          | EV%    |
|-------------|---------------------|---------------------|--------|
| TB+ATL+CIN  | 0.4174053250861558  | 0.37037037037037035 | 12.70% |
| TB+ATL+BAL  | 0.4164279960570443  | 0.37037037037037035 | 12.44% |
| TB+CIN+BAL  | 0.41236652608064744 | 0.37037037037037035 | 11.34% |
| ATL+CIN+BAL | 0.4080455691215005  | 0.37037037037037035 | 10.17% |
| TB+ATL      | 0.5641586431236891  | 0.5238095238095238  | 7.70%  |
| TB+CIN      | 0.5586563392136087  | 0.5238095238095238  | 6.65%  |
| TB+BAL      | 0.5573482795775753  | 0.5238095238095238  | 6.40%  |
| ATL+CIN     | 0.5528024935592587  | 0.5238095238095238  | 5.54%  |
| ATL+BAL     | 0.5515081403446485  | 0.5238095238095238  | 5.29%  |
| CIN+BAL     | 0.5461292182381688  | 0.5238095238095238  | 4.26%  |

### Exposure by leg id

| Leg id                | Units |
|-----------------------|-------|
| `2026_02_CAR_ATL-ATL` | 2     |
| `2026_02_CIN_HOU-CIN` | 2     |
| `2026_02_CLE_TB-TB`   | 2     |
| `2026_02_NO_BAL-BAL`  | 2     |

Presentation only: this report formats the stored card and derives no model value. Probabilities, EV, selection and exposure are read from `card_2026w02_492bb1ded5b3` exactly as the grading layer wrote them.
