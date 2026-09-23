# STREAMLIT_MARKET_TO_PROPOSAL_HANDOFF

**For:** Codex, implementing in the Streamlit app repository.
**Deadline:** Saturday (CFB PAPER slate), and the NFL slate on Sunday.
**Scope:** wiring and UX only. No model change of any kind.

> **What was verified, and what was not.** The Streamlit app was not available when this was
> written. The interfaces below that are marked **[verified]** exist in
> `Football-Teasers-v1.0` at commit `a29afd5` (`src/teaser_model_v1/live/`). Everything
> marked **[app: locate]** is a component the operator says the app already has, and Codex
> must find it and reuse it. If an app component already does what a section asks, reuse it
> and do not rebuild it.

---

## 1. Non-negotiables

1. **Frozen models stay frozen.** Do not edit `teaser_model_v1/engine/`. Do not touch ATS v0 or
   Moneyline v0: both are completed NO MODEL / NO BET results, locked in
   `Football-Betting-Research`, and none of this work surfaces them. Do not add a moneyline
   proposal. Moneylines are carried for display only.
2. **One model path per league, never per source.**
   - NFL: slate → `MarketSnapshot` → `live.card.grade_week` **[verified]**.
   - CFB: slate → `live.paper.PregameLineInput` → `build_cfb_paper_legs` →
     `primary_paper_legs` → `build_cfb_paper_tickets` **[verified]**.
   - How the slate arrived (public, screenshot, manual) must never change what these receive.
3. **PROPOSED is never PLACED.** Only an explicit operator action writes a placement row.
   Nothing ever submits a wager.
4. **Snapshots are append-only.** A correction or a later capture is a new snapshot that
   points at its parent. Nothing is edited in place.
5. **Timestamps carry an offset. Lines and totals stay exact decimals.**
6. **Enter once, inherit everywhere.** Every fact present in a confirmed snapshot, or in the
   operator's saved settings, is inherited downstream. It is never asked again.

---

## 2. Target UX: one page, top to bottom

```
LEAGUE        (•) NFL   ( ) CFB                               ← remembered per session
MARKET SOURCE (•) Public lines  ( ) My sportsbook  ( ) Manual
┌ source controls ───────────────────────────────────────────┐
│ Public:     date [today]  [Fetch]      or  [Use saved ▾]    │
│ Sportsbook: [Upload screenshots]       or  [Use saved ▾]    │
│ Manual:     [Open editor (pre-filled from selected slate)]  │
└─────────────────────────────────────────────────────────────┘
SELECTED MARKET
  Source: ESPN (DraftKings lines)   Status: REFERENCE
  Captured: Sat 11:42 -04:00 (18 min ago)   Games: 47 usable / 52   [Review slate ▸]
  Banners: excluded games (reasons) · stale · started games · conflicts
TEASER MENU  (6-point)
  2-team: −110  ✓ from snapshot     3-team: [ +170 ]  ← asked ONLY because it is missing
  Menu book: DraftKings (inherited)
[ BUILD PROPOSAL ]                ← disabled only while a blocking error remains
─────────────────────────────────────────────────────────────
PROPOSAL CARD
  Banner (always shown), one of:
    CFB → "CFB PAPER/RESEARCH — NOT LIVE v1.0"
    NFL + REFERENCE → "REFERENCE PRICING — SCREENING ONLY — NOT EXECUTABLE"
    NFL + EXECUTION → "EXECUTABLE PROPOSAL — PROPOSED, NOT PLACED"
  [Record placement…] appears ONLY on NFL + EXECUTION cards (§6)
```

A normal Saturday takes **five clicks**: CFB → Public lines → Fetch → [Use this slate for
proposal] → Build proposal. Typing one or two prices happens only when no menu exists anywhere
in the system that day.

---

## 3. Normalized data contract

Every source produces **exactly this**. Everything downstream consumes only this.

