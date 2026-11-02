"""Enrich immutable Fiction Retail v0.1 sidecar with product knowledge and operational evidence.

Creates a fully deterministic v0.2 sidecar and a separate provenance-labelled Markdown corpus.
No writes to the original Fiction database or v0.1 extension. Python 3.12+ stdlib only.
"""
from __future__ import annotations
import argparse
from collections import Counter
from contextlib import closing
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
from uuid import uuid5, NAMESPACE_URL
from scripts.product_knowledge import render as render_product_guide
from scripts.business_policies import POLICY_RETURNS, POLICY_TRANSFER

VERSION = 'fiction-retail-extension-v0.2.0'
SEED = 20261102
MONTH = '2024-04'
PROVENANCE = 'scenario_generated'

CATALOG = {
 'electronics': [('Wireless Earbuds', 'Bluetooth 5.3; USB-C charging; stereo audio', 'Bluetooth-capable device; USB-C power supply'), ('Portable Speaker', 'Bluetooth 5.2; 10-hour rated playback; USB-C charging', 'Bluetooth audio sources'), ('USB-C Hub', '4 USB ports; 1 HDMI port; 60 W passthrough', 'USB-C host with video output for HDMI use'), ('Laptop Sleeve', 'Polyester shell; padded compartment; 13-inch size', '13-inch laptop form factor'), ('Wireless Charging Pad', 'Qi-compatible wireless charger; USB-C input; power supply not included', 'Compatible Qi-enabled receiver and suitable USB-C power adapter')],
 'apparel': [('Everyday Cotton T-Shirt', '100% cotton; regular fit; machine wash cold', 'Apparel sizing chart required'), ('Lightweight Hoodie', 'Cotton blend; drawstring hood; machine wash cold', 'Select size from garment chart'), ('Travel Jacket', 'Nylon shell; zip front; wind-resistant finish', 'Outerwear, not waterproof certified'), ('Relaxed Fit Chinos', 'Cotton twill; machine wash cold', 'Check waist and inseam'), ('Everyday Polo Shirt', 'Cotton knit; short sleeves; machine wash cold', 'Check garment chart for collar, chest and length')],
 'books': [('Practical Photography Handbook', 'Paperback; illustrated chapters; English', 'No electronic format included'), ('Everyday Cooking Guide', 'Paperback; recipe illustrations; English', 'Food allergy suitability not guaranteed'), ('Introduction to Data Analysis', 'Paperback; worked examples; English', 'No digital course access included'), ('Urban Gardening Guide', 'Paperback; full-color photos; English', 'Regional planting advice may vary')],
 'home_goods': [('Ceramic Coffee Mug', 'Ceramic; 350 mL nominal capacity; hand wash recommended', 'Not certified for microwave use'), ('Cotton Throw Blanket', 'Cotton; 130 x 170 cm; cold machine wash', 'Indoor home textile'), ('LED Desk Lamp', 'LED; 5 W nominal; USB power', '5 V USB power supply'), ('Kitchen Storage Set', 'BPA-free plastic; three containers; hand wash', 'Not certified for oven use')],
 'beauty': [('Gentle Face Cleanser', '200 mL; fragrance free; external use only', 'Patch test recommended'), ('Daily Moisturizer', '50 mL; glycerin-based formula; external use', 'Skin suitability varies'), ('Hair Conditioning Mask', '250 mL; rinse-out; external use', 'Follow usage directions'), ('Hand Cream', '75 mL; glycerin-based; external use', 'Patch test recommended')],
 'food': [('Roasted Almond Snack', '200 g; contains tree nuts; shelf-stable unopened', 'Contains almonds; allergen warning'), ('Whole Grain Oats', '500 g; dry oats; shelf-stable unopened', 'Check label for cross-contact allergens'), ('Ground Coffee', '250 g; roasted coffee; sealed bag', 'Contains caffeine'), ('Dried Fruit Mix', '200 g; assorted dried fruit', 'Check label for sulfites')],
 'toys': [('Wooden Building Blocks', '30 wooden blocks; ages 3+; small-parts warning', 'Adult supervision for young children'), ('Puzzle Set', '120 pieces; ages 6+; cardboard', 'Not suitable for children under 3'), ('Remote Control Car', '2.4 GHz controller; batteries not included; ages 8+', 'Requires compatible batteries'), ('Art Activity Kit', 'Crayons and paper set; ages 5+', 'Adult supervision recommended')],
 'sports': [('Training Yoga Mat', '6 mm foam; 180 x 60 cm; wipe clean', 'Indoor exercise use'), ('Insulated Sports Bottle', '600 mL stainless steel; hand wash', 'Not designed for hot carbonated liquids'), ('Resistance Band Set', 'Three resistance bands; latex material', 'Contains latex'), ('Cycling Gloves', 'Polyester blend; padded palm', 'Select fit by hand circumference')],
 'tools': [('Hex Key Set', 'Metric 1.5–10 mm; steel; 9 pieces', 'Metric socket sizes'), ('Cordless Screwdriver', '3.6 V lithium battery; USB charging', 'Household screwdriving only'), ('Tape Measure', '5 m steel tape; metric and imperial markings', 'General measurement'), ('Utility Tool Organizer', 'Polyester case; multiple pockets', 'Tools not included')],
 'automotive': [('Car Phone Mount', 'Dashboard adhesive mount; adjustable grip', 'Verify surface suitability'), ('Interior Cleaning Cloths', 'Microfiber; pack of six; machine washable', 'Vehicle interior surfaces'), ('Tire Pressure Gauge', 'Digital; range 0–100 psi; battery powered', 'Valve type Schrader'), ('Emergency Flashlight', 'LED; AA battery powered', 'Batteries not included')],
 'jewelry': [('Minimalist Pendant Necklace', 'Stainless steel; adjustable chain; nickel content not verified', 'Check metal sensitivity'), ('Classic Stud Earrings', 'Stainless steel; pair; secure backs', 'Check metal sensitivity'), ('Braided Bracelet', 'Synthetic cord; adjustable clasp', 'Not designed for water immersion'), ('Everyday Ring', 'Stainless steel; assorted sizes', 'Use ring size guide')],
 'other': [('Reusable Shopping Tote', 'Cotton canvas; 15 L approximate volume', 'General retail use'), ('Travel Cable Pouch', 'Polyester; zip enclosure; three mesh pockets', 'Accessories not included'), ('Desk Notebook', 'A5; 120 ruled pages; paper', 'No digital synchronization'), ('Reusable Gift Bag', 'Paperboard; medium size; rope handles', 'Weight rating not certified')]
}

