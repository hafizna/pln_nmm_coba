"""Tests for the workbook -> CIM builder."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

from pln_nmm.builder import (
    build_cim,
    check_topology,
    expand_bay,
    read_workbook,
    stable_id,
)

REPO = Path(__file__).resolve().parents[1]
WORKBOOK = REPO / "NMM_Model_Input_TEMPLATE.xlsx"


@pytest.fixture(scope="module")
def workbook(tmp_path_factory):
    """Build the workbook fresh so tests never depend on a stale file."""
    out = tmp_path_factory.mktemp("wb") / "wb.xlsx"
    subprocess.run(
        [sys.executable, str(REPO / "scripts" / "build_workbook_template.py"), str(out)],
        check=True,
        capture_output=True,
    )
    return read_workbook(out)


@pytest.fixture(scope="module")
def built(workbook, tmp_path_factory):
    out = tmp_path_factory.mktemp("cim") / "EQ.xml"
    report = build_cim(workbook, out, scenario_id="BP-2026-05-15")
    return out, report


# --- template expansion -----------------------------------------------------


def test_stable_id_is_deterministic():
    assert stable_id("SW", "GIL", "BAY1", "CB") == stable_id("SW", "GIL", "BAY1", "CB")
    assert stable_id("SW", "GIL", "BAY1", "CB") != stable_id("SW", "GIL", "BAY2", "CB")


def test_double_busbar_bay_has_one_breaker_and_three_disconnectors():
    row = {
        "bay_id": "GIL-150-BAY-X",
        "gi_id": "GIL",
        "bay_tipe": "PENGHANTAR",
        "template_id": "BAY_PHT_DB_150",
        "bus_normal": "A",
    }
    exp = expand_bay(row, "DOUBLE")
    assert len(exp.breakers) == 1
    assert len(exp.disconnectors) == 3


def test_bus_normal_selects_exactly_one_closed_bus_disconnector():
    """The whole point of a double busbar: one selector closed, one open."""
    for chosen, other in (("A", "B"), ("B", "A")):
        row = {
            "bay_id": "BAY",
            "gi_id": "GIL",
            "bay_tipe": "PENGHANTAR",
            "template_id": "BAY_PHT_DB_150",
            "bus_normal": chosen,
        }
        exp = expand_bay(row, "DOUBLE")
        closed = {s.role for s in exp.disconnectors if not s.normal_open}
        assert f"DS_BUS_{chosen}" in closed
        assert f"DS_BUS_{other}" not in closed


def test_single_busbar_bay_has_no_bus_selector():
    row = {
        "bay_id": "BAY",
        "gi_id": "PSG-AIS",
        "bay_tipe": "PENGHANTAR",
        "template_id": "BAY_PHT_SS_150",
        "bus_normal": "-",
    }
    exp = expand_bay(row, "SINGLE_SECTION")
    roles = {s.role for s in exp.switches}
    assert "DS_BUS" in roles
    assert "DS_BUS_A" not in roles and "DS_BUS_B" not in roles


def test_diameter_has_three_breakers_and_one_is_shared():
    """1-1/2 CB: 3 breakers serve 2 circuits; the centre one is shared."""
    row = {
        "bay_id": "CLB-150-DIA-1",
        "gi_id": "CLB",
        "bay_tipe": "DIAMETER",
        "template_id": "BAY_DIAMETER_150",
        "bus_normal": "-",
    }
    exp = expand_bay(row, "ONE_HALF_CB")
    assert len(exp.breakers) == 3
    shared = [s for s in exp.breakers if s.shared]
    assert len(shared) == 1
    assert shared[0].role == "CB2_TENGAH"


def test_shared_breaker_joins_both_circuit_sides():
    """The centre breaker must bridge the two circuit branches, not duplicate."""
    row = {
        "bay_id": "DIA",
        "gi_id": "CLB",
        "bay_tipe": "DIAMETER",
        "template_id": "BAY_DIAMETER_150",
        "bus_normal": "-",
    }
    exp = expand_bay(row, "ONE_HALF_CB")
    centre = next(s for s in exp.breakers if s.shared)
    cb1 = next(s for s in exp.breakers if s.role == "CB1")
    cb3 = next(s for s in exp.breakers if s.role == "CB3")
    # Centre sits between CB1's far side and CB3's far side.
    assert centre.node_a == cb1.node_b
    assert centre.node_b == cb3.node_b
    assert centre.node_a != centre.node_b


def test_coupler_touches_both_busbars():
    row = {
        "bay_id": "COUPLER",
        "gi_id": "GIL",
        "bay_tipe": "KOPEL",
        "template_id": "BAY_KOPEL_DB_150",
        "bus_normal": "-",
    }
    exp = expand_bay(row, "DOUBLE")
    from pln_nmm.builder.templates import bus_node_id

    touched = {n for s in exp.switches for n in (s.node_a, s.node_b)}
    assert bus_node_id("GIL", "A") in touched
    assert bus_node_id("GIL", "B") in touched


# --- emitted CIM ------------------------------------------------------------


def test_build_produces_expected_object_classes(built):
    _path, report = built
    for cls in ("Bay", "Breaker", "Disconnector", "ConnectivityNode", "Terminal"):
        assert report.counts.get(cls, 0) > 0, f"tidak ada objek {cls}"


def test_no_dangling_references_or_duplicate_ids(built):
    path, _report = built
    topo = check_topology(path)
    assert topo.dangling == []
    assert topo.duplicate_ids == []


def test_every_switch_has_exactly_two_terminals(built):
    path, _report = built
    s = path.read_text(encoding="utf-8")
    per_equipment: dict[str, int] = {}
    for m in re.finditer(r"<cim:Terminal[^>]*>(.*?)</cim:Terminal>", s, re.S):
        eq = re.search(
            r'Terminal.ConductingEquipment rdf:resource="#_([^"]+)"', m.group(1)
        )
        if eq:
            per_equipment[eq.group(1)] = per_equipment.get(eq.group(1), 0) + 1

    for m in re.finditer(r'<cim:(?:Breaker|Disconnector) rdf:ID="_([^"]+)"', s):
        assert per_equipment.get(m.group(1)) == 2


def test_shared_breaker_emitted_once_with_two_terminals(built):
    """Regression: emitting the centre breaker twice breaks N-1 analysis."""
    path, _report = built
    s = path.read_text(encoding="utf-8")
    shared = re.findall(
        r'<cim:Breaker rdf:ID="_([^"]+)">(?:(?!</cim:Breaker>).)*?'
        r"plnnmm:sharedBreaker>true<",
        s,
        re.S,
    )
    assert shared, "tidak ada PMT berbagi yang ditandai"
    for bid in shared:
        assert s.count(f'rdf:ID="_{bid}"') == 1
        assert s.count(f'Terminal.ConductingEquipment rdf:resource="#_{bid}"') == 2


def test_unknown_impedance_is_omitted_not_zero(built):
    """PLN's aggregate file writes 0 for unknown r/x. We must not."""
    path, report = built
    s = path.read_text(encoding="utf-8")
    assert "<cim:ACLineSegment.r>" not in s
    assert "<cim:ACLineSegment.x>" not in s
    assert report.omitted_parameters.get("cim:ACLineSegment.x", 0) > 0


