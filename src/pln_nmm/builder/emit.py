"""Emit CIM16 / CGMES 2.4.15 EQ from an expanded workbook model.

Produces the same object shapes as the Gilimanuk canonical draft, so output
round-trips through the existing adapter unchanged.

Two rules this module exists to enforce:

* Unknown stays unknown. A parameter the workbook left blank is omitted, never
  written as zero. cimpy will refuse such a file on typed import; that refusal
  is correct and is the point.
* Every derived object carries provenance. Nothing generated from a bay
  template can be mistaken for a measured fact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

from .templates import BayExpansion, Node, Switch, busbar_nodes, expand_all, stable_id

NS_CIM = "http://iec.ch/TC57/2013/CIM-schema-cim16#"
NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
NS_MD = "http://iec.ch/TC57/61970-552/ModelDescription/1#"
NS_PLNICP = "http://iconpln.co.id#"
NS_PLNNMM = "http://pln.co.id/nmm/poc#"

# Workbook confidence -> plnnmm:confidence. Derived objects never reach 1.0.
_CONFIDENCE = {
    "VERIFIED": "0.95",
    "INFERRED": "0.70",
    "ASSUMED": "0.50",
    "UNKNOWN": "0.30",
}


@dataclass
class BuildReport:
    counts: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    omitted_parameters: dict[str, int] = field(default_factory=dict)

    def bump(self, key: str, n: int = 1) -> None:
        self.counts[key] = self.counts.get(key, 0) + n

    def omit(self, key: str) -> None:
        self.omitted_parameters[key] = self.omitted_parameters.get(key, 0) + 1

    def __str__(self) -> str:
        lines = ["Objek yang dibangkitkan:"]
        for k in sorted(self.counts):
            lines.append(f"  {self.counts[k]:5d}  {k}")
        if self.omitted_parameters:
            lines.append("")
            lines.append("Parameter dihilangkan karena belum diketahui:")
            for k in sorted(self.omitted_parameters):
                lines.append(f"  {self.omitted_parameters[k]:5d}  {k}")
        if self.warnings:
            lines.append("")
            lines.append(f"Peringatan ({len(self.warnings)}):")
            for w in self.warnings:
                lines.append(f"  [!] {w}")
        return "\n".join(lines)


def _t(tag: str, value, indent: int = 4) -> str:
    """A text element, or nothing when the value is unknown."""
    if value is None or value == "":
        return ""
    return f"{' ' * indent}<{tag}>{escape(str(value))}</{tag}>\n"


def _ref(tag: str, target_id: str, indent: int = 4) -> str:
    return f"{' ' * indent}<{tag} rdf:resource=\"#_{target_id}\"/>\n"


def _num(v):
    return v if isinstance(v, (int, float)) else None


def _provenance(sumber: str | None, confidence: str | None, note: str = "") -> str:
    out = ""
    if sumber:
        out += _t("plnnmm:provenance", sumber)
    if confidence:
        out += _t("plnnmm:confidence", _CONFIDENCE.get(str(confidence), "0.30"))
        out += _t("plnnmm:sourceQuality", confidence)
    out += _t("plnnmm:modelStatus", "DRAFT")
    if note:
        out += _t("plnnmm:mappingNote", note)
    return out


def _identified(obj_id: str, name: str, description: str = "") -> str:
    out = _t("cim:IdentifiedObject.mRID", obj_id)
    out += _t("cim:IdentifiedObject.name", name)
    if description:
        out += _t("cim:IdentifiedObject.description", description)
    return out


class CimBuilder:
    """Assembles CIM EQ XML from workbook rows."""

    def __init__(self, wb, scenario_id: str | None = None):
        self.wb = wb
        self.scenario_id = scenario_id
        self.report = BuildReport()
        self.parts: list[str] = []
        self._base_voltages: dict[float, str] = {}

    # --- containers ------------------------------------------------------

    def _base_voltage(self, kv: float) -> str:
        if kv not in self._base_voltages:
            bv_id = stable_id("BV", str(kv))
            self._base_voltages[kv] = bv_id
            self.parts.append(
                f'  <cim:BaseVoltage rdf:ID="_{bv_id}">\n'
                + _identified(bv_id, f"{kv:g} kV")
                + _t("cim:BaseVoltage.nominalVoltage", f"{kv:g}")
                + "  </cim:BaseVoltage>\n"
            )
            self.report.bump("BaseVoltage")
        return self._base_voltages[kv]

    def _emit_region(self) -> tuple[str, str]:
        geo = stable_id("GEO", "BALI")
        sub = stable_id("SUBGEO", "BALI")
        self.parts.append(
            f'  <cim:GeographicalRegion rdf:ID="_{geo}">\n'
            + _identified(geo, "JAWA MADURA BALI")
            + "  </cim:GeographicalRegion>\n"
        )
        self.parts.append(
            f'  <cim:SubGeographicalRegion rdf:ID="_{sub}">\n'
            + _identified(sub, "SUB SISTEM BALI")
            + _ref("cim:SubGeographicalRegion.Region", geo)
            + "  </cim:SubGeographicalRegion>\n"
        )
        self.report.bump("GeographicalRegion")
        self.report.bump("SubGeographicalRegion")
        return geo, sub

    def _emit_substations(self, sub_region: str) -> dict[str, tuple[str, str]]:
        """One Substation + one VoltageLevel per GI. Returns gi -> (ss, vl)."""
        out: dict[str, tuple[str, str]] = {}
        for row in self.wb.rows("01_GI"):
            gi = str(row["gi_id"])
            ss_id = stable_id("SS", gi)
            vl_id = stable_id("VL", gi, "150")
            bv = self._base_voltage(150.0)

            self.parts.append(
                f'  <cim:Substation rdf:ID="_{ss_id}">\n'
                + _identified(ss_id, str(row.get("gi_nama") or gi))
                + _t("plnnmm:canonicalBusinessId", gi)
                + _t("plnnmm:busbarScheme", row.get("skema_busbar"))
                + _provenance(
                    row.get("busbar_sumber"),
                    row.get("busbar_confidence"),
                    str(row.get("busbar_dok_ref") or ""),
                )
                + _ref("cim:Substation.Region", sub_region)
                + "  </cim:Substation>\n"
            )
            self.parts.append(
                f'  <cim:VoltageLevel rdf:ID="_{vl_id}">\n'
                + _identified(vl_id, f"{row.get('gi_nama') or gi} 150 kV")
                + _ref("cim:VoltageLevel.BaseVoltage", bv)
                + _ref("cim:VoltageLevel.Substation", ss_id)
                + "  </cim:VoltageLevel>\n"
            )
            self.report.bump("Substation")
            self.report.bump("VoltageLevel")
            out[gi] = (ss_id, vl_id)
        return out

    # --- topology --------------------------------------------------------

    def _emit_node(self, node: Node, container: str, gi: str) -> None:
        self.parts.append(
            f'  <cim:ConnectivityNode rdf:ID="_{node.id}">\n'
            + _identified(node.id, node.name)
            + _t("plnnmm:canonicalBusinessId", f"CN-{gi}-{node.role}")
            + _provenance("TEMPLATE", "INFERRED", "Dibangkitkan dari template bay")
            + _ref("cim:ConnectivityNode.ConnectivityNodeContainer", container)
            + "  </cim:ConnectivityNode>\n"
        )
        self.report.bump("ConnectivityNode")

    def _emit_terminal(self, equip_id: str, node_id: str, seq: int, name: str) -> None:
        t_id = stable_id("T", equip_id, str(seq))
        self.parts.append(
            f'  <cim:Terminal rdf:ID="_{t_id}">\n'
            + _identified(t_id, str(seq), name)
            + _t("cim:ACDCTerminal.sequenceNumber", seq)
            + _ref("cim:Terminal.ConductingEquipment", equip_id)
            + _ref("cim:Terminal.ConnectivityNode", node_id)
            + "  </cim:Terminal>\n"
        )
        self.report.bump("Terminal")

    def _emit_switch(self, sw: Switch, container: str) -> None:
        cls = "Breaker" if sw.kind == "BREAKER" else "Disconnector"
        note = (
            "PMT tengah diameter 1-1/2 CB: SATU objek dipakai bersama dua sirkit"
            if sw.shared
            else "Dibangkitkan dari template bay"
        )
        self.parts.append(
            f'  <cim:{cls} rdf:ID="_{sw.id}">\n'
            + _identified(sw.id, sw.name)
            + _t("plnnmm:canonicalBusinessId", f"{sw.bay_id}-{sw.role}")
            + (_t("plnnmm:sharedBreaker", "true") if sw.shared else "")
            + _provenance("TEMPLATE", "INFERRED", note)
            + _ref("cim:Equipment.EquipmentContainer", container)
            + _t("cim:Switch.normalOpen", "true" if sw.normal_open else "false")
            + _t("cim:Switch.retained", "true" if sw.kind == "BREAKER" else "false")
            + f"  </cim:{cls}>\n"
        )
        self.report.bump(cls)
        # Two terminals, in the order the template laid them out.
        self._emit_terminal(sw.id, sw.node_a, 1, sw.name)
        self._emit_terminal(sw.id, sw.node_b, 2, sw.name)

    def _emit_bay(self, exp: BayExpansion, vl_id: str, bay_row: dict) -> str:
        bay_uuid = stable_id("BAY", exp.gi_id, exp.bay_id)
        self.parts.append(
            f'  <cim:Bay rdf:ID="_{bay_uuid}">\n'
            + _identified(bay_uuid, str(bay_row.get("bay_nama") or exp.bay_id))
            + _t("plnnmm:canonicalBusinessId", exp.bay_id)
            + _t("plnnmm:bayTemplate", exp.template_id)
            + _provenance(
                bay_row.get("sumber"),
                bay_row.get("confidence"),
                str(bay_row.get("catatan") or ""),
            )
            + _ref("cim:Bay.VoltageLevel", vl_id)
            + "  </cim:Bay>\n"
        )
        self.report.bump("Bay")
        return bay_uuid

    def _emit_busbars(self, gi: str, skema: str, vl_id: str) -> None:
        for node in busbar_nodes(gi, skema):
            self._emit_node(node, vl_id, gi)
            bb_id = stable_id("BB", gi, node.role)
            self.parts.append(
                f'  <cim:BusbarSection rdf:ID="_{bb_id}">\n'
                + _identified(bb_id, f"BUSBAR {node.role[-1]} {gi} 150 kV")
                + _t("plnnmm:canonicalBusinessId", f"{gi}-{node.role}")
                + _provenance("SLD_P2B", "INFERRED", f"Skema busbar GI: {skema}")
                + _ref("cim:Equipment.EquipmentContainer", vl_id)
                + "  </cim:BusbarSection>\n"
            )
            self.report.bump("BusbarSection")
            self._emit_terminal(bb_id, node.id, 1, f"BUSBAR {gi}")

    # --- electrical equipment -------------------------------------------

    def _emit_lines(self, expansions: dict[str, BayExpansion]) -> None:
        """One ACLineSegment per circuit, attached to its bay's line node."""
        salur = self.wb.index_by("05_SALURAN", "sambungan_id")
        bv = self._base_voltage(150.0)

        for row in self.wb.rows("04_SAMBUNGAN"):
            sid = str(row.get("sambungan_id") or "")
            if not sid:
                continue
            line_id = stable_id("LINE", sid)
            par = salur.get(sid, {})

            body = _identified(
                line_id,
                str(row.get("nama_ruas") or sid),
                f"Sirkit {row.get('sirkit_ke')} dari {row.get('jml_sirkit')}",
            )
            body += _t("plnnmm:canonicalBusinessId", sid)
            body += _t("plnnmm:phi", row.get("phi"))
            body += _t("plnnmm:circuitCount", row.get("jml_sirkit"))
            body += _provenance(
                row.get("sumber"), row.get("confidence"), str(row.get("dok_ref") or "")
            )
            body += _ref("cim:ConductingEquipment.BaseVoltage", bv)

            # Unknown impedance is omitted, never written as zero.
            for col, tag in (
                ("r_ohm", "cim:ACLineSegment.r"),
                ("x_ohm", "cim:ACLineSegment.x"),
                ("b_us", "cim:ACLineSegment.bch"),
                ("panjang_km", "cim:Conductor.length"),
            ):
                v = _num(par.get(col))
                if v is None:
                    self.report.omit(tag)
                else:
                    body += _t(tag, repr(float(v)))

            self.parts.append(
                f'  <cim:ACLineSegment rdf:ID="_{line_id}">\n{body}'
                "  </cim:ACLineSegment>\n"
            )
            self.report.bump("ACLineSegment")

            bay_id = str(row.get("dari_bay") or "")
            exp = expansions.get(bay_id)
            if exp and exp.equipment_node:
                self._emit_terminal(line_id, exp.equipment_node, 1, str(row.get("nama_ruas") or sid))
            else:
                self.report.warnings.append(
                    f"ACLineSegment '{sid}': bay '{bay_id}' tidak punya titik sambung; "
                    "terminal tidak dibuat."
                )

    def _emit_loads(self, gi_vl: dict[str, tuple[str, str]]) -> None:
        """EnergyConsumer per GI load row, for the selected scenario."""
        bv = self._base_voltage(150.0)
        for row in self.wb.rows("07_BEBAN"):
            if self.scenario_id and str(row.get("skenario_id")) != self.scenario_id:
                continue
            gi = str(row.get("gi_id"))
            if gi not in gi_vl:
                continue
            load_id = stable_id("LOAD", str(row.get("beban_id")))
            body = _identified(load_id, f"BEBAN {gi}", str(row.get("titik_ukur") or ""))
            body += _t("plnnmm:canonicalBusinessId", row.get("beban_id"))
            body += _t("plnnmm:scenarioId", row.get("skenario_id"))
            body += _t("plnnmm:valueKind", row.get("jenis_nilai"))
            body += _provenance(
                row.get("sumber"), row.get("confidence"), str(row.get("dok_ref") or "")
            )
            body += _ref("cim:ConductingEquipment.BaseVoltage", bv)
            body += _ref("cim:Equipment.EquipmentContainer", gi_vl[gi][1])

            p = _num(row.get("p_mw"))
            q = _num(row.get("q_mvar"))
            if p is None:
                self.report.omit("cim:EnergyConsumer.pfixed")
            else:
                body += _t("cim:EnergyConsumer.pfixed", repr(float(p)))
            if q is None:
                self.report.omit("cim:EnergyConsumer.qfixed")
            else:
                body += _t("cim:EnergyConsumer.qfixed", repr(float(q)))

            self.parts.append(
                f'  <cim:EnergyConsumer rdf:ID="_{load_id}">\n{body}'
                "  </cim:EnergyConsumer>\n"
            )
            self.report.bump("EnergyConsumer")

    # --- driver ----------------------------------------------------------

    def build(self) -> str:
        _geo, sub_region = self._emit_region()
        gi_vl = self._emit_substations(sub_region)
        skema_map = self.wb.gi_skema_map()

        # Busbars first: bay disconnectors reference their nodes.
        gis_with_bays = {str(r.get("gi_id")) for r in self.wb.rows("02_BAY")}
        for gi, (_ss, vl) in gi_vl.items():
            if gi in gis_with_bays:
                self._emit_busbars(gi, skema_map.get(gi, "DOUBLE"), vl)

        bay_rows = {str(r["bay_id"]): r for r in self.wb.rows("02_BAY") if r.get("bay_id")}
        expansions_list = expand_all(self.wb.rows("02_BAY"), skema_map)
        expansions = {e.bay_id: e for e in expansions_list}

        for exp in expansions_list:
            self.report.warnings.extend(exp.warnings)
            if not exp.switches:
                continue
            gi = exp.gi_id
            if gi not in gi_vl:
                continue
            vl = gi_vl[gi][1]
            bay_uuid = self._emit_bay(exp, vl, bay_rows.get(exp.bay_id, {}))
            for node in exp.nodes:
                self._emit_node(node, vl, gi)
            for sw in exp.switches:
                self._emit_switch(sw, bay_uuid)

        self._emit_lines(expansions)
        self._emit_loads(gi_vl)

        return self._document()

    def _document(self) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        model_id = stable_id("MODEL", "BALI", self.scenario_id or "-")
        head = (
            "<?xml version='1.0' encoding='UTF-8'?>\n"
            f'<rdf:RDF xmlns:cim="{NS_CIM}" xmlns:rdf="{NS_RDF}" '
            f'xmlns:md="{NS_MD}" xmlns:plnicp="{NS_PLNICP}" '
            f'xmlns:plnnmm="{NS_PLNNMM}">\n'
            f'  <md:FullModel rdf:about="urn:uuid:{model_id}">\n'
            f"    <md:Model.created>{now}</md:Model.created>\n"
            "    <md:Model.modelingAuthoritySet>PLN NMM</md:Model.modelingAuthoritySet>\n"
            "    <md:Model.profile>http://entsoe.eu/CIM/EquipmentCore/3/1</md:Model.profile>\n"
            "    <md:Model.profile>http://entsoe.eu/CIM/EquipmentOperation/3/1</md:Model.profile>\n"
            "    <md:Model.version>0.1</md:Model.version>\n"
            "    <plnnmm:scope>Dibangkitkan dari NMM model-input workbook</plnnmm:scope>\n"
            "    <plnnmm:disclaimer>Susunan bay berasal dari template rekonstruksi, "
            "bukan standar PLN resmi. Parameter yang belum diketahui DIHILANGKAN, "
            "bukan diisi nol.</plnnmm:disclaimer>\n"
            + (_t("plnnmm:scenarioId", self.scenario_id, indent=4) if self.scenario_id else "")
            + "  </md:FullModel>\n"
        )
        return head + "".join(self.parts) + "</rdf:RDF>\n"


def build_cim(wb, output_path: str | Path, scenario_id: str | None = None) -> BuildReport:
    """Build CIM EQ from a workbook and write it to output_path."""
    builder = CimBuilder(wb, scenario_id=scenario_id)
    xml = builder.build()
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(xml, encoding="utf-8")
    return builder.report