```python
@dataclass(frozen=True)
class SlateGame:
    game_key: str             # stable id: f"{league}:{season}:{week}:{away_key}@{home_key}"
    league: str               # "NFL" | "CFB"
    season: int
    week: int | None          # NFL required (inherited from source); CFB may be None
    kickoff: datetime         # tz-aware
    home: TeamRef             # TeamRef(key, display, source_name)
    away: TeamRef
    home_spread: Decimal      # HOME perspective; negative = home favoured; half-point grid
    total: Decimal | None     # None → game excluded (MISSING_TOTAL); never imputed
    home_ml: Decimal | None   # display only
    away_ml: Decimal | None   # display only
    raw: dict                 # exactly what the source said, before normalization
    exclusion: str | None     # STARTED | MISSING_SPREAD | MISSING_TOTAL | INVALID_VALUE |
                              # UNRESOLVED_TEAM | CONFLICT (see §7)

@dataclass(frozen=True)
class TeaserMenu:
    prices: dict[int, Decimal | None]   # {2: -110, 3: +170}; None = operator says unavailable
    sportsbook: str
    captured_at: datetime               # when the prices were observed
    origin: str                         # SNAPSHOT | OPERATOR_ENTRY | OPERATOR_RECONFIRMED
    parent_menu_id: str | None

@dataclass(frozen=True)
class NormalizedSlate:
    slate_id: str             # content hash (reuse live.provenance.new_record_id [verified])
    league: str
    source_kind: str          # PUBLIC | SPORTSBOOK_SCREENSHOT | MANUAL
    market_status: str        # REFERENCE | EXECUTION
    provider: str             # "ESPN", "screenshot-ocr", "manual"
    sportsbook: str           # book behind the lines (ESPN odds provider name, screenshot book, …)
    captured_at: datetime
    confirmed_at: datetime
    games: tuple[SlateGame, ...]
    teaser_menu: TeaserMenu | None      # present if the source carried one
    parent_slate_id: str | None         # set when this slate corrects or re-captures another
    corrections: tuple[dict, ...]       # {game_key, field, old, new, by, at}
    app_snapshot_id: str                # the app's existing immutable snapshot id [app: locate]
```

**Converters.** These are pure functions, the only bridge into the frozen code, and each one
is unit-tested.

| Function | Output | Notes |
|---|---|---|
| `to_nfl_market_snapshot(slate)` | `live.schemas.MarketSnapshot` **[verified]** | **Expands each game into both sides**: home `MarketQuote(spread=home_spread)`, away `MarketQuote(spread=-home_spread)`. The quote's `sportsbook` is `slate.sportsbook`; `ingestion_method` is `source_kind`; `captured_at` is `slate.captured_at`. Excluded games are not emitted. This expansion is the fix for the manual quoted-side step. |
| `to_cfb_pregame_inputs(slate)` | `list[live.paper.PregameLineInput]` **[verified]** | Two inputs per game (home and away perspective). `line_label = "current_pregame"`; `source = f"{provider}/{sportsbook}"`. Do **not** route CFB through `MarketQuote`: `normalize_team` accepts NFL clubs only. |
| `to_price_snapshot(menu, season, week)` | `live.schemas.TeaserPriceSnapshot` **[verified]** or `None` | Only sizes with a price. A missing size → EV `UNAVAILABLE` (existing engine behaviour). |
| `build_proposal(slate, menu)` | PROPOSED card plus a provenance record | NFL → `grade_week(market, prices)`. CFB → the paper pipeline with `profit_by_size = prices.profit_by_size()`. Stores `slate_id`, `app_snapshot_id`, menu id, `market_status` and the banner. |

**Per-league invariants, checked at normalization:**
- `away ≠ home`;
- the spread is on the half-point grid, |spread| ≤ 30 (`schemas.validate_spread` **[verified]**);
- the total is in [20, 80] (`validate_total` **[verified]**);
- one game per `game_key`.

---

## 4. State transitions

```
            ┌─────────── Public: Fetch ───────────┐
NONE ──────►│ Sportsbook: Upload → OCR/extract     ├──► DRAFT ──review/correct──► DRAFT'
            └─────────── Manual: editor ──────────┘            │
                                                     [Confirm]  ▼
     [Use saved ▾] ─────────────────────────────────► CONFIRMED  (immutable; REFERENCE | EXECUTION)
                                                                │ resolve menu (§5)
                                                                ▼
                                                       READY ──[Build]──► PROPOSED (immutable card)
                                                                              │
                     NFL + EXECUTION only:  [Record placement…] → re-check (§6) ─► PLACED ─► SETTLED
                     REFERENCE or CFB:      terminal at PROPOSED (no path to PLACED)
```

