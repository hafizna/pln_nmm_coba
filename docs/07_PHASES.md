# 07 — One-GI SSOT MVP Phases

Direction updated 25 September 2026. The previous full-Bali milestone is deferred
until the source-to-canonical-model workflow is proven on one real GI.

## Phase 0 — Governance contract

Before production scale, BPO must designate:

- Network Model Owner;
- authoritative source per data domain;
- domain stewards/reviewers;
- publication approval flow;
- security/access classification;
- downstream model consumers and refresh SLA.

The software pilot may proceed before all production governance is finalized,
but assumptions must remain explicit.

## Phase 1 — One-GI source intake

- Choose one GI with a usable asset register and approved SLD.
- Preserve raw source files, hashes, timestamps and source row/page references.
- Reuse the Babel MxLoader adapter where applicable.
- Do not infer electrical connectivity from LOCATION/PARENT hierarchy.

Acceptance:

- source assets are ingested without manual re-entry;
- duplicate/source-identity findings are explicit;
- source refresh can be compared.

## Phase 2 — Functional equipment reconciliation

- Group phase-level physical assets where evidence supports one functional object.
- Map physical asset type to functional CIM/network role.
- Use SLD evidence to resolve bus/line/transformer/coupler roles.
- Generate AUTO_RESOLVED / REVIEW_REQUIRED / UNRESOLVED decisions.

Acceptance:

- no silent assignment of ambiguous PMS/DS roles;
- all mapping decisions preserve evidence and reviewer state;
- one functional object may map to multiple physical assets.

## Phase 3 — Canonical topology

- Build Substation, VoltageLevel, Bay, Equipment, Terminal and ConnectivityNode.
- Keep CT/PT/CVT/LA semantics distinct from switching/conducting topology.
- Validate dangling references, branch structure and boundary nodes.
- Separate normal state, scenario state and diagram layout.

Acceptance:

- zero dangling references in publishable topology;
- assumptions/conflicts remain visible;
- same evidence produces deterministic canonical identities.

## Phase 4 — Publish and review

- Auto-render PLN-oriented SLD from topology.
- Make XY drag an optional layout override, never a connectivity input.
- Export canonical JSON/model state and CIM/XML.
- Re-import the export and compare identity/topology/provenance.
- Publish model-version manifest and readiness states.

Acceptance:

- ASSET_READY / TOPOLOGY_READY / CIM_READY reported independently;
- round-trip does not silently drop supported objects/relations;
- model can be rebuilt from the same evidence.

## Phase 5 — Feasibility decision

Measure:

- source rows ingested without retyping;
- automatic functional grouping;
- automatic topology derivation;
- number of human review decisions;
- unresolved/conflicting evidence;
- elapsed time to reviewed publication;
- change behavior after source refresh.

BPO uses the results to decide whether to scale to more GI or first improve
upstream data governance.

## Phase 6 — Engineering enrichment

Only after topology feasibility:

- line R/X/B and ratings;
- transformer electrical model;
- load/generation P/Q and scenario;
- study-ready parameter validation;
- early PowerFactory/PSS®E/ETAP import tests.

NMM remains the model provider; solvers remain external.

## Phase 7 — Scale and advanced integration

- multiple GI / SS / system model;
- operational-state integration;
- protection/defense-scheme context;
- broader CGMES profiles and package validation;
- controlled external/cross-utility exchange where required;
- production hosting, RBAC, audit and release automation.
