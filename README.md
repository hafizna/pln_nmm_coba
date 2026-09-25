# PLN NMM — One-GI SSOT Feasibility & CIM Interchange

> **Direction update — 25 September 2026**
>
> The immediate milestone is no longer “complete Bali SLD” or “fill a workbook until
> simulation works.” The repository now tests whether **existing PLN asset data +
> existing SLD evidence can produce a governed network model with minimal manual
> re-entry**.
>
> Start here:
>
> - [Reengineering direction](docs/16_REENGINEERING_DIRECTION.md)
> - [SSOT governance proposal](docs/17_SSOT_GOVERNANCE.md)
> - [One-GI MVP flow](docs/18_ONE_GI_MVP.md)
> - [Target repository structure](docs/19_REPO_TARGET_STRUCTURE.md)
> - [BPO presentation (HTML)](docs/bpo/NMM_SSOT_BPO_BRIEF.html)

## Current product thesis

NMM is the canonical **network-model layer** between asset systems, approved SLD /
as-built evidence, operational systems, engineering data, and downstream study
applications.

It is **not** a second asset register and it should not require engineers to
retype fields that already exist upstream.

The near-term feasibility test is:

```text
real asset register + real GI SLD
              ↓
       normalize evidence
              ↓
  reconcile physical assets ↔ functional equipment
              ↓
     review only ambiguities
              ↓
       canonical network graph
              ↓
CIM/XML + generated SLD + readiness/provenance report
```

Load flow, short-circuit, protection-setting calculation and CGMES external
exchange remain later enrichment/integration stages. NMM provides the governed
model; PowerFactory/PSS®E/ETAP and other tools execute studies.

## What the current branch already contributes

The existing Babel intake, CIM round-trip kernel, workbook/builder experiments,
line-bay review, validation code and viewer are **retained as engineering assets**.
They are being repositioned around a canonical model and evidence/reconciliation
workflow. The workbook becomes an adapter/review surface, not the permanent SSOT.


---

## Masalah yang sedang diselesaikan

PoC NMM 2025 (PLN Icon Plus + tim Universitas Indonesia) membuktikan alur
end-to-end ED → CIM → PowerFactory → SV → NMM bisa berjalan. Yang belum
terselesaikan adalah **isinya**.

Pemeriksaan pada `CIM_sample-db_userdef_python.xml` (3.716 objek) menunjukkan:

| Temuan | Angka |
|---|---:|
| Placeholder `$(Isi_*)` pada field teknis | 4.061 |
| `ACLineSegment.r/x/bch` terisi | **0 dari 111** |
| `PowerTransformerEnd.ratedU/ratedS/r/x` terisi | **0 dari 226** |
| `EnergyConsumer.pfixed/qfixed` terisi | **0 dari 24** |
| Objek Breaker | **0** |
| Objek Bay | **0** |
| ConnectivityNode berderajat 1 (ujung buntu) | **283 dari 637** |
| Satu node menampung terminal | **58** |

Dua hal yang perlu dipisahkan dari angka-angka ini:

**Mengisi parameter saja belum menyelesaikan konektivitas.** Node berderajat 1
memiliki satu terminal, bukan tanpa sambungan, dan bisa sah pada batas model.
Node dengan banyak terminal juga bisa merupakan bus yang sah. Angka-angka ini
menjadi petunjuk pemeriksaan, bukan bukti tunggal graf salah: hubungan terminal,
batas model, dan susunan bay harus dibandingkan dengan sumber SLD.

**Hierarki ED belum cukup untuk menetapkan konektivitas.** Struktur Enterprise
Data yang dirujuk adalah hierarki lokasi fungsional SAP:

```
UI/UPT | Gardu Induk | Bay | ID_FUNCTLOC | SUP_FUNCTLOC | NM_LOKASI |
DESKRIPSI | UNIT | NLEVEL | STATUS | ID_LOCATION | ID_PARENT |
TEGANGAN | KD_FUNGSI
```

`SUP_FUNCTLOC` menyatakan *"alat X berada di bawah bay Y"* — relasi
administratif, bukan *"alat X tersambung ke alat Z"*. ED dirancang untuk
memelihara aset, bukan menyimulasikan jaringan. Meminta ED menyediakan topologi
listrik sama seperti meminta daftar inventaris menjelaskan cara merakit.

