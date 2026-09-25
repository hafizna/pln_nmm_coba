"""Experimental RDF/XML review exchange with CIM16 switches and PLN objects.

This deliberately uses a dedicated reader. It is NOT a CGMES EQ profile export
and must not be round-tripped through cimpy, which drops unsupported objects.
Connectivity is reconstructed from terminal/reference XML, not a JSON graph blob.
"""
from copy import deepcopy
import json
from lxml import etree as E

from .identity import stable_id
from .line_bay import validate_line_model

CIM = 'http://iec.ch/TC57/2013/CIM-schema-cim16#'
NMM = 'http://pln.co.id/nmm/poc#'
RDF = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
NS = {'cim': CIM, 'plnnmm': NMM, 'rdf': RDF}
ID = '{'+RDF+'}ID'
REF = '{'+RDF+'}resource'
FORMAT = 'pln-nmm.line-review-xml.v1'


def tag(ns, name):
    return '{'+ns+'}'+name


def dumps_line_xml(model):
    validate_line_model(model)
    root = E.Element(tag(RDF, 'RDF'), nsmap=NS)
    def obj(ns, kind, oid):
        return E.SubElement(root, tag(ns, kind), {ID: '_'+oid})
    def value(el, ns, name, text):
        E.SubElement(el, tag(ns, name)).text = str(text)
    def ref(el, ns, name, oid):
        E.SubElement(el, tag(ns, name), {REF: '#_'+oid})
    def metadata(el, data):
        value(el, NMM, 'details', json.dumps(data, ensure_ascii=False))
    doc = obj(NMM, 'ReviewModel', stable_id(FORMAT))
    value(doc, NMM, 'format', FORMAT)
    metadata(doc, {k: v for k, v in model.items() if k != 'bays'})
    seen = {}
    for bay in model['bays']:
        if bay['gi_id'] not in seen:
            ss = obj(CIM, 'Substation', bay['gi_id'])
            value(ss, CIM, 'IdentifiedObject.name', next(
                g.get('raw', {}).get('DESCRIPTION', g['id'])
                for g in model['inventory']['gis'] if g['id'] == bay['gi_id']))
            seen[bay['gi_id']] = True
        el = obj(CIM, 'Bay', bay['id'])
        value(el, CIM, 'IdentifiedObject.name', bay['name'])
        ref(el, NMM, 'substation', bay['gi_id'])
        metadata(el, {k: v for k, v in bay.items()
                      if k not in {'id', 'name', 'gi_id', 'nodes', 'equipment'}})
        for node in bay['nodes']:
            ref(el, NMM, 'node', node['id'])
            if node['id'] in seen:
                if seen[node['id']] != node:
                    raise ValueError('Conflicting shared node')
                continue
            seen[node['id']] = node
            n = obj(NMM if node['role'] == 'EARTH' else CIM,
                    'EarthReference' if node['role'] == 'EARTH' else 'ConnectivityNode', node['id'])
            metadata(n, {k: v for k, v in node.items() if k not in {'id', 'x', 'y'}})
            value(n, NMM, 'diagramX', repr(node['x']))
            value(n, NMM, 'diagramY', repr(node['y']))
            if node['role'] in {'BUS_A', 'BUS_B'}:
                bus_id = stable_id('LINE_REVIEW_BUSBAR', node['id'])
                bus = obj(CIM, 'BusbarSection', bus_id)
                value(bus, CIM, 'IdentifiedObject.name', node['role'])
                ref(n, NMM, 'busbar', bus_id)
                t = obj(CIM, 'Terminal', stable_id('LINE_REVIEW_TERMINAL', bus_id, '1'))
                ref(t, CIM, 'Terminal.ConductingEquipment', bus_id)
                ref(t, CIM, 'Terminal.ConnectivityNode', node['id'])
                value(t, CIM, 'ACDCTerminal.sequenceNumber', 1)
        for device in bay['equipment']:
            role = device['role']
            standard = role in {'PMT', 'PMS_REL_1', 'PMS_REL_2', 'PMS_LINE'}
            d = obj(CIM if standard else NMM,
                    ('Breaker' if role == 'PMT' else 'Disconnector') if standard else 'PrimaryDevice',
                    device['id'])
            ref(el, NMM, 'equipment', device['id'])
            details = deepcopy(device)
            del details['id']
            endpoints = details['connection'].pop('value')
            metadata(d, details)
            if standard:
                ref(d, CIM, 'Equipment.EquipmentContainer', bay['id'])
                # Scenario values are never serialized as EQ normalOpen.
                if device['normal_open'] is not None:
                    value(d, CIM, 'Switch.normalOpen', str(device['normal_open']).lower())
                for i, endpoint in enumerate(endpoints, 1):
                    t = obj(CIM, 'Terminal', stable_id('LINE_REVIEW_TERMINAL', device['id'], str(i)))
                    ref(t, CIM, 'Terminal.ConductingEquipment', device['id'])
                    ref(t, CIM, 'Terminal.ConnectivityNode', endpoint)
                    value(t, CIM, 'ACDCTerminal.sequenceNumber', i)
            else:
                # Instrument/earthing attachments are explicit extension links,
                # never pretend that diagram earth is an electrical bus.
                for endpoint in endpoints:
                    ref(d, NMM, 'attachment', endpoint)
    return E.tostring(root, encoding='utf-8', xml_declaration=True, pretty_print=True)


