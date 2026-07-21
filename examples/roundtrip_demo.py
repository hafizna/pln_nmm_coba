"""
Round-trip demonstration script.

Reads the bundled sample EQ file, imports it through cimpy with the PLN
extension adapter, exports it back in both modes, and prints a small
summary that you can compare against the original by eye.

Run from the project root with:

    python examples/roundtrip_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make src/ importable when running this script directly without installing
# the package.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from pln_nmm import export_pln_eq, import_pln_eq  # noqa: E402


def main() -> int:
    sample = ROOT / "tests" / "fixtures" / "sample_EQ.xml"
    out_dir = ROOT / "examples" / "out"
    out_dir.mkdir(exist_ok=True)

    if not sample.exists():
        print(f"Sample file missing: {sample}", file=sys.stderr)
        return 1

    print(f"Reading {sample.relative_to(ROOT)}")
    print(f"  size: {sample.stat().st_size:,} bytes")

    result = import_pln_eq(sample)
    print(f"\nImport summary:")
    print(f"  cimpy objects: {len(result.topology)}")
    print(f"  extensions:    {result.extensions_report}")

    print(f"\nClass distribution:")
    for cls, n in sorted(result.class_counts().items(), key=lambda x: -x[1]):
        print(f"  {cls:<28} {n}")

    preserve_path = out_dir / "roundtrip_preserve.xml"
    standard_path = out_dir / "roundtrip_standard.xml"

    p_stats = export_pln_eq(result, preserve_path, mode="preserve_extensions")
    s_stats = export_pln_eq(result, standard_path, mode="standard_cgmes")

    print(f"\nExport (preserve_extensions): {preserve_path.relative_to(ROOT)}")
    print(f"  size: {preserve_path.stat().st_size:,} bytes")
    print(f"  reinjected: x={p_stats['x_reinjected']} y={p_stats['y_reinjected']} "
          f"nhftui={p_stats['nhftui_reinjected']}")

    print(f"\nExport (standard_cgmes):      {standard_path.relative_to(ROOT)}")
    print(f"  size: {standard_path.stat().st_size:,} bytes")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
