"""Generate the NMM model-input workbook template.

This workbook is the single hand-filled contract that sits between PLN's
Enterprise Data (identity) and the CIM EQ generator (output). It holds only
what ED does not know: bay arrangement, inter-GI connections, electrical
parameters, and load.

Bay templates in sheet 03 are RECONSTRUCTED from the Gilimanuk canonical draft
in this repo, not taken from a formal PLN standard. They are hypotheses to be
confirmed by engineers against SLD evidence.

Usage:
    python scripts/build_workbook_template.py [output.xlsx]
"""

from __future__ import annotations

import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

# ---------------------------------------------------------------------------
# Controlled vocabularies. The validator and the CIM generator both read these.
# ---------------------------------------------------------------------------

BAY_TIPE = [
    "PENGHANTAR",
    "TRAFO",
    "GENERATOR",
    "KOPEL",
    "BUS_SECTION",
    "TRAFO_20KV",
    "DIAMETER",
]

TEMPLATE_ID = [
    "BAY_PHT_DB_150",
    "BAY_TRF_DB_150",
    "BAY_GEN_DB_150",
    "BAY_KOPEL_DB_150",
    "BAY_PHT_SB_150",
    "BAY_TRF_SB_150",
    "BAY_PHT_DB_500",
    "BAY_TRF_DB_500",
]

BUS_NORMAL = ["A", "B", "-"]

# Busbar arrangement is a property of the GI, not of the bay template.
# Evidence: Buku Kerawanan SJB 2026 names single-busbar stations explicitly
# (AIS Pesanggaran p.244, GI Perak p.190, GI Garung p.169), so absence of such
# a note is weak evidence of double busbar -- INFERRED, never VERIFIED.
SKEMA_BUSBAR = ["DOUBLE", "SINGLE", "SINGLE_SECTION", "DOUBLE_SECTION", "ONE_HALF_CB"]

# "Phi" is PLN operational shorthand for how many circuits run between two GI.
# Single phi = one line/circuit toward that GI (fails N-1). It is a property of
# the inter-GI corridor, NOT of the bay arrangement.
PHI = ["SINGLE", "DOUBLE", "MULTI"]

# Provenance vocabulary maps 1:1 onto plnnmm:provenance on export.
SUMBER = [
    "ED",
    "SLD_P2B",
    "SLD_ENGINE",
    "DB_SETTING",
    "DOK_SETTING",
    "LAPORAN_P2B",
    "BUKU_KERAWANAN",
    "ASUMSI",
    "TEMPLATE",
]

CONFIDENCE = ["VERIFIED", "INFERRED", "ASSUMED", "UNKNOWN"]

TITIK_UKUR = ["SISI_150KV", "SISI_20KV", "INCOMING_TRAFO", "PENYULANG", "TIDAK_DIKETAHUI"]

# A load figure is only meaningful with the system condition it was measured in.
# Buku Kerawanan Gambar 6.2 is one snapshot (15 May 2026 19:00 WITA, 1,296 MW
# diversity peak), not a rating and not a generic "normal" load.
JENIS_NILAI = ["SNAPSHOT", "RERATA", "PUNCAK", "RATING", "DUMMY"]

# ---------------------------------------------------------------------------
# Sheet definitions: (name, note, columns, rows)
# Column tuple: (header, width, required, validation_list_or_None)
# ---------------------------------------------------------------------------

REQ = True
OPT = False


def _sheet_gi():
    cols = [
        ("gi_id", 14, REQ, None),
        ("gi_nama", 26, REQ, None),
        ("uit", 10, OPT, None),
        ("upt", 12, OPT, None),
        ("skema_busbar", 18, REQ, SKEMA_BUSBAR),
        ("jml_bus_section", 16, OPT, None),
        ("busbar_sumber", 18, REQ, SUMBER),
        ("busbar_confidence", 18, REQ, CONFIDENCE),
        ("busbar_dok_ref", 26, OPT, None),
        ("nama_gbr62", 14, OPT, None),
        ("ed_functloc_root", 20, OPT, None),
        ("sld_ref", 20, OPT, None),
        ("catatan", 40, OPT, None),
    ]
    rows = [
        # 22 GI from Gambar 6.2 (Aliran Daya Beban Puncak UP2B Bali,
        # 15 May 2026 19:00 WITA). nama_gbr62 keeps the abbreviated label used
        # in that figure so figures can be traced back to their source.
        ["GIL", "GI GILIMANUK", "UIT JBM", "UPT BALI", "DOUBLE", 1, "BUKU_KERAWANAN", "INFERRED", "Kerawanan hal. 243-244", "GI GLNUK", "", "SLD Bali 2026",
         "Buku: 'salah satu bus yang operasi' -> double busbar. Bus Section diusulkan COD 2026."],
        ["BWI", "GI BANYUWANGI", "UIT JBM", "", "DOUBLE", 1, "SLD_P2B", "INFERRED", "Single Line Bali 2026", "GI BWNGI", "", "SLD Bali 2026",
         "GI lawan di sisi Jawa Timur; pangkal SKLT Jawa-Bali"],
        ["NEG", "GI NEGARA", "UIT JBM", "UPT BALI", "DOUBLE", 1, "SLD_P2B", "INFERRED", "Single Line Bali 2026", "GI NGARA", "", "SLD Bali 2026", ""],
        ["CLB", "PLTU CELUKAN BAWANG", "UIT JBM", "UPT BALI", "ONE_HALF_CB", 1, "SLD_P2B", "INFERRED", "Single Line Bali 2026", "PLTU CLBWG", "", "SLD Bali 2026",
         "Konfigurasi 1-1/2 CB (diameter). Unit dasar = DIAMETER; CB tengah dipakai bersama 2 sirkit. Isi sheet 10_DIAMETER."],
        ["PMR", "GI PEMARON", "UIT JBM", "UPT BALI", "DOUBLE", 1, "SLD_P2B", "INFERRED", "Single Line Bali 2026", "GI PMRON", "", "SLD Bali 2026",
         "Lokasi PLTD Sewa Tahap-1 (60 MW) & Tahap-2 (50 MW) (Kerawanan hal. 239)"],
        ["KPL", "GI KAPAL", "UIT JBM", "UPT BALI", "DOUBLE", 1, "BUKU_KERAWANAN", "INFERRED", "Kerawanan hal. 243", "GI KAPAL", "", "SLD Bali 2026",
         "GI simpul sub sistem Bali. Bus Section diusulkan COD 2030."],
        ["PSG-AIS", "AIS PESANGGARAN", "UIT JBM", "UPT BALI", "SINGLE_SECTION", 2, "BUKU_KERAWANAN", "VERIFIED", "Kerawanan hal. 244", "GI PSGRN", "", "SLD Bali 2026",
         "BUKU EKSPLISIT: 'single busbar dengan 1 bus section' (Timur 108 MW, Barat 125 MW). Busbar baru diusulkan COD 2026."],
        ["PSG-GIS", "GIS PESANGGARAN", "UIT JBM", "UPT BALI", "DOUBLE_SECTION", 2, "BUKU_KERAWANAN", "INFERRED", "Kerawanan hal. 245", "GIS PSGRN", "", "SLD Bali 2026",
         "Section Utara (503 MW) dan Selatan (45,6 MW). Skema busbar per section belum eksplisit."],
        ["GNYAR", "GI GIANYAR", "UIT JBM", "UPT BALI", "DOUBLE", 1, "SLD_P2B", "INFERRED", "Single Line Bali 2026", "GI GNYAR", "", "SLD Bali 2026",
         "2 trafo 60 MVA + 1 trafo mobile 30 MVA (Kerawanan hal. 244). Kapasitor 1x50 MVAR."],
        ["BTRTI", "GI BATURITI", "UIT JBM", "UPT BALI", "DOUBLE", 1, "SLD_P2B", "INFERRED", "Single Line Bali 2026", "GI BTRTI", "", "SLD Bali 2026",
         "Titik OLS tahapan 1-4 (Kerawanan hal. 241)"],
        ["PNGAN", "GI PAYANGAN", "UIT JBM", "UPT BALI", "DOUBLE", 1, "SLD_P2B", "INFERRED", "Single Line Bali 2026", "GI PNGAN", "", "SLD Bali 2026", ""],
        ["AMPRA", "GI AMLAPURA", "UIT JBM", "UPT BALI", "DOUBLE", 1, "SLD_P2B", "INFERRED", "Single Line Bali 2026", "GI AMPRA", "", "SLD Bali 2026", ""],
        ["KUBU", "GI KUBU", "UIT JBM", "UPT BALI", "DOUBLE", 1, "SLD_P2B", "INFERRED", "Single Line Bali 2026", "GI KUBU", "", "SLD Bali 2026",
         "Lokasi PLTD Sewa Tahap-3 (170 MW), COD bertahap 2026 (Kerawanan hal. 239)"],
        ["SANUR", "GI SANUR", "UIT JBM", "UPT BALI", "DOUBLE", 1, "SLD_P2B", "INFERRED", "Single Line Bali 2026", "GI SANUR", "", "SLD Bali 2026",
         "Kapasitor 1x25 MVAR"],
        ["PBIAN", "GI PADANG SAMBIAN", "UIT JBM", "UPT BALI", "DOUBLE", 1, "SLD_P2B", "INFERRED", "Single Line Bali 2026", "GI PBIAN", "", "SLD Bali 2026",
         "Kapasitor 1x30 MVAR"],
        ["PKLOD", "GI PEMECUTAN KELOD", "UIT JBM", "UPT BALI", "DOUBLE", 1, "SLD_P2B", "INFERRED", "Single Line Bali 2026", "GI PKLOD", "", "SLD Bali 2026",
         "Titik OLS 283,2 MW (Kerawanan hal. 242)"],
        ["TNLOT", "GIS TANAH LOT", "UIT JBM", "UPT BALI", "DOUBLE", 1, "SLD_P2B", "INFERRED", "Single Line Bali 2026", "GIS TNLOT", "", "SLD Bali 2026", ""],
        ["ASARI", "GI ANTOSARI", "UIT JBM", "UPT BALI", "DOUBLE", 1, "SLD_P2B", "INFERRED", "Single Line Bali 2026", "GI ASARI", "", "SLD Bali 2026", ""],
        ["BNDRA", "GIS BANDARA", "UIT JBM", "UPT BALI", "DOUBLE", 1, "SLD_P2B", "INFERRED", "Single Line Bali 2026", "GIS BANDARA", "", "SLD Bali 2026", ""],
        ["PECATU", "GIS PECATU", "UIT JBM", "UPT BALI", "DOUBLE", 1, "SLD_P2B", "INFERRED", "Single Line Bali 2026", "GIS PECATU", "", "SLD Bali 2026",
         "docs/09 menandai Pecatu perlu rekonsiliasi tanggal efektif/label operasional"],
        ["NSDUA", "GI NUSA DUA", "UIT JBM", "UPT BALI", "DOUBLE", 1, "SLD_P2B", "INFERRED", "Single Line Bali 2026", "GI NSDUA", "", "SLD Bali 2026", ""],
        ["PLTS", "GI PLTS", "UIT JBM", "UPT BALI", "DOUBLE", 1, "SLD_P2B", "UNKNOWN", "Single Line Bali 2026", "GI PLTS", "", "SLD Bali 2026",
         "Gambar 6.2 menunjukkan 0,0 MW. Identitas dan skema busbar belum jelas."],
    ]
    note = (
        "Daftar gardu induk. Satu baris = satu GI fisik. "
        "Sheet ini mencegah masalah 360 objek Substation untuk 19 nama GI. "
        "skema_busbar adalah properti GI, BUKAN properti bay -- template bay di sheet 03 "
        "harus konsisten dengan nilai di sini (ditegakkan validator). "
        "PERINGATAN: 'tidak disebut single busbar di buku' bukan bukti double busbar. "
        "Pakai INFERRED kecuali ada pernyataan eksplisit."
    )
    return "01_GI", note, cols, rows


