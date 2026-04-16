Param()
Set-StrictMode -Version Latest
$db = Join-Path -Path (Get-Location) -ChildPath 'plan.db'
if (Test-Path $db) {
    $bak = "$db.bak.$((Get-Date).ToString('yyyyMMddHHmmss'))"
    Copy-Item -Path $db -Destination $bak -Force
    Write-Output "Backup created: $bak"
} else {
    Write-Output "No plan.db found, skipping backup."
}
Write-Output "Running init_db via venv python..."
& .\.venv\Scripts\python.exe -c "import app; app.init_db(); print('INIT_DB_DONE')"