Laporan PoC menyebutnya "tidak ada distinct indicator" untuk CB, DS, koneksi
generator, trafo, dan penghantar (hal. 30–34).

## Pendekatan: gabungkan sumber melalui core NMM

Pertanyaan yang tepat bukan *"bagaimana mengisi field kosong di ED?"* melainkan
*"dari sumber mana tiap jenis pengetahuan seharusnya datang?"*

| Pengetahuan | Sumber | Status |
|---|---|---|
| Identitas, hierarki, jenis alat, tegangan | **ED** | ada, belum diterima di repo ini |
| Susunan bay, sambungan, sirkit, posisi normal | **SLD P2B / SLD engine** | sebagian terpanen |
| Beban, aliran, tegangan, kapasitor | **Buku Kerawanan / laporan P2B** | terisi untuk 1 skenario |
| Impedansi saluran, data trafo | **database & dokumen setting** | belum tersedia |

Alur target berikut belum tersambung sepenuhnya:

```text
ED / workbook pelengkap / SLD / XML lama / laporan operasi
                         ↓
      Baca → normalisasi → rekonsiliasi ID → validasi
                         ↓
                  Model internal NMM
        ├── peralatan, parameter, konektivitas, posisi normal
        ├── skenario dan snapshot
        ├── layout per diagram
        └── provenance per field, asumsi, konflik, dan gap
                         ↓
       Ekspor paket: EQ + DL + pendamping yang diperlukan
                         ↓
        Impor ulang → periksa → SLD sistem / GI / bay
                         ↓
       Edit → validasi → simpan → buka dan periksa kembali

Paket pertukaran → uji impor dan interpretasi di aplikasi studi
```

Workbook adalah salah satu pintu masuk dan kontrak pelengkapan **delta** terhadap
ED. Saat ED belum tersedia, identitas sementara boleh dipakai dengan sumber dan
status yang jelas. ED asli nanti dipetakan ke identitas model yang sama; refresh
sumber tidak boleh menghilangkan pelengkapan, skenario, atau layout pengguna.

Core perlu menyediakan kemampuan berikut tanpa bergantung pada web:

1. Membaca sumber dan menyimpan bukti asli beserta lokasi baris/objek, versi,
   satuan, dan tanggal yang tersedia. Adapter ED nyata mengikuti sampel ED yang
   diterima; contoh sintetis untuk pengembangan harus diberi label.
2. Menormalisasi nama, jenis, dan satuan; memetakan ID sumber seperti
   `ed_functloc` ke ID model yang stabil. Nama sama saja tidak cukup untuk merge.
3. Menggabungkan field pelengkap, mencatat kandidat yang konflik dan keputusan
   reviewer. Impor ulang sumber harus dapat dibandingkan tanpa menduplikasi aset
   atau diam-diam menimpa nilai yang telah ditinjau.
4. Membentuk peralatan dan konektivitas eksplisit dari bukti atau template
   berstatus asumsi, lalu memvalidasi struktur dan hubungan listriknya.
5. Mengekspor dan mengimpor kembali model, skenario, provenance, serta layout.
   Viewer demonstrasi membaca hasil impor ulang agar gambar membuktikan isi XML.

CLI dan API nantinya memanggil fungsi core yang sama. Halaman upload menampilkan
apa yang dikenali, berubah, konflik, dan belum diketahui dari laporan core.

### Dua sasaran penerimaan

| Sasaran | Bukti keberhasilan |
|---|---|
| **Kemampuan NMM** | Contoh representatif dapat dikonversi, ditampilkan, diedit, disimpan, dan dibuka kembali tanpa kehilangan arti atau informasi |
| **Kelengkapan Bali** | Cakupan GI/bay/peralatan/parameter terukur terhadap revisi sumber, dengan asumsi dan bagian yang belum diketahui tetap terlihat |

Asumsi yang dilabeli diperbolehkan untuk membuktikan kemampuan aplikasi.
Lulus demonstrasi tidak menjadikan data Bali terverifikasi. Data riil dikumpulkan
sambil membangun core; model lengkap yang terverifikasi tetap sasaran produk.

### Validasi bertingkat

