$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Package-Integrity.ps1')
if ($env:OS -ne 'Windows_NT') { throw 'This test build requires Windows 11 x64.' }
if (-not [Environment]::Is64BitOperatingSystem -or $env:PROCESSOR_ARCHITECTURE -ne 'AMD64') {
    throw 'Use Windows x64 and 64-bit Windows PowerShell. ARM64 execution is not qualified.'
}
$null = Test-TrueEnginePackage -Root $PSScriptRoot
Write-Host 'PASS: Windows x64 and all packaged file SHA-256 values.'
Write-Host 'Rust, Python, Visual Studio, and a separate VC++ runtime are not required to run this kit.'
Write-Host 'libunwind.dll is bundled; Windows 11 supplies UCRT and system graphics libraries.'
Write-Host 'A functioning GPU driver is required. Only opening the viewport can verify GPU compatibility.'
Write-Host 'If graphics initialization fails, update your GPU driver using Windows Update or the manufacturer.'
