from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from library_store import LibraryStore


class LibraryStoreTests(unittest.TestCase):
    def test_favorites_tags_settings_and_history_survive_reload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "library.json"
            store = LibraryStore(path)
            self.assertTrue(store.toggle_favorite("测试曲"))
            self.assertEqual(store.set_tags("测试曲", [" 动漫 ", "日语", "动漫"]), ["动漫", "日语"])
            store.set_song_settings("测试曲", beat_ms=720, transpose=-2)
            store.record_play("测试曲")
            store.record_play("另一首")
            store.record_play("测试曲")

            reloaded = LibraryStore(path)
            metadata = reloaded.get("测试曲")
            self.assertTrue(metadata["favorite"])
            self.assertEqual(metadata["tags"], ["动漫", "日语"])
            self.assertEqual(metadata["settings"]["beat_ms"], 720)
            self.assertEqual(metadata["play_count"], 2)
            self.assertEqual(reloaded.recent(2), ["测试曲", "另一首"])
            self.assertEqual(reloaded.favorite_names(), {"测试曲"})

    def test_invalid_json_recovers_to_empty_store(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "library.json"
            path.write_text("not-json", encoding="utf-8")
            store = LibraryStore(path)
            self.assertEqual(store.favorite_names(), set())
            self.assertEqual(store.recent(), [])


if __name__ == "__main__":
    unittest.main()

