from __future__ import annotations

from pathlib import Path
import unittest

from app import recommended_beat_ms
from player_core import parse_song


class FoxSpiritSongTests(unittest.TestCase):
    def test_new_songs_have_recommended_tempo_and_parse(self) -> None:
        songs_dir = Path(__file__).resolve().parents[1] / "builtin_songs"
        expected = {"若当来世": 500, "满庭芳": 811, "东流": 472, "此梦缘君": 750, "落空": 556, "孤勇者": 923, "玉盘": 526, "调查中": 732, "世界赠予我的": 968, "大鱼": 857, "热爱105°C的你": 438, "恋愛サーキュレーション（恋爱循环）": 500, "真英雄（姜姜女生版）": 600, "好汉歌": 619, "大香蕉": 480, "小苹果": 480, "阿呦阿呦（神奇阿呦主题曲）": 395, "再飞行": 759, "疯狂果宝": 750, "梦的光点": 480, "不问别离": 566, "拜无忧": 698, "不败的英雄（铠甲勇士刑天）": 500}
        for title, beat_ms in expected.items():
            with self.subTest(title=title):
                path = songs_dir / f"{title}.txt"
                text = path.read_text(encoding="utf-8")
                self.assertIn(f"# 推荐节拍：{beat_ms} ms/拍", text)
                self.assertEqual(recommended_beat_ms(title), beat_ms)
                self.assertGreater(len(parse_song(path)), 0)


if __name__ == "__main__":
    unittest.main()
