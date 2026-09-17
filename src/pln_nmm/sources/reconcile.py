"""Compare SLD engine evidence against the model-input workbook.

Neither source is authoritative on its own. The workbook is hand-filled from
figures and books; the SLD engine traces drawings at stated confidence. Where
they agree, confidence rises. Where they disagree, that is a finding for a
human -- never something to resolve silently by picking one.

This module only reports. It does not edit the workbook and does not decide.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .sld_engine import SldEvidence

# Workbook GI names carry a facility prefix the handoff keys do not.
_PREFIX = re.compile(r"^(GI|GIS|GITET|AIS|PLTU|PLTG|PLTD|PLTA)\s+", re.I)


def normalise_gi(name: str) -> str:
    """Reduce a GI label to something comparable across sources."""
    s = str(name).upper().strip()
    s = _PREFIX.sub("", s)
    return s.replace("_", " ").replace("-", " ").strip()


@dataclass
class Finding:
    kind: str  # MATCH / ONLY_SLD / ONLY_WORKBOOK / CONFLICT
    subject: str
    detail: str

    def __str__(self) -> str:
        mark = {
            "MATCH": "ok ",
            "ONLY_SLD": "sld",
            "ONLY_WORKBOOK": "wb ",
            "CONFLICT": "!! ",
        }.get(self.kind, "   ")
        return f"[{mark}] {self.subject}: {self.detail}"


@dataclass
class ReconciliationReport:
    findings: list[Finding] = field(default_factory=list)
    gi_matched: int = 0
    corridor_matched: int = 0

    def add(self, kind: str, subject: str, detail: str) -> None:
        self.findings.append(Finding(kind, subject, detail))

    def of_kind(self, kind: str) -> list[Finding]:
        return [f for f in self.findings if f.kind == kind]

    @property
    def conflicts(self) -> list[Finding]:
        return self.of_kind("CONFLICT")

    def __str__(self) -> str:
        counts = {
            k: len(self.of_kind(k))
            for k in ("MATCH", "CONFLICT", "ONLY_SLD", "ONLY_WORKBOOK")
        }
        lines = [
            "=== REKONSILIASI SLD ENGINE vs WORKBOOK ===",
            "",
            f"GI cocok        : {self.gi_matched}",
            f"ruas cocok      : {self.corridor_matched}",
            f"konflik         : {counts['CONFLICT']}",
            f"hanya di SLD    : {counts['ONLY_SLD']}",
            f"hanya di workbook: {counts['ONLY_WORKBOOK']}",
        ]
        for kind, title in (
            ("CONFLICT", "KONFLIK -- perlu keputusan manusia"),
            ("ONLY_SLD", "Ada di SLD engine, belum di workbook"),
            ("ONLY_WORKBOOK", "Ada di workbook, tidak di SLD engine"),
        ):
            rows = self.of_kind(kind)
            if rows:
                lines += ["", title + ":"]
                lines += [f"  {f}" for f in rows]
        return "\n".join(lines)


def _wb_gi_index(wb) -> dict[str, dict]:
    return {
        normalise_gi(r.get("gi_nama") or r.get("gi_id")): r
        for r in wb.rows("01_GI")
        if r.get("gi_id")
    }


def _wb_corridors(wb) -> dict[tuple[str, str], dict]:
    """Corridors keyed by an undirected, normalised GI pair."""
    gi_name = {
        str(r["gi_id"]): normalise_gi(r.get("gi_nama") or r["gi_id"])
        for r in wb.rows("01_GI")
        if r.get("gi_id")
    }
    out: dict[tuple[str, str], dict] = {}
    for row in wb.rows("04_SAMBUNGAN"):
        a = gi_name.get(str(row.get("dari_gi")))
        b = gi_name.get(str(row.get("ke_gi")))
        if not a or not b or a == b:
            continue
        out.setdefault(tuple(sorted((a, b))), row)
    return out


def reconcile(evidence: SldEvidence, wb) -> ReconciliationReport:
    """Compare evidence with a workbook read by sources.workbook.read_workbook."""
    rep = ReconciliationReport()

    wb_gi = _wb_gi_index(wb)

    # Match on external_key first: a handoff's site_name can be a descriptive
    # label ("Transfer SKLT Banyuwangi") while its key is the GI ("BANYUWANGI").
    sld_gi: dict[str, object] = {}
    for g in evidence.gis:
        by_key = normalise_gi(g.key)
        by_name = normalise_gi(g.name or g.key)
        chosen = by_key if by_key in wb_gi else (by_name if by_name in wb_gi else by_key)
        sld_gi[chosen] = g

    for name in sorted(set(sld_gi) & set(wb_gi)):
        rep.gi_matched += 1
        sld, row = sld_gi[name], wb_gi[name]
        sld_scheme = sld.skema_busbar
        wb_scheme = row.get("skema_busbar")
        if sld_scheme and wb_scheme and sld_scheme != wb_scheme:
            rep.add(
                "CONFLICT",
                name,
                f"skema busbar: SLD engine '{sld_scheme}' vs workbook '{wb_scheme}'",
            )

    for name in sorted(set(sld_gi) - set(wb_gi)):
        g = sld_gi[name]
        rep.add("ONLY_SLD", name, f"{g.kind}, confidence {g.confidence}")
    for name in sorted(set(wb_gi) - set(sld_gi)):
        rep.add("ONLY_WORKBOOK", name, "tidak ada di bukti SLD engine")

    # Corridor endpoints are external_keys; resolve them through the same
    # choice made above so both sides of the comparison use one spelling.
    key_to_label = {normalise_gi(g.key): label for label, g in sld_gi.items()}

    def endpoint(raw: str) -> str:
        return key_to_label.get(normalise_gi(raw), normalise_gi(raw))

    wb_cor = _wb_corridors(wb)
    sld_cor: dict[tuple[str, str], list] = {}
    for c in evidence.corridors:
        a, b = endpoint(c.from_gi), endpoint(c.to_gi)
        if a == b:
            continue
        sld_cor.setdefault(tuple(sorted((a, b))), []).append(c)

    for pair in sorted(set(sld_cor) & set(wb_cor)):
        rep.corridor_matched += 1
        rows = sld_cor[pair]
        wb_row = wb_cor[pair]
        # Several handoff rows can describe one corridor (SKLT #1,2 and #3,4).
        sld_count = sum(c.circuit_count or 0 for c in rows) or None
        wb_count = wb_row.get("jml_sirkit")
        label = " - ".join(pair)
        if sld_count and wb_count and int(sld_count) != int(wb_count):
            rep.add(
                "CONFLICT",
                label,
                f"jumlah sirkit: SLD engine {sld_count} vs workbook {wb_count}",
            )
        sld_phi = rows[0].phi
        wb_phi = wb_row.get("phi")
        if sld_phi and wb_phi and sld_phi != wb_phi and not (sld_count and wb_count and int(sld_count) != int(wb_count)):
            rep.add("CONFLICT", label, f"phi: SLD engine '{sld_phi}' vs workbook '{wb_phi}'")

    for pair in sorted(set(sld_cor) - set(wb_cor)):
        rows = sld_cor[pair]
        n = sum(c.circuit_count or 0 for c in rows) or "?"
        rep.add("ONLY_SLD", " - ".join(pair), f"ruas {rows[0].circuit_type}, {n} sirkit")
    for pair in sorted(set(wb_cor) - set(sld_cor)):
        rep.add("ONLY_WORKBOOK", " - ".join(pair), "ruas tidak ada di bukti SLD engine")

    return rep
