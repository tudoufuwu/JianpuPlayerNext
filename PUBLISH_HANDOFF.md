# GitHub 发布交接（下回合从这里继续）

## 当前待发布版本 beta.47（2026-08-22）

- Windows/Android 当前曲库为 267 首；新增 `song_264`–`song_267` 候选，均需游戏内试听确认。
- Windows `dist/JianpuPlayerNext-v1.0.0-beta.47.exe`，SHA-256 `B70EC3E992E378A3DF4047C1A9B3AF8C6602E8B02DB13815E77FA57BCFA66FF4`。
- Windows 主界面可直接调整播放倍率；设置页继续调整一拍时间；倍率范围 `0.25x`–`4.00x`。
- Android 最新 debug APK：`app/build/outputs/apk/debug/app-debug.apk`，SHA-256 `C94255ECE23B76FFF6042A091E97480900E36E83A0FEC5CD3CEFB5951CC943D5`。
- Android 悬浮曲库已将基础节拍和倍速分开调整，支持直接输入倍速。
- 本次只更新仓库代码和交接文档；Release 附件和自动更新源仍待确认后发布。

## 当前本地曲库（2026-08-21）

- Windows/Android 当前曲库为 264 首；新增 `song_264`《夏空的歌（短原版）》，推荐 535 ms/拍，状态 `requires_in_game_audition`。
- Windows `dist/JianpuPlayerNext-v1.0.0-beta.46.exe`：14,924,412 bytes，SHA-256 `8FA86100D6C3FBB08A9D82FA8E577574346DE1FA582029BF95514DE0586416DE`。
- Android `artifacts/PocketMusic21-v0.1.0-264songs-no-recording-debug.apk`：10,166,777 bytes，SHA-256 `6B69587A1D1DD77F1BE7928B6B9A5D2609AD7784C85EB49857109BE790C02707`。

- Windows/Android 当前曲库为263首；新增 `song_258`–`song_263`：红豆、匆匆那年、素颜、一直很安静、传奇、千年之恋。
- 六首均为 `requires_in_game_audition` 自动候选，未完成游戏内试听，不能称为 final。
- GitHub 未上传，未创建 Release；263首包需完成本轮构建门禁后再记录附件哈希。
- Windows 263首候选构建：`dist/JianpuPlayerNext-v1.0.0-beta.45.exe`，14,923,368 bytes，SHA-256 `3A388142A1AEBFB3F151121486050FB1CBEACB39759BDD81C9CAE2B90DDF9E14`。

## 2026-08-20 爆种 OLD-HITS04（暂不上传）

- 当前 Windows/Android 曲库为 255 首；新增《一生所爱》`song_255`，仍需游戏内试听，未标 final。
- 《泡沫》《我们的爱》《God knows...》来源阻塞，未入正式曲库。
- Android 255 首 APK 与跨端门禁结果记录在 `mobile_player_android/PUBLISH_HANDOFF.md`；GitHub 未上传。
- Windows 当前构建：`dist/JianpuPlayerNext-v1.0.0-beta.44.exe`，14,897,765 bytes，SHA-256 `46FE95A80E05614268149AC92BD1414377DA5A696EAC0255F3D723513841946D`。

## 当前发布状态

## 2026-08-20 最新曲库状态

- Windows/Android 当前曲库 254 首；本轮新增 8 首候选，状态 `requires_in_game_audition`，尚不能标记为 final。

- 项目：`JianpuPlayerNext`（Windows 端）
- Windows 版本：`1.0.0-beta.44`；内置曲库 254 首；曲库版本 182
- 当前已核验 EXE：`dist/JianpuPlayerNext-v1.0.0-beta.44.exe`，14,894,042 bytes，SHA-256 `3633446460756F02721F4B12EF0E4A1B8B4833E4137574B50AF1CB956597B513`
- Android 主播放器（无录制版）：`PocketMusic21-v0.1.0-254songs-no-recording-debug.apk`，10,166,067 bytes，SHA-256 `DA1F07246EFBB3FB1CA73806D3FC9C34363D8E7A3E3E06351B0BCDE7357F3985`
- 独立制谱器：`PocketMusic21-ScoreMaker-v0.1.0-240songs-debug.apk`，9,484,970 bytes，SHA-256 `26C72A3BC1F734E0F0BB297067C698E874049BA6A68A3284FB81699669BEF0FD`
- 本轮14首已入库；14首候选均已通过 SongParser、21键和时长门禁，仍需游戏内试听
- 《须弥》确认为网易《一梦江湖》（原《楚留香》手游）少林门派曲，双端正式曲库均已保留；Android ID 为 `song_157`，推荐节拍 511 ms/拍
- 第 213 首《記憶（缘之空）》推荐 627 ms/拍，来源完整、跨端与构建门禁通过，状态仍为 `requires_in_game_audition`。
- 原 14 首热门曲批次：13 首已打包入库；《Secret Base ～君がくれたもの～》仍为 `blocked_source`，未生成或打包谱面
- 2026-08-19 九首结构异常曲已重制并同步（含《东风破》完整 310.869 秒来源）；均标记 `requires_in_game_audition`，四首用户已试听正常的既有曲目未改动。
- 状态：候选曲仍需游戏内试听；GitHub 尚未上传，现在不要上传 GitHub，不要创建或更新 Release
- 上传脚本：`一键上传GitHub.ps1`；开源日发布标题和附件应以254首最新构建为准。

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
