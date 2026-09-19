# Research Queue

Ideas, questions and observed anomalies that **must not** change Teaser Model v1.0 during
the 2026 season. Nothing here is implemented. Nothing here may be implemented before the
**2027 preseason review**.

Adding an item here is the correct response to noticing a possible improvement. Editing
`src/teaser_model_v1/engine/` is not.

Status legend: `queued` — recorded, no work done. `analysed` — research written up in
`reports/`, still not implemented.

---

## Specified research topics

### R-01 — sigma functional form and intercept
`sigma = 0.30 * total` has no intercept and no floor. Alternatives worth *studying*:
`sigma = a + b * total`, a variance model on total, or an empirical sigma by total bucket.
Status: `queued`.

### R-02 — spread dependence of sigma
The current sigma ignores the spread entirely. Margin dispersion plausibly varies with how
lopsided a game is. Study whether residual dispersion is a function of `|spread|` as well as
total. Status: `queued`.

### R-03 — empirical key-number mass
The bump is explicitly provisional. Measure the empirical probability mass at margins of 3
and 7 — and at 4, 6 and 10 — directly, per league and per era.

The frozen v1.0 key-number set is exactly `{3, 7}` in both leagues
(`TEASER_MODEL_V1_0.md` §5.1). **Whatever this research finds, 10 must not be added to
`KEY_NUMBERS`, and no measured mass may be fed back into the v1.0 bump values**, before the
2027 preseason review. Status: `queued`.

### R-04 — empirical margin-minus-spread distribution
The model assumes a normal distribution for `margin - spread`. Measure the actual shape:
skew, kurtosis, and the discrete pile-ups at key numbers that a continuous normal cannot
represent. Status: `queued`.

### R-05 — CFB versus NFL differences
Everything from sigma coefficient to key-number mass likely differs. The CFB bump values
are provisional. **No proposed CFB bump correction is hard-coded anywhere in this
repository, and none may be.** Status: `queued`.

Separately: whether college football warrants treating **10** as a key number is an open
research question. **10 is NOT a v1.0 key number and must not be added to `KEY_NUMBERS`.**
The frozen v1.0 set is exactly `{3, 7}` in both leagues (`TEASER_MODEL_V1_0.md` §5.1).

### R-06 — secondary geometry
Whole-number lines (+2, -8) and the wider half-point shapes are paper-only in v1.0. Measure
them on the paper track before anyone argues about promoting them. Note that whole-number
teased lines can push, which the current probability model does not represent at all.
Status: `queued`.

### R-07 — recency and regime effects
Rule changes, kicking accuracy, two-point conversion rates and pace all move the margin
distribution. Study whether a lookback window or regime split is warranted. Status:
`queued`.

---

## Items raised during Phase 1 implementation

These were noticed while building the foundation. They are recorded here rather than acted
on, per `AGENTS.md`.

### R-08 — leg independence assumption in `P_ticket`
`P_ticket` is the product of leg `P_est` values, which assumes independence. Legs on the
same slate share weather, injury news and market-wide mispricing; correlation would bias
ticket probability. Measure realised joint hit rates against the product for 2- and 3-team
tickets. Status: `queued`. *This is a measurement task, not a licence to change §6.*

### R-09 — the top-four rule truncates before EV is known
§8 ranks legs by `P_est` and keeps four, then computes ticket EV. Since ticket price
generally does not vary by leg, this is usually equivalent to ranking by EV — but not
necessarily when a book prices teasers by leg count only. Worth characterising. Status:
`queued`.

### R-10 — within the primary set, `P_est` ordering collapses to total ordering
Every primary leg crosses both key numbers, so the bump is constant across the primary set
and `P_est` is a monotone decreasing function of the game total alone. The top-four rule is
therefore, in practice, "the four lowest-total primary games". Whether that is the intended
selection principle is a v2 question. Status: `queued`. See `AMBIGUITIES.md` derived facts.

### R-11 — no bump interpolation or partial-credit for near-misses
A leg whose teaser stops exactly at a key number receives no credit, and the bump is a step
function. An empirically fitted continuous adjustment is an obvious v2 candidate and is
explicitly out of bounds for v1.0. Status: `queued`.

### R-12 — `P_est` has no upper bound
`P_est = P_raw + bump` is unclipped (see `AMBIGUITIES.md` A-6). Whether a v2 model should be
specified so that it cannot exceed 1 by construction is a modelling question. Status:
`queued`.

### R-13 — the exposure cap interacts with leg correlation
The 2-unit cap limits single-leg exposure but not exposure to a correlated *group* of legs
(e.g. four legs all needing low-scoring games). Characterise the realised correlation of
selected portfolios. **Do not replace the greedy rule with an optimizer.** Status: `queued`.

---

## Data and measurement infrastructure (not model changes)

These are tooling gaps rather than model questions. They may be *built* without touching
v1.0, but they are listed here so they are not forgotten.

### D-01 — no historical teaser menu prices
The nflverse source contains no teaser prices, and none have been invented. Until a real
historical teaser menu is sourced, historical work is restricted to hit rate, calibration,
fair break-even pricing, and clearly labelled hypothetical-price sensitivity. Finding a
documented historical teaser menu is high value. Status: `queued`.

### D-02 — no true timestamped close in the historical source
`spread_line` / `total_line` in nflverse/nfldata carry no documented capture time and are
labelled `archived_reference_line`. Phase 1.5 commit-history work strengthened this: the
stored value is whatever a periodic scrape caught last before the final score landed, at an
irregular lag, with observed feed dropouts. CLV and line-movement measurement (spec §11) are
simply not computable from this source. For 2026, capture our own timestamped lines at
placement and near kickoff. Status: `queued`.

### D-03 — cross-season source-regime shift in the historical NFL source — INVESTIGATED
**Status: `analysed`.** See `reports/nfl_line_composition_investigation.md` (Phase 1.5).

Established: the 2025 season runs on a different upstream line feed from 2024 and every
season back to 1999. 2025 carries zero whole-number totals (all prior seasons carry 105-168)
and retains integer spreads only at 3, 6, 7, 10 and 14 — integers at 1, 2, 8 and 9 vanish
entirely. The change is in the incoming feed, not a transformation of stored values, and the
collection mechanism is unchanged. 2026 continues on the 2025 regime.

Half-point fidelity is intact in both seasons, so neither fails the data-quality gate.

Consequence that must be honoured in all later work: primary-geometry legs are far more
frequent in 2025 than 2024 for feed reasons rather than market reasons (+1.5 legs 13 -> 35,
+8.5 legs 1 -> 9). **Report per season. Never pool silently.** Treat 2026 as continuous with
2025, not with 2024.

Remaining open: the identity of the upstream provider in either era, and whether the 2025
feed is a single sportsbook. Not documented anywhere in the source. No cause beyond "the
feed changed" is asserted.

### D-04 — sportsbook identity is not recorded per game
The historical source does not say which book each archived line came from. Any claim about
obtainability of a given line is therefore unsupported. Status: `queued`.

### D-05 — college football data not yet sourced
Phase 1 is NFL-only. A CFB source must clear the same half-point fidelity gate before any
CFB paper track can run; CFB data is considerably more likely to be rounded or averaged
across books. Status: `queued`.
