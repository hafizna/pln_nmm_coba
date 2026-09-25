from copy import deepcopy
import json

from fastapi.testclient import TestClient
from lxml import etree as E
import pytest

from pln_nmm.model.line_bay import reconstruct_line_bays, PROFILE
from pln_nmm.model.line_xml import dumps_line_xml, loads_line_xml, CIM, NMM, NS, REF, tag
from pln_nmm_web.api import app


def model():
    inv = {'gis': [{'id': 'g'}], 'locations': [{'id': 'b', 'gi_id': 'g',
           'sheet': 'Locations', 'row': 3, 'raw': {'DESCRIPTION': 'TEST BAY'}}],
           'assets': [{'id': 'ct1', 'location_id': 'b', 'raw': {'ASSETTYPE': 'Current Transformer'}}]}
    return reconstruct_line_bays(inv, [{'location_id': 'b'}], {'g': PROFILE}, demo_scenario=True)


def test_xml_roundtrip_objects_attachments_source_assembly_and_exact_coordinates():
    m = model()
    m['bays'][0]['nodes'][0]['x'] = 1.2345678901234567
    data = dumps_line_xml(m)
    reopened = loads_line_xml(data)
    assert reopened == m
    assert reopened['bays'][0]['nodes'][0]['x'].hex() == m['bays'][0]['nodes'][0]['x'].hex()
    assert b'Switch.normalOpen' not in data
    assert b'PrimaryDevice' in data
    assert len(E.fromstring(data).findall(tag(CIM, 'BusbarSection'))) == 2
    eq = {o['role']: o for o in reopened['bays'][0]['equipment']}
    assert eq['PMS_LINE']['assembly'] == eq['PMS_TANAH']['assembly']
    assert loads_line_xml(dumps_line_xml(reopened)) == m


def test_import_reads_terminal_changes_from_xml_not_cached_graph():
    m = model()
    root = E.fromstring(dumps_line_xml(m))
    terminal = next(t for t in root.findall(tag(CIM, 'Terminal'))
                    if t.find(tag(CIM, 'Terminal.ConductingEquipment')).attrib[REF]
                    == '#_'+m['bays'][0]['equipment'][0]['id'])
    old = terminal.find(tag(CIM, 'Terminal.ConnectivityNode'))
    new = next(n['id'] for n in m['bays'][0]['nodes'] if n['role'] == 'BUS_B')
    old.attrib[REF] = '#_'+new
    reopened = loads_line_xml(E.tostring(root))
    assert reopened['bays'][0]['equipment'][0]['connection']['value'][0] == new


def test_missing_ct_and_dangling_terminal_are_rejected_not_dropped():
    root = E.fromstring(dumps_line_xml(model()))
    primary = root.find(tag(NMM, 'PrimaryDevice'))
    root.remove(primary)
    with pytest.raises(KeyError):
        loads_line_xml(E.tostring(root))
    root = E.fromstring(dumps_line_xml(model()))
    root.find('.//'+tag(CIM, 'Terminal.ConnectivityNode')).attrib[REF] = '#_missing'
    with pytest.raises(ValueError, match='attachment|reference'):
        loads_line_xml(E.tostring(root))


def test_web_import_edit_export_reimport_and_assumed_interlock():
    client = TestClient(app)
    data = dumps_line_xml(model())
    files = {'file': ('fixture.xml', data, 'application/xml')}
    result = client.post('/api/line-review/import', files=files)
    assert result.status_code == 200
    assert 'Diagram dibentuk setelah impor XML' in result.json()['html']
    eq = {o['role']: o['id'] for o in model()['bays'][0]['equipment']}
    states = {eq['PMS_LINE']: True, eq['PMS_TANAH']: False}
    changed = client.post('/api/line-review/scenario', files=files, data={'states': json.dumps(states)})
    assert changed.status_code == 200
    reopened = loads_line_xml(changed.content)
    assert reopened['scenario']['open'][eq['PMS_TANAH']] is False
    assert all(o['normal_open'] is None for o in reopened['bays'][0]['equipment'])
    assert client.post('/api/line-review/import', files={'file': ('edited.xml', changed.content)}).status_code == 200
    bad = client.post('/api/line-review/scenario', files=files,
                      data={'states': json.dumps({eq['PMS_TANAH']: False})})
    assert bad.status_code == 422
    bad = client.post('/api/line-review/scenario', files=files,
                      data={'states': json.dumps({eq['CT']: True})})
    assert bad.status_code == 422


