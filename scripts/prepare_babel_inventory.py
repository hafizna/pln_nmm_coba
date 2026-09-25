"""Extract source-backed Babel inventory and NMM workbook tables; never emit CIM."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from pln_nmm.sources.maximo import read_maximo
from build_workbook_template import SHEETS


def prepare(source):
    inventory = read_maximo(source)
    sheets = {}
    for fn in SHEETS:
        name, _, cols, _ = fn()
        sheets[name] = {'headers': [c[0] for c in cols], 'rows': []}

    def add(name, row):
        sheets[name]['rows'].append([row.get(h) for h in sheets[name]['headers']])

    for g in inventory['gis']:
        raw = g['raw']
        add('01_GI', {'gi_id': g['id'], 'gi_nama': raw['DESCRIPTION'],
            'busbar_confidence': 'UNKNOWN',
            'catatan': f"Maximo SITEID={raw['SITEID']}; LOCATION={raw['LOCATION']}; Locations row {g['row']}. Skema busbar menunggu SLD. ed_functloc belum dipetakan."})
    by_location = {l['id']: l for l in inventory['locations']}
    candidates = {}
    for loc in inventory['locations']:
        raw = loc['raw']; name = raw['DESCRIPTION']; upper = name.upper()
        if 'GEDUNG' in upper or not any(t in upper for t in ['BAY', 'TRAFO', 'KOPEL', 'BUS SECTION']):
            continue
        candidates[loc['id']] = loc
        add('02_BAY', {'bay_id': loc['id'], 'gi_id': loc['gi_id'], 'bay_nama': name,
            'bay_tipe': loc['candidate_type'], 'sumber': 'ED', 'confidence': 'INFERRED',
            'catatan': f"Kandidat dari Locations_Bay row {loc['row']}; SITEID={raw['SITEID']}; LOCATION={raw['LOCATION']}. Jenis, tegangan, template dan sambungan perlu review SLD; kode Maximo bukan SAP FUNCTLOC."})
    gi_names = {g['id']: g['raw']['DESCRIPTION'] for g in inventory['gis']}
    asset_headers = ['gi_nama','location_nama','ASSETTYPE','ASSETNUM','scope','asset_id','gi_id','location_id','bay_id_candidate','source_sheet','source_row']
    raw_headers = [h for h in inventory['assets'][0]['raw'] if h not in {'ASSETTYPE','ASSETNUM'}] if inventory['assets'] else []
    sheets['16_ASET_SUMBER'] = {'headers': asset_headers + raw_headers, 'rows': []}
    for a in inventory['assets']:
        sheets['16_ASET_SUMBER']['rows'].append([
            gi_names[a['gi_id']],by_location[a['location_id']]['raw']['DESCRIPTION'],
            a['raw']['ASSETTYPE'],a['raw']['ASSETNUM'],a['scope'],
            a['id'], a['gi_id'], a['location_id'],
            a['location_id'] if a['location_id'] in candidates else None,
            a['sheet'],a['row'],*[a['raw'].get(h) for h in raw_headers]])
    sheets['17_LOKASI_SUMBER'] = {'headers':['location_id','gi_id','SITEID','LOCATION','DESCRIPTION','PARENT','STATUS','source_sheet','source_row'], 'rows':[
        [l['id'],l['gi_id'],*[l['raw'].get(h) for h in ['SITEID','LOCATION','DESCRIPTION','PARENT','STATUS']],l['sheet'],l['row']]
        for l in inventory['locations']]}
    sheets['18_TEMUAN'] = {'headers':['kind','source_sheet','source_row','source_record'], 'rows':[
        [f['kind'],f['sheet'],f['row'],json.dumps(f['raw'],ensure_ascii=False,default=str)] for f in inventory['findings']]}
    sheets['00_IMPORT_STATUS'] = {'headers':['stage','source_file','sha256','catatan'], 'rows':[[
        'INVENTORY_ONLY',inventory['source']['path'],inventory['source']['sha256'],
        'Belum siap CIM. Sambungan, rating, grouping fasa, template bay, skenario dan layout menunggu rekonsiliasi. ACTIVE adalah status administrasi.']]}
    inventory['candidate_bays'] = len(candidates)
    return inventory, sheets


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source'); parser.add_argument('output_dir')
    args = parser.parse_args()
    inventory, sheets = prepare(args.source)
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    for name, value in [('inventory.json',inventory), ('workbook_tables.json',sheets)]:
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    print(json.dumps({**inventory['counts'],'candidate_bays':inventory['candidate_bays'],'findings':len(inventory['findings'])},indent=2))
