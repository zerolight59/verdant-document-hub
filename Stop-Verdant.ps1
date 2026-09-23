$ErrorActionPreference = 'Stop'
foreach ($name in @('frontend','backend')) {
    $recordPath = Join-Path $PSScriptRoot ('.local\' + $name + '.json')
    if (Test-Path -LiteralPath $recordPath) {
        $record = Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json
        $process = Get-Process -Id $record.Id -ErrorAction SilentlyContinue
        if ($process -and $process.StartTime.ToUniversalTime().Ticks.ToString() -eq $record.StartTicks) {
            # The verified launcher may own Python/Vite child processes.
            # Stop only this recorded process tree, never unrelated listeners.
            & taskkill.exe /PID $process.Id /T /F | Out-Null
            if ($LASTEXITCODE -ne 0) { throw "Could not stop $name process tree." }
            Write-Host "$name stopped."
        }
        Remove-Item -LiteralPath $recordPath
    }
}