| Tingkat | Yang diperiksa |
|---|---|
| Struktur | ID unik, referensi terurai, tipe, satuan, dan field wajib |
| Konektivitas | Urutan peralatan bay, terminal/CN, bus pilihan, ujung saluran, dan batas model |
| Pelestarian data | ID, objek, nilai/unknown, attachment, provenance, skenario, dan koordinat setelah ekspor–impor |
| Tampilan | SLD dari hasil impor ulang sesuai model; diagram sistem dan detail diperiksa visual |
| Interoperabilitas | Aplikasi tujuan menerima paket dan menafsirkan peralatan, sambungan, satuan, serta parameter sesuai model |

Uji aplikasi tujuan dimulai dengan paket kecil. Berhasil membuka XML belum
membuktikan interpretasinya benar; bandingkan isi model terlebih dahulu, kemudian
hasil studi setelah parameter studi mencukupi. Dukungan tiap aplikasi/profil
harus dibuktikan tersendiri.

---

## Yang sudah jalan

### Intake aset Babel (23 September 2026)

Adapter PST/MxLoader tersedia di `sources/maximo.py`. Workbook Babel terpisah
memuat 10 GI, 65 kandidat bay dan 3.385 record aset terhubung (1.019 primer).
ID sumber, sheet/baris dan hash berkas tetap tersimpan. Statusnya
`INVENTORY_ONLY`: builder menolak ekspor CIM sebelum rekonsiliasi SLD.
Nama GI sama dengan ID berbeda dan penempatan aset yang perlu diperiksa dicatat
sebagai temuan. Ini intake inventaris; belum merge refresh atau model listrik.
Lihat [14_BABEL_INVENTORY.md](docs/14_BABEL_INVENTORY.md) untuk cakupan dan cara
mengulang ekstraksi. Data Babel tidak mengganti model atau template Bali.

Rekonstruksi bay penghantar tersedia sebagai **tahap review core**, terpisah dari
builder CIM: `scripts/reconstruct_babel_lines.py`. Dengan pilihan eksplisit
`--assume-double-bus`, register Babel menghasilkan 33 kandidat bay pada 10 GI,
264 posisi fungsional asumsi, manifest per GI, JSON konektivitas, dan laporan
HTML dari JSON yang dibuka ulang. CVT, LA dan PMS tanah adalah cabang; CT berada
seri. Kandidat aset belum menjadi pemetaan fase/peran terverifikasi. Posisi
normal tetap unknown; `--demo-scenario` menyimpan status ilustratif terpisah.
Ini **belum ekspor CIM atau integrasi viewer utama**. Lihat
[kontrak dan batas rekonstruksi](docs/15_LINE_BAY_RECONSTRUCTION.md).

### Review XML Kelapa yang bisa dijalankan

Contoh satu bay **Kelapa–Muntok #1** sekarang dapat diekspor sebagai RDF/XML NMM
eksperimental, diimpor ulang, digambar, diubah status skenarionya, dan diunduh.
Bus 1 dipilih; PMS rel 1, PMT dan PMS line closed; PMS rel 2 dan ES open.
PMS line/ES adalah dua fungsi dalam satu rakitan asumsi; posisi normal unknown.

```powershell
python scripts/prepare_kelapa_demo.py outputs/babel_inventory_20260923/inventory.json outputs/kelapa_xml_demo
python -m uvicorn pln_nmm_web.api:app --host 127.0.0.1 --port 8000
```

Buka **http://127.0.0.1:8000/line-review** lalu klik **Muat contoh Kelapa**.
Tampilan 25 September memakai bay vertikal, busbar horizontal, dan cabang
CVT/LA/ES ringkas. SVG CT/CVT/LA bersumber dari QElectroTech melalui SynergyCodes
dengan atribusi CC-BY 3.0; detail revisi ada di `web/public/devices/qet/SOURCE.txt`.
Urutan perangkat ditelusuri dari konektivitas XML. Layout ini merupakan proyeksi
skematik otomatis dan tidak menimpa koordinat yang tersimpan di XML.
Gunakan **Unduh XML yang tampil**, kemudian **Impor ulang XML** untuk memeriksa
hasil yang sama. Bagian status dapat ditampilkan melalui **Ubah status skenario
asumsi**. Halaman ini dilayani backend yang sama; tidak memerlukan Vite.
Script pembuatan contoh menolak overwrite; tidak perlu dijalankan ulang bila
contohnya sudah tersedia.

