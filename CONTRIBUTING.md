# 参与开发

## 环境

- Windows 10/11
- Python 3.11+

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m unittest discover -s tests -p "test_*.py" -v
```

## 提交要求

- 不提交 `build/`、`dist/`、虚拟环境、缓存、日志、原始音视频或模型。
- 新增曲谱必须能够被播放器解析，并同步推荐节拍、曲库数量和变更记录。
- 修改发布版本时同步 `app.py` 与 `pyproject.toml`。
- 提交前必须运行全部测试；Windows 发布包使用 `build.ps1` 构建。
- 曲谱及第三方内容还需遵守 `SONGS_NOTICE.md` 与 `THIRD_PARTY_NOTICES.md`。
