from __future__ import annotations

import threading
import time

from midi_importer import LOW_TO_HIGH_KEYS, PLAYABLE_MIDI_NOTES
from player_core import SongEvent

try:
    import winsound
except ImportError:  # pragma: no cover
    winsound = None


KEY_TO_MIDI = dict(zip(LOW_TO_HIGH_KEYS, PLAYABLE_MIDI_NOTES, strict=True))


class LocalPreview:
    """Lightweight monophonic preview that never sends keys to the game."""

    def __init__(self) -> None:
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def stop(self) -> None:
        self._stop.set()

    def start(self, events: list[SongEvent], beat_ms: int, *, max_seconds: float = 30.0) -> None:
        if winsound is None:
            raise RuntimeError("本地试听仅支持 Windows。")
        self.stop()
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            args=(list(events), beat_ms, max_seconds),
            daemon=True,
            name="local-song-preview",
        )
        self._thread.start()

    def _run(self, events: list[SongEvent], beat_ms: int, max_seconds: float) -> None:
        deadline = time.monotonic() + max_seconds
        for event in events:
            if self._stop.is_set() or time.monotonic() >= deadline:
                break
            duration_ms = max(20, int(event.beats * beat_ms))
            duration_ms = min(duration_ms, max(20, int((deadline - time.monotonic()) * 1000)))
            if event.keys == "p":
                self._stop.wait(duration_ms / 1000.0)
                continue
            # Chords are reduced to the highest note for this deliberately
            # lightweight preview; game playback still preserves every key.
            key = max(event.keys, key=lambda item: KEY_TO_MIDI[item])
            midi_note = KEY_TO_MIDI[key]
            frequency = int(round(440.0 * (2.0 ** ((midi_note - 69) / 12.0))))
            try:
                winsound.Beep(max(37, min(32767, frequency)), duration_ms)
            except RuntimeError:
                break

