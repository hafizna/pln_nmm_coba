"""
Tests parameterized across the small single-substation fixture and the
2.7 MB aggregate fixture (CIM_sample-db_userdef_python.xml). The aggregate
file scales the adapter to 4,353 elements and 637 nhftui:info attributes,
and surfaces a real PLN data-quality pattern: many fields contain
unfilled `$(Isi_*)` placeholder strings instead of numeric values, which
cimpy cannot parse.

The adapter layer is pure XML and tolerates the placeholders. The cimpy
import path does not; that case is documented as xfail below so the
failure mode is recorded rather than silently broken.
"""

from pathlib import Path

import pytest
from lxml import etree

from pln_nmm import import_pln_eq
from pln_nmm.adapter import (
    extract_pln_extensions,
    reinject_pln_extensions,
    strip_pln_extensions,
)

FIXTURES = Path(__file__).parent / "fixtures"
SMALL = FIXTURES / "sample_EQ.xml"
LARGE = FIXTURES / "CIM_sample-db_userdef_python.xml"

NS_RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"


def _count_rdf_ids(path: Path) -> int:
    return sum(
        1
        for e in etree.parse(str(path)).iter()
        if isinstance(e.tag, str) and e.get(f"{NS_RDF}ID")
    )


@pytest.mark.parametrize("fixture", [SMALL, LARGE], ids=["small", "large"])
def test_adapter_round_trip_preserves_extensions(fixture, tmp_path):
    """Extract → strip → reinject yields byte-identical extension data."""
    cleaned = tmp_path / "cleaned.xml"
    final = tmp_path / "final.xml"

    before = extract_pln_extensions(fixture)
    strip_pln_extensions(fixture, cleaned)
    reinject_pln_extensions(cleaned, final, before.extensions)
    after = extract_pln_extensions(final)

    assert before.extensions.keys() == after.extensions.keys()
    for mrid, b in before.extensions.items():
        a = after.extensions[mrid]
        assert b.x == a.x, f"x diverged at {mrid}"
        assert b.y == a.y, f"y diverged at {mrid}"
        assert b.nhftui_info == a.nhftui_info, f"nhftui diverged at {mrid}"


@pytest.mark.parametrize("fixture", [SMALL, LARGE], ids=["small", "large"])
def test_adapter_round_trip_preserves_rdf_id_count(fixture, tmp_path):
    """No element gets dropped or invented during strip+reinject."""
    cleaned = tmp_path / "cleaned.xml"
    final = tmp_path / "final.xml"

    strip_pln_extensions(fixture, cleaned)
    before = extract_pln_extensions(fixture)
    reinject_pln_extensions(cleaned, final, before.extensions)

    assert _count_rdf_ids(fixture) == _count_rdf_ids(final)


def test_large_fixture_baseline_counts():
    """Regression guard for the headline counts on the large fixture."""
    report = extract_pln_extensions(LARGE)
    assert len(report.extensions) == 637
    # The large file is a template — no coordinates were filled in.
    assert report.elements_with_x == 0
    assert report.elements_with_y == 0
    assert report.elements_with_nhftui == 637
    # PLN's id/mrid divergence pattern scales: 9 in the small file, 291 here.
    assert report.elements_with_id_mrid_mismatch == 291


@pytest.mark.xfail(
    raises=ValueError,
    strict=True,
    reason=(
        "Large fixture contains unfilled $(Isi_*) placeholder strings in "
        "float-typed CIM fields (e.g. ACLineSegment.bch). cimpy 1.1.0 has no "
        "hook to tolerate them. Documented limitation, not a regression."
    ),
)
def test_large_fixture_cimpy_import_fails_on_placeholders():
    import_pln_eq(LARGE)
