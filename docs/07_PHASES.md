# 07 — Final Roadmap: One-GI SSOT Feasibility

Direction finalized 25 September 2026.

## Scope decision

**Input MVP:** one GI, structurally cleaned asset dataset + corresponding SLD.

**Review:** per bay.

**Published unit:** one GI canonical network model.

**Bulk ULTG/UPT/SS:** later orchestration; bulk is staged/cleaned then split into
independent per-GI jobs.

This decision keeps the MVP focused on the real NMM problem — reconstruction and
governance of electrical network semantics — instead of turning the first version
into a large ETL/master-data program.

## Phase 0 — Direction and governance framing

Status: **DONE**

- Define NMM as governed network-model SSOT, not second asset register.
- Define federated source ownership.
- Separate physical asset, functional equipment, topology, state, parameters,
  layout and published release.
- Define security/audit/versioning requirements.
- Define NMM as model provider; external apps execute studies.

Exit: product thesis and governance discussion documented.

## Phase 1 — One-GI input contract

Status: **NEXT**

Required pilot package:

```text
GI_<NAME>/
├── assets_clean.xlsx
└── SLD_<GI>.<supported format>
```

Clean asset input must retain:

- source asset ID;
- GI identity;
- bay/location containment;
- raw + normalized asset type;
- source description;
- phase if available;
- available NIA/TECHIDENTNO/manufacturer/install date;
- source/provenance identity.

It must **not** require the user to pre-enter Terminal, ConnectivityNode, PMS
role, electrical sequence, or diagram coordinates.

Exit:

- schema validated;
- sample GI package can be loaded deterministically;
- input gaps reported, not silently filled.

## Phase 2 — Physical asset normalization and functional grouping

Status: **NEXT**

Implement three evidence classes:

- **DETERMINISTIC** — directly established by source;
- **HEURISTIC** — high-confidence proposed grouping;
- **ENGINEERING_EVIDENCE_REQUIRED** — cannot be decided from asset table.

Examples:

- `Circuit Breaker → CB`: deterministic normalization.
- R/S/T CB rows → one functional breaker: heuristic/proposed until grouping rules
  are proven.
- which DS is Bus-I/Bus-II/Line: engineering evidence required.

Exit:

- physical asset remains lossless;
- one functional object can map to multiple assets;
- all heuristic decisions are reviewable.

## Phase 3 — SLD evidence extraction

Status: **NEXT**

Extract/represent:

- busbar configuration;
- bay labels/boundaries;
- PMT/PMS/earthing-switch role;
- line/transformer/generator endpoint;
- CT/PT/CVT/LA presence when supported by evidence;
- sequence/connectivity evidence;
- revision/source metadata.

Initial extraction may be assisted. The key requirement is evidence traceability,
not full computer vision automation.

Exit:

- SLD evidence has explicit source and confidence;
- ambiguous visual interpretation remains unresolved/reviewable.

## Phase 4 — Reconciliation and review UI

Status: **NEXT**

Compare cleaned inventory and SLD evidence.

Decision states:

- `AUTO_RESOLVED`
- `REVIEW_REQUIRED`
- `UNRESOLVED`
- `CONFLICT`

User sees only exceptions and ambiguous mappings.

Review unit = bay.

Exit:

- user does not retype source-known fields;
- review decisions are persisted with reviewer/evidence;
- source refresh does not silently overwrite reviewed decisions.

## Phase 5 — Canonical GI graph

Status: **NEXT**

Build:

- Substation;
- VoltageLevel;
- Bay;
- functional equipment;
- Terminal;
- ConnectivityNode;
- asset mapping;
- provenance;
- boundary objects;
- readiness state.

Rules:

- LOCATION/PARENT is containment, not electrical connectivity.
- XY is presentation, not topology.
- unknown ≠ zero/closed/verified.

Exit:

- zero dangling internal references;
- topology assumptions explicit;
- deterministic canonical identities.

## Phase 6 — CIM/XML + generated SLD

Status: **NEXT**

- serialize supported model to CIM/XML;
- re-import and compare semantic identity/connectivity;
- auto-render SLD from topology;
- preserve optional user layout override separately;
- publish reconciliation/readiness report.

Exit:

- `ASSET_READY`, `TOPOLOGY_READY`, `CIM_READY` evaluated independently;
- supported topology survives export/re-import;
- SLD can be regenerated without manually placing every object.

## Phase 7 — One-GI feasibility gate

Status: **GATE**

Measure:

- % rows ingested without retyping;
- % functional grouping automatic/proposed;
- % topology derived from source evidence;
- number of human decisions;
- unresolved/conflict count;
- time from source package to reviewed publication;
- source-refresh diff behavior;
- CIM validation/interoperability status.

BPO decision:

- **scale**, if automation and governance burden are acceptable;
- **improve upstream data first**, if manual reconstruction remains dominant;
- **stop/re-scope**, if business value does not justify maintenance cost.

## Phase 8 — Engineering enrichment

Status: **LATER**

Add only after topology feasibility:

- line R/X/B and rating;
- transformer model;
- load/generation P/Q;
- scenario/snapshot;
- study-readiness checks;
- PowerFactory/PSS®E/ETAP import interpretation tests.

Exit: `LOADFLOW_READY` where data is sufficient.

## Phase 9 — Bulk orchestration

Status: **LATER**

Support ULTG/UPT/SS input through:

```text
bulk source
→ staging/cleansing
→ GI scope resolution
→ per-GI job queue
→ independent review/publication
```

Exit:

- one GI failure/review does not block others;
- bulk refresh generates per-GI diffs;
- model ownership remains scoped and auditable.

## Phase 10 — Advanced integration

Status: **LATER**

Potential scope:

- EMS/SCADA operational state;
- native TP/SSH/SV packages;
- protection/defense-scheme context;
- planning/asset-criticality consumers;
- broader CGMES exchange;
- cross-utility/cross-border exchange if required;
- production RBAC/audit/release automation.

## Non-goals of MVP

Do not block the One-GI pilot waiting for:

- full national asset cleansing;
- real-time SCADA integration;
- complete load flow dataset;
- protection settings;
- automatic CV extraction of every SLD symbol;
- cross-border CGMES transaction readiness.

The MVP answers one question first:

> Can existing PLN asset data + an existing GI SLD become a trustworthy,
> maintainable network model with little manual re-entry?
