"""Data ingestion. Deliberately separate from :mod:`teaser_model_v1.engine`.

Nothing in here may change a model rule. Ingestion's only jobs are: fetch, preserve the
original source fields, record provenance honestly, and shape rows into legs.
"""
