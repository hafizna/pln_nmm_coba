# 10 — Model Input Workbook

Status: template dan validator tersedia; generator CIM belum ditulis.

## Peran

Workbook ini adalah kontrak pengisian data antara Enterprise Data PLN dan
generator CIM EQ. Ia menampung **hanya apa yang ED tidak punya**.

```
ED (identitas)  ──┐
                  ├──►  Workbook  ──►  Generator  ──►  CIM EQ  ──►  PowerFactory
SLD (relasi)    ──┘
```

Yang menentukan keberhasilan desain ini adalah pembatasan ruang lingkup: bila
workbook menjadi tempat menyalin ulang isi ED, ia akan berhenti dirawat.
Workbook hanya memuat delta.

## Alasan bentuknya multi-sheet, bukan satu tabel

Empat sumber data dengan siklus hidup berbeda:

| Sheet | Isi | Sumber | Frekuensi ubah |
|---|---|---|---|
| 01–04 | topologi | SLD P2B / SLD engine | jarang |
| 05–06 | parameter | DB setting, dokumen setting | saat ada studi |
| 07–08 | operasi | laporan bulanan P2B, Buku Kerawanan | bulanan |
| 09 | register asumsi | reviewer | mengikuti |

Memaksa semuanya jadi satu tabel datar membuat refresh beban bulanan menyentuh
baris topologi. Pemisahan per sumber juga yang membuat rencana *upload
per-function* nanti bisa dipetakan langsung: satu unggahan mengisi satu sheet.

## Sheet

| Sheet | Kunci | Catatan |
|---|---|---|
| `01_GI` | `gi_id` | mengunci masalah 360 objek Substation untuk 19 nama GI; memuat `skema_busbar` |
| `02_BAY` | `bay_id` | inti; `bus_normal` → `Switch.normalOpen` |
| `03_TEMPLATE` | `template_id` | kamus susunan bay, berlaku nasional |
| `04_SAMBUNGAN` | `sambungan_id` | satu baris = satu sirkit; memuat `phi` |
| `05_SALURAN` | `sambungan_id` | impedansi dari DB setting |
| `06_TRAFO` | `trafo_id` | MVA/winding dari ED, Z% dari dokumen setting |
| `07_BEBAN` | `beban_id` | dipisah karena paling sering di-refresh |
| `08_PEMBANGKIT` | `gen_id` | termasuk GSU |
| `09_ASUMSI` | `asumsi_id` | wajib untuk setiap nilai `ASSUMED` |
| `10_DIAMETER` | `diameter_id` | khusus GI berkonfigurasi 1½ CB |
| `11_SKENARIO` | `skenario_id` | kondisi sistem saat nilai snapshot diukur |
| `12_ALIRAN` | `aliran_id` | aliran penghantar; **validasi**, bukan input beban |

## Tiga konsep yang tidak boleh tertukar

Ketiganya sempat saya campur, dan koreksi dari lapangan memperbaikinya.

**`skema_busbar` — properti GI (sheet 01).** Double, single, single+section, atau
1½ CB. Bukan properti bay: satu GI punya satu skema, dan semua bay di dalamnya
mengikutinya. Validator menolak bay double-busbar di GI yang dideklarasikan
single busbar.

**`phi` — properti ruas penghantar (sheet 04).** Istilah operasional PLN untuk
jumlah sirkit menuju satu GI. *Single phi* = hanya satu sirkit ke arah GI itu,
sehingga N-1 tidak terpenuhi. Buku Kerawanan memakainya begitu: *"Usulan Double
Phi sehingga menjadi 2 sirkit"* (hal. 105). Tidak ada hubungannya dengan susunan
bay. Validator memastikan `phi` konsisten dengan `jml_sirkit`.

**`jenis_nilai` + `skenario_id` — konteks nilai (sheet 07/11).** Satu angka beban
tidak bermakna tanpa kondisi saat diukur.

## Bukti busbar Bali

Klaim "Bali sudah double busbar semua" **tidak seluruhnya benar**. Buku menyebut
stasiun single busbar secara eksplisit, jadi penyebutan itu adalah bukti positif —
tetapi ketiadaannya bukan bukti sebaliknya.

