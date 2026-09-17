# 11 — Laporan Gap Pengisian Workbook Bali

Status per 17 September 2026. Sumber: Buku Kerawanan SJB 2026 (Gambar 6.2 dan
tabel kerawanan Bali hal. 239–245), Single Line Bali 2026, dan canonical draft
Gilimanuk di repo ini.

Validator: **LULUS**, 24 peringatan, 0 error.

## Ringkasan angka

| Aspek | Terisi | Total | Cakupan |
|---|---:|---:|---:|
| GI | 22 | 22 | 100% |
| Ruas penghantar | 27 ruas / 55 sirkit | — | dari gambar |
| Beban GI (snapshot) | 17 | 22 | 77% |
| Aliran penghantar | 28 | ~30 | ~93% |
| Tegangan bus | 20 | 22 | 91% |
| Kapasitor | 4 | 4 | 100% |
| Pembangkit | 9 | ? | belum pasti |
| **Bay** | **10** | **~150–200** | **~5%** |
| **Impedansi saluran** | **0** | **55** | **0%** |
| **Data trafo** | **0** | **~40** | **0%** |

Beban termodel 1.153,5 MW terhadap beban puncak sistem 1.296 MW = **89%**.
Sisa 11% wajar: sebagian GI belum punya angka beban terbaca, dan rugi jaringan
tidak termasuk.

## Gap 1 — Bay: yang terbesar dan memblokir semuanya

Hanya 10 bay terisi, seluruhnya di Gilimanuk dan Celukan Bawang. Dua puluh GI
lain belum punya satu bay pun.

Ini bukan kekurangan data yang bisa ditutup dari dokumen yang ada. Gambar 6.2
adalah diagram aliran daya tingkat sistem — ia menunjukkan GI sebagai kotak,
bukan isi switchyard-nya. Susunan bay hanya ada di **SLD per-GI**, yang belum
tersedia di repo ini.

Konsekuensi: tanpa bay, tidak ada CB, DS, Terminal, maupun ConnectivityNode,
sehingga **topologi tidak bisa dibentuk**. Ini gap yang sama persis dengan yang
membuat file aset PoC punya 283 node berderajat-1.

Yang dibutuhkan: SLD per-GI dari P2B atau UPT Bali. Perkiraan 150–200 bay untuk
22 GI.

## Gap 2 — Impedansi saluran: 0 dari 55

Tidak ada satu pun nilai r, x, b, atau panjang saluran. Kolom sengaja
dikosongkan, bukan diisi nol — nol adalah klaim yang salah, dan validator
menolaknya tanpa `confidence=VERIFIED`.

Yang tersedia dari gambar hanyalah jenis konduktor dan IKHA untuk sebagian ruas
(mis. ACCC LISBON 2×310 mm², IKHA 2500 A; ACSR 2×Zebra 1600 A). Itu rating
termal, **bukan impedansi**.

Yang dibutuhkan: database setting Anda. Ini gap yang paling mudah ditutup karena
sumbernya sudah teridentifikasi.

## Gap 3 — Data trafo: 0 dari ~40

Gambar 6.2 menunjukkan simbol trafo di hampir setiap GI (Gianyar 2×60 MVA + 1
mobile 30 MVA menurut hal. 244), tetapi tidak memuat MVA per unit, winding kV,
vektor group, maupun Z%.

Yang dibutuhkan: ED (untuk MVA dan winding) + dokumen perhitungan setting
(untuk Z%, X/R, vektor group).

## Gap 4 — Diameter Celukan Bawang belum lengkap

Tiga diameter tercatat, tetapi kolom `posisi_2` (pasangan sirkit dalam satu
diameter) kosong untuk dua di antaranya. Gambar yang tersedia beresolusi terlalu
rendah untuk menelusuri jalur tiap sirkit.

Ini penting karena pada 1½ CB, **CB tengah dipakai bersama dua sirkit**. Tanpa
tahu pasangannya, generator CIM tidak bisa menentukan Terminal mana yang
menempel ke Breaker yang mana — dan analisis N-1 akan keliru.

Yang dibutuhkan: SLD GIS Celukan Bawang resolusi penuh.

## Neraca daya dan kriteria cadangan

Sheet `15_NERACA_DAYA` menampung konteks yang menjelaskan mengapa sebuah
skenario terlihat seperti itu. Dari Kerawanan hal. 239–240:

| Komponen pasokan | MW |
|---|---:|
| Transfer SKLT Jawa–Bali | 270 |
| KIT non-BBM | 598 |
| KIT BBM | 666 |
| **Total DMN** | **1.534** |

