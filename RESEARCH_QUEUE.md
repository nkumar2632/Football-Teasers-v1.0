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
The bump is explicitly provisional and its key numbers are not enumerated in the spec
(see `AMBIGUITIES.md` A-1). Measure the empirical probability mass at margins of 3 and 7
(and at 4, 6, 10) directly, per league and per era. **Do not feed the result back into
v1.0.** Status: `queued`.

### R-04 — empirical margin-minus-spread distribution
The model assumes a normal distribution for `margin - spread`. Measure the actual shape:
skew, kurtosis, and the discrete pile-ups at key numbers that a continuous normal cannot
represent. Status: `queued`.

### R-05 — CFB versus NFL differences
Everything from sigma coefficient to key-number mass likely differs. The CFB bump values
are provisional. **No proposed CFB bump correction is hard-coded anywhere in this
repository, and none may be.** Status: `queued`.

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
labelled `archived_reference_line`. CLV and line-movement measurement (spec §11) are simply
not computable from this source. For 2026, capture our own timestamped lines at placement
and near kickoff. Status: `queued`.

### D-03 — cross-season composition shift in the historical source
The 2024 and 2025 seasons in nflverse/nfldata differ markedly in line composition: the
half-point share of spreads is 52.3% in 2024 versus 75.1% in 2025, and *every* 2025 total
ends in .5 versus 58.2% in 2024. Half-point fidelity is preserved in both seasons (the audit
passes), but this is consistent with a change of upstream line source or book between
seasons. Leg counts and eligibility rates must be reported per season, never pooled without
comment, and the cause should be investigated before any multi-season claim is made.
Status: `queued`.

### D-04 — sportsbook identity is not recorded per game
The historical source does not say which book each archived line came from. Any claim about
obtainability of a given line is therefore unsupported. Status: `queued`.

### D-05 — college football data not yet sourced
Phase 1 is NFL-only. A CFB source must clear the same half-point fidelity gate before any
CFB paper track can run; CFB data is considerably more likely to be rounded or averaged
across books. Status: `queued`.
