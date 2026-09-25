# 00 — Project Brief

Direction finalized 25 September 2026.

Repo ini menguji apakah data existing PLN dapat direkonsiliasi menjadi
authoritative network model dengan manual re-entry seminimal mungkin.

MVP boundary:

- **input:** one structurally-cleaned GI asset extract + corresponding GI SLD;
- **review:** per bay;
- **publication:** one canonical GI model;
- **bulk:** later staging + per-GI orchestration.

NMM menjadi governed network-model layer; upstream system tetap authoritative
untuk native fact-nya.

Master product/governance/data-request document:

[16_NMM_SSOT_REALIGNMENT_AND_PILOT.md](16_NMM_SSOT_REALIGNMENT_AND_PILOT.md)

Implementation roadmap:

[07_PHASES.md](07_PHASES.md)

Target code structure:

[19_REPO_TARGET_STRUCTURE.md](19_REPO_TARGET_STRUCTURE.md)
