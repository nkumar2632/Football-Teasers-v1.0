# NFL 2026 Week 2 — REAL-BOOK SHADOW GRADING

> **PROPOSED SHADOW CARD — NOT PLACED.** Nothing in this repository places a wager.
> Actual placements: **0**. Actual units staked: **0**.

| | |
|---|---|
| Market snapshot | **`mkt_2026w02_8ccd64d8fae1`** |
| Teaser price snapshot | **`prc_2026w02_d29ff0515315`** |
| Card | **`card_2026w02_492bb1ded5b3`** — status **PROPOSED** |
| Source | `user sportsbook screenshot` |
| Captured at | `2026-09-19T14:50:00-04:00` |
| Raw source | 4 attached screenshots: Sun 9/20 + Mon 9/21 board, and the 2-6T teaser payout menu |
| Graded at | `2026-09-19T21:51:41+00:00` |
| Re-check | **NOT PERFORMED** — tonight's grading snapshot only |

The earlier nflverse provisional snapshot `mkt_2026w02_f544808f1a87` is **untouched**.
Records are append-only and content-addressed; this is a new snapshot beside it, not a
replacement. Both remain in `data/live/snapshots/`.

---

## 1. Extracted market — 15 games, 30 sides

Transcribed from the screenshots exactly as displayed. **No consensus, nflverse or
search-derived value was substituted anywhere.** Prices next to each spread are the
sportsbook's own juice and are recorded in `raw_source_value`.

| Kickoff (ET) | Game | Away | Home | Total |
|---|---|---|---|---:|
| Sun 1:00 | GB @ NYJ | GB −3 (−120) | NYJ +3 (+100) | 44.5 |
| Sun 1:00 | MIN @ CHI | MIN +4½ (−110) | CHI −4½ (−110) | 48 |
| Sun 1:00 | PIT @ NE | PIT +5 (−110) | NE −5 (−110) | 41.5 |
| Sun 1:00 | CAR @ ATL | CAR −2½ (−115) | **ATL +2½ (−105)** | 43.5 |
| Sun 1:00 | CLE @ TB | CLE +8½ (−110) | **TB −8½ (−110)** | 41.5 |
| Sun 1:00 | CIN @ HOU | **CIN +2½ (−110)** | HOU −2½ (−110) | 45.5 |
| Sun 1:00 | NO @ BAL | NO +8½ (−110) | **BAL −8½ (−110)** | 46 |
| Sun 1:00 | PHI @ TEN | PHI −7 (−110) | TEN +7 (−110) | 39 |
| Sun 4:05 | LV @ LAC | LV +6½ (−110) | LAC −6½ (−110) | 43.5 |
| Sun 4:05 | JAX @ DEN | JAX +3 (−120) | DEN −3 (+100) | 45.5 |
| Sun 4:25 | WAS @ DAL | WAS +4 (−110) | DAL −4 (−110) | 50.5 |
| Sun 4:25 | SEA @ ARI | SEA −4 (−110) | ARI +4 (−110) | 41 |
| Sun 4:25 | MIA @ SF | MIA +13 (−110) | SF −13 (−110) | 45 |
| Sun 8:20 | IND @ KC | IND +6½ (−110) | KC −6½ (−110) | 46.5 |
| Mon 8:15 | NYG @ LAR | NYG +7 (−120) | LAR −7 (+100) | 48 |

All fifteen match the operator's expected list line for line.

## 2. Actual teaser prices

Menu header: **"2-6T Teaser (6 pts FB, 4 pts BK)"** — 6 points per football leg, which is
exactly frozen v1.0's `TEASER_POINTS = 6`.

| Ticket size | Offered | Decimal | Net profit / unit | Recorded? |
|---|---|---|---|---|
| 2-team | **−110** | 1.909090… | 0.909090909090… | **yes** |
| 3-team | **+170** | 2.70 | 1.70 | **yes** |
| 4-team | +300 | — | — | **no — v1.0 does not use it** |
| 5-team | +450 | — | — | **no** |
| 6-team | +700 | — | — | **no** |

The 4/5/6-team rungs are visible on the menu and were deliberately **not** ingested.
`TICKET_SIZES = (2, 3)` is frozen. Recording the higher rungs would imply an expansion
of v1.0 that the specification does not permit.

## 3. Qualifying primary legs

Frozen NFL PRIMARY/LIVE screen: spread ∈ {+1.5, +2.5, −7.5, −8.5} from the bet team's
perspective, half-points only, total ≤ 47.

σ = 0.30 × total · P_raw = Φ(6/σ) · both-key bump +0.07 · P_est = P_raw + 0.07