| GI | Skema | Confidence | Bukti |
|---|---|---|---|
| AIS Pesanggaran | `SINGLE_SECTION` | **VERIFIED** | hal. 244: *"beroperasi single busbar dengan 1 bus section"* (Timur 108 MW, Barat 125 MW) |
| GIS Celukan Bawang | `ONE_HALF_CB` | INFERRED | SLD Bali 2026: konfigurasi diameter |
| GIS Pesanggaran | `DOUBLE_SECTION` | INFERRED | hal. 245: Section Utara 503 MW, Selatan 45,6 MW |
| Gilimanuk | `DOUBLE` | INFERRED | hal. 243–244: *"salah satu bus yang operasi"*; bus section baru diusulkan COD 2026 |
| Kapal | `DOUBLE` | INFERRED | hal. 243; bus section diusulkan COD 2030 |
| lainnya | `DOUBLE` | INFERRED | SLD Bali 2026 |

Hanya 1 dari 10 GI berstatus `VERIFIED`. Itu keadaan yang jujur saat ini.

## Konfigurasi 1½ CB memerlukan penanganan khusus

GIS Celukan Bawang memakai **one-and-a-half breaker**, dengan unit dasar
**diameter**: 3 CB melayani 2 sirkit, dan **CB tengah dipakai bersama** oleh
keduanya.

Ini melanggar asumsi "satu bay = satu CB" yang mendasari semua template lain,
sehingga template double-busbar tidak boleh dipakai di sana. Generator CIM harus
membuat CB tengah sebagai **satu objek `Breaker` dengan dua Terminal**, bukan dua
Breaker terpisah — bila salah, analisis N-1 dan aliran daya akan keliru.

Validator menegakkan: GI `ONE_HALF_CB` wajib punya bay bertipe `DIAMETER`, dan
tiap bay `DIAMETER` wajib punya baris di `10_DIAMETER`.

## Status template bay: rekonstruksi

`03_TEMPLATE` **bukan standar bay PLN resmi**. Tidak ada dokumen standar yang
tersedia saat ini. Isinya direkonstruksi dari 13 bay pada
`Gilimanuk_NMM_POC_Canonical_Draft.xml`:

| Pola | Jumlah contoh | Susunan |
|---|---:|---|
| Bay penghantar | 9 | `DS_BUS_A, DS_BUS_B, CB, DS_LINE` |
| Bay trafo | 2 | `DS_BUS_A, DS_BUS_B, CB, DS_TRAFO` |
| Bay generator | 1 | `DS_BUS_A, DS_BUS_B, CB, DS_GSU` |
| Bay kopel | 1 | `DS_BUS_A, CB, DS_BUS_B` |

Seluruhnya berpola double busbar. Template single busbar diturunkan dari
`02_Substation_Level_GI_Gill_Canonical.xml` (1 busbar, 2 DS per bay). Template
500 kV adalah placeholder tanpa bukti.

Setiap baris membawa kolom `status_rekonstruksi` dan `dasar_rekonstruksi`.
Semuanya saat ini `INFERRED`/`ASSUMED`/`UNKNOWN`; tidak ada yang `VERIFIED`.
Validator melaporkan hal ini sebagai peringatan, bukan error — itu keadaan yang
benar sampai ada engineer yang memvalidasinya terhadap SLD.

CT, PT/CVT, dan arrester belum masuk template. Dokumen `09` mensyaratkannya
untuk paket SLD lengkap; tambahkan saat bukti SLD tersedia.

## Kolom ED

`ed_functloc` dan `ed_functloc_root` sengaja dikosongkan. ED belum tersedia.
Kolomnya sudah disiapkan agar pemetaan nanti tidak mengubah struktur workbook.

## Aturan yang ditegakkan validator

Error (memblokir generator):

- kolom wajib kosong; `*_id` duplikat; nilai di luar kosakata terkendali
- referensi antar-sheet tidak ditemukan
- bay KOPEL dengan `bus_normal` ≠ `-`; bay double busbar tanpa `A`/`B`
- **nilai 0 pada impedansi tanpa `confidence=VERIFIED`** — nol berarti nol
  sungguhan, bukan "belum diketahui". Ini pola cacat yang tercatat di CLAUDE.md
