## plan.log format

The application `app.py` configures a FileHandler with the logging format:

  `%(asctime)s %(levelname)s: %(message)s`

Where `asctime` uses the date/time format:

  `YYYY-MM-DD HH:MM:SS,fff`

Examples

- `2026-04-16 12:29:13,520 INFO: Wrote PID 16768 to D:\Proyectos\Planificacion\.flask_pid`
- `2026-04-16 12:30:09,155 INFO: stop_app.ps1 requested KILL of PID 16768 (via -Kill) by Sergio`

Guidelines
- When appending to `plan.log` from other tools (e.g. `stop_app.ps1`), follow the
  same format to keep the file consistent and easy to parse.
- Use UTF-8 encoding when writing to the file.
- Keep log entries short and prefixed by a timestamp and level (e.g. `INFO`, `ERROR`).

Recommended helper (PowerShell)

Use a small helper function to append lines with the same format, for example (already
used in `stop_app.ps1`):

```powershell
function Log-Plan { param([string]$msg)
  $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss,fff")
  Add-Content -Path $logFile -Value ("{0} INFO: {1}" -f $ts, $msg) -Encoding UTF8
}
```
