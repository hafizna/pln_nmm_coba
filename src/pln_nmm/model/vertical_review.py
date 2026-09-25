"""Compact vertical bay projection derived from connectivity, never asset order.

This is a generated display view. It does not rewrite stored XML X/Y values.
Only a two-selector, unbranched series spine is supported; other arrangements
must receive their own layout instead of being silently drawn as this pattern.
"""
from collections import defaultdict
from html import escape
from functools import lru_cache
from lxml import etree as E

from .review_symbols import SYMBOLS, switch_svg, glyph


@lru_cache
def artwork(name):
    filename = {'CT': 'ct.svg', 'CVT': 'cvt.svg', 'LA': 'surge-arrester.svg'}[name]
    root = E.parse(str(SYMBOLS / 'qet' / filename)).getroot()
    return ''.join(E.tostring(c, encoding='unicode') for c in root)


def source_symbol(name, x, y):
    transform = {'CT': 'translate(-12 -30)', 'CVT': 'translate(-12 -14)',
                 'LA': 'rotate(-90) translate(-10 -30)'}[name]
    return (f'<g fill="none" color="#bd242d" data-symbol="{name}" '
            f'data-artwork="QElectroTech-CC-BY-3.0" '
            f'transform="translate({x} {y}) {transform}">{artwork(name)}</g>')


def spine(bay):
    by_role = {o['role']: o for o in bay['equipment']}
    selectors = [by_role[r] for r in ('PMS_REL_1', 'PMS_REL_2')]
    common = set(selectors[0]['connection']['value']) & set(selectors[1]['connection']['value'])
    if len(common) != 1:
        raise ValueError('Vertical view requires two selectors with one common junction')
    start = next(iter(common))
    graph = defaultdict(list)
    series = [o for o in bay['equipment'] if o['mode'] == 'SERIES' and o not in selectors]
    for obj in series:
        a, b = obj['connection']['value']
        graph[a].append((b, obj)); graph[b].append((a, obj))
    node, used, path = start, set(), []
    while node != bay['boundary']['node_id']:
        options = [(n, o) for n, o in graph[node] if o['id'] not in used]
        if len(options) != 1:
            raise ValueError('Vertical view requires an unambiguous series path to the boundary')
        following, obj = options[0]
        path.append((node, following, obj)); used.add(obj['id']); node = following
    if len(used) != len(series) or not path:
        raise ValueError('Vertical view cannot omit disconnected or shared series equipment')
    return start, path, selectors


