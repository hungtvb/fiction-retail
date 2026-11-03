"""Index one English Markdown guide per original product into the v0.4 sidecar."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sqlite3

from scripts.build_v03 import BASELINE_HASH, sha

VERSION = 'fiction-retail-extension-v0.4.0'
PARENT_VERSION = 'fiction-retail-extension-v0.3.0'


def scan_product_guides(source: sqlite3.Connection, knowledge: Path) -> list[dict]:
    """Require exactly one distinct, editable guide for each source product ID."""
    root = Path(knowledge).resolve()
    expected = {row[0] for row in source.execute('SELECT product_id FROM products')}
    found: dict[str, dict] = {}
    hashes: set[str] = set()
    for path in sorted((root / 'products').rglob('*.md')):
        product_id = path.stem
        if product_id in found:
            raise ValueError(f'Duplicate product guide for {product_id}')
        body = path.read_text(encoding='utf-8')
        if not body.startswith('# ') or '\n## ' not in body:
            raise ValueError(f'Product guide lacks title or sections: {path}')
        digest = sha(path)
        if digest in hashes:
            raise ValueError(f'Duplicate product guide content: {path}')
        hashes.add(digest)
        found[product_id] = {'product_id': product_id,
                             'relative_path': path.relative_to(root).as_posix(),
                             'sha256': digest}
    missing = expected - found.keys()
    extra = found.keys() - expected
    if missing or extra:
        raise ValueError(f'Missing {len(missing)} or extra {len(extra)} product guides; '
                         f'examples: {sorted(missing)[:3]} {sorted(extra)[:3]}')
    return [found[pid] for pid in sorted(expected)]


def build(source_path: Path, v03_path: Path, knowledge: Path, output: Path) -> dict:
    source_path, v03_path, knowledge, output = map(
        lambda p: Path(p).resolve(), (source_path, v03_path, knowledge, output))
    if source_path == output or v03_path == output or source_path == v03_path:
        raise ValueError('Source, parent runtime, and output must be different files')
    if not source_path.is_file() or sha(source_path) != BASELINE_HASH:
        raise ValueError('Canonical source hash mismatch')
    if not v03_path.is_file() or not knowledge.is_dir():
        raise FileNotFoundError('v0.3 runtime and knowledge directory are required')
    if output.exists():
        raise FileExistsError(output)
    with sqlite3.connect(f'file:{source_path.as_posix()}?mode=ro', uri=True) as source, \
         sqlite3.connect(f'file:{v03_path.as_posix()}?mode=ro', uri=True) as parent:
        meta = dict(parent.execute('SELECT key,value FROM metadata'))
        if meta.get('version') != PARENT_VERSION or meta.get('baseline_sha256') != BASELINE_HASH:
            raise ValueError('v0.3 version or source lineage mismatch')
        if parent.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('Invalid v0.3 SQLite')
        guides = scan_product_guides(source, knowledge)
        existing = {r[0]: (r[1], r[2]) for r in parent.execute('''
            SELECT product_id,relative_path,sha256 FROM knowledge_documents
            WHERE kind='product_guide' ''')}
        if len(existing) != 50:
            raise ValueError(f'Expected 50 curated v0.3 guides, found {len(existing)}')
        for guide in guides:
            if guide['product_id'] in existing and existing[guide['product_id']] != (
                    guide['relative_path'], guide['sha256']):
                raise ValueError(f'Curated guide changed without v0.3 rebuild: {guide["product_id"]}')
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(v03_path, output)
    with sqlite3.connect(output) as db:
        db.execute('PRAGMA foreign_keys=ON')
        for guide in guides:
            if guide['product_id'] in existing:
                continue
            document_id = 'DOC-' + sha256(guide['product_id'].encode()).hexdigest()[:24]
            db.execute('INSERT INTO knowledge_documents VALUES (?,?,?,?,?,?,?)',
                       (document_id, guide['product_id'], None, 'product_guide',
                        guide['relative_path'], guide['sha256'], 'scenario_generated'))
        for key, value in {
            'version': VERSION,
            'parent_version': PARENT_VERSION,
            'parent_v03_sha256': sha(v03_path),
            'product_guide_count': str(len(guides)),
            'product_guide_source': 'individual_markdown_files',
            'product_guide_provenance': 'scenario_generated; fictional catalog interpretation',
        }.items():
            db.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)', (key, value))
        db.commit()
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or \
           db.execute('PRAGMA foreign_key_check').fetchall():
            raise ValueError('v0.4 SQLite integrity failure')
        if db.execute("SELECT count(*) FROM knowledge_documents WHERE kind='product_guide'").fetchone()[0] != len(guides):
            raise ValueError('Product guide index is incomplete')
        db.execute('VACUUM')
    manifest = {
        'dataset_version': VERSION,
        'source_baseline_sha256': BASELINE_HASH,
        'parent_v03_sha256': sha(v03_path),
        'runtime_sha256': sha(output),
        'runtime_db': output.name,
        'product_guide_count': len(guides),
        'knowledge_document_count': len(guides) + 3,
        'guide_index_sha256': sha256(''.join(
            g['product_id'] + g['sha256'] for g in guides).encode()).hexdigest(),
        'answer_labels_in_runtime': False,
    }
    (output.parent / 'v04_manifest.json').write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--v03', required=True, type=Path)
    parser.add_argument('--knowledge', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.v03, args.knowledge, args.output), indent=2))


if __name__ == '__main__':
    main()
