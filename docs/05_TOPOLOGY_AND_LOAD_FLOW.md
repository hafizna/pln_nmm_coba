# 05 ? Connectivity, Scenarios, And Later Analysis

## Sekarang: konektivitas untuk SLD lengkap

Bangun dan validasi Equipment?Terminal?ConnectivityNode, winding trafo, dan
mapping bay/bus. Ini bagian milestone SLD. Bus-branch reduction untuk solver
bukan milestone pertama. Switching provisional tetap objek berkoneksi dengan
asumsi eksplisit; jangan dianggap koneksi lapangan terverifikasi.

## Skenario

Pisahkan normal position, scenario open/closed/unknown, availability, dan
snapshot. Buka kopel tidak otomatis melepas beban: hasilnya bergantung koneksi
bay dan sumber. Defense scheme perlu trigger, delay, target breaker, serta
beban/pembangkit yang terdampak sebelum dapat dieksekusi.

Snapshot 15 Mei 2026 pukul 19.00 WITA adalah satu operating point, bukan profil
harian. Nilai dampak kontingensi dalam tabel kerawanan bukan otomatis loading
busbar. Nilai dummy harus berlabel illustrative; jangan disebut hasil solver.

## Setelah milestone

- Load flow: line R/X/B, transformer impedance/loss/tap, P/Q loads,
  generator dispatch/voltage control, reference source, operating topology.
- Short circuit: source fault level, sequence impedances sesuai jenis gangguan,
  grounding dan parameter mesin/trafo.
- Equipment duty: evaluasi hasil gangguan terhadap kemampuan PMT dan rating
  short-time peralatan. Breaking capacity bukan input load flow.
- Protection/defense scheme: CT/PT, relay settings, logic, delay, target mapping.

Pemilihan solver dan tambahan dependency menunggu kebutuhan studi; lisensi wajib
permisif. Solver mengonsumsi model tervalidasi dan tidak masuk kernel preservasi.
