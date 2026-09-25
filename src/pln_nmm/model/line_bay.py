"""Review-stage primary connectivity; deliberately not a CIM export adapter.

An assumed functional position is distinct from a physical asset. Candidate
records are evidence, not confirmed phase groups or one-to-one assignments.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import re

from .identity import stable_id

PROFILE = 'ASSUMED_DOUBLE_BUS_LINE_V1'
ROLES = {
    'PMS_REL_1': 'Disconnecting Switch',
    'PMS_REL_2': 'Disconnecting Switch',
    'PMT': 'Circuit Breaker',
    'CT': 'Current Transformer',
    'PMS_LINE': 'Disconnecting Switch',
    'PMS_TANAH': 'Earthing Switch',
    'CVT': 'Potential Transformer',
    'LA': 'Lightning Arrester',
    'WAVE_TRAP': 'Wave Trap',
    'SEALING_END': 'Sealing End',
}


def fact(value, quality, basis):
    return {'value': value, 'quality': quality, 'basis': basis}


def propose_line_bays(inventory):
    """Conservative name candidates only; callers must choose an arrangement.

    A numbered destination is not proof of a remote electrical connection.
    Transformer/coupler/reactor/MT and unnumbered bays are excluded.
    """
    candidates = []
    for location in sorted(inventory['locations'], key=lambda x: x['id']):
        name = location['raw'].get('DESCRIPTION', '')
        match = re.search(r'\bBAY\s+(.+?)\s+#?\s*(\d+)\s*$', name, re.I)
        if not match or re.search(
            r'\b(TRAFO|MT|KOPEL|COUPLE|COUPLER|REAKTOR|REACTOR|BUS|KAPASITOR)\b',
            match[1], re.I,
        ) or 'GEDUNG' in name.upper():
            continue
        candidates.append({'location_id': location['id'], 'gi_id': location['gi_id'],
                           'remote_label': match[1], 'circuit_label': match[2]})
    return candidates


def reconstruct_line_bays(inventory, selections, gi_profiles, *, demo_scenario=False):
    """Expand only explicit selections and per-GI assumption profiles.

    Unknown ratings/normal states remain unknown. Generic PT records do not
    establish CVT technology; generic PMS records do not establish roles.
    """
    locations = {x['id']: x for x in inventory['locations']}
    gi_ids = {x['id'] for x in inventory['gis']}
    if len({s['location_id'] for s in selections}) != len(selections):
        raise ValueError('Duplicate bay selection')
    result = {'schema': 'pln-nmm.line-bay-review.v1', 'stage': 'ASSUMED_CONNECTIVITY_REVIEW',
              'source': deepcopy(inventory.get('source', {})),
              'inventory': deepcopy(inventory), 'bays': [], 'findings': [],
              'scenario': {'id': 'ILLUSTRATIVE_BUS_A', 'quality': 'ASSUMED', 'open': {}}
              if demo_scenario else None,
              'limitations': ['Not a standard CIM/CGMES package',
                              'Asset grouping and functional roles require review',
                              'Remote endpoints are boundaries, not loads or verified lines']}
    for selection in sorted(selections, key=lambda x: x['location_id']):
        loc = locations[selection['location_id']]
        gid, bid = loc['gi_id'], loc['id']
        if gid not in gi_ids or gi_profiles.get(gid) != PROFILE:
            raise ValueError(f'Explicit supported GI assumption profile required: {gid}')
        if selection.get('gi_id', gid) != gid:
            raise ValueError('Selection GI differs from source parent')
        optional = selection.get('optional', {})
        if set(optional) - {'WAVE_TRAP', 'SEALING_END'} or any(
            v not in (None, True, False) for v in optional.values()
        ):
            raise ValueError('Optional devices require bool or null')
        assets = sorted((a for a in inventory['assets'] if a['location_id'] == bid),
                        key=lambda a: a['id'])
        evidence = f"{loc['sheet']}:{loc['row']}"
        bay = {'id': bid, 'gi_id': gid, 'name': loc['raw']['DESCRIPTION'],
               'profile': fact(PROFILE, 'ASSUMED', 'User-authorized reconstruction pattern'),
               'bay_type': fact('LINE', 'ASSUMED', evidence),
               'remote_label': fact(selection.get('remote_label'), 'INFERRED', evidence),
               'circuit_label': fact(selection.get('circuit_label'), 'INFERRED', evidence),
               'nodes': [], 'equipment': [], 'optional': deepcopy(optional),
               'unmapped_asset_ids': [], 'boundary': None}
        def node(role, x, y, shared=False):
            nid = stable_id('LINE_REVIEW_CN', gid if shared else bid, role)
            bay['nodes'].append({'id': nid, 'role': role, 'x': x, 'y': y,
                                 'quality': 'ASSUMED'})
            return nid
        a = node('BUS_A', 70, 100, True)
        b = node('BUS_B', 70, 190, True)
        joint = node('SELECTOR_JOIN', 250, 145)
        post_cb = node('POST_CB', 400, 145)
        post_ct = node('POST_CT', 530, 145)
        line = node('LINE_SIDE', 680, 145)
        earth = node('EARTH', 680, 350)
        def equipment(role, nodes, mode):
            candidates = [x['id'] for x in assets if x['raw'].get('ASSETTYPE') == ROLES[role]]
            obj = {'id': stable_id('LINE_REVIEW_POSITION', bid, role), 'role': role,
                   'connection': fact(nodes, 'ASSUMED', PROFILE), 'mode': mode,
                   'candidate_asset_ids': candidates, 'confirmed_asset_ids': [],
                   'mapping_quality': 'UNRESOLVED', 'normal_open': None,
                   'ratings': {}, 'technology': fact('CVT', 'ASSUMED',
                       'Generic Potential Transformer does not establish CVT') if role == 'CVT' else None}
            bay['equipment'].append(obj)
            kind = 'ASSET_ROLE_OR_GROUPING_UNRESOLVED' if candidates else 'ASSUMED_WITHOUT_ASSET_MATCH'
            result['findings'].append({'kind': kind, 'bay_id': bid, 'object_id': obj['id'],
                                       'role': role, 'candidate_count': len(candidates)})
            if demo_scenario and role.startswith('PMS_') or demo_scenario and role == 'PMT':
                result['scenario']['open'][obj['id']] = role in {'PMS_REL_2', 'PMS_TANAH'}
            return obj
        equipment('PMS_REL_1', [a, joint], 'SERIES')
        equipment('PMS_REL_2', [b, joint], 'SERIES')
        equipment('PMT', [joint, post_cb], 'SERIES')
        equipment('CT', [post_cb, post_ct], 'SERIES')
        pms = equipment('PMS_LINE', [post_ct, line], 'SERIES')
        es = equipment('PMS_TANAH', [line, earth], 'GROUND_BRANCH')
        assembly = fact(stable_id('LINE_REVIEW_ASSEMBLY', bid, 'PMS_LINE_ES'),
                        'ASSUMED', 'PMS line and ES functions in one assumed assembly')
        pms['assembly'] = deepcopy(assembly)
        es['assembly'] = deepcopy(assembly)
        es['function_label'] = 'ES (fungsi pentanahan rakitan PMS line)'
        equipment('CVT', [line, earth], 'GROUND_BRANCH')
        equipment('LA', [line, earth], 'GROUND_BRANCH')
        tail = line
        x = 820
        for role in ('WAVE_TRAP', 'SEALING_END'):
            if optional.get(role) is True:
                end = node(role + '_OUT', x, 145)
                equipment(role, [tail, end], 'SERIES')
                tail, x = end, x + 140
            elif optional.get(role) is None:
                result['findings'].append({'kind': 'OPTIONAL_PRESENCE_UNKNOWN',
                                           'bay_id': bid, 'role': role})
        bay['boundary'] = {'node_id': tail, 'kind': 'REMOTE_NETWORK_UNRESOLVED',
                           'remote_gi_id': None, 'load_id': None}
        # Candidates have NOT been assigned to model positions. Keep every record.
        bay['unmapped_asset_ids'] = [x['id'] for x in assets]
        result['bays'].append(bay)
    validate_line_model(result)
    result['counts'] = {'bays': len(result['bays']),
        'gis': len({b['gi_id'] for b in result['bays']}),
        'functional_positions': sum(len(b['equipment']) for b in result['bays']),
        'findings': dict(Counter(f['kind'] for f in result['findings']))}
    return result


def validate_line_model(model):
    """Reject dangling attachments, duplicate positions and invalid branches."""
    ids = set()
    asset_ids = {a['id'] for a in model['inventory']['assets']}
    for bay in model['bays']:
        nodes = {n['id'] for n in bay['nodes']}
        if len(nodes) != len(bay['nodes']):
            raise ValueError('Duplicate node')
        earth = next(n['id'] for n in bay['nodes'] if n['role'] == 'EARTH')
        for obj in bay['equipment']:
            if obj['id'] in ids:
                raise ValueError('Duplicate equipment identity')
            ids.add(obj['id'])
            ends = obj['connection']['value']
            if len(ends) != 2 or ends[0] == ends[1] or not set(ends) <= nodes:
                raise ValueError('Invalid connection reference')
            if obj['role'] in {'CVT', 'LA', 'PMS_TANAH'} and (
                obj['mode'] != 'GROUND_BRANCH' or ends[1] != earth
            ):
                raise ValueError('Ground device must be a branch')
            if not set(obj['candidate_asset_ids']) <= asset_ids:
                raise ValueError('Unknown source asset')
        if bay['boundary']['node_id'] not in nodes or bay['boundary']['load_id'] is not None:
            raise ValueError('Invalid remote boundary')
    scenario = model.get('scenario')
    if scenario and not set(scenario['open']) <= ids:
        raise ValueError('Dangling scenario state')
    if scenario:
        for bay in model['bays']:
            switches = {o['role']: o['id'] for o in bay['equipment']
                        if o['role'].startswith('PMS_') or o['role'] == 'PMT'}
            for obj in bay['equipment']:
                if obj['id'] in scenario['open'] and (
                    obj['id'] not in switches.values() or
                    type(scenario['open'][obj['id']]) not in (bool, type(None))
                ):
                    raise ValueError('Invalid scenario switch state')
            if all(scenario['open'].get(switches.get(role)) is False
                   for role in ('PMS_LINE', 'PMS_TANAH')):
                raise ValueError('Assumed interlock: PMS line and ES cannot both be closed')