Ini **bukan paket CGMES EQ standar atau uji PowerFactory**, dan belum seluruh GI.
Objek primer dan fungsi ES memakai ekstensi NMM dengan pembaca tersendiri;
uploader EQ umum/cimpy menolak format ini agar perangkat tidak hilang diam-diam.
Interlock yang diuji baru larangan demo PMS line/ES closed bersamaan; tidak ada
perhitungan energized, load flow atau impedansi.

### 1. Kernel round-trip CIM untuk cakupan yang didukung

Membungkus cimpy agar ekstensi PLN tidak hilang saat impor–ekspor.

- Namespace terjaga: `plnicp:DiagramProperty.x/y`, `nhftui:info`, `plnnmm`
- Koordinat float bit-exact lewat `repr()` — `float(repr(x)) == x`
- Kunci kanonik `rdf:ID` tanpa underscore, bukan `mRID` saat keduanya berbeda
- Diagnostik `$(Isi_*)` sebelum impor bertipe
- Regresi tersedia di `tests/`; jalankan suite untuk status pada revisi aktif.
  Preservasi properti yang ada belum membuktikan preservasi seluruh objek CT/CVT.

### 2. Model input workbook (baru, terisi untuk Bali)

`NMM_Model_Input_TEMPLATE.xlsx` — 16 sheet, dibangkitkan dari skrip, dengan
validator yang menegakkan aturan domain.

```powershell
python scripts/build_workbook_template.py NMM_Model_Input_TEMPLATE.xlsx
python scripts/validate_workbook.py NMM_Model_Input_TEMPLATE.xlsx
```

Kelompok sheet mengikuti sumber dan siklus hidupnya:

| Sheet | Isi | Sumber | Frekuensi ubah |
|---|---|---|---|
| `01`–`04` | GI, bay, template, sambungan | SLD | jarang |
| `05`–`06` | impedansi saluran, trafo | DB/dokumen setting | saat ada studi |
| `07`–`08` | beban, pembangkit | laporan P2B | bulanan |
| `10` | diameter 1½ CB | SLD | jarang |
| `11`–`15` | skenario, aliran, tegangan, kapasitor, neraca daya | Buku Kerawanan | per snapshot |
| `09` | register asumsi | reviewer | mengikuti |

Pemisahan ini bukan kosmetik: refresh beban bulanan tidak boleh menyentuh baris
topologi, dan tiap sheet punya satu sumber sehingga rencana *upload per-function*
nanti bisa dipetakan langsung.

### 3. Template bay hasil rekonstruksi

Tidak ada standar bay PLN formal yang tersedia, jadi 11 template direkonstruksi
dari 13 bay pada canonical draft Gilimanuk:

| Pola | Contoh | Susunan |
|---|---:|---|
| Bay penghantar | 9 | `DS_BUS_A, DS_BUS_B, CB, DS_LINE` |
| Bay trafo | 2 | `DS_BUS_A, DS_BUS_B, CB, DS_TRAFO` |
| Bay generator | 1 | `DS_BUS_A, DS_BUS_B, CB, DS_GSU` |
| Bay kopel | 1 | `DS_BUS_A, CB, DS_BUS_B` |

**Semuanya berstatus `INFERRED`/`ASSUMED`/`UNKNOWN`. Tidak ada yang `VERIFIED`.**
Ini hipotesis yang menunggu validasi engineer, bukan standar.

### 4. Data Bali terisi dari Gambar 6.2

Snapshot 15 Mei 2026 19:00 WITA, beban puncak diversity 1.296 MW:

| Aspek | Terisi | Cakupan |
|---|---:|---:|
| GI | 22 | 100% |
| Ruas / sirkit | 27 / 55 | dari gambar |
| Beban GI | 17 | 77% |
| Aliran penghantar | 28 | ~93% |
| Tegangan bus | 20 | 91% |
| Kapasitor | 4 | 100% |

Beban termodel 1.153,5 MW vs puncak 1.296 MW = **89%**.

### 5. Builder workbook → CIM EQ (baru)

`src/pln_nmm/builder/` mengubah baris workbook menjadi objek CIM eksplisit.

```powershell
python -m pln_nmm.cli build NMM_Model_Input_TEMPLATE.xlsx out\bali_EQ.xml --scenario BP-2026-05-15
```