POLICIES = [
    ('FR-RET-2024-04', POLICY_RETURNS),
    ('FR-WH-2024-04', POLICY_TRANSFER),
]


def sha(path: Path) -> str:
 h = sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()


def stable(kind: str, text: str) -> str:
 return kind + '-' + str(uuid5(NAMESPACE_URL,f'{VERSION}:{SEED}:{text}'))


def iso(day: str, h: int, minute: int=0) -> str:
 return f'{day}T{h:02d}:{minute:02d}:00Z'


def day_plus(value: str, n: int) -> str:
 return (date.fromisoformat(value) + timedelta(days=n)).isoformat()


def create_tables(db):
 db.executescript('''
 CREATE TABLE product_enrichment (
  product_id TEXT PRIMARY KEY, source_name TEXT NOT NULL, category TEXT NOT NULL,
  synthetic_display_name TEXT NOT NULL, product_type TEXT NOT NULL,
  synthetic_specs TEXT NOT NULL, compatibility_note TEXT NOT NULL,
  provenance TEXT NOT NULL CHECK(provenance='scenario_generated'));
 CREATE TABLE knowledge_documents (
  document_id TEXT PRIMARY KEY, product_id TEXT, policy_id TEXT,
  kind TEXT NOT NULL CHECK(kind IN ('product_guide','business_policy')),
  relative_path TEXT NOT NULL UNIQUE, sha256 TEXT NOT NULL, provenance TEXT NOT NULL,
  CHECK ((product_id IS NOT NULL AND policy_id IS NULL AND kind='product_guide') OR
         (product_id IS NULL AND policy_id IS NOT NULL AND kind='business_policy')));
 CREATE TABLE operational_events (
  event_id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES fulfillment_cases,
  event_type TEXT NOT NULL, occurred_at TEXT NOT NULL, recorded_at TEXT NOT NULL,
  source_system TEXT NOT NULL, provenance TEXT NOT NULL CHECK(provenance='scenario_generated'),
  CHECK(recorded_at>=occurred_at));
 CREATE TABLE inventory_snapshots_v2 (
  snapshot_id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES fulfillment_cases,
  product_id TEXT NOT NULL, warehouse_id TEXT NOT NULL, observed_at TEXT NOT NULL,
  received_at TEXT NOT NULL, on_hand INTEGER NOT NULL CHECK(on_hand>=0),
  reserved INTEGER NOT NULL CHECK(reserved>=0 AND reserved<=on_hand),
  source_system TEXT NOT NULL, provenance TEXT NOT NULL CHECK(provenance='scenario_generated'),
  UNIQUE(case_id, warehouse_id, observed_at), CHECK(received_at>=observed_at));
 CREATE TABLE inventory_movements_v2 (
  movement_id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES fulfillment_cases,
  product_id TEXT NOT NULL, warehouse_id TEXT NOT NULL, occurred_at TEXT NOT NULL,
  delta_on_hand INTEGER NOT NULL, delta_reserved INTEGER NOT NULL,
  reason TEXT NOT NULL, provenance TEXT NOT NULL CHECK(provenance='scenario_generated'));
 CREATE TABLE fulfillment_decisions_v2 (
  case_id TEXT PRIMARY KEY REFERENCES fulfillment_cases,
  evidence_cutoff TEXT NOT NULL, outcome TEXT NOT NULL,
  selected_warehouse_id TEXT, source_age_minutes INTEGER,
  policy_id TEXT NOT NULL, requires_manager_approval INTEGER NOT NULL CHECK(requires_manager_approval IN (0,1)),
  evidence_quality TEXT NOT NULL, provenance TEXT NOT NULL CHECK(provenance='scenario_generated'));
 CREATE INDEX ix_v2_stock ON inventory_snapshots_v2(case_id,warehouse_id,observed_at);
 CREATE INDEX ix_v2_events ON operational_events(case_id,occurred_at);
 CREATE INDEX ix_v2_docs ON knowledge_documents(product_id,kind);
 ''')


