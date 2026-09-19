# AGENTS.md — read this before touching anything

## THE FROZEN-SPECIFICATION RULE (highest priority)

**Teaser Model v1.0 is frozen for the entire 2026 season.**

The operational model is specified in [`TEASER_MODEL_V1_0.md`](TEASER_MODEL_V1_0.md).
That document is the contract. The code in `src/teaser_model_v1/engine/` implements it.

While working in this repository you **MUST NOT**:

- optimize parameters
- change filters
- reinterpret the rules
- improve the geometry
- substitute your own betting assumptions
- fit parameters using historical outcomes
- silently resolve ambiguities in ways that alter the model

This applies even when you are confident the change is an improvement. **Especially** then.

If you identify a possible improvement, **write it into [`RESEARCH_QUEUE.md`](RESEARCH_QUEUE.md)
and change nothing else.**

## Why this rule exists

The purpose of the 2026 season is to collect an *out-of-sample* prospective record of a
model that was specified in advance. Every parameter tweak, filter adjustment, or
"obvious fix" made during the season destroys that. A model that is edited while it is
being measured cannot be measured.

Backtests in this repository are **research instruments**, not a fitting loop. Historical
outcomes must never flow back into v1.0 parameters.

## What you MAY change

- Data ingestion, provenance tracking, auditing, reporting, plotting, docs, tests, tooling.
- Genuine **errors**: data-entry, source, formula, or implementation errors — i.e. places
  where the code does not do what `TEASER_MODEL_V1_0.md` says. These are corrections *toward*
  the spec, never away from it.
- Every such correction must be logged in [`CORRECTIONS_LOG.md`](CORRECTIONS_LOG.md).

If you are unsure whether something is an error correction or a model change: **it is a model
change.** Put it in `RESEARCH_QUEUE.md`.

## Ambiguities

Known ambiguities in the written specification, and the exact reading this implementation
uses, are listed in [`AMBIGUITIES.md`](AMBIGUITIES.md). Do not resolve a new ambiguity
silently — record it there, and prefer the reading that changes nothing about the four
primary NFL geometries.

Specifically: **do not hard-code any proposed CFB bump correction.** The CFB bump values in
the spec are the ones in the code, provisional or not.

## Scope reminder — two dimensions, never conflated

Every leg carries **two independent classifications**. Do not merge them, do not infer one
from the other, and do not add a field that encodes both as a single value.

| Dimension | Values | Determined by |
|---|---|---|
| **Geometry class** | `PRIMARY` / `SECONDARY` | the shape of the line, alone |
| **Operational track** | `LIVE` / `PAPER` | the league, plus the geometry class |

Primary geometry is the **same structural geometry in both leagues**:

```
dog       +1.5 -> +7.5        favorite   -7.5 -> -1.5
dog       +2.5 -> +8.5        favorite   -8.5 -> -2.5
```

| Leg | geometry_class | track |
|---|---|---|
| NFL `+2.5 → +8.5` | PRIMARY | LIVE |
| CFB `+2.5 → +8.5` | PRIMARY | PAPER |
| NFL `+4.5 → +10.5` | SECONDARY | PAPER |
| CFB `+4.5 → +10.5` | SECONDARY | PAPER |

- **LIVE:** NFL primary geometry only.
- **PAPER / RESEARCH ONLY:** NFL secondary geometry, *all* college football — including
  **CFB primary geometry** — and the *entire* 2026 season.

All college football is paper-only for the whole 2026 v1.0 season. **CFB primary geometry
must nevertheless stay distinguishable from CFB secondary geometry**, because research on
the paper track depends on telling them apart. Classifying CFB primary legs as SECONDARY is
an implementation error, not a safe conservative choice — it was one, and it was corrected;
see `CORRECTIONS_LOG.md`.

Nothing in this repository places a bet. `placement_eligible` is a model-designation flag,
not an instruction.

## Key numbers are frozen at {3, 7}

```
KEY_NUMBERS = {3, 7}
```

Both leagues. This is settled, not an open question. `+4.5 → +10.5` crosses 7 but not 3 and
is therefore a **one**-key-number shape under v1.0.

**Do not add 10 as a v1.0 key number.** Whether college football warrants separate treatment
of 10 is a research question (`RESEARCH_QUEUE.md` R-03) and must not be implemented before
the 2027 preseason review.

## Language discipline

- `P_est` is a **model-estimated hit probability**. Never call it an objective, true, or
  actual probability, in code, comments, reports, or commit messages.
- Never call an archived line a "close" unless the source documentation proves it was the
  last market price before kickoff. Use `archived_reference_line` by default; reserve
  `true_timestamped_close` for sources that document it.
- "Void" refers only to sportsbook settlement after placement. A pre-placement ticket that
  fails the re-check is **discarded**, not voided.
- Hypothetical teaser prices must be labeled hypothetical, every time, in every output.

## Prospective live operations (Phase 4)

`src/teaser_model_v1/live/` and `src/teaser_model_v1/cli/` operate the frozen model week to
week. They **read** the engine and never change it. Rules for that layer:

- **No automated wager placement, ever.** Nothing in this repository may submit a bet to a
  sportsbook. `record-placement` writes down what the operator says they already did.
- **PROPOSED is never PLACED.** A card is a proposal. Only an explicit operator action
  creates a placement record.
- **Records are append-only.** A later market or price capture is a NEW snapshot, never an
  edit. Corrections are new records that point at the superseded one; history is never
  rewritten.
- **Timestamps carry an explicit offset**, and half-points stay exact `Decimal` values.
- **A ticket with no actual captured price has no EV** and is never placement-eligible. A
  hypothetical price can never become a live one.
- **A model-designated placement requires a current, VALIDATED re-check and a pregame
  timestamp.** There is no override, and none may be added. A refused attempt is logged
  separately and creates no placement record.
- **Placement and settlement status is derived from the event ledgers at read time.** Never
  copy it into the immutable grading record; that is how operator state drifts.
- **Do not re-implement a model rule in `live/`.** Geometry, ranking, ticket construction,
  EV and selection all come from `engine/`. A test asserts no live module rebinds a frozen
  constant and that the engine never imports upward.

Weekly checklist: `LIVE_OPERATIONS.md`. Design: `reports/phase4_operations_design.md`.

## Change control

The v1.0 operational model does not change during 2026. Research may continue but cannot
alter v1.0 until the **2027 preseason review**.
