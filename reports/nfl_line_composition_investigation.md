# Investigation — NFL 2024 / 2025 line-composition shift

**Scope:** provenance only. No model outcome, hit rate, calibration or profitability figure
appears in this document, and none was computed to produce it. Every number below describes
the *shape and history of the lines themselves*.

**Source under investigation:** nflverse/nfldata `data/games.csv`
(snapshot `data/raw/nflverse_nfldata_games.csv`, sha256 `35bc182c6e81…`, upstream commit
`4a7ebfde2a7c784255f95c457d8c638a7ca188fa`, retrieved 2026-09-19).

**Reproduce:** `python scripts/investigate_line_composition.py`. The commit-history sections
additionally require a deep clone of the source repository; the exact commands are given
inline.

---

## 1. Observed differences

The Phase 1 audit flagged this pair of gaps between the two seasons:

| Metric | 2024 | 2025 |
|---|---|---|
| Spread half-point share | 52.3% | 75.1% |
| Total half-point share | 58.2% | **100.0%** |

Widening the window to every season in the snapshot shows that **2024 is unremarkable and
2025 is the departure**:

| Era | Seasons | Spread half-point share | Total half-point share |
|---|---|---|---|
| 1999–2024 | 26 seasons | 33.3% – 52.3% | 37.1% – 60.7% |
| 2025 | 1 season | 75.1% | 100.0% |
| 2026 (in progress, 48 games) | partial | 77.1% | 100.0% |

2024 sits at the top of a slow 26-season drift but inside it. 2025 steps outside the entire
historical range for both fields, and 2026 continues at the 2025 level. **Zero** of 285
games in 2025 carry a whole-number total; every prior season has between 105 and 168.

### 1.1 The integer spreads that survive in 2025 are only key numbers

This is the sharper signal. Whole-number spreads do not disappear in 2025 — they collapse
onto the numbers a sportsbook actually holds:

| Season | Distinct integer \|spread\| values | Values present (count) |
|---|---|---|
| 2022 | 14 | 1(31), 2(7), 3(42), 4(12), 5(3), 6(10), 7(8), 8(4), 9(1), 10(12), 11(5), 13(2), 14(7), 17(1) |
| 2023 | 15 | 1(13), 2(11), 3(48), 4(14), 5(5), 6(13), 7(10), 8(2), 9(2), 10(5), 11(2), 12(1), 13(5), 14(5), 15(2) |
| 2024 | 13 | 1(14), 2(8), 3(46), 4(12), 5(5), 6(16), 7(15), 8(6), 9(4), 10(4), 11(1), 13(1), 14(4) |
| **2025** | **5** | **3(29), 6(13), 7(19), 10(5), 14(5)** |
| 2026 (partial) | 3 | 3(7), 6(1), 7(3) |

Through 2024 the data carries integer spreads at essentially every value from 1 to 15. From
2025 it carries them only at 3, 6, 7, 10 and 14. Integer spreads at **1, 2, 8 and 9 vanish
entirely** — and those are precisely the neighbours of this model's primary geometry.

### 1.2 Consequence for primary-geometry leg counts

| Season | +1.5 | −1.5 | +2.5 | −2.5 | +7.5 | −7.5 | +8.5 | −8.5 |
|---|---|---|---|---|---|---|---|---|
| 2024 | 13 | 13 | 31 | 31 | 16 | 16 | 1 | 1 |
| 2025 | 35 | 35 | 39 | 39 | 16 | 16 | 9 | 9 |

Legs on ±1.5 and ±8.5 roughly triple and multiply ninefold respectively. This is a direct
mechanical consequence of §1.1: lines that the 2024-era feed would have recorded as `1` or
`2` or `8` appear in the 2025 feed as `1.5`, `2.5` or `8.5`. **The two seasons do not offer
the model the same number of opportunities, for reasons that have nothing to do with the
model.**

---

## 2. Evidence about cause

### 2.1 Documentation — no explanation available

- `DATASETS.md` documents `spread_line` only as "The spread line for the game…" and
  `total_line` as "The total line for the game." No provider is named, no capture time is
  given, and there are **no season-specific source notes** anywhere in the repository.
- The repository has no changelog, NEWS file, or release notes.
- Every commit touching `data/games.csv` carries the message "Automated data update"
  (9,823 such commits in the fetched window). No commit documents a source change.
- `code/` contains no script that generates `games.csv`; the file is produced outside the
  repository. `code/draft_kings.R` *does* query DraftKings for spread and total on games
  with no result yet, which establishes that DraftKings is **a** line source used somewhere
  in this project's tooling — but that script does not write `games.csv`, and this is not
  evidence that DraftKings is the `games.csv` feed.

