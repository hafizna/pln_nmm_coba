"""
Exporter: wrap cimpy.cim_export with the PLN extension reinjection step.

Public API:
    export_pln_eq(import_result, output_path, mode='preserve_extensions')

mode values:
    'preserve_extensions' (default)
        Re-attach plnicp:DiagramProperty.x/y and nhftui:info to every
        matching element. Output is a drop-in replacement for the
        original PLN format.

    'standard_cgmes'
        Emit cimpy's clean CGMES output as-is, without any PLN extensions.
        Useful for cross-validation against external CGMES tools.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Literal

import cimpy
from lxml import etree

from .adapter import NS_RDF, reinject_pln_extensions
from .importer import CGMES_VERSION, ImportResult


ExportMode = Literal["preserve_extensions", "standard_cgmes"]


def _normalize_local_references(xml_path: Path) -> int:
    """Match local resource fragments to emitted rdf:ID spelling.

    cimpy can emit rdf:ID="_uuid" but rdf:resource="#uuid". Only repair
    uniquely resolvable local aliases. External and unresolved references stay
    untouched so this does not invent connections or conceal missing objects.
    """
    tree = etree.parse(str(xml_path))
    id_attr, resource_attr = f"{{{NS_RDF}}}ID", f"{{{NS_RDF}}}resource"
    ids = {e.get(id_attr) for e in tree.iter() if e.get(id_attr)}
    aliases: dict[str, set[str]] = {}
    for identifier in ids:
        aliases.setdefault(identifier.lstrip("_"), set()).add(identifier)
    changed = 0
    for elem in tree.iter():
        resource = elem.get(resource_attr, "")
        if not resource.startswith("#") or resource[1:] in ids:
            continue
        candidates = aliases.get(resource[1:].lstrip("_"), set())
        if len(candidates) == 1:
            elem.set(resource_attr, "#" + next(iter(candidates)))
            changed += 1
    if changed:
        tree.write(str(xml_path), encoding="UTF-8", xml_declaration=True)
    return changed


def _normalize_cimpy_xml_encoding(xml_path: Path) -> bool:
    """Repair legacy Windows-1252 bytes in cimpy's nominally UTF-8 XML.

    Some CIM string values contain punctuation copied from spreadsheets.
    cimpy writes those bytes using the Windows locale while retaining its
    UTF-8 XML declaration.  Preserve already-valid UTF-8 runs and translate
    only bytes that cannot be decoded as UTF-8.

    Returns True when the file had to be rewritten.
    """
    raw = xml_path.read_bytes()
    try:
        raw.decode("utf-8")
        return False
    except UnicodeDecodeError:
        pass

    decoded: list[str] = []
    remaining = raw
    while remaining:
        try:
            decoded.append(remaining.decode("utf-8"))
            break
        except UnicodeDecodeError as exc:
            decoded.append(remaining[: exc.start].decode("utf-8"))
            invalid = remaining[exc.start : exc.start + 1]
            decoded.append(invalid.decode("cp1252"))
            remaining = remaining[exc.start + 1 :]

    xml_path.write_text("".join(decoded), encoding="utf-8", newline="")
    return True


def export_pln_eq(
    import_result: ImportResult,
    output_path: str | Path,
    mode: ExportMode = "preserve_extensions",
) -> dict:
    """
    Serialize the cimpy topology back to XML, optionally reinjecting the
    PLN extensions captured during import.

    Returns a small statistics dict describing what was reinjected.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # cimpy.cim_export takes a basename and writes <basename>_Equipment.xml
    # for the EQ profile. We give it a basename inside a temp directory,
    # then move/rewrite the result to the user's chosen output_path.
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        basename = tmpdir_path / "out"

        cimpy.cim_export(
            import_result.cimpy_result,
            str(basename),
            CGMES_VERSION,
            ["EQ"],
        )

        cimpy_eq = tmpdir_path / "out_Equipment.xml"
        if not cimpy_eq.exists():
            raise RuntimeError(
                f"cimpy did not produce the expected EQ file at {cimpy_eq}"
            )

        encoding_normalized = _normalize_cimpy_xml_encoding(cimpy_eq)
        references_normalized = _normalize_local_references(cimpy_eq)

        if mode == "standard_cgmes":
            shutil.copyfile(cimpy_eq, output_path)
            return {
                "mode": "standard_cgmes",
                "reinjected": 0,
                "encoding_normalized": encoding_normalized,
                "references_normalized": references_normalized,
            }

        if mode == "preserve_extensions":
            stats = reinject_pln_extensions(
                cimpy_eq,
                output_path,
                import_result.extensions_report.extensions,
            )
            stats["mode"] = "preserve_extensions"
            stats["encoding_normalized"] = encoding_normalized
            stats["references_normalized"] = references_normalized
            return stats

        raise ValueError(f"Unknown export mode: {mode!r}")
