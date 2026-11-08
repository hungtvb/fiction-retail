"""Fast SQL-only regression for the distributed Fiction Lite v1 pack.

Does not claim the application/LLM/LangGraph is tested.
"""
import hashlib
import json
import sqlite3
from pathlib import Path
import pytest

HERE=Path(__file__).resolve().parents[1]
DB=HERE/'fiction_retail_lite.sqlite'
MANIFEST=json.loads((HERE/'manifest_lite.json').read_text(encoding='utf-8'))
GOLDEN=json.loads((HERE/'golden_poc.json').read_text(encoding='utf-8'))

@pytest.fixture
def c():
    con=sqlite3.connect(DB.resolve().as_uri()+'?mode=ro',uri=True)
    con.execute('PRAGMA query_only=ON')
    yield con
    con.close()

def test_pinned_source_and_compact_size():
    assert DB.stat().st_size < 20*1024*1024
    assert hashlib.sha256(DB.read_bytes()).hexdigest()==MANIFEST['runtime_sha256']
    assert MANIFEST['parent_release_sha256']!=MANIFEST['runtime_sha256']

def test_27_tables_integrity_foreign_keys(c):
    assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert c.execute('PRAGMA foreign_key_check').fetchall()==[]
    assert len(MANIFEST['table_counts'])==27
    for table,count in MANIFEST['table_counts'].items():
        assert c.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]==count

def test_100_cases_preserved_with_complete_source_evidence(c):
    assert c.execute('SELECT count(*) FROM fulfillment_cases').fetchone()[0]==100
    assert c.execute('SELECT count(*) FROM inventory_snapshots_v2').fetchone()[0]==216
    assert c.execute('SELECT count(*) FROM operational_events').fetchone()[0]==400
    assert c.execute('''SELECT count(*) FROM fulfillment_cases f
        LEFT JOIN order_items i ON i.order_item_id=f.order_item_id
        WHERE i.order_item_id IS NULL OR i.order_id<>f.order_id OR i.product_id<>f.product_id''').fetchone()[0]==0

def test_all_original_refund_outliers_preserved(c):
    above_order=c.execute('SELECT count(*) FROM returns r JOIN orders o USING(order_id) WHERE r.refund_amount > o.total_amount + .01').fetchone()[0]
    above_line=c.execute('''SELECT count(*) FROM returns r WHERE r.refund_amount > COALESCE(
      (SELECT SUM(i.quantity * i.unit_price * (100-i.discount_pct)/100.0)
       FROM order_items i WHERE i.order_id=r.order_id AND i.product_id=r.product_id),0) + .01''').fetchone()[0]
    assert (above_order,above_line)==(140,350)

def test_sales_top_three_october_and_rank_two_inventory_oracle(c):
    ranked=c.execute('''SELECT p.product_id,p.sku,SUM(i.quantity) AS units
        FROM order_items i JOIN products p USING(product_id) JOIN orders o USING(order_id)
        WHERE o.order_status='delivered' AND o.order_date >= '2026-10-01' AND o.order_date < '2026-11-01'
        GROUP BY p.product_id,p.sku ORDER BY units DESC,p.sku LIMIT 3''').fetchall()
    expected=GOLDEN['top3']
    assert [(sku,n) for pid,sku,n in ranked]==[(x['sku'],x['units']) for x in expected]
    assert ranked[1][0]==GOLDEN['second_rank_product_id']
    stock=c.execute('SELECT COALESCE(SUM(quantity_on_hand-reserved_quantity),0) FROM inventory WHERE product_id=?',(ranked[1][0],)).fetchone()[0]
    assert stock==GOLDEN['second_rank_available_units_undated']

def test_policy_and_product_guides_exact_sha():
    for item in MANIFEST['knowledge_documents_required']:
        f=HERE/'knowledge'/item['path']
        assert f.is_file()
        assert hashlib.sha256(f.read_bytes()).hexdigest()==item['sha256']

def test_source_cannot_be_written_by_runtime_connection(c):
    with pytest.raises(sqlite3.OperationalError):
        c.execute('DELETE FROM products WHERE 1=0')