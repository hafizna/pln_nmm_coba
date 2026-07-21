"""Tests for tolerant SLD extraction."""

from pathlib import Path

from pln_nmm.sld import extract_sld_model


FIXTURES = Path(__file__).parent / "fixtures"
SMALL = FIXTURES / "sample_EQ.xml"
LARGE = FIXTURES / "CIM_sample-db_userdef_python.xml"


def test_sld_extracts_visible_equipment_from_small_fixture():
    model = extract_sld_model(SMALL)
    classes = {node.cim_class for node in model.nodes}

    assert "BusbarSection" in classes
    assert "PowerTransformer" in classes
    assert model.terminal_count == 18
    assert model.connectivity_node_count == 16
    assert any(node.has_coordinates for node in model.nodes)
    assert len(model.edges) == 18
    assert any(node.cim_class == "ConnectivityNode" and not node.visible for node in model.nodes)


def test_sld_extracts_large_fixture_without_cimpy():
    model = extract_sld_model(LARGE)

    assert model.equipment_count > 0
    assert model.terminal_count > 0
    assert model.connectivity_node_count > 0
    assert all(node.source in {"plnicp", "auto", "derived"} for node in model.nodes)
    assert any(node.cim_class == "ConnectivityNode" and not node.visible for node in model.nodes)
