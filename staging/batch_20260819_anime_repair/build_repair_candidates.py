from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from midi_importer import analyze_midi, convert_midi
from player_core import parse_song


SONGS = {
    "光るなら": {
        "midi": "光るなら_ichigos_4673_repaired.mid",
        "source": "Ichigo's Sheet Music",
        "source_url": "https://ichigos.com/res/getfile.php?id=4673&type=midi&token=7a2d0afbafcc27a8eacf32e6dfbea451",
        "original_midi": "source_audio/batch_20260819_anime/光るなら_ichigos_4673.mid",
        "repair": {
            "kind": "structural_byte_repair",
            "removed_offsets_hex": [
                "0x344", "0x38e", "0x40e", "0x458", "0x4c6", "0x522",
                "0x618", "0x66b", "0x67f", "0x7aa", "0x80f", "0x81a",
                "0x876", "0x8db", "0x8e6", "0x8f1", "0x95f", "0x985",
            ],
            "removed_bytes": 18,
            "reason": "Each listed zero byte preceded an explicit status byte (0x80/0x90/0xb0), causing strict MIDI parsers to treat the status as a data byte. Removing only these malformed separator bytes preserves all note/status bytes and makes the original track parseable.",
        },
    },
    "残酷天使的行动纲领": {
        "midi": "残酷天使的行动纲领_ichigos_4337_verified.mid",
        "source": "Ichigo's Sheet Music",
        "source_url": "https://ichigos.com/res/getfile.php?id=4337&type=midi&token=6c871a4a5d9962da0b58968d1c034ba4",
        "original_midi": "source_audio/batch_20260819_anime/残酷天使的行动纲领_ichigos_4337.mid",
        "repair": {
            "kind": "byte_identical_local_verification_copy",
            "removed_bytes": 0,
            "reason": "The existing Ichigo's MIDI is parser-valid; the verified copy is isolated in this repair batch without changing musical bytes.",
        },
    },
}


def render(events) -> str:
    return "\n".join(f"{event.keys} {event.beats:g}" for event in events) + "\n"


def main() -> None:
    staging = Path(__file__).resolve().parent
    source_dir = ROOT / "source_audio" / "batch_20260819_anime_repair"
    for title, metadata in SONGS.items():
        midi_path = source_dir / metadata["midi"]
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
        candidate_path = staging / f"{title}.candidate.txt"
        candidate_path.write_text(txt, encoding="utf-8")
        parsed = parse_song(candidate_path)
        if parsed != list(result.events):
            raise RuntimeError(f"{title}: parser round-trip mismatch")
        beat_path = staging / f"{title}.beat.json"
        report_path = staging / f"{title}.report.json"
        beat_path.write_text(
            json.dumps({"title": title, "beatMs": result.beat_ms}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        report = {
            "title": title,
            "artist": "Goose house" if title == "光るなら" else "高橋洋子",
            "audio": str(midi_path.relative_to(ROOT)).replace("\\", "/"),
            "source": metadata["source"],
            "source_url": metadata["source_url"],
            "original_midi": metadata["original_midi"],
            "repair": metadata["repair"],
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
                str(candidate_path.relative_to(ROOT)).replace("\\", "/"),
                str(beat_path.relative_to(ROOT)).replace("\\", "/"),
                str(report_path.relative_to(ROOT)).replace("\\", "/"),
            ],
        }
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"OK {title}: events={len(result.events)} beatMs={result.beat_ms} raw_notes={result.stats.source_notes}")


if __name__ == "__main__":
    main()
