# LIVE_OPERATIONS.md — the Sunday checklist

Frozen Teaser Model v1.0. **This system never places a wager.** It proposes, records what
you tell it you placed, and keeps the audit trail.

Full design: [`reports/phase4_operations_design.md`](reports/phase4_operations_design.md).

---

## Once per week

### 1. Capture the board (any time before you want a card)

```bash
python src/teaser_model_v1/cli/live.py market-template --season 2026 --week 3
```

Fill `data/live/input/nfl_2026_week_03_market.csv`. One row **per side** you want
considered. Rules that will reject the file rather than guess:

- `spread` and `total` must be exact multiples of **0.5**. Never average two books.
- `kickoff` and `captured_at` need an **explicit UTC offset** (`2026-09-20T13:00:00-04:00`).
- One sportsbook per snapshot is preferred; mixing books labels the snapshot `MIXED`.

```bash
python src/teaser_model_v1/cli/live.py ingest-market --file <that file>
```

Note the `snapshot id`. Re-ingesting the same file is a harmless no-op.

### 2. Capture the ACTUAL teaser price

```bash
python src/teaser_model_v1/cli/live.py price-template --season 2026 --week 3
```

Record only prices **you have actually seen** on the book's 6-point teaser menu.

```bash
python src/teaser_model_v1/cli/live.py ingest-prices --file <that file> --season 2026 --week 3
```

> A size you leave out has **no price**. Its tickets show a probability but no EV, and
> **cannot be placed by the model.** That is correct behaviour, not a bug.

### 3. Grade the week

```bash
python src/teaser_model_v1/cli/live.py grade-week --season 2026 --week 3 \
    --market <market id> --prices <price id>
```

Writes the card, the weekly report (`reports/live/`), and the season-ledger row — **even
if zero legs qualify.**

Read `reports/live/nfl_2026_week_03.md`. Possible outcomes:

- **NO CONSTRUCTIBLE LIVE PRIMARY TICKET** — fewer than two qualifying legs. Done for the
  week; the zero is already recorded.
- A **PROPOSED LIVE CARD** — continue.

---

## Immediately before you place anything

### 4. Re-capture the board and the price, then re-check

Repeat steps 1 and 2 with **fresh** files and current timestamps, then:

```bash
python src/teaser_model_v1/cli/live.py recheck --card <card id> \
    --market <NEW market id> --prices <NEW price id>
```

- **VALIDATED** — the ticket is still good at the current board and price.
- **DISCARD — REBUILD REQUIRED** — the ticket is dead. It is **not** substituted and **not**
  downgraded from 3-team to 2-team. A rebuilt card is written; start from it.

Re-checking against the snapshot the card was graded from is refused: it would prove
nothing.

### 5. Place it yourself, at the book

Nothing in this repository talks to a sportsbook.

### 6. Record what you actually placed

```bash
python src/teaser_model_v1/cli/live.py record-placement \
    --card <card id> --ticket "<ticket key>" --recheck <recheck id> \
    --book BookName --odds -120 \
    --placed-at 2026-09-20T12:45:00-04:00 --by yourname
```

Pass `--recheck`: a ticket the re-check discarded is refused. The 2-unit per-leg cap is
enforced here too. A wager you made outside the model goes in with `--external` and is
excluded from every v1.0 performance number.

**PROPOSED is never PLACED.** If you do not run this command, nothing was bet.

---

## After the games

### 7. Settle

```bash
python src/teaser_model_v1/cli/live.py settle --placement <placement id> \
    --leg "<leg id>:MIA:8.5:-3" --leg "<leg id>:PHI:-1.5:3" \
    --book-settlement WIN --settled-at 2026-09-20T23:30:00-04:00 --by yourname
```

`--leg` is `LEG_ID:TEAM:TEASED_SPREAD:FINAL_MARGIN`, margin signed from that team's view.

The model's grade and the book's settlement are stored **separately**. If the book VOIDs or
CANCELS something the model graded a win, record `--book-settlement VOID` and the book's own
P/L via `--profit-loss`. No generic rule reconciles them.

### 8. Check the season

```bash
python src/teaser_model_v1/cli/live.py season-status --season 2026
```

---

## Recovery

**Records are append-only. Never edit a file in `data/live/`.** Every fix is a new record
plus a correction that points at the old one.

| Problem | What to do |
|---|---|
| **Wrong line entered** | Fix the CSV, re-ingest (new snapshot id), re-grade against it, then `correct --supersedes <old market id> --reason "..." --replacement <new id>`. The bad snapshot stays on disk. |
| **Duplicate snapshot** | Nothing to do. Identical content is a no-op; the store says `already stored`. |
| **Wrong teaser price** | Same as a wrong line, against the price snapshot. Any card graded from it must be re-graded — EV is only as good as the price. |
| **Stale snapshot** | Do not place. Capture a current board and re-check. The report marks an un-rechecked card as stale. |
| **Accidental placement record** | `correct --supersedes <placement id> --reason "recorded in error; no wager was made" --by you`. The row stays; season figures should be read with the correction applied. |
| **Edited a stored file by hand** | Rehydration recomputes the content hash and will refuse it. Restore from git. |

```bash
python src/teaser_model_v1/cli/live.py correct \
    --supersedes <record id> --reason "what was wrong" --by yourname [--replacement <new id>]
```

---

## Language that matters

- `P_est` is a **model-estimated hit probability** — never an objective or true probability.
- A line you captured is an **archived/observed** line. Call it a *close* only if the source
  documents it as the last market price before kickoff. Nothing here does.
- **Void** describes a sportsbook settling a placed wager. A pre-placement ticket that fails
  the re-check is **discarded**.
- **"Best available" never means positive EV.**
