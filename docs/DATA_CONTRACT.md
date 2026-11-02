# Fiction Retail — Data Contract

Fiction is a synthetic retail business. Business documents are written for store employees; source IDs, creation provenance and checksums live in structured data rather than prose.

## Canonical identity and dated catalog

- The immutable upstream `fiction-retail.db` retains all **5,000 original products** with their original names, import prices and weights; the source is not a clean retail catalog.
- `product_enrichment` provides 50 curated product titles and types, each linked through the **same original `product_id`**. Since the original import names do not describe real product types, this is an explicit **fictional merchandising interpretation**, not a claim about manufacturers or historical SKU attributes.
- For these 50 entries, `curated_list_price_usd` and `curated_shipping_weight_kg` are internally plausible *synthetic business values*, **valid from 2024-05-01 (inclusive) to 2024-06-01 (exclusive)**. The prices/weights are fixed in `scripts/merchandising.py`. Do not confuse them with undated import `products.price`/`products.weight_kg` or earlier orders.
- A date-sensitive catalog lookup must check `catalog_effective_from <= :as_of < catalog_effective_to`. Outside that period, the curated offer is **not available**. Do not substitute a future price into April sales or April order investigations.
- Transaction facts use `order_items.unit_price`, quantity and line discounts at the relevant order date; these are historical transaction values. Comparing them directly against the May-2024 curated list price is **not** a valid historical price-variance or profit calculation.
- All 5,000 original IDs have a distinct fictional product guide in `knowledge/products/`, indexed by `knowledge_documents` in v0.4. The 4,950 new guides are not assertions about historical or manufacturer attributes. Only 50 products have a separately curated list price and packed weight; the remaining guides do not create a dated price offer.

Example when the baseline and extension are attached to one SQLite connection:

```sql
SELECT p.product_id, e.synthetic_display_name AS display_name,
       e.curated_list_price_usd AS list_price_usd,
       e.curated_shipping_weight_kg AS packed_weight_kg,
       e.catalog_effective_from, e.catalog_effective_to
FROM source.products AS p
JOIN extension.product_enrichment AS e ON e.product_id = p.product_id
WHERE :as_of >= e.catalog_effective_from
  AND :as_of < e.catalog_effective_to;
```

## Business facts and scope

- **Sales:** 564 assisted-sales opportunities, linked to real historical customer/order IDs when won. These are synthetic assisted-attribution scenarios, not proof of a real employee's performance.
- **Fulfillment:** 100 scoped April-2024 backorder cases with invented, timestamped stock evidence. They are **not** a complete warehouse inventory ledger. Do not infer present stock or global stock histories from a case-specific snapshot.
- **Pricing:** 20 selected SKUs have May-2024 unit costs and both margin/discount bounds. `product_pricing_constraints.policy_id = FR-PRICE-2024-05`, matching its company policy document. Proposed prices are not approved or executed sales.
- **Warehouse rules:** `fulfillment_policies.policy_id = FR-WH-2024-04`, matching the Warehouse Inventory Transfer Policy document, including the 24-hour stock-evidence limit and manager review.
- **Returns:** The April-2024 Returns & Refunds Policy is a hypothetical Fiction company rule. Actual baseline returns can contain refund anomalies, and order/return records alone do not prove approval or completion of payment.
- **Knowledge:** 5,000 individual product guides and three company policies. The first 50 guides include ten deeper selection/troubleshooting references. The guides contain no AI/RAG instructions, checksums or provenance metadata; those live in the database and corpus metadata.

## Source ownership and publishing

- `knowledge/products/` is the **editable source** for v0.4 product guides. `scripts/build_v04.py` reads and hashes one file per original product ID; it does not render guides from a common template. The original 50 curated files must remain byte-for-byte aligned with the v0.3 builder until their authoring source and v0.3 release are changed together. Policy text remains owned by `scripts/business_policies.py`.
- The `knowledge_documents` table maps source IDs and policy IDs to document SHA-256 hashes. `manifest.json` records the repository distribution hashes. Technical lineage stays in structured data rather than business prose.
- The unchanged original SQLite database, v0.4 runtime SQLite, individual Markdown files, JSONL RAG corpus, and manifest are committed. `data/fiction-retail.db` uses Git LFS. Evaluation ground truth and RetailIQ-specific reports are not committed.
- `scripts/build_agent_dataset.py` packages the source SQLite, v0.4 extension, 5,003 Markdown documents and JSONL RAG corpus. Its 5,000 source-product cards contain only actual import fields; its 50 curated-offer cards are visibly synthetic and dated. The corpus also contains one self-contained chunk per product guide, policy sections and schemas. See [agent dataset usage](AGENT_DATASET.md).
- All documentation, product characteristics, prices, costs and policies created by this extension are **fictional**. They are not verified manufacturer facts, real customer agreements or production security controls.

Further fictional attributes must be visibly marked as authored assumptions and linked to an original product ID. Do not backfill them into source transaction records.
