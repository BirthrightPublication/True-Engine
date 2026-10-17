param([string]$Root = $(if ([IO.Path]::GetFileName($PSCommandPath) -eq 'TrueEngine-Bootstrap.ps1') { $PSScriptRoot } else { Split-Path $PSScriptRoot -Parent }))
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:UpdateLog = $null

function Write-UpdateLog([string]$Message) {
    Write-Host $Message
    if ($script:UpdateLog) { Add-Content -LiteralPath $script:UpdateLog -Value (([DateTime]::UtcNow.ToString('o')) + ' ' + $Message) -Encoding UTF8 }
}
function Get-StableRelease {
    $release = Invoke-RestMethod -Uri 'https://api.github.com/repos/BirthrightPublication/True-Engine/releases/latest' -Headers @{'User-Agent'='TrueEngineUpdater';Accept='application/vnd.github+json'} -TimeoutSec 60
    if ($release.draft -or $release.prerelease -or $release.tag_name -notmatch '^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$') { throw 'GitHub returned an invalid stable release.' }
    $version = $release.tag_name.Substring(1)
    $name = "True-Engine-v$version-windows-x64.zip"
    $zip = @($release.assets | Where-Object { $_.name -ceq $name })
    $sum = @($release.assets | Where-Object { $_.name -ceq ($name + '.sha256') })
    if ($zip.Count -ne 1 -or $sum.Count -ne 1) { throw "Stable release $version has no unique standard Windows package/checksum. No application files changed." }
    foreach ($asset in @($zip[0],$sum[0])) {
        $expected = "https://github.com/BirthrightPublication/True-Engine/releases/download/$($release.tag_name)/$($asset.name)"
        if ($asset.browser_download_url -cne $expected) { throw 'Unexpected release asset URL.' }
    }
    [pscustomobject]@{Version=$version;Name=$name;ZipUrl=$zip[0].browser_download_url;ChecksumUrl=$sum[0].browser_download_url}
}
function Get-ReleaseFile([string]$Url,[string]$Path) {
    Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $Path -Headers @{'User-Agent'='TrueEngineUpdater'} -TimeoutSec 300
}
function Read-Checksum([string]$Path,[string]$Name) {
    if ((Get-Item -LiteralPath $Path).Length -gt 4096) { throw 'Checksum file too large.' }
    $text = (Get-Content -LiteralPath $Path -Raw -Encoding UTF8).Trim()
    if ($text -notmatch '^([a-fA-F0-9]{64})(?:\s+\*?([^\r\n]+))?$') { throw 'Malformed SHA-256 sidecar.' }
    $hash = $Matches[1].ToLowerInvariant()
    if ($Matches.ContainsKey(2) -and $Matches[2] -cne $Name) { throw 'Checksum filename does not match package.' }
    return $hash
}
function Test-PlainPath([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Refusing reparse point: $Path" }
}
function New-SafeUpdateDirectory([string]$Root,[string]$Relative) {
    $current=$Root
    foreach ($part in $Relative.Split('/')) {
        if ($part -eq '' -or $part -eq '..' -or $part -eq '.' -or $part.Contains('\') -or $part.Contains(':')) { throw 'Invalid updater directory.' }
        $current=Join-Path $current $part
        if (Test-Path -LiteralPath $current) { Test-PlainPath $current }
        else { $null=New-Item -ItemType Directory -Path $current }
    }
    return $current
}
function Read-AppManifest([string]$App) {
    $path = Join-Path $App 'manifest.json'
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        $legacy=Join-Path (Split-Path $App -Parent) 'RELEASE_MANIFEST.json'
        if (Test-Path -LiteralPath $legacy) {
            $m=Get-Content -LiteralPath $legacy -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($m.engine_version -eq '0.1.0' -and $m.sdk -eq '0.1' -and $m.project_schema -eq 1) {
                $files=[ordered]@{}
                foreach ($p in $m.files.PSObject.Properties) { if ($p.Name.StartsWith('App/')) { $files['app/'+$p.Name.Substring(4)]=$p.Value } }
                if ($files.Contains('app/true-engine-viewport.exe')) { return [pscustomobject]@{version='0.1.0';sdk='0.1';schema=1;files=[pscustomobject]$files} }
            }
        }
        throw "Unmanaged app directory preserved: $App. Move it aside manually before installing."
    }
    Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
}
function Test-ManagedApp([string]$App,$Manifest) {
    foreach ($property in $Manifest.files.PSObject.Properties) {
        $name = [string]$property.Name
        Assert-PackagePath $name
        $path = Join-Path $App $name.Substring(4)
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing installed file: $name" }
        if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -cne $property.Value) { throw "Installed hash mismatch: $name" }
    }
}
function Assert-PackagePath([string]$Name) {
    if (-not $Name.StartsWith('app/',[StringComparison]::Ordinal) -or $Name.Contains('\') -or $Name -match '[\x00-\x1f:<>"|?*]') { throw "Unsafe package path: $Name" }
    foreach ($part in $Name.Split('/')) {
        if ($part -eq '' -or $part -eq '.' -or $part -eq '..' -or $part.EndsWith('.') -or $part.EndsWith(' ') -or $part -match '^(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)') { throw "Unsafe package path: $Name" }
    }
}
function Expand-VerifiedPackage([string]$Package,[string]$Hash,[string]$Stage,[string]$Version) {
    if ($Hash -notmatch '^[a-fA-F0-9]{64}$' -or (Get-FileHash -LiteralPath $Package -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Hash.ToLowerInvariant()) { throw 'Package SHA-256 mismatch.' }
    if ((Get-Item -LiteralPath $Package).Length -gt 536870912) { throw 'Package exceeds size limit.' }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    # Lock the checked archive against modification while it is read/extracted.
    $stream = [IO.File]::Open($Package,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    try {
        $sha = [Security.Cryptography.SHA256]::Create()
        try { $lockedHash = [BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-','').ToLowerInvariant() } finally { $sha.Dispose() }
        if ($lockedHash -ne $Hash.ToLowerInvariant()) { throw 'Package changed before extraction.' }
        $stream.Position=0
        $zip = [IO.Compression.ZipArchive]::new($stream,[IO.Compression.ZipArchiveMode]::Read,$true)
        try {
            $names = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
            [long]$total=0
            if ($zip.Entries.Count -gt 10000) { throw 'Too many ZIP entries.' }
            foreach ($entry in $zip.Entries) {
                if (@('Update True Engine.bat','Start True Engine.bat','TrueEngine-Bootstrap.ps1','README - FIRST TIME SETUP.txt') -cnotcontains $entry.FullName) { Assert-PackagePath $entry.FullName }
                if (-not $names.Add($entry.FullName)) { throw 'Duplicate ZIP path.' }
                if ((($entry.ExternalAttributes -shr 16) -band 61440) -eq 40960) { throw 'ZIP symlink rejected.' }
                $total += $entry.Length
                if ($total -gt 536870912) { throw 'Expanded package exceeds size limit.' }
            }
            $manifestEntry = $zip.GetEntry('app/manifest.json')
            if (-not $manifestEntry -or $manifestEntry.Length -gt 2097152) { throw 'Missing/oversized manifest.' }
            $reader=[IO.StreamReader]::new($manifestEntry.Open())
            try { $manifest=$reader.ReadToEnd() | ConvertFrom-Json } finally { $reader.Dispose() }
            if ($manifest.format_version -ne 1 -or $manifest.version -cne $Version -or $manifest.sdk -cne '0.1' -or $manifest.schema -ne 1 -or $manifest.migration -cne 'none') { throw 'Package version/SDK/schema/migration incompatible.' }
            $expected = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
            $null=$expected.Add('app/manifest.json')
            foreach ($p in $manifest.files.PSObject.Properties) {
                Assert-PackagePath $p.Name
                if ($p.Name -ceq 'app/manifest.json' -or $p.Value -notmatch '^[a-f0-9]{64}$' -or -not $expected.Add($p.Name)) { throw 'Invalid manifest file list.' }
            }
            $bootstrapNames=@('Update True Engine.bat','Start True Engine.bat','TrueEngine-Bootstrap.ps1','README - FIRST TIME SETUP.txt')
            if (@($manifest.bootstrap_files.PSObject.Properties).Count -ne 4) { throw 'Invalid bootstrap list.' }
            foreach ($p in $manifest.bootstrap_files.PSObject.Properties) {
                if ($bootstrapNames -cnotcontains $p.Name -or $p.Value -notmatch '^[a-f0-9]{64}$' -or -not $expected.Add($p.Name)) { throw 'Invalid bootstrap payload.' }
            }
            if (-not $expected.SetEquals($names)) { throw 'Unlisted or missing ZIP payload.' }
            foreach ($entry in $zip.Entries) {
                $path=Join-Path $Stage $entry.FullName
                $null=New-Item -ItemType Directory -Path (Split-Path $path -Parent) -Force
                $inputStream=$entry.Open();$out=[IO.File]::Open($path,[IO.FileMode]::CreateNew)
                try { $inputStream.CopyTo($out) } finally { $inputStream.Dispose();$out.Dispose() }
            }
            $app=Join-Path $Stage 'app'
            Test-ManagedApp $app $manifest
            foreach ($p in $manifest.bootstrap_files.PSObject.Properties) {
                if ((Get-FileHash -LiteralPath (Join-Path $Stage $p.Name) -Algorithm SHA256).Hash.ToLowerInvariant() -cne $p.Value) { throw 'Bootstrap hash mismatch.' }
            }
            foreach ($required in @('true-engine-viewport.exe','Update-TrueEngine.ps1','Start-TrueEngine.ps1','Update True Engine.bat','Start True Engine.bat')) {
                if (-not ($manifest.files.PSObject.Properties.Name -ccontains ('app/'+$required))) { throw "Required application file missing: $required" }
            }
            return $manifest
        } finally { $zip.Dispose() }
    } finally { $stream.Dispose() }
}
function Copy-PersistentAppFiles([string]$OldApp,[string]$NewApp,$OldManifest,$NewManifest) {
    $managed=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $null=$managed.Add('manifest.json')
    foreach ($p in $OldManifest.files.PSObject.Properties) { Assert-PackagePath $p.Name; $null=$managed.Add($p.Name.Substring(4)) }
    $incoming=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $null=$incoming.Add('manifest.json')
    foreach ($p in $NewManifest.files.PSObject.Properties) { $null=$incoming.Add($p.Name.Substring(4)) }
    $queue=[Collections.Generic.Queue[string]]::new()
    $queue.Enqueue($OldApp)
    $items=[Collections.Generic.List[object]]::new()
    while ($queue.Count -gt 0) {
        foreach ($item in (Get-ChildItem -LiteralPath $queue.Dequeue() -Force)) {
            Test-PlainPath $item.FullName
            $items.Add($item)
            if ($item.PSIsContainer) { $queue.Enqueue($item.FullName) }
        }
    }
    foreach ($file in $items) {
        Test-PlainPath $file.FullName
        $relative=$file.FullName.Substring($OldApp.Length).TrimStart([IO.Path]::DirectorySeparatorChar).Replace('\','/')
        if (-not $managed.Contains($relative)) {
            if ($incoming.Contains($relative)) { throw "New application path conflicts with persistent data: $relative" }
            $dest=Join-Path $NewApp $relative
            if ($file.PSIsContainer) { $null=New-Item -ItemType Directory -Path $dest -Force }
            else { if (Test-Path -LiteralPath $dest) { throw "Persistent file conflicts with new package directory: $relative" }; $null=New-Item -ItemType Directory -Path (Split-Path $dest -Parent) -Force; Copy-Item -LiteralPath $file.FullName -Destination $dest -ErrorAction Stop }
        }
    }
}
function Move-UpdateDirectory([string]$From,[string]$To) { [IO.Directory]::Move($From,$To) }
function Save-UpdateJournal([string]$Folder,[string]$Phase) {
    [IO.File]::WriteAllText((Join-Path $Folder 'journal.json'),(@{phase=$Phase} | ConvertTo-Json))
}
function Recover-InterruptedUpdate([string]$Root) {
    $area=Join-Path $Root 'Backups/Updates'
    if (-not (Test-Path -LiteralPath $area)) { return }
    Test-PlainPath $area
    foreach ($folder in (Get-ChildItem -LiteralPath $area -Directory)) {
        Test-PlainPath $folder.FullName
        $journal=Join-Path $folder.FullName 'journal.json'
        if (-not (Test-Path -LiteralPath $journal)) { continue }
        $state=Get-Content -LiteralPath $journal -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($state.phase -notin @('pending','activated')) { continue }
        $app=Join-Path $Root 'app';$backup=Join-Path $folder.FullName 'app'
        if (Test-Path -LiteralPath $backup) {
            if (Test-Path -LiteralPath $app) { Move-UpdateDirectory $app (Join-Path $folder.FullName ('interrupted-app-'+[guid]::NewGuid().ToString('N'))) }
            Move-UpdateDirectory $backup $app
            Write-UpdateLog 'Recovered previous app from an interrupted update; displaced files retained in Backups.'
        }
        Save-UpdateJournal $folder.FullName 'recovered'
    }
}
function Install-VerifiedUpdate([string]$Root,[string]$Package,[string]$Hash,[string]$Version) {
    $app=Join-Path $Root 'app'
    $stage=Join-Path $Root ('.true-engine-stage-'+[guid]::NewGuid().ToString('N'))
    $null=New-Item -ItemType Directory -Path $stage
    $transaction=$null;$activated=$false;$backedUp=$false
    $created=[Collections.Generic.List[string]]::new()
    try {
        $manifest=Expand-VerifiedPackage $Package $Hash $stage $Version
        $newApp=Join-Path $stage 'app'
        if (Test-Path -LiteralPath $app) {
            Test-PlainPath $app
            $old=Read-AppManifest $app
            if ($old.sdk -cne '0.1' -or $old.schema -ne 1) { throw 'Existing app SDK/schema incompatible.' }
            Copy-PersistentAppFiles $app $newApp $old $manifest
        }
        foreach ($process in @(Get-Process -Name 'true-engine-viewport' -ErrorAction SilentlyContinue)) {
            if (-not $process.Path -or $process.Path.StartsWith($app,[StringComparison]::OrdinalIgnoreCase)) { throw 'Close the installed True Engine viewport before updating.' }
        }
        $transaction=New-SafeUpdateDirectory $Root ('Backups/Updates/'+[guid]::NewGuid().ToString('N'))
        Save-UpdateJournal $transaction 'pending'
        if (Test-Path -LiteralPath $app) { Move-UpdateDirectory $app (Join-Path $transaction 'app');$backedUp=$true }
        Move-UpdateDirectory $newApp $app
        $activated=$true
        Save-UpdateJournal $transaction 'activated'
        Test-ManagedApp $app $manifest
        foreach ($pair in @(@('Update True Engine.bat','Update True Engine.bat'),@('Start True Engine.bat','Start True Engine.bat'),@('Update-TrueEngine.ps1','TrueEngine-Bootstrap.ps1'))) {
            $dest=Join-Path $Root $pair[1]
            if (-not (Test-Path -LiteralPath $dest)) {
                $bytes=[IO.File]::ReadAllBytes((Join-Path $app $pair[0]))
                $out=[IO.File]::Open($dest,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
                try { $out.Write($bytes,0,$bytes.Length);$created.Add($dest) } finally { $out.Dispose() }
            }
        }
        Save-UpdateJournal $transaction 'complete'
        Write-UpdateLog "Installed version: $Version. Result: SUCCESS. Previous app retained: $transaction"
    } catch {
        $reason=$_.Exception.Message
        foreach ($file in $created) { Remove-Item -LiteralPath $file -Force }
        if ($activated -and (Test-Path -LiteralPath $app)) { Move-UpdateDirectory $app (Join-Path $transaction 'failed-app') }
        if ($backedUp) { Move-UpdateDirectory (Join-Path $transaction 'app') $app }
        if ($transaction) { Save-UpdateJournal $transaction 'rolled-back' }
        throw "Update failed; previous files preserved/restored: $reason"
    } finally {
        if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
    }
}
function Invoke-TrueEngineUpdate([string]$Root) {
    $Root=[IO.Path]::GetFullPath($Root).TrimEnd([IO.Path]::DirectorySeparatorChar)
    $null=New-Item -ItemType Directory -Path $Root -Force
    Test-PlainPath $Root
    foreach ($name in @('Build','Backups','Logs','app')) { $p=Join-Path $Root $name;if (Test-Path -LiteralPath $p) { Test-PlainPath $p } }
    $null=New-Item -ItemType Directory -Path (Join-Path $Root 'Logs') -Force
    $script:UpdateLog=Join-Path $Root ('Logs/Update-'+[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N')+'.log')
    $lock=$null
    try {
        [Net.ServicePointManager]::SecurityProtocol=[Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
        $lockPath=Join-Path $Root '.true-engine-update.lock'
        if (Test-Path -LiteralPath $lockPath) { Test-PlainPath $lockPath }
        $lock=[IO.File]::Open($lockPath,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
        Recover-InterruptedUpdate $Root
        $current=$null;$app=Join-Path $Root 'app'
        if (Test-Path -LiteralPath $app) { $current=Read-AppManifest $app }
        if ($current) { Write-UpdateLog "Installed version: $($current.version)" } else { Write-UpdateLog 'Installed version: no managed app (legacy Current/Versions installations are retained).' }
        $release=Get-StableRelease
        Write-UpdateLog "Available stable version: $($release.Version)"
        if ($current -and [version]$current.version -gt [version]$release.Version) { throw 'Refusing to downgrade installed version.' }
        if ($current -and [version]$current.version -eq [version]$release.Version) { Test-ManagedApp $app $current;Write-UpdateLog 'Result: already up to date.';return }
        $downloads=New-SafeUpdateDirectory $Root ('Build/Releases/v'+$release.Version+'/'+[guid]::NewGuid().ToString('N'))
        $package=Join-Path $downloads $release.Name;$sum=$package+'.sha256'
        Get-ReleaseFile $release.ChecksumUrl $sum
        $hash=Read-Checksum $sum $release.Name
        Get-ReleaseFile $release.ZipUrl $package
        Install-VerifiedUpdate $Root $package $hash $release.Version
    } catch {
        Write-UpdateLog ('Result: FAILED. '+$_.Exception.Message)
        throw
    } finally {
        if ($lock) { $lock.Dispose() }
        Write-Host "Update log: $script:UpdateLog"
    }
}
if ($MyInvocation.InvocationName -ne '.') {
    try {
        $delegate=Join-Path $Root 'app/Update-TrueEngine.ps1'
        if ((Test-Path -LiteralPath $delegate) -and [IO.Path]::GetFullPath($delegate) -ne $PSCommandPath) { & $delegate -Root $Root;exit $LASTEXITCODE }
        Invoke-TrueEngineUpdate $Root
        exit 0
    } catch { Write-Host $_ -ForegroundColor Red;exit 1 }
}
