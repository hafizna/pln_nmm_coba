"""
Pure-XML diagnostics for PLN CIM files.

This module intentionally runs before cimpy. Some PLN aggregate files are
template-like: they still contain `$(Isi_*)` placeholders where an engineer
or upstream generator is expected to provide a real value such as a bay name,
bus label, equipment number, or electrical parameter. cimpy correctly rejects
those placeholders in numeric CIM fields, so we surface them as actionable
data-quality findings first.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

from lxml import etree

from .adapter import ATTR_RDF_ID, TAG_CIM_MRID


PLACEHOLDER_RE = re.compile(r"\$\(Isi_[^)]+\)")


@dataclass(frozen=True)
class TemplatePlaceholder:
    """One unresolved `$(Isi_*)` value found in an XML text node or attribute."""

    token: str
    field: str
    owner_tag: str
    owner_mrid: Optional[str]
    location: str
    line: Optional[int]


@dataclass
class DiagnosticReport:
    """Summary of pre-cimpy data-quality findings."""

    placeholders: list[TemplatePlaceholder] = field(default_factory=list)

    @property
    def has_blocking_placeholders(self) -> bool:
        return bool(self.placeholders)

    def placeholder_field_counts(self) -> dict[str, int]:
        return dict(Counter(item.field for item in self.placeholders))

    def placeholder_token_counts(self) -> dict[str, int]:
        return dict(Counter(item.token for item in self.placeholders))

    def __str__(self) -> str:
        return (
            "DiagnosticReport("
            f"placeholders={len(self.placeholders)}, "
            f"blocking={self.has_blocking_placeholders}"
            ")"
        )


def diagnose_pln_eq(xml_path: str | Path) -> DiagnosticReport:
    """Scan a CIM XML file for findings that should be shown before import."""
    tree = etree.parse(str(Path(xml_path)))
    report = DiagnosticReport()

    for elem in tree.iter():
        if not isinstance(elem.tag, str):
            continue

        owner = _nearest_identified_owner(elem)
        owner_tag = _local_name(owner.tag) if owner is not None else _local_name(elem.tag)
        owner_mrid = _element_key(owner) if owner is not None else _element_key(elem)

        if elem.text:
            _append_placeholders(
                report.placeholders,
                value=elem.text,
                field=_local_name(elem.tag),
                owner_tag=owner_tag,
                owner_mrid=owner_mrid,
                location="text",
                line=elem.sourceline,
            )

        for attr_name, attr_value in elem.attrib.items():
            _append_placeholders(
                report.placeholders,
                value=attr_value,
                field=f"@{_local_name(attr_name)}",
                owner_tag=owner_tag,
                owner_mrid=owner_mrid,
                location="attribute",
                line=elem.sourceline,
            )

    return report


def _append_placeholders(
    out: list[TemplatePlaceholder],
    *,
    value: str,
    field: str,
    owner_tag: str,
    owner_mrid: Optional[str],
    location: str,
    line: Optional[int],
) -> None:
    for match in PLACEHOLDER_RE.finditer(value):
        out.append(
            TemplatePlaceholder(
                token=match.group(0),
                field=field,
                owner_tag=owner_tag,
                owner_mrid=owner_mrid,
                location=location,
                line=line,
            )
        )


def _nearest_identified_owner(elem: etree._Element) -> Optional[etree._Element]:
    current: Optional[etree._Element] = elem
    while current is not None:
        if _element_key(current) is not None:
            return current
        current = current.getparent()
    return None


def _element_key(elem: Optional[etree._Element]) -> Optional[str]:
    if elem is None:
        return None

    rdf_id = elem.get(ATTR_RDF_ID)
    if rdf_id:
        return rdf_id.lstrip("_")

    mrid_elem = elem.find(TAG_CIM_MRID)
    if mrid_elem is not None and mrid_elem.text:
        return mrid_elem.text.strip()

    return None


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def summarize_top_placeholders(
    report: DiagnosticReport,
    *,
    limit: int = 10,
) -> Iterable[tuple[str, int]]:
    """Return the most common unresolved placeholder fields."""
    counts = Counter(item.field for item in report.placeholders)
    return counts.most_common(limit)
