"""Generate small, deterministic, synthetic Sales and Fulfillment extensions for Fiction Retail.

Authoritative business data is NEVER modified; all enrichment is labelled scenario_generated.
No third-party dependencies. Python >=3.12.
"""
from __future__ import annotations
import argparse
from contextlib import closing
from datetime import date, timedelta
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import random
import sqlite3
from uuid import uuid5, NAMESPACE_URL

VERSION = 'fiction-retail-extension-v0.1.0'
SEED = 20261102
PERIOD = '2024-04'


def digest(path: Path) -> str:
    h = sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def uid(prefix: str, name: str) -> str:
    return prefix + '-' + str(uuid5(NAMESPACE_URL, f'{VERSION}:{SEED}:{name}'))


def schema(db: sqlite3.Connection) -> None:
    db.executescript('''
    PRAGMA foreign_keys=ON;
    CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE teams(team_id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE);
    CREATE TABLE employees(
      employee_id TEXT PRIMARY KEY, team_id TEXT NOT NULL REFERENCES teams,
      display_name TEXT NOT NULL, role TEXT NOT NULL CHECK(role='sales_advisor'),
      hire_date TEXT NOT NULL, active INTEGER NOT NULL CHECK(active IN (0,1)));
    CREATE TABLE sales_opportunities(
      opportunity_id TEXT PRIMARY KEY, employee_id TEXT NOT NULL REFERENCES employees,
      customer_id TEXT NOT NULL, order_id TEXT UNIQUE, opened_at TEXT NOT NULL,
      closed_at TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('won','lost')),
      scenario_tag TEXT NOT NULL, provenance TEXT NOT NULL DEFAULT 'scenario_generated',
      CHECK(closed_at >= opened_at),
      CHECK((status='won' AND order_id IS NOT NULL) OR (status='lost' AND order_id IS NULL)));
    CREATE TABLE sales_activities(
      activity_id TEXT PRIMARY KEY,
      opportunity_id TEXT NOT NULL REFERENCES sales_opportunities,
      employee_id TEXT NOT NULL REFERENCES employees,
      occurred_at TEXT NOT NULL,
      activity_type TEXT NOT NULL CHECK(activity_type IN ('consultation','follow_up','product_demo')),
      outcome TEXT NOT NULL, provenance TEXT NOT NULL DEFAULT 'scenario_generated');
    CREATE TABLE sales_targets(
      employee_id TEXT NOT NULL REFERENCES employees, month TEXT NOT NULL,
      metric_key TEXT NOT NULL CHECK(metric_key='delivered_merchandise_value_usd'),
      target_value_usd TEXT NOT NULL, provenance TEXT NOT NULL DEFAULT 'scenario_generated',
      PRIMARY KEY(employee_id,month,metric_key));
    CREATE TABLE fulfillment_cases(
      case_id TEXT PRIMARY KEY, order_id TEXT NOT NULL UNIQUE,
      order_item_id TEXT NOT NULL, product_id TEXT NOT NULL,
      request_qty INTEGER NOT NULL CHECK(request_qty>0),
      assigned_warehouse_id TEXT NOT NULL, case_date TEXT NOT NULL,
      scenario_tag TEXT NOT NULL CHECK(scenario_tag IN ('eligible_alternative','no_eligible_stock','ineligible_alternative','freshness_unknown')),
      provenance TEXT NOT NULL DEFAULT 'scenario_generated');
    CREATE TABLE inventory_observations(
      observation_id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES fulfillment_cases,
      product_id TEXT NOT NULL, warehouse_id TEXT NOT NULL,
      observed_at TEXT NOT NULL, on_hand INTEGER NOT NULL CHECK(on_hand>=0),
      reserved INTEGER NOT NULL CHECK(reserved>=0 AND reserved<=on_hand),
      provenance TEXT NOT NULL DEFAULT 'scenario_generated',
      UNIQUE(case_id,warehouse_id));
    CREATE TABLE warehouse_eligibility(
      case_id TEXT NOT NULL REFERENCES fulfillment_cases,warehouse_id TEXT NOT NULL,
      eligible INTEGER NOT NULL CHECK(eligible IN (0,1)),
      reason_code TEXT NOT NULL, provenance TEXT NOT NULL DEFAULT 'scenario_generated',
      PRIMARY KEY(case_id,warehouse_id));
    CREATE TABLE fulfillment_events(
      event_id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES fulfillment_cases,
      event_time TEXT NOT NULL, event_type TEXT NOT NULL,
      provenance TEXT NOT NULL DEFAULT 'scenario_generated');
    CREATE TABLE fulfillment_policies(
      policy_id TEXT PRIMARY KEY, policy_summary TEXT NOT NULL,
      requires_manager_approval INTEGER NOT NULL CHECK(requires_manager_approval IN (0,1)),
      provenance TEXT NOT NULL DEFAULT 'scenario_generated');
    CREATE INDEX ix_ops_employee_closed ON sales_opportunities(employee_id,closed_at);
    CREATE INDEX ix_activity_opp ON sales_activities(opportunity_id,occurred_at);
    CREATE INDEX ix_cases_product ON fulfillment_cases(product_id);
    CREATE INDEX ix_obs_case ON inventory_observations(case_id);
    ''')


