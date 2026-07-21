"""
PLN custom extension adapter for cimpy.

cimpy parses CGMES 2.4.15 / CIM16 cleanly but silently drops two extensions
that PLN's existing CIM toolchain (Nur Hidayat's db config v1.13) writes
into every EQ file:

  1. plnicp:DiagramProperty.x   (child element)
     plnicp:DiagramProperty.y   (child element)
     - per-equipment 2D canvas coordinates injected inline on most
       ConductingEquipment, ConnectivityNode, and BusbarSection elements.
     - namespace: http://iconpln.co.id#

  2. nhftui:info                (XML attribute on opening tag)
     - sirkit / circuit annotation, primarily on ConnectivityNode
     - namespace: https://eng.ui.ac.id/lab-simulasi/nhjarman2025#
     - default value in the sample is "$NO_SIRKIT"

This module sits on either side of cimpy:

  Import path:
    original.xml --[extract_pln_extensions]--> dict keyed by mRID
                 --[strip_pln_extensions]----> cleaned.xml
                                               cleaned.xml --> cimpy.cim_import

  Export path:
    cimpy.cim_export --> cimpy_output.xml
                         cimpy_output.xml --[reinject_pln_extensions]--> final.xml
                                                  with stored extensions

The dict is the bridge. Keys are mRIDs (UUIDs without the leading underscore
that rdf:ID conventionally carries). Values are dicts with optional 'x',
'y', and 'nhftui_info' keys.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from lxml import etree


NS_CIM = "http://iec.ch/TC57/2013/CIM-schema-cim16#"
NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
NS_PLNICP = "http://iconpln.co.id#"
NS_NHFTUI = "https://eng.ui.ac.id/lab-simulasi/nhjarman2025#"
NS_PLNNMM = "http://pln.co.id/nmm/poc#"

# Tag names with namespaces baked in (lxml fully-qualified form).
TAG_PLNICP_X = f"{{{NS_PLNICP}}}DiagramProperty.x"
TAG_PLNICP_Y = f"{{{NS_PLNICP}}}DiagramProperty.y"
ATTR_NHFTUI_INFO = f"{{{NS_NHFTUI}}}info"
ATTR_RDF_ID = f"{{{NS_RDF}}}ID"
TAG_CIM_MRID = f"{{{NS_CIM}}}IdentifiedObject.mRID"
DOCUMENT_EXTENSION_KEY = "__pln_nmm_document__"


@dataclass
class PlnExtension:
    """Per-element PLN extension data, keyed in the side-table by mRID."""

    x: Optional[float] = None
    y: Optional[float] = None
    nhftui_info: Optional[str] = None
    # Generator provenance/data-quality properties, kept as XML fragments.
    plnnmm_children: list[bytes] = field(default_factory=list)
    # Keep the original rdf:ID string (with or without underscore) so we
    # can also match by it during reinjection if mRID lookup misses.
    original_rdf_id: Optional[str] = None
    # Track whether the original rdf:ID and mRID differed (data quality flag).
    id_mrid_mismatch: bool = False

    def is_empty(self) -> bool:
        return (
            self.x is None
            and self.y is None
            and self.nhftui_info is None
            and not self.plnnmm_children
        )


@dataclass
class ExtractionReport:
    """Summary of what was extracted, for diagnostics and tests."""

    extensions: Dict[str, PlnExtension] = field(default_factory=dict)
    elements_with_x: int = 0
    elements_with_y: int = 0
    elements_with_nhftui: int = 0
    plnnmm_properties: int = 0
    elements_with_id_mrid_mismatch: int = 0

    def __str__(self) -> str:
        return (
            f"ExtractionReport(total={len(self.extensions)}, "
            f"x={self.elements_with_x}, y={self.elements_with_y}, "
            f"nhftui={self.elements_with_nhftui}, "
            f"plnnmm={self.plnnmm_properties}, "
            f"id_mrid_mismatch={self.elements_with_id_mrid_mismatch})"
        )


def _canonical_mrid(elem: etree._Element) -> tuple[Optional[str], Optional[str], bool]:
    """
    Return (mrid, original_rdf_id, mismatch_flag) for an element.

    The canonical key is the mRID as written in cim:IdentifiedObject.mRID
    if present. Otherwise we fall back to rdf:ID with any leading underscore
    stripped. cimpy uses the rdf:ID-derived form internally on export, so
    we always store a stripped-underscore version as the lookup key.
    """
    rdf_id = elem.get(ATTR_RDF_ID)
    rdf_id_stripped = rdf_id.lstrip("_") if rdf_id else None

    mrid_elem = elem.find(TAG_CIM_MRID)
    mrid_text = mrid_elem.text.strip() if (mrid_elem is not None and mrid_elem.text) else None

    # Prefer the rdf:ID-stripped form because that is what cimpy emits
    # back as rdf:ID="_<key>" on export. If mRID disagrees, we still use
    # rdf:ID as the key but flag the mismatch for diagnostics.
    if rdf_id_stripped is not None:
        mismatch = mrid_text is not None and mrid_text != rdf_id_stripped
        return rdf_id_stripped, rdf_id, mismatch

    if mrid_text is not None:
        return mrid_text, None, False

    return None, None, False


def extract_pln_extensions(xml_path: str | Path) -> ExtractionReport:
    """
    Parse the source EQ XML and lift every PLN custom extension into a
    side-table keyed by mRID.

    The source file is not modified.
    """
    xml_path = Path(xml_path)
    tree = etree.parse(str(xml_path))
    root = tree.getroot()

    report = ExtractionReport()

    for elem in root.iter():
        if not isinstance(elem.tag, str):
            continue  # skip comments and processing instructions

        mrid, original_rdf_id, mismatch = _canonical_mrid(elem)
        if mrid is None:
            document_fragments = [
                etree.tostring(child, with_tail=False)
                for child in elem
                if isinstance(child.tag, str)
                and child.tag.startswith(f"{{{NS_PLNNMM}}}")
            ]
            if document_fragments:
                report.extensions[DOCUMENT_EXTENSION_KEY] = PlnExtension(
                    plnnmm_children=document_fragments
                )
                report.plnnmm_properties += len(document_fragments)
            continue

        ext = PlnExtension(original_rdf_id=original_rdf_id, id_mrid_mismatch=mismatch)

        nhftui_value = elem.get(ATTR_NHFTUI_INFO)
        if nhftui_value is not None:
            ext.nhftui_info = nhftui_value
            report.elements_with_nhftui += 1

        x_elem = elem.find(TAG_PLNICP_X)
        if x_elem is not None and x_elem.text:
            try:
                ext.x = float(x_elem.text.strip())
                report.elements_with_x += 1
            except ValueError:
                pass

        y_elem = elem.find(TAG_PLNICP_Y)
        if y_elem is not None and y_elem.text:
            try:
                ext.y = float(y_elem.text.strip())
                report.elements_with_y += 1
            except ValueError:
                pass

        for child in elem:
            if isinstance(child.tag, str) and child.tag.startswith(f"{{{NS_PLNNMM}}}"):
                ext.plnnmm_children.append(etree.tostring(child, with_tail=False))
                report.plnnmm_properties += 1

        if mismatch:
            report.elements_with_id_mrid_mismatch += 1

        if not ext.is_empty():
            report.extensions[mrid] = ext

    return report


def strip_pln_extensions(xml_path: str | Path, output_path: str | Path) -> None:
    """
    Read the source XML, remove all plnicp:* child elements and nhftui:info
    attributes, write a cimpy-compatible cleaned XML.

    cimpy can technically parse the file with the extensions in place
    (it just ignores them), but stripping reduces parser noise and makes
    the round-trip behavior more deterministic.
    """
    xml_path = Path(xml_path)
    output_path = Path(output_path)

    tree = etree.parse(str(xml_path))
    root = tree.getroot()

    for elem in root.iter():
        if not isinstance(elem.tag, str):
            continue

        # Remove nhftui:info attribute if present.
        if ATTR_NHFTUI_INFO in elem.attrib:
            del elem.attrib[ATTR_NHFTUI_INFO]

        # Remove custom children before handing the document to cimpy.
        for child in list(elem):
            if isinstance(child.tag, str) and (
                child.tag.startswith(f"{{{NS_PLNICP}}}")
                or child.tag.startswith(f"{{{NS_PLNNMM}}}")
            ):
                elem.remove(child)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(
        str(output_path),
        xml_declaration=True,
        encoding="UTF-8",
        pretty_print=False,
    )


def reinject_pln_extensions(
    cimpy_output_path: str | Path,
    final_output_path: str | Path,
    extensions: Dict[str, PlnExtension],
) -> dict:
    """
    Take cimpy's exported XML and re-attach the PLN extensions to each
    matching element. Returns a small statistics dict.

    Matching policy:
      - Look up by rdf:ID stripped of leading underscore (canonical key).
      - If not found, fall back to mRID child element text.
      - If still not found, the element passes through unchanged.

    The output namespace declaration on the root element is augmented to
    include plnicp and nhftui if they are not already declared. cimpy
    happens to declare both namespaces on its root because the import
    parser preserved them, but we double-check.
    """
    cimpy_output_path = Path(cimpy_output_path)
    final_output_path = Path(final_output_path)

    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(str(cimpy_output_path), parser)
    root = tree.getroot()

    # Ensure plnicp and nhftui namespaces are declared on the root.
    # If lxml already has them in nsmap, this is a no-op. If not, we
    # need to rewrite the root with augmented nsmap, which is awkward
    # because nsmap is read-only in lxml. We solve it by registering
    # the prefix on first use; lxml will hoist it to the root.
    existing_ns = set(root.nsmap.values())
    needs_root_rewrite = (
        NS_PLNICP not in existing_ns or NS_NHFTUI not in existing_ns
    )
    if needs_root_rewrite:
        root = _rewrite_root_with_namespaces(root, [
            ("plnicp", NS_PLNICP),
            ("nhftui", NS_NHFTUI),
        ])
        tree = etree.ElementTree(root)

    stats = {
        "matched": 0,
        "missed": 0,
        "x_reinjected": 0,
        "y_reinjected": 0,
        "nhftui_reinjected": 0,
        "plnnmm_reinjected": 0,
    }

    document_ext = extensions.get(DOCUMENT_EXTENSION_KEY)
    if document_ext is not None:
        # POC-wide scope/disclaimer properties live on md:FullModel, which
        # uses rdf:about rather than rdf:ID and therefore has no object key.
        document_owner = next(
            (
                elem
                for elem in root
                if isinstance(elem.tag, str) and elem.tag.endswith("}FullModel")
            ),
            root,
        )
        for fragment in document_ext.plnnmm_children:
            document_owner.append(etree.fromstring(fragment))
            stats["plnnmm_reinjected"] += 1

    for elem in root.iter():
        if not isinstance(elem.tag, str):
            continue

        mrid, _, _ = _canonical_mrid(elem)
        if mrid is None:
            continue

        ext = extensions.get(mrid)
        if ext is None:
            stats["missed"] += 1
            continue

        stats["matched"] += 1

        if ext.nhftui_info is not None:
            elem.set(ATTR_NHFTUI_INFO, ext.nhftui_info)
            stats["nhftui_reinjected"] += 1

        if ext.x is not None:
            x_child = etree.SubElement(elem, TAG_PLNICP_X)
            x_child.text = _format_coord(ext.x)
            stats["x_reinjected"] += 1

        if ext.y is not None:
            y_child = etree.SubElement(elem, TAG_PLNICP_Y)
            y_child.text = _format_coord(ext.y)
            stats["y_reinjected"] += 1

        for fragment in ext.plnnmm_children:
            elem.append(etree.fromstring(fragment))
            stats["plnnmm_reinjected"] += 1

    final_output_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(
        str(final_output_path),
        xml_declaration=True,
        encoding="UTF-8",
        pretty_print=False,
    )

    return stats


def _format_coord(value: float) -> str:
    """
    Format a coordinate value in a way that round-trips through float()
    without precision loss. The original PLN files use Python's default
    repr-style float formatting (e.g. 558.0909726137421), so we mimic it.
    """
    return repr(value)


def _rewrite_root_with_namespaces(
    root: etree._Element, prefixes: list[tuple[str, str]]
) -> etree._Element:
    """
    Return a copy of the root element with additional namespace prefixes
    declared on the root. lxml does not allow mutating nsmap in place, so
    we have to rebuild the tree.
    """
    new_nsmap = dict(root.nsmap)
    for prefix, uri in prefixes:
        if uri not in new_nsmap.values():
            new_nsmap[prefix] = uri

    new_root = etree.Element(root.tag, attrib=dict(root.attrib), nsmap=new_nsmap)
    # Move all children from old root to new root.
    for child in root:
        new_root.append(copy.deepcopy(child))
    if root.text:
        new_root.text = root.text
    if root.tail:
        new_root.tail = root.tail
    return new_root