- **Public fetch:** confirming is one click on the review screen: the
  **[Use this slate for proposal]** button (`confirm_btn`). Nothing is re-typed.
- **Confirming an unchanged saved slate** is idempotent: same content hash, same snapshot.
  Existing `AppendOnlyStore` behaviour **[verified]**.
- **Any edit** after confirmation creates a **new** slate with `parent_slate_id` set.

---

## 5. Source selection and inheritance rules

| Source | Adapter [app: locate] | `market_status` | `sportsbook` | season/week | Teaser menu |
|---|---|---|---|---|---|
| Public lines | existing ESPN/public ingestion | REFERENCE | ESPN odds provider name (e.g. DraftKings); if absent, `"ESPN"` | from ESPN event metadata | never present → §5.2 |
| My sportsbook | existing OCR/import + review | EXECUTION | from the confirmed snapshot | from the snapshot, else derived from the kickoff date via the app's NFL week table | inherited if extracted |
| Manual | existing quoted-side editor (fallback only) | chosen **once** in the editor: "From my sportsbook (EXECUTION)" (default) or "Reference" | settings default, editable once | from the editor header, pre-filled | entered in the same editor if wanted |

### 5.1 Default selection

- On load, preselect the **most recent confirmed slate** for the current league from today,
  if one exists (§8 AT-18).
- If none exists, preselect "Public lines" for CFB and "My sportsbook" for NFL.

### 5.2 Teaser menu resolution

This is the **only** place prices are ever asked for. First match wins:

1. **Carried.** The selected slate carries a menu → use it (`origin = SNAPSHOT`).
2. **Saved.** A saved menu exists for (league, `menu_book`) from today → prefill it, showing
   "from <book> at <time>". Accepting it asks nothing.
   2b. **Other league.** Only the other league's menu exists for that book today → offer it as
   a one-click prefill ("Use DraftKings NFL menu −110/+170 for CFB? [Use]"). It is never applied
   silently, because a book's CFB and NFL teaser menus can differ.
3. **Missing.** Otherwise render inputs **only for missing sizes**. Accept `-110`, `+170`,
   `170` or decimal `2.70`. A "Not offered" checkbox is available per size.

Where `menu_book` comes from:
- for EXECUTION slates, `slate.sportsbook`;
- for REFERENCE slates, `settings.default_teaser_book`, set once in Settings and shown next
  to the menu. It is never asked per proposal.

Prices entered once are stored as a `TeaserPriceSnapshot` (existing schema) keyed to that book
and time, and linked to the proposal. A missing price never blocks the build: those tickets
show `P_ticket` with EV `UNAVAILABLE` (existing engine behaviour).

---

## 6. REFERENCE vs EXECUTION semantics

| | REFERENCE (public) | EXECUTION (sportsbook) | PLACED |
|---|---|---|---|
| Can build a proposal | **Yes** (CFB PAPER; NFL screening) | Yes | — |
| NFL EV shown | yes, labelled "reference pricing" | yes | — |
| "Record placement" control | **not rendered** | NFL only | — |
| Creates exposure / P&L | never | never | **only this** |
| Re-check source | — | a **newer** EXECUTION snapshot (existing rule) | — |

**NFL EXECUTION placement.** This reuses `live.recheck.recheck_card` and
`live.placement.PlacementLedger` **[verified]** unchanged. Their existing refusals stay:
- re-check must be VALIDATED and at most 30 minutes old;
- re-check must use a newer market snapshot than the card;
- teaser price lag at most 30 minutes;
- pre-kickoff only.

**Minimum-entry placement flow:**

1. Click "Record placement…". The dialog shows the ticket.
2. **Fresh board.** "Capture current board" re-opens the screenshot uploader. The confirm
   screen **pre-fills from the card's snapshot** and highlights only the changed cells. This
   is new information required by the frozen spec, not re-entry.
