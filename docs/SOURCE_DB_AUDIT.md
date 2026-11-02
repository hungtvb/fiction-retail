# Source SQLite Data Quality Audit

**Scope:** Read-only audit of `data/fiction-retail.db`, the unchanged [DataHub Fiction Retail source](https://github.com/datahub-project/static-assets/blob/main/datasets/fiction-retail/README.md). SHA-256: `9f95373e46219e880ae54f995b6f2c2c439c3746e500e484fe3ab2bf9ac55754`. Audit date: 2026-11-02 (Asia/Saigon). The data is fictional and orders end on 2024-04-30; findings concern this snapshot, not a live business. The database was not modified.

## Assessment

**SQLite integrity is sound, but the source is not reliable for every business decision.** IDs and tested links are internally consistent. Promotions, warehouse capacity, and some refund values contain substantial semantic inconsistencies. Keep the source immutable, identify affected records in a derived quality layer, and avoid automatic agent actions based on those fields.

| Priority | Finding | Evidence in this snapshot | Consequence |
|---|---|---|---|
| High | Category-specific promotions without an eligible item | 16,995 of 20,361 orders with a category-specific promotion (83.47%) contain no order item in that promotion's `applies_to_category`. | A promotion agent cannot infer that the order qualified from `promo_id` alone. Investigate assignment and discount logic before measuring campaign performance. |
| High | Nominal warehouse capacity exceeded | Summed `inventory.quantity_on_hand` exceeds `warehouses.capacity_units` at all 15 warehouses, by 4.56–32.19 times. Total on-hand is 28,692,758 units against total nominal capacity of 3,258,000 (8.81 times). | Do not use these fields together for space planning or automated transfer decisions. `inventory` has no snapshot timestamp, which also prevents historical or current-stock claims. |
| Medium | Refund amount above purchase value | 140 of 11,934 returns (1.17%) have `refund_amount > orders.total_amount + 0.01`; 350 (2.93%) exceed the post-discount value of the returned product's order lines. | Queue for financial reconciliation. A return record does not prove that the refund was approved or paid; the cause of the difference is unknown. |
| Medium | Missing declared keys and indexes | All ten source tables have zero declared SQLite primary keys, zero declared foreign keys, and the source database has zero persistent indexes. Current ID values are unique, but the schema does not enforce this. | Future imports can break joins; large joins and correlated checks are slow. Add constraints/indexes to a **derived** database or query layer if needed, not to the canonical source file. |
| Medium | Product import labels do not describe merchandise | 5,000 product IDs have 4,992 distinct `name` values; samples include phrases such as “Future-proofed zero tolerance framework.” | Do not use import names as product specifications or identify fictional guides as manufacturer facts. |

### Important promotion convention

The actual SQLite uses the literal string **`'all'`** in `promotions.applies_to_category` for unrestricted promotions: 47 of 200 promotion rows have this value, and 6,609 orders use them. The upstream README describes `NULL` as the unrestricted value, but this database has no `NULL` in that column. Checks that treat every non-NULL value as a product category will overcount mismatches. This audit excludes `'all'` before assessing the 20,361 category-specific promo orders.

The actual SQLite declares `order_items.discount_pct` and `promotions.discount_pct` as `INTEGER` (percentage points), although the upstream README describes them as `REAL`. Use the actual schema when building tools.

## Checks that passed

- `PRAGMA integrity_check` returned `ok`; the source hash matches the pinned baseline. `PRAGMA foreign_key_check` returns no rows, but this is **not** a relationship test because the source declares no foreign keys.
- All ten logical ID columns have zero duplicates and zero NULLs. Eleven tested parent-child references have zero orphan rows: orders→customers/promotions, order items→orders/products, products→suppliers, inventory→products/warehouses, shipments→orders/warehouses, and returns→orders/products.
- All 150,000 orders have lines, and `orders.total_amount` matches the sum of `quantity * unit_price * (1 - discount_pct / 100)` within USD 0.02 for every order. No nonpositive order totals or quantities, negative line prices/refunds, or out-of-range line/promotion discounts were found.
- Date fields tested parse as SQLite dates. No orders predate customer signup, shipments predate orders, deliveries predate shipment, or returns predate order/delivery. Every order with `returned` status has a return row; every return row belongs to a `returned` order and names a product in that order.
- Shipment states align with the corresponding order statuses in this snapshot. No delivered order lacks a shipment, canceled order has a shipment, or returned order lacks a returned shipment.
- No promotion use falls outside its recorded validity interval or exceeds `max_uses`. No inventory row has negative on-hand/reserved amounts or `reserved_quantity > quantity_on_hand`. Product/warehouse inventory pairs are unique; all 5,000 products and all 15 warehouses appear in inventory.

## Reproduce the key findings

Run against the unchanged source SQLite. The category query may take several seconds because the source has no indexes.

```sql
PRAGMA integrity_check;

SELECT COUNT(*) AS category_specific_promo_orders
FROM orders o JOIN promotions pr ON pr.promo_id = o.promo_id
WHERE pr.applies_to_category <> 'all';
-- 20361

WITH order_categories AS (
  SELECT DISTINCT i.order_id, p.category
  FROM order_items i JOIN products p ON p.product_id = i.product_id
)
SELECT COUNT(*) AS mismatched_category_promo_orders
FROM orders o
JOIN promotions pr ON pr.promo_id = o.promo_id
LEFT JOIN order_categories oc
  ON oc.order_id = o.order_id AND oc.category = pr.applies_to_category
WHERE pr.applies_to_category <> 'all' AND oc.order_id IS NULL;
-- 16995

SELECT w.warehouse_id, w.capacity_units,
       SUM(i.quantity_on_hand) AS on_hand,
       ROUND(1.0 * SUM(i.quantity_on_hand) / w.capacity_units, 2) AS ratio
FROM warehouses w JOIN inventory i ON i.warehouse_id = w.warehouse_id
GROUP BY w.warehouse_id ORDER BY ratio DESC;
-- All 15 ratios exceed 1.0; maximum 32.19, minimum 4.56.

SELECT COUNT(*) AS refund_above_order_count
FROM returns r JOIN orders o ON o.order_id = r.order_id
WHERE r.refund_amount > o.total_amount + 0.01;
-- 140

WITH product_line_value AS (
  SELECT order_id, product_id,
         SUM(quantity * unit_price * (1 - discount_pct / 100.0)) AS value_usd
  FROM order_items GROUP BY order_id, product_id
)
SELECT COUNT(*) AS refund_above_returned_product_lines
FROM returns r JOIN product_line_value v
  ON v.order_id = r.order_id AND v.product_id = r.product_id
WHERE r.refund_amount > v.value_usd + 0.01;
-- 350
```

## Use in the agent dataset

For promotion eligibility, join to actual order lines and product categories; if the recorded promotion has no eligible item, report the inconsistency rather than asserting a valid discount. For refunds, present recorded amounts and request reconciliation rather than marking payment complete or fraudulent. For stock, use only the separately timestamped, case-scoped extension evidence under its policy; neither the source inventory nor the capacity totals establish available stock today. See the [schema reference](SCHEMA.md) and [agent dataset guide](AGENT_DATASET.md).
