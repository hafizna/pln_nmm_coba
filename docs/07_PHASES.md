# 07 ? Bali SLD Milestone

Direction updated 2026-09-17: prove the core source-to-model-to-XML-to-SLD
workflow before expanding web uploads. One week is a proposed timebox, not a
promise of full-Bali acceptance. Capability acceptance and verified Bali data
coverage are separate. The steps below are targets, not completed features.

## Sequence

| Order | Deliverable |
|---|---|
| 1 | Representative GI fixture with line/remote endpoint, transformer/load, coupler, applicable primary equipment, and explicit source/assumption manifest; separate shared-breaker diameter example |
| 2 | Core source adapters and internal model contract: stable identity, per-field provenance, reconciliation, conflicts, and repeat-import change reports; validate the ED adapter against actual ED when received |
| 3 | CLI input → model → validation → EQ/DL/required companions → re-import; preserve unsupported primary objects and separate scenario values from asset parameters |
| 4 | Existing viewer displays the re-imported model at system/GI level, including DL, ratings, sources and gaps; core edits survive save/reopen |
| 5 | Early small-package import into PowerFactory; compare model interpretation before study results; each additional application needs its own evidence |
| 6 | Expand Bali coverage and build guided uploads using the same core functions and diagnostics |

Collect ED, per-GI SLDs and study parameters while implementing the core. Labeled
synthetic input and assumptions can demonstrate capability without claiming
verified Bali data. Workbook input is one adapter, not the permanent model store.
Study execution belongs to external applications; native result exchange is later.

## Core capability acceptance

- [ ] Representative sources reconcile to stable model identities; ambiguous
      matches remain visible and source refresh preserves reviewed enrichment.
- [ ] Structural validity and electrical connectivity are checked separately;
      valid references alone do not establish correct bay or remote-end wiring.
- [ ] XML is exported and independently re-imported for the demonstration SLD;
      the viewer does not bypass this check by rendering the pre-export workbook.
- [ ] Model, provenance, scenario and layout retain their values and references
      after core edits and save/reopen, including unknowns and applicable CT/CVT.
- [ ] A small package has an application-specific import/interpretation report,
      or an explicit untested status if that application is unavailable.
- [ ] Demonstration data assumptions and measured Bali coverage are reported
      separately; successful capability tests do not verify source data.

## Full-Bali milestone acceptance

- [ ] Manifest enumerates all GI, boundary, circuits and applicable equipment
      in the selected Bali source revision; exclusions/conflicts are explicit.
- [ ] Every scoped GI/circuit appears in system SLD and links to detail.
- [ ] Bay equipment has stable IDs and valid attachment/connectivity references;
      no duplicate IDs, dangling internal references or silently omitted objects.
- [ ] Bus configurations and equipment order follow evidence or labeled assumptions.
- [ ] CT/CVT and other applicable primary equipment are present; unknown rating
      fields remain inspectable. Source-limited detail is labeled provisional.
- [ ] Rating/unit/source/quality are inspectable; OCR setting, Inom and IKHA
      are distinct; inferred values cannot masquerade as verified.
- [ ] Switch state supports open/closed/unknown per scenario; normal state separate.
- [ ] Edit/save/reopen preserves model, scenario, layout and identity.
- [ ] Preserve export/import retains primary objects, CT/CVT attachments, supported
      ratings, provenance and bit-exact coordinates; companion files remain linked.
- [ ] Standard export explicitly reports excluded PLN data.
- [ ] Appropriate Python regression checks and web build pass; overview/detail
      visually reviewed for connectivity, symbols and readability.

## If the timebox is too tight

Reduce automated layout polish, bulk editing and snapshot overlays first.
Use reviewed template-assisted bay modeling with explicit assumptions.
Do not hide missing primary equipment, drop fields on export, or call partial
coverage ?full Bali.? If source review remains incomplete, deliver a provisional
Bali model with a measured coverage/gap report and record unfinished acceptance.

## Later

1. Replace assumptions using per-bay asset registers and as-built SLDs.
2. Add operating snapshots and illustrative risk/defense-scheme scenarios.
3. Establish solver-ready parameter coverage and validate load flow/short-circuit
   studies in external applications using NMM exports.
4. Add model/result exchange for further studies, native additional CGMES
   profiles and production hosting. NMM remains the model provider.