def choose_products(src, cases):
 # Fixed 50 distinct product *types* for varied RAG questions: 5 electronics,
 # 5 apparel and 4 from each of 10 other categories. Retain all top-10 sellers.
 quotas={cat:(5 if cat in ('apparel','electronics') else 4) for cat in CATALOG}
 leaders=[r[0] for r in src.execute('''SELECT oi.product_id FROM orders o JOIN order_items oi ON oi.order_id=o.order_id
   WHERE o.order_status='delivered' AND o.order_date>='2024-04-01' AND o.order_date<'2024-05-01'
   GROUP BY oi.product_id ORDER BY SUM(oi.quantity) DESC, oi.product_id LIMIT 10''')]
 by_id={r['product_id']:r['category'] for r in src.execute('SELECT product_id,category FROM products')}
 chosen=[]
 counts=Counter()
 def add(pid):
  category=by_id[pid]
  if pid in chosen or counts[category]>=quotas[category]:return
  chosen.append(pid)
  counts[category]+=1
 for pid in leaders:add(pid)
 if len(chosen)!=len(leaders):
  raise ValueError('Top-ten seller coverage conflicts with category variety quota')
 # Priority to source-linked fulfillment cases, then fill category quota.
 for case in cases:add(case['product_id'])
 for pid,category in src.execute('SELECT product_id,category FROM products ORDER BY product_id'):
  add(pid)
 if len(chosen)!=50 or any(counts[c]!=q for c,q in quotas.items()):
  raise ValueError(f'Unable to select 50 category-balanced products: {dict(counts)}')
 info={r['product_id']:dict(r) for r in src.execute('SELECT product_id,name,category,brand,price,weight_kg FROM products WHERE product_id IN ('+','.join('?' for _ in chosen)+')',chosen)}
 if len(info)!=50:raise ValueError('Product source mismatch')
 return [info[pid] for pid in chosen]


