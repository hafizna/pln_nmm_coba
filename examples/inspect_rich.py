"""Probe /api/inspect with the rich CIM file and print SLD/topology breakdown."""
import sys, json
sys.path.insert(0, 'src')
from fastapi.testclient import TestClient
from pln_nmm_web.api import app

client = TestClient(app)
with open('examples/02d_CIM_EQ_1-SS_Filled-WithCoordinate_250604.xml', 'rb') as f:
    files = {'file': ('02d_CIM_EQ_1-SS_Filled-WithCoordinate_250604.xml', f, 'application/xml')}
    r = client.post('/api/inspect', files=files)
data = r.json()

print('=== SLD nodes by type ===')
by_type = {}
for n in data['sld']['nodes']:
    t = n.get('cim_class') or n.get('type') or n.get('kind') or 'unknown'
    by_type[t] = by_type.get(t, 0) + 1
print(json.dumps(by_type, indent=2))

print('\n=== Sample nodes (first 3) ===')
for n in data['sld']['nodes'][:3]:
    print(json.dumps(n, indent=2, default=str)[:500])
    print('---')

print('\n=== Sample edges (first 3) ===')
for e in data['sld']['edges'][:3]:
    print(json.dumps(e, indent=2, default=str)[:300])
    print('---')

print('\n=== Topology ===')
sub = data['topology']['substations'][0]
print('sub keys:', list(sub.keys()))
print('sub name:', sub.get('name'))
vls = sub.get('voltage_levels', [])
print('voltage_levels:', len(vls))
for vl in vls:
    bays = vl.get('bays', [])
    print(f"  VL {vl.get('name')} ({vl.get('nominal_voltage', vl.get('nominalVoltage', '?'))} kV): bays={len(bays)}")
    for bay in bays:
        items = bay.get('items', [])
        types = [i.get('type') or i.get('kind') or i.get('class') for i in items]
        print(f"    Bay {bay.get('name')}: items={len(items)} | types={types}")

print('\n=== Coordinate coverage ===')
nodes_with_xy = sum(1 for n in data['sld']['nodes'] if n.get('x') is not None and n.get('y') is not None)
print(f"nodes_with_xy: {nodes_with_xy} / {len(data['sld']['nodes'])}")
print('\n=== Orphans ===')
print('orphan_equipment_ids:', data['topology'].get('orphan_equipment_ids', [])[:10])