| Rank | Leg | Original | Teased | Total | σ | P_raw | Bump | **P_est** | Keys |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| 1 | **TB** vs CLE | −8.5 | −2.5 | 41.5 | 12.45 | 0.6850713500 | +0.07 | **0.7550713500** | 2 |
| 2 | **ATL** vs CAR | +2.5 | +8.5 | 43.5 | 13.05 | 0.6771593819 | +0.07 | **0.7471593819** | 2 |
| 3 | **CIN** vs HOU | +2.5 | +8.5 | 45.5 | 13.65 | 0.6698722508 | +0.07 | **0.7398722508** | 2 |
| 4 | **BAL** vs NO | −8.5 | −2.5 | 46 | 13.80 | 0.6681398852 | +0.07 | **0.7381398852** | 2 |

**Exactly four qualify.** Notable exclusions:

- **JAX is +3, not +2.5** — whole number, not primary geometry. Excluded. (The operator
  flagged this; the screenshot confirms JAX +3 −120 / DEN −3 +100.)
- **MIN/CHI (48), WAS/DAL (50.5), NYG/LAR (48)** — fail the total ≤ 47 guardrail.
- GB/NYJ ±3, PIT/NE ±5, PHI/TEN ±7, LV/LAC ±6½, SEA/ARI ±4, MIA/SF ±13, IND/KC ±6½ —
  none is primary geometry.

`P_est` is a **model-estimated hit probability**, not an objective probability.

## 4. Top four retained

Four legs qualify and four are retained, so the top-four cut dropped nothing:

**TB → ATL → CIN → BAL**, ranked by full-precision `P_est` descending.

## 5. Complete ticket board

All C(4,2)=6 two-team and C(4,3)=4 three-team combinations. Every ticket is shown.

| # | Ticket | n | `P_ticket` | Offered | Break-even | EV / unit | EV% | Verdict |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1 | TB+ATL+CIN | 3 | 0.4174053251 | +170 | 0.3703703704 | +0.1269943777 | **+12.70%** | POSITIVE EV |
| 2 | TB+ATL+BAL | 3 | 0.4164279961 | +170 | 0.3703703704 | +0.1243555894 | **+12.44%** | POSITIVE EV |
| 3 | TB+CIN+BAL | 3 | 0.4123665261 | +170 | 0.3703703704 | +0.1133896204 | **+11.34%** | POSITIVE EV |
| 4 | ATL+CIN+BAL | 3 | 0.4080455691 | +170 | 0.3703703704 | +0.1017230366 | **+10.17%** | POSITIVE EV |
| 5 | TB+ATL | 2 | 0.5641586431 | −110 | 0.5238095238 | +0.0770301369 | **+7.70%** | POSITIVE EV |
| 6 | TB+CIN | 2 | 0.5586563392 | −110 | 0.5238095238 | +0.0665257385 | **+6.65%** | POSITIVE EV |
| 7 | TB+BAL | 2 | 0.5573482796 | −110 | 0.5238095238 | +0.0640285337 | **+6.40%** | POSITIVE EV |
| 8 | ATL+CIN | 2 | 0.5528024936 | −110 | 0.5238095238 | +0.0553502150 | **+5.54%** | POSITIVE EV |
| 9 | ATL+BAL | 2 | 0.5515081403 | −110 | 0.5238095238 | +0.0528791770 | **+5.29%** | POSITIVE EV |
| 10 | CIN+BAL | 2 | 0.5461292182 | −110 | 0.5238095238 | +0.0426103257 | **+4.26%** | POSITIVE EV |

All ten are positive-EV **at the model's estimate**. That is a statement about `P_est`, not
about the world: the entire edge rests on the +0.07 both-key bump, whose empirical support
is exactly what the 2026 prospective record is being collected to test.

These are **actual offered prices**, not hypothetical. `price_is_hypothetical = False`.

## 6. PROPOSED SHADOW CARD — NOT PLACED

Frozen greedy selection: positive EV only, descending full-precision EV, 1 unit each, max
2 aggregate units per leg.

| Order | Ticket | n | Stake | EV% | Offered |
|---:|---|---:|---|---:|---:|
| 1 | **TB + ATL + CIN** | 3 | 1 unit | +12.70% | +170 |
| 2 | **TB + ATL + BAL** | 3 | 1 unit | +12.44% | +170 |
| 3 | **CIN + BAL** | 2 | 1 unit | +4.26% | −110 |

**3 tickets, 3 units proposed.**

