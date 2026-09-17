# 01 ? Data Model

## Lapisan yang sudah ada

Kernel membungkus cimpy dan menyimpan ekstensi PLN yang didukung dalam side-table.
Kunci round-trip adalah rdf:ID dengan leading underscore dihapus, bukan nilai
IdentifiedObject.mRID yang mungkin berbeda. Koordinat memakai Python repr().

## Kontrak target

1. Source evidence: file asli, dokumen/halaman, tanggal, label sumber.
2. Asset/connectivity: GI, VoltageLevel, Bay, equipment, Terminal,
   ConnectivityNode, winding trafo, dan rating.
3. Diagram: posisi/orientasi per view, referensi ke ID objek yang sama.
4. Scenario: referensi versi model, posisi switch, availability, asumsi dispatch.
5. Snapshot: timestamp, P/Q/V/I, arah, satuan, dan granularitas pengukuran.
6. Review: provenance dan kualitas per objek serta per atribut.

ID SLD engine/asset register dipetakan secara eksplisit ke ID CIM stabil.
Dua ujung satu sirkit memakai satu identitas aset. Jangan menggabungkan sirkit
paralel atau memecah angka aliran koridor ke per-sirkit tanpa asumsi tercatat.

Field minimum ada di [spesifikasi](09_BALI_PRIMARY_SLD_SPEC.md).
Field domain dalam spesifikasi belum merupakan nama properti CIM resmi;
mapping harus diperiksa terhadap profile/class yang benar sebelum implementasi.

## Kualitas dan readiness

Gunakan kualitas verified/inferred/assumed/unknown per atribut, dengan sumber,
alasan asumsi, reviewer bila tersedia, dan tanggal berlaku. Verified memerlukan
bukti/review; hasil OCR tidak otomatis verified.

Track readiness terpisah: XML parsable, EQ importable, references resolved,
primary SLD coverage, scenario complete, load-flow ready. Satu flag valid tidak
mewakili semuanya. Unknown bukan numeric zero atau status closed.

Raw XML dipertahankan; edit menghasilkan versi baru. Penyimpanan file paket
lokal cukup untuk milestone. Database produksi tidak menjadi prasyarat.
