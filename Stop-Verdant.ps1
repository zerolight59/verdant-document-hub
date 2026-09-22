$ErrorActionPreference = 'Stop'
foreach ($name in @('frontend','backend')) {
    $recordPath = Join-Path $PSScriptRoot ('.local\' + $name + '.json')
    if (Test-Path -LiteralPath $recordPath) {
        $record = Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json
        $process = Get-Process -Id $record.Id -ErrorAction SilentlyContinue
        if ($process -and $process.StartTime.ToUniversalTime().Ticks.ToString() -eq $record.StartTicks) {
            Stop-Process -Id $process.Id
            Write-Host "$name stopped."
        }
        Remove-Item -LiteralPath $recordPath
    }
}
