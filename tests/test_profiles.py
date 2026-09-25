"""Tests for DL emission and profile separation."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

from pln_nmm.builder import build_cim
from pln_nmm.check import check_profiles
from pln_nmm.emit import Diagram, build_dl_xml, read_eq_mrids, write_dl
from pln_nmm.model import stable_id
from pln_nmm.sources import read_workbook

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def eq_file(tmp_path_factory):
    wb_path = tmp_path_factory.mktemp("wb") / "wb.xlsx"
    subprocess.run(
        [sys.executable, str(REPO / "scripts" / "build_workbook_template.py"), str(wb_path)],
        check=True,
        capture_output=True,
    )
    out = tmp_path_factory.mktemp("eq") / "EQ.xml"
    build_cim(read_workbook(wb_path), out, scenario_id="BP-2026-05-15")
    return out


@pytest.fixture(scope="module")
def dl_file(eq_file, tmp_path_factory):
    known = read_eq_mrids(eq_file)
    text = eq_file.read_text(encoding="utf-8")
    breakers = re.findall(r'<cim:Breaker rdf:ID="_([^"]+)"', text)[:5]
    busbars = re.findall(r'<cim:BusbarSection rdf:ID="_([^"]+)"', text)[:3]

    diagram = Diagram(
        mrid=stable_id("DIAGRAM", "TEST", "SISTEM"), name="Sistem uji 150 kV"
    )
    for i, b in enumerate(busbars):
        diagram.place(b, 100.0 + i * 400, 80.0)
    for i, b in enumerate(breakers):
        # A deliberately awkward float: repr() must survive the round-trip.
        diagram.place(b, 120.0 + i * 150, 260.0 + i / 3.0)

    out = tmp_path_factory.mktemp("dl") / "DL.xml"
    write_dl(
        [diagram], out, model_id=stable_id("MODEL", "TEST", "DL"), known_mrids=known
    )
    return out


# --- DL emission ------------------------------------------------------------


def test_dl_declares_the_diagram_layout_profile(dl_file):
    assert "DiagramLayout" in dl_file.read_text(encoding="utf-8")


def test_dl_contains_only_dl_classes(dl_file):
    classes = set(re.findall(r"<cim:(\w+) rdf:ID", dl_file.read_text(encoding="utf-8")))
    assert classes <= {"Diagram", "DiagramObject", "DiagramObjectPoint"}


def test_dl_links_to_equipment_by_resource_not_text(dl_file):
    """cimpy's own exporter writes this as text, which does not resolve."""
    text = dl_file.read_text(encoding="utf-8")
    assert 'DiagramObject.IdentifiedObject rdf:resource="#_' in text
    assert "<cim:DiagramObject.IdentifiedObject>" not in text


def test_every_dl_link_resolves_into_eq(dl_file, eq_file):
    eq_ids = read_eq_mrids(eq_file)
    refs = re.findall(
        r'DiagramObject\.IdentifiedObject rdf:resource="#_([^"]+)"',
        dl_file.read_text(encoding="utf-8"),
    )
    assert refs
    assert all(r in eq_ids for r in refs)


def test_coordinates_survive_repr_round_trip(dl_file):
    coords = re.findall(
        r"DiagramObjectPoint\.[xy]Position>([-\d.eE+]+)<",
        dl_file.read_text(encoding="utf-8"),
    )
    assert coords
    for c in coords:
        assert repr(float(c)) == c, f"{c} tidak bit-exact"


def test_dl_is_deterministic(eq_file):
    """Same diagram, same bytes -- so layout changes are diffable."""
    d = Diagram(mrid=stable_id("DIAGRAM", "X"), name="X")
    d.place("abc", 1.5, 2.5)
    a, _ = build_dl_xml([d], model_id="m1")
    b, _ = build_dl_xml([d], model_id="m1")
    strip = lambda s: re.sub(r"<md:Model.created>[^<]*<", "<", s)
    assert strip(a) == strip(b)


def test_unresolved_placement_is_reported_not_dropped():
    """Dropping a bad reference would hide the fault."""
    d = Diagram(mrid=stable_id("DIAGRAM", "Y"), name="Y")
    d.place("does-not-exist", 0.0, 0.0)
    xml, report = build_dl_xml([d], model_id="m", known_mrids={"something-else"})
    assert report.unresolved == ["does-not-exist"]
    assert "does-not-exist" in xml


def test_one_diagram_can_hold_many_equipment_and_many_diagrams_one_equipment():
    """The reason for moving off plnicp: layout is per diagram, not per object."""
    a = Diagram(mrid=stable_id("D", "sistem"), name="sistem")
    b = Diagram(mrid=stable_id("D", "gi"), name="detail GI")
    a.place("eq1", 10.0, 10.0)
    b.place("eq1", 999.0, 999.0)
    xml, report = build_dl_xml([a, b], model_id="m")
    assert report.diagrams == 2
    assert report.objects == 2
    # Two distinct DiagramObjects for one piece of equipment.
    assert len(set(re.findall(r'<cim:DiagramObject rdf:ID="_([^"]+)"', xml))) == 2


# --- profile separation -----------------------------------------------------


def test_eq_carries_no_layout(eq_file):
    assert "plnicp:DiagramProperty" not in eq_file.read_text(encoding="utf-8")


def test_profiles_pass_the_separation_check(eq_file, dl_file):
    rep = check_profiles(eq_file, dl_file)
    assert rep.ok, rep.errors


def test_layout_inside_eq_is_rejected(tmp_path, eq_file, dl_file):
    polluted = tmp_path / "EQ_polluted.xml"
    text = eq_file.read_text(encoding="utf-8")
    text = text.replace(
        "</cim:Substation>",
        "  <plnicp:DiagramProperty.x>10.0</plnicp:DiagramProperty.x>\n"
        "</cim:Substation>",
        1,
    )
    polluted.write_text(text, encoding="utf-8")

    rep = check_profiles(polluted, dl_file)
    assert not rep.ok
    assert any("plnicp" in e for e in rep.errors)

    # ...unless the build explicitly asked for the PLN compatibility shadow.
    allowed = check_profiles(polluted, dl_file, allow_plnicp_in_eq=True)
    assert allowed.ok


def test_equipment_inside_dl_is_rejected(tmp_path, eq_file, dl_file):
    polluted = tmp_path / "DL_polluted.xml"
    text = dl_file.read_text(encoding="utf-8")
    text = text.replace("</rdf:RDF>", '  <cim:Breaker rdf:ID="_x"/>\n</rdf:RDF>')
    polluted.write_text(text, encoding="utf-8")
    rep = check_profiles(eq_file, polluted)
    assert not rep.ok
    assert any("Breaker" in e for e in rep.errors)


def test_dangling_diagram_link_is_rejected(tmp_path, eq_file):
    d = Diagram(mrid=stable_id("D", "bad"), name="bad")
    d.place("nonexistent-mrid", 1.0, 1.0)
    dl = tmp_path / "DL_bad.xml"
    write_dl([d], dl, model_id="m")
    rep = check_profiles(eq_file, dl)
    assert not rep.ok
    assert any("tidak ada di EQ" in e for e in rep.errors)


def test_missing_dl_file_is_a_warning_not_an_error(eq_file):
    """A model without layout yet is incomplete, not broken."""
    rep = check_profiles(eq_file, None)
    assert rep.ok
    assert any("belum dipisahkan" in w for w in rep.warnings)
