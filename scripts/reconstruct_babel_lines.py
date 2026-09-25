"""Produce an explicit assumption manifest and a review model, never edit input.

Example: python scripts/reconstruct_babel_lines.py inventory.json output_dir
         --assume-double-bus --demo-scenario
Use --manifest reviewed.json to choose profiles/bays/optional devices explicitly.
"""
import argparse
import json
from pathlib import Path

from pln_nmm.model.line_bay import PROFILE, propose_line_bays, reconstruct_line_bays
from pln_nmm.model.line_review import render_review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inventory', type=Path)
    parser.add_argument('output', type=Path)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--assume-double-bus', action='store_true')
    choice.add_argument('--manifest', type=Path)
    parser.add_argument('--demo-scenario', action='store_true')
    args = parser.parse_args()
    inventory = json.loads(args.inventory.read_text(encoding='utf-8'))
    if args.manifest:
        manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    else:
        selections = propose_line_bays(inventory)
        manifest = {'quality': 'ASSUMED', 'reason': 'User-authorized line-bay reconstruction',
                    'gi_profiles': {s['gi_id']: PROFILE for s in selections},
                    'selections': selections}
    model = reconstruct_line_bays(inventory, manifest['selections'], manifest['gi_profiles'],
                                  demo_scenario=args.demo_scenario)
    # Avoid accidentally overwriting reviewed work or the source inventory.
    args.output.mkdir(parents=True, exist_ok=True)
    paths = [args.output / f for f in ('assumptions.json', 'line_model.json', 'review.html')]
    if any(p.exists() for p in paths):
        parser.error('Output exists; choose a fresh output directory to preserve reviewed work.')
    paths[0].write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    paths[1].write_text(json.dumps(model, indent=2, ensure_ascii=False), encoding='utf-8')
    reopened = json.loads(paths[1].read_text(encoding='utf-8'))
    paths[2].write_text(render_review(reopened), encoding='utf-8')
    print(json.dumps(model['counts'], indent=2))
    print(f'Review: {paths[2].resolve()}')


if __name__ == '__main__':
    main()
