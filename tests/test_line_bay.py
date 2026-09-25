import json
from copy import deepcopy

import pytest

from pln_nmm.model.line_bay import (
    PROFILE, propose_line_bays, reconstruct_line_bays, validate_line_model,
)
from pln_nmm.model.line_review import render_review


def inventory():
    return {'gis': [{'id': 'g'}], 'locations': [
        {'id': 'b', 'gi_id': 'g', 'sheet': 'Locations', 'row': 3,
         'raw': {'DESCRIPTION': 'GI 150KV A BAY B #1'}},
        {'id': 't', 'gi_id': 'g', 'sheet': 'Locations', 'row': 4,
         'raw': {'DESCRIPTION': 'GI 150KV A BAY MT #1 150/6,3KV'}},
        {'id': 'c', 'gi_id': 'g', 'sheet': 'Locations', 'row': 5,
         'raw': {'DESCRIPTION': 'GI 150KV A BAY COUPLE'}}],
        'assets': [{'id': str(i), 'location_id': 'b', 'sheet': 'Assets', 'row': i+3,
                    'raw': {'ASSETTYPE': kind, 'DESCRIPTION': f'{kind} phase unknown'}}
                   for i, kind in enumerate(['Current Transformer'] * 3 +
                                            ['Disconnecting Switch'] * 3 +
                                            ['Potential Transformer'] * 6)]}


def build(**kwargs):
    inv = inventory()
    return reconstruct_line_bays(inv, propose_line_bays(inv), {'g': PROFILE}, **kwargs)


def test_explicit_gi_profile_required_and_source_unchanged():
    inv = inventory()
    before = deepcopy(inv)
    with pytest.raises(ValueError, match='Explicit'):
        reconstruct_line_bays(inv, propose_line_bays(inv), {})
    build()
    assert inv == before
    assert [x['location_id'] for x in propose_line_bays(inv)] == ['b']


def test_selector_merge_and_ground_branches_do_not_become_series_loads():
    bay = build()['bays'][0]
    eq = {e['role']: e for e in bay['equipment']}
    ends = lambda role: eq[role]['connection']['value']
    assert ends('PMS_REL_1')[1] == ends('PMS_REL_2')[1] == ends('PMT')[0]
    assert ends('PMT')[1] == ends('CT')[0]
    assert ends('CT')[1] == ends('PMS_LINE')[0]
    for role in ('CVT', 'LA', 'PMS_TANAH'):
        assert eq[role]['mode'] == 'GROUND_BRANCH'
        assert ends(role)[0] == ends('PMS_LINE')[1]
    assert bay['boundary']['node_id'] == ends('PMS_LINE')[1]
    assert bay['boundary']['load_id'] is None


def test_ambiguous_phase_records_are_preserved_not_silently_assigned():
    model = build()
    bay = model['bays'][0]
    eq = {e['role']: e for e in bay['equipment']}
    assert len(eq['CT']['candidate_asset_ids']) == 3
    assert len(eq['CVT']['candidate_asset_ids']) == 6
    assert eq['CVT']['technology']['quality'] == 'ASSUMED'
    assert eq['PMS_REL_1']['candidate_asset_ids'] == eq['PMS_LINE']['candidate_asset_ids']
    assert len(bay['unmapped_asset_ids']) == 12
    assert all(e['confirmed_asset_ids'] == [] for e in eq.values())
    assert all(e['normal_open'] is None and e['ratings'] == {} for e in eq.values())
    assert model['scenario'] is None


def test_scenario_survives_reopen_without_becoming_normal_position():
    model = build(demo_scenario=True)
    reopened = json.loads(json.dumps(model))
    validate_line_model(reopened)
    eq = {e['role']: e for e in reopened['bays'][0]['equipment']}
    assert reopened['scenario']['open'][eq['PMS_REL_2']['id']] is True
    assert reopened['scenario']['open'][eq['PMS_REL_1']['id']] is False
    assert all(e['normal_open'] is None for e in eq.values())
    assert 'CVT' in render_review(reopened)
    assert reopened == model


def test_optional_equipment_and_stable_ids_under_source_reorder():
    inv = inventory()
    selections = propose_line_bays(inv)
    selections[0]['optional'] = {'WAVE_TRAP': True, 'SEALING_END': True}
    first = reconstruct_line_bays(inv, selections, {'g': PROFILE})
    inv['assets'].reverse()
    second = reconstruct_line_bays(inv, selections, {'g': PROFILE})
    assert first['bays'] == second['bays']
    eq = {e['role']: e for e in first['bays'][0]['equipment']}
    assert eq['WAVE_TRAP']['connection']['value'][1] == eq['SEALING_END']['connection']['value'][0]
    assert first['bays'][0]['boundary']['node_id'] == eq['SEALING_END']['connection']['value'][1]


def test_dangling_attachment_and_ground_series_fail_validation():
    model = build()
    model['bays'][0]['equipment'][0]['connection']['value'][0] = 'missing'
    with pytest.raises(ValueError, match='reference'):
        validate_line_model(model)
    model = build()
    next(e for e in model['bays'][0]['equipment'] if e['role'] == 'CVT')['mode'] = 'SERIES'
    with pytest.raises(ValueError, match='branch'):
        validate_line_model(model)
