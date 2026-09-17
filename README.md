# PLN NMM — Kernel CIM & Model Input untuk SLD Bali

Repo ini membangun model CIM sistem Bali dari data yang PLN benar-benar punya,
dengan setiap angka membawa sumber dan tingkat keyakinannya.

Tujuan akhirnya adalah SLD peralatan primer Bali yang lengkap — GI, busbar, bay,
PMT, PMS, trafo, pembangkit — yang bisa diimpor, diperiksa, diedit, dan diekspor
kembali sebagai CIM tanpa kehilangan informasi.

**NMM menyediakan model; aplikasi sekitar mengeksekusi studi.** Load flow,
hubung singkat, dan studi pola operasi dijalankan di PowerFactory, PSS/E, atau
ETAP dengan model dari sini — bukan di NMM. Lihat
[docs/12_CIM_SCOPE.md](docs/12_CIM_SCOPE.md).

Sebagian sudah jalan. Sebagian besar belum. Dokumen ini membedakan keduanya.

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

**Parameter kosong bukan masalah utama.** Sekalipun 4.061 placeholder diisi
angka yang benar, file itu tetap tidak menghasilkan load flow yang bermakna —
karena grafnya salah. 44% node tidak menyambung apa pun, sementara satu node
meringkus seluruh GI jadi satu titik listrik.

**Akar penyebabnya ada di ED, dan itu bukan kegagalan ED.** Enterprise Data
adalah hierarki lokasi fungsional SAP:

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

## Pendekatan: tiga sumber, tiga peran

Pertanyaan yang tepat bukan *"bagaimana mengisi field kosong di ED?"* melainkan
*"dari sumber mana tiap jenis pengetahuan seharusnya datang?"*

| Pengetahuan | Sumber | Status |
|---|---|---|
| Identitas, hierarki, jenis alat, tegangan | **ED** | ada, belum diterima di repo ini |
| Susunan bay, sambungan, sirkit, posisi normal | **SLD P2B / SLD engine** | sebagian terpanen |
| Beban, aliran, tegangan, kapasitor | **Buku Kerawanan / laporan P2B** | terisi untuk 1 skenario |
| Impedansi saluran, data trafo | **database & dokumen setting** | belum tersedia |

```
ED (identitas)  ──┐
                  ├──►  Workbook  ──►  builder/  ──►  CIM EQ  ──►  PowerFactory
SLD (relasi)    ──┘      + provenance
```

Workbook di tengah hanya menampung **delta** — apa yang ED tidak tahu. Bukan
salinan jaringan, bukan pengganti ED.

---

## Yang sudah jalan

### 1. Kernel round-trip CIM (selesai, teruji)

Membungkus cimpy agar ekstensi PLN tidak hilang saat impor–ekspor.

- Namespace terjaga: `plnicp:DiagramProperty.x/y`, `nhftui:info`, `plnnmm`
- Koordinat float bit-exact lewat `repr()` — `float(repr(x)) == x`
- Kunci kanonik `rdf:ID` tanpa underscore, bukan `mRID` saat keduanya berbeda
- Diagnostik `$(Isi_*)` sebelum impor bertipe
- **49 test, 48 passed / 1 xfailed**

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

Dari 10 bay Bali yang terisi, menghasilkan 378 objek:

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

`check_topology()` memeriksa hasilnya dan menolak cacat struktural. Pada model
sekarang ia melaporkan node berderajat-1 26% (file aset PoC: 44%) dan satu node
berderajat-56 — keduanya **akibat gap bay yang belum tertutup**, bukan bug
builder: 55 sirkit masih menunjuk `dari_bay` placeholder yang sama.

### 6. Viewer dan API (dari milestone sebelumnya)

FastAPI inspection API dan React/TypeScript viewer dengan canonical coordinates
dan derived topology schematic. Belum tersambung ke workbook.

---

## Yang belum ada

Tiga gap ini memblokir model Bali yang utuh. Rincian di
[docs/11_BALI_FILL_GAP_REPORT.md](docs/11_BALI_FILL_GAP_REPORT.md).

| Gap | Keadaan | Yang dibutuhkan |
|---|---|---|
| **Bay** | 10 dari ~150–200 (~5%) | SLD per-GI dari P2B/UPT Bali |
| **Impedansi saluran** | **0 dari 55** | database setting |
| **Data trafo** | **0 dari ~40** | ED + dokumen perhitungan setting |

Bay adalah yang terbesar. Gambar 6.2 adalah diagram tingkat sistem — ia
menunjukkan GI sebagai kotak, bukan isi switchyard. Tanpa bay: tidak ada CB, DS,
Terminal, ConnectivityNode, sehingga topologi tidak terbentuk — gap yang sama
persis dengan penyebab 283 node berderajat-1 pada file aset PoC.

