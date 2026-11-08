# Fiction Lite v1.0.0 — verified development subset

**Status:** Created and independently verified from real Fiction Retail Full release (source file **199.38 MiB**, 209,063,936 bytes). This is a **derived test dataset**, not an alternative production / full acceptance release. No Supabase migration or change to the original Full dataset was made.

## Use Lite directly from GitHub (no Full download)

The repo tracks **`lite/fiction_retail_lite.sqlite.xz`** (1,989,656 bytes, 1.90 MiB), not the raw SQLite. After cloning `fiction-retail`, run these commands from the repository root:

```bash
python lite/prepare.py
python -m pytest -q lite/tests/test_fiction_lite_pack.py
```

`prepare.py` uses only the Python standard library: it verifies archive SHA-256, restores the 11.18 MiB SQLite without overwriting a different existing file, restores six exact source-verified knowledge documents, and runs 22 read-only Lite integrity gates. Git ignores locally generated files. To run an additional 13 source-comparison gates with the original 199 MiB release:

```bash
python lite/verify_fiction_lite.py --source data/fiction_retail.sqlite
```

Only the additional source comparison requires the Full Git LFS file. This is **not** RetailIQ LangGraph/MCP/LLM E2E acceptance.

**SHA-256:** XZ `8eae82668a140281eedcb9a438bd71c7729fd82e17a48254ca77dfa0ec1c37f6`; restored SQLite `ae387295f15f432f954e073320697071a1f25bee6bced4bda555db37c3f6f1ff`.

## Package

| File | Purpose |
|---|---|
| `fiction_retail_lite.sqlite.xz` | Versioned 1.90 MiB compressed SQLite; `prepare.py` restores the actual 11.18 MiB source-backed database |
| `manifest_lite.json` | Separate size, tables, variant, hash, parent source hash, sample KPI, selected document refs |
| `knowledge/policies/*.md` | 3 original exact policy documents, SHA-256 verified |
| `knowledge/products/*.md` | 3 selected exact product guides, SHA-256 verified |
| `golden_poc.json` | Independent SQL oracle for Top-3 October → inventory/rank-2 conversation |
| `qa_report.json` | Locally generated verifier report (ignored by Git; not a committed acceptance artifact) |
| `create_fiction_lite.py` | Reproducible source-backed selective builder; **never overwrites Full** |
| `build_knowledge.py` | Install/check 6 selected docs, exact source bytes, no network needed |
| `verify_fiction_lite.py` | Read-only integrity, SQLite FK, source/manifest hash, exact docs and business-case oracles |

## What is kept

- **All 100 Backorder cases**, all case events, snapshots, observations, movements, warehouse eligibility and required original orders/order items. Exact case-scoped source rows are preserved.
- **4,556 orders**, stratified across months and statuses, with their complete original order line, return and shipment records. The sampler also keeps all known refund anomalies (140 above order total; 350 above product-line amount), and additional return reasons and curated product examples.
- Catalog rows referenced by selected orders, all 50 curated enriched products and all 20 pricing constraints. Original product IDs/SKUs and all stock rows for selected products are unchanged. All 15 warehouses and 24 employees are present.
- All 3 policy document registry entries and 3 exact curated product guides + the corresponding document registry rows.
- The *original* 27 SQLite tables and associated indexes, with unchanged table-level schemas and foreign key relationships. Changes are strictly row selection plus explicit Lite provenance metadata.

**All numerical KPIs calculated from order history are Lite-specific**, because this is only ~3% of the 150,000 source orders. RetailIQ must not claim the Full October Top Seller or Full company revenue based on this Lite source. We **do** preserve original product IDs, case policy/cutoffs and the exact 100 case-scoped operational observations. Base inventory is undated, not 'real-time'.

## How to verify

```bash
python lite/prepare.py
# Stronger check, if you also have the pinned original file:
python lite/verify_fiction_lite.py --source /path/to/fiction_retail.sqlite
```

Expected: `PASS 35 gates ...`, depending on whether a Full source path is supplied. `qa_report.json` is overwritten by that run.

### How to rebuild without altering Full

```bash
python create_fiction_lite.py \
  --source /path/to/fiction_retail.sqlite \
  --output /some/new/folder/fiction_retail_lite.sqlite
# Run build_knowledge.py alongside the newly built manifest_lite.json
```

Requires the pinned Full SHA-256: `015b0a84d8d93870c6facd359347f4c039bc7fc570000890c581010d0451af42`. The script refuses to overwrite an existing output file and never writes to the input source. Use Python 3.12+ recommended.

## Try in RetailIQ (local testing only)

**No code or workflow in the RetailIQ GitHub repository was changed in creating this package.** To experiment locally (using the existing env-based configuration paths from `docs/FICTION_RUNTIME.md`):

1. Copy `fiction_retail_lite.sqlite` to `retailIQ/data/fiction/fiction_retail_lite.sqlite` and `manifest_lite.json` to `retailIQ/data/fiction/manifest_lite.json`.
2. Copy `knowledge/` into `retailIQ/data/fiction/knowledge_lite/`.
3. Configure the app process (not the default production release) with:

```dotenv
RETAILIQ_MODE=full
RETAILIQ_FICTION_DB=data/fiction/fiction_retail_lite.sqlite
RETAILIQ_FICTION_MANIFEST=data/fiction/manifest_lite.json
RETAILIQ_FICTION_KNOWLEDGE_ROOT=data/fiction/knowledge_lite
```

4. For read-only source queries, the existing `FictionStore.open` contract requires the upstream **schema generation** `fiction-retail-unified-v1.0.0`, which is intentionally retained in `pack_version`, plus the Lite variant, distinct binary SHA and row counts in `manifest_lite.json`. It can verify the schema/hash/metadata/SKU invariants; this compatibility has been checked against source code, but **the production RetailIQ runtime itself has not been executed against this file here**.
5. Use the included `golden_poc.json` rather than hardcoded Full expected sales/revenue results. Use the original Full DB & original manifest for official UC-01 live CI, release integrity and full-source acceptance. Do not replace `data/fiction/manifest.json` on `main` or overwrite the Full SQLite.

## Known limits and non-goals

- **Product RAG coverage:** this package contains 3 original guides only, not all 5,000. The source registry includes only those 3 and 3 verified policies. For broad Product RAG, use the Full knowledge corpus.
- **Full SQL oracles are not interchangeable** with Lite. For sales rankings, totals, refunds by general population or analytic aggregates, generate expectations from the Lite SQL itself.
- **Full release verifier** `scripts.verify_fiction_runtime` has full-population assumptions; do not report its population-specific assertions as Lite acceptance. This pack's dedicated verifier checks subset integrity separately.
- **No remote LLM / full LangGraph / browser tests were executed** while producing this pack. The QA report is real SQLite and source integrity evidence only.
- No change to pricing approval, read-only protections, authentication, HITL, source freshness or any real business data.

## Generation details

- Deterministic sample: SHA-256 seeded order choice, stratified by month and status, mandatory FK closure, all anomalous refund source records, all 100 bounded cases. No random floating sampling or synthetic business rows.
- The source binary, policy documents and three product guides were individually verified by SHA-256. The SQLite file was checked by `PRAGMA integrity_check`, `PRAGMA foreign_key_check`, canonical row content checksum and whole-binary SHA-256.
- The Full source hash is independently rechecked when running the verifier with `--source`.

**Source:** [`hungtvb/fiction-retail`](https://github.com/hungtvb/fiction-retail), `fiction-retail-unified-v1.0.0`, and RetailIQ `docs/FICTION_RUNTIME.md`.