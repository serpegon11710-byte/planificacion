# normalize_plan_log.py

This script normalizes existing `plan.log` entries so their timestamp and message format
match the application's logging produced by `app.py`.

Location
- `tools/normalize_plan_log.py`

What it does
- Creates a timestamped backup of `plan.log` named `plan.log.bak.YYYYmmddHHMMSS`.
- Parses each line in `plan.log` and attempts to extract a timestamp and message.
- Rewrites `plan.log` so each line follows the format used by `app.py`:

  `YYYY-MM-DD HH:MM:SS,mmm LEVEL: message`

Notes
- The script is best-effort: unparseable lines are preserved but prefixed with a
  current timestamp and `INFO:` level.
- Requires Python 3.6+. If `python-dateutil` is available it will be used for
  more flexible parsing, otherwise the standard library is used.

Usage
1. From the project root, run:

```bash
python tools/normalize_plan_log.py
```

2. The script prints the path of the backup and a summary of rewritten lines.

Safety
- The original `plan.log` is kept as a backup; the script overwrites `plan.log`
  only after the backup is created.
