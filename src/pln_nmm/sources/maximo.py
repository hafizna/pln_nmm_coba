"""Read a PST/MxLoader inventory without inferring electrical connectivity.

Source identities are scoped by site. All source fields are retained with their
sheet/row; primary asset records are not collapsed into three-phase equipment.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
import re

from openpyxl import load_workbook

from ..model.identity import stable_id

PRIMARY = {
    "Circuit Breaker", "Disconnecting Switch", "Current Transformer",
    "Potential Transformer", "Lightning Arrester", "Trafo", "Reactor",
    "Neutral Grounding Resistance",
}


def text(value):
    return "" if value is None else str(value).strip()


def read_rows(ws):
    """MxLoader headers are row 2; retain nonempty unnamed fields explicitly."""
    headers = next(ws.iter_rows(min_row=2, max_row=2, values_only=True))
    result = []
    for number, values in enumerate(ws.iter_rows(min_row=3, values_only=True), 3):
        if not any(v is not None for v in values):
            continue
        raw = {text(h) if h is not None else f"_column_{i + 1}": v
               for i, (h, v) in enumerate(zip(headers, values))
               if h is not None or v is not None}
        result.append({"sheet": ws.title, "row": number, "raw": raw})
    return result


def unique_index(records, field):
    result = {}
    for record in records:
        raw = record["raw"]
        key = (text(raw.get("SITEID")), text(raw.get(field)))
        if not all(key):
            raise ValueError(f"Missing {field}/SITEID at {record['sheet']}:{record['row']}")
        if key in result:
            raise ValueError(f"Duplicate source key {key} in {record['sheet']}")
        result[key] = record
    return result


def candidate_bay_type(name):
    """Label a candidate from text, never assign a switching template."""
    name = name.upper()
    if "GEDUNG" in name:
        return None
    if "KOPEL" in name:
        return "KOPEL"
    if "BUS SECTION" in name:
        return "BUS_SECTION"
    if "TRAFO" in name:
        return "TRAFO"
    if "BAY" in name:
        return None  # Bay alone does not establish line/generator/shunt type.
    return None


def reconcile_inventory(gis, locations, assets, sites):
    """Join only explicit same-site keys; retain unresolved assets as findings."""
    gi_index = unique_index(gis, "LOCATION")
    loc_index = unique_index(locations, "LOCATION")
    unique_index(assets, "ASSETNUM")
    result = {"gis": [], "locations": [], "assets": [], "findings": []}
    used_gis, used_locations = set(), set()
    excluded = Counter()
    for record in assets:
        raw = record["raw"]
        site, loc = text(raw.get("SITEID")), text(raw.get("LOCATION"))
        if site not in sites:
            excluded["other_site"] += 1
            continue
        location = loc_index.get((site, loc))
        gi_key = (site, text(location["raw"].get("PARENT"))) if location else None
        gi = gi_index.get(gi_key)
        if not gi:
            excluded["not_joined_to_gi"] += 1
            if raw.get("GROUPTYPE") in {"Peralatan Gardu Induk", "Peralatan Proteksi"}:
                result["findings"].append({"kind": "UNRESOLVED_GI_ASSET", **record})
            continue
        used_gis.add(gi_key)
        used_locations.add((site, loc))
        kind = text(raw.get("ASSETTYPE"))
        scope = "PRIMARY" if kind in PRIMARY else (
            "PROTECTION" if raw.get("GROUPTYPE") == "Peralatan Proteksi" else "AUXILIARY")
        result["assets"].append({
            **record, "id": stable_id("MAXIMO", site, "ASSET", text(raw["ASSETNUM"])),
            "gi_id": stable_id("MAXIMO", site, "LOCATION", gi_key[1]),
            "location_id": stable_id("MAXIMO", site, "LOCATION", loc),
            "scope": scope, "normal_open": None, "scenario_open": None,
        })
        if scope == "PRIMARY" and "GEDUNG" in text(location["raw"].get("DESCRIPTION")).upper():
            result["findings"].append({"kind": "PRIMARY_IN_BUILDING", **record})
    for key in sorted(used_gis):
        record = gi_index[key]
        result["gis"].append({**record, "id": stable_id("MAXIMO", key[0], "LOCATION", key[1])})
    for key in sorted(used_locations):
        record = loc_index[key]
        result["locations"].append({
            **record, "id": stable_id("MAXIMO", key[0], "LOCATION", key[1]),
            "gi_id": stable_id("MAXIMO", key[0], "LOCATION", text(record['raw']['PARENT'])),
            "candidate_type": candidate_bay_type(text(record['raw'].get('DESCRIPTION'))),
        })
    for key, record in gi_index.items():
        if key[0] in sites and key not in used_gis:
            result["findings"].append({"kind": "UNREFERENCED_GI_LOCATION", **record})
    names = defaultdict(list)
    for key, record in gi_index.items():
        if key[0] in sites:
            names[(key[0], text(record['raw'].get('DESCRIPTION')))].append(record)
    for matches in names.values():
        if len(matches) > 1:
            for record in matches:
                result["findings"].append({"kind": "SAME_NAME_DIFFERENT_ID", **record})
    result["counts"] = {
        "source_assets": len(assets), "joined_assets": len(result['assets']),
        "gis": len(result['gis']), "used_locations": len(result['locations']),
        "asset_scope": dict(Counter(a['scope'] for a in result['assets'])),
        "excluded": dict(excluded),
    }
    return result


def read_maximo(path, sites=("66131", "66132")):
    path = Path(path)
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        result = reconcile_inventory(
            read_rows(workbook['Locations']), read_rows(workbook['Locations_Bay']),
            read_rows(workbook['Assets_BBL_T&S']), set(sites),
        )
    finally:
        workbook.close()
    result['source'] = {'path': str(path.resolve()), 'sha256': sha256(path.read_bytes()).hexdigest()}
    result['stage'] = 'INVENTORY_ONLY'
    return result
