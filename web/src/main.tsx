import React, { useCallback, useEffect, useMemo, useState } from 'react';
import ReactDOM from 'react-dom/client';
import ReactFlow, {
  Background,
  Controls,
  Edge,
  Handle,
  MiniMap,
  Node,
  NodeChange,
  NodeProps,
  Position,
  useEdgesState,
  useNodesState,
} from 'reactflow';
import ELK from 'elkjs/lib/elk.bundled.js';
import {
  AlertTriangle,
  Download,
  FileSearch,
  FileUp,
  Network,
  RotateCcw,
  TableProperties,
  Zap,
} from 'lucide-react';
import 'reactflow/dist/style.css';
import './styles.css';

const elk = new ELK();

const NODE_SIZE: Record<string, { width: number; height: number }> = {
  BusbarSection: { width: 280, height: 28 },
  default: { width: 90, height: 88 },
};

const ELK_LAYOUT_OPTIONS = {
  'elk.algorithm': 'layered',
  'elk.direction': 'DOWN',
  'elk.layered.spacing.nodeNodeBetweenLayers': '70',
  'elk.spacing.nodeNode': '48',
  'elk.layered.nodePlacement.strategy': 'NETWORK_SIMPLEX',
  'elk.layered.crossingMinimization.semiInteractive': 'true',
  'elk.edgeRouting': 'ORTHOGONAL',
};

async function applyElkLayout(
  nodes: Node<ApiNode>[],
  edges: Edge[],
): Promise<Node<ApiNode>[]> {
  if (nodes.length === 0) return nodes;

  const elkGraph = {
    id: 'root',
    layoutOptions: ELK_LAYOUT_OPTIONS,
    children: nodes.map((node) => {
      const size =
        NODE_SIZE[node.data.cim_class] ?? NODE_SIZE.default;
      return {
        id: node.id,
        width: size.width,
        height: size.height,
      };
    }),
    edges: edges.map((edge) => ({
      id: edge.id,
      sources: [edge.source],
      targets: [edge.target],
    })),
  };

  const laid = await elk.layout(elkGraph);
  const positions = new Map<string, { x: number; y: number }>();
  for (const child of laid.children ?? []) {
    if (child.id && typeof child.x === 'number' && typeof child.y === 'number') {
      positions.set(child.id, { x: child.x, y: child.y });
    }
  }

  return nodes.map((node) => {
    const next = positions.get(node.id);
    return next ? { ...node, position: next } : node;
  });
}

type ApiNode = {
  id: string;
  cim_class: string;
  label: string;
  x: number;
  y: number;
  source: string;
  has_coordinates: boolean;
  visible: boolean;
  ports?: Array<{ id: string; leftPercent: number }>;
};

type ApiEdge = {
  id: string;
  source: string;
  target: string;
  label: string;
};

type ApiBayItem = {
  equipment_id: string;
  cim_class: string;
  label: string;
};

type ApiBay = {
  id: string;
  busbar_id: string;
  head_cn_id: string;
  leaf_kind: string;
  items: ApiBayItem[];
};

type ApiVoltageLevel = {
  id: string;
  name: string;
  nominal_kv: number;
  busbar_ids: string[];
  bays: ApiBay[];
};

type ApiSubstation = {
  id: string;
  name: string;
  transformer_ids: string[];
  voltage_levels: ApiVoltageLevel[];
};

type ApiTopology = {
  substations: ApiSubstation[];
  orphan_equipment_ids: string[];
};

type ApiTopologyDiagnostics = {
  substation_count: number;
  voltage_level_count: number;
  bay_count: number;
  empty_substations: number;
  open_bays: number;
  bays_without_switches: number;
};

type InspectResult = {
  source_mode?: 'uploaded_cim';
  file: {
    name: string;
    size: number;
  };
  extensions: {
    total: number;
    x: number;
    y: number;
    nhftui: number;
    id_mrid_mismatch: number;
  };
  diagnostics: {
    placeholder_count: number;
    blocking_semantic_import: boolean;
    top_placeholder_fields: Array<{ field: string; count: number }>;
  };
  sld: {
    nodes: ApiNode[];
    edges: ApiEdge[];
    equipment_count: number;
    terminal_count: number;
    connectivity_node_count: number;
  };
  topology: ApiTopology | null;
  topology_diagnostics: ApiTopologyDiagnostics | null;
  gap_workbench?: GapRow[];
  source_mapping?: SourceMappingRow[];
};

