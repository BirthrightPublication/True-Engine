$ErrorActionPreference = 'Stop'
try {
    & (Join-Path $PSScriptRoot 'Check-Dependencies.ps1')
    $settings = Join-Path $PSScriptRoot 'installation.json'
    if (Test-Path -LiteralPath $settings) {
        $data = (Get-Content -LiteralPath $settings -Raw | ConvertFrom-Json).data_directory
    } else {
        $data = Join-Path $PSScriptRoot 'UserData\TestProject'
    }
    $null = New-Item -ItemType Directory -Path $data -Force
    $data = [IO.Path]::GetFullPath($data)
    $project = Join-Path $data 'project.json'
    if (Test-Path -LiteralPath $project) {
        $backupDir = Join-Path $data 'Backups'
        $null = New-Item -ItemType Directory -Path $backupDir -Force
        $backup = Join-Path $backupDir ('project-' + [guid]::NewGuid().ToString('N') + '.json')
        Copy-Item -LiteralPath $project -Destination $backup -ErrorAction Stop
        Write-Host "Existing test project backed up to: $backup"
    }
    Write-Host "Test project directory: $data"
    Write-Host 'S saves project.json (replaces that test file); L loads it. Camera position is not saved.'
    $log = Join-Path $data ('launch-' + [guid]::NewGuid().ToString('N') + '.log')
    $process = Start-Process -FilePath (Join-Path $PSScriptRoot 'App\true-engine-viewport.exe') -WorkingDirectory $data -RedirectStandardError $log -NoNewWindow -Wait -PassThru
    $code = $process.ExitCode
    if ($code -ne 0) { throw "Viewport exited with code $code. See $log" }
    Write-Host "Viewport closed. Launch log: $log"
} catch {
    Write-Host $_ -ForegroundColor Red
    exit 1
}
