# 06 ? Architecture

## Existing foundation

Python pln_nmm wraps cimpy for EQ import/export and PLN extension preservation.
FastAPI inspection endpoints and React/TypeScript/React Flow workspace already
live here. Tolerant XML extraction supports diagnostics and SLD inspection when
semantic import is blocked.

## Target milestone pipeline

Source files / SLD_engine snapshot / asset register
? staged observations and identity reconciliation
? canonical equipment/connectivity plus asset extensions
? system and GI diagram projections
? versioned local package save/export/import.

Scenario and snapshot records reference the same model IDs but remain separate
from asset ratings and geometry. Start with local files; a production database,
authentication, hosting, and live integration are not milestone dependencies.

## Profile boundary

Use supported CIM16/CGMES 2.4.15 EQ classes for electrical structure. The installed
cimpy profile lacks CurrentTransformer/PotentialTransformer classes; do not
assume full CIM coverage or silently discard instrumentation.

Implement an explicit PLN extension preservation path for unsupported asset
objects/fields, including attachment references. Existing property preservation
does not prove unsupported whole-object preservation. Test new support.

Normal switch position belongs to EQ; scenario open belongs to SSH in CGMES.
For the first milestone, use a versioned scenario companion rather than
misrepresent scenario state as standard EQ. Native SSH/TP/SV/DL/GL support is later.

SLD_engine remains separate. Imported evidence records keep repository revision,
source IDs and document references. Renderer reuse, if needed, requires a
separate code/license review; no runtime coupling is assumed.
