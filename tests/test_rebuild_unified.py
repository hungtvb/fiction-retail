"""Verify the published release can be rebuilt from source and authored guides."""
from contextlib import closing
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from scripts.rebuild_pack import rebuild_unified
from scripts.build_unified import EVENT_FIELDS, TEMPORAL_FIELDS


ROOT = Path(__file__).resolve().parents[1]


class FullRebuildTests(unittest.TestCase):
    def test_rebuild_from_source_and_guides(self):
        with tempfile.TemporaryDirectory() as temp:
            release = Path(temp) / 'release'
            result = rebuild_unified(ROOT / 'data/fiction-retail.db',
                                     ROOT / 'knowledge/products', release)
            self.assertEqual(27, len(result['table_counts']))
            self.assertEqual(27, len(result['input_table_counts']))
            self.assertEqual(20, result['input_table_counts']['metadata'])
            self.assertEqual(34, result['table_counts']['metadata'])
            self.assertEqual(
                {name: count for name, count in result['input_table_counts'].items()
                 if name != 'metadata'},
                {name: count for name, count in result['table_counts'].items()
                 if name != 'metadata'})
            self.assertEqual(5003, result['knowledge_document_count'])
            self.assertEqual(916, result['temporal_offset_days'])
            self.assertEqual(10093, result['rag_chunk_count'])
            self.assertEqual(0, sum(result['validation'].values()))
            with closing(sqlite3.connect(release / 'data/fiction_retail.sqlite')) as db:
                db.execute('PRAGMA foreign_keys=ON')
                names = {r[0] for r in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")}
                self.assertEqual(27, len(names))
                self.assertEqual(150000, db.execute('SELECT count(*) FROM orders').fetchone()[0])
                self.assertEqual(5000, db.execute('SELECT count(*) FROM products').fetchone()[0])
                self.assertEqual(5000, db.execute('SELECT count(DISTINCT sku) FROM products').fetchone()[0])
                self.assertEqual('ok', db.execute('PRAGMA integrity_check').fetchone()[0])
                self.assertEqual([], db.execute('PRAGMA foreign_key_check').fetchall())
                self.assertIsNotNone(db.execute("SELECT 1 FROM sqlite_master WHERE type='index' AND name='ix_v2_stock'").fetchone())
                self.assertIsNotNone(db.execute("SELECT 1 FROM sqlite_master WHERE type='index' AND name='idx_orders_status_date_amount'").fetchone())
                self.assertEqual('2026-11-02', db.execute('SELECT max(order_date) FROM orders').fetchone()[0])
                self.assertEqual('2026-10-04', db.execute('SELECT min(period_start) FROM sales_targets').fetchone()[0])
                self.assertEqual('2026-11-03', db.execute('SELECT max(period_end) FROM sales_targets').fetchone()[0])
                recognized = {(t, c) for t, cols in TEMPORAL_FIELDS.items() for c in cols}
                recognized.update({('sales_targets', 'month'),
                                   ('sales_targets', 'period_start'),
                                   ('sales_targets', 'period_end')})
                local_dates = []
                for table in names - {'metadata'}:
                    for column in db.execute(f'PRAGMA table_info("{table}")'):
                        name = column[1]
                        if any(token in name for token in
                               ('date', '_at', 'month', 'valid_', 'effective_',
                                'opened', 'closed', 'shipped', 'delivered', 'restocked')):
                            self.assertIn((table, name), recognized)
                    for field in EVENT_FIELDS.get(table, ()):
                        latest = db.execute(f'SELECT max("{field}") FROM "{table}"').fetchone()[0]
                        if latest:
                            observed = (datetime.fromisoformat(latest.replace('Z', '+00:00'))
                                        .astimezone(timezone(timedelta(hours=7))).date()
                                        if 'T' in latest else date.fromisoformat(latest))
                            local_dates.append(observed)
                self.assertEqual(date(2026, 11, 2), max(local_dates))
            with (release / 'rag/chunks.jsonl').open(encoding='utf-8') as stream:
                chunks = [json.loads(line) for line in stream]
            self.assertEqual(5000, sum(c['kind'] == 'product_guide' for c in chunks))
            self.assertTrue(all(c['metadata'].get('sku') for c in chunks
                                if c['kind'] == 'product_guide'))
            self.assertFalse(any('FR-WH-2024-04' in c['text'] for c in chunks))
            published = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(published['input_table_counts'], result['input_table_counts'])
            self.assertEqual(published['table_counts'], result['table_counts'])
            for key in ('runtime_sha256', 'content_sha256', 'rag_sha256'):
                self.assertEqual(published[key], result[key], key)
            for policy in (release / 'knowledge/policies').glob('*.md'):
                self.assertEqual(sha256((ROOT / 'knowledge/policies' / policy.name).read_bytes()).hexdigest(),
                                 sha256(policy.read_bytes()).hexdigest())


if __name__ == '__main__':
    unittest.main()
