import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import app
from app import Plan
with app.app_context():
    p = Plan.query.get(11)
    if not p:
        print('Plan 11 not found')
    else:
        print('id',p.id)
        print('item',p.item.name if p.item else None)
        print('kind',p.kind)
        print('freq',p.freq)
        print('weekdays',p.weekdays)
        print('start_dt',p.start_dt)
        print('has_time',getattr(p,'has_time',None))
        print('all_day',getattr(p,'all_day',None))
        print('deleted',getattr(p,'deleted',None))
