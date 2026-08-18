from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Iterable

from player_core import KEY_ORDER, SongEvent

try:
    import mido
except ImportError:  # pragma: no cover - surfaced as a friendly runtime error
    mido = None


# The game keyboard is arranged from low to high as Z-row, A-row, Q-row.
LOW_TO_HIGH_KEYS = "zxcvbnmasdfghjqwertyu"
WHITE_PITCH_CLASSES = frozenset({0, 2, 4, 5, 7, 9, 11})
PLAYABLE_MIDI_NOTES = tuple(
    note for note in range(48, 84) if note % 12 in WHITE_PITCH_CLASSES
)
MIDI_TO_KEY = dict(zip(PLAYABLE_MIDI_NOTES, LOW_TO_HIGH_KEYS, strict=True))


@dataclass(frozen=True)
class MidiTrackInfo:
    index: int
    name: str
    instrument: str
    note_count: int
    min_note: int | None
    max_note: int | None
    percussion: bool
    score: float

    @property
    def range_text(self) -> str:
        if self.min_note is None or self.max_note is None:
            return "—"
        return f"{note_name(self.min_note)} – {note_name(self.max_note)}"


@dataclass(frozen=True)
class MidiAnalysis:
    path: Path
    ticks_per_beat: int
    duration_seconds: float
    tempo_bpm: float
    tracks: tuple[MidiTrackInfo, ...]
    recommended_tracks: tuple[int, ...]


@dataclass(frozen=True)
class ConversionStats:
    source_notes: int
    kept_notes: int
    dropped_notes: int
    approximated_notes: int
    out_of_range_notes: int
    chord_count: int


@dataclass(frozen=True)
class MidiConversionResult:
    events: tuple[SongEvent, ...]
    beat_ms: int
    transpose: int
    duration_seconds: float
    stats: ConversionStats


def _require_mido() -> None:
    if mido is None:
        raise RuntimeError("缺少 MIDI 依赖，请执行：python -m pip install mido")


def note_name(note: int) -> str:
    names = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
    return f"{names[note % 12]}{note // 12 - 1}"


def _absolute_messages(track) -> list[tuple[int, object]]:
    absolute = 0
    result: list[tuple[int, object]] = []
    for message in track:
        absolute += int(message.time)
        result.append((absolute, message))
    return result


def _tempo_events(mid) -> list[tuple[int, int]]:
    events: list[tuple[int, int]] = [(0, 500_000)]
    for track in mid.tracks:
        for tick, message in _absolute_messages(track):
            if message.type == "set_tempo":
                events.append((tick, int(message.tempo)))
    events.sort(key=lambda item: item[0])
    collapsed: list[tuple[int, int]] = []
    for tick, tempo in events:
        if collapsed and collapsed[-1][0] == tick:
            collapsed[-1] = (tick, tempo)
        else:
            collapsed.append((tick, tempo))
    return collapsed


def _tick_to_seconds(tick: int, tempo_events: list[tuple[int, int]], ticks_per_beat: int) -> float:
    seconds = 0.0
    previous_tick = 0
    tempo = 500_000
    for change_tick, new_tempo in tempo_events:
        if change_tick >= tick:
            break
        seconds += mido.tick2second(change_tick - previous_tick, ticks_per_beat, tempo)
        previous_tick = change_tick
        tempo = new_tempo
    seconds += mido.tick2second(tick - previous_tick, ticks_per_beat, tempo)
    return seconds


def _track_program_and_name(track, index: int) -> tuple[str, str]:
    name = f"音轨 {index + 1}"
    program = None
    for message in track:
        if message.type == "track_name" and str(message.name).strip():
            name = str(message.name).strip()
        elif message.type == "program_change" and program is None:
            program = int(message.program)
    if program is None:
        instrument = "未标注"
    else:
        try:
            instrument = mido.get_instrument_name(program)
        except (AttributeError, LookupError):
            instrument = f"GM {program}"
    return name, instrument


