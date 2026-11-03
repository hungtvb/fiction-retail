"""Build the standalone, time-rebased Fiction Retail SQLite and RAG release.

Inputs are the immutable DataHub source, the deterministic v0.4 extension, and
the individually authored product guides. No upstream or input file is edited.
"""
from __future__ import annotations

import argparse
from calendar import month_name
from collections import Counter
from contextlib import closing
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import sqlite3

from scripts.build_agent_dataset import (BASELINE_HASH, SOURCE_URL,
    TABLE_PURPOSES, chunk, digest, markdown_sections)
from scripts.business_policies import POLICY_RETURNS, POLICY_TRANSFER, POLICY_PRICING


VERSION = 'fiction-retail-unified-v1.0.0'
TRANSFORMATION_VERSION = 'november-2026-rebase-v1'
AS_OF_DATE = date(2026, 11, 3)
BUSINESS_TIMEZONE = 'Asia/Ho_Chi_Minh'
EVENT_FIELDS = {
    'customers': ('signup_date',), 'orders': ('order_date',),
    'shipments': ('shipped_date', 'delivered_date'),
    'returns': ('return_date',), 'inventory': ('last_restocked_date',),
    'warehouses': ('opened_date',), 'suppliers': ('contract_start_date',),
    'employees': ('hire_date',),
    'sales_opportunities': ('opened_at', 'closed_at'),
    'sales_activities': ('occurred_at',),
    'fulfillment_cases': ('case_date',),
    'fulfillment_events': ('event_time',),
    'inventory_observations': ('observed_at',),
    'operational_events': ('occurred_at', 'recorded_at'),
    'inventory_snapshots_v2': ('observed_at', 'received_at'),
    'inventory_movements_v2': ('occurred_at',),
}
VALIDITY_FIELDS = {
    'promotions': ('valid_from', 'valid_until'),
    'product_enrichment': ('catalog_effective_from', 'catalog_effective_to'),
    'product_pricing_constraints': ('effective_from', 'effective_to'),
}
TEMPORAL_FIELDS = {**EVENT_FIELDS, **VALIDITY_FIELDS}
POLICY_IDS = {
    'FR-RET-2024-04': 'FR-RET-2026-10-04',
    'FR-WH-2024-04': 'FR-WH-2026-10-04',
    'FR-PRICE-2024-05': 'FR-PRICE-2026-11-03',
}
LEGACY_POLICIES = {
    'FR-RET-2024-04': POLICY_RETURNS,
    'FR-WH-2024-04': POLICY_TRANSFER,
    'FR-PRICE-2024-05': POLICY_PRICING,
}
POLICY_INTERVALS = {
    'FR-RET-2026-10-04': ('2026-10-04', '2026-11-03'),
    'FR-WH-2026-10-04': ('2026-10-04', '2026-11-03'),
    'FR-PRICE-2026-11-03': ('2026-11-03', '2026-12-04'),
}
SOURCE_KEYS = {
    'customers': 'customer_id', 'orders': 'order_id',
    'order_items': 'order_item_id', 'products': 'product_id',
    'suppliers': 'supplier_id', 'inventory': 'inventory_id',
    'warehouses': 'warehouse_id', 'shipments': 'shipment_id',
    'returns': 'return_id', 'promotions': 'promo_id',
}
EXTRA_FKS = {
    'sales_opportunities': [('customer_id', 'customers', 'customer_id'),
                            ('order_id', 'orders', 'order_id')],
    'fulfillment_cases': [('order_id', 'orders', 'order_id'),
                          ('order_item_id', 'order_items', 'order_item_id'),
                          ('product_id', 'products', 'product_id'),
                          ('assigned_warehouse_id', 'warehouses', 'warehouse_id')],
    'inventory_observations': [('product_id', 'products', 'product_id'),
                               ('warehouse_id', 'warehouses', 'warehouse_id')],
    'warehouse_eligibility': [('warehouse_id', 'warehouses', 'warehouse_id')],
    'inventory_snapshots_v2': [('product_id', 'products', 'product_id'),
                               ('warehouse_id', 'warehouses', 'warehouse_id')],
    'inventory_movements_v2': [('product_id', 'products', 'product_id'),
                               ('warehouse_id', 'warehouses', 'warehouse_id')],
    'product_enrichment': [('product_id', 'products', 'product_id')],
    'product_pricing_constraints': [('product_id', 'products', 'product_id')],
    'knowledge_documents': [('product_id', 'products', 'product_id')],
}
SOURCE_FKS = {
    'orders': [('customer_id', 'customers', 'customer_id'),
               ('promo_id', 'promotions', 'promo_id')],
    'order_items': [('order_id', 'orders', 'order_id'),
                    ('product_id', 'products', 'product_id')],
    'products': [('supplier_id', 'suppliers', 'supplier_id')],
    'inventory': [('product_id', 'products', 'product_id'),
                  ('warehouse_id', 'warehouses', 'warehouse_id')],
    'shipments': [('order_id', 'orders', 'order_id'),
                  ('warehouse_id', 'warehouses', 'warehouse_id')],
    'returns': [('order_id', 'orders', 'order_id'),
                ('product_id', 'products', 'product_id')],
}
INDEXES = (
    'CREATE INDEX idx_orders_customer ON orders(customer_id)',
    'CREATE INDEX idx_orders_date_status ON orders(order_date,order_status)',
    'CREATE INDEX idx_orders_status_date_amount ON orders(order_status,order_date,total_amount)',
    'CREATE INDEX idx_orders_promo ON orders(promo_id)',
    'CREATE INDEX idx_order_items_order_product ON order_items(order_id,product_id)',
    'CREATE INDEX idx_order_items_product ON order_items(product_id)',
    'CREATE UNIQUE INDEX idx_inventory_product_warehouse ON inventory(product_id,warehouse_id)',
    'CREATE INDEX idx_inventory_warehouse ON inventory(warehouse_id)',
    'CREATE INDEX idx_shipments_order ON shipments(order_id)',
    'CREATE INDEX idx_shipments_tracking ON shipments(tracking_number)',
    'CREATE INDEX idx_returns_order_product ON returns(order_id,product_id)',
    'CREATE INDEX idx_sales_opportunities_customer ON sales_opportunities(customer_id)',
)
LOAD_ORDER = (
    'customers', 'promotions', 'suppliers', 'warehouses', 'products',
    'orders', 'order_items', 'inventory', 'shipments', 'returns',
    'teams', 'employees', 'sales_opportunities', 'sales_activities',
    'sales_targets', 'fulfillment_policies', 'fulfillment_cases',
    'fulfillment_events', 'inventory_observations', 'warehouse_eligibility',
    'operational_events', 'inventory_snapshots_v2', 'inventory_movements_v2',
    'product_enrichment', 'product_pricing_constraints',
    'knowledge_documents', 'metadata',
)