### 2.2 Commit history — the stored 2024 values were never retro-transformed

Fetched history back to 2024-11-18 (`git fetch --depth=15000 origin master`), sampling one
commit per fortnight and recomputing composition:

| Snapshot date | 2024 games w/ lines | 2024 total half-share | 2025 games w/ lines | 2025 total half-share |
|---|---|---|---|---|
| 2024-11-30 | 208 | 0.529 | 0 | — |
| 2024-12-31 | 271 | 0.546 | 0 | — |
| 2025-01-30 | 285 | **0.582** | 0 | — |
| 2025-05-30 | 285 | 0.582 | 232 | **1.000** |
| 2025-09-14 | 285 | 0.582 | 48 | 1.000 |
| 2025-12-31 | 285 | 0.582 | 272 | 1.000 |
| 2026-01-30 | 285 | 0.582 | 285 | 1.000 |
| 2026-09-19 | 285 | 0.582 | 285 | 1.000 |

Two findings:

1. **2024 froze at 0.582 when the season ended and has not moved since.** No later
   normalisation was applied to it.
2. **2025 rows were already at 100% half-point totals from their first appearance**, in
   offseason look-ahead lines in May 2025, months before any 2025 game was played, and
   stayed there all season.

### 2.3 The 2025 values were never whole at any point, not even mid-week

If a transformation were applied when a game's result landed, whole totals would appear in
mid-week snapshots and vanish at freeze time. They do not. Sampling 182 in-season snapshots
between 2025-09-01 and 2026-01-15, covering **30,761 row-snapshots** of 2025 lines:

- whole-number totals observed at *any* moment: **1**
- whole-number `|spread|` values observed at any moment: 1, 3, 6, 7, 10, 14

So the half-point-only totals are a property of the incoming feed, **not** a transformation
applied to stored values.

### 2.4 The collection mechanism is unchanged — only the feed behind it differs

Tracking single games through their game week shows identical mechanics in both eras: the
row is refreshed every few hours, moves with the market, and freezes at whatever the last
refresh captured once the final score lands.

`2024_14_GB_DET`, across 125 snapshots: spread 5.0 → 4.5 → 3.5 → 3.0 (oscillating 3.0/3.5),
total 51.5 → 51.0 → 51.5 → **52.0 → 52.5 → 53.0**, frozen at 3.0 / 53.0 when the score
appeared. Note the totals passing through whole numbers — the 2024-era feed genuinely posted
them.

`2025_10_LV_DEN`, across 66 snapshots: spread 10.5 → 10.0 → 8.5/9.5 oscillating → frozen at
9.5; total 42.5 throughout, never whole. The feed also dropped out briefly (three
consecutive snapshots with both fields blank) before returning.

**Conclusion supported by the evidence:** the collection mechanism (periodic scrape, freeze
at result) is the same in both seasons. What changed, effective from the 2025 season and
continuing into 2026, is the **upstream line feed** — from something behaving like a
consensus or multi-book average (integers at every value, whole totals common) to something
behaving like a single sportsbook's board (half-points everywhere except genuine key
numbers, essentially never a whole total).

---

## 3. What is known

1. The 2024 and 2025 seasons differ materially in line composition, in both spreads and
   totals. Confirmed, reproducible from the snapshot.
2. 2024 is consistent with the preceding 25 seasons. 2025 is outside the entire 1999–2024
   range on both metrics, and 2026 continues at the 2025 level.
3. The break coincides exactly with the 2025 season boundary, including offseason look-ahead
   lines written in May 2025.
4. 2025's half-point-only totals are a property of the incoming data, not a transformation
   applied at freeze time (§2.3).
5. Stored 2024 values were never retro-edited (§2.2).
6. The collection mechanism — periodic refresh through game week, frozen at the final score
   — is unchanged across both seasons (§2.4).
7. Integer spreads in 2025 survive only at 3, 6, 7, 10 and 14, and are absent at 1, 2, 8
   and 9 (§1.1).
8. Both seasons preserve exact half-point values. Neither rounds `+2.5` to `+3` or `-7.5`
   to `-8`; all values lie exactly on the 0.5 grid. This is the property the model actually
   requires, and it holds in both.
9. Neither season's lines carry a documented capture timestamp. Both are correctly labelled
   `archived_reference_line`. §2.4 strengthens this: the stored value is whatever the last
   scrape before the result happened to catch, at an irregular and undocumented lag, with
   observed feed dropouts. It is **not** a `true_timestamped_close` and cannot support a CLV
   claim.

