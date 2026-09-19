# Phase 4 — prospective operations design

Infrastructure for running frozen Teaser Model v1.0 week to week in the 2026 NFL season.

**Frozen Teaser Model v1.0 is unchanged.** Geometry, total caps, sigma, key-number bumps,
the ticket probability formula, top-four construction, exposure rules and staking are
untouched. The live layer delegates every model decision to
`src/teaser_model_v1/engine/`; it contributes no model rule of its own.

**No automated wager placement.** Nothing in this repository can submit a bet. The system
proposes cards, records what the operator says they placed, and preserves the audit trail.

Operator checklist: [`LIVE_OPERATIONS.md`](../LIVE_OPERATIONS.md).

---

## 1. Architecture

Dependencies run one way only, and a test enforces it:

```
engine/     frozen model              <- imports nothing below it
ingest/     historical data
analysis/   historical research
live/       prospective operations    -> imports engine only
cli/        operator commands         -> imports live
```

| Module | Responsibility |
|---|---|
| `live/provenance.py` | timezone-aware time, canonical JSON, content-hash record ids |
| `live/schemas.py` | market quote/snapshot, teaser price quote/snapshot, validation |
| `live/snapshot.py` | append-only store and ledger, correction records |
| `live/market.py` | manual CSV ingestion (required) + provider adapter interface (optional) |
| `live/pricing.py` | capture of the **actual** sportsbook teaser menu |
| `live/card.py` | grading-time board and the PROPOSED card |
| `live/recheck.py` | placement-time re-check, discard and rebuild |
| `live/placement.py` | the explicit placement ledger and its guard rails |
| `live/settlement.py` | model grade and book settlement, kept separate |
| `live/ledger.py` | market-quality observations and the append-only season ledger |
| `live/report.py` | the human-readable weekly report |
| `live/rehydrate.py` | rebuild records from disk, re-verifying content hashes |
| `live/workspace.py` | where each kind of record lives |
| `cli/live.py` | `teaser-live` operator commands |

## 2. Market data contract

Provider-neutral. Every quote preserves season, week, `game_id`, kickoff, both teams, the
side quoted, spread, total, sportsbook, `captured_at`, ingestion method, source reference
and the **raw source value** exactly as supplied.

Three validation rules exist to prevent silent corruption:

- **Half points are exact.** Spreads and totals are `Decimal` on the 0.5 grid. A value off
  the grid is rejected outright — an averaged or rounded line is unusable for this model,
  and accepting one would repeat the failure mode the historical audit was built to catch.
- **Timestamps carry an offset.** A naive datetime raises. Assuming UTC or local time would
  silently move a `captured_at` by hours, and a market snapshot exists precisely to say
  *when*.
- **Rows fail loudly.** An unparseable row aborts ingestion with its row number. A silently
  skipped row is a missing leg, and a missing leg changes the card.

## 3. Snapshot and audit-trail design

**A record's id embeds a hash of its content.** Consequences:

- Storing identical content twice is an idempotent no-op — duplicate capture is harmless.
- Different content yields a different id, so a later capture is always a **new record**,
  never an edit.
- A stored file whose content no longer matches its id has been tampered with; rehydration
  recomputes the hash and refuses it.

Corrections never rewrite history. A `correction` record names the superseded record, the
reason, who made it and optionally the replacement. The original stays byte-for-byte.

## 4. Actual teaser-price capture

This is the object the historical work never had, and the reason Phase 3 could only run
hypothetical grids.

A price quote records ticket size, sportsbook, `captured_at`, the offered odds in American
**or** decimal form (the other is derived), the canonical net profit per unit, source
reference and notes. Only 6-point teasers are accepted.

The enforcement that matters: **a ticket size with no captured price has no EV.** Its
tickets are still constructed and displayed with their `P_ticket`, but break-even and EV
read `UNAVAILABLE` and the ticket is not placement-eligible. Separately, the frozen engine
refuses to treat a hypothetically-priced ticket as eligible at all, so a Phase 3 sensitivity
price cannot leak into a live card by any route.

## 5. Grading-time card

One market snapshot plus one actual-price snapshot produces the weekly board:

1. every quote becomes a leg via the engine's `build_leg`;
2. `eligible_live_primary_legs` keeps NFL primary geometry inside the `total <= 47` guardrail;
3. legs are ranked by full-precision `P_est` and the top four retained;
4. all 2-team and 3-team combinations are generated and priced;
5. the frozen greedy walks positive-EV tickets in descending precise EV, 1 unit each,
   capped at 2 aggregate units per leg.

