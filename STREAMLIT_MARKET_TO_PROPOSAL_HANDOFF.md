# STREAMLIT_MARKET_TO_PROPOSAL_HANDOFF — Revision 2 (final, Codex-ready)

**For:** Codex, working in the Streamlit app repository.
**Deadline:** Saturday (CFB PAPER), then the NFL Sunday slate.
**Scope:** wiring and UX only.

**This document supersedes Revision 1** (commit `1b54b8b`). Where the two differ, this one
governs. Both operator decisions are resolved (§15). The build checklist is in §0.

## Ground rules for Codex

- **The teaser repository is a read-only dependency.** Import `teaser_model_v1`; do not edit
  it, and do not write runtime data into its checkout (see §4.4).
- **No model logic in Streamlit.** The app never computes a teased spread, key-number count,
  geometry class, track, bump, P_raw, P_est, total guardrail, leg ranking, top-four cut,
  ticket combination, P_ticket, break-even, EV, ticket selection or exposure cap, re-check
  verdict, placement gate, or settlement grade. Each of these has exactly one implementation,
  cited in §4. The app parses, normalizes, validates **input format**, calls those functions,
  stores their outputs and displays them.
- **Citations.** Every interface marked **[verified]** was read at `Football-Teasers-v1.0`
  commit `a29afd5`, path `src/teaser_model_v1/...`. **[app: locate]** marks a component the
  operator says the app already has.
- **ESPN fields.** ESPN field names come from the public scoreboard JSON. ESPN was
  unreachable from the environment where this was written, so confirm each name against the
  app's existing ESPN ingester output before relying on it.

---

## 0. Implementation checklist

**Blocker** means it must work for Saturday's CFB PAPER run or Sunday's NFL run.
Component names marked [app: locate] must be confirmed in the app repository.

### P0 — required for Saturday

| # | Item | App component to find [app: locate] | Teaser-repo reuse [verified] | Acceptance test | Blocker |
|---|---|---|---|---|---|
| P0-1 | Three market-source choices: Public lines / Sportsbook snapshot / Manual | proposal page; existing ESPN fetch page, screenshot import page, manual quoted-side editor | — (UI) | AT-01, AT-03, AT-07 | **Yes** |
| P0-2 | ESPN/public → `NormalizedSlate` → proposal, with zero manual quoted-side entry | ESPN/public ingester and its REFERENCE snapshot store | `live.schemas.MarketSnapshot`/`MarketQuote` (NFL); `live.paper.PregameLineInput` (CFB); `live.provenance.new_record_id`, `require_aware` | AT-01, AT-02 | **Yes** |
| P0-3 | Confirmed EXECUTION snapshot → proposal, with zero manual quoted-side entry | screenshot OCR/import, review grid, EXECUTION snapshot confirm | `MarketSnapshot`/`MarketQuote`; `live.snapshot.AppendOnlyStore` | AT-03 | **Yes** (Sunday NFL) |
| P0-4 | Both quoted sides generated from the per-game `home_spread` | new converter module (app) | `MarketQuote` construction (its `__post_init__` validates); the precedent is `scripts/run_cfb_paper_board.py::load` | AT-13, AT-15 | **Yes** |
| P0-5 | Source and sportsbook inherited, never re-entered | proposal page; snapshot metadata | `MarketQuote.sportsbook`, `MarketSnapshot.sportsbook`; `WeeklyCard.sportsbook`; `GradedLeg.sportsbook` | AT-04 | **Yes** |
| P0-6 | Teaser menu inherited when present | screenshot import (teaser-menu extraction), if it exists | `live.schemas.TeaserPriceSnapshot`, `TeaserPriceQuote`; `live.pricing.price_from_american` | AT-05 | **Yes** |
| P0-7 | Ask only for missing 2-team/3-team prices, and reuse the saved menu (league, book, day) | proposal page menu block; settings store | `TeaserPriceQuote` validation (rejects 0, 4+ team sizes, non-6-point); `TeaserPriceSnapshot.profit_by_size()` | AT-06, AT-19, AT-25 | **Yes** |
| P0-8 | Operator setting `default_teaser_book = "bluecoins.ag"` (D-1) and mixed-source labelling (§8) | settings page/store | `TeaserPriceQuote.sportsbook` | AT-38, AT-39 | **Yes** |
| P0-9 | One-click "I verified these teaser prices are unchanged now" (D-2) | proposal page and placement dialog | new `TeaserPriceSnapshot` via `price_from_american(..., captured_at=click time)`; satisfies `live.placement.MAX_PRICE_LAG` unchanged | AT-20, AT-40, AT-41 | **Yes** (NFL placement) |
| P0-10 | CFB PAPER runs directly from public/reference lines and saves its board record | proposal page; the app's data store | `live.paper.build_cfb_paper_legs`, `primary_paper_legs`, `secondary_paper_legs`, `build_cfb_paper_tickets`, `PAPER_BANNER`, `CURRENT_PREGAME`; record format = `data/live/cards/cfb_paper_board_2026-09-19.json` (F-2) | AT-02, AT-34, AT-37 | **Yes** |
| P0-11 | NFL public lines → a clearly labelled screening/reference proposal | proposal page; card view | `live.card.grade_week`; `live.report.render_weekly_report`; `live.research.teased_board_rows` | AT-01, AT-38 | **Yes** |
| P0-12 | NFL placement only from a valid EXECUTION workflow plus an explicit PLACED action | existing placement page/handler | `live.recheck.recheck_card`; `live.placement.PlacementLedger.validate_model_placement` → `.record` / `.log_refusal` (the sequence in `cli/live.py::cmd_record_placement`); `EXTERNAL_NON_MODEL` | AT-08, AT-09, AT-21, AT-39 | **Yes** |
| P0-13 | CFB never placement-eligible, whatever `Ticket.placement_eligible` returns (F-1) | card view; placement handler | read `Leg.track` / `PaperLeg.live_eligible` (always False); never branch on `engine.tickets.Ticket.placement_eligible` for CFB | AT-31 | **Yes** |
| P0-14 | Identical normalized slate → identical teaser output regardless of source | converters + `build_proposal` | the single engine path per league (§1.2) | AT-12, AT-32 (numeric-equality part) | **Yes** |
| P0-15 | Started games excluded; invalid values excluded per game, never slate-wide | converters | `MarketValidationError` from `MarketQuote`; `engine.numeric.on_half_point_grid` (CFB) | AT-16, AT-17, AT-34 | **Yes** |
| P0-16 | Persistence outside the teaser checkout; selection survives Streamlit reruns | app data store / `st.session_state` | `live.workspace.Workspace(root=APP_DATA_ROOT)`; `AppendOnlyStore`; `live.rehydrate.*_from_dict` | AT-10, AT-14, AT-18 (rerun part) | **Yes** |

