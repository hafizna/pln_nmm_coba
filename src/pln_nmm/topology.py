"""
Derive an SLD-shaped tree from the cimpy object graph.

CIM gives us Substation → VoltageLevel containment, and a flat web of
Terminals + ConnectivityNodes. It does *not* (in PLN's data) populate
cim:Bay containers, so this module synthesizes them by walking the
connectivity graph outward from each BusbarSection.

The output is a deterministic tree the renderer can lay out without
guessing. It is decoupled from cimpy's own classes so the SLD layer
does not import cimpy.

A bay here is: an ordered series of equipment between a busbar and a
"leaf" device (line, transformer, load, generator) or another busbar.
Switching equipment (Breaker / Disconnector / LoadBreakSwitch) sits
in the middle of the bay.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Literal

LeafKind = Literal[
    "line",
    "transformer",
    "load",
    "generator",
    "bus_tie",
    "open",
    "unknown",
]

# Devices that mark the end of a bay walk.
TERMINAL_LEAF_CLASSES = {
    "ConformLoad": "load",
    "NonConformLoad": "load",
    "EnergyConsumer": "load",
    "SynchronousMachine": "generator",
    "AsynchronousMachine": "generator",
}
BRIDGE_LEAF_CLASSES = {
    "ACLineSegment": "line",
    "PowerTransformer": "transformer",
}
SWITCH_CLASSES = {
    "Breaker",
    "Disconnector",
    "GroundDisconnector",
    "LoadBreakSwitch",
    "Switch",
    "Fuse",
    "Jumper",
}


@dataclass(frozen=True)
class BayItem:
    equipment_id: str
    cim_class: str
    label: str


@dataclass(frozen=True)
class Bay:
    """An ordered series of equipment between a busbar and a leaf."""

    id: str
    busbar_id: str
    head_cn_id: str
    # Busbar-side first, leaf last. Does NOT include the busbar itself.
    items: tuple[BayItem, ...]
    leaf_kind: LeafKind


@dataclass(frozen=True)
class VoltageLevelGroup:
    id: str
    name: str
    substation_id: str
    nominal_kv: float
    busbar_ids: tuple[str, ...]
    bays: tuple[Bay, ...]


@dataclass(frozen=True)
class SubstationGroup:
    id: str
    name: str
    voltage_levels: tuple[VoltageLevelGroup, ...]
    # PowerTransformer mRIDs whose ends touch ≥2 VLs in this substation.
    transformer_ids: tuple[str, ...]


@dataclass(frozen=True)
class TopologyModel:
    substations: tuple[SubstationGroup, ...]
    # Equipment that didn't fit any substation (bare lines, lone devices).
    orphan_equipment_ids: tuple[str, ...]


@dataclass(frozen=True)
class TopologyDiagnostics:
    """Counts of structural gaps that the SLD layer should surface."""

    substation_count: int
    voltage_level_count: int
    bay_count: int
    # Substations whose VLs all have zero busbars.
    empty_substations: int
    # Bays whose walk ended on a switch with no continuation. These are
    # often earthing switches or signs of incomplete CIM.
    open_bays: int
    # Bays containing zero switching equipment (no Breaker/Disconnector
    # between busbar and leaf). Operationally suspicious.
    bays_without_switches: int


def compute_diagnostics(model: TopologyModel) -> TopologyDiagnostics:
    bays = [
        bay
        for ss in model.substations
        for vl in ss.voltage_levels
        for bay in vl.bays
    ]
    empty_ss = sum(
        1
        for ss in model.substations
        if all(not vl.busbar_ids for vl in ss.voltage_levels)
    )
    open_bays = sum(1 for bay in bays if bay.leaf_kind == "open")
    bays_without_switches = sum(
        1
        for bay in bays
        if not any(item.cim_class in SWITCH_CLASSES for item in bay.items)
    )
    vl_count = sum(len(ss.voltage_levels) for ss in model.substations)
    return TopologyDiagnostics(
        substation_count=len(model.substations),
        voltage_level_count=vl_count,
        bay_count=len(bays),
        empty_substations=empty_ss,
        open_bays=open_bays,
        bays_without_switches=bays_without_switches,
    )


# ---------------------------------------------------------------------------


@dataclass
class _Indexes:
    """Reverse-reference indexes derived from a flat cimpy topology dict.

    cimpy populates only forward references (Terminal.ConductingEquipment,
    Terminal.ConnectivityNode, Equipment.EquipmentContainer, ...) and leaves
    the reverse-collection fields as placeholder strings. We rebuild what
    we need here.
    """

    cn_to_terminals: dict[str, list[Any]]  # CN mRID → Terminal objects
    eq_to_terminals: dict[str, list[Any]]  # Equipment mRID → Terminal objects
    container_to_equipment: dict[str, list[Any]]  # VL/SS mRID → Equipment
    substation_to_voltage_levels: dict[str, list[Any]]  # SS mRID → VL objects


def derive_topology(
    cimpy_topology: dict[str, Any],
    *,
    merge_substations_by_name: bool = True,
) -> TopologyModel:
    """
    Walk a cimpy result['topology'] dict and build the SLD-shaped tree.

    `cimpy_topology` is the dict cimpy returns under the 'topology' key:
    rdf:ID → CIM object (Terminal, BusbarSection, Substation, ...).

    `merge_substations_by_name` collapses Substation entries that share a
    name into one logical group. PLN's source tool emits multiple Substation
    objects with identical names but UUIDs that differ only in the last
    character — visible artifacts of manual UUID-suffix incrementing.
    Merging makes the SLD show one substation instead of N empty shells.
    """
    indexes = _build_indexes(cimpy_topology.values())

    substations: list[SubstationGroup] = []
    accounted_equipment: set[str] = set()

    for obj in cimpy_topology.values():
        if _classname(obj) != "Substation":
            continue
        ss_group = _build_substation(obj, indexes, accounted_equipment)
        substations.append(ss_group)

    if merge_substations_by_name:
        substations = _merge_by_name(substations)

    orphans = tuple(
        sorted(
            obj.mRID
            for obj in cimpy_topology.values()
            if _is_sld_equipment(obj) and obj.mRID not in accounted_equipment
        )
    )

    return TopologyModel(
        substations=tuple(substations),
        orphan_equipment_ids=orphans,
    )


def _merge_by_name(groups: list[SubstationGroup]) -> list[SubstationGroup]:
    """Collapse Substation groups that share the same `name`."""
    by_name: dict[str, list[SubstationGroup]] = {}
    for ss in groups:
        by_name.setdefault(ss.name, []).append(ss)

    merged: list[SubstationGroup] = []
    for name, members in by_name.items():
        if len(members) == 1:
            merged.append(members[0])
            continue
        # Merge: keep the lowest-mRID id as canonical, concatenate VLs and
        # transformer ids. VLs from different members keep their own ids.
        canonical = min(members, key=lambda m: m.id)
        all_vls = tuple(vl for m in members for vl in m.voltage_levels)
        all_transformers = tuple(
            sorted({tid for m in members for tid in m.transformer_ids})
        )
        merged.append(
            SubstationGroup(
                id=canonical.id,
                name=name,
                voltage_levels=all_vls,
                transformer_ids=all_transformers,
            )
        )
    return merged


def _build_indexes(objs: Iterable[Any]) -> _Indexes:
    cn_to_terminals: dict[str, list[Any]] = {}
    eq_to_terminals: dict[str, list[Any]] = {}
    container_to_equipment: dict[str, list[Any]] = {}
    ss_to_vls: dict[str, list[Any]] = {}

    for obj in objs:
        cls = _classname(obj)
        if cls == "Terminal":
            eq = getattr(obj, "ConductingEquipment", None)
            if eq is not None:
                eq_to_terminals.setdefault(eq.mRID, []).append(obj)
            cn = getattr(obj, "ConnectivityNode", None)
            if cn is not None:
                cn_to_terminals.setdefault(cn.mRID, []).append(obj)
        elif cls == "VoltageLevel":
            ss = getattr(obj, "Substation", None)
            if ss is not None:
                ss_to_vls.setdefault(ss.mRID, []).append(obj)
        elif _is_sld_equipment(obj) or cls in ("PowerTransformer",):
            container = getattr(obj, "EquipmentContainer", None)
            if container is not None:
                container_to_equipment.setdefault(container.mRID, []).append(obj)

    return _Indexes(
        cn_to_terminals=cn_to_terminals,
        eq_to_terminals=eq_to_terminals,
        container_to_equipment=container_to_equipment,
        substation_to_voltage_levels=ss_to_vls,
    )


# ---------------------------------------------------------------------------
# Substation / VoltageLevel build
# ---------------------------------------------------------------------------


def _build_substation(
    ss: Any,
    indexes: _Indexes,
    accounted: set[str],
) -> SubstationGroup:
    vls = []
    for vl in indexes.substation_to_voltage_levels.get(ss.mRID, []):
        vl_group = _build_voltage_level(vl, indexes, accounted)
        vls.append(vl_group)

    transformer_ids = tuple(
        sorted(
            eq.mRID
            for eq in indexes.container_to_equipment.get(ss.mRID, [])
            if _classname(eq) == "PowerTransformer"
        )
    )
    for tid in transformer_ids:
        accounted.add(tid)

    return SubstationGroup(
        id=ss.mRID,
        name=getattr(ss, "name", "") or ss.mRID[:8],
        voltage_levels=tuple(vls),
        transformer_ids=transformer_ids,
    )


def _build_voltage_level(
    vl: Any,
    indexes: _Indexes,
    accounted: set[str],
) -> VoltageLevelGroup:
    vl_equipment = indexes.container_to_equipment.get(vl.mRID, [])
    busbars = [eq for eq in vl_equipment if _classname(eq) == "BusbarSection"]

    bays: list[Bay] = []
    for bb in busbars:
        accounted.add(bb.mRID)
        bays.extend(_derive_bays(bb, indexes, accounted))

    base_voltage = getattr(vl, "BaseVoltage", None)
    nominal_kv = float(getattr(base_voltage, "nominalVoltage", 0.0) or 0.0)

    return VoltageLevelGroup(
        id=vl.mRID,
        name=getattr(vl, "name", "") or vl.mRID[:8],
        substation_id=getattr(getattr(vl, "Substation", None), "mRID", ""),
        nominal_kv=nominal_kv,
        busbar_ids=tuple(bb.mRID for bb in busbars),
        bays=tuple(bays),
    )


# ---------------------------------------------------------------------------
# Bay derivation
# ---------------------------------------------------------------------------


def _derive_bays(
    busbar: Any,
    indexes: _Indexes,
    accounted: set[str],
) -> list[Bay]:
    bays: list[Bay] = []
    for bb_term in indexes.eq_to_terminals.get(busbar.mRID, []):
        cn = getattr(bb_term, "ConnectivityNode", None)
        if cn is None:
            continue
        head_cn_id = cn.mRID
        for sibling in indexes.cn_to_terminals.get(head_cn_id, []):
            sib_eq = getattr(sibling, "ConductingEquipment", None)
            if sib_eq is None or sib_eq.mRID == busbar.mRID:
                continue
            items, leaf_kind = _walk_bay(sibling, indexes)
            if not items:
                continue
            for item in items:
                accounted.add(item.equipment_id)
            bays.append(
                Bay(
                    id=f"bay:{busbar.mRID}:{sibling.mRID}",
                    busbar_id=busbar.mRID,
                    head_cn_id=head_cn_id,
                    items=tuple(items),
                    leaf_kind=leaf_kind,
                )
            )
    return bays


def _walk_bay(
    start_terminal: Any,
    indexes: _Indexes,
) -> tuple[list[BayItem], LeafKind]:
    """Walk in series from one bay-side terminal until a leaf or dead end."""
    items: list[BayItem] = []
    visited_cn: set[str] = set()
    visited_eq: set[str] = set()
    current_term = start_terminal

    # Bound the walk; real bays are short. Avoids pathological loops.
    for _ in range(64):
        eq = getattr(current_term, "ConductingEquipment", None)
        if eq is None or eq.mRID in visited_eq:
            return items, "open"
        visited_eq.add(eq.mRID)

        cls = _classname(eq)
        items.append(
            BayItem(
                equipment_id=eq.mRID,
                cim_class=cls,
                label=getattr(eq, "name", "") or cls,
            )
        )

        if cls in TERMINAL_LEAF_CLASSES:
            return items, TERMINAL_LEAF_CLASSES[cls]  # type: ignore[return-value]
        if cls in BRIDGE_LEAF_CLASSES:
            return items, BRIDGE_LEAF_CLASSES[cls]  # type: ignore[return-value]
        if cls == "BusbarSection":
            return items, "bus_tie"
        if cls not in SWITCH_CLASSES:
            # Unknown intermediate equipment; stop rather than guess.
            return items, "unknown"

        # Find the OTHER terminal on this switch and step through it.
        terms = indexes.eq_to_terminals.get(eq.mRID, [])
        next_term = next(
            (t for t in terms if getattr(t, "mRID", None) != current_term.mRID),
            None,
        )
        if next_term is None:
            return items, "open"
        next_cn = getattr(next_term, "ConnectivityNode", None)
        if next_cn is None or next_cn.mRID in visited_cn:
            return items, "open"
        visited_cn.add(next_cn.mRID)

        # Pick a continuing terminal — one not on the equipment we just came from.
        successors = [
            t
            for t in indexes.cn_to_terminals.get(next_cn.mRID, [])
            if (
                getattr(getattr(t, "ConductingEquipment", None), "mRID", None)
                != eq.mRID
            )
        ]
        if not successors:
            return items, "open"
        # PoC: pick the first. Branching CNs (rare in well-formed bays)
        # become a "first wins" choice. Flag this in a future revision.
        current_term = successors[0]

    return items, "open"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _classname(obj: Any) -> str:
    return type(obj).__name__


def _is_sld_equipment(obj: Any) -> bool:
    cls = _classname(obj)
    return (
        cls in BRIDGE_LEAF_CLASSES
        or cls in TERMINAL_LEAF_CLASSES
        or cls in SWITCH_CLASSES
        or cls == "BusbarSection"
    )