3. **Menu freshness.** If the menu is older than 30 minutes, offer
   **[Menu unchanged at <book> — confirm now]**. This writes a new `TeaserPriceSnapshot` with
   the same prices, `captured_at = now` and `origin = OPERATOR_RECONFIRMED` (decision D-2).
   Typing new prices is needed only if they changed.
4. **Placement fields.** Book, odds, ticket legs, stake (1u) and `placed_at = now` are all
   pre-filled from the snapshot and ticket. The operator adds only the optional book ticket
   reference, then confirms.

**Defence in depth.** Before `PlacementLedger` is called, the app must refuse any placement
whose card came from a REFERENCE slate or from CFB, even if a URL or state hack renders the
button. Raise `PlacementRefused`; do not write a row. Do this in the app layer, not in
`engine/`.

A bet the operator actually made from a REFERENCE screen can only be recorded as
`EXTERNAL_NON_MODEL` (existing designation **[verified]**). It never counts toward the model
record.

---

## 7. Edge and error states

| State | Detection | Behaviour | Blocks build? |
|---|---|---|---|
| No saved snapshot | the picker is empty | Show the source CTA (Fetch / Upload / Open editor). Build is disabled with "No market selected". | yes |
| Partially populated slate | some games lack spread/total/team | Those games are excluded with a reason; banner "N of M usable"; [Fix] opens an inline cell editor for **only** those cells → a new slate. | no (if ≥ 1 usable) |
| Duplicated games | same `game_key` twice (overlapping screenshots) | Identical values → merge silently and note it. Different values → CONFLICT (next row). | no / yes |
| Conflicting screenshot fields | side spreads not negatives of each other, two totals, two kickoffs | The review grid highlights the cell and the operator picks a value (radio). The choice is recorded in `corrections`. | yes, until resolved |
| Public vs EXECUTION disagreement | the existing comparison view **[app: locate]** | Informational diff panel only. Never auto-merge. EXECUTION governs executable proposals; REFERENCE governs nothing it wasn't selected for. | no |
| Stale snapshot | `now − captured_at` > `STALE_WARN` (default 2 h) or older than today | Amber banner with the age. The build is still allowed and the card records the age. Placement freshness is enforced by the existing 30-minute rules. | no |
| Teaser price absent | §5.2 step 3 | Ask only the missing sizes; "Not offered" allowed. | no |
| Malformed teaser price | 0, \|A\| < 100, non-numeric, decimal ≤ 1, any size other than 2 or 3 | Inline error on that field. Soft warning (with confirm) if outside plausible ranges (2-team −150…+100, 3-team +100…+250). | only that field |
| Game already started | `kickoff ≤ now` at build time | Excluded with STARTED and shown greyed. Never priced. NFL placement is also blocked by the existing `PostKickoffPlacement`. Historical CFB reconstruction keeps using the existing archived-pregame path and is out of scope. | no |
| Unsupported spread geometry | the engine classifies | **Not an error.** Legs outside primary geometry, or failing the total guardrail, appear in the existing "all 6-point legs" research section with their reason. Only legal values are validated here. | no |
| Missing total | `total is None` | Game excluded (MISSING_TOTAL). The inline fix asks for that one total only. Totals are never imputed. | no |
| Ambiguous team name | alias lookup fails or has more than one match | Per-game dropdown of candidate teams. The choice is saved to an **alias table** (append-only, audited) so it is never asked again. | that game only |
| Screenshot parser failure | OCR raises or returns nothing | Keep the images. Open the review grid pre-filled with whatever parsed plus blank rows for the rest. The Manual editor pre-fills from the same grid. The upload is never lost. | until confirmed |
| Operator correcting OCR | cell edited in review | Stored in `corrections` with the old value, new value and time. The raw OCR is kept in `raw`. | no |
| Selecting an older saved snapshot | picker | Shows source, book, status, captured time and age, and the stale banner if applicable. The proposal records this snapshot's id. For placement the §6 freshness rules apply. | no |
| Season/week unknown (NFL) | missing from the source | Derive it from the kickoff date via the app's week table. If that is still unknown, ask **once** in the slate header; the answer is stored on the slate. | yes, until set |