def _sheet_bay():
    cols = [
        ("bay_id", 22, REQ, None),
        ("gi_id", 12, REQ, None),
        ("bay_nama", 30, REQ, None),
        ("bay_tipe", 16, REQ, BAY_TIPE),
        ("tegangan_kv", 12, REQ, None),
        ("template_id", 20, REQ, TEMPLATE_ID),
        ("bus_normal", 12, REQ, BUS_NORMAL),
        ("ed_functloc", 20, OPT, None),
        ("sld_ref", 22, OPT, None),
        ("sumber", 16, REQ, SUMBER),
        ("confidence", 14, REQ, CONFIDENCE),
        ("catatan", 30, OPT, None),
    ]
    rows = [
        ["GIL-150-BAY-BWI-C1", "GIL", "LINE BAY BWI-C1 GILIMANUK", "PENGHANTAR", 150, "BAY_PHT_DB_150", "A", "", "SLD Bali 2026", "SLD_P2B", "INFERRED", ""],
        ["GIL-150-BAY-BWI-C2", "GIL", "LINE BAY BWI-C2 GILIMANUK", "PENGHANTAR", 150, "BAY_PHT_DB_150", "B", "", "SLD Bali 2026", "SLD_P2B", "INFERRED", ""],
        ["GIL-150-BAY-NEG-C1", "GIL", "LINE BAY NEG-C1 GILIMANUK", "PENGHANTAR", 150, "BAY_PHT_DB_150", "A", "", "SLD Bali 2026", "SLD_P2B", "INFERRED", ""],
        ["GIL-150-BAY-TRF1", "GIL", "TRANSFORMER BAY TRF1 GILIMANUK", "TRAFO", 150, "BAY_TRF_DB_150", "A", "", "SLD Bali 2026", "SLD_P2B", "INFERRED", ""],
        ["GIL-150-BAY-TRF2", "GIL", "TRANSFORMER BAY TRF2 GILIMANUK", "TRAFO", 150, "BAY_TRF_DB_150", "B", "", "SLD Bali 2026", "SLD_P2B", "INFERRED", ""],
        ["GIL-150-BAY-GEN1", "GIL", "GENERATOR BAY PLTG GILIMANUK", "GENERATOR", 150, "BAY_GEN_DB_150", "B", "", "SLD Bali 2026", "SLD_P2B", "ASSUMED", "Susunan GSU perlu konfirmasi"],
        ["GIL-150-BAY-COUPLER", "GIL", "BUS COUPLER GILIMANUK 150 kV", "KOPEL", 150, "BAY_KOPEL_DB_150", "-", "", "SLD Bali 2026", "SLD_P2B", "INFERRED", ""],
        ["CLB-150-DIA-1", "CLB", "DIAMETER 1 GIS CELUKAN BAWANG", "DIAMETER", 150, "BAY_DIAMETER_150", "-", "", "SLD Bali 2026", "SLD_P2B", "ASSUMED", "1-1/2 CB; isi sheet 10_DIAMETER"],
        ["CLB-150-DIA-2", "CLB", "DIAMETER 2 GIS CELUKAN BAWANG", "DIAMETER", 150, "BAY_DIAMETER_150", "-", "", "SLD Bali 2026", "SLD_P2B", "ASSUMED", "1-1/2 CB; isi sheet 10_DIAMETER"],
        ["CLB-150-DIA-3", "CLB", "DIAMETER 3 GIS CELUKAN BAWANG", "DIAMETER", 150, "BAY_DIAMETER_150", "-", "", "SLD Bali 2026", "SLD_P2B", "ASSUMED", "1-1/2 CB; isi sheet 10_DIAMETER"],
    ]
    note = (
        "INTI WORKBOOK. Satu baris = satu bay. Kolom bus_normal menyatakan rel mana yang "
        "normal masuk (menjadi Switch.normalOpen di CIM); isi '-' untuk bay kopel. "
        "template_id menentukan CB/DS/Terminal/ConnectivityNode apa yang dibangkitkan otomatis."
    )
    return "02_BAY", note, cols, rows


def _sheet_template():
    cols = [
        ("template_id", 20, REQ, None),
        ("deskripsi", 40, REQ, None),
        ("skema_bus", 16, REQ, SKEMA_BUSBAR),
        ("urutan_alat", 56, REQ, None),
        ("jumlah_cb", 12, REQ, None),
        ("jumlah_ds", 12, REQ, None),
        ("status_rekonstruksi", 20, REQ, CONFIDENCE),
        ("dasar_rekonstruksi", 40, REQ, None),
    ]
    rows = [
        ["BAY_PHT_DB_150", "Bay penghantar, double busbar 150 kV", "DOUBLE", "DS_BUS_A,DS_BUS_B,CB,DS_LINE", 1, 3, "INFERRED", "Rekonstruksi dari 9 line bay Gilimanuk canonical draft"],
        ["BAY_TRF_DB_150", "Bay trafo, double busbar 150 kV", "DOUBLE", "DS_BUS_A,DS_BUS_B,CB,DS_TRAFO", 1, 3, "INFERRED", "Rekonstruksi dari 2 transformer bay Gilimanuk canonical draft"],
        ["BAY_GEN_DB_150", "Bay generator + GSU, double busbar 150 kV", "DOUBLE", "DS_BUS_A,DS_BUS_B,CB,DS_GSU", 1, 3, "ASSUMED", "Rekonstruksi dari 1 generator bay; susunan GSU belum terkonfirmasi"],
        ["BAY_KOPEL_DB_150", "Bay kopel bus 150 kV", "DOUBLE", "DS_BUS_A,CB,DS_BUS_B", 1, 2, "INFERRED", "Rekonstruksi dari bus coupler bay Gilimanuk canonical draft"],
        ["BAY_PHT_SB_150", "Bay penghantar, single busbar 150 kV", "SINGLE", "DS_BUS,CB,DS_LINE", 1, 2, "INFERRED", "Rekonstruksi dari GI_Gill focused model (1 busbar, 2 DS per bay)"],
        ["BAY_TRF_SB_150", "Bay trafo, single busbar 150 kV", "SINGLE", "DS_BUS,CB,DS_TRAFO", 1, 2, "INFERRED", "Rekonstruksi dari GI_Gill focused model"],
        ["BAY_PHT_SS_150", "Bay penghantar, single busbar + bus section 150 kV", "SINGLE_SECTION", "DS_BUS,CB,DS_LINE", 1, 2, "INFERRED", "Untuk AIS Pesanggaran (Kerawanan hal. 244); bay sama seperti single busbar, section dibentuk oleh bay BUS_SECTION"],
        ["BAY_SECTION_150", "Bay bus section (pemisah antar section busbar) 150 kV", "SINGLE_SECTION", "DS_SEC_1,CB,DS_SEC_2", 1, 2, "INFERRED", "Pemisah Section Timur/Barat AIS Pesanggaran (Kerawanan hal. 244)"],
        ["BAY_DIAMETER_150", "Diameter 1-1/2 CB: 3 CB melayani 2 sirkit", "ONE_HALF_CB",
         "DS_BUS_A,CB1,DS_S1_A,[SIRKIT-1],DS_S1_B,CB2_TENGAH,DS_S2_A,[SIRKIT-2],DS_S2_B,CB3,DS_BUS_B",
         3, 6, "INFERRED", "GIS Celukan Bawang (SLD Bali 2026). CB2 dipakai BERSAMA oleh sirkit 1 dan 2 -- satu bay != satu CB"],
        ["BAY_PHT_DB_500", "Bay penghantar, double busbar 500 kV", "DOUBLE", "DS_BUS_A,DS_BUS_B,CB,DS_LINE", 1, 3, "UNKNOWN", "Belum ada bukti SLD 500 kV; placeholder"],
        ["BAY_TRF_DB_500", "Bay trafo/IBT, double busbar 500 kV", "DOUBLE", "DS_BUS_A,DS_BUS_B,CB,DS_TRAFO", 1, 3, "UNKNOWN", "Belum ada bukti SLD 500 kV; placeholder"],
    ]
    note = (
        "KAMUS SUSUNAN BAY -- REKONSTRUKSI, BUKAN STANDAR PLN RESMI. "
        "Diturunkan dari 13 bay pada Gilimanuk canonical draft di repo ini. "
        "Setiap baris wajib divalidasi engineer terhadap SLD sebelum dipakai produksi. "
        "CT/PT/arrester belum dimasukkan; tambahkan bila SLD memuatnya. "
        "Ini satu-satunya sheet yang berlaku nasional -- sheet lain per-GI."
    )
    return "03_TEMPLATE", note, cols, rows


