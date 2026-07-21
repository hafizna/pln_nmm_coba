"""
Command-line entry point.

Usage:

    python -m pln_nmm.cli roundtrip <input.xml> <output.xml> [--mode preserve|standard]
    python -m pln_nmm.cli inspect <input.xml>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import export_pln_eq, extract_pln_extensions, import_pln_eq
from .diagnostics import diagnose_pln_eq, summarize_top_placeholders


def cmd_roundtrip(args: argparse.Namespace) -> int:
    src = Path(args.input)
    dst = Path(args.output)
    mode = "preserve_extensions" if args.mode == "preserve" else "standard_cgmes"

    result = import_pln_eq(src)
    stats = export_pln_eq(result, dst, mode=mode)

    print(f"Imported {len(result.topology)} objects from {src}")
    print(f"Extensions: {result.extensions_report}")
    print(f"Wrote {dst} ({dst.stat().st_size:,} bytes)")
    print(f"Stats: {stats}")
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    src = Path(args.input)
    extensions = extract_pln_extensions(src)
    diagnostics = diagnose_pln_eq(src)

    print(f"File: {src}")
    print(f"Size: {src.stat().st_size:,} bytes")
    print(f"Extension report: {extensions}")
    print(f"Diagnostics: {diagnostics}")

    if diagnostics.placeholders:
        print()
        print("Unresolved template fields:")
        for field, count in summarize_top_placeholders(diagnostics):
            print(f"  {field:<36} {count}")
        print()
        print("Semantic cimpy import skipped until template placeholders are filled.")
        return 0

    result = import_pln_eq(src)
    print(f"Total cimpy objects: {len(result.topology)}")
    print()
    print("Class distribution:")
    for cls, n in sorted(result.class_counts().items(), key=lambda x: -x[1]):
        print(f"  {cls:<28} {n}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pln_nmm")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_round = sub.add_parser("roundtrip", help="Import then re-export a CIM EQ file")
    p_round.add_argument("input")
    p_round.add_argument("output")
    p_round.add_argument(
        "--mode",
        choices=["preserve", "standard"],
        default="preserve",
        help="preserve = reattach plnicp/nhftui (default); standard = clean CGMES",
    )
    p_round.set_defaults(func=cmd_roundtrip)

    p_inspect = sub.add_parser("inspect", help="Print a summary of a CIM EQ file")
    p_inspect.add_argument("input")
    p_inspect.set_defaults(func=cmd_inspect)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
