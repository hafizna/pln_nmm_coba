"""Tests for pre-cimpy diagnostics on PLN CIM files."""

from pathlib import Path

from pln_nmm import diagnose_pln_eq, import_pln_eq


FIXTURES = Path(__file__).parent / "fixtures"
SMALL = FIXTURES / "sample_EQ.xml"
LARGE = FIXTURES / "CIM_sample-db_userdef_python.xml"


def test_small_fixture_has_no_template_placeholders():
    report = diagnose_pln_eq(SMALL)
    assert report.placeholders == []
    assert not report.has_blocking_placeholders


def test_large_fixture_reports_unresolved_isi_placeholders():
    report = diagnose_pln_eq(LARGE)
    counts = report.placeholder_field_counts()

    assert report.has_blocking_placeholders
    assert counts["ACLineSegment.r"] > 0
    assert counts["ACLineSegment.x"] > 0
    assert counts["Conductor.length"] > 0
    assert all(item.token.startswith("$(Isi_") for item in report.placeholders)


def test_import_result_carries_diagnostics_for_valid_files():
    result = import_pln_eq(SMALL)
    assert result.diagnostics_report.placeholders == []
