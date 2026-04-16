import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app, db, Item, Plan
from datetime import datetime, time, date

with app.app_context():
    item = Item.query.filter(Item.id.isnot(None)).first()
    assert item is not None, 'No item found'

    plan = Plan(
        item_id=item.id,
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

    client = app.test_client()
    response = client.post(
        f'/project/{item.project_id}/',
        data={
            'update_plan_id': str(plan_id),
            'plan_item_id': str(item.id),
            'selected_item': str(item.id),
            'kind': 'once',
            'date': '2026-04-30',
            'time_only': '10:15',
            'note': '__edit_test_updated__',
        },
        follow_redirects=False,
    )

    after_count = Plan.query.count()
    updated = Plan.query.get(plan_id)

    ok = (
        response.status_code in (302, 303)
        and after_count == before_count
        and updated is not None
        and updated.note == '__edit_test_updated__'
        and updated.start_dt is not None
        and updated.start_dt.time().strftime('%H:%M') == '10:15'
    )

    print(f'status_ok: {response.status_code in (302, 303)}')
    print(f'count_unchanged: {after_count == before_count}')
    print(f'note_updated: {updated.note == "__edit_test_updated__"}')
    print(f'time_updated: {updated.start_dt is not None and updated.start_dt.time().strftime("%H:%M") == "10:15"}')

    if updated is not None:
        db.session.delete(updated)
        db.session.commit()

    if not ok:
        raise SystemExit(1)
