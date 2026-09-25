# 16 — NMM SSOT Realignment, One-GI Pilot, and BPO Data Request

Status: **master direction document — 25 September 2026**

Dokumen ini menggabungkan realignment produk NMM, konsep SSOT/governance,
kontrak MVP satu GI, dan permintaan data pilot ke BPO. Dokumen teknis implementasi
repo tetap dipisah di `07_PHASES.md` dan `19_REPO_TARGET_STRUCTURE.md`.

## 1. Kenapa arah NMM perlu direalign

PoC sebelumnya sudah cukup untuk menunjukkan bahwa jalur:

```text
ED → CIM/XML → PowerFactory → result/state → NMM
```

secara teknis bisa dibangun.

Tetapi itu belum menjawab pertanyaan yang lebih penting untuk production:

> Bisakah data existing PLN membentuk dan mempertahankan network model yang benar
> dengan sedikit manual re-entry?

Gap utama bukan lagi serializer XML. Gap utama ada pada:

- identity reconciliation;
- physical asset → functional equipment mapping;
- topology reconstruction;
- source ownership;
- versioning dan update;
- review burden;
- governance SSOT;
- security dan publication.

Karena itu repo tidak lagi diposisikan sebagai “workbook → CIM generator”.
Arah barunya adalah:

```text
evidence → reconcile → canonical network graph → validate → publish
```

## 2. Product thesis

NMM adalah **canonical network-model layer**, bukan asset register kedua,
bukan drawing tool utama, dan bukan solver.

NMM berada di antara:

- asset master / Maximo / ED;
- SLD / as-built;
- operational systems;
- protection/engineering sources;
- PowerFactory, PSS®E, ETAP, dan consumer lain.

SSOT di sini berarti:

> **one canonical identity + one authoritative source per domain + one governed
> published network model**

Upstream system tetap authoritative untuk native fact-nya.

Contoh:

- Maximo/asset source tetap authoritative untuk physical asset identity/lifecycle;
- approved SLD/as-built menjadi evidence utama untuk primary topology;
- EMS/SCADA menjadi source operational state;
- protection repository menjadi source setting/protection context;
- NMM menjadi authoritative publication layer untuk **network model hasil
  reconciliation**.

## 3. Keputusan scope MVP

### Input = satu GI

MVP menerima:

```text
GI_<NAME>/
├── assets_clean.xlsx
└── SLD_<GI>.<pdf|png|jpg|vsd|structured-export>
```

Asset data sudah **structurally cleaned**, artinya minimal:

- GI identity jelas;
- source asset identity jelas;
- location/bay containment jelas;
- basic asset type sudah dinormalisasi;
- duplicate/orphan sudah ditandai bila ada;
- provenance source tetap dipertahankan;
- phase R/S/T dipertahankan jika tersedia.

### Review = per bay

Bay adalah unit review paling praktis karena ambiguity biasanya muncul di level:

- PMS Bus-I / Bus-II / Line;
- grouping asset R/S/T;
- endpoint line/transformer;
- equipment presence/order.

### Publish = per GI

Satu GI adalah unit terkecil yang masih punya konteks cukup untuk:

- busbar arrangement;
- coupler/bus section;
- inter-bay consistency;
- transformer antar-voltage-level;
- line/circuit consistency.

### Kenapa bukan per bay sebagai input

Per-bay terlalu sempit untuk memvalidasi konteks GI secara utuh.

### Kenapa belum raw bulk ULTG/UPT/SS

Raw bulk mencampur dua problem:

1. enterprise ETL/master-data cleansing;
2. electrical network reconstruction.

Untuk MVP, keduanya dipisahkan supaya feasibility NMM bisa diukur dengan jelas.

Production nanti tetap dapat menerima bulk:

```text
ULTG / UPT / SS bulk
        ↓
 staging / cleansing
        ↓
  per-GI scope splitter
        ↓
 independent GI jobs
```

## 4. Boundary cleansing vs NMM

### Harus sudah clean sebelum masuk NMM

- source identity;
- GI scope;
- location/bay containment;
- basic asset type;
- obvious duplicate/orphan flag;
- source provenance.

### Justru menjadi pekerjaan NMM

- phase asset rows → functional equipment;
- PMT/PMS/ES functional role;
- equipment sequence;
- busbar attachment;
- Terminal;
- ConnectivityNode;
- topology validation;
- boundary resolution;
- readiness publication.