Catatan build workbook Bali yang tersedia mencatat 10 bay dan 378 objek
(angka ini bukan hasil pengukuran ulang pada setiap perubahan README):

| Objek | Jumlah |
|---|---:|
| Substation / VoltageLevel | 22 / 22 |
| Bay | 10 |
| Breaker | 16 |
| Disconnector | 32 |
| BusbarSection | 4 |
| ConnectivityNode | 42 |
| Terminal | 155 |
| ACLineSegment | 55 |
| EnergyConsumer | 17 |

Sifat yang dijamin dan diuji:

- **0 dangling, 0 rdf:ID duplikat**
- Setiap switch tepat 2 Terminal
- **CB tengah diameter = satu objek `Breaker` dengan dua Terminal** — bukan dua
  breaker terpisah; ada test regresinya
- `bus_normal` menjadi tepat satu PMS rel tertutup dan satu terbuka
- **Parameter belum diketahui DIHILANGKAN, bukan diisi nol** — 55 `r`, 55 `x`,
  55 `bch`, 17 `qfixed` sengaja tidak ditulis
- Setiap objek turunan membawa `plnnmm:provenance`
- Output deterministik: workbook sama → byte sama, sehingga bisa di-diff

`check_topology()` memeriksa sebagian cacat struktural. Catatan build melaporkan
node berderajat-1 26% dan satu node berderajat-56, dengan 55 sirkit masih menunjuk
`dari_bay` placeholder yang sama. Lulus pemeriksaan referensi belum menjamin
konektivitas benar; pemetaan endpoint dan penanganan placeholder perlu dibereskan.

Perintah `build` saat ini menulis EQ saja. Nilai P/Q dari skenario yang dipilih
masih ditulis ke `EnergyConsumer.pfixed/qfixed`; pemisahan snapshot ke pendamping
skenario belum selesai dan menjadi pekerjaan core berikutnya.

### 6. Viewer dan API (dari milestone sebelumnya)

FastAPI inspection API dan React/TypeScript viewer dengan canonical coordinates
dan derived topology schematic. Jalur inspeksi SLD masih membaca koordinat
`plnicp` atau memakai posisi otomatis. Belum tersambung ke workbook atau impor
paket EQ + DL + skenario dalam satu alur aplikasi.

### 7. Modul DL dan pemeriksaan profil

`src/pln_nmm/emit/dl.py` menyediakan penulisan DL terpisah;
`src/pln_nmm/check/profile.py` dan `tests/test_profiles.py` memeriksa pemisahan
profil dan referensinya. Modul ini belum dihubungkan ke perintah `build` maupun
pembacaan layout viewer. Keberadaan modul bukan bukti alur EQ + DL sudah utuh.

---

## Yang belum ada

Tiga gap ini memblokir model Bali yang utuh. Rincian di
[docs/11_BALI_FILL_GAP_REPORT.md](docs/11_BALI_FILL_GAP_REPORT.md).

| Gap | Keadaan | Yang dibutuhkan |
|---|---|---|
| **Bay** | 10 dari ~150–200 (~5%) | SLD per-GI dari P2B/UPT Bali |
| **Impedansi saluran** | **0 dari 55** | database setting |
| **Data trafo** | **0 dari ~40** | ED + dokumen perhitungan setting |

Gambar 6.2 menunjukkan hubungan tingkat sistem, bukan rincian seluruh switchyard.
Detail bay diperlukan untuk sasaran SLD primer kita. Core dapat dikembangkan
dengan contoh representatif dan susunan asumsi yang dilabeli sambil menunggu
SLD per-GI untuk memverifikasi model Bali.

Belum ditulis juga: penanganan CT/CVT, paket skenario, dan persistensi edit.

Builder sudah ada, tetapi model saat ini belum terbukti siap untuk studi.
Kelengkapan parameter, kebenaran konektivitas, dan penerimaan aplikasi tujuan
adalah pemeriksaan yang berbeda. Adapter ED nyata, model internal terpadu, merge
per field, dan laporan perubahan lintas sumber juga belum menjadi alur utuh.

---

## Aturan yang ditegakkan validator

Aturan ini lahir dari cacat nyata pada data PLN dan dari kesalahan yang
tertangkap saat mengisi workbook ini.

