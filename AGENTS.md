# Agent instructions for pln_nmm_coba

## Product direction

This repository contains the CIM parser/serializer kernel AND the local web
workspace. The next milestone is a complete primary-equipment SLD model of Bali:
system overview down to GI/bay, busbars, CB/PMT, disconnector/PMS, earthing switch,
CT, CVT/PT, arrester, transformers, generators and shunts applicable to sources.
Ratings, scenario status and per-field provenance must be inspectable.

Read README.md, docs/09_BALI_PRIMARY_SLD_SPEC.md and docs/07_PHASES.md before
product work. Those describe planned acceptance, not features already complete.
SLD_engine remains a separate repository used as reconciled source evidence;
do not merge it or assume a runtime dependency.

## Critical invariants

1. Never modify or fork cimpy. Wrap it externally.
2. Canonical round-trip key is rdf:ID with leading underscore stripped, NOT
   IdentifiedObject.mRID when the two disagree.
3. Preserve float coordinates bit-exact using Python repr(); no rounding.
4. Model switching as explicit connected equipment. Inferred/assumed bay and
   switching structures are authorized for the demo with visible provenance.
   This supersedes the old annotation-only switching direction.
5. Do not assume every GI is double busbar or apply a universal bay arrangement.
   Follow evidence or mark the specific assumption.
6. Separate physical connectivity/ratings, normal position, scenario state,
   snapshot values and diagram geometry. Unknown is not zero or closed.
7. Do not fabricate verified nameplate ratings. Dummy operating values belong
   to explicitly labeled scenarios. Inom, IKHA and OCR settings remain distinct.
8. Use supported CIM16/CGMES 2.4.15 EQ structure. Unsupported asset objects
   (including CT/CVT) require explicit tested extension preservation; current
   property preservation does not guarantee whole-object round-trip.
9. Scenario open state must not be presented as standard EQ normalOpen.
   Scenario companions are planned; native SSH/TP/SV/DL/GL remain later work.
10. Primary connectivity validation is in scope now. Solver bus-branch reduction,
    load flow, short circuit and defense-scheme execution follow the SLD milestone.

Use PMS/disconnector for switching and ?defense scheme? for the protection scheme
to avoid ambiguous DS labels. Opening a coupler does not automatically shed load.

## How to run

```powershell
python -m pip install -e ".[dev,web]"
python -m pytest -q
python examples/roundtrip_demo.py
python -m uvicorn pln_nmm_web.api:app --host 127.0.0.1 --port 8000 --reload
```

Frontend in a separate terminal:

```powershell
cd web
npm install
npm run dev -- --port 5173 --strictPort
npm run build
```

CLI: python -m pln_nmm.cli inspect path/to/file.xml
See README for preserve/standard export commands.

## Source layout

- src/pln_nmm/adapter.py: pure XML extract/strip/reinject.
- importer.py / exporter.py: cimpy wrappers.
- diagnostics.py / sld.py / topology.py: diagnostics and derived inspection.
- src/pln_nmm_web/api.py: local FastAPI inspection.
- web/: React/TypeScript workspace.
- tests/: regression tests and fixtures.
- docs/: direction, minimum field contract, acceptance and historical evidence.

## Domain and verification

CIM namespace: http://iec.ch/TC57/2013/CIM-schema-cim16#
PLN coordinate namespace: http://iconpln.co.id#
PLN nhftui namespace: https://eng.ui.ac.id/lab-simulasi/nhjarman2025#
Preserve supported plnnmm review metadata as well.

Unresolved $(Isi_*) values are template prompts; diagnose before cimpy typed
import. Keep raw evidence and identity mappings. New round-trip support requires
regressions for IDs, references, values, attachments and coordinate equality.
Check web builds for UI changes and visually review system/detail diagrams.

The one-week target is a timebox. Report measured coverage and unfinished
acceptance honestly. Prefer deferring layout polish and analysis overlays over
silently dropping primary equipment or provenance.

## Dependencies and licensing

Permissive dependencies only (MIT/BSD/Apache-2.0 etc.). No GPL/AGPL dependencies.
cimpy remains unmodified. Production deployment/authentication and a production
database are not prerequisites for the local demo.

AGENTS.md and CLAUDE.md intentionally contain the same project conventions.
Keep them synchronized when updating direction.