def render_vertical_bay(bay, scenario):
    start, path, selectors = spine(bay)
    x, top, bottom = 290, 250, 530
    positions = {start: (x, bottom)}
    for i, (_, following, _) in enumerate(path, 1):
        positions[following] = (x, bottom - (bottom-top)*i/len(path))
    states = scenario['open'] if scenario else {}
    out = ['<svg class="vertical-sld" viewBox="0 0 720 750" role="img" '
           'aria-label="SLD bay vertikal dari konektivitas XML">',
           '<style>.vertical-sld .wire{fill:none;stroke:#bd242d;stroke-width:1.8}'
           '.vertical-sld text{fill:#192b40;font:13px system-ui}</style>']
    def wire(d, extra=''):
        out.append(f'<path class="wire" d="{d}" {extra}/>')
    def label(px, py, text, anchor='start'):
        out.append(f'<text x="{px}" y="{py}" text-anchor="{anchor}">{escape(text)}</text>')
    def earth(px, py):
        wire(f'M{px} {py-10} V{py+10} M{px+4} {py-7} V{py+7} M{px+8} {py-4} V{py+4}',
             'data-earth-symbol="true"')
    def state_label(obj):
        state = states.get(obj['id'])
        return 'UNKNOWN' if state is None else ('OPEN' if state else 'CLOSED')
    label(x, 28, 'ARAH ' + str(bay['remote_label']['value'] or 'BATAS MODEL'), 'middle')
    label(x, 49, 'Sirkit ' + str(bay['circuit_label']['value'] or '?') + ' · asumsi', 'middle')
    label(440, 76, 'Warna = gaya gambar; bukan energized')
    wire(f'M{x} 75 V{top}')
    wire(f'M{x-4} 83 L{x} 75 L{x+4} 83')
    label(315, 95, 'Ujung model')
    for a, b, obj in path:
        y1, y2 = positions[a][1], positions[b][1]
        y = (y1+y2)/2
        is_switch = obj['role'].startswith('PMS_') or obj['role'] == 'PMT'
        half = 22.5 if is_switch else 0
        wire(f'M{x} {y1} V{y+half} M{x} {y-half} V{y2}', f'data-equipment-id="{escape(obj["id"])}"')
        if is_switch:
            out.append(switch_svg(obj['role'], x, y, states.get(obj['id']), vertical=True))
            label(x+30, y+5, obj['role'] + ' · ' + state_label(obj))
        elif obj['role'] == 'CT':
            out.append(source_symbol('CT', x, y))
            label(x+30, y+4, 'CT · rasio belum diketahui')
        else:
            out.append(f'<circle cx="{x}" cy="{y}" r="12" fill="white" stroke="#bd242d"/>')
            label(x+30, y+4, obj['role'] + ' · simbol sementara')
    branches = defaultdict(list)
    for obj in bay['equipment']:
        if obj['mode'] == 'GROUND_BRANCH':
            branches[obj['connection']['value'][0]].append(obj)
    for node, devices in branches.items():
        if node not in positions:
            raise ValueError('Branch is outside the supported vertical series path')
        for i, obj in enumerate(devices):
            # Boundary attachments fan along an equipment-free conductor segment.
            # Internal attachments remain at their actual node, with separate lanes.
            y = positions[node][1] - (i*62 if node == bay['boundary']['node_id'] else 0)
            sx = x + 65 + (i*125 if node != bay['boundary']['node_id'] else 0)
            role = obj['role']
            out.append(f'<g data-device-role="{escape(role)}" data-attachment-node="{escape(node)}">')
            if role == 'PMS_TANAH':
                wire(f'M{x} {y} H{sx-22.5}')
                out.append(switch_svg(role, sx, y, states.get(obj['id'])))
                wire(f'M{sx+22.5} {y} H{sx+42}', 'data-earth-lead="true"')
                earth(sx+42, y)
                label(sx+62, y+4, 'ES · '+state_label(obj))
                label(sx+62, y+23, 'fungsi rakitan PMS line')
            elif role == 'CVT':
                wire(f'M{x} {y} H{sx}')
                out.append(source_symbol('CVT', sx, y))
                label(sx+30, y+14, 'CVT · rasio belum diketahui')
            elif role == 'LA':
                wire(f'M{x} {y} H{sx-10}')
                out.append(source_symbol('LA', sx, y))
                wire(f'M{sx+10} {y} H{sx+28}', 'data-earth-lead="true"')
                earth(sx+28, y)
                label(sx+62, y+4, 'LA · rating belum diketahui')
            else:
                raise ValueError('Unsupported branch symbol')
            out.append('</g>')
    for i, selector in enumerate(selectors):
        px, bus_y = 230+i*120, 630+i*60
        # All connection IDs come from the selector, not a fixed bus assignment.
        bus = next(n for n in selector['connection']['value'] if n != start)
        role = next(n['role'] for n in bay['nodes'] if n['id'] == bus)
        out.append(f'<g data-symbol="Busbar" data-bus-node="{escape(bus)}" '
                   f'transform="translate(80 {bus_y-19}) scale(5 1)" fill="none">{glyph("Busbar")}</g>')
        label(80, bus_y-14, 'BUS 1' if role == 'BUS_A' else 'BUS 2')
        wire(f'M{x} {bottom} H{px} V557.5 M{px} 602.5 V{bus_y}')
        out.append(switch_svg(selector['role'], px, 580, states.get(selector['id']), vertical=True))
        label(px+18, 573, selector['role'])
        label(px+18, 593, state_label(selector))
        out.append(f'<circle cx="{px}" cy="{bus_y}" r="3" fill="#bd242d"/>')
    label(80, 732, 'Layout skematik otomatis · koordinat sumber dan sambungan XML tetap tersimpan')
    out.append('</svg>')
    return ''.join(out)
