"""Tests for the PLN extension adapter module."""

from pathlib import Path

import pytest
from lxml import etree

from pln_nmm.adapter import (
    NS_NHFTUI,
    NS_PLNICP,
    extract_pln_extensions,
    reinject_pln_extensions,
    strip_pln_extensions,
)


FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_EQ = FIXTURES / "sample_EQ.xml"


def test_extract_finds_expected_counts():
    """Sample EQ has 26 elements with x/y and 16 with nhftui:info."""
    report = extract_pln_extensions(SAMPLE_EQ)
    assert report.elements_with_x == 26
    assert report.elements_with_y == 26
    assert report.elements_with_nhftui == 16
    assert len(report.extensions) == 26


def test_extract_preserves_float_precision():
    """The known busbar element has these exact coordinates in the source."""
    report = extract_pln_extensions(SAMPLE_EQ)
    busbar_mrid = "460b6e83-6e01-413f-aa70-6280bee4104a"
    ext = report.extensions[busbar_mrid]
    assert ext.x == 558.0909726137421
    assert ext.y == 123.65246948593943


def test_extract_detects_id_mrid_mismatches():
    """The sample has 9 elements where rdf:ID and mRID disagree."""
    report = extract_pln_extensions(SAMPLE_EQ)
    assert report.elements_with_id_mrid_mismatch >= 1


def test_strip_removes_all_pln_namespaces(tmp_path):
    """After stripping, no plnicp:* children or nhftui:info attributes remain."""
    cleaned = tmp_path / "cleaned.xml"
    strip_pln_extensions(SAMPLE_EQ, cleaned)

    tree = etree.parse(str(cleaned))
    for elem in tree.iter():
        if not isinstance(elem.tag, str):
            continue
        # No plnicp child elements
        for child in elem:
            if isinstance(child.tag, str):
                assert not child.tag.startswith(f"{{{NS_PLNICP}}}"), (
                    f"plnicp child survived strip: {child.tag}"
                )
        # No nhftui:info attributes
        assert f"{{{NS_NHFTUI}}}info" not in elem.attrib


def test_strip_preserves_object_count(tmp_path):
    """Stripping must not delete any rdf:ID-bearing elements."""
    NS_RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"

    def count_ids(path):
        return sum(
            1
            for e in etree.parse(str(path)).iter()
            if isinstance(e.tag, str) and e.get(f"{NS_RDF}ID") is not None
        )

    cleaned = tmp_path / "cleaned.xml"
    strip_pln_extensions(SAMPLE_EQ, cleaned)
    assert count_ids(cleaned) == count_ids(SAMPLE_EQ)


def test_reinject_round_trip(tmp_path):
    """Strip then reinject produces a file where all extensions reappear."""
    cleaned = tmp_path / "cleaned.xml"
    final = tmp_path / "final.xml"

    report = extract_pln_extensions(SAMPLE_EQ)
    strip_pln_extensions(SAMPLE_EQ, cleaned)
    stats = reinject_pln_extensions(cleaned, final, report.extensions)

    assert stats["x_reinjected"] == 26
    assert stats["y_reinjected"] == 26
    assert stats["nhftui_reinjected"] == 16


def test_reinject_preserves_coordinate_values(tmp_path):
    """Reinjected coordinates match the originals bit-for-bit."""
    cleaned = tmp_path / "cleaned.xml"
    final = tmp_path / "final.xml"

    original = extract_pln_extensions(SAMPLE_EQ)
    strip_pln_extensions(SAMPLE_EQ, cleaned)
    reinject_pln_extensions(cleaned, final, original.extensions)

    after = extract_pln_extensions(final)

    assert original.extensions.keys() == after.extensions.keys()
    for mrid, before in original.extensions.items():
        nowx = after.extensions[mrid]
        assert before.x == nowx.x, f"x diverged for {mrid}: {before.x} -> {nowx.x}"
        assert before.y == nowx.y, f"y diverged for {mrid}: {before.y} -> {nowx.y}"
        assert before.nhftui_info == nowx.nhftui_info


def test_round_trip_preserves_plnnmm_provenance_properties(tmp_path):
    """POC generator metadata must not be silently dropped by cimpy."""
    source = tmp_path / "source.xml"
    cleaned = tmp_path / "cleaned.xml"
    final = tmp_path / "final.xml"
    ns_plnnmm = "http://pln.co.id/nmm/poc#"
    rdf_id = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID"

    tree = etree.parse(str(SAMPLE_EQ))
    owner = next(elem for elem in tree.iter() if elem.get(rdf_id))
    child = etree.SubElement(owner, f"{{{ns_plnnmm}}}confidence")
    child.text = "SLD_DERIVED"
    tree.write(str(source), encoding="UTF-8", xml_declaration=True)

    report = extract_pln_extensions(source)
    assert report.plnnmm_properties == 1
    strip_pln_extensions(source, cleaned)
    assert not etree.parse(str(cleaned)).findall(f".//{{{ns_plnnmm}}}confidence")

    stats = reinject_pln_extensions(cleaned, final, report.extensions)
    assert stats["plnnmm_reinjected"] == 1
    restored = etree.parse(str(final)).find(f".//{{{ns_plnnmm}}}confidence")
    assert restored is not None
    assert restored.text == "SLD_DERIVED"
