# pln_nmm_coba

PLN Network Model Management — CIM round-trip toolkit. Proof of concept.

This repository contains a Python library that round-trips PLN's CIM16 /
CGMES 2.4.15 Equipment (EQ) profile XML files without losing the two
custom namespaces that PLN's existing toolchain (Nur Hidayat's db config)
embeds inline:

- `plnicp:DiagramProperty.x` / `.y` — per-equipment 2D canvas coordinates
  used by PLN's diagram tools
- `nhftui:info` — sirkit annotation, primarily on `ConnectivityNode`

The library is a thin adapter layer on top of [cimpy](https://github.com/sogno-platform/cimpy),
the SOGNO platform's Python implementation of the IEC 61970 CIM standard.
cimpy itself is unmodified. We do not fork it. The PLN-specific behavior
lives entirely in `src/pln_nmm/adapter.py`.

## Status

Phase 1 (EQ round-trip) — working. All 14 tests pass against the bundled
sample file `tests/fixtures/sample_EQ.xml`.

Out of scope for now: TP/SSH/SV profiles, load flow, web UI, multi-substation
editing. See `docs/` for the planned next phases.

## Quick start

```bash
# Install dependencies (Python 3.10+)
pip install -e ".[dev]"

# Run the demo against the bundled sample
python examples/roundtrip_demo.py

# Run the test suite
pytest

# Use the CLI
python -m pln_nmm.cli inspect tests/fixtures/sample_EQ.xml
python -m pln_nmm.cli roundtrip input.xml output.xml --mode preserve
```

## What the round-trip preserves

| Aspect | Preserved? |
|---|---|
| All `rdf:ID` values (mRIDs) | yes |
| Class distribution (counts per CIM class) | yes |
| Electrical parameters (r, x, b, ratedS, ratedU, etc.) | yes |
| Container hierarchy (Region → Substation → VoltageLevel) | yes |
| Terminal-to-equipment-to-ConnectivityNode chains | yes |
| `plnicp:DiagramProperty.x` / `.y` coordinates | yes (preserve mode) |
| `nhftui:info` attributes | yes (preserve mode) |
| Float coordinate precision | yes (bit-exact) |
| Original `md:FullModel` metadata | no — cimpy overwrites |
| `cim:IdentifiedObject.mRID` child element | no — cimpy emits only `rdf:ID` |
| Original whitespace / element ordering | no — cimpy normalizes |

## Architecture in one paragraph

Importing a PLN EQ file goes through three steps. First, `extract_pln_extensions`
walks the XML and lifts every `plnicp:DiagramProperty.x/y` and `nhftui:info`
into a side-table keyed by mRID. Second, `strip_pln_extensions` writes a
cleaned copy of the XML to a temp file with all PLN-specific elements
removed. Third, cimpy parses the cleaned file into its native object graph.
On export, cimpy serializes the object graph back to XML (without the
PLN extensions, since cimpy does not know about them), then `reinject_pln_extensions`
walks that output and reattaches the extensions from the side-table by
matching on `rdf:ID`.

## Project layout

```
pln_nmm_coba/
├── src/pln_nmm/        # library
│   ├── adapter.py      # extract / strip / reinject PLN extensions
│   ├── importer.py     # wraps cimpy.cim_import
│   ├── exporter.py     # wraps cimpy.cim_export with reinjection
│   └── cli.py          # command-line entry point
├── tests/              # pytest suite
│   └── fixtures/       # bundled PLN sample CIM files
├── examples/           # runnable demos
├── docs/               # design specs, decision records
├── CLAUDE.md           # context for Claude Code agent
├── AGENTS.md           # context for Codex / generic agents
└── pyproject.toml      # build, deps, test config
```

## Working with agentic tools

This repo is set up for use with multiple agentic coding tools. The
top-level instruction files describe project conventions for each:

- **Claude Code** reads `CLAUDE.md`
- **Codex** and other generic agents read `AGENTS.md`
- **Antigravity (Gemini)** reads `.gemini/config.md`

All three files describe the same project the same way. They diverge only
in tool-specific commands and flags.

## License

Proprietary — internal PLN Icon Plus tooling.

Third-party dependencies and their licenses:

- cimpy — Apache License 2.0 — © ACS RWTH Aachen / OPAL-RT Technologies
- lxml — BSD-style — © Infrae
- xmltodict (transitive via cimpy) — MIT — © Martin Blech
- chevron (transitive via cimpy) — MIT — © Noah Morrison

A copy of the cimpy LICENSE is bundled by pip in the installed package's
`dist-info` directory; no separate redistribution step is required.
