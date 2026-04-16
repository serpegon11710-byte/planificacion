<#
Stop the Flask app started by start_app.ps1. Reads .flask_pid and stops that process only.
#>
param([switch]$Force, [switch]$List, [switch]$Help, [int]$Kill)

$scriptDir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
Set-Location $scriptDir

# Ensure console uses UTF-8 for input/output to avoid garbled accented characters
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding  = [System.Text.Encoding]::UTF8

$pidFile = Join-Path $scriptDir '.flask_pid'
 $logFile = Join-Path $scriptDir 'plan.log'
function Log-Plan {
    param([string]$msg)
    try {
        # match Python logging formatter: "%(asctime)s %(levelname)s: %(message)s"
        # where asctime looks like: 2026-04-16 12:29:13,520
        $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss,fff")
        Add-Content -Path $logFile -Value ("{0} INFO: {1}" -f $ts, $msg) -Encoding UTF8
    } catch {
        # ignore logging errors to avoid breaking stop logic
    }
}
if ($Help) {
    Write-Host ('Uso: stop_app.ps1 [-Force] [-List] [-Help] [-Kill <pid>]') -ForegroundColor Cyan
    Write-Host ('Equivalente en batch: stop_app.bat [/f] [/l] [/h] [/k <pid>]') -ForegroundColor Cyan
    Write-Host ('')
    Write-Host ('Opciones:') -ForegroundColor Cyan
    Write-Host ( '  -Force    /f    Forzar detenci' + [char]0x00F3 + 'n (si no se encuentra .flask_pid buscar' + [char]0x00E1 + ' procesos que contengan ''app.py'' y los detendr' + [char]0x00E1 + ').' ) -ForegroundColor Cyan
    Write-Host ( '  -List     /l    Listar el PID almacenado (si existe) y los PID de los procesos que ser' + [char]0x00E1 + 'n detenidos, sin detenerlos.' ) -ForegroundColor Cyan
    Write-Host ( '  -Kill     /k    Detener el PID indicado. Ej: stop_app.ps1 -Kill 12345  (batch: stop_app.bat /k 12345)' ) -ForegroundColor Cyan
    Write-Host ( '  -Help     /h    Mostrar esta ayuda.' ) -ForegroundColor Cyan
    exit 0
}

# If user passed -Kill <pid>, attempt to stop that PID directly and exit
if ($Kill) {
    try {
        Write-Host ( 'Attempting to stop PID {0} (requested via -Kill)...' -f $Kill )
        Log-Plan ("stop_app.ps1 requested KILL of PID {0} (via -Kill) by {1}" -f $Kill, $env:USERNAME)
        Stop-Process -Id $Kill -Force -ErrorAction Stop
        Write-Host ( 'Stopped PID {0}.' -f $Kill )
        exit 0
    } catch {
        Write-Host ( 'No se pudo detener el PID {0}: {1}' -f $Kill, $_ ) -ForegroundColor Yellow
        Write-Host ('Puede intentar con -Force: stop_app.ps1 -Force  o desde batch: stop_app.bat /f') -ForegroundColor Yellow
        Write-Host ('O use -Kill con otro PID: stop_app.ps1 -Kill <pid>  (busque PID en plan.log)') -ForegroundColor Yellow
        exit 1
    }
}

