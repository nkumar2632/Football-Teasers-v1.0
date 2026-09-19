"""Run the frozen v1.0 CFB PAPER board over an operator-supplied pregame slate.

Reads a per-GAME csv (favourite's spread), enumerates BOTH SIDES of every game, and
hands them to the frozen engine via ``live/paper.py``. Nothing here re-implements a
model rule: geometry, the CFB guardrail, the bump, P_est, ranking, the top-four cut and
ticket construction all come from ``engine/``.

Outcomes are never read. No EV is produced without an actual contemporaneous teaser
price, and none is invented.
"""

from __future__ import annotations

import argparse
import csv
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from teaser_model_v1.engine.constants import CFB, TOTAL_GUARDRAIL  # noqa: E402
from teaser_model_v1.engine.geometry import passes_total_guardrail  # noqa: E402
from teaser_model_v1.live.paper import (  # noqa: E402
    ARCHIVED_PREGAME_REFERENCE,
    PAPER_BANNER,
    PregameLineInput,
    build_cfb_paper_legs,
    build_cfb_paper_tickets,
    primary_paper_legs,
    secondary_paper_legs,
)


def load(path: Path, label: str) -> list[PregameLineInput]:
    """One csv row per game -> two PregameLineInputs, one per side."""
    inputs: list[PregameLineInput] = []
    with path.open() as fh:
        for row in csv.DictReader(line for line in fh if not line.startswith("#")):
            away, home, fav = row["away"], row["home"], row["favourite"]
            fav_spread = Decimal(row["spread_fav"])
            total = Decimal(row["total"])
            dog = away if fav == home else home
            game_id = f"{away.replace(' ', '')}@{home.replace(' ', '')}"
            source = row.get("source") or "operator-supplied board"
            if row.get("window"):
                source = f"{source} [{row['window']}]"
            if row.get("note"):
                source = f"{source}; {row['note']}"
            for team, opponent, spread in (
                (fav, dog, fav_spread),
                (dog, fav, -fav_spread),
            ):
                inputs.append(
                    PregameLineInput(
                        game_id=game_id, team=team, opponent=opponent,
                        spread=spread, total=total,
                        kickoff=row["kickoff_et"], source=source, line_label=label,
                    )
                )
    return inputs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path", type=Path)
    ap.add_argument("--label", default=ARCHIVED_PREGAME_REFERENCE)
    args = ap.parse_args()

    inputs = load(args.csv_path, args.label)
    legs = build_cfb_paper_legs(inputs)
    primary = primary_paper_legs(legs)
    secondary = secondary_paper_legs(legs)

    print(PAPER_BANNER)
    print(f"\nsource file : {args.csv_path}")
    print(f"line label  : {args.label}")
    print(f"games       : {len(inputs) // 2}")
    print(f"sides built : {len(legs)}")
    print(f"CFB total guardrail: <= {TOTAL_GUARDRAIL[CFB]}\n")

    print("--- every side, and why it is in or out ---")
    for leg in sorted(legs, key=lambda x: (x.game_id, x.leg_id)):
        cap_ok = passes_total_guardrail("CFB", leg.total)
        if leg.is_primary and cap_ok:
            why = "QUALIFIES (primary geometry, inside guardrail)"
        elif leg.is_primary:
            why = f"out: primary geometry but total {leg.total} > {TOTAL_GUARDRAIL[CFB]}"
        elif not cap_ok:
            why = f"out: not primary geometry; also total {leg.total} > {TOTAL_GUARDRAIL[CFB]}"
        else:
            why = "out: not primary geometry"
        print(f"  {leg.team:<20} {str(leg.spread):>6} -> {str(leg.teased_spread):>6}"
              f"  tot {str(leg.total):>5}  {leg.geometry_class}/{leg.track}  {why}")

    print(f"\n--- PRIMARY / PAPER (qualifying) : {len(primary)} ---")
    for rank, leg in enumerate(primary, 1):
        print(f"  {rank}. {leg.team:<20} {leg.spread} -> {leg.teased_spread}"
              f"  keys={leg.key_numbers_crossed}  P_est={leg.p_est:.4f}")
    if not primary:
        print("  (none)")

    print(f"\n--- SECONDARY / PAPER (ranked separately) : {len(secondary)} ---")
    for rank, leg in enumerate(secondary, 1):
        print(f"  {rank}. {leg.team:<20} {leg.spread} -> {leg.teased_spread}"
              f"  keys={leg.key_numbers_crossed}  P_est={leg.p_est:.4f}")
    if not secondary:
        print("  (none)")

    top, tickets = build_cfb_paper_tickets(primary, profit_by_size=None)
    print(f"\ntop-four primary legs : {len(top)}")
    print(f"paper tickets         : {len(tickets)}")
    for t in tickets:
        names = " + ".join(leg.team for leg in t.legs)
        be = f"{t.fair_break_even_profit:.4f}"
        print(f"  {t.n_legs}-team: {names}")
        print(f"      P_ticket={t.p_ticket:.4f}  "
              f"EV={t.ev if t.ev is not None else 'UNAVAILABLE (no actual price)'}  "
              f"model-implied fair break-even profit per unit={be}  "
              f"placement_eligible={t.placement_eligible}")
    print("\nEV is UNAVAILABLE for every ticket unless an actual contemporaneous CFB "
          "teaser price is supplied. None was. No price was invented.")
    print("All CFB output is PAPER/RESEARCH. Placements: 0. Units staked: 0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
