# Agent instructions for pln_nmm_coba

This file is read by OpenAI Codex and other generic agentic coding tools
that follow the AGENTS.md convention. Claude Code reads `CLAUDE.md`
instead; the two files describe the same project with the same conventions.

## Project summary

Python library that round-trips PLN's CIM16 / CGMES 2.4.15 Equipment
profile XML files through the SOGNO `cimpy` library, preserving two
custom PLN namespaces (`plnicp:DiagramProperty.x/y`, `nhftui:info`, and POC
`plnnmm` review metadata) that cimpy alone would silently drop on export.

End goal: web-based Network Model Management tool for PLN Transmisi.
This repo is the parser/serializer kernel. The next product phase is an
SLD-first web editor; topology processing and load-flow analysis are
deferred until the diagram workflow and data-quality layer are useful.

## How to run

```bash
pip install -e ".[dev]"   # Python 3.10+
pytest                     # 31 tests, ~10s
python examples/roundtrip_demo.py
```

## Source layout

- `src/pln_nmm/adapter.py` — pure-XML extract/strip/reinject. The core IP.
- `src/pln_nmm/importer.py` — wraps `cimpy.cim_import` with the strip step.
- `src/pln_nmm/exporter.py` — wraps `cimpy.cim_export` with the reinject step.
- `src/pln_nmm/cli.py` — argparse CLI.
- `tests/` — pytest suite, fixtures in `tests/fixtures/`.
- `docs/` — design specs and roadmap.

## Critical invariants — do not break these

1. cimpy must remain unmodified. Wrap it externally; never fork or patch
   files inside the cimpy package.
2. The canonical key for matching elements between import and re-export
   is `rdf:ID` with leading underscore stripped. Do not switch to
   `cim:IdentifiedObject.mRID` even when the two disagree (~9 elements
   in the sample disagree; cimpy emits the rdf:ID form).
3. Float coordinates must round-trip bit-exact via Python `repr()`.
   Tests assert `before.x == after.x` after the round-trip. Do not
   change the float-to-string formatting.
4. SLD-first for the next app phase. Do not prioritize bus-branch topology
   processing yet. Focus the web MVP on CIM import, diagnostics, and SLD
   creation/editing. Switching equipment (Breaker, Disconnector) should be
   treated as schematic/annotation-only unless the source CIM clearly
   identifies it.

## Domain context

- CIM = Common Information Model, IEC 61970 standard for power system
  data exchange.
- CGMES 2.4.15 = ENTSO-E's CIM 16 profile. PLN files use this exact
  namespace: `http://iec.ch/TC57/2013/CIM-schema-cim16#`.
- EQ profile = Equipment, the static topology and parameters. Other
  profiles (TP, SSH, SV, DL, GL) are out of scope for v1.
- `plnicp` namespace `http://iconpln.co.id#` and `nhftui` namespace
  `https://eng.ui.ac.id/lab-simulasi/nhjarman2025#` are PLN-internal
  extensions, not standard CGMES.

## Common tasks

**Add a regression fixture**: drop the XML in `tests/fixtures/`, write
a test that imports it, exports it, and compares the rdf:ID set.

**Run the full sanity check**: `pytest && python examples/roundtrip_demo.py`.
The demo writes round-tripped files into `examples/out/` for visual
inspection.

**Inspect a CIM file without round-tripping**:
`python -m pln_nmm.cli inspect path/to/file.xml`

## Dependencies and licensing

Permissively licensed only:
- cimpy — Apache 2.0
- lxml — BSD
- pytest — MIT

No GPL / AGPL dependencies. The product will be deployed on a public PLN
web property; copyleft licenses are off the table by procurement policy.
