# 21键曲谱播放器

一个面向 Windows 21 键游戏乐器的本地曲库、MIDI 转换与后台演奏工具。新版位于独立目录，和旧版播放器的数据、配置与程序互不覆盖。

当前发布元数据：`1.0.0-beta.33`，内置曲库版本 `147`（195 首）。本轮并行新增 19 首周杰伦候选；均为音频转写候选，使用前请在游戏内试听校准。

## 主要功能

- 内置 195 首 TXT 曲谱，可搜索、收藏、打标签并维护播放历史。
- 导入标准 MIDI，自动分析音轨并推荐主旋律。
- 将 MIDI 映射到 21 个白键，支持自动移调、黑键取最近白键或丢弃、1/4～1/16 量化。
- 转换结果可在本机试听 30 秒、保存为 TXT，并立即加入曲库。
- 可绑定指定游戏窗口，提供播放、暂停、停止、队列、顺序与单曲循环。
- 录谱、全局热键、按键间隔和倒计时等设置继续保留。
- AI 制谱与交接规范见 [`docs/AI_SONG_WORKFLOW.md`](docs/AI_SONG_WORKFLOW.md)，包含提示语、工具顺序和验收门禁。

## 直接运行

普通玩家建议从 GitHub Releases 下载 `JianpuPlayerNext-*.exe`。程序无需安装；首次启动会把内置曲谱复制到：

```text
%LOCALAPPDATA%\JianpuPlayerNext
```

播放器使用 Windows 输入接口向目标窗口发送按键。若游戏以管理员身份运行，播放器也需要管理员权限，因此发布版会显示 Windows UAC 提示。

## 从源码运行

需要 Windows 10/11 和 Python 3.11 或更高版本：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python app.py
```

## MIDI 使用建议

1. 选择 MIDI 后，优先保留系统推荐的旋律音轨。
2. 默认使用“最近白键 + 自动移调 + 1/8 量化”，通常最适合直接试听。
3. 鼓组会被识别并默认排除；多音轨同时转换可能让 21 键结果过密。
4. MIDI 的力度、延音踏板、音色和复杂和声不能被 21 个键完整复现，转换结果应当视为可继续编辑的草稿。
5. 转换页右上角的“？ 使用说明”会区分适合直接转换的旋律 MIDI 与需要另做主旋律提取的复杂单轨钢琴 MIDI。

## 测试与打包

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
.\build.ps1
```

打包结果位于 `dist\JianpuPlayerNext-*.exe`。推送 `v*` 标签时，GitHub Actions 也会构建 Windows 发布文件并附加到 Release。

首次上传、后续一键发布和定时发布方法见 [PUBLISHING.md](PUBLISHING.md)。其他 AI 或维护者接手前请先读 [AGENTS.md](AGENTS.md) 与 [PROJECT_STATE.md](PROJECT_STATE.md)。

## 项目结构

```text
music_player_next/
├─ app.py                 # Tkinter 界面与应用编排
├─ player_core.py         # 曲谱解析、播放和录谱核心
├─ midi_importer.py       # MIDI 分析与 21 键转换
├─ library_store.py       # 收藏、标签、历史等元数据
├─ preview_audio.py       # 本机短试听
├─ builtin_songs/         # 内置 TXT 曲谱
├─ tests/                 # 自动测试
├─ .github/workflows/     # Windows CI 与发布构建
└─ JianpuPlayerNext.spec  # PyInstaller 配置
```

界面和实现为本项目独立设计，没有复制其他播放器的源代码、名称或素材。功能思路本身可借鉴行业常见做法。

## 版权与许可

程序源代码按 [MIT License](LICENSE) 开放。`builtin_songs/` 中的编配文本不因代码开源而自动获得原作品授权；发布和使用前请阅读 [SONGS_NOTICE.md](SONGS_NOTICE.md)。第三方依赖见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

