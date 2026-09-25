"""Local XML round-trip workbench for the experimental primary model."""
import json
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response
from lxml.etree import XMLSyntaxError

from pln_nmm.model.line_bay import validate_line_model
from pln_nmm.model.line_review import render_review
from pln_nmm.model.line_xml import dumps_line_xml, loads_line_xml

router = APIRouter()
EXAMPLE = Path(__file__).resolve().parents[2] / 'outputs/kelapa_xml_demo/Kelapa_Muntok_1_NMM.xml'


def parse(data):
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(413, 'XML exceeds 8 MB')
    try:
        return loads_line_xml(data)
    except (ValueError, KeyError, IndexError, TypeError, XMLSyntaxError) as exc:
        raise HTTPException(422, f'XML NMM review tidak valid: {exc}') from exc


@router.get('/line-review', response_class=HTMLResponse)
def page():
    return Path(__file__).with_name('line_review.html').read_text(encoding='utf-8')


@router.get('/api/line-review/example')
def example():
    if not EXAMPLE.exists():
        raise HTTPException(404, 'Generate the Kelapa example with scripts/prepare_kelapa_demo.py')
    return Response(EXAMPLE.read_bytes(), media_type='application/xml',
                    headers={'Content-Disposition': 'attachment; filename="Kelapa_Muntok_1_NMM.xml"'})


@router.post('/api/line-review/import')
async def import_review(file: UploadFile = File(...)):
    model = parse(await file.read(8 * 1024 * 1024 + 1))
    states = model['scenario']['open'] if model.get('scenario') else {}
    try:
        html = render_review(model, from_xml=True)
    except ValueError as exc:
        raise HTTPException(422, f'Layout bay belum mendukung susunan ini: {exc}') from exc
    return {'html': html, 'switches': [
        {'id': o['id'], 'name': b['name'] + ' / ' + o['role'], 'open': states.get(o['id'])}
        for b in model['bays'] for o in b['equipment']
        if o['role'].startswith('PMS_') or o['role'] == 'PMT']}


@router.post('/api/line-review/scenario')
async def scenario(file: UploadFile = File(...), states: str = Form(...)):
    model = parse(await file.read(8 * 1024 * 1024 + 1))
    try:
        incoming = json.loads(states)
        if not isinstance(incoming, dict):
            raise ValueError('States must be an object')
        if not model.get('scenario'):
            model['scenario'] = {'id': 'ILLUSTRATIVE_REVIEW', 'quality': 'ASSUMED', 'open': {}}
        model['scenario']['open'].update(incoming)
        validate_line_model(model)
        result = dumps_line_xml(model)
        # Do not return a package that our reader cannot reopen.
        loads_line_xml(result)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(422, str(exc)) from exc
    return Response(result, media_type='application/xml')
