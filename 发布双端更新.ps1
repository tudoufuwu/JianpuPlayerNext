[CmdletBinding()]
param(
    [string]$ServerHost,
    [string]$ServerUser = "root",
    [string]$RemoteRoot = "/var/www/update",
    [string]$SshKeyPath,
    [string[]]$ReleaseNotes = @(
        "双端曲库更新至 301 首，新增《永不失联的爱（简谱版）》与《永不失联的爱（完整版）》。",
        "推荐速度分别为 706 ms/拍与 654 ms/拍；两版均为 candidate，需游戏内试听。",
        "覆盖安装会保留用户导入和录制的 TXT 曲谱，历史版本仍可从更新页下载。"
    ),
    [switch]$Upload
)

$ErrorActionPreference = "Stop"
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$androidDir = Join-Path (Split-Path -Parent $projectDir) "mobile_player_android"
$windowsAsset = Join-Path $projectDir "dist\JianpuPlayerNext-v1.0.0-beta.55.exe"
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
$androidName = "PocketMusic21-v0.1.0-mvp-20260925-301songs-debug.apk"
$windowsTarget = Join-Path $windowsDir $windowsName
$androidTarget = Join-Path $androidReleaseDir $androidName
Copy-Item -LiteralPath $windowsAsset -Destination $windowsTarget
Copy-Item -LiteralPath $androidAsset -Destination $androidTarget

$manifest = [ordered]@{
    schema = 2
    product = "JianpuPlayerNext / PocketMusic21"
    version = "1.0.0-beta.55"
    libraryCount = 301
    androidVersion = "0.1.0-mvp-20260925"
    userContentPolicy = "User-imported and recorded TXT songs are stored outside bundled assets and preserved across updates."
    releaseId = $timestamp
    publishedAt = (Get-Date).ToUniversalTime().ToString("o")
    releaseNotes = @($ReleaseNotes)
    dataPolicy = [ordered]@{
        builtin = "The packaged library is managed by releases."
        userData = "User-recorded or imported TXT files must remain in the user's data directory and are not replaced by library updates."
    }
    platforms = [ordered]@{
        windows = [ordered]@{ latestVersion = "1.0.0-beta.55"; download = "/windows/$windowsName"; archive = "/releases/$timestamp/windows/$windowsName"; sha256 = (Get-FileHash $windowsTarget -Algorithm SHA256).Hash.ToLowerInvariant() }
        android = [ordered]@{ latestVersion = "0.1.0-mvp-20260925"; download = "/android/$androidName"; archive = "/releases/$timestamp/android/$androidName"; sha256 = (Get-FileHash $androidTarget -Algorithm SHA256).Hash.ToLowerInvariant() }
    }
}
$manifestPath = Join-Path $releaseDir "manifest.json"
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding UTF8

