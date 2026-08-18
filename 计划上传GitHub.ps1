[CmdletBinding()]
param(
    [datetime]$At = [datetime]"2026-08-20 12:00:00",
    [string]$RepoName = "JianpuPlayerNext",
    [ValidateSet("private", "public")]
    [string]$Visibility = "private"
)

$ErrorActionPreference = "Stop"
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$publishScript = Join-Path $projectDir "一键上传GitHub.ps1"
$taskName = "JianpuPlayerNext-GitHub-Publish"
$powerShell = (Get-Command powershell.exe).Source
$arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$publishScript`" -RepoName `"$RepoName`" -Visibility $Visibility -Build -PublishRelease"

$action = New-ScheduledTaskAction -Execute $powerShell -Argument $arguments -WorkingDirectory $projectDir
$trigger = New-ScheduledTaskTrigger -Once -At $At
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "测试、构建并发布 JianpuPlayerNext 到 GitHub" -Force | Out-Null
Write-Host "已注册：$taskName"
Write-Host "执行时间：$($At.ToString('yyyy-MM-dd HH:mm:ss'))"
Write-Host "仓库：$RepoName（$Visibility）"

