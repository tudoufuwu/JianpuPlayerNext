[CmdletBinding()]
param(
    [string]$ServerHost,
    [string]$ServerUser = "root",
    [string]$RemoteRoot = "/var/www/update",
    [string]$SshKeyPath,
    [switch]$Upload
)

$ErrorActionPreference = "Stop"
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$androidDir = Join-Path (Split-Path -Parent $projectDir) "mobile_player_android"
$windowsAsset = Join-Path $projectDir "dist\JianpuPlayerNext-v1.0.0-beta.48.exe"
$androidAsset = Join-Path $androidDir "app\build\outputs\apk\debug\app-debug.apk"

if (-not (Test-Path -LiteralPath $windowsAsset)) { throw "Windows artifact missing: $windowsAsset" }
if (-not (Test-Path -LiteralPath $androidAsset)) { throw "Android artifact missing: $androidAsset" }
if ($Upload -and [string]::IsNullOrWhiteSpace($ServerHost)) { throw "-ServerHost is required with -Upload" }
if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) { throw "ssh is required" }
if (-not (Get-Command scp -ErrorAction SilentlyContinue)) { throw "scp is required" }

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$releaseDir = Join-Path $projectDir "publish\releases\$timestamp"
$windowsDir = Join-Path $releaseDir "windows"
$androidReleaseDir = Join-Path $releaseDir "android"
New-Item -ItemType Directory -Force -Path $windowsDir, $androidReleaseDir | Out-Null

$windowsName = Split-Path -Leaf $windowsAsset
$androidName = "PocketMusic21-v0.1.0-270songs-debug.apk"
$windowsTarget = Join-Path $windowsDir $windowsName
$androidTarget = Join-Path $androidReleaseDir $androidName
Copy-Item -LiteralPath $windowsAsset -Destination $windowsTarget
Copy-Item -LiteralPath $androidAsset -Destination $androidTarget

$manifest = [ordered]@{
    schema = 2
    product = "JianpuPlayerNext / PocketMusic21"
    version = "1.0.0-beta.48"
    libraryCount = 270
    releaseId = $timestamp
    publishedAt = (Get-Date).ToUniversalTime().ToString("o")
    platforms = [ordered]@{
        windows = [ordered]@{ latestVersion = "1.0.0-beta.48"; download = "/windows/$windowsName"; archive = "/releases/$timestamp/windows/$windowsName"; sha256 = (Get-FileHash $windowsTarget -Algorithm SHA256).Hash.ToLowerInvariant() }
        android = [ordered]@{ latestVersion = "0.1.0-mvp-270"; download = "/android/$androidName"; archive = "/releases/$timestamp/android/$androidName"; sha256 = (Get-FileHash $androidTarget -Algorithm SHA256).Hash.ToLowerInvariant() }
    }
}
$manifestPath = Join-Path $releaseDir "manifest.json"
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding UTF8

Write-Host "Prepared release: $releaseDir"
Write-Host "Manifest: $manifestPath"
if (-not $Upload) {
    Write-Host "Local only. Add -Upload -ServerHost <host> to upload over SSH."
    exit 0
}

$target = "$ServerUser@$ServerHost"
$sshArgs = @()
if (-not [string]::IsNullOrWhiteSpace($SshKeyPath)) { $sshArgs += @("-i", $SshKeyPath) }
& ssh @sshArgs $target "mkdir -p '$RemoteRoot/releases/$timestamp' '$RemoteRoot/windows' '$RemoteRoot/android'"
if ($LASTEXITCODE -ne 0) { throw "Remote directory creation failed" }
& scp @sshArgs -r $releaseDir "$target`:$RemoteRoot/releases/"
if ($LASTEXITCODE -ne 0) { throw "Upload failed" }
& scp @sshArgs $windowsTarget "$target`:$RemoteRoot/windows/$windowsName"
if ($LASTEXITCODE -ne 0) { throw "Windows latest upload failed" }
& scp @sshArgs $androidTarget "$target`:$RemoteRoot/android/$androidName"
if ($LASTEXITCODE -ne 0) { throw "Android latest upload failed" }
& scp @sshArgs $manifestPath "$target`:$RemoteRoot/manifest.json"
if ($LASTEXITCODE -ne 0) { throw "Manifest upload failed" }
Write-Host "Uploaded archive and latest files: $target`:$RemoteRoot (release $timestamp)"
