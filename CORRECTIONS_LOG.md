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
