from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Protocol
import ctypes
from ctypes import wintypes
import threading
import time


PLAYABLE_KEYS = "qwertyuasdfghjzxcvbnm"
ALLOWED_KEYS = frozenset(PLAYABLE_KEYS + "p")
KEY_ORDER = {key: index for index, key in enumerate(PLAYABLE_KEYS)}


@dataclass(frozen=True)
class SongEvent:
    keys: str
    beats: float


def recorded_presses_to_events(
    presses: Iterable[tuple[float, str]],
    *,
    started_at: float,
    stopped_at: float,
    beat_ms: int,
    chord_window_ms: int = 55,
    beat_step: float = 0.125,
) -> list[SongEvent]:
    """Convert timestamped 21-key presses into the player's TXT event model."""
    if not 50 <= beat_ms <= 5000:
        raise ValueError("一拍时间必须在 50–5000 毫秒之间。")
    if stopped_at <= started_at:
        raise ValueError("录制结束时间必须晚于开始时间。")
    cleaned = sorted(
        (float(timestamp), key.lower())
        for timestamp, key in presses
        if key.lower() in PLAYABLE_KEYS and started_at <= float(timestamp) <= stopped_at
    )
    if not cleaned:
        raise ValueError("没有录到21键琴键，请先弹奏后再结束录制。")

    chord_window = chord_window_ms / 1000.0
    groups: list[tuple[float, list[str]]] = []
    for timestamp, key in cleaned:
        if (
            groups
            and timestamp - groups[-1][0] <= chord_window
            and key not in groups[-1][1]
        ):
            groups[-1][1].append(key)
        else:
            groups.append((timestamp, [key]))

    def quantize(seconds: float) -> float:
        raw_beats = max(0.0, seconds) * 1000.0 / beat_ms
        units = int(raw_beats / beat_step + 0.5)
        return max(beat_step, units * beat_step)

    events: list[SongEvent] = []

    def append_with_limit(keys: str, beats: float) -> None:
        remaining = beats
        current_keys = keys
        while remaining > 64:
            events.append(SongEvent(current_keys, 64.0))
            remaining -= 64
            current_keys = "p"
        if remaining > 0:
            events.append(SongEvent(current_keys, round(remaining, 6)))

    initial_seconds = groups[0][0] - started_at
    initial_units = int((initial_seconds * 1000.0 / beat_ms) / beat_step + 0.5)
    if initial_units > 0:
        append_with_limit("p", initial_units * beat_step)

    for index, (timestamp, keys) in enumerate(groups):
        next_timestamp = groups[index + 1][0] if index + 1 < len(groups) else stopped_at
        ordered_keys = "".join(sorted(keys, key=KEY_ORDER.__getitem__))
        append_with_limit(ordered_keys, quantize(next_timestamp - timestamp))
    return events


def format_song_txt(events: Iterable[SongEvent], *, beat_ms: int | None = None) -> str:
    """Serialize events as a beginner-readable, parser-compatible UTF-8 TXT."""
    lines = ["# 由21键曲谱播放器生成", "# 格式：按键 拍数；p 表示休止，同时按键写在一起"]
    if beat_ms is not None:
        lines.append(f"# 录制基准：{beat_ms} ms/拍")
    for event in events:
        beats = f"{event.beats:.6f}".rstrip("0").rstrip(".")
        lines.append(f"{event.keys} {beats}")
    return "\n".join(lines) + "\n"


def parse_song(path: str | Path) -> list[SongEvent]:
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = path.read_text(encoding="gb18030")
    events: list[SongEvent] = []
    for line_no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        parts = line.split()
        if len(parts) != 2:
            raise ValueError(f"第 {line_no} 行格式错误，应为：按键 拍数")
        keys = parts[0].lower()
        invalid = sorted(set(keys) - ALLOWED_KEYS)
        if invalid:
            raise ValueError(f"第 {line_no} 行包含不支持的按键：{''.join(invalid)}")
        # `p` is a logical rest marker, not a playable keyboard key.  It
        # must occupy the whole event; accepting e.g. `ap` would otherwise
        # send the physical P key and silently turn a malformed rest/chord
        # into a different performance.
        if "p" in keys and keys != "p":
            raise ValueError(f"第 {line_no} 行休止符 p 不能与其他按键组成和弦")
        if len(set(keys)) != len(keys):
            raise ValueError(f"第 {line_no} 行存在重复按键：{keys}")
        try:
            beats = float(parts[1])
        except ValueError as exc:
            raise ValueError(f"第 {line_no} 行拍数不是数字：{parts[1]}") from exc
        if not 0 < beats <= 64:
            raise ValueError(f"第 {line_no} 行拍数必须大于0且不超过64")
        events.append(SongEvent(keys, beats))
    if not events:
        raise ValueError("TXT 中没有可播放的音符事件。")
    return events


