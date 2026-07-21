# 07 - Phases

## Phase 1 - Parser Kernel

Status: active and mostly working.

- Preserve PLN extensions.
- Round-trip valid EQ through cimpy.
- Diagnose unresolved `$(Isi_*)` template placeholders.
- Expose CLI inspect and roundtrip commands.

## Phase 2 - SLD Web Editor MVP

- FastAPI upload/import API.
- React + TypeScript workspace.
- React Flow SLD canvas.
- Diagnostics panel for unresolved `$(Isi_*)` tokens.
- Initial SLD rendering from PLN coordinates where available.
- Manual creation/editing for busbars, transformers, and line/corridor symbols.

## Phase 3 - Tolerant SLD Extraction

- Read enough XML directly to render SLDs even when cimpy import is blocked.
- Extract object class, mRID/rdf:ID, labels, terminals, connectivity nodes, and
  `plnicp` coordinates.
- Treat switching/bay details as schematic annotations unless source evidence is
  strong enough to identify them.

## Phase 4 - Data Quality And Normalization

- Add dangling reference diagnostics.
- Classify placeholder fields by expected input type.
- Add repair/fill workflow for unresolved template values.
- Store validation reports in backend-ready JSON.

## Phase 5 - Canonical XML Review Workflow

- Compare canonical drafts against recent CIM/XML and approved SLD evidence.
- Keep provenance, confidence, and technical-parameter status explicit.
- Review single-GI bay connectivity before promoting system-level topology.
- Keep inferred switching equipment and diagram coordinates reviewable.

## Phase 6 - Topology And Analysis

- Evaluate cimpy bus-branch conversion.
- Produce NetworkX graph.
- pandapower conversion.
- Load-flow execution and result visualization.
- Export edited CIMXML / PLN-compatible EQ.

## Phase 7 - CGMES Expansion

- Add TP/SSH/SV support.
- Evaluate PowSyBl for full CGMES package validation and exchange.
- Consider standard Diagram Layout profile migration.
