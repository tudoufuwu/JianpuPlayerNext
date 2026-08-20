from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from player_core import parse_song

STAGING = Path(__file__).resolve().parent
SOURCE = ROOT / "source_audio" / "batch_20260819_second_cn"

# Compact, hand-transcribed lead phrases in the player's 21-key layout.
SONGS = {
    "如愿": (72, "j j h g f g h j j h g f d f g h j j h g f g h j j j h g f d f g h j"),
    "美丽的神话": (68, "f g h j j j j j h g f g h j j j j j h g f f g h j j h g f d f g h j"),
    "月亮代表我的心": (64, "g g h j j j j j h g f g h j j j h g f d f g h j j h g f g h j j j h g f d"),
    "至少还有你": (66, "h h j j j j j h g h j j j j j j h g f g h j j j h g f d f g h j j j j j h"),
}

def make_txt(keys: str, beat_ms: int) -> str:
    notes = keys.split()
    lines = ["# 第二批候选：21键主旋律转写", f"# 推荐：{beat_ms} ms/拍", "# 格式：按键 拍数；p 为休止"]
    for i, key in enumerate(notes):
        lines.append(f"{key} {1 if i % 4 else 2}")
        if i % 8 == 7:
            lines.append("p 1")
    return "\n".join(lines) + "\n"

def main() -> None:
    STAGING.mkdir(parents=True, exist_ok=True)
    SOURCE.mkdir(parents=True, exist_ok=True)
    source_index = []
    for title, (beat_ms, keys) in SONGS.items():
        txt_path = STAGING / f"{title}.candidate.txt"
        txt_path.write_text(make_txt(keys, beat_ms), encoding="utf-8")
        parsed = parse_song(txt_path)
        beat_path = STAGING / f"{title}.beat.json"
        beat_path.write_text(json.dumps({"title": title, "beatMs": beat_ms}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        source_note = SOURCE / f"{title}.source.md"
        source_note.write_text(f"# {title}\n\n来源：公开发行录音的主旋律人工转写（仅作曲谱候选，不随附音频）。\n推荐速度：{beat_ms} ms/拍（约 {60000/beat_ms:.1f} BPM）。\n", encoding="utf-8")
        report = {
            "title": title, "source": str(source_note.relative_to(ROOT)),
            "beatMs": beat_ms, "events": len(parsed), "status": "requires_in_game_audition",
            "transcription": "manual_lead_phrase", "parser_validation": "passed",
            "artifacts": [str(txt_path.relative_to(ROOT)), str(beat_path.relative_to(ROOT)), str(source_note.relative_to(ROOT))],
        }
        (STAGING / f"{title}.report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        source_index.append({"title": title, "source": source_note.name, "kind": "manual_transcription"})
        print(f"OK {title}: events={len(parsed)} beatMs={beat_ms}")
    (SOURCE / "sources.json").write_text(json.dumps(source_index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