def analyze_midi(path: str | Path) -> MidiAnalysis:
    _require_mido()
    path = Path(path)
    mid = mido.MidiFile(path)
    tempo_events = _tempo_events(mid)
    tempos = [tempo for _tick, tempo in tempo_events]
    tempo_bpm = float(mido.tempo2bpm(int(median(tempos))))
    track_infos: list[MidiTrackInfo] = []
    end_tick = 0

    for index, track in enumerate(mid.tracks):
        absolute_messages = _absolute_messages(track)
        if absolute_messages:
            end_tick = max(end_tick, absolute_messages[-1][0])
        notes: list[int] = []
        percussion_notes = 0
        for _tick, message in absolute_messages:
            if message.type == "note_on" and int(message.velocity) > 0:
                notes.append(int(message.note))
                if getattr(message, "channel", -1) == 9:
                    percussion_notes += 1
        name, instrument = _track_program_and_name(track, index)
        percussion = bool(notes and percussion_notes >= len(notes) * 0.8)
        if notes:
            span = max(notes) - min(notes)
            center = median(notes)
            # Melody tracks tend to contain enough notes, avoid channel 10, sit
            # above the bass register, and have a manageable pitch span.
            score = min(len(notes), 600) - max(0, span - 36) * 2 + max(0, center - 48) * 0.8
            if percussion:
                score -= 1000
        else:
            score = -1000
        track_infos.append(
            MidiTrackInfo(
                index=index,
                name=name,
                instrument=instrument,
                note_count=len(notes),
                min_note=min(notes) if notes else None,
                max_note=max(notes) if notes else None,
                percussion=percussion,
                score=float(score),
            )
        )

    candidates = [item for item in track_infos if item.note_count and not item.percussion]
    candidates.sort(key=lambda item: item.score, reverse=True)
    recommended = tuple(item.index for item in candidates[:1])
    duration = _tick_to_seconds(end_tick, tempo_events, mid.ticks_per_beat)
    return MidiAnalysis(
        path=path,
        ticks_per_beat=mid.ticks_per_beat,
        duration_seconds=duration,
        tempo_bpm=tempo_bpm,
        tracks=tuple(track_infos),
        recommended_tracks=recommended,
    )


def _collect_notes(mid, track_indices: set[int]) -> tuple[list[tuple[int, int]], int]:
    notes: list[tuple[int, int]] = []
    end_tick = 0
    for index, track in enumerate(mid.tracks):
        if index not in track_indices:
            continue
        messages = _absolute_messages(track)
        if messages:
            end_tick = max(end_tick, messages[-1][0])
        for tick, message in messages:
            if (
                message.type == "note_on"
                and int(message.velocity) > 0
                and getattr(message, "channel", -1) != 9
            ):
                notes.append((tick, int(message.note)))
    notes.sort(key=lambda item: (item[0], item[1]))
    return notes, end_tick


def choose_best_transpose(notes: Iterable[int]) -> int:
    note_list = list(notes)
    if not note_list:
        return 0
    best: tuple[float, int] | None = None
    playable_set = set(PLAYABLE_MIDI_NOTES)
    for transpose in range(-24, 25):
        exact = 0
        approximation_distance = 0
        out_of_range = 0
        for note in note_list:
            shifted = note + transpose
            if shifted in playable_set:
                exact += 1
            else:
                nearest = min(PLAYABLE_MIDI_NOTES, key=lambda value: abs(value - shifted))
                approximation_distance += abs(nearest - shifted)
                if shifted < PLAYABLE_MIDI_NOTES[0] or shifted > PLAYABLE_MIDI_NOTES[-1]:
                    out_of_range += 1
        score = exact * 6 - approximation_distance * 1.5 - out_of_range * 8 - abs(transpose) * 0.05
        candidate = (score, -abs(transpose))
        if best is None or candidate > (best[0], -abs(best[1])):
            best = (score, transpose)
    return 0 if best is None else best[1]


def _quantize_beats(seconds: float, beat_ms: int, step: float) -> float:
    raw = max(0.0, seconds) * 1000.0 / beat_ms
    units = max(1, int(raw / step + 0.5))
    return round(units * step, 6)


