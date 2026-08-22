from __future__ import annotations

from pathlib import Path
import ctypes
import tempfile
import threading
import time
import unittest

from player_core import (
    INPUT,
    PlaybackEngine,
    SongEvent,
    WindowMessageKeyBackend,
    format_song_txt,
    parse_song,
    recorded_presses_to_events,
)
from app import filter_song_names, normalize_playback_rate, recommended_beat_ms


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


class PlaybackRateTests(unittest.TestCase):
    def test_presets_and_custom_values(self) -> None:
        self.assertEqual(normalize_playback_rate("1.25x"), 1.25)
        self.assertEqual(normalize_playback_rate("0.83"), 0.83)
        self.assertEqual(normalize_playback_rate("3.50x"), 3.5)

    def test_rate_range_is_bounded(self) -> None:
        with self.assertRaises(ValueError):
            normalize_playback_rate("0.24")
        with self.assertRaises(ValueError):
            normalize_playback_rate("4.01")

class AccessDeniedBackend:
    def key_down(self, _key: str) -> None:
        error = PermissionError(5, "Access is denied")
        error.winerror = 5
        raise error

    def key_up(self, _key: str) -> None:
        return


class FakeUser32:
    def __init__(self, valid: bool = True) -> None:
        self.valid = valid
        self.messages: list[tuple[int, int, int, int]] = []

    def IsWindow(self, _hwnd: int) -> bool:
        return self.valid

    def MapVirtualKeyW(self, vk: int, _mode: int) -> int:
        return vk - 0x40

    def PostMessageW(self, hwnd: int, message: int, vk: int, lparam: int) -> bool:
        self.messages.append((hwnd, message, vk, lparam))
        return True


