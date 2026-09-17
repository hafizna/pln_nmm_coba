# 00 ? Project Brief

Arah disepakati 16 September 2026: repo ini menjadi workspace NMM berbasis CIM
untuk SLD peralatan primer seluruh sistem Bali, dengan kernel preservasi XML
sebagai fondasinya. Web API dan UI sudah berada di repo ini.

## Hasil yang dituju

SLD sistem dan detail GI/bay berasal dari model yang sama. Peralatan memiliki
identitas, koneksi, rating, status skenario, dan provenance. Data sumber yang
belum lengkap dapat dilengkapi struktur asumsi yang direview; unknown tetap
terlihat. Kelengkapan primer tidak mencakup wiring sekunder atau pembuktian
kelayakan operasi lapangan.

Lihat [spesifikasi minimum](09_BALI_PRIMARY_SLD_SPEC.md) untuk field,
[roadmap](07_PHASES.md) untuk timebox dan acceptance, serta README untuk status
implementasi dan cara menjalankan.

## Keputusan lingkup

- Bali adalah kasus integrasi pertama; model umum tetap dapat dipakai GI lain.
- SLD_engine tetap repo terpisah dan menjadi sumber masukan, bukan sumber
  kebenaran otomatis atau dependency runtime.
- SLD buku, gambar aliran daya, dan data aset direkonsiliasi berdasarkan tanggal,
  identitas, dan granularitas.
- Equipment switching menjadi objek jaringan eksplisit, termasuk ketika
  provisional. Aturan lama ?switching hanya annotation? digantikan keputusan ini.
- EQ menjadi inti pertukaran; detail aset yang belum didukung dan skenario
  memerlukan jalur preservasi tambahan, bukan patch cimpy.
- Snapshot/dummy operation diperbolehkan dengan label; solver dan defense scheme
  execution ditunda sampai SLD tersimpan dan round-trip berjalan.
- Tidak ada jaminan as-built atau load-flow-ready hanya karena diagram lengkap.