## 4. What remains unknown

1. **The identity of the upstream provider in either era.** Not documented anywhere in the
   repository. `code/draft_kings.R` shows DraftKings is used by *some* tooling in the
   project but does not generate `games.csv`.
2. **Whether the 2025 feed is a single sportsbook or a different aggregate.** The integer
   pattern in §1.1 is consistent with a single book's board, but "consistent with" is not
   "established". No documentation confirms it.
3. **Whether the change was deliberate, announced, or incidental.** No commit message,
   changelog or source note addresses it. The maintainer may have announced it in a channel
   outside this repository; that was not verifiable from the source.
4. **Whether the 2024-era and 2025-era lines are equally obtainable in practice.** Unknown
   for both eras, since no sportsbook is identified per game in either.
5. **The exact lag between the stored value and kickoff, per game.** Refresh cadence is
   irregular (observed gaps of roughly 1–9 hours) and undocumented.

**No further cause is asserted.** The evidence establishes *what* changed, *when*, and that
it is a feed change rather than a transformation of stored values. It does not establish
*who* changed it or *to what*.

---

## 5. Should either season fail the data-quality gate?

**No. Neither season fails.**

The gate exists to detect a source that has destroyed half-point fidelity — one that rounds
`+2.5` to `+3` or `-7.5` to `-8`, per `TEASER_MODEL_V1_0.md` §12. That is a loss of
resolution. What was found is the opposite: the 2025 feed carries *more* resolution than
2024, not less.

Re-checking each season independently against the pre-registered gates:

| Check | 2024 | 2025 |
|---|---|---|
| Spreads on the 0.5 grid | PASS (0 off-grid) | PASS (0 off-grid) |
| Spread half-point share ≥ 40% | PASS (52.3%) | PASS (75.1%) |
| All four primary shapes present | PASS | PASS |
| Whole numbers retain adjacent half-points | PASS | PASS |
| Missing spreads / totals | PASS (0) | PASS (0) |
| Duplicates | PASS (0) | PASS (0) |
| Impossible values | PASS (0) | PASS (0) |

Both seasons clear every critical gate on their own. The composition shift is reported as a
**non-blocking WARN** (`season_composition_consistency`), which is the correct severity: it
informs analysis design, it does not invalidate data.

**Neither season should be dropped, and no thresholds were adjusted in response to this
finding.**

---

## 6. Implications for later analysis

1. **Analyse each season separately. Do not pool silently.** A pooled 2024+2025 figure mixes
   two different line-generating regimes. Any pooled number must be accompanied by the
   per-season breakdown and an explicit statement that the regimes differ.
2. **Leg counts, qualification rates and weekly volume are not comparable across the
   regimes.** Primary-geometry legs are far more frequent in 2025 (§1.2) for feed reasons,
   not market reasons. Any statement about "how many opportunities per week" must name the
   season it came from. This bears directly on the specification's requirement (§11) to
   record the number of qualifying legs each week, including zero — those counts are
   regime-dependent.
3. **Treat 2026 as continuous with the 2025 regime, not with 2024.** The live 2026 season is
   running on the post-change feed. If a historical baseline is wanted for context on 2026
   volume, 2025 is the comparable season.
4. **Two seasons is a thin base and one of them is a different regime.** Sample-size
   caveats should be stated loudly, and no regime-specific conclusion should rest on a
   single season.
5. **Neither season supports a CLV or line-movement claim.** §3.9 applies to both. Market-
   quality measurement (spec §11) requires our own timestamped capture during 2026.
6. **Do not "correct" either season toward the other.** Normalising 2024 integers to
   half-points, or vice versa, would fabricate lines that were never posted. Half-point
   fidelity means recording what the source recorded.
7. **Re-run this investigation if the source is re-snapshotted.** The 2026 season is live and
   the feed could change again. The audit's `season_composition_consistency` check will flag
   it; this document is the template for the follow-up.

---

## Appendix — commands used

```bash
# Season composition, integer-value breakdown, primary-shape counts (from the snapshot)
python scripts/investigate_line_composition.py

# Commit-history evidence (requires a deep clone of the source repository)
git clone https://github.com/nflverse/nfldata
git -C nfldata fetch --depth=15000 origin master
git -C nfldata log --format='%H %cI' -- data/games.csv
git -C nfldata show <sha>:data/games.csv     # recompute composition per snapshot
```
