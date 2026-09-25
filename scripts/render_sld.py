"""Render whatever the SLD parser actually reads, as a standalone SVG.

Deliberately unpolished. This draws the parsed graph as-is -- including
auto-grid positions when the CIM carries no plnicp coordinates -- so topology
faults stay visible instead of being hidden by a tidy layout.

Usage:
    python scripts/render_sld.py out/bali_EQ.xml out/bali_sld.svg
"""

from __future__ import annotations

import collections
import sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pln_nmm.sld import extract_sld_model  # noqa: E402

# Colour by CIM class so the drawing reads without a legend lookup.
STYLE = {
    "BusbarSection": ("#1f3864", 9, "rect"),
    "Breaker": ("#c00000", 7, "rect"),
    "Disconnector": ("#ed7d31", 5, "diamond"),
    "ConnectivityNode": ("#7f7f7f", 3, "circle"),
    "ACLineSegment": ("#2e7d32", 5, "circle"),
    "EnergyConsumer": ("#7030a0", 6, "triangle"),
    "PowerTransformer": ("#0070c0", 8, "circle"),
    "SynchronousMachine": ("#008080", 8, "circle"),
}
DEFAULT_STYLE = ("#404040", 4, "circle")


def _shape(x: float, y: float, colour: str, size: int, kind: str, title: str) -> str:
    t = f"<title>{escape(title)}</title>"
    if kind == "rect":
        return (
            f'<rect x="{x - size:.1f}" y="{y - size / 2:.1f}" width="{size * 2}" '
            f'height="{size}" fill="{colour}">{t}</rect>'
        )
    if kind == "diamond":
        return (
            f'<polygon points="{x:.1f},{y - size:.1f} {x + size:.1f},{y:.1f} '
            f'{x:.1f},{y + size:.1f} {x - size:.1f},{y:.1f}" fill="{colour}">{t}</polygon>'
        )
    if kind == "triangle":
        return (
            f'<polygon points="{x:.1f},{y + size:.1f} {x + size:.1f},{y - size:.1f} '
            f'{x - size:.1f},{y - size:.1f}" fill="{colour}">{t}</polygon>'
        )
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{size}" fill="{colour}">{t}</circle>'


def render(xml_path: str | Path, out_path: str | Path) -> dict:
    model = extract_sld_model(xml_path)
    pos = {n.id: (n.x, n.y) for n in model.nodes}
    by_id = {n.id: n for n in model.nodes}

    xs = [n.x for n in model.nodes] or [0.0]
    ys = [n.y for n in model.nodes] or [0.0]
    pad = 60.0
    min_x, max_x = min(xs) - pad, max(xs) + pad
    min_y, max_y = min(ys) - pad, max(ys) + pad
    w, h = max_x - min_x, max_y - min_y

    # How many edges land on each node: the degree-56 node should be obvious.
    degree: collections.Counter = collections.Counter()
    for e in model.edges:
        degree[e.source] += 1
        degree[e.target] += 1

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{min_x:.0f} {min_y:.0f} '
        f'{w:.0f} {h:.0f}" width="{min(w, 2400):.0f}">',
        '<rect x="%.0f" y="%.0f" width="%.0f" height="%.0f" fill="#fbfbfd"/>'
        % (min_x, min_y, w, h),
        "<g stroke='#b8b8c0' stroke-width='1' opacity='0.75'>",
    ]

    for e in model.edges:
        a, b = pos.get(e.source), pos.get(e.target)
        if a and b:
            parts.append(
                f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" '
                f'x2="{b[0]:.1f}" y2="{b[1]:.1f}"/>'
            )
    parts.append("</g>")

    for n in model.nodes:
        colour, size, kind = STYLE.get(n.cim_class, DEFAULT_STYLE)
        d = degree.get(n.id, 0)
        # Flag any node that swallows an implausible number of connections.
        if n.cim_class == "ConnectivityNode" and d > 40:
            parts.append(
                f'<circle cx="{n.x:.1f}" cy="{n.y:.1f}" r="{size + 14}" '
                'fill="none" stroke="#d40000" stroke-width="2.5"/>'
            )
            colour = "#d40000"
        title = f"{n.cim_class}: {n.label} (derajat {d})"
        parts.append(_shape(n.x, n.y, colour, size, kind, title))

    counts = collections.Counter(n.cim_class for n in model.nodes)
    legend_x, legend_y = min_x + 20, min_y + 26
    parts.append(
        f'<text x="{legend_x}" y="{legend_y}" font-family="system-ui,sans-serif" '
        f'font-size="15" font-weight="700" fill="#1f3864">'
        f"Parsed SLD — {len(model.nodes)} objek, {len(model.edges)} sambungan</text>"
    )
    for i, (cls, n) in enumerate(counts.most_common()):
        colour, size, kind = STYLE.get(cls, DEFAULT_STYLE)
        y = legend_y + 24 + i * 19
        parts.append(_shape(legend_x + 7, y - 4, colour, size, kind, cls))
        parts.append(
            f'<text x="{legend_x + 24}" y="{y}" font-family="system-ui,sans-serif" '
            f'font-size="13" fill="#333">{escape(cls)} — {n}</text>'
        )

    over = [k for k, v in degree.items() if v > 40 and by_id.get(k) and by_id[k].cim_class == "ConnectivityNode"]
    if over:
        y = legend_y + 24 + len(counts) * 19 + 12
        parts.append(
            f'<text x="{legend_x}" y="{y}" font-family="system-ui,sans-serif" '
            f'font-size="13" font-weight="700" fill="#d40000">'
            f"{len(over)} node dilingkari merah: menampung &gt;40 sambungan</text>"
        )

    parts.append("</svg>")

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")

    with_coords = sum(1 for n in model.nodes if n.has_coordinates)
    return {
        "nodes": len(model.nodes),
        "edges": len(model.edges),
        "classes": dict(counts),
        "with_coordinates": with_coords,
        "oversized": len(over),
        "max_degree": max(degree.values()) if degree else 0,
    }


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    info = render(argv[1], argv[2])
    print(f"objek           : {info['nodes']}")
    print(f"sambungan       : {info['edges']}")
    print(f"punya koordinat : {info['with_coordinates']}/{info['nodes']}")
    print(f"derajat maksimum: {info['max_degree']}")
    if info["oversized"]:
        print(f"node >40 sambungan: {info['oversized']} (dilingkari merah)")
    print()
    for cls, n in sorted(info["classes"].items(), key=lambda x: -x[1]):
        print(f"  {n:5d}  {cls}")
    print()
    print(f"Ditulis ke {argv[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
