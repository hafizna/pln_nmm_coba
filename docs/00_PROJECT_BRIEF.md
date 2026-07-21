# 00 — Project Brief

> Status: active. Filled out incrementally as decisions are confirmed with
> stakeholders and fixtures.

## Vision

A web-based Network Model Management (NMM) tool for PLN Transmisi that
lets engineers import, edit, and export single-line diagrams of
substations and transmission corridors using the IEC 61970 CIM standard
(specifically CGMES 2.4.15 / CIM16, the format produced by PLN's
existing toolchain).

## Why

Today PLN's CIM toolchain is a Python script (Nur Hidayat's db config
v1.13) that string-substitutes templates and concatenates XML. This works
but does not survive round-trips through standard CGMES tools, has no
visual editor, and produces files with custom inline extensions
(`plnicp:DiagramProperty.x/y`, `nhftui:info`) that no external tool
understands.

The new tool should:

1. Parse PLN's existing files without losing the custom extensions.
2. Provide a web canvas for diagram editing.
3. Export back to the same custom format for backward compatibility,
   with an option to export standard CGMES for interoperability.
4. Eventually feed a load-flow solver.

## What this repo is

The parser/serializer kernel. v1 covers the EQ profile only and supports
bus-branch topology. The web UI, topology processor, and load-flow
integration will live in separate modules / repos and depend on this one.

## Scope decisions confirmed so far

- **CIM dialect**: CGMES 2.4.15 / CIM16 with the ENTSO-E EquipmentCore +
  EquipmentOperation profile, as in the PLN sample.
- **Custom extensions**: preserve `plnicp` and `nhftui` on round-trip.
- **Library backbone**: SOGNO cimpy (Apache 2.0). No fork. Adapter only.
- **Topology model for v1**: bus-branch. No switching equipment in the
  asset import path because PLN's physical asset data does not
  differentiate it. PMT and PMS will appear in the SVG palette as
  schematic-only annotations in a later phase.
- **Coordinate handling**: extract custom inline `plnicp` x/y on import
  into a side-table, reinject on export. Standard CGMES Diagram Layout
  profile is a future option but not v1.
- **Template placeholders**: unresolved `$(Isi_*)` values are treated as
  fields requiring user or upstream-generator input, not as arbitrary corrupt
  XML. The pure-XML adapter tolerates them; semantic cimpy import should be
  skipped until diagnostics are resolved.

## Open questions deferred to later phases

- Whether to migrate to standard DL profile in v2.
- Synthetic-bay generation for visual completeness.
- Inter-substation line container handling.
- Handling of ACLineSegments with missing electrical parameters.
- Solver choice (pandapower is the leading candidate).
- Where this lives in PLN's stack (standalone NMM vs integrated).

## Acceptance criteria for v1 (this repo)

- [x] PLN sample EQ file imports without errors.
- [x] All 126 cimpy objects resolve from the import.
- [x] Round-trip preserves all rdf:IDs.
- [x] Round-trip preserves all `plnicp:DiagramProperty.x/y` bit-exact.
- [x] Round-trip preserves all `nhftui:info` attributes.
- [x] Optional clean-CGMES export mode works.
- [x] CLI: inspect and roundtrip subcommands.
- [x] Tested against the larger sample database (`CIM_sample-db_userdef_python.xml`).
- [x] Documented data-quality findings exposed to callers for unresolved
      `$(Isi_*)` template placeholders and mismatched mRIDs.
- [ ] Dangling reference diagnostics.
