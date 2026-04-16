import sqlite3
from datetime import datetime
p='plan.db'
conn=sqlite3.connect(p)
cur=conn.cursor()
print('id|item_id|kind|freq|start_dt|has_time|all_day|deleted|note')
for row in cur.execute('SELECT id,item_id,kind,freq,start_dt,has_time,all_day,deleted,note FROM plan'):
    sid=row[0]
    start=row[4]
    try:
        sd = datetime.fromisoformat(start) if start else None
        start_str = sd.isoformat() if sd else ''
    except Exception:
        start_str = str(start)
    print(f"{row[0]}|{row[1]}|{row[2]}|{row[3]}|{start_str}|{row[5]}|{row[6]}|{row[7]}|{row[8]}")
conn.close()
