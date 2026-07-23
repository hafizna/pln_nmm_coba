# Illustrative fill guide — Gilimanuk canonical draft

## Purpose

`Gilimanuk_NMM_POC_Canonical_Draft_ILLUSTRATIVE_FILLED.xml` is a derivative of
`Gilimanuk_NMM_POC_Canonical_Draft.xml` with every `PENDING_*` technical
parameter filled in with a plausible value, so it shows **what a fully
populated CIM file looks like**. It is not a corrected or approved model — the
underlying PLN source data still does not contain these values. Its purpose is
to be a template: PLN's asset-register team can see exactly which fields a
complete model needs and build a data-collection sheet against them.

Every value this file adds is marked two ways so it can never be mistaken for
confirmed data:

- `plnnmm:technicalParameterStatus` changes from `PENDING_*` to
  `ILLUSTRATIVE_TEMPLATE_NOT_CONFIRMED`.
- `plnnmm:mappingNote` explains, in plain language, how the illustrative value
  was derived and what document should replace it.

Do not import this file into any operational or load-flow system as if it
were real. Treat `ILLUSTRATIVE_TEMPLATE_NOT_CONFIRMED` the same way you would
treat a value that is still blank.

## What was filled, and where it should come from in a real asset register

### 1. Line corridors (9x `ACLineSegment`: BWI-C1..4, NEG-C1/C2, CLB-C1/C2, PMR-C1)

| CIM field | Illustrative source used here | Real PLN document/column needed |
|---|---|---|
| `ACLineSegment.r`, `.x`, `.bch`, `.gch` | Computed from the conductor type(s) and length already present in `plnnmm:conductorDescription` (e.g. ACSR HAWK, ACCC LISBON) using typical published per-km constants | Conductor test/design data sheet or SUTT corridor electrical parameter register (per-circuit R/X/B at 50 Hz, positive sequence) |
| `Conductor.length` (CLB-C1, CLB-C2, PMR-C1 only) | Estimated distance, since the source SLD gave a corridor label but no confirmed route length | Route/right-of-way survey length or tower schedule |

Asset-register implication: PLN needs a **per-circuit conductor and electrical
parameter table** — columns for conductor type per segment, segment length,
and either manufacturer R/X/B constants or a computed per-circuit R/X/B/G at a
reference frequency. Composite routes (mixed conductor types along one
circuit, as seen in BWI-C1..C4) need segment-level rows, not just one row per
circuit.

### 2. Transformers (`PowerTransformerEnd`, TRF 1 & TRF 2 Gilimanuk, 2 ends each)

| CIM field | Illustrative source used here | Real PLN document/column needed |
|---|---|---|
| `TransformerEnd.r`, `.x` | Typical impedance percentage for a GI step-down transformer of this MVA class | Transformer factory test report (short-circuit impedance test) |
| `TransformerEnd.phaseAngleClock`, `plnnmm:vectorGroup` | Assumed `Dyn11`, the PLN-standard vector group for 150/20 kV GI transformers | Transformer nameplate |
| `plnnmm:tapChangerType` | Assumed on-load tap changer, +10%/-10%, 17 steps | Tap changer nameplate/OLTC datasheet |

Asset-register implication: a **transformer nameplate table** — vector group,
impedance (%, on rated base), tap changer type/range/step count, and which end
each parameter applies to (HV/LV).

### 3. Generator step-up unit (`PowerTransformerEnd`, GSU GEN1, 2 ends)

Same fields as above, but vector group assumed `YNd11` (typical for a
generator step-up unit) with an off-circuit tap changer (typical for GSU
class, since GSU taps are normally changed de-energized, unlike a grid
transformer). `PowerTransformerEnd.ratedS` (130 MVA) was also filled here
because the source had `ratedU` only — this value was chosen to match the
illustrative generator rating below, not from independent GSU nameplate
evidence.

Asset-register implication: same nameplate table as transformers, but keep
GSU as a distinct equipment class/row so its typically-different tap-changer
practice isn't confused with a grid transformer's.

### 4. Generator (`SynchronousMachine` + `ThermalGeneratingUnit`, PLTG Gilimanuk Unit 1)

| CIM field | Illustrative source used here | Real PLN document/column needed |
|---|---|---|
| `SynchronousMachine.ratedS`, `.maxQ`, `.minQ`, `ratedPowerFactor` | Typical single-shaft open-cycle gas turbine class figures (144 MVA / 0.9 pf) | Generator nameplate / capability curve |
| `GeneratingUnit.ratedNetMaxP`, `.maxOperatingP`, `.minOperatingP` | Illustrative 130 MW / 40 MW min-load figure for this unit class | Commissioning/COD test report or dispatch operating envelope |
| `ThermalGeneratingUnit.fuelType` | Set to `gas`, consistent with "PLTG" (Pembangkit Listrik Tenaga Gas) in the asset name | Fuel type is usually already known from the plant name/class; confirm against plant registration |

Asset-register implication: a **generating unit capability table** — rated
MVA/MW, min/max active power, reactive power limits (or a capability curve),
power factor, and fuel type, sourced from commissioning documents rather than
guessed from plant naming convention.

## Suggested asset-register sheet structure

Based on the four tables above, a practical PLN "technical parameter
completion" workbook would have one tab per equipment class:

1. **Line corridors** — keyed by circuit ID, one row per conductor segment,
   columns for conductor type, cross-section, length, and either per-km
   constants or the aggregated per-circuit R/X/B/G.
2. **Transformers** — keyed by transformer ID + end number, columns for
   vector group, impedance %, tap changer type/range.
3. **GSU** — same structure as transformers, kept as its own tab since tap
   changer practice and typical vector group differ from grid transformers.
4. **Generating units** — keyed by unit ID, columns for rated MVA/MW, P/Q
   limits, power factor, fuel type.

Each row should carry a source/provenance column (test report number, survey
date, or "estimated — pending confirmation") so the register itself keeps the
same visible-gap discipline this project already uses in
`plnnmm:technicalParameterStatus`.
