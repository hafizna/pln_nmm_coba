"""Sanity tests for the bay-derivation topology layer."""

from collections import Counter
from pathlib import Path

from pln_nmm import derive_topology, import_pln_eq

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_EQ = FIXTURES / "sample_EQ.xml"


def test_derive_topology_finds_real_substation():
    """All 10 Substation entries with the same name merge into one group."""
    result = import_pln_eq(SAMPLE_EQ)
    model = derive_topology(result.topology)

    assert len(model.substations) == 1
    ss = model.substations[0]
    assert ss.name == "GI_Gill"

    # After merging, the single group carries every VL from every shard,
    # plus the transformers that were attached to side-substations.
    assert len(ss.voltage_levels) >= 1
    assert len(ss.transformer_ids) == 2  # two PowerTransformers in the file

    # Exactly one VL has a real busbar.
    vl_with_busbar = [vl for vl in ss.voltage_levels if vl.busbar_ids]
    assert len(vl_with_busbar) == 1
    assert vl_with_busbar[0].nominal_kv == 150.0


def test_merge_by_name_off_keeps_shards():
    """Disabling the merge yields the raw cimpy substation count."""
    result = import_pln_eq(SAMPLE_EQ)
    model = derive_topology(result.topology, merge_substations_by_name=False)
    assert len(model.substations) >= 2  # multiple shards in the source file


def test_bay_leaf_kinds_match_known_distribution():
    """The single populated VL has 11 derived bays of the expected kinds."""
    result = import_pln_eq(SAMPLE_EQ)
    model = derive_topology(result.topology)

    bays = [
        bay
        for ss in model.substations
        for vl in ss.voltage_levels
        for bay in vl.bays
    ]
    assert len(bays) == 11

    leaf_counts = Counter(bay.leaf_kind for bay in bays)
    # The known equipment in the sample: 2 lines, 2 transformers,
    # 2 generators, 3 loads, 2 stub disconnectors.
    assert leaf_counts["line"] == 2
    assert leaf_counts["transformer"] == 2
    assert leaf_counts["generator"] == 2
    assert leaf_counts["load"] == 3
    assert leaf_counts["open"] == 2


def test_every_bay_has_items_in_busbar_to_leaf_order():
    """Item order: walk-start (busbar-side) first, leaf last."""
    result = import_pln_eq(SAMPLE_EQ)
    model = derive_topology(result.topology)

    for ss in model.substations:
        for vl in ss.voltage_levels:
            for bay in vl.bays:
                assert len(bay.items) >= 1
                # The leaf item's class should agree with the leaf kind
                # (open bays end on a switch, so we skip them).
                if bay.leaf_kind == "line":
                    assert bay.items[-1].cim_class == "ACLineSegment"
                elif bay.leaf_kind == "transformer":
                    assert bay.items[-1].cim_class == "PowerTransformer"
                elif bay.leaf_kind == "generator":
                    assert bay.items[-1].cim_class in {
                        "SynchronousMachine",
                        "AsynchronousMachine",
                    }
                elif bay.leaf_kind == "load":
                    assert bay.items[-1].cim_class in {
                        "ConformLoad",
                        "NonConformLoad",
                        "EnergyConsumer",
                    }
