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

Every leg carries **two independent classifications**, which must never be conflated:

| Dimension | Values | Determined by |
|---|---|---|
| **Geometry class** | `PRIMARY` / `SECONDARY` | the shape of the line, alone |
| **Operational track** | `LIVE` / `PAPER` | the league, plus the geometry class |

Primary geometry is the same structure in both leagues. The league restricts the *track*:

| Leg | geometry_class | track |
|---|---|---|
| NFL `+2.5 → +8.5` | PRIMARY | LIVE |
| CFB `+2.5 → +8.5` | PRIMARY | PAPER |
| NFL `+4.5 → +10.5` | SECONDARY | PAPER |
| CFB `+4.5 → +10.5` | SECONDARY | PAPER |

| Track | Contents |
|---|---|
| **LIVE** | NFL primary geometry only |
| **PAPER / RESEARCH ONLY** | NFL secondary geometry; all college football — *including CFB primary geometry*; the entire 2026 season |

All college football is paper-only for the whole 2026 season, and CFB primary geometry stays
distinguishable from CFB secondary geometry so research can tell them apart.

Key numbers are frozen at **{3, 7}** in both leagues. `+4.5 → +10.5` crosses 7 but not 3 and
is a one-key-number shape. 10 is not a v1.0 key number.

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
    classification.py      The two dimensions: geometry class and operational track.
    geometry.py            Teased spread, total guardrail, geometry lookups.
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
  analysis/                Measures the frozen model. Never changes it.
    grading.py             WIN/LOSS grading and the no-PUSH invariant.
    calibration.py         Predeclared buckets, Brier, exact binomial intervals.
    backtest.py            Weekly construction and ticket enumeration.
    validation.py          Group comparison and monotonicity for predeclared hypotheses.
    dependence.py          Independence audit: Monte Carlo null and permutation tests.

scripts/
  ingest_nfl.py            Snapshot the source, build processed games and legs frames.
  run_data_quality_audit.py  Run the gate. Exits non-zero on FAIL.
  investigate_line_composition.py  Season-by-season line-shape provenance report.
  run_phase2_calibration.py  Calibration of P_est against outcomes. No prices, no EV.
  run_phase2b_validation.py  Out-of-sample validation on 2018-2023. No prices, no EV.
  run_phase2c_independence_audit.py  Audit of the ticket independence assumption.

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
python scripts/investigate_line_composition.py                # line-shape provenance
python scripts/run_phase2_calibration.py                      # calibration (no pricing)
python scripts/run_phase2b_validation.py                      # 2018-2023 validation
python scripts/run_phase2c_independence_audit.py              # independence audit
```

The audit accepts `--per-season` to apply the gate to each season independently, and
`--tag` to select a processed dataset.

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

## Known source-regime caveat

The 2025 NFL season in the historical source runs on a **different upstream line feed** from
2024 and every season back to 1999: zero whole-number totals, and integer spreads only at 3,
6, 7, 10 and 14. Half-point fidelity is intact in both seasons and neither fails the gate,
but primary-geometry legs are substantially more frequent in 2025 for feed reasons rather
than market reasons.

**Report per season. Never pool silently.** 2026 is continuous with the 2025 regime, not
with 2024. Full evidence: `reports/nfl_line_composition_investigation.md`.

## Status

Phase 1 complete: repository structure, frozen engine, unit tests, NFL 2024–2025 ingestion,
data-quality audit.

Phase 1.5 complete: CFB primary/secondary interpretation corrected, key numbers stated
explicitly as {3, 7}, line-composition shift investigated.

Phase 2 complete: NFL 2024 and 2025 calibration of `P_est` against actual outcomes, reported
per season. See `reports/phase2_nfl_2024_calibration.md`,
`reports/phase2_nfl_2025_calibration.md` and `reports/phase2_nfl_comparison.md`.

Phase 2B complete: out-of-sample validation on NFL 2018-2023, with hypotheses declared
before those outcomes were examined. All six seasons pass the unchanged data-quality gate.
See `reports/phase2b_nfl_2018_2023_validation.md`,
`reports/phase2b_dog_favorite_validation.md` and `reports/phase2b_total_dependence.md`.

Phase 2C complete: audit of the independence assumption behind `P_ticket`. Evidence for
positive within-week dependence is **weak** — see
`reports/phase2c_independence_audit.md` for the evidentiary basis. No correction was
applied; the frozen ticket formula is unchanged.

**No profitability, EV or ROI figure has been produced.** No historical teaser prices exist
in the source and none have been invented.
