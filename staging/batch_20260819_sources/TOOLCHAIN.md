# 勇气音频工具链诊断

状态：已找到并验证可用工具链；未安装任何依赖，也未写入 WAV、曲库或应用文件。

## 已验证组件

- FFmpeg：`C:\Program Files (x86)\Moo0\VideoCutter 1.17\optional_tools\ffmpeg.exe`
  - `N-89861-g78e884f-Reino`（2018 build）
  - 支持 `mov,mp4,m4a,3gp,3g2,mj2`、AAC 解码和 `pcm_s16le` WAV 编码。
- Python：`F:\codexai\01\.venv_audio\Scripts\python.exe` (Python 3.11.8)
  - `basic-pitch 0.4.0`, `librosa 0.11.0`, `soundfile 0.14.0`, `audioread 3.1.0`, `onnxruntime 1.27.0`, `mido 1.3.3`。

## 输入确认

`source.m4a` 是 358.53 秒、AAC-LC、48 kHz、立体声 M4A（FFmpeg 报告 bitrate 322 kb/s）。以下命令以 `NUL` 丢弃输出，仅验证，不生成文件：

```powershell
$ffDir = 'C:\Program Files (x86)\Moo0\VideoCutter 1.17\optional_tools'
$env:Path = "$ffDir;$env:Path"
$src = 'F:\codexai\01\music_player_next\staging\batch_20260819_sources\勇气\source.m4a'
$ffmpeg = Join-Path $ffDir 'ffmpeg.exe'

& $ffmpeg -hide_banner -i $src -map 0:a:0 -f null NUL
# exit 0; AAC -> pcm_s16le 解码成功

& $ffmpeg -y -hide_banner -i $src -map 0:a:0 -vn -ac 1 -ar 16000 `
    -c:a pcm_s16le -f wav NUL
# exit 0; WAV 编码成功
```

实际生成 WAV 时，将最后一个 `NUL` 换成目标 `.wav` 路径即可。

## 已验证候选流水线

`librosa.load(source.m4a, sr=22050, mono=True)` 在上述 PATH 下成功，得到 7,905,543 samples（358.528 秒）。Basic Pitch 的仓库转谱入口也已无写入运行成功：

```powershell
@'
from pathlib import Path
from basic_pitch.inference import predict
src = Path(r'F:\codexai\01\music_player_next\staging\batch_20260819_sources\勇气\source.m4a')
model_output, midi_data, note_events = predict(src)
print(len(note_events), len(midi_data.instruments), sorted(model_output))
'@ | & F:\codexai\01\.venv_audio\Scripts\python.exe -
```

结果：`2407` note events、`1` MIDI instrument、输出键为 `contour/note/onset`。M4A 读取会先提示 PySoundFile failed，再由 librosa/audioread 调用 PATH 中的 FFmpeg，这是预期的兼容路径。

## 不要使用

`C:\Program Files\BlueStacks_nxt_cn\ffmpeg.exe` 虽能识别 M4A 容器，但其 build 配置禁用了 AAC 等大多数解码器，不能作为本源文件的解码器。

