"""Rebuild Fiction Retail from its immutable source and authored guides.

The 2024 v0.1–v0.4 stages are internal inputs; --unified publishes the
standalone November 2026 SQLite and RAG release.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import tempfile

from scripts.generate_extension import generate
from scripts.build_v02 import build as build_v02
from scripts.build_v03 import build as build_v03
from scripts.build_v04 import build as build_v04
from scripts.build_unified import build as build_unified_release


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


def rebuild_unified(source: Path, product_guides: Path,
                    output_dir: Path) -> dict:
    """Reuse v0.1→v0.4 builders, then normalize into one released database."""
    source, product_guides, output_dir = (
        Path(p).resolve() for p in (source, product_guides, output_dir))
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError('Output directory must be empty')
    if not product_guides.is_dir():
        raise FileNotFoundError(product_guides)
    with tempfile.TemporaryDirectory(prefix='fiction-rebuild-') as temp:
        work = Path(temp)
        parent = work / 'legacy'
        rebuilt = rebuild(source, parent)
        knowledge = Path(rebuilt['knowledge'])
        shutil.copytree(product_guides, knowledge / 'products', dirs_exist_ok=True)
        v04 = work / 'fiction_runtime_v04.sqlite'
        build_v04(source, Path(rebuilt['runtime']), knowledge, v04)
        return build_unified_release(source, v04, knowledge, output_dir)



def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--unified', action='store_true',
                        help='Build the standalone November 2026 release')
    parser.add_argument('--product-guides', type=Path,
                        help='Directory containing the 5,000 authored Markdown guides')
    args = parser.parse_args()
    if args.unified:
        if not args.product_guides:
            parser.error('--unified requires --product-guides')
        result = rebuild_unified(args.source, args.product_guides,
                                 args.output_dir)
    else:
        result = rebuild(args.source, args.output_dir)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
