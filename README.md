# PLN Network Model Management — CIM/SLD Toolkit

Python and web tooling for importing, inspecting, visualizing, and round-tripping
PLN CIM16 / CGMES 2.4.15 Equipment-profile XML.

The parser wraps SOGNO `cimpy` without modifying it. PLN diagram coordinates and
custom metadata are preserved outside cimpy and reinjected on export.

## Current scope

- CIM EQ XML import and diagnostics.
- Preservation of `plnicp:DiagramProperty.x/y`, `nhftui:info`, and the POC
  `plnnmm` provenance/data-quality properties.
- SLD-first web inspection using canonical coordinates.
- Optional derived topology schematic for data-quality review.
- Explicit diagnostics for unresolved template placeholders and incomplete bay
  connectivity.

Operational topology processing, load flow, and non-EQ CGMES profiles remain
future work.

## Install

```powershell
python -m pip install -e ".[dev,web]"
```

Python 3.10 or newer is required.

## CLI

Inspect an XML file:

```powershell
python -m pln_nmm.cli inspect "path\to\model.xml"
```

Round-trip while preserving PLN extensions:

```powershell
python -m pln_nmm.cli roundtrip "input.xml" "out\roundtrip_EQ.xml" --mode preserve
```

Emit standard CGMES without PLN extensions:

```powershell
python -m pln_nmm.cli roundtrip "input.xml" "out\standard_EQ.xml" --mode standard
```

## Web SLD viewer

Run these in separate terminals:

```powershell
python -m uvicorn pln_nmm_web.api:app --host 127.0.0.1 --port 8000 --reload
```

```powershell
cd web
npm install
npm run dev -- --port 5173 --strictPort
```

Open <http://127.0.0.1:5173> and upload a CIM XML file.

The viewer defaults to **Canonical coordinates**, which displays the layout
encoded in the XML. **Topology schematic** is a derived diagnostic view and may
surface orphan equipment or incomplete switching chains.

## Canonical demonstration files

- `Gilimanuk_NMM_POC_Package/Gilimanuk_NMM_POC_Canonical_Draft.xml` — system /
  inter-GI Gilimanuk proof of concept.
- `NMM_Two_Level_Model_Demonstration/02_Substation_Level/` — focused single-GI
  internal bay demonstration.
- `docs/08_CANONICAL_XML_GAP_RECAP.md` — evidence-based recap of the XML gaps
  filled relative to the initial aggregate source.

These are review drafts, not as-built operational models.

## Validation

```powershell
python -m pytest -q
cd web
npm run build
```

## Architecture

- `src/pln_nmm/adapter.py` — extract, strip, and reinject PLN extensions.
- `src/pln_nmm/importer.py` — cimpy import wrapper.
- `src/pln_nmm/exporter.py` — cimpy export wrapper and UTF-8 normalization.
- `src/pln_nmm/diagnostics.py` — pure-XML data-quality diagnostics.
- `src/pln_nmm/sld.py` — tolerant SLD extraction.
- `src/pln_nmm/topology.py` — derived bay/topology model.
- `src/pln_nmm_web/api.py` — local FastAPI inspection API.
- `web/` — React/TypeScript SLD workspace.

## Licensing

Runtime dependencies are permissively licensed: cimpy (Apache-2.0), lxml
(BSD), FastAPI, React, and React Flow. GPL/AGPL dependencies are out of scope.
