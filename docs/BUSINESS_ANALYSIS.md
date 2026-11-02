# Fiction Retail: Business and Data Assessment

**Business status:** Fiction Retail is a synthetic e-commerce business for analysis and education, not a live retailer. The [DataHub source](https://github.com/datahub-project/static-assets/blob/main/datasets/fiction-retail/README.md) is a ten-table SQLite database with SHA-256 `9f95373e46219e880ae54f995b6f2c2c439c3746e500e484fe3ab2bf9ac55754`. Source orders run from **2023-01-01 through 2024-04-30**. These figures do not describe 2026 operations.

## Business model represented

The data connects `customers → orders → order_items → products → suppliers`, with promotions, warehouse inventory, shipments, and returns. It contains 50,000 customers, 150,000 orders, 346,202 order lines, 5,000 products, 500 suppliers, and 15 warehouses. Destinations include the US, UK, Canada, Germany, and Australia. `orders.total_amount` is recorded in USD, but there is no payment settlement table. The source inventory has no snapshot timestamp, so it does not establish stock at an order date or today.

The repository adds synthetic scenario data: 24 advisors in four sales teams, 564 opportunities and 1,008 activities, 100 backorder investigations with timestamped evidence, dated pricing constraints for 20 products, and fictional business policies. These are exercises linked to source IDs, not observations of actual staff or warehouse operations. See the [data contract](DATA_CONTRACT.md) and [agent dataset guide](AGENT_DATASET.md).

## Measured source indicators

| Indicator | Result | Definition and limitation |
|---|---:|---|
| All orders | 150,000 | `COUNT(*) FROM orders` |
| Orders with `delivered` status | 97,540 (65.03%) | Share of all orders in the dataset snapshot |
| Recorded value of `delivered` orders | USD 143,655,523.24 | `SUM(orders.total_amount)` where `order_status='delivered'`; **not reconciled cash revenue** |
| Mean value of `delivered` orders | USD 1,472.79 | `AVG(total_amount)` across those 97,540 orders |
| Orders with `returned` status | 11,934 (7.96%) | Share of all orders; not a delivered-order cohort return rate |
| Orders placed in April 2024 | 20,919 | `order_date` in `[2024-04-01, 2024-05-01)`; March had 16,966, so April's count is 23.3% higher |
| Inventory rows at/below reorder threshold | 793 of 11,476 | `quantity_on_hand - reserved_quantity <= reorder_threshold`; undated stock snapshot |
| Mean recorded shipping-to-delivery interval | 5.31 days | 109,474 shipments with a delivery date; not an on-time delivery measure |

For delivered orders, line value is `quantity * unit_price * (1 - discount_pct / 100)`. Electronics contributes USD 63,616,437.85 (44.3% of delivered-order value), jewelry USD 21,256,068.24 (14.8%), and home goods USD 14,552,959.19 (10.1%). Electronics and jewelry together account for about 59.1%. This synthetic mix does not establish profit: historical unit costs are unavailable.

The 11,934 return records include 2,977 `BUYER_REMORSE` and 2,398 `FIT_ISSUE` reasons, together 45.0% of returns. This makes expectation-setting and sizing useful scenarios to evaluate, but it does not prove that an agent would reduce returns. In 140 records, `refund_amount` exceeds the corresponding `orders.total_amount` by more than USD 0.01. Those records warrant reconciliation; the data does not prove fraud or completed payment.

## Quality and interpretation limits

- All 150,000 `orders.total_amount` values match their post-discount order-line sums within USD 0.02 in the local reconciliation. Four checked relationships (`orders→customers`, `order_items→orders/products`, and `returns→orders`) have no orphan IDs. The source does not enforce SQLite foreign keys; other relationships need separate checks when used.
- The 5,000 product IDs have 4,992 distinct import names, many of which are generic business jargon rather than merchandise descriptions. New product guides are explicitly fictional interpretations linked by ID, not manufacturer specifications or historical attributes.
- Source product price and weight have no validity period. Historical sale value belongs to `order_items`; a dated synthetic list price cannot be applied to April transactions. The 20 May 2024 synthetic unit costs cannot establish historical gross margins.
- The 100 extension cases cover selected backorders. There are 3,039 source orders with `backordered` status; do not extrapolate case outcomes to the full order set or all warehouses.
- The [source DB audit](SOURCE_DB_AUDIT.md) found 16,995 category-specific promotion links without an eligible order item and summed stock above nominal capacity at all 15 warehouses. Do not use those fields for unverified campaign attribution or capacity planning.
- There is no promised delivery date, return approval state, or refund payment confirmation. Therefore on-time SLA and completed-refund rates cannot be measured from these tables.
- The extension's 564 opportunities include 204 synthetic wins (36.2%) linked to delivered orders with recorded value USD 288,322.91. This assisted attribution is not evidence of employee performance or incremental sales.

## Useful agent tasks

| Job | Evidence | Answer check | Action boundary |
|---|---|---|---|
| Investigate an order | `orders`, `order_items`, `shipments`, `returns` | Join by order ID and cite status/dates | Do not promise delivery or a completed refund without confirmation |
| Explain a fictional product | Product guide linked to the original product ID | Cite the exact guide and state its synthetic provenance | Do not turn invented details into historical manufacturer claims |
| Review a backorder transfer | Case, latest snapshot, warehouse eligibility, matching policy | Stock evidence no older than 24 hours at the case cutoff, sufficient quantity, eligible route | Proposal only; manager approval required |
| Review a May 2024 price | Dated offer, cost/rule row, matching policy | Margin on proposed selling price and discount against list price | No price change without Commercial Manager approval |
| Triage unusual returns | `returns`, `orders`, dated return policy | Inspect the 140 above-order refund amounts | Do not infer fraud, approval, or payment completion |

An agent is most useful for multi-step cases that combine records, timestamps, and policy text. Simple aggregate KPIs should come from SQL or a dashboard rather than an embedding index. Before operational use, evaluate retrieval recall, citation accuracy, SQL correctness, refusal when evidence is missing, and time-to-checked-answer against a manual workflow on the same cases.

## Reproduce the main figures

Run against `data/fiction-retail.db`:

```sql
SELECT order_status, COUNT(*) AS orders, ROUND(SUM(total_amount), 2) AS value_usd
FROM orders GROUP BY order_status ORDER BY orders DESC;

SELECT p.category,
       ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct / 100.0)), 2) AS delivered_line_value_usd
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p ON p.product_id = oi.product_id
WHERE o.order_status = 'delivered'
GROUP BY p.category ORDER BY delivered_line_value_usd DESC;

SELECT COUNT(*) AS refund_above_order_count
FROM returns r JOIN orders o ON o.order_id = r.order_id
WHERE r.refund_amount > o.total_amount + 0.01;
```

Percentages are rounded. Re-run queries against the exact published source and a target system's KPI definitions before using results for decisions.
