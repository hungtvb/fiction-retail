import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.build_agent_dataset import make_document_chunks, make_product_chunks, markdown_sections, verified_documents


class AgentDatasetTests(unittest.TestCase):
    def test_product_chunks_keep_import_and_dated_offer_distinct(self):
        with sqlite3.connect(':memory:') as source, sqlite3.connect(':memory:') as runtime:
            source.execute('CREATE TABLE products (product_id TEXT, name TEXT, category TEXT, brand TEXT, price REAL, weight_kg REAL, supplier_id TEXT)')
            source.execute("INSERT INTO products VALUES ('p1','Import label','electronics','Brand X',12.5,0.3,'s1')")
            runtime.execute('CREATE TABLE product_enrichment (product_id TEXT, synthetic_display_name TEXT, curated_list_price_usd TEXT, curated_shipping_weight_kg TEXT, catalog_effective_from TEXT, catalog_effective_to TEXT, provenance TEXT)')
            runtime.execute("INSERT INTO product_enrichment VALUES ('p1','USB-C Hub','54.00','0.22','2024-05-01','2024-06-01','scenario_generated')")
            chunks = list(make_product_chunks(source, runtime))
        self.assertEqual([c['kind'] for c in chunks], ['source_product', 'curated_offer'])
        self.assertEqual(chunks[0]['provenance'], 'upstream_source')
        self.assertIsNone(chunks[0]['valid_from'])
        self.assertIn('Import label', chunks[0]['text'])
        self.assertNotIn('54.00', chunks[0]['text'])
        self.assertEqual(chunks[1]['valid_from'], '2024-05-01')
        self.assertEqual(chunks[1]['valid_to'], '2024-06-01')
        self.assertIn('fictional', chunks[1]['text'].lower())
        self.assertNotIn('Vietnamese', chunks[1]['text'])
        self.assertNotIn('search_terms_vi', chunks[1]['metadata'])

    def test_sections_preserve_question_context(self):
        sections = markdown_sections('# Title\n\n## FAQ\n### Does it fit?\nCheck dimensions.\n')
        self.assertEqual(len(sections), 1)
        self.assertIn('Title', sections[0][1])
        self.assertIn('Does it fit?', sections[0][1])
        self.assertIn('Check dimensions.', sections[0][1])

    def test_document_hash_mismatch_stops_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'policies').mkdir()
            (root / 'policies' / 'P.md').write_text('# Policy\nText', encoding='utf-8')
            with sqlite3.connect(':memory:') as runtime:
                runtime.execute('CREATE TABLE knowledge_documents (document_id TEXT, product_id TEXT, policy_id TEXT, kind TEXT, relative_path TEXT, sha256 TEXT, provenance TEXT)')
                runtime.execute("INSERT INTO knowledge_documents VALUES ('d1',NULL,'P','business_policy','policies/P.md','bad-hash','scenario_generated')")
                with self.assertRaisesRegex(ValueError, 'hash'):
                    list(verified_documents(runtime, root))

    def test_product_guide_is_one_self_contained_rag_chunk(self):
        with tempfile.TemporaryDirectory() as tmp, sqlite3.connect(':memory:') as runtime:
            root = Path(tmp)
            (root / 'products').mkdir()
            body = '# One Product\n\n## Selection\nFit advice.\n\n## Care\nCare advice.\n'
            path = root / 'products' / 'p1.md'
            path.write_text(body, encoding='utf-8')
            runtime.execute('CREATE TABLE knowledge_documents (document_id TEXT, product_id TEXT, policy_id TEXT, kind TEXT, relative_path TEXT, sha256 TEXT, provenance TEXT)')
            runtime.execute('INSERT INTO knowledge_documents VALUES (?,?,?,?,?,?,?)',
                            ('d1', 'p1', None, 'product_guide', 'products/p1.md',
                             hashlib.sha256(path.read_bytes()).hexdigest(), 'scenario_generated'))
            chunks = list(make_document_chunks(runtime, root))
        self.assertEqual(len(chunks), 1)
        self.assertIn('Fit advice.', chunks[0]['text'])
        self.assertIn('Care advice.', chunks[0]['text'])


if __name__ == '__main__':
    unittest.main()