def shift_date(value: str | None, days: int) -> str | None:
    """Shift only the ISO date prefix, preserving time, precision and UTC offset."""
    if value is None:
        return None
    if not re.match(r'^\d{4}-\d{2}-\d{2}(?:$|T)', value):
        raise ValueError(f'Not an ISO date or timestamp: {value}')
    return (date.fromisoformat(value[:10]) + timedelta(days=days)).isoformat() + value[10:]


def sku_for(product_id: str) -> str:
    """A source-ID-derived fictional SKU; collision is checked at build time."""
    return 'FR-' + sha256(product_id.encode('utf-8')).hexdigest()[:16].upper()


def q(name: str) -> str:
    if not re.fullmatch(r'[a-z][a-z0-9_]*', name):
        raise ValueError(f'Unsafe SQL identifier: {name}')
    return '"' + name + '"'


def tables(db: sqlite3.Connection) -> list[str]:
    return [r[0] for r in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name")]


def source_schema(src: sqlite3.Connection, table: str) -> str:
    key = SOURCE_KEYS[table]
    parts = []
    for row in src.execute(f'PRAGMA table_info({q(table)})'):
        name, kind = row[1], row[2]
        parts.append(f'{q(name)} {kind}' + (' NOT NULL' if name == key else ''))
    if table == 'products':
        parts.append('sku TEXT NOT NULL UNIQUE CHECK(length(sku)>0)')
    parts.append(f'PRIMARY KEY({q(key)})')
    for column, parent, parent_key in SOURCE_FKS.get(table, ()):
        parts.append(f'FOREIGN KEY({q(column)}) REFERENCES {q(parent)}({q(parent_key)})')
    return f'CREATE TABLE {q(table)} (' + ','.join(parts) + ')'


def extension_schema(ext: sqlite3.Connection, table: str) -> str:
    sql = ext.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                      (table,)).fetchone()[0].rstrip(';')
    extra = []
    if table == 'sales_targets':
        # Exact translated reporting window crosses calendar months.
        sql = sql.replace('PRIMARY KEY(employee_id,month,metric_key)',
                          'period_start TEXT NOT NULL, period_end TEXT NOT NULL, '
                          'PRIMARY KEY(employee_id,month,metric_key)')
    for column, parent, parent_key in EXTRA_FKS.get(table, ()):
        extra.append(f'FOREIGN KEY({q(column)}) REFERENCES {q(parent)}({q(parent_key)})')
    if extra:
        at = sql.rfind(')')
        sql = sql[:at] + ', ' + ', '.join(extra) + sql[at:]
    return sql


