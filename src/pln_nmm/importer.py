"""
Importer: wrap cimpy.cim_import with the PLN extension extraction step.

Public API:
    import_pln_eq(xml_path) -> ImportResult

Where ImportResult bundles together the cimpy result, the extracted PLN
extensions, and a small diagnostics report. The cimpy result itself is
the same dict you would get from cimpy.cim_import directly, so any code
expecting cimpy objects keeps working.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import cimpy

from .adapter import ExtractionReport, extract_pln_extensions, strip_pln_extensions
from .diagnostics import DiagnosticReport, diagnose_pln_eq

CGMES_VERSION = "cgmes_v2_4_15"


@dataclass
class ImportResult:
    cimpy_result: Dict[str, Any]
    extensions_report: ExtractionReport
    diagnostics_report: DiagnosticReport
    source_path: Path

    @property
    def topology(self) -> Dict[str, Any]:
        return self.cimpy_result["topology"]

    @property
    def meta_info(self) -> Dict[str, Any]:
        return self.cimpy_result.get("meta_info", {})

    def class_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for obj in self.topology.values():
            cls = type(obj).__name__
            counts[cls] = counts.get(cls, 0) + 1
        return counts


def import_pln_eq(xml_path: str | Path) -> ImportResult:
    """
    Two-step import: pull PLN custom extensions to a side-table, then hand
    the cleaned XML to cimpy. The temporary cleaned file is created in
    tempfile.gettempdir() and removed after import.
    """
    xml_path = Path(xml_path)
    if not xml_path.exists():
        raise FileNotFoundError(f"Source CIM file not found: {xml_path}")

    if b'pln-nmm.line-review-xml.v1' in xml_path.read_bytes():
        raise ValueError('NMM line-review XML requires loads_line_xml or /line-review; '
                         'cimpy would discard primary-device extensions.')

    extraction = extract_pln_extensions(xml_path)
    diagnostics = diagnose_pln_eq(xml_path)

    with tempfile.NamedTemporaryFile(
        suffix="_cleaned_EQ.xml", delete=False, mode="w"
    ) as tmp:
        cleaned_path = Path(tmp.name)

    try:
        strip_pln_extensions(xml_path, cleaned_path)
        cimpy_result = cimpy.cim_import([str(cleaned_path)], CGMES_VERSION)
    finally:
        # On Windows, cimpy can leave a file handle open if it raised
        # mid-parse, blocking unlink. Swallow that — the OS reclaims the
        # tempfile on reboot, and surfacing PermissionError here would mask
        # the real cimpy error.
        try:
            cleaned_path.unlink(missing_ok=True)
        except PermissionError:
            pass

    return ImportResult(
        cimpy_result=cimpy_result,
        extensions_report=extraction,
        diagnostics_report=diagnostics,
        source_path=xml_path,
    )
