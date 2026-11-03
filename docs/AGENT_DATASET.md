# Fiction Retail Agent Dataset

**Release:** `fiction-retail-unified-v1.0.0`. The business reference date is **2026-11-03 in Asia/Ho_Chi_Minh**. The dataset is fictional and rebased; it is not live retail data.

## Files and ownership

| Path | Purpose |
|---|---|
| `data/fiction_retail.sqlite` | Standalone 27-table runtime for SQL applications |
| `data/fiction-retail.db` | Immutable ten-table upstream source for provenance and rebuilds |
| `knowledge/products/**/*.md` | 5,000 individually authored fictional product guides |
| `knowledge/policies/*.md` | Three fictional policies with translated effective dates |
| `rag/chunks.jsonl` | 10,093 English retrieval records |
| `manifest.json` | File hashes, table and chunk counts, offset, as-of time, and preserved quality findings |

The source and unified SQLite files are tracked with Git LFS. Run `git lfs pull` after cloning. The former v0.4 sidecar is an internal build stage; applications connect only to the unified runtime.

## Rebuild

Use Python 3.12+ and Git LFS. The existing pipeline runs v0.1, v0.2, v0.3, and v0.4 in order, adds all authored guides, then builds the unified release and RAG corpus.

```powershell
python -m scripts.rebuild_pack --unified --source data/fiction-retail.db --product-guides knowledge/products --output-dir .generated/release
```

The output directory must be absent or empty. The builder checks the immutable source SHA-256 before writing. To publish a verified build, copy `.generated/release/data/fiction_retail.sqlite`, `.generated/release/knowledge/policies/`, `.generated/release/rag/chunks.jsonl`, and `.generated/release/manifest.json` to the corresponding repository paths. The 5,000 product guides stay editable in `knowledge/products/`. Rebuilding from the same inputs yields the same database and RAG content hashes; `build_generated_at_utc` in the manifest records the separate build time and is expected to change.

Run `python -m unittest discover -s tests -v` to rebuild independently and compare the database, canonical content, RAG, and policy document hashes with the published artifact. The full integration test processes more than 700,000 rows and 5,003 Markdown documents, so it takes several minutes on a typical desktop. Inspect `manifest.json` for `input_table_counts` and `table_counts` across all 27 tables, 15 zero-violation validation checks, and the four retained source-quality findings; a passing build does not erase those findings.

## Query one database

```python
import sqlite3

db = sqlite3.connect('file:data/fiction_retail.sqlite?mode=ro', uri=True)
db.execute('PRAGMA foreign_keys=ON')
as_of = '2026-11-03'
sku = db.execute('SELECT sku FROM products ORDER BY product_id LIMIT 1').fetchone()[0]
rows = db.execute("""
    SELECT p.product_id, p.sku, e.synthetic_display_name,
           e.curated_list_price_usd, k.relative_path AS guide_path
    FROM products p
    LEFT JOIN product_enrichment e ON e.product_id = p.product_id
      AND e.catalog_effective_from <= ? AND ? < e.catalog_effective_to
    JOIN knowledge_documents k ON k.product_id = p.product_id
      AND k.kind = 'product_guide'
    WHERE p.sku = ?
""", (as_of, as_of, sku)).fetchall()
```

The SKU is a Fiction-generated business identifier; `product_id` remains the database identity and all foreign keys continue to use it. Only 50 products have a dated curated list price. The other 4,950 guides do not create a price or verified manufacturer specification.

## RAG contract

Each JSONL line contains `chunk_id`, `kind`, `text`, `text_sha256`, `source_id`, `source_ref`, `provenance`, `valid_from`, `valid_to`, and `metadata`. Product records and guides carry both `product_id` and `sku` in metadata. Validity intervals are half-open: `valid_from <= as_of < valid_to`. A null interval means unknown validity, never an active offer. Use `source_ref` for citations.

| Kind | Chunks | Use |
|---|---:|---|
| `source_product` | 5,000 | Literal imported fields and Fiction SKU; import price is undated |
| `curated_offer` | 50 | Dated synthetic list prices and packed weights |
| `product_guide` | 5,000 | Individual fictional selection/support prose |
| `business_policy` | 16 | Sections from three dated policy documents |
| `table_schema` | 27 | Unified table columns and row counts |

```python
import json
with open('rag/chunks.jsonl', encoding='utf-8') as stream:
    chunks = (json.loads(line) for line in stream)
    as_of = '2026-11-03'
    eligible = [c for c in chunks
                if c['kind'] in {'curated_offer', 'product_guide', 'business_policy'}
                and c['valid_from'] is not None
                and c['valid_from'] <= as_of < c['valid_to']]
```

Query SQLite for orders, money, stock evidence, and eligibility. RAG explains catalog and policy context but does not prove a transaction amount or live status. The warehouse and returns policies end before the 2026-11-03 reference date; do not call them current. The price policy and 50 curated offers begin on that date solely because their prior dated period was translated by the same 916-day offset. Case-scoped stock observations still do not establish company-wide stock. Customer identity rows are not included in RAG; restrict SQL access in any application.

See [the data contract](DATA_CONTRACT.md), [unified schema](SCHEMA.md), and [source audit](SOURCE_DB_AUDIT.md) for exact semantics and retained anomalies.
