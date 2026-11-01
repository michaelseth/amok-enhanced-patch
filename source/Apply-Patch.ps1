param(
    [string]$Source,
    [string]$Destination,
    [switch]$NoGui
)
$ErrorActionPreference = 'Stop'
$stage = $null
function Get-ByteHash([byte[]]$Bytes) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash($Bytes))).Replace('-', '').ToLowerInvariant() }
    finally { $sha.Dispose() }
}
function Get-FileHashValue([string]$Path) {
    return Get-ByteHash ([IO.File]::ReadAllBytes($Path))
}
function Select-Folder([string]$Description) {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = $Description
    $dialog.ShowNewFolderButton = $true
    try {
        if ($dialog.ShowDialog() -ne [Windows.Forms.DialogResult]::OK) { throw 'Cancelled. No game files were changed.' }
        return $dialog.SelectedPath
    } finally { $dialog.Dispose() }
}
function Resolve-ContainedPath([string]$Root, [string]$Relative) {
    $base = [IO.Path]::GetFullPath($Root).TrimEnd('\') + '\'
    $path = [IO.Path]::GetFullPath([IO.Path]::Combine($base, $Relative))
    if (-not $path.StartsWith($base, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Invalid path in patch manifest.'
    }
    return $path
}
try {
    Write-Host 'AMOK Enhanced 4K - patch installer'
    Write-Host 'Your original files will remain unchanged.'
    $manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'patch-manifest.json') -Raw | ConvertFrom-Json
    if ($manifest.format -ne 1) { throw 'Unsupported patch format.' }
    if (-not $Source) {
        if ($NoGui) { throw 'Specify -Source and -Destination when using -NoGui.' }
        $Source = Select-Folder 'Choose your original AMOK game folder, AMOKFILS folder, or extracted CD root.'
    }
    $Source = (Resolve-Path -LiteralPath $Source).Path
    if (-not (Test-Path -LiteralPath $Source -PathType Container)) { throw 'The source must be a game folder.' }
    $roots = @($Source, (Join-Path $Source 'AMOKFILS'))
    if ((Split-Path $Source -Leaf) -ieq 'FILES95') { $roots = @((Split-Path $Source -Parent)) + $roots }
    $dataRoot = $null
    $original = $null
    foreach ($root in $roots) {
        foreach ($relative in @('FILES95\AMOK.BIN', 'AMOK.EXE', 'AMOK.BIN')) {
            $candidate = Join-Path $root $relative
            if ((Test-Path -LiteralPath $candidate -PathType Leaf) -and
                (Get-FileHashValue $candidate) -eq $manifest.original_sha256) {
                $dataRoot = $root
                $original = $candidate
                break
            }
        }
        if ($original) { break }
    }
    if (-not $original) {
        throw 'No supported original Windows 95 AMOK executable was found. This release requires the original AMOK.BIN (or identical AMOK.EXE). Modified builds and other editions are not supported.'
    }
    Write-Host 'Checking original game data...'
    foreach ($asset in $manifest.assets) {
        $path = Resolve-ContainedPath $dataRoot $asset.path
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing game data: $($asset.path). Supply the complete original game data folder." }
        if ((Get-FileHashValue $path) -ne $asset.sha256) { throw "Game data differs from the supported edition: $($asset.path). No output was created." }
    }
    foreach ($file in $manifest.payload) {
        $path = Resolve-ContainedPath (Join-Path $PSScriptRoot 'payload') $file.path
        if ((Get-FileHashValue $path) -ne $file.sha256) { throw "Patch package is damaged: $($file.path). Extract a fresh copy of the ZIP." }
    }
    $inputBytes = [IO.File]::ReadAllBytes($original)
    $patched = New-Object byte[] ([int]$manifest.result_size)
    [Array]::Copy($inputBytes, $patched, $inputBytes.Length)
    foreach ($change in $manifest.changes) {
        $replacement = [Convert]::FromBase64String($change.bytes)
        $offset = [int]$change.offset
        if ($offset -lt 0 -or $offset + $replacement.Length -gt $patched.Length) { throw 'Invalid patch range.' }
        [Array]::Copy($replacement, 0, $patched, $offset, $replacement.Length)
    }
    if ((Get-ByteHash $patched) -ne $manifest.result_sha256) { throw 'Patched executable failed verification. No output was created.' }
    if (-not $Destination) {
        if ($NoGui) { throw 'Specify -Destination when using -NoGui.' }
        $parent = Select-Folder 'Choose where to create the new AMOK-Enhanced-4K folder.'
        $Destination = Join-Path $parent 'AMOK-Enhanced-4K'
    }
    $Destination = [IO.Path]::GetFullPath($Destination).TrimEnd('\')
    if (Test-Path -LiteralPath $Destination) { throw 'The destination already exists. Choose a new folder to preserve your existing game and settings.' }
    $destinationParent = Split-Path $Destination -Parent
    if (-not (Test-Path -LiteralPath $destinationParent -PathType Container)) { throw 'The destination parent folder must already exist.' }
    $stage = $Destination + '.building-' + [Guid]::NewGuid().ToString('N')
    [IO.Directory]::CreateDirectory((Join-Path $stage 'Game')) | Out-Null
    Write-Host 'Creating your enhanced portable copy...'
    foreach ($asset in $manifest.assets) {
        $from = Resolve-ContainedPath $dataRoot $asset.path
        $to = Resolve-ContainedPath (Join-Path $stage 'Game') $asset.path
        [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($to)) | Out-Null
        [IO.File]::Copy($from, $to, $false)
        if ((Get-FileHashValue $to) -ne $asset.sha256) { throw "Copy verification failed: $($asset.path)." }
    }
    foreach ($file in $manifest.payload) {
        $from = Resolve-ContainedPath (Join-Path $PSScriptRoot 'payload') $file.path
        $to = Resolve-ContainedPath $stage $file.path
        [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($to)) | Out-Null
        [IO.File]::Copy($from, $to, $false)
        if ((Get-FileHashValue $to) -ne $file.sha256) { throw "Copy verification failed: $($file.path)." }
    }
    [IO.File]::WriteAllBytes((Join-Path $stage 'Game\AMOK.EXE'), $patched)
    [IO.Directory]::Move($stage, $Destination)
    $stage = $null
    Write-Host "Success! Open $Destination and double-click Play-Amok.cmd."
    exit 0
} catch {
    Write-Host "Patch could not be applied: $($_.Exception.Message)" -ForegroundColor Red
    if ($stage -and (Test-Path -LiteralPath $stage)) {
        # Remove only this invocation's uniquely named temporary directory.
        $resolvedStage = (Resolve-Path -LiteralPath $stage).Path
        $expectedPrefix = $Destination + '.building-'
        if ($resolvedStage.StartsWith($expectedPrefix, [StringComparison]::OrdinalIgnoreCase) -and
            (Split-Path $resolvedStage -Parent) -eq $destinationParent) {
            Remove-Item -LiteralPath $resolvedStage -Recurse -Force
        }
    }
    exit 1
}
