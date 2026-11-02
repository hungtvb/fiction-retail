import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.build_v04 import scan_product_guides


class V04GuideIndexTests(unittest.TestCase):
    def test_each_source_product_needs_its_own_guide(self):
        with tempfile.TemporaryDirectory() as tmp, sqlite3.connect(':memory:') as source:
            root = Path(tmp)
            (root / 'products').mkdir()
            source.execute('CREATE TABLE products(product_id TEXT, category TEXT)')
            source.executemany('INSERT INTO products VALUES (?,?)', [('p1', 'books'), ('p2', 'food')])
            (root / 'products' / 'p1.md').write_text('# A Print Guide\n\n## Selection\nCheck the format and edition.\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Missing'):
                scan_product_guides(source, root)
            (root / 'products' / 'p2.md').write_text('# A Food Guide\n\n## Selection\nCheck the ingredient label.\n', encoding='utf-8')
            rows = scan_product_guides(source, root)
        self.assertEqual({r['product_id'] for r in rows}, {'p1', 'p2'})
        self.assertEqual(len({r['sha256'] for r in rows}), 2)


if __name__ == '__main__':
    unittest.main()
