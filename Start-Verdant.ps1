$ErrorActionPreference = 'Stop'
$runtime = Join-Path $PSScriptRoot '.local'
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
$python = Join-Path $PSScriptRoot 'backend\.venv\Scripts\python.exe'
$node = (Get-Command node.exe -ErrorAction Stop).Source
$cli = Join-Path $PSScriptRoot 'frontend\node_modules\vinext\dist\cli.js'
foreach ($file in @($python, $cli, (Join-Path $PSScriptRoot 'backend\.env'))) {
    if (-not (Test-Path -LiteralPath $file)) { throw "Missing installation file: $file" }
}
$services = @(
    @{ Name='backend'; Port=8000; File=$python; Args=@('-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000'); Folder='backend'; Url='http://localhost:8000/api/health' },
    @{ Name='frontend'; Port=3000; File=$node; Args=@(('"' + $cli + '"'),'dev','--hostname','127.0.0.1','--port','3000'); Folder='frontend'; Url='http://localhost:3000' }
)
foreach ($service in $services) {
    $recordPath = Join-Path $runtime ($service.Name + '.json')
    $existing = $null
    if (Test-Path -LiteralPath $recordPath) {
        $record = Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json
        $existing = Get-Process -Id $record.Id -ErrorAction SilentlyContinue
        if ($existing -and $existing.StartTime.ToUniversalTime().Ticks.ToString() -ne $record.StartTicks) { $existing = $null }
    }
    if (-not $existing) {
        if (Get-NetTCPConnection -LocalPort $service.Port -State Listen -ErrorAction SilentlyContinue) {
            throw "Port $($service.Port) is already in use by another process."
        }
        $process = Start-Process -FilePath $service.File -ArgumentList $service.Args -WorkingDirectory (Join-Path $PSScriptRoot $service.Folder) -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtime ($service.Name + '.log')) -RedirectStandardError (Join-Path $runtime ($service.Name + '.error.log'))
        @{ Id=$process.Id; StartTicks=$process.StartTime.ToUniversalTime().Ticks.ToString() } | ConvertTo-Json | Set-Content -LiteralPath $recordPath
    }
    $ready = $false
    for ($attempt=0; $attempt -lt 30; $attempt++) {
        try { $response = Invoke-WebRequest -Uri $service.Url -UseBasicParsing -TimeoutSec 3; if ($response.StatusCode -eq 200) { $ready=$true; break } } catch { Start-Sleep -Seconds 1 }
    }
    if (-not $ready) { throw "$($service.Name) did not start. See logs in $runtime" }
    Write-Host "$($service.Name) ready: $($service.Url)"
}
Write-Host 'Open http://localhost:3000. PostgreSQL must be running before signing in.'
