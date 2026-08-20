from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from midi_importer import analyze_midi, convert_midi
from player_core import parse_song

title = "残酷天使的行动纲领"
source = ROOT / "source_audio" / "batch_20260819_anime" / "残酷天使的行动纲领_ichigos_4337.mid"
staging = Path(__file__).resolve().parent
analysis = analyze_midi(source)
result = convert_midi(source, analysis.recommended_tracks, black_key_strategy="nearest", beat_step=0.125)
candidate = staging / f"{title}.candidate.txt"
candidate.write_text("\n".join(f"{event.keys} {event.beats:g}" for event in result.events) + "\n", encoding="utf-8")
if parse_song(candidate) != list(result.events):
    raise RuntimeError("parser round-trip mismatch")
(staging / f"{title}.beat.json").write_text(json.dumps({"title": title, "beatMs": result.beat_ms}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
report = {
    "title": title,
    "audio": str(source.relative_to(ROOT)),
    "beatMs": result.beat_ms,
    "events": len(result.events),
    "raw_notes": result.stats.source_notes,
    "status": "requires_in_game_audition",
    "selected_tracks": list(analysis.recommended_tracks),
    "tempo_bpm": analysis.tempo_bpm,
    "duration_seconds": analysis.duration_seconds,
    "transpose": result.transpose,
    "conversion": {"kept_notes": result.stats.kept_notes, "dropped_notes": result.stats.dropped_notes, "approximated_notes": result.stats.approximated_notes, "out_of_range_notes": result.stats.out_of_range_notes, "chord_count": result.stats.chord_count},
    "parser_validation": "passed",
}
(staging / f"{title}.report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False))
