# PLN Network Model Management (NMM)
## One-GI SSOT Feasibility → CIM Interchange → Engineering Model Reuse

> **Active direction — 25 September 2026**
>
> MVP menerima **satu GI yang sudah structurally cleaned + corresponding GI SLD**.
> Review dilakukan per bay dan hasil dipublish per GI.
>
> Bulk ULTG/UPT/SS adalah fase berikutnya melalui staging/cleansing dan per-GI
> job splitter.

NMM adalah **canonical network-model layer**, bukan asset register kedua, bukan
drawing tool utama, dan bukan solver.

Product thesis:

> **one canonical identity + one authoritative source per domain + one governed
> published network model**

Core flow:

```text
clean asset + GI SLD
        ↓
normalize / extract evidence
        ↓
reconcile
        ↓
review only ambiguity/conflict
        ↓
canonical GI graph
        ↓
CIM/XML + generated SLD + readiness/provenance
```

MVP berhenti di:

- `ASSET_READY`
- `TOPOLOGY_READY`
- `CIM_READY`

Load flow/protection completeness menyusul sebagai enrichment.

## Start here

Untuk konteks produk, governance, kontrak MVP, dan permintaan data BPO, gunakan
**satu master document**:

- [NMM SSOT Realignment + One-GI Pilot + BPO Data Request](docs/16_NMM_SSOT_REALIGNMENT_AND_PILOT.md)

Dokumen pendukung yang tetap terpisah karena sifatnya teknis:

- [Implementation roadmap](docs/07_PHASES.md)
- [Target repository structure](docs/19_REPO_TARGET_STRUCTURE.md)
- [BPO discussion HTML](docs/bpo/NMM_BPO_DISCUSSION.html)

## Current implementation assets retained

Branch `restructure/cim-layer` sudah menyediakan fondasi yang tetap dipakai:

- CIM round-trip kernel;
- Babel/MxLoader intake + row/hash provenance;
- inventory-only guard;
- assumption-aware line-bay review;
- validators/profile checks;
- local viewer;
- experimental line-review XML.

Arah migrasi:

```text
intake → canonical → reconcile → topology → validate → serialize → publish
```

## Development commands

```powershell
python -m pip install -e ".[dev,web]"
python -m pytest -q
python -m uvicorn pln_nmm_web.api:app --host 127.0.0.1 --port 8000 --reload
```

Current code remains transitional. Existing demo output must not be interpreted
as verified as-built network data.
