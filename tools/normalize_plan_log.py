#!/usr/bin/env python3
"""
Normalize plan.log timestamps/messages to match app.py format:
  "YYYY-MM-DD HH:MM:SS,mmm LEVEL: message"
Creates a backup `plan.log.bak.YYYYmmddHHMMSS` before overwriting.
"""
import os, shutil, re, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE)
LOG_PATH = os.path.join(PROJECT_ROOT, 'plan.log')

if not os.path.exists(LOG_PATH):
    print('plan.log not found at', LOG_PATH)
    raise SystemExit(1)

bak_name = 'plan.log.bak.' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
BAK_PATH = os.path.join(PROJECT_ROOT, bak_name)
shutil.copy2(LOG_PATH, BAK_PATH)
print('Backup created:', BAK_PATH)

try:
    from dateutil import parser as date_parser
except Exception:
    date_parser = None

lines = open(LOG_PATH, 'r', encoding='utf-8', errors='replace').read().splitlines()
new_lines = []
parsed = 0
prefixed = 0

for ln in lines:
    s = ln.rstrip('\n')
    if not s.strip():
        new_lines.append('')
        continue

    dt = None
    rest = None

    # pattern 1: ISO-like with T and timezone
    m = re.match(r'^\s*(?P<ts>\d{4}-\d{2}-\d{2}T[^\s]+)\s+(?P<rest>.*)$', s)
    if m:
        ts = m.group('ts')
        rest = m.group('rest')
        try:
            if date_parser:
                dt = date_parser.parse(ts)
            else:
                dt = datetime.datetime.fromisoformat(ts)
        except Exception:
            dt = None

    # pattern 2: already in desired form or similar "YYYY-mm-dd HH:MM:SS,fff"
    if dt is None:
        m2 = re.match(r'^\s*(?P<ts>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}[\.,]\d+)\s+(?P<rest>.*)$', s)
        if m2:
            ts = m2.group('ts')
            rest = m2.group('rest')
            try:
                if date_parser:
                    dt = date_parser.parse(ts.replace(',', '.'))
                else:
                    # try parse with microseconds
                    fmt = '%Y-%m-%d %H:%M:%S.%f'
                    dt = datetime.datetime.strptime(ts.replace(',', '.'), fmt)
            except Exception:
                dt = None

    # fallback: try to parse a prefix up to 40 chars
    if dt is None:
        prefix = s[:40]
        try:
            if date_parser:
                dt = date_parser.parse(prefix)
                # rest is the remainder after the parsed textual prefix if it was at the start
                # best-effort: split original by first whitespace after parsed prefix length
                rest = s[len(prefix):].strip() or s
            else:
                # try isofrom
                dt = datetime.datetime.fromisoformat(prefix)
                rest = s[len(prefix):].strip() or s
        except Exception:
            dt = None

    if dt is not None:
        # format ts as 2026-04-16 12:29:13,520 (milliseconds)
        ts_out = dt.strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
        # try to extract level and message from rest
        level = 'INFO'
        msg = rest if rest is not None else s
        m3 = re.match(r'^(?P<level>[A-Z]+)[:\-\s]+(?P<msg>.*)$', msg)
        if m3:
            level = m3.group('level')
            msg = m3.group('msg')
        new_lines.append(f"{ts_out} {level}: {msg}")
        parsed += 1
    else:
        # leave the original message but prefix with current timestamp
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
        new_lines.append(f"{now} INFO: {s}")
        prefixed += 1

# write back
open(LOG_PATH, 'w', encoding='utf-8', newline='\n').write('\n'.join(new_lines) + '\n')
print('Rewrote', len(new_lines), 'lines (parsed:', parsed, 'prefixed:', prefixed, ')')
print('Original backed up to', BAK_PATH)
