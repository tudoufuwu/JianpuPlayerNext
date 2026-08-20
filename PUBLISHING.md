# GitHub 发布说明

> **当前发布门禁：不要上传。** 本地测试基线为 Windows `1.0.0-beta.37` / 208 首，Android 测试 APK 命名为 `PocketMusic21-v0.1.0-mvp-208songs-recording-fix-debug.apk`。原 14 首批次中只有 13 首已打包，《Secret Base ～君がくれたもの～》仍为 `blocked_source`；候选曲仍需游戏内试听。以下命令只能在维护者明确解除门禁后使用。

## 仓库内容

`music_player_next/` 本身就是仓库根目录，包含 README、LICENSE、变更记录、
依赖说明、测试和 GitHub Actions。`build/`、`dist/`、缓存和本地发布日志已由
`.gitignore` 排除；EXE 通过 GitHub Releases 分发，不写入 Git 历史。

## 一键上传

当前电脑已安装 Git 与 GitHub CLI。首次发布默认创建 **private** 仓库，避免在
最终检查前意外公开：

```powershell
.\一键上传GitHub.ps1 -Build -PublishRelease
```

脚本会在执行当时读取最新版本和歌曲，因此在计划日期前新增并完成验收的歌曲会
自动进入最终快照。流程为：测试 → 可选构建 → 大文件检查 → 初始化 Git → 提交 →
创建/连接远程仓库 → 推送 main → 创建版本标签 → 上传 EXE Release。

仅检查、不上传：

```powershell
.\一键上传GitHub.ps1 -DryRun
```

指定仓库名或公开仓库：

```powershell
.\一键上传GitHub.ps1 -RepoName JianpuPlayerNext -Visibility public -Build -PublishRelease
```

## 定时任务

`计划上传GitHub.ps1` 用于注册 Windows 一次性任务。默认时间为
2026-08-20 12:00（北京时间），默认创建 private 仓库：

```powershell
.\计划上传GitHub.ps1
```

查看任务：

```powershell
Get-ScheduledTask -TaskName JianpuPlayerNext-GitHub-Publish
```

取消任务：

```powershell
Unregister-ScheduledTask -TaskName JianpuPlayerNext-GitHub-Publish -Confirm:$false
```

定时任务采用“执行时快照”，不是现在冻结文件。电脑需开机、当前用户需登录，且
GitHub CLI 登录仍有效。执行日志写入 `publish_logs/`，该目录不会上传。
