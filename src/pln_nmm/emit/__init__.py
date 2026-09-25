"""Serialise the canonical model to CIM profile files.

One module per profile, because profiles are separate files with separate
version sequences:

    eq.py   Equipment  -- what the network is
    dl.py   DiagramLayout -- where it is drawn

Layout never belongs in EQ. plnicp coordinates inside EQ are a PLN convention
kept only for compatibility with existing Icon Plus tooling, and are generated
from the same layout DL uses so the two cannot disagree.
"""

from .dl import Diagram, DlReport, Placement, build_dl_xml, read_eq_mrids, write_dl

__all__ = [
    "Diagram",
    "DlReport",
    "Placement",
    "build_dl_xml",
    "read_eq_mrids",
    "write_dl",
]
