# Babel inventory intake — 23 September 2026

This is a source inventory stage, not a connected CIM model. The PST/MxLoader
workbook is read without executing macros or modifying its data. Babel is an
additional core-workflow fixture; the Bali milestone remains unchanged.

## Reproduce the extraction

```powershell
python scripts/prepare_babel_inventory.py "C:\lab\pln-maximo-lab\data\raw\MxLoader-mas_2_Location_GI_BAY_v1-1 (GI & BAY) (Babel).xlsm" outputs/babel_inventory_20260923
```

The local output includes `inventory.json` (raw records, scoped stable IDs,
sheet/row provenance, source SHA256 and findings) and `workbook_tables.json`
(tables following the existing NMM input headers, with inventory extensions).
Generated source data under `outputs/` is ignored by Git. The original file stays
at its source location. Re-extraction is a fresh snapshot; merging later manual
edits is not implemented, so preserve reviewed workbooks separately.

The accompanying `NMM_Babel_Inventory.xlsx` was authored from these tables. It
contains 01_GI and 02_BAY candidates, empty electrical/scenario sheets, and:

- 16_ASET_SUMBER: all 3,385 records joined through explicit bay-to-GI hierarchy,
  retaining primary, protection and auxiliary assets without phase collapsing.
- 17_LOKASI_SUMBER: all 75 source locations used by those assets, including
  buildings. Only 65 text-based bay candidates enter 02_BAY.
- 18_TEMUAN: records needing review, including otherwise excluded GI assets.
- 00_IMPORT_STATUS: source path/hash and INVENTORY_ONLY marker.

## Measured coverage

| Item | Count |
|---|---:|
| Source asset records | 51,551 |
| Joined GI identities | 10 |
| Joined asset records | 3,385 |
| Primary records (includes NGR) | 1,019 |
| Protection records | 126 |
| Auxiliary records | 2,240 |
| Not joined through the GI/bay tables | 48,166 |
| Primary records at a GEDUNG location | 124 |
| GI-group assets without this hierarchy join | 17 |
| Unreferenced GI location records | 10 |
| Records sharing a GI name with another location ID | 20 |

The 171 findings are finding rows, not 171 distinct faulty assets. A primary asset
in GEDUNG is a review candidate, not proof its placement is wrong. The broader
Locations_BBL_T&S network/tower hierarchy is outside this intake stage.

## Interpretation rules

Join on `(SITEID, LOCATION)` and `(SITEID, PARENT)`, never names alone. Preserve
source `ASSETNUM` as text and derive stable model IDs from site and source key.
Same-name GI records are not merged. Duplicate scoped IDs fail the import.
Maximo LOCATION is not silently written as SAP FUNCTLOC.

Bay type is a candidate inferred only for explicit KOPEL / TRAFO / BUS SECTION
labels. Other bay types stay unknown. Busbar configuration, electrical attachment,
normal/scenario switch positions, ratings and phase grouping remain unresolved.
ACTIVE is administrative status. CT/PT instrumentation is retained in inventory;
this does not establish CIM whole-object preservation support.

The CIM builder rejects workbooks marked INVENTORY_ONLY before creating output.
Do not remove the marker to bypass missing topology: actual-asset emission,
SLD reconciliation and the model's readiness validation still need implementation.
The empty 06_TRAFO sheet does not discard transformer assets: their 20 physical
records remain in 16_ASET_SUMBER pending winding/phase reconciliation.

## Next gate

Update 24 September: a separate assumed line-bay core review is implemented in
[15_LINE_BAY_RECONSTRUCTION.md](15_LINE_BAY_RECONSTRUCTION.md). It adds explicit
per-GI assumptions, connectivity and an HTML review without changing this source
inventory stage or enabling its CIM workbook export.

Review locations and primary-in-building findings; reconcile one GI against the
SLD handoff. Establish equipment grouping, bus arrangement and electrical
connections before populating model templates or generating terminals/CN.
