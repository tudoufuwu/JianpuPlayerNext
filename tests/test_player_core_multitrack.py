from __future__ import annotations

from pathlib import Path
import tempfile
import threading
import time
import unittest

from player_core import (
    PlaybackEngine,
    SongEvent,
    SongProgram,
    Track,
    format_song_txt,
    parse_song,
    parse_song_program,
)
from app import recommended_beat_ms


V2_TEXT = """#format: 2
# 曲名: 测试双轨

[track main]
a 2
s 1

[track accomp]
q 3
p 1
"""


class FakeBackend:
    def __init__(self) -> None:
        self.actions: list[tuple[str, str]] = []
        self.down: set[str] = set()
        self.lock = threading.Lock()

    def key_down(self, key: str) -> None:
        with self.lock:
            self.actions.append(("down", key))
            self.down.add(key)

    def key_up(self, key: str) -> None:
        with self.lock:
            self.actions.append(("up", key))
            self.down.discard(key)


def write_txt(text: str) -> Path:
    temp = tempfile.NamedTemporaryFile(
        suffix=".txt", delete=False, mode="w", encoding="utf-8"
    )
    temp.write(text)
    temp.close()
    return Path(temp.name)


class MultiTrackParseTests(unittest.TestCase):
    def test_v1_file_loads_as_single_main_track(self) -> None:
        path = write_txt("a 1\np 0.5\nsd 2\n")
        program = parse_song_program(path)
        self.assertFalse(program.is_multi)
        self.assertEqual([t.name for t in program.tracks], ["main"])
        self.assertEqual(program.main_events, parse_song(path))

    def test_v2_sections_split_tracks(self) -> None:
        path = write_txt(V2_TEXT)
        program = parse_song_program(path)
        self.assertTrue(program.is_multi)
        self.assertEqual([t.name for t in program.tracks], ["main", "accomp"])
        self.assertEqual(
            program.main_events,
            [SongEvent("a", 2.0), SongEvent("s", 1.0)],
        )
        self.assertEqual(
            list(program.tracks[1].events),
            [SongEvent("q", 3.0), SongEvent("p", 1.0)],
        )

    def test_v2_is_rejected_by_legacy_parser(self) -> None:
        path = write_txt(V2_TEXT)
        # The exact message differs per line content; the contract is a loud
        # ValueError, never a silent single-track mash.
        with self.assertRaises(ValueError):
            parse_song(path)

    def test_explicit_leading_main_marker_is_not_a_duplicate(self) -> None:
        path = write_txt("[track main]\na 1\n[track accomp]\ns 1\n")
        program = parse_song_program(path)
        self.assertEqual([t.name for t in program.tracks], ["main", "accomp"])

    def test_duplicate_track_rejected(self) -> None:
        path = write_txt("[track main]\na 1\n[track main]\ns 1\n")
        with self.assertRaisesRegex(ValueError, "轨道重复"):
            parse_song_program(path)

    def test_unknown_track_name_rejected(self) -> None:
        path = write_txt("[track drums]\na 1\n")
        with self.assertRaisesRegex(ValueError, "不支持的轨道名"):
            parse_song_program(path)

    def test_empty_track_rejected(self) -> None:
        path = write_txt("[track main]\na 1\n[track accomp]\n")
        with self.assertRaisesRegex(ValueError, "至少需要一个音符事件"):
            parse_song_program(path)

    def test_invalid_event_line_reports_line_number(self) -> None:
        path = write_txt("[track main]\na 1\n[track accomp]\nk 1\n")
        with self.assertRaisesRegex(ValueError, "第 4 行"):
            parse_song_program(path)


class MultiTrackPlaybackTests(unittest.TestCase):
    def run_engine(self, engine: PlaybackEngine, program: SongProgram, **kwargs) -> None:
        engine.start(program, beat_ms=50, **kwargs)
        deadline = time.monotonic() + 3
        while engine.running and time.monotonic() < deadline:
            time.sleep(0.005)

    def test_parallel_tracks_press_and_release_independently(self) -> None:
        backend = FakeBackend()
        engine = PlaybackEngine(backend)
        program = parse_song_program(write_txt(V2_TEXT))
        self.run_engine(engine, program)
        self.assertEqual(
            backend.actions,
            [
                ("down", "a"),
                ("down", "q"),
                ("up", "a"),
                ("up", "q"),
                ("down", "s"),
                ("up", "s"),
            ],
        )
        self.assertFalse(backend.down)

    def test_same_key_overlap_sends_single_press(self) -> None:
        backend = FakeBackend()
        engine = PlaybackEngine(backend)
        program = parse_song_program(
            write_txt("[track main]\na 2\n\n[track accomp]\na 1\n")
        )
        self.run_engine(engine, program)
        self.assertEqual(backend.actions, [("down", "a"), ("up", "a")])
        self.assertFalse(backend.down)

    def test_seek_from_main_index_keeps_crossing_holds(self) -> None:
        backend = FakeBackend()
        engine = PlaybackEngine(backend)
        program = parse_song_program(
            write_txt("[track main]\na 1\ns 1\nd 1\n\n[track accomp]\nq 6\n")
        )
        self.run_engine(engine, program, start_index=2)
        self.assertEqual(
            backend.actions,
            [("down", "q"), ("down", "d"), ("up", "d"), ("up", "q")],
        )
        self.assertFalse(backend.down)

    def test_stop_releases_every_held_key(self) -> None:
        backend = FakeBackend()
        states: list[str] = []
        engine = PlaybackEngine(backend, on_state=lambda state, _m: states.append(state))
        program = parse_song_program(
            write_txt("[track main]\na 20\n\n[track accomp]\nq 20\n")
        )
        engine.start(program, beat_ms=50)
        time.sleep(0.05)
        engine.stop()
        time.sleep(0.05)
        self.assertFalse(backend.down)
        self.assertIn("stopped", states)

    def test_progress_reports_main_track_index(self) -> None:
        backend = FakeBackend()
        progress: list[int] = []
        engine = PlaybackEngine(
            backend, on_progress=lambda index, _total, _event: progress.append(index)
        )
        program = parse_song_program(
            write_txt("[track main]\na 1\ns 1\nd 1\n\n[track accomp]\nq 3\n")
        )
        self.run_engine(engine, program)
        self.assertEqual(progress, [1, 2, 3])

    def test_rejects_out_of_range_start_event(self) -> None:
        engine = PlaybackEngine(FakeBackend())
        program = parse_song_program(write_txt(V2_TEXT))
        with self.assertRaisesRegex(ValueError, "播放起点"):
            engine.start(program, beat_ms=50, start_index=99)


class BuiltinLibraryRegressionTests(unittest.TestCase):
    def test_every_builtin_song_parses_identically_through_program_loader(self) -> None:
        songs_dir = Path(__file__).resolve().parents[1] / "builtin_songs"
        files = sorted(songs_dir.glob("*.txt"))
        self.assertGreater(len(files), 200)
        for path in files:
            with self.subTest(song=path.name):
                legacy = parse_song(path)
                program = parse_song_program(path)
                self.assertFalse(program.is_multi, path.name)
                self.assertEqual(program.main_events, legacy, path.name)


if __name__ == "__main__":
    unittest.main()