def test_no_unresolved_template_tokens(built):
    path, _report = built
    assert "$(Isi_" not in path.read_text(encoding="utf-8")


def test_derived_objects_carry_provenance(built):
    path, _report = built
    s = path.read_text(encoding="utf-8")
    for m in re.finditer(r"<cim:(Breaker|Disconnector)[^>]*>(.*?)</cim:\1>", s, re.S):
        assert "plnnmm:provenance" in m.group(2)


def test_bus_normal_survives_into_cim(built):
    """A double-busbar bay must emit one open and one closed bus disconnector."""
    path, _report = built
    s = path.read_text(encoding="utf-8")
    opened = len(
        re.findall(
            r"<cim:Disconnector[^>]*>(?:(?!</cim:Disconnector>).)*?"
            r"Switch.normalOpen>true<",
            s,
            re.S,
        )
    )
    assert opened > 0, "tidak ada PMS rel yang normal terbuka"


def test_generated_file_round_trips_through_adapter(built, tmp_path):
    """The builder's output must survive the existing preserve round-trip."""
    from pln_nmm.adapter import extract_pln_extensions

    path, _report = built
    report = extract_pln_extensions(path)
    assert report.extensions, "tidak ada ekstensi PLN yang terbaca"


def test_deterministic_output(workbook, tmp_path):
    """Same workbook, same bytes -- so exports are diffable."""
    a = tmp_path / "a.xml"
    b = tmp_path / "b.xml"
    build_cim(workbook, a, scenario_id="BP-2026-05-15")
    build_cim(workbook, b, scenario_id="BP-2026-05-15")

    def strip_created(p):
        return re.sub(r"<md:Model.created>[^<]*<", "<md:Model.created><", p.read_text(encoding="utf-8"))

    assert strip_created(a) == strip_created(b)
