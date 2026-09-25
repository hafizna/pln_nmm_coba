"""Reuse the repository device SVGs, with explicit switch-state variants.

Original PMT/PMS artwork is vertical and open. Reuse its glyph geometry but
omit the outlined text label, supply readable labels in the diagram, and move
only the contact blade for the closed scenario. Source SVGs stay unchanged.
"""
from functools import lru_cache
from pathlib import Path
from lxml import etree as E

SYMBOLS = Path(__file__).resolve().parents[3] / 'web/public/devices'


@lru_cache
def glyph(name, closed=False):
    root = E.parse(str(SYMBOLS / (name + '.svg'))).getroot()
    children = list(root)
    if name in {'PMT', 'PMS'}:
        children = children[:3]  # geometry and terminal dots, before label outlines
        if closed:
            path = children[0]
            drawing = path.attrib['d']
            if name == 'PMT':
                drawing = drawing.replace('L1 32.719', 'L13.75 34.969')
            else:
                drawing = drawing.replace('L1 31.781', 'L13.781 34')
            path.attrib['d'] = drawing
    elif name == 'Busbar':
        children = children[:1]
    return ''.join(E.tostring(c, encoding='unicode') for c in children)


def switch_svg(role, x, y, state, *, vertical=False):
    name = 'PMT' if role == 'PMT' else 'PMS'
    center = 13.75 if name == 'PMT' else 13.781
    rotation = '' if vertical else 'rotate(-90) '
    return (f'<g fill="none" data-symbol="{name}" data-state="{state}" transform="translate({x} {y}) '
            f'{rotation}translate({-center} -26.5)">{glyph(name, state is False)}</g>')


def device_svg(name, x, y):
    width, height = (54, 48) if name == 'CT' else (50, 64)
    return (f'<g fill="none" data-symbol="{name}" transform="translate({x-width/2} {y-height/2})">'
            + glyph(name) + '</g>')


def busbar_svg(x, y):
    return (f'<g fill="none" data-symbol="Busbar" transform="translate({x} {y-19}) scale(0.55 1)">'
            + glyph('Busbar') + '</g>')
