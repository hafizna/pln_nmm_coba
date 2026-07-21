# Claude Code instructions for pln_nmm_coba

## What this project is

A Python library that round-trips PLN's CIM16 / CGMES 2.4.15 Equipment (EQ)
profile XML files through `cimpy` without losing PLN custom namespaces
(`plnicp:DiagramProperty.x/y`, `nhftui:info`, and POC `plnnmm` review
metadata). cimpy alone silently drops these extensions on export; this library wraps cimpy with a thin
pre-/post-processing layer that preserves them.

The end goal is a web-based NMM tool for PLN Transmisi that imports CIM, lets
engineers edit the single-line diagram, and exports CIM back. This repo is the
round-trip kernel that the rest of the tool will sit on.

Current product direction: SLD-first. Build the web MVP around CIM import,
diagnostics, and single-line diagram creation/editing before topology
processing or load-flow analysis.

## Hard constraints

1. **Never modify cimpy.** It is a third-party Apache 2.0 dependency. All
   PLN-specific code lives in `src/pln_nmm/`. If cimpy needs a behavior change,
   write an adapter, not a fork.
2. **SLD-first for the next app phase.** Defer bus-branch topology processing.
   The web MVP should focus on importing CIM, showing diagnostics, and creating
   or editing SLDs. Reliably support busbars, power transformers, and
   line/corridor symbols first. Switching equipment (Breaker, Disconnector)
   should be schematic/annotation-only unless source CIM evidence is strong
   enough to identify it.
3. **mRID is the canonical key.** Some elements in PLN files have inconsistent
   `rdf:ID` vs `cim:IdentifiedObject.mRID` (about 9 of 126 in the sample). The
   adapter keys everything by `rdf:ID` stripped of leading underscore, because
   that is what cimpy emits on export. Do not change this without re-verifying
   the round-trip.
4. **Extension preservation must be bit-exact for float coordinates.**
   Coordinates use Python `repr()` formatting on emit so that round-trip
   `float(repr(x)) == x`. Tests assert this. Do not switch to f-string
   formatting or rounding.

## How to run things

```bash
# Install for development
pip install -e ".[dev]"

# Run the test suite (31 tests, ~10s)
pytest

# Run the demo
python examples/roundtrip_demo.py

# CLI
python -m pln_nmm.cli inspect <file.xml>
python -m pln_nmm.cli roundtrip <input.xml> <output.xml>
```

## Layout

```text
src/pln_nmm/
  adapter.py      - core extract/strip/reinject logic. Pure XML, no cimpy.
  diagnostics.py  - pre-cimpy checks for unresolved template tokens.
  importer.py     - wraps cimpy.cim_import with the strip step.
  exporter.py     - wraps cimpy.cim_export with the reinject step.
  cli.py          - argparse CLI.

tests/
  fixtures/sample_EQ.xml                       - canonical 1-substation PLN test file.
  fixtures/CIM_sample-db_userdef_python.xml    - 2.7 MB aggregate fixture.
  test_adapter.py                              - pure-XML adapter tests.
  test_diagnostics.py                          - unresolved `$(Isi_*)` diagnostics tests.
  test_roundtrip.py                            - full cimpy round-trip tests.
  test_large_fixture.py                        - large fixture coverage + cimpy xfail.
```

## Known data quality issues in PLN files

These are observations about PLN's existing EQ files, not bugs in this library.
The library tolerates them.

- ~9 elements in the sample have `rdf:ID` and `cim:IdentifiedObject.mRID`
  values that disagree. The adapter keys by `rdf:ID` (stripped underscore) and
  flags the mismatch in `ExtractionReport.elements_with_id_mrid_mismatch`.
- VoltageLevel container UUIDs differ only in the last character
  (e.g. `...87b0`, `...87b1`, `...87b2`). Looks like manual UUID-suffix
  incrementing in the source tool.
- Some `ConnectivityNode.ConnectivityNodeContainer` references point to IDs
  that do not exist (off-by-one in the suffix pattern above). cimpy silently
  absorbs these.
- `ACLineSegment.r` and `bch` are sometimes 0 because PLN does not have
  per-corridor electrical parameters in any database. This is a domain problem,
  not a parser problem.
- Some PLN files are templates with unfilled `$(Isi_*)` placeholder strings
  sitting in float-typed CIM fields (e.g. `$(Isi_ACLineSegment.bch)`). The
  adapter layer (pure XML) is fine with these; cimpy's `cim_import` raises
  `ValueError` because it cannot coerce them to float. The aggregate fixture
  exhibits this, with an xfail test pinning the behavior. The exact business
  meaning of `Isi` is unconfirmed, but the suffix usually identifies the CIM
  class/property whose value is unresolved.

## Things that are NOT in scope for this library

- Topology processing (node-breaker to bus-branch reduction) is deferred. When
  written, it will live in a separate `topology.py` module.
- Load flow execution. This will eventually call out to pandapower in a separate
  `loadflow/` subpackage.
- Production deployment and authentication for the local web UI.
- TP, SSH, SV, GL, DL profiles. v1 is EQ-only.

## Dependencies

- cimpy 1.1.0+ (Apache 2.0)
- lxml 4.9+ (BSD)
- pytest 8.0+ (dev only, MIT)

When adding new dependencies, prefer permissively-licensed packages (MIT, BSD,
Apache 2.0). PLN's enterprise software intake disfavors GPL and AGPL because of
redistribution clauses on a public-facing web product.

## Common tasks

**Add a new test**: drop a `test_*.py` file in `tests/`. Use the existing
fixtures pattern for sample CIM files.

**Add support for a new PLN namespace**: add namespace URI constant in
`adapter.py`, extend `PlnExtension` dataclass, update extract/strip/reinject
methods. Add a regression test against a fixture file that exercises it.

**Verify round-trip on a new file**: drop the file in `tests/fixtures/`, add a
parameterized test or run `python -m pln_nmm.cli roundtrip` and diff the input
and output.

## When in doubt

Read `src/pln_nmm/adapter.py` end to end. It is the heart of the round-trip
kernel. For product direction, read `README.md` and `docs/07_PHASES.md`.
