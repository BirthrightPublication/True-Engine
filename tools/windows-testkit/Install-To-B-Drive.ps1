param([string]$Destination = 'B:\True Engine')
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Package-Integrity.ps1')
$manifest = Test-TrueEnginePackage -Root $PSScriptRoot
if ($env:OS -ne 'Windows_NT') { throw 'Run this optional installer on Windows.' }
$null = & (Join-Path $PSScriptRoot 'Check-Dependencies.ps1')
$destinationPath = [IO.Path]::GetFullPath($Destination)
if (-not (Test-Path -LiteralPath ([IO.Path]::GetPathRoot($destinationPath)))) { throw "Drive not available: $Destination" }
$versionName = '0.1.0-windows11-testkit-r2'
$target = Join-Path $destinationPath ('Versions\' + $versionName)
if (Test-Path -LiteralPath $target) { throw "Preserving existing version: $target. Launch it or use a different -Destination." }
$null = New-Item -ItemType Directory -Path $destinationPath -Force
$versions = Join-Path $destinationPath 'Versions'
$null = New-Item -ItemType Directory -Path $versions -Force
$stage = Join-Path $versions ('.install-' + [guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $stage
try {
    foreach ($property in $manifest.files.PSObject.Properties) {
        $out = Join-Path $stage $property.Name
        $null = New-Item -ItemType Directory -Path (Split-Path $out -Parent) -Force
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot $property.Name) -Destination $out -ErrorAction Stop
    }
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'RELEASE_MANIFEST.json') -Destination (Join-Path $stage 'RELEASE_MANIFEST.json')
    $null = Test-TrueEnginePackage -Root $stage
    $data = Join-Path $destinationPath ('Data\TestKit-0.1.0-' + [guid]::NewGuid().ToString('N'))
    @{data_directory=$data} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $stage 'installation.json') -Encoding UTF8
    # Rename activates a new version only. Existing versions, Current, and Data are never replaced.
    [IO.Directory]::Move($stage, $target)
} finally {
    if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
}
$shortcut = Join-Path $destinationPath 'START APPLICATION.bat'
try {
    $stream = [IO.File]::Open($shortcut, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try {
        $text = "@echo off`r`ncall `"%~dp0Versions\$versionName\START APPLICATION.bat`"`r`n"
        $bytes = [Text.Encoding]::ASCII.GetBytes($text)
        $stream.Write($bytes, 0, $bytes.Length)
    } finally { $stream.Dispose() }
} catch [IO.IOException] {
    if (Test-Path -LiteralPath $shortcut) { Write-Host 'Existing root launcher preserved. Use the version-specific launcher printed below.' } else { throw }
}
Write-Host "Installed without replacing earlier versions: $target"
Write-Host "Launch: $target\START APPLICATION.bat"
Write-Host "Private test data: $data"
Write-Host 'Rollback: close this test viewport and launch the earlier version directly; it was not modified.'
