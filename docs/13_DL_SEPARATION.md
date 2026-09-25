s# 13 — Pemisahan Diagram Layout: apa yang salah dan bagaimana diperbaiki

Catatan ini untuk ditunjukkan kepada tim PoC dan pengguna. Seluruh isinya
berasal dari file nyata di repo, bukan penjelasan konseptual. Setiap klaim bisa
diperiksa sendiri dengan perintah yang disertakan.

Nada dokumen ini sengaja teknis, bukan menyalahkan: keputusan tim PoC masuk akal
untuk membuktikan alur end-to-end dalam waktu singkat. Yang perlu diperbaiki
adalah struktur, bukan orangnya.

---

## 1. Keadaan sekarang: koordinat tinggal di dalam file Equipment

Ambil `02d_CIM_EQ_1-SS_Filled-WithCoordinate_250604.xml` — keluaran UI NMM
setelah pengguna merapikan SLD. Isinya seperti ini:

```xml
<cim:BusbarSection rdf:ID="_ab6a2494-...">
  <cim:IdentifiedObject.name>1</cim:IdentifiedObject.name>
  <plnicp:DiagramProperty.x>558.0909726137421</plnicp:DiagramProperty.x>
  <plnicp:DiagramProperty.y>123.65246948593943</plnicp:DiagramProperty.y>
</cim:BusbarSection>
```

Koordinat menempel langsung pada objek peralatan. Namespace `plnicp`
(`http://iconpln.co.id#`) adalah ekstensi PLN Icon Plus, bukan CIM.

Yang menarik, file itu **menyatakan dirinya sebagai profil Equipment**:

```xml
<md:Model.profile>http://entsoe.eu/CIM/EquipmentCore/3/1</md:Model.profile>
<md:Model.profile>http://entsoe.eu/CIM/EquipmentOperation/3/1</md:Model.profile>
```

Jadi ada 52 properti koordinat di dalam file yang mengaku hanya berisi model
peralatan. Aplikasi lain yang membaca file ini sebagai EQ murni akan mengabaikan
koordinat itu tanpa pesan apa pun.

Verifikasi sendiri:

```powershell
python -c "import re; s=open('02d_CIM_EQ_1-SS_Filled-WithCoordinate_250604.xml',encoding='utf-8',errors='replace').read(); print('plnicp:',len(re.findall(r'plnicp:DiagramProperty.x',s)), '| kelas Diagram:',len(re.findall(r'<cim:Diagram',s)))"
```

Hasilnya: `plnicp: 52 | kelas Diagram: 0`.

---

## 2. Empat akibat nyata

### 2.1 Satu peralatan hanya bisa punya satu posisi

`DiagramProperty.x` adalah properti dari objek peralatan. Sebuah PMT tidak bisa
punya posisi berbeda pada diagram sistem dan pada diagram detail GI, karena
hanya ada satu tempat menyimpannya.

Padahal `docs/01_DATA_MODEL.md` repo ini sendiri sudah mensyaratkan *"Diagram:
posisi/orientasi per view, referensi ke ID objek yang sama"* — kebutuhan yang
tidak bisa dipenuhi struktur ini.

### 2.2 Layout dan model berbagi satu file, jadi refresh berisiko

Setiap kali model diperbarui dari ED, file EQ ditulis ulang. Kalau layout ada di
dalamnya, kerja pengguna merapikan SLD ikut tertimpa. Satu-satunya perlindungan
adalah lapisan preservasi seperti `adapter.py` di repo ini — yang memang
dibangun persis untuk menambal masalah ini.

Dengan kata lain: separuh nilai repo ini selama ini adalah menambal akibat dari
keputusan struktur tersebut.

### 2.3 Ekspor standar harus membuang layout

`docs/02_FILE_FORMAT.md` mencatat mode `standard_cgmes` "will not preserve PLN's
diagram/UI annotations". Jadi pengguna dihadapkan pilihan: file standar tanpa
tata letak, atau file dengan tata letak yang tidak standar.

### 2.4 Koordinat itu hasil kerja manual yang seharusnya tidak perlu

Perhatikan angkanya: `558.0909726137421`, `123.65246948593943`. Pecahan panjang
seperti itu adalah jejak posisi drag mouse.

Bandingkan dengan `Gilimanuk_NMM_POC_Canonical_Draft.xml` yang koordinatnya
`80`, `165`, `180`, `195`, `700` — bulat, berjarak tetap 15. Itu dibangkitkan
program.

Laporan PoC halaman 24 menyatakannya terus terang: *"SLD yang muncul perlu
dirapikan oleh pengguna secara manual... opsi agar NMM secara otomatis membuat
SLD rapi belum tersedia."*

