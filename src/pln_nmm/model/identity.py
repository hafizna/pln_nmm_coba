"""Deterministic identity for generated CIM objects.

The same input must always yield the same mRIDs. Without that, every export
produces a fresh set of UUIDs and two runs cannot be diffed, which makes review
impossible and breaks any downstream reference.

UUID5 over a stable business key gives that for free: no state to persist, no
counter to keep, and the key itself documents what the object is.
"""

from __future__ import annotations

import uuid

# Fixed namespace. Changing it renumbers every object ever generated, so treat
# it as permanent.
NAMESPACE = uuid.UUID("6f2a1c4e-8b3d-5f7a-9c1e-2d4b6a8c0e2f")


def stable_id(*parts: str) -> str:
    """Deterministic UUID for a business key."""
    return str(uuid.uuid5(NAMESPACE, "|".join(parts)))