### P1 — right after Saturday

| # | Item | Test |
|---|---|---|
| P1-1 | Inline fixes for single cells: missing total (G3), no-odds game pair (G4) | AT-17, AT-36 |
| P1-2 | Append-only CFB team-alias table with a dropdown (G6); until then an unresolved game is excluded with its reason | AT-24 |
| P1-3 | OCR conflict resolution radio and duplicate merge; until then a conflicting game is excluded | AT-22, AT-23 |
| P1-4 | ESPN spread-sign cross-check shown as CONFLICT (P0 behaviour is to exclude on disagreement) | AT-33 |
| P1-5 | Stale-snapshot banner (> 2 h / not today) and an older-snapshot picker with ages | AT-28 |
| P1-6 | Selection restored after a full browser reload, not just a rerun | AT-18 (reload part) |
| P1-7 | Screenshot uploader pre-fills from the prior EXECUTION snapshot and highlights changed cells | — |
| P1-8 | Home/away for screenshots derived from the same-day schedule match | — |

### P2 — later polish

| # | Item |
|---|---|
| P2-1 | Public vs EXECUTION diff panel refinements (display-only, AT-26) |
| P2-2 | Price plausibility soft warnings (2-team −150…+100; 3-team +100…+250) |
| P2-3 | Moneyline display columns (inert, AT-29) |
| P2-4 | Static "no duplicated model math" linter in CI (AT-32 static part) |
| P2-5 | Settings UI for `STALE_WARN` and other display defaults |

---

## 1. Non-negotiables

1. **Frozen models stay frozen.** No edit to `teaser_model_v1/` of any kind. ATS v0 and
   Moneyline v0 are completed NO MODEL / NO BET results and are out of scope. Moneylines are
   carried for display only.
2. **One engine path per league, never per source:**
   - **NFL:** `live.card.grade_week(MarketSnapshot, TeaserPriceSnapshot | None)` **[verified]**
   - **CFB:** `live.paper.build_cfb_paper_legs(list[PregameLineInput])` → `primary_paper_legs` /
     `secondary_paper_legs` → `build_cfb_paper_tickets(primary, profit_by_size)` **[verified]**

   How a slate arrived (public, screenshot or manual) never changes what these functions
   receive.
3. **PROPOSED is never PLACED.** A placement row is written only by an explicit operator action
   through `live.placement.PlacementLedger` **[verified]**. Nothing submits a wager.
4. **Append-only.** Corrections and later captures are new records pointing at their parent.
5. **Timestamps carry an offset. Lines and totals stay exact decimals.**
6. **Enter once, inherit everywhere** (§10).

---

## 2. Target UX: one page

```
LEAGUE        (•) NFL  ( ) CFB
MARKET SOURCE (•) Public lines  ( ) My sportsbook  ( ) Manual
  Public:     date [today] [Fetch]            or [Use saved ▾]
  Sportsbook: [Upload screenshots] → review   or [Use saved ▾]
  Manual:     [Open editor]  (always pre-filled from the selected slate; fallback only)
SELECTED MARKET
  Source ESPN · lines DraftKings · REFERENCE · captured 11:42 -04:00 (18 min) · 47/52 usable
  [Review slate ▸]   banners: excluded (reasons) · stale · started · conflicts
  [Use this slate for proposal]
TEASER MENU (6-pt): 2-team −110 ✓(snapshot)   3-team [ +170 ]  ← only missing sizes are inputs
  menu book: bluecoins.ag (inherited / Settings)
[BUILD PROPOSAL]
PROPOSAL CARD   banner, one of (exact rules in §8):
  CFB             "CFB PAPER/RESEARCH TRACK — NOT LIVE v1.0"   (live.paper.PAPER_BANNER)
                  + "Lines: ESPN/<provider> (reference) · Teaser pricing: bluecoins.ag"
  NFL public      "PUBLIC/REFERENCE-MARKET PROPOSAL — lines: ESPN/<provider> ·
                   teaser pricing: bluecoins.ag — NOT AN EXECUTABLE BLUECOINS SLATE"
  NFL EXECUTION   "EXECUTABLE PROPOSAL (bluecoins.ag lines + bluecoins.ag menu) — PROPOSED, NOT PLACED"
  [Record placement…] only on EXECUTABLE cards
```

The normal Saturday path is five clicks: **CFB → Public → Fetch → Use this slate → Build.**

---

## 3. Normalized slate: the one internal format

```python
@dataclass(frozen=True)
class TeamRef:
    key: str            # NFL: project code (normalize_team); CFB: ESPN team id
    display: str        # NFL: project code; CFB: school name used on the card
    source_name: str    # exactly as the source printed it

@dataclass(frozen=True)
class SlateGame:
    game_key: str       # uniqueness key, see §5.4
    league: str         # "NFL" | "CFB"
    season: int
    week: int | None
    kickoff: datetime   # tz-aware
    home: TeamRef
    away: TeamRef
    home_spread: Decimal | None   # HOME perspective; negative = home favoured
    total: Decimal | None
    home_ml: Decimal | None       # display only
    away_ml: Decimal | None       # display only
    value_origin: dict            # per field: SOURCE | OPERATOR_ENTRY | OCR_CORRECTED
    raw: dict                     # untouched source payload for this game
    exclusion: str | None         # STARTED | NO_ODDS | MISSING_TOTAL | INVALID_VALUE |
                                  # UNRESOLVED_TEAM | CONFLICT

@dataclass(frozen=True)
class NormalizedSlate:
    slate_id: str                 # live.provenance.new_record_id("slate", payload) [verified]
    league: str
    source_kind: str              # PUBLIC | SPORTSBOOK_SCREENSHOT | MANUAL
    market_status: str            # REFERENCE | EXECUTION
    provider: str                 # "ESPN" | "screenshot-ocr" | "manual"
    sportsbook: str               # book behind the lines
    captured_at: datetime
    games: tuple[SlateGame, ...]
    teaser_menu: "TeaserMenu | None"
    parent_slate_id: str | None
    corrections: tuple[dict, ...]
    app_snapshot_id: str          # the app's existing immutable snapshot id [app: locate]

@dataclass(frozen=True)
class TeaserMenu:                 # becomes live.schemas.TeaserPriceSnapshot
    prices: dict                  # {2: Decimal|None, 3: Decimal|None}; None = "not offered"
    sportsbook: str
    captured_at: datetime
    origin: str                   # SNAPSHOT | OPERATOR_ENTRY | OPERATOR_RECONFIRMED
```

