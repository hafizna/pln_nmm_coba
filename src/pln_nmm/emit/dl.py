"""Emit the CGMES DiagramLayout (DL) profile as its own file.

Why this exists: PLN's current practice hangs coordinates off the equipment
object itself, as `plnicp:DiagramProperty.x/y` inside the EQ file. That has two
costs. One piece of equipment can then hold only one position, so a system
diagram and a per-GI diagram cannot coexist. And because layout shares a file
with the model, refreshing the model risks overwriting work a person did by
hand.

CGMES already solves this. DL is a separate profile with its own version
sequence, and its object chain is:

    Diagram  -->  DiagramObject  -->  DiagramObjectPoint
                        |
                        +-- IdentifiedObject --> the EQ object's mRID

So many diagrams can describe the same equipment, and layout versions
independently of the model. EPRI's Network Model Manager requirements (R1.2)
ask for exactly this.

We write DL ourselves rather than through `cimpy.cim_export`. cimpy has the
full DL class set, but `_sort_classes_to_profile` compares a string on one line
and a Profile enum on another, so freshly authored objects are dropped. Objects
that came from `cim_import` carry a `serializationProfile` dict that sidesteps
the check; ones we build do not. Writing the XML directly is simpler than
constructing objects that pretend to have been imported, and it keeps us clear
of the rule against modifying cimpy.

Coordinates keep Python `repr()` formatting so `float(repr(x)) == x` holds
through a round-trip, the same invariant the EQ adapter enforces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

NS_CIM = "http://iec.ch/TC57/2013/CIM-schema-cim16#"
NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
NS_MD = "http://iec.ch/TC57/61970-552/ModelDescription/1#"

PROFILE_URI = "http://entsoe.eu/CIM/DiagramLayout/3/1"


def _coord(value: float) -> str:
    """Emit a coordinate so re-reading it yields the identical float."""
    return repr(float(value))


@dataclass
class Placement:
    """One piece of equipment at one position on one diagram."""

    equipment_mrid: str
    x: float
    y: float
    drawing_order: int = 0
    style: str | None = None


@dataclass
class Diagram:
    """A named drawing: the system overview, or one substation's detail."""

    mrid: str
    name: str
    description: str = ""
    placements: list[Placement] = field(default_factory=list)

    def place(self, equipment_mrid: str, x: float, y: float, **kw) -> Placement:
        p = Placement(equipment_mrid=equipment_mrid, x=x, y=y, **kw)
        self.placements.append(p)
        return p


@dataclass
class DlReport:
    diagrams: int = 0
    objects: int = 0
    points: int = 0
    unresolved: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        lines = [
            f"diagram        : {self.diagrams}",
            f"DiagramObject  : {self.objects}",
            f"titik koordinat: {self.points}",
        ]
        if self.unresolved:
            lines.append(
                f"  [!] {len(self.unresolved)} objek menunjuk mRID yang tidak ada di EQ"
            )
            for m in self.unresolved[:5]:
                lines.append(f"      {m}")
            if len(self.unresolved) > 5:
                lines.append(f"      ... dan {len(self.unresolved) - 5} lainnya")
        return "\n".join(lines)


def _stable_suffix(*parts: str) -> str:
    """Deterministic ids, so republishing a diagram diffs cleanly."""
    from ..model.identity import stable_id

    return stable_id("DL", *parts)