if (-not (Test-Path $pidFile)) {
    if (-not $Force -and -not $List) {
        Write-Host ( 'No se ha encontrado el indentificador PID de la aplicaci' + [char]0x00F3 + 'n en "{0}".' -f $pidFile ) -ForegroundColor Yellow
        Write-Host ('') -ForegroundColor Yellow
        Write-Host ( 'Para detenerlo, invoca: ''stop_app.bat /k <PID>''  ' + [char]0xF3 + '  ''stop_app.ps1 -Kill <PID>''' ) -ForegroundColor Yellow
        Write-Host ( 'NOTA: consulta el PID en el fichero de log "{0}"' -f $logFile ) -ForegroundColor Yellow
        Write-Host ('') -ForegroundColor Yellow
        Write-Host ( 'Tambi' + [char]0x00E9 + 'n puedes forzar la detenci' + [char]0x00F3 + 'n, invocando: ''stop_app.bat /f''  ' + [char]0x00F3 + '  ''stop_app.ps1 -Force''' ) -ForegroundColor Yellow
        Write-Host ( 'NOTA: Esto puede matar procesos python de otras aplicaciones.' ) -ForegroundColor Yellow
        Write-Host ('') -ForegroundColor Yellow
        Write-Host ( 'Utilice ''stop_app.bat /h''   ' + [char]0x00F3 + '  ''stop_app.ps1 -Help'' para mostrar la ayuda.' ) -ForegroundColor Yellow
        Read-Host -Prompt ('Presiona Enter para continuar...')
        exit 1
    }
    if ($List) {
        Write-Host ( 'No se ha encontrado el indentificador PID de la aplicaci' + [char]0x00F3 + 'n en ' + $pidFile + '.' ) -ForegroundColor Yellow
        Write-Host ( 'Listado de procesos que coinciden con ''app.py'':' ) -ForegroundColor Cyan
        try {
            $candidates = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ($_.CommandLine -match 'app\.py') }
            if (-not $candidates) {
                Write-Host ('No matching python process with ''app.py'' found.') -ForegroundColor Yellow
                exit 0
            }
            foreach ($proc in $candidates) {
                Write-Host ( '  PID {0}  -  CommandLine: {1}' -f $proc.ProcessId, $proc.CommandLine )
            }
            exit 0
        } catch {
            Write-Host ( 'Error searching processes: {0}' -f $_ ) -ForegroundColor Yellow
            exit 1
        }
    }
    Write-Host ( '/f proporcionado, buscando procesos ''app.py''...' ) -ForegroundColor Yellow
    try {
        $candidates = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ($_.CommandLine -match 'app\.py') }
                if (-not $candidates) {
                    Write-Host ( 'No matching python process with ''app.py'' found.' ) -ForegroundColor Yellow
                    exit 1
                }
            if ($List) {
                Write-Host ( 'PID(s) de procesos que coinciden con ''app.py'':' ) -ForegroundColor Cyan
                foreach ($proc in $candidates) {
                    Write-Host ( '  PID {0}  -  CommandLine: {1}' -f $proc.ProcessId, $proc.CommandLine )
                }
                exit 0
            }
            foreach ($proc in $candidates) {
            Log-Plan ("stop_app.ps1 requested KILL of candidate PID {0} (search-mode -Force) by {1}" -f $proc.ProcessId, $env:USERNAME)
                try {
                    Stop-Process -Id $proc.ProcessId -Force -ErrorAction Stop
                    Write-Host ( 'Stopped PID {0}' -f $proc.ProcessId )
                } catch {
                    Write-Host ( 'Failed to stop PID {0}: {1}' -f $proc.ProcessId, $_ ) -ForegroundColor Yellow
                }
            }
            exit 0
    } catch {
        Write-Host ( 'Error searching processes: {0}' -f $_ ) -ForegroundColor Yellow
        exit 1
    }
}

try {
    $storedPid = Get-Content $pidFile | Select-Object -First 1
    if (-not $storedPid) { throw "Empty PID file" }
    $rawStored = $storedPid.ToString().Trim()
    # extract first numeric sequence to be robust against malformed pid files
    if ($rawStored -match '\d+') { $numericPid = [int]$Matches[0] } else { $numericPid = $null }
    # Try to get the stored process; allow null so we can still list matching processes
    if ($numericPid) { $proc = Get-Process -Id $numericPid -ErrorAction SilentlyContinue } else { $proc = $null }
    Write-Host ( 'PID almacenado en {0}: {1}' -f $pidFile, $rawStored ) -ForegroundColor Cyan
    if ($List) {
        try {
            $candidates = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ($_.CommandLine -match 'app\.py') }
            if (-not $candidates) {
                Write-Host ( 'No hay procesos que coincidan con ''app.py''.' ) -ForegroundColor Yellow
                if (-not $proc) { Write-Host ( 'El PID almacenado no corresponde a ningún proceso en ejecuci' + [char]0x00F3 + 'n.' ) -ForegroundColor Yellow }
                exit 0
            }
            Write-Host ( 'Procesos que coinciden con ''app.py'':' ) -ForegroundColor Cyan
            foreach ($c in $candidates) {
                if ($numericPid -and ($c.ProcessId -eq $numericPid)) {
                    Write-Host ( '  PID {0}  -  CommandLine: {1}    <-- ALMACENADO' -f $c.ProcessId, $c.CommandLine )
                } else {
                    Write-Host ( '  PID {0}  -  CommandLine: {1}' -f $c.ProcessId, $c.CommandLine )
                }
            }
            if (-not $proc) { Write-Host (''); Write-Host ( 'El PID almacenado no corresponde a ningún proceso en ejecuci' + [char]0x00F3 + 'n.' ) -ForegroundColor Yellow }
            exit 0
        } catch {
            Write-Host ( 'Error searching processes: {0}' -f $_ ) -ForegroundColor Yellow
            exit 1
        }
    }
    if (-not $numericPid) { throw "Stored PID is not a valid number: $rawStored" }
    Write-Host ( 'Stopping process PID {0} (Name: {1})...' -f $numericPid, $proc.ProcessName )
    Log-Plan ("stop_app.ps1 requested KILL of stored PID {0} (from {1}) by {2}" -f $numericPid, $pidFile, $env:USERNAME)
    $proc | Stop-Process -Force
    Remove-Item $pidFile -ErrorAction SilentlyContinue
    Write-Host ( 'Stopped. PID file removed.' )
} catch {
    $errMsg = $_.ToString()
    $displayPid = if ($numericPid) { $numericPid } else { $rawStored }
    Write-Host ( 'Could not stop process with PID {0}: {1}' -f $displayPid, $errMsg ) -ForegroundColor Yellow
    if (Test-Path $pidFile) { Remove-Item $pidFile -ErrorAction SilentlyContinue }
}
