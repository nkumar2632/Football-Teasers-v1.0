"""Uncertainty-band screen for the 2026-09-19 CFB paper slate.

This is a REPORTING/AUDIT instrument, not a model component. It answers one
question about recovered lines whose provenance is untrustworthy:

    Given that the recovered spread and total may each be wrong by up to
    +/- BAND points, is the v1.0 eligibility answer for this game the same
    for EVERY value in the band?

If yes, the game can be excluded (or admitted) despite the imprecision.
If no, the game's answer depends on numbers this environment could not
verify, and it is DATA_INSUFFICIENT.

It does not estimate, average, or repair any line. It never writes a board.
Frozen v1.0 constants are imported, never restated.
"""

from __future__ import annotations

import csv
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from teaser_model_v1.engine.constants import (  # noqa: E402
    CFB,
    PRIMARY_SPREADS,
    TOTAL_GUARDRAIL,
)

#: Largest disagreement OBSERVED between repeat queries of the only reachable
#: channel, in points. This is a measured property of the recovery channel for
#: this run, not a model parameter.
BAND = Decimal("1.0")

CAP = TOTAL_GUARDRAIL[CFB]
PRIMARY_ABS = sorted({abs(s) for s in PRIMARY_SPREADS})

CSV_PATH = Path(__file__).resolve().parents[1] / "data/live/input/cfb_2026-09-19_recovered_lines.csv"
OUT_PATH = Path(__file__).resolve().parents[1] / "reports/live/2026_cfb_2026-09-19_band_screen.csv"


def main() -> int:
    rows = []
    with CSV_PATH.open() as fh:
        reader = csv.DictReader(line for line in fh if not line.startswith("#"))
        for row in reader:
            fav = abs(Decimal(row["spread_fav"]))
            total = Decimal(row["total"])

            # Could the true spread be a primary-geometry spread, anywhere in the band?
            geom_possible = any(abs(fav - p) <= BAND for p in PRIMARY_ABS)
            # Could the true total clear the frozen CFB guardrail, anywhere in the band?
            cap_possible = (total - BAND) <= CAP
            # Is the true spread certainly a primary spread (band entirely on one value)?
            geom_certain = any(fav == p for p in PRIMARY_ABS) and not any(
                abs(fav - p) <= BAND for p in PRIMARY_ABS if p != fav
            )
            cap_certain = (total + BAND) <= CAP

            if not (geom_possible and cap_possible):
                verdict = "ROBUSTLY_EXCLUDED"
            elif geom_certain and cap_certain:
                verdict = "ROBUSTLY_ADMITTED"
            else:
                verdict = "UNDETERMINED"

            reasons = []
            if not geom_possible:
                reasons.append("no primary geometry within band")
            if not cap_possible:
                reasons.append(f"total exceeds {CAP} cap by more than band")
            if verdict == "UNDETERMINED":
                if geom_possible and not geom_certain:
                    reasons.append("geometry depends on exact half-point")
                if cap_possible and not cap_certain:
                    reasons.append("cap depends on exact total")

            rows.append((row, fav, total, verdict, "; ".join(reasons)))

    width = max(len(f"{r['away']} @ {r['home']}") for r, *_ in rows)
    print(f"BAND = +/-{BAND} pt (observed source disagreement)   CFB total cap = {CAP}")
    print(f"Primary geometry |spread| in {[str(p) for p in PRIMARY_ABS]}\n")
    for row, fav, total, verdict, reasons in rows:
        game = f"{row['away']} @ {row['home']}"
        print(f"{game:<{width}}  {row['favourite']:>18} -{fav:<5} tot {total:<5}  {verdict:<18} {reasons}")

    print()
    for verdict in ("ROBUSTLY_ADMITTED", "UNDETERMINED", "ROBUSTLY_EXCLUDED"):
        n = sum(1 for *_, v, _ in rows if v == verdict)
        print(f"{verdict:<18} {n}")
    print(f"{'TOTAL':<18} {len(rows)}")

    with OUT_PATH.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["away", "home", "favourite", "spread_fav", "total", "kickoff_et",
             "source_note", "band_pts", "verdict", "reason"]
        )
        for row, fav, total, verdict, reasons in rows:
            writer.writerow(
                [row["away"], row["home"], row["favourite"], row["spread_fav"],
                 row["total"], row["kickoff_et"], row["source_note"], str(BAND),
                 verdict, reasons]
            )
    print(f"\nwrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