def write_document(root,relative,body):
 path=(root/relative)
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(body,encoding='utf8',newline='\r\n')
 return sha(path)


def add_knowledge(db,root,products):
  tally=Counter()
  published_names=set()
  for p in products:
    cat=p['category'];templates=CATALOG[cat]
    index=tally[cat];tally[cat]+=1
    if index>=len(templates):
      raise ValueError(f'Insufficient unique product descriptions for {cat}: {index}')
    name,spec,compat=templates[index]
    if name in published_names:
      raise ValueError(f'Duplicate public product display name: {name}')
    published_names.add(name)
    item_type=name.lower().replace(' ','_')
    # Canonical public title for this selected product, independent of the
    # low-quality historical source name. Retain source label for lineage only.
    db.execute('INSERT INTO product_enrichment VALUES (?,?,?,?,?,?,?,?)',
       (p['product_id'],p['name'],cat,name,item_type,spec,compat,PROVENANCE))
    relative=f'products/{p["product_id"]}.md'
    body=render_product_guide(p,name,spec,compat)
    h=write_document(root,relative,body)
    db.execute('INSERT INTO knowledge_documents VALUES (?,?,?,?,?,?,?)',
      (stable('DOC',p['product_id']),p['product_id'],None,'product_guide',relative,h,PROVENANCE))
  for policy,body in POLICIES:
    relative=f'policies/{policy}.md'
    h=write_document(root,relative,body)
    db.execute('INSERT INTO knowledge_documents VALUES (?,?,?,?,?,?,?)',
      (stable('DOC',policy),None,policy,'business_policy',relative,h,PROVENANCE))


