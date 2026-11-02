# Fiction Retail Agent Dataset

**Scope:** A repository distribution of the public Fiction Retail SQLite database, this repository's v0.4 extension, and a grounded RAG corpus. All business data is fictional and intended for education. The [DataHub source description](https://github.com/datahub-project/static-assets/blob/main/datasets/fiction-retail/README.md) identifies the ten-table source database and its CC0 license. See the [schema reference](SCHEMA.md) for all 27 tables and the [data contract](DATA_CONTRACT.md) for identity, provenance, and temporal limits.

## Repository files

| Path | Contents | Role |
|---|---|---|
| `data/fiction-retail.db` | Original ten-table SQLite database; 150,000 orders and 5,000 products | Historical facts within the fictional source dataset |
| `data/fiction_runtime_v04.sqlite` | Seventeen extension tables; 50 dated offers, 20 pricing constraints, 100 fulfillment cases, 564 sales opportunities, and an index of 5,000 guides | Synthetic scenarios linked to original IDs |
| `knowledge/products/**/*.md` | 5,000 individual product guides | Fictional customer-support knowledge |
| `knowledge/policies/*.md` | Three company policies | Fictional, dated business rules |
| `rag/chunks.jsonl` | 10,093 chunks with IDs, sources, provenance, and validity intervals | Input for keyword or vector retrieval |
| `manifest.json` | File hashes and counts | Release verification |

`data/fiction-retail.db` is tracked with Git LFS because it is approximately 95 MiB. Install Git LFS before cloning or run `git lfs pull` after cloning; a pointer file is not a usable SQLite database. The other database and JSONL are regular Git files. The original source is retained byte-for-byte; the extension holds the authored changes.

## Code and current implementation

`scripts/generate_extension.py` creates v0.1 sales and fulfillment scenarios. `scripts/build_v02.py` adds the first 50 curated guides and operational evidence. `scripts/build_v03.py` adds dated offers and pricing constraints, then removes scenario labels and precomputed fulfillment decisions from the runtime. `scripts/rebuild_pack.py` runs those three builders in sequence. `scripts/build_v04.py` indexes one committed Markdown guide for each of the 5,000 original product IDs, checks that the original 50 guides still match v0.3, and records document hashes in SQLite. `scripts/build_agent_dataset.py` verifies the baseline and document hashes before packaging the databases and RAG corpus. None of these builders modifies the source database.

The Markdown files under `knowledge/products/` are the editable source for product knowledge in v0.4. Each product has a separate file; the build indexes these files rather than writing a common template over them. The 4,950 new profiles are deliberately fictional catalog interpretations of source IDs whose import names do not describe merchandise. They are suitable for a synthetic agent exercise, not for claims about manufacturers or historical orders. A [product authoring note](PRODUCT_AUTHORING.md) describes quality checks and editing.

The repository provides data and ingestion material. It does not include a vector index, embedding model, SQL tool, agent runtime, interface, or RAG benchmark. Passing the data checks below does not establish answer quality.

## Rebuild and publish

Requirements: Python 3.12+ and Git LFS. No Python packages are required. From the repository root:

```powershell
New-Item -ItemType Directory -Force .generated/source | Out-Null
curl.exe -L --fail --silent --show-error "https://raw.githubusercontent.com/datahub-project/static-assets/main/datasets/fiction-retail/fiction-retail.db" -o .generated/source/fiction-retail.db
(Get-FileHash .generated/source/fiction-retail.db -Algorithm SHA256).Hash
python -m scripts.rebuild_pack --source .generated/source/fiction-retail.db --output-dir .generated/fiction-v03
python -m scripts.build_v04 --source .generated/source/fiction-retail.db --v03 .generated/fiction-v03/data/fiction_runtime_v03.sqlite --knowledge knowledge --output .generated/fiction-v04/data/fiction_runtime_v04.sqlite
python -m scripts.build_agent_dataset --source .generated/source/fiction-retail.db --runtime .generated/fiction-v04/data/fiction_runtime_v04.sqlite --knowledge knowledge --output-dir .generated/agent-dataset-v04
Copy-Item .generated/agent-dataset-v04/data/fiction-retail.db data/fiction-retail.db -Force
Copy-Item .generated/agent-dataset-v04/data/fiction_runtime_v04.sqlite data/fiction_runtime_v04.sqlite -Force
Copy-Item .generated/agent-dataset-v04/rag/chunks.jsonl rag/chunks.jsonl -Force
Copy-Item .generated/agent-dataset-v04/manifest.json manifest.json -Force
```

