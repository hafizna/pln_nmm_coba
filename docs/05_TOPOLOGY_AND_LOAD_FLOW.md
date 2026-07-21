# 05 - Topology And Load Flow

## Topology

The next backend milestone is bus-branch derivation from the cimpy object graph.
The first spike should test cimpy's `convert_node_breaker_to_bus_branch` on the
small valid PLN EQ fixture.

If cimpy works directly, wrap it lightly so PLN diagnostics and naming rules are
kept outside cimpy. If it does not, derive a NetworkX graph from:

- ConductingEquipment
- Terminal
- ConnectivityNode
- PowerTransformerEnd
- BaseVoltage / VoltageLevel

## Load Flow

pandapower should be the first load-flow target because it is pragmatic for
operational power-flow studies in Python. PyPSA can come later for planning and
optimization workflows.

Load-flow readiness requires more than EQ import. The platform will need
complete enough values for line impedances, transformer parameters, nominal
voltages, generators, loads, and operating state. Current `$(Isi_*)`
placeholders block that readiness.

## Boundary

The parser kernel should not become the solver. It should produce validated,
traceable model data that topology and solver modules can consume.
