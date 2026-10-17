param([Parameter(Mandatory=$true)][string]$PackageRoot)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
function Assert($Value, [string]$Message) { if (-not $Value) { throw $Message } }
$root = (Resolve-Path -LiteralPath $PackageRoot).Path
$syntaxCount = 0
foreach ($file in (Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'windows-testkit') -Filter '*.ps1')) {
    $tokens = $null; $errors = $null
    $null = [Management.Automation.Language.Parser]::ParseFile($file.FullName, [ref]$tokens, [ref]$errors)
    Assert ($errors.Count -eq 0) "PowerShell parse errors in $($file.Name): $errors"
    $syntaxCount++
}
. (Join-Path $root 'Package-Integrity.ps1')
$null = Test-TrueEnginePackage -Root $root
Write-Host "PASS: $syntaxCount PowerShell scripts parse, actual packaged file hashes match"
$runtime = Join-Path $root 'App/libunwind.dll'
$original = [IO.File]::ReadAllBytes($runtime)
try {
    [IO.File]::WriteAllBytes($runtime, [byte[]](1,2,3))
    $rejected = $false
    try { $null = Test-TrueEnginePackage -Root $root } catch { $rejected = $true }
    Assert $rejected 'Tampered runtime was accepted'
} finally { [IO.File]::WriteAllBytes($runtime,$original) }
Write-Host 'PASS: tampered DLL rejected'
$temp = Join-Path ([IO.Path]::GetTempPath()) ('true-engine-installer-' + [guid]::NewGuid().ToString('N'))
$oldOS=$env:OS; $oldArch=$env:PROCESSOR_ARCHITECTURE
try {
    # Simulate only the OS environment gate. This does NOT run a Windows binary.
    $env:OS='Windows_NT'; $env:PROCESSOR_ARCHITECTURE='AMD64'
    $null = New-Item -ItemType Directory -Path (Join-Path $temp 'Current') -Force
    $null = New-Item -ItemType Directory -Path (Join-Path $temp 'Data') -Force
    Set-Content -LiteralPath (Join-Path $temp 'Current/earlier-version.txt') -Value 'keep old version'
    Set-Content -LiteralPath (Join-Path $temp 'Data/personal-project.json') -Value 'keep personal project'
    Set-Content -LiteralPath (Join-Path $temp 'START APPLICATION.bat') -Value 'keep old launcher'
    & (Join-Path $root 'Install-To-B-Drive.ps1') -Destination $temp
    $installed = Join-Path $temp 'Versions/0.1.0-windows11-testkit-r2'
    $null = Test-TrueEnginePackage -Root $installed
    Assert ((Get-Content -LiteralPath (Join-Path $temp 'Current/earlier-version.txt')) -eq 'keep old version') 'Earlier version changed'
    Assert ((Get-Content -LiteralPath (Join-Path $temp 'Data/personal-project.json')) -eq 'keep personal project') 'Personal project changed'
    Assert ((Get-Content -LiteralPath (Join-Path $temp 'START APPLICATION.bat')) -eq 'keep old launcher') 'Existing launcher replaced'
    $rejected=$false
    try { & (Join-Path $root 'Install-To-B-Drive.ps1') -Destination $temp } catch { $rejected=$true }
    Assert $rejected 'Repeated install replaced an existing version'
    $fresh = Join-Path $temp 'fresh installation with spaces'
    & (Join-Path $root 'Install-To-B-Drive.ps1') -Destination $fresh
    $launcher = Get-Content -LiteralPath (Join-Path $fresh 'START APPLICATION.bat') -Raw
    Assert ($launcher.Contains('Versions\0.1.0-windows11-testkit-r2\START APPLICATION.bat')) 'New root launcher is incorrect'
    Write-Host 'PASS: side-by-side install, previous version/project/launcher preservation, repeated-install refusal, new root launcher and paths with spaces' 
    $config = Get-Content -LiteralPath (Join-Path $installed 'installation.json') -Raw | ConvertFrom-Json
    $null=New-Item -ItemType Directory -Path $config.data_directory -Force
    $project=Join-Path $config.data_directory 'project.json'
    Set-Content -LiteralPath $project -Value 'existing test project'
    function global:Start-Process {
        param($FilePath,$WorkingDirectory,$RedirectStandardError,[switch]$NoNewWindow,[switch]$Wait,[switch]$PassThru)
        $global:TestKitWorkingDirectory=$WorkingDirectory
        Set-Content -LiteralPath $RedirectStandardError -Value 'MOCK process; Windows EXE not run'
        [pscustomobject]@{ExitCode=0}
    }
    & (Join-Path $installed 'Start-Application.ps1')
    Assert ($global:TestKitWorkingDirectory -eq $config.data_directory) 'Wrong application data directory'
    $backups = @(Get-ChildItem -LiteralPath (Join-Path $config.data_directory 'Backups') -Filter '*.json')
    Assert ($backups.Count -eq 1) 'Existing test project backup missing'
    Assert ((Get-Content -LiteralPath $backups[0].FullName) -eq 'existing test project') 'Backup content mismatch'
    Assert ((Get-Content -LiteralPath $project) -eq 'existing test project') 'Launch modified the project'
    Write-Host 'PASS: launch working directory, prelaunch backup and logs (native process MOCKED)'
} finally {
    Remove-Item Function:\Start-Process -ErrorAction SilentlyContinue
    $env:OS=$oldOS; $env:PROCESSOR_ARCHITECTURE=$oldArch
    if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
}
Write-Host 'PowerShell logic checks complete. Windows executable, CMD and Windows PowerShell 5.1 NOT RUN.'