def generate(source: Path, dest: Path, force: bool = False) -> dict:
    source, dest = source.resolve(), dest.resolve()
    if not source.is_file(): raise FileNotFoundError(source)
    if source == dest: raise ValueError('Refusing to overwrite baseline')
    if dest.exists():
        if not force: raise FileExistsError(f'{dest} already exists; specify --force for regeneration')
        dest.unlink()
    dest.parent.mkdir(parents=True, exist_ok=True)
    source_sha = digest(source)
    rng = random.Random(SEED)
    with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)) as src, closing(sqlite3.connect(dest)) as out:
        src.row_factory=sqlite3.Row
        out.execute('PRAGMA foreign_keys=ON')
        schema(out)
        # Only verified delivered orders are attributed to synthetic assisted sales.
        eligible_orders = [dict(r) for r in src.execute('''
          SELECT order_id,customer_id,order_date FROM orders
          WHERE order_status='delivered' AND order_date BETWEEN '2024-04-10' AND '2024-04-25'
          ORDER BY order_id''')]
        customers = [r[0] for r in src.execute('SELECT customer_id FROM customers ORDER BY customer_id')]
        backorders = [dict(r) for r in src.execute('''
          SELECT o.order_id,o.order_date,oi.order_item_id,oi.product_id,oi.quantity
          FROM orders o JOIN order_items oi ON oi.order_id=o.order_id
          WHERE o.order_status='backordered' AND o.order_date BETWEEN '2024-04-03' AND '2024-04-23'
          AND oi.order_item_id=(SELECT MIN(oi2.order_item_id) FROM order_items oi2 WHERE oi2.order_id=o.order_id)
          ORDER BY o.order_id LIMIT 32''')]
        warehouses = [r[0] for r in src.execute('SELECT warehouse_id FROM warehouses ORDER BY warehouse_id')]
        if len(eligible_orders)<250 or len(customers)<100 or len(backorders)<32 or len(warehouses)<2:
            raise ValueError('Source database does not contain enough historical baseline records')
        rng.shuffle(eligible_orders)
        rng.shuffle(customers)
        out.executemany('INSERT INTO metadata VALUES (?,?)',[
          ('version',VERSION),('seed',str(SEED)),('baseline_sha256',source_sha),
          ('source_file',source.name),('reporting_period',PERIOD),
          ('provenance','scenario_generated; not observed company operations'),
          ('temporal_note','Inventory observations are invented historical snapshots for selected exception cases only')])
        for t in range(4):out.execute('INSERT INTO teams VALUES (?,?)',(f'TEAM-{t+1:02d}',f'Sales Team {t+1:02d}'))
        profiles=[('HIGH_WIN_LOW_LEAD',12,.67,'12500'),('HIGH_VOLUME',35,.34,'24000'),
                  ('LOW_WIN_HIGH_ACTIVITY',25,.20,'18000'),('STANDARD',22,.40,'16000')]
        cursor=0
        opp_counter=0
        for idx in range(24):
            emp=f'EMP-{idx+1:03d}'
            profile, count, rate, target=profiles[idx%4]
            out.execute('INSERT INTO employees VALUES (?,?,?,?,?,?)',
                        (emp,f'TEAM-{idx//6+1:02d}',f'Sales Advisor {idx+1:02d}','sales_advisor','2023-01-01',1))
            out.execute('INSERT INTO sales_targets VALUES (?,?,?,?,?)',(emp,PERIOD,'delivered_merchandise_value_usd',target,'scenario_generated'))
            n_won=round(count*rate)
            for j in range(count):
                opp_counter+=1
                oid=uid('OPP',f'{emp}:{j}')
                if j<n_won:
                    order=eligible_orders[cursor];cursor+=1
                    customer_id,order_id=order['customer_id'],order['order_id']
                    closed=date.fromisoformat(order['order_date'])
                    opened=closed-timedelta(days=rng.randint(2,5))
                    status='won'
                else:
                    customer_id=customers[rng.randrange(len(customers))]
                    order_id=None
                    opened=date(2024,4,rng.randint(5,20))
                    closed=opened+timedelta(days=rng.randint(2,6))
                    status='lost'
                out.execute('INSERT INTO sales_opportunities(opportunity_id,employee_id,customer_id,order_id,opened_at,closed_at,status,scenario_tag) VALUES (?,?,?,?,?,?,?,?)',
                            (oid,emp,customer_id,order_id,opened.isoformat(),closed.isoformat(),status,profile))
                # Activities occur after opportunity opened, on/before close, even for lost opportunities.
                num_acts=3 if profile=='LOW_WIN_HIGH_ACTIVITY' else (2 if j%3==0 else 1)
                span=(closed-opened).days
                for k in range(num_acts):
                    offset=min(span,int((k+1)*span/(num_acts+1)))
                    at=opened+timedelta(days=offset)
                    kind=('consultation','follow_up','product_demo')[k%3]
                    outcome='customer_engaged' if k==0 else ('followup_completed' if k==1 else 'demo_completed')
                    out.execute('INSERT INTO sales_activities VALUES (?,?,?,?,?,?,?)',
                                (uid('ACT',f'{oid}:{k}'),oid,emp,at.isoformat(),kind,outcome,'scenario_generated'))
        # Each sample case refers to an existing backordered order + an actual order-item.
        # Do not use present snapshot to infer historical causality.
        for i,item in enumerate(backorders):
            cid=uid('CASE',item['order_id']);scenario=['eligible_alternative','no_eligible_stock',
                                                     'ineligible_alternative','freshness_unknown'][i%4]
            assigned=warehouses[i%len(warehouses)]
            alternative=warehouses[(i+1)%len(warehouses)]
            day=date.fromisoformat(item['order_date'])
            out.execute('INSERT INTO fulfillment_cases(case_id,order_id,order_item_id,product_id,request_qty,assigned_warehouse_id,case_date,scenario_tag) VALUES (?,?,?,?,?,?,?,?)',
                        (cid,item['order_id'],item['order_item_id'],item['product_id'],item['quantity'],assigned,day.isoformat(),scenario))
            out.execute('INSERT INTO fulfillment_events VALUES (?,?,?,?,?)',
                        (uid('EVT',cid+':opened'),cid,day.isoformat(),'order_submitted','scenario_generated'))
            out.execute('INSERT INTO fulfillment_events VALUES (?,?,?,?,?)',
                        (uid('EVT',cid+':backorder'),cid,(day+timedelta(days=1)).isoformat(),'backorder_flagged','scenario_generated'))
            if scenario != 'freshness_unknown':
                for warehouse,onhand,reserved in [
                    (assigned,0,0),
                    (alternative,item['quantity']+5,1) if scenario in ('eligible_alternative','ineligible_alternative') else (alternative,0,0)
                ]:
                    out.execute('INSERT INTO inventory_observations VALUES (?,?,?,?,?,?,?,?)',
                                (uid('OBS',cid+':'+warehouse),cid,item['product_id'],warehouse,day.isoformat(),onhand,reserved,'scenario_generated'))
            if scenario=='eligible_alternative':allowed,reason=1,'REGION_ELIGIBLE_SYNTHETIC'
            elif scenario=='ineligible_alternative':allowed,reason=0,'REGION_BLOCKED_SYNTHETIC'
            elif scenario=='no_eligible_stock':allowed,reason=1,'REGION_ELIGIBLE_SYNTHETIC'
            else:allowed,reason=1,'ELIGIBILITY_ASSUMED_STOCK_UNKNOWN'
            for warehouse,elig,why in [(assigned,1,'ASSIGNED_WAREHOUSE'),(alternative,allowed,reason)]:
                out.execute('INSERT INTO warehouse_eligibility VALUES (?,?,?,?,?)',
                            (cid,warehouse,elig,why,'scenario_generated'))
        out.executemany('INSERT INTO fulfillment_policies VALUES (?,?,?,?)',[
            ('transfer_review','Alternative warehouse stock and eligibility require manager review before transfer',1,'scenario_generated'),
            ('stock_unknown','Do not recommend stock allocation when no time-matched observation exists',1,'scenario_generated'),
            ('pricing_change','No automatic pricing changes; cost/margin policy not yet modeled',1,'scenario_generated')])
        out.commit()
        report={'dataset_version':VERSION,'seed':SEED,'source_sha256':source_sha,
            'rows':{name:out.execute('SELECT COUNT(*) FROM '+name).fetchone()[0] for name in
            ('teams','employees','sales_opportunities','sales_activities','sales_targets','fulfillment_cases','inventory_observations','warehouse_eligibility','fulfillment_events','fulfillment_policies')},
            'scenario_distribution':dict(out.execute('SELECT scenario_tag,COUNT(*) FROM fulfillment_cases GROUP BY scenario_tag')),
            'opportunity_outcomes':dict(out.execute('SELECT status,COUNT(*) FROM sales_opportunities GROUP BY status')),
            'disclaimer':'All extension data synthetic, baseline original unchanged; does not establish real business or causal claims'}
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--force',action='store_true')
    args=p.parse_args()
    print(json.dumps(generate(args.source,args.output,args.force),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
