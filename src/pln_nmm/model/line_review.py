"""Portable HTML inspection of the saved reconstruction model (no JS/network)."""
from html import escape
import json

from .line_bay import validate_line_model
from .vertical_review import render_vertical_bay


def render_review(model, *, from_xml=False):
    validate_line_model(model)
    out = ['<!doctype html><html lang="id"><meta charset="utf-8">',
           '<title>NMM — Review bay penghantar Babel</title>',
           '<style>body{font:15px system-ui;margin:32px;background:#f6f7f9;color:#182331}'
           'section{background:white;padding:20px;margin:24px 0;border:1px solid #ccd3dc}'
           'svg{width:100%;max-width:880px;min-width:620px}.diagram{overflow:auto}text{font:13px system-ui}'
           'pre{white-space:pre-wrap;overflow-wrap:anywhere}summary{cursor:pointer}'
           'td,th{padding:8px;border:1px solid #ccd3dc;text-align:left}'
           'table{border-collapse:collapse}a{color:#2459a5}</style>',
           '<h1>Rekonstruksi bay penghantar Babel</h1>',
           '<details><summary>Asumsi, sumber dan batas cakupan</summary>',
           '<p><strong>ASUMSI — bukan SLD terverifikasi atau paket CGMES standar.</strong> '
           'Susunan double bus diterapkan pada GI yang dipilih di manifest. '
           'Semua garis/peran alat merupakan asumsi. Rating dan posisi normal belum diketahui.</p>',
           '<p>CVT diasumsikan; register Potential Transformer belum memastikan jenis CVT. '
           'Angka kandidat adalah record aset, bukan jumlah alat SLD atau fase yang terkonfirmasi. '
           'Satu kandidat PMS dapat muncul pada beberapa peran; belum ada penetapan aset.</p>',
           '<p>Wave trap/sealing end dengan keberadaan unknown tidak digambar sebagai alat terpasang. '
           'Ujung bay adalah batas jaringan, bukan load. Diagram ini memperlihatkan konektivitas, '
           'bukan status bertegangan. Earth adalah referensi gambar, bukan bus studi.</p>',
           '<pre>' + escape(json.dumps(model['counts'], indent=2)) + '</pre>']
    scenario = model.get('scenario')
    if from_xml:
        out.append('<p><strong>Diagram dibentuk setelah impor XML NMM.</strong> '
                   'XML eksperimen ini memakai objek CIM16 dan ekstensi primer NMM; '
                   'belum paket CGMES untuk aplikasi studi.</p>')
    out.append('<p>PMS line dan ES dimodelkan sebagai dua fungsi dalam satu rakitan asumsi. '
               'Cabang CVT adalah pengukuran, bukan kontak pentanahan. '
               'Referensi tanah internal CVT tidak digambar pada SLD ini. '
               'Simbol PMT/PMS/busbar memakai SVG repo. CT/CVT/LA: QElectroTech, CC-BY 3.0, melalui SynergyCodes; orientasi dan posisi disesuaikan. '
               'Closed/Open di bawah adalah posisi kontak, bukan indikasi bertegangan.</p>')
    out.append('<p>Skenario: ' + ('ILLUSTRATIVE_BUS_A (asumsi demo, terpisah dari posisi normal).'
                                  if scenario else 'Tidak dibuat; seluruh status operasi unknown.') + '</p>')
    out.append('<p>Artwork: <a href="https://github.com/synergycodes/ng-diagram-single-line-diagram/blob/449df49147f8095143351139ab9d3bdac0e4cc96/NOTICE.md">QElectroTech / SynergyCodes</a> ? <a href="https://creativecommons.org/licenses/by/3.0/">CC-BY 3.0</a>.</p></details>')
    for bay in model['bays']:
        out.append('<section><h2>' + escape(bay['name']) + '</h2><div class="diagram">')
        out.append(render_vertical_bay(bay, scenario))
        out.append('</div>')
        out.append('<table><tr><th>Posisi fungsional</th><th>Kandidat record aset</th>'
                   '<th>Posisi normal</th><th>Status skenario</th></tr>')
        for obj in bay['equipment']:
            state = scenario['open'].get(obj['id']) if scenario else None
            is_switch = obj['role'].startswith('PMS_') or obj['role'] == 'PMT'
            label = ('Unknown' if state is None else ('Open (asumsi)' if state else 'Closed (asumsi)')) if is_switch else 'Tidak berlaku'
            out.append(f'<tr><td>{escape(obj["role"])}</td><td>{len(obj["candidate_asset_ids"])}, belum dipetakan</td>'
                       f'<td>Unknown</td><td>{label}</td></tr>')
        out.append('</table><details><summary>ID, sambungan, provenance dan kandidat aset</summary><pre>'
                   + escape(json.dumps(bay, indent=2, ensure_ascii=False)) + '</pre></details></section>')
    out.append('</html>')
    return '\n'.join(out)
