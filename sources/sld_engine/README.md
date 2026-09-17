# Bukti sumber dari SLD engine

Diselamatkan dari percobaan `Bali_NMM_Prefill` yang dihapus 17 September 2026.
Percobaan itu menyederhanakan gap dan bukan acuan kebenaran, tetapi berkas
sumber di bawah ini tetap berguna sebagai bukti yang direkonsiliasi.

## `ss_bali_ingest.json`

Handoff dari repo SLD_engine: 27 objek, 31 koneksi antar-GI, 11 catatan risiko.
Efektif 2026-06-30, dirujuk ke Buku Kerawanan SJB 2026 sec. 6.3, Tabel 6.1,
Lampiran-5.

Bentuk koneksinya:

```json
{
  "from_external_key": "BANYUWANGI",
  "to_external_key": "GILIMANUK",
  "relation_type": "CONNECTED_TO",
  "circuit_type_hint": "SKLT",
  "status_hint": "ENERGIZED",
  "circuit_count": 2,
  "unit_no": "1,2",
  "confidence": 0.8,
  "note": "Traced from Appendix-5; verify circuit label against native SLD."
}
```

Berguna untuk memeriksa silang sheet `04_SAMBUNGAN`: `circuit_count` dan
`unit_no` adalah kandidat pembanding bagi `jml_sirkit` dan `sirkit_ke`.

Perhatikan `confidence: 0.8` dan catatan verifikasinya. Nilai ini **belum
terkonfirmasi terhadap SLD native**, jadi pakai sebagai kandidat, bukan fakta.
Catatan pada percobaan terdahulu juga menyebut nomor sirkit hanya eksplisit
untuk SKLT 1,2 dan 3,4; sisanya ordinal asumsi.

## `manifest.json`

Repositori, revisi, dan sha256 berkas sumber, untuk penelusuran.

## Tidak diselamatkan

`Bali_Prefill_EQ.xml`, `Bali_Prefill_Preview.html`, `validation.json`,
`scenario_unknown.json`, `risk_evidence.json`, dan
`gilimanuk_workbook_audit.json` dihapus. Semuanya turunan dari model prefill
yang digantikan oleh alur workbook → `builder/`.

Gap yang dicatat `ISSUES.md` percobaan itu kini terlacak di
`docs/11_BALI_FILL_GAP_REPORT.md` dengan angka terukur.