---

## 8. Acceptance tests (exact)

Use `pytest` for the pure layer and `streamlit.testing.v1.AppTest` for the UI.

**Fixtures:**
- recorded ESPN JSON: NFL week 3 2026 and a CFB Saturday slate, **pregame only**;
- a recorded OCR output for a sportsbook screenshot set, with the OCR engine mocked (no live
  OCR in CI);
- a manual-entry CSV in the existing template **[verified]** `live.market.TEMPLATE_COLUMNS`;
- a frozen clock.

**Widget keys** are part of the contract: `src_radio`, `fetch_btn`, `use_saved`, `confirm_btn`,
`menu_2`, `menu_3`, `build_btn`, `place_btn`, `manual_side_editor`.

| # | Test | Pass condition |
|---|---|---|
| AT-01 | ESPN NFL → proposal | Clicks: NFL, Public, Fetch, Use this slate, Build. `manual_side_editor` never rendered. Card exists with the REFERENCE banner. Zero quote-text inputs touched. |
| AT-02 | ESPN CFB → PAPER | Same click path. Card has the `PAPER_BANNER` **[verified]**. `live_eligible` is False for every leg. No sportsbook screenshot required. |
| AT-03 | Screenshot → proposal | Upload (mocked OCR), Confirm, Build. No side entry. Card banner is EXECUTION. |
| AT-04 | Book/source inherited | The card's `sportsbook`, every `GradedLeg.sportsbook` and the price-snapshot book equal the confirmed snapshot's. No widget asking for a sportsbook is rendered on the proposal page. |
| AT-05 | Menu inherited | Snapshot carries −110/+170 → `menu_2`/`menu_3` are not rendered as inputs; the card uses those prices. |
| AT-06 | Only missing prices asked | Snapshot has 2-team only → exactly one price input (`menu_3`) is rendered; nothing else is asked. |
| AT-07 | Manual still works | The template CSV loads through the manual editor → Confirm → Build → a card identical to the CLI `grade-week` output for the same market and prices. |
| AT-08 | REFERENCE can't be placed | `place_btn` is absent on a REFERENCE card. Calling the placement handler directly with that card raises `PlacementRefused`, and the placement ledger's row count is unchanged. |
| AT-09 | EXECUTION not auto-placed | After Build, the ledger's row count is unchanged and card status is `PROPOSED`. It becomes `PLACED` only after the explicit dialog confirm, and only with a VALIDATED fresh re-check. |
| AT-10 | Snapshots immutable | Re-confirming an unchanged slate returns the same id (no new file). Editing one cell creates a new id with `parent_slate_id`. The original file bytes are unchanged (hash before/after). |
| AT-11 | Settlement intact | The existing settlement/accounting test suite passes unmodified. A placed fixture ticket settles to the same units as before this change. |
| AT-12 | Source-independent model output | The same games, lines, totals and menu delivered via public (with status forced for the test), screenshot and manual produce identical `(leg_id, spread, teased_spread, geometry_class, track, p_est)` rows, identical tickets and identical EV. Only provenance ids may differ. |
| AT-13 | Side expansion | For every game: two quotes, away = −home, same total. `leg_key`s are unique. |
| AT-14 | Engine untouched | `git diff` over `teaser_model_v1/engine/` is empty. The engine's own test suite passes. |
| AT-15 | CFB never through `MarketQuote` | Spy on `normalize_team`: never called with CFB names. CFB routes only through `PregameLineInput`. |
| AT-16 | Started games excluded | A frozen clock after one kickoff → that game is STARTED and absent from the legs; the others are unaffected. |
| AT-17 | Partial slate builds | 2 of 10 games have no total → a card from 8, with the banner listing 2 MISSING_TOTAL. The fix prompt renders exactly 2 inputs. |
| AT-18 | Rerun/refresh survives | After an `AppTest` rerun (simulated reload), the selected slate and menu are restored from storage. No refetch and no re-entry. |
| AT-19 | Menu entered once | Enter the 3-team price, build the CFB card, rebuild from a newer CFB slate the same day → not asked again (§5.2 step 2). Switch to NFL with the same book → one [Use] click, no typing, never silent (step 2b). |
| AT-20 | Reconfirm menu | NFL EXECUTION placement with a 45-minute-old menu → one click "Menu unchanged" creates a new price snapshot (`OPERATOR_RECONFIRMED`) and placement proceeds. No typing. |
| AT-21 | Placement prefill | The placement dialog renders no required text inputs except the optional ticket reference. |
| AT-22 | Conflict blocks confirm | Conflicting OCR sides → Confirm is disabled until resolved. The resolution appears in `corrections`. |
| AT-23 | Duplicates merge | Two identical overlapping screenshots → one game. A differing duplicate → a conflict. |
| AT-24 | Ambiguous team remembered | Resolve "Miami" → FL once. The next fetch resolves it silently from the alias table. |
| AT-25 | Malformed prices | `0`, `50`, `abc`, `1.0` rejected inline. `+170`, `170`, `2.70` accepted and equal. |
| AT-26 | Public/EXECUTION diff is display-only | Building from EXECUTION never reads REFERENCE values: mutating the REFERENCE fixture leaves the EXECUTION card unchanged. |
| AT-27 | No hypothetical leakage | No price enters a card unless it came from a snapshot, operator entry or reconfirmation with a book and time. Cards never show "hypothetical" prices as actual. |
| AT-28 | Older snapshot | Selecting yesterday's slate shows the stale banner. The card records that `slate_id`. Placement from it is refused by the existing freshness rules. |
| AT-29 | Moneylines inert | Changing `home_ml`/`away_ml` in the fixture leaves the card byte-identical (after removing provenance). |
| AT-30 | Research repos untouched | No import of `ats_model` or `moneyline_model` anywhere in the app. |

