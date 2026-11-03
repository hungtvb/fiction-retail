"""Legacy v0.4 packager and shared chunk helpers.

The published unified release is built by scripts.build_unified via
scripts.rebuild_pack --unified; this module retains historical 2024 inputs.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3

from scripts.build_v03 import BASELINE_HASH

SOURCE_URL = 'https://github.com/datahub-project/static-assets/tree/main/datasets/fiction-retail'
TABLE_PURPOSES = {
    'customers': 'Customer identities, locations and segment labels; contains personal data.',
    'orders': 'Order header, customer, order date, status and recorded USD order total.',
    'order_items': 'Line items with quantity, transaction unit price and percentage discount.',
    'products': 'Original imported catalog; price and weight have no effective dates.',
    'suppliers': 'Supplier identity, country, contract start and status.',
    'inventory': 'Undated inventory snapshot; it cannot prove stock at a historical order date or today.',
    'warehouses': 'Warehouse locations and nominal capacity.',
    'shipments': 'Shipment status and recorded shipping and delivery dates.',
    'returns': 'Recorded returns and refund amounts; payment completion is not established.',
    'promotions': 'Promotion definitions and validity windows.',
    'product_enrichment': 'Fictional merchandising interpretation for 50 original product IDs, with May 2024 dated offers.',
    'knowledge_documents': 'Links product and policy IDs to Markdown files and content hashes.',
    'product_pricing_constraints': 'Synthetic May 2024 costs, margin floors and discount caps for 20 products.',
    'fulfillment_cases': 'One hundred scoped synthetic backorder investigation cases.',
    'inventory_snapshots_v2': 'Case-specific synthetic timestamped stock evidence; not a global inventory ledger.',
    'inventory_movements_v2': 'Synthetic movements associated with selected cases.',
    'warehouse_eligibility': 'Case-specific synthetic warehouse eligibility.',
    'operational_events': 'Synthetic order and evidence event timeline.',
    'sales_opportunities': 'Synthetic assisted-sales opportunities linked to historical IDs when won.',
    'sales_activities': 'Synthetic advisor activities for opportunities.',
    'sales_targets': 'Synthetic April 2024 advisor targets.',
}
VALIDITY = {
    'FR-RET-2024-04': ('2024-04-01', '2024-05-01'),
    'FR-WH-2024-04': ('2024-04-01', '2024-05-01'),
    'FR-PRICE-2024-05': ('2024-05-01', '2024-06-01'),
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def chunk(kind: str, source_id: str, text: str, source_ref: str, provenance: str,
          valid_from: str | None = None, valid_to: str | None = None,
          metadata: dict | None = None) -> dict:
    key = f'{kind}:{source_id}'
    return {
        'chunk_id': hashlib.sha256(key.encode()).hexdigest()[:24],
        'kind': kind, 'source_id': source_id, 'source_ref': source_ref,
        'provenance': provenance, 'valid_from': valid_from, 'valid_to': valid_to,
        'text': text, 'text_sha256': hashlib.sha256(text.encode()).hexdigest(),
        'metadata': metadata or {},
    }


def markdown_sections(body: str) -> list[tuple[str, str]]:
    """Split on headings while retaining title, opening metadata and FAQ parent."""
    title = ''
    opening: list[str] = []
    heading: list[str] = []
    lines: list[str] = []
    sections: list[tuple[str, str]] = []

    def flush() -> None:
        content = '\n'.join(lines).strip()
        if content:
            label = ' / '.join(heading) if heading else 'Overview'
            prefix = '\n'.join(x for x in [title, *opening] if x).strip()
            section_title = '\n'.join(f'{"#" * (i + 2)} {part}' for i, part in enumerate(heading))
            sections.append((label, f'{prefix}\n\n{section_title}\n{content}'.strip()))

    for line in body.splitlines():
        if line.startswith('# ') and not title:
            title = line
        elif line.startswith('## '):
            flush()
            heading = [line[3:].strip()]
            lines = []
        elif line.startswith('### '):
            flush()
            heading = heading[:1] + [line[4:].strip()]
            lines = []
        elif heading:
            lines.append(line)
        else:
            opening.append(line)
    flush()
    if not sections and (title or opening):
        sections.append(('Document', body.strip()))
    return sections


def verified_documents(runtime: sqlite3.Connection, knowledge: Path):
    root = knowledge.resolve()
    rows = runtime.execute('''SELECT document_id,product_id,policy_id,kind,relative_path,sha256,provenance
                              FROM knowledge_documents ORDER BY relative_path''')
    for document_id, product_id, policy_id, kind, relative_path, expected, provenance in rows:
        path = (root / relative_path).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f'Missing or unsafe knowledge path: {relative_path}')
        if digest(path) != expected:
            raise ValueError(f'Knowledge hash mismatch: {relative_path}')
        yield {'document_id': document_id, 'product_id': product_id, 'policy_id': policy_id,
               'kind': kind, 'relative_path': relative_path, 'provenance': provenance,
               'body': path.read_text(encoding='utf-8')}


def make_product_chunks(source: sqlite3.Connection, runtime: sqlite3.Connection):
    curated = {r[0]: r[1:] for r in runtime.execute('''SELECT product_id,synthetic_display_name,
        curated_list_price_usd,curated_shipping_weight_kg,catalog_effective_from,
        catalog_effective_to,provenance FROM product_enrichment''')}
    for product_id, name, category, brand, price, weight, supplier_id in source.execute('''
            SELECT product_id,name,category,brand,price,weight_kg,supplier_id
            FROM products ORDER BY product_id'''):
        raw = (f'Original imported product record. Product ID: {product_id}. '
               f'Import name: {name}. Category: {category}. Brand: {brand}. '
               f'Import price: USD {Decimal(str(price)):.2f}. Import weight: {weight} kg. '
               f'Supplier ID: {supplier_id}. Import price and weight have no effective dates; '
               'this record does not establish a current offer or verified product specifications.')
        yield chunk('source_product', product_id, raw, f'sqlite:source.products:{product_id}',
                    'upstream_source', metadata={'product_id': product_id, 'category': category})
        if product_id in curated:
            display, list_price, packed_weight, start, end, provenance = curated.pop(product_id)
            if not start or not end or start >= end or provenance != 'scenario_generated':
                raise ValueError(f'Invalid curated offer: {product_id}')
            text = (f'Fictional curated offer for original product ID {product_id}. '
                    f'Display name: {display}. Category: {category}. '
                    f'List price: USD {list_price}. Packed shipping weight: {packed_weight} kg. '
                    f'Valid from {start} inclusive to {end} exclusive. '
                    'These are synthetic merchandising values, not historical transaction facts.')
            yield chunk('curated_offer', product_id, text,
                        f'sqlite:extension.product_enrichment:{product_id}', provenance,
                        start, end, {'product_id': product_id, 'category': category,
                                     'display_name': display})
    if curated:
        raise ValueError(f'Curated product IDs missing from source: {sorted(curated)}')


def make_document_chunks(runtime: sqlite3.Connection, knowledge: Path):
    for doc in verified_documents(runtime, knowledge):
        if doc['kind'] == 'business_policy':
            start, end = VALIDITY[doc['policy_id']]
            sections = markdown_sections(doc['body'])
        else:
            start, end = '2024-05-01', '2024-06-01'
            sections = [('Complete product guide', doc['body'].strip())]
        for number, (section, text) in enumerate(sections, 1):
            source_id = f"{doc['document_id']}:{number:02d}"
            yield chunk(doc['kind'], source_id, text,
                        f"knowledge/{doc['relative_path']}#{number}", doc['provenance'],
                        start, end,
                        {'document_id': doc['document_id'], 'product_id': doc['product_id'],
                         'policy_id': doc['policy_id'], 'section': section})


def make_schema_chunks(source: sqlite3.Connection, runtime: sqlite3.Connection):
    for alias, db, provenance in [('source', source, 'upstream_source'),
                                  ('extension', runtime, 'scenario_generated')]:
        names = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        for name in names:
            columns = [(r[1], r[2]) for r in db.execute(f'PRAGMA table_info("{name}")')]
            count = db.execute(f'SELECT count(*) FROM "{name}"').fetchone()[0]
            description = TABLE_PURPOSES.get(name, 'See the table columns and the data contract for scope.')
            body = (f'SQL table {alias}.{name}. {description} Snapshot rows: {count}. '
                    'Columns: ' + ', '.join(f'{col} ({typ})' for col, typ in columns) + '.')
            yield chunk('table_schema', f'{alias}.{name}', body, f'sqlite:{alias}.{name}',
                        provenance, metadata={'database': alias, 'table': name, 'row_count': count})


def build(source_path: Path, runtime_path: Path, knowledge: Path, output_dir: Path) -> dict:
    source_path, runtime_path, knowledge, output_dir = map(
        lambda p: Path(p).resolve(), (source_path, runtime_path, knowledge, output_dir))
    if not source_path.is_file() or digest(source_path) != BASELINE_HASH:
        raise ValueError('Canonical source database SHA-256 mismatch')
    if not runtime_path.is_file() or not knowledge.is_dir():
        raise FileNotFoundError('v0.4 runtime and knowledge directory are required')
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError('Output directory must be empty')
    if output_dir == source_path.parent or output_dir in source_path.parents:
        raise ValueError('Output cannot replace source directory')
    with sqlite3.connect(f'file:{source_path.as_posix()}?mode=ro', uri=True) as source, \
         sqlite3.connect(f'file:{runtime_path.as_posix()}?mode=ro', uri=True) as runtime:
        version = runtime.execute("SELECT value FROM metadata WHERE key='version'").fetchone()
        origin = runtime.execute("SELECT value FROM metadata WHERE key='baseline_sha256'").fetchone()
        if version != ('fiction-retail-extension-v0.4.0',) or origin != (BASELINE_HASH,):
            raise ValueError('Runtime version or source lineage mismatch')
        if source.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or \
           runtime.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('SQLite integrity check failed')
        chunks = list(make_product_chunks(source, runtime))
        chunks.extend(make_document_chunks(runtime, knowledge))
        chunks.extend(make_schema_chunks(source, runtime))
    identifiers = [c['chunk_id'] for c in chunks]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError('Duplicate RAG chunk ID')
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'data').mkdir()
    (output_dir / 'rag').mkdir()
    shutil.copyfile(source_path, output_dir / 'data' / 'fiction-retail.db')
    shutil.copyfile(runtime_path, output_dir / 'data' / 'fiction_runtime_v04.sqlite')
    shutil.copytree(knowledge, output_dir / 'knowledge')
    corpus = output_dir / 'rag' / 'chunks.jsonl'
    with corpus.open('w', encoding='utf-8', newline='\n') as stream:
        for item in chunks:
            stream.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + '\n')
    counts = dict(sorted(Counter(c['kind'] for c in chunks).items()))
    manifest = {
        'pack_version': 'fiction-retail-agent-dataset-v2',
        'upstream_url': SOURCE_URL,
        'source_sha256': digest(output_dir / 'data' / 'fiction-retail.db'),
        'runtime_sha256': digest(output_dir / 'data' / 'fiction_runtime_v04.sqlite'),
        'rag_sha256': digest(corpus),
        'rag_chunk_count': len(chunks), 'rag_chunks_by_kind': counts,
        'knowledge_document_count': len(list((output_dir / 'knowledge').rglob('*.md'))),
        'source_table_count': 10, 'source_product_count': counts.get('source_product', 0),
        'curated_product_count': counts.get('curated_offer', 0),
        'classification': 'Synthetic educational data; extension and business documents are scenario_generated',
    }
    (output_dir / 'manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--runtime', required=True, type=Path)
    parser.add_argument('--knowledge', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.runtime, args.knowledge, args.output_dir), indent=2))


if __name__ == '__main__':
    main()
