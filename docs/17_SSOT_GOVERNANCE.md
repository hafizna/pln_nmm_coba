# 17 — SSOT Governance and Security Proposal

Status: proposal for BPO discussion. Organizational ownership below is a starting
point, not a statement of current formal mandate.

## SSOT principle

A sustainable NMM needs **federated ownership with canonical publication**.

No single team should manually own every field. Instead, BPO should designate:

- a Network Model Owner accountable for the published model;
- domain Data Owners for authoritative source domains;
- Data Stewards who resolve data-quality findings;
- an NMM Platform Custodian responsible for software, validation and releases;
- model reviewers/approvers for publication.

The published NMM release is the SSOT for the **network model**, while upstream
systems remain authoritative for their native facts.

## Proposed domain ownership

| Domain | Candidate authoritative source | Proposed steward/approver discussion |
|---|---|---|
| Physical asset identity/lifecycle | Maximo / enterprise asset source | UIT + asset-master owner |
| As-built primary topology | approved SLD / commissioning/as-built package | UIT / engineering owner |
| Operational topology/state | EMS/SCADA / dispatch-approved operating data | P2B |
| Protection & defense-scheme data | protection/setting repositories | OSL / protection owner |
| Engineering taxonomy / equipment standards | corporate engineering standards | TSJ / RST as applicable |
| Electrical study parameters | approved setting/design/study sources | designated engineering owner |
| Canonical identity, reconciliation, release | NMM registry | BPO-designated Network Model Owner |
| Platform operation & validation | NMM application | NMM Platform Custodian |
| Access policy & cyber controls | PLN security governance | designated cyber/security owner |

Exact assignments must be confirmed by BPO. The important design decision is
that every field category has an explicit source and accountable owner.

## Change workflow

1. Source system changes.
2. NMM ingests a new immutable snapshot.
3. Automatic diff and reconciliation run.
4. Non-conflicting authoritative changes are proposed.
5. Conflicts or topology ambiguity enter a review queue.
6. Domain steward resolves evidence.
7. Network Model Owner approves the release.
8. Versioned model is published to downstream applications.
9. Every downstream package records its source model version.

No silent overwrite of reviewed values.

## Security model

NMM should be designed for PLN-controlled deployment from the beginning:

- private/on-premise or approved PLN cloud deployment;
- no requirement to expose the network model publicly;
- RBAC by role and domain;
- least-privilege source connectors;
- read-only source ingestion by default;
- write-back disabled until a separate approved workflow exists;
- immutable raw source snapshots;
- field-level provenance and audit log;
- versioned releases and rollback;
- separation of draft, reviewed and published models;
- encrypted transport and storage according to PLN policy;
- sensitive topology/export controls based on model scope;
- service-to-service credentials isolated from user sessions.

## Governance objects NMM must store

For each important fact:

- source system/file;
- source record/page/row/object;
- source timestamp/version/hash;
- authoritative-domain label;
- confidence/evidence status;
- reviewer;
- approval timestamp;
- superseded value/history;
- published model version.

This makes NMM useful for audit and reconciliation, not just conversion.

## Decision BPO needs to make

Before scaling beyond a pilot GI:

1. Who is accountable for the published network model?
2. Which source is authoritative for each domain?
3. Who must approve topology changes?
4. Which downstream applications are consumers?
5. What refresh SLA is required?
6. What classification/access policy applies?
7. Is NMM allowed to publish only, or eventually write back upstream?

Without these decisions, NMM risks becoming another database rather than an SSOT.
