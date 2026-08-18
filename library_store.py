from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1


class LibraryStore:
    """Small, resilient JSON store for user-owned song metadata."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.data = self._load()

    def _blank(self) -> dict[str, Any]:
        return {"schema_version": SCHEMA_VERSION, "songs": {}, "history": []}

    def _load(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return self._blank()
        if not isinstance(payload, dict) or not isinstance(payload.get("songs", {}), dict):
            return self._blank()
        payload.setdefault("schema_version", SCHEMA_VERSION)
        payload.setdefault("songs", {})
        payload.setdefault("history", [])
        return payload

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def get(self, song_name: str) -> dict[str, Any]:
        raw = self.data["songs"].get(song_name, {})
        return deepcopy(raw) if isinstance(raw, dict) else {}

    def update(self, song_name: str, **changes: Any) -> dict[str, Any]:
        record = self.data["songs"].setdefault(song_name, {})
        record.update(changes)
        record["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.save()
        return deepcopy(record)

    def toggle_favorite(self, song_name: str) -> bool:
        favorite = not bool(self.get(song_name).get("favorite", False))
        self.update(song_name, favorite=favorite)
        return favorite

    def set_tags(self, song_name: str, tags: list[str]) -> list[str]:
        cleaned = sorted({tag.strip() for tag in tags if tag.strip()}, key=str.casefold)
        self.update(song_name, tags=cleaned)
        return cleaned

    def set_song_settings(self, song_name: str, **settings: Any) -> dict[str, Any]:
        record = self.get(song_name)
        merged = dict(record.get("settings", {}))
        merged.update(settings)
        self.update(song_name, settings=merged)
        return merged

    def record_play(self, song_name: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        record = self.get(song_name)
        self.update(
            song_name,
            play_count=int(record.get("play_count", 0)) + 1,
            last_played_at=now,
        )
        history = [item for item in self.data.get("history", []) if item.get("song") != song_name]
        history.insert(0, {"song": song_name, "played_at": now})
        self.data["history"] = history[:100]
        self.save()

    def recent(self, limit: int = 20) -> list[str]:
        return [
            str(item["song"])
            for item in self.data.get("history", [])[: max(0, limit)]
            if isinstance(item, dict) and item.get("song")
        ]

    def favorite_names(self) -> set[str]:
        return {
            name
            for name, metadata in self.data["songs"].items()
            if isinstance(metadata, dict) and metadata.get("favorite")
        }