Jadi pengguna diminta mengerjakan sesuatu yang bisa dikerjakan komputer, lalu
hasilnya disimpan di tempat yang membuatnya rapuh.

---

## 3. Yang standar sebenarnya sudah sediakan

CGMES memisahkan ini sejak awal. Layout milik profil **DL (DiagramLayout)**,
didefinisikan di IEC 61970-453, dengan rantai objek:

```
Diagram  ──►  DiagramObject  ──►  DiagramObjectPoint
                    │                  (xPosition, yPosition)
                    └── IdentifiedObject ──► mRID objek di EQ
```

Kuncinya: **posisi menempel pada DiagramObject, bukan pada peralatan.** Satu
peralatan bisa muncul di banyak diagram, masing-masing dengan posisi sendiri.

EPRI *Network Model Manager Technical Market Requirements* (3002003053),
requirement R1.2, mewajibkan sistem NMM mengelola DL secara bawaan, dan halaman
72 menempatkan DL sebagai bagian model tersendiri dengan **urutan versi
terpisah** dari EQ.

### Anggapan yang keliru dan perlu dikoreksi

Dokumen repo ini sebelumnya menyatakan DL adalah "fase depan" karena dianggap
belum didukung. **Itu tidak benar.** cimpy 1.1.0 yang sudah dipakai memuat
seluruh kelas DL:

```powershell
python -c "import cimpy,os,glob; p=os.path.dirname(cimpy.__file__); print([os.path.basename(f) for f in glob.glob(p+'/cgmes_v2_4_15/Diagram*.py')])"
```

Hasilnya: `Diagram.py`, `DiagramLayoutVersion.py`, `DiagramObject.py`,
`DiagramObjectGluePoint.py`, `DiagramObjectPoint.py`, `DiagramObjectStyle.py`,
`DiagramStyle.py` — ditambah `TextDiagramObject.py` dan `VisibilityLayer.py`.
Enum profilnya di `cgmes_v2_4_15/Base.py` juga memuat seluruh sepuluh profil,
termasuk `DL=7`.

Dukungannya sudah ada sejak awal; yang belum ada hanyalah pemakaiannya.

---

## 4. Bentuk yang kita hasilkan sekarang

Dua file terpisah. **`bali_EQ.xml`** — model listrik, tanpa satu pun data
tampilan:

```xml
<md:Model.profile>http://entsoe.eu/CIM/EquipmentCore/3/1</md:Model.profile>
<cim:Breaker rdf:ID="_c30f2ea6-...">
  <cim:IdentifiedObject.name>CB GIL-150-BAY-BWI-C1</cim:IdentifiedObject.name>
  <cim:Switch.normalOpen>false</cim:Switch.normalOpen>
</cim:Breaker>
```

**`bali_DL.xml`** — tata letak, menunjuk balik ke mRID di EQ:

```xml
<md:Model.profile>http://entsoe.eu/CIM/DiagramLayout/3/1</md:Model.profile>

<cim:Diagram rdf:ID="_700668d3-...">
  <cim:IdentifiedObject.name>Sistem Bali 150 kV</cim:IdentifiedObject.name>
</cim:Diagram>

<cim:DiagramObject rdf:ID="_aa2ca1f1-...">
  <cim:DiagramObject.Diagram rdf:resource="#_700668d3-..."/>
  <cim:DiagramObject.IdentifiedObject rdf:resource="#_c30f2ea6-..."/>
</cim:DiagramObject>

<cim:DiagramObjectPoint rdf:ID="_76245b19-...">
  <cim:DiagramObjectPoint.DiagramObject rdf:resource="#_aa2ca1f1-..."/>
  <cim:DiagramObjectPoint.sequenceNumber>1</cim:DiagramObjectPoint.sequenceNumber>
  <cim:DiagramObjectPoint.xPosition>120.0</cim:DiagramObjectPoint.xPosition>
  <cim:DiagramObjectPoint.yPosition>260.3333333333</cim:DiagramObjectPoint.yPosition>
</cim:DiagramObjectPoint>
```

### Perbandingan langsung

| | PoC (`02d`) | Sekarang |
|---|---|---|
| File | 1 (EQ) | 2 (EQ + DL) |
| Profil dinyatakan | EquipmentCore + EquipmentOperation | EQ: sama · DL: DiagramLayout |
| Koordinat disimpan di | properti objek peralatan | `DiagramObjectPoint` |
| Namespace koordinat | `plnicp` (ekstensi PLN) | `cim` (standar) |
| Jumlah posisi per peralatan | tepat 1 | sebanyak diagram |
| Versi layout | ikut EQ | terpisah |
| Aman saat model di-refresh | tidak | ya |
| Terbaca aplikasi CIM lain | tidak | ya |
| Ekspor standar | harus buang layout | tidak perlu |