Belum ditulis juga: penanganan CT/CVT, paket skenario, dan persistensi edit.

Builder sudah ada, tetapi hasilnya hanya sebaik masukannya: dengan bay 6% dan
impedansi 0%, model yang dihasilkan belum bisa diterima solver.

---

## Aturan yang ditegakkan validator

Aturan ini lahir dari cacat nyata pada data PLN dan dari kesalahan yang
tertangkap saat mengisi workbook ini.

### Error — memblokir generator CIM

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
src/pln_nmm_web/api.py  - FastAPI inspection

  builder/
    workbook.py    - baca .xlsx menjadi dict
    templates.py   - ekspansi template bay -> switch, terminal, node
    emit.py        - serialisasi CIM16 / CGMES 2.4.15 EQ
    check.py       - pemeriksaan topologi hasil

scripts/
  build_workbook_template.py - generator workbook (kosakata = sumber kebenaran)
  validate_workbook.py       - validator aturan domain
  render_sld.py              - render hasil parser SLD apa adanya ke SVG

sources/sld_engine/ - bukti sumber dari repo SLD_engine

web/               - workspace React/TypeScript
tests/             - 49 test + fixture
docs/              - spesifikasi, rekap, laporan gap
```

## Dokumen

| Dokumen | Isi |
|---|---|
| [10_MODEL_INPUT_WORKBOOK.md](docs/10_MODEL_INPUT_WORKBOOK.md) | struktur workbook dan aturannya |
| [11_BALI_FILL_GAP_REPORT.md](docs/11_BALI_FILL_GAP_REPORT.md) | **status pengisian Bali dan gapnya** |
| [12_CIM_SCOPE.md](docs/12_CIM_SCOPE.md) | **peran NMM dan kesiapan model untuk solver** |
| [09_BALI_PRIMARY_SLD_SPEC.md](docs/09_BALI_PRIMARY_SLD_SPEC.md) | kontrak field minimum |
| [08_CANONICAL_XML_GAP_RECAP.md](docs/08_CANONICAL_XML_GAP_RECAP.md) | bukti historis fixture Gilimanuk |
| [07_PHASES.md](docs/07_PHASES.md) | rencana milestone dan kriteria penerimaan |
| [01_DATA_MODEL.md](docs/01_DATA_MODEL.md) · [06_ARCHITECTURE.md](docs/06_ARCHITECTURE.md) | data model dan arsitektur |

Percobaan `Bali_NMM_Prefill` dihapus 17 September 2026: ia menyederhanakan gap
dan digantikan alur workbook → `builder/`. Berkas sumbernya diselamatkan di
[sources/sld_engine/](sources/sld_engine/README.md).

---

## Langkah berikutnya

1. **SLD per-GI** — membuka gap bay yang memblokir topologi. Prioritas tertinggi.
2. **Database setting** — mengisi 55 baris impedansi yang sudah menunggu.
3. **Q atau cos φ** — tanpa ini profil tegangan tidak bisa dihitung.
4. **ED** — mengisi kolom `ed_functloc` dan sebagian data trafo.
5. **Uji ekspor ke PowerFactory** dengan cakupan apa adanya, untuk menemukan
   persyaratan impor yang belum terlihat.

Langkah 1–3 bisa paralel; sumbernya berbeda. Langkah 5 layak dilakukan lebih
awal daripada terasa nyaman — lebih murah menemukan penolakan saat model masih
kecil.

Parser dan halaman unggah dibangun **setelah** workbook terbukti terisi: kolom
yang benar-benar dipakai engineer adalah spesifikasi parser yang tidak perlu
ditebak.

---

## Batas teknis

- **cimpy tidak boleh dimodifikasi atau di-fork.** Bungkus dari luar.
- Kunci round-trip `rdf:ID` tanpa leading underscore, bukan `mRID`.
- Koordinat float mempertahankan `repr()`; tanpa pembulatan.
- Rating aset, posisi normal, status skenario, dan nilai snapshot terpisah.
- Unknown bukan nol dan bukan closed.
- Inom, IKHA, dan setting OCR adalah field berbeda.
- Status skenario tidak boleh disajikan sebagai `Switch.normalOpen` standar.
- v1 hanya profil EQ. TP/SSH/SV/GL/DL menyusul.
- Dependency berlisensi permisif (MIT/BSD/Apache-2.0); GPL/AGPL ditolak.

SLD engine tetap repo terpisah — dipakai sebagai bukti sumber yang
direkonsiliasi, tanpa ketergantungan runtime atau penggabungan repo.
