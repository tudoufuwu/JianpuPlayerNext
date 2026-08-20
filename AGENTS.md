# AI 接手说明

本目录是独立的新版播放器仓库根目录。不要把父目录 `F:\codexai\01`、旧版
`music_player/`、音频素材、模型、构建缓存或历史归档加入本仓库。

## 当前真值

- 应用版本：以 `app.py` 中的 `APP_VERSION` 为准。
- Python 包版本：`pyproject.toml`，升版时必须同步。
- 内置曲库：`builtin_songs/`。
- 当前基线：`1.0.0-beta.41`、240 首、曲库版本 175。
- 最新已验证程序：`dist/JianpuPlayerNext-v1.0.0-beta.41.exe`。

## 每次新增歌曲后的门禁

1. 同步 `builtin_songs/`、推荐节拍、曲库版本及测试数量。
2. 同步 `app.py`、`pyproject.toml`、`CHANGELOG.md` 与 README 中的版本/曲数。
3. 在本目录运行：

   ```powershell
   python -m unittest discover -s tests -p "test_*.py" -v
   .\build.ps1
   ```

4. 核验 EXE 文件名与 `APP_VERSION` 一致，再执行 `一键上传GitHub.ps1`。
5. 不得打印 GitHub token、Cookie 或其他凭据。

父工作区的连续制谱状态以 `F:\codexai\01\制谱任务队列.jsonl` 最后一行和
`F:\codexai\01\制谱续跑日志.md` 末尾为准。