def latest_observed_date(src: sqlite3.Connection, ext: sqlite3.Connection) -> date:
    latest = date.min
    source_tables = set(tables(src))
    for table, fields in EVENT_FIELDS.items():
        db = src if table in source_tables else ext
        for field in fields:
            value = db.execute(f'SELECT max({q(field)}) FROM {q(table)}').fetchone()[0]
            if value:
                latest = max(latest, date.fromisoformat(value[:10]))
    return latest


def english_date(value: str) -> str:
    day = date.fromisoformat(value)
    return f'{day.day} {month_name[day.month]} {day.year}'


def write_policies(input_knowledge: Path, output_knowledge: Path, offset: int) -> dict[str, tuple[str, str]]:
    (output_knowledge / 'policies').mkdir(parents=True, exist_ok=True)
    result = {}
    for old_id, new_id in POLICY_IDS.items():
        old_path = input_knowledge / 'policies' / f'{old_id}.md'
        original = (old_path.read_text(encoding='utf-8') if old_path.is_file()
                    else LEGACY_POLICIES[old_id])
        start, end = POLICY_INTERVALS[new_id]
        expected_start = shift_date('2024-05-01' if 'PRICE' in old_id else '2024-04-01', offset)
        expected_end = shift_date('2024-06-01' if 'PRICE' in old_id else '2024-05-01', offset)
        if (start, end) != (expected_start, expected_end):
            raise ValueError(f'Policy interval does not match offset: {new_id}')
        original = original.replace(old_id, new_id)
        original, changes = re.subn(
            r'^\*\*Effective:\*\* .+$',
            f'**Effective:** {english_date(start)} – {english_date(shift_date(end, -1))}',
            original, count=1, flags=re.MULTILINE)
        if changes != 1:
            raise ValueError(f'Policy effective line missing: {old_id}')
        relative = f'policies/{new_id}.md'
        path = output_knowledge / relative
        path.write_text(original, encoding='utf-8', newline='\r\n')
        result[old_id] = (relative, digest(path))
    return result


def insert_table(src: sqlite3.Connection, ext: sqlite3.Connection,
                 out: sqlite3.Connection, table: str, offset: int,
                 policies: dict[str, tuple[str, str]]) -> tuple[int, int]:
    origin = src if table in SOURCE_KEYS else ext
    cursor = origin.execute(f'SELECT * FROM {q(table)} ORDER BY rowid')
    names = [col[0] for col in cursor.description]
    target_names = names + (['sku'] if table == 'products' else
                            ['period_start', 'period_end'] if table == 'sales_targets' else [])
    statement = (f'INSERT INTO {q(table)} (' + ','.join(map(q, target_names)) +
                 ') VALUES (' + ','.join('?' for _ in target_names) + ')')
    before = 0
    while rows := cursor.fetchmany(5000):
        converted = []
        for record in rows:
            row = dict(zip(names, record))
            for field in TEMPORAL_FIELDS.get(table, ()):
                row[field] = shift_date(row[field], offset)
            if table == 'products':
                row['sku'] = sku_for(row['product_id'])
            elif table == 'sales_targets':
                if row['month'] != '2024-04':
                    raise ValueError(f'Unexpected target month: {row["month"]}')
                row['period_start'] = shift_date('2024-04-01', offset)
                row['period_end'] = shift_date('2024-05-01', offset)
                row['month'] = row['period_start'][:7]  # Cohort label only.
            elif table == 'knowledge_documents' and row['policy_id']:
                old_id = row['policy_id']
                row['policy_id'] = POLICY_IDS[old_id]
                row['relative_path'], row['sha256'] = policies[old_id]
            elif table in ('fulfillment_policies', 'product_pricing_constraints'):
                row['policy_id'] = POLICY_IDS[row['policy_id']]
            converted.append(tuple(row[name] for name in target_names))
        out.executemany(statement, converted)
        before += len(converted)
    after = out.execute(f'SELECT count(*) FROM {q(table)}').fetchone()[0]
    if before != after:
        raise ValueError(f'{table}: copied {before}, found {after}')
    return before, after


