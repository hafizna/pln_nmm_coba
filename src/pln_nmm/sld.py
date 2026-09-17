"""
Tolerant XML-based SLD extraction.

This is intentionally lighter than topology processing. It reads enough CIM XML
to let the web MVP show a single-line diagram even when semantic cimpy import is
blocked by unresolved template tokens.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from lxml import etree

from .adapter import ATTR_RDF_ID, NS_CIM, NS_RDF, extract_pln_extensions


ATTR_RDF_RESOURCE = f"{{{NS_RDF}}}resource"

SLD_CLASSES = {
    "ACLineSegment",
    "Breaker",
    "BusbarSection",
    "ConformLoad",
    "Disconnector",
    "EquivalentInjection",
    "GroundDisconnector",
    "LoadBreakSwitch",
    "PowerTransformer",
    "SynchronousMachine",
}

CLASS_LABELS = {
    "ACLineSegment": "Line",
    "Breaker": "Breaker",
    "BusbarSection": "Busbar",
    "ConformLoad": "Load",
    "Disconnector": "Switch",
    "EquivalentInjection": "Equivalent injection",
    "GroundDisconnector": "Ground switch",
    "LoadBreakSwitch": "Load break switch",
    "PowerTransformer": "Transformer",
    "SynchronousMachine": "Generator",
}


@dataclass(frozen=True)
class SldNode:
    id: str
    cim_class: str
    label: str
    x: float
    y: float
    source: str
    has_coordinates: bool
    visible: bool = True


@dataclass(frozen=True)
class SldEdge:
    id: str
    source: str
    target: str
    label: str = ""


@dataclass
class SldModel:
    nodes: list[SldNode] = field(default_factory=list)
    edges: list[SldEdge] = field(default_factory=list)
    equipment_count: int = 0
    terminal_count: int = 0
    connectivity_node_count: int = 0


def extract_sld_model(xml_path: str | Path) -> SldModel:
    """Extract a diagram-oriented model directly from CIM XML."""
    xml_path = Path(xml_path)
    tree = etree.parse(str(xml_path))
    root = tree.getroot()
    extensions = extract_pln_extensions(xml_path).extensions

    elements_by_id: dict[str, etree._Element] = {}
    terminals: list[etree._Element] = []
    connectivity_ids: set[str] = set()

    for elem in root.iter():
        if not isinstance(elem.tag, str):
            continue

        elem_id = _element_id(elem)
        local = _local_name(elem.tag)
        if elem_id:
            elements_by_id[elem_id] = elem
            if local == "Terminal":
                terminals.append(elem)
            elif local == "ConnectivityNode":
                connectivity_ids.add(elem_id)

    node_ids = {
        elem_id
        for elem_id, elem in elements_by_id.items()
        if _local_name(elem.tag) in SLD_CLASSES
    }

    model = SldModel(
        equipment_count=len(node_ids),
        terminal_count=len(terminals),
        connectivity_node_count=len(connectivity_ids),
    )

    placed = 0
    for elem_id in sorted(node_ids, key=lambda item: (_local_name(elements_by_id[item].tag), item)):
        elem = elements_by_id[elem_id]
        cim_class = _local_name(elem.tag)
        ext = extensions.get(elem_id)
        has_coords = ext is not None and ext.x is not None and ext.y is not None
        if has_coords:
            x = float(ext.x)
            y = float(ext.y)
            source = "plnicp"
        else:
            x, y = _auto_position(placed)
            source = "auto"
        placed += 1

        model.nodes.append(
            SldNode(
                id=elem_id,
                cim_class=cim_class,
                label=_display_label(elem, cim_class, elem_id),
                x=x,
                y=y,
                source=source,
                has_coordinates=has_coords,
            )
        )

    cn_to_equipment: dict[str, set[str]] = {}

    for terminal in terminals:
        equipment_ref = _child_resource(terminal, "Terminal.ConductingEquipment")
        cn_ref = _child_resource(terminal, "Terminal.ConnectivityNode")
        if equipment_ref in node_ids and cn_ref:
            cn_to_equipment.setdefault(cn_ref, set()).add(equipment_ref)

    for cn_id, equipment_ids in sorted(cn_to_equipment.items()):
        if not equipment_ids:
            continue

        anchor_id = f"cn:{cn_id}"
        anchor_x, anchor_y = _connectivity_anchor_position(
            [node for node in model.nodes if node.id in equipment_ids]
        )
        model.nodes.append(
            SldNode(
                id=anchor_id,
                cim_class="ConnectivityNode",
                label=f"CN {cn_id[:8]}",
                x=anchor_x,
                y=anchor_y,
                source="derived",
                has_coordinates=False,
                visible=False,
            )
        )

        for equipment_id in sorted(equipment_ids):
            model.edges.append(
                SldEdge(
                    id=f"e:{cn_id}:{equipment_id}",
                    source=anchor_id,
                    target=equipment_id,
                )
            )

    return model


def _element_id(elem: etree._Element) -> Optional[str]:
    rdf_id = elem.get(ATTR_RDF_ID)
    if rdf_id:
        return rdf_id.lstrip("_")
    return None


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _display_label(elem: etree._Element, cim_class: str, elem_id: str) -> str:
    name_elem = elem.find(f"{{{NS_CIM}}}IdentifiedObject.name")
    if name_elem is not None and name_elem.text and name_elem.text.strip():
        return name_elem.text.strip()

    prefix = CLASS_LABELS.get(cim_class, cim_class)
    return f"{prefix} {elem_id[:8]}"


def _child_resource(elem: etree._Element, child_name: str) -> Optional[str]:
    child = elem.find(f"{{{NS_CIM}}}{child_name}")
    if child is None:
        return None

    ref = child.get(ATTR_RDF_RESOURCE)
    if not ref:
        return None

    return ref.lstrip("#_")


def _auto_position(index: int) -> tuple[float, float]:
    columns = 8
    col = index % columns
    row = math.floor(index / columns)
    return 120.0 + col * 190.0, 100.0 + row * 130.0


def _connectivity_anchor_position(nodes: list[SldNode]) -> tuple[float, float]:
    if not nodes:
        return 0.0, 0.0

    return (
        sum(node.x for node in nodes) / len(nodes) + 80.0,
        sum(node.y for node in nodes) / len(nodes) + 35.0,
    )
