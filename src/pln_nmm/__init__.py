"""
pln_nmm: PLN Network Model Management - CIM round-trip toolkit.

This package wraps the SOGNO `cimpy` library with thin pre- and
post-processors so that PLN's CIM16 / CGMES 2.4.15 EQ files survive a
full round-trip without losing the two custom namespaces that PLN's
existing toolchain (Nur Hidayat's db config) embeds inline:

    plnicp:DiagramProperty.x / .y    (canvas coordinates)
    nhftui:info                       (sirkit annotation)

cimpy itself is unmodified. We do not fork it. The PLN-specific behavior
lives entirely in this package's adapter, importer, and exporter modules.
"""

from .adapter import (
    PlnExtension,
    ExtractionReport,
    extract_pln_extensions,
    strip_pln_extensions,
    reinject_pln_extensions,
)
from .importer import ImportResult, import_pln_eq
from .exporter import export_pln_eq
from .diagnostics import DiagnosticReport, TemplatePlaceholder, diagnose_pln_eq
from .topology import (
    Bay,
    BayItem,
    SubstationGroup,
    TopologyDiagnostics,
    TopologyModel,
    VoltageLevelGroup,
    compute_diagnostics,
    derive_topology,
)

__all__ = [
    "PlnExtension",
    "ExtractionReport",
    "ImportResult",
    "DiagnosticReport",
    "TemplatePlaceholder",
    "Bay",
    "BayItem",
    "SubstationGroup",
    "TopologyDiagnostics",
    "TopologyModel",
    "VoltageLevelGroup",
    "extract_pln_extensions",
    "strip_pln_extensions",
    "reinject_pln_extensions",
    "diagnose_pln_eq",
    "import_pln_eq",
    "export_pln_eq",
    "derive_topology",
    "compute_diagnostics",
]

__version__ = "0.1.0"