class PlayerTests(unittest.TestCase):
    def test_song_name_search(self) -> None:
        names = ["春庭雪", "长天雪满", "鸳鸯戏"]
        self.assertEqual(filter_song_names(names, " 雪 "), ["春庭雪", "长天雪满"])
        self.assertEqual(filter_song_names(names, "鸳鸯"), ["鸳鸯戏"])
        self.assertEqual(filter_song_names(names, "不存在"), [])

    def test_recommended_tempo_lookup(self) -> None:
        self.assertEqual(recommended_beat_ms("最后的旅行"), 870)
        self.assertEqual(recommended_beat_ms("莫问归期"), 980)
        self.assertEqual(recommended_beat_ms("你若三冬"), 614)
        self.assertEqual(recommended_beat_ms("天亮之前说再见"), 769)
        self.assertEqual(recommended_beat_ms("探窗"), 912)
        self.assertEqual(recommended_beat_ms("风筝误"), 807)
        self.assertEqual(recommended_beat_ms("天下"), 745)
        self.assertEqual(recommended_beat_ms("有点甜"), 605)
        self.assertEqual(recommended_beat_ms("明月天涯"), 484)
        self.assertEqual(recommended_beat_ms("海阔天空"), 807)
        self.assertEqual(recommended_beat_ms("望故乡"), 921)
        self.assertEqual(recommended_beat_ms("离别开出花"), 549)
        self.assertEqual(recommended_beat_ms("长生诀"), 826)
        self.assertEqual(recommended_beat_ms("十年人间"), 619)
        self.assertEqual(recommended_beat_ms("红昭愿"), 541)
        self.assertEqual(recommended_beat_ms("芒种"), 740)
        self.assertEqual(recommended_beat_ms("我本将心向明月"), 673)
        self.assertEqual(recommended_beat_ms("游山恋"), 706)
        self.assertEqual(recommended_beat_ms("半壶纱"), 706)
        self.assertEqual(recommended_beat_ms("青衣"), 870)
        self.assertEqual(recommended_beat_ms("星炬不熄"), 706)
        self.assertEqual(recommended_beat_ms("Running For Your Life（无所遁藏）"), 625)
        self.assertEqual(recommended_beat_ms("悠忽舞于梦中"), 395)
        self.assertEqual(recommended_beat_ms("Catch Me If You Can"), 438)
        self.assertEqual(recommended_beat_ms("Turning Around（余烬重燃）"), 500)
        self.assertEqual(recommended_beat_ms("「拉海洛」之心"), 500)
        self.assertEqual(recommended_beat_ms("致以无名的抗争者"), 849)
        self.assertEqual(recommended_beat_ms("那颗星梦见的春日"), 722)
        self.assertEqual(recommended_beat_ms("小小奇迹"), 343)
        self.assertEqual(recommended_beat_ms("远航星的告别"), 500)
        self.assertEqual(recommended_beat_ms("愿戴荣光坠入天渊"), 500)
        self.assertEqual(recommended_beat_ms("春日影"), 625)
        self.assertEqual(recommended_beat_ms("XY&Z"), 236)
        self.assertEqual(recommended_beat_ms("目标是宝可梦大师（TV版）"), 480)
        self.assertEqual(recommended_beat_ms("Butter-Fly"), 366)
        self.assertEqual(recommended_beat_ms("前前前世"), 333)
        self.assertEqual(recommended_beat_ms("打上花火"), 645)
        self.assertEqual(recommended_beat_ms("游京"), 645)
        self.assertEqual(recommended_beat_ms("奇迹再现"), 395)
        self.assertEqual(recommended_beat_ms("九九八十一"), 486)
        self.assertEqual(recommended_beat_ms("起风了"), 900)
        self.assertEqual(recommended_beat_ms("小重山"), 488)
        self.assertEqual(recommended_beat_ms("能伴此梦无"), 473)
        self.assertEqual(recommended_beat_ms("马步谣"), 833)
        self.assertEqual(recommended_beat_ms("虽万千人"), 508)
        self.assertEqual(recommended_beat_ms("是侠"), 556)
        self.assertEqual(recommended_beat_ms("天地惊白"), 600)
        self.assertEqual(recommended_beat_ms("恕我"), 533)
        self.assertEqual(recommended_beat_ms("春庭雪"), 800)
        self.assertEqual(recommended_beat_ms("鸳鸯戏"), 938)
        self.assertEqual(recommended_beat_ms("长安姑娘"), 750)
        self.assertEqual(recommended_beat_ms("传刀"), 429)
        self.assertEqual(recommended_beat_ms("封喉"), 533)
        self.assertEqual(recommended_beat_ms("忘此生"), 511)
        self.assertEqual(recommended_beat_ms("琵琶行"), 720)
        self.assertEqual(recommended_beat_ms("虞兮叹"), 706)
        self.assertEqual(recommended_beat_ms("迟暮"), 580)
        self.assertEqual(recommended_beat_ms("栖凰"), 750)
        self.assertEqual(recommended_beat_ms("囍"), 909)
        self.assertEqual(recommended_beat_ms("坐忘道"), 645)
        self.assertIsNone(recommended_beat_ms("用户导入曲目"))

    def test_parse_crlf_chord_and_rest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "song.txt"
            path.write_bytes(b"as 0.5\r\np 1")
            self.assertEqual(parse_song(path), [SongEvent("as", 0.5), SongEvent("p", 1.0)])

    def test_recorded_presses_create_rest_chord_and_intervals(self) -> None:
        events = recorded_presses_to_events(
            [(0.7, "a"), (0.73, "d"), (1.4, "a")],
            started_at=0.0,
            stopped_at=2.1,
            beat_ms=700,
        )
        self.assertEqual(
            events,
            [SongEvent("p", 1.0), SongEvent("ad", 1.0), SongEvent("a", 1.0)],
        )

    def test_recorded_repeat_is_not_mistaken_for_chord(self) -> None:
        events = recorded_presses_to_events(
            [(0.1, "a"), (0.13, "a")],
            started_at=0.1,
            stopped_at=0.23,
            beat_ms=800,
        )
        self.assertEqual(events, [SongEvent("a", 0.125), SongEvent("a", 0.125)])

    def test_recorded_txt_round_trips_through_parser(self) -> None:
        events = [SongEvent("p", 0.5), SongEvent("qg", 1.25)]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "recorded.txt"
            path.write_text(format_song_txt(events, beat_ms=700), encoding="utf-8")
            self.assertEqual(parse_song(path), events)

    def test_recording_without_piano_keys_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "没有录到21键"):
            recorded_presses_to_events(
                [(0.5, "p"), (0.7, "1")],
                started_at=0.0,
                stopped_at=1.0,
                beat_ms=700,
            )

    def test_invalid_key_reports_line(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.txt"
            path.write_text("k 1", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "第 1 行"):
                parse_song(path)

    def test_rest_marker_cannot_be_chord(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad-rest.txt"
            path.write_text("ap 1", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "休止符"):
                parse_song(path)

    def test_player_releases_every_key(self) -> None:
        backend = FakeBackend()
        states: list[str] = []
        engine = PlaybackEngine(backend, on_state=lambda state, _msg: states.append(state))
        engine.start([SongEvent("as", 0.25), SongEvent("p", 0.25)], beat_ms=50)
        deadline = time.monotonic() + 2
        while engine.running and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertFalse(backend.down)
        self.assertIn("finished", states)
        self.assertEqual(backend.actions, [("down", "a"), ("down", "s"), ("up", "a"), ("up", "s")])

    def test_player_can_start_from_an_event_and_keeps_original_progress(self) -> None:
        backend = FakeBackend()
        progress: list[tuple[int, int]] = []
        engine = PlaybackEngine(
            backend,
            on_progress=lambda index, total, _event: progress.append((index, total)),
        )
        events = [SongEvent("a", 0.1), SongEvent("s", 0.1), SongEvent("d", 0.1)]
        engine.start(events, beat_ms=50, start_index=1)
        deadline = time.monotonic() + 2
        while engine.running and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertEqual(progress, [(2, 3), (3, 3)])
        self.assertEqual(
            backend.actions,
            [("down", "s"), ("up", "s"), ("down", "d"), ("up", "d")],
        )
        self.assertFalse(backend.down)

    def test_player_rejects_out_of_range_start_event(self) -> None:
        engine = PlaybackEngine(FakeBackend())
        with self.assertRaisesRegex(ValueError, "播放起点"):
            engine.start([SongEvent("a", 1)], beat_ms=50, start_index=1)

    def test_windows_input_structure_has_native_size(self) -> None:
        expected = 40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28
        self.assertEqual(ctypes.sizeof(INPUT), expected)

    def test_bound_window_backend_posts_down_and_up(self) -> None:
        user32 = FakeUser32()
        backend = WindowMessageKeyBackend(1234, user32=user32)
        backend.key_down("a")
        backend.key_up("a")
        self.assertEqual(user32.messages[0][:3], (1234, 0x0100, ord("A")))
        self.assertEqual(user32.messages[1][:3], (1234, 0x0101, ord("A")))
        self.assertFalse(user32.messages[0][3] & 0xC0000000)
        self.assertEqual(user32.messages[1][3] & 0xC0000000, 0xC0000000)

    def test_bound_window_backend_rejects_closed_window(self) -> None:
        backend = WindowMessageKeyBackend(1234, user32=FakeUser32(valid=False))
        with self.assertRaisesRegex(RuntimeError, "失效"):
            backend.key_down("a")

    def test_access_denied_explains_elevation_mismatch(self) -> None:
        states: list[tuple[str, str]] = []
        engine = PlaybackEngine(
            AccessDeniedBackend(),
            on_state=lambda state, message: states.append((state, message)),
        )
        engine.start([SongEvent("a", 0.1)], beat_ms=50)
        deadline = time.monotonic() + 2
        while engine.running and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(any(state == "error" and "管理员身份" in message for state, message in states))

    def test_stop_releases_held_keys(self) -> None:
        backend = FakeBackend()
        states: list[str] = []
        engine = PlaybackEngine(backend, on_state=lambda state, _msg: states.append(state))
        engine.start([SongEvent("asd", 20)], beat_ms=50)
        time.sleep(0.05)
        engine.stop()
        time.sleep(0.05)
        self.assertFalse(backend.down)
        self.assertIn("stopped", states)


if __name__ == "__main__":
    unittest.main()
