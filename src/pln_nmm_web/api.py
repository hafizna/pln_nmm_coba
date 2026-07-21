"""FastAPI app for local SLD-first inspection."""

from __future__ import annotations

import tempfile
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pln_nmm import (
    compute_diagnostics,
    derive_topology,
    diagnose_pln_eq,
    extract_pln_extensions,
    import_pln_eq,
)
from pln_nmm.diagnostics import summarize_top_placeholders
from pln_nmm.sld import extract_sld_model
from pln_nmm.topology import TopologyModel


app = FastAPI(title="PLN NMM Local SLD API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.post("/api/inspect")
async def inspect_cim(file: UploadFile = File(...)) -> JSONResponse:
    suffix = Path(file.filename or "model.xml").suffix or ".xml"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        return JSONResponse(_inspect_xml_payload(tmp_path, filename=file.filename, source_mode="uploaded_cim"))
    finally:
        tmp_path.unlink(missing_ok=True)


def _inspect_xml_payload(xml_path: Path, *, filename: str | None, source_mode: str) -> dict:
    extensions = extract_pln_extensions(xml_path)
    diagnostics = diagnose_pln_eq(xml_path)
    sld = extract_sld_model(xml_path)
    topology_payload, topology_diag = _try_build_topology(xml_path)
    diagnostics_payload = {
        "placeholder_count": len(diagnostics.placeholders),
        "blocking_semantic_import": diagnostics.has_blocking_placeholders,
        "top_placeholder_fields": [
            {"field": field, "count": count}
            for field, count in summarize_top_placeholders(diagnostics, limit=12)
        ],
    }

    return {
        "source_mode": source_mode,
        "file": {
            "name": filename,
            "size": xml_path.stat().st_size,
        },
        "extensions": {
            "total": len(extensions.extensions),
            "x": extensions.elements_with_x,
            "y": extensions.elements_with_y,
            "nhftui": extensions.elements_with_nhftui,
            "id_mrid_mismatch": extensions.elements_with_id_mrid_mismatch,
        },
        "diagnostics": diagnostics_payload,
        "sld": {
            "nodes": [asdict(node) for node in sld.nodes],
            "edges": [asdict(edge) for edge in sld.edges],
            "equipment_count": sld.equipment_count,
            "terminal_count": sld.terminal_count,
            "connectivity_node_count": sld.connectivity_node_count,
        },
        "topology": topology_payload,
        "topology_diagnostics": topology_diag,
        "gap_workbench": _build_gap_workbench(diagnostics_payload, topology_diag),
        "source_mapping": _source_mapping_payload(),
    }


def _try_build_topology(xml_path: Path) -> tuple[dict | None, dict | None]:
    """
    Run cimpy import → derive_topology → diagnostics.

    Returns (None, None) if cimpy can't parse the file (placeholder-template
    XMLs raise ValueError on float coercion). The frontend falls back to the
    flat sld view in that case.
    """
    try:
        result = import_pln_eq(xml_path)
    except (ValueError, KeyError, AttributeError):
        return None, None

    model = derive_topology(result.topology)
    diag = compute_diagnostics(model)
    return _serialize_topology(model), asdict(diag)


def _serialize_topology(model: TopologyModel) -> dict:
    return {
        "substations": [
            {
                "id": ss.id,
                "name": ss.name,
                "transformer_ids": list(ss.transformer_ids),
                "voltage_levels": [
                    {
                        "id": vl.id,
                        "name": vl.name,
                        "nominal_kv": vl.nominal_kv,
                        "busbar_ids": list(vl.busbar_ids),
                        "bays": [
                            {
                                "id": bay.id,
                                "busbar_id": bay.busbar_id,
                                "head_cn_id": bay.head_cn_id,
                                "leaf_kind": bay.leaf_kind,
                                "items": [asdict(item) for item in bay.items],
                            }
                            for bay in vl.bays
                        ],
                    }
                    for vl in ss.voltage_levels
                ],
            }
            for ss in model.substations
        ],
        "orphan_equipment_ids": list(model.orphan_equipment_ids),
    }


def _build_gap_workbench(
    diagnostics: dict,
    topology_diag: dict | None,
) -> list[dict]:
    rows: list[dict] = []
    field_labels = {
        "ACLineSegment.r": ("Line Data", "resistansi saluran", "PST/line parameter sheet"),
        "ACLineSegment.x": ("Line Data", "reaktansi saluran", "PST or confirmed physical line data"),
        "ACLineSegment.bch": ("Line Data", "line charging susceptance", "PST or network study source"),
        "ACLineSegment.gch": ("Line Data", "line charging conductance", "PST or network study source"),
        "Conductor.length": ("Line Data", "panjang penghantar", "SLD/PST/line asset registry"),
        "PowerTransformerEnd.ratedS": ("Transformer", "kapasitas trafo MVA", "SLD/nameplate/asset registry"),
        "PowerTransformerEnd.ratedU": ("Transformer", "tegangan nominal winding", "SLD/nameplate/asset registry"),
        "EnergyConsumer.pfixed": ("Load", "beban aktif tetap", "load profile or manual forecast"),
        "EnergyConsumer.qfixed": ("Load", "beban reaktif tetap", "load profile or manual forecast"),
    }

    for item in diagnostics.get("top_placeholder_fields", []):
        field = item["field"]
        area, label, source = field_labels.get(field, ("CIM Field", field, "manual engineering input"))
        rows.append(
            {
                "id": f"placeholder:{field}",
                "severity": "blocker",
                "area": area,
                "cim_field": field,
                "label": label,
                "count": item["count"],
                "source_candidate": source,
                "confidence": "needs mapping",
                "next_action": "Map source field, then approve before semantic CIM import.",
            }
        )

    if topology_diag:
        if topology_diag.get("bays_without_switches", 0) > 0:
            rows.append(
                {
                    "id": "topology:bays_without_switches",
                    "severity": "warning",
                    "area": "SLD/Topology",
                    "cim_field": "Bay switching chain",
                    "label": "bay tanpa PMT/PMS di source CIM",
                    "count": topology_diag["bays_without_switches"],
                    "source_candidate": "SLD PDF/VSD validation",
                    "confidence": "review",
                    "next_action": "Confirm whether switching equipment is intentionally schematic-only.",
                }
            )
        if topology_diag.get("open_bays", 0) > 0:
            rows.append(
                {
                    "id": "topology:open_bays",
                    "severity": "warning",
                    "area": "SLD/Topology",
                    "cim_field": "Terminal.ConnectivityNode",
                    "label": "bay chain berhenti sebelum leaf equipment",
                    "count": topology_diag["open_bays"],
                    "source_candidate": "recent CIM/XML or SLD VSD",
                    "confidence": "review",
                    "next_action": "Check missing terminal/connectivity-node continuation.",
                }
            )

    if not rows:
        rows.append(
            {
                "id": "status:no_blocking_gap",
                "severity": "ok",
                "area": "Readiness",
                "cim_field": "-",
                "label": "tidak ada blocker otomatis terdeteksi",
                "count": 0,
                "source_candidate": "current file",
                "confidence": "ready for review",
                "next_action": "Continue SLD review and compare with field evidence.",
            }
        )
    return rows


def _source_mapping_payload() -> list[dict]:
    return [
        {
            "source": "Recent CIM/XML",
            "records": "uploaded file",
            "status": "active",
            "fills": "existing EQ objects, terminals, connectivity nodes, PLN diagram coordinates",
            "parser": "src/pln_nmm/sld.py + diagnostics.py",
        },
        {
            "source": "SLD PDF/VSD",
            "records": "engineering evidence",
            "status": "candidate evidence",
            "fills": "actual SLD station scope, endpoint candidates, visual validation backlog",
            "parser": "manual review",
        },
    ]
