import pytest

from pln_nmm.sources.maximo import reconcile_inventory
from pln_nmm.sources.workbook import Workbook
from pln_nmm.builder import build_cim


def rec(sheet, row, **raw):
    return {'sheet':sheet,'row':row,'raw':raw}


def example():
    gis = [rec('Locations',3,SITEID='A',LOCATION='G1',DESCRIPTION='GI TEST'),
           rec('Locations',4,SITEID='A',LOCATION='G2',DESCRIPTION='GI TEST')]
    bays = [rec('Locations_Bay',3,SITEID='A',LOCATION='B1',PARENT='G1',DESCRIPTION='BAY LAWAN 1')]
    assets = [rec('Assets',3,SITEID='A',ASSETNUM='001',LOCATION='B1',ASSETTYPE='Circuit Breaker',
                  GROUPTYPE='Peralatan Gardu Induk',STATUS='ACTIVE',SERIALNUM='0009')]
    return gis,bays,assets


def test_preserve_raw_and_do_not_turn_active_into_closed():
    result = reconcile_inventory(*example(), {'A'})
    asset = result['assets'][0]
    assert asset['raw']['SERIALNUM']=='0009'
    assert asset['normal_open'] is None and asset['scenario_open'] is None
    assert result['locations'][0]['candidate_type'] is None
    assert len(result['gis'])==1
    assert any(f['kind']=='UNREFERENCED_GI_LOCATION' for f in result['findings'])
    assert any(f['kind']=='SAME_NAME_DIFFERENT_ID' for f in result['findings'])


def test_same_location_different_site_is_not_joined():
    gis,bays,assets=example()
    assets[0]['raw']['SITEID']='B'
    result=reconcile_inventory(gis,bays,assets,{'A','B'})
    assert not result['assets']
    assert result['findings'][0]['kind']=='UNRESOLVED_GI_ASSET'


def test_stable_ids_under_reordering_and_source_row_change():
    gis,bays,assets=example()
    first=reconcile_inventory(gis,bays,assets,{'A'})
    assets[0]['row']=30
    second=reconcile_inventory(list(reversed(gis)),bays,assets,{'A'})
    assert first['assets'][0]['id']==second['assets'][0]['id']


def test_duplicate_key_fails_instead_of_last_row_wins():
    gis,bays,assets=example()
    with pytest.raises(ValueError,match='Duplicate source key'):
        reconcile_inventory(gis,bays,assets+assets,{'A'})


def test_inventory_workbook_cannot_silently_build_double_bus(tmp_path):
    wb=Workbook({'00_IMPORT_STATUS':[{'stage':'INVENTORY_ONLY'}]})
    output=tmp_path/'EQ.xml'
    with pytest.raises(ValueError,match='Inventory-only'):
        build_cim(wb,output)
    assert not output.exists()
