# PLN Network Model Management (NMM)
## One-GI SSOT Feasibility → CIM Interchange → Engineering Model Reuse

> **Active direction — 25 September 2026**
>
> MVP NMM menerima **satu GI yang sudah structurally cleaned + satu SLD GI yang
> relevan/approved**. Review dilakukan per bay. Bulk ULTG/UPT/SS adalah fase
> berikutnya dan nantinya dipecah menjadi job per GI.
>
> Tujuan MVP bukan menjalankan load flow di dalam NMM. Tujuannya membuktikan bahwa
> data PLN yang sudah ada dapat direkonsiliasi menjadi **network model yang
> versioned, auditable, secure, dan reusable** dengan input manual seminimal mungkin.

## 1. Product thesis

NMM adalah **canonical network-model layer** di antara:

- asset master / Maximo / ED;
- SLD dan dokumen as-built;
- sistem operasi/dispatch;
- data engineering dan protection;
- PowerFactory, PSS®E, ETAP, dan consumer lainnya.

NMM **bukan** asset register kedua, **bukan** drawing tool utama, dan **bukan**
solver.

SSOT di sini berarti:

> **one canonical identity + one authoritative source per domain + one governed
> published network model**

Upstream system tetap authoritative untuk native fact-nya. NMM menggabungkan
fakta tersebut menjadi satu model jaringan yang dapat dipakai ulang.

## 2. Keputusan scope MVP

### Input scope = satu GI

Aplikasi MVP **tidak menerima raw bulk UPT/ULTG sebagai input utama**.

Paket input MVP:

```text
GI_<NAME>/
├── assets_clean.xlsx
└── SLD_<GI>.<pdf|png|jpg|vsd|structured-export>
```

Asset file harus sudah **structurally cleaned**, minimal:

- GI identity diketahui;
- asset identity unik atau duplicate sudah ditandai;
- location/bay containment diketahui;
- asset type dasar sudah dinormalisasi;
- source identity/provenance tidak hilang;
- phase dipertahankan jika tersedia.

Yang **tidak perlu** diisi user sebelum masuk NMM:

- PMS Bus-I / Bus-II / Line role;
- terminal;
- ConnectivityNode;
- urutan electrical equipment;
- x/y diagram;
- parameter load flow;
- relay/protection setting.

Itu adalah bagian reconciliation/model-building NMM atau enrichment tahap lanjut.

### Review scope = per bay

Setelah satu GI di-upload, UI memecah hasil menjadi review per bay:

```text
GI KELAPA
├── Bay MUNTOK #1       REVIEW_REQUIRED
├── Bay MUNTOK #2       AUTO_RESOLVED
├── Bay KOPEL           REVIEW_REQUIRED
└── Bay TRAFO #1        UNRESOLVED
```

### Output scope = satu GI canonical model

MVP menghasilkan:

- physical asset ↔ functional equipment mapping;
- explicit Terminal/ConnectivityNode topology;
- generated SLD;
- CIM/XML export;
- provenance + reconciliation report;
- readiness status;
- model-version manifest.

## 3. Kenapa bukan per-bay input?

Per-bay terlalu sempit untuk memvalidasi:

- busbar scheme;
- Bus-I/Bus-II selection;
- coupler/bus section;
- transformer antar-voltage-level;
- consistency antar-bay;
- line/circuit endpoint.

Bay tetap menjadi unit review yang baik, tetapi **GI adalah unit input dan
publication terkecil yang masih memiliki konteks topologi cukup lengkap**.

## 4. Kenapa belum bulk UPT/ULTG?

Raw bulk intake adalah problem ETL/master-data yang berbeda dari problem network
model reconstruction.

Untuk MVP, memaksa aplikasi sekaligus menyelesaikan:

```text
50k+ raw rows
→ cleansing
→ GI split
→ asset grouping
→ SLD matching
→ topology
→ CIM
```

akan membuat feasibility NMM sulit diukur.

Production roadmap tetap mendukung bulk:

```text
UPT / ULTG / SS bulk source
          ↓
   staging / cleansing
          ↓
      scope splitter
          ↓
 ┌────────┼────────┐
 GI A     GI B     GI C
 job      job      job
```

Dengan demikian satu GI dapat gagal/review tanpa menggagalkan semua scope.

## 5. Core workflow

```text
CLEAN ASSET TABLE             APPROVED GI SLD
       │                              │
       ▼                              ▼
asset normalization      topology evidence extraction
       │                              │
       └──────────────┬───────────────┘
                      ▼
                RECONCILIATION
             ┌────────┼────────┐
             ▼        ▼        ▼
          AUTO    REVIEW    UNRESOLVED
             │        │
             │        ▼
             │   engineer review
             └────────┬────────┘
                      ▼
             CANONICAL GI GRAPH
                      │
        ┌─────────────┼──────────────┐
        ▼             ▼              ▼
      CIM/XML     generated SLD   readiness/report
```

Prinsip UX:

> **User corrects the model; user does not rebuild the model.**

## 6. Canonical layers

Layer berikut tidak boleh dicampur:

1. **Raw evidence** — source file/hash/row/page/revision.
2. **Physical asset** — asset identity dan lifecycle facts.
3. **Functional equipment** — fungsi electrical satu atau beberapa physical asset.
4. **Electrical topology** — Terminal + ConnectivityNode.
5. **Operational/scenario state** — open/closed, load/generation snapshot.
6. **Engineering parameters** — impedance, rating, transformer model, dll.
7. **Diagram layout** — x/y/rotation/presentation.
8. **Published model** — reviewed immutable release.

**XY bukan topology. LOCATION/PARENT bukan connectivity.**