---

## 4. Frozen code to reuse (exact)

### 4.1 Converters the app writes

These are thin adapters with no calculation beyond sign flips and string formatting.

**`to_nfl_market_snapshot(slate) -> live.schemas.MarketSnapshot`**
- Construct `MarketSnapshot(season, week, captured_at, sportsbook, ingestion_method, quotes, label, notes)` **[verified]**.
- For every non-excluded game, add **two** `MarketQuote` **[verified]**:
  - home quote: `team=home, spread=home_spread`;
  - away quote: `team=away, spread=-home_spread`.
- `MarketQuote.__post_init__` already runs `normalize_team`, `validate_spread` (half-point
  grid, ±30), `validate_total` (grid, 20–80) and `require_aware`.
  **Catch `MarketValidationError` per game → exclusion INVALID_VALUE.** Do not re-implement
  these checks.
- This mirrors how `scripts/run_cfb_paper_board.py::load` **[verified]** turns one row per game
  into both sides. That script is the precedent for the per-game to per-side expansion.

**`to_cfb_pregame_inputs(slate) -> list[live.paper.PregameLineInput]`**
- Build `PregameLineInput(game_id, team, opponent, spread, total, kickoff, source, line_label)`
  **[verified]**, two per game.
- `line_label = live.paper.CURRENT_PREGAME` **[verified]**.
- Do **not** use `MarketQuote` for CFB: `normalize_team` rejects non-NFL names, and
  `validate_spread` / `validate_total` are NFL plausibility envelopes (±30; 20–80) that would
  wrongly drop legitimate CFB lines such as −35.5 or a total of 81.
- For CFB format checks use only `engine.numeric.on_half_point_grid` **[verified]**. Off-grid →
  INVALID_VALUE.

**`to_price_snapshot(menu, season, week) -> live.schemas.TeaserPriceSnapshot | None`**
- `TeaserPriceSnapshot(season, week, captured_at, sportsbook, quotes)` built from
  `live.pricing.price_from_american(ticket_size, american_odds, sportsbook, captured_at, source_reference)`
  **[verified]**.
- Only sizes with a price are included. A missing size is left out, so EV is `UNAVAILABLE`,
  which is existing behaviour.

### 4.2 Engine calls

The app calls these and never reproduces them.

| Purpose | Call [verified] | App displays |
|---|---|---|
| NFL card | `live.card.grade_week(market, prices, notes=...)` → `WeeklyCard` | the rendered report (next row) |
| NFL rendering | `live.report.render_weekly_report(card, recheck=, placements=, settlements=, teased_board=)` → markdown string | `st.markdown(...)`. Do not rebuild card tables from raw numbers. |
| NFL "all 6-point legs" research | `live.research.teased_board_rows(market)`, `teased_board_summary(rows)` | passed into `render_weekly_report(teased_board=...)` |
| CFB legs | `live.paper.build_cfb_paper_legs(inputs)` → `list[PaperLeg]` | `PaperLeg` fields as stored |
| CFB qualifying / secondary | `live.paper.primary_paper_legs(legs)`, `secondary_paper_legs(legs)` | as returned (already ranked) |
| CFB tickets | `live.paper.build_cfb_paper_tickets(primary, profit_by_size=prices.profit_by_size() if prices else None)` → `(top, list[engine.tickets.Ticket])` | `Ticket.p_ticket`, `.ev`, `.fair_break_even_profit`, `.legs` |
| Re-check (NFL placement) | `live.recheck.recheck_card(card, new_market, new_prices)` | `RecheckResult.overall`, per-ticket verdicts and reasons |
| Placement | `PlacementLedger.validate_model_placement(...)` then `.record(...)`; refusals via `.log_refusal(...)` | exactly the sequence in `cli/live.py::cmd_record_placement` |
| Settlement | `live.settlement.grade_leg_settlement(...)`, `settle_ticket(...)` | unchanged from `cli/live.py::cmd_settle` |
| Rehydration | `live.rehydrate.market_from_dict`, `prices_from_dict`, `card_from_dict`, `recheck_from_dict` | used when loading saved records |

### 4.3 Engine-produced fields the app must display, not compute

- **NFL:** `WeeklyCard` / `GradedLeg` / `TicketView` fields in `live/card.py`, including
  `teased_spread`, `geometry_class`, `track`, `key_numbers_crossed`, `p_raw`, `bump`, `p_est`,
  `p_ticket`, `break_even`, `ev_percent`, `selected` and `status`.
- **CFB:** `PaperLeg` fields and `engine.tickets.Ticket` fields.

### 4.4 Persistence

- **Where to write.** Use `live.workspace.Workspace(root=<APP_DATA_ROOT>)` **[verified]**, pointed at
  the app's own data directory and never at the teaser checkout, or the app's existing store
  if it already wraps one **[app: locate]**.
- **What each piece does:**
  - `Workspace.snapshots.put(id, payload, kind=...)`, `.cards.put(...)`, `.placements` and
    `.season_ledger` are the append-only stores.
  - `snapshot.AppendOnlyStore` makes re-storing identical content a no-op.
  - `snapshot.correction_record` is the correction mechanism.
- **NFL sequence to mirror:** `cli/live.py::cmd_ingest_market`, `cmd_ingest_prices`,
  `cmd_grade_week`. For example, `workspace.cards.put(card.card_id, card.to_dict(), kind="weekly_card")`
  followed by `season_ledger.record_week(WeekLedgerEntry(...))`.

