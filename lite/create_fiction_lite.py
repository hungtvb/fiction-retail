#!/usr/bin/env python3
"""Build a deterministic, source-backed Fiction Lite *derivative* from the pinned Full SQLite.

No synthetic runtime rows and no writes to the Full database. Requires Python >=3.10.
Run: python create_fiction_lite.py --source /path/to/fiction_retail.sqlite --output fiction_retail_lite.sqlite
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

PARENT_SHA = '015b0a84d8d93870c6facd359347f4c039bc7fc570000890c581010d0451af42'
RELEASE = 'fiction-retail-unified-v1.0.0'  # Compatibility with existing FictionStore; variant is explicit below.
VARIANT = 'fiction-lite-v1.0.0'
MONTH_TARGETS = {'2026-10': 1600, '2026-09': 850, '2026-08': 400, '2026-11': 200}
DEFAULT_OTHER_MONTH = 110
SCHEMA_TABLES = 27


def digest(path: Path) -> str:
    with path.open('rb') as fh:
        return __import__('hashlib').file_digest(fh, 'sha256').hexdigest()


def stable_key(value: str) -> str:
    return sha256(('fiction-lite-v1|' + value).encode()).hexdigest()


def q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def checksum(conn: sqlite3.Connection) -> str:
    # Exactly the canonical table-row checksum algorithm from fiction-retail/scripts/build_unified.py.
    h = sha256()
    for table, in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
        h.update((table + '\n').encode())
        for row in conn.execute(f'SELECT * FROM {q(table)} ORDER BY rowid'):
            if table == 'metadata' and row[0] == 'output_checksum':
                continue
            h.update(json.dumps(row, ensure_ascii=False, separators=(',', ':')).encode())
            h.update(b'\n')
    return h.hexdigest()


def sample_order_ids(src: sqlite3.Connection) -> tuple[set[str], dict]:
    rows = src.execute('SELECT order_id, substr(order_date,1,7), order_status FROM orders').fetchall()
    by_month = defaultdict(list)
    by_month_status = defaultdict(list)
    for oid, month, status in rows:
        by_month[month].append(oid)
        by_month_status[(month, status)].append(oid)
    selected: set[str] = set()
    # Diverse status examples per month, then a reproducible top-up per month.
    for (month, status), group in sorted(by_month_status.items()):
        selected.update(sorted(group, key=stable_key)[:min(8, len(group))])
    for month, group in sorted(by_month.items()):
        goal = MONTH_TARGETS.get(month, DEFAULT_OTHER_MONTH)
        ordered = sorted(group, key=stable_key)
        existing = len(set(group) & selected)
        selected.update(ordered[:max(0, goal - existing)])
    # All 100 source-backed backorder cases must remain available, including their complete orders.
    selected.update(oid for oid, in src.execute('SELECT order_id FROM fulfillment_cases'))

    # Preserve ALL outlier refund rows (140 above order total, 350 above returned lines in Full),
    # plus diverse ordinary return requests. Always retain the complete associated order.
    anomaly_sql = '''SELECT r.order_id FROM returns r JOIN orders o ON o.order_id=r.order_id
      WHERE r.refund_amount > o.total_amount + 0.01
      OR r.refund_amount > COALESCE((SELECT SUM(i.quantity * i.unit_price * (100-i.discount_pct)/100.0)
                  FROM order_items i WHERE i.order_id=r.order_id AND i.product_id=r.product_id),0) + 0.01'''
    selected.update(oid for oid, in src.execute(anomaly_sql))
    # Additional returned-order diversity, independently of anomalies.
    for reason, in src.execute('SELECT DISTINCT return_reason_code FROM returns'):
        group = [oid for oid, in src.execute('SELECT order_id FROM returns WHERE return_reason_code=?', (reason,))]
        selected.update(sorted(group, key=stable_key)[:18])
    # Ensure product-curated examples are present in actual orders where possible.
    curated = [pid for pid, in src.execute('SELECT product_id FROM product_enrichment')]
    for pid in curated:
        group = [oid for oid, in src.execute('SELECT order_id FROM order_items WHERE product_id=? LIMIT 400', (pid,))]
        selected.update(sorted(group, key=stable_key)[:4])
    return selected, {'source_months': dict(sorted(Counter(month for _, month, _ in rows).items())),
                      'source_statuses': dict(sorted(Counter(status for _, _, status in rows).items()))}


def temp_ids(conn: sqlite3.Connection, table: str, ids) -> None:
    conn.execute(f'CREATE TEMP TABLE {q(table)}(id TEXT PRIMARY KEY) WITHOUT ROWID')
    conn.executemany(f'INSERT OR IGNORE INTO temp.{q(table)}(id) VALUES (?)', ((x,) for x in ids))


def copy(conn: sqlite3.Connection, table: str, where: str = '1=1') -> int:
    conn.execute(f'INSERT INTO main.{q(table)} SELECT * FROM src.{q(table)} WHERE {where}')
    return conn.execute(f'SELECT count(*) FROM main.{q(table)}').fetchone()[0]


def build(source: Path, output: Path, expected_sha: str, docs_per_curated: int) -> dict:
    source=source.resolve(); output=output.resolve()
    if source == output: raise ValueError('Refusing to overwrite source Full SQLite')
    if not source.is_file(): raise FileNotFoundError(source)
    actual_sha=digest(source)
    if actual_sha != expected_sha: raise ValueError('Full source SHA mismatch: '+actual_sha)
    if output.exists(): raise FileExistsError('Refusing to overwrite: '+str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    src=sqlite3.connect(f'file:{source}?mode=ro', uri=True)
    try:
        if src.execute('PRAGMA quick_check').fetchone()[0] != 'ok': raise ValueError('Full SQLite corrupt')
        if src.execute('PRAGMA journal_mode').fetchone()[0].lower() != 'delete': raise ValueError('Full DB journal mode changed')
        case_count=src.execute('SELECT count(*) FROM fulfillment_cases').fetchone()[0]
        if case_count != 100: raise ValueError(f'Expected pinned 100 cases, found {case_count}')
        orders, strata=sample_order_ids(src)
        print(f'Order selection: {len(orders)} out of 150000',flush=True)
    finally:
        src.close()
    con=sqlite3.connect(str(output),uri=True)
    try:
        con.execute('PRAGMA foreign_keys=OFF')
        con.execute('PRAGMA journal_mode=DELETE')
        con.execute('PRAGMA synchronous=OFF') # On failed build, output must be discarded/rebuilt.
        con.execute('PRAGMA temp_store=MEMORY')
        con.execute('ATTACH DATABASE ? AS src', (f'file:{source}?mode=ro',))
        tables=con.execute("SELECT name, sql FROM src.sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
        if len(tables)!=SCHEMA_TABLES: raise ValueError('Unexpected schema table count')
        for table, ddl in tables:con.execute(ddl)
        temp_ids(con,'keep_orders',orders)
        con.execute('CREATE TEMP TABLE keep_products(id TEXT PRIMARY KEY) WITHOUT ROWID')
        for sql in [
          'SELECT product_id FROM src.order_items WHERE order_id IN (SELECT id FROM temp.keep_orders)',
          'SELECT product_id FROM src.fulfillment_cases',
          'SELECT product_id FROM src.product_enrichment',
          'SELECT product_id FROM src.product_pricing_constraints',
          # Include unsold and missing-stock controls for source uncertainty testing.
          'SELECT p.product_id FROM src.products p WHERE NOT EXISTS (SELECT 1 FROM src.order_items i WHERE i.product_id=p.product_id) ORDER BY p.product_id LIMIT 15',
          'SELECT p.product_id FROM src.products p WHERE NOT EXISTS (SELECT 1 FROM src.inventory i WHERE i.product_id=p.product_id) ORDER BY p.product_id LIMIT 15'
        ]:
            con.execute('INSERT OR IGNORE INTO temp.keep_products(id) '+sql)
        con.execute('CREATE TEMP TABLE keep_opps(id TEXT PRIMARY KEY) WITHOUT ROWID')
        con.execute('INSERT INTO temp.keep_opps SELECT opportunity_id FROM src.sales_opportunities WHERE order_id IN (SELECT id FROM temp.keep_orders)')
        con.execute('CREATE TEMP TABLE keep_docs(id TEXT PRIMARY KEY) WITHOUT ROWID')
        con.execute("INSERT INTO temp.keep_docs SELECT document_id FROM src.knowledge_documents WHERE kind='business_policy'")
        con.execute('INSERT OR IGNORE INTO temp.keep_docs SELECT document_id FROM src.knowledge_documents WHERE kind=\'product_guide\' AND product_id IN (SELECT product_id FROM src.product_enrichment ORDER BY product_id LIMIT ?) ',(docs_per_curated,))
        clauses={
          'customers': 'customer_id IN (SELECT customer_id FROM src.orders WHERE order_id IN (SELECT id FROM temp.keep_orders))',
          'suppliers': 'supplier_id IN (SELECT supplier_id FROM src.products WHERE product_id IN (SELECT id FROM temp.keep_products))',
          'promotions': 'promo_id IN (SELECT promo_id FROM src.orders WHERE order_id IN (SELECT id FROM temp.keep_orders))',
          'products': 'product_id IN (SELECT id FROM temp.keep_products)',
          'product_enrichment': 'product_id IN (SELECT id FROM temp.keep_products)',
          'product_pricing_constraints': 'product_id IN (SELECT id FROM temp.keep_products)',
          'orders': 'order_id IN (SELECT id FROM temp.keep_orders)',
          'order_items': 'order_id IN (SELECT id FROM temp.keep_orders)',
          'returns': 'order_id IN (SELECT id FROM temp.keep_orders)',
          'shipments': 'order_id IN (SELECT id FROM temp.keep_orders)',
          'inventory': 'product_id IN (SELECT id FROM temp.keep_products)',
          'sales_opportunities': 'opportunity_id IN (SELECT id FROM temp.keep_opps)',
          'sales_activities': 'opportunity_id IN (SELECT id FROM temp.keep_opps)',
          'knowledge_documents': 'document_id IN (SELECT id FROM temp.keep_docs)',
        }
        # Every case-related fact remains intact; tables not in clauses are small.
        counts={}
        for table,_ in tables:
            if table=='metadata': continue
            counts[table]=copy(con,table,clauses.get(table,'1=1'))
        counts['metadata']=copy(con,'metadata')
        # The original output checksum is no longer valid for this selected subset.
        con.execute("DELETE FROM metadata WHERE key='output_checksum'")
        source_meta={k:v for k,v in con.execute('SELECT key,value FROM metadata')}
        additions={
          'lite_variant':VARIANT,
          'lite_parent_runtime_sha256': actual_sha,
          'lite_build_selection':'stratified_by_month_status + complete_cases + refund_anomalies + curated_products',
          'product_guide_count':str(docs_per_curated),
          'data_scope':'Subset of historical orders; all 100 original case observations; selected knowledge docs; not complete company KPI',
        }
        con.executemany('INSERT OR REPLACE INTO metadata(key,value) VALUES (?,?)',sorted(additions.items()))
        # Preserve production-compatible release major version and verify a distinct pinned SHA/variant in manifest.
        con.execute("UPDATE metadata SET value=? WHERE key='version'",(RELEASE,))
        indexes=con.execute("SELECT name,sql FROM src.sqlite_master WHERE type='index' AND sql IS NOT NULL ORDER BY name").fetchall()
        for _,sql in indexes:con.execute(sql)
        con.commit()
        print('Tables copied, indexes built. Verifying...',flush=True)
        if con.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Lite integrity failed')
        fk=con.execute('PRAGMA foreign_key_check').fetchall()
        if fk:raise ValueError('Foreign keys broken: '+repr(fk[:8]))
        for table in ['fulfillment_cases','inventory_snapshots_v2','warehouse_eligibility','operational_events','fulfillment_events','inventory_movements_v2','inventory_observations']:
            full=con.execute(f'SELECT count(*) FROM src.{q(table)}').fetchone()[0]
            lite=con.execute(f'SELECT count(*) FROM main.{q(table)}').fetchone()[0]
            if full!=lite:raise ValueError(f'Case evidence truncated in {table}: {lite}/{full}')
        for table,key in [('orders','order_id'),('order_items','order_item_id'),('inventory','inventory_id'),('returns','return_id'),('shipments','shipment_id')]:
            # Full row data for each selected record is exact (no invented facts).
            count_diff=con.execute(f'SELECT count(*) FROM main.{q(table)} a JOIN src.{q(table)} b ON a.{q(key)}=b.{q(key)} WHERE '+
                                   ' OR '.join(f'a.{q(c[1])} IS NOT b.{q(c[1])}' for c in con.execute(f'PRAGMA table_info({q(table)})'))).fetchone()[0]
            if count_diff:raise ValueError(f'Mismatched source facts in {table}: {count_diff}')
        if con.execute('SELECT count(*) FROM fulfillment_cases').fetchone()[0]!=100:raise ValueError('Lost cases')
        if con.execute('SELECT count(*) FROM fulfillment_cases c LEFT JOIN order_items i ON i.order_item_id=c.order_item_id WHERE i.order_id<>c.order_id OR i.product_id<>c.product_id OR i.order_item_id IS NULL').fetchone()[0]:
            raise ValueError('Case order line/product relation broken')
        content_sha=checksum(con)
        con.execute('INSERT INTO metadata(key,value) VALUES (?,?)',('output_checksum',content_sha))
        con.commit()
        con.execute('PRAGMA synchronous=FULL')
        con.execute('VACUUM')
        con.commit()
        if checksum(con)!=content_sha:raise ValueError('Checksum changed after VACUUM')
        if con.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Post-VACUUM integrity failed')
        if con.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('Post-VACUUM FK failure')
        counts={t:con.execute(f'SELECT count(*) FROM main.{q(t)}').fetchone()[0] for t,_ in tables}
        guide_rows=con.execute("SELECT relative_path,sha256 FROM knowledge_documents WHERE kind='product_guide' ORDER BY relative_path").fetchall()
        policy_rows=con.execute("SELECT relative_path,sha256 FROM knowledge_documents WHERE kind='business_policy' ORDER BY relative_path").fetchall()
        period_counts=dict(con.execute('SELECT substr(order_date,1,7),count(*) FROM orders GROUP BY 1 ORDER BY 1'))
        status_counts=dict(con.execute('SELECT order_status,count(*) FROM orders GROUP BY 1 ORDER BY 1'))
        selected_qual=con.execute("SELECT p.sku, SUM(i.quantity) AS sold FROM order_items i JOIN products p ON p.product_id=i.product_id JOIN orders o ON o.order_id=i.order_id WHERE o.order_status='delivered' AND o.order_date>='2026-10-01' AND o.order_date<'2026-11-01' GROUP BY p.sku ORDER BY sold DESC,p.sku LIMIT 3").fetchall()
        con.execute('DETACH DATABASE src')
        con.close()
        binary_sha=digest(output)
        meta={
          'pack_version':RELEASE,
          'dataset_variant':VARIANT,
          'variant_is_subset':True,
          'parent_release_sha256':actual_sha,
          'runtime_sha256':binary_sha,
          'content_sha256':content_sha,
          'dataset_business_as_of': source_meta.get('dataset_business_as_of'),
          'business_timezone':source_meta.get('business_timezone'),
          'table_counts':counts,
          'selection_method':'deterministic stratification + complete 100-case evidence + all refund anomalies',
          'selected_order_counts_by_month':period_counts,
          'selected_order_counts_by_status':status_counts,
          'source_order_counts_by_month':strata['source_months'],
          'source_order_counts_by_status':strata['source_statuses'],
          'knowledge_documents_required': [dict(path=p,sha256=s) for p,s in (policy_rows+guide_rows)],
          'sample_sql_top3_delivered_october_2026': [dict(sku=s,units=u) for s,u in selected_qual],
          'limitations': ['KPI totals/ranking are subset-specific; never compare to full-data KPIs',
                          'Not all 5000 product guides are available; only listed knowledge files are supported',
                          'Base inventory is undated; source cannot prove current stock',
                          'Do not present this subset as complete/full Fiction release acceptance'],
        }
        manifest_path=output.parent/'manifest_lite.json'
        manifest_path.write_text(json.dumps(meta,indent=2,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf-8')
        return meta
    except Exception:
        try:con.close()
        except Exception:pass
        try:output.unlink(missing_ok=True)
        except Exception:pass
        raise


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--source',type=Path,required=True)
    a.add_argument('--output',type=Path,default=Path('fiction_retail_lite.sqlite'))
    a.add_argument('--expected-sha',default=PARENT_SHA)
    a.add_argument('--guides',type=int,default=3)
    args=a.parse_args()
    if not 0<=args.guides<=50:raise SystemExit('--guides must be between 0 and 50')
    r=build(args.source,args.output,args.expected_sha,args.guides)
    print(json.dumps({'bytes':args.output.stat().st_size,'size_mib':round(args.output.stat().st_size/1048576,2),'tables':len(r['table_counts']),'orders':r['table_counts']['orders'],'order_items':r['table_counts']['order_items'],'cases':r['table_counts']['fulfillment_cases'],'sha256':r['runtime_sha256']},indent=2))

if __name__=='__main__':main()