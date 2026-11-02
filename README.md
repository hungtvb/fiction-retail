# Fiction Retail

A small, fictional retail business dataset with linked product catalog, sales, inventory and company knowledge. Its historical [Fiction Retail E-Commerce source](https://www.kaggle.com/datasets/nasalakshay/fiction-retail-e-commerce-dataset) remains outside Git.

## Run locally

Requires Python 3.12+ and the original `fiction-retail.db`:

```bash
python -m scripts.rebuild_pack --source /path/to/fiction-retail.db --output-dir .generated/fiction-v03
```

The generated SQLite extension and product/policy documents are under `.generated/fiction-v03/`. See [Data Contract](docs/DATA_CONTRACT.md) for product identity, scope and limitations.
