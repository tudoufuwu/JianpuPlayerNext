$ErrorActionPreference = "Stop"
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$versionMatch = Select-String -LiteralPath (Join-Path $projectDir "app.py") -Pattern '^APP_VERSION = "([^"]+)"$'
if (-not $versionMatch) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show("无法读取新版播放器版本。", "启动失败", "OK", "Error") | Out-Null
    exit 1
}

$version = $versionMatch.Matches[0].Groups[1].Value
$exe = Join-Path $projectDir "dist\JianpuPlayerNext-v$version.exe"
if (-not (Test-Path -LiteralPath $exe)) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show("尚未找到 $exe，请先构建最新版。", "启动失败", "OK", "Error") | Out-Null
    exit 1
}

Start-Process -FilePath $exe -WorkingDirectory $projectDir

