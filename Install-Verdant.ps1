param(
    [switch]$DemoData,
    [switch]$SkipDatabase
)

$ErrorActionPreference = 'Stop'
$node = (Get-Command node.exe -ErrorAction Stop).Source
$npm = (Get-Command npm.cmd -ErrorAction Stop).Source
& $node -e "const [major,minor]=process.versions.node.split('.').map(Number);process.exit(major>22||(major===22&&minor>=13)?0:1)"
if ($LASTEXITCODE -ne 0) { throw 'Install Node.js 22.13 or newer, then rerun this script.' }

if (Get-Command py.exe -ErrorAction SilentlyContinue) {
    $python = & py.exe -3 -c 'import sys; print(sys.executable)'
} else {
    $python = (Get-Command python.exe -ErrorAction Stop).Source
}
& $python -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)'
if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.12 or newer, then rerun this script.' }

$backend = Join-Path $PSScriptRoot 'backend'
$venvPython = Join-Path $backend '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) {
    & $python -m venv (Join-Path $backend '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
}

Push-Location $backend
try {
    & $venvPython -m pip install -e '.[test]'
    if ($LASTEXITCODE -ne 0) { throw 'Backend dependency installation failed.' }
    & $venvPython -m scripts.setup_local --configure-only
    if ($LASTEXITCODE -ne 0) { throw 'Local configuration failed.' }
} finally { Pop-Location }

Push-Location (Join-Path $PSScriptRoot 'frontend')
try {
    & $npm ci
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
} finally { Pop-Location }

if ($SkipDatabase) {
    Write-Host 'Dependencies and local settings are ready. Run Setup-Database.ps1 when PostgreSQL is ready.'
} else {
    & (Join-Path $PSScriptRoot 'Setup-Database.ps1') -DemoData:$DemoData
}
Write-Host 'Next: powershell -ExecutionPolicy Bypass -File .\Start-Verdant.ps1'