def test_bad_xml_returns_error_and_dtd_is_rejected():
    client = TestClient(app)
    assert client.post('/api/line-review/import', files={'file': ('bad.xml', b'<broken>')}).status_code == 422
    data = b'<!DOCTYPE test [<!ENTITY x "bad">]><test/>'
    with pytest.raises(ValueError, match='DTD'):
        loads_line_xml(data)


def test_generic_cimpy_route_refuses_to_silently_drop_primary_objects(tmp_path):
    from pln_nmm.importer import import_pln_eq
    data = dumps_line_xml(model())
    path = tmp_path / 'review.xml'
    path.write_bytes(data)
    with pytest.raises(ValueError, match='discard'):
        import_pln_eq(path)
    client = TestClient(app)
    response = client.post('/api/inspect', files={'file': ('review.xml', data)})
    assert response.status_code == 422
    assert '/line-review' in response.json()['detail']


def test_repo_symbols_and_cvt_display_do_not_change_model_connectivity():
    from pln_nmm.model.line_review import render_review
    m = model()
    before = deepcopy(m)
    tree = E.HTML(render_review(m, from_xml=True))
    cvt = tree.xpath('//*[@data-device-role="CVT"]')[0]
    assert cvt.xpath('.//*[@data-symbol="CVT"]')
    assert not cvt.xpath('.//*[@data-earth-lead or @data-earth-symbol]')
    es = tree.xpath('//*[@data-device-role="PMS_TANAH"]')[0]
    assert es.xpath('.//*[@data-symbol="PMS"]')
    assert es.xpath('.//*[@data-earth-symbol]')
    pmt = tree.xpath('//*[@data-symbol="PMT"]')[0]
    assert 'L13.75 34.969' in pmt.xpath('.//path')[0].attrib['d']
    assert tree.xpath('//*[@data-symbol="CT"]')
    assert len(tree.xpath('//*[@data-symbol="Busbar"]')) == 2
    assert m == before


def test_vertical_view_follows_connections_not_equipment_list_order():
    from pln_nmm.model.vertical_review import spine, render_vertical_bay
    m = model()
    bay = m['bays'][0]
    eq = {o['role']: o for o in bay['equipment']}
    # Swap the physical positions of CT and PMS line without changing IDs.
    eq['CT']['connection']['value'], eq['PMS_LINE']['connection']['value'] = (
        eq['PMS_LINE']['connection']['value'], eq['CT']['connection']['value'])
    bay['equipment'].reverse()
    assert [o['role'] for _, _, o in spine(bay)[1]] == ['PMT', 'PMS_LINE', 'CT']
    eq['CVT']['connection']['value'][0] = eq['PMT']['connection']['value'][1]
    tree = E.HTML(render_vertical_bay(bay, m['scenario']))
    assert tree.xpath('//*[@data-device-role="CVT"]')[0].attrib['data-attachment-node'] == eq['PMT']['connection']['value'][1]


def test_vertical_view_rejects_disconnected_series_device():
    from pln_nmm.model.vertical_review import spine
    bay = model()['bays'][0]
    extra = deepcopy(next(o for o in bay['equipment'] if o['role'] == 'CT'))
    extra['id'] = 'orphan'
    extra['connection']['value'] = ['unconnected-a', 'unconnected-b']
    bay['equipment'].append(extra)
    with pytest.raises(ValueError, match='omit'):
        spine(bay)
