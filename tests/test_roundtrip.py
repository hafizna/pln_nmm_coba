"""End-to-end tests: import through cimpy, export, verify integrity."""

from pathlib import Path

import pytest
from lxml import etree

from pln_nmm import (
    export_pln_eq,
    extract_pln_extensions,
    import_pln_eq,
)
from pln_nmm.exporter import _normalize_cimpy_xml_encoding


FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_EQ = FIXTURES / "sample_EQ.xml"

NS_RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"


def test_normalizes_legacy_bytes_in_nominally_utf8_cimpy_output(tmp_path):
    """Spreadsheet punctuation exported as CP-1252 becomes valid UTF-8."""
    output = tmp_path / "cimpy.xml"
    output.write_bytes(
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<root><name>Bay \x96 GI Gilimanuk</name></root>'
    )

    assert _normalize_cimpy_xml_encoding(output) is True
    tree = etree.parse(str(output))
    assert tree.findtext("name") == "Bay \N{EN DASH} GI Gilimanuk"
    assert _normalize_cimpy_xml_encoding(output) is False


def _collect_rdf_ids(xml_path: Path) -> set[str]:
    """Return all rdf:ID values (with leading underscore stripped)."""
    return {
        elem.get(f"{NS_RDF}ID").lstrip("_")
        for elem in etree.parse(str(xml_path)).iter()
        if isinstance(elem.tag, str) and elem.get(f"{NS_RDF}ID")
    }


def _class_counts(xml_path: Path) -> dict[str, int]:
    """Count instances of each cim:* class in the file."""
    counts: dict[str, int] = {}
    for elem in etree.parse(str(xml_path)).iter():
        if not isinstance(elem.tag, str):
            continue
        if elem.tag.startswith("{http://iec.ch/TC57/2013/CIM-schema-cim16#}"):
            local = elem.tag.split("}", 1)[1]
            # Skip property elements (X.Y form). Real classes are top-level
            # and never contain a dot in their local name.
            if "." not in local:
                counts[local] = counts.get(local, 0) + 1
    return counts


def test_import_yields_expected_topology():
    """All known cimpy-resolvable objects appear in the topology dict."""
    result = import_pln_eq(SAMPLE_EQ)
    counts = result.class_counts()

    # Spot-check the headline classes from the data exploration phase.
    assert counts["Terminal"] == 18
    assert counts["BusbarSection"] == 1
    assert counts["PowerTransformer"] == 2
    assert counts["PowerTransformerEnd"] == 4
    assert counts["ACLineSegment"] == 2
    assert counts["Substation"] == 10
    assert counts["VoltageLevel"] == 12


def test_import_extracts_extensions_to_side_table():
    """Extension extraction should run as part of import_pln_eq."""
    result = import_pln_eq(SAMPLE_EQ)
    assert len(result.extensions_report.extensions) == 26
    assert result.extensions_report.elements_with_nhftui == 16


def test_export_preserve_mode_keeps_all_extensions(tmp_path):
    """preserve_extensions mode reattaches every plnicp/nhftui datum."""
    out = tmp_path / "out.xml"
    result = import_pln_eq(SAMPLE_EQ)
    stats = export_pln_eq(result, out, mode="preserve_extensions")

    assert stats["x_reinjected"] == 26
    assert stats["y_reinjected"] == 26
    assert stats["nhftui_reinjected"] == 16

    # Re-extract from the output and confirm parity with the input.
    after = extract_pln_extensions(out)
    before = result.extensions_report
    assert after.elements_with_x == before.elements_with_x
    assert after.elements_with_y == before.elements_with_y
    assert after.elements_with_nhftui == before.elements_with_nhftui


def test_export_standard_cgmes_mode_drops_extensions(tmp_path):
    """standard_cgmes mode emits clean CGMES with no PLN extensions."""
    out = tmp_path / "out.xml"
    result = import_pln_eq(SAMPLE_EQ)
    export_pln_eq(result, out, mode="standard_cgmes")

    after = extract_pln_extensions(out)
    assert after.elements_with_x == 0
    assert after.elements_with_y == 0
    assert after.elements_with_nhftui == 0


def test_round_trip_preserves_all_rdf_ids(tmp_path):
    """No element gets dropped or invented during the round trip."""
    out = tmp_path / "out.xml"
    result = import_pln_eq(SAMPLE_EQ)
    export_pln_eq(result, out, mode="preserve_extensions")

    before = _collect_rdf_ids(SAMPLE_EQ)
    after = _collect_rdf_ids(out)
    assert before == after, f"differing rdf:IDs: {before.symmetric_difference(after)}"


def test_round_trip_preserves_class_distribution(tmp_path):
    """Class-by-class counts match between input and output."""
    out = tmp_path / "out.xml"
    result = import_pln_eq(SAMPLE_EQ)
    export_pln_eq(result, out, mode="preserve_extensions")

    before = _class_counts(SAMPLE_EQ)
    after = _class_counts(out)
    # cimpy has its own internal nuances around BaseVoltage emission;
    # we tolerate small variances in container-only metadata classes.
    for cls in [
        "Terminal",
        "BusbarSection",
        "PowerTransformer",
        "PowerTransformerEnd",
        "ACLineSegment",
        "Disconnector",
        "SynchronousMachine",
        "ConformLoad",
        "Substation",
        "VoltageLevel",
        "ConnectivityNode",
    ]:
        assert before.get(cls, 0) == after.get(cls, 0), (
            f"class {cls} count diverged: {before.get(cls, 0)} -> {after.get(cls, 0)}"
        )


def test_round_trip_preserves_coordinate_precision(tmp_path):
    """Float coordinates survive the cimpy round trip with full precision."""
    out = tmp_path / "out.xml"
    result = import_pln_eq(SAMPLE_EQ)
    export_pln_eq(result, out, mode="preserve_extensions")

    before = result.extensions_report.extensions
    after = extract_pln_extensions(out).extensions

    common = set(before.keys()) & set(after.keys())
    assert len(common) == len(before)

    for mrid in common:
        assert before[mrid].x == after[mrid].x, f"x diverged at {mrid}"
        assert before[mrid].y == after[mrid].y, f"y diverged at {mrid}"
        assert before[mrid].nhftui_info == after[mrid].nhftui_info
