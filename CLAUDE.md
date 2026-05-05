# Claude Code instructions for pln_nmm_coba

## What this project is

A Python library that round-trips PLN's CIM16 / CGMES 2.4.15 Equipment (EQ)
profile XML files through `cimpy` without losing PLN's two custom
namespaces (`plnicp:DiagramProperty.x/y` and `nhftui:info`). cimpy alone
silently drops both extensions on export; this library wraps cimpy with
a thin pre-/post-processing layer that preserves them.

The end goal is a web-based NMM tool for PLN Transmisi that imports CIM,
lets engineers edit the single-line diagram, and exports CIM back. This
repo is the round-trip kernel that the rest of the tool will sit on.

## Hard constraints

1. **Never modify cimpy.** It is a third-party Apache 2.0 dependency. All
   PLN-specific code lives in `src/pln_nmm/`. If cimpy needs a behavior
   change, write an adapter, not a fork.
2. **Bus-branch only for v1.** The data model is restricted to BusbarSection,
   PowerTransformer (+ ends), ACLineSegment, ConformLoad, SynchronousMachine,
   plus their containers. Switching equipment (Breaker, Disconnector) is
   excluded from the asset import path because PLN's physical asset data
   does not differentiate them. They appear in the SVG palette as schematic
   annotations only — see `docs/00_PROJECT_BRIEF.md` (when written) for
   the full reasoning.
3. **mRID is the canonical key.** Some elements in PLN files have
   inconsistent `rdf:ID` vs `cim:IdentifiedObject.mRID` (about 9 of 126
   in the sample). The adapter keys everything by `rdf:ID` stripped of
   leading underscore, because that is what cimpy emits on export. Do not
   change this without re-verifying the round-trip.
4. **Extension preservation must be bit-exact for float coordinates.**
   Coordinates use Python `repr()` formatting on emit so that round-trip
   `float(repr(x)) == x`. Tests assert this. Do not switch to f-string
   formatting or rounding.

## How to run things

```bash
# Install for development
pip install -e ".[dev]"

# Run the test suite (14 tests, ~0.5s)
pytest

# Run the demo
python examples/roundtrip_demo.py

# CLI
python -m pln_nmm.cli inspect <file.xml>
python -m pln_nmm.cli roundtrip <input.xml> <output.xml>
```

## Layout

```
src/pln_nmm/
  adapter.py     - core extract/strip/reinject logic. Pure XML, no cimpy.
  importer.py    - wraps cimpy.cim_import with the strip step
  exporter.py    - wraps cimpy.cim_export with the reinject step
  cli.py         - argparse CLI

tests/
  fixtures/sample_EQ.xml      - the canonical PLN test file (CIM16, 126 objects)
  test_adapter.py             - 7 tests covering the pure-XML layer
  test_roundtrip.py           - 7 tests covering the full cimpy round-trip
```

## Known data quality issues in PLN files

These are observations about PLN's existing EQ files, not bugs in this
library. The library tolerates them.

- ~9 elements in the sample have `rdf:ID` and `cim:IdentifiedObject.mRID`
  values that disagree. The adapter keys by `rdf:ID` (stripped underscore)
  and flags the mismatch in `ExtractionReport.elements_with_id_mrid_mismatch`.
- VoltageLevel container UUIDs differ only in the last character
  (e.g. `...87b0`, `...87b1`, `...87b2`). Looks like manual UUID-suffix
  incrementing in the source tool.
- Some `ConnectivityNode.ConnectivityNodeContainer` references point to
  IDs that do not exist (off-by-one in the suffix pattern above). cimpy
  silently absorbs these.
- `ACLineSegment.r` and `bch` are sometimes 0 because PLN does not have
  per-corridor electrical parameters in any database. This is a domain
  problem, not a parser problem.

## Things that are NOT in scope for this library

- Topology processing (node-breaker → bus-branch reduction). When written,
  it will live in a separate `topology.py` module.
- Load flow execution. This will eventually call out to pandapower in a
  separate `loadflow/` subpackage.
- The web UI. That will be a separate repo.
- TP, SSH, SV, GL, DL profiles. v1 is EQ-only.

## Dependencies

- cimpy 1.1.0+ (Apache 2.0)
- lxml 4.9+ (BSD)
- pytest 8.0+ (dev only, MIT)

When adding new dependencies, prefer permissively-licensed packages
(MIT, BSD, Apache 2.0). PLN's enterprise software intake disfavors GPL
and AGPL because of redistribution clauses on a public-facing web product.

## Common tasks

**Add a new test**: drop a `test_*.py` file in `tests/`. Use the existing
fixtures pattern for sample CIM files.

**Add support for a new PLN namespace**: add namespace URI constant in
`adapter.py`, extend `PlnExtension` dataclass, update extract/strip/reinject
methods. Add a regression test against a fixture file that exercises it.

**Verify round-trip on a new file**: drop the file in `tests/fixtures/`,
add a parameterized test or run `python -m pln_nmm.cli roundtrip` and
diff the input and output.

## When in doubt

Read `src/pln_nmm/adapter.py` end to end. It is ~250 lines and is the
heart of the project. Everything else is glue around it.
