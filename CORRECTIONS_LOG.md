# Corrections Log

Change control for Teaser Model v1.0 (see `AGENTS.md`).

The v1.0 operational model does not change during the 2026 season. **Only genuine
data-entry, source, formula, or implementation errors may be corrected**, and every
correction must be logged here.

A correction is a change that moves the code *toward* `TEASER_MODEL_V1_0.md`. Anything that
moves it away — including anything that makes results better — is a model change and is
forbidden until the 2027 preseason review.

## Format

Each entry records:

| field | meaning |
|---|---|
| Date | UTC date of the correction |
| Class | `data-entry` / `source` / `formula` / `implementation` |
| What was wrong | the defect, stated plainly |
| Evidence | why it is a defect against the frozen spec, not a preference |
| Change | what was actually changed |
| Effect | which prior outputs are invalidated, if any |

---

## Entries

### 2026-09-19 — Repository created (not a correction)

Phase 1 foundation built: frozen engine, unit tests, NFL 2024–2025 ingestion, data-quality
audit. No corrections to log yet. This entry exists so the log is not empty and the format
is visible.

### 2026-09-19 — Phase 1.5 correction 1: CFB primary geometry misclassified as SECONDARY

| field | value |
|---|---|
| **Date** | 2026-09-19 (UTC) |
| **Class** | `implementation` |

**What was wrong.** The Phase 1 implementation classified *every* college-football leg as
`SECONDARY`, including legs on the four primary shapes (+1.5, +2.5, −7.5, −8.5). A CFB leg
at +2.5 was labelled `cfb_paper_track_primary_shape` but its geometry class was `SECONDARY`,
making CFB primary geometry indistinguishable from CFB secondary geometry in any grouping
that keyed on geometry class.

**Evidence that this is a defect, not a preference.** The frozen specification has two
independent dimensions — geometry class (`PRIMARY` / `SECONDARY`) and operational track
(`LIVE` / `PAPER`). Primary geometry is a structural property of the line and is the same in
both leagues; it is the *track* that restricts live play to the NFL. Phase 1 conflated the
two, which is why `AMBIGUITIES.md` A-2 recorded the wrong reading. The correction moves the
code toward `TEASER_MODEL_V1_0.md` §1.1 and §3, not away from it.

**Change.**
- New `engine/classification.py` holding `LegClassification(geometry_class, track,
  secondary_reason)` and the functions `geometry_class_for`, `track_for`,
  `secondary_reason_for`, `classify`.
- `Geometry` and `Track` changed from `str`-enums to plain enums with no shared members, so
  `Geometry.PRIMARY == Track.LIVE` is False and neither equals a bare string. The two
  dimensions can no longer be conflated by a stray comparison or dict key.
- `PRIMARY_NFL_SPREADS` renamed `PRIMARY_SPREADS` (alias retained); new `LIVE_LEAGUES = {NFL}`.
- `classify_geometry(league, spread)` now returns `PRIMARY` for CFB primary shapes. The
  conflated predicate `is_primary()` was **removed** and replaced by `is_primary_geometry()`
  and `is_live_track()`, so no call site can ask the ambiguous question.
- `Leg` carries one `classification` field exposing both dimensions via properties, plus
  `qualifies_primary` (geometry, either league) and `qualifies_live_primary` (NFL primary,
  guardrail applied).
- `eligible_primary_nfl_legs` renamed `eligible_live_primary_legs` (alias retained); new
  research helpers `primary_geometry_legs`, `paper_track_legs`, `legs_by_classification`.
- Secondary reasons are now league-independent (`whole_number_line` /
  `other_half_point_shape`); the `cfb_paper_track_*` labels are gone.

**Effect.** **No change to live-model behaviour.** The weekly construction still admits
exactly NFL primary geometry inside the NFL total guardrail, and no CFB leg can reach a
constructed ticket — pinned by
`test_cfb_primary_legs_cannot_reach_a_constructed_ticket`. No prior output is invalidated,
because no model-performance output has been produced. The correction restores research
visibility that Phase 1 had destroyed.

**Regression tests added.** `tests/test_geometry_labels.py` — the four-case matrix
(NFL/CFB × primary/secondary), `test_cfb_primary_stays_distinguishable_from_cfb_secondary`,
and `test_geometry_and_track_are_distinct_types_that_never_compare_equal`.

### 2026-09-19 — Phase 1.5 correction 2: key numbers stated explicitly as {3, 7}

| field | value |
|---|---|
| **Date** | 2026-09-19 (UTC) |
| **Class** | `implementation` (clarification) |

**What was wrong.** Nothing in the code. The written specification gave bump sizes for
"crosses both key numbers" and "crosses one" without enumerating the key numbers, so Phase 1
implemented `{3, 7}` as a documented *reading* in `AMBIGUITIES.md` A-1 rather than as a
stated constant.

**Evidence.** The frozen v1.0 key-number set is `{3, 7}`, in both leagues. This is an
implementation clarification, not a parameter change.

**Change.** Added `KEY_NUMBERS_V1_0 = frozenset({3, 7})`; documented in
`TEASER_MODEL_V1_0.md` §5.1 with worked crossing examples and in `AGENTS.md`;
`AMBIGUITIES.md` A-1 marked CLOSED. `RESEARCH_QUEUE.md` R-03 and R-05 explicitly fence off
the CFB-10 question.

**Effect.** **No numerical change whatsoever.** `KEY_NUMBERS` already held `(3, 7)` for both
leagues; every probability, bump and crossing count is identical before and after.

**Tests added.** `tests/test_key_numbers.py` — the set is exactly `{3, 7}`, 10 is not a key
number in either league, `+2.5 → +8.5` and `−8.5 → −2.5` cross both, and `+4.5 → +10.5`
crosses 7 but not 3 and is therefore a one-key-number shape.
