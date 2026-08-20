from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import librosa
import numpy as np


BASE = Path(__file__).resolve().parent
STAGING = BASE.parents[1] / "staging" / "batch_20260819_cn_pop"
ROWS = {-1: "zxcvbnm", 0: "asdfghj", 1: "qwertyu"}
MAJOR = (0, 2, 4, 5, 7, 9, 11)
PC_NAMES = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")

SONGS = {
    "xiaoxingyun": {
        "title": "小幸运", "artist": "田馥甄（社区镜像条目标注：田馥甄的小迷妹）",
        "netease_id": 3343236872, "source_kind": "community mirror; exact-title full-length recording",
    },
    "tonghua": {
        "title": "童话", "artist": "光良", "netease_id": 1954748375,
        "source_kind": "NetEase duplicate catalog entry credited to original artist",
    },
    "yekong": {
        "title": "夜空中最亮的星", "artist": "陈自言（逃跑计划原作的公开翻唱）",
        "netease_id": 2141396848, "source_kind": "full-length cover; original catalog stream unavailable without entitlement",
    },
    "pingfan": {
        "title": "平凡之路", "artist": "治愈房车（朴树原作的公开翻唱）",
        "netease_id": 2147354177, "source_kind": "full-length cover; original catalog stream unavailable without entitlement",
    },
    "zhuiguang": {
        "title": "追光者", "artist": "岑宁儿", "netease_id": 1392908905,
        "source_kind": "NetEase duplicate catalog entry credited to original artist",
    },
}


def normalized_tempo(value: float) -> float:
    while value < 65:
        value *= 2
    while value > 130:
        value /= 2
    return value


def append_limited(events: list[tuple[str, float]], key: str, beats: float) -> None:
    while beats > 0:
        if events and events[-1][0] == key and events[-1][1] < 64:
            take = min(beats, 64 - events[-1][1])
            events[-1] = (key, events[-1][1] + take)
        else:
            take = min(beats, 64)
            events.append((key, take))
        beats -= take


def process(slug: str) -> dict:
    config = SONGS[slug]
    audio_path = BASE / f"{slug}.mp3"
    y, sr = librosa.load(audio_path, sr=16000, mono=True)
    harmonic, _ = librosa.effects.hpss(y, margin=(1.0, 4.0))
    onset = librosa.onset.onset_strength(y=harmonic, sr=sr)
    tempo_raw, _ = librosa.beat.beat_track(onset_envelope=onset, sr=sr)
    tempo = normalized_tempo(float(np.asarray(tempo_raw).item()))
    beat_ms = int(round(60000 / tempo))

    hop = 512
    f0, voiced, probability = librosa.pyin(
        harmonic, fmin=librosa.note_to_hz("C3"), fmax=librosa.note_to_hz("C6"),
        sr=sr, frame_length=2048, hop_length=hop, fill_na=np.nan,
    )
    midi = librosa.hz_to_midi(f0)
    valid = voiced & np.isfinite(midi) & (np.nan_to_num(probability) >= 0.45)
    weights = np.zeros(12)
    for pitch, confidence in zip(midi[valid], probability[valid]):
        weights[int(round(float(pitch))) % 12] += float(confidence)
    scores = [sum(weights[(tonic + step) % 12] for step in MAJOR) for tonic in range(12)]
    tonic_pc = int(np.argmax(scores))
    median_pitch = float(np.nanmedian(midi[valid])) if np.any(valid) else 60.0
    tonic_midi = min((tonic_pc + 12 * octave for octave in range(3, 7)), key=lambda p: abs(p - median_pitch))

    step_beats = 0.25
    slot_seconds = beat_ms / 1000 * step_beats
    frame_times = np.arange(len(midi)) * hop / sr
    slots = max(1, math.ceil((len(y) / sr) / slot_seconds))
    values: list[str] = []
    chromatic_slots = 0
    for slot in range(slots):
        mask = valid & (frame_times >= slot * slot_seconds) & (frame_times < (slot + 1) * slot_seconds)
        if not np.any(mask):
            values.append("p")
            continue
        pitch = int(round(float(np.nanmedian(midi[mask]))))
        candidates = [
            (abs(pitch - (tonic_midi + 12 * octave + step)), degree, octave)
            for octave in range(-2, 3) for degree, step in enumerate(MAJOR)
        ]
        distance, degree, octave = min(candidates)
        chromatic_slots += int(distance > 0)
        octave = max(-1, min(1, octave))
        values.append(ROWS[octave][degree])

    events: list[tuple[str, float]] = []
    for key in values:
        append_limited(events, key, step_beats)
    header = [
        f"# 曲名：{config['title']}",
        f"# 推荐节拍：{beat_ms} ms/拍（音频估计 {tempo:.2f} BPM）",
        f"# 来源版本：{config['artist']}；网易云公开条目 {config['netease_id']}",
        f"# 制谱说明：完整音频经 HPSS + pYIN 提取主旋律，自动估计 {PC_NAMES[tonic_pc]} 大调/相对小调音集，四分之一拍量化为21键候选；必须游戏内试听复核。",
    ]
    text = "\n".join(header + [f"{key} {beats:g}" for key, beats in events]) + "\n"
    STAGING.mkdir(parents=True, exist_ok=True)
    txt_path = STAGING / f"{config['title']}.txt"
    txt_path.write_text(text, encoding="utf-8")
    report = {
        "title": config["title"], "artist_or_version": config["artist"],
        "source_url": f"https://music.163.com/#/song?id={config['netease_id']}",
        "source_kind": config["source_kind"], "source_audio": str(audio_path),
        "method": "HPSS + pYIN; best-fit diatonic pitch-class set; quarter-beat slot quantization",
        "audio_seconds": round(len(y) / sr, 3), "detected_bpm": round(tempo, 3),
        "recommended_beat_ms": beat_ms, "estimated_scale": f"{PC_NAMES[tonic_pc]} major / relative minor",
        "events": len(events), "rests": sum(key == "p" for key, _ in events),
        "beats": sum(beats for _, beats in events), "chromatic_slots_folded": chromatic_slots,
        "txt_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest().upper(),
        "status": "audio-derived candidate; requires in-game audition",
        "limitations": "Automatic monophonic extraction can follow accompaniment or harmony; cover sources are explicitly identified and are not represented as original masters.",
    }
    (BASE / f"{slug}.report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("slug", choices=SONGS)
    args = parser.parse_args()
    print(json.dumps(process(args.slug), ensure_ascii=False))
