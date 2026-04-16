import os
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app, db, Item, Plan
from datetime import datetime, time, date

with app.app_context():
    item = Item.query.filter(Item.id.isnot(None)).first()
    assert item is not None, 'No item found'
    item_id = item.id
    project_id = item.project_id

    plan = Plan(
        item_id=item_id,
        kind='once',
        start_dt=datetime.combine(date(2026, 4, 30), time(9, 0)),
        note='__edit_test_original__',
        all_day=False,
        has_time=True,
    )
    db.session.add(plan)
    db.session.commit()
    plan_id = plan.id
    before_count = Plan.query.count()

payload = urlencode({
    'update_plan_id': str(plan_id),
    'plan_item_id': str(item_id),
    'selected_item': str(item_id),
    'kind': 'once',
    'date': '2026-04-30',
    'time_only': '10:15',
    'note': '__edit_test_updated__',
}).encode('utf-8')

req = Request(f'http://127.0.0.1:5000/project/{project_id}/', data=payload, method='POST')
resp = urlopen(req)
_ = resp.read()

with app.app_context():
    after_count = Plan.query.count()
    updated = Plan.query.get(plan_id)
    status_ok = True
    count_unchanged = after_count == before_count
    note_updated = updated is not None and updated.note == '__edit_test_updated__'
    time_updated = updated is not None and updated.start_dt is not None and updated.start_dt.time().strftime('%H:%M') == '10:15'

    print(f'status_ok: {status_ok}')
    print(f'count_unchanged: {count_unchanged}')
    print(f'note_updated: {note_updated}')
    print(f'time_updated: {time_updated}')

    if updated is not None:
        db.session.delete(updated)
        db.session.commit()

    if not (status_ok and count_unchanged and note_updated and time_updated):
        raise SystemExit(1)
