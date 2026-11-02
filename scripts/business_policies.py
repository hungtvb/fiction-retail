"""Fiction Retail internal business-policy content. Publication metadata is in SQLite.

These policies are fictional company rules. The corpus does not contain AI-agent
behavior rules, source lineage or instructions for evaluating a model.
"""

POLICY_RETURNS = """# Returns and Refunds Policy

**Policy reference:** FR-RET-2024-04  
**Owner:** Customer Operations  
**Effective:** 1 April 2024 – 30 April 2024

## Purpose
This policy defines how customer return requests are received, assessed and resolved. It applies to purchases fulfilled by Fiction Retail.

## Return window
For standard products, customers may submit a return request within 30 calendar days after the recorded delivery date. The original order or proof of purchase is required. Requests outside this window must be escalated to Customer Operations for exception review rather than automatically approved.

## Condition and eligibility
An unopened, unused item with its supplied accessories is normally eligible for a standard return. A defective, damaged or incorrectly supplied item should be assessed separately and may require photographs or inspection. For food, personal-care and hygiene products, opened or used goods are not eligible for an ordinary change-of-mind return unless an applicable defect or legal obligation requires review.

## Customer support procedure
The support representative records the order, the returned item, the customer’s reason and the date received. A return request is not a confirmed refund. The team may ask for additional details, inspect the item or refer the case for an exception decision. Customers must be informed when additional verification is required.

## Refund review
Approved refunds are limited to the value and quantities eligible under the original transaction, subject to any applicable adjustment. Financial Operations must reconcile amounts that exceed the purchase value or disagree with the order records. The refund is complete only when the payment status has been confirmed; a recorded return request alone does not confirm a payment.

## Exceptions and responsibility
Customer Operations reviews disputes about delivery dates, item condition and policy exceptions. Financial Operations reviews unusual refund amounts. No representative may promise approval before required checks are complete.
"""

POLICY_TRANSFER = """# Warehouse Inventory Transfer Policy

**Policy reference:** FR-WH-2024-04  
**Owner:** Inventory Operations  
**Effective:** 1 April 2024 – 30 April 2024

## Purpose
This policy governs requests to move inventory between Fiction Retail warehouses when the assigned warehouse cannot fulfill an order.

## Transfer eligibility
An alternative warehouse may be considered only when it is authorized to serve the order’s route and has enough available units for the requested item quantity. Available units equal physical on-hand stock less units already reserved for other commitments. A transfer must not create a negative available-stock balance.

## Inventory information
The decision must use the latest available inventory observation for the relevant item and warehouse. Observations more than 24 hours old are not sufficient to authorize a transfer. When information is missing, outdated or inconsistent, Inventory Operations must request verification before advancing the request.

## Review and approval
An Inventory Operations specialist prepares a transfer request identifying the order, item, quantity, origin warehouse and proposed supplying warehouse. An authorized Operations Manager must approve the request before any transfer, reservation or order change is executed. Preparation of a transfer proposal does not reserve units.

## Exceptions
A warehouse without sufficient available stock or without an authorized transfer route cannot be chosen. If no qualifying warehouse can be confirmed, the order remains pending investigation and the fulfillment team reviews alternatives. Rejected requests do not change recorded stock.
"""

POLICY_PRICING = """# Product Pricing and Discount Approval Policy

**Policy reference:** FR-PRICE-2024-05  
**Owner:** Commercial Operations  
**Effective:** 1 May 2024 – 31 May 2024

## Purpose
Fiction Retail uses product-level cost and discount limits when reviewing proposed selling prices. These controls protect minimum gross margin and prevent unapproved discounting.

## Gross margin
For a proposed unit selling price, gross margin is the proposed price less the recorded unit cost for the same product and effective period, divided by the proposed price. The margin must meet or exceed the product’s active minimum gross-margin percentage. Margin is calculated on selling price, not as markup on cost.

## Discount limit
The proposed discount relative to the applicable dated catalog list price must not exceed the product’s active maximum-discount percentage. A proposal must satisfy both the margin requirement and the discount limit. Meeting one limit does not override the other.

## Approval authority
A Commercial Manager must approve a qualifying proposal before a catalog price is changed. Compliance with the numerical limits does not constitute approval. Proposals with missing costs, unsupported currency conversions or expired product rules are returned for review.

## Exceptions and records
Commercial Operations documents the product, current list price, proposed selling price, estimated margin, discount and effective date. Requests violating either limit must be revised or escalated under a separate authorized exception process. No price change may be represented as effective until the approved update is recorded.
"""
