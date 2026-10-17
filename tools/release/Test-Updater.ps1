param([Parameter(Mandatory=$true)][string]$Fixtures)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'Update-TrueEngine.ps1')
$script:Passes=0
function Assert($Value,[string]$Message) { if (-not $Value) { throw $Message } }
function Pass([string]$Message) { $script:Passes++;Write-Host "PASS $script:Passes`: $Message" }
function Reject([scriptblock]$Action) { $failed=$false;try { & $Action } catch { $failed=$true };Assert $failed 'Expected rejection did not occur' }
$script:Version='0.1.0';$script:Mode='normal';$script:NetworkFailure=$false;$script:Downloads=0
function Invoke-RestMethod {
    param($Uri,$Headers,$TimeoutSec)
    Assert ($Uri -eq 'https://api.github.com/repos/BirthrightPublication/True-Engine/releases/latest') 'Unexpected API endpoint'
    if ($script:NetworkFailure) { throw 'simulated API 403' }
    $tag='v'+$script:Version;$name='True-Engine-'+$tag+'-windows-x64.zip'
    $release=[pscustomobject]@{tag_name=$tag;draft=$false;prerelease=$false;assets=@([pscustomobject]@{name=$name;browser_download_url="https://github.com/BirthrightPublication/True-Engine/releases/download/$tag/$name"},[pscustomobject]@{name=($name+'.sha256');browser_download_url="https://github.com/BirthrightPublication/True-Engine/releases/download/$tag/$name.sha256"})}
    if ($script:Mode -eq 'prerelease') { $release.prerelease=$true }
    if ($script:Mode -eq 'foreign') { $release.assets[0].browser_download_url='https://example.com/payload.zip' }
    return $release
}
function Get-ReleaseFile([string]$Url,[string]$Path) {
    $script:Downloads++
    $folder=$script:Version
    if ($script:Mode -in @('unsafe','sdk','conflict')) { $folder=$script:Mode }
    $file=Join-Path (Join-Path $Fixtures $folder) ($Url.Substring($Url.LastIndexOf('/')+1))
    Copy-Item -LiteralPath $file -Destination $Path
    if ($script:Mode -eq 'corrupt' -and $Url.EndsWith('.zip')) { [IO.File]::AppendAllText($Path,'corrupt transport') }
}
$base=Join-Path ([IO.Path]::GetTempPath()) ('true-engine-update-tests-'+[guid]::NewGuid().ToString('N'))
$root=Join-Path $base 'Engine with spaces'
$null=New-Item -ItemType Directory -Path (Join-Path $root 'Build') -Force
$null=New-Item -ItemType Directory -Path (Join-Path $root 'Data') -Force
Set-Content -LiteralPath (Join-Path $root 'Build/source.txt') -Value 'source must survive'
Set-Content -LiteralPath (Join-Path $root 'Data/project.json') -Value 'personal project'
Set-Content -LiteralPath (Join-Path $root 'preferences.json') -Value 'user root preference'
function Installed { (Read-AppManifest (Join-Path $root 'app')).version }
try {
    Invoke-TrueEngineUpdate $root
    Assert ((Installed) -eq '0.1.0') 'Fresh install failed'
    Assert (Test-Path -LiteralPath (Join-Path $root 'Update True Engine.bat')) 'Missing root updater'
    Pass 'latest-stable lookup, automatic download, SHA-256, complete fresh install and root bootstrap'
    $null=New-Item -ItemType Directory -Path (Join-Path $root 'app/Assets')
    Set-Content -LiteralPath (Join-Path $root 'app/private-setting.json') -Value 'user app preference'
    Set-Content -LiteralPath (Join-Path $root 'app/Assets/local.asset') -Value 'personal asset'
    $script:Version='0.1.1'
    Invoke-TrueEngineUpdate $root
    Assert ((Installed) -eq '0.1.1') 'Upgrade failed'
    foreach ($pair in @(@('Build/source.txt','source must survive'),@('Data/project.json','personal project'),@('preferences.json','user root preference'),@('app/private-setting.json','user app preference'),@('app/Assets/local.asset','personal asset'))) {
        Assert ((Get-Content -LiteralPath (Join-Path $root $pair[0])) -eq $pair[1]) "Data changed: $($pair[0])"
    }
    Assert (@(Get-ChildItem -LiteralPath (Join-Path $root 'Backups/Updates') -Directory | Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'app') }).Count -ge 1) 'Backup missing'
    Pass 'upgrade retains app backup, Build source, projects, root preferences and app-local persistent files'
    $count=$script:Downloads;Invoke-TrueEngineUpdate $root
    Assert ($script:Downloads -eq $count) 'Already-current install downloaded again'
    Pass 'already-current version/result and no replacement'
    $script:Version='0.1.0';Reject { Invoke-TrueEngineUpdate $root };Assert ((Installed) -eq '0.1.1') 'Downgrade changed app'
    Pass 'downgrade refusal'
    $script:Version='0.1.2'
    foreach ($mode in @('corrupt','unsafe','sdk','foreign','prerelease','conflict')) {
        $script:Mode=$mode;Reject { Invoke-TrueEngineUpdate $root };Assert ((Installed) -eq '0.1.1') "App changed on $mode"
        Assert ((Get-Content -LiteralPath (Join-Path $root 'app/private-setting.json')) -eq 'user app preference') 'Private data overwritten'
        Pass "reject $mode with old app and private data intact"
    }
    $script:Mode='normal'
    $script:OriginalMove=(Get-Item Function:Move-UpdateDirectory).ScriptBlock
    function Move-UpdateDirectory([string]$From,[string]$To) {
        if ($From.Contains('.true-engine-stage-')) { throw 'simulated activation rename failure' }
        & $script:OriginalMove $From $To
    }
    Reject { Invoke-TrueEngineUpdate $root };Assert ((Installed) -eq '0.1.1') 'Rename failure did not restore app'
    Set-Item Function:Move-UpdateDirectory $script:OriginalMove
    Pass 'activation failure restores complete previous app'
    $script:OriginalTest=(Get-Item Function:Test-ManagedApp).ScriptBlock
    function Test-ManagedApp([string]$App,$Manifest) {
        if ($App -eq (Join-Path $root 'app') -and $Manifest.version -eq '0.1.2') { throw 'simulated post-install validation failure' }
        & $script:OriginalTest $App $Manifest
    }
    Reject { Invoke-TrueEngineUpdate $root };Assert ((Installed) -eq '0.1.1') 'Post-install failure did not restore'
    Set-Item Function:Test-ManagedApp $script:OriginalTest
    Pass 'post-install validation failure restores previous app and retains failed payload'
    $script:NetworkFailure=$true;Reject { Invoke-TrueEngineUpdate $root };Assert ((Installed) -eq '0.1.1') 'API failure changed app'
    $script:NetworkFailure=$false
    Pass 'API denial logged without app replacement'
    $lock=[IO.File]::Open((Join-Path $root '.true-engine-update.lock'),[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
    try { Reject { Invoke-TrueEngineUpdate $root } } finally { $lock.Dispose() }
    Pass 'exclusive lock prevents concurrent update'
    $transaction=Join-Path $root ('Backups/Updates/'+[guid]::NewGuid().ToString('N'))
    $null=New-Item -ItemType Directory -Path $transaction
    Save-UpdateJournal $transaction 'pending'
    Move-UpdateDirectory (Join-Path $root 'app') (Join-Path $transaction 'app')
    $null=New-Item -ItemType Directory -Path (Join-Path $root 'app')
    Set-Content -LiteralPath (Join-Path $root 'app/partial-user-data.txt') -Value 'preserve failed-new data'
    $script:NetworkFailure=$true;Reject { Invoke-TrueEngineUpdate $root };$script:NetworkFailure=$false
    Assert ((Installed) -eq '0.1.1') 'Interrupted update recovery failed'
    Assert (@(Get-ChildItem -LiteralPath $transaction -Directory | Where-Object { $_.Name.StartsWith('interrupted-app-') }).Count -eq 1) 'Displaced interrupted files lost'
    Pass 'interrupted transaction recovery retains displaced app files'
    $legacy=Join-Path $base 'Legacy';$null=New-Item -ItemType Directory -Path $legacy
    $old=Join-Path (Join-Path $Fixtures '0.1.0') 'True-Engine-v0.1.0-windows-x64.zip'
    $hash=(Get-FileHash -LiteralPath $old -Algorithm SHA256).Hash
    $staged=Join-Path $base 'legacy-stage';$null=New-Item -ItemType Directory -Path $staged
    $m=Expand-VerifiedPackage $old $hash $staged '0.1.0'
    Move-UpdateDirectory (Join-Path $staged 'app') (Join-Path $legacy 'app')
    $legacyFiles=[ordered]@{};foreach($p in $m.files.PSObject.Properties){$legacyFiles['App/'+$p.Name.Substring(4)]=$p.Value}
    @{engine_version='0.1.0';sdk='0.1';project_schema=1;files=$legacyFiles} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $legacy 'RELEASE_MANIFEST.json')
    Remove-Item -LiteralPath (Join-Path $legacy 'app/manifest.json')
    $script:Version='0.1.1';Invoke-TrueEngineUpdate $legacy
    Assert ((Read-AppManifest (Join-Path $legacy 'app')).version -eq '0.1.1') 'Legacy App upgrade failed'
    Pass 'recognized 0.1.0 test-kit App upgrade and root manifest preservation'
    $custom=Join-Path $root 'Data/Chosen Test Project';$null=New-Item -ItemType Directory -Path $custom -Force
    Set-Content -LiteralPath (Join-Path $custom 'project.json') -Value 'existing chosen project'
    @{data_directory=$custom} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $root 'TrueEngine-Launcher.json')
    function global:Start-Process {
        param($FilePath,$WorkingDirectory,$RedirectStandardError,[switch]$Wait,[switch]$PassThru,[switch]$NoNewWindow)
        $global:LaunchWorkingDirectory=$WorkingDirectory
        Set-Content -LiteralPath $RedirectStandardError -Value 'MOCK process; viewport not executed'
        [pscustomobject]@{ExitCode=0}
    }
    & (Join-Path $root 'app/Start-TrueEngine.ps1') -Root $root
    Assert ($global:LaunchWorkingDirectory -eq $custom) 'Launcher ignored persistent data selection'
    Assert ((Get-Content -LiteralPath (Join-Path $custom 'project.json')) -eq 'existing chosen project') 'Launcher changed project'
    Assert (@(Get-ChildItem -LiteralPath (Join-Path $custom 'Backups') -File).Count -eq 1) 'Prelaunch project backup missing'
    Remove-Item Function:\Start-Process
    Pass 'managed launcher honors data selection, backs up projects and retains logs (process mocked)'
    $logs=@(Get-ChildItem -LiteralPath (Join-Path $root 'Logs') -Filter '*.log')
    Assert ($logs.Count -ge 10) 'Update logs missing'
    Assert ((Get-Content -LiteralPath $logs[0].FullName -Raw).Length -gt 0) 'Empty update log'
    Pass 'unique retained update logs'
    Write-Host "Updater integration checks passed: $script:Passes. PE fixtures synthetic; no viewport binary was executed."
} finally {
    if (Test-Path -LiteralPath $base) { Remove-Item -LiteralPath $base -Recurse -Force }
}
