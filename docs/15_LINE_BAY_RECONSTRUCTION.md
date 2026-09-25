# Assumed line-bay reconstruction — 24 September 2026

This is an additional core review stage over the Babel inventory, not completion
of the Bali primary SLD milestone. The user authorized an assumed double-bus
line-bay pattern while detailed SLDs are pending. Every selected GI receives an
explicit profile entry; other bay types do not inherit this arrangement.

## Reproduce

```powershell
python scripts/reconstruct_babel_lines.py outputs/babel_inventory_20260923/inventory.json outputs/babel_lines_review --assume-double-bus --demo-scenario
```

The script preserves its input and refuses to overwrite existing deliverables.
It writes `assumptions.json`, `line_model.json`, and `review.html`. HTML is rendered
from the saved and reopened JSON. Use `--manifest path/to/assumptions.json` instead
of `--assume-double-bus` to explicitly select bays, GI profiles, remote labels,
and optional equipment. `optional.WAVE_TRAP` and `optional.SEALING_END` accept
true (assumed present), false (assumed absent), or null/omitted (unknown).
Unknown optional equipment is recorded as a gap, not drawn as installed.

## Model semantics

- Bay and GI identities retain the inventory's scoped source identity. Functional
  positions and nodes have deterministic IDs; they are not physical asset IDs.
- Two bus selector PMS merge before PMT; PMT -> CT -> PMS line form the series
  path. CVT, LA, and PMS tanah branch from the line-side node to a diagram earth
  reference. This attachment position is assumed, not verified against as-built.
- Optional wave trap and cable termination extend the series path when selected.
  The endpoint is an unresolved remote boundary, never an invented load.
- Generic Potential Transformer records are candidates for the assumed CVT
  position, not evidence of capacitive technology. Normal positions and ratings
  remain unknown. Administrative ACTIVE never becomes closed.
- All matching asset records remain available. Three phase records are not
  silently collapsed into one confirmed physical assembly, nor placed in series.
  Some source descriptions explicitly contain R/S/T or RST; grouping remains a
  review decision in this version. The same generic PMS candidates may appear
  at several positions; this does not allocate the asset more than once.
- Every position has candidate IDs, empty confirmed IDs, assumed attachment,
  and a mapping finding. All original source records, sheet/row evidence and
  source hash are retained in the JSON inventory. Unmapped records are retained.
- Illustrative Bus A switch states are stored in a separate scenario object;
  they are not written as normal positions. No energized-state calculation runs.

The core validates attachment references, position IDs, source candidates,
ground branches, scenario references and boundary references. Tests cover
selector merging, CT order, optional series devices, preserved unknowns,
source immutability, stable identity, ambiguity and JSON save/reopen.

## Measured local coverage

The 23 September inventory produces 33 numbered line-bay candidates across 10 GI
(7 Bangka, 3 Belitung), with 264 assumed functional positions. There are 231
position findings with unresolved asset roles/grouping, 33 earth-switch positions
without an exact asset-type match, and 66 unknown optional-device presences.
These are review findings, not evidence of missing installed equipment.

This is not proof of complete system coverage. The inventory adapter only includes
locations reached by its asset joins. Name-based remote/circuit labels are hints,
not confirmed line identities, paired endpoints or operating status. The model
does not connect Bangka and Belitung simply because both are in the inventory.

## Remaining integration

25 September display update: the XML review now uses a generated vertical bay
view with horizontal busbars and compact side branches, following the user's
SLD reference style. The series order is traversed from XML connectivity rather
than sorting assets or trusting the old horizontal X coordinates. CT/CVT/LA
artwork is vendored unchanged under `web/public/devices/qet`, pinned to commit
449df49147f8095143351139ab9d3bdac0e4cc96 with upstream notice and CC-BY-3.0
attribution. The rendered report includes the attribution and license links.
SVG transforms supply orientation/position; upstream terminal leads are composed
by the renderer. CVT uses a compact measurement glyph without a drawn earth lead;
LA and ES use short horizontal earth branches. Neither alters XML connectivity.

The vertical projection supports the two-selector line-bay spine. Unsupported
branching/disconnected series structures raise an explicit error instead of
silently omitting devices. Stored coordinates remain unchanged: this is a
generated schematic view, not a saved DL layout or geographic placement.

Update: a dedicated experimental RDF/XML reader/writer and local web route
`/line-review` now cover Kelapa–Muntok #1. Run `scripts/prepare_kelapa_demo.py`
with the inventory JSON and a fresh output directory (the web example expects
`outputs/kelapa_xml_demo`). See the README for commands. This adds XML re-import
and scenario edit/download/reopen, but does not complete the standard package
or main React canvas integration described below.

The XML uses CIM16 Bay, Substation, BusbarSection, ConnectivityNode, Breaker,
Disconnector and Terminal objects plus explicit NMM primary-device/earth
attachments and metadata. Terminal references reconstruct switching connectivity;
primary objects reconstruct their attachment references. There is no cached JSON
graph that overrides XML links. Ratings, raw evidence, field provenance, assembly
relationships, coordinates and scenario data survive the dedicated round trip.
The scenario is embedded NMM metadata, not native SSH or EQ normalOpen. The
generic cimpy import path refuses this format to prevent loss of primary objects.

PMS line and ES share an assumed assembly identity. Their contacts retain
separate scenario states; this does not claim two separate registered assets.
The demo checks only the assumed mutual exclusion of closed PMS line and ES.
It does not establish complete actual switchgear interlocks or energized topology.

The review renderer reuses PMT/PMS/Busbar SVG geometry from `web/public/devices`
(the repository's original device artwork). Original PMT/PMS files depict open
contacts; the renderer changes the contact blade for a closed scenario and keeps
the source files intact. CT, CVT and LA SVGs were added because those symbols
were absent from the existing set. The compact CVT SLD glyph intentionally omits
the earth lead/symbol; its model attachment remains intact. The earth contact
is shown on ES. Rendering changes do not rewrite electrical connections or XML.

The original JSON contract and HTML report are not a standard CIM/CGMES export and are not
integrated into the main web viewer. They do not prove XML export/re-import,
whole-object CT/CVT preservation, or external application interpretation.
The INVENTORY_ONLY workbook guard remains in force. Do not bypass it or feed this
review JSON into the workbook builder as if its asset mappings were verified.

Next integration needs reviewed or explicitly assumed asset grouping/role
assignments, reciprocal remote-bay reconciliation, a tested primary-extension
package export/re-import, and rendering in the existing viewer. Coupler,
transformer, generator and shunt templates remain separate work.