class KeyBackend(Protocol):
    def key_down(self, key: str) -> None: ...
    def key_up(self, key: str) -> None: ...


if hasattr(wintypes, "ULONG_PTR"):
    ULONG_PTR = wintypes.ULONG_PTR
else:
    ULONG_PTR = ctypes.c_size_t


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUTUNION(ctypes.Union):
    # Keep the largest native union member. Without MOUSEINPUT, INPUT is only
    # 32 bytes on 64-bit Windows instead of 40 and SendInput fails with error 87.
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", INPUTUNION)]


class WindowsKeyBackend:
    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_SCANCODE = 0x0008
    MAPVK_VK_TO_VSC = 0

    def __init__(self) -> None:
        if not hasattr(ctypes, "windll"):
            raise RuntimeError("键盘发送功能仅支持 Windows。")
        self.user32 = ctypes.windll.user32
        self.user32.SendInput.argtypes = (
            wintypes.UINT,
            ctypes.POINTER(INPUT),
            ctypes.c_int,
        )
        self.user32.SendInput.restype = wintypes.UINT

    def _send(self, key: str, key_up: bool) -> None:
        vk = ord(key.upper())
        scan = self.user32.MapVirtualKeyW(vk, self.MAPVK_VK_TO_VSC)
        flags = self.KEYEVENTF_SCANCODE | (self.KEYEVENTF_KEYUP if key_up else 0)
        item = INPUT(type=self.INPUT_KEYBOARD, ki=KEYBDINPUT(0, scan, flags, 0, 0))
        sent = self.user32.SendInput(1, ctypes.byref(item), ctypes.sizeof(INPUT))
        if sent != 1:
            raise ctypes.WinError()

    def key_down(self, key: str) -> None:
        self._send(key, False)

    def key_up(self, key: str) -> None:
        self._send(key, True)


class WindowMessageKeyBackend:
    """Send keyboard messages to one bound window without taking focus."""

    WM_KEYDOWN = 0x0100
    WM_KEYUP = 0x0101
    MAPVK_VK_TO_VSC = 0

    def __init__(self, hwnd: int = 0, user32=None) -> None:
        if user32 is None:
            if not hasattr(ctypes, "windll"):
                raise RuntimeError("后台窗口按键仅支持 Windows。")
            user32 = ctypes.windll.user32
            user32.PostMessageW.argtypes = (
                wintypes.HWND,
                wintypes.UINT,
                wintypes.WPARAM,
                wintypes.LPARAM,
            )
            user32.PostMessageW.restype = wintypes.BOOL
        self.user32 = user32
        self._hwnd = int(hwnd)

    @property
    def hwnd(self) -> int:
        return self._hwnd

    def bind(self, hwnd: int) -> None:
        self._hwnd = int(hwnd)

    def clear(self) -> None:
        self._hwnd = 0

    def is_bound(self) -> bool:
        return bool(self._hwnd and self.user32.IsWindow(self._hwnd))

    def _send(self, key: str, key_up: bool) -> None:
        if not self.is_bound():
            raise RuntimeError("绑定窗口已关闭或失效，请重新绑定。")
        vk = ord(key.upper())
        scan = self.user32.MapVirtualKeyW(vk, self.MAPVK_VK_TO_VSC)
        # Bits 30 and 31 distinguish a key release from the initial press.
        lparam = 1 | (scan << 16) | (0xC0000000 if key_up else 0)
        message = self.WM_KEYUP if key_up else self.WM_KEYDOWN
        if not self.user32.PostMessageW(self._hwnd, message, vk, lparam):
            raise ctypes.WinError()

    def key_down(self, key: str) -> None:
        self._send(key, False)

    def key_up(self, key: str) -> None:
        self._send(key, True)


