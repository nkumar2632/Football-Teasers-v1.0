"""Provenance vocabulary and the manifest written beside every raw snapshot.

Specification §12: do not assume a field called ``closing_line`` is truly the last market
price before kickoff. Use ``true_timestamped_close`` only when the source documentation
supports it.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

#: A line archived by a third party with no documented capture timestamp. The default,
#: and the honest label for nflverse/nfldata ``spread_line`` and ``total_line``.
ARCHIVED_REFERENCE_LINE = "archived_reference_line"

#: A line the source documents as the last market price before kickoff, with a timestamp.
#: Do not use this label unless the source documentation proves it.
TRUE_TIMESTAMPED_CLOSE = "true_timestamped_close"

#: A line captured by us at a recorded moment during the week.
OBSERVED_TIMESTAMPED_LINE = "observed_timestamped_line"

PROVENANCE_TERMS = (
    ARCHIVED_REFERENCE_LINE,
    TRUE_TIMESTAMPED_CLOSE,
    OBSERVED_TIMESTAMPED_LINE,
)


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass
class SourceManifest:
    """Everything needed to say where a raw file came from and what it is allowed to claim."""

    dataset: str
    source_name: str
    source_url: str
    source_commit: str | None
    retrieved_at_utc: str
    local_path: str
    sha256: str
    rows: int
    line_provenance: str
    line_provenance_justification: str
    documented_fields: dict = field(default_factory=dict)
    caveats: list = field(default_factory=list)

    def write(self, path: str | Path) -> Path:
        path = Path(path)
        path.write_text(json.dumps(asdict(self), indent=2, sort_keys=True) + "\n")
        return path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
