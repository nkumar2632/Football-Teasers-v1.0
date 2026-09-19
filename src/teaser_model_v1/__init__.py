"""Teaser Model v1.0 — frozen operational model plus research tooling.

The operational model lives in :mod:`teaser_model_v1.engine` and is FROZEN for the
2026 season. See ``TEASER_MODEL_V1_0.md`` and ``AGENTS.md``.

Computation (``engine``) is deliberately kept free of any dependency on data
ingestion (``ingest``) or reporting (``audit``).
"""

__version__ = "1.0.0"
MODEL_VERSION = "v1.0"
