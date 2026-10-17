param([Parameter(Mandatory=$true)][string]$Version,[switch]$Candidate)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if ($env:OS -ne 'Windows_NT') { throw 'Use a native Windows x64 runner for this release build.' }
Push-Location (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent)
$work=Join-Path ([IO.Path]::GetTempPath()) ('true-engine-release-'+[guid]::NewGuid().ToString('N'))
$null=New-Item -ItemType Directory -Path $work
$results=[Collections.Generic.List[object]]::new()
function Run-Checked([string]$Program,[string[]]$Arguments) {
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Failed ($LASTEXITCODE): $Program $Arguments" }
    $results.Add(@{command=($Program+' '+($Arguments -join ' '));exit_code=0;platform='native Windows runner'})
}
try {
    # Static MSVC CRT: runtime prerequisites stay within Windows 11 system DLLs.
    $env:RUSTFLAGS='-C target-feature=+crt-static'
    Run-Checked cargo @('fmt','--all','--','--check')
    Run-Checked cargo @('clippy','--workspace','--all-targets','--locked','--','-D','warnings')
    Run-Checked cargo @('test','-p','true-engine','--test','sdk','--locked')
    Run-Checked cargo @('test','-p','true-engine','--doc','--locked')
    Run-Checked python @('-m','unittest','discover','-s','tools','-v')
    Run-Checked python @('tools/release/test_fixtures.py',(Join-Path $work 'fixtures'))
    Run-Checked powershell.exe @('-NoProfile','-ExecutionPolicy','Bypass','-File','tools/release/Test-Updater.ps1','-Fixtures',(Join-Path $work 'fixtures'))
    Run-Checked cargo @('build','--release','-p','true-engine-viewport','--locked')
    $results.Add(@{command='Interactive Windows GPU viewport and real GitHub network';result='NOT RUN by this script; native CPU/installer tests do not establish graphics compatibility'})
    $results.Add(@{command='rustc -Vv';result=((& rustc -Vv) -join "`n")})
    $evidence=Join-Path $work 'evidence.json'
    ConvertTo-Json -InputObject @($results.ToArray()) -Depth 8 | Set-Content -LiteralPath $evidence -Encoding UTF8
    $metadata=Join-Path $work 'metadata.json'
    & cargo metadata --locked --format-version 1 --filter-platform x86_64-pc-windows-msvc | Out-File -LiteralPath $metadata -Encoding utf8
    if ($LASTEXITCODE -ne 0) { throw 'Cargo metadata failed' }
    $rustRoot=(& rustc --print sysroot).Trim()
    $arguments=@('tools/release/package.py','--binary','target/release/true-engine-viewport.exe','--version',$Version,'--evidence',$evidence,'--metadata',$metadata,'--rust-root',$rustRoot,'--output','Build')
    if ($Candidate) { $arguments += '--candidate' }
    Run-Checked python $arguments
} finally { Pop-Location }