### Error — harus diselesaikan sebelum build

Saat ini validator workbook dijalankan terpisah melalui
`scripts/validate_workbook.py`; perintah `build` belum memanggilnya otomatis.
Menjadikan validasi sebagai gerbang wajib pada alur core adalah pekerjaan berikutnya.

| Aturan | Alasan |
|---|---|
| Nol pada impedansi tanpa `VERIFIED` | `r=0` adalah klaim salah; kosong berarti belum diketahui |
| `hv_kv == lv_kv` pada trafo | pola cacat 150/150 kV di file aset PoC |
| `ASSUMED` tanpa baris di `09_ASUMSI` | asumsi harus tetap bisa dibedakan dari fakta |
| Template bay ≠ skema busbar GI-nya | kontradiksi tidak boleh sampai ke CIM |
| `phi` ≠ jumlah sirkit | konsistensi ruas |
| GI `ONE_HALF_CB` tanpa bay `DIAMETER` | 1½ CB melanggar asumsi satu-bay-satu-CB |
| Beban = aliran penghantar menuju GI itu | **beban ganda** |
| Total beban > 110% puncak sistem | **beban ganda / salah klasifikasi** |
| Tegangan di luar 0,85–1,15 pu | salah baca angka |

Dua aturan terakhir terbukti bekerja saat pengisian: total beban sempat mencapai
1.433 MW terhadap puncak 1.296 MW, menyingkap bahwa 279,5 MW di Pesanggaran
salah dicatat sebagai beban padahal itu pusat pembangkitan Bali.

### Peringatan — tidak memblokir

Template belum `VERIFIED`, GI tanpa bay, `titik_ukur` tidak diketahui,
`posisi_2` diameter kosong.

---

## Tiga konsep yang tidak boleh tertukar

Ketiganya sempat tercampur dan dikoreksi dari lapangan.

**`skema_busbar` — properti GI.** `DOUBLE`, `SINGLE`, `SINGLE_SECTION`,
`DOUBLE_SECTION`, `ONE_HALF_CB`. Satu GI satu skema; semua bay mengikutinya.

**`phi` — properti ruas penghantar.** Istilah operasional PLN untuk jumlah
sirkit menuju satu GI. *Single phi* = hanya satu sirkit ke arah GI itu, sehingga
N-1 tidak terpenuhi. Buku Kerawanan: *"Usulan Double Phi sehingga menjadi 2
sirkit"* (hal. 105). Tidak berhubungan dengan susunan bay.

**`jenis_nilai` + `skenario_id` — konteks angka.** Satu angka beban tidak
bermakna tanpa kondisi saat diukur.

### Beban bukan aliran

| Angka di Gambar 6.2 | Contoh | Sheet |
|---|---|---|
| Panah turun di GI | Negara 28,8 MW | `07_BEBAN` |
| Angka pada garis antar-GI | Gilimanuk–Negara 233,6 MW | `12_ALIRAN` |

Aliran penghantar adalah **akibat** dari beban GI tujuan. Menjadikannya objek
beban menghitung beban dua kali. Gunakan `12_ALIRAN` untuk memvalidasi hasil
load flow, bukan sebagai input.

---

## Bukti konfigurasi Bali

Anggapan "Bali sudah double busbar semua" tidak seluruhnya benar. Buku menyebut
stasiun single busbar secara eksplisit, jadi penyebutan adalah bukti positif —
tetapi ketiadaannya bukan bukti sebaliknya.

| GI | Skema | Confidence | Bukti |
|---|---|---|---|
| AIS Pesanggaran | `SINGLE_SECTION` | **VERIFIED** | hal. 244: *"single busbar dengan 1 bus section"* |
| GIS Celukan Bawang | `ONE_HALF_CB` | INFERRED | SLD Bali 2026: konfigurasi diameter |
| GIS Pesanggaran | `DOUBLE_SECTION` | INFERRED | hal. 245: Section Utara/Selatan |
| Gilimanuk, Kapal | `DOUBLE` | INFERRED | hal. 243–244; bus section masih usulan |
| 18 GI lainnya | `DOUBLE` | INFERRED | SLD Bali 2026 |

**1 dari 22 GI berstatus `VERIFIED`.**

### Celukan Bawang perlu penanganan khusus

