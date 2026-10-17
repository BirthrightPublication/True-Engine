Set-StrictMode -Version Latest
function Test-TrueEnginePackage {
    param([Parameter(Mandatory=$true)][string]$Root)
    $rootPath = [IO.Path]::GetFullPath($Root).TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    $manifestPath = Join-Path $Root 'RELEASE_MANIFEST.json'
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    if ($manifest.engine_version -ne '0.1.0' -or $manifest.project_schema -ne 1 -or $manifest.sdk -ne '0.1') {
        throw 'Incompatible version manifest. No files were installed.'
    }
    foreach ($property in $manifest.files.PSObject.Properties) {
        $relative = [string]$property.Name
        if ([IO.Path]::IsPathRooted($relative) -or $relative.Contains(':') -or $relative.Split('/') -contains '..') {
            throw "Unsafe manifest path: $relative"
        }
        $full = [IO.Path]::GetFullPath((Join-Path $Root $relative))
        if (-not $full.StartsWith($rootPath, [StringComparison]::OrdinalIgnoreCase)) { throw 'Path escapes package' }
        if (-not (Test-Path -LiteralPath $full -PathType Leaf)) { throw "Missing package file: $relative" }
        if ((Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash.ToLowerInvariant() -ne $property.Value) {
            throw "Integrity check failed: $relative. Re-extract a verified ZIP."
        }
    }
    return $manifest
}