The required source SHA-256 is `9f95373e46219e880ae54f995b6f2c2c439c3746e500e484fe3ab2bf9ac55754`. Builders stop on an unexpected source rather than silently consuming a changed upstream file. Output directories must be absent or empty before rebuilding. The generated Markdown files must match the tracked `knowledge/` files byte-for-byte; if the authoring scripts change, update the tracked documents as part of the same change.

## Query the two databases

Open both databases read-only and join by original IDs:

```python
from pathlib import Path
import sqlite3

root = Path('.').resolve()
db = sqlite3.connect('file::memory:?cache=private', uri=True)
db.execute('ATTACH DATABASE ? AS source',
           ((root / 'data/fiction-retail.db').as_uri() + '?mode=ro',))
db.execute('ATTACH DATABASE ? AS extension',
           ((root / 'data/fiction_runtime_v04.sqlite').as_uri() + '?mode=ro',))

as_of = '2024-05-15'
rows = db.execute('''
    SELECT p.product_id, e.synthetic_display_name, e.curated_list_price_usd
    FROM source.products AS p
    JOIN extension.product_enrichment AS e USING (product_id)
    WHERE ? >= e.catalog_effective_from AND ? < e.catalog_effective_to
    ORDER BY e.synthetic_display_name
''', (as_of, as_of)).fetchall()
print(len(rows))  # 50
```

`products.price` and `products.weight_kg` are undated import fields. The synthetic `curated_list_price_usd` and `curated_shipping_weight_kg` apply only from 2024-05-01 inclusive to 2024-06-01 exclusive. Do not apply those values to April orders. For historical order value, use `orders.total_amount` or `order_items.quantity * unit_price * (1 - discount_pct / 100)` at the transaction date.

## RAG record contract

Each JSONL line is one object:

| Field | Usage |
|---|---|
| `chunk_id` | Stable deduplication and tracing key |
| `kind` | `source_product`, `curated_offer`, `product_guide`, `business_policy`, or `table_schema` |
| `text` | English content for embedding and cited answers |
| `source_id`, `source_ref` | Original ID, table, or document reference to return as a citation |
| `provenance` | `upstream_source` or `scenario_generated` |
| `valid_from`, `valid_to` | Half-open interval `[from, to)`; `null` means unknown validity, **not** currently active |
| `metadata` | Product/policy IDs, section title, category, or SQL table |
| `text_sha256` | Integrity check for the chunk text |

Embed `text`, keep metadata as filterable fields, and return `source_ref` in citations. Filter by `kind`, exact product or policy ID, and the requested date before generating an answer. The 5,000 `source_product` cards contain literal import fields only. They do not substantiate compatibility, materials, or a current offer. All 5,000 product IDs have an individual fictional guide. Only 50 have a separately curated, dated list price and packed weight. Guides and offers are scoped to May 2024; the returns and warehouse policies are scoped to April 2024, and the pricing policy to May 2024. Do not extend any of these policies into the present.

```python
import json
from pathlib import Path

with Path('rag/chunks.jsonl').open(encoding='utf-8') as stream:
    chunks = [json.loads(line) for line in stream]
as_of = '2024-05-15'
eligible = [c for c in chunks
            if c['kind'] in {'curated_offer', 'product_guide', 'business_policy'}
            and c['valid_from'] is not None
            and c['valid_from'] <= as_of < c['valid_to']]
```

## Agent routing and controls

1. **Orders, amounts, returns, stock, prices, and eligibility:** query the SQLite databases with parameterized, read-only SQL. RAG can supply definitions and policies, but it is not the source of transaction values.
2. **Product selection and support:** retrieve the individual guide by product ID or its fictional display name, then cite `source_ref`. State that the guide is fictional; do not equate its specifications with original manufacturer facts. For price, only the 50 dated offers have a synthetic curated list price.
3. **Policies:** filter `business_policy` by the question's `as_of` date. Outside its interval, do not call a policy current.
4. **Warehouse transfer and price proposals:** use case-specific evidence or dated pricing constraints with the matching policy. A qualifying result is a proposal requiring manager approval, never an executed change.
5. **Customer data:** `customers` contains fictional names, emails, and phone numbers. Customer rows are excluded from the RAG corpus; enforce access restrictions in any SQL tool rather than embedding them.

The source `inventory` table has no snapshot timestamp. The extension's 100 timestamped cases do not form a company-wide inventory ledger. Neither database can establish stock in 2026.

## Verification

```powershell
python -m unittest discover -s tests -v
python -c "import json,pathlib; m=json.loads(pathlib.Path('manifest.json').read_text()); print(m['rag_chunk_count'],m['source_product_count'],m['knowledge_document_count'])"
```

The expected counts for this release are `10093 5000 5003`. Compare the SHA-256 values in `manifest.json` with the three published data files after cloning. The builder also runs SQLite integrity checks and verifies each knowledge document hash.
