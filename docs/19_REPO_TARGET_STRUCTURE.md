# 19 — Target Repository Structure

This is the target structure for the reengineered product. Existing modules do
not need a big-bang move; migrate behind stable interfaces.

```text
src/pln_nmm/
  intake/
    asset/              # Maximo/MxLoader/ED adapters
    sld/                # SLD evidence adapters
    operations/         # future operational snapshots
    engineering/        # future parameter sources
  canonical/
    identity.py
    asset.py
    equipment.py
    topology.py
    provenance.py
    readiness.py
  reconcile/
    grouping.py
    topology.py
    conflicts.py
    review.py
  validate/
    structural.py
    topology.py
    cim.py
    readiness.py
  serialize/
    cim16/
    cgmes/
    json/
  diagram/
    layout.py
    pln_sld.py
  web/
    application services only; no domain logic

tests/
  fixtures/
    source_asset/
    source_sld/
    canonical/
  acceptance/
    one_gi/
```

## Migration map from the current branch

| Current module | Target responsibility |
|---|---|
| `sources/maximo.py` | `intake/asset/maximo.py` |
| `model/line_bay.py` | split into canonical topology + review assumptions |
| `model/line_xml.py` | serializer/review exchange, not canonical model |
| `builder/` | canonical → CIM serializer path |
| `sources/reconcile.py` | generalized reconcile service |
| `sld.py` | diagram/existing-CIM evidence reader |
| `topology.py` | validation/derived topology helpers |
| `pln_nmm_web` | thin application/API layer |

## Migration rules

- no source adapter may assign unverified electrical topology silently;
- no UI component owns domain truth;
- canonical IDs are stable across source refresh;
- raw evidence remains immutable;
- assumptions are first-class records, never hidden in layout coordinates;
- workbook is an adapter/view, not the canonical database;
- CIM XML is a serialization/export format, not the only in-memory model.

## First implementation slice

Do not move all files immediately.

1. Introduce canonical interfaces.
2. Adapt existing Babel intake to them.
3. Add one-GI SLD evidence adapter.
4. Implement exception-only reconciliation.
5. Export the reviewed canonical graph through the existing CIM kernel.
6. Only then retire duplicated line-review-specific model code.
