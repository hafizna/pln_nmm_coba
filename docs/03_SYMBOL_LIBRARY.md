# 03 ? Symbol Library

## Lingkup milestone Bali

Dukung busbar/section, saluran/kabel, transformer, generator, beban ekuivalen,
kapasitor/reaktor, CB/PMT, disconnector/PMS, earthing switch, CT, CVT/PT, arrester,
serta wave trap bila terdapat pada sumber. Coupler adalah rangkaian bay yang
menghubungkan bus, bukan ikon pengganti semua peralatan di dalamnya.

## Semantik

- Simbol merujuk objek stabil dengan lokasi dan koneksi.
- CT ditempatkan pada posisi bay yang benar; CVT/PT dan arrester pada titik
  sambungan yang benar. Mapping instrumen tidak boleh menciptakan cabang
  impedansi fiktif.
- Urutan peralatan mengikuti sumber atau template berlabel assumed.
- Switch mendukung open/closed/unknown; provenance dan status dapat diperiksa.
- Terminal/CN dapat disembunyikan pada tampilan normal namun dapat diinspeksi.
- Layout tidak boleh menentukan koneksi listrik hanya karena garis bersilangan.

Gunakan koordinat PLN bila sesuai view. Posisi hasil layout/manual dicatat
asalnya. Simbol dan jalur tetap terbaca pada overview serta detail GI.
