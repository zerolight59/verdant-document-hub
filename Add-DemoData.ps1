$ErrorActionPreference = 'Stop'
$backend = Join-Path $PSScriptRoot 'backend'
$python = Join-Path $backend '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Run Install-Verdant.ps1 first.' }
Write-Host 'Adding the optional fictional showcase. Existing users, files and demo progress will not be reset.'
Push-Location $backend
try {
    & $python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw 'Database migration failed.' }
    & $python -m scripts.seed_showcase
    if ($LASTEXITCODE -ne 0) { throw 'Demo seed stopped. Check the message above; no existing data was replaced.' }
} finally { Pop-Location }