def loads_line_xml(data):
    parser = E.XMLParser(resolve_entities=False, no_network=True)
    root = E.fromstring(data, parser)
    if root.getroottree().docinfo.doctype:
        raise ValueError('DTD is not supported')
    def text(el, ns, name):
        found = el.find(tag(ns, name))
        if found is None or found.text is None:
            raise ValueError(f'Missing {name}')
        return found.text
    def key(raw):
        return raw.removeprefix('#').removeprefix('_')
    def refs(el, ns, name):
        return [key(x.attrib[REF]) for x in el.findall(tag(ns, name))]
    def details(el):
        return json.loads(text(el, NMM, 'details'))
    objects = {}
    for el in root:
        oid = key(el.attrib[ID])
        if oid in objects:
            raise ValueError('Duplicate rdf:ID')
        objects[oid] = el
    docs = root.findall(tag(NMM, 'ReviewModel'))
    if len(docs) != 1 or text(docs[0], NMM, 'format') != FORMAT:
        raise ValueError('Expected NMM line-review XML v1, not arbitrary EQ XML')
    model = details(docs[0])
    model['bays'] = []
    terminals = {}
    for t in root.findall(tag(CIM, 'Terminal')):
        equipment = refs(t, CIM, 'Terminal.ConductingEquipment')[0]
        endpoint = refs(t, CIM, 'Terminal.ConnectivityNode')[0]
        order = int(text(t, CIM, 'ACDCTerminal.sequenceNumber'))
        terminals.setdefault(equipment, []).append((order, endpoint))
    for el in root.findall(tag(CIM, 'Bay')):
        bay = details(el)
        bay.update(id=key(el.attrib[ID]), name=text(el, CIM, 'IdentifiedObject.name'),
                   gi_id=refs(el, NMM, 'substation')[0], nodes=[], equipment=[])
        if bay['gi_id'] not in objects:
            raise ValueError('Missing substation')
        for nid in refs(el, NMM, 'node'):
            n = objects[nid]
            if details(n)['role'] in {'BUS_A', 'BUS_B'}:
                bus_id = refs(n, NMM, 'busbar')[0]
                if objects[bus_id].tag != tag(CIM, 'BusbarSection') or terminals.get(bus_id) != [(1, nid)]:
                    raise ValueError('Invalid busbar attachment')
            bay['nodes'].append({**details(n), 'id': nid,
                'x': float(text(n, NMM, 'diagramX')), 'y': float(text(n, NMM, 'diagramY'))})
        for did in refs(el, NMM, 'equipment'):
            d = objects[did]
            dev = details(d)
            dev['id'] = did
            if d.tag in {tag(CIM, 'Breaker'), tag(CIM, 'Disconnector')}:
                ends = sorted(terminals.get(did, []))
                if [i for i, _ in ends] != [1, 2]:
                    raise ValueError('Expected exactly two ordered switch terminals')
                dev['connection']['value'] = [n for _, n in ends]
                normal = d.find(tag(CIM, 'Switch.normalOpen'))
                if normal is not None and normal.text not in {'true', 'false'}:
                    raise ValueError('Invalid normalOpen')
                actual = None if normal is None else normal.text == 'true'
                if actual != dev['normal_open']:
                    raise ValueError('Conflicting normalOpen metadata')
            elif d.tag == tag(NMM, 'PrimaryDevice'):
                dev['connection']['value'] = refs(d, NMM, 'attachment')
            else:
                raise ValueError('Unsupported equipment class')
            bay['equipment'].append(dev)
        model['bays'].append(bay)
    if not model['bays']:
        raise ValueError('No line bays')
    validate_line_model(model)
    return model
