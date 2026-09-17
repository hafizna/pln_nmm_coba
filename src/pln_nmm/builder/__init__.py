"""Build CIM EQ from the NMM model-input workbook.

    workbook.py   - read the .xlsx into plain dicts
    templates.py  - expand bay templates into switches, terminals, nodes
    emit.py       - serialise CIM16 / CGMES 2.4.15 EQ

The workbook must pass scripts/validate_workbook.py first; this package assumes
valid input and does not re-check domain rules.
"""

from .check import TopologyReport, check_topology
from .emit import BuildReport, build_cim
from .templates import BayExpansion, expand_all, expand_bay, stable_id
from .workbook import Workbook, read_workbook

__all__ = [
    "BuildReport",
    "TopologyReport",
    "check_topology",
    "BayExpansion",
    "Workbook",
    "build_cim",
    "expand_all",
    "expand_bay",
    "read_workbook",
    "stable_id",
]
