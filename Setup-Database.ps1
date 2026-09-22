param([switch]$DemoData)

$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot 'backend')
try {
    $setupArguments = @('-m', 'scripts.setup_local')
    if ($DemoData) { $setupArguments += '--seed-demo' }
    & '.\.venv\Scripts\python.exe' @setupArguments
    if ($LASTEXITCODE -ne 0) { throw 'Database setup failed. Check that PostgreSQL is running and the password is correct.' }
} finally { Pop-Location }