def content_checksum(db: sqlite3.Connection) -> str:
    h = sha256()
    for table in tables(db):
        h.update((table + '\n').encode())
        for row in db.execute(f'SELECT * FROM {q(table)} ORDER BY rowid'):
            if table == 'metadata' and row[0] == 'output_checksum':
                continue
            h.update(json.dumps(row, ensure_ascii=False, separators=(',', ':')).encode())
            h.update(b'\n')
    return h.hexdigest()


def quality_counts(db: sqlite3.Connection) -> dict[str, int]:
    queries = {
        'promotion_category_mismatches': '''SELECT count(*) FROM orders o
            JOIN promotions p ON p.promo_id=o.promo_id
            WHERE p.applies_to_category<>'all' AND NOT EXISTS (
              SELECT 1 FROM order_items i JOIN products pr USING(product_id)
              WHERE i.order_id=o.order_id AND pr.category=p.applies_to_category)''',
        'warehouses_over_nominal_capacity': '''SELECT count(*) FROM (
            SELECT w.warehouse_id FROM warehouses w JOIN inventory i USING(warehouse_id)
            GROUP BY w.warehouse_id HAVING sum(i.quantity_on_hand)>w.capacity_units)''',
        'refunds_above_order_value': '''SELECT count(*) FROM returns r
            JOIN orders o USING(order_id) WHERE r.refund_amount>o.total_amount+0.01''',
        'refunds_above_returned_product_lines': '''WITH v AS (
            SELECT order_id,product_id,sum(quantity*unit_price*(1-discount_pct/100.0)) amount
            FROM order_items GROUP BY order_id,product_id)
            SELECT count(*) FROM returns r JOIN v USING(order_id,product_id)
            WHERE r.refund_amount>v.amount+0.01''',
    }
    return {name: db.execute(sql).fetchone()[0] for name, sql in queries.items()}


def validation_counts(db: sqlite3.Connection) -> dict[str, int]:
    """Count violations independently of schema constraints and source audit prose."""
    queries = {
        'customer_signup_after_order': '''SELECT count(*) FROM orders o
            JOIN customers c USING(customer_id) WHERE c.signup_date>o.order_date''',
        'shipment_before_order': '''SELECT count(*) FROM shipments s
            JOIN orders o USING(order_id) WHERE s.shipped_date<o.order_date''',
        'delivery_before_shipment': '''SELECT count(*) FROM shipments
            WHERE delivered_date IS NOT NULL AND delivered_date<shipped_date''',
        'return_before_order': '''SELECT count(*) FROM returns r JOIN orders o USING(order_id)
            WHERE r.return_date<o.order_date''',
        'return_before_delivery': '''SELECT count(*) FROM returns r
            JOIN shipments s USING(order_id) WHERE s.delivered_date IS NOT NULL
            AND r.return_date<s.delivered_date''',
        'activity_outside_opportunity': '''SELECT count(*) FROM sales_activities a
            JOIN sales_opportunities o USING(opportunity_id)
            WHERE a.occurred_at<o.opened_at OR a.occurred_at>o.closed_at
               OR a.employee_id<>o.employee_id''',
        'event_recorded_before_occurrence': '''SELECT count(*) FROM operational_events
            WHERE recorded_at<occurred_at''',
        'stock_received_before_observation': '''SELECT count(*) FROM inventory_snapshots_v2
            WHERE received_at<observed_at''',
        'recorded_event_after_as_of': '''SELECT count(*) FROM operational_events
            WHERE substr(recorded_at,1,10)>='2026-11-03' ''',
        'case_without_one_cutoff': '''SELECT count(*) FROM (
            SELECT c.case_id, count(e.event_id) n FROM fulfillment_cases c
            LEFT JOIN operational_events e ON e.case_id=c.case_id
              AND e.event_type='evidence_cutoff_reached'
            GROUP BY c.case_id HAVING n<>1)''',
        'case_outside_warehouse_policy': '''SELECT count(*) FROM fulfillment_cases
            WHERE case_date<'2026-10-04' OR case_date>='2026-11-03' ''',
        'promotion_outside_validity': '''SELECT count(*) FROM orders o
            JOIN promotions p ON p.promo_id=o.promo_id
            WHERE o.order_date<p.valid_from OR o.order_date>p.valid_until''',
        'pricing_interval_mismatch': '''SELECT count(*) FROM product_pricing_constraints pc
            JOIN product_enrichment e USING(product_id)
            WHERE pc.policy_id<>'FR-PRICE-2026-11-03'
               OR pc.effective_from<>e.catalog_effective_from
               OR pc.effective_to<>e.catalog_effective_to''',
        'sales_target_period_mismatch': '''SELECT count(*) FROM sales_targets
            WHERE month<>'2026-10' OR period_start<>'2026-10-04'
               OR period_end<>'2026-11-03' ''',
        'order_total_mismatch': '''SELECT count(*) FROM (
            SELECT o.order_id FROM orders o JOIN order_items i USING(order_id)
            GROUP BY o.order_id HAVING abs(o.total_amount-
              sum(i.quantity*i.unit_price*(1-i.discount_pct/100.0)))>0.02)''',
    }
    result = {name: db.execute(sql).fetchone()[0] for name, sql in queries.items()}
    if any(result.values()):
        raise ValueError(f'Temporal or business invariant failed: {result}')
    return result