def _append_limited(events: list[SongEvent], keys: str, beats: float) -> None:
    remaining = beats
    current = keys
    while remaining > 64:
        events.append(SongEvent(current, 64.0))
        remaining -= 64
        current = "p"
    if remaining > 0:
        events.append(SongEvent(current, round(remaining, 6)))


def convert_midi(
    path: str | Path,
    track_indices: Iterable[int],
    *,
    transpose: int | None = None,
    black_key_strategy: str = "nearest",
    beat_step: float = 0.125,
    chord_window_ms: int = 45,
) -> MidiConversionResult:
    _require_mido()
    if black_key_strategy not in {"nearest", "drop"}:
        raise ValueError("黑键策略必须是 nearest 或 drop。")
    if beat_step not in {0.25, 0.125, 0.0625}:
        raise ValueError("量化精度仅支持 1/4、1/8 或 1/16 拍。")
    selected = {int(index) for index in track_indices}
    if not selected:
        raise ValueError("请至少选择一个包含音符的 MIDI 音轨。")

    path = Path(path)
    mid = mido.MidiFile(path)
    notes, end_tick = _collect_notes(mid, selected)
    if not notes:
        raise ValueError("所选音轨没有可转换的非打击乐音符。")
    tempo_events = _tempo_events(mid)
    if transpose is None:
        transpose = choose_best_transpose(note for _tick, note in notes)
    if not -48 <= transpose <= 48:
        raise ValueError("移调范围必须在 -48 到 +48 半音之间。")

    end_seconds = _tick_to_seconds(end_tick, tempo_events, mid.ticks_per_beat)
    total_beats = end_tick / mid.ticks_per_beat if mid.ticks_per_beat else 0
    if total_beats > 0 and end_seconds > 0:
        beat_ms = int(round(end_seconds * 1000.0 / total_beats))
    else:
        beat_ms = 500
    beat_ms = min(5000, max(50, beat_ms))

    mapped: list[tuple[float, str]] = []
    approximated = 0
    dropped = 0
    out_of_range = 0
    playable_set = set(PLAYABLE_MIDI_NOTES)
    for tick, source_note in notes:
        shifted = source_note + transpose
        if shifted not in playable_set:
            if shifted < PLAYABLE_MIDI_NOTES[0] or shifted > PLAYABLE_MIDI_NOTES[-1]:
                out_of_range += 1
            if black_key_strategy == "drop":
                dropped += 1
                continue
            shifted = min(PLAYABLE_MIDI_NOTES, key=lambda value: abs(value - shifted))
            approximated += 1
        seconds = _tick_to_seconds(tick, tempo_events, mid.ticks_per_beat)
        mapped.append((seconds, MIDI_TO_KEY[shifted]))

    if not mapped:
        raise ValueError("按当前策略转换后没有留下任何可播放音符。")

    groups: list[tuple[float, list[str]]] = []
    chord_window = chord_window_ms / 1000.0
    for seconds, key in mapped:
        if groups and seconds - groups[-1][0] <= chord_window:
            if key not in groups[-1][1]:
                groups[-1][1].append(key)
        else:
            groups.append((seconds, [key]))

    events: list[SongEvent] = []
    if groups[0][0] > beat_ms / 2000.0:
        _append_limited(events, "p", _quantize_beats(groups[0][0], beat_ms, beat_step))
    for index, (seconds, keys) in enumerate(groups):
        following = groups[index + 1][0] if index + 1 < len(groups) else max(end_seconds, seconds + beat_ms / 1000.0)
        ordered = "".join(sorted(keys, key=KEY_ORDER.__getitem__))
        _append_limited(events, ordered, _quantize_beats(following - seconds, beat_ms, beat_step))

    return MidiConversionResult(
        events=tuple(events),
        beat_ms=beat_ms,
        transpose=transpose,
        duration_seconds=sum(event.beats for event in events) * beat_ms / 1000.0,
        stats=ConversionStats(
            source_notes=len(notes),
            kept_notes=len(notes) - dropped,
            dropped_notes=dropped,
            approximated_notes=approximated,
            out_of_range_notes=out_of_range,
            chord_count=sum(1 for event in events if event.keys != "p" and len(event.keys) > 1),
        ),
    )