# Build a release page and a root history page from all archived manifests.
$htmlEncode = { param([object]$Value) [System.Net.WebUtility]::HtmlEncode([string]$Value) }
$releaseNotesHtml = (($ReleaseNotes | ForEach-Object { "<li>$(& $htmlEncode $_)</li>" }) -join "`n")
if ([string]::IsNullOrWhiteSpace($releaseNotesHtml)) { $releaseNotesHtml = "<li>暂无更新说明。</li>" }
$releaseIndex = @"
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>$(& $htmlEncode $manifest.product) $(& $htmlEncode $manifest.version) 下载</title>
  <style>
    :root { color-scheme: light; --ink: #172033; --muted: #64748b; --line: #dbe4f0; --panel: #ffffff; --blue: #2563eb; --blue-dark: #1d4ed8; --green: #059669; }
    * { box-sizing: border-box; }
    body { margin: 0; color: var(--ink); background: #f4f7fb; font-family: "Microsoft YaHei", "PingFang SC", system-ui, -apple-system, sans-serif; line-height: 1.65; }
    a { color: var(--blue); }
    .wrap { width: min(1040px, calc(100% - 32px)); margin: 0 auto; padding: 48px 0 64px; }
    .hero { overflow: hidden; position: relative; padding: 42px; color: #fff; border-radius: 24px; background: linear-gradient(135deg, #172554, #2563eb 68%, #38bdf8); box-shadow: 0 24px 60px rgba(30, 64, 175, .22); }
    .eyebrow { margin: 0 0 8px; font-size: .9rem; font-weight: 700; letter-spacing: .08em; opacity: .82; }
    h1 { margin: 0; font-size: clamp(2rem, 5vw, 3.4rem); line-height: 1.16; }
    .lead { max-width: 720px; margin: 16px 0 0; font-size: 1.08rem; color: #dbeafe; }
    .meta { margin: 18px 0 0; font-size: .88rem; color: #bfdbfe; overflow-wrap: anywhere; }
    .download-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin-top: 26px; }
    .download { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 18px 20px; color: var(--ink); text-decoration: none; border: 1px solid rgba(255,255,255,.6); border-radius: 16px; background: rgba(255,255,255,.96); box-shadow: 0 12px 24px rgba(15, 23, 42, .12); transition: transform .18s ease, box-shadow .18s ease; }
    .download:hover { transform: translateY(-2px); box-shadow: 0 16px 30px rgba(15, 23, 42, .18); }
    .download strong, .download span { display: block; }
    .download span { margin-top: 2px; color: var(--muted); font-size: .88rem; }
    .download b { flex: 0 0 auto; padding: 7px 11px; color: #fff; border-radius: 999px; background: var(--blue); font-size: .82rem; }
    .panel { margin-top: 24px; padding: 30px 34px; border: 1px solid var(--line); border-radius: 20px; background: var(--panel); box-shadow: 0 12px 36px rgba(15, 23, 42, .06); }
    h2 { margin: 0 0 12px; font-size: 1.35rem; }
    ul { margin: 0; padding-left: 1.35rem; }
    li + li { margin-top: 8px; }
    .history-link { display: inline-flex; margin-top: 24px; font-weight: 700; text-decoration: none; }
    .history-link:hover { text-decoration: underline; }
    @media (max-width: 680px) {
      .wrap { width: min(100% - 20px, 1040px); padding: 20px 0 36px; }
      .hero { padding: 26px 20px; border-radius: 18px; }
      .download-grid { grid-template-columns: 1fr; }
      .download { padding: 16px; }
      .panel { padding: 22px 20px; border-radius: 16px; }
    }
  </style>
</head>
<body>
  <main class="wrap">
    <section class="hero">
      <p class="eyebrow">最新版本 · 可直接下载</p>
      <h1>$(& $htmlEncode $manifest.product)</h1>
      <p class="lead">桌面端 $(& $htmlEncode $manifest.platforms.windows.latestVersion) 与 Android 端 $(& $htmlEncode $manifest.platforms.android.latestVersion) 已发布。</p>
      <p class="meta">发布时间：$(& $htmlEncode $manifest.publishedAt)（UTC） · 发布编号：$(& $htmlEncode $manifest.releaseId)</p>
      <div class="download-grid" aria-label="最新版下载">
        <a class="download" href="windows/$(& $htmlEncode $windowsName)"><span><strong>Windows 桌面版</strong><span>版本 $(& $htmlEncode $manifest.platforms.windows.latestVersion)</span></span><b>下载 EXE</b></a>
        <a class="download" href="android/$(& $htmlEncode $androidName)"><span><strong>Android 手机版</strong><span>版本 $(& $htmlEncode $manifest.platforms.android.latestVersion)</span></span><b>下载 APK</b></a>
      </div>
    </section>
    <section class="panel">
      <h2>本次更新内容</h2>
      <ul>$releaseNotesHtml</ul>
      <a class="history-link" href="../../index.html">查看全部历史版本 →</a>
    </section>
  </main>
</body>
</html>
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
    $archivedHref = & $htmlEncode "releases/$archivedReleaseId/$archivedPage"
    $historyItems += @"
<details class="release-card">
  <summary><span><strong>版本 $(& $htmlEncode $archivedManifest.version)</strong><small>发布编号 $(& $htmlEncode $archivedReleaseId)</small></span><span class="toggle">查看详情</span></summary>
  <div class="release-body">
    <p class="release-meta">发布时间：$(& $htmlEncode $archivedPublishedAt)（UTC） · 平台：$platforms</p>
    <ul>$notesHtml</ul>
    <a class="release-link" href="$archivedHref">打开此版本 →</a>
  </div>
</details>
"@
}
$historyPath = Join-Path $publishRoot "index.html"
$historyHtml = @"
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>JianpuPlayerNext / PocketMusic21 下载与历史版本</title>
  <style>
    :root { color-scheme: light; --ink: #172033; --muted: #64748b; --line: #dbe4f0; --panel: #ffffff; --blue: #2563eb; --blue-dark: #1d4ed8; }
    * { box-sizing: border-box; }
    body { margin: 0; color: var(--ink); background: #f4f7fb; font-family: "Microsoft YaHei", "PingFang SC", system-ui, -apple-system, sans-serif; line-height: 1.65; }
    a { color: var(--blue); }
    .wrap { width: min(1040px, calc(100% - 32px)); margin: 0 auto; padding: 48px 0 64px; }
    .hero { padding: 40px; color: #fff; border-radius: 24px; background: linear-gradient(135deg, #172554, #2563eb 68%, #38bdf8); box-shadow: 0 24px 60px rgba(30, 64, 175, .22); }
    .badge { display: inline-block; padding: 5px 10px; border: 1px solid rgba(255,255,255,.35); border-radius: 999px; background: rgba(255,255,255,.12); font-size: .82rem; font-weight: 700; }
    h1 { margin: 14px 0 0; font-size: clamp(2rem, 5vw, 3.35rem); line-height: 1.15; }
    .lead { margin: 14px 0 0; color: #dbeafe; font-size: 1.05rem; }
    .meta { margin: 16px 0 0; color: #bfdbfe; font-size: .86rem; overflow-wrap: anywhere; }
    .download-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin-top: 26px; }
    .download { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 18px 20px; color: var(--ink); text-decoration: none; border-radius: 16px; background: #fff; box-shadow: 0 12px 24px rgba(15, 23, 42, .13); transition: transform .18s ease, box-shadow .18s ease; }
    .download:hover { transform: translateY(-2px); box-shadow: 0 16px 30px rgba(15, 23, 42, .2); }
    .download strong, .download span { display: block; }
    .download span { margin-top: 2px; color: var(--muted); font-size: .88rem; }
    .download b { flex: 0 0 auto; padding: 7px 11px; color: #fff; border-radius: 999px; background: var(--blue); font-size: .82rem; }
    .latest-notes, .history { margin-top: 24px; }
    .latest-notes { padding: 28px 32px; border: 1px solid var(--line); border-radius: 20px; background: var(--panel); box-shadow: 0 12px 36px rgba(15, 23, 42, .06); }
    h2 { margin: 0; font-size: 1.45rem; }
    .section-copy { margin: 6px 0 18px; color: var(--muted); }
    ul { margin: 12px 0 0; padding-left: 1.35rem; }
    li + li { margin-top: 7px; }
    .release-card { margin-top: 12px; overflow: hidden; border: 1px solid var(--line); border-radius: 16px; background: var(--panel); box-shadow: 0 8px 24px rgba(15, 23, 42, .045); }
    summary { display: flex; align-items: center; justify-content: space-between; gap: 18px; padding: 20px 22px; cursor: pointer; list-style: none; }
    summary::-webkit-details-marker { display: none; }
    summary strong, summary small { display: block; }
    summary small { margin-top: 2px; color: var(--muted); font-weight: 400; overflow-wrap: anywhere; }
    .toggle { flex: 0 0 auto; color: var(--blue); font-size: .88rem; font-weight: 700; }
    details[open] .toggle { font-size: 0; }
    details[open] .toggle::after { content: "收起"; font-size: .88rem; }
    .release-body { padding: 0 22px 22px; border-top: 1px solid #edf2f7; }
    .release-meta { color: var(--muted); font-size: .9rem; overflow-wrap: anywhere; }
    .release-link { display: inline-flex; margin-top: 16px; font-weight: 700; text-decoration: none; }
    .release-link:hover { text-decoration: underline; }
    @media (max-width: 680px) {
      .wrap { width: min(100% - 20px, 1040px); padding: 20px 0 36px; }
      .hero { padding: 26px 20px; border-radius: 18px; }
      .download-grid { grid-template-columns: 1fr; }
      .download { padding: 16px; }
      .latest-notes { padding: 22px 20px; border-radius: 16px; }
      summary { align-items: flex-start; padding: 17px 18px; }
      .release-body { padding: 0 18px 18px; }
    }
  </style>
</head>
<body>
  <main class="wrap">
    <section class="hero">
      <span class="badge">最新版</span>
      <h1>简谱播放器双端下载</h1>
      <p class="lead">JianpuPlayerNext Windows 桌面版与 PocketMusic21 Android 手机版。</p>
      <p class="meta">发布时间：$(& $htmlEncode $manifest.publishedAt)（UTC） · 发布编号：$(& $htmlEncode $manifest.releaseId)</p>
      <div class="download-grid" aria-label="最新版下载">
        <a class="download" href="windows/$(& $htmlEncode $windowsName)"><span><strong>Windows 桌面版</strong><span>版本 $(& $htmlEncode $manifest.platforms.windows.latestVersion)</span></span><b>下载 EXE</b></a>
        <a class="download" href="android/$(& $htmlEncode $androidName)"><span><strong>Android 手机版</strong><span>版本 $(& $htmlEncode $manifest.platforms.android.latestVersion)</span></span><b>下载 APK</b></a>
      </div>
    </section>
    <section class="latest-notes">
      <h2>最新版更新内容</h2>
      <ul>$releaseNotesHtml</ul>
    </section>
    <section class="history">
      <h2>历史版本</h2>
      <p class="section-copy">按发布时间从新到旧排列，点击版本卡片查看更新说明和归档下载。</p>
      $($historyItems -join "`n")
    </section>
  </main>
</body>
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
