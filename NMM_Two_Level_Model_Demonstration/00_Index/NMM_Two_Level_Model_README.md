# NMM Two-Level Model Demonstration

## Model 1 — System / Inter-GI
- Physical focus: GI Gilimanuk and its interconnection corridors.
- Main output: `01_System_Level/01_System_Level_Gilimanuk_Canonical.xml`
- Review workbook: `Gilimanuk_NMM_POC_Review_Workbook.xlsx`
- Role: identifies substations, circuits, transformers, generators, and remote boundary endpoints.

## Model 2 — Single Substation / Internal GI
- Physical focus: the focused sample substation `GI_Gill`.
- Main output: `02_Substation_Level/02_Substation_Level_GI_Gill_Canonical.xml`
- Review workbook: `GI_Gill_NMM_Substation_Level_Review.xlsx`
- Role: resolves internal bay topology using explicit Breaker, Disconnector, Terminal, and ConnectivityNode objects.

## How the levels link
The system model owns the network circuit and high-level endpoint. The substation-detail model owns the internal
bay and switching topology. A persistent boundary or terminal identifier should be shared or mapped between the two.

## Important limitation
The two supplied source XML files do not describe the same physical substation. They demonstrate two complementary
model granularities. The GI_Gill file is a focused single-substation sample; the Gilimanuk model is derived from the
Bali system source and overview SLD.