Why the greedy stops there: after tickets 1 and 2, TB and ATL sit at 2 units each — the
cap. Tickets 3–9 each contain TB or ATL and are skipped. Ticket 10 (CIN+BAL) is the
highest-EV remaining ticket touching neither, so it is taken. That exhausts every leg.

## 7. Aggregate leg exposure

| Leg | Units | Cap |
|---|---:|---:|
| `2026_02_CLE_TB-TB` | **2** | 2 |
| `2026_02_CAR_ATL-ATL` | **2** | 2 |
| `2026_02_CIN_HOU-CIN` | **2** | 2 |
| `2026_02_NO_BAL-BAL` | **2** | 2 |

Every leg is exactly at the cap; none exceeds it. Total exposure 3 units across 3 tickets.

## 8. Screenshot-reading ambiguities

Four, all recorded rather than silently resolved:

1. **"EST" in September.** The board labels every kickoff `EST`, but on 2026-09-20 US
   Eastern is **EDT (UTC−4)**. Stored timestamps use `-04:00`. If the book literally means
   UTC−5 the kickoffs shift an hour; this changes no model output, because kickoff affects
   only pregame gating, and all fifteen games are in the future.
2. **Half-point glyphs.** The board renders halves as `½` (`+4½`, `−8½`) and whole numbers
   plainly (`−3`, `+5`, `+7`, `+13`). Transcribed literally. The distinction is decisive —
   JAX `+3` vs `+2.5` is the difference between a qualifying leg and no leg.
3. **The Monday game.** NYG/LAR is under a `MONDAY, SEP 21` header, not Sunday. Ingested at
   `2026-09-21T20:15:00-04:00`. It fails the total guardrail (48) either way.
4. **Cropped menu.** The teaser menu screenshot cuts off mid-row at the 6-team rung; rows
   beyond 6 teams, and any "ties lose/push" rule text, are not visible. Immaterial — v1.0
   uses only the 2- and 3-team rungs, both fully legible.

No unreadable value was guessed. Nothing was averaged.

## 9. Real book vs nflverse — 22 of 30 sides disagree

The two snapshots cover identical games. Comparing them is the point of having both:

| Side | nflverse | Screenshot | Consequence |
|---|---|---|---|
| **JAX / DEN** | JAX +2.5 | **JAX +3** | **JAX qualified on nflverse and does not qualify at the book.** |
| **NO / BAL** | total 46.5 | **total 46** | BAL qualifies either way, but `P_est` changes and BAL enters the top four. |
| GB / NYJ | ±3.5 | ±3 | no effect |
| PIT / NE | ±5.5 | ±5 | no effect |
| IND / KC | ±6 | ±6.5 | no effect |
| MIA / SF | ±13.5, 44.5 | ±13, 45 | no effect |
| MIN / CHI | 47.5 | 48 | already out on the guardrail |
| SEA / ARI | ±3.5, 40.5 | ±4, 41 | no effect |
| WAS / DAL | ±3.5 | ±4 | already out on the guardrail |
| PHI / TEN, NYG / LAR | totals 39.5 / 48.5 | 39 / 48 | no effect |

**Board impact:** nflverse gave 5 qualifying legs and a top four of TB/ATL/CIN/**JAX**. The
real book gives 4 qualifying legs and a top four of TB/ATL/CIN/**BAL**.

This is the concrete justification for the provenance discipline. A provisional feed and the
book the operator actually faces disagree on **22 of 30 sides**, and one of those
disagreements swaps a leg in and out of the card. The nflverse snapshot was never labelled a
close and is retained as what it is: provisional.

## 10. Totals stayed in their frozen role

Totals were used for exactly two things, as specified: the **≤ 47 guardrail**, and the
**σ = 0.30 × total** input. No teased total was constructed, priced or considered.

Teasing totals is a **research topic only** and must not enter v1.0 before the 2027
preseason review.

## 11. Integrity

| | |
|---|---|
| Engine diff vs HEAD | **empty** — no parameter, filter, guardrail or key number touched |
| `KEY_NUMBERS` | `{3, 7}` — unchanged, 10 not added |
| `TICKET_SIZES` | `(2, 3)` — 4/5/6-team rungs not ingested |
| Re-check performed | **no** — tonight's grading snapshot only |
| Placement records | **0** |
| **Actual placements** | **0** |
| **Actual units staked** | **0** |
| Test suite | **553 passed** |

The card is `PROPOSED`. It is stale by construction and the report says so: it must be
re-checked against a fresh snapshot before any placement could be recorded, and that
re-check has deliberately not been run tonight.