type GapRow = {
  id: string;
  severity: 'ok' | 'info' | 'warning' | 'blocker';
  area: string;
  cim_field: string;
  label: string;
  count: number;
  source_candidate: string;
  confidence: string;
  next_action: string;
};

type SourceMappingRow = {
  source: string;
  records: string | number;
  status: string;
  fills: string;
  parser: string;
};

type GapDraft = {
  proposedValue: string;
  role: string;
  evidence: string;
  saveMode: 'review_overlay' | 'confirmed_import';
};

type PanelId = 'preview' | 'gaps' | 'sources';
type LayoutMode = 'canonical' | 'topology';

const deviceIcon: Record<string, string> = {
  ACLineSegment: '/devices/PHT.svg',
  Breaker: '/devices/PMT.svg',
  BusbarSection: '/devices/Busbar.svg',
  ConformLoad: '/devices/Beban.svg',
  Disconnector: '/devices/PMS.svg',
  GroundDisconnector: '/devices/PMS.svg',
  LoadBreakSwitch: '/devices/PMS.svg',
  PowerTransformer: '/devices/Trafo.svg',
  SynchronousMachine: '/devices/Generator.svg',
};

function SldNode({ data }: NodeProps<ApiNode>) {
  if (!data.visible) {
    return (
      <div className="cn-anchor">
        <Handle type="target" position={Position.Top} />
        <Handle type="source" position={Position.Bottom} />
      </div>
    );
  }

  const icon = deviceIcon[data.cim_class];
  const isBusbar = data.cim_class === 'BusbarSection';

  if (isBusbar) {
    return (
      <div className="busbar-rail">
        <Handle type="target" position={Position.Top} />
        {(data.ports ?? [{ id: 'default', leftPercent: 50 }]).map((port) => (
          <Handle
            key={port.id}
            id={port.id}
            type="source"
            position={Position.Bottom}
            style={{ left: `${port.leftPercent}%` }}
          />
        ))}
        <div className="busbar-bar" />
        <div className="busbar-label">{data.label}</div>
      </div>
    );
  }

  return (
    <div className="symbol-tile">
      <Handle type="target" position={Position.Top} />
      {icon ? (
        <img className="symbol-glyph" src={icon} alt="" draggable={false} />
      ) : (
        <div className="symbol-fallback" />
      )}
      <div className="symbol-label">{data.label}</div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

const nodeTypes = { sld: SldNode };

// Layout constants for the structured topology renderer.
// Tuned so that a small substation (1 VL, ~10 bays) reads at first sight
// without horizontal scrolling.
const BAY_SPACING = 190;     // px between bay columns; keeps long PLN labels readable
const ITEM_SPACING = 92;     // px between items stacked vertically in a bay
const BAND_GAP = 520;        // px between voltage-level bands
const SUBSTATION_GAP = 120;  // px between substations laid out horizontally
const BUSBAR_PAD = 40;       // px of busbar overhang on each side
const BUSBAR_GAP = 72;       // px between actual BusbarSection rails

function buildCanonicalLayout(nodes: ApiNode[]): Node<ApiNode>[] {
  const busbars = nodes.filter((node) => node.visible && node.cim_class === 'BusbarSection');
  const bounds = new Map<string, { minX: number; maxX: number }>();

  // Associate each positioned device with the nearest busbar vertically. This
  // lets each voltage-level rail span its own bays without inventing topology.
  for (const item of nodes) {
    if (!item.visible || item.cim_class === 'BusbarSection' || !item.has_coordinates) continue;
    const nearest = busbars.reduce<ApiNode | null>((best, busbar) => {
      if (!best) return busbar;
      return Math.abs(item.y - busbar.y) < Math.abs(item.y - best.y) ? busbar : best;
    }, null);
    if (!nearest) continue;
    const current = bounds.get(nearest.id);
    bounds.set(nearest.id, {
      minX: Math.min(current?.minX ?? item.x, item.x),
      maxX: Math.max(current?.maxX ?? item.x, item.x),
    });
  }

  return nodes.map((item) => {
    const bound = bounds.get(item.id);
    if (item.cim_class !== 'BusbarSection' || !bound) {
      return { id: item.id, type: 'sld', position: { x: item.x, y: item.y }, data: item };
    }
    const padding = 70;
    const x = bound.minX - padding;
    const width = Math.max(280, bound.maxX - bound.minX + padding * 2);
    return {
      id: item.id,
      type: 'sld',
      position: { x, y: item.y },
      style: { width },
      data: { ...item, x },
    };
  });
}

function buildCanonicalGraph(sld: InspectResult['sld']): {
  nodes: Node<ApiNode>[];
  edges: Edge[];
} {
  let nodes = buildCanonicalLayout(sld.nodes);
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const busbarIds = new Set(
    nodes.filter((node) => node.data.cim_class === 'BusbarSection').map((node) => node.id),
  );
  const collapsedAnchors = new Set<string>();
  const busbarByAnchor = new Map<string, string>();

  // CIM commonly models all taps on one busbar ConnectivityNode. For an SLD,
  // draw each adjacent DS directly from the rail instead of showing one shared
  // centre tap followed by a long horizontal junction line.
  for (const edge of sld.edges) {
    const busbarId = busbarIds.has(edge.source)
      ? edge.source
      : busbarIds.has(edge.target)
        ? edge.target
        : null;
    if (!busbarId) continue;
    const anchorId = edge.source === busbarId ? edge.target : edge.source;
    if (nodeById.get(anchorId)?.data.cim_class === 'ConnectivityNode') {
      collapsedAnchors.add(anchorId);
      busbarByAnchor.set(anchorId, busbarId);
    }
  }

  const rawEdges: Edge[] = [];
  for (const item of sld.edges) {
    if (busbarIds.has(item.source) || busbarIds.has(item.target)) continue;
    const sourceBusbar = busbarByAnchor.get(item.source);
    const targetBusbar = busbarByAnchor.get(item.target);
    rawEdges.push({
      id: item.id,
      source: sourceBusbar ?? item.source,
      target: targetBusbar ?? item.target,
      type: 'step',
      animated: false,
      style: { stroke: '#1e293b', strokeWidth: 1.25 },
    });
  }
  nodes = nodes.filter((node) => !collapsedAnchors.has(node.id));

  const edgesByBusbar = new Map<string, Edge[]>();
  for (const edge of rawEdges) {
    if (busbarIds.has(edge.source)) {
      edgesByBusbar.set(edge.source, [...(edgesByBusbar.get(edge.source) ?? []), edge]);
    }
    if (busbarIds.has(edge.target)) {
      edgesByBusbar.set(edge.target, [...(edgesByBusbar.get(edge.target) ?? []), edge]);
    }
  }

  for (const [busbarId, connected] of edgesByBusbar) {
    const busbar = nodes.find((node) => node.id === busbarId);
    if (!busbar) continue;
    const width = Number(busbar.style?.width) || 280;
    connected.sort((a, b) => {
      const aOther = nodeById.get(a.source === busbarId ? a.target : a.source);
      const bOther = nodeById.get(b.source === busbarId ? b.target : b.source);
      return (aOther?.position.x ?? 0) - (bOther?.position.x ?? 0);
    });
    const ports = connected.map((edge, index) => {
      const other = nodeById.get(edge.source === busbarId ? edge.target : edge.source);
      const relativeX = (other?.position.x ?? busbar.position.x) - busbar.position.x + 45;
      const portId = `tap-${index}`;
      if (edge.source === busbarId) edge.sourceHandle = portId;
      return { id: portId, leftPercent: Math.max(2, Math.min(98, relativeX / width * 100)) };
    });
    busbar.data = { ...busbar.data, ports };
  }

  return { nodes, edges: rawEdges };
}

function buildStructuredLayout(topology: ApiTopology): {
  nodes: Node<ApiNode>[];
  edges: Edge[];
} {
  const nodes: Node<ApiNode>[] = [];
  const edges: Edge[] = [];
  let cursorX = 0;

  for (const ss of topology.substations) {
    // Skip substations with no real busbars; they're container artifacts.
    const populatedVLs = ss.voltage_levels
      .filter((vl) => vl.busbar_ids.length > 0 && vl.bays.length > 0)
      .sort((a, b) => b.nominal_kv - a.nominal_kv); // highest kV at top

    if (populatedVLs.length === 0) continue;

    const uniqueBayCount = (vl: ApiVoltageLevel) => new Set(
      vl.bays.map((bay) => bay.items.map((item) => item.equipment_id).sort().join('|')),
    ).size;
    const ssWidth = Math.max(
      ...populatedVLs.map((vl) => Math.max(1, uniqueBayCount(vl)) * BAY_SPACING),
    );

    populatedVLs.forEach((vl, bandIndex) => {
      const bandY = bandIndex * BAND_GAP;
      // Keep one derived bay per equipment chain. A double-bus walk discovers
      // the same chain from both rails, in opposite directions.
      const seenChains = new Set<string>();
      const bays = vl.bays.filter((bay) => {
        const key = bay.items.map((item) => item.equipment_id).sort().join('|');
        if (seenChains.has(key)) return false;
        seenChains.add(key);
        return true;
      });
      const busbarIds = vl.busbar_ids.length > 0 ? vl.busbar_ids : [`virtual:${vl.id}`];
      const railWidth = Math.max(280, Math.max(1, bays.length) * BAY_SPACING);
      const portsByBusbar = new Map<string, Array<{ id: string; leftPercent: number }>>();
      bays.forEach((bay, bayIndex) => {
        const portId = `tap-${bayIndex}`;
        const tapX = BUSBAR_PAD + bayIndex * BAY_SPACING + 45;
        portsByBusbar.set(bay.busbar_id, [
          ...(portsByBusbar.get(bay.busbar_id) ?? []),
          { id: portId, leftPercent: Math.max(2, Math.min(98, tapX / railWidth * 100)) },
        ]);
      });

      busbarIds.forEach((actualBusbarId, railIndex) => {
        const busbarId = `bb:${actualBusbarId}`;
        const railY = bandY + railIndex * BUSBAR_GAP;
        nodes.push({
          id: busbarId,
          type: 'sld',
          position: { x: cursorX, y: railY },
          style: { width: railWidth },
          data: {
            id: actualBusbarId,
            cim_class: 'BusbarSection',
            label: `${vl.name} — Bus ${railIndex + 1} (${vl.nominal_kv.toFixed(0)} kV)`,
            x: cursorX,
            y: railY,
            source: 'topology',
            has_coordinates: false,
            visible: true,
            ports: portsByBusbar.get(actualBusbarId) ?? [],
          },
        });
      });

      bays.forEach((bay, bayIndex) => {
        const bayX = cursorX + BUSBAR_PAD + bayIndex * BAY_SPACING;
        let lastNodeId = `bb:${bay.busbar_id}`;

        const displayItems = bay.leaf_kind === 'bus_tie'
          ? bay.items.filter((item) => item.cim_class !== 'BusbarSection')
          : bay.items;
        displayItems.forEach((item, itemIndex) => {
          const itemNodeId = `eq:${bay.id}:${itemIndex}`;
          nodes.push({
            id: itemNodeId,
            type: 'sld',
            position: {
              x: bayX,
              y: bandY + busbarIds.length * BUSBAR_GAP + 45 + itemIndex * ITEM_SPACING,
            },
            data: {
              id: itemNodeId,
              cim_class: item.cim_class,
              label: item.label,
              x: bayX,
              y: bandY + busbarIds.length * BUSBAR_GAP + 45 + itemIndex * ITEM_SPACING,
              source: 'topology',
              has_coordinates: true,
              visible: true,
            },
          });

          edges.push({
            id: `e:${lastNodeId}->${itemNodeId}`,
            source: lastNodeId,
            target: itemNodeId,
            sourceHandle: itemIndex === 0 ? `tap-${bayIndex}` : undefined,
            type: 'step',
            animated: false,
            style: { stroke: '#1e293b', strokeWidth: 1.4 },
          });
          lastNodeId = itemNodeId;
        });
      });
    });

    cursorX += ssWidth + SUBSTATION_GAP;
  }

  return { nodes, edges };
}

function formatBytes(value: number) {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / 1024 / 1024).toFixed(2)} MB`;
}

function App() {
  const [result, setResult] = useState<InspectResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLayoutDirty, setIsLayoutDirty] = useState(false);
  const [activePanel, setActivePanel] = useState<PanelId>('preview');
  const [layoutMode, setLayoutMode] = useState<LayoutMode>('canonical');
  const [gapDrafts, setGapDrafts] = useState<Record<string, GapDraft>>({});
  const [nodes, setNodes, onNodesChangeBase] = useNodesState<ApiNode>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const visibleNodeCount = nodes.filter((node) => node.data.visible).length;
  const gapDraftCount = Object.values(gapDrafts).filter(
    (draft) => draft.proposedValue.trim() || draft.evidence.trim(),
  ).length;

  const topologyLayoutAvailable = useMemo(() => {
    if (!result?.topology) return false;
    return result.topology.substations.some((ss) =>
      ss.voltage_levels.some((vl) => vl.busbar_ids.length > 0 && vl.bays.length > 0),
    );
  }, [result]);
  const useStructuredTopology = layoutMode === 'topology' && topologyLayoutAvailable;
  const canonicalCoordinateCount = result?.sld.nodes.filter(
    (node) => node.visible && node.has_coordinates,
  ).length ?? 0;
  const sourceBusbarCount = result?.sld.nodes.filter(
    (node) => node.visible && node.cim_class === 'BusbarSection',
  ).length ?? 0;
  const sourceDisconnectorCount = result?.sld.nodes.filter(
    (node) => node.visible && node.cim_class === 'Disconnector',
  ).length ?? 0;
  const canonicalGraph = useMemo(
    () => (result ? buildCanonicalGraph(result.sld) : { nodes: [], edges: [] }),
    [result],
  );

  const importedNodes = useMemo<Node<ApiNode>[]>(() => {
    if (!result) return [];
    if (useStructuredTopology && result.topology) {
      return buildStructuredLayout(result.topology).nodes;
    }
    return canonicalGraph.nodes;
  }, [canonicalGraph.nodes, result, useStructuredTopology]);

  const importedEdges = useMemo<Edge[]>(() => {
    if (!result) return [];
    if (useStructuredTopology && result.topology) {
      return buildStructuredLayout(result.topology).edges;
    }
    return canonicalGraph.edges;
  }, [canonicalGraph.edges, result, useStructuredTopology]);

  useEffect(() => {
    setNodes(importedNodes);
    setEdges(importedEdges);
    setIsLayoutDirty(false);

    // Structured layout already places nodes deterministically. Only fall
    // back to ELK when we couldn't build topology AND the API gave us a
    // flat node list with no PLN coordinates.
    if (useStructuredTopology) return undefined;

    const hasPlnCoords = importedNodes.some((node) => node.data.has_coordinates);
    if (importedNodes.length > 0 && !hasPlnCoords) {
      let cancelled = false;
      void applyElkLayout(importedNodes, importedEdges).then((laidOut) => {
        if (!cancelled) setNodes(laidOut);
      });
      return () => {
        cancelled = true;
      };
    }
    return undefined;
  }, [importedEdges, importedNodes, setEdges, setNodes, useStructuredTopology]);

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => {
      if (changes.some((change) => change.type === 'position' && change.dragging !== false)) {
        setIsLayoutDirty(true);
      }
      onNodesChangeBase(changes);
    },
    [onNodesChangeBase],
  );

  async function inspectFile(file: File) {
    setIsLoading(true);
    setError(null);
    const body = new FormData();
    body.append('file', file);

    try {
      const response = await fetch('/api/inspect', {
        method: 'POST',
        body,
      });
      if (!response.ok) {
        throw new Error(`Inspection failed with HTTP ${response.status}`);
      }
      setResult((await response.json()) as InspectResult);
      setLayoutMode('canonical');
      setActivePanel('preview');
      setGapDrafts({});
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Inspection failed');
    } finally {
      setIsLoading(false);
    }
  }

  function resetLayout() {
    setNodes(importedNodes);
    setIsLayoutDirty(false);
  }

  function downloadLayout() {
    if (!result) return;
    const byId = new Map(result.sld.nodes.map((item) => [item.id, item]));
    const layout = {
      file: result.file.name,
      exportedAt: new Date().toISOString(),
      positions: nodes.map((node) => {
        const source = byId.get(node.id);
        return {
          id: node.id,
          label: source?.label ?? node.id,
          cimClass: source?.cim_class ?? 'Unknown',
          x: node.position.x,
          y: node.position.y,
        };
      }),
    };
    const blob = new Blob([JSON.stringify(layout, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${result.file.name.replace(/\.[^.]+$/, '')}-sld-layout.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  function updateGapDraft(id: string, patch: Partial<GapDraft>) {
    setGapDrafts((current) => ({
      ...current,
      [id]: {
        ...(current[id] ?? {
          proposedValue: '',
          role: 'transmission_user',
          evidence: '',
          saveMode: 'review_overlay',
        }),
        ...patch,
      },
    }));
  }

  function downloadGapOverlay() {
    if (!result) return;
    const proposals = (result.gap_workbench ?? [])
      .map((row) => ({ row, proposal: gapDrafts[row.id] }))
      .filter(({ proposal }) => proposal?.proposedValue.trim() || proposal?.evidence.trim());
    const overlay = {
      file: result.file.name,
      sourceMode: result.source_mode,
      exportedAt: new Date().toISOString(),
      writePolicy: 'review_overlay_only_until_user_confirmation',
      proposals,
    };
    const blob = new Blob([JSON.stringify(overlay, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${result.file.name.replace(/\.[^.]+$/, '')}-gap-overlay.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Zap size={20} />
          </div>
          <div>
            <h1>PLN NMM</h1>
            <p>SLD workspace</p>
          </div>
        </div>

        <label className="upload-target">
          <FileUp size={22} />
          <span>{isLoading ? 'Inspecting...' : 'Upload CIM XML'}</span>
          <input
            type="file"
            accept=".xml,text/xml,application/xml"
            disabled={isLoading}
            onChange={(event) => {
              const file = event.currentTarget.files?.[0];
              if (file) void inspectFile(file);
              event.currentTarget.value = '';
            }}
          />
        </label>

        {error && (
          <div className="notice error">
            <AlertTriangle size={18} />
            <span>{error}</span>
          </div>
        )}

        {result ? (
          <section className="details">
            <div className="file-title">
              <Network size={18} />
              <div>
                <strong>{result.file.name}</strong>
                <span>
                  Uploaded CIM XML
                  {' · '}
                  {formatBytes(result.file.size)}
                </span>
              </div>
            </div>

            <div className="panel-tabs" role="tablist" aria-label="NMM workspace panels">
              <PanelTab
                id="preview"
                active={activePanel}
                setActive={setActivePanel}
                icon={<Network size={15} />}
                label="SLD"
              />
              <PanelTab
                id="gaps"
                active={activePanel}
                setActive={setActivePanel}
                icon={<TableProperties size={15} />}
                label="Gaps"
              />
              <PanelTab
                id="sources"
                active={activePanel}
                setActive={setActivePanel}
                icon={<FileSearch size={15} />}
                label="Sources"
              />
            </div>

            {activePanel === 'gaps' && (
              <>
                <GapWorkbench
                  rows={result.gap_workbench ?? []}
                  drafts={gapDrafts}
                  onDraftChange={updateGapDraft}
                />
                {gapDraftCount > 0 && (
                  <button className="ghost-button" type="button" onClick={downloadGapOverlay}>
                    <Download size={16} />
                    Gap overlay JSON
                  </button>
                )}
              </>
            )}

            {activePanel === 'sources' && <SourceMapping result={result} />}


            {activePanel === 'preview' && (
            <>
            <div className="metric-grid">
              <Metric label="SLD nodes" value={visibleNodeCount} />
              <Metric label="Edges shown" value={edges.length} />
              <Metric label="Terminals" value={result.sld.terminal_count} />
              <Metric label="CNs" value={result.sld.connectivity_node_count} />
              <Metric label="Extensions" value={result.extensions.total} />
              <Metric label="ID mismatch" value={result.extensions.id_mrid_mismatch} />
            </div>

            <div className={result.diagnostics.blocking_semantic_import ? 'notice warn' : 'notice ok'}>
              <AlertTriangle size={18} />
              <span>
                {result.diagnostics.placeholder_count > 0
                  ? `${result.diagnostics.placeholder_count} unresolved template tokens`
                  : 'No unresolved template tokens'}
              </span>
            </div>

            {result.topology_diagnostics && (
              <section className="topology-summary">
                <h3>Topology</h3>
                <div className="metric-grid">
                  <Metric label="Substations" value={result.topology_diagnostics.substation_count} />
                  <Metric label="Bays" value={result.topology_diagnostics.bay_count} />
                </div>
                {(result.topology_diagnostics.bays_without_switches > 0 ||
                  result.topology_diagnostics.open_bays > 0) && (
                  <div className="notice warn">
                    <AlertTriangle size={18} />
                    <span>
                      {result.topology_diagnostics.bays_without_switches > 0 && (
                        <>
                          <strong>{result.topology_diagnostics.bays_without_switches}</strong> bays
                          have no switching equipment in source CIM.
                          <br />
                        </>
                      )}
                      {result.topology_diagnostics.open_bays > 0 && (
                        <>
                          <strong>{result.topology_diagnostics.open_bays}</strong> bays end on a
                          switch with no continuation.
                        </>
                      )}
                    </span>
                  </div>
                )}
              </section>
            )}

            {layoutMode === 'canonical' && sourceBusbarCount < 2 && (
              <div className="notice warn">
                <AlertTriangle size={18} />
                <span>
                  Source XML contains <strong>{sourceBusbarCount}</strong> BusbarSection and{' '}
                  <strong>{sourceDisconnectorCount}</strong> disconnectors. A double-bus view
                  needs a second busbar and its bus-selector DS objects in the CIM model.
                </span>
              </div>
            )}

            {!result.topology && (
              <div className="notice muted">
                <Network size={18} />
                <span>
                  Topology unavailable — cimpy could not parse this file. Showing flat XML view.
                </span>
              </div>
            )}

            {result.diagnostics.top_placeholder_fields.length > 0 && (
              <div className="field-list">
                {result.diagnostics.top_placeholder_fields.map((item) => (
                  <div key={item.field} className="field-row">
                    <span>{item.field}</span>
                    <strong>{item.count}</strong>
                  </div>
                ))}
              </div>
            )}

            <div className={isLayoutDirty ? 'notice edit' : 'notice muted'}>
              <Network size={18} />
              <span>
                {isLayoutDirty
                  ? 'Layout edited locally. Download the JSON snapshot before clearing.'
                  : 'Drag nodes on the canvas to adjust the SLD layout locally.'}
              </span>
            </div>

            <div className="layout-mode" role="group" aria-label="SLD layout mode">
              <button
                className={layoutMode === 'canonical' ? 'active' : ''}
                type="button"
                onClick={() => setLayoutMode('canonical')}
              >
                Canonical coordinates
              </button>
              <button
                className={layoutMode === 'topology' ? 'active' : ''}
                type="button"
                disabled={!topologyLayoutAvailable}
                onClick={() => setLayoutMode('topology')}
              >
                Topology schematic
              </button>
            </div>

            <div className={layoutMode === 'topology' ? 'notice warn' : 'notice ok'}>
              <Network size={18} />
              <span>
                {layoutMode === 'canonical'
                  ? `Showing ${canonicalCoordinateCount} positioned objects from the XML. This is the faithful diagram view.`
                  : `Derived schematic view. ${result.topology?.orphan_equipment_ids.length ?? 0} orphan equipment are not placed in bay chains.`}
              </span>
            </div>

            <div className="button-row">
              <button className="ghost-button" type="button" onClick={downloadLayout}>
                <Download size={16} />
                Layout JSON
              </button>
              <button className="ghost-button" type="button" onClick={resetLayout}>
                <RotateCcw size={16} />
                Reset layout
              </button>
            </div>
            </>
            )}

            <button className="ghost-button" type="button" onClick={() => setResult(null)}>
              <RotateCcw size={16} />
              Clear workspace
            </button>
          </section>
        ) : (
          <section className="empty-copy">
            <h2>Import a CIM XML file</h2>
            <p>
              The canvas renders SLD-visible assets directly from XML, so unresolved
              template tokens do not block diagram review.
            </p>
          </section>
        )}
      </aside>

      <section className="canvas-area">
        {nodes.length > 0 ? (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            fitView
            minZoom={0.05}
            maxZoom={1.8}
            nodesDraggable
            nodesConnectable={false}
          >
            <Background color="#d7dde6" gap={22} />
            <MiniMap pannable zoomable nodeStrokeWidth={3} />
            <Controls />
          </ReactFlow>
        ) : (
          <div className="canvas-empty">
            <Network size={42} />
            <h2>SLD canvas</h2>
            <p>Upload a PLN CIM XML file to inspect and render the diagram model.</p>
          </div>
        )}
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value.toLocaleString()}</strong>
    </div>
  );
}

function PanelTab({
  id,
  active,
  setActive,
  icon,
  label,
}: {
  id: PanelId;
  active: PanelId;
  setActive: (id: PanelId) => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      type="button"
      className={`panel-tab ${active === id ? 'active' : ''}`}
      onClick={() => setActive(id)}
    >
      {icon}
      {label}
    </button>
  );
}

function GapWorkbench({
  rows,
  drafts,
  onDraftChange,
}: {
  rows: GapRow[];
  drafts: Record<string, GapDraft>;
  onDraftChange: (id: string, patch: Partial<GapDraft>) => void;
}) {
  return (
    <section className="gap-workbench">
      {rows.map((row) => (
        <article key={row.id} className={`gap-card ${row.severity}`}>
          <div className="gap-head">
            <span>{row.area}</span>
            <strong>{row.count > 0 ? row.count : row.severity}</strong>
          </div>
          <h3>{row.label}</h3>
          <dl>
            <div>
              <dt>CIM</dt>
              <dd>{row.cim_field}</dd>
            </div>
            <div>
              <dt>Candidate source</dt>
              <dd>{row.source_candidate}</dd>
            </div>
            <div>
              <dt>Confidence</dt>
              <dd>{row.confidence}</dd>
            </div>
          </dl>
          <p>{row.next_action}</p>
          <div className="gap-proposal">
            <label>
              <span>User-facing value</span>
              <input
                value={drafts[row.id]?.proposedValue ?? ''}
                placeholder="Isi istilah lapangan, nilai, koneksi, atau catatan bay"
                onChange={(event) => onDraftChange(row.id, { proposedValue: event.target.value })}
              />
            </label>
            <div className="proposal-grid">
              <label>
                <span>Filled by</span>
                <select
                  value={drafts[row.id]?.role ?? 'transmission_user'}
                  onChange={(event) => onDraftChange(row.id, { role: event.target.value })}
                >
                  <option value="transmission_user">Transmission user</option>
                  <option value="generator_engineer">Generator engineer</option>
                  <option value="protection_engineer">Protection engineer</option>
                  <option value="model_engineer">Model engineer</option>
                </select>
              </label>
              <label>
                <span>Write mode</span>
                <select
                  value={drafts[row.id]?.saveMode ?? 'review_overlay'}
                  onChange={(event) =>
                    onDraftChange(row.id, {
                      saveMode: event.target.value as GapDraft['saveMode'],
                    })
                  }
                >
                  <option value="review_overlay">Review overlay</option>
                  <option value="confirmed_import">Confirmed import</option>
                </select>
              </label>
            </div>
            <label>
              <span>Evidence</span>
              <textarea
                rows={2}
                value={drafts[row.id]?.evidence ?? ''}
                placeholder="Contoh: halaman SLD PDF, field confirmation, nameplate, atau VSD"
                onChange={(event) => onDraftChange(row.id, { evidence: event.target.value })}
              />
            </label>
          </div>
        </article>
      ))}
    </section>
  );
}

function SourceMapping({ result }: { result: InspectResult }) {
  const rows = result.source_mapping ?? [];
  return (
    <section className="source-mapping">
      {rows.map((row) => (
        <article key={row.source} className="source-row">
          <div className="source-title">
            <strong>{row.source}</strong>
            <span>{row.records}</span>
          </div>
          <p>{row.fills}</p>
          <div className="source-meta">
            <span>{row.status}</span>
            <code>{row.parser}</code>
          </div>
        </article>
      ))}
    </section>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
