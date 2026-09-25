# 12 — Cakupan CIM: penyedia model, bukan penghitung

Status: arah yang disepakati 17 September 2026. Perhitungan setting proteksi
ditunda; dokumen ini hanya menetapkan peran.

## Peran NMM

NMM **menyediakan model**; aplikasi sekitar **mengeksekusi studi**.

```
ED + SLD + laporan P2B  ──►  Workbook  ──►  CIM EQ  ──┬──►  PowerFactory (load flow, hubung singkat)
                                                      ├──►  PSS/E
                                                      ├──►  ETAP
                                                      └──►  OpenDSS (distribusi)
```

Konsekuensi yang menyederhanakan lingkup: NMM tidak perlu punya solver, tidak
perlu menghitung setting, dan tidak perlu menjalankan studi pola operasi. Yang
harus dijamin NMM adalah **model yang keluar cukup lengkap dan benar** untuk
dipakai aplikasi-aplikasi itu.

Ini sejalan dengan laporan PoC: translator awal menargetkan DIgSILENT
PowerFactory, dengan pengembangan lanjutan ke ETAP, PSS/E, dan OpenDSS
(hal. 28 dan 36). Daftar pustaka laporan juga memuat PSS/CAPE (tools koordinasi
proteksi), yang menandakan arah proteksi sudah terbayang sejak awal.

## Kesiapan model saat ini

Diukur terhadap kebutuhan minimum load flow, per 17 September 2026:

| Kebutuhan | Terisi | Perkiraan total | Cakupan |
|---|---:|---:|---:|
| Bus / GI | 22 | 22 | **100%** |
| Saluran: identitas & sambungan | 55 | 55 | **100%** |
| Pembangkit: P | 10 | ~9 | **100%** |
| Beban: P | 17 | ~22 | 77% |
| Bay (topologi switching) | 10 | ~175 | **6%** |
| Trafo: identitas | 2 | ~40 | **5%** |
| **Saluran: impedansi r/x/b** | **0** | **55** | **0%** |
| **Trafo: impedansi Z%** | **0** | **~40** | **0%** |
| **Beban: Q** | **0** | **~22** | **0%** |

Yang sudah kuat adalah **kerangka**: GI, ruas, sirkit, dan sambungan antar-GI
lengkap. Yang kosong adalah **isi listriknya**.

## Tiga hal yang memblokir ekspor ke solver

### 1. Impedansi — 0 dari 55 saluran, 0 dari ~40 trafo

Tanpa ini tidak ada load flow. Titik. Solver tidak bisa menghitung aliran tanpa
impedansi, dan mengisi nol akan menghasilkan hasil yang salah namun tampak
berjalan — persis cacat yang ada di file aset PoC.

Sumber sudah teridentifikasi (database setting dan dokumen perhitungan setting),
dan 55 baris sudah menunggu di `05_SALURAN`. Ini gap termudah ditutup.

### 2. Topologi bay — 10 dari ~175

Solver butuh tahu peralatan tersambung ke node mana. Tanpa bay: tidak ada CB,
PMS, Terminal, maupun ConnectivityNode.

PowerFactory dapat mereduksi node-breaker menjadi bus-branch sendiri, tetapi
hanya jika konektivitasnya benar. Model dengan 44% node berderajat-1 — keadaan
file aset PoC — akan menghasilkan pulau-pulau terpisah, bukan jaringan.

Sumber: SLD per-GI, belum tersedia di repo.

### 3. Daya reaktif Q — 0 dari ~22

Gambar 6.2 hanya memuat MW. Tanpa Q atau faktor daya, solver tidak bisa
menghitung profil tegangan, dan hasilnya tidak akan cocok dengan tegangan
terukur di `13_TEGANGAN`.

Opsi: ambil dari laporan P2B yang memuat MVAR, atau tetapkan cos φ per GI
sebagai asumsi eksplisit yang terdaftar di `09_ASUMSI`.

## Yang sudah siap dan sering terlewat

Beberapa hal yang sudah terisi justru penting untuk kualitas studi:

- **Kapasitor shunt** (`14_KAPASITOR`) — 4 unit, 135 MVAR total. Tanpa ini
  profil tegangan hasil simulasi tidak akan cocok dengan kenyataan.
- **Tegangan terukur** (`13_TEGANGAN`) — 20 bus. Ini pembanding untuk
  memvalidasi hasil load flow, bukan input.
- **Aliran penghantar** (`12_ALIRAN`) — 28 ruas. Pembanding, bukan input.
  Menjadikannya beban akan menghitung ganda.
- **Neraca daya** (`15_NERACA_DAYA`) — menjelaskan mengapa suatu skenario
  terlihat seperti itu; berguna saat hasil simulasi perlu dinilai wajar.

## Batas yang tetap berlaku

| NMM lakukan | NMM tidak lakukan |
|---|---|
| Menyimpan topologi dan parameter | Menjalankan load flow |
| Menyimpan skenario dan snapshot | Menghitung setting proteksi |
| Menjaga provenance tiap nilai | Menjalankan studi pola operasi |
| Ekspor CIM EQ + ekstensi PLN | Menggantikan PowerFactory/PSS-E |
| Impor kembali hasil (SV) | Menyimpan konfigurasi IED |

Studi pola operasi, koordinasi proteksi, dan hubung singkat dijalankan di
aplikasi sekitar, dengan model dari NMM sebagai masukan. Itu justru nilai
NMM: semua studi memakai model yang sama, sehingga hasil antar-unit sebanding.

## Urutan yang disarankan

1. **Database setting → impedansi.** Menutup gap paling menghalangi, sumbernya
   sudah jelas, 55 baris siap diisi.
2. **SLD per-GI → bay.** Membuka topologi; pekerjaan terbesar.
3. **Q atau cos φ.** Bisa paralel; boleh asumsi asal terdaftar.
4. **`builder/`** — ekspansi template menjadi objek CIM.
5. **Uji ekspor ke PowerFactory** dengan cakupan apa adanya, untuk menemukan
   persyaratan yang belum terlihat.

Langkah 5 layak dilakukan lebih awal daripada terasa nyaman: lebih baik
menemukan bahwa PowerFactory menolak sesuatu saat modelnya masih kecil.

## Catatan

Perhitungan setting proteksi ditunda dan akan dibahas terpisah. Kelas CIM untuk
proteksi memang ada (`ProtectionEquipment`, `CurrentRelay`, `ProtectedSwitch`,
`CurrentTransformer`), tetapi profil pertukarannya jauh kurang matang dibanding
CGMES untuk load flow, dan invariant #8 mensyaratkan preservasi objek CT/CVT
yang teruji sebelum itu bisa diklaim.
