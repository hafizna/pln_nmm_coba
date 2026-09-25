"""Tests for the SLD engine adapter and workbook reconciliation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from pln_nmm.sources import load_handoff, read_workbook, reconcile
from pln_nmm.sources.sld_engine import (
    BUSBAR_CONFIG_MAP,
    confidence_band,
    load_db,
    phi_for,
)
from pln_nmm.sources.reconcile import normalise_gi

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "sources" / "sld_engine" / "ss_bali_ingest.json"


@pytest.fixture(scope="module")
def evidence():
    return load_handoff(HANDOFF)


@pytest.fixture(scope="module")
def workbook(tmp_path_factory):
    out = tmp_path_factory.mktemp("wb") / "wb.xlsx"
    subprocess.run(
        [sys.executable, str(REPO / "scripts" / "build_workbook_template.py"), str(out)],
        check=True,
        capture_output=True,
    )
    return read_workbook(out)


# --- vocabulary mapping -----------------------------------------------------


def test_breaker_and_half_maps_to_one_half_cb():
    """GIS Celukan Bawang: the arrangement where the centre CB is shared."""
    assert BUSBAR_CONFIG_MAP["BREAKER_AND_HALF"] == "ONE_HALF_CB"


def test_unknown_busbar_config_maps_to_none_not_double():
    """Absence of evidence must not become evidence of a double busbar."""
    assert BUSBAR_CONFIG_MAP["UNKNOWN"] is None


def test_phi_from_circuit_count():
    assert phi_for(1) == "SINGLE"
    assert phi_for(2) == "DOUBLE"
    assert phi_for(4) == "MULTI"
    assert phi_for(None) is None


def test_single_phi_flag_wins_over_count():
    """The engine derives single_phi from the drawing; trust it over a count."""
    assert phi_for(2, single_phi=True) == "SINGLE"


def test_sld_evidence_is_never_verified():
    """Tracing a drawing is not verification; only a person verifies."""
    assert confidence_band(1.0) != "VERIFIED"
    assert confidence_band(0.8) == "INFERRED"
    assert confidence_band(None) == "UNKNOWN"


# --- handoff loading --------------------------------------------------------


def test_handoff_loads_bali_subsystem(evidence):
    assert "Bali" in (evidence.subsystem or "")
    assert len(evidence.gis) == 21
    assert len(evidence.generators) == 6
    assert len(evidence.corridors) == 31


def test_handoff_carries_source_reference(evidence):
    assert evidence.source_ref and "Kerawanan" in evidence.source_ref
    assert evidence.effective_date == "2026-06-30"


def test_handoff_records_carry_confidence(evidence):
    for g in evidence.gis:
        assert g.confidence in {"VERIFIED", "INFERRED", "ASSUMED", "UNKNOWN"}
        assert g.raw_confidence is not None


def test_handoff_states_it_is_not_final(evidence):
    """The Bali SLD still needs correcting; that must travel with the data."""
    joined = " ".join(evidence.caveats).lower()
    assert "belum final" in joined
    assert "template" in joined


def test_handoff_supplies_no_switchgear(evidence):
    """Bays, busbars, CB and PMS still come from templates, not from here."""
    assert all(g.skema_busbar is None for g in evidence.gis)


def test_generators_reference_their_outlet(evidence):
    keys = evidence.gi_keys()
    for gen in evidence.generators:
        assert gen.outlet_gi in keys


# --- reconciliation ---------------------------------------------------------


def test_normalise_strips_facility_prefix():
    assert normalise_gi("GI Gilimanuk") == "GILIMANUK"
    assert normalise_gi("GIS Celukan Bawang") == "CELUKAN BAWANG"
    assert normalise_gi("PADANG_SAMBIAN") == "PADANG SAMBIAN"


def test_reconciliation_matches_most_of_bali(evidence, workbook):
    rep = reconcile(evidence, workbook)
    assert rep.gi_matched >= 19
    assert rep.corridor_matched >= 20


def test_reconciliation_reports_rather_than_resolves(evidence, workbook):
    """Disagreement is a finding for a person, never silently picked."""
    rep = reconcile(evidence, workbook)
    for f in rep.conflicts:
        assert "vs" in f.detail


def test_reconciliation_surfaces_corridors_missing_from_workbook(evidence, workbook):
    rep = reconcile(evidence, workbook)
    only_sld = rep.of_kind("ONLY_SLD")
    assert only_sld, "bukti SLD engine seharusnya menambah ruas baru"


def test_reconciliation_does_not_mutate_the_workbook(evidence, workbook):
    before = len(workbook.rows("04_SAMBUNGAN"))
    reconcile(evidence, workbook)
    assert len(workbook.rows("04_SAMBUNGAN")) == before


# --- SQLite path ------------------------------------------------------------

MANTAPS = Path("C:/Users/hafizna.fadhli/Downloads/mantaps-topology-engine/mantaps.db")


@pytest.mark.skipif(not MANTAPS.exists(), reason="mantaps.db tidak tersedia")
def test_sqlite_loads_read_only_and_reports_gaps():
    ev = load_db(MANTAPS)
    assert ev.gis and ev.corridors
    joined = " ".join(ev.caveats).lower()
    # bus_section and device are empty upstream; that must be stated.
    assert "kosong" in joined