def _sheet_sambungan():
    cols = [
        ("ruas_id", 18, REQ, None),
        ("dari_gi", 10, REQ, None),
        ("ke_gi", 10, REQ, None),
        ("nama_ruas", 34, REQ, None),
        ("phi", 10, REQ, PHI),
        ("jml_sirkit", 12, REQ, None),
        ("sirkit_ke", 10, REQ, None),
        ("sambungan_id", 18, REQ, None),
        ("dari_bay", 22, REQ, None),
        ("ke_bay", 22, OPT, None),
        ("sumber", 16, REQ, SUMBER),
        ("confidence", 14, REQ, CONFIDENCE),
        ("dok_ref", 24, OPT, None),
        ("catatan", 34, OPT, None),
    ]
    rows = [
        # One row per CIRCUIT. Rows sharing ruas_id form one corridor.
        # dari_bay is a placeholder until per-GI bays are enumerated.
        ["RUAS-GIL-BWI", "GIL", "BWI", "SKLT 150kV GILIMANUK - BANYUWANGI", "MULTI", 4, 1, "PHT-GIL-BWI-C1", "GIL-150-BAY-NEG-C1", "", "BUKU_KERAWANAN", "INFERRED", "Kerawanan hal. 239", "Buku menyebut SKLT #1-4"],
        ["RUAS-GIL-BWI", "GIL", "BWI", "SKLT 150kV GILIMANUK - BANYUWANGI", "MULTI", 4, 2, "PHT-GIL-BWI-C2", "GIL-150-BAY-NEG-C1", "", "BUKU_KERAWANAN", "INFERRED", "Kerawanan hal. 239", ""],
        ["RUAS-GIL-BWI", "GIL", "BWI", "SKLT 150kV GILIMANUK - BANYUWANGI", "MULTI", 4, 3, "PHT-GIL-BWI-C3", "GIL-150-BAY-NEG-C1", "", "BUKU_KERAWANAN", "INFERRED", "Kerawanan hal. 239", ""],
        ["RUAS-GIL-BWI", "GIL", "BWI", "SKLT 150kV GILIMANUK - BANYUWANGI", "MULTI", 4, 4, "PHT-GIL-BWI-C4", "GIL-150-BAY-NEG-C1", "", "BUKU_KERAWANAN", "INFERRED", "Kerawanan hal. 239", ""],
        ["RUAS-GIL-NEG", "GIL", "NEG", "SUTT 150kV GILIMANUK - NEGARA", "DOUBLE", 2, 1, "PHT-GIL-NEG-C1", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-GIL-NEG", "GIL", "NEG", "SUTT 150kV GILIMANUK - NEGARA", "DOUBLE", 2, 2, "PHT-GIL-NEG-C2", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-GIL-CLB", "GIL", "CLB", "SUTT 150kV GILIMANUK - CELUKAN BAWANG", "DOUBLE", 2, 1, "PHT-GIL-CLB-C1", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-GIL-CLB", "GIL", "CLB", "SUTT 150kV GILIMANUK - CELUKAN BAWANG", "DOUBLE", 2, 2, "PHT-GIL-CLB-C2", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-CLB-PMR", "CLB", "PMR", "SUTT 150kV CELUKAN BAWANG - PEMARON", "DOUBLE", 2, 1, "PHT-CLB-PMR-C1", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-CLB-PMR", "CLB", "PMR", "SUTT 150kV CELUKAN BAWANG - PEMARON", "DOUBLE", 2, 2, "PHT-CLB-PMR-C2", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-CLB-KPL", "CLB", "KPL", "SUTT 150kV CELUKAN BAWANG - KAPAL", "DOUBLE", 2, 1, "PHT-CLB-KPL-C1", "GIL-150-BAY-NEG-C1", "", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan hal. 241", "Buku: 'Celukan Bawang - Kapal #1,2'"],
        ["RUAS-CLB-KPL", "CLB", "KPL", "SUTT 150kV CELUKAN BAWANG - KAPAL", "DOUBLE", 2, 2, "PHT-CLB-KPL-C2", "GIL-150-BAY-NEG-C1", "", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan hal. 241", ""],
        ["RUAS-PMR-BTRTI", "PMR", "BTRTI", "SUTT 150kV PEMARON - BATURITI", "DOUBLE", 2, 1, "PHT-PMR-BTRTI-C1", "GIL-150-BAY-NEG-C1", "", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan hal. 241", "Buku: 'Pemaron - Baturiti #1,2'"],
        ["RUAS-PMR-BTRTI", "PMR", "BTRTI", "SUTT 150kV PEMARON - BATURITI", "DOUBLE", 2, 2, "PHT-PMR-BTRTI-C2", "GIL-150-BAY-NEG-C1", "", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan hal. 241", ""],
        ["RUAS-BTRTI-PNGAN", "BTRTI", "PNGAN", "SUTT 150kV BATURITI - PAYANGAN", "DOUBLE", 2, 1, "PHT-BTRTI-PNGAN-C1", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-BTRTI-PNGAN", "BTRTI", "PNGAN", "SUTT 150kV BATURITI - PAYANGAN", "DOUBLE", 2, 2, "PHT-BTRTI-PNGAN-C2", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-BTRTI-GNYAR", "BTRTI", "GNYAR", "SUTT 150kV BATURITI - GIANYAR", "DOUBLE", 2, 1, "PHT-BTRTI-GNYAR-C1", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-BTRTI-GNYAR", "BTRTI", "GNYAR", "SUTT 150kV BATURITI - GIANYAR", "DOUBLE", 2, 2, "PHT-BTRTI-GNYAR-C2", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-PNGAN-GNYAR", "PNGAN", "GNYAR", "SUTT 150kV PAYANGAN - GIANYAR", "DOUBLE", 2, 1, "PHT-PNGAN-GNYAR-C1", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-PNGAN-GNYAR", "PNGAN", "GNYAR", "SUTT 150kV PAYANGAN - GIANYAR", "DOUBLE", 2, 2, "PHT-PNGAN-GNYAR-C2", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-NEG-ASARI", "NEG", "ASARI", "SUTT 150kV NEGARA - ANTOSARI", "DOUBLE", 2, 1, "PHT-NEG-ASARI-C1", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-NEG-ASARI", "NEG", "ASARI", "SUTT 150kV NEGARA - ANTOSARI", "DOUBLE", 2, 2, "PHT-NEG-ASARI-C2", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-ASARI-TNLOT", "ASARI", "TNLOT", "SUTT 150kV ANTOSARI - TANAH LOT", "DOUBLE", 2, 1, "PHT-ASARI-TNLOT-C1", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-ASARI-TNLOT", "ASARI", "TNLOT", "SUTT 150kV ANTOSARI - TANAH LOT", "DOUBLE", 2, 2, "PHT-ASARI-TNLOT-C2", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-TNLOT-KPL", "TNLOT", "KPL", "SUTT 150kV TANAH LOT - KAPAL", "DOUBLE", 2, 1, "PHT-TNLOT-KPL-C1", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-TNLOT-KPL", "TNLOT", "KPL", "SUTT 150kV TANAH LOT - KAPAL", "DOUBLE", 2, 2, "PHT-TNLOT-KPL-C2", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-GNYAR-AMPRA", "GNYAR", "AMPRA", "SUTT 150kV GIANYAR - AMLAPURA", "DOUBLE", 2, 1, "PHT-GNYAR-AMPRA-C1", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-GNYAR-AMPRA", "GNYAR", "AMPRA", "SUTT 150kV GIANYAR - AMLAPURA", "DOUBLE", 2, 2, "PHT-GNYAR-AMPRA-C2", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-AMPRA-KUBU", "AMPRA", "KUBU", "SUTT 150kV AMLAPURA - KUBU", "DOUBLE", 2, 1, "PHT-AMPRA-KUBU-C1", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-AMPRA-KUBU", "AMPRA", "KUBU", "SUTT 150kV AMLAPURA - KUBU", "DOUBLE", 2, 2, "PHT-AMPRA-KUBU-C2", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-GNYAR-SANUR", "GNYAR", "SANUR", "SUTT 150kV GIANYAR - SANUR", "DOUBLE", 2, 1, "PHT-GNYAR-SANUR-C1", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-GNYAR-SANUR", "GNYAR", "SANUR", "SUTT 150kV GIANYAR - SANUR", "DOUBLE", 2, 2, "PHT-GNYAR-SANUR-C2", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-PSG-SANUR", "PSG-GIS", "SANUR", "SUTT 150kV PESANGGARAN - SANUR", "DOUBLE", 2, 1, "PHT-PSG-SANUR-C1", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-PSG-SANUR", "PSG-GIS", "SANUR", "SUTT 150kV PESANGGARAN - SANUR", "DOUBLE", 2, 2, "PHT-PSG-SANUR-C2", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-KPL-PBIAN", "KPL", "PBIAN", "SUTT 150kV KAPAL - PADANG SAMBIAN", "DOUBLE", 2, 1, "PHT-KPL-PBIAN-C1", "GIL-150-BAY-NEG-C1", "", "BUKU_KERAWANAN", "INFERRED", "Kerawanan hal. 242", "Buku menyebut N-2 Kapal - Padang Sambian"],
        ["RUAS-KPL-PBIAN", "KPL", "PBIAN", "SUTT 150kV KAPAL - PADANG SAMBIAN", "DOUBLE", 2, 2, "PHT-KPL-PBIAN-C2", "GIL-150-BAY-NEG-C1", "", "BUKU_KERAWANAN", "INFERRED", "Kerawanan hal. 242", ""],
        ["RUAS-KPL-PKLOD", "KPL", "PKLOD", "SUTT 150kV KAPAL - PEMECUTAN KELOD", "SINGLE", 1, 1, "PHT-KPL-PKLOD-C1", "GIL-150-BAY-NEG-C1", "", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan hal. 242", "BUKU EKSPLISIT: '1 sirkit dengan Inom 973 A' -> single phi"],
        ["RUAS-PBIAN-PSG", "PBIAN", "PSG-GIS", "SUTT 150kV PADANG SAMBIAN - PESANGGARAN", "DOUBLE", 2, 1, "PHT-PBIAN-PSG-C1", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-PBIAN-PSG", "PBIAN", "PSG-GIS", "SUTT 150kV PADANG SAMBIAN - PESANGGARAN", "DOUBLE", 2, 2, "PHT-PBIAN-PSG-C2", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-KPL-PSG", "KPL", "PSG-GIS", "SUTT 150kV KAPAL - PESANGGARAN", "DOUBLE", 2, 1, "PHT-KPL-PSG-C1", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "UNKNOWN", "Single Line Bali 2026", "Keberadaan ruas belum pasti"],
        ["RUAS-KPL-PSG", "KPL", "PSG-GIS", "SUTT 150kV KAPAL - PESANGGARAN", "DOUBLE", 2, 2, "PHT-KPL-PSG-C2", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "UNKNOWN", "Single Line Bali 2026", ""],
        ["RUAS-BNDRA-PKLOD", "BNDRA", "PKLOD", "SKTT 150kV BANDARA - PEMECUTAN KELOD", "DOUBLE", 2, 1, "PHT-BNDRA-PKLOD-C1", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-BNDRA-PKLOD", "BNDRA", "PKLOD", "SKTT 150kV BANDARA - PEMECUTAN KELOD", "DOUBLE", 2, 2, "PHT-BNDRA-PKLOD-C2", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-BNDRA-PECATU", "BNDRA", "PECATU", "SKTT 150kV BANDARA - PECATU", "DOUBLE", 2, 1, "PHT-BNDRA-PECATU-C1", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-BNDRA-PECATU", "BNDRA", "PECATU", "SKTT 150kV BANDARA - PECATU", "DOUBLE", 2, 2, "PHT-BNDRA-PECATU-C2", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-PECATU-NSDUA", "PECATU", "NSDUA", "SKTT 150kV PECATU - NUSA DUA", "DOUBLE", 2, 1, "PHT-PECATU-NSDUA-C1", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-PECATU-NSDUA", "PECATU", "NSDUA", "SKTT 150kV PECATU - NUSA DUA", "DOUBLE", 2, 2, "PHT-PECATU-NSDUA-C2", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-NSDUA-PSG", "NSDUA", "PSG-GIS", "SKTT 150kV NUSA DUA - PESANGGARAN", "DOUBLE", 2, 1, "PHT-NSDUA-PSG-C1", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-NSDUA-PSG", "NSDUA", "PSG-GIS", "SKTT 150kV NUSA DUA - PESANGGARAN", "DOUBLE", 2, 2, "PHT-NSDUA-PSG-C2", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-PKLOD-PSG", "PKLOD", "PSG-GIS", "SUTT 150kV PEMECUTAN KELOD - PESANGGARAN", "DOUBLE", 2, 1, "PHT-PKLOD-PSG-C1", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-PKLOD-PSG", "PKLOD", "PSG-GIS", "SUTT 150kV PEMECUTAN KELOD - PESANGGARAN", "DOUBLE", 2, 2, "PHT-PKLOD-PSG-C2", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "INFERRED", "Single Line Bali 2026", ""],
        ["RUAS-BNDRA-PSG", "BNDRA", "PSG-GIS", "SKTT 150kV BANDARA - PESANGGARAN", "DOUBLE", 2, 1, "PHT-BNDRA-PSG-C1", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "UNKNOWN", "Single Line Bali 2026", "Keberadaan ruas belum pasti"],
        ["RUAS-BNDRA-PSG", "BNDRA", "PSG-GIS", "SKTT 150kV BANDARA - PESANGGARAN", "DOUBLE", 2, 2, "PHT-BNDRA-PSG-C2", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "UNKNOWN", "Single Line Bali 2026", ""],
        ["RUAS-PSGAIS-PSGGIS", "PSG-AIS", "PSG-GIS", "HUBUNGAN AIS - GIS PESANGGARAN", "DOUBLE", 2, 1, "PHT-PSGAIS-PSGGIS-C1", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "UNKNOWN", "Single Line Bali 2026", "Bentuk hubungan AIS-GIS belum pasti"],
        ["RUAS-PSGAIS-PSGGIS", "PSG-AIS", "PSG-GIS", "HUBUNGAN AIS - GIS PESANGGARAN", "DOUBLE", 2, 2, "PHT-PSGAIS-PSGGIS-C2", "GIL-150-BAY-NEG-C1", "", "SLD_P2B", "UNKNOWN", "Single Line Bali 2026", ""],
    ]
    note = (
        "Relasi antar-GI. Satu baris = SATU SIRKIT; beberapa baris dengan ruas_id sama "
        "membentuk satu ruas penghantar. "
        "phi = istilah operasional PLN untuk jumlah sirkit menuju satu GI: 'single phi' berarti "
        "hanya satu sirkit ke arah GI tersebut (tidak memenuhi N-1). Ini properti RUAS, "
        "bukan properti bay -- jangan dicampur dengan skema busbar di sheet 01. "
        "GI lawan DITETAPKAN manusia di sini, bukan hasil tebak string dari description. "
        "Kandidat boleh di-prefill dari description dan nhftui:info (SIRKIT1/SIRKIT2), tetap wajib dikonfirmasi."
    )
    return "04_SAMBUNGAN", note, cols, rows


def _sheet_saluran():
    cols = [
        ("nama_pht", 34, REQ, None),
        ("sambungan_id", 20, REQ, None),
        ("r_ohm", 12, OPT, None),
        ("x_ohm", 12, OPT, None),
        ("b_us", 12, OPT, None),
        ("panjang_km", 12, OPT, None),
        ("konduktor", 18, OPT, None),
        ("ikha_a", 12, OPT, None),
        ("sumber", 16, REQ, SUMBER),
        ("confidence", 14, REQ, CONFIDENCE),
        ("dok_ref", 26, OPT, None),
        ("tgl_data", 14, OPT, None),
    ]
    rows = [
        # One row per circuit. r/x/b DELIBERATELY EMPTY: PLN has no
        # per-corridor electrical parameters in any database yet.
        # Empty means unknown; 0 would be a false claim.
        ["SKLT 150kV GILIMANUK - BANYUWANGI #1", "PHT-GIL-BWI-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SKLT 150kV GILIMANUK - BANYUWANGI #2", "PHT-GIL-BWI-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SKLT 150kV GILIMANUK - BANYUWANGI #3", "PHT-GIL-BWI-C3", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SKLT 150kV GILIMANUK - BANYUWANGI #4", "PHT-GIL-BWI-C4", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV GILIMANUK - NEGARA #1", "PHT-GIL-NEG-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV GILIMANUK - NEGARA #2", "PHT-GIL-NEG-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV GILIMANUK - CELUKAN BAWANG #1", "PHT-GIL-CLB-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV GILIMANUK - CELUKAN BAWANG #2", "PHT-GIL-CLB-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV CELUKAN BAWANG - PEMARON #1", "PHT-CLB-PMR-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV CELUKAN BAWANG - PEMARON #2", "PHT-CLB-PMR-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV CELUKAN BAWANG - KAPAL #1", "PHT-CLB-KPL-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV CELUKAN BAWANG - KAPAL #2", "PHT-CLB-KPL-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV PEMARON - BATURITI #1", "PHT-PMR-BTRTI-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV PEMARON - BATURITI #2", "PHT-PMR-BTRTI-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV BATURITI - PAYANGAN #1", "PHT-BTRTI-PNGAN-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV BATURITI - PAYANGAN #2", "PHT-BTRTI-PNGAN-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV BATURITI - GIANYAR #1", "PHT-BTRTI-GNYAR-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV BATURITI - GIANYAR #2", "PHT-BTRTI-GNYAR-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV PAYANGAN - GIANYAR #1", "PHT-PNGAN-GNYAR-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV PAYANGAN - GIANYAR #2", "PHT-PNGAN-GNYAR-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV NEGARA - ANTOSARI #1", "PHT-NEG-ASARI-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV NEGARA - ANTOSARI #2", "PHT-NEG-ASARI-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV ANTOSARI - TANAH LOT #1", "PHT-ASARI-TNLOT-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV ANTOSARI - TANAH LOT #2", "PHT-ASARI-TNLOT-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV TANAH LOT - KAPAL #1", "PHT-TNLOT-KPL-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV TANAH LOT - KAPAL #2", "PHT-TNLOT-KPL-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV GIANYAR - AMLAPURA #1", "PHT-GNYAR-AMPRA-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV GIANYAR - AMLAPURA #2", "PHT-GNYAR-AMPRA-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV AMLAPURA - KUBU #1", "PHT-AMPRA-KUBU-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV AMLAPURA - KUBU #2", "PHT-AMPRA-KUBU-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV GIANYAR - SANUR #1", "PHT-GNYAR-SANUR-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV GIANYAR - SANUR #2", "PHT-GNYAR-SANUR-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV PESANGGARAN - SANUR #1", "PHT-PSG-SANUR-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV PESANGGARAN - SANUR #2", "PHT-PSG-SANUR-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV KAPAL - PADANG SAMBIAN #1", "PHT-KPL-PBIAN-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV KAPAL - PADANG SAMBIAN #2", "PHT-KPL-PBIAN-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV KAPAL - PEMECUTAN KELOD #1", "PHT-KPL-PKLOD-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV PADANG SAMBIAN - PESANGGARAN #1", "PHT-PBIAN-PSG-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV PADANG SAMBIAN - PESANGGARAN #2", "PHT-PBIAN-PSG-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV KAPAL - PESANGGARAN #1", "PHT-KPL-PSG-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV KAPAL - PESANGGARAN #2", "PHT-KPL-PSG-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SKTT 150kV BANDARA - PEMECUTAN KELOD #1", "PHT-BNDRA-PKLOD-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SKTT 150kV BANDARA - PEMECUTAN KELOD #2", "PHT-BNDRA-PKLOD-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SKTT 150kV BANDARA - PECATU #1", "PHT-BNDRA-PECATU-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SKTT 150kV BANDARA - PECATU #2", "PHT-BNDRA-PECATU-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SKTT 150kV PECATU - NUSA DUA #1", "PHT-PECATU-NSDUA-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SKTT 150kV PECATU - NUSA DUA #2", "PHT-PECATU-NSDUA-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SKTT 150kV NUSA DUA - PESANGGARAN #1", "PHT-NSDUA-PSG-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SKTT 150kV NUSA DUA - PESANGGARAN #2", "PHT-NSDUA-PSG-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV PEMECUTAN KELOD - PESANGGARAN #1", "PHT-PKLOD-PSG-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SUTT 150kV PEMECUTAN KELOD - PESANGGARAN #2", "PHT-PKLOD-PSG-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SKTT 150kV BANDARA - PESANGGARAN #1", "PHT-BNDRA-PSG-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["SKTT 150kV BANDARA - PESANGGARAN #2", "PHT-BNDRA-PSG-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["HUBUNGAN AIS - GIS PESANGGARAN #1", "PHT-PSGAIS-PSGGIS-C1", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
        ["HUBUNGAN AIS - GIS PESANGGARAN #2", "PHT-PSGAIS-PSGGIS-C2", None, None, None, None, "", None, "DB_SETTING", "UNKNOWN", "", ""],
    ]
    note = (
        "Impedansi saluran dari database setting. KOSONGKAN sel yang belum diketahui -- "
        "jangan isi 0. Nilai 0 pada r/bch adalah akar masalah data PLN yang sudah tercatat "
        "di CLAUDE.md; validator akan menolak 0 yang tidak disertai confidence VERIFIED."
    )
    return "05_SALURAN", note, cols, rows


def _sheet_trafo():
    cols = [
        ("trafo_id", 18, REQ, None),
        ("gi_id", 12, REQ, None),
        ("bay_id", 22, REQ, None),
        ("mva", 10, OPT, None),
        ("hv_kv", 10, OPT, None),
        ("lv_kv", 10, OPT, None),
        ("tv_kv", 10, OPT, None),
        ("vektor_group", 14, OPT, None),
        ("z_persen", 12, OPT, None),
        ("x_r", 10, OPT, None),
        ("tap_nominal", 12, OPT, None),
        ("pentanahan", 16, OPT, None),
        ("sumber", 16, REQ, SUMBER),
        ("confidence", 14, REQ, CONFIDENCE),
        ("dok_ref", 24, OPT, None),
    ]
    rows = [
        ["GIL-TRF1", "GIL", "GIL-150-BAY-TRF1", None, 150, 20, None, "", None, None, None, "", "DOK_SETTING", "UNKNOWN", ""],
        ["GIL-TRF2", "GIL", "GIL-150-BAY-TRF2", None, 150, 20, None, "", None, None, None, "", "DOK_SETTING", "UNKNOWN", ""],
    ]
    note = (
        "Data trafo. Sebagian (MVA, winding kV) kemungkinan ada di ED; sisanya (Z%, X/R, "
        "vektor group) dari dokumen perhitungan setting. Catatan: file aset PoC berisi "
        "trafo dengan winding 150/150 kV -- periksa hv_kv dan lv_kv tidak sama."
    )
    return "06_TRAFO", note, cols, rows


def _sheet_beban():
    cols = [
        ("beban_id", 20, REQ, None),
        ("gi_id", 10, REQ, None),
        ("skenario_id", 18, REQ, None),
        ("jenis_nilai", 14, REQ, JENIS_NILAI),
        ("p_mw", 10, OPT, None),
        ("q_mvar", 10, OPT, None),
        ("cos_phi", 10, OPT, None),
        ("titik_ukur", 18, REQ, TITIK_UKUR),
        ("trafo_id", 16, OPT, None),
        ("sumber", 16, REQ, SUMBER),
        ("confidence", 14, REQ, CONFIDENCE),
        ("dok_ref", 30, OPT, None),
    ]
    rows = [
        # All load arrows read from Gambar 6.2 (15 May 2026 19:00 WITA).
        # Down-arrow at a GI = load there. Figures on inter-GI lines are NOT
        # loads and belong in 12_ALIRAN.
        ["BEBAN-GIL-BP26", "GIL", "BP-2026-05-15", "SNAPSHOT", 5.5, None, None, "SISI_150KV", "", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2"],
        ["BEBAN-NEG-BP26", "NEG", "BP-2026-05-15", "SNAPSHOT", 28.8, None, None, "SISI_150KV", "", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2"],
        ["BEBAN-PMR-BP26", "PMR", "BP-2026-05-15", "SNAPSHOT", 64.7, None, None, "SISI_150KV", "", "BUKU_KERAWANAN", "ASSUMED", "Kerawanan Gbr 6.2 (tanda panah hijau, arah belum pasti)"],
        ["BEBAN-BTRTI-BP26", "BTRTI", "BP-2026-05-15", "SNAPSHOT", 20.2, None, None, "SISI_150KV", "", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2"],
        ["BEBAN-PNGAN-BP26", "PNGAN", "BP-2026-05-15", "SNAPSHOT", 71.1, None, None, "SISI_150KV", "", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2"],
        ["BEBAN-GNYAR-BP26", "GNYAR", "BP-2026-05-15", "SNAPSHOT", 111.1, None, None, "SISI_150KV", "", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2"],
        ["BEBAN-AMPRA-BP26", "AMPRA", "BP-2026-05-15", "SNAPSHOT", 37.6, None, None, "SISI_150KV", "", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2"],
        ["BEBAN-KUBU-BP26", "KUBU", "BP-2026-05-15", "SNAPSHOT", 16.5, None, None, "SISI_150KV", "", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2"],
        ["BEBAN-SANUR-BP26", "SANUR", "BP-2026-05-15", "SNAPSHOT", 138.5, None, None, "SISI_150KV", "", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2"],
        ["BEBAN-KPL-BP26", "KPL", "BP-2026-05-15", "SNAPSHOT", 160.7, None, None, "SISI_150KV", "", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2"],
        ["BEBAN-PBIAN-BP26", "PBIAN", "BP-2026-05-15", "SNAPSHOT", 100.1, None, None, "SISI_150KV", "", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2"],
        ["BEBAN-PKLOD-BP26", "PKLOD", "BP-2026-05-15", "SNAPSHOT", 160.9, None, None, "SISI_150KV", "", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2"],
        ["BEBAN-TNLOT-BP26", "TNLOT", "BP-2026-05-15", "SNAPSHOT", 38.5, None, None, "SISI_150KV", "", "BUKU_KERAWANAN", "INFERRED", "Kerawanan Gbr 6.2",],
        ["BEBAN-ASARI-BP26", "ASARI", "BP-2026-05-15", "SNAPSHOT", 18.0, None, None, "SISI_150KV", "", "BUKU_KERAWANAN", "INFERRED", "Kerawanan Gbr 6.2"],
        ["BEBAN-BNDRA-BP26", "BNDRA", "BP-2026-05-15", "SNAPSHOT", 48.4, None, None, "SISI_150KV", "", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2"],
        ["BEBAN-PECATU-BP26", "PECATU", "BP-2026-05-15", "SNAPSHOT", 54.6, None, None, "SISI_150KV", "", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2"],
        ["BEBAN-NSDUA-BP26", "NSDUA", "BP-2026-05-15", "SNAPSHOT", 78.3, None, None, "SISI_150KV", "", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2"],
        # 279,5 MW di Pesanggaran DIHAPUS dari beban: total beban termodel jadi
        # 1.433 MW > beban puncak sistem 1.296 MW, dan Pesanggaran adalah pusat
        # pembangkitan Bali. Angka itu hampir pasti pembangkitan, bukan beban.
        # Dicatat sebagai asumsi ASM-009 sampai dibaca ulang dari gambar asli.
    ]
    note = (
        "Beban dari laporan P2B / Buku Kerawanan. SHEET PALING SERING DI-REFRESH -- "
        "itu sebabnya dipisah dari sheet topologi 01-04. "
        "skenario_id WAJIB: satu angka beban tidak bermakna tanpa kondisi sistem saat "
        "diukur. Gambar 6.2 Buku Kerawanan adalah SNAPSHOT 15 Mei 2026 19:00 WITA "
        "(beban puncak diversity 1.296 MW), bukan beban normal dan bukan rating. "
        "Daftarkan tiap skenario di sheet 11_SKENARIO. "
        "titik_ukur wajib: angka di sisi 150 kV bukan konsumsi sisi 20 kV (ada rugi trafo). "
        "JANGAN membuat objek beban dari angka aliran daya PENGHANTAR -- itu beban ganda: "
        "aliran penghantar adalah AKIBAT dari beban GI tujuan yang sudah dimodelkan."
    )
    return "07_BEBAN", note, cols, rows


def _sheet_pembangkit():
    cols = [
        ("gen_id", 18, REQ, None),
        ("gi_id", 12, REQ, None),
        ("bay_id", 22, REQ, None),
        ("jenis", 14, OPT, None),
        ("mw_maks", 12, OPT, None),
        ("mw_min", 12, OPT, None),
        ("mvar_min", 12, OPT, None),
        ("mvar_maks", 12, OPT, None),
        ("kv_gen", 10, OPT, None),
        ("gsu_mva", 12, OPT, None),
        ("gsu_z_persen", 14, OPT, None),
        ("sumber", 16, REQ, SUMBER),
        ("confidence", 14, REQ, CONFIDENCE),
    ]
    rows = [
        # Generation read from Gambar 6.2. mw_maks here is the SNAPSHOT output at
        # 15 May 2026 19:00, not the nameplate rating -- see catatan.
        ["GIL-PLTG", "GIL", "GIL-150-BAY-GEN1", "PLTG", 126.4, None, None, None, None, None, None, "BUKU_KERAWANAN", "INFERRED"],
        ["CLB-U1", "CLB", "CLB-150-DIA-1", "PLTU", 125.0, None, None, None, None, None, None, "SLD_P2B", "INFERRED"],
        ["CLB-U2", "CLB", "CLB-150-DIA-2", "PLTU", 125.0, None, None, None, None, None, None, "SLD_P2B", "INFERRED"],
        ["CLB-U3", "CLB", "CLB-150-DIA-3", "PLTU", 130.0, None, None, None, None, None, None, "SLD_P2B", "INFERRED"],
        ["PMR-PLTG", "PMR", "GIL-150-BAY-GEN1", "PLTG", 196.5, None, None, None, None, None, None, "BUKU_KERAWANAN", "INFERRED"],
        ["PMR-PLTD-SEWA", "PMR", "GIL-150-BAY-GEN1", "PLTD_SEWA", 110.0, None, None, None, None, None, None, "BUKU_KERAWANAN", "INFERRED"],
        ["KUBU-PLTD-SEWA", "KUBU", "GIL-150-BAY-GEN1", "PLTD_SEWA", 170.0, None, None, None, None, None, None, "BUKU_KERAWANAN", "INFERRED"],
        ["PSGAIS-KIT", "PSG-AIS", "GIL-150-BAY-GEN1", "PLTDG", 159.6, None, None, None, None, None, None, "BUKU_KERAWANAN", "INFERRED"],
        # 279,5 MW semula salah dicatat sebagai beban (total jadi 1.433 MW > puncak
        # 1.296 MW). Kerawanan hal. 240 menegaskan Pesanggaran adalah pusat pembangkit
        # BBM Bali, jadi ini pembangkitan. Pembagian AIS/GIS belum terbaca -> ASM-013.
        ["PSG-KIT-279", "PSG-GIS", "GIL-150-BAY-GEN1", "PLTDG", 279.5, None, None, None, None, None, None, "BUKU_KERAWANAN", "ASSUMED"],
        ["PLTS-1", "PLTS", "GIL-150-BAY-GEN1", "PLTS", 0.0, None, None, None, None, None, None, "BUKU_KERAWANAN", "UNKNOWN"],
    ]
    note = (
        "Pembangkit dan trafo penaik (GSU). Laporan PoC mencatat koneksi generator "
        "disimplifikasi dan GSU belum selalu terwakili -- isi gsu_mva/gsu_z bila ada."
    )
    return "08_PEMBANGKIT", note, cols, rows


def _sheet_diameter():
    cols = [
        ("diameter_id", 20, REQ, None),
        ("gi_id", 12, REQ, None),
        ("bay_id", 22, REQ, None),
        ("posisi_1", 24, REQ, None),
        ("posisi_1_tipe", 16, REQ, None),
        ("posisi_2", 24, OPT, None),
        ("posisi_2_tipe", 16, OPT, None),
        ("cb_tengah_bersama", 18, REQ, None),
        ("sumber", 16, REQ, SUMBER),
        ("confidence", 14, REQ, CONFIDENCE),
        ("dok_ref", 22, OPT, None),
        ("catatan", 34, OPT, None),
    ]
    rows = [
        ["CLB-DIA-1", "CLB", "CLB-150-DIA-1", "U1 GENERATOR 125 MW", "GENERATOR", "", "PENGHANTAR", "YA", "SLD_P2B", "ASSUMED", "Single Line Bali 2026",
         "Pasangan posisi_2 belum terbaca dari gambar; wajib dikonfirmasi ke SLD resolusi penuh"],
        ["CLB-DIA-2", "CLB", "CLB-150-DIA-2", "U2 GENERATOR 125 MW", "GENERATOR", "", "PENGHANTAR", "YA", "SLD_P2B", "ASSUMED", "Single Line Bali 2026", ""],
        ["CLB-DIA-3", "CLB", "CLB-150-DIA-3", "U3 GENERATOR 130 MW", "GENERATOR", "TFT 60 MVA", "TRAFO", "YA", "SLD_P2B", "ASSUMED", "Single Line Bali 2026", ""],
    ]
    note = (
        "KHUSUS GI BERKONFIGURASI 1-1/2 CB (diameter). Isi hanya untuk GI dengan "
        "skema_busbar=ONE_HALF_CB. "
        "Pada 1-1/2 CB, satu diameter berisi 3 CB yang melayani 2 sirkit, dan CB TENGAH "
        "DIPAKAI BERSAMA oleh kedua sirkit. Karena itu asumsi 'satu bay = satu CB' TIDAK "
        "berlaku, dan template bay double busbar tidak boleh dipakai di sini. "
        "Generator CIM harus membuat CB tengah SATU objek Breaker dengan dua Terminal, "
        "bukan dua Breaker terpisah -- bila salah, N-1 dan aliran daya akan keliru."
    )
    return "10_DIAMETER", note, cols, rows


def _sheet_skenario():
    cols = [
        ("skenario_id", 18, REQ, None),
        ("nama", 34, REQ, None),
        ("tanggal", 14, REQ, None),
        ("jam", 10, OPT, None),
        ("zona_waktu", 12, OPT, None),
        ("beban_sistem_mw", 16, OPT, None),
        ("kondisi", 26, REQ, None),
        ("sumber", 16, REQ, SUMBER),
        ("dok_ref", 30, OPT, None),
        ("catatan", 40, OPT, None),
    ]
    rows = [
        ["BP-2026-05-15", "Beban puncak diversity Bali 2026", "2026-05-15", "19:00", "WITA", 1296.0,
         "Normal, seluruh sirkit operasi", "BUKU_KERAWANAN", "Kerawanan SJB 2026 Gbr 6.2",
         "Realisasi aliran daya subsistem Bali. Nilai ini SNAPSHOT, bukan rating dan bukan beban normal."],
    ]
    note = (
        "Daftar skenario/snapshot. Setiap baris di 07_BEBAN merujuk satu skenario di sini. "
        "Ini memenuhi pemisahan yang diwajibkan CLAUDE.md: rating aset, posisi normal, "
        "state skenario, dan nilai snapshot adalah empat hal berbeda dan tidak boleh dicampur. "
        "Nilai snapshot TIDAK BOLEH diekspor sebagai nilai EQ biasa; ia milik companion "
        "skenario. Status buka/tutup skenario juga tidak boleh disajikan sebagai "
        "Switch.normalOpen standar."
    )
    return "11_SKENARIO", note, cols, rows


def _sheet_aliran():
    cols = [
        ("aliran_id", 18, REQ, None),
        ("skenario_id", 18, REQ, None),
        ("ruas_id", 18, REQ, None),
        ("sambungan_id", 18, OPT, None),
        ("dari_gi", 10, REQ, None),
        ("ke_gi", 10, REQ, None),
        ("p_mw", 10, OPT, None),
        ("arah", 12, OPT, None),
        ("sumber", 16, REQ, SUMBER),
        ("confidence", 14, REQ, CONFIDENCE),
        ("dok_ref", 28, OPT, None),
        ("catatan", 40, OPT, None),
    ]
    rows = [
        # Figures on inter-GI lines in Gambar 6.2. These are CONSEQUENCES of the
        # loads in 07_BEBAN, never loads themselves.
        ["ALIR-BWI-GIL", "BP-2026-05-15", "RUAS-GIL-BWI", "", "BWI", "GIL", 318.5, "BWI->GIL", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2",
         "Transfer SKLT Jawa-Bali. Buku hal. 239: transfer dijaga 270 MW; nilai snapshot lebih tinggi."],
        ["ALIR-GIL-NEG", "BP-2026-05-15", "RUAS-GIL-NEG", "", "GIL", "NEG", 233.6, "GIL->NEG", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2", ""],
        ["ALIR-GIL-CLB", "BP-2026-05-15", "RUAS-GIL-CLB", "", "GIL", "CLB", 121.7, "GIL->CLB", "BUKU_KERAWANAN", "INFERRED", "Kerawanan Gbr 6.2", "Arah dibaca dari posisi angka; perlu konfirmasi"],
        ["ALIR-CLB-PMR", "BP-2026-05-15", "RUAS-CLB-PMR", "", "CLB", "PMR", 79.7, "CLB->PMR", "BUKU_KERAWANAN", "INFERRED", "Kerawanan Gbr 6.2", ""],
        ["ALIR-CLB-KPL", "BP-2026-05-15", "RUAS-CLB-KPL", "", "CLB", "KPL", 281.3, "CLB->KPL", "BUKU_KERAWANAN", "INFERRED", "Kerawanan Gbr 6.2",
         "Ruas kritis: Kerawanan hal. 241 membahas N-2 Celukan Bawang - Kapal #1,2"],
        ["ALIR-CLB-PMR2", "BP-2026-05-15", "RUAS-CLB-PMR", "", "CLB", "PMR", 6.3, "CLB->PMR", "BUKU_KERAWANAN", "UNKNOWN", "Kerawanan Gbr 6.2",
         "Angka 6,3 MW dekat PLTU CLBWG; ruas dan arah belum pasti"],
        ["ALIR-PMR-BTRTI", "BP-2026-05-15", "RUAS-PMR-BTRTI", "", "PMR", "BTRTI", 236.8, "PMR->BTRTI", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2",
         "Ruas OLS; Kerawanan hal. 241 membahas potensi overload"],
        ["ALIR-BTRTI-PNGAN", "BP-2026-05-15", "RUAS-BTRTI-PNGAN", "", "BTRTI", "PNGAN", 119.2, "BTRTI->PNGAN", "BUKU_KERAWANAN", "INFERRED", "Kerawanan Gbr 6.2", ""],
        ["ALIR-BTRTI-GNYAR", "BP-2026-05-15", "RUAS-BTRTI-GNYAR", "", "BTRTI", "GNYAR", 88.4, "BTRTI->GNYAR", "BUKU_KERAWANAN", "INFERRED", "Kerawanan Gbr 6.2", ""],
        ["ALIR-PNGAN-GNYAR", "BP-2026-05-15", "RUAS-PNGAN-GNYAR", "", "PNGAN", "GNYAR", 45.6, "PNGAN->GNYAR", "BUKU_KERAWANAN", "INFERRED", "Kerawanan Gbr 6.2", ""],
        ["ALIR-NEG-ASARI", "BP-2026-05-15", "RUAS-NEG-ASARI", "", "NEG", "ASARI", 199.4, "NEG->ASARI", "BUKU_KERAWANAN", "INFERRED", "Kerawanan Gbr 6.2", ""],
        ["ALIR-ASARI-TNLOT", "BP-2026-05-15", "RUAS-ASARI-TNLOT", "", "ASARI", "TNLOT", 178.2, "ASARI->TNLOT", "BUKU_KERAWANAN", "INFERRED", "Kerawanan Gbr 6.2", ""],
        ["ALIR-TNLOT-KPL", "BP-2026-05-15", "RUAS-TNLOT-KPL", "", "TNLOT", "KPL", 137.3, "TNLOT->KPL", "BUKU_KERAWANAN", "INFERRED", "Kerawanan Gbr 6.2", ""],
        ["ALIR-GNYAR-AMPRA", "BP-2026-05-15", "RUAS-GNYAR-AMPRA", "", "GNYAR", "AMPRA", 33.9, "GNYAR->AMPRA", "BUKU_KERAWANAN", "INFERRED", "Kerawanan Gbr 6.2", ""],
        ["ALIR-AMPRA-KUBU", "BP-2026-05-15", "RUAS-AMPRA-KUBU", "", "AMPRA", "KUBU", -3.4, "KUBU->AMPRA", "BUKU_KERAWANAN", "INFERRED", "Kerawanan Gbr 6.2",
         "Nilai negatif = aliran berbalik arah (Kubu memasok Amlapura)"],
        ["ALIR-GNYAR-SANUR", "BP-2026-05-15", "RUAS-GNYAR-SANUR", "", "GNYAR", "SANUR", 14.7, "GNYAR->SANUR", "BUKU_KERAWANAN", "INFERRED", "Kerawanan Gbr 6.2", ""],
        ["ALIR-PSG-SANUR", "BP-2026-05-15", "RUAS-PSG-SANUR", "", "PSG-GIS", "SANUR", 155.0, "PSG->SANUR", "BUKU_KERAWANAN", "INFERRED", "Kerawanan Gbr 6.2", ""],
        ["ALIR-KPL-PBIAN", "BP-2026-05-15", "RUAS-KPL-PBIAN", "", "KPL", "PBIAN", 174.8, "KPL->PBIAN", "BUKU_KERAWANAN", "INFERRED", "Kerawanan Gbr 6.2", ""],
        ["ALIR-KPL-PKLOD", "BP-2026-05-15", "RUAS-KPL-PKLOD", "", "KPL", "PKLOD", 75.6, "KPL->PKLOD", "BUKU_KERAWANAN", "INFERRED", "Kerawanan Gbr 6.2",
         "Kerawanan hal. 242: ruas 1 sirkit, Inom 973 A (single phi)"],
        ["ALIR-PBIAN-PSG", "BP-2026-05-15", "RUAS-PBIAN-PSG", "", "PBIAN", "PSG-GIS", 72.8, "PBIAN->PSG", "BUKU_KERAWANAN", "INFERRED", "Kerawanan Gbr 6.2", ""],
        ["ALIR-KPL-PSG", "BP-2026-05-15", "RUAS-KPL-PSG", "", "KPL", "PSG-GIS", 2.8, "KPL->PSG", "BUKU_KERAWANAN", "UNKNOWN", "Kerawanan Gbr 6.2", "Ruas belum pasti"],
        ["ALIR-BNDRA-PKLOD", "BP-2026-05-15", "RUAS-BNDRA-PKLOD", "", "BNDRA", "PKLOD", 25.6, "BNDRA->PKLOD", "BUKU_KERAWANAN", "INFERRED", "Kerawanan Gbr 6.2", ""],
        ["ALIR-BNDRA-PECATU", "BP-2026-05-15", "RUAS-BNDRA-PECATU", "", "BNDRA", "PECATU", 41.9, "BNDRA->PECATU", "BUKU_KERAWANAN", "INFERRED", "Kerawanan Gbr 6.2", ""],
        ["ALIR-PECATU-NSDUA", "BP-2026-05-15", "RUAS-PECATU-NSDUA", "", "PECATU", "NSDUA", 12.7, "PECATU->NSDUA", "BUKU_KERAWANAN", "INFERRED", "Kerawanan Gbr 6.2", ""],
        ["ALIR-NSDUA-PSG", "BP-2026-05-15", "RUAS-NSDUA-PSG", "", "NSDUA", "PSG-GIS", 91.4, "NSDUA->PSG", "BUKU_KERAWANAN", "INFERRED", "Kerawanan Gbr 6.2", ""],
        ["ALIR-PKLOD-PSG", "BP-2026-05-15", "RUAS-PKLOD-PSG", "", "PKLOD", "PSG-GIS", -39.4, "PSG->PKLOD", "BUKU_KERAWANAN", "INFERRED", "Kerawanan Gbr 6.2",
         "Nilai negatif = Pesanggaran memasok Pemecutan Kelod"],
        ["ALIR-BNDRA-PSG", "BP-2026-05-15", "RUAS-BNDRA-PSG", "", "BNDRA", "PSG-GIS", 67.2, "BNDRA->PSG", "BUKU_KERAWANAN", "UNKNOWN", "Kerawanan Gbr 6.2", "Ruas belum pasti"],
        ["ALIR-PSGAIS-PSGGIS", "BP-2026-05-15", "RUAS-PSGAIS-PSGGIS", "", "PSG-AIS", "PSG-GIS", 89.1, "AIS->GIS", "BUKU_KERAWANAN", "UNKNOWN", "Kerawanan Gbr 6.2",
         "Hubungan AIS-GIS Pesanggaran belum pasti"],
    ]
    note = (
        "Aliran daya penghantar per skenario, dari Gambar 6.2 Buku Kerawanan. "
        "PERINGATAN PALING PENTING DI WORKBOOK INI: angka di sini TIDAK BOLEH diubah "
        "menjadi objek EnergyConsumer/ConformLoad. Aliran penghantar adalah AKIBAT dari "
        "beban GI tujuan yang sudah dimodelkan di 07_BEBAN; menjadikannya beban tambahan "
        "akan menghitung beban dua kali dan membuat load flow salah. "
        "Gunakan sheet ini untuk VALIDASI hasil load flow, bukan sebagai input beban."
    )
    return "12_ALIRAN", note, cols, rows


def _sheet_tegangan():
    cols = [
        ("tegangan_id", 18, REQ, None),
        ("skenario_id", 18, REQ, None),
        ("gi_id", 12, REQ, None),
        ("kv_terukur", 14, REQ, None),
        ("kv_nominal", 14, OPT, None),
        ("pu", 10, OPT, None),
        ("sumber", 16, REQ, SUMBER),
        ("confidence", 14, REQ, CONFIDENCE),
        ("dok_ref", 24, OPT, None),
        ("catatan", 40, OPT, None),
    ]
    rows = [
        ["TEG-GIL-BP26", "BP-2026-05-15", "GIL", 145.5, 150, None, "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2", ""],
        ["TEG-NEG-BP26", "BP-2026-05-15", "NEG", 391.0, 150, None, "BUKU_KERAWANAN", "UNKNOWN", "Kerawanan Gbr 6.2",
         "JANGGAL: 391,0 kV pada sistem 150 kV (2,6 pu). Kemungkinan salah baca/salah cetak. Jangan dipakai sebelum dicek."],
        ["TEG-CLB-BP26", "BP-2026-05-15", "CLB", 150.6, 150, None, "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2", ""],
        ["TEG-PMR-BP26", "BP-2026-05-15", "PMR", 149.9, 150, None, "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2", ""],
        ["TEG-BTRTI-BP26", "BP-2026-05-15", "BTRTI", 146.5, 150, None, "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2", ""],
        ["TEG-PNGAN-BP26", "BP-2026-05-15", "PNGAN", 149.4, 150, None, "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2", ""],
        ["TEG-GNYAR-BP26", "BP-2026-05-15", "GNYAR", 145.6, 150, None, "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2", ""],
        ["TEG-AMPRA-BP26", "BP-2026-05-15", "AMPRA", 144.1, 150, None, "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2", ""],
        ["TEG-KUBU-BP26", "BP-2026-05-15", "KUBU", 146.3, 150, None, "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2", ""],
        ["TEG-SANUR-BP26", "BP-2026-05-15", "SANUR", 146.5, 150, None, "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2", ""],
        ["TEG-KPL-BP26", "BP-2026-05-15", "KPL", 144.9, 150, None, "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2", ""],
        ["TEG-PBIAN-BP26", "BP-2026-05-15", "PBIAN", 144.1, 150, None, "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2", ""],
        ["TEG-PKLOD-BP26", "BP-2026-05-15", "PKLOD", 147.1, 150, None, "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2", ""],
        ["TEG-TNLOT-BP26", "BP-2026-05-15", "TNLOT", 143.4, 150, None, "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2", ""],
        ["TEG-ASARI-BP26", "BP-2026-05-15", "ASARI", 145.8, 150, None, "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2", ""],
        ["TEG-BNDRA-BP26", "BP-2026-05-15", "BNDRA", 144.1, 150, None, "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2", ""],
        ["TEG-PECATU-BP26", "BP-2026-05-15", "PECATU", 144.3, 150, None, "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2", ""],
        ["TEG-NSDUA-BP26", "BP-2026-05-15", "NSDUA", 145.5, 150, None, "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2", ""],
        ["TEG-PSGGIS-BP26", "BP-2026-05-15", "PSG-GIS", 145.7, 150, None, "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2", ""],
        ["TEG-PLTS-BP26", "BP-2026-05-15", "PLTS", 143.0, 150, None, "BUKU_KERAWANAN", "INFERRED", "Kerawanan Gbr 6.2", ""],
    ]
    note = (
        "Tegangan bus terukur per skenario, dari Gambar 6.2. Ini nilai SNAPSHOT "
        "(hasil pengukuran), bukan tegangan nominal dan bukan setelan. "
        "Berguna untuk memvalidasi hasil load flow: tegangan hasil simulasi "
        "seharusnya mendekati nilai di sini pada skenario yang sama. "
        "Validator menandai nilai di luar 0,85-1,15 pu sebagai janggal."
    )
    return "13_TEGANGAN", note, cols, rows


def _sheet_kapasitor():
    cols = [
        ("kapasitor_id", 18, REQ, None),
        ("gi_id", 12, REQ, None),
        ("jumlah_step", 12, OPT, None),
        ("mvar_per_step", 16, REQ, None),
        ("mvar_total", 14, OPT, None),
        ("skenario_id", 18, OPT, None),
        ("status", 12, OPT, None),
        ("sumber", 16, REQ, SUMBER),
        ("confidence", 14, REQ, CONFIDENCE),
        ("dok_ref", 30, OPT, None),
    ]
    rows = [
        ["KAP-GNYAR", "GNYAR", 1, 50.0, 50.0, "BP-2026-05-15", "OPERASI", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2 kotak 'Kapasitor Operasi'"],
        ["KAP-SANUR", "SANUR", 1, 25.0, 25.0, "BP-2026-05-15", "OPERASI", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2 kotak 'Kapasitor Operasi'"],
        ["KAP-PBIAN", "PBIAN", 1, 30.0, 30.0, "BP-2026-05-15", "OPERASI", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2 kotak 'Kapasitor Operasi'"],
        ["KAP-KPL", "KPL", 1, 30.0, 30.0, "BP-2026-05-15", "OPERASI", "BUKU_KERAWANAN", "VERIFIED", "Kerawanan Gbr 6.2 kotak 'Kapasitor Operasi'"],
    ]
    note = (
        "Kapasitor shunt, dari kotak 'Kapasitor Operasi' pada Gambar 6.2. "
        "Kolom status menyatakan kondisi pada skenario tersebut (OPERASI/LEPAS); "
        "itu state skenario, bukan properti aset. Dalam CIM ini menjadi "
        "LinearShuntCompensator. Tanpa kapasitor ini, profil tegangan hasil "
        "load flow tidak akan cocok dengan sheet 13_TEGANGAN."
    )
    return "14_KAPASITOR", note, cols, rows


def _sheet_neraca():
    cols = [
        ("neraca_id", 16, REQ, None),
        ("skenario_id", 18, OPT, None),
        ("tahun", 10, REQ, None),
        ("beban_puncak_mw", 18, REQ, None),
        ("basis_beban", 20, REQ, None),
        ("transfer_sklt_mw", 18, OPT, None),
        ("kit_non_bbm_mw", 16, OPT, None),
        ("kit_bbm_mw", 14, OPT, None),
        ("dmn_total_mw", 14, OPT, None),
        ("cadangan_mw", 14, OPT, None),
        ("kriteria_cadangan", 22, REQ, None),
        ("unit_terbesar_mw", 18, OPT, None),
        ("defisit_n1_mw", 16, OPT, None),
        ("defisit_n11_mw", 16, OPT, None),
        ("ambang_bbm_mw", 16, OPT, None),
        ("sumber", 16, REQ, SUMBER),
        ("confidence", 14, REQ, CONFIDENCE),
        ("dok_ref", 24, OPT, None),
        ("catatan", 44, OPT, None),
    ]
    rows = [
        ["NRC-BALI-2026-RLS", "BP-2026-05-15", 2026, 1296.0, "REALISASI", 270.0, 598.0, 666.0, 1534.0, 238.0,
         "N-1 UNIT TERBESAR", None, None, None, 870.0, "BUKU_KERAWANAN", "VERIFIED", "Kerawanan hal. 239-240",
         "Realisasi 15 Mei 2026 19:00 WITA. Cadangan 238 MW (18,4%)."],
        ["NRC-BALI-2026-ROT", "", 2026, 1425.0, "ASUMSI_ROT", 270.0, 598.0, 666.0, 1534.0, 109.0,
         "N-1 UNIT TERBESAR", 161.0, 52.0, 177.0, 870.0, "BUKU_KERAWANAN", "VERIFIED", "Kerawanan hal. 239-240",
         "Basis perencanaan. Cadangan 109 MW (7,6%) -> defisit 52 MW saat N-1, 177 MW saat N-1-1. "
         "unit_terbesar_mw 161 MW adalah TURUNAN (109-52+... ), bukan angka tercetak: tandai ulang bila ada data unit."],
        ["NRC-BALI-2025", "", 2025, 1264.0, "REALISASI", None, None, None, None, None,
         "N-1 UNIT TERBESAR", None, None, None, None, "BUKU_KERAWANAN", "INFERRED", "Kerawanan hal. 237",
         "Puncak 14 Oktober 2025 19:00 WITA. Komposisi DMN 2025 tidak dinyatakan."],
    ]
    note = (
        "Neraca daya per tahun/skenario: berapa pasokan tersedia dibanding beban, dan "
        "berapa cadangan yang tersisa. Ini konteks yang menjelaskan MENGAPA sebuah "
        "skenario terlihat seperti itu, dan dipakai untuk memvalidasi hasil load flow. "
        "Kriteria cadangan Bali: N-1 unit terbesar (cadangan >= kapasitas unit terbesar). "
        "Catatan khas Bali: 270 dari 1.534 MW (18%) datang lewat SKLT kabel laut, bukan "
        "pembangkit lokal -- itu sebabnya gangguan busbar Gilimanuk bisa memicu island Bali. "
        "ambang_bbm_mw = beban sistem saat pembangkit BBM mulai wajib dioperasikan."
    )
    return "15_NERACA_DAYA", note, cols, rows


def _sheet_asumsi():
    cols = [
        ("asumsi_id", 14, REQ, None),
        ("ref_sheet", 16, REQ, None),
        ("ref_id", 22, REQ, None),
        ("field", 18, REQ, None),
        ("nilai", 16, REQ, None),
        ("dasar_asumsi", 44, REQ, None),
        ("pengusul", 16, OPT, None),
        ("tgl", 14, OPT, None),
        ("status_review", 16, OPT, None),
    ]
    rows = [
        ["ASM-001", "07_BEBAN", "BEBAN-NEG-2026-09", "p_mw per trafo", "14.4", "28,8 MW dibagi rata ke 2 trafo 30 MVA; buku tidak menyatakan pembagian", "", "", "BELUM"],
        ["ASM-002", "02_BAY", "GIL-150-BAY-GEN1", "template_id", "BAY_GEN_DB_150", "Susunan bay generator + GSU direkonstruksi dari 1 contoh; belum ada bukti SLD", "", "", "BELUM"],
        ["ASM-003", "02_BAY", "CLB-150-DIA-1", "template_id", "BAY_DIAMETER_150", "Jumlah diameter GIS Celukan Bawang dibaca dari gambar SLD beresolusi rendah", "", "", "BELUM"],
        ["ASM-004", "02_BAY", "CLB-150-DIA-2", "template_id", "BAY_DIAMETER_150", "Jumlah diameter GIS Celukan Bawang dibaca dari gambar SLD beresolusi rendah", "", "", "BELUM"],
        ["ASM-005", "02_BAY", "CLB-150-DIA-3", "template_id", "BAY_DIAMETER_150", "Jumlah diameter GIS Celukan Bawang dibaca dari gambar SLD beresolusi rendah", "", "", "BELUM"],
        ["ASM-006", "10_DIAMETER", "CLB-DIA-1", "posisi_2", "(kosong)", "Pasangan sirkit pada tiap diameter belum terbaca; perlu SLD resolusi penuh", "", "", "BELUM"],
        ["ASM-007", "10_DIAMETER", "CLB-DIA-2", "posisi_2", "(kosong)", "Pasangan sirkit pada tiap diameter belum terbaca; perlu SLD resolusi penuh", "", "", "BELUM"],
        ["ASM-008", "10_DIAMETER", "CLB-DIA-3", "posisi_2", "TFT 60 MVA", "Pasangan TFT dengan U3 dibaca dari gambar; perlu konfirmasi", "", "", "BELUM"],
        ["ASM-009", "08_PEMBANGKIT", "PSG-KIT-279", "klasifikasi", "PEMBANGKITAN", "Semula dicatat sebagai beban; total 1.433 MW > puncak 1.296 MW. Kerawanan hal. 240: Pesanggaran pusat pembangkit BBM. Dipindah ke pembangkitan.", "", "", "SELESAI"],
        ["ASM-010", "07_BEBAN", "BEBAN-PMR-BP26", "p_mw", "64.7", "Pemaron punya panah pembangkitan dan beban; arah panah 64,7 MW belum pasti", "", "", "BELUM"],
        ["ASM-011", "13_TEGANGAN", "TEG-NEG-BP26", "kv_terukur", "391.0", "391,0 kV pada sistem 150 kV = 2,61 pu. Hampir pasti salah baca atau salah cetak; jangan dipakai.", "", "", "BELUM"],
        ["ASM-012", "08_PEMBANGKIT", "PSGAIS-KIT", "mw_maks", "159.6", "Angka snapshot dari gambar, bukan kapasitas terpasang", "", "", "BELUM"],
        ["ASM-013", "08_PEMBANGKIT", "PSG-KIT-279", "gi_id", "PSG-GIS", "Pembagian 279,5 MW antara AIS dan GIS Pesanggaran belum terbaca; perlu SLD resolusi penuh", "", "", "BELUM"],
        ["ASM-014", "15_NERACA_DAYA", "NRC-BALI-2026-ROT", "unit_terbesar_mw", "161.0", "Turunan dari cadangan 109 MW dan defisit N-1 52 MW; buku tidak mencetak kapasitas unit terbesar", "", "", "BELUM"],
    ]
    note = (
        "REGISTER ASUMSI. Setiap nilai ber-confidence ASSUMED wajib punya baris di sini. "
        "Inilah yang membedakan asumsi dari fakta enam bulan kemudian, dan yang diekspor "
        "menjadi plnnmm:provenance/confidence pada CIM."
    )
    return "09_ASUMSI", note, cols, rows


SHEETS = [
    _sheet_gi,
    _sheet_bay,
    _sheet_template,
    _sheet_sambungan,
    _sheet_saluran,
    _sheet_trafo,
    _sheet_beban,
    _sheet_pembangkit,
    _sheet_diameter,
    _sheet_skenario,
    _sheet_aliran,
    _sheet_tegangan,
    _sheet_kapasitor,
    _sheet_neraca,
    _sheet_asumsi,
]

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

HDR_FILL = PatternFill("solid", fgColor="1F3864")
HDR_FONT = Font(color="FFFFFF", bold=True, size=10)
REQ_FILL = PatternFill("solid", fgColor="FFF2CC")
NOTE_FILL = PatternFill("solid", fgColor="E7E6E6")
NOTE_FONT = Font(italic=True, size=9, color="404040")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def _build_sheet(wb, name, note, cols, rows):
    ws = wb.create_sheet(name)

    # Row 1: note spanning the table width.
    ws.cell(row=1, column=1, value=note)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max(len(cols), 1))
    c = ws.cell(row=1, column=1)
    c.fill = NOTE_FILL
    c.font = NOTE_FONT
    c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[1].height = 46

    # Row 2: headers. Required columns get a marker.
    for i, (hdr, width, required, _vals) in enumerate(cols, start=1):
        label = f"{hdr} *" if required else hdr
        cell = ws.cell(row=2, column=i, value=label)
        cell.fill = HDR_FILL
        cell.font = HDR_FONT
        cell.border = BORDER
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(i)].width = width
    ws.row_dimensions[2].height = 28

    # Data rows.
    for r, row in enumerate(rows, start=3):
        for i, val in enumerate(row, start=1):
            cell = ws.cell(row=r, column=i, value=val)
            cell.border = BORDER
            cell.alignment = Alignment(vertical="top", wrap_text=False)
            if cols[i - 1][2]:
                cell.fill = REQ_FILL

    # Dropdown validation, applied well past the sample rows so engineers can
    # keep typing without re-adding validation.
    last = 400
    for i, (_hdr, _w, _req, vals) in enumerate(cols, start=1):
        if not vals:
            continue
        dv = DataValidation(
            type="list",
            formula1='"' + ",".join(vals) + '"',
            allow_blank=True,
            showDropDown=False,
        )
        ws.add_data_validation(dv)
        col = get_column_letter(i)
        dv.add(f"{col}3:{col}{last}")

    ws.freeze_panes = "A3"
    return ws


def _build_readme(wb):
    ws = wb.create_sheet("00_BACA_DULU", 0)
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 96

    lines = [
        ("NMM Model Input Workbook", ""),
        ("", ""),
        ("Apa ini", "Kontrak pengisian data antara Enterprise Data PLN dan generator CIM EQ."),
        ("Bukan apa", "Bukan pengganti ED, dan bukan tempat menyalin ulang isi ED."),
        ("Isi", "HANYA yang ED tidak punya: susunan bay, sambungan antar-GI, parameter, beban."),
        ("", ""),
        ("PEMBAGIAN SUMBER", ""),
        ("Sheet 01-04", "Topologi. Sumber: SLD P2B / SLD engine. Jarang berubah."),
        ("Sheet 05-06", "Parameter. Sumber: database setting & dokumen perhitungan setting."),
        ("Sheet 07-08", "Operasi. Sumber: laporan bulanan P2B / Buku Kerawanan. Sering di-refresh."),
        ("Sheet 09", "Register asumsi. Wajib untuk setiap nilai ber-confidence ASSUMED."),
        ("Sheet 10", "Khusus GI berkonfigurasi 1-1/2 CB (diameter), mis. GIS Celukan Bawang."),
        ("Sheet 11-12", "Skenario/snapshot dan aliran penghantar. Bukan nilai EQ biasa."),
        ("", ""),
        ("TIGA KONSEP BERBEDA", ""),
        ("skema_busbar (sheet 01)", "Properti GI: DOUBLE / SINGLE / SINGLE_SECTION / ONE_HALF_CB."),
        ("", "Semua bay di GI itu mengikutinya. Bukan properti bay."),
        ("phi (sheet 04)", "Properti RUAS penghantar: jumlah sirkit menuju satu GI."),
        ("", "'Single phi' = hanya 1 sirkit ke arah GI itu (N-1 tidak terpenuhi)."),
        ("", "Tidak ada hubungannya dengan susunan bay atau busbar."),
        ("jenis_nilai (sheet 07)", "Konteks angka: SNAPSHOT / RERATA / PUNCAK / DUMMY."),
        ("", "Satu angka beban tidak bermakna tanpa skenario saat diukur."),
        ("", ""),
        ("BEBAN vs ALIRAN", ""),
        ("Panah turun di GI", "Itu BEBAN -> sheet 07_BEBAN."),
        ("Angka pada garis antar-GI", "Itu ALIRAN -> sheet 12_ALIRAN."),
        ("Jangan tertukar", "Aliran penghantar adalah AKIBAT dari beban GI tujuan."),
        ("", "Menjadikannya objek beban = menghitung beban dua kali."),
        ("", "Validator menolak p_mw yang sama persis dengan aliran menuju GI itu."),
        ("", ""),
        ("ATURAN WAJIB", ""),
        ("1. Kolom sumber", "Setiap baris parameter wajib menyebut sumbernya. Ini jadi plnnmm:provenance."),
        ("2. bay_id kunci", "Semua sheet merujuk bay_id, bukan nama bay. Nama bay PLN tidak konsisten."),
        ("3. Kosong bukan nol", "Nilai belum diketahui DIKOSONGKAN. Jangan isi 0. Nol berarti nol sungguhan."),
        ("4. Sheet 07 terpisah", "Refresh beban bulanan tidak boleh menyentuh sheet 01-06."),
        ("5. Asumsi tercatat", "confidence=ASSUMED tanpa baris di sheet 09 akan ditolak validator."),
        ("", ""),
        ("STATUS TEMPLATE BAY", ""),
        ("Peringatan", "Sheet 03_TEMPLATE adalah REKONSTRUKSI dari canonical draft Gilimanuk,"),
        ("", "BUKAN standar bay PLN resmi. Wajib divalidasi engineer sebelum dipakai produksi."),
        ("Busbar Bali", "Hanya AIS Pesanggaran yang VERIFIED (buku eksplisit: single busbar"),
        ("", "dengan 1 bus section). Sisanya INFERRED. 'Tidak disebut single busbar'"),
        ("", "BUKAN bukti double busbar."),
        ("Dasar", "13 bay pada Gilimanuk_NMM_POC_Canonical_Draft.xml: 9 bay penghantar,"),
        ("", "2 bay trafo, 1 bay generator, 1 bay kopel -- semuanya pola double busbar."),
        ("", ""),
        ("KOLOM ED", ""),
        ("ed_functloc", "Dikosongkan untuk sekarang. ED belum tersedia. Kolom sudah disiapkan"),
        ("", "supaya pemetaan nanti tidak mengubah struktur workbook."),
        ("", ""),
        ("Tanda *", "Kolom berbintang = wajib diisi. Sel kuning = kolom wajib."),
        ("Baris contoh", "Baris data yang ada adalah CONTOH dari GI Gilimanuk. Ganti dengan data asli."),
    ]

    for r, (a, b) in enumerate(lines, start=1):
        ca = ws.cell(row=r, column=1, value=a)
        cb = ws.cell(row=r, column=2, value=b)
        ca.alignment = Alignment(vertical="top", wrap_text=True)
        cb.alignment = Alignment(vertical="top", wrap_text=True)
        if a and not b:
            ca.font = Font(bold=True, size=11, color="1F3864")
        else:
            ca.font = Font(bold=True, size=10)
    ws.cell(row=1, column=1).font = Font(bold=True, size=14, color="1F3864")
    return ws


def main(argv):
    out = Path(argv[1]) if len(argv) > 1 else Path("NMM_Model_Input_TEMPLATE.xlsx")

    wb = Workbook()
    wb.remove(wb.active)

    for fn in SHEETS:
        name, note, cols, rows = fn()
        _build_sheet(wb, name, note, cols, rows)

    _build_readme(wb)

    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    print(f"wrote {out}")
    print(f"sheets: {', '.join(wb.sheetnames)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
