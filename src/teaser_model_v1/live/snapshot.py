"""Append-only storage for prospective records.

**Nothing in this module ever overwrites or edits a stored record.** A record's id embeds
a hash of its content, so:

* storing identical content twice is a no-op that returns the existing record;
* storing different content produces a different id and a new file;
* a mismatch between an existing file and new content under the same id is impossible, and
  if one is ever detected it raises rather than being reconciled.

Corrections are handled by writing a :class:`CorrectionRecord` that *points at* the
superseded record. The original stays exactly as it was written.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from teaser_model_v1.live.provenance import canonical_json, iso, require_aware, utc_now


class ImmutableRecordError(RuntimeError):
    """Raised on any attempt to change a record that is already stored."""


@dataclass(frozen=True)
class StoreResult:
    """What happened when a record was offered to the store."""

    record_id: str
    path: Path
    created: bool

    @property
    def already_present(self) -> bool:
        return not self.created


class AppendOnlyStore:
    """A directory of immutable JSON records, plus an append-only index."""

    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.root / "index.jsonl"

    def path_for(self, record_id: str) -> Path:
        return self.root / f"{record_id}.json"

    def exists(self, record_id: str) -> bool:
        return self.path_for(record_id).exists()

    def put(self, record_id: str, payload: dict, *, kind: str) -> StoreResult:
        """Store *payload* under *record_id*, or confirm it is already stored unchanged."""
        path = self.path_for(record_id)
        body = canonical_json(payload)

        if path.exists():
            existing = path.read_text()
            if existing != body:
                raise ImmutableRecordError(
                    f"{record_id} already exists with different content. Records are "
                    "append-only and are never rewritten; write a correction record "
                    "instead."
                )
            return StoreResult(record_id, path, created=False)

        path.write_text(body)
        with self.index_path.open("a") as handle:
            handle.write(
                json.dumps(
                    {
                        "record_id": record_id,
                        "kind": kind,
                        "stored_at": iso(utc_now()),
                        "path": path.name,
                    },
                    sort_keys=True,
                )
                + "\n"
            )
        return StoreResult(record_id, path, created=True)

    def get(self, record_id: str) -> dict:
        path = self.path_for(record_id)
        if not path.exists():
            raise KeyError(f"no record {record_id} in {self.root}")
        return json.loads(path.read_text())

    def list_records(self, kind: str | None = None) -> list:
        if not self.index_path.exists():
            return []
        rows = [json.loads(line) for line in self.index_path.read_text().splitlines() if line]
        if kind is not None:
            rows = [row for row in rows if row["kind"] == kind]
        return rows

    def latest(self, kind: str | None = None) -> dict | None:
        rows = self.list_records(kind)
        return self.get(rows[-1]["record_id"]) if rows else None


class AppendOnlyLedger:
    """A JSON-lines ledger. Entries are appended; none is ever modified or removed."""

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, entry: dict) -> dict:
        with self.path.open("a") as handle:
            handle.write(canonical_json(entry) + "\n")
        return entry

    def entries(self) -> list:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text().splitlines() if line]

    def find(self, **match) -> list:
        return [
            entry
            for entry in self.entries()
            if all(entry.get(key) == value for key, value in match.items())
        ]


def correction_record(
    *,
    supersedes_id: str,
    reason: str,
    corrected_by: str,
    replacement_id: str = "",
    notes: str = "",
) -> dict:
    """A record that supersedes another **without touching it**.

    Recovery from a wrong line, a wrong price or a mistaken placement entry always takes
    this form: the original stays on disk exactly as written, and this record says what was
    wrong and what replaces it. History is never rewritten.
    """
    if not supersedes_id:
        raise ValueError("a correction must name the record it supersedes")
    if not reason.strip():
        raise ValueError("a correction must state a reason")
    return {
        "kind": "correction",
        "supersedes_id": supersedes_id,
        "replacement_id": replacement_id,
        "reason": reason,
        "corrected_by": corrected_by,
        "corrected_at": iso(utc_now()),
        "notes": notes,
    }
