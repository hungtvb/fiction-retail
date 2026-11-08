#!/usr/bin/env python3
"""Install six selected, source-verified Fiction Retail markdown documents for Lite."""
from pathlib import Path
from hashlib import sha256
import re
import json
ROOT=Path(__file__).resolve().parent
DOCS={
'policies/FR-PRICE-2026-11-03.md': '''# Product Pricing and Discount Approval Policy

**Policy reference:** FR-PRICE-2026-11-03  
**Owner:** Commercial Operations  
**Effective:** 3 November 2026 – 3 December 2026

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
''',
'policies/FR-RET-2026-10-04.md': '''# Returns and Refunds Policy

**Policy reference:** FR-RET-2026-10-04  
**Owner:** Customer Operations  
**Effective:** 4 October 2026 – 2 November 2026

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
''',
'policies/FR-WH-2026-10-04.md': '''# Warehouse Inventory Transfer Policy

**Policy reference:** FR-WH-2026-10-04  
**Owner:** Inventory Operations  
**Effective:** 4 October 2026 – 2 November 2026

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
''',
'products/001c1095-1d2a-4bbf-877d-c293399d00ac.md': '''# Utility Tool Organizer

## Overview

Polyester storage case with multiple pockets for holding hand tools.

## Tool specifications

Polyester case; multiple pockets.

## Selecting and using the tool

Tools not included. Compare the actual tools with pocket sizes, which are not individually specified.

## Care and maintenance

Wipe the polyester case clean and dry before storing tools.

## Shopping and support notes

This polyester organizer has multiple pockets for storing hand tools. The case does not include tools. Customers should compare pocket dimensions with their own tools, as pocket sizing and safe carrying weight are not specified. It is a storage accessory, not an impact-rated protective case.

## Additional product information

Tools are not included; no maximum weight or waterproof rating is specified.

## Frequently asked questions

### Are tools included?

No. The listing explicitly says tools are not included.

### Is it made of leather?

No. Polyester is the stated material.

### How much weight can it carry?

No certified load capacity is documented.
''',
'products/00572c89-2202-4d1b-a52e-06af7a10465b.md': '''# Cordless Screwdriver

## Overview

Compact 3.6 V lithium-battery screwdriver for ordinary household screwdriving.

## Tool specifications

3.6 V lithium battery; USB charging.

## Selecting and using the tool

Household screwdriving only. Use an appropriate bit and fastening task; do not interpret 3.6 V as a torque rating.

## Care and maintenance

Recharge through USB as specified and keep the tool dry.

## Shopping and support notes

The compact 3.6 V screwdriver is intended for ordinary household screws. It should be paired with an appropriate bit and is not described as a masonry drill. Voltage is not a measure of output torque. The product uses USB charging, but detailed charging time and torque settings are not supplied.

## Supported work

This 3.6 V rechargeable tool is intended for ordinary household screwdriving with an appropriate bit. It is not described as a drill for masonry or a high-torque impact driver.

## Charging and bit selection

Charge through the specified USB connection and keep the tool dry. Use the correct bit profile and size so that the screw head is not damaged. Voltage should not be treated as torque output.

## Support example

If the driver spins but a screw does not tighten, confirm the bit fits the screw and consider whether the material needs pilot-hole preparation. The documented product has no rated drilling function.

## Additional product information

No drill capability, torque specification, water protection or professional duty-cycle rating is supplied.

## Frequently asked questions

### Can it drill holes in masonry?

No. It is described only for household screwdriving.

### How is it charged?

USB charging is specified.

### What torque does it provide?

A torque rating is not included in the product description.
''',
'products/00e7bfdb-04ab-4165-8e2e-cd9b3828facc.md': '''# Hair Conditioning Mask

## Overview

Rinse-out hair conditioning treatment in a 250 mL pack.

## Formula and packaging

250 mL; rinse-out; external use.

## Choosing and applying the product

Follow usage directions. Apply only as the product label directs and rinse thoroughly; the formula is not described as leave-in.

## Care and maintenance

Close the container after use and avoid unintended eye contact.

## Shopping and support notes

Use this rinse-out conditioning product according to the packaging instructions after washing the hair. It is not identified as a leave-in treatment. Customers with color-treated or sensitive hair should review the complete ingredient information before relying on a compatibility claim.

## Additional product information

No documented color-safety guarantee, clinical repair claims or exact ingredient formula.

## Frequently asked questions

### Should I leave this product in my hair?

No. This product is a rinse-out treatment.

### What is the container size?

250 mL.

### Is it safe for color-treated hair?

Color-treated suitability is not documented; check the detailed label before recommending.
''',
}

def main():
    m=json.loads((ROOT/'manifest_lite.json').read_text())
    expected={x['path']:x['sha256'] for x in m['knowledge_documents_required']}
    if set(expected)!=set(DOCS):raise AssertionError('Knowledge paths and manifest differ')
    for path,original in DOCS.items():
        # Original source markdown is CRLF encoded; preserve trailing spaces in metadata lines.
        original=re.sub(r'(#{2,3} [^\n]+)\n\n', r'\1\n', original)
        if path.startswith('products/'): original+='\n'
        contents=original.replace('\n','\r\n').encode('utf-8')
        actual=sha256(contents).hexdigest()
        if actual!=expected[path]:raise AssertionError(f'Knowledge source mismatch: {path} {actual} != {expected[path]}')
        dest=ROOT/'knowledge'/path
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(contents)
    print('PASS',len(DOCS),'source-authenticated knowledge documents')

if __name__=='__main__':main()