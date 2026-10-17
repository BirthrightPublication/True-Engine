param([string]$Output = 'B:\True Engine\Build')
$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    $results = @()
    $commands = @(
        @('fmt', '--all', '--', '--check'),
        @('test', '-p', 'true-engine', '--test', 'sdk', '--locked'),
        @('test', '-p', 'true-engine', '--doc', '--locked'),
        @('build', '--release', '-p', 'true-engine-viewport', '--locked')
    )
    foreach ($arguments in $commands) {
        & cargo @arguments
        $status = $LASTEXITCODE
        $results += @{command=('cargo ' + ($arguments -join ' ')); exit_code=$status}
        if ($status -ne 0) { throw "Command failed: cargo $arguments" }
    }
    & py -3 -m unittest discover -s tools -v
    if ($LASTEXITCODE -ne 0) { throw 'Updater tests failed' }
    $results += @{command='py -3 -m unittest discover -s tools -v'; exit_code=0}
    $results += @{command='Interactive Windows viewport and batch updater'; result='NOT RUN by this script; manual qualification required'}
    $evidence = Join-Path $env:TEMP ('true-engine-tests-' + [guid]::NewGuid() + '.json')
    ConvertTo-Json -InputObject $results -Depth 4 | Set-Content -Encoding UTF8 $evidence
    try {
        & py -3 tools/package.py --binary target/release/true-engine-viewport.exe --tests $evidence --output $Output
        if ($LASTEXITCODE -ne 0) { throw 'Packaging failed' }
    } finally { Remove-Item -LiteralPath $evidence }
} finally { Pop-Location }
