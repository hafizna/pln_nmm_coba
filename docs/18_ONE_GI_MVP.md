# 18 — One-GI MVP Product Flow

## Goal

Prove that one real GI can be reconstructed from existing PLN evidence with
minimal manual re-entry and published as a versioned canonical network model.

## User flow

### 1. Create/import GI scope

User selects one GI and uploads:

- asset/MxLoader workbook;
- approved SLD file (PDF, image, VSD/export, or structured SLD source if available).

The original files are stored as immutable evidence.

### 2. Inventory normalization

The backend:

- resolves GI and bay containment from explicit source keys;
- normalizes equipment types;
- retains every physical asset row;
- detects phase labels and possible R/S/T grouping;
- never infers electrical connection from LOCATION hierarchy alone.

### 3. SLD evidence extraction

Initial implementation may be manual-assisted. The target extractor identifies:

- busbars;
- bay boundaries/labels;
- PMT/PMS/earth-switch roles;
- line/transformer/generator endpoints;
- CT/PT/CVT/LA presence where visible;
- connection order.

The SLD is evidence. It is not automatically authoritative when ambiguous.

### 4. Reconciliation

The engine compares asset inventory and SLD evidence.

Three outcomes:

- **AUTO_RESOLVED** — source evidence is unambiguous;
- **REVIEW_REQUIRED** — multiple candidates or conflicting evidence;
- **UNRESOLVED** — required fact is absent.

Only REVIEW_REQUIRED items are shown to the engineer.

### 5. Canonical graph

After review, the model contains at minimum:

- Substation;
- VoltageLevel;
- Bay;
- functional ConductingEquipment;
- AuxiliaryEquipment/asset attachments where supported;
- Terminal;
- ConnectivityNode;
- physical-asset mapping;
- provenance per mapping/field.

### 6. Validation

Validation produces independent readiness states:

- `ASSET_READY`
- `TOPOLOGY_READY`
- `CIM_READY`
- `LOADFLOW_READY`
- `PROTECTION_STUDY_READY`

Completing one state must not imply the next.

### 7. Publish

For the MVP, publish:

- canonical model JSON/database state;
- CIM/XML package;
- auto-generated SLD;
- reconciliation report;
- model-version manifest.

Later enrichment can add electrical parameters and scenario profiles without
rebuilding the asset/topology layers.

## Proposed UI

The web workspace should have five main views:

1. **Sources** — uploaded evidence, hashes, dates, scope.
2. **Inventory** — physical assets and grouping suggestions.
3. **Reconcile** — exception-only review queue.
4. **Topology** — generated SLD/network graph and validation findings.
5. **Publish** — readiness status, diff, version, export.

Dragging XY remains an optional diagram override. It is not required to define
connectivity.

## Pilot metrics

Suggested pilot targets for discussion, not fixed acceptance policy:

- ≥ 95% source asset rows ingested without manual retyping;
- ≥ 80% functional grouping automatically proposed;
- ≥ 80% topology relations derived from source evidence;
- < 20% model objects requiring human decision;
- 100% unresolved assumptions visible;
- zero dangling references in published topology;
- deterministic repeat build from the same evidence;
- source refresh produces an explicit diff rather than duplicate records.

If one GI requires extensive manual reconstruction, that is a valid feasibility
finding: upstream data governance must improve before national scale.
