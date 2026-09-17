# 09 ? Bali Primary SLD: Minimum Contract

Status: agreed product requirements, implementation pending. Field names below
are domain concepts, not claims of exact CIM property availability.

## Scope and evidence

Use Single Line Bali 2026 for physical inventory/connections; SLD_engine data
as reconciled observations; asset registers/as-built drawings for verification.
The user-supplied flow image describes 15 May 2026, 19.00 WITA, 1,296 MW.
Archive source files with document/page/date when available; images from the
conversation are not yet committed source artifacts.

Reconcile conflicting effective dates and operational/planned labels, including
Pecatu. Do not force every GI into double busbar. Detailed switching assumptions
are allowed, including couplers and selector arrangements, when labeled.

## Common fields

Stable ID; source IDs; name/tag; equipment type; GI/voltage level/bay; nominal
voltage; service lifecycle; source document/page/date; quality per field
(verified/inferred/assumed/unknown); reason/reviewer where applicable.
Electrical objects have terminal/CN references; instrumentation has explicit
attachment and diagram position appropriate to its model.

Unknown numeric values remain null, not zero. Units and rating basis are explicit.
Keep original source text beside normalized values. Snapshot timestamps and
scenario model-version references are mandatory when those records are present.

## Minimum equipment fields

| Equipment | Minimum inspectable fields |
|---|---|
| Busbar/section | Bus/section ID, nominal kV, rated A, connection points |
| Bay | Type (line/trafo/coupler/generator/shunt), equipment list, connection order, selectable buses |
| CB/PMT | Endpoints, normal position, scenario open/closed/unknown, rated kV/A, breaking capacity kA |
| PMS/disconnector | Endpoints, selector/line/isolation role, normal position, scenario state, rated kV/A |
| Earthing switch | Grounding attachment, normal position, scenario state |
| CT | Bay position/attachment, primary/secondary A, available ratios and selected ratio; core function, class, burden VA when known |
| CVT/PT | Type, attachment, primary/secondary voltage ratio with phase basis; winding function, class, burden when known |
| Arrester | Attachment, rated voltage, continuous operating voltage when known |
| Line/cable | Endpoint bays, circuit number, type, nominal kV, length, conductor/configuration, current limit and applicable conditions |
| Transformer | Winding attachments, MVA, winding kV, vector group, neutral grounding, tap position when known |
| Generator | Unit/aggregate identity, attachment, type, rated MW/MVA |
| Capacitor/reactor | Attachment, MVAr and voltage basis, steps if applicable, scenario state |
| Equivalent load | Attachment, scenario/snapshot P/Q or explicit power-factor assumption |

Wave traps and other primary devices appearing in source must be inventoried
with identity, location/attachment and available nameplate data. Secondary wiring,
relay internals and complete asset lifecycle metadata are outside this milestone.

The schema must expose these fields, but unknown ratings do not block drawing.
Generated assumed equipment must be countable separately from sourced equipment.

## Rating and state semantics

Store continuous current, operational/declared conductor limit (IKHA), and OCR
setting separately with units and source context. A CT selected ratio is not a
circuit thermal rating. Transformer MVA is not loading. Breaking capacity is
not continuous current. Aggregate corridor MW is not automatically per-circuit MW.

Separate asset rating, normal switching position, scenario state and measured/
illustrative snapshot. Closed does not imply energized. Unknown must remain
visible and must not default through cimpy to a claimed closed/zero value.

Defense scheme is distinct from PMS. Coupler opening alone does not establish
load shedding; trigger/target-breaker/bay/source relationships are required.
Scenario switching here is illustrative editing, not operational instruction.

## Package and preservation acceptance

Planned package: core EQ XML + preserved PLN asset extensions + versioned
scenario/snapshot companion and source manifest. The exact serialization schema
is an implementation task. Companion records reference model version and object ID.

CT/CVT whole objects and references need explicit preservation support; current
PLN property round-trip is insufficient proof. Standard-only export must report
omissions and must not claim to reproduce the complete primary SLD package.

Validate identity/reference sets, equipment coverage, field values and units,
CT/CVT attachment, scenario links and float coordinate equality after reopen
and preserve round-trip. Audit both overview and GI detail visually.