---

## 9. Reuse; do not rewrite

**[verified], in `teaser_model_v1/live/`:**
- `schemas.MarketQuote`, `MarketSnapshot`, `TeaserPriceQuote`, `TeaserPriceSnapshot`,
  `validate_spread`, `validate_total`, `normalize_team`, `TEAM_ALIASES`;
- `card.grade_week`, `WeeklyCard`;
- `paper.PregameLineInput`, `build_cfb_paper_legs`, `primary_paper_legs`,
  `build_cfb_paper_tickets`, `PAPER_BANNER`;
- `recheck.recheck_card`;
- `placement.PlacementLedger`, `PlacementRecord`, `PostKickoffPlacement`,
  `EXTERNAL_NON_MODEL`;
- `snapshot.AppendOnlyStore`, `correction_record`;
- `provenance.new_record_id`, `require_aware`;
- `research.teased_board_rows` (the "all 6-point legs" section);
- `report.*` (card rendering);
- `market.read_market_csv` (the manual CSV path).

**[app: locate]:**
- ESPN/public ingestion;
- screenshot OCR, its review grid and snapshot confirm;
- REFERENCE/EXECUTION snapshot store and comparison view;
- the existing manual quoted-side editor;
- proposal/placement/settlement pages.

**New code is limited to** the `NormalizedSlate` layer, the three adapters into it, the
converters, the menu resolver, the page layout, and the app-level placement guard.

---

## 10. Implementation order

1. **Contract + converters** (§3), pure and unit-tested. AT-12 and AT-13 are green here first.
2. **Adapters.** Wrap the existing ESPN, OCR and manual outputs into `NormalizedSlate`. Include
   the alias table and exclusion reasons.
3. **Menu resolver + Settings** (`default_teaser_book`, `STALE_WARN`).
4. **Page.** Source radio, saved-slate picker, review grid, menu, build. Persist the selection
   (AT-18).
5. **Placement guard + prefilled placement dialog + menu reconfirm** (AT-08, 09, 20, 21).
6. **Edge states** (§7).
7. **Full acceptance suite** and existing suites green. Then a Saturday dry run: build the CFB
   PAPER card from the live ESPN slate, with no placement.

---

## 11. Non-goals

- No change to Teaser v1.0 rules, parameters, geometry, ranking, ticket construction, EV or
  thresholds.
