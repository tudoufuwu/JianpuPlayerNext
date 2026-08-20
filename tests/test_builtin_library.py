from __future__ import annotations

from pathlib import Path
import unittest

from player_core import parse_song


class BuiltinLibraryTests(unittest.TestCase):
    def test_every_builtin_song_parses_and_has_events(self) -> None:
        songs_dir = Path(__file__).resolve().parents[1] / "builtin_songs"
        paths = sorted(songs_dir.glob("*.txt"))

        self.assertEqual(len(paths), 240)
        for path in paths:
            with self.subTest(song=path.name):
                self.assertGreater(len(parse_song(path)), 0)


if __name__ == "__main__":
    unittest.main()
