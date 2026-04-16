<#
Start the Planificacion Flask app from PowerShell.

Usage:
  .\start_app.ps1
or (if your execution policy blocks scripts):
  powershell -ExecutionPolicy Bypass -File .\start_app.ps1

This script will try to activate a virtualenv at .\venv if present,
then run `python app.py` in the project directory.
#>
$scriptDir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
Set-Location $scriptDir

# Prefer dot-sourcing the activation script using an explicit path to avoid parsing issues
$activatePs = Join-Path $scriptDir '.venv\Scripts\Activate.ps1'
$activateBat = Join-Path $scriptDir '.venv\Scripts\activate.bat'
if (Test-Path $activatePs) {
  Write-Host ('Activating virtualenv .venv...')
  . $activatePs
} elseif (Test-Path $activateBat) {
  Write-Host ('Activating virtualenv (batch)...')
  cmd /c $activateBat
} else {
  Write-Host ('No virtualenv found at .venv - using system python.')
}

Write-Host ('Starting Flask app (app.py)...')
# If a PID file exists and process is running, warn and exit
$pidFile = Join-Path $scriptDir '.flask_pid'
if (Test-Path $pidFile) {
  try {
    $existing = Get-Content $pidFile -ErrorAction Stop
    if ($existing -and (Get-Process -Id [int]$existing -ErrorAction SilentlyContinue)) {
      Write-Host ('A Flask process is already recorded with PID {0}. Use stop_app.ps1 first or delete {1}.' -f $existing, $pidFile) -ForegroundColor Yellow
      exit 1
    } else {
      Remove-Item $pidFile -ErrorAction SilentlyContinue
    }
  } catch {
    # ignore
  }
}

# Start python in a new process and record its PID
try {
    $startInfo = Start-Process -FilePath python -ArgumentList 'app.py' -WorkingDirectory $scriptDir -PassThru
    Start-Sleep -Milliseconds 200
    if ($startInfo -and $startInfo.Id) {
      $startedPid = $startInfo.Id
      Write-Host ('Flask started (PID {0}). The application will record its PID in {1}.' -f $startedPid, $pidFile)
    } else {
        Write-Error ('Failed to start Flask process')
        exit 1
    }
} catch {
    Write-Error ('Failed to start process: {0}' -f $_)
    exit 1
}
