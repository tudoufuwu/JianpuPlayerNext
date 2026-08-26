[CmdletBinding()]
param(
    [string]$ServerHost,
    [string]$ServerUser = "root",
    [string]$RemoteRoot = "/var/www/update",
    [string]$SshKeyPath,
    [string[]]$ReleaseNotes = @("Windows and Android update."),
    [switch]$Upload
)

$ErrorActionPreference = "Stop"
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$androidDir = Join-Path (Split-Path -Parent $projectDir) "mobile_player_android"
$windowsAsset = Join-Path $projectDir "dist\JianpuPlayerNext-v1.0.0-beta.50.exe"
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
$androidName = "PocketMusic21-v0.1.0-mvp-20260826-282songs-debug.apk"
$windowsTarget = Join-Path $windowsDir $windowsName
$androidTarget = Join-Path $androidReleaseDir $androidName
Copy-Item -LiteralPath $windowsAsset -Destination $windowsTarget
Copy-Item -LiteralPath $androidAsset -Destination $androidTarget

$manifest = [ordered]@{
    schema = 2
    product = "JianpuPlayerNext / PocketMusic21"
    version = "1.0.0-beta.50"
    libraryCount = 282
    androidVersion = "0.1.0-mvp-20260826"
    userContentPolicy = "User-imported and recorded TXT songs are stored outside bundled assets and preserved across updates."
    releaseId = $timestamp
    publishedAt = (Get-Date).ToUniversalTime().ToString("o")
    releaseNotes = @($ReleaseNotes)
    dataPolicy = [ordered]@{
        builtin = "The packaged library is managed by releases."
        userData = "User-recorded or imported TXT files must remain in the user's data directory and are not replaced by library updates."
    }
    platforms = [ordered]@{
        windows = [ordered]@{ latestVersion = "1.0.0-beta.50"; download = "/windows/$windowsName"; archive = "/releases/$timestamp/windows/$windowsName"; sha256 = (Get-FileHash $windowsTarget -Algorithm SHA256).Hash.ToLowerInvariant() }
        android = [ordered]@{ latestVersion = "0.1.0-mvp-20260826"; download = "/android/$androidName"; archive = "/releases/$timestamp/android/$androidName"; sha256 = (Get-FileHash $androidTarget -Algorithm SHA256).Hash.ToLowerInvariant() }
    }
}
$manifestPath = Join-Path $releaseDir "manifest.json"
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding UTF8

# Build a small release page and a root history page from all archived manifests.
$htmlEncode = { param([object]$Value) [System.Net.WebUtility]::HtmlEncode([string]$Value) }
$releaseNotesHtml = (($ReleaseNotes | ForEach-Object { "<li>$(& $htmlEncode $_)</li>" }) -join "`n")
$releaseIndex = @"
<!doctype html>
<html lang="en"><meta charset="utf-8"><title>$(& $htmlEncode $manifest.product) $(& $htmlEncode $manifest.version)</title>
<h1>$(& $htmlEncode $manifest.product) $(& $htmlEncode $manifest.version)</h1>
<p>Published: $(& $htmlEncode $manifest.publishedAt) (UTC) | Release: $(& $htmlEncode $manifest.releaseId)</p>
<details open><summary>Release notes</summary><ul>$releaseNotesHtml</ul></details>
<h2>Downloads</h2><ul>
<li><a href="windows/$(& $htmlEncode $windowsName)">Windows ($(& $htmlEncode $manifest.platforms.windows.latestVersion))</a></li>
<li><a href="android/$(& $htmlEncode $androidName)">Android ($(& $htmlEncode $manifest.platforms.android.latestVersion))</a></li>
</ul><p><a href="../../index.html">Version history</a></p></html>
"@
$releaseIndexPath = Join-Path $releaseDir "index.html"
$releaseIndex | Set-Content -LiteralPath $releaseIndexPath -Encoding UTF8

$publishRoot = Join-Path $projectDir "publish"
$historyItems = @()
foreach ($archivedDir in (Get-ChildItem -LiteralPath (Join-Path $publishRoot "releases") -Directory | Sort-Object Name -Descending)) {
    $archivedManifestPath = Join-Path $archivedDir.FullName "manifest.json"
    if (-not (Test-Path -LiteralPath $archivedManifestPath)) { continue }
    try { $archivedManifest = Get-Content -LiteralPath $archivedManifestPath -Raw | ConvertFrom-Json } catch { continue }
    $archivedReleaseId = if ([string]::IsNullOrWhiteSpace($archivedManifest.releaseId)) { $archivedDir.Name } else { $archivedManifest.releaseId }
    $archivedPublishedAt = if ($archivedManifest.publishedAt) { $archivedManifest.publishedAt } else { $archivedManifest.createdAt }
    $notes = @($archivedManifest.releaseNotes)
    if ($notes.Count -eq 0) { $notes = @("Release $archivedReleaseId") }
    $notesHtml = (($notes | ForEach-Object { "<li>$(& $htmlEncode $_)</li>" }) -join "`n")
    $platformNames = if ($archivedManifest.platforms) { @($archivedManifest.platforms.PSObject.Properties.Name) } else { @("windows", "android") }
    $platforms = @($platformNames | ForEach-Object { & $htmlEncode $_ }) -join ", "
    $archivedPage = if (Test-Path -LiteralPath (Join-Path $archivedDir.FullName "index.html")) { "index.html" } else { "manifest.json" }
    $historyItems += "<details><summary>$(& $htmlEncode $archivedManifest.version) - $(& $htmlEncode $archivedReleaseId)</summary><p>Published: $(& $htmlEncode $archivedPublishedAt) (UTC) | Platforms: $platforms</p><ul>$notesHtml</ul><p><a href=`"releases/$archivedReleaseId/$archivedPage`">Open release</a></p></details>"
}
$historyPath = Join-Path $publishRoot "index.html"
$historyHtml = @"
<!doctype html>
<html lang="en"><meta charset="utf-8"><title>JianpuPlayerNext / PocketMusic21 version history</title>
<h1>JianpuPlayerNext / PocketMusic21 version history</h1>
<p>Current releases and archived downloads.</p>
$($historyItems -join "`n")
</html>
"@
$historyHtml | Set-Content -LiteralPath $historyPath -Encoding UTF8

Write-Host "Prepared release: $releaseDir"
Write-Host "Manifest: $manifestPath"
Write-Host "History: $historyPath"
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
& scp @sshArgs $historyPath "$target`:$RemoteRoot/index.html"
if ($LASTEXITCODE -ne 0) { throw "History upload failed" }
Write-Host "Uploaded archive and latest files: $target`:$RemoteRoot (release $timestamp)"