Every ticket is displayed, including negative-EV ones. Fewer than two qualifying legs gives
**NO CONSTRUCTIBLE LIVE PRIMARY TICKET**, and the week is still recorded with its leg count,
including zero.

The output is a **PROPOSED** card carrying both snapshot ids and the grading timestamp.

## 6. Placement-time re-check

Requires a genuinely new market snapshot — re-checking against the one the card was graded
from is refused, because it would prove nothing.

For each proposed ticket, every leg is re-tested against the current board: still primary
geometry, still inside the guardrail, still present in the market, still valid data. The
ticket's EV is recomputed at the **current** price.

Any failure gives **DISCARD — REBUILD REQUIRED**. The system does not substitute another
team, does not downgrade a 3-team ticket to a 2-team ticket, and does not reuse the stale
ticket. A rebuilt card is generated from the current board. Both snapshots are kept.

## 7. Placement recording

Two rules:

1. **Nothing is placed unless a human explicitly records it.** There is no path from
   PROPOSED to PLACED that does not pass through an operator command.
2. **This software never submits a wager.**

Guard rails on a model-designated placement:

- the ticket must exist on the card;
- it must have been **proposed** by the frozen selection;
- if a re-check is supplied, the ticket must be **VALIDATED** in it;
- it must not breach the 2-unit aggregate cap.

A wager made outside the model is recordable as `EXTERNAL_NON_MODEL`; it is stored for
completeness, exempt from the cap check, and excluded from every v1.0 performance figure.

## 8. Settlement

`model_result` (frozen v1.0 graded from the final score) and `book_settlement` (what the
sportsbook actually did, including VOID and CANCELLED) are stored in **separate fields**,
even when they agree. They are different claims and can legitimately diverge.

A live-primary leg grading PUSH raises rather than being absorbed: every primary teased line
is a half-point, so a push means the recorded line or score is wrong.

## 9. Market-quality record

Kept apart from model quality, because CLV does not validate probability calibration.

Line observations are labelled `grading_line`, `placement_line` or
`final_observed_market_snapshot`. The label `true_timestamped_close` is **rejected by the
code** unless a source genuinely documents the last market price before kickoff — no source
in this project does. Line movement is reported; CLV is explicitly *not* computed, with the
reason attached to the record.

## 10. Append-only season ledger

Every week is recorded: games scanned, qualifying legs, top-four legs, positive-EV tickets,
proposed, placed, units, results, P/L, and model-expected versus actual.

**Zero-qualifier and zero-bet weeks appear exactly like active ones.** Omitting them would
build survivorship bias into the prospective record by construction — the one thing a
prospective record exists to avoid.

## 11. Defects found by the synthetic rehearsal

The rehearsal was worth running: it exposed three real implementation defects, all fixed and
all now covered by tests.

1. **A ticket discarded at re-check could still be recorded as a model-designated
   placement.** This was exactly the "reuse the stale ticket" failure the specification
   forbids. `PlacementLedger.record` now accepts the re-check and refuses anything not
   VALIDATED.
2. **A vanished leg produced an unexplained discard.** The reason was attached to the leg
   but never propagated to the ticket, leaving a discard with no stated cause in the audit
   record.
3. **The snapshot tamper-detection was dead code.** Rehydration passed the stored id back
   into the constructor, which short-circuited recomputation, so an edited file would have
   been accepted. It now recomputes the hash from content.

A fourth, found by the isolation tests: `live/schemas.py` **duplicated** the frozen
`TEASER_POINTS` rather than importing it, which could have drifted out of step with the
specification. It now imports the engine constant.

## 12. Limitations

- **No odds provider is configured.** `MarketProvider` is an abstract interface with no
  implementation; manual CSV entry is the supported path. No credentials are read or
  fabricated, and nothing in the workflow depends on an external API.
- **Manual entry is the weakest link.** Validation catches bad grids, bad teams, naive
  timestamps and duplicates, but it cannot catch a plausible wrong number typed from the
  screen. The `raw_source_value` field exists so a transcription question can be settled
  later.
- **One book per snapshot is assumed.** Mixing books labels the snapshot `MIXED`; the model
  has no opinion about which book's line is authoritative.
- **CLV is not computed**, by design, until a genuinely documented closing reference exists.
- **The season ledger is written at grading time** and reflects placements only when
  re-recorded after placing. `season-status` reads the latest entry per week.
- **Kickoff times are captured but not enforced.** Nothing blocks grading or recording after
  kickoff; the timestamps make it visible rather than impossible.
