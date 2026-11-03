# Fiction Retail — Data Contract

The released runtime is `data/fiction_retail.sqlite`. It combines the ten immutable-source tables and 17 synthetic-extension tables without changing business IDs, transaction counts, monetary amounts, statuses, or row grain. This is a fictional educational dataset, not evidence of a live retailer. The original `data/fiction-retail.db` remains byte-for-byte unchanged with SHA-256 `9f95373e46219e880ae54f995b6f2c2c439c3746e500e484fe3ab2bf9ac55754`.

## Time and provenance

- Fixed business reference: **2026-11-03T00:00:00+07:00**, `Asia/Ho_Chi_Minh`. This is an as-of boundary, not a file creation time or proof of live refresh. The manifest records `build_generated_at_utc` separately.
- The latest observed business date across source and extension is 2024-04-30. The transformation shifts ISO dates and timestamp date prefixes forward **916 days**, making the latest observed date 2026-11-02. Time of day, fractional precision, UTC suffix/offset, event ordering, and durations are preserved.
- Source order dates translate from `[2023-01-01, 2024-04-30]` to `[2025-07-05, 2026-11-02]`. Catalog and policy *validity intervals* receive the same offset but are not counted as observed historical events. A future validity end is not a future completed transaction.
- `sales_targets.month` is the **start-month cohort label** `2026-10`; the exact translated target window is `period_start = 2026-10-04` to `period_end = 2026-11-03` (exclusive). It crosses calendar months. KPI queries must use these boundaries and must not treat `month` as a complete October calendar month.
- Source facts retain `upstream_source` provenance. Extension rows, product guides, policies, curated offers and generated SKUs are `scenario_generated`. Rebasing dates changes neither provenance nor freshness.

## Product identity and catalog

- `products.product_id` is the canonical database key. Every product has one unique, non-null Fiction-generated `sku`: `FR-` plus the first 16 uppercase hexadecimal characters of SHA-256(`product_id`). The builder checks collisions and never derives SKU from insertion order. It is not a GTIN, UPC, manufacturer code, variant, or evidence of a real listing.
- The original 5,000 import names, `products.price`, and `weight_kg` remain as recorded. Most names are poor merchandise labels. Import price and weight have no effective dates.
- `product_enrichment` contains 50 explicitly fictional interpreted products with a dated list price and packed shipping weight for `[2026-11-03, 2026-12-04)`. The other 4,950 products have no curated price. Use `catalog_effective_from <= :as_of AND :as_of < catalog_effective_to`; never backfill that price into historical `order_items`.
- All 5,000 product guides remain individually authored Markdown documents. They link to SQL through `knowledge_documents.product_id → products.product_id → products.sku`; RAG product metadata includes both IDs. Guide characteristics are fictional support content, not verified manufacturer specifications.

## Money, orders and returns

- Currency is USD. `orders.total_amount` is recorded order value, not settled revenue. `order_items.unit_price` is historical transaction price; `discount_pct` is integer percentage points. All 150,000 orders reconcile with their lines within USD 0.02 in the source audit.
- `delivered` is fulfillment status, not payment settlement. A `returns` row records a requested/processed return amount; it does not prove payment approval or payout. The 140 refunds above order value and 350 above the returned product's order-line net value remain visible for reconciliation.
- `promotions.applies_to_category='all'` is the actual unrestricted sentinel. The 16,995 category-specific promo links lacking an eligible order item remain recorded. Validate eligibility against order lines before campaign attribution; the rebase does not repair assignment logic.

## Inventory, cases and policies

- Base `inventory` has no observation timestamp. `last_restocked_date` is not a stock snapshot time. All 15 warehouses have nominal capacity below summed on-hand rows in the source. Do not treat this as verified live available stock or use capacity for automated transfer decisions.
- `inventory_snapshots_v2` and `operational_events` describe 100 selected synthetic fulfillment investigations, not an enterprise-wide inventory ledger. At a case's `evidence_cutoff_reached`, use only observations whose `received_at` and `observed_at` are no later than the cutoff; check the 24-hour freshness limit and warehouse eligibility. A qualifying result is a proposal requiring manager approval.
- The released cases contain zero snapshots with `received_at` after their case cutoff. The dataset therefore cannot demonstrate a real late-arrival exclusion outcome; the two-timestamp cutoff rule remains required for queries and future data.
- The warehouse and returns policies are valid for `[2026-10-04, 2026-11-03)`, with IDs `FR-WH-2026-10-04` and `FR-RET-2026-10-04`. The pricing policy `FR-PRICE-2026-11-03` and 20 cost/discount constraints apply to `[2026-11-03, 2026-12-04)`. These dates are translated historical/synthetic intervals, not newly negotiated real policies.
- Pricing margin is calculated on the proposed selling price; the discount cap is measured against the dated curated list price. Passing numerical limits does not constitute approval.

## Release and access

The unified file enforces PK, FK, and supported UNIQUE constraints with `PRAGMA foreign_keys=ON` during build; applications should enable that pragma on write connections. `PRAGMA integrity_check` and `PRAGMA foreign_key_check` are required release gates. `manifest.json` records the database file SHA-256, a canonical content checksum stored in `metadata.output_checksum`, the RAG hash, table counts, and retained quality findings. The content checksum excludes its own row to avoid a self-reference; `build_generated_at_utc` is intentionally outside the database so the binary can be reproduced.

The repository contains data and retrieval material. It does not provide live stock, settlement evidence, delivery promises, a vector index, an agent runtime, or application-specific SQL authorization. See [usage](AGENT_DATASET.md), [schema](SCHEMA.md), and [source audit](SOURCE_DB_AUDIT.md).
