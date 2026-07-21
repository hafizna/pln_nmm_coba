# 04 - Editor UX

## First Useful Screen

The first screen should be the model workspace, not a landing page:

- Upload/import CIM XML.
- Show validation status.
- Show unresolved `$(Isi_*)` fields.
- Show object counts and extension counts.
- Render the SLD when coordinates/topology are sufficient.

## User Input Flow

Unresolved template fields should be editable as a review queue. The user should
see the CIM object, field name, current placeholder token, and suggested input
type when known.

Examples:

- `ACLineSegment.r`: numeric resistance.
- `Conductor.length`: numeric length.
- name-like fields: bay, bus, equipment, or circuit label depending on context.

The UI should save these edits separately from the original uploaded file until
the user chooses to export or commit a new model version.

## Editing Guardrails

The editor should distinguish:

- CIM semantic data.
- Diagram-only coordinates.
- PLN custom UI annotations.
- Generated helper values.

This prevents accidental changes to electrical model data when the user only
wants to adjust diagram layout.