Jika user harus mengisi topology manual di Excel sebelum upload, maka NMM tidak
memberikan value yang diharapkan.

## 5. Canonical model

Layer harus dipisahkan:

1. **Raw Evidence** — file/hash/revision/page/row.
2. **Physical Asset** — asset identity dan lifecycle.
3. **Functional Equipment** — fungsi electrical.
4. **Electrical Topology** — Terminal + ConnectivityNode.
5. **Operational/Scenario State** — actual/normal/scenario state.
6. **Engineering Parameters** — impedance, rating, transformer model, dll.
7. **Diagram Layout** — XY/rotation/style.
8. **Published Model** — reviewed immutable release.

Dua aturan penting:

> **LOCATION/PARENT adalah containment, bukan electrical connectivity.**

> **XY adalah presentation, bukan topology.**

CIM/XML adalah serialization/interchange representation dari canonical model,
bukan satu-satunya internal data structure.

## 6. One-GI workflow

```text
CLEAN ASSET TABLE                 GI SLD
       │                            │
       ▼                            ▼
asset normalization        topology evidence
       │                            │
       └──────────────┬─────────────┘
                      ▼
                 RECONCILE
          ┌───────────┼───────────┐
          ▼           ▼           ▼
     AUTO_RESOLVED   REVIEW    UNRESOLVED
                      │
                      ▼
                BAY REVIEW
                      │
                      ▼
              CANONICAL GI GRAPH
                      │
        ┌─────────────┼──────────────┐
        ▼             ▼              ▼
     CIM/XML      generated SLD   readiness/report
```

UX principle:

> **User corrects the model; user does not rebuild the model.**

## 7. Readiness ladder

| Level | Status | Minimum information | Output |
|---|---|---|---|
| L0 | `ASSET_READY` | identity + containment | reconciled inventory |
| L1 | `TOPOLOGY_READY` | role + Terminal/ConnectivityNode | canonical GI graph / SLD |
| L2 | `CIM_READY` | supported semantic/profile mapping | CIM/XML |
| L3 | `LOADFLOW_READY` | R/X/B, trafo model, P/Q, scenario | solver base case |
| L4 | `PROTECTION_STUDY_READY` | CT/PT, relay/settings/scheme context | protection study context |

MVP berhenti di **L2**.

Load flow, short circuit, protection, dan engineering studies tetap dijalankan di
aplikasi eksternal.

## 8. Governance SSOT

Sustainable NMM membutuhkan **federated ownership with canonical publication**.

Peran minimum:

- **Network Model Owner** — accountable untuk published network model;
- **Domain Data Owner** — accountable untuk authoritative source domain;
- **Data Steward / Reviewer** — menyelesaikan conflict/data-quality issue;
- **NMM Platform Custodian** — software, validation, release;
- **Approver** — publication approval;
- **Cyber/Security Owner** — access policy dan security control.

### Proposed domain ownership for BPO discussion

| Domain | Candidate authoritative source | Proposed discussion owner |
|---|---|---|
| Physical asset identity/lifecycle | Maximo / enterprise asset source | UIT + asset-master owner |
| As-built primary topology | approved SLD / commissioning/as-built | UIT / engineering owner |
| Operational topology/state | EMS/SCADA / dispatch source | P2B |
| Protection & defense scheme | protection/setting repository | OSL / protection owner |
| Engineering taxonomy/standards | corporate engineering standards | TSJ / RST as applicable |
| Electrical study parameters | approved engineering/study source | designated engineering owner |
| Canonical model publication | NMM registry | BPO-designated Network Model Owner |
| Platform/security | NMM platform + PLN security governance | designated platform/cyber owner |

Final assignment tetap keputusan BPO.

## 9. Change and publication workflow

```text
source update
    ↓
immutable source snapshot
    ↓
automatic diff / reconcile
    ↓
review conflict / ambiguity
    ↓
domain steward resolution
    ↓
Network Model Owner approval
    ↓
versioned published model
    ↓
downstream consumers
```

Tidak boleh ada silent overwrite terhadap reviewed facts.

## 10. Security principle

NMM harus PLN-controlled:

