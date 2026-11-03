# Product Knowledge Authoring and Review

The source database has 5,000 product IDs but its imported names are generic business phrases, not usable merchandise descriptions. The guides in `knowledge/products/` are **fictional merchandising profiles** assigned to those IDs. They do not describe verified manufacturers, historical sale items, or current inventory.

## Ownership and layout

Each product ID has one Markdown file. The original 50 curated guides are in `knowledge/products/<product_id>.md`; the other 4,950 are sharded under `knowledge/products/<first-two-ID-characters>/<product_id>.md`. Sharding keeps directory width manageable. The file itself is the editable knowledge source. `scripts/build_v04.py` reads these files, checks complete ID coverage and unique content hashes, and records their paths and SHA-256 values in `knowledge_documents`. The unified builder preserves their prose and adds SKU links in structured product and RAG metadata. Neither builder writes product prose.

The initial 4,950 additional guides were batch drafted as **synthetic content** from category-specific product concepts, configurations, care directions, and limits. They are distinct files with distinct titles and configuration details. They have **not** received individual human product review. Their value is as an internally consistent fictional RAG exercise; they must not be presented as verified retail catalog facts. The first 50 curated guides also have fictional provenance, despite their deeper descriptions.

## Editing a guide

1. Locate the file by the exact original `product_id`. Do not rename or reuse an ID.
2. Keep the product category and configuration internally coherent. State concrete specifications, selection advice, care, and important limits without implying independent certification.
3. Avoid copying prose between products. A reviewer should be able to explain what differentiates the edited product from other items of the same type.
4. Do not place source hashes, agent prompts, customer data, stock claims, or undated/current prices in customer-facing prose.
5. For one of the original 50 guides, update its authoring source in `scripts/product_knowledge.py` and rebuild v0.3 before rebuilding v0.4; the v0.4 builder rejects a mismatched legacy guide. For the other 4,950, edit the Markdown file directly.
6. Run the build and verification commands in [AGENT_DATASET.md](AGENT_DATASET.md). Review a sample of guides from every category and inspect near-duplicate wording before publishing.

`product_enrichment` contains dated list prices and shipping weights for only 50 products. A guide for any other product does not create a price or stock offer. If a user asks for a specification absent from the guide, an agent should say it is unavailable rather than infer it from the source import name.
