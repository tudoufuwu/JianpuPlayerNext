from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import mido

from midi_importer import (
    LOW_TO_HIGH_KEYS,
    analyze_midi,
    choose_best_transpose,
    convert_midi,
)
from player_core import parse_song, format_song_txt


def build_fixture(path: Path) -> None:
    mid = mido.MidiFile(ticks_per_beat=480)
    meta = mido.MidiTrack()
    meta.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(120), time=0))
    meta.append(mido.MetaMessage("end_of_track", time=1920))
    mid.tracks.append(meta)

    melody = mido.MidiTrack()
    melody.append(mido.MetaMessage("track_name", name="Lead Melody", time=0))
    melody.append(mido.Message("program_change", program=73, channel=0, time=0))
    melody.append(mido.Message("note_on", note=60, velocity=90, channel=0, time=0))
    melody.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=240))
    melody.append(mido.Message("note_on", note=64, velocity=90, channel=0, time=240))
    melody.append(mido.Message("note_on", note=67, velocity=90, channel=0, time=0))
    melody.append(mido.Message("note_off", note=64, velocity=0, channel=0, time=240))
    melody.append(mido.Message("note_off", note=67, velocity=0, channel=0, time=0))
    melody.append(mido.Message("note_on", note=66, velocity=80, channel=0, time=240))
    melody.append(mido.Message("note_off", note=66, velocity=0, channel=0, time=480))
    mid.tracks.append(melody)

    drums = mido.MidiTrack()
    drums.append(mido.MetaMessage("track_name", name="Drums", time=0))
    for _ in range(4):
        drums.append(mido.Message("note_on", note=36, velocity=100, channel=9, time=120))
        drums.append(mido.Message("note_off", note=36, velocity=0, channel=9, time=120))
    mid.tracks.append(drums)
    mid.save(path)


class MidiImporterTests(unittest.TestCase):
    def test_analysis_recommends_melody_and_marks_drums(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.mid"
            build_fixture(path)
            analysis = analyze_midi(path)
            self.assertEqual(analysis.recommended_tracks, (1,))
            self.assertEqual(analysis.tracks[1].name, "Lead Melody")
            self.assertEqual(analysis.tracks[1].note_count, 4)
            self.assertTrue(analysis.tracks[2].percussion)
            self.assertAlmostEqual(analysis.tempo_bpm, 120.0, places=1)

    def test_conversion_creates_chord_and_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            midi_path = Path(directory) / "fixture.mid"
            txt_path = Path(directory) / "fixture.txt"
            build_fixture(midi_path)
            result = convert_midi(midi_path, [1], transpose=0, black_key_strategy="nearest")
            self.assertEqual(result.beat_ms, 500)
            self.assertTrue(any(len(event.keys) == 2 for event in result.events))
            self.assertEqual(result.stats.approximated_notes, 1)
            txt_path.write_text(format_song_txt(result.events, beat_ms=result.beat_ms), encoding="utf-8")
            self.assertEqual(parse_song(txt_path), list(result.events))

    def test_drop_strategy_removes_black_key(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.mid"
            build_fixture(path)
            result = convert_midi(path, [1], transpose=0, black_key_strategy="drop")
            self.assertEqual(result.stats.dropped_notes, 1)
            self.assertEqual(result.stats.kept_notes, 3)

    def test_auto_transpose_prefers_playable_range(self) -> None:
        transpose = choose_best_transpose([84, 86, 88])
        self.assertLess(transpose, 0)

    def test_keyboard_has_exactly_twenty_one_unique_keys(self) -> None:
        self.assertEqual(len(LOW_TO_HIGH_KEYS), 21)
        self.assertEqual(len(set(LOW_TO_HIGH_KEYS)), 21)


if __name__ == "__main__":
    unittest.main()

