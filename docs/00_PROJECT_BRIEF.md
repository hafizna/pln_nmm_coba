# 00 — Project Brief

Direction finalized 25 September 2026.

## Objective

Evaluate whether PLN can build a governed Network Model Management layer from
existing data **without requiring large-scale manual re-entry**.

The first feasibility unit is **one GI**.

## MVP contract

Input:

- structurally cleaned asset extract for one GI;
- matching/relevant GI SLD with revision/source information.

Review:

- per bay, exception-only.

Output:

- canonical GI network graph;
- generated SLD;
- CIM/XML;
- reconciliation/provenance/readiness report;
- published model version.

## Why one GI

Per bay is too narrow to establish busbar/coupler/inter-bay context.

Raw UPT/ULTG bulk is too broad for the first feasibility test because it mixes
enterprise cleansing with network reconstruction.

Future bulk support will stage/clean data and split it into independent GI jobs.

## Product boundary

NMM is the SSOT for the **published network model**, not for every upstream
native fact.

It does not replace:

- asset master/Maximo;
- approved SLD/as-built source;
- EMS/SCADA;
- protection repositories;
- PowerFactory/PSS®E/ETAP.

It reconciles them through stable identity, topology, provenance, versioning and
publication governance.

## Immediate acceptance question

> Can one GI be reconstructed from existing asset data + SLD evidence with
> substantially less engineering effort than rebuilding the model manually?

The result determines whether to scale, improve upstream data first, or re-scope.