def create_rag(db: sqlite3.Connection, knowledge: Path, path: Path) -> dict:
    chunks = []
    curated = {r[0]: r[1:] for r in db.execute('''SELECT product_id,
        synthetic_display_name,curated_list_price_usd,curated_shipping_weight_kg,
        catalog_effective_from,catalog_effective_to,provenance FROM product_enrichment''')}
    for pid, sku, name, category, brand, price, weight, supplier in db.execute('''
            SELECT product_id,sku,name,category,brand,price,weight_kg,supplier_id
            FROM products ORDER BY product_id'''):
        text = (f'Original imported product. Product ID: {pid}. Fiction-generated SKU: {sku}. '
                f'Import name: {name}. Category: {category}. Brand: {brand}. '
                f'Import price: USD {price:.2f}. Import weight: {weight} kg. '
                f'Supplier ID: {supplier}. Import price and weight are undated; '
                'they do not establish a current offer or verified specifications.')
        chunks.append(chunk('source_product', pid, text, f'sqlite:products:{pid}',
                            'upstream_source', metadata={'product_id': pid, 'sku': sku,
                                                         'category': category}))
        if pid in curated:
            display, list_price, packed_weight, start, end, provenance = curated.pop(pid)
            text = (f'Fictional curated offer for product ID {pid}, SKU {sku}. '
                    f'Display name: {display}. Category: {category}. '
                    f'List price: USD {list_price}. Packed shipping weight: {packed_weight} kg. '
                    f'Valid from {start} inclusive to {end} exclusive. '
                    'These are synthetic merchandising values, not transaction facts.')
            chunks.append(chunk('curated_offer', pid, text,
                                f'sqlite:product_enrichment:{pid}', provenance,
                                start, end, {'product_id': pid, 'sku': sku,
                                             'category': category, 'display_name': display}))
    if curated:
        raise ValueError('Curated product IDs missing from products')
    sku_by_id = dict(db.execute('SELECT product_id,sku FROM products'))
    for doc_id, pid, policy_id, kind, relative, expected, provenance in db.execute('''
            SELECT document_id,product_id,policy_id,kind,relative_path,sha256,provenance
            FROM knowledge_documents ORDER BY relative_path'''):
        file = (knowledge / relative).resolve()
        if not file.is_relative_to(knowledge.resolve()):
            raise ValueError(f'Unsafe document path: {relative}')
        raw = file.read_bytes()
        if sha256(raw).hexdigest() != expected:
            raise ValueError(f'Document hash mismatch: {relative}')
        body = raw.decode('utf-8')
        start, end = (POLICY_INTERVALS[policy_id] if kind == 'business_policy'
                      else ('2026-11-03', '2026-12-04'))
        sections = markdown_sections(body) if kind == 'business_policy' else [
            ('Complete product guide', body.strip())]
        for n, (section, text) in enumerate(sections, 1):
            metadata = {'document_id': doc_id, 'product_id': pid,
                        'policy_id': policy_id, 'section': section}
            if pid:
                metadata['sku'] = sku_by_id[pid]
            chunks.append(chunk(kind, f'{doc_id}:{n:02d}', text,
                                f'knowledge/{relative}#{n}', provenance,
                                start, end, metadata))
    for table in tables(db):
        columns = [(r[1], r[2]) for r in db.execute(f'PRAGMA table_info({q(table)})')]
        count = db.execute(f'SELECT count(*) FROM {q(table)}').fetchone()[0]
        origin = 'upstream_source' if table in SOURCE_KEYS else 'scenario_generated'
        purpose = TABLE_PURPOSES.get(table, 'See the data contract.')
        purpose = purpose.replace('May 2024', 'the 2026-11-03 to 2026-12-03 interval')
        purpose = purpose.replace('April 2024', 'the 2026-10-04 to 2026-11-02 interval')
        text = (f'SQL table {table}. {purpose} '
                f'Rows: {count}. Columns: ' +
                ', '.join(f'{name} ({kind})' for name, kind in columns) + '.')
        chunks.append(chunk('table_schema', table, text, f'sqlite:{table}',
                            origin, metadata={'database': 'fiction_retail',
                                              'table': table, 'row_count': count}))
    ids = [c['chunk_id'] for c in chunks]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate RAG chunk IDs')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='\n') as stream:
        for item in chunks:
            stream.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + '\n')
    return {'count': len(chunks), 'by_kind': dict(sorted(Counter(c['kind'] for c in chunks).items()))}


