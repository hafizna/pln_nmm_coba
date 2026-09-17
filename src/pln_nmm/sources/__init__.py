"""Adapters that read evidence from upstream systems.

Each source owns one domain and nothing else:

    sld_engine.py  topology evidence -- which GI exist, which corridors join
                   them, how many circuits. From mantaps-topology-engine.
    workbook.py    parameters, load, scenarios. Hand-filled.
    reconcile.py   compares the two and reports disagreements.
    ed.py          asset identity. Not yet available.

Nothing here writes back to its source, and nothing here decides which source
wins. Conflicts are reported for a person to settle.
"""

from .reconcile import ReconciliationReport, reconcile
from .sld_engine import (
    CorridorRecord,
    GeneratorRecord,
    GiRecord,
    SldEvidence,
    load,
    load_db,
    load_handoff,
)
from .workbook import Workbook, read_workbook

__all__ = [
    "CorridorRecord",
    "GeneratorRecord",
    "GiRecord",
    "ReconciliationReport",
    "SldEvidence",
    "Workbook",
    "load",
    "load_db",
    "load_handoff",
    "read_workbook",
    "reconcile",
]
