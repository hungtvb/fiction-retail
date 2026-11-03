# Fiction Retail — Unified Dataset

A fictional B2C retail dataset for SQL analysis and grounded retrieval. The standalone runtime is [`data/fiction_retail.sqlite`](data/fiction_retail.sqlite): 27 business tables, 5,000 stable Fiction-generated SKUs, 150,000 orders, and 100 scoped fulfillment cases. Its business reference date is **3 November 2026, Asia/Ho_Chi_Minh**. Rebasing dates does not make this live operational data.

The unchanged [DataHub SQLite source](https://github.com/datahub-project/static-assets/tree/main/datasets/fiction-retail) remains at [`data/fiction-retail.db`](data/fiction-retail.db) for provenance and rebuilding. Both large databases use Git LFS; run `git lfs pull` after cloning. The authored corpus contains 5,000 individual [product guides](knowledge/products), three dated [policies](knowledge/policies), and 10,093 [RAG chunks](rag/chunks.jsonl).

Build from the immutable source and authored guides:

```powershell
python -m scripts.rebuild_pack --unified --source data/fiction-retail.db --product-guides knowledge/products --output-dir .generated/release
```

The destination must be absent or empty. Use [the dataset guide](docs/AGENT_DATASET.md) for SQL and RAG examples, [the schema](docs/SCHEMA.md) for keys and indexes, [the data contract](docs/DATA_CONTRACT.md) for time and financial semantics, [the business assessment](docs/BUSINESS_ANALYSIS.md) for source-era measures, and [the source audit](docs/SOURCE_DB_AUDIT.md) before interpreting promotions, refunds, or capacity.
