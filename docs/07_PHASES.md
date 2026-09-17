# 07 ? Bali SLD Milestone

Direction agreed 2026-09-16. One week is a proposed timebox; acceptance below,
not elapsed days, determines completion. These tasks are planned, not implemented.

## Sequence

| Day | Deliverable |
|---|---|
| 1 | Source/coverage manifest; reconcile GI/circuit IDs, dates, existing/planned status; agree representative bay templates and assumptions |
| 2 | Canonical Bali system equipment/connectivity and deterministic IDs |
| 3 | GI/bay detail including switching, CT/CVT and other primary equipment; implement unsupported-data preservation |
| 4 | System/detail SLD, rating inspector, gap/source display |
| 5 | Scenario status editing and local versioned save/export/import |
| 6 | Full-Bali coverage audit and representative end-to-end round-trip checks |
| 7 | Fix failures, prepare demonstration and list unresolved evidence |

Baseline flow snapshot is stretch scope after acceptance. Load flow and defense
scheme execution are later milestones.

## Acceptance checklist

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
3. Establish solver-ready parameter coverage, then load flow/short circuit.
4. Add protection studies, native additional CGMES profiles and production hosting.
