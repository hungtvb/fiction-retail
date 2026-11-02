"""Build Fiction Retail business data v0.3 from the original source and v0.2.

The extension contains no precomputed fulfillment decisions or test answers.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
from decimal import Decimal
from scripts.business_policies import POLICY_PRICING
from scripts.merchandising import MERCHANDISING

BASELINE_HASH = '9f95373e46219e880ae54f995b6f2c2c439c3746e500e484fe3ab2bf9ac55754'
POLICY_ID = 'FR-PRICE-2024-05'
CATALOG_START = '2024-05-01'
CATALOG_END = '2024-06-01'
VERSION = 'fiction-retail-extension-v0.3.0'


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build(source: Path, v02: Path, output: Path, knowledge: Path, *, overwrite=False):
    source, v02, output, knowledge = (Path(p).resolve() for p in (source, v02, output, knowledge))
    if output in (source, v02) or source == v02:
        raise ValueError('Source, parent version and output paths must be distinct')
    if not source.is_file() or sha(source) != BASELINE_HASH:
        raise ValueError('Unexpected or missing canonical baseline SHA-256')
    if not v02.is_file() or not knowledge.is_dir():
        raise FileNotFoundError('v0.2 input and knowledge corpus are required')
    with sqlite3.connect(f'file:{v02.as_posix()}?mode=ro', uri=True) as parent_db:
        row = parent_db.execute("SELECT value FROM metadata WHERE key='version'").fetchone()
        origin = parent_db.execute("SELECT value FROM metadata WHERE key='baseline_sha256'").fetchone()
    if not row or row[0] != 'fiction-retail-extension-v0.2.0' or not origin or origin[0] != BASELINE_HASH:
        raise ValueError('Parent v0.2 version/source mismatch')
    if output.exists() and not overwrite:
        raise FileExistsError('output already exists; explicitly use --overwrite to rebuild')
    output.parent.mkdir(parents=True, exist_ok=True)
    original_v02_sha = sha(v02)
    # Never write to v0.2; work on a fresh copy.
    shutil.copyfile(v02, output)
    base = sqlite3.connect(f'file:{source.as_posix()}?mode=ro', uri=True)
    base.row_factory = sqlite3.Row
    db = sqlite3.connect(output)
    db.row_factory = sqlite3.Row
    baseline_ids = {r['product_id'] for r in base.execute('SELECT product_id FROM products')}
    # Parent identity and origin were validated before writing output.
    
    # Hold out ALL precomputed outcomes and case tags. They must not appear in agent SQL.
    case_count = db.execute("SELECT COUNT(*) FROM fulfillment_cases").fetchone()[0]
    if case_count != 100:
        raise ValueError(f"Expected 100 fulfillment cases, got {case_count}")
    db.execute('DROP TABLE fulfillment_decisions_v2')
    db.execute('ALTER TABLE fulfillment_cases DROP COLUMN scenario_tag')
    db.execute('ALTER TABLE sales_opportunities DROP COLUMN scenario_tag')
    # Last event supplies the real-as-simulated decision cutoff, NOT an answer.
    db.execute("UPDATE operational_events SET event_type='evidence_cutoff_reached' WHERE event_type='proposal_recorded_not_executed'")
    # One canonical policy document owns both stock verification and transfers.
    # Replace legacy rule-code-as-policy IDs with the actual business policy ID.
    db.execute("DELETE FROM fulfillment_policies")
    db.execute("INSERT INTO fulfillment_policies VALUES (?,?,?,?)", (
        'FR-WH-2024-04',
        'Warehouse transfer eligibility, 24-hour inventory verification and approval',
        1, 'scenario_generated'))

    # Curated May catalog is a *new, dated* offer, not a rewrite of historical
    # transaction prices or the old imported source price/weight.
    for col in ('curated_list_price_usd TEXT', 'curated_shipping_weight_kg TEXT',
                'catalog_effective_from TEXT', 'catalog_effective_to TEXT'):
        db.execute(f'ALTER TABLE product_enrichment ADD COLUMN {col}')
    enriched = list(db.execute('SELECT product_id, synthetic_display_name FROM product_enrichment'))
    if len(enriched) != 50:
        raise ValueError(f'Expected 50 enriched products, found {len(enriched)}')
    for r in enriched:
        name = r['synthetic_display_name']
        if name not in MERCHANDISING:
            raise ValueError(f'Missing merchandising values for {name}')
        list_price, weight = (Decimal(x) for x in MERCHANDISING[name])
        if not (Decimal('1.00') <= list_price <= Decimal('150.00')) or not (Decimal('0.03') <= weight <= Decimal('2.00')):
            raise ValueError(f'Invalid merchandising values for {name}')
        db.execute("""UPDATE product_enrichment SET curated_list_price_usd=?,
          curated_shipping_weight_kg=?,catalog_effective_from=?,catalog_effective_to=?
          WHERE product_id=?""",
          (str(list_price),str(weight),CATALOG_START,CATALOG_END,r['product_id']))
    if set(MERCHANDISING) != {r['synthetic_display_name'] for r in enriched}:
        raise ValueError('Merchandising catalog must cover exactly 50 guides')
    
    # Add one business table, with source-linked price boundaries and unambiguous USD decimals.
    db.execute('''CREATE TABLE product_pricing_constraints (
      product_id TEXT PRIMARY KEY, unit_cost_usd TEXT NOT NULL,
      min_margin_bps INTEGER NOT NULL CHECK(min_margin_bps BETWEEN 0 AND 9500),
      max_discount_bps INTEGER NOT NULL CHECK(max_discount_bps BETWEEN 0 AND 9000),
      effective_from TEXT NOT NULL, effective_to TEXT NOT NULL,
      policy_id TEXT NOT NULL, provenance TEXT NOT NULL CHECK(provenance='scenario_generated'),
      CHECK(effective_to > effective_from)
    )''')
    # Select products with both a guide and operational case; use the NEW dated catalog.
    eligible_products = [x[0] for x in db.execute('''SELECT DISTINCT e.product_id
      FROM product_enrichment e JOIN fulfillment_cases c ON c.product_id=e.product_id
      ORDER BY e.product_id''')]
    nominated = 'c3bb47e3-6638-4c55-ac33-ea36d4d28f11'
    chosen = [nominated] + [x for x in eligible_products if x != nominated]
    chosen = chosen[:20]
    if len(chosen) != 20 or any(x not in baseline_ids for x in chosen):
        raise ValueError('Pricing scope must contain 20 valid original Product IDs')
    constraints = []
    for i, pid in enumerate(chosen):
        src = db.execute('SELECT curated_list_price_usd FROM product_enrichment WHERE product_id=?', (pid,)).fetchone()
        list_price = Decimal(src['curated_list_price_usd']).quantize(Decimal('0.01'))
        if list_price <= 0:
            raise ValueError('Non-positive current catalog list price')
        cost = (list_price * Decimal(str([.48, .55, .63, .69][i % 4]))).quantize(Decimal('.01'))
        min_margin_bps = [1500, 1800, 2000][i % 3]
        max_discount_bps = [500, 1000, 1500][i % 3]
        if (list_price - cost) / list_price < Decimal(min_margin_bps) / 10000:
            raise ValueError('Generated cost violates the active minimum margin rule')
        db.execute('INSERT INTO product_pricing_constraints VALUES (?,?,?,?,?,?,?,?)',
                   (pid, str(cost), min_margin_bps, max_discount_bps, CATALOG_START, CATALOG_END, POLICY_ID, 'scenario_generated'))
        constraints.append({'product_id': pid, 'list_price_usd': str(list_price), 'unit_cost_usd': str(cost),
                            'min_margin_bps': min_margin_bps, 'max_discount_bps': max_discount_bps,
                            'provenance': 'scenario_generated'})
    if len(constraints) != 20:
        raise ValueError('Pricing rules did not cover 20 products')
    
    # Publish company-facing policy text, not ingestion/evaluation instructions.
    policy_text = POLICY_PRICING
    policy_path = knowledge / 'policies' / (POLICY_ID + '.md')
    policy_path.write_text(policy_text, encoding='utf-8')
    doc_id = 'DOC-' + hashlib.sha256(POLICY_ID.encode()).hexdigest()[:24]
    db.execute('INSERT INTO knowledge_documents VALUES (?,?,?,?,?,?,?)',
               (doc_id, None, POLICY_ID, 'business_policy', f'policies/{POLICY_ID}.md', sha(policy_path), 'scenario_generated'))
    
    # Version metadata only; do not carry answer labels inside the runtime database.
    for k, v in {
        'version': VERSION,
        'parent_version': 'fiction-retail-extension-v0.2.0',
        'parent_v02_sha256': original_v02_sha,
        'v03_packs': 'dated_catalog_merchandising,pricing_constraints,product_knowledge,operational_evidence',
        'curated_catalog_valid_from': CATALOG_START,
        'curated_catalog_valid_until': CATALOG_END,
        'runtime_answer_labels': 'excluded',
        'data_scope': 'partial scenario-linked operational evidence; not full-company WMS history',
    }.items():
        db.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)', (k, v))
    db.commit()
    db.execute('VACUUM')
    db.close()

    # Release manifest describes only the business data and its source lineage.
    doc_count = db_read_one(output, 'SELECT COUNT(*) AS count FROM knowledge_documents')['count']
    manifest = {'dataset_version': VERSION, 'source_baseline_sha256': BASELINE_HASH,
                'parent_v02_sha256': original_v02_sha, 'runtime_sha256': sha(output),
                'runtime_db': output.name, 'pricing_product_count': len(constraints),
                'fulfillment_scenario_count': case_count, 'knowledge_document_count': doc_count,
                'curated_catalog_valid_from': CATALOG_START,
                'curated_catalog_valid_until': CATALOG_END,
                'corpus_files': {str(p.relative_to(knowledge)): sha(p)
                                 for p in sorted(knowledge.rglob('*.md'))},
                'answer_labels_in_runtime': False}
    dump(output.parent / 'v03_manifest.json', manifest)
    base.close()
    return manifest


def db_all(path,query,args=()):
    with sqlite3.connect(path) as c:
        c.row_factory=sqlite3.Row
        return [dict(r) for r in c.execute(query,args)]


def db_read_one(path,query,args=()):
    return db_all(path,query,args)[0]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--v02',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--knowledge',type=Path,required=True)
    p.add_argument('--overwrite',action='store_true')
    a=p.parse_args()
    print(json.dumps(build(a.source,a.v02,a.output,a.knowledge,overwrite=a.overwrite),indent=2))

if __name__=='__main__':
    main()