GIS Celukan Bawang memakai **one-and-a-half breaker**, dengan unit dasar
**diameter**: 3 CB melayani 2 sirkit, dan **CB tengah dipakai bersama**.

Ini melanggar asumsi "satu bay = satu CB" yang mendasari semua template lain.
Generator CIM harus membuat CB tengah sebagai **satu objek `Breaker` dengan dua
Terminal**, bukan dua Breaker terpisah — bila salah, N-1 dan aliran daya keliru.

---

## Menjalankan

Python 3.10+:

```powershell
python -m pip install -e ".[dev,web]"
python -m pytest -q
```

Workbook:

```powershell
python scripts/build_workbook_template.py NMM_Model_Input_TEMPLATE.xlsx
python scripts/validate_workbook.py NMM_Model_Input_TEMPLATE.xlsx
```

CLI:

```powershell
python -m pln_nmm.cli inspect "path\to\model.xml"
python -m pln_nmm.cli roundtrip "input.xml" "out\roundtrip_EQ.xml" --mode preserve
python -m pln_nmm.cli roundtrip "input.xml" "out\standard_EQ.xml" --mode standard
```

Mode `standard` tidak mempertahankan ekstensi PLN.

Viewer:

```powershell
python -m uvicorn pln_nmm_web.api:app --host 127.0.0.1 --port 8000 --reload
```

Terminal lain:

```powershell
cd web
npm install
npm run dev -- --port 5173 --strictPort
```

Buka http://127.0.0.1:5173 lalu unggah CIM XML.

---

## Struktur repo

```text
src/pln_nmm/
  adapter.py       - extract/strip/reinject ekstensi PLN. Pure XML, tanpa cimpy.
  importer.py      - pembungkus cimpy.cim_import + strip
  exporter.py      - pembungkus cimpy.cim_export + reinject
  diagnostics.py   - deteksi $(Isi_*) sebelum impor bertipe
  sld.py           - ekstraksi SLD
  topology.py      - inspeksi topologi turunan
  cli.py           - CLI argparse
  sources/
    workbook.py    - baca workbook
    sld_engine.py  - baca bukti sumber SLD engine
    reconcile.py  - bandingkan bukti SLD engine dengan workbook
  model/
    identity.py    - ID deterministik; model internal terpadu masih perlu dibangun
  builder/
    templates.py   - ekspansi template bay -> switch, terminal, node
    emit.py        - serialisasi CIM16 / CGMES 2.4.15 EQ
  emit/dl.py       - penulisan layout DL terpisah
  check/
    topology.py    - pemeriksaan konektivitas struktural
    profile.py     - pemeriksaan pemisahan EQ/DL
src/pln_nmm_web/api.py  - FastAPI inspection

scripts/
  build_workbook_template.py - generator workbook (kosakata = sumber kebenaran)
  validate_workbook.py       - validator aturan domain
  render_sld.py              - render hasil parser SLD apa adanya ke SVG

sources/sld_engine/ - bukti sumber dari repo SLD_engine

web/               - workspace React/TypeScript
tests/             - regresi + fixture
docs/              - spesifikasi, rekap, laporan gap
```

## Dokumen

Urutan kerja dan status integrasi pada README ini menjadi acuan terbaru.
Dokumen 07 mengikuti urutan core terlebih dahulu. Beberapa catatan lain masih
merekam tahap sebelumnya: dokumen 10 menyebut builder belum ada; dokumen 13
menjelaskan rancangan EQ/DL yang belum sepenuhnya terhubung ke CLI dan viewer.
Jangan membaca contoh atau target tersebut sebagai jaminan fitur telah selesai.

