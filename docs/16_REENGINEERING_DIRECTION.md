# 16 — Reengineering Direction

Status: **finalized MVP direction — 25 September 2026**

## Core decision

The application MVP processes **one GI at a time**.

Input:

- structurally cleaned asset table for the GI;
- corresponding SLD GI with known source/revision.

Review:

- per bay.

Output:

- one canonical GI model;
- generated SLD;
- CIM/XML;
- reconciliation/provenance/readiness report.

Raw bulk ULTG/UPT/SS ingestion is not the first UI contract. In production it can
exist as an upstream staging/orchestration layer that splits work into independent
GI jobs.

## Why this boundary

### Not per bay

A bay alone lacks enough context to establish:

- busbar arrangement;
- coupler/bus section relationships;
- consistency across bays;
- transformer links between voltage levels;
- line/circuit naming and endpoint consistency.

Bay remains the best **review** unit, not the best input/publication unit.

### Not raw bulk first

A bulk ULTG/UPT source combines two different problems:

1. master-data ETL/cleansing;
2. electrical network reconstruction.

Solving both in MVP makes it difficult to measure whether NMM itself reduces
network-model work.

Therefore the pilot deliberately starts after structural cleansing.

## Where cleansing stops

Before NMM:

- asset/source identity resolved;
- GI scope resolved;
- location/bay containment resolved;
- basic asset type normalized;
- obvious duplicate/orphan issues reported;
- original source provenance retained.

Inside NMM:

- phase rows grouped into functional equipment where justified;
- switching role inferred/reconciled using SLD evidence;
- equipment order/connectivity constructed;
- Terminal/ConnectivityNode generated;
- topology validated;
- readiness published.

If users must manually pre-enter topology in Excel, the product has failed its
purpose.

## Product thesis

NMM is a governed **network-model layer**, not a replacement for upstream
systems.

```text
Asset master / ED ───┐
Approved SLD ────────┤
Operational systems ─┤
Engineering sources ─┘
          │
          ▼
       Evidence
          │
          ▼
       Reconcile
          │
          ▼
 Canonical Network Graph
          │
     ┌────┼─────┐
     ▼    ▼     ▼
   CIM   SLD   downstream engineering tools
```

The canonical graph is the domain core. CIM/XML is a serialization/interchange
representation.

## SSOT interpretation

SSOT does not require NMM to own every source field.

It requires:

- stable canonical identities;
- explicit authoritative source per domain;
- auditable reconciliation;
- governed model publication;
- downstream consumers referring to a model version.

## Existing repo work to retain

Keep:

- CIM extension round-trip kernel;
- Babel MxLoader/PST intake;
- row/hash provenance;
- inventory-only guard;
- explicit assumption handling;
- validators/profile checks;
- line-review XML experiments;
- web review concepts.

Reposition:

- workbook → adapter/review artifact;
- manual XY → optional presentation override;
- assumed topology → review evidence, never silent truth;
- builder → canonical model serializer;
- viewer → topology/reconciliation/publish workspace.

## Acceptance statement

A successful One-GI pilot is not “XML generated successfully.”

It is:

> Existing source data can be transformed into an electrically meaningful,
> reviewable, reproducible GI model with substantially less human work than
> rebuilding the SLD/model manually.