- No ATS, Moneyline, parlay or any new model.
- No automated wagering and no sportsbook API writes.
- No paid odds feed.
- No CFB live placement.
- No 4-, 5- or 6-team teasers, and no "special" teaser products.
- No redesign of the settlement/accounting logic.
- No backfilling of started games from live lines.

---

## 12. Saturday-ready definition of done

- [ ] CFB → Public → Fetch → Confirm → Build produces the CFB PAPER card in ≤ 5 clicks, with
      prices typed at most once per day.
- [ ] NFL public screening card, and NFL screenshot → EXECUTION card, both build without side
      entry.
- [ ] A REFERENCE or CFB card cannot reach the placement ledger (UI and handler).
- [ ] An EXECUTION card becomes PLACED only through the explicit dialog, and the existing
      re-check rules still apply.
- [ ] AT-01 to AT-30 pass. The existing app, live-layer, engine and settlement suites pass.
      `engine/` is unchanged.
- [ ] A dry run on the live Saturday CFB slate is completed and its card saved.

---

## 13. Adversarial review: "Can the operator still get trapped into re-entering information already in a saved snapshot?"

The first draft of this spec answered **yes** in nine places, and a second pass found a tenth.
Each is now closed in the sections above:

| # | Trap in the first draft | Fix (where) |
|---|---|---|
| T1 | Proposal page asked for the sportsbook again after a confirmed snapshot | The book is inherited everywhere; no sportsbook widget on the proposal page (§5, AT-04) |
| T2 | REFERENCE slates had no book for the teaser menu, so it would be asked per proposal | `default_teaser_book` set once in Settings (§5.2, D-1) |
| T3 | The teaser menu was re-typed for every proposal and after switching league | Saved menu per (league, book, day) prefilled; other league's menu from the same book offered as one click (§5.2 steps 2/2b, AT-19) |
| T10 | Second review: saved menus keyed by league, but the test assumed silent cross-league reuse | Resolved as step 2b: offered, never silent; test rewritten |
| T4 | Placement required a menu ≤ 30 minutes old, forcing re-typing of unchanged prices | One-click "Menu unchanged — confirm now" (§6, AT-20, D-2) |
| T5 | The placement form re-asked book, odds, legs and time | Fully prefilled from snapshot and ticket (§6, AT-21) |
| T6 | Streamlit reruns and reloads dropped the selection, forcing a refetch or re-entry | Selection and menu persisted and restored (§5.1, AT-18) |
| T7 | Fixing one bad cell meant falling back to a blank manual editor | Inline fix of only the bad cells; the manual editor always opens pre-filled from the selected slate (§7, AT-17) |
| T8 | Ambiguous CFB names re-asked on every fetch | Append-only alias table (§7, AT-24) |
| T9 | Unknown NFL week asked on every build | Derived from kickoff; if still unknown, asked once and stored on the slate (§7) |

**What legitimately remains, and is not re-entry:**
- **Placement board capture.** An NFL placement still needs a **new** capture of the current
  board, because the frozen live rules require a re-check against a newer market snapshot.
  That is new information. The uploader pre-fills from the prior snapshot and highlights only
  changed cells.
- **Missing prices.** Prices that exist nowhere in the system are asked once.

**Answer after the fixes: no.** No fact present in a confirmed snapshot, saved menu, alias
table or setting is asked for twice.

**One conditional exception: decision D-2.** Until D-2 is approved, a stale menu at NFL
placement time must be re-typed. That is a governance choice about what counts as a fresh
price observation, not a UX defect.

---

## 14. Decisions Codex needs from the operator

| ID | Decision | Default Codex should use if not told otherwise |
|---|---|---|
| D-1 | The sportsbook whose 6-point menu applies to REFERENCE (public) slates, per league | The book used for the NFL week 2 screenshots, applied to both NFL and CFB |
| D-2 | Is a one-click "menu unchanged — confirm now" attestation acceptable as a fresh teaser-price capture for the existing 30-minute placement rule? | **No**, until the operator approves it: show the reconfirm button disabled with an explanation, and fall back to typing the two prices at placement |

Every other choice above (staleness warning 2 h, price plausibility ranges, click path, widget
keys) is a UI default that Codex may use as written.
