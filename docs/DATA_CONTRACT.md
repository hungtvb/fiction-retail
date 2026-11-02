# Fiction Retail — Data Contract

Fiction is a synthetic retail business. Business documents are written for store employees; source IDs, creation provenance and checksums live in structured data rather than prose.

## Canonical identity and dated catalog

- The immutable upstream `fiction-retail.db` retains all **5,000 original products** with their original names, import prices and weights; the source is not a clean retail catalog.
- `product_enrichment` provides 50 curated product titles and types, each linked through the **same original `product_id`**. Since the original import names do not describe real product types, this is an explicit **fictional merchandising interpretation**, not a claim about manufacturers or historical SKU attributes.
- For these 50 entries, `curated_list_price_usd` and `curated_shipping_weight_kg` are internally plausible *synthetic business values*, **valid from 2024-05-01 (inclusive) to 2024-06-01 (exclusive)**. The prices/weights are fixed in `scripts/merchandising.py`. Do not confuse them with undated import `products.price`/`products.weight_kg` or earlier orders.
- A date-sensitive catalog lookup must check `catalog_effective_from <= :as_of < catalog_effective_to`. Outside that period, the curated offer is **not available**. Do not substitute a future price into April sales or April order investigations.
- Transaction facts use `order_items.unit_price`, quantity and line discounts at the relevant order date; these are historical transaction values. Comparing them directly against the May-2024 curated list price is **not** a valid historical price-variance or profit calculation.
- Only 50 of 5,000 original IDs have curated merchandise and knowledge. An uncurated SKU has no corresponding product guide, and its old import name does not imply a credible retail product description.

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
- **Knowledge:** 50 product guides, including ten deeper selection/troubleshooting references, and three company policies. The guides contain no AI/RAG instructions, checksums or provenance metadata.

## Source ownership and publishing

- `scripts/product_knowledge.py`, `scripts/business_policies.py`, `scripts/merchandising.py` and the builders are the **single editable sources** for generated content and data. `knowledge/` in this repo is a **generated readable distribution**, not an independent authoring source. Rebuild the package and compare bytes/hashes when changing a guide or policy; do not edit Markdown and generator independently.
- The `knowledge_documents` table maps source IDs and policy IDs to document SHA-256 hashes. `v03_manifest.json` records release hashes. Technical lineage never appears inside the business documents.
- The original 96 MB SQLite database, generated SQLite outputs, evaluation ground truth, test cases and RetailIQ-specific reports are not committed.
- All documentation, product characteristics, prices, costs and policies created by this extension are **fictional**. They are not verified manufacturer facts, real customer agreements or production security controls.

**Stop rule:** extend the business data only when a specific mandatory course scenario cannot be supported by the selected source facts.
