Param(
    [string]$Action = 'help',
    [string]$Message = ''
)

Set-StrictMode -Version Latest
$venv_py = Join-Path -Path (Get-Location) -ChildPath '.venv\Scripts\python.exe'
if (-not (Test-Path $venv_py)) {
    Write-Error "Python executable not found at $venv_py. Activate venv or adjust path."
    exit 1
}

function Run-FlaskDb {
    param($args)
    $env:FLASK_APP = 'app.py'
    & $venv_py -m flask db $args
}

switch ($Action.ToLower()) {
    'init' {
        Run-FlaskDb 'init'
        break
    }
    'migrate' {
        if (-not $Message) { Write-Error 'Provide -Message for migrate (e.g. -Message "Add foo" )'; exit 1 }
        Run-FlaskDb "migrate -m \"$Message\""
        break
    }
    'upgrade' {
        Run-FlaskDb 'upgrade head'
        break
    }
    'downgrade' {
        Run-FlaskDb 'downgrade -1'
        break
    }
    'help' {
        @"
Usage: .\scripts\migrate.ps1 -Action <init|migrate|upgrade|downgrade> [-Message "desc"]
Examples:
  .\scripts\migrate.ps1 -Action migrate -Message "Add start_date to project"
  .\scripts\migrate.ps1 -Action upgrade
  .\scripts\migrate.ps1 -Action downgrade
"@
        break
    }
    Default {
        Write-Error "Unknown action: $Action"
        exit 1
    }
}