def build(source_path: Path, extension_path: Path, knowledge: Path,
          output_dir: Path) -> dict:
    source_path, extension_path, knowledge, output_dir = (
        Path(p).resolve() for p in (source_path, extension_path, knowledge, output_dir))
    if source_path == extension_path or output_dir in source_path.parents:
        raise ValueError('Source, extension and output paths must be separate')
    if not source_path.is_file() or digest(source_path) != BASELINE_HASH:
        raise ValueError('Canonical source SHA-256 mismatch')
    if not extension_path.is_file() or not knowledge.is_dir():
        raise FileNotFoundError('v0.4 extension and authored guides are required')
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError('Output directory must be empty')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_knowledge = output_dir / 'knowledge'
    shutil.copytree(knowledge / 'products', output_knowledge / 'products')
    db_path = output_dir / 'data' / 'fiction_retail.sqlite'
    db_path.parent.mkdir()
    with closing(sqlite3.connect(source_path.as_uri() + '?mode=ro', uri=True)) as src, \
         closing(sqlite3.connect(extension_path.as_uri() + '?mode=ro', uri=True)) as ext, \
         closing(sqlite3.connect(db_path)) as out:
        source_tables, extension_tables = tables(src), tables(ext)
        if len(source_tables) != 10 or len(extension_tables) != 17:
            raise ValueError('Expected 10 source and 17 extension tables')
        extension_meta = dict(ext.execute('SELECT key,value FROM metadata'))
        if extension_meta.get('version') != 'fiction-retail-extension-v0.4.0' or \
           extension_meta.get('baseline_sha256') != BASELINE_HASH:
            raise ValueError('Extension version or source lineage mismatch')
        latest = latest_observed_date(src, ext)
        offset = ((AS_OF_DATE - timedelta(days=1)) - latest).days
        if latest != date(2024, 4, 30) or offset != 916:
            raise ValueError(f'Unreviewed temporal offset: {latest}, {offset}')
        policies = write_policies(knowledge, output_knowledge, offset)
        out.execute('PRAGMA foreign_keys=ON')
        out.execute('PRAGMA page_size=4096')
        for table in source_tables:
            out.execute(source_schema(src, table))
        for table in extension_tables:
            out.execute(extension_schema(ext, table))
        if set(LOAD_ORDER) != set(source_tables + extension_tables):
            raise ValueError('Load order does not cover exactly the 27 tables')
        out.execute('BEGIN')
        input_counts = {}
        counts = {}
        for table in LOAD_ORDER:
            input_counts[table], counts[table] = insert_table(
                src, ext, out, table, offset, policies)
        metadata = {
            'version': VERSION, 'source_sha256': BASELINE_HASH,
            'extension_version': extension_meta['version'],
            'extension_sha256': digest(extension_path),
            'transformation_version': TRANSFORMATION_VERSION,
            'rebase_reference_date': AS_OF_DATE.isoformat(),
            'temporal_offset_days': str(offset),
            'source_latest_observed_date': latest.isoformat(),
            'dataset_business_as_of': AS_OF_DATE.isoformat() + 'T00:00:00+07:00',
            'business_timezone': BUSINESS_TIMEZONE,
            'reporting_period': shift_date('2024-04-01', offset)[:7],
            'reporting_period_start': shift_date('2024-04-01', offset),
            'reporting_period_end': shift_date('2024-05-01', offset),
            'curated_catalog_valid_from': shift_date('2024-05-01', offset),
            'curated_catalog_valid_until': shift_date('2024-06-01', offset),
            'synthetic_provenance': 'Extension, guides, policies, and SKU are fictional',
            'output_checksum_scope': 'Canonical table rows excluding output_checksum itself',
        }
        out.executemany('INSERT OR REPLACE INTO metadata(key,value) VALUES (?,?)',
                        sorted(metadata.items()))
        out.commit()
        inherited_indexes = [r[0] for r in ext.execute(
            "SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL ORDER BY name")]
        for statement in inherited_indexes + list(INDEXES):
            out.execute(statement)
        out.commit()
        if out.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('Unified SQLite integrity failed')
        orphan_rows = out.execute('PRAGMA foreign_key_check').fetchall()
        if orphan_rows:
            raise ValueError(f'Foreign key errors: {orphan_rows[:5]}')
        if out.execute('SELECT count(DISTINCT sku) FROM products').fetchone()[0] != 5000:
            raise ValueError('SKU collision or missing SKU')
        if out.execute('SELECT count(*) FROM fulfillment_cases c JOIN order_items i '
                       'ON i.order_item_id=c.order_item_id '
                       'WHERE i.order_id<>c.order_id OR i.product_id<>c.product_id').fetchone()[0]:
            raise ValueError('Fulfillment case line identity mismatch')
        checksum = content_checksum(out)
        out.execute('INSERT INTO metadata VALUES (?,?)', ('output_checksum', checksum))
        out.commit()
        counts['metadata'] = out.execute('SELECT count(*) FROM metadata').fetchone()[0]
        data_quality = quality_counts(out)
        if data_quality != {
            'promotion_category_mismatches': 16995,
            'warehouses_over_nominal_capacity': 15,
            'refunds_above_order_value': 140,
            'refunds_above_returned_product_lines': 350,
        }:
            raise ValueError(f'Unexpected quality counts: {data_quality}')
        validation = validation_counts(out)
        rag = create_rag(out, output_knowledge, output_dir / 'rag' / 'chunks.jsonl')
        if rag['count'] != 10093:
            raise ValueError(f'Unexpected RAG count: {rag["count"]}')
        out.execute('VACUUM')
    manifest = {
        'pack_version': VERSION,
        'source_url': SOURCE_URL,
        'source_sha256': BASELINE_HASH,
        'extension_version': extension_meta['version'],
        'extension_sha256': digest(extension_path),
        'transformation_version': TRANSFORMATION_VERSION,
        'rebase_reference_date': AS_OF_DATE.isoformat(),
        'source_latest_observed_date': latest.isoformat(),
        'temporal_offset_days': offset,
        'dataset_business_as_of': AS_OF_DATE.isoformat() + 'T00:00:00+07:00',
        'business_timezone': BUSINESS_TIMEZONE,
        'build_generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'runtime_sha256': digest(db_path),
        'content_sha256': checksum,
        'rag_sha256': digest(output_dir / 'rag' / 'chunks.jsonl'),
        'rag_chunk_count': rag['count'], 'rag_chunks_by_kind': rag['by_kind'],
        'knowledge_document_count': counts['knowledge_documents'],
        'input_table_counts': dict(sorted(input_counts.items())),
        'table_counts': dict(sorted(counts.items())),
        'data_quality': data_quality,
        'validation': validation,
        'policy_id_mapping': POLICY_IDS,
        'synthetic_provenance': 'Extension, guides, policies, and SKU are fictional',
    }
    (output_dir / 'manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8')
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--extension', type=Path, required=True)
    parser.add_argument('--knowledge', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.extension, args.knowledge,
                           args.output_dir), indent=2))


if __name__ == '__main__':
    main()
