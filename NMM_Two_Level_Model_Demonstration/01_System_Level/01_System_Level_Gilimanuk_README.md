# GI Gilimanuk NMM/CIM Proof of Concept

## Scope
This package reconstructs a canonical node-breaker model for GI Gilimanuk using:
- `CIM_sample-db_userdef_python.xml` as the source object inventory;
- the supplied overview SLD Bali Utara as the topology and rating reference;
- `02d_CIM_EQ_1-SS_Filled-WithCoordinate_250604.xml` as the coordinate-extension pattern.

## Files
- `Gilimanuk_NMM_POC_Canonical_Draft.xml` — canonical CIM/RDF XML draft.
- `Gilimanuk_NMM_POC_Review_Workbook.xlsx` — object registry, connectivity, mapping, assumptions, validation, and source diagnostics.

## Canonical output counts
- Breaker: 13
- Disconnector: 38
- ACLineSegment: 9
- PowerTransformer: 3
- SynchronousMachine: 1
- Terminal: 130
- ConnectivityNode: 51

## Key design decisions
1. One canonical Substation is used for GI Gilimanuk.
2. Every equipment side has a unique Terminal and every physical junction has a ConnectivityNode.
3. End-specific source line records are reconciled into one canonical inter-GI circuit.
4. CB/DS are generated as provisional objects using a double-bus single-breaker template.
5. Unknown electrical parameters are marked `PENDING`; they are not fabricated as zero.
6. Source mRIDs are preserved through `plnnmm:sourceObjectMRID` and the workbook mapping sheet.

## Important limitations
This is an SLD-derived draft, not an as-built or operationally approved model. Detailed substation SLDs,
SAP equipment identifiers, SCADA operational tags, conductor configuration data, transformer test sheets,
and generator/GSU data are required before load-flow use or production publication.
