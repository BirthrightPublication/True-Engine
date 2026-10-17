param(
    [string]$Python = 'python',
    [string]$Stage = (Join-Path $PSScriptRoot '..\..\Build\sdk-web')
)

$ErrorActionPreference = 'Stop'
$sourceRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
foreach ($command in @($Python, 'cargo', 'rustc', 'wasm-bindgen')) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "Missing prerequisite: $command. Read docs/SDK_WINDOWS_BUILD.md; this script does not install tools."
    }
}
& $Python -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'
if ($LASTEXITCODE -ne 0) { throw 'Python 3.11 or newer is required.' }

$previousDirectory = Get-Location
try {
    Set-Location $sourceRoot
    & $Python (Join-Path $PSScriptRoot 'build.py') --stage $Stage
    if ($LASTEXITCODE -ne 0) { throw "SDK build failed with exit code $LASTEXITCODE" }
    Write-Host "SDK staged at $Stage"
    Write-Host 'Run the documented browser tests, then pack.py with actual evidence. No release archive has been published by this script.'
} finally {
    Set-Location $previousDirectory
}