def add_cases(src,db):
 current=[dict(r) for r in db.execute('SELECT * FROM fulfillment_cases ORDER BY order_id')]
 existed={r['order_id'] for r in current}
 candidate=[dict(r) for r in src.execute('''SELECT o.order_id,o.order_date,oi.order_item_id,oi.product_id,oi.quantity
     FROM orders o JOIN order_items oi ON oi.order_id=o.order_id
     WHERE o.order_status='backordered' AND o.order_date BETWEEN '2024-04-03' AND '2024-04-23'
     AND oi.order_item_id=(SELECT MIN(x.order_item_id) FROM order_items x WHERE x.order_id=o.order_id)
     ORDER BY o.order_id''') if r['order_id'] not in existed]
 if len(candidate)<68:raise ValueError('Not enough backorders to expand to 100')
 wh=[r[0] for r in src.execute('SELECT warehouse_id FROM warehouses ORDER BY warehouse_id')]
 labels=['eligible_alternative','no_eligible_stock','ineligible_alternative','freshness_unknown']
 for n,item in enumerate(candidate[:68]):
  kind=labels[n%4];cid=stable('CASE',item['order_id']);day=item['order_date']
  assigned=wh[(n+3)%len(wh)];alt=wh[(n+5)%len(wh)]
  db.execute('INSERT INTO fulfillment_cases(case_id,order_id,order_item_id,product_id,request_qty,assigned_warehouse_id,case_date,scenario_tag) VALUES (?,?,?,?,?,?,?,?)',
   (cid,item['order_id'],item['order_item_id'],item['product_id'],item['quantity'],assigned,day,kind))
  stale=(kind=='eligible_alternative' and n//4<12)
  eligible=0 if kind=='ineligible_alternative' else 1
  for warehouse,allowed,reason in [(assigned,1,'ASSIGNED_WAREHOUSE'),(alt,eligible,'POLICY_REGION_BLOCK' if not eligible else 'SYNTHETIC_REGION_ALLOWED')]:
   db.execute('INSERT INTO warehouse_eligibility VALUES (?,?,?,?,?)',(cid,warehouse,allowed,reason,PROVENANCE))
  if kind != 'freshness_unknown':
   # Stock observations are synthetic (not the baseline's undated snapshot).
   for warehouse,onhand,reserved in [(assigned,0,0),(alt,item['quantity']+5,1 if kind in ('eligible_alternative','ineligible_alternative') else 0) if kind in ('eligible_alternative','ineligible_alternative') else (alt,0,0)]:
    if not stale: 
     db.execute('INSERT INTO inventory_observations VALUES (?,?,?,?,?,?,?,?)',
      (stable('OBS',cid+warehouse),cid,item['product_id'],warehouse,day,onhand,reserved,PROVENANCE))
  db.execute('INSERT INTO fulfillment_events VALUES (?,?,?,?,?)',(stable('EVT',cid+'opened'),cid,day,'order_submitted',PROVENANCE))
  db.execute('INSERT INTO fulfillment_events VALUES (?,?,?,?,?)',(stable('EVT',cid+'backordered'),cid,day_plus(day,1),'backorder_flagged',PROVENANCE))
 return current+[dict(r) for r in db.execute('SELECT * FROM fulfillment_cases WHERE order_id NOT IN ('+','.join('?' for _ in existed)+') ORDER BY order_id',sorted(existed))]


def add_ops_evidence(db,cases, legacy_case_ids):
 for c in sorted(cases,key=lambda x:x['case_id']):
  cid,pid,qty=c['case_id'],c['product_id'],c['request_qty']
  day=c['case_date'];nextday=day_plus(day,1)
  selected=db.execute('SELECT warehouse_id,eligible FROM warehouse_eligibility WHERE case_id=? ORDER BY warehouse_id',(cid,)).fetchall()
  alternative=next((r[0] for r in selected if r[0]!=c['assigned_warehouse_id']),None)
  if not alternative:raise ValueError('No alternative warehouse for case')
  is_old=cid in legacy_case_ids
  stale=(c['scenario_tag']=='eligible_alternative' and not is_old and
         db.execute('SELECT count(*) FROM inventory_observations WHERE case_id=?',(cid,)).fetchone()[0]==0)
  # Legacy v0.1 has date-stamped observations; label exact timestamp as scenario-generated.
  # New cases have a two-snapshot reservation lifecycle, except stale/missing cases.
  inputobs=[dict(r) for r in db.execute('SELECT * FROM inventory_observations WHERE case_id=? ORDER BY warehouse_id',(cid,))]
  if inputobs:
   for o in inputobs:
    onhand,reserved=o['on_hand'],o['reserved']
    # old: single snapshot at day 12:00; new: initial snapshot at day 12:00,
    # then reservation movement (if reserved>0) before later snapshot.
    first_obs=iso(day,12)
    db.execute('INSERT INTO inventory_snapshots_v2 VALUES (?,?,?,?,?,?,?,?,?,?)',
      (stable('SNAP',cid+o['warehouse_id']+'initial'),cid,pid,o['warehouse_id'],first_obs,iso(day,12,5),onhand,0 if not is_old else reserved,'fiction_synthetic_wms',PROVENANCE))
    if not is_old:
     if reserved:
      movement_time=iso(nextday,9,30)
      db.execute('INSERT INTO inventory_movements_v2 VALUES (?,?,?,?,?,?,?,?,?)',
       (stable('MOVE',cid+o['warehouse_id']),cid,pid,o['warehouse_id'],movement_time,0,reserved,'simulated_stock_reservation',PROVENANCE))
     db.execute('INSERT INTO inventory_snapshots_v2 VALUES (?,?,?,?,?,?,?,?,?,?)',
      (stable('SNAP',cid+o['warehouse_id']+'final'),cid,pid,o['warehouse_id'],iso(nextday,10),iso(nextday,10,5),onhand,reserved,'fiction_synthetic_wms',PROVENANCE))
  elif stale:
   # Evidence deliberately too old for the 24h policy, not incorrectly used as live stock.
   oldday=day_plus(day,-4)
   db.execute('INSERT INTO inventory_snapshots_v2 VALUES (?,?,?,?,?,?,?,?,?,?)',
      (stable('SNAP',cid+'stale'),cid,pid,alternative,iso(oldday,9),iso(oldday,9,10),qty+5,1,'fiction_synthetic_wms',PROVENANCE))
  def add_event(kind,occurred,recorded):
   db.execute('INSERT INTO operational_events VALUES (?,?,?,?,?,?,?)',
    (stable('OPEV',cid+kind),cid,kind,occurred,recorded,'fiction_synthetic_oms',PROVENANCE))
  add_event('order_registered',iso(day,9),iso(day,9,1))
  add_event('backorder_detected',iso(nextday,9),iso(nextday,9,1))
  add_event('allocation_evidence_checked',iso(nextday,10,30),iso(nextday,10,31))
  cutoff=iso(nextday,11)
  allrows=db.execute('SELECT warehouse_id,observed_at,received_at,on_hand-reserved AS available FROM inventory_snapshots_v2 WHERE case_id=? AND observed_at<=? AND received_at<=?',(cid,cutoff,cutoff)).fetchall()
  def age(o):
   t1=datetime.fromisoformat(o['observed_at'].replace('Z','+00:00'))
   t2=datetime.fromisoformat(cutoff.replace('Z','+00:00'))
   return int((t2-t1).total_seconds()//60)
  # Only the latest evidence per warehouse is decisive, never a convenient older reading.
  latest={}
  for row in allrows:
   wh=row['warehouse_id']
   if wh not in latest or row['observed_at']>latest[wh]['observed_at']:
    latest[wh]=row
  current=[row for row in latest.values() if age(row)<=1440]
  eligible_warehouses={r['warehouse_id'] for r in db.execute("SELECT warehouse_id FROM warehouse_eligibility WHERE case_id=? AND eligible=1",(cid,))}
  allowed=[row for row in current if row['warehouse_id']!=c['assigned_warehouse_id'] and row['warehouse_id'] in eligible_warehouses and row['available']>=qty]
  allowed.sort(key=lambda r:(-int(datetime.fromisoformat(r['observed_at'].replace('Z','+00:00')).timestamp()),r['warehouse_id']))
  any_alt=[row for row in current if row['warehouse_id']!=c['assigned_warehouse_id'] and row['available']>=qty]
  if not current:
   outcome='ABSTAIN_STALE_STOCK' if allrows else 'ABSTAIN_MISSING_STOCK'
   reason='STALE' if allrows else 'MISSING'
   selected_wh=None;age_minutes=min((age(x) for x in allrows),default=None)
  elif allowed:
   outcome='PROPOSE_TRANSFER_FOR_APPROVAL';reason='VERIFIED_ELIGIBLE';selected_wh=allowed[0]['warehouse_id'];age_minutes=age(allowed[0])
  elif any_alt:
   outcome='BLOCK_INELIGIBLE_WAREHOUSE';reason='POLICY';selected_wh=None;age_minutes=min(age(x) for x in any_alt)
  else:
   outcome='ESCALATE_NO_ELIGIBLE_STOCK';reason='INSUFFICIENT';selected_wh=None;age_minutes=min((age(x) for x in current),default=None)
  db.execute('INSERT INTO fulfillment_decisions_v2 VALUES (?,?,?,?,?,?,?,?,?)',
    (cid,cutoff,outcome,selected_wh,age_minutes,'MOCK-TRANSFER-2024',1 if outcome=='PROPOSE_TRANSFER_FOR_APPROVAL' else 0,reason,PROVENANCE))
  add_event('proposal_recorded_not_executed',iso(nextday,11),iso(nextday,11,1))


def build(source: Path,v01:Path,output:Path,knowledge:Path,force=False):
 source,v01,output,knowledge=map(lambda p:Path(p).resolve(),(source,v01,output,knowledge))
 if not source.is_file() or not v01.is_file():raise FileNotFoundError('Missing baseline or v0.1 extension')
 if source in (output,v01) or v01==output or knowledge in (source,v01,output):raise ValueError('Cannot overwrite source')
 if (output.exists() or knowledge.exists()) and not force:raise FileExistsError('Output already exists')
 expected_source=sha(source)
 with closing(sqlite3.connect(v01.as_uri()+'?mode=ro',uri=True)) as old:
  meta=dict(old.execute('SELECT key,value FROM metadata'))
  if meta.get('baseline_sha256')!=expected_source or meta.get('version')!='fiction-retail-extension-v0.1.0':
   raise ValueError('v0.1 extension does not match the supplied baseline')
  if old.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Invalid v0.1 SQLite')
 # Refuse overwrite unless explicitly forced; build complete data in temp dir first.
 with tempfile.TemporaryDirectory(prefix='fiction-v02-') as temp:
  temp=Path(temp)
  dbtmp=temp/'extension.sqlite';knowtmp=temp/'knowledge';knowtmp.mkdir()
  with closing(sqlite3.connect(v01.as_uri()+'?mode=ro',uri=True)) as old,closing(sqlite3.connect(dbtmp)) as new:
   old.backup(new)
  with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as src,closing(sqlite3.connect(dbtmp)) as db:
   src.row_factory=sqlite3.Row;db.row_factory=sqlite3.Row
   db.execute('PRAGMA foreign_keys=ON')
   create_tables(db)
   legacy_case_ids={r[0] for r in db.execute('SELECT case_id FROM fulfillment_cases')}
   cases=add_cases(src,db)
   if len(cases)!=100:raise ValueError(f'Expected 100 cases, got {len(cases)}')
   products=choose_products(src,cases)
   add_knowledge(db,knowtmp,products)
   add_ops_evidence(db,cases,legacy_case_ids)
   db.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)',('version',VERSION))
   db.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)',('parent_version','fiction-retail-extension-v0.1.0'))
   db.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)',('v02_packs','product_knowledge,operational_evidence'))
   db.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)',('freshness_policy','scenario_wms_24_hours_as_of_case_decision'))
   db.commit()
   if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or db.execute('PRAGMA foreign_key_check').fetchall():
    raise ValueError('Generated SQLite failed integrity')
   names=['product_enrichment','knowledge_documents','fulfillment_cases','operational_events','inventory_snapshots_v2','inventory_movements_v2','fulfillment_decisions_v2']
   counts={t:db.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in names}
   outcomes=dict(db.execute('SELECT outcome,COUNT(*) FROM fulfillment_decisions_v2 GROUP BY outcome'))
  output.parent.mkdir(parents=True,exist_ok=True)
  knowledge.parent.mkdir(parents=True,exist_ok=True)
  if force:
   output.unlink(missing_ok=True)
   if knowledge.exists():shutil.rmtree(knowledge)
  shutil.move(str(dbtmp),str(output));shutil.move(str(knowtmp),str(knowledge))
 return {'version':VERSION,'seed':SEED,'baseline_sha256':expected_source,'source_unchanged':sha(source)==expected_source,
         'rows':counts,'outcomes':outcomes,'extension_sha256':sha(output),
         'classification':'All v0.2 knowledge and events are scenario_generated; nothing observed or live'}


def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--source',type=Path,required=True);p.add_argument('--v01',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True);p.add_argument('--knowledge',type=Path,required=True)
 p.add_argument('--force',action='store_true');a=p.parse_args()
 print(json.dumps(build(a.source,a.v01,a.output,a.knowledge,a.force),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
