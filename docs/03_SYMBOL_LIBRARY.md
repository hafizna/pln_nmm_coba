# 03 - Symbol Library

## Purpose

The symbol library will map CIM equipment classes to visual single-line diagram
symbols in the web editor.

## Version 1 Symbols

V1 should prioritize SLD-visible assets that PLN's current data can identify
reliably:

- Busbar section
- AC line segment
- Power transformer
- Synchronous machine
- Conform load
- Terminal
- Connectivity node

Switching equipment such as breaker and disconnector may exist in imported CIM,
but v1 should not depend on it for supported asset import. PLN's current source
data does not appear complete enough for full node-breaker editing.

## Coordinates

Initial symbol placement should use `plnicp:DiagramProperty.x/y` when present.
When missing, the topology processor or editor may generate temporary layout
coordinates, but generated coordinates must be clearly marked as generated.

## Rendering Recommendation

Start with React + TypeScript + React Flow for editable node-edge SLD behavior.
Use Cytoscape.js later if graph analysis and large-network rendering become
more important than direct diagram editing.
