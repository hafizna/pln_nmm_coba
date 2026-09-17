"""The canonical model that sits between sources and emitters.

Sources fill it; emitters read it. Neither knows about the other.
"""

from .identity import NAMESPACE, stable_id

__all__ = ["NAMESPACE", "stable_id"]
