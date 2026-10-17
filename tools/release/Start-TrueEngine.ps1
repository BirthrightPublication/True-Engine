param([string]$Root = (Split-Path $PSScriptRoot -Parent))
$ErrorActionPreference='Stop'
try {
    . (Join-Path $PSScriptRoot 'Update-TrueEngine.ps1')
    $manifest=Read-AppManifest $PSScriptRoot
    Test-ManagedApp $PSScriptRoot $manifest
    $settings=Join-Path $Root 'TrueEngine-Launcher.json'
    if (Test-Path -LiteralPath $settings) { $data=(Get-Content -LiteralPath $settings -Raw -Encoding UTF8 | ConvertFrom-Json).data_directory }
    else { $data=Join-Path $Root 'Data/ManagedViewport' }
    $null=New-Item -ItemType Directory -Path $data -Force
    $project=Join-Path $data 'project.json'
    if (Test-Path -LiteralPath $project) {
        $backups=Join-Path $data 'Backups';$null=New-Item -ItemType Directory -Path $backups -Force
        Copy-Item -LiteralPath $project -Destination (Join-Path $backups ('project-'+[guid]::NewGuid().ToString('N')+'.json'))
    }
    $log=Join-Path $data ('launch-'+[guid]::NewGuid().ToString('N')+'.log')
    Write-Host "True Engine $($manifest.version); test projects: $data"
    Write-Host 'S saves/replaces project.json; L loads it. Existing project backed up before launch.'
    $process=Start-Process -FilePath (Join-Path $PSScriptRoot 'true-engine-viewport.exe') -WorkingDirectory $data -RedirectStandardError $log -Wait -PassThru -NoNewWindow
    if ($process.ExitCode -ne 0) { throw "Viewport failed: $($process.ExitCode); log: $log" }
} catch { Write-Host $_ -ForegroundColor Red;exit 1 }
