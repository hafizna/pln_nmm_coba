# 16 — Reengineering Direction: One-GI SSOT MVP

Status: proposed direction after reviewing the 2025 NMM PoC, the Babel PST/MxLoader
asset source, and the current reconstruction branch.

## Reframe the problem

The next question is no longer whether CIM XML can be imported into a simulation
tool. The 2025 PoC already demonstrated a narrow ED → CIM → PowerFactory → SV
round-trip.

The unresolved question is more important:

> Can existing PLN data be transformed into a maintainable, electrically meaningful
> network model with minimal re-entry, explicit evidence, and auditable human review?

That is the feasibility gate for a production NMM.

## Product thesis

NMM is not a replacement for Maximo, EMS/SCADA, SLD repositories, protection
databases, or PowerFactory/PSS®E/ETAP.

NMM is the canonical **network-model layer** joining those domains:

- asset identity and lifecycle remain in the asset master;
- as-built/topology evidence comes from approved engineering sources;
- operational state comes from operational systems;
- protection/engineering parameters remain owned by their domain;
- NMM reconciles those facts into one versioned network graph;
- CIM/CGMES is an interchange/semantic representation of that graph;
- external engineering applications execute the studies.

SSOT therefore does **not** mean one database becomes authoritative for every
field. It means one canonical object identity, one explicit authoritative source
per field/domain, and one governed published network-model version.

## MVP scope

The first product milestone is deliberately small:

**one real GI**

Inputs:

1. existing asset register / MxLoader export;
2. existing approved SLD for that GI;
3. optional user confirmation only for unresolved mappings.

Outputs:

1. canonical asset-to-functional-equipment mapping;
2. explicit Terminal/ConnectivityNode topology;
3. generated SLD view;
4. CIM/XML export;
5. readiness/quality report;
6. provenance and unresolved-review queue.

Not MVP:

- load flow execution;
- short-circuit calculation;
- protection-setting calculation;
- defense-scheme simulation;
- CGMES cross-border exchange;
- continuous SCADA synchronization.

Those become enrichment/integration phases after the topology pipeline is proven.

## Design rule: no manual re-entry of known data

Users should not rebuild existing asset records in a second application.

The system must ingest source data, normalize it, propose matches, and request
human input only for facts that the source cannot establish.

Example:

- three R/S/T Circuit Breaker asset rows may map automatically to one functional
  `Breaker`;
- three generic Disconnecting Switch candidates cannot be silently assigned to
  Bus-I / Bus-II / Line roles without SLD evidence;
- the UI should ask only for that ambiguity, not for manufacturer, install date,
  asset number, or other fields already present upstream.

## Canonical layers

Keep these separate:

1. **Raw evidence** — immutable source snapshots, file hash, sheet/page/row.
2. **Physical asset** — source asset identity and lifecycle fields.
3. **Functional equipment** — electrical role represented in the network model.
4. **Electrical topology** — Terminal and ConnectivityNode relations.
5. **Operational/scenario state** — switch state, load/generation snapshot.
6. **Engineering parameters** — impedance, ratings, transformer model, etc.
7. **Diagram layout** — coordinates and presentation only.
8. **Published model** — reviewed release used by downstream tools.

A diagram coordinate must never substitute for electrical connectivity.

## What to retain from the current branch

The current `restructure/cim-layer` branch contains useful assets that should be
preserved:

- lossless CIM extension round-trip kernel;
- Babel MxLoader intake with raw row provenance;
- explicit inventory-only guard;
- assumed line-bay review that keeps assumptions visible;
- line-review XML reader/writer;
- workbook validator;
- profile checks and DL separation;
- local web viewer and review concepts.

The major change is priority: the workbook is no longer the product's central
manual contract. It becomes an optional import/export/review surface around the
canonical model.

## Acceptance question

The One-GI MVP should measure:

- percentage of physical assets recognized automatically;
- percentage grouped into functional equipment automatically;
- percentage of topology reconstructed from asset + SLD evidence;
- number of human decisions required;
- unresolved/contradictory facts;
- time to publish a reviewed model;
- reproducibility after a source refresh;
- CIM validation / downstream import result.

A successful prototype reduces human work. It does not merely move manual work
from one spreadsheet into another.
