# 02 - File Format

## Input

Version 1 accepts PLN CIM16 / CGMES 2.4.15 Equipment profile XML using:

- CIM namespace: `http://iec.ch/TC57/2013/CIM-schema-cim16#`
- RDF namespace: `http://www.w3.org/1999/02/22-rdf-syntax-ns#`
- PLN coordinate namespace: `http://iconpln.co.id#`
- PLN UI annotation namespace:
  `https://eng.ui.ac.id/lab-simulasi/nhjarman2025#`

The current scope is EQ only. TP, SSH, SV, DL, and GL are future phases.

The Bali milestone plans an EQ core plus preserved PLN asset extensions and
versioned scenario/snapshot companions. This package is not implemented yet and
is not a claim of standard-only CGMES compliance. See
[the minimum contract](09_BALI_PRIMARY_SLD_SPEC.md).

## PLN Extensions

The adapter preserves:

- `plnicp:DiagramProperty.x`
- `plnicp:DiagramProperty.y`
- `nhftui:info`
- Supported `plnnmm` review/provenance properties.

These fields are extracted before cimpy import, stripped from the temporary
cimpy input, and reinjected after cimpy export.

Whole unsupported primary-equipment objects such as CT/CVT need additional
preservation support and reference tests; existing property handling is not
sufficient. Normal switch position and scenario state must remain separate.

## Template Placeholders

The larger aggregate fixture contains unresolved values such as:

- `$(Isi_ACLineSegment.r)`
- `$(Isi_ACLineSegment.x)`
- `$(Isi_Conductor.length)`
- `$(Isi_PowerTransformerEnd.ratedU)`

These are interpreted as upstream template prompts for a user or generator to
fill. They may represent bay names, bus labels, equipment numbers, or required
electrical parameters depending on the field. The CLI `inspect` command reports
them before semantic import.

## Export Modes

`preserve_extensions` exports PLN-compatible XML with the custom namespaces
reinserted.

`standard_cgmes` exports cimpy's clean CGMES EQ output without PLN extensions.
This is useful for interoperability testing, but it will not preserve PLN's
diagram/UI annotations.
