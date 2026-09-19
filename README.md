# teaser-model-v1

A rigorous historical backtesting harness for **Teaser Model v1.0**, a 6-point football
teaser model whose specification is **frozen for the entire 2026 season**.

This is a research project. It is not a betting system, a signal service, or an
optimisation loop. Nothing here places a wager.

> **Before changing anything, read [`AGENTS.md`](AGENTS.md).** The model specification in
> [`TEASER_MODEL_V1_0.md`](TEASER_MODEL_V1_0.md) is frozen. Parameters may not be tuned,
> filters may not be adjusted, and historical outcomes may not be fitted. Improvements go
> in [`RESEARCH_QUEUE.md`](RESEARCH_QUEUE.md).

## Why freeze the model

The whole point of 2026 is to produce an out-of-sample, prospectively recorded track for a
model that was written down in advance. A model edited while it is being measured cannot be
measured. Every backtest in this repository is a research instrument, never a fitting loop.

## Scope

| Track | Contents |
|---|---|
| **LIVE** | NFL primary geometry only |
| **PAPER / RESEARCH ONLY** | NFL secondary geometry; all college football; the entire 2026 season |

Weekly betting volume is **measured**, not assumed. Some weeks will produce zero qualifying
legs, and zero is recorded like any other number.

## Layout

```
AGENTS.md                  The frozen-specification rule. Read first.
TEASER_MODEL_V1_0.md       The frozen specification. The contract.
AMBIGUITIES.md             Every point the written spec left open, and the reading used.
RESEARCH_QUEUE.md          Ideas that may NOT touch v1.0 until the 2027 preseason review.
CORRECTIONS_LOG.md         Change control: error corrections only, all logged.

src/teaser_model_v1/
  engine/                  The frozen model. Pure functions, no I/O.
    constants.py           Every frozen number, in one place.
    numeric.py             Exact-decimal helpers protecting half-point fidelity.
    leagues.py             League normalization.
    geometry.py            Primary/secondary classification, teased spread, guardrail.
    probability.py         sigma, P_raw, key-number crossings, bump, P_est.
    pricing.py             break-even, EV per unit, price conversions.
    legs.py                The Leg value object.
    tickets.py             Ticket generation, EV ranking, greedy exposure selection.
    weekly.py              Weekly construction and the mandatory weekly counts.
    presentation.py        Rounding and the mandatory labels.
  ingest/                  Data acquisition. Kept strictly separate from the engine.
    nflverse.py            nflverse/nfldata games.csv ingestion.
    provenance.py          Provenance vocabulary and raw-snapshot manifests.
  audit/                   The mandatory pre-analysis data-quality gate.
    data_quality.py        Checks, thresholds, PASS/FAIL verdict.
    report.py              Markdown/JSON rendering.

scripts/
  ingest_nfl.py            Snapshot the source, build processed games and legs frames.
  run_data_quality_audit.py  Run the gate. Exits non-zero on FAIL.

tests/                     Written before any historical analysis.
data/raw/                  Verbatim source snapshots plus provenance manifests.
data/processed/            Derived frames.
reports/                   Audit and research reports.
```

Computation is deliberately separated from data ingestion: nothing in `engine/` reads a
file, hits a network, or knows what a data source is.

## Install

```bash
pip install -r requirements.txt     # or: pip install -e ".[dev]"
```

Python 3.10+. pandas, numpy, scipy, pytest.

## Run

```bash
python -m pytest                                              # unit tests
python scripts/ingest_nfl.py --from-url                       # snapshot + process NFL data
python scripts/run_data_quality_audit.py                      # the mandatory gate
```

`scripts/ingest_nfl.py` also accepts `--from-clone /path/to/nfldata` or
`--from-file games.csv` if you already have the source locally.

**The data-quality audit must PASS before any strategy calculation is run.** The script
exits non-zero on FAIL so a pipeline cannot walk past it.

## Data source

NFL game results and lines come from
[nflverse/nfldata](https://github.com/nflverse/nfldata) (`data/games.csv`, maintained by
Lee Sharpe). The raw file is snapshotted into `data/raw/` with a SHA-256, the upstream
commit, and a manifest recording exactly what the source documentation does and does not
claim.

**The `spread_line` and `total_line` fields are labelled `archived_reference_line`.** The
source documents them only as "the spread line for the game" and "the total line for the
game"; it makes no claim about when they were captured. They are therefore **not** a close,
not a "true timestamped close", and cannot support any CLV claim. This is a hard rule, not
a stylistic preference — see `TEASER_MODEL_V1_0.md` §12.

The source contains **no teaser menu prices**. None have been invented. Historical work is
restricted to hit rate, calibration, fair break-even pricing, and sensitivity analysis at
prices that are labelled hypothetical every time they appear.

## Language rules

- `P_est` is a **model-estimated hit probability**, never an objective or true probability.
- A line is a `archived_reference_line` unless the source documents otherwise.
- **"Void"** refers only to sportsbook settlement after placement. A pre-placement ticket
  that fails the re-check is *discarded*.
- Hypothetical prices are labelled hypothetical, everywhere, always.

## Status

Phase 1 complete: repository structure, frozen engine, unit tests, NFL 2024–2025 ingestion,
data-quality audit. **No model-performance results have been produced.**
