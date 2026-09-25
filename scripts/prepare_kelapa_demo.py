"""Export and independently reopen the single-bay Kelapa XML review fixture."""
import argparse
import json
from pathlib import Path

from pln_nmm.model.line_bay import PROFILE, propose_line_bays, reconstruct_line_bays
from pln_nmm.model.line_review import render_review
from pln_nmm.model.line_xml import dumps_line_xml, loads_line_xml


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('inventory', type=Path)
    p.add_argument('output', type=Path)
    args = p.parse_args()
    inv = json.loads(args.inventory.read_text(encoding='utf-8'))
    locations = {l['id']: l for l in inv['locations']}
    selected = [s for s in propose_line_bays(inv)
                if locations[s['location_id']]['raw']['DESCRIPTION'].strip() ==
                'GI 150KV KELAPA BAY MUNTOK #1']
    if len(selected) != 1:
        raise ValueError('Expected one unambiguous Kelapa-Muntok #1 source bay')
    # Keep only this bay's evidence in the shareable review, not all Babel assets.
    bid, gid = selected[0]['location_id'], selected[0]['gi_id']
    inv = {**inv, 'gis': [g for g in inv['gis'] if g['id'] == gid],
           'locations': [locations[bid]],
           'assets': [a for a in inv['assets'] if a['location_id'] == bid],
           'findings': [], 'counts': {'scope': 'SINGLE_BAY_EVIDENCE_SUBSET'}}
    model = reconstruct_line_bays(inv, selected, {gid: PROFILE}, demo_scenario=True)
    args.output.mkdir(parents=True, exist_ok=True)
    xml = args.output / 'Kelapa_Muntok_1_NMM.xml'
    if xml.exists():
        raise ValueError('Output exists; preserve reviewed work and choose a new directory')
    data = dumps_line_xml(model)
    reopened = loads_line_xml(data)
    if reopened != model:
        raise ValueError('Round-trip changed the model')
    xml.write_bytes(data)
    (args.output / 'reimported.html').write_text(render_review(reopened, from_xml=True), encoding='utf-8')
    print(f'Export/re-import equality passed: {xml.resolve()}')


if __name__ == '__main__':
    main()
