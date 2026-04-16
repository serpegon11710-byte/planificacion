import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import get_occurrences, _span_dates_for_view, app
from datetime import datetime, date
view='week'
ref_date = datetime.fromisoformat('2026-04-26').date()
start,end = _span_dates_for_view(view, ref_date)
with app.app_context():
    evts = get_occurrences(start,end)
print('date|time|item|plan_id|note|all_day')
for e in evts:
    d=e['date'].isoformat()
    t = e['time'].isoformat() if e['time'] else ''
    print(f"{d}|{t}|{e['item'].name}|{e['plan'].id}|{e.get('note','')}|{e.get('all_day')}")
