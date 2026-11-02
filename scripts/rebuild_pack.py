"""Rebuild the Fiction Retail business data from an immutable baseline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.generate_extension import generate
from scripts.build_v02 import build as build_v02
from scripts.build_v03 import build as build_v03


def rebuild(source: Path, output_dir: Path) -> dict:
    source = source.resolve()
    output_dir = output_dir.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if output_dir == source.parent or output_dir in source.parents:
        raise ValueError('Output directory must not be the source directory or its ancestor')
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError('Output directory must be empty; refuse destructive rebuild')
    output_dir.mkdir(parents=True, exist_ok=True)
    data = output_dir / 'data'
    data.mkdir()
    v01 = data / 'fiction_extension_v01.sqlite'
    v02 = data / 'fiction_extension_v02.sqlite'
    v03 = data / 'fiction_runtime_v03.sqlite'
    knowledge = output_dir / 'knowledge'
    generate(source, v01)
    build_v02(source, v01, v02, knowledge)
    manifest = build_v03(source, v02, v03, knowledge)
    return {'runtime': str(v03), 'knowledge': str(knowledge),
            'manifest': str(data / 'v03_manifest.json'),
            'source_sha256': manifest['source_baseline_sha256'],
            'runtime_sha256': manifest['runtime_sha256']}



def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(rebuild(args.source, args.output_dir), indent=2))


if __name__ == '__main__':
    main()
