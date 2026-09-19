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

## Scope reminder

- **LIVE:** NFL primary geometry only.
- **PAPER / RESEARCH ONLY:** NFL secondary geometry, all college football, and the *entire*
  2026 season.

Nothing in this repository places a bet. `placement_eligible` is a model-designation flag,
not an instruction.

## Language discipline

- `P_est` is a **model-estimated hit probability**. Never call it an objective, true, or
  actual probability, in code, comments, reports, or commit messages.
- Never call an archived line a "close" unless the source documentation proves it was the
  last market price before kickoff. Use `archived_reference_line` by default; reserve
  `true_timestamped_close` for sources that document it.
- "Void" refers only to sportsbook settlement after placement. A pre-placement ticket that
  fails the re-check is **discarded**, not voided.
- Hypothetical teaser prices must be labeled hypothetical, every time, in every output.

## Change control

The v1.0 operational model does not change during 2026. Research may continue but cannot
alter v1.0 until the **2027 preseason review**.
