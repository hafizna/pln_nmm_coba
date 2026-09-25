# 18 — One-GI MVP Product Contract

## Goal

Prove one real GI end-to-end from **cleaned asset data + existing SLD** into a
versioned canonical model with minimal manual re-entry.

## Input contract

### A. Cleaned asset workbook

Minimum logical fields:

| Field | Required | Purpose |
|---|---|---|
| source_asset_id / ASSETNUM | yes | source identity |
| gi_id / gi_name | yes | scope |
| location_id / bay/location name | yes | containment |
| asset_type_raw | yes | traceability |
| asset_type_normalized | yes | basic normalization |
| description | yes | matching evidence |
| phase | if available | grouping evidence |
| NIA / TECHIDENTNO | if available | additional identity/matching |
| manufacturer / serial / install date | if available | asset facts, not topology |
| source reference/version | yes | provenance |

The input must not require pre-filled electrical topology.

### B. SLD

Preferred:

- one GI;
- full primary SLD;
- known revision/date;
- approved/as-built if available;
- legible equipment/bay/circuit labels.

The SLD supplies topology evidence that the asset table does not contain.

## User workflow

### 1. Upload GI package

System stores source fingerprints and validates scope.

### 2. Inventory check

System verifies:

- one GI scope;
- unique source identities;
- containment consistency;
- supported/basic asset types;
- missing/duplicate findings.

### 3. Functional grouping

Examples:

```text
CB-R
CB-S
CB-T
  ↓
candidate functional Breaker ABC
```

Grouping remains evidence-based and reviewable.

### 4. SLD evidence extraction

Represent:

- busbars;
- bay boundaries;
- PMT/PMS/ES role;
- line/transformer/generator endpoints;
- measurement/protection primary equipment presence where visible;
- connection sequence.

### 5. Reconciliation

Results:

- `AUTO_RESOLVED`
- `REVIEW_REQUIRED`
- `CONFLICT`
- `UNRESOLVED`

Only exceptions go to user review.

### 6. Bay review

Example:

```text
Bay MUNTOK #1
✓ CB group resolved
✓ CT set resolved
? DS #1 = PMS Bus-I
? DS #2 = PMS Bus-II
? DS #3 = PMS Line
```

User confirms ambiguous engineering facts, not source-known asset metadata.

### 7. Canonical graph

Minimum domain objects:

- Substation;
- VoltageLevel;
- Bay;
- functional Equipment;
- Terminal;
- ConnectivityNode;
- physical Asset mapping;
- provenance/evidence;
- boundary;
- readiness state.

### 8. Validate and publish

Outputs:

- canonical model state;
- generated SLD;
- CIM/XML;
- review/conflict report;
- model version;
- readiness status.

## UI

Five main views:

1. **Sources**
2. **Inventory**
3. **Reconcile**
4. **Topology**
5. **Publish**

XY dragging is optional layout adjustment only.

## Readiness

MVP targets:

- `ASSET_READY`
- `TOPOLOGY_READY`
- `CIM_READY`

It does not require `LOADFLOW_READY` or `PROTECTION_STUDY_READY`.

## Scale path

Future bulk input:

```text
UPT / ULTG / SS bulk
       ↓
 staging + cleansing
       ↓
 per-GI splitter
       ↓
 independent One-GI workflow
```

This preserves the same domain contract when the platform scales.
