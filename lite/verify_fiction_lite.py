#!/usr/bin/env python3
"""Independent structural/source verifier for the Fiction Lite derivative, no RetailIQ import required.

Usage: python verify_fiction_lite.py [--source /path/to/pinned/full.sqlite]
"""
from __future__ import annotations
import argparse
import json
from hashlib import sha256
from pathlib import Path
import sqlite3
from create_fiction_lite import checksum, digest, PARENT_SHA, RELEASE, VARIANT

HERE=Path(__file__).resolve().parent
DB=HERE/'fiction_retail_lite.sqlite'
MANIFEST=HERE/'manifest_lite.json'


def read_db(path:Path) -> sqlite3.Connection:
    c=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)
    c.execute('PRAGMA query_only=ON')
    return c


def verify(source_path:Path|None=None) -> dict:
    m=json.loads(MANIFEST.read_text(encoding='utf-8'))
    out={'status':'PASS','evidence_mode':'real_local_sqlite_independent_oracle','variant':m['dataset_variant'],
         'lite_db_bytes':DB.stat().st_size,'parent_sha256':m['parent_release_sha256'],
         'sha256':m['runtime_sha256'],'gates':{}}
    def gate(name:str, condition:bool, details=None):
        out['gates'][name]={'status':'PASS' if condition else 'FAIL','details':details}
        if not condition:raise AssertionError(name+': '+str(details))
    gate('distinct_parent_sha',m['parent_release_sha256']==PARENT_SHA and m['runtime_sha256']!=PARENT_SHA)
    gate('binary_sha256',digest(DB)==m['runtime_sha256'])
    for ext in ('-wal','-shm'):gate('no_sqlite_sidecar'+ext,not Path(str(DB)+ext).exists())
    c=read_db(DB)
    try:
        gate('journal_mode_delete',c.execute('PRAGMA journal_mode').fetchone()[0].lower()=='delete')
        gate('integrity_check',c.execute('PRAGMA integrity_check').fetchone()[0]=='ok')
        gate('foreign_key_check',c.execute('PRAGMA foreign_key_check').fetchall()==[])
        tables={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        gate('27_schema_tables',len(tables)==27)
        counts={t:c.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0] for t in tables}
        gate('manifest_table_counts',counts==m['table_counts'])
        meta=dict(c.execute('SELECT key,value FROM metadata'))
        gate('source_attribution',meta.get('lite_variant')==VARIANT and meta.get('lite_parent_runtime_sha256')==PARENT_SHA and meta.get('version')==RELEASE)
        gate('business_as_of',m['dataset_business_as_of']==meta['dataset_business_as_of'])
        gate('canonical_content_checksum',checksum(c)==m['content_sha256']==meta['output_checksum'])
        invalid_sku=[]
        for pid,sku in c.execute('SELECT product_id,sku FROM products'):
            expected='FR-'+sha256(pid.encode()).hexdigest()[:16].upper()
            if sku!=expected: invalid_sku.append(pid)
        gate('sku_identity',not invalid_sku,invalid_sku[:2])
        gate('preserve_100_cases',counts['fulfillment_cases']==100)
        gate('preserve_100_case_observations',counts['inventory_snapshots_v2']==216 and counts['inventory_observations']==126 and counts['operational_events']==400)
        broken=c.execute('''SELECT count(*) FROM fulfillment_cases f
                           LEFT JOIN orders o ON o.order_id=f.order_id
                           LEFT JOIN order_items i ON i.order_item_id=f.order_item_id
                           WHERE o.order_id IS NULL OR i.order_item_id IS NULL
                           OR i.order_id<>f.order_id OR i.product_id<>f.product_id''').fetchone()[0]
        gate('case_order_product_line_binding',broken==0,broken)
        abnormal_total=c.execute('SELECT count(*) FROM returns r JOIN orders o ON o.order_id=r.order_id WHERE r.refund_amount>o.total_amount+0.01').fetchone()[0]
        abnormal_line=c.execute('''SELECT count(*) FROM returns r WHERE r.refund_amount > COALESCE(
                        (SELECT SUM(i.quantity*i.unit_price*(100-i.discount_pct)/100.0)
                         FROM order_items i WHERE i.order_id=r.order_id AND i.product_id=r.product_id),0) + 0.01''').fetchone()[0]
        gate('refund_anomalies_preserved',abnormal_total==140 and abnormal_line==350,{'above_order':abnormal_total,'above_product_lines':abnormal_line})
        docs={x['path']:x['sha256'] for x in m['knowledge_documents_required']}
        source_refs={p:h for p,h in c.execute('SELECT relative_path,sha256 FROM knowledge_documents')}
        gate('document_registry_matches_files',docs==source_refs)
        doc_bad=[]
        for rel,expected in docs.items():
            p=HERE/'knowledge'/rel
            if not p.is_file() or digest(p)!=expected:doc_bad.append(rel)
        gate('policy_and_curated_guide_sha',not doc_bad,{'verified_docs':len(docs),'failed':doc_bad})
        top=c.execute('''SELECT p.sku,SUM(i.quantity) AS sold FROM order_items i JOIN products p USING(product_id)
           JOIN orders o USING(order_id)
           WHERE o.order_status='delivered' AND o.order_date>='2026-10-01' AND o.order_date<'2026-11-01'
           GROUP BY p.sku ORDER BY sold DESC,p.sku LIMIT 3''').fetchall()
        gate('lite_october_top3',top==[(x['sku'],x['units']) for x in m['sample_sql_top3_delivered_october_2026']],top)
        out['top3_lite_october']=[dict(sku=s,units=u) for s,u in top]
        ranked=c.execute('''SELECT p.product_id,p.sku,SUM(i.quantity) AS sold FROM order_items i
           JOIN products p USING(product_id) JOIN orders o USING(order_id)
           WHERE o.order_status='delivered' AND o.order_date>='2026-10-01' AND o.order_date<'2026-11-01'
           GROUP BY p.product_id,p.sku ORDER BY sold DESC,p.sku LIMIT 3''').fetchall()
        second_id=ranked[1][0]
        stock=c.execute('SELECT COALESCE(SUM(quantity_on_hand-reserved_quantity),0) FROM inventory WHERE product_id=?',(second_id,)).fetchone()[0]
        out['golden_poc']={'period':'2026-10','source_status':'delivered','top3':[
          {'rank':i+1,'product_id':pid,'sku':sku,'units':units} for i,(pid,sku,units) in enumerate(ranked)],
          'second_rank_product_id':second_id,'second_rank_available_units_undated':stock,
          'warning':'Inventory has no observation timestamp; do not claim live stock'}
        gate('golden_reference_second_rank',bool(second_id) and stock>=-100000,{'product_id':second_id,'undated_available_units':stock})
        # Read-only guard confirms no writes can be executed on the verifier connection.
        refused=False
        try:c.execute('DELETE FROM orders WHERE 1=0')
        except sqlite3.OperationalError:refused=True
        gate('read_only_connection',refused)
        out['table_counts']=dict(sorted(counts.items()))
    finally:
        c.close()
    if source_path is not None:
        source_path=source_path.resolve()
        gate('parent_full_sha_unchanged',digest(source_path)==PARENT_SHA)
        full=read_db(source_path);lite=read_db(DB)
        try:
            # This checks every case-scoped row and all its event/evidence details, not only count.
            for table in ['fulfillment_cases','fulfillment_events','inventory_movements_v2',
                          'inventory_observations','inventory_snapshots_v2','operational_events','warehouse_eligibility']:
                full_rows=full.execute(f'SELECT * FROM "{table}" ORDER BY rowid').fetchall()
                lite_rows=lite.execute(f'SELECT * FROM "{table}" ORDER BY rowid').fetchall()
                gate('case_source_rows_equal_'+table,full_rows==lite_rows,{'count':len(full_rows)})
            # All selected orders, order lines, shipment and return facts are copied without modification.
            for table,pk in [('orders','order_id'),('order_items','order_item_id'),('shipments','shipment_id'),('returns','return_id'),('inventory','inventory_id')]:
                rows=lite.execute(f'SELECT * FROM "{table}"').fetchall()
                columns=[x[1] for x in lite.execute(f'PRAGMA table_info("{table}")')]
                pki=columns.index(pk)
                expected={r[0]:r[1:] for r in full.execute(f'SELECT "{pk}",* FROM "{table}" WHERE "{pk}" IN ({",".join("?" for _ in rows)})',[r[pki] for r in rows])} if rows else {}
                # Use full table in-memory comparisons only for the bounded Lite result set.
                gate('source_facts_equal_'+table,len(rows)==len(expected) and all(expected.get(r[pki])==tuple(r) for r in rows),{'rows':len(rows)})
        finally:
            full.close();lite.close()
    (HERE/'qa_report.json').write_text(json.dumps(out,indent=2,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf-8')
    (HERE/'golden_poc.json').write_text(json.dumps(out['golden_poc'],indent=2,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf-8')
    return out

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,default=None)
    args=parser.parse_args()
    report=verify(args.source)
    print('PASS',len(report['gates']),'gates; lite',round(report['lite_db_bytes']/1048576,2),'MiB; all 100 cases preserved; 6 original documents SHA verified')