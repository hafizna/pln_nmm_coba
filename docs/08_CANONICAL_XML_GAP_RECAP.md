# 08 — Canonical XML Gap Recap

## Purpose

This note records the XML/data changes that make the canonical demonstration
files usable for NMM inspection. It intentionally describes changes to the XML
model only; converter and web-viewer implementation changes are not part of
this comparison.

The main comparison is:

- Initial aggregate: `CIM_sample-db_userdef_python.xml`
- Canonical system model: `Gilimanuk_NMM_POC_Package/Gilimanuk_NMM_POC_Canonical_Draft.xml`
- Focused substation model: `NMM_Two_Level_Model_Demonstration/02_Substation_Level/02_Substation_Level_GI_Gill_Canonical.xml`

## Measured comparison

| Finding | Initial aggregate | Gilimanuk canonical | GI_Gill focused |
|---|---:|---:|---:|
| RDF objects (`rdf:ID`) | 4,353 | 294 | 155 |
| Duplicate `rdf:ID` | 0 | 0 | 0 |
| Internal RDF references | 5,265 | 440 | 235 |
| Dangling internal references | 0 | 0 | 0 |
| Unresolved `$(Isi_*)` values | 4,061 | 0 | 0 |
| `plnicp` coordinate properties | 0 | 236 | 138 |
| `plnnmm` review/provenance properties | 0 | 1,251 | 648 |

The canonical files are intentionally scoped subsets. The lower object count is
not data loss from conversion; it reflects selection of the equipment relevant
to the demonstration.

## Gaps filled in the canonical XML

### 1. Unresolved templates replaced by reviewable values

The aggregate source contains 4,061 unresolved `$(Isi_*)` occurrences in names,
identifiers, and technical fields. The canonical drafts contain none. Values
that could be supported by the source inventory or SLD evidence were populated.
Unknown technical parameters were marked through review metadata instead of
being fabricated as numeric zero.

### 2. Scope reduced to a coherent network case

The initial file is a large template-like aggregate with hundreds of repeated
region, substation, voltage-level, and base-voltage containers. The Gilimanuk
draft selects one system case:

- 5 substations: GI Gilimanuk plus four remote boundary substations;
- 7 voltage levels and 3 base voltages;
- 9 line corridors;
- 3 transformers and 1 synchronous machine.

The focused GI_Gill draft is a separate one-substation example and is not the
same physical station as GI Gilimanuk.

### 3. Explicit node-breaker objects added

The canonical Gilimanuk system XML contains:

- 13 `Bay` objects;
- 13 `Breaker` objects;
- 38 `Disconnector` objects;
- 130 `Terminal` objects;
- 51 `ConnectivityNode` objects;
- 3 `BusbarSection` objects.

This makes switching equipment and electrical junctions explicit enough for
SLD review. These CB/DS arrangements remain provisional where detailed as-built
substation evidence was unavailable.

The focused GI_Gill XML contains one `BusbarSection`, 9 bays, 9 breakers, and 18
disconnectors. It therefore represents a single-bus arrangement: one bus-side
DS and one equipment-side DS per bay. A double-bus selector arrangement must not
be inferred from this file without adding a second busbar and additional DS/CN
objects from engineering evidence.

### 4. Terminal and ConnectivityNode relations completed

Every modeled equipment side receives an explicit `Terminal`, and physical
junctions are represented by `ConnectivityNode` references. All internal
`rdf:resource="#..."` references resolve to an object in each canonical file.

One shared ConnectivityNode may connect a busbar and several bus-side
disconnectors. That is electrically valid CIM even when an SLD draws multiple
visual taps along the busbar.

### 5. Line-end records reconciled

End-specific source records were consolidated into one canonical
`ACLineSegment` per inter-GI circuit. Remote stations are retained as boundary
containers/endpoints so that one circuit is not represented as two unrelated
line assets.

Names such as `LINE GILL` are preserved from the focused source. They should be
read as source asset/bay labels, not automatically interpreted as a destination.
Ambiguous labels remain a naming-quality review item.

### 6. Diagram coordinates embedded

The canonical drafts add `plnicp:DiagramProperty.x/y` values for SLD-visible
objects and junctions. These positions provide the deterministic canonical
layout used by the web viewer. They are diagram data, not electrical topology.

### 7. Provenance and review state made explicit

The POC `plnnmm` namespace records information that was implicit or absent in
the aggregate source, including:

- `canonicalBusinessId`;
- `sourceObjectMRID`;
- `provenance`;
- `confidence`;
- `modelStatus`;
- `technicalParameterStatus`;
- conductor descriptions and mapping notes;
- model-level scope and disclaimer.

This metadata distinguishes mapped source facts from SLD-derived or provisional
content. It is review metadata, not standard CGMES.

## Remaining XML gaps

- The canonical models are SLD-derived drafts, not as-built models.
- Detailed SAP identifiers and SCADA tags are not yet confirmed.
- Line conductor/configuration parameters require authoritative study or asset
  records.
- Transformer impedance, winding, and nameplate data require confirmed source
  documents.
- Generator and GSU parameters remain incomplete.
- Switching state is schematic unless explicitly supported by the source.
- The Gilimanuk system case still contains equipment whose internal bay
  connectivity is insufficient for a fully derived topology schematic; canonical
  coordinates remain the authoritative demonstration layout.

These gaps must remain visible and reviewable rather than being filled with
invented defaults.