class PlaybackEngine:
    """Threaded player preserving the original half-hold/half-rest timing."""

    def __init__(
        self,
        backend: KeyBackend,
        on_progress: Callable[[int, int, SongEvent], None] | None = None,
        on_state: Callable[[str, str], None] | None = None,
    ) -> None:
        self.backend = backend
        self.on_progress = on_progress or (lambda _i, _n, _e: None)
        self.on_state = on_state or (lambda _state, _message: None)
        self._stop = threading.Event()
        self._pause = threading.Event()
        self._thread: threading.Thread | None = None
        self._held: set[str] = set()
        self._lock = threading.RLock()

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    @property
    def paused(self) -> bool:
        return self._pause.is_set()

    def start(
        self,
        events: Iterable[SongEvent],
        beat_ms: int,
        countdown: int = 0,
        start_index: int = 0,
    ) -> None:
        if self.running:
            if self.paused:
                self.resume()
            return
        if not 50 <= beat_ms <= 5000:
            raise ValueError("一拍时间必须在 50–5000 毫秒之间。")
        event_list = list(events)
        if not event_list:
            raise ValueError("没有可播放事件。")
        if not 0 <= start_index < len(event_list):
            raise ValueError("播放起点超出歌曲范围。")
        self._stop.clear()
        self._pause.clear()
        self._thread = threading.Thread(
            target=self._run,
            args=(event_list, beat_ms / 1000.0, max(0, countdown), start_index),
            daemon=True,
            name="song-playback",
        )
        self._thread.start()

    def pause(self) -> None:
        if self.running and not self.paused:
            self._pause.set()
            self.release_all()
            self.on_state("paused", "已暂停")

    def resume(self) -> None:
        if self.running and self.paused:
            self._pause.clear()
            self.on_state("playing", "继续播放")

    def toggle_pause(self) -> None:
        self.resume() if self.paused else self.pause()

    def stop(self) -> None:
        self._stop.set()
        self._pause.clear()
        self.release_all()
        if self.running:
            self.on_state("stopping", "正在停止…")

    def release_all(self) -> None:
        with self._lock:
            for key in list(self._held):
                try:
                    self.backend.key_up(key)
                finally:
                    self._held.discard(key)

    def _press(self, keys: str) -> None:
        with self._lock:
            for key in keys:
                self.backend.key_down(key)
                self._held.add(key)

    def _release(self, keys: str) -> None:
        with self._lock:
            for key in keys:
                if key in self._held:
                    self.backend.key_up(key)
                    self._held.discard(key)

    def _wait(self, seconds: float, keys_to_restore: str = "") -> bool:
        remaining = max(0.0, seconds)
        last = time.monotonic()
        was_paused = False
        while remaining > 0:
            if self._stop.is_set():
                return False
            if self._pause.is_set():
                if not was_paused:
                    self.release_all()
                    was_paused = True
                time.sleep(0.015)
                last = time.monotonic()
                continue
            if was_paused and keys_to_restore:
                self._press(keys_to_restore)
                was_paused = False
                last = time.monotonic()
            now = time.monotonic()
            remaining -= now - last
            last = now
            time.sleep(min(0.01, max(0.001, remaining)))
        return not self._stop.is_set()

    def _run(
        self,
        events: list[SongEvent],
        beat_seconds: float,
        countdown: int,
        start_index: int,
    ) -> None:
        stopped_by_user = False
        try:
            for value in range(countdown, 0, -1):
                self.on_state("countdown", f"{value} 秒后开始")
                if not self._wait(1.0):
                    return
            self.on_state("playing", "正在播放")
            total = len(events)
            for index, event in enumerate(events[start_index:], start_index + 1):
                if self._stop.is_set():
                    return
                self.on_progress(index, total, event)
                # `p` is the TXT rest marker, not the physical P key.
                if event.keys == "p":
                    if not self._wait(beat_seconds * event.beats):
                        return
                    continue
                half = beat_seconds * event.beats / 2.0
                self._press(event.keys)
                if not self._wait(half, event.keys):
                    return
                self._release(event.keys)
                if not self._wait(half):
                    return
            self.on_state("finished", "播放完成")
        except Exception as exc:  # noqa: BLE001 - report device errors to the UI
            if getattr(exc, "winerror", None) == 5:
                message = "目标窗口权限更高，Windows 已阻止后台按键。请以管理员身份运行播放器后重新绑定。"
            else:
                message = str(exc)
            self.on_state("error", f"播放错误：{message}")
        finally:
            stopped_by_user = self._stop.is_set()
            self.release_all()
            self._pause.clear()
            self._stop.clear()
            if stopped_by_user:
                self.on_state("stopped", "已停止")
