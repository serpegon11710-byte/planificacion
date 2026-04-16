import os
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import app, db, Project, Item, Plan
from datetime import datetime, date, time

with app.app_context():
    project = Project.query.first()
    assert project is not None, 'No project found'
    item = Item(name='__cascade_test_item__', project_id=project.id)
    db.session.add(item)
    db.session.commit()
    item_id = item.id
    project_id = project.id

    plan = Plan(item_id=item_id, kind='once', start_dt=datetime.combine(date(2026, 4, 30), time(9, 0)), note='__cascade_test_plan__', has_time=True, all_day=False)
    db.session.add(plan)
    db.session.commit()
    plan_id = plan.id

req = Request(f'http://127.0.0.1:5000/item/{item_id}/delete', data=urlencode({}).encode('utf-8'), method='POST')
resp = urlopen(req)
_ = resp.read()

with app.app_context():
    item_exists = db.session.get(Item, item_id) is not None
    plan_exists = db.session.get(Plan, plan_id) is not None
    print(f'item_deleted: {not item_exists}')
    print(f'plan_deleted: {not plan_exists}')
    if item_exists:
        db.session.delete(db.session.get(Item, item_id))
        db.session.commit()
    if plan_exists:
        db.session.delete(db.session.get(Plan, plan_id))
        db.session.commit()
    if item_exists or plan_exists:
        raise SystemExit(1)
