"""Identity, hashing and time handling for prospective records.

Three rules hold across the whole live layer:

1. **Timestamps are timezone-aware.** A naive datetime is rejected, never assumed to be
   UTC or local. Getting this wrong silently mislabels when a line was seen, which is the
   one thing a market snapshot exists to record.
2. **Records are identified by their content.** A record's id embeds a hash of its
   canonical form, so writing the same content twice is idempotent and writing different
   content can never collide with an earlier record.
3. **Decimals are exact.** Lines and totals round-trip through strings, never through
   binary floats. Half-point fidelity is as critical prospectively as it was historically.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

#: Length of the short content hash embedded in record ids.
HASH_PREFIX_LENGTH = 12


class NaiveTimestampError(ValueError):
    """Raised when a timestamp has no timezone information."""


def utc_now() -> datetime:
    """Current time, timezone-aware, second resolution."""
    return datetime.now(timezone.utc).replace(microsecond=0)


def require_aware(value: datetime | str, *, field: str = "timestamp") -> datetime:
    """Return *value* as a timezone-aware datetime, or raise.

    Accepts a datetime or an ISO-8601 string. A naive value raises
    :class:`NaiveTimestampError` rather than being coerced: guessing a zone would silently
    move a captured_at by hours.
    """
    if isinstance(value, str):
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            value = datetime.fromisoformat(text)
        except ValueError as exc:
            raise ValueError(f"{field}: cannot parse timestamp {value!r}") from exc
    if not isinstance(value, datetime):
        raise TypeError(f"{field}: expected datetime or ISO-8601 string, got {type(value).__name__}")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise NaiveTimestampError(
            f"{field}: timestamp {value.isoformat()} has no timezone. "
            "Provide an explicit offset (e.g. '2026-09-20T13:05:00-04:00' or "
            "'2026-09-20T17:05:00Z'); it will not be assumed."
        )
    return value


def iso(value: datetime) -> str:
    """Serialise a timezone-aware datetime."""
    return require_aware(value).isoformat()


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return iso(value)
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def canonical_json(payload: dict) -> str:
    """Deterministic JSON for hashing and on-disk storage.

    Keys sorted, Decimals as exact strings, datetimes as ISO-8601 with offset. Two records
    with the same meaning always produce the same bytes.
    """
    return json.dumps(_jsonable(payload), sort_keys=True, separators=(",", ":"))


def content_hash(payload: dict) -> str:
    """SHA-256 of the canonical form."""
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def new_record_id(prefix: str, payload: dict) -> str:
    """A stable, content-derived id, e.g. ``mkt_2026w03_9f1c2ab34d55``.

    Because the id embeds the content hash, re-recording identical content yields the same
    id (so the store can no-op) and different content can never overwrite an earlier
    record.
    """
    return f"{prefix}_{content_hash(payload)[:HASH_PREFIX_LENGTH]}"
