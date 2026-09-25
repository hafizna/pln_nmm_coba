# 04 ? Editor UX

## Target alur

Buka kasus Bali atau import XML ? SLD sistem ? pilih GI ? detail bay/peralatan
? inspeksi/edit field ? validasi ? simpan versi ? export/import kembali.

## Tampilan minimum

- Overview menampilkan semua GI dan sirkit dalam manifest lingkup.
- Detail GI menampilkan bus/section, bay, PMT, PMS, ES, CT, CVT/PT, arrester,
  trafo, generator, shunt, dan perangkat sumber lainnya yang berlaku.
- Panel peralatan: ID, lokasi, terminal/koneksi, rating dan satuan, sumber,
  kualitas per field, serta status skenario terpilih.
- Pilihan skenario terpisah dari edit aset. Open/closed/unknown dibedakan;
  warna energized tidak ditetapkan hanya berdasarkan closed.
- Daftar gap membedakan objek hilang, koneksi unresolved, nilai unknown,
  asumsi, konflik sumber, dan placeholder template.
- Layer rating dan snapshot boleh ditoggle agar diagram tetap terbaca.

Drag hanya mengubah layout. Edit koneksi/parameter membuat perubahan model.
Perubahan status switch membuat perubahan skenario. Semua view merujuk identitas
aset yang sama. Simpan/export lengkap adalah target, belum klaim fitur tersedia.
