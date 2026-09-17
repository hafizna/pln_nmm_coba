"""Read topology evidence from the SLD engine (mantaps-topology-engine).

The SLD engine is the source of truth for inter-GI topology: which substations
exist, which corridors join them, how many circuits each carries. This module
reads that evidence and hands it to the model layer. It never writes back.

Two input shapes are supported, because the engine produces both:

* **handoff JSON** (`SLD_HANDOFF_JSON`) -- what the engine exports for one
  subsystem. This is what exists for Bali.
* **SQLite** (`mantaps.db`) -- the engine's own database. Richer, but at the
  time of writing it holds Jakarta-Banten (JBB), not Bali.

What the SLD engine does NOT provide, and must still come from bay templates:
bus sections, breakers and disconnectors. Its `bus_section` and `device` tables
are empty, and `busbar_config` is `UNKNOWN` for most substations. Treat this
module as supplying the corridor graph, not the switchyard.

Every record carries its confidence forward. Bali handoff evidence is traced
from Buku Kerawanan Appendix-5 at confidence 0.8 and is explicitly marked
"verify circuit label against native SLD" -- so nothing from here may be
presented as verified.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

# --- vocabulary mapping -----------------------------------------------------

# The SLD engine's busbar vocabulary onto ours. Note BREAKER_AND_HALF ->
# ONE_HALF_CB: that is the GIS Celukan Bawang arrangement, where the centre
# breaker is shared between two circuits.
BUSBAR_CONFIG_MAP = {
    "SINGLE": "SINGLE",
    "DOUBLE_1CB": "DOUBLE",
    "DOUBLE_SECTIONALIZED": "DOUBLE_SECTION",
    "BREAKER_AND_HALF": "ONE_HALF_CB",
    "UNKNOWN": None,  # absence of evidence, not evidence of DOUBLE
}

# Circuit count -> the operational "phi" shorthand.
PHI_BY_COUNT = {1: "SINGLE", 2: "DOUBLE"}


def phi_for(circuit_count: int | None, single_phi: bool | None = None) -> str | None:
    """Corridor phi from its circuit count.

    `single_phi` is the engine's own flag; it wins when set, because the engine
    derives it from the drawing rather than from a count that may be unfilled.
    """
    if single_phi:
        return "SINGLE"
    if circuit_count is None:
        return None
    if circuit_count >= 3:
        return "MULTI"
    return PHI_BY_COUNT.get(int(circuit_count))


def confidence_band(value: float | None) -> str:
    """Float confidence -> our controlled vocabulary.

    Deliberately conservative: SLD engine evidence is traced from drawings and
    is never VERIFIED here. Verification is a human act against native SLD.
    """
    if value is None:
        return "UNKNOWN"
    if value >= 0.95:
        return "INFERRED"
    if value >= 0.6:
        return "INFERRED"
    if value > 0:
        return "ASSUMED"
    return "UNKNOWN"


# --- records ----------------------------------------------------------------


@dataclass
class GiRecord:
    key: str
    name: str
    kind: str  # GI / GIS / GITET / KTT
    voltage_kv: float | None
    skema_busbar: str | None
    confidence: str
    raw_confidence: float | None
    status: str | None
    uit: str | None = None
    note: str | None = None


@dataclass
class CorridorRecord:
    from_gi: str
    to_gi: str
    circuit_type: str | None
    circuit_count: int | None
    phi: str | None
    unit_no: str | None
    confidence: str
    raw_confidence: float | None
    status: str | None
    note: str | None = None
    length_km: float | None = None


@dataclass
class GeneratorRecord:
    key: str
    name: str
    outlet_gi: str | None
    confidence: str
    raw_confidence: float | None
    status: str | None


@dataclass
class SldEvidence:
    """What the SLD engine knows, with its provenance attached."""

    source: str
    source_ref: str | None = None
    effective_date: str | None = None
    subsystem: str | None = None
    gis: list[GiRecord] = field(default_factory=list)
    corridors: list[CorridorRecord] = field(default_factory=list)
    generators: list[GeneratorRecord] = field(default_factory=list)
    caveats: list[str] = field(default_factory=list)

    def gi_keys(self) -> set[str]:
        return {g.key for g in self.gis}

    def corridor_pairs(self) -> set[tuple[str, str]]:
        """Undirected corridor pairs, so A-B and B-A compare equal."""
        return {tuple(sorted((c.from_gi, c.to_gi))) for c in self.corridors}

    def __str__(self) -> str:
        lines = [
            f"sumber        : {self.source}",
            f"subsistem     : {self.subsystem or '-'}",
            f"dokumen       : {self.source_ref or '-'}",
            f"berlaku       : {self.effective_date or '-'}",
            f"GI/GIS        : {len(self.gis)}",
            f"ruas          : {len(self.corridors)} "
            f"({len(self.corridor_pairs())} pasangan unik)",
            f"pembangkit    : {len(self.generators)}",
        ]
        unknown = sum(1 for g in self.gis if g.skema_busbar is None)
        if unknown:
            lines.append(
                f"skema busbar  : {len(self.gis) - unknown}/{len(self.gis)} diketahui "
                f"({unknown} UNKNOWN -- bukan bukti double busbar)"
            )
        for c in self.caveats:
            lines.append(f"  [!] {c}")
        return "\n".join(lines)


# --- handoff JSON -----------------------------------------------------------

_GI_TYPES = {"GI", "GIS", "GITET", "KTT", "SWITCHING", "GISTET"}


def load_handoff(path: str | Path) -> SldEvidence:
    """Read an SLD_HANDOFF_JSON export for one subsystem."""
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))

    meta = data.get("meta", {})
    sub = data.get("subsystem", {})
    ev = SldEvidence(
        source=f"handoff:{p.name}",
        source_ref=meta.get("source_ref"),
        effective_date=meta.get("effective_date"),
        subsystem=sub.get("name") or sub.get("code"),
    )

    for obj in data.get("objects", []):
        kind = str(obj.get("object_type") or "")
        conf = obj.get("confidence")
        if kind in _GI_TYPES:
            ev.gis.append(
                GiRecord(
                    key=str(obj["external_key"]),
                    name=str(obj.get("site_name") or obj.get("raw_label") or ""),
                    kind=kind,
                    voltage_kv=obj.get("voltage_hv_kv"),
                    # The handoff carries no busbar arrangement at all.
                    skema_busbar=None,
                    confidence=confidence_band(conf),
                    raw_confidence=conf,
                    status=obj.get("status_hint"),
                )
            )
        elif kind == "GENERATING_UNIT":
            ev.generators.append(
                GeneratorRecord(
                    key=str(obj["external_key"]),
                    name=str(obj.get("raw_label") or obj["external_key"]),
                    outlet_gi=obj.get("outlet_key"),
                    confidence=confidence_band(conf),
                    raw_confidence=conf,
                    status=obj.get("status_hint"),
                )
            )

    for con in data.get("connections", []):
        conf = con.get("confidence")
        count = con.get("circuit_count")
        ev.corridors.append(
            CorridorRecord(
                from_gi=str(con["from_external_key"]),
                to_gi=str(con["to_external_key"]),
                circuit_type=con.get("circuit_type_hint"),
                circuit_count=count,
                phi=phi_for(count),
                unit_no=con.get("unit_no"),
                confidence=confidence_band(conf),
                raw_confidence=conf,
                status=con.get("status_hint"),
                note=con.get("note"),
            )
        )

    ev.caveats.append(
        "Handoff ini belum final: struktur SLD per-GI dan relasi antar-GI masih "
        "perlu dikoreksi terhadap SLD native. Jangan perlakukan sebagai VERIFIED."
    )
    ev.caveats.append(
        "Tidak memuat susunan bay, busbar, CB atau PMS -- itu tetap dari template."
    )
    return ev


# --- SQLite -----------------------------------------------------------------


def load_db(path: str | Path, *, subsystem_code: str | None = None) -> SldEvidence:
    """Read the SLD engine's own SQLite database.

    Read-only: opened via a file URI with `mode=ro` so a bug here can never
    touch the engine's data.
    """
    p = Path(path)
    uri = f"file:{p.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        ev = SldEvidence(source=f"sqlite:{p.name}")

        subs = {}
        for row in conn.execute(
            "SELECT id, code, name, substation_type, voltage_kv, uit, status,"
            " busbar_config, busbar_note, confidence"
            " FROM substation WHERE active = 1"
        ):
            raw_cfg = row["busbar_config"]
            rec = GiRecord(
                key=row["code"],
                name=row["name"],
                kind=row["substation_type"],
                voltage_kv=row["voltage_kv"],
                skema_busbar=BUSBAR_CONFIG_MAP.get(raw_cfg),
                confidence=confidence_band(row["confidence"]),
                raw_confidence=row["confidence"],
                status=row["status"],
                uit=row["uit"],
                note=row["busbar_note"],
            )
            subs[row["id"]] = rec
            ev.gis.append(rec)

        for row in conn.execute(
            "SELECT from_substation_id, to_substation_id, circuit_type,"
            " circuit_count, single_phi, length_km, status, note, confidence"
            " FROM circuit WHERE active = 1"
        ):
            a = subs.get(row["from_substation_id"])
            b = subs.get(row["to_substation_id"])
            if a is None or b is None:
                continue
            ev.corridors.append(
                CorridorRecord(
                    from_gi=a.key,
                    to_gi=b.key,
                    circuit_type=row["circuit_type"],
                    circuit_count=row["circuit_count"],
                    phi=phi_for(row["circuit_count"], bool(row["single_phi"])),
                    unit_no=None,
                    confidence=confidence_band(row["confidence"]),
                    raw_confidence=row["confidence"],
                    status=row["status"],
                    note=row["note"],
                    length_km=row["length_km"],
                )
            )

        for row in conn.execute(
            "SELECT code, name, outlet_substation_id, status, confidence"
            " FROM generating_unit WHERE active = 1"
        ):
            outlet = subs.get(row["outlet_substation_id"])
            ev.generators.append(
                GeneratorRecord(
                    key=row["code"],
                    name=row["name"],
                    outlet_gi=outlet.key if outlet else None,
                    confidence=confidence_band(row["confidence"]),
                    raw_confidence=row["confidence"],
                    status=row["status"],
                )
            )

        unknown = sum(1 for g in ev.gis if g.skema_busbar is None)
        if unknown:
            ev.caveats.append(
                f"{unknown} GI tanpa skema busbar. UNKNOWN bukan bukti double "
                "busbar; isi dari SLD atau biarkan kosong."
            )
        for table, what in (("bus_section", "busbar"), ("device", "CB/PMS")):
            n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            if n == 0:
                ev.caveats.append(
                    f"Tabel {table} kosong: {what} tidak tersedia dari SLD engine, "
                    "tetap dibangkitkan dari template bay."
                )
        return ev
    finally:
        conn.close()


def load(path: str | Path, **kwargs) -> SldEvidence:
    """Load whichever shape the path points at."""
    p = Path(path)
    if p.suffix.lower() == ".json":
        return load_handoff(p)
    return load_db(p, **kwargs)
