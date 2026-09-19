"""Prospective live-operations layer for frozen Teaser Model v1.0.

This layer **operates** the frozen model week to week. It never changes it: every
geometry test, probability, ticket probability, EV and selection decision is delegated to
:mod:`teaser_model_v1.engine`, which this package only reads.

**No function in this package can place a wager.** The system records what a human
operator says they placed; it never submits anything to a sportsbook and never infers a
placement from a proposal.

Layering, deliberately one-directional::

    engine/      frozen model            <- never imports anything below
    ingest/      historical data
    analysis/    historical research
    live/        prospective operations  -> imports engine only
    cli/         operator commands       -> imports live
"""

from teaser_model_v1.live.provenance import (  # noqa: F401
    canonical_json,
    content_hash,
    new_record_id,
    require_aware,
    utc_now,
)
