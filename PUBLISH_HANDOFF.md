# GitHub 发布交接（下回合从这里继续）

## 当前发布状态

## 2026-08-20 最新曲库状态

- Windows/Android 当前曲库 239 首；本轮新增14首经典候选，状态均为 `requires_in_game_audition`，尚不能标记为 final。

- 项目：`JianpuPlayerNext`（Windows 端）
- Windows 版本：`1.0.0-beta.40`；内置曲库 239 首；曲库版本 174
- 当前已核验 EXE：`dist/JianpuPlayerNext-v1.0.0-beta.40.exe`，14,850,064 bytes，SHA-256 `6F0FAD6D9C52E8C53D8659E522BCBCFC14AFA0FABE3D1494A860DCDD2B6B8C4C`
- Android 主播放器（无录制版）：`PocketMusic21-v0.1.0-239songs-no-recording-debug.apk`，10,165,002 bytes，SHA-256 `1875C3E2EB9507B0F2E220B602CE825EBC95C65C9B6B921507547E551BB55478`
- 独立制谱器：`PocketMusic21-ScoreMaker-v0.1.0-239songs-debug.apk`，9,484,970 bytes，SHA-256 `26C72A3BC1F734E0F0BB297067C698E874049BA6A68A3284FB81699669BEF0FD`
- 本轮14首已入库；14首候选均已通过 SongParser、21键和时长门禁，仍需游戏内试听
- 《须弥》确认为网易《一梦江湖》（原《楚留香》手游）少林门派曲，双端正式曲库均已保留；Android ID 为 `song_157`，推荐节拍 511 ms/拍
- 第 213 首《記憶（缘之空）》推荐 627 ms/拍，来源完整、跨端与构建门禁通过，状态仍为 `requires_in_game_audition`。
- 原 14 首热门曲批次：13 首已打包入库；《Secret Base ～君がくれたもの～》仍为 `blocked_source`，未生成或打包谱面
- 2026-08-19 九首结构异常曲已重制并同步（含《东风破》完整 310.869 秒来源）；均标记 `requires_in_game_audition`，四首用户已试听正常的既有曲目未改动。
- 状态：候选曲仍需游戏内试听；GitHub 尚未上传，现在不要上传 GitHub，不要创建或更新 Release
- 上传脚本：`一键上传GitHub.ps1`；开源日发布标题和附件应以239首最新构建为准。

## 标准文件边界

应提交：源码、`builtin_songs/*.txt`、README、LICENSE、CHANGELOG、测试、`.github/workflows`、`docs/`、交接日志和发布脚本。

不得提交：`build/`、`dist/`、`__pycache__/`、`.venv/`、`.publish/`、`publish_logs/`、密钥、Cookie、原始下载音频、Basic Pitch 大文件和本机配置。

歌曲 TXT 只保留按键事件和 `# 推荐节拍: N ms/拍`；来源、许可、事件数和阻塞原因放在报告/日志，不把录音塞进仓库。

## 发布门禁解除后的命令（当前不要执行）

仅在游戏内试听完成、候选状态更新，且维护者明确解除“不要上传”门禁后，才先在项目根目录执行 DryRun：

```powershell
powershell -ExecutionPolicy Bypass -File .\一键上传GitHub.ps1 -RepoName JianpuPlayerNext -Visibility public -PublishRelease -DryRun
```

DryRun 通过后再执行实际发布：

```powershell
powershell -ExecutionPolicy Bypass -File .\一键上传GitHub.ps1 -RepoName JianpuPlayerNext -Visibility public -PublishRelease
```

脚本会测试、检查版本一致性、初始化/提交 Git、推送 `main`、创建当时的版本标签并上传 EXE Release。中文文件名必须使用 `core.quotePath=false` 读取，避免 PowerShell `Test-Path` 误判。

## AI 制谱提示语与工具

先要求 AI 确认可追溯来源和许可；再用 `yt-dlp`/直接下载、`ffmpeg`、Basic Pitch、项目转换脚本生成 TXT；最后运行 `player_core.parse_song`、全库单测和 Android 跨平台检查。下载受限时写 `blocked_source_download`，不得凭歌名猜谱。

## 公开前检查

确认 `gh auth status` 已登录但不打印令牌；确认 README、SONGS_NOTICE、AI 工作流和版本号一致；确认 APK/EXE 大小与 SHA-256 仅写日志或 Release 说明；确认所有自动转谱候选仍标记 `requires_in_game_audition`。
