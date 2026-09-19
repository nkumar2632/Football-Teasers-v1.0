# NFL 2026 Week 2 — PROSPECTIVE SHADOW RUN

**SHADOW ONLY. ACTUAL PLACEMENTS = 0. ACTUAL UNITS STAKED = 0.**

Frozen Teaser Model v1.0, unchanged. Nothing in this system places a wager, and no wager was recorded.

## Grading snapshot

| Field | Value |
|---|---|
| Source | nflverse/nfldata `games.csv` — **a data feed, not a sportsbook** |
| Source commit | `ad855ef72bc4` |
| Feed last updated (captured_at) | `2026-09-19T17:55:13+00:00` |
| Market snapshot id | `mkt_2026w02_f544808f1a87` (immutable, content-addressed) |
| Card id | `card_2026w02_665ac88b756c` |
| Graded at | `2026-09-19T18:02:14+00:00` |
| Games scanned (pregame) | 15 |
| Teaser price snapshot | **NONE — no sportsbook configured** |

### Source and provenance caveats

- nflverse/nfldata is a **reference feed**. It carries **no book attribution** and **no documented capture time** beyond when the feed itself last updated. It is a clearly identified source, which is what a shadow grading run needs; it is **not** a sportsbook board and **not** a closing line.
- Independent web sources disagree with this feed on exact half-points for some games (for example a 13 vs 13.5 spread, and a 46.5 vs 47.5 total). Half-point fidelity is decisive for this model, so a single consistent source was used throughout rather than mixing feeds. **Your sportsbook's numbers may differ, and its numbers are the ones that count.**
- The Thursday game (DET @ BUF) had already been played and was **excluded as post-kickoff**. 15 pregame games were ingested; 14 kick off Sunday 2026-09-20 and one Monday 2026-09-21.

## Primary qualifiers

5 legs cleared the frozen NFL live-primary screen (+1.5/+2.5/−7.5/−8.5, half-points only, total ≤ 47).

| Rank | Team | Opp | Original | Teased | Total | P_est | Displayed | Kickoff |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 1 | TB | CLE | -8.5 | -2.5 | 41.5 | 0.755071 | 76% | 2026-09-20T13:00:00-04:00 |
| 2 | ATL | CAR | 2.5 | 8.5 | 43.5 | 0.747159 | 75% | 2026-09-20T13:00:00-04:00 |
| 3 | CIN | HOU | 2.5 | 8.5 | 45.5 | 0.739872 | 74% | 2026-09-20T13:00:00-04:00 |
| 4 | JAX | DEN | 2.5 | 8.5 | 45.5 | 0.739872 | 74% | 2026-09-20T16:05:00-04:00 |
| 5 | BAL | NO | -8.5 | -2.5 | 46.5 | 0.736441 | 74% | 2026-09-20T13:00:00-04:00 |

Displayed percentages are *model-estimated hit probability*, rounded for presentation only; ranking uses full precision.

**Top four retained:** TB, ATL, CIN, JAX (BAL is the qualifier that drops out, at rank 5).

All five qualifiers kick off **Sunday 2026-09-20**, so restricting the board to tomorrow's games alone would give the identical top four. The Monday game (NYG @ LA, −7.0/+7.0) is a whole-number line and is not primary geometry.

## Ticket board

**No sportsbook is configured for this project, so no actual teaser price exists.** Per the frozen rule, EV is not inferred: tickets are constructed and displayed with their probability, and the price column shows the *model-implied fair* price — what the model thinks the ticket is worth, **not** a price anyone offered.

| Ticket | Legs | P_ticket | Displayed | Model-implied fair price | Break-even at fair | Actual price | EV |
|---|---:|---:|---:|---:|---:|---|---|
| ATL+CIN | 2 | 0.552802 | 55% | -123.6 | 55.28% | UNAVAILABLE | **UNAVAILABLE** |
| ATL+JAX | 2 | 0.552802 | 55% | -123.6 | 55.28% | UNAVAILABLE | **UNAVAILABLE** |
| CIN+JAX | 2 | 0.547411 | 55% | -121.0 | 54.74% | UNAVAILABLE | **UNAVAILABLE** |
| TB+ATL | 2 | 0.564159 | 56% | -129.4 | 56.42% | UNAVAILABLE | **UNAVAILABLE** |
| TB+CIN | 2 | 0.558656 | 56% | -126.6 | 55.87% | UNAVAILABLE | **UNAVAILABLE** |
| TB+JAX | 2 | 0.558656 | 56% | -126.6 | 55.87% | UNAVAILABLE | **UNAVAILABLE** |
| ATL+CIN+JAX | 3 | 0.409003 | 41% | +144.5 | 40.90% | UNAVAILABLE | **UNAVAILABLE** |
| TB+ATL+CIN | 3 | 0.417405 | 42% | +139.6 | 41.74% | UNAVAILABLE | **UNAVAILABLE** |
| TB+ATL+JAX | 3 | 0.417405 | 42% | +139.6 | 41.74% | UNAVAILABLE | **UNAVAILABLE** |
| TB+CIN+JAX | 3 | 0.413334 | 41% | +141.9 | 41.33% | UNAVAILABLE | **UNAVAILABLE** |

Every ticket is shown, including ones that would be negative EV at a typical price. **"Best available" does not mean positive EV.**

## Proposed shadow card

### NO LIVE-ELIGIBILITY DETERMINATION — TEASER PRICE REQUIRED

No sportsbook was specified, so no actual 6-point teaser price was captured. Without one, break-even and EV are undefined and **no ticket can become model-designated positive EV**. This is the frozen rule working as intended, not a failure of the run.

### What you need to supply

Two numbers from your sportsbook's **6-point teaser** menu:

| Ticket size | What to supply | Rough reference point |
|---|---|---|
| **2-team 6-point teaser** | the offered price (e.g. −120) | this board's 2-team tickets are fair at about **−121 to −129**, so a price better than that would be positive EV under the frozen model |
| **3-team 6-point teaser** | the offered price (e.g. +140) | this board's 3-team tickets are fair at about **+140 to +145**, so a price better than that would be positive EV |

Capture them with:

```bash
python src/teaser_model_v1/cli/live.py price-template --season 2026 --week 2
# fill in the actual prices you see, then:
python src/teaser_model_v1/cli/live.py ingest-prices --file <that file> --season 2026 --week 2
```

Then re-grade against the same market snapshot plus the price snapshot to get a real EV column. **Also supply your book's spreads and totals if they differ from the feed** — the board above is only as good as the lines it was graded from.

## Operational status

| Item | Status |
|---|---|
| Grading | **COMPLETE** |
| Placement re-check | **NOT YET PERFORMED** |
| Actual placements | **0** |
| Actual units staked | **0** |
| Model-designated tickets | **0** (no price) |

Today's grading and tomorrow's re-check are **separate events**. The snapshot above is a genuine prospective record and will not be overwritten.

Before any placement decision tomorrow, Phase 4.1 requires, with no override: a fresh market snapshot; a fresh actual teaser-price snapshot; a mandatory re-check whose verdict is VALIDATED; ≤30-minute freshness and price contemporaneity; every leg still primary geometry; total still ≤ 47; positive EV at the actual price; and placement strictly before kickoff for every constituent game.