### 4.5 Findings Codex must handle

These gaps are in the teaser repository. The workaround lives in the app, and no model code
changes.

| # | Finding | Required app behaviour |
|---|---|---|
| F-1 | `engine.tickets.Ticket.placement_eligible` is **league-agnostic** (positive EV at an actual price). A CFB ticket with a real menu price and positive EV returns `True`. | For CFB, **never** display or act on `Ticket.placement_eligible`. Display PAPER status derived from the legs' `track` field (every CFB leg has track PAPER, `PaperLeg.live_eligible` is always False). The placement button is never rendered for CFB (AT-31). |
| F-2 | `live/` has **no function that persists or renders a CFB PAPER board**. The stored precedent, `data/live/cards/cfb_paper_board_2026-09-19.json`, was assembled around `paper.py` calls. | The app writes a record of `kind="cfb_paper_board"` with the precedent's fields (`board_id`, `banner`, `frozen_at`, `slate_date`, `line_label`, `games`, `sides`, `primary_qualifiers`, `secondary_top`, `tickets`, `ev_note`, `actual_placements=0`, `actual_units_staked=0`, `model_version="v1.0"`, `outcomes_joined_at_freeze=false`) plus `slate_id` and `price_snapshot_id`. Every value is **copied** from `PaperLeg`/`Ticket` objects. Rendering is display-only. |
| F-3 | `validate_spread` / `validate_total` encode NFL plausibility envelopes. | Apply them to NFL only, via `MarketQuote`. CFB uses the half-point grid check only (§4.1). |
| F-4 | Earlier EXECUTION snapshots stored `sportsbook="USER_SPORTSBOOK_SCREENSHOT"` with the real book in `source_reference` (e.g. `bluecoins.ag`). | New snapshots store the confirmed book name in `sportsbook`. Do not rewrite old records. Treat both forms as valid when reading history. |

---

## 5. Source-to-engine field mappings

**Classification:**
- **REQUIRED:** the engine cannot run without it, and it must come from the source (or,
  failing that, from a minimal operator input, §6).
- **DERIVED:** computed by the adapter from other fields or context. Never typed by the
  operator.
- **OPTIONAL:** not consumed by the engine; kept for display or provenance.

### 5.1 ESPN (public) → normalized → NFL engine input

| ESPN scoreboard field (confirm vs app ingester) | Normalized field | Teaser v1.0 input (`MarketQuote` / `MarketSnapshot`) | Class |
|---|---|---|---|
| `events[].season.year` | `season` | `MarketQuote.season`, `MarketSnapshot.season`, `TeaserPriceSnapshot.season` | REQUIRED |
| `events[].week.number` | `week` | `MarketQuote.week`, `MarketSnapshot.week`, `TeaserPriceSnapshot.week` | REQUIRED (if absent: DERIVED from kickoff via app week table) |
| `events[].date` (UTC ISO) | `kickoff` | `MarketQuote.kickoff` (aware) | REQUIRED |
| `competitions[0].status.type.state` | `exclusion=STARTED` unless `"pre"` | gate only: a started game is not passed | REQUIRED (for gating) |
| `competitors[homeAway=="home"].team.abbreviation` | `home.key` | `MarketQuote.home_team` (normalized by `normalize_team`; ESPN `LAR`→`LA`, `WSH`→`WAS` via `TEAM_ALIASES` [verified]) | REQUIRED |
| `competitors[homeAway=="away"].team.abbreviation` | `away.key` | `MarketQuote.away_team` | REQUIRED |
| `competitions[0].odds[0].details` (e.g. `"KC -3.5"`, `"EVEN"`) | `home_spread` (**authoritative parse**: favourite abbreviation + magnitude; `EVEN` → 0) | home `MarketQuote.spread` | REQUIRED |
| `odds[0].spread`, `odds[0].homeTeamOdds.favorite`, `awayTeamOdds.favorite` | cross-check of `home_spread` sign; disagreement → `CONFLICT` | — | OPTIONAL (validation only) |
| `odds[0].overUnder` | `total` | `MarketQuote.total` | REQUIRED |
| `odds[0].provider.name` | `sportsbook` (fallback `"ESPN"`) | `MarketQuote.sportsbook`, `MarketSnapshot.sportsbook` (non-empty required) | REQUIRED (fallback DERIVED) |
| `odds[0].homeTeamOdds.moneyLine` / `awayTeamOdds.moneyLine` | `home_ml` / `away_ml` | — | OPTIONAL |
| spread and total juice fields | `raw` | — | OPTIONAL |
| `competitions[0].neutralSite`, `events[].id`, `name` | `raw` | `MarketQuote.source_reference` (event id) | OPTIONAL |
| fetch completion time | `captured_at` | `MarketQuote.captured_at`, `MarketSnapshot.captured_at` | DERIVED |
| constant | `source_kind=PUBLIC`, `market_status=REFERENCE` | `MarketQuote.ingestion_method = "espn_public"` | DERIVED |
| `f"{season}_{week:02d}_{away}_{home}"` | `game_key` | `MarketQuote.game_id` (same format as `live.market._derive_game_id` [verified]) | DERIVED |
| side expansion (§4.1) | — | `MarketQuote.team`; away `spread = -home_spread` | DERIVED |
| `details` raw text | `raw` | `MarketQuote.raw_source_value` | OPTIONAL |
| (engine) | — | `leg_id = MarketQuote.leg_key`; `league="NFL"` is set **inside** `grade_week` | never app |

### 5.2 ESPN (public) → normalized → CFB engine input

