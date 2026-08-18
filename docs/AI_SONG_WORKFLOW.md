# AI 制谱工作流（可复现摘要）

这份文档把本项目的制谱交接日志压缩成可复用流程，供维护者或其他 AI 接手。它描述工具链和验收门禁，不授予任何歌曲原作或录音的授权。

## 推荐提示语

```text
你是 21 键游戏曲谱维护者。只处理指定歌曲和指定文件范围。
先确认可追溯音频/MIDI 来源及许可；来源不可核验时写阻塞报告，禁止凭歌名猜旋律。
用 Basic Pitch 或等价音高转写得到 MIDI/CSV，再做单旋律聚类、滑音/重复音压缩、21 键白键映射和节拍估计。
生成 UTF-8 TXT，首行写“# 推荐节拍: N ms/拍”，并保留 source、status、beatMs、events、raw_notes 报告。
运行 player_core.parse_song 和全库测试；状态只能是 requires_in_game_audition 或 final，自动转谱默认前者。
不要修改其他歌曲、版本号或发布文件；完成后报告文件、来源、事件数和验证命令。
```

## 工具顺序

1. 选择可访问且可记录的来源（官方/授权、Wikimedia、Internet Archive 或用户提供文件）。不绕过登录、反爬或版权限制。
2. `yt-dlp`/直接下载只用于取得允许使用的音频；`ffmpeg` 转 WAV。
3. `.venv_audio\Scripts\python.exe` 调用 `basic_pitch.inference.predict_and_save`，保留 CSV、MIDI 和报告。
4. 使用项目已有构建脚本把 MIDI/CSV 转为 TXT；事件必须通过 `player_core.parse_song`。
5. 同步 `builtin_songs/`、推荐速度、曲库版本和测试数量，再运行：

```powershell
python -m unittest discover -s tests -p "test_*.py"
.\build.ps1
```

6. Android 端以桌面 `builtin_songs/` 为真值，运行 `tools\Check-CrossPlatformLibrary.ps1`，再执行 Android 单测、Lint、assembleDebug。

## 交接报告最低字段

`title`、`source`、`source_license`（如有）、`audio`、`beat_ms`/`beatMs`、`events`、`raw_notes`、`status`、`artifacts`。

如果下载受限，写 `blocked_source_download`，记录尝试过的 URL/ID 和错误；不要创建空谱或猜测谱。所有音频转谱候选都必须在游戏内试听后才能标记 final。
