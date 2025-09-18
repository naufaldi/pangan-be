from __future__ import annotations

import hashlib
from datetime import date
from decimal import Decimal


def _normalize(value: object) -> str:
    if isinstance(value, Decimal):
        # Ensure stable decimal representation
        return format(value, 'f').rstrip('0').rstrip('.') if '.' in format(value, 'f') else format(value, 'f')
    if isinstance(value, date):
        return value.isoformat()
    if value is None:
        return ""  # treat None as empty
    return str(value)


def compute_price_checksum(
    *,
    price: Decimal,
    unit: str,
    level_harga_id: int,
    period_start: date,
    period_end: date,
    commodity_id: str,
) -> str:
    """Compute a stable checksum for a price fact.

    Hash covers key value fields to detect content updates while preserving
    idempotency via the unique window key.
    """
    parts = [
        _normalize(price),
        _normalize(unit),
        _normalize(level_harga_id),
        _normalize(period_start),
        _normalize(period_end),
        _normalize(commodity_id),
    ]
    h = hashlib.sha256()
    h.update("|".join(parts).encode("utf-8"))
    return h.hexdigest()