| Dokumen | Isi |
|---|---|
| [10_MODEL_INPUT_WORKBOOK.md](docs/10_MODEL_INPUT_WORKBOOK.md) | struktur workbook dan aturannya |
| [11_BALI_FILL_GAP_REPORT.md](docs/11_BALI_FILL_GAP_REPORT.md) | **status pengisian Bali dan gapnya** |
| [12_CIM_SCOPE.md](docs/12_CIM_SCOPE.md) | **peran NMM dan kesiapan model untuk solver** |
| [13_DL_SEPARATION.md](docs/13_DL_SEPARATION.md) | **koordinat di EQ: apa yang salah dan bagaimana diperbaiki** |
| [09_BALI_PRIMARY_SLD_SPEC.md](docs/09_BALI_PRIMARY_SLD_SPEC.md) | kontrak field minimum |
| [08_CANONICAL_XML_GAP_RECAP.md](docs/08_CANONICAL_XML_GAP_RECAP.md) | bukti historis fixture Gilimanuk |
| [07_PHASES.md](docs/07_PHASES.md) | rencana milestone dan kriteria penerimaan |
| [01_DATA_MODEL.md](docs/01_DATA_MODEL.md) · [06_ARCHITECTURE.md](docs/06_ARCHITECTURE.md) | data model dan arsitektur |

Percobaan `Bali_NMM_Prefill` dihapus 17 September 2026: ia menyederhanakan gap
dan digantikan alur workbook → `builder/`. Berkas sumbernya diselamatkan di
[sources/sld_engine/](sources/sld_engine/README.md).

---

## Langkah berikutnya

1. **Tetapkan contoh penerimaan kecil:** satu GI dengan bay penghantar dan ujung
   GI lawan, trafo–beban, kopel, serta peralatan primer yang berlaku. Uji susunan
   1½ CB secara terpisah untuk membuktikan CB bersama. Asumsi dan batas contoh
   harus eksplisit.
2. **Bangun core rekonsiliasi:** adapter sumber, kontrak model internal, ID
   stabil, pelengkapan per field, konflik, dan laporan perubahan. Gunakan contoh
   input berlabel sintetis bila ED nyata belum tersedia; validasi adapter ED
   terhadap sampel asli sebelum mengklaim kompatibilitas.
3. **Sambungkan alur CLI:** input → model → validasi → paket EQ/DL/pendamping →
   impor ulang. Hubungkan validator ke alur tersebut; pertahankan unknown dan
   pisahkan snapshot dari parameter aset. Tambahkan preservasi objek yang belum
   didukung, termasuk CT/CVT, sebelum mengklaim SLD primer lengkap.
4. **Pakai viewer untuk membuktikan hasil impor:** tampilkan sistem/detail,
   sumber, dan gap; uji perubahan parameter, skenario, serta layout melalui
   fungsi core lalu simpan dan buka kembali. Identitas dan bagian lain tetap utuh.
5. **Uji paket kecil di PowerFactory lebih awal:** periksa penerimaan dan
   interpretasi model. Tambahkan pembandingan hasil studi setelah parameter
   cukup; perluasan ke aplikasi lain memerlukan pengujian tersendiri.
6. **Perluas cakupan Bali dan web upload:** terapkan alur yang sudah terbukti
   pada sumber yang lebih luas. Upload menggunakan fungsi dan laporan core yang
   sama, tanpa menduplikasi aturan konversi di frontend.

Pengumpulan ED, SLD per-GI, impedansi, serta Q/cos φ berjalan bersamaan dengan
pengembangan core. Kekurangan data Bali tidak menghalangi pengujian kemampuan
NMM memakai contoh asumsi yang terlihat. Target satu minggu adalah timebox untuk
hasil yang bisa dibuktikan; kelengkapan Bali dilaporkan terpisah.

---

## Batas teknis

- **cimpy tidak boleh dimodifikasi atau di-fork.** Bungkus dari luar.
- Kunci round-trip `rdf:ID` tanpa leading underscore, bukan `mRID`.
- Koordinat float mempertahankan `repr()`; tanpa pembulatan.
- Rating aset, posisi normal, status skenario, dan nilai snapshot terpisah.
- Unknown bukan nol dan bukan closed.
- Inom, IKHA, dan setting OCR adalah field berbeda.
- Status skenario tidak boleh disajikan sebagai `Switch.normalOpen` standar.
- EQ menyimpan struktur peralatan; DL menjadi target layout terpisah. Modul
  penulis DL tersedia, integrasi paket dan viewer belum lengkap. Native
  TP/SSH/SV/GL menyusul; skenario memakai pendamping yang masih perlu dibangun.
- Dependency berlisensi permisif (MIT/BSD/Apache-2.0); GPL/AGPL ditolak.

SLD engine tetap repo terpisah — dipakai sebagai bukti sumber yang
direkonsiliasi, tanpa ketergantungan runtime atau penggabungan repo.
