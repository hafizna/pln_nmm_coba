"""Expand bay templates into explicit node-breaker objects.

A workbook row says "this bay uses BAY_PHT_DB_150". This module turns that into
the switches, terminals and connectivity nodes that CIM needs, so the topology
is explicit rather than implied.

Two arrangements need special care:

* Double busbar. Each bay carries one bus-side PMS per busbar. Only one is
  normally closed; `bus_normal` in the workbook says which.
* One-and-a-half breaker. Three breakers serve two circuits and the centre
  breaker is SHARED. It must become ONE Breaker with two terminals, not two
  breakers, or N-1 analysis is wrong.

Everything produced here is derived, never measured, so each object carries
provenance from the row that produced it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Literal

from ..model.identity import stable_id


SwitchKind = Literal["BREAKER", "DISCONNECTOR"]


@dataclass
class Switch:
    """A breaker or disconnector with its two connectivity endpoints."""

    id: str
    name: str
    kind: SwitchKind
    role: str
    normal_open: bool
    node_a: str
    node_b: str
    bay_id: str
    shared: bool = False


@dataclass
class Node:
    """A ConnectivityNode: an electrical junction."""

    id: str
    name: str
    role: str
    bay_id: str | None = None


@dataclass
class BayExpansion:
    """Everything one bay row expands into."""

    bay_id: str
    gi_id: str
    template_id: str
    switches: list[Switch] = field(default_factory=list)
    nodes: list[Node] = field(default_factory=list)
    equipment_node: str | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def breakers(self) -> list[Switch]:
        return [s for s in self.switches if s.kind == "BREAKER"]

    @property
    def disconnectors(self) -> list[Switch]:
        return [s for s in self.switches if s.kind == "DISCONNECTOR"]


def bus_node_id(gi_id: str, bus: str) -> str:
    """Busbar nodes are shared across every bay in the GI."""
    return stable_id("CN", gi_id, "BUS", bus)


def _node(gi_id: str, bay_id: str, role: str) -> Node:
    return Node(
        id=stable_id("CN", gi_id, bay_id, role),
        name=f"{bay_id} {role}",
        role=role,
        bay_id=bay_id,
    )


def _switch(
    gi_id: str,
    bay_id: str,
    role: str,
    kind: SwitchKind,
    node_a: str,
    node_b: str,
    normal_open: bool,
    shared: bool = False,
) -> Switch:
    return Switch(
        id=stable_id("SW", gi_id, bay_id, role),
        name=f"{role} {bay_id}",
        kind=kind,
        role=role,
        normal_open=normal_open,
        node_a=node_a,
        node_b=node_b,
        bay_id=bay_id,
        shared=shared,
    )


# --- Arrangement builders ---------------------------------------------------


def _expand_double_busbar(
    gi_id: str, bay_id: str, bus_normal: str, equipment_role: str
) -> BayExpansion:
    """DS_BUS_A, DS_BUS_B, CB, DS_<equipment>.

    Both bus-side disconnectors exist; only the one matching bus_normal is
    closed. That is the whole point of a double busbar -- the selector.
    """
    exp = BayExpansion(bay_id=bay_id, gi_id=gi_id, template_id="")

    bus_a = bus_node_id(gi_id, "A")
    bus_b = bus_node_id(gi_id, "B")
    n_pre_cb = _node(gi_id, bay_id, "PRE_CB")
    n_post_cb = _node(gi_id, bay_id, "POST_CB")
    n_equip = _node(gi_id, bay_id, equipment_role)
    exp.nodes += [n_pre_cb, n_post_cb, n_equip]

    exp.switches.append(
        _switch(gi_id, bay_id, "DS_BUS_A", "DISCONNECTOR", bus_a, n_pre_cb.id,
                normal_open=(bus_normal != "A"))
    )
    exp.switches.append(
        _switch(gi_id, bay_id, "DS_BUS_B", "DISCONNECTOR", bus_b, n_pre_cb.id,
                normal_open=(bus_normal != "B"))
    )
    exp.switches.append(
        _switch(gi_id, bay_id, "CB", "BREAKER", n_pre_cb.id, n_post_cb.id,
                normal_open=False)
    )
    exp.switches.append(
        _switch(gi_id, bay_id, f"DS_{equipment_role}", "DISCONNECTOR",
                n_post_cb.id, n_equip.id, normal_open=False)
    )
    exp.equipment_node = n_equip.id
    return exp


def _expand_single_busbar(
    gi_id: str, bay_id: str, equipment_role: str, bus: str = "A"
) -> BayExpansion:
    """DS_BUS, CB, DS_<equipment>. No selector: one busbar, no choice."""
    exp = BayExpansion(bay_id=bay_id, gi_id=gi_id, template_id="")

    n_pre_cb = _node(gi_id, bay_id, "PRE_CB")
    n_post_cb = _node(gi_id, bay_id, "POST_CB")
    n_equip = _node(gi_id, bay_id, equipment_role)
    exp.nodes += [n_pre_cb, n_post_cb, n_equip]

    exp.switches.append(
        _switch(gi_id, bay_id, "DS_BUS", "DISCONNECTOR",
                bus_node_id(gi_id, bus), n_pre_cb.id, normal_open=False)
    )
    exp.switches.append(
        _switch(gi_id, bay_id, "CB", "BREAKER", n_pre_cb.id, n_post_cb.id,
                normal_open=False)
    )
    exp.switches.append(
        _switch(gi_id, bay_id, f"DS_{equipment_role}", "DISCONNECTOR",
                n_post_cb.id, n_equip.id, normal_open=False)
    )
    exp.equipment_node = n_equip.id
    return exp


def _expand_coupler(gi_id: str, bay_id: str) -> BayExpansion:
    """DS_BUS_A, CB, DS_BUS_B. Joins the two busbars; selects neither."""
    exp = BayExpansion(bay_id=bay_id, gi_id=gi_id, template_id="")

    n_a = _node(gi_id, bay_id, "COUPLER_A")
    n_b = _node(gi_id, bay_id, "COUPLER_B")
    exp.nodes += [n_a, n_b]

    exp.switches.append(
        _switch(gi_id, bay_id, "DS_BUS_A", "DISCONNECTOR",
                bus_node_id(gi_id, "A"), n_a.id, normal_open=False)
    )
    exp.switches.append(
        _switch(gi_id, bay_id, "CB", "BREAKER", n_a.id, n_b.id, normal_open=False)
    )
    exp.switches.append(
        _switch(gi_id, bay_id, "DS_BUS_B", "DISCONNECTOR",
                n_b.id, bus_node_id(gi_id, "B"), normal_open=False)
    )
    return exp


def _expand_bus_section(gi_id: str, bay_id: str) -> BayExpansion:
    """DS_SEC_1, CB, DS_SEC_2. Splits one busbar into two sections."""
    exp = BayExpansion(bay_id=bay_id, gi_id=gi_id, template_id="")

    n_1 = _node(gi_id, bay_id, "SEC_1")
    n_2 = _node(gi_id, bay_id, "SEC_2")
    exp.nodes += [n_1, n_2]

    exp.switches.append(
        _switch(gi_id, bay_id, "DS_SEC_1", "DISCONNECTOR",
                bus_node_id(gi_id, "A"), n_1.id, normal_open=False)
    )
    exp.switches.append(
        _switch(gi_id, bay_id, "CB", "BREAKER", n_1.id, n_2.id, normal_open=False)
    )
    exp.switches.append(
        _switch(gi_id, bay_id, "DS_SEC_2", "DISCONNECTOR",
                n_2.id, bus_node_id(gi_id, "B"), normal_open=False)
    )
    return exp


def _expand_diameter(gi_id: str, bay_id: str) -> BayExpansion:
    """One-and-a-half breaker diameter: 3 CB serving 2 circuits.

        BUS A ─[DS_BUS_A]─ n1 ─[CB1]─ n2 ─[DS_S1]─ circuit 1
                                       │
                                     [CB2]   <-- SHARED by both circuits
                                       │
        BUS B ─[DS_BUS_B]─ n4 ─[CB3]─ n3 ─[DS_S2]─ circuit 2

    CB2 is emitted as a SINGLE Breaker joining n2 and n3. Emitting it twice
    would make the model think there are two independent breakers, and any
    N-1 result drawn from that is wrong.
    """
    exp = BayExpansion(bay_id=bay_id, gi_id=gi_id, template_id="")

    n1 = _node(gi_id, bay_id, "DIA_N1")
    n2 = _node(gi_id, bay_id, "DIA_N2")
    n3 = _node(gi_id, bay_id, "DIA_N3")
    n4 = _node(gi_id, bay_id, "DIA_N4")
    s1 = _node(gi_id, bay_id, "SIRKIT_1")
    s2 = _node(gi_id, bay_id, "SIRKIT_2")
    exp.nodes += [n1, n2, n3, n4, s1, s2]

    exp.switches += [
        _switch(gi_id, bay_id, "DS_BUS_A", "DISCONNECTOR",
                bus_node_id(gi_id, "A"), n1.id, normal_open=False),
        _switch(gi_id, bay_id, "CB1", "BREAKER", n1.id, n2.id, normal_open=False),
        _switch(gi_id, bay_id, "DS_S1", "DISCONNECTOR", n2.id, s1.id,
                normal_open=False),
        # The shared centre breaker: one object, two terminals.
        _switch(gi_id, bay_id, "CB2_TENGAH", "BREAKER", n2.id, n3.id,
                normal_open=False, shared=True),
        _switch(gi_id, bay_id, "DS_S2", "DISCONNECTOR", n3.id, s2.id,
                normal_open=False),
        _switch(gi_id, bay_id, "CB3", "BREAKER", n4.id, n3.id, normal_open=False),
        _switch(gi_id, bay_id, "DS_BUS_B", "DISCONNECTOR",
                bus_node_id(gi_id, "B"), n4.id, normal_open=False),
    ]
    exp.equipment_node = s1.id
    return exp


# --- Dispatch ---------------------------------------------------------------

_EQUIPMENT_ROLE = {
    "PENGHANTAR": "LINE",
    "TRAFO": "TRAFO",
    "TRAFO_20KV": "TRAFO",
    "GENERATOR": "GSU",
}


def expand_bay(row: dict, gi_skema: str) -> BayExpansion:
    """Expand one 02_BAY row into node-breaker objects.

    `row` uses the workbook's own column names; `gi_skema` is the GI's
    skema_busbar from 01_GI, which decides the arrangement.
    """
    bay_id = str(row["bay_id"])
    gi_id = str(row["gi_id"])
    tipe = str(row["bay_tipe"])
    template_id = str(row.get("template_id") or "")
    bus_normal = str(row.get("bus_normal") or "-")

    if tipe == "KOPEL":
        exp = _expand_coupler(gi_id, bay_id)
    elif tipe == "BUS_SECTION":
        exp = _expand_bus_section(gi_id, bay_id)
    elif tipe == "DIAMETER":
        exp = _expand_diameter(gi_id, bay_id)
    else:
        role = _EQUIPMENT_ROLE.get(tipe, "EQUIP")
        if gi_skema in ("DOUBLE", "DOUBLE_SECTION"):
            if bus_normal not in ("A", "B"):
                exp = _expand_double_busbar(gi_id, bay_id, "A", role)
                exp.warnings.append(
                    f"{bay_id}: bus_normal='{bus_normal}' tidak sah untuk double "
                    "busbar; memakai 'A'. Periksa 02_BAY."
                )
            else:
                exp = _expand_double_busbar(gi_id, bay_id, bus_normal, role)
        elif gi_skema in ("SINGLE", "SINGLE_SECTION"):
            exp = _expand_single_busbar(gi_id, bay_id, role)
        elif gi_skema == "ONE_HALF_CB":
            exp = _expand_diameter(gi_id, bay_id)
            exp.warnings.append(
                f"{bay_id}: GI berskema 1-1/2 CB tetapi bay_tipe='{tipe}'; "
                "diperlakukan sebagai diameter."
            )
        else:
            exp = _expand_single_busbar(gi_id, bay_id, role)
            exp.warnings.append(
                f"{bay_id}: skema_busbar '{gi_skema}' tidak dikenali; "
                "memakai single busbar."
            )

    exp.template_id = template_id
    return exp


def busbar_nodes(gi_id: str, gi_skema: str) -> list[Node]:
    """The busbar nodes a GI needs, given its arrangement."""
    if gi_skema in ("DOUBLE", "DOUBLE_SECTION", "ONE_HALF_CB"):
        buses = ["A", "B"]
    elif gi_skema in ("SINGLE_SECTION",):
        buses = ["A", "B"]  # two sections, joined by a BUS_SECTION bay
    else:
        buses = ["A"]
    return [
        Node(id=bus_node_id(gi_id, b), name=f"{gi_id} BUS {b}", role=f"BUS_{b}")
        for b in buses
    ]


def expand_all(bay_rows: Iterable[dict], gi_skema_map: dict[str, str]) -> list[BayExpansion]:
    """Expand every bay row, skipping ones whose GI is unknown."""
    out = []
    for row in bay_rows:
        gi = str(row.get("gi_id"))
        skema = gi_skema_map.get(gi)
        if skema is None:
            exp = BayExpansion(
                bay_id=str(row.get("bay_id")), gi_id=gi, template_id=""
            )
            exp.warnings.append(f"GI '{gi}' tidak ada di 01_GI; bay dilewati.")
            out.append(exp)
            continue
        out.append(expand_bay(row, skema))
    return out