- private/on-premise atau approved PLN cloud;
- RBAC dan least privilege;
- read-only source ingestion by default;
- immutable source evidence;
- audit log dan field provenance;
- draft / reviewed / published separation;
- model versioning dan rollback;
- controlled export by scope/version;
- no write-back upstream tanpa workflow terpisah dan approval.

## 11. Data yang diminta ke BPO untuk pilot

Permintaan dibuat sekecil mungkin: **satu GI representatif**.

### A. Cleaned asset extract

Preferred format: XLSX/CSV.

| Field | Need |
|---|---|
| ASSETNUM / source asset ID | required |
| SITEID / source site | required |
| GI identity/name | required |
| LOCATION / location ID | required |
| bay/location description | required |
| ASSETTYPE | required |
| GROUPTYPE | preferred |
| asset description | required |
| NIA | preferred |
| TECHIDENTNO | preferred |
| phase / R-S-T indication | preferred |
| manufacturer / serial / install date | optional MVP |
| status/active | preferred, but not interpreted as switch state |
| source version/date | required |
| original row/reference | preferred |

Yang **tidak** diminta untuk diisi manual:

- PMS Bus-I / Bus-II / Line role;
- Terminal;
- ConnectivityNode;
- XY;
- load-flow parameters;
- relay setting.

### B. Corresponding GI SLD

Preferred:

- full primary SLD satu GI;
- revision/date visible;
- approved/as-built/current status jika tersedia;
- readable bay/circuit labels;
- PMT/PMS/ES/CT/PT-CVT/LA/trafo/line symbols readable;
- busbar arrangement visible;
- original/vector source preferred, tetapi PDF/image acceptable.

Jika asset extract dan SLD berbeda revision, perbedaan itu dicatat sebagai
reconciliation finding — bukan disembunyikan.

## 12. Data yang belum diperlukan

Pilot pertama tidak perlu menunggu:

- complete R/X/B;
- transformer impedance;
- P/Q;
- generator dispatch;
- SCADA real-time;
- protection setting;
- defense-scheme logic;
- system-wide load-flow case;
- cross-border CGMES transaction package.

Data tersebut baru ditambahkan setelah topology feasibility terbukti.

## 13. Deliverable balik ke BPO

Dari satu GI, pilot mengembalikan:

- reconciled asset inventory;
- physical asset ↔ functional equipment map;
- per-bay review findings;
- explicit topology graph;
- generated SLD;
- CIM/XML;
- conflict/data-quality report;
- provenance;
- readiness status;
- measured manual-review burden.

## 14. Pilot KPI / feasibility gate

Discussion targets:

- ≥95% asset rows ingested tanpa retyping;
- ≥80% functional grouping auto/proposed;
- ≥80% topology relation berasal dari source evidence;
- <20% objects memerlukan keputusan manusia;
- 100% assumption/conflict/unresolved terlihat;
- 0 dangling internal reference saat publish;
- same input → deterministic canonical identity;
- source refresh → explicit diff, bukan duplicate.

Jika hasilnya buruk, itu bukan kegagalan eksperimen. Itu evidence bahwa upstream
data governance perlu diperbaiki sebelum NMM diskalakan.

## 15. Decision requested from BPO

1. Pilih satu GI pilot.
2. Tentukan source owner/contact untuk asset extract.
3. Tentukan source owner/contact untuk SLD.
4. Konfirmasi revision/status SLD.
5. Konfirmasi handling/security constraint.
6. Nominate engineering reviewer untuk exception review terbatas.
7. Tentukan siapa yang akan berperan sebagai Network Model Owner pada pilot.

Pilot ini bukan commitment rollout nasional.

Tujuannya menentukan dengan data apakah PLN sebaiknya:

- scale NMM;
- perbaiki upstream data dulu;
- atau re-scope/stop.

## 16. Repo implication

Aset repo yang dipertahankan:

- CIM round-trip kernel;
- Babel/MxLoader intake;
- provenance;
- inventory-only guard;
- validators/profile checks;
- line-review experiment;
- viewer concept.

Arah implementasi:

```text
intake
→ canonical identity/asset
→ functional grouping
→ SLD evidence
→ reconcile
→ topology
→ validate
→ serialize
→ publish
```

Detail teknis migrasi ada di `19_REPO_TARGET_STRUCTURE.md`.
Roadmap implementasi ada di `07_PHASES.md`.
