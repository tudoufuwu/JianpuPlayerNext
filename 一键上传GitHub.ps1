[CmdletBinding()]
param(
    [string]$RepoName = "JianpuPlayerNext",
    [ValidateSet("private", "public")]
    [string]$Visibility = "private",
    [switch]$Build,
    [switch]$PublishRelease,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectDir

$logDir = Join-Path $projectDir "publish_logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logPath = Join-Path $logDir ("publish-{0}.log" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
Start-Transcript -LiteralPath $logPath | Out-Null

try {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Git 未安装" }
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw "GitHub CLI 未安装" }
    gh auth status | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "GitHub CLI 尚未登录，请先执行 gh auth login" }

    $versionMatch = Select-String -LiteralPath ".\app.py" -Pattern '^APP_VERSION = "([^"]+)"$'
    if (-not $versionMatch) { throw "app.py 中未找到 APP_VERSION" }
    $version = $versionMatch.Matches[0].Groups[1].Value
    $packageVersion = (Select-String -LiteralPath ".\pyproject.toml" -Pattern '^version = "([^"]+)"$').Matches[0].Groups[1].Value
    $normalizedPackageVersion = $packageVersion -replace 'b(\d+)$', '-beta.$1'
    if ($normalizedPackageVersion -ne $version) {
        throw "版本不一致：app.py=$version，pyproject.toml=$packageVersion"
    }

    python -m unittest discover -s tests -p "test_*.py" -v
    if ($LASTEXITCODE -ne 0) { throw "自动测试失败" }

    if ($Build) {
        & ".\build.ps1"
    }

    $asset = Join-Path $projectDir "dist\JianpuPlayerNext-v$version.exe"
    if ($PublishRelease -and -not (Test-Path -LiteralPath $asset)) {
        throw "发布文件不存在：$asset；请加 -Build 或先完成构建"
    }

    $candidateFiles = Get-ChildItem -Recurse -File | Where-Object {
        $_.FullName -notmatch '\\(build|dist|__pycache__|[^\\]+\.egg-info|publish_logs|\.publish)\\'
    }
    $tooLarge = $candidateFiles | Where-Object Length -GT 90MB
    if ($tooLarge) { throw "发现超过 90 MiB 的源码候选文件：$($tooLarge.FullName -join ', ')" }

    Write-Host "检查完成：版本 $version，歌曲 $((Get-ChildItem .\builtin_songs -File -Filter *.txt).Count) 首。"
    if ($DryRun) {
        Write-Host "DryRun：未初始化、提交或上传 GitHub。"
        return
    }

    if (-not (Test-Path -LiteralPath ".git\config")) {
        git init -b main
        if ($LASTEXITCODE -ne 0) { throw "git init 失败" }
    }

    $login = gh api user --jq .login
    $userId = gh api user --jq .id
    if (-not (git config user.name)) { git config user.name $login }
    if (-not (git config user.email)) { git config user.email "$userId+$login@users.noreply.github.com" }

    git add --all
    # Disable Git's C-style quoting so non-ASCII song filenames remain valid paths in PowerShell.
    $stagedPaths = git -c core.quotePath=false diff --cached --name-only
    $trackedTooLarge = foreach ($path in $stagedPaths) {
        if (Test-Path -LiteralPath $path) {
            $item = Get-Item -LiteralPath $path
            if ($item.Length -gt 90MB) { $item }
        }
    }
    if ($trackedTooLarge) { throw "暂存区含超大文件：$($trackedTooLarge.FullName -join ', ')" }

    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        git commit -m "release: v$version"
        if ($LASTEXITCODE -ne 0) { throw "git commit 失败" }
    } else {
        Write-Host "没有需要提交的新变化。"
    }

    $owner = gh api user --jq .login
    $repo = "$owner/$RepoName"
    $remoteNames = @(git remote)
    if (-not ($remoteNames -contains "origin")) {
        # gh emits a native error for a missing repo; temporarily relax PowerShell's
        # native-error policy so that the existence check remains a boolean.
        $previousErrorAction = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        gh repo view $repo 2>$null | Out-Null
        $repoExists = ($LASTEXITCODE -eq 0)
        $ErrorActionPreference = $previousErrorAction
        if ($repoExists) {
            git remote add origin "https://github.com/$repo.git"
        } else {
            gh repo create $repo "--$Visibility" --source . --remote origin
            if ($LASTEXITCODE -ne 0) { throw "创建 GitHub 仓库失败" }
        }
    }

    git push -u origin main
    if ($LASTEXITCODE -ne 0) { throw "推送 main 失败" }

    if ($PublishRelease) {
        $tag = "v$version"
        $existingTag = @(git tag --list $tag)
        if (-not ($existingTag -contains $tag)) { git tag -a $tag -m "JianpuPlayerNext $version" }
        git push origin $tag
        $previousErrorAction = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        gh release view $tag --repo $repo 2>$null | Out-Null
        $releaseExists = ($LASTEXITCODE -eq 0)
        $ErrorActionPreference = $previousErrorAction
        if ($releaseExists) {
            gh release upload $tag $asset --repo $repo --clobber
        } else {
            gh release create $tag $asset --repo $repo --generate-notes --title "JianpuPlayerNext $version"
        }
        if ($LASTEXITCODE -ne 0) { throw "GitHub Release 发布失败" }
    }

    Write-Host "发布完成：https://github.com/$repo"
}
finally {
    Stop-Transcript | Out-Null
}