## 7. Readiness ladder

| Level | Status | Minimum information | Output |
|---|---|---|---|
| L0 | `ASSET_READY` | identity + containment | reconciled inventory |
| L1 | `TOPOLOGY_READY` | functional role + terminal/connectivity | authoritative GI graph / SLD |
| L2 | `CIM_READY` | supported semantic/profile mapping | CIM/XML |
| L3 | `LOADFLOW_READY` | R/X/B, transformer model, P/Q, scenario | solver base case |
| L4 | `PROTECTION_STUDY_READY` | CT/PT, relay/settings/scheme context | protection study context |

**MVP acceptance berhenti di L2.**

L3/L4 adalah enrichment berikutnya dan tidak boleh memaksa topology dibangun ulang.

## 8. Roadmap final

| Phase | Status | Scope | Exit condition |
|---|---|---|---|
| 0. Direction & governance framing | **DONE** | SSOT role, source ownership concept, security framing | product thesis documented |
| 1. One-GI input contract | **NEXT** | cleaned asset workbook + approved GI SLD | fixture package accepted without re-entry |
| 2. Asset normalization & grouping | **NEXT** | physical asset → functional candidate | deterministic + heuristic mappings separated |
| 3. SLD evidence extraction | **NEXT** | busbar/bay/equipment/connectivity evidence | source evidence represented with confidence/provenance |
| 4. Reconciliation workflow | **NEXT** | asset ↔ SLD matching | AUTO / REVIEW / UNRESOLVED queue works |
| 5. Canonical GI graph | **NEXT** | Equipment + Terminal + ConnectivityNode | zero dangling internal references |
| 6. CIM + generated SLD | **NEXT** | serialization and diagram | export/re-import preserves supported semantics |
| 7. One-GI feasibility review | **GATE** | measure automation/review burden | BPO go/no-go for scale |
| 8. Engineering enrichment | **LATER** | line/trafo parameters, P/Q, scenario | `LOADFLOW_READY` and solver import test |
| 9. Bulk orchestration | **LATER** | ULTG/UPT/SS staging + GI job splitter | multiple GI processed independently |
| 10. Operational/protection/CGMES expansion | **LATER** | SSH/SV/TP, protection context, broader exchange | governed multi-domain integration |

## 9. Pilot metrics

Threshold berikut adalah **discussion target**, bukan kebijakan final:

- ≥95% source asset rows masuk tanpa manual retyping;
- ≥80% functional grouping dapat auto/proposed;
- ≥80% topology relation berasal dari source evidence;
- <20% model objects membutuhkan keputusan manusia;
- 100% assumption/conflict/unresolved terlihat;
- 0 dangling internal reference pada published topology;
- same input → deterministic same canonical identities;
- source refresh → explicit diff, bukan duplicate model.

Jika satu GI tetap membutuhkan reconstruction manual besar, itu adalah hasil
feasibility yang valid: upstream data governance perlu diperbaiki sebelum scale.

## 10. Data yang dibutuhkan untuk pilot

Untuk satu GI kandidat:

1. **cleaned asset extract** untuk GI tersebut;
2. **SLD GI** yang relevan dan sedapat mungkin approved/as-built;
3. metadata revisi/tanggal/source owner;
4. optional: kamus kode asset/type bila diperlukan.

Belum diperlukan untuk MVP:

- impedance lengkap;
- P/Q snapshot;
- relay setting;
- defense-scheme setting;
- SCADA real-time;
- CGMES transaction package.

Lihat [BPO data request](docs/20_BPO_DATA_REQUEST.md).

## 11. Governance

Production NMM membutuhkan:

- Network Model Owner;
- authoritative source per domain;
- Data Steward/reviewer per domain;
- Platform Custodian;
- publication approval;
- RBAC, audit, model versioning, dan source provenance.

Proposal lengkap: [docs/17_SSOT_GOVERNANCE.md](docs/17_SSOT_GOVERNANCE.md).

## 12. Current repo assets yang dipertahankan

Branch `restructure/cim-layer` sudah memberi fondasi penting:

- CIM16/CGMES 2.4.15 round-trip kernel;
- Babel PST/MxLoader intake + row/hash provenance;
- `INVENTORY_ONLY` guard;
- explicit assumed line-bay review;
- workbook validator;
- profile/DL checks;
- local web viewer;
- experimental line-review XML.

Aset tersebut **tidak dibuang**. Fokus migrasinya diubah menjadi:

```text
evidence → canonical graph → validate → serialize/publish
```

Workbook menjadi adapter/review surface, bukan canonical database.

## 13. Repository docs

- [Project brief](docs/00_PROJECT_BRIEF.md)
- [Final roadmap](docs/07_PHASES.md)
- [Reengineering direction](docs/16_REENGINEERING_DIRECTION.md)
- [SSOT governance](docs/17_SSOT_GOVERNANCE.md)
- [One-GI MVP](docs/18_ONE_GI_MVP.md)
- [Target repository structure](docs/19_REPO_TARGET_STRUCTURE.md)
- [BPO data request](docs/20_BPO_DATA_REQUEST.md)
- [BPO SSOT discussion HTML](docs/bpo/NMM_SSOT_BPO_BRIEF.html)
- [BPO pilot/data-request HTML](docs/bpo/NMM_BPO_DATA_REQUEST_DISCUSSION.html)

## 14. Existing development commands

```powershell
python -m pip install -e ".[dev,web]"
python -m pytest -q
python -m uvicorn pln_nmm_web.api:app --host 127.0.0.1 --port 8000 --reload
```

Current code is still transitional. Roadmap above defines the target behavior;
existing demo outputs must not be interpreted as verified as-built models.