| ESPN scoreboard field | Normalized | Teaser v1.0 input (`PregameLineInput`) | Class |
|---|---|---|---|
| `competitors[home].team.location` (school name) | `home.display` | `team` / `opponent` | REQUIRED |
| `competitors[*].team.id` | `home.key` / `away.key` | — (`game_key` uniqueness) | DERIVED |
| `competitors[away].team.location` | `away.display` | `team` / `opponent` | REQUIRED |
| `odds[0].details` | `home_spread` (authoritative parse, as §5.1) | `spread` (home side), `-spread` (away side) | REQUIRED |
| `odds[0].overUnder` | `total` | `total` | REQUIRED |
| `events[].date` | `kickoff` | `kickoff` (ISO string) | REQUIRED |
| `status.type.state` | STARTED if not `"pre"` | gate only; `line_label` must be `CURRENT_PREGAME` | REQUIRED (gating) |
| `events[].season.year`, `week.number` | `season`, `week` | only `TeaserPriceSnapshot.season/week` (paper legs don't take them) | REQUIRED for the menu; DERIVED from date if absent |
| `odds[0].provider.name` | `sportsbook` | `source = f"ESPN/{provider}"` | DERIVED |
| constant | — | `line_label = live.paper.CURRENT_PREGAME` | DERIVED |
| `f"{away.display}@{home.display}"` (spaces removed) | — | `game_id` (precedent format in `run_cfb_paper_board.py`) | DERIVED |
| moneylines, juice, neutral site | `raw` / `home_ml` | — | OPTIONAL |
| (engine) | — | `leg_id` (a `PregameLineInput` property); `league="CFB"` is set inside `build_cfb_paper_legs` | never app |

### 5.3 Screenshot extraction → normalized → NFL engine input

This follows the precedent of `data/live/input/nfl_2026_week_02_market_screenshot_1243.csv` and
the stored `prc_2026w02_*` teaser-price snapshots.

| Extraction field (OCR/import) | Normalized | Teaser v1.0 input | Class |
|---|---|---|---|
| row team label (`"GB"` / `"Green Bay Packers"`) | `home` / `away` TeamRef | `MarketQuote.team`, `home_team`, `away_team` via `normalize_team` | REQUIRED |
| home/away: row order or `@` marker | `home` vs `away` | `home_team` / `away_team` | REQUIRED. **DERIVED** first by matching the pair to the same-day REFERENCE/schedule. If that is ambiguous, one swap toggle per game. |
| row spread (`-3`, `+3`) | paired into `home_spread` (sides must be negatives, else CONFLICT) | `MarketQuote.spread` both sides | REQUIRED |
| row spread juice (`-110`) | `raw` | — (teaser engine ignores side juice) | OPTIONAL |
| total (`o/u 44`, often once per game) | `total` | `MarketQuote.total` | REQUIRED |
| moneyline column | `home_ml` / `away_ml` | — | OPTIONAL |
| day header + row time | `kickoff` | `MarketQuote.kickoff` | REQUIRED (the date may be DERIVED from the schedule match) |
| book identity (logo/domain) | `sportsbook` | `MarketQuote.sportsbook`, `MarketSnapshot.sportsbook`, placement book | REQUIRED, confirmed **once per snapshot**, prefilled from the last EXECUTION snapshot |
| screenshot time (status-bar clock / file time) | `captured_at` | `MarketQuote.captured_at`, `MarketSnapshot.captured_at` | REQUIRED, DERIVED default and adjustable once per snapshot |
| kickoff date → week table | `season`, `week` | `MarketQuote.season/week` | DERIVED |
| raw OCR row text | `raw` | `MarketQuote.raw_source_value` | OPTIONAL |
| image filenames | — | `MarketQuote.source_reference` | OPTIONAL |
| constant | `market_status=EXECUTION` | `MarketQuote.ingestion_method = "screenshot_ocr"` | DERIVED |
| `f"{season}_{week:02d}_{away}_{home}"` | `game_key` | `MarketQuote.game_id` | DERIVED |

### 5.4 Teaser menu (any source) → `TeaserPriceSnapshot`

| Field | Engine input | Class | Public (ESPN) | Screenshot |
|---|---|---|---|---|
| rung size (2, 3) | `TeaserPriceQuote.ticket_size` ∈ {2, 3} | REQUIRED | **never supplied** | "2 Teams" / "3 Teams" rung |
| points | `teaser_points` must equal `engine.constants.TEASER_POINTS` (6) | DERIVED/validated | — | "6 pts". Anything else (10- or 13-point "Specials") is ignored. |
| price | `american_odds` (or `decimal_odds`) | REQUIRED for EV | **never supplied → GAP G1** | rung price |
| book | `TeaserPriceQuote.sportsbook`, `TeaserPriceSnapshot.sportsbook` | REQUIRED | **GAP G2** | inherited from the snapshot |
| observed time | `captured_at` | REQUIRED | DERIVED (time of entry) | DERIVED (screenshot time) |
| season/week | `TeaserPriceSnapshot.season/week` | REQUIRED | DERIVED from the slate | DERIVED from the slate |
| 4/5/6-team rungs | — | ignored; noted in `notes` | — | as the existing `prc_2026w02_*` notes do |

### 5.5 Manual (fallback)

The existing quoted-side editor or CSV maps field-for-field onto `live.market.TEMPLATE_COLUMNS`
**[verified]** and `read_market_csv(...)`. That is the manual path; it stays as is. It
**opens pre-filled** from the selected slate, whenever one exists.

---

## 6. What ESPN cannot supply: gaps and the smallest input for each

The engine needs nothing else that public ingestion lacks. In particular `captured_at`,
`game_id`, sides, `line_label`, `ingestion_method` and `source` are all DERIVED.

| Gap | Engine field | Smallest UI input | Never |
|---|---|---|---|
| **G1** teaser prices | `TeaserPriceQuote.american_odds` per size | One numeric field **per missing size** (usually two: 2-team and 3-team), with a "Not offered" checkbox. Entered once per (league, book, day) and then reused (§10). Absent → EV `UNAVAILABLE`, and the card still builds. | re-entering the slate |
| **G2** book for the menu when the lines are REFERENCE | `TeaserPriceQuote.sportsbook` | One **Settings** value, `default_teaser_book` (precedent: `bluecoins.ag`), shown beside the menu. Never asked per proposal. | asking per proposal |
| **G3** total missing for a game | `MarketQuote.total` / `PregameLineInput.total` | That game shows `MISSING_TOTAL` with one inline numeric field (or it stays excluded). | editing other games |
| **G4** no odds at all for a game (common for small CFB games) | spread + total | The game is excluded as `NO_ODDS`. An optional inline pair (spread, total) for that game only, marked `OPERATOR_ENTRY` in `value_origin`. | opening the manual slate editor |
| **G5** NFL week absent | `MarketQuote.week` | DERIVED from kickoff. If still unknown, **one** header field stored on the slate. | asking per game |
| **G6** CFB team name unresolved/ambiguous | `PregameLineInput.team/opponent` | One dropdown for that game, saved to an append-only alias table and never asked again. The NFL needs none: ESPN's `LAR`/`WSH` are already in `TEAM_ALIASES`. | — |

---

## 7. State transitions

```
NONE → (Fetch | Upload→OCR | Manual editor) → DRAFT ⇄ review/correct
DRAFT → [Use this slate for proposal] → CONFIRMED (immutable; REFERENCE | EXECUTION)
[Use saved ▾] → CONFIRMED
CONFIRMED → menu resolved (§10) → READY → [Build] → PROPOSED (immutable card/board)
PROPOSED (NFL + EXECUTION) → [Record placement…] → recheck_card VALIDATED → PLACED → SETTLED
PROPOSED (REFERENCE or CFB) → terminal
```

- Confirming unchanged content is a no-op (same content hash).
- Any edit creates a new slate with `parent_slate_id`.

---

## 8. REFERENCE vs EXECUTION

| | REFERENCE | EXECUTION | PLACED |
|---|---|---|---|
| Build a proposal | yes (CFB PAPER; NFL screening) | yes | — |
| Placement control | not rendered | NFL only, and only when the card is EXECUTABLE (below) | — |
| Exposure / P&L | never | never | **only** |

**D-1: the menu book and labelling.**

- **Default book.** `default_teaser_book` is an operator setting, default `"bluecoins.ag"`,
  changeable later. It supplies the menu book for REFERENCE slates.
- **Card classification.** A card is **EXECUTABLE** only if all three hold:
  1. `league == "NFL"`;
  2. `slate.market_status == "EXECUTION"`;
  3. `slate.sportsbook == menu.sportsbook`.

  Every other combination is a **public/reference-market proposal**, and the banner names
  both sources. For example, ESPN/DraftKings lines with bluecoins.ag teaser pricing give
  "PUBLIC/REFERENCE-MARKET PROPOSAL — lines: ESPN/DraftKings · teaser pricing: bluecoins.ag
  — NOT AN EXECUTABLE BLUECOINS SLATE".
- **Mixed books.** An EXECUTION slate from one book priced with another book's menu is
  labelled "MIXED-BOOK PROPOSAL — NOT EXECUTABLE", and no placement control is rendered
  (AT-38, AT-39).
- **Card record.** The card stores `lines_source`, `lines_book`, `menu_book` and
  `executable: bool`, so the classification is auditable.

**D-2: fresh teaser-price confirmation.**

- **The control.** A button labelled **"I verified these teaser prices are unchanged now"**.
  It appears wherever a saved menu is used: the proposal page, and the placement dialog when
  the menu is older than `MAX_PRICE_LAG` (30 min).
- **Explicit action only.** It is recorded only when the operator clicks it. It is never
  automatic, never on page load, and never triggered by another action.
- **What a click writes.** A **new** `TeaserPriceSnapshot` built with
  `price_from_american(ticket_size, american_odds, sportsbook, captured_at=<click time, tz-aware>, source_reference="operator verified unchanged; parent <old prc id>")`
  for each confirmed size. `label = "OPERATOR_RECONFIRMED"`. The sportsbook and the confirmed
  2-team/3-team prices are recorded in it.
- **No silent extension.** The old snapshot is **not** modified and keeps its original
  `captured_at`. The new snapshot has its own content hash and id.
- **Same effect as re-typing.** Downstream it is used exactly like a manually re-entered
  menu. It is passed as `new_prices` to `recheck_card` and so satisfies `MAX_PRICE_LAG` by the
  existing code path. No change to `live/placement.py` or `live/recheck.py`.
- **Prices changed.** If the prices changed, the operator types the new ones instead. The
  button cannot alter prices.

**Placement** reuses `cmd_record_placement`'s exact sequence:
- `validate_model_placement` runs **before** anything is written;
- on refusal, `log_refusal` is called and no row is written;
- on success, `record(...)` is called.

All existing gates stay:
- the re-check must be VALIDATED and at most 30 minutes old (`MAX_RECHECK_AGE`);
- the re-check must use a newer market snapshot than the card;
- the price lag must be at most 30 minutes (`MAX_PRICE_LAG`);
- pre-kickoff only (`PostKickoffPlacement`).

**Additional app-level guard.** The app refuses, and logs through `log_refusal`, any
placement whose card came from a REFERENCE slate or from CFB. This covers the case where the
button is somehow reached. A bet made from a REFERENCE screen can be recorded only as
`EXTERNAL_NON_MODEL` **[verified]**.

**Prefill.** The placement dialog fills book, odds (the ticket's `offered_american`), legs,
stake (`UNITS_PER_TICKET`) and `placed_at=now` from the records. The only operator input is
the optional book reference.

**Stale menu at placement.** Use the D-2 button above; no prices are retyped.

---

## 9. Edge states

| State | Behaviour | Blocks build? |
|---|---|---|
| No saved snapshot | Show the Fetch / Upload / Open-editor CTA; Build disabled | yes |
| Partially populated | Excluded games listed with reasons; inline fixes (§6 G3/G4) for only those cells | no (if ≥ 1 usable) |
| Duplicated games | Identical → merge and note; different → CONFLICT | only if conflicting |
| Conflicting screenshot fields | Cell highlighted; operator picks the value; recorded in `corrections` | yes, until resolved |
| Public vs EXECUTION disagreement | Diff panel (existing comparison view [app: locate]), display-only; never merged | no |
| Stale snapshot | Amber banner if > 2 h old or not today; the card records the age; placement freshness comes from existing gates | no |
| Teaser price absent | G1: only the missing sizes asked | no |
| Malformed teaser price | Inline error (0, \|A\| < 100, non-numeric, decimal ≤ 1). Rendered by `TeaserPriceQuote` validation where possible. Soft warning outside 2-team −150…+100 / 3-team +100…+250. | that field |
| Game already started | STARTED, greyed, never passed to the engine | no |
| Unsupported geometry / guardrail fail | Not an error. The engine classifies it; it shows in the research section (NFL `teased_board_rows`, CFB `secondary_paper_legs`) | no |
| Missing total | G3 | no |
| Ambiguous team name | G6 | that game |
| Screenshot parser failure | Images kept; review grid pre-filled with whatever parsed; the manual editor pre-fills from the grid | until confirmed |
| Operator correcting OCR | Stored in `corrections` (old, new, time); raw OCR kept | no |
| Older saved snapshot | Picker shows source, book, status, captured time and age; the card records `slate_id`; placement is governed by the existing freshness gates | no |
| ESPN spread sign disagreement | `details` vs `spread`/favourite flags disagree → CONFLICT; one radio to resolve | that game |

---

## 10. Inheritance: nothing asked twice

| Fact | Source of truth | Asked? |
|---|---|---|
| Line book | confirmed slate `sportsbook` | never downstream |
| Menu book | EXECUTION: the slate; REFERENCE: Settings `default_teaser_book` (`bluecoins.ag`) | Settings, once |
| Menu freshness | D-2 one-click verification | one click, never retyping |
| Menu prices | slate menu → saved menu (league, book, day) → other league's same-book menu offered as one click, never silently → ask only missing sizes | at most once per league, book and day |
| Season / week | source → kickoff-derived → one header field | at most once per slate |
| Home / away (screenshot) | schedule match → one toggle per ambiguous game | at most once per game |
| Team alias (CFB) | alias table | once ever per name |
| Capture time | fetch time / screenshot time | adjust at most once per snapshot |
| Placement fields | card, ticket and snapshot | only the optional book reference |
| Selection after a Streamlit rerun or reload | persisted working selection | never |

**Adversarial check: can the operator be trapped into re-entry? No.** Every fact above has
one origin and is inherited from it. Only two things legitimately remain:
- an NFL placement needs a **new** board capture, because the frozen re-check rule requires a
  newer market snapshot. That is new information;
- prices that exist nowhere in the system are asked once.

Stale menus are handled by the D-2 click.

---

## 11. Acceptance tests

Use `pytest` for converters and adapters, and `streamlit.testing.v1.AppTest` for the UI.

**Fixtures:**
- recorded ESPN NFL and CFB scoreboard JSON (pregame);
- mocked OCR output modelled on `nfl_2026_week_02_market_screenshot_1243.csv`;
- the `TEMPLATE_COLUMNS` CSV;
- a frozen clock.

**Widget keys** (part of the contract): `src_radio`, `fetch_btn`, `use_saved`, `confirm_btn`,
`menu_2`, `menu_3`, `build_btn`, `place_btn`, `manual_side_editor`.

| # | Test | Pass condition |
|---|---|---|
| AT-01 | ESPN NFL → proposal | NFL, Public, Fetch, Use-slate, Build → REFERENCE card; `manual_side_editor` never rendered |
| AT-02 | ESPN CFB → PAPER | Same path → CFB board with `PAPER_BANNER`; no screenshot needed |
| AT-03 | Screenshot → proposal | Upload (mock), confirm, Build → EXECUTION card; no side entry |
| AT-04 | Book inherited | Every `GradedLeg.sportsbook`, `WeeklyCard.sportsbook` and price book equal the slate's; no sportsbook widget on the proposal page |
| AT-05 | Menu inherited | Snapshot has 2 and 3 → `menu_2`/`menu_3` not rendered as inputs |
| AT-06 | Only missing asked | Snapshot has 2-team only → exactly one price input |
| AT-07 | Manual works | Template CSV → card equal to `cmd_grade_week` output on the same market and prices |
| AT-08 | REFERENCE cannot place | No `place_btn`; a direct handler call raises; `log_refusal` row written; placement row count unchanged |
| AT-09 | EXECUTION not auto-placed | After Build the ledger is unchanged; PLACED only via the dialog and a VALIDATED fresh re-check |
| AT-10 | Snapshots immutable | Re-confirm → same id, no new file; one edit → new id with parent; original bytes unchanged |
| AT-11 | Settlement intact | Existing settlement/accounting tests pass unmodified |
| AT-12 | Source-independent output | Same games, lines and menu via public, screenshot and manual → identical `(leg_id, spread, teased_spread, geometry_class, track, p_est)`, tickets, `p_ticket` and EV; only provenance ids differ |
| AT-13 | Side expansion | Two quotes per game; away = −home; same total; unique `leg_key` |
| AT-14 | Teaser repo untouched | The app never writes under the teaser checkout; `Workspace.root` is the app data directory; the installed `teaser_model_v1` hash is unchanged |
| AT-15 | CFB never through `MarketQuote` | Spy: `normalize_team` / `validate_spread` never called for CFB |
| AT-16 | Started games excluded | Frozen clock after one kickoff → that game is not passed to the engine |
| AT-17 | Partial slate | 2 of 10 missing totals → card from 8; exactly 2 inline inputs offered |
| AT-18 | Reload survives | After an AppTest rerun: same slate and menu, no refetch, no re-entry |
| AT-19 | Menu once | Second CFB build the same day asks nothing; switching to NFL with the same book → one [Use] click, never silent |
| AT-20 | Menu reconfirm (D-2) | 45-minute-old menu → one click creates an `OPERATOR_RECONFIRMED` snapshot → placement passes the existing `MAX_PRICE_LAG` gate |
| AT-21 | Placement prefill | The dialog has no required text input except the optional reference |
| AT-22 | Conflict blocks confirm | Conflicting OCR sides → `confirm_btn` disabled until resolved |
| AT-23 | Duplicates | Identical overlap merged; differing overlap → conflict |
| AT-24 | Alias memory | Resolve an ambiguous CFB name once; the next fetch resolves it silently |
| AT-25 | Malformed prices | `0`, `50`, `abc`, `1.0` rejected; `+170`, `170`, `2.70` equal |
| AT-26 | Diff is display-only | Mutating the REFERENCE fixture leaves the EXECUTION card unchanged |
| AT-27 | No invented prices | Every card price traces to a snapshot, an entry or a reconfirm with book and time |
| AT-28 | Older snapshot | Stale banner; `slate_id` recorded; placement refused by the existing gates |
| AT-29 | Moneylines inert | Changing moneylines leaves the card unchanged after removing provenance |
| AT-30 | No research imports | No `ats_model` / `moneyline_model` import in the app |
| AT-31 | **CFB never placement-eligible (F-1)** | CFB fixture with an actual menu price and a positive-EV ticket: `Ticket.placement_eligible` may be True, but the UI shows PAPER, renders no `place_btn`, and the handler refuses |
| AT-32 | **No duplicated model math** | Static check: app modules import no private engine helpers, and define no functions named or computing `p_est`, `p_raw`, `bump`, `teased`, `break_even`, `ev`, `guardrail`, `classify`. Card numbers equal `grade_week` / paper outputs exactly. |
| AT-33 | ESPN sign cross-check | `details="KC -3.5"` with a contradicting numeric sign → CONFLICT, not silently flipped |
| AT-34 | CFB envelope | CFB line −35.5 and total 81 are accepted and passed to the engine (secondary/research, not dropped); an off-grid value is rejected |
| AT-35 | NFL aliases | ESPN `LAR`, `WSH` → `LA`, `WAS` through `normalize_team`, with no app alias code |
| AT-36 | No-odds game | Only a two-field inline pair is offered for that game; the manual editor is not opened |
| AT-38 | Mixed-source labelling (D-1) | ESPN lines + bluecoins.ag menu → banner names both and says "NOT AN EXECUTABLE BLUECOINS SLATE"; the card records `executable=false`, `lines_book`, `menu_book` |
| AT-39 | Executable only when books match | EXECUTION slate from book X + bluecoins.ag menu → MIXED-BOOK, no `place_btn`, handler refuses. EXECUTION bluecoins.ag slate + bluecoins.ag menu → EXECUTABLE. |
| AT-40 | Reconfirm is explicit and additive | No new price snapshot appears without the click. After the click, the old snapshot's bytes and `captured_at` are unchanged; the new one has the click time, same prices and book, and a parent reference. |
| AT-41 | Reconfirm ≡ re-entry | The placement gate outcome with a reconfirmed snapshot equals the outcome with a manually re-entered identical snapshot at the same timestamp |
| AT-37 | CFB board record | The stored `cfb_paper_board` contains the F-2 precedent fields, and every numeric value equals the `PaperLeg`/`Ticket` value |

---

## 12. Implementation order

Build P0 in this order; P1 and P2 follow the checklist in §0.

1. Converters and side expansion (P0-4, P0-14, P0-15), with AT-12, 13, 15, 16, 34, 35.
2. Adapters from the existing ESPN, OCR and manual outputs into `NormalizedSlate` (P0-2, P0-3).
3. Settings (`default_teaser_book = "bluecoins.ag"`), the menu resolver and the D-2 button
   (P0-6 to P0-9).
4. Page: source choice, persisted selection, engine calls and rendering, CFB board record, and
   banners (P0-1, P0-5, P0-10, P0-11, P0-16).
5. Placement: executable classification, app-level guard, prefilled dialog, and F-1 (P0-12,
   P0-13).
6. P0 acceptance tests and existing suites green, then the Saturday dry run.

## 13. Non-goals

- No edit to the teaser repository.
- No model, parameter, geometry, EV or threshold change.
- No reimplementation of engine math.
- No ATS, Moneyline or parlay work.
- No automated wagering.
- No paid feed.
- No CFB placement.
- No 4-, 5- or 6-team or "Special" teasers.
- No settlement redesign.
- No backfilling of started games.

## 14. Saturday definition of done (exact)

Saturday-ready means **all** of the following are true on the app's main branch.

1. **Every P0 item (P0-1 … P0-16) is implemented.**
2. **Every P0 test passes:**
   AT-01 to AT-16, AT-17 (exclusion part), AT-18 (rerun part), AT-19 to AT-21, AT-25 to AT-27,
   AT-29 to AT-32 (numeric-equality part of 32), AT-34, AT-35, AT-37 to AT-41.
   P1 tests (AT-22, 23, 24, 28, 33, 36, and the reload part of AT-18) may be marked
   `xfail(reason="P1")`. They may not be deleted.
3. **Existing suites pass unmodified:** the app's own tests, and the teaser repo's
   `live`/`engine`/settlement suites run against the installed `teaser_model_v1`.
4. **No teaser file is changed and no model math is duplicated.** `git diff` of the teaser
   dependency is empty (AT-14), and no model math is duplicated in the app (AT-32).
5. **Live CFB dry run.** On Saturday's actual ESPN CFB slate, the path CFB → Public lines →
   Fetch → Use this slate → Build produces a saved `cfb_paper_board` record with:
   - the PAPER banner and the "Lines: ESPN/<provider> · Teaser pricing: bluecoins.ag" label;
   - zero quoted-side inputs;
   - teaser prices typed at most once, or zero times if a menu was already saved or verified
     that day;
   - no placement control.
6. **NFL rehearsal on fixtures.**
   - A public slate produces a "PUBLIC/REFERENCE-MARKET PROPOSAL … NOT AN EXECUTABLE BLUECOINS
     SLATE" card with no placement control.
   - A bluecoins.ag screenshot EXECUTION slate produces an EXECUTABLE card.
   - A recorded placement succeeds only after a fresh re-check. A stale menu is refreshed by
     the D-2 click without retyping.
   - A direct placement call against the public card is refused and appears in
     `refusals.jsonl`.
7. **Placements unchanged by the dry runs.** Placement ledger row count and units are
   unchanged, except for rows the operator explicitly records.

## 15. Operator decisions (resolved)

| ID | Decision | Resolution |
|---|---|---|
| D-1 | Menu book for public-line slates | **`bluecoins.ag`**, kept as the operator setting `default_teaser_book`. Proposals built from public lines plus the Bluecoins menu are labelled public/reference-market proposals using Bluecoins teaser pricing. They are executable only when the lines also come from a confirmed Bluecoins EXECUTION snapshot (§8). |
| D-2 | One-click fresh menu confirmation | **Approved.** The "I verified these teaser prices are unchanged now" click writes a new, explicitly operator-created price observation with the click time, book and prices. It satisfies the existing 30-minute rule exactly as re-entry would, and never extends an old menu's age (§8). |

Nothing else is open for the operator.
