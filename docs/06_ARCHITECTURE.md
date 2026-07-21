# 06 - Architecture

## Recommended Shape

Keep this repository as the parser/serializer kernel and build the web platform
around it.

Backend:

- Python FastAPI
- `pln_nmm` kernel for import/export/diagnostics
- NetworkX for derived topology
- pandapower for first load-flow integration

Frontend:

- React + TypeScript
- React Flow for first SLD editor
- Cytoscape.js later if graph-scale exploration becomes central

Storage:

- PostgreSQL + JSONB first
- PostGIS later only for geographic coordinates or map overlays

## Why Not Replace cimpy Now

cimpy already gives a working path for valid CGMES 2.4.15 EQ round-trip. The
larger fixture problem is not that cimpy is the wrong tool; it is that the file
contains unresolved template prompts in typed fields. A diagnostics and
normalization layer should come before any library replacement.

RDFLib may be useful for tolerant RDF querying, and PowSyBl may be useful once
full CGMES package workflows are in scope. Neither should replace the current
lossless adapter kernel yet.