| Basis beban | Cadangan | Margin |
|---|---:|---:|
| Realisasi 2026 (1.296 MW) | 238 MW | 18,4% |
| Asumsi ROT 2026 (1.425 MW) | 109 MW | 7,6% |

Kriteria yang dipakai: **N-1 unit terbesar**. Pada basis ROT, buku mencatat
potensi defisit 52 MW saat N-1 dan 177 MW saat N-1-1. Ambang operasi pembangkit
BBM: beban sistem di atas 870 MW.

Validator memeriksa konsistensi aritmetiknya (komponen = DMN, DMN − beban =
cadangan) dan melaporkan saat cadangan lebih kecil dari unit terbesar.

Kerentanan khas Bali: 270 dari 1.534 MW (18%) datang lewat SKLT kabel laut,
bukan pembangkit lokal — itu sebabnya gangguan busbar Gilimanuk bisa memicu
island Bali (hal. 243).

## Empat hal yang perlu dibaca ulang dari gambar

Ini bukan gap data melainkan **ketidakpastian pembacaan saya**. Semuanya sudah
terdaftar di sheet `09_ASUMSI`.

| # | Temuan | Alasan |
|---|---|---|
| ASM-009 | 279,5 MW di Pesanggaran **dipindah ke pembangkitan** (SELESAI) | Dengan angka itu sebagai beban, total 1.433 MW > puncak sistem 1.296 MW. Kerawanan hal. 240 menegaskan Pesanggaran pusat pembangkit BBM Bali. Validator yang menangkapnya. |
| ASM-013 | Pembagian 279,5 MW antara AIS dan GIS Pesanggaran | Belum terbaca; perlu SLD resolusi penuh. |
| ASM-014 | `unit_terbesar_mw` 161 MW | Angka turunan dari cadangan 109 MW dan defisit N-1 52 MW; buku tidak mencetak kapasitas unit terbesar. |
| ASM-010 | 64,7 MW di Pemaron ditandai `ASSUMED` | Pemaron punya panah pembangkitan dan beban; arah panah belum pasti. |
| ASM-011 | Tegangan Negara 391,0 kV ditandai `UNKNOWN` | 391 kV pada sistem 150 kV = 2,61 pu. Hampir pasti salah baca atau salah cetak. Jangan dipakai. |
| ASM-012 | Pembangkitan sebagai `mw_maks` | Angka di gambar adalah keluaran saat snapshot, bukan kapasitas terpasang. |

Tiga ruas juga ditandai `UNKNOWN` karena keberadaannya belum pasti dari gambar:
Kapal–Pesanggaran, Bandara–Pesanggaran, dan hubungan AIS–GIS Pesanggaran.

## Yang justru bertambah jelas

**Busbar.** Hanya AIS Pesanggaran yang `VERIFIED` single busbar — buku
menyebutnya eksplisit (hal. 244). Dua puluh satu GI lain `INFERRED` double
busbar. Celukan Bawang `ONE_HALF_CB`. Gilimanuk dan Kapal belum punya bus
section; keduanya masih usulan (COD 2026 dan 2030).

**Phi.** Satu ruas `VERIFIED` single phi: Kapal–Pemecutan Kelod, buku menyebut
*"1 sirkit dengan Inom 973 A"* (hal. 242). Dua ruas `VERIFIED` double phi dari
penyebutan "#1,2". SKLT Gilimanuk–Banyuwangi `MULTI` 4 sirkit dari "SKLT #1–4".

**Pemisahan beban vs aliran.** Semua 28 angka pada garis antar-GI masuk
`12_ALIRAN`, bukan `07_BEBAN`. Validator menolak baris beban yang nilainya sama
persis dengan aliran menuju GI itu — diuji dan terbukti menangkap.

## Urutan yang disarankan

1. **SLD per-GI** — membuka Gap 1, yang memblokir topologi. Prioritas tertinggi.
2. **Database setting** — menutup Gap 2 (55 baris siap diisi).
3. **Baca ulang Gambar 6.2 resolusi penuh** — menyelesaikan ASM-009 s.d. 012.
4. **ED** — menutup sebagian Gap 3 dan mengisi kolom `ed_functloc`.

Langkah 1 dan 2 bisa berjalan paralel; keduanya dari sumber berbeda.

## Catatan metode

Setiap angka membawa `sumber` dan `confidence`, dan setiap nilai `ASSUMED`
terdaftar di `09_ASUMSI`. Tidak ada nilai yang diisi nol untuk menutupi
ketidaktahuan. Itu yang membedakan workbook ini dari percobaan prefill terdahulu
(dihapus 17 September 2026): gap tetap terlihat dan terhitung, bukan tersamar.