Verifikasi:

```powershell
python -m pln_nmm.cli build NMM_Model_Input_TEMPLATE.xlsx out\bali_EQ.xml --scenario BP-2026-05-15
python -c "import re; print('plnicp di EQ:', len(re.findall(r'plnicp', open('out/bali_EQ.xml',encoding='utf-8').read())))"
python -c "from pln_nmm.check import check_profiles; print(check_profiles('out/bali_EQ.xml','out/bali_DL.xml'))"
```

---

## 5. Dua rintangan teknis dan cara mengatasinya

Keduanya nyata dan sudah diverifikasi. Ini yang mungkin membuat tim sebelumnya
menyimpulkan DL tidak praktis.

### 5.1 Bug tipe pada pemilah profil cimpy

`cimpy/cimexport.py` fungsi `_sort_classes_to_profile` membandingkan **string**
pada baris 222 tetapi **enum `Profile`** pada baris 263. Akibatnya objek yang
baru dibuat program ditolak:

```
RuntimeError: Profile EQ not available for export, export_dict=dict_keys([])
```

Objek hasil `cim_import` lolos karena membawa `serializationProfile` dari
importer. Objek yang kita karang sendiri tidak.

**Penyelesaian kami:** menulis XML DL langsung, tanpa melalui `cim_export`.
Lebih sederhana daripada memalsukan keadaan objek hasil impor, dan tetap
mematuhi aturan **tidak memodifikasi cimpy** (invariant #1 CLAUDE.md).

Alternatif yang juga terbukti bekerja bila ingin lewat cimpy: isi
`serializationProfile` pada setiap objek yang dibuat.

### 5.2 cimpy menulis tautan DL→EQ sebagai teks

Ekspor bawaan cimpy menghasilkan:

```xml
<cim:DiagramObject.IdentifiedObject>brk1</cim:DiagramObject.IdentifiedObject>
```

Itu teks biasa, bukan referensi RDF — tidak akan resolve. Kami menulis:

```xml
<cim:DiagramObject.IdentifiedObject rdf:resource="#_brk1"/>
```

Ada test yang menjaga ini (`test_dl_links_to_equipment_by_resource_not_text`).

---

## 6. Yang dijaga otomatis

`check/profile.py` menolak pencemaran profil di kedua arah, dijalankan tiap
build:

| Aturan | Akibat bila dilanggar |
|---|---|
| EQ tidak memuat `plnicp:DiagramProperty` | error, kecuali mode kompatibilitas diminta |
| DL tidak memuat kelas EQ | error |
| Tiap `DiagramObject.IdentifiedObject` resolve ke mRID di EQ | error |
| Tautan ditulis `rdf:resource`, bukan teks | error |
| Koordinat bit-exact terhadap `repr()` | error |
| Peralatan tanpa posisi | peringatan, bukan error |

Test sengaja mencemari tiap file lalu memastikan pemeriksa menolaknya, sehingga
aturan ini tidak bisa diam-diam melemah.

---

## 7. Kompatibilitas dengan tools Icon Plus yang ada

Menghapus `plnicp` sepenuhnya akan membuat file kita tidak terbaca tata
letaknya oleh UI NMM Icon Plus. Karena itu `plnicp` tetap **bisa** dibangkitkan
sebagai bayangan kompatibilitas — tetapi dari sumber layout yang sama dengan
DL, sehingga keduanya tidak mungkin berbeda, dan hanya bila diminta eksplisit.

DL tetap sumber kebenaran. `plnicp` adalah salinan untuk pembaca lama.

---

## 8. Ringkasan untuk disampaikan

Tiga kalimat inti:

1. **Koordinat tidak boleh tinggal di file Equipment.** File PoC menyatakan
   dirinya profil Equipment tetapi memuat 52 properti koordinat; aplikasi CIM
   lain akan mengabaikannya diam-diam.
2. **Standarnya sudah menyediakan tempatnya, dan tools-nya sudah mendukung.**
   Profil DL ada di IEC 61970-453, diwajibkan EPRI R1.2, dan seluruh kelasnya
   sudah ada di cimpy yang dipakai sejak PoC.
3. **Akibatnya bukan soal kerapian.** Dengan struktur lama, satu peralatan hanya
   bisa punya satu posisi, layout hilang saat ekspor standar, dan kerja manual
   pengguna berisiko tertimpa tiap kali model diperbarui.

Yang perlu ditekankan: keputusan tim PoC wajar untuk membuktikan alur end-to-end
dalam waktu terbatas, dan namespace kustom memang cara yang sah untuk menampung
data non-CIM. Yang keliru hanyalah menempatkan data yang **sudah punya tempat di
standar** ke dalam ekstensi.
