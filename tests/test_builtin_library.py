from __future__ import annotations

from pathlib import Path
import unittest

from player_core import parse_song, parse_song_program


class BuiltinLibraryTests(unittest.TestCase):
    def test_every_builtin_song_parses_and_has_events(self) -> None:
        songs_dir = Path(__file__).resolve().parents[1] / "builtin_songs"
        paths = sorted(songs_dir.glob("*.txt"))

        self.assertEqual(len(paths), 296)
        for path in paths:
            with self.subTest(song=path.name):
                program = parse_song_program(path)
                self.assertGreater(len(program.main_events), 0)
                if not program.is_multi:
                    self.assertEqual(program.main_events, parse_song(path))


if __name__ == "__main__":
    unittest.main()
