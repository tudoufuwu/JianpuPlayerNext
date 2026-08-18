# GitHub 发布交接（下回合从这里继续）

## 当前发布状态

- 项目：`JianpuPlayerNext`（Windows 端）
- 版本：`1.0.0-beta.33`；内置曲库 195 首；曲库版本 147
- EXE：`dist/JianpuPlayerNext-v1.0.0-beta.33.exe`（只作为 Release 附件，不进 Git 历史）
- 19 首周杰伦候选已入库；《轨迹》《半岛铁盒》《菊花台》只有阻塞报告
- 上传脚本：`一键上传GitHub.ps1`

## 标准文件边界

应提交：源码、`builtin_songs/*.txt`、README、LICENSE、CHANGELOG、测试、`.github/workflows`、`docs/`、交接日志和发布脚本。

不得提交：`build/`、`dist/`、`__pycache__/`、`.venv/`、`.publish/`、`publish_logs/`、密钥、Cookie、原始下载音频、Basic Pitch 大文件和本机配置。

歌曲 TXT 只保留按键事件和 `# 推荐节拍: N ms/拍`；来源、许可、事件数和阻塞原因放在报告/日志，不把录音塞进仓库。

## 下一回合上传命令

先在项目根目录执行 DryRun：

```powershell
powershell -ExecutionPolicy Bypass -File .\一键上传GitHub.ps1 -RepoName JianpuPlayerNext -Visibility public -PublishRelease -DryRun
```

DryRun 通过后再执行实际发布：

```powershell
powershell -ExecutionPolicy Bypass -File .\一键上传GitHub.ps1 -RepoName JianpuPlayerNext -Visibility public -PublishRelease
```

脚本会测试、检查版本一致性、初始化/提交 Git、推送 `main`、创建 `v1.0.0-beta.33` 标签并上传 EXE Release。中文文件名必须使用 `core.quotePath=false` 读取，避免 PowerShell `Test-Path` 误判。

## AI 制谱提示语与工具

先要求 AI 确认可追溯来源和许可；再用 `yt-dlp`/直接下载、`ffmpeg`、Basic Pitch、项目转换脚本生成 TXT；最后运行 `player_core.parse_song`、全库单测和 Android 跨平台检查。下载受限时写 `blocked_source_download`，不得凭歌名猜谱。

## 公开前检查

确认 `gh auth status` 已登录但不打印令牌；确认 README、SONGS_NOTICE、AI 工作流和版本号一致；确认 APK/EXE 大小与 SHA-256 仅写日志或 Release 说明；确认所有自动转谱候选仍标记 `requires_in_game_audition`。