- **`hv_kv == lv_kv`** — pola cacat trafo 150/150 kV pada file aset PoC
- `cos_phi` di luar (0,1]
- **`confidence=ASSUMED` tanpa baris di `09_ASUMSI`** — inilah yang mencegah
  asumsi tidak terbedakan dari fakta enam bulan kemudian

Peringatan (tidak memblokir):

- template belum `VERIFIED`; GI tanpa bay; `titik_ukur` tidak diketahui
- `bay_tipe` tampak tidak cocok dengan `template_id`

## Cara pakai

```bash
python scripts/build_workbook_template.py NMM_Model_Input_TEMPLATE.xlsx
python scripts/validate_workbook.py NMM_Model_Input_TEMPLATE.xlsx
```

Template dibangkitkan ulang dari skrip, bukan diedit sebagai biner. Kosakata
terkendali di `build_workbook_template.py` adalah sumber kebenaran tunggal —
validator dan (nanti) generator CIM membacanya dari sana.

## Gambar 6.2: aliran daya beban puncak

Buku Kerawanan memuat realisasi aliran daya subsistem Bali pada **15 Mei 2026
pukul 19:00 WITA, beban puncak diversity 1.296 MW** (hal. 237, Gambar 6.2).
Gambar itu memberi dua jenis angka yang **harus masuk sheet berbeda**:

| Angka di gambar | Contoh | Sheet | Alasan |
|---|---|---|---|
| Panah turun di GI (beban) | Negara 28,8 MW | `07_BEBAN` | konsumsi di lokasi itu |
| Angka pada garis antar-GI (aliran) | Gilimanuk–Negara 233,6 MW | `12_ALIRAN` | akibat dari beban, bukan beban |

Gambar juga memuat tegangan bus terukur (mis. Gilimanuk 145,5 kV) dan kapasitor
operasi (Gianyar 1×50 MVAR, Sanur 1×25 MVAR, Pbian 1×30 MVAR, Kapal 1×30 MVAR).

Seluruh nilai ini adalah **snapshot**, bukan rating dan bukan beban normal.
Karena itu `07_BEBAN` mewajibkan `skenario_id` + `jenis_nilai`, dan nilainya
milik companion skenario — tidak boleh diekspor sebagai nilai EQ biasa
(invariant #6 dan #9 di CLAUDE.md).

## Tiga aturan domain yang mudah dilanggar

**Titik ukur beban.** Angka 28,8 MW di sisi 150 kV bukan konsumsi sisi 20 kV;
ada rugi trafo. Kolom `titik_ukur` wajib diisi.

**Jangan hitung beban dua kali.** Bila GI tujuan sudah dimodelkan beserta
bebannya, aliran daya di penghantar adalah akibat dari beban itu — bukan beban
tambahan. Membuat `EnergyConsumer` dari tiap angka flow penghantar akan
melipatgandakan beban sistem.

Validator menegakkan ini: baris `07_BEBAN` yang `p_mw`-nya sama persis dengan
aliran penghantar menuju GI itu pada skenario yang sama ditolak sebagai error.
Gunakan `12_ALIRAN` untuk **memvalidasi hasil** load flow, bukan sebagai input.

**Snapshot bukan rating.** `jenis_nilai=RATING` ditolak di sheet beban — rating
trafo milik `06_TRAFO`. `jenis_nilai=DUMMY` wajib `confidence=ASSUMED`.

## Langkah berikutnya

1. Isi 1 GI penuh sebagai uji kelayakan pengisian.
2. Bereskan klasifikasi pada file aset (24 ConformLoad berlabel PLTD/BUS_SECTION/PHT).
3. Selidiki `nhftui:info` (`SIRKIT1`/`SIRKIT2`) sebagai penanda sirkit ganda.
4. Tulis `builder/` — ekspansi template → CB/DS/Terminal/ConnectivityNode.

Parser dan halaman unggah dibangun setelah workbook terbukti terisi. Kolom yang
benar-benar dipakai engineer adalah spesifikasi parser yang tidak perlu ditebak.
