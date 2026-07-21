# Antigravity (Gemini) config for pln_nmm_coba

This file is read by Google's Antigravity IDE and Gemini-based agents.
It mirrors the conventions documented in `CLAUDE.md` and `AGENTS.md` at
the repo root; refer to those for the canonical project description.

## Quick reference

- Language: Python 3.10+
- Test runner: `pytest` (31 tests in `tests/`)
- Entry point: `python -m pln_nmm.cli` or `python examples/roundtrip_demo.py`
- Core module: `src/pln_nmm/adapter.py` (~250 lines, read this first)

## Project rules in 5 lines

1. Do not modify `cimpy` (third-party Apache 2.0 dep).
2. SLD-first; switching equipment stays schematic unless supported by source evidence.
3. Match elements by `rdf:ID` stripped of leading underscore.
4. Float coordinates round-trip via `repr()`, bit-exact.
5. Permissive licenses only (MIT/BSD/Apache); no GPL/AGPL.

See `../CLAUDE.md` for the full version.
