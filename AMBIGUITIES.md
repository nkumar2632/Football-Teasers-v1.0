# Ambiguities in the written v1.0 specification

The specification is frozen, but a written specification is not executable: a few points
had to be pinned down before code could run. This file records every one of them, the
reading used, and why that reading was chosen.

**Rule:** where a choice existed, the reading that leaves the four primary geometries and
their probabilities unchanged was taken. None of the entries below alters the live model's
behaviour on NFL primary legs.

Entries marked **CLOSED** were settled in Phase 1.5 and are no longer open questions.

Do not resolve a new ambiguity silently. Add it here, and if the resolution could plausibly
change results, add it to `RESEARCH_QUEUE.md` as well.

---

## A-1. The key numbers — RESOLVED, no longer an ambiguity

**Status: CLOSED (Phase 1.5).** The key numbers are fixed for frozen v1.0 at exactly
`{3, 7}`, in both leagues. This is recorded in `TEASER_MODEL_V1_0.md` §5.1 and in
`KEY_NUMBERS_V1_0`. It is an implementation clarification of the frozen specification, not
a parameter change.

`+4.5 → +10.5` crosses 7 but not 3 and is a **one**-key-number shape under v1.0. **10 is
not a v1.0 key number**; whether CFB warrants separate treatment of 10 is research only
(`RESEARCH_QUEUE.md` R-03) and must not be implemented.

*Historical note:* Phase 1 implemented `{3, 7}` as a reading of an under-specified point,
because the bump table gave sizes for "crosses both" and "crosses one" without enumerating
the numbers. Phase 1.5 confirmed that reading as the frozen value. No behaviour changed.

## A-2. Geometry class versus operational track — CORRECTED

**Status: CLOSED (Phase 1.5). The Phase 1 reading was wrong and has been corrected.**

Phase 1 read "§3 Primary *NFL* geometry" plus "§1 all college football is paper" as meaning
CFB legs were never primary, and classified every CFB leg as SECONDARY. That conflated the
two dimensions.

**Correct reading:** geometry class and operational track are independent.

* **Geometry class** is a property of the line's shape alone, and the primary geometry
  `{+1.5, +2.5, -7.5, -8.5}` is the same structure in both leagues.
* **Operational track** is what restricts live play to the NFL.

So CFB `+2.5 → +8.5` is `PRIMARY` geometry on the `PAPER` track, and stays distinguishable
from CFB `+4.5 → +10.5`, which is `SECONDARY` geometry on the `PAPER` track.

**Effect on the live model:** none. `eligible_live_primary_legs()` still admits exactly NFL
primary geometry inside the NFL guardrail, and no CFB leg can reach a constructed ticket.
The correction restores research visibility that Phase 1 destroyed.

Implementation: `Geometry` and `Track` are distinct plain enums with no shared members, and
a leg carries a single `LegClassification` holding both. `Geometry.PRIMARY == Track.LIVE`
is False and neither compares equal to a bare string, so the dimensions cannot be conflated
by a stray comparison. Logged in `CORRECTIONS_LOG.md`.

## A-3. What "crosses a key number" means precisely

**Reading used:** a bet on a team at line `L` wins when `margin + L > 0`. Teasing `L` to
`L + 6` newly covers exactly the signed margins in the half-open interval `(-L - 6, -L]`.
A key number `k` is crossed when `k` or `-k` lies in that interval.

The interval is open at the bottom and closed at the top because a margin equal to the
*teased* line is a push, while a margin equal to the *original* line was a push before the
teaser and becomes a win after it.

**Why:** it is the only reading under which "crossing" means the teaser actually buys that
margin. It yields "crosses both" for all four primary geometries, which matches the
specification's framing.

**Effect on the live model:** none — every primary leg gets the "both" bump either way.

## A-4. Tie-breaking beyond what the specification states

§8 ranks legs by `P_est`; §9 ranks tickets by precise EV then by fewer legs. Neither says
what to do when values are *exactly* equal after that.

**Reading used:** a final tiebreak on the leg id (and for tickets, the tuple of leg ids),
ascending.

**Why:** this is a determinism device, not a model rule. Without it, output would depend on
input row order, and the same week could produce different tickets on two runs. It is
reached only after the specification's own rules have fully tied.

## A-5. Whether EV exactly equal to zero counts as "positive EV"

**Reading used:** strict. `EV > 0`. A ticket at exactly break-even is **not**
placement-eligible.

**Why:** §8.7 says live placement eligibility *requires* positive EV. Zero is not positive.

## A-6. Whether `P_est` is clipped to [0, 1]

**Reading used:** no clipping. `P_est = P_raw + bump`, exactly as written.

**Why:** clipping is a rule the specification does not contain. `P_est > 1` requires a game
total below roughly 13.5, which is not a real NFL or CFB number; if it ever appears it means
the input data is broken. `p_est_is_degenerate()` surfaces that rather than hiding it behind
a silent repair.

## A-7. What counts as one unit of "exposure to a leg"

**Reading used:** each selected ticket stakes 1 unit and contributes 1 unit of exposure to
each of its constituent legs, regardless of ticket size. A leg may therefore appear in at
most two selected tickets in a week.

**Why:** §9 sets a flat 1 unit per ticket and caps aggregate leg exposure at 2 units per
week. A 3-team ticket does not stake more, so it cannot contribute more.

## A-8. A hypothetical price can never create placement eligibility

**Reading used:** `Ticket.placement_eligible` requires positive EV **and**
`price_is_hypothetical == False`.

**Why:** §7 requires hypothetical prices to be labelled as such, and §8.7 requires positive
EV *at the actual offered price*. A sensitivity scenario is not an offered price.

---

## Derived facts (not ambiguities, recorded to prevent re-litigation)

- **No game can contribute two primary legs.** The primary set `{+1.5, +2.5, -7.5, -8.5}`
  contains no complementary pair, so if one side of a game is primary the other side is not.
  A ticket therefore can never contain both sides of the same game. Pinned by a test.
- **Ranking primary legs by `P_est` is, within the primary set, ranking by game total
  ascending.** Every primary leg crosses both key numbers, so the bump is a constant and
  `P_est` is a strictly decreasing function of the total. This is a consequence of the
  frozen model, not a shortcut taken in code — the code computes `P_est` as specified.
- **Teased primary lines are all half-points** (+7.5, +8.5, -1.5, -2.5), so a primary leg
  can never push.
