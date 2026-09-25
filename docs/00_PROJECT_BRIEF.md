# 00 — Project Brief

Direction updated 25 September 2026.

## Why this repository exists

The 2025 NMM PoC demonstrated that a CIM-based integration path can reach
PowerFactory and return simulation state variables. It did not yet prove that
existing PLN data can populate and maintain an authoritative network model at
scale.

This repository now focuses on that missing feasibility question.

## Immediate milestone

Prove one real GI end-to-end using existing evidence:

1. ingest asset/MxLoader/ED data without retyping it;
2. ingest the approved GI SLD as topology evidence;
3. reconcile assets to functional equipment;
4. ask an engineer only about unresolved mappings/conflicts;
5. build explicit electrical topology;
6. validate and publish a versioned canonical model;
7. export CIM/XML and an automatically generated SLD;
8. measure automation rate and review burden.

A poor automation result is still useful: it indicates that upstream data
governance must improve before scaling.

## Product boundary

NMM is the governed network-model layer. It does not replace:

- Maximo / enterprise asset master;
- EMS/SCADA operational systems;
- SLD/as-built repositories;
- protection/setting repositories;
- PowerFactory, PSS®E or ETAP.

Upstream systems remain authoritative for their native facts. NMM reconciles
those facts into one published network model with stable identity, topology,
provenance, versioning and readiness.

## Core concepts

Keep separate:

- raw source evidence;
- physical asset;
- functional electrical equipment;
- Terminal/ConnectivityNode topology;
- scenario/operating state;
- engineering parameters;
- diagram layout;
- published model version.

Unknown is never silently converted into zero, closed, or verified.

## Governance

SSOT requires an accountable Network Model Owner plus domain owners/stewards.
See [17_SSOT_GOVERNANCE.md](17_SSOT_GOVERNANCE.md). Proposed organizational
assignments are discussion material for BPO and must not be treated as formal
mandate until confirmed.

## Repository direction

Existing CIM kernel, Babel intake, validators, line-review work, Bali fixtures
and workbook experiments are retained. New work should migrate toward the target
architecture in [19_REPO_TARGET_STRUCTURE.md](19_REPO_TARGET_STRUCTURE.md)
without a big-bang rewrite.
