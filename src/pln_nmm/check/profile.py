"""Enforce that profiles stay separate.

The failure this guards against is quiet: layout data leaking into the
equipment file, or a diagram pointing at equipment that does not exist. Both
files still parse, both still look right, and the fault only surfaces later
when a model refresh overwrites someone's layout or a viewer draws nothing.

Rules:

* EQ carries no diagram data. `plnicp:DiagramProperty` is allowed only when a
  build explicitly asked for the PLN compatibility shadow.
* DL carries no equipment classes.
* Every `DiagramObject.IdentifiedObject` resolves to an object in EQ.
* Coordinates survive `repr()` round-tripping.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Classes that belong to EQ and must never appear in a DL file.
_EQ_CLASSES = (
    "Substation", "VoltageLevel", "Bay", "Breaker", "Disconnector",
    "BusbarSection", "ACLineSegment", "Terminal", "ConnectivityNode",
    "PowerTransformer", "EnergyConsumer", "SynchronousMachine", "BaseVoltage",
)

_DL_CLASSES = ("Diagram", "DiagramObject", "DiagramObjectPoint", "DiagramObjectStyle")


@dataclass
class ProfileReport:
    eq_objects: int = 0
    dl_objects: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def __str__(self) -> str:
        lines = [
            f"objek EQ : {self.eq_objects}",
            f"objek DL : {self.dl_objects}",
        ]
        for e in self.errors:
            lines.append(f"  [X] {e}")
        for w in self.warnings:
            lines.append(f"  [!] {w}")
        for n in self.notes:
            lines.append(f"  [i] {n}")
        lines.append("")
        lines.append("HASIL: " + ("LULUS" if self.ok else "GAGAL"))
        return "\n".join(lines)


def _ids(text: str) -> set[str]:
    return set(re.findall(r'rdf:ID="_([^"]+)"', text))


def check_profiles(
    eq_path: str | Path,
    dl_path: str | Path | None = None,
    *,
    allow_plnicp_in_eq: bool = False,
) -> ProfileReport:
    """Check an EQ file, and a DL file when one was written."""
    rep = ProfileReport()

    eq_text = Path(eq_path).read_text(encoding="utf-8")
    eq_ids = _ids(eq_text)
    rep.eq_objects = len(eq_ids)

    # --- EQ must not carry layout -------------------------------------------
    plnicp = len(re.findall(r"plnicp:DiagramProperty", eq_text))
    if plnicp:
        if allow_plnicp_in_eq:
            rep.notes.append(
                f"{plnicp} properti plnicp di EQ (mode kompatibilitas PLN diminta). "
                "Sumber layout tetap DL; ini salinan."
            )
        else:
            rep.errors.append(
                f"{plnicp} properti plnicp:DiagramProperty di dalam EQ. Layout milik "
                "profil DL. Pakai mode kompatibilitas bila ini disengaja."
            )
    for cls in _DL_CLASSES:
        if re.search(rf"<cim:{cls}\b", eq_text):
            rep.errors.append(f"kelas DL '{cls}' muncul di dalam EQ")

    # A declared-but-unused namespace suggests layout was meant to live here.
    if not plnicp and "iconpln.co.id" in eq_text:
        rep.warnings.append(
            "EQ mendeklarasikan namespace plnicp tetapi tidak memakainya; "
            "hapus deklarasi agar tidak menyiratkan layout ada di EQ"
        )

    if dl_path is None:
        rep.warnings.append("tidak ada file DL: layout belum dipisahkan")
        return rep

    dl_text = Path(dl_path).read_text(encoding="utf-8")
    dl_ids = _ids(dl_text)
    rep.dl_objects = len(dl_ids)

    # --- DL must not carry equipment ----------------------------------------
    for cls in _EQ_CLASSES:
        if re.search(rf"<cim:{cls}\b", dl_text):
            rep.errors.append(f"kelas EQ '{cls}' muncul di dalam DL")

    if "DiagramLayout" not in dl_text:
        rep.errors.append("header DL tidak menyatakan profil DiagramLayout")

    # --- every diagram object points at real equipment ----------------------
    refs = re.findall(
        r'DiagramObject\.IdentifiedObject rdf:resource="#_([^"]+)"', dl_text
    )
    dangling = sorted({r for r in refs if r not in eq_ids})
    if dangling:
        rep.errors.append(
            f"{len(dangling)} DiagramObject menunjuk mRID yang tidak ada di EQ: "
            + ", ".join(dangling[:3])
            + (" ..." if len(dangling) > 3 else "")
        )
    else:
        rep.notes.append(f"{len(refs)} tautan DL->EQ resolve seluruhnya")

    # A diagram object referenced as text instead of rdf:resource does not
    # resolve; cimpy's own exporter writes it that way.
    literal = re.findall(
        r"<cim:DiagramObject\.IdentifiedObject>([^<]+)</", dl_text
    )
    if literal:
        rep.errors.append(
            f"{len(literal)} DiagramObject.IdentifiedObject ditulis sebagai teks, "
            "bukan rdf:resource -- referensi tidak akan resolve"
        )

    # --- internal DL references ---------------------------------------------
    internal = re.findall(
        r'(?:DiagramObject\.Diagram|DiagramObjectPoint\.DiagramObject) '
        r'rdf:resource="#_([^"]+)"',
        dl_text,
    )
    broken = sorted({r for r in internal if r not in dl_ids})
    if broken:
        rep.errors.append(f"{len(broken)} referensi internal DL menggantung")

    # --- coordinates keep their precision -----------------------------------
    coords = re.findall(
        r"DiagramObjectPoint\.[xy]Position>([-\d.eE+]+)<", dl_text
    )
    bad = [c for c in coords if repr(float(c)) != c]
    if bad:
        rep.errors.append(
            f"{len(bad)} koordinat tidak memakai format repr(); round-trip float "
            f"tidak terjamin (contoh: {bad[0]})"
        )
    elif coords:
        rep.notes.append(f"{len(coords)} koordinat bit-exact terhadap repr()")

    # --- equipment with no placement ----------------------------------------
    placed = set(refs)
    drawable = set()
    for cls in ("Breaker", "Disconnector", "BusbarSection", "ACLineSegment",
                "PowerTransformer", "EnergyConsumer"):
        drawable |= set(re.findall(rf'<cim:{cls} rdf:ID="_([^"]+)"', eq_text))
    missing = drawable - placed
    if missing:
        rep.warnings.append(
            f"{len(missing)} dari {len(drawable)} peralatan belum punya posisi di DL"
        )

    return rep
