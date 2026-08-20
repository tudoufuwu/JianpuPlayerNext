from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from midi_importer import analyze_midi, convert_midi
from player_core import parse_song


SONGS = {
    "天空之城（君をのせて）": "天空之城_ichigos_743.mid",
    "Summer": "Summer_ichigos_4645.mid",
    "青鸟": "青鸟_ichigos_2190.mid",
    "光るなら": "光るなら_ichigos_4673.mid",
    "残酷天使的行动纲领": "残酷天使的行动纲领_ichigos_4337.mid",
}


def render(events) -> str:
    return "\n".join(f"{event.keys} {event.beats:g}" for event in events) + "\n"


def main() -> None:
    staging = Path(__file__).resolve().parent
    source_dir = ROOT / "source_audio" / "batch_20260819_anime"
    for title, filename in SONGS.items():
        midi_path = source_dir / filename
        analysis = analyze_midi(midi_path)
        if not analysis.recommended_tracks:
            raise RuntimeError(f"{title}: no recommended melody track")
        result = convert_midi(
            midi_path,
            analysis.recommended_tracks,
            black_key_strategy="nearest",
            beat_step=0.125,
        )
        txt = render(result.events)
        # player_core.parse_song accepts a path; validate the exact candidate bytes.
        candidate_path = Path(__file__).resolve().parent / f"{title}.candidate.txt"
        candidate_path.write_text(txt, encoding="utf-8")
        parsed = parse_song(candidate_path)
        if parsed != list(result.events):
            raise RuntimeError(f"{title}: parser round-trip mismatch")
        candidate_path.write_text(txt, encoding="utf-8")
        report = {
            "title": title,
            "audio": str(midi_path.relative_to(ROOT)),
            "beatMs": result.beat_ms,
            "events": len(result.events),
            "raw_notes": result.stats.source_notes,
            "status": "requires_in_game_audition",
            "selected_tracks": list(analysis.recommended_tracks),
            "track_analysis": [
                {
                    "index": t.index,
                    "name": t.name,
                    "instrument": t.instrument,
                    "note_count": t.note_count,
                    "range": t.range_text,
                    "percussion": t.percussion,
                    "score": t.score,
                }
                for t in analysis.tracks
            ],
            "tempo_bpm": analysis.tempo_bpm,
            "duration_seconds": analysis.duration_seconds,
            "transpose": result.transpose,
            "conversion": {
                "kept_notes": result.stats.kept_notes,
                "dropped_notes": result.stats.dropped_notes,
                "approximated_notes": result.stats.approximated_notes,
                "out_of_range_notes": result.stats.out_of_range_notes,
                "chord_count": result.stats.chord_count,
            },
            "parser_validation": "passed",
            "artifacts": [
                str((staging / f"{title}.candidate.txt").relative_to(ROOT)),
                str((staging / f"{title}.beat.json").relative_to(ROOT)),
            ],
        }
        (staging / f"{title}.beat.json").write_text(
            json.dumps({"title": title, "beatMs": result.beat_ms}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (staging / f"{title}.report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"OK {title}: events={len(result.events)} beatMs={result.beat_ms} raw_notes={result.stats.source_notes}")


if __name__ == "__main__":
    main()
