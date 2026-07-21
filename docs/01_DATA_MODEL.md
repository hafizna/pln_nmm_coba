# 01 - Data Model

## Current Kernel Model

The current package has two layers:

1. A lossless XML side-table keyed by canonical mRID.
2. The cimpy object graph for files that are semantically valid CGMES 2.4.15 EQ.

The side-table stores PLN-only extensions that cimpy does not model:

- `plnicp:DiagramProperty.x`
- `plnicp:DiagramProperty.y`
- `nhftui:info`

The canonical key is `rdf:ID` with the leading underscore stripped. This must
remain true even when `cim:IdentifiedObject.mRID` disagrees, because cimpy emits
the `rdf:ID`-derived form on export.

## Platform Model

The web platform should store three related representations:

- Raw CIM XML file version, for audit and exact export lineage.
- Normalized CIM object records, preferably in PostgreSQL JSONB first.
- Derived topology graph, produced from CIM terminals, connectivity nodes,
  conducting equipment, and transformers.

PostGIS should be added only when the product needs real geographic coordinates
or map overlays. The current `plnicp` x/y values are diagram canvas coordinates,
not geospatial coordinates.

## Data Quality State

Objects and files need validation state:

- `raw`: uploaded but not inspected.
- `needs_input`: unresolved `$(Isi_*)` placeholders exist.
- `valid_eq`: cimpy can import the EQ profile.
- `topology_ready`: bus-branch graph can be derived.
- `load_flow_ready`: required electrical parameters are complete enough for
  pandapower.

`$(Isi_*)` values are template prompts. They should be shown to users as fields
to complete, not hidden as parser errors.