def build_dl_xml(
    diagrams: list[Diagram],
    *,
    model_id: str,
    known_mrids: set[str] | None = None,
    scenario: str | None = None,
) -> tuple[str, DlReport]:
    """Serialise diagrams as a DL profile document.

    `known_mrids` is the set of EQ object ids. Placements pointing outside it
    are still written -- silently dropping them would hide the fault -- but are
    reported so a caller can fail the build.
    """
    report = DlReport()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    out: list[str] = [
        "<?xml version='1.0' encoding='UTF-8'?>",
        f'<rdf:RDF xmlns:cim="{NS_CIM}" xmlns:rdf="{NS_RDF}" xmlns:md="{NS_MD}">',
        f'  <md:FullModel rdf:about="urn:uuid:{model_id}">',
        f"    <md:Model.created>{now}</md:Model.created>",
        "    <md:Model.modelingAuthoritySet>PLN NMM</md:Model.modelingAuthoritySet>",
        f"    <md:Model.profile>{PROFILE_URI}</md:Model.profile>",
        "    <md:Model.version>1</md:Model.version>",
    ]
    if scenario:
        out.append(f"    <md:Model.scenarioTime>{escape(scenario)}</md:Model.scenarioTime>")
    out.append("  </md:FullModel>")

    for diagram in diagrams:
        report.diagrams += 1
        out.append(f'  <cim:Diagram rdf:ID="_{diagram.mrid}">')
        out.append(f"    <cim:IdentifiedObject.mRID>{diagram.mrid}</cim:IdentifiedObject.mRID>")
        out.append(f"    <cim:IdentifiedObject.name>{escape(diagram.name)}</cim:IdentifiedObject.name>")
        if diagram.description:
            out.append(
                f"    <cim:IdentifiedObject.description>{escape(diagram.description)}"
                "</cim:IdentifiedObject.description>"
            )
        out.append("  </cim:Diagram>")

        for i, p in enumerate(diagram.placements):
            if known_mrids is not None and p.equipment_mrid not in known_mrids:
                report.unresolved.append(p.equipment_mrid)

            do_id = _stable_suffix(diagram.mrid, p.equipment_mrid)
            report.objects += 1
            out.append(f'  <cim:DiagramObject rdf:ID="_{do_id}">')
            out.append(f"    <cim:IdentifiedObject.mRID>{do_id}</cim:IdentifiedObject.mRID>")
            out.append(f'    <cim:DiagramObject.Diagram rdf:resource="#_{diagram.mrid}"/>')
            # The link back into EQ. A resource reference, not a literal --
            # cimpy's own exporter writes this one as text, which does not
            # resolve.
            out.append(
                f'    <cim:DiagramObject.IdentifiedObject rdf:resource="#_{p.equipment_mrid}"/>'
            )
            if p.drawing_order:
                out.append(
                    f"    <cim:DiagramObject.drawingOrder>{p.drawing_order}"
                    "</cim:DiagramObject.drawingOrder>"
                )
            out.append("  </cim:DiagramObject>")

            pt_id = _stable_suffix(diagram.mrid, p.equipment_mrid, "pt")
            report.points += 1
            out.append(f'  <cim:DiagramObjectPoint rdf:ID="_{pt_id}">')
            out.append(
                f'    <cim:DiagramObjectPoint.DiagramObject rdf:resource="#_{do_id}"/>'
            )
            out.append(
                "    <cim:DiagramObjectPoint.sequenceNumber>1"
                "</cim:DiagramObjectPoint.sequenceNumber>"
            )
            out.append(
                f"    <cim:DiagramObjectPoint.xPosition>{_coord(p.x)}"
                "</cim:DiagramObjectPoint.xPosition>"
            )
            out.append(
                f"    <cim:DiagramObjectPoint.yPosition>{_coord(p.y)}"
                "</cim:DiagramObjectPoint.yPosition>"
            )
            out.append("  </cim:DiagramObjectPoint>")

    out.append("</rdf:RDF>")
    return "\n".join(out) + "\n", report


def write_dl(
    diagrams: list[Diagram],
    output_path: str | Path,
    *,
    model_id: str,
    known_mrids: set[str] | None = None,
    scenario: str | None = None,
) -> DlReport:
    xml, report = build_dl_xml(
        diagrams, model_id=model_id, known_mrids=known_mrids, scenario=scenario
    )
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(xml, encoding="utf-8")
    return report


def read_eq_mrids(eq_path: str | Path) -> set[str]:
    """Collect the mRIDs an EQ file declares, to validate DL against it."""
    import re

    text = Path(eq_path).read_text(encoding="utf-8")
    return set(re.findall(r'rdf:ID="_([^"]+)"', text))
