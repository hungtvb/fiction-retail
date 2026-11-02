# Fiction Retail Agent Dataset

A fictional retail dataset for SQL and RAG-based agent experiments. It combines the unchanged [DataHub Fiction Retail SQLite source](https://github.com/datahub-project/static-assets/tree/main/datasets/fiction-retail), a synthetic extension, and English product and policy knowledge.

## Included in this repository

- `data/fiction-retail.db`: original ten-table source database, tracked with Git LFS.
- `data/fiction_runtime_v04.sqlite`: scenario extension, including dated catalog offers and a hash index for all 5,000 product guides.
- `knowledge/products/`: one editable fictional guide per original product ID (5,000 files).
- `knowledge/policies/`: three dated fictional business policies.
- `rag/chunks.jsonl`: 10,093 English RAG chunks, including one complete guide chunk per product.
- `manifest.json`: hashes and release counts.

Install Git LFS before cloning, or run `git lfs pull` after cloning. The large source database is otherwise only an LFS pointer. To query the two databases together, build again, or ingest the RAG corpus, see the [dataset and usage guide](docs/AGENT_DATASET.md). The [schema reference](docs/SCHEMA.md) lists all 27 tables, columns, keys, and joins. The [data contract](docs/DATA_CONTRACT.md) distinguishes source facts from fictional additions, and the [business assessment](docs/BUSINESS_ANALYSIS.md) reports measured indicators and limits.

The original import names do not identify credible retail products. All new guides are explicitly fictional interpretations linked by original `product_id`; only 50 products have dated curated list prices. The repository contains data for an agent, not an agent runtime or vector index.
