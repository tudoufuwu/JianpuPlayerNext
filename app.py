from __future__ import annotations

from pathlib import Path
import ctypes
from ctypes import wintypes
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from library_store import LibraryStore
from midi_importer import MidiAnalysis, MidiConversionResult, analyze_midi, convert_midi
from player_core import (
    PLAYABLE_KEYS,
    PlaybackEngine,
    SongEvent,
    WindowMessageKeyBackend,
    WindowsKeyBackend,
    format_song_txt,
    parse_song,
    recorded_presses_to_events,
)
from preview_audio import LocalPreview


APP_NAME = "21键弹琴自动化"
APP_VERSION = "1.0.0-beta.45"
HOTKEYS = [f"F{i}" for i in range(1, 13)]
BUILTIN_LIBRARY_VERSION = 183
RECOMMENDED_BEAT_MS = {
    "嗵嗵": 493,
    "Daisy Crown（Japanese Ver.）": 757,
    "发如雪": 1083,
    "自无垠处归航之星": 874,
    "不老梦": 800,
    "牵丝戏": 800,
    "童话镇": 857,
    "群青": 441,
    "锦鲤抄": 800,
    "念张师DJ版": 441,
    "新宝岛": 372,
    "超级马力欧地面主题": 275,
    "小幸运": 768,
    "童话": 896,
    "平凡之路": 544,
    "追光者": 714,
    "最后的旅行": 870,
    "莫问归期": 980,
    "你若三冬": 614,
    "天亮之前说再见": 769,
    "探窗": 912,
    "盗将行": 625,
    "是风动": 857,
    "鸟之诗": 487,
    "年轮": 418,
    "霜雪千年": 418,
    "寄明月": 418,
    "风筝误": 807,
    "天下": 745,
    "有点甜": 605,
    "明月天涯": 484,
    "海阔天空": 807,
    "望故乡": 921,
    "离别开出花": 549,
    "长生诀": 826,
    "十年人间": 619,
    "红昭愿": 541,
    "芒种": 740,
    "我本将心向明月": 673,
    "游山恋": 706,
    "半壶纱": 706,
    "青衣": 870,
    "青衣（草帽酱原版）": 441,
    "落了白": 418,
    "难却": 418,
    "星炬不熄": 706,
    "Running For Your Life（无所遁藏）": 625,
    "悠忽舞于梦中": 395,
    "Catch Me If You Can": 438,
    "Turning Around（余烬重燃）": 500,
    "「拉海洛」之心": 500,
    "致以无名的抗争者": 849,
    "那颗星梦见的春日": 722,
    "小小奇迹": 343,
    "酣梦于彼岸深红": 1020,
    "Saving Light": 1112,
    "逐光筑昼": 432,
    "繁星、新生，与你（Astrum Unicum）": 1049,
    "定玄": 985,
    "木兰行": 698,
    "清醒梦": 544,
    "本草纲目": 1150,
    "兰亭序": 1004,
    "双截棍": 565,
    "烟花易冷": 715,
    "夜曲": 328,
    "以父之名": 1555,
    "告白气球": 790,
    "稻香": 978,
    "七里香": 874,
    "青花瓷": 1176,
    "晴天": 882,
    "Against the Tide（逆潮）": 833,
    "远航星的告别": 500,
    "愿戴荣光坠入天渊": 500,
    "春日影": 625,
    "循迹": 608,
    "惊鹊": 667,
    "辞九门回忆": 857,
    "莫愁乡": 909,
    "百战成诗": 536,
    "逐光之路": 811,
    "纸飞机": 857,
    "Lemon": 430,
    "千本桜（千本樱）": 390,
    "紅蓮華": 444,
    "XY&Z": 236,
    "目标是宝可梦大师（TV版）": 480,
    "Butter-Fly": 366,
    "前前前世": 333,
    "打上花火": 645,
    "游京": 645,
    "半山腰": 441,
    "奇迹再现": 395,
    "九九八十一": 486,
    "极乐净土": 458,
    "大东北我的家乡": 469,
    "起风了": 900,
    "我还有点小糊涂": 625,
    "别看我只是一只羊": 625,
    "Only My Railgun": 444,
    "不染": 800,
    "千盏灯": 441,
    "心外江湖": 618,
    "暮色回响": 882,
    "有人": 1000,
    "此去半生": 968,
    "燕无歇": 625,
    "祖籁": 488,
    "虽万千人": 508,
    "马步谣": 833,
    "是侠": 556,
    "天地惊白": 600,
    "恕我": 533,
    "肘我": 556,
    "归零": 534,
    "偶像": 449,
    "朋友的酒": 465,
    "咏春": 409,
    "二泉映月": 488,
    "简单爱": 629,
    "龙卷风": 463,
    "安静": 428,
    "搁浅": 470,
    "彩虹": 427,
    "珊瑚海": 537,
    "一路向北": 514,
    "花海": 464,
    "爱在西元前": 510,
    "东风破": 476,
    "蒲公英的约定": 474,
    "听妈妈的话": 468,
    "给我一首歌的时间": 513,
    "说好的幸福呢": 509,
    "霍元甲": 542,
    "等你下课": 412,
    "说好不哭": 413,
    "Mojito": 513,
    "最伟大的作品": 419,
    "春庭雪": 800,
    "鸳鸯戏": 938,
    "长安姑娘": 750,
    "将夜·未明": 464,
    "小重山": 488,
    "江湖歌": 488,
    "虚空中的瓶子": 533,
    "能伴此梦无": 473,
    "传刀": 429,
    "封喉": 533,
    "忘此生": 511,
    "琵琶行": 720,
    "虞兮叹": 706,
    "迟暮": 580,
    "栖凰": 750,
    "不谓侠": 1034,
    "赤伶": 811,
    "关山酒": 714,
    "出山": 583,
    "下山": 732,
    "精卫": 545,
    "乘云归": 1071,
    "须弥": 511,
    "十洲记": 534,
    "硬骨": 418,
    "赴红尘": 789,
    "潮来天地": 464,
    "赐我": 500,
    "囍": 909,
    "坐忘道": 645,
    "免我蹉跎苦": 800,
    "南山雪": 674,
    "风催雨": 698,
    "肯定": 534,
    "天下局": 511,
    "梦回还": 700,
    "我用什么把你留住": 488,
    "纵此生": 673,
    "唐人恋曲": 534,
    "若当来世": 500,
    "满庭芳": 811,
    "东流": 472,
    "此梦缘君": 750,
    "落空": 556,
    "孤勇者": 923,
    "玉盘": 526,
    "调查中": 732,
    "世界赠予我的": 968,
    "大鱼": 857,
    "热爱105°C的你": 438,
    "恋愛サーキュレーション（恋爱循环）": 500,
    "真英雄（姜姜女生版）": 600,
    "好汉歌": 619,
    "大香蕉": 480,
    "小苹果": 480,
    "阿呦阿呦（神奇阿呦主题曲）": 395,
    "再飞行": 759,
    "疯狂果宝": 750,
    "梦的光点": 480,
    "不问别离": 566,
    "拜无忧": 698,
    "不败的英雄（铠甲勇士刑天）": 500,
    "記憶（缘之空）": 627,
    "浪人琵琶（胡66）": 650,
    "云与海（YueYue）": 1000,
    "生僻字": 500,
    "左手指月": 650,
    "无羁": 750,
    "归去来兮": 857,
    "轨迹": 500,
    "江南": 500,
    "枫": 500,
    "修炼爱情": 500,
    "可惜没如果": 500,
    "Megalovania": 500,
    "红豆": 500,
    "匆匆那年": 500,
    "素颜": 500,
    "一直很安静": 500,
    "传奇": 500,
    "千年之恋": 827,
}


def recommended_beat_ms(song_name: str) -> int | None:
    """Return the calibrated playback speed for a built-in song, if known."""
    return RECOMMENDED_BEAT_MS.get(song_name)


def filter_song_names(names: list[str], query: str) -> list[str]:
    """Return song names containing the trimmed, case-insensitive query."""
    needle = query.strip().casefold()
    if not needle:
        return names
    return [name for name in names if needle in name.casefold()]


def resource_path(relative: str) -> Path:
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return root / relative


def data_root() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    return base / "JianpuPlayerNext"


class HotkeyPoller:
    VK = {f"F{i}": 0x6F + i for i in range(1, 13)}

    def __init__(self, getter, callback) -> None:
        self.getter = getter
        self.callback = callback
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True, name="global-hotkeys")
        self._previous: dict[str, bool] = {}

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        user32 = __import__("ctypes").windll.user32
        while not self._stop.is_set():
            bindings = self.getter()
            for action, name in bindings.items():
                down = bool(user32.GetAsyncKeyState(self.VK.get(name, 0)) & 0x8000)
                key = f"{action}:{name}"
                if down and not self._previous.get(key, False):
                    self.callback(action)
                self._previous[key] = down
            time.sleep(0.035)


class PerformanceRecorder:
    """Opt-in global polling limited to the 21 piano keys and two F-key controls."""

    VK = {f"F{i}": 0x6F + i for i in range(1, 13)} | {
        key.upper(): ord(key.upper()) for key in PLAYABLE_KEYS
    }

    def __init__(self, config_getter, callback) -> None:
        self.config_getter = config_getter
        self.callback = callback
        self._stop = threading.Event()
        self._lock = threading.RLock()
        self._thread = threading.Thread(target=self._run, daemon=True, name="performance-recorder")
        self._recording = False
        self._started_at = 0.0
        self._presses: list[tuple[float, str]] = []
        self._previous: dict[str, bool] = {}

    @property
    def recording(self) -> bool:
        with self._lock:
            return self._recording

    def start(self) -> None:
        self._thread.start()

    def close(self) -> None:
        self._stop.set()

    def begin(self) -> bool:
        config = self.config_getter()
        if not config["enabled"]:
            return False
        with self._lock:
            if self._recording:
                return False
            self._recording = True
            self._started_at = time.monotonic()
            self._presses = []
        self.callback("started", {"started_at": self._started_at})
        return True

    def finish(self) -> bool:
        with self._lock:
            if not self._recording:
                return False
            stopped_at = time.monotonic()
            payload = {
                "started_at": self._started_at,
                "stopped_at": stopped_at,
                "presses": list(self._presses),
            }
            self._recording = False
            self._presses = []
        self.callback("stopped", payload)
        return True

    def cancel(self) -> None:
        with self._lock:
            was_recording = self._recording
            self._recording = False
            self._presses = []
        if was_recording:
            self.callback("cancelled", {})

    def _run(self) -> None:
        user32 = ctypes.windll.user32
        while not self._stop.is_set():
            config = self.config_getter()
            if not config["enabled"]:
                self._previous.clear()
                time.sleep(0.035)
                continue

            start_name = config["start_key"]
            stop_name = config["stop_key"]
            start_down = bool(user32.GetAsyncKeyState(self.VK[start_name]) & 0x8000)
            stop_down = bool(user32.GetAsyncKeyState(self.VK[stop_name]) & 0x8000)
            if start_down and not self._previous.get("start", False):
                self.begin()
            if stop_down and not self._previous.get("stop", False):
                self.finish()
            self._previous["start"] = start_down
            self._previous["stop"] = stop_down

            now = time.monotonic()
            count = None
            for key in PLAYABLE_KEYS:
                down = bool(user32.GetAsyncKeyState(self.VK[key.upper()]) & 0x8000)
                marker = f"note:{key}"
                if down and not self._previous.get(marker, False):
                    with self._lock:
                        if self._recording:
                            self._presses.append((now, key))
                            count = len(self._presses)
                self._previous[marker] = down
            if count is not None:
                self.callback("count", {"count": count})
            time.sleep(0.02)


class JianpuPlayerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self._set_app_icon()
        self.geometry("1120x740")
        self.minsize(940, 660)
        self.configure(background="#eef1f2")
        self.data_dir = data_root()
        self.songs_dir = self.data_dir / "songs"
        self.config_path = self.data_dir / "config.json"
        self.library_store = LibraryStore(self.data_dir / "library.json")
        self.songs_dir.mkdir(parents=True, exist_ok=True)
        self._install_builtin_songs()
        self.config_data = self._load_config()
        self.events: list[SongEvent] = []
        self.song_paths: dict[str, Path] = {}
        self._hotkey_lock = threading.Lock()
        self._record_lock = threading.Lock()

        self.song_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.library_filter_var = tk.StringVar(value="全部")
        self.favorite_button_var = tk.StringVar(value="☆")
        self.tags_var = tk.StringVar()
        self.song_meta_var = tk.StringVar(value="尚未选择歌曲")
        self.beat_var = tk.StringVar(value=str(self.config_data.get("beat_ms", 700)))
        self.countdown_var = tk.StringVar(value=str(self.config_data.get("countdown", 2)))
        self.sequence_enabled_var = tk.BooleanVar(value=self.config_data.get("sequence_enabled", False))
        self.repeat_one_var = tk.BooleanVar(value=self.config_data.get("repeat_one", False))
        self.sequence_delay_var = tk.StringVar(value=str(self.config_data.get("sequence_delay", 0)))
        self.sequence_status_var = tk.StringVar(value="队列为空")
        self.start_key_var = tk.StringVar(value=self.config_data.get("start_key", "F8"))
        self.stop_key_var = tk.StringVar(value=self.config_data.get("stop_key", "F9"))
        self.pause_key_var = tk.StringVar(value=self.config_data.get("pause_key", "F10"))
        self.show_guide_var = tk.BooleanVar(value=False)
        self.record_enabled_var = tk.BooleanVar(value=False)
        self.record_start_key_var = tk.StringVar(value=self.config_data.get("record_start_key", "F6"))
        self.record_stop_key_var = tk.StringVar(value=self.config_data.get("record_stop_key", "F7"))
        self.record_status_var = tk.StringVar(value="录谱功能未开启")
        self.guard_var = tk.BooleanVar(value=self.config_data.get("guard_enabled", False))
        self.window_title_var = tk.StringVar(value=self.config_data.get("window_title", "一梦江湖"))
        self.background_window_var = tk.BooleanVar(value=self.config_data.get("background_window", False))
        self.window_choice_var = tk.StringVar()
        self.bound_window_var = tk.StringVar(value="未绑定窗口")
        self.window_choices: dict[str, int] = {}
        self._hotkey_values = {
            "start": self.start_key_var.get(),
            "stop": self.stop_key_var.get(),
            "pause": self.pause_key_var.get(),
        }
        self._record_config = {
            "enabled": False,
            "start_key": self.record_start_key_var.get(),
            "stop_key": self.record_stop_key_var.get(),
        }
        self.status_var = tk.StringVar(value="请选择歌曲。")
        self.detail_var = tk.StringVar(value="")
        self.song_count_var = tk.StringVar(value="0 首歌曲")
        self.search_count_var = tk.StringVar(value="0 首")
        self.current_song_var = tk.StringVar(value="尚未选择歌曲")
        self.progress_text_var = tk.StringVar(value="0%")
        self.progress_var = tk.DoubleVar(value=0)
        self.midi_path_var = tk.StringVar()
        self.midi_status_var = tk.StringVar(value="选择一个 MIDI，系统会分析音轨并推荐主旋律。")
        self.midi_strategy_var = tk.StringVar(value="最近白键")
        self.midi_transpose_var = tk.StringVar(value="自动")
        self.midi_quantize_var = tk.StringVar(value="1/8 拍")
        self.midi_name_var = tk.StringVar()
        self.midi_summary_var = tk.StringVar(value="尚未分析")
        self.keyboard_labels: dict[str, ttk.Label] = {}
        self.sequence_queue: list[str] = []
        self._sequence_after_id: str | None = None
        self._playback_start_index = 0
        self._has_seek_position = False
        self._seeking = False
        self._resume_after_seek = False
        self._seek_target_index = 0
        self.midi_analysis: MidiAnalysis | None = None
        self.midi_result: MidiConversionResult | None = None
        self.preview = LocalPreview()

        self.foreground_backend = WindowsKeyBackend()
        self.window_backend = WindowMessageKeyBackend()
        self.engine = PlaybackEngine(
            self.window_backend if self.background_window_var.get() else self.foreground_backend,
            on_progress=lambda i, n, e: self.after(0, self._on_progress, i, n, e),
            on_state=lambda state, msg: self.after(0, self._on_state, state, msg),
        )
        self._build_ui()
        self.refresh_windows(auto_bind_title=self.config_data.get("bound_window_title"))
        self.refresh_songs(select=self.config_data.get("last_song"))
        self.hotkeys = HotkeyPoller(self._hotkey_bindings, lambda action: self.after(0, self._hotkey_action, action))
        self.hotkeys.start()
        self.recorder = PerformanceRecorder(
            self._recording_config,
            lambda event, payload: self.after(0, self._on_recorder_event, event, payload),
        )
        self.recorder.start()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _set_app_icon(self) -> None:
        icon_path = resource_path("assets/app_icon.png")
        if not icon_path.exists():
            return
        try:
            self._app_icon = tk.PhotoImage(file=str(icon_path))
            self.iconphoto(True, self._app_icon)
        except tk.TclError:
            pass

    def _install_builtin_songs(self) -> None:
        source = resource_path("builtin_songs")
        if not source.exists():
            return
        version_path = self.data_dir / "builtin_library_version.txt"
        try:
            installed_version = int(version_path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            installed_version = 0
        upgrade = installed_version < BUILTIN_LIBRARY_VERSION
        for item in source.glob("*.txt"):
            destination = self.songs_dir / item.name
            if upgrade or not destination.exists():
                shutil.copy2(item, destination)
        if upgrade:
            version_path.write_text(str(BUILTIN_LIBRARY_VERSION), encoding="utf-8")

    def _load_config(self) -> dict:
        try:
            return json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def save_config(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "beat_ms": int(float(self.beat_var.get() or 700)),
            "countdown": int(float(self.countdown_var.get() or 0)),
            "sequence_enabled": self.sequence_enabled_var.get(),
            "repeat_one": self.repeat_one_var.get(),
            "sequence_delay": int(float(self.sequence_delay_var.get() or 0)),
            "start_key": self.start_key_var.get(),
            "stop_key": self.stop_key_var.get(),
            "pause_key": self.pause_key_var.get(),
            "record_start_key": self.record_start_key_var.get(),
            "record_stop_key": self.record_stop_key_var.get(),
            "guard_enabled": self.guard_var.get(),
            "window_title": self.window_title_var.get().strip(),
            "background_window": self.background_window_var.get(),
            "bound_window_title": self._bound_window_title(),
            "last_song": self.song_var.get(),
        }
        self.config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _build_ui_legacy(self) -> None:
        self._setup_styles()
        outer = ttk.Frame(self, padding=(20, 16, 20, 18), style="App.TFrame")
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(1, weight=1)
        outer.rowconfigure(1, weight=1)

        header = ttk.Frame(outer, style="App.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text=APP_NAME, style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="本地曲库 · 21 键自动演奏", style="Meta.TLabel").grid(row=1, column=0, sticky="w", pady=(3, 0))
        ttk.Label(header, textvariable=self.song_count_var, style="Count.TLabel").grid(row=0, column=1, rowspan=2, sticky="e")

        library = ttk.Frame(outer, padding=14, style="Panel.TFrame")
        library.grid(row=1, column=0, sticky="nsew", padx=(0, 14))
        library.rowconfigure(2, weight=1)
        library.columnconfigure(0, weight=1)
        library_header = ttk.Frame(library, style="Panel.TFrame")
        library_header.grid(row=0, column=0, sticky="ew")
        library_header.columnconfigure(0, weight=1)
        ttk.Label(library_header, text="曲库", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(library_header, textvariable=self.search_count_var, style="MetaPanel.TLabel").grid(row=0, column=1, sticky="e")
        search_row = ttk.Frame(library, style="Panel.TFrame")
        search_row.grid(row=1, column=0, sticky="ew", pady=(10, 10))
        search_row.columnconfigure(0, weight=1)
        search_entry = ttk.Entry(search_row, textvariable=self.search_var, width=25)
        search_entry.grid(row=0, column=0, sticky="ew")
        search_entry.bind("<Return>", self._select_first_search_result)
        ttk.Button(search_row, text="清空", command=lambda: self.search_var.set(""), style="Quiet.TButton").grid(row=0, column=1, padx=(6, 0))
        list_frame = ttk.Frame(library, style="Panel.TFrame")
        list_frame.grid(row=2, column=0, sticky="nsew")
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        self.song_list = tk.Listbox(
            list_frame,
            width=27,
            activestyle="none",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#d8dde3",
            highlightcolor="#176b5b",
            background="#ffffff",
            foreground="#20252b",
            selectbackground="#dcefe9",
            selectforeground="#124b40",
            font=("Microsoft YaHei UI", 10),
            exportselection=False,
        )
        self.song_list.grid(row=0, column=0, sticky="nsew")
        song_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.song_list.yview)
        song_scrollbar.grid(row=0, column=1, sticky="ns")
        self.song_list.configure(yscrollcommand=song_scrollbar.set)
        self.song_list.bind("<<ListboxSelect>>", self._on_song_list_selected)
        library_actions = ttk.Frame(library, style="Panel.TFrame")
        library_actions.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(library_actions, text="导入 TXT", command=self.import_songs).pack(side="left")
        ttk.Button(library_actions, text="打开文件夹", command=self.open_song_folder, style="Quiet.TButton").pack(side="right")
        self.search_var.trace_add("write", lambda *_args: self._apply_song_filter())

        workspace = ttk.Frame(outer, style="App.TFrame")
        workspace.grid(row=1, column=1, sticky="nsew")
        workspace.columnconfigure(0, weight=1)
        workspace.rowconfigure(3, weight=1)

        now_playing = ttk.Frame(workspace, padding=(18, 16), style="Panel.TFrame")
        now_playing.grid(row=0, column=0, sticky="ew")
        now_playing.columnconfigure(0, weight=1)
        ttk.Label(now_playing, text="当前歌曲", style="Eyebrow.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(now_playing, textvariable=self.current_song_var, style="SongTitle.TLabel").grid(row=1, column=0, sticky="w", pady=(3, 0))
        ttk.Label(now_playing, textvariable=self.detail_var, style="Detail.TLabel", wraplength=330).grid(row=2, column=0, sticky="w", pady=(5, 0))
        keyboard = ttk.Frame(now_playing, style="Panel.TFrame")
        keyboard.grid(row=0, column=1, rowspan=3, sticky="e", padx=(14, 0))
        ttk.Label(keyboard, text="实时键位", style="Eyebrow.TLabel").grid(row=0, column=0, columnspan=7, sticky="e", pady=(0, 5))
        for row, keys in enumerate(("qwertyu", "asdfghj", "zxcvbnm"), start=1):
            for column, key in enumerate(keys):
                label = ttk.Label(keyboard, text=key.upper(), style="Key.TLabel", anchor="center", width=2)
                label.grid(row=row, column=column, padx=1, pady=1)
                self.keyboard_labels[key] = label

        status = ttk.Frame(workspace, padding=(18, 14), style="Dark.TFrame")
        status.grid(row=1, column=0, sticky="ew", pady=(12, 12))
        status.columnconfigure(0, weight=1)
        self.status_label = ttk.Label(status, textvariable=self.status_var, style="Status.TLabel")
        self.status_label.grid(row=0, column=0, sticky="w")
        self.current_var = tk.StringVar(value="尚未播放")
        ttk.Label(status, textvariable=self.current_var, style="StatusMeta.TLabel").grid(row=0, column=1, sticky="e", padx=(12, 8))
        ttk.Label(status, textvariable=self.progress_text_var, style="Percent.TLabel").grid(row=0, column=2, sticky="e")
        self.progress = ttk.Scale(
            status,
            variable=self.progress_var,
            from_=0,
            to=100,
            orient="horizontal",
            command=self._on_seek_changed,
            style="Accent.Horizontal.TScale",
        )
        self.progress.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(11, 0))
        self.progress.bind("<ButtonPress-1>", self._on_seek_press)
        self.progress.bind("<ButtonRelease-1>", self._on_seek_release)

        binding_bar = ttk.Frame(workspace, padding=(12, 9), style="Panel.TFrame")
        binding_bar.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        binding_bar.columnconfigure(1, weight=1)
        ttk.Label(binding_bar, text="目标窗口", style="Subsection.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.window_combo = ttk.Combobox(binding_bar, textvariable=self.window_choice_var, state="readonly", width=38)
        self.window_combo.grid(row=0, column=1, sticky="ew")
        ttk.Button(binding_bar, text="刷新", command=self.refresh_windows, style="Inline.TButton").grid(row=0, column=2, padx=(6, 0))
        ttk.Button(binding_bar, text="绑定", command=self.bind_selected_window, style="Inline.TButton").grid(row=0, column=3, padx=(4, 0))
        ttk.Button(binding_bar, text="解绑", command=self.unbind_window, style="Inline.TButton").grid(row=0, column=4, padx=(4, 0))
        ttk.Label(binding_bar, textvariable=self.bound_window_var, style="MetaPanel.TLabel").grid(row=1, column=0, columnspan=5, sticky="w", pady=(5, 0))

        settings_container = ttk.Frame(workspace, style="App.TFrame")
        settings_container.grid(row=3, column=0, sticky="nsew")
        settings_container.rowconfigure(0, weight=1)
        settings_container.columnconfigure(0, weight=1)
        settings_canvas = tk.Canvas(
            settings_container,
            borderwidth=0,
            highlightthickness=0,
            background="#ffffff",
        )
        settings_canvas.grid(row=0, column=0, sticky="nsew")
        settings_scrollbar = ttk.Scrollbar(settings_container, orient="vertical", command=settings_canvas.yview)
        settings_scrollbar.grid(row=0, column=1, sticky="ns")
        settings_canvas.configure(yscrollcommand=settings_scrollbar.set)
        settings = ttk.Frame(settings_canvas, padding=16, style="Panel.TFrame")
        settings_window = settings_canvas.create_window((0, 0), window=settings, anchor="nw")
        settings.bind(
            "<Configure>",
            lambda _event: settings_canvas.configure(scrollregion=settings_canvas.bbox("all")),
        )
        settings_canvas.bind(
            "<Configure>",
            lambda event: settings_canvas.itemconfigure(settings_window, width=event.width),
        )
        settings_canvas.bind("<Enter>", lambda _event: self._bind_settings_mousewheel(settings_canvas))
        settings_canvas.bind("<Leave>", lambda _event: self._unbind_settings_mousewheel())
        settings.columnconfigure(1, weight=1)
        settings.columnconfigure(3, weight=1)
        ttk.Label(settings, text="播放设置", style="Section.TLabel").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 12))
        ttk.Label(settings, text="一拍时间").grid(row=1, column=0, sticky="w")
        ttk.Spinbox(settings, from_=50, to=5000, increment=10, textvariable=self.beat_var, width=10).grid(row=1, column=1, sticky="w", padx=(8, 24))
        ttk.Button(settings, text="使用推荐值", command=self._use_recommended_speed, style="Inline.TButton").grid(row=1, column=1, sticky="w", padx=(90, 20))
        ttk.Label(settings, text="开始倒计时").grid(row=1, column=2, sticky="w")
        ttk.Spinbox(settings, from_=0, to=10, textvariable=self.countdown_var, width=8).grid(row=1, column=3, sticky="w", padx=(8, 0))

        ttk.Separator(settings).grid(row=2, column=0, columnspan=4, sticky="ew", pady=12)
        sequence = ttk.Frame(settings, style="Panel.TFrame")
        sequence.grid(row=3, column=0, columnspan=4, sticky="ew")
        sequence.columnconfigure(2, weight=1)
        ttk.Checkbutton(sequence, text="顺序弹琴", variable=self.sequence_enabled_var).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(sequence, text="单曲循环", variable=self.repeat_one_var).grid(row=0, column=1, sticky="w", padx=(12, 0))
        ttk.Label(sequence, text="间隔秒数").grid(row=0, column=2, sticky="e", padx=(12, 6))
        ttk.Spinbox(sequence, from_=0, to=600, increment=1, textvariable=self.sequence_delay_var, width=7).grid(row=0, column=3, sticky="w")
        ttk.Button(sequence, text="加入队列", command=self.add_current_to_sequence, style="Inline.TButton").grid(row=0, column=4, sticky="e", padx=(8, 0))
        ttk.Button(sequence, text="移除", command=self.remove_sequence_item, style="Inline.TButton").grid(row=0, column=5, sticky="e", padx=(6, 0))
        ttk.Button(sequence, text="清空", command=self.clear_sequence, style="Inline.TButton").grid(row=0, column=6, sticky="e", padx=(6, 0))
        self.sequence_list = tk.Listbox(
            sequence,
            height=2,
            activestyle="none",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#d8dde3",
            highlightcolor="#176b5b",
            background="#ffffff",
            foreground="#20252b",
            selectbackground="#dcefe9",
            selectforeground="#124b40",
            font=("Microsoft YaHei UI", 9),
            exportselection=False,
        )
        self.sequence_list.grid(row=1, column=0, columnspan=7, sticky="ew", pady=(8, 4))
        ttk.Label(sequence, textvariable=self.sequence_status_var, style="MetaPanel.TLabel").grid(row=2, column=0, columnspan=7, sticky="w")

        ttk.Separator(settings).grid(row=4, column=0, columnspan=4, sticky="ew", pady=12)
        ttk.Label(settings, text="全局热键", style="Subsection.TLabel").grid(row=5, column=0, columnspan=4, sticky="w", pady=(0, 8))
        hotkeys = ttk.Frame(settings, style="Panel.TFrame")
        hotkeys.grid(row=6, column=0, columnspan=4, sticky="ew")
        for column in range(3):
            hotkeys.columnconfigure(column, weight=1)
        for column, (label, variable) in enumerate((("开始 / 继续", self.start_key_var), ("暂停 / 继续", self.pause_key_var), ("停止", self.stop_key_var))):
            box = ttk.Frame(hotkeys, style="Panel.TFrame")
            box.grid(row=0, column=column, sticky="w", padx=(0, 28) if column < 2 else 0)
            ttk.Label(box, text=label, style="MetaPanel.TLabel").pack(anchor="w")
            ttk.Combobox(box, values=HOTKEYS, textvariable=variable, state="readonly", width=9).pack(anchor="w", pady=(4, 0))

        guard = ttk.Frame(settings, style="Panel.TFrame")
        guard.grid(row=7, column=0, columnspan=4, sticky="ew", pady=(12, 0))
        ttk.Checkbutton(guard, text="仅在指定游戏窗口位于前台时允许开始", variable=self.guard_var).pack(side="left")
        ttk.Entry(guard, textvariable=self.window_title_var, width=20).pack(side="left", padx=(10, 0))

        ttk.Separator(settings).grid(row=8, column=0, columnspan=4, sticky="ew", pady=12)
        ttk.Checkbutton(
            settings,
            text="显示：TXT 是怎么工作的？（小白教程）",
            variable=self.show_guide_var,
            command=self._toggle_guide,
        ).grid(row=9, column=0, columnspan=4, sticky="w")
        self.guide_frame = ttk.Frame(settings, padding=(12, 9), style="Panel.TFrame")
        self.guide_frame.grid(row=10, column=0, columnspan=4, sticky="ew", pady=(6, 0))
        guide_text = (
            "原理很简单：播放器从上到下读取 TXT。每行左边是要按的琴键，右边是等待几拍。\n"
            "例：a 1 = 按 A 后等 1 拍；ad 0.5 = A、D 同时按并等半拍；p 2 = 空两拍。\n"
            "可用琴键正好是三排：QWERTYU / ASDFGHJ / ZXCVBNM。‘一拍时间’越小，播放越快。\n"
            "不想手写就开启下面的录谱工具：定好一拍时间，按开始热键，正常弹奏，再按结束热键即可。"
        )
        ttk.Label(
            self.guide_frame,
            text=guide_text,
            justify="left",
            wraplength=570,
            style="MetaPanel.TLabel",
        ).pack(anchor="w")
        self.guide_frame.grid_remove()

        ttk.Separator(settings).grid(row=11, column=0, columnspan=4, sticky="ew", pady=12)
        recorder = ttk.Frame(settings, style="Panel.TFrame")
        recorder.grid(row=12, column=0, columnspan=4, sticky="ew")
        recorder.columnconfigure(5, weight=1)
        ttk.Checkbutton(
            recorder,
            text="开启录谱工具（仅记录21个琴键）",
            variable=self.record_enabled_var,
            command=self._toggle_recording_enabled,
        ).grid(row=0, column=0, columnspan=6, sticky="w")
        ttk.Label(recorder, text="开始热键", style="MetaPanel.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Combobox(
            recorder, values=HOTKEYS, textvariable=self.record_start_key_var, state="readonly", width=7
        ).grid(row=1, column=1, sticky="w", padx=(6, 16), pady=(8, 0))
        ttk.Label(recorder, text="结束热键", style="MetaPanel.TLabel").grid(row=1, column=2, sticky="w", pady=(8, 0))
        ttk.Combobox(
            recorder, values=HOTKEYS, textvariable=self.record_stop_key_var, state="readonly", width=7
        ).grid(row=1, column=3, sticky="w", padx=(6, 16), pady=(8, 0))
        self.record_start_button = ttk.Button(
            recorder, text="立即开始", command=self.start_recording, style="Inline.TButton"
        )
        self.record_start_button.grid(row=1, column=4, sticky="w", pady=(8, 0))
        self.record_stop_button = ttk.Button(
            recorder, text="结束并生成 TXT", command=self.stop_recording, style="Danger.TButton"
        )
        self.record_stop_button.grid(row=1, column=5, sticky="w", padx=(6, 0), pady=(8, 0))
        self.record_start_button.state(["disabled"])
        self.record_stop_button.state(["disabled"])
        ttk.Label(recorder, textvariable=self.record_status_var, style="MetaPanel.TLabel").grid(
            row=2, column=0, columnspan=6, sticky="w", pady=(7, 0)
        )

        controls = ttk.Frame(workspace, style="App.TFrame")
        controls.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        self.start_button = ttk.Button(controls, text="▶ 播放", command=self.start_playback, style="Primary.TButton")
        self.start_button.pack(side="left")
        self.pause_button = ttk.Button(controls, text="⏸ 暂停", command=self.pause_playback)
        self.pause_button.pack(side="left", padx=8)
        self.stop_button = ttk.Button(controls, text="■ 停止", command=self.stop_playback, style="Danger.TButton")
        self.stop_button.pack(side="left")
        self.pause_button.state(["disabled"])
        self.stop_button.state(["disabled"])
        ttk.Button(controls, text="保存设置", command=self._save_with_notice, style="Quiet.TButton").pack(side="right")
        self._update_hotkey_hint()
        for var in (self.start_key_var, self.stop_key_var, self.pause_key_var):
            var.trace_add("write", lambda *_args: self._sync_hotkeys())
        for var in (self.record_start_key_var, self.record_stop_key_var):
            var.trace_add("write", lambda *_args: self._record_hotkeys_changed())
        self.beat_var.trace_add("write", lambda *_args: self._refresh_song_detail())
        self.sequence_delay_var.trace_add("write", lambda *_args: self._update_sequence_status())

    def _build_ui(self) -> None:
        """Build the new, original page-based interface."""
        self._setup_styles()
        shell = ttk.Frame(self, padding=(22, 16, 22, 16), style="App.TFrame")
        shell.pack(fill="both", expand=True)
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(1, weight=1)

        header = ttk.Frame(shell, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.columnconfigure(1, weight=1)
        ttk.Label(header, text="21键曲谱播放器", style="Title.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(
            header,
            text="本地曲库 · MIDI 转换 · 游戏窗口后台演奏",
            style="Meta.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w")
        ttk.Label(header, text=f"Beta {APP_VERSION}", style="Count.TLabel").grid(row=0, column=2, rowspan=2, sticky="e")

        self.pages = ttk.Notebook(shell, style="Studio.TNotebook")
        self.pages.grid(row=1, column=0, sticky="nsew")
        self.library_page = ttk.Frame(self.pages, padding=14, style="App.TFrame")
        self.midi_page = ttk.Frame(self.pages, padding=14, style="App.TFrame")
        self.recorder_page = ttk.Frame(self.pages, padding=14, style="App.TFrame")
        self.settings_page = ttk.Frame(self.pages, padding=14, style="App.TFrame")
        self.pages.add(self.library_page, text="  曲库与播放  ")
        self.pages.add(self.midi_page, text="  MIDI 转换  ")
        self.pages.add(self.recorder_page, text="  录谱与说明  ")
        self.pages.add(self.settings_page, text="  设置  ")

        self._build_library_page()
        self._build_midi_page()
        self._build_recorder_page()
        self._build_settings_page()
        self._build_transport(shell)

        self.search_var.trace_add("write", lambda *_args: self._apply_song_filter())
        self.library_filter_var.trace_add("write", lambda *_args: self._apply_song_filter())
        for var in (self.start_key_var, self.stop_key_var, self.pause_key_var):
            var.trace_add("write", lambda *_args: self._sync_hotkeys())
        for var in (self.record_start_key_var, self.record_stop_key_var):
            var.trace_add("write", lambda *_args: self._record_hotkeys_changed())
        self.beat_var.trace_add("write", lambda *_args: self._refresh_song_detail())
        self.sequence_delay_var.trace_add("write", lambda *_args: self._update_sequence_status())

    def _build_library_page(self) -> None:
        page = self.library_page
        page.columnconfigure(0, weight=0)
        page.columnconfigure(1, weight=1)
        page.rowconfigure(0, weight=1)

        sidebar = ttk.Frame(page, padding=14, style="Panel.TFrame")
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        sidebar.columnconfigure(0, weight=1)
        sidebar.rowconfigure(3, weight=1)
        library_header = ttk.Frame(sidebar, style="Panel.TFrame")
        library_header.grid(row=0, column=0, sticky="ew")
        library_header.columnconfigure(0, weight=1)
        ttk.Label(library_header, text="我的曲库", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(library_header, textvariable=self.song_count_var, style="MetaPanel.TLabel").grid(row=0, column=1, sticky="e")
        search = ttk.Entry(sidebar, textvariable=self.search_var, width=29)
        search.grid(row=1, column=0, sticky="ew", pady=(12, 8))
        search.bind("<Return>", self._select_first_search_result)
        filter_row = ttk.Frame(sidebar, style="Panel.TFrame")
        filter_row.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        ttk.Combobox(
            filter_row,
            textvariable=self.library_filter_var,
            values=("全部", "收藏", "最近播放"),
            state="readonly",
            width=12,
        ).pack(side="left")
        ttk.Label(filter_row, textvariable=self.search_count_var, style="MetaPanel.TLabel").pack(side="right")
        list_frame = ttk.Frame(sidebar, style="Panel.TFrame")
        list_frame.grid(row=3, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        self.song_list = tk.Listbox(
            list_frame,
            width=30,
            activestyle="none",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#d7dddc",
            highlightcolor="#1e6a62",
            background="#fbfcfc",
            foreground="#1d2927",
            selectbackground="#d6ebe5",
            selectforeground="#124b45",
            font=("Microsoft YaHei UI", 10),
            exportselection=False,
        )
        self.song_list.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.song_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.song_list.configure(yscrollcommand=scrollbar.set)
        self.song_list.bind("<<ListboxSelect>>", self._on_song_list_selected)
        actions = ttk.Frame(sidebar, style="Panel.TFrame")
        actions.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(actions, text="导入 TXT", command=self.import_songs, style="Inline.TButton").pack(side="left")
        ttk.Button(actions, text="导入 MIDI", command=self._open_midi_from_library, style="Inline.TButton").pack(side="left", padx=5)
        ttk.Button(actions, text="文件夹", command=self.open_song_folder, style="Quiet.TButton").pack(side="right")

        main = ttk.Frame(page, style="App.TFrame")
        main.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(4, weight=1)

        now = ttk.Frame(main, padding=(18, 14), style="Panel.TFrame")
        now.grid(row=0, column=0, sticky="ew")
        now.columnconfigure(0, weight=1)
        ttk.Label(now, text="正在准备", style="Eyebrow.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(now, textvariable=self.current_song_var, style="SongTitle.TLabel").grid(row=1, column=0, sticky="w", pady=(3, 0))
        ttk.Label(now, textvariable=self.detail_var, style="Detail.TLabel").grid(row=2, column=0, sticky="w", pady=(4, 0))
        self.favorite_button = ttk.Button(
            now,
            textvariable=self.favorite_button_var,
            command=self._toggle_current_favorite,
            style="Star.TButton",
            width=3,
        )
        self.favorite_button.grid(row=0, column=1, rowspan=2, sticky="e")
        tags = ttk.Frame(now, style="Panel.TFrame")
        tags.grid(row=2, column=1, sticky="e")
        ttk.Entry(tags, textvariable=self.tags_var, width=23).pack(side="left")
        ttk.Button(tags, text="保存标签", command=self._save_current_tags, style="Inline.TButton").pack(side="left", padx=(5, 0))
        ttk.Label(now, textvariable=self.song_meta_var, style="MetaPanel.TLabel").grid(row=3, column=0, columnspan=2, sticky="w", pady=(7, 0))

        visual = ttk.Frame(main, padding=(18, 12), style="Dark.TFrame")
        visual.grid(row=1, column=0, sticky="ew", pady=(10, 10))
        visual.columnconfigure(0, weight=1)
        status_row = ttk.Frame(visual, style="Dark.TFrame")
        status_row.grid(row=0, column=0, sticky="ew")
        status_row.columnconfigure(0, weight=1)
        self.status_label = ttk.Label(status_row, textvariable=self.status_var, style="Status.TLabel")
        self.status_label.grid(row=0, column=0, sticky="w")
        self.current_var = tk.StringVar(value="尚未播放")
        ttk.Label(status_row, textvariable=self.current_var, style="StatusMeta.TLabel").grid(row=0, column=1, padx=(8, 8))
        ttk.Label(status_row, textvariable=self.progress_text_var, style="Percent.TLabel").grid(row=0, column=2)
        self.progress = ttk.Scale(visual, variable=self.progress_var, from_=0, to=100, orient="horizontal", command=self._on_seek_changed, style="Accent.Horizontal.TScale")
        self.progress.grid(row=1, column=0, sticky="ew", pady=(9, 10))
        self.progress.bind("<ButtonPress-1>", self._on_seek_press)
        self.progress.bind("<ButtonRelease-1>", self._on_seek_release)
        keyboard = ttk.Frame(visual, style="Dark.TFrame")
        keyboard.grid(row=2, column=0)
        for row, keys in enumerate(("qwertyu", "asdfghj", "zxcvbnm")):
            for column, key in enumerate(keys):
                label = ttk.Label(keyboard, text=key.upper(), style="DarkKey.TLabel", anchor="center", width=4)
                label.grid(row=row, column=column, padx=2, pady=2)
                self.keyboard_labels[key] = label

        binding = ttk.Frame(main, padding=(12, 9), style="Panel.TFrame")
        binding.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        binding.columnconfigure(1, weight=1)
        ttk.Label(binding, text="目标窗口", style="Subsection.TLabel").grid(row=0, column=0, padx=(0, 10))
        self.window_combo = ttk.Combobox(binding, textvariable=self.window_choice_var, state="readonly", width=42)
        self.window_combo.grid(row=0, column=1, sticky="ew")
        ttk.Button(binding, text="刷新", command=self.refresh_windows, style="Inline.TButton").grid(row=0, column=2, padx=(6, 0))
        ttk.Button(binding, text="绑定", command=self.bind_selected_window, style="Primary.TButton").grid(row=0, column=3, padx=(5, 0))
        ttk.Button(binding, text="解绑", command=self.unbind_window, style="Quiet.TButton").grid(row=0, column=4, padx=(5, 0))
        ttk.Label(binding, textvariable=self.bound_window_var, style="MetaPanel.TLabel").grid(row=1, column=0, columnspan=5, sticky="w", pady=(5, 0))

        queue = ttk.Frame(main, padding=(12, 9), style="Panel.TFrame")
        queue.grid(row=3, column=0, sticky="ew")
        queue.columnconfigure(0, weight=1)
        ttk.Label(queue, text="播放队列", style="Subsection.TLabel").grid(row=0, column=0, sticky="w")
        options = ttk.Frame(queue, style="Panel.TFrame")
        options.grid(row=0, column=1, sticky="e")
        ttk.Checkbutton(options, text="顺序", variable=self.sequence_enabled_var).pack(side="left")
        ttk.Checkbutton(options, text="单曲循环", variable=self.repeat_one_var).pack(side="left", padx=(8, 0))
        ttk.Button(options, text="加入", command=self.add_current_to_sequence, style="Inline.TButton").pack(side="left", padx=(8, 0))
        ttk.Button(options, text="移除", command=self.remove_sequence_item, style="Inline.TButton").pack(side="left")
        ttk.Button(options, text="清空", command=self.clear_sequence, style="Inline.TButton").pack(side="left")
        self.sequence_list = tk.Listbox(queue, height=3, borderwidth=0, highlightthickness=1, highlightbackground="#d7dddc", exportselection=False, font=("Microsoft YaHei UI", 9))
        self.sequence_list.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(7, 3))
        ttk.Label(queue, textvariable=self.sequence_status_var, style="MetaPanel.TLabel").grid(row=2, column=0, columnspan=2, sticky="w")

    def _build_midi_page(self) -> None:
        page = self.midi_page
        page.columnconfigure(0, weight=1)
        page.rowconfigure(2, weight=1)
        source = ttk.Frame(page, padding=14, style="Panel.TFrame")
        source.grid(row=0, column=0, sticky="ew")
        source.columnconfigure(1, weight=1)
        ttk.Label(source, text="MIDI 转换向导", style="Section.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Button(
            source,
            text="？ 使用说明",
            command=self._show_midi_help,
            style="Quiet.TButton",
            width=10,
        ).grid(row=0, column=2, sticky="e")
        ttk.Label(source, text="文件", style="MetaPanel.TLabel").grid(row=1, column=0, sticky="w", pady=(12, 0))
        ttk.Entry(source, textvariable=self.midi_path_var, state="readonly").grid(row=1, column=1, sticky="ew", padx=8, pady=(12, 0))
        ttk.Button(source, text="选择 MIDI", command=self._choose_midi_file, style="Primary.TButton").grid(row=1, column=2, pady=(12, 0))
        ttk.Label(source, textvariable=self.midi_status_var, style="MetaPanel.TLabel").grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 0))

        options = ttk.Frame(page, padding=(14, 10), style="Panel.TFrame")
        options.grid(row=1, column=0, sticky="ew", pady=(10, 10))
        ttk.Label(options, text="黑键处理").pack(side="left")
        ttk.Combobox(options, textvariable=self.midi_strategy_var, values=("最近白键", "忽略黑键"), state="readonly", width=12).pack(side="left", padx=(6, 18))
        ttk.Label(options, text="移调半音").pack(side="left")
        ttk.Combobox(options, textvariable=self.midi_transpose_var, values=("自动",) + tuple(str(value) for value in range(-24, 25)), width=8).pack(side="left", padx=(6, 18))
        ttk.Label(options, text="量化").pack(side="left")
        ttk.Combobox(options, textvariable=self.midi_quantize_var, values=("1/4 拍", "1/8 拍", "1/16 拍"), state="readonly", width=9).pack(side="left", padx=(6, 18))
        ttk.Button(options, text="转换为21键", command=self._convert_selected_midi, style="Gold.TButton").pack(side="right")

        content = ttk.Panedwindow(page, orient="horizontal")
        content.grid(row=2, column=0, sticky="nsew")
        tracks_panel = ttk.Frame(content, padding=12, style="Panel.TFrame")
        preview_panel = ttk.Frame(content, padding=12, style="Panel.TFrame")
        content.add(tracks_panel, weight=2)
        content.add(preview_panel, weight=3)
        tracks_panel.rowconfigure(1, weight=1)
        tracks_panel.columnconfigure(0, weight=1)
        ttk.Label(tracks_panel, text="音轨（双击切换）", style="Subsection.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.midi_tracks = ttk.Treeview(tracks_panel, columns=("notes", "range", "instrument"), show="tree headings", selectmode="browse")
        self.midi_tracks.heading("#0", text="选择 / 音轨")
        self.midi_tracks.heading("notes", text="音符")
        self.midi_tracks.heading("range", text="音域")
        self.midi_tracks.heading("instrument", text="乐器")
        self.midi_tracks.column("#0", width=190)
        self.midi_tracks.column("notes", width=55, anchor="center")
        self.midi_tracks.column("range", width=105, anchor="center")
        self.midi_tracks.column("instrument", width=120)
        self.midi_tracks.grid(row=1, column=0, sticky="nsew")
        self.midi_tracks.bind("<Double-1>", self._toggle_midi_track)

        preview_panel.rowconfigure(2, weight=1)
        preview_panel.columnconfigure(0, weight=1)
        ttk.Label(preview_panel, text="21键结果预览", style="Subsection.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(preview_panel, textvariable=self.midi_summary_var, style="MetaPanel.TLabel", wraplength=510, justify="left").grid(row=1, column=0, sticky="ew", pady=(6, 8))
        self.midi_canvas = tk.Canvas(preview_panel, background="#172523", highlightthickness=0, height=250)
        self.midi_canvas.grid(row=2, column=0, sticky="nsew")
        save_row = ttk.Frame(preview_panel, style="Panel.TFrame")
        save_row.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        save_row.columnconfigure(1, weight=1)
        ttk.Button(save_row, text="试听前30秒", command=self._preview_midi_result, style="Inline.TButton").grid(row=0, column=0)
        ttk.Entry(save_row, textvariable=self.midi_name_var).grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(save_row, text="保存到曲库", command=self._save_midi_result, style="Primary.TButton").grid(row=0, column=2)

    def _build_recorder_page(self) -> None:
        page = self.recorder_page
        page.columnconfigure(0, weight=1)
        intro = ttk.Frame(page, padding=18, style="Panel.TFrame")
        intro.grid(row=0, column=0, sticky="ew")
        ttk.Label(intro, text="把实际演奏变成 TXT", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            intro,
            text="播放器只监听 QWERTYU / ASDFGHJ / ZXCVBNM。设置拍速后开始录制，正常弹奏，再结束生成可编辑 TXT。",
            style="MetaPanel.TLabel",
            wraplength=780,
            justify="left",
        ).pack(anchor="w", pady=(7, 0))
        recorder = ttk.Frame(page, padding=18, style="Panel.TFrame")
        recorder.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        recorder.columnconfigure(5, weight=1)
        ttk.Checkbutton(recorder, text="开启21键录谱监听", variable=self.record_enabled_var, command=self._toggle_recording_enabled).grid(row=0, column=0, columnspan=6, sticky="w")
        ttk.Label(recorder, text="开始热键").grid(row=1, column=0, pady=(12, 0))
        ttk.Combobox(recorder, values=HOTKEYS, textvariable=self.record_start_key_var, state="readonly", width=8).grid(row=1, column=1, padx=(6, 18), pady=(12, 0))
        ttk.Label(recorder, text="结束热键").grid(row=1, column=2, pady=(12, 0))
        ttk.Combobox(recorder, values=HOTKEYS, textvariable=self.record_stop_key_var, state="readonly", width=8).grid(row=1, column=3, padx=(6, 18), pady=(12, 0))
        self.record_start_button = ttk.Button(recorder, text="开始录谱", command=self.start_recording, style="Primary.TButton")
        self.record_start_button.grid(row=1, column=4, pady=(12, 0))
        self.record_stop_button = ttk.Button(recorder, text="结束并生成 TXT", command=self.stop_recording, style="Danger.TButton")
        self.record_stop_button.grid(row=1, column=5, sticky="w", padx=(8, 0), pady=(12, 0))
        self.record_start_button.state(["disabled"])
        self.record_stop_button.state(["disabled"])
        ttk.Label(recorder, textvariable=self.record_status_var, style="MetaPanel.TLabel").grid(row=2, column=0, columnspan=6, sticky="w", pady=(10, 0))

        self.guide_frame = ttk.Frame(page, padding=18, style="Panel.TFrame")
        self.guide_frame.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        ttk.Label(self.guide_frame, text="TXT 快速说明", style="Subsection.TLabel").pack(anchor="w")
        ttk.Label(
            self.guide_frame,
            text="a 1 = 按 A 后等待一拍；ad 0.5 = A、D 同时按并等待半拍；p 2 = 休止两拍。每行只写一次事件。",
            style="MetaPanel.TLabel",
            justify="left",
        ).pack(anchor="w", pady=(7, 0))
        self.show_guide_var.set(True)

    def _build_settings_page(self) -> None:
        page = self.settings_page
        page.columnconfigure(0, weight=1)
        playback = ttk.LabelFrame(page, text="播放与队列", padding=16)
        playback.grid(row=0, column=0, sticky="ew")
        ttk.Label(playback, text="一拍时间（ms）").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(playback, from_=50, to=5000, increment=10, textvariable=self.beat_var, width=10).grid(row=0, column=1, padx=(8, 22))
        ttk.Button(playback, text="使用当前歌曲推荐值", command=self._use_recommended_speed, style="Inline.TButton").grid(row=0, column=2, padx=(0, 22))
        ttk.Label(playback, text="开始倒计时").grid(row=0, column=3)
        ttk.Spinbox(playback, from_=0, to=10, textvariable=self.countdown_var, width=7).grid(row=0, column=4, padx=(8, 22))
        ttk.Label(playback, text="队列间隔秒数").grid(row=0, column=5)
        ttk.Spinbox(playback, from_=0, to=600, textvariable=self.sequence_delay_var, width=7).grid(row=0, column=6, padx=(8, 0))

        hotkeys = ttk.LabelFrame(page, text="全局热键", padding=16)
        hotkeys.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        for column, (label, variable) in enumerate((("开始 / 继续", self.start_key_var), ("暂停 / 继续", self.pause_key_var), ("停止", self.stop_key_var))):
            ttk.Label(hotkeys, text=label).grid(row=0, column=column * 2, sticky="w", padx=(0 if column == 0 else 22, 6))
            ttk.Combobox(hotkeys, values=HOTKEYS, textvariable=variable, state="readonly", width=8).grid(row=0, column=column * 2 + 1)

        safety = ttk.LabelFrame(page, text="窗口与安全", padding=16)
        safety.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        ttk.Checkbutton(safety, text="仅在指定游戏窗口位于前台时允许开始", variable=self.guard_var).grid(row=0, column=0, sticky="w")
        ttk.Entry(safety, textvariable=self.window_title_var, width=24).grid(row=0, column=1, padx=(10, 0))
        ttk.Label(safety, text="绑定窗口后会自动切换为后台发送；解绑后恢复前台发送。", style="MetaPanel.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

        actions = ttk.Frame(page, style="App.TFrame")
        actions.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        ttk.Button(actions, text="保存全部设置", command=self._save_with_notice, style="Primary.TButton").pack(side="left")
        ttk.Button(actions, text="保存当前歌曲速度", command=self._save_current_song_settings, style="Gold.TButton").pack(side="left", padx=8)
        ttk.Label(actions, text=f"数据目录：{self.data_dir}", style="Meta.TLabel").pack(side="right")

    def _build_transport(self, shell: ttk.Frame) -> None:
        transport = ttk.Frame(shell, padding=(14, 10), style="Transport.TFrame")
        transport.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        transport.columnconfigure(3, weight=1)
        self.start_button = ttk.Button(transport, text="▶ 播放", command=self.start_playback, style="Primary.TButton")
        self.start_button.grid(row=0, column=0)
        self.pause_button = ttk.Button(transport, text="⏸ 暂停", command=self.pause_playback)
        self.pause_button.grid(row=0, column=1, padx=8)
        self.stop_button = ttk.Button(transport, text="■ 停止", command=self.stop_playback, style="Danger.TButton")
        self.stop_button.grid(row=0, column=2)
        self.pause_button.state(["disabled"])
        self.stop_button.state(["disabled"])
        self.hotkey_hint = ttk.Label(transport, text="", style="TransportMeta.TLabel")
        self.hotkey_hint.grid(row=0, column=3, sticky="e")
        self._update_hotkey_hint()

    def _setup_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", font=("Microsoft YaHei UI", 9), foreground="#1d2927")
        style.configure("App.TFrame", background="#eef1f2")
        style.configure("Panel.TFrame", background="#ffffff")
        style.configure("Dark.TFrame", background="#172523")
        style.configure("Transport.TFrame", background="#dde5e3")
        style.configure("Brand.TLabel", background="#eef1f2", foreground="#b07a2a", font=("STKaiti", 25, "bold"))
        style.configure("Title.TLabel", background="#eef1f2", foreground="#172523", font=("Microsoft YaHei UI", 17, "bold"))
        style.configure("Meta.TLabel", background="#eef1f2", foreground="#687572", font=("Microsoft YaHei UI", 9))
        style.configure("Count.TLabel", background="#dbe8e4", foreground="#1e6a62", padding=(10, 5), font=("Microsoft YaHei UI", 9, "bold"))
        style.configure("Section.TLabel", background="#ffffff", foreground="#17202a", font=("Microsoft YaHei UI", 12, "bold"))
        style.configure("Subsection.TLabel", background="#ffffff", foreground="#303840", font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("Eyebrow.TLabel", background="#ffffff", foreground="#6d7782", font=("Microsoft YaHei UI", 9))
        style.configure("SongTitle.TLabel", background="#ffffff", foreground="#17202a", font=("Microsoft YaHei UI", 17, "bold"))
        style.configure("Detail.TLabel", background="#ffffff", foreground="#176b5b")
        style.configure("MetaPanel.TLabel", background="#ffffff", foreground="#69727d")
        style.configure("Status.TLabel", background="#172523", foreground="#ffffff", font=("Microsoft YaHei UI", 11, "bold"))
        style.configure("StatusMeta.TLabel", background="#172523", foreground="#bdcbc7")
        style.configure("Percent.TLabel", background="#172523", foreground="#80d4bc", font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("Key.TLabel", background="#edf0f2", foreground="#68727c", padding=(4, 3), font=("Consolas", 8, "bold"))
        style.configure("ActiveKey.TLabel", background="#54b497", foreground="#ffffff", padding=(4, 3), font=("Consolas", 8, "bold"))
        style.configure("DarkKey.TLabel", background="#263b37", foreground="#b9c9c5", padding=(7, 5), font=("Consolas", 9, "bold"))
        style.configure("DarkActiveKey.TLabel", background="#d4a651", foreground="#172523", padding=(7, 5), font=("Consolas", 9, "bold"))
        style.configure("TransportMeta.TLabel", background="#dde5e3", foreground="#53625f")
        style.configure("Studio.TNotebook", background="#eef1f2", borderwidth=0, tabmargins=(0, 0, 0, 0))
        style.configure("Studio.TNotebook.Tab", background="#dde5e3", foreground="#45534f", padding=(16, 9), borderwidth=0)
        style.map("Studio.TNotebook.Tab", background=[("selected", "#ffffff"), ("active", "#e6ecea")], foreground=[("selected", "#1e6a62")])
        style.configure("TButton", padding=(12, 7), borderwidth=0)
        style.configure("Primary.TButton", background="#176b5b", foreground="#ffffff", font=("Microsoft YaHei UI", 10, "bold"))
        style.map("Primary.TButton", background=[("active", "#125648"), ("pressed", "#0e473c")])
        style.configure("Danger.TButton", background="#f4e5df", foreground="#9d351f")
        style.map("Danger.TButton", background=[("active", "#ead2c9")])
        style.configure("Quiet.TButton", background="#e9edf0", foreground="#3f4851")
        style.map("Quiet.TButton", background=[("active", "#dce2e6")])
        style.configure("Inline.TButton", background="#ffffff", foreground="#176b5b", padding=(8, 4), font=("Microsoft YaHei UI", 8))
        style.map("Inline.TButton", background=[("active", "#e4f0ec")])
        style.configure("Gold.TButton", background="#ead8b5", foreground="#6f4b12", font=("Microsoft YaHei UI", 9, "bold"))
        style.map("Gold.TButton", background=[("active", "#dfc28a"), ("pressed", "#d4ae67")])
        style.configure("Star.TButton", background="#fbfcfc", foreground="#8b6b2d", font=("Segoe UI Symbol", 13), padding=(4, 1))
        style.map("Star.TButton", background=[("active", "#f3ead8"), ("pressed", "#ead8b5")])
        style.configure("Accent.Horizontal.TProgressbar", troughcolor="#3b4652", background="#54b497", bordercolor="#3b4652", lightcolor="#54b497", darkcolor="#54b497", thickness=8)
        style.configure("Accent.Horizontal.TScale", troughcolor="#3b4652", background="#54b497")

    def _bind_settings_mousewheel(self, canvas: tk.Canvas) -> None:
        self.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-event.delta / 120), "units"))

    def _unbind_settings_mousewheel(self) -> None:
        self.unbind_all("<MouseWheel>")

    def _update_hotkey_hint(self) -> None:
        if hasattr(self, "hotkey_hint"):
            self.hotkey_hint.configure(text=f"全局热键：{self.start_key_var.get()} 开始/继续　{self.pause_key_var.get()} 暂停/继续　{self.stop_key_var.get()} 停止")

    def _sync_hotkeys(self) -> None:
        with self._hotkey_lock:
            self._hotkey_values = {
                "start": self.start_key_var.get(),
                "stop": self.stop_key_var.get(),
                "pause": self.pause_key_var.get(),
            }
        self._update_hotkey_hint()
        if hasattr(self, "record_start_key_var"):
            self._sync_recording_config()

    def _toggle_guide(self) -> None:
        if self.show_guide_var.get():
            self.guide_frame.grid()
        else:
            self.guide_frame.grid_remove()

    def _validate_record_hotkeys(self) -> None:
        playback = {self.start_key_var.get(), self.stop_key_var.get(), self.pause_key_var.get()}
        record_start = self.record_start_key_var.get()
        record_stop = self.record_stop_key_var.get()
        if record_start == record_stop:
            raise ValueError("录谱开始和结束必须使用两个不同的热键。")
        overlap = playback & {record_start, record_stop}
        if overlap:
            raise ValueError(f"录谱热键不能与播放热键重复：{', '.join(sorted(overlap))}")

    def _sync_recording_config(self) -> None:
        enabled = self.record_enabled_var.get()
        if enabled:
            try:
                self._validate_record_hotkeys()
            except ValueError as exc:
                enabled = False
                self.record_status_var.set(f"热键冲突：{exc}")
        with self._record_lock:
            self._record_config = {
                "enabled": enabled,
                "start_key": self.record_start_key_var.get(),
                "stop_key": self.record_stop_key_var.get(),
            }
        if hasattr(self, "record_start_button"):
            self.record_start_button.state(["!disabled"] if enabled else ["disabled"])

    def _recording_config(self) -> dict[str, str | bool]:
        with self._record_lock:
            return dict(self._record_config)

    def _record_hotkeys_changed(self) -> None:
        self._sync_recording_config()
        if self.record_enabled_var.get() and self._recording_config()["enabled"]:
            self.record_status_var.set(
                f"已开启：{self.record_start_key_var.get()} 开始，{self.record_stop_key_var.get()} 结束"
            )

    def _toggle_recording_enabled(self) -> None:
        if self.record_enabled_var.get():
            try:
                self._validate_record_hotkeys()
            except ValueError as exc:
                self.record_enabled_var.set(False)
                self._sync_recording_config()
                messagebox.showerror("无法开启录谱", str(exc))
                return
            self.record_status_var.set(
                f"已开启但尚未录制：按 {self.record_start_key_var.get()} 开始"
            )
        else:
            if hasattr(self, "recorder"):
                self.recorder.cancel()
            self.record_status_var.set("录谱功能未开启")
            if hasattr(self, "record_stop_button"):
                self.record_stop_button.state(["disabled"])
        self._sync_recording_config()

    def start_recording(self) -> None:
        try:
            self._validate_record_hotkeys()
            self._beat_ms()
        except ValueError as exc:
            messagebox.showerror("无法录制", str(exc))
            return
        if self.engine.running:
            messagebox.showwarning("无法录制", "请先停止自动播放，再开始手动录谱。")
            return
        if not self.record_enabled_var.get():
            messagebox.showinfo("录谱工具", "请先勾选“开启录谱工具”。")
            return
        if not self.recorder.begin() and self.recorder.recording:
            self.record_status_var.set("正在录制，请弹奏21键琴键。")

    def stop_recording(self) -> None:
        if not self.recorder.finish():
            self.record_status_var.set("尚未开始录制。")

    def _on_recorder_event(self, event: str, payload: dict) -> None:
        if event == "started":
            if self.engine.running:
                self.recorder.cancel()
                messagebox.showwarning("无法录制", "请先停止自动播放，再开始手动录谱。")
                return
            self.record_status_var.set("● 正在录制：请正常弹奏，完成后按结束热键")
            self.record_start_button.state(["disabled"])
            self.record_stop_button.state(["!disabled"])
            return
        if event == "count":
            self.record_status_var.set(f"● 正在录制：已记录 {payload['count']} 次按键")
            return
        if event == "cancelled":
            self.record_status_var.set("录制已取消，没有保存按键。")
            self.record_stop_button.state(["disabled"])
            self._sync_recording_config()
            return
        if event != "stopped":
            return

        self.record_stop_button.state(["disabled"])
        self._sync_recording_config()
        try:
            beat_ms = self._beat_ms()
            events = recorded_presses_to_events(
                payload["presses"],
                started_at=payload["started_at"],
                stopped_at=payload["stopped_at"],
                beat_ms=beat_ms,
            )
        except ValueError as exc:
            self.record_status_var.set(str(exc))
            messagebox.showwarning("没有生成琴谱", str(exc))
            return

        name = simpledialog.askstring(
            "录谱完成",
            f"已生成 {len(events)} 个事件。请输入歌曲名称：",
            initialvalue="我的琴谱",
            parent=self,
        )
        if not name:
            self.record_status_var.set("录制完成，但用户取消了命名，未保存。")
            return
        name = name.strip()
        if not name or any(character in '<>:"/\\|?*' or ord(character) < 32 for character in name):
            messagebox.showerror("名称无效", "名称不能为空，也不能包含 < > : \" / \\ | ? *。")
            self.record_status_var.set("名称无效，未保存。")
            return
        destination = self.songs_dir / f"{name.rstrip('. ')}.txt"
        if destination.exists() and not messagebox.askyesno("覆盖歌曲", f"曲库中已有 {destination.name}，是否覆盖？"):
            self.record_status_var.set("未覆盖已有歌曲。")
            return
        destination.write_text(format_song_txt(events, beat_ms=beat_ms), encoding="utf-8")
        self.refresh_songs(select=destination.stem)
        self.save_config()
        self.record_status_var.set(f"已保存并加入曲库：{destination.name}")
        messagebox.showinfo("录谱成功", f"已保存为：\n{destination}")

    def refresh_songs(self, select: str | None = None) -> None:
        self.song_paths = {path.stem: path for path in sorted(self.songs_dir.glob("*.txt"), key=lambda p: p.name.lower())}
        names = list(self.song_paths)
        self.song_count_var.set(f"{len(names)} 首歌曲")
        if select in self.song_paths:
            self.song_var.set(select)
        elif names and self.song_var.get() not in self.song_paths:
            self.song_var.set(names[0])
        self._apply_song_filter()
        self.load_selected_song()

    def _filtered_song_names(self) -> list[str]:
        names = list(self.song_paths)
        mode = self.library_filter_var.get() if hasattr(self, "library_filter_var") else "全部"
        if mode == "收藏":
            favorites = self.library_store.favorite_names()
            names = [name for name in names if name in favorites]
        elif mode == "最近播放":
            names = [name for name in self.library_store.recent(100) if name in self.song_paths]
        return filter_song_names(names, self.search_var.get())

    def _apply_song_filter(self) -> None:
        if not hasattr(self, "song_list"):
            return
        matches = self._filtered_song_names()
        self._render_song_list(matches)
        if self.search_var.get().strip() or self.library_filter_var.get() != "全部":
            self.status_var.set(f"搜索到 {len(matches)} 首歌曲。")

    def _render_song_list(self, names: list[str]) -> None:
        self.search_count_var.set(f"{len(names)} 首")
        self.song_list.delete(0, tk.END)
        for name in names:
            self.song_list.insert(tk.END, name)
        current = self.song_var.get()
        if current in names:
            index = names.index(current)
            self.song_list.selection_set(index)
            self.song_list.see(index)

    def _on_song_list_selected(self, _event=None) -> None:
        selection = self.song_list.curselection()
        if not selection:
            return
        self.song_var.set(self.song_list.get(selection[0]))
        self._on_song_selected()

    def _select_first_search_result(self, _event=None) -> None:
        matches = self._filtered_song_names()
        if not matches:
            self.status_var.set("没有找到匹配的歌曲。")
            return
        self.song_var.set(matches[0])
        self._render_song_list(matches)
        self._on_song_selected()

    def load_selected_song(self) -> None:
        name = self.song_var.get()
        path = self.song_paths.get(name)
        if not path:
            self.events = []
            self.current_song_var.set("尚未选择歌曲")
            self.detail_var.set("曲库为空，请导入TXT。")
            return
        try:
            self.events = parse_song(path)
        except Exception as exc:  # noqa: BLE001
            self.events = []
            self.current_song_var.set(name)
            self.detail_var.set(f"文件错误：{exc}")
            return
        self.current_song_var.set(name)
        self._refresh_song_detail()
        self._update_song_metadata_ui()
        self.status_var.set(f"已载入：{name}")
        self._playback_start_index = 0
        self._has_seek_position = False
        self.progress_var.set(0)
        self._update_progress_text(0)
        self._highlight_keys("")

    def _on_song_selected(self, _event=None) -> None:
        metadata = self.library_store.get(self.song_var.get())
        saved_speed = metadata.get("settings", {}).get("beat_ms") if isinstance(metadata.get("settings", {}), dict) else None
        recommended = recommended_beat_ms(self.song_var.get())
        if saved_speed is not None:
            self.beat_var.set(str(saved_speed))
        elif recommended is not None:
            self.beat_var.set(str(recommended))
        self.load_selected_song()

    def _update_song_metadata_ui(self) -> None:
        if not hasattr(self, "favorite_button_var"):
            return
        name = self.song_var.get()
        metadata = self.library_store.get(name)
        favorite = bool(metadata.get("favorite", False))
        tags = metadata.get("tags", []) if isinstance(metadata.get("tags", []), list) else []
        self.favorite_button_var.set("★" if favorite else "☆")
        self.tags_var.set(", ".join(str(tag) for tag in tags))
        plays = int(metadata.get("play_count", 0))
        self.song_meta_var.set(f"播放 {plays} 次" + (f" · 标签：{'、'.join(tags)}" if tags else " · 尚未添加标签"))

    def _toggle_current_favorite(self) -> None:
        name = self.song_var.get()
        if not name:
            return
        self.library_store.toggle_favorite(name)
        self._update_song_metadata_ui()
        if self.library_filter_var.get() == "收藏":
            self._apply_song_filter()

    def _save_current_tags(self) -> None:
        name = self.song_var.get()
        if not name:
            return
        tags = [item.strip() for item in self.tags_var.get().replace("，", ",").split(",")]
        self.library_store.set_tags(name, tags)
        self._update_song_metadata_ui()
        self.status_var.set("当前歌曲标签已保存。")

    def _save_current_song_settings(self) -> None:
        name = self.song_var.get()
        if not name:
            messagebox.showwarning("没有歌曲", "请先选择歌曲。")
            return
        try:
            beat_ms = self._beat_ms()
        except ValueError as exc:
            messagebox.showerror("设置错误", str(exc))
            return
        self.library_store.set_song_settings(name, beat_ms=beat_ms)
        self._update_song_metadata_ui()
        self.status_var.set(f"已保存《{name}》的专属速度：{beat_ms} ms/拍")

    def _refresh_song_detail(self) -> None:
        if not self.events:
            return
        beat_ms = self._beat_ms(default=700)
        seconds = sum(event.beats for event in self.events) * beat_ms / 1000
        recommended = recommended_beat_ms(self.song_var.get())
        recommendation = f" · 推荐 {recommended} ms/拍" if recommended is not None else ""
        self.detail_var.set(
            f"{len(self.events)} 个事件{recommendation} · 当前预计 "
            f"{int(seconds // 60)}:{int(seconds % 60):02d}"
        )

    def _use_recommended_speed(self) -> None:
        recommended = recommended_beat_ms(self.song_var.get())
        if recommended is None:
            self.status_var.set("当前歌曲没有推荐速度。")
            return
        self.beat_var.set(str(recommended))
        self.status_var.set(f"已恢复推荐速度：{recommended} ms/拍")

    def import_songs(self) -> None:
        paths = filedialog.askopenfilenames(title="导入琴谱TXT", filetypes=[("琴谱TXT", "*.txt")])
        if not paths:
            return
        imported = []
        for raw in paths:
            source = Path(raw)
            try:
                parse_song(source)
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror("无法导入", f"{source.name}\n{exc}")
                continue
            destination = self.songs_dir / source.name
            if destination.exists() and not messagebox.askyesno("覆盖歌曲", f"曲库中已有 {source.name}，是否覆盖？"):
                continue
            shutil.copy2(source, destination)
            imported.append(destination.stem)
        if imported:
            self.refresh_songs(select=imported[-1])
            self.save_config()
            messagebox.showinfo("导入完成", f"已导入 {len(imported)} 首歌曲。")

    def _open_midi_from_library(self) -> None:
        self.pages.select(self.midi_page)
        self._choose_midi_file()

    def _show_midi_help(self) -> None:
        messagebox.showinfo(
            "MIDI 转换适用说明",
            "适合直接转换\n"
            "• 独立主旋律轨，或已经整理好的单旋律 MIDI。\n"
            "• 多轨 MIDI 可取消鼓、贝斯与伴奏，只保留旋律轨。\n\n"
            "需要重点复核\n"
            "• 单轨钢琴 MIDI 可能把左右手、旋律与和弦混在一起。\n"
            "• 大量和弦、越界音或黑键近似，表示结果更适合作为草稿。\n"
            "• 转换器不会从 MP3、人声录音中自动生成可靠 MIDI。\n\n"
            "推荐流程\n"
            "选择 MIDI → 保留旋律轨 → 转换 → 试听前30秒 → 调整轨道、移调或黑键策略 → 保存。\n\n"
            "复杂单轨若试听出现伴奏、乱跳八度或密集和弦，需要另外做主旋律提取，不能只看“转换成功”。",
        )

    def _choose_midi_file(self) -> None:
        path = filedialog.askopenfilename(
            title="选择 MIDI 文件",
            filetypes=[("MIDI 文件", "*.mid *.midi"), ("所有文件", "*.*")],
        )
        if not path:
            return
        self.midi_path_var.set(path)
        self.midi_name_var.set(Path(path).stem)
        self._analyze_selected_midi()

    def _analyze_selected_midi(self) -> None:
        path = self.midi_path_var.get().strip()
        if not path:
            return
        self.midi_status_var.set("正在分析 MIDI 音轨…")
        self.update_idletasks()
        try:
            analysis = analyze_midi(path)
        except Exception as exc:  # noqa: BLE001
            self.midi_analysis = None
            self.midi_status_var.set(f"分析失败：{exc}")
            messagebox.showerror("MIDI 分析失败", str(exc))
            return
        self.midi_analysis = analysis
        self.midi_result = None
        self.midi_tracks.delete(*self.midi_tracks.get_children())
        recommended = set(analysis.recommended_tracks)
        for track in analysis.tracks:
            checked = track.index in recommended
            flags = []
            if track.percussion:
                flags.append("打击乐")
            if checked:
                flags.append("推荐")
            suffix = f"  [{' / '.join(flags)}]" if flags else ""
            self.midi_tracks.insert(
                "",
                "end",
                iid=f"track:{track.index}",
                text=("☑ " if checked else "☐ ") + track.name + suffix,
                values=(track.note_count, track.range_text, track.instrument),
            )
        self.midi_status_var.set(
            f"分析完成：{len(analysis.tracks)} 个音轨 · {analysis.duration_seconds:.1f} 秒 · 约 {analysis.tempo_bpm:.1f} BPM"
        )
        musical_tracks = [track for track in analysis.tracks if track.note_count and not track.percussion]
        if (
            len(musical_tracks) == 1
            and musical_tracks[0].note_count >= 1000
            and musical_tracks[0].min_note is not None
            and musical_tracks[0].max_note is not None
            and musical_tracks[0].max_note - musical_tracks[0].min_note > 48
        ):
            self.midi_status_var.set(
                f"分析完成：复杂单轨钢琴编配 · {musical_tracks[0].note_count} 个音符；建议先查看右上角“使用说明”。"
            )
        self.midi_summary_var.set("双击左侧音轨切换选择，然后点击“转换为21键”。")
        self._render_midi_grid(())

    def _toggle_midi_track(self, _event=None) -> None:
        item = self.midi_tracks.focus()
        if not item:
            return
        text = self.midi_tracks.item(item, "text")
        self.midi_tracks.item(item, text=("☐ " + text[2:] if text.startswith("☑ ") else "☑ " + text[2:]))

    def _selected_midi_tracks(self) -> list[int]:
        result: list[int] = []
        for item in self.midi_tracks.get_children():
            if str(self.midi_tracks.item(item, "text")).startswith("☑ "):
                result.append(int(item.split(":", 1)[1]))
        return result

    def _convert_selected_midi(self) -> None:
        if self.midi_analysis is None:
            messagebox.showwarning("尚未分析", "请先选择一个 MIDI 文件。")
            return
        strategy = "nearest" if self.midi_strategy_var.get() == "最近白键" else "drop"
        transpose_text = self.midi_transpose_var.get().strip()
        try:
            transpose = None if transpose_text == "自动" else int(transpose_text)
        except ValueError:
            messagebox.showerror("移调错误", "移调必须是“自动”或 -48 到 +48 的整数。")
            return
        step = {"1/4 拍": 0.25, "1/8 拍": 0.125, "1/16 拍": 0.0625}[self.midi_quantize_var.get()]
        try:
            result = convert_midi(
                self.midi_analysis.path,
                self._selected_midi_tracks(),
                transpose=transpose,
                black_key_strategy=strategy,
                beat_step=step,
            )
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("MIDI 转换失败", str(exc))
            return
        self.midi_result = result
        stats = result.stats
        self.midi_transpose_var.set(str(result.transpose))
        self.midi_summary_var.set(
            f"{len(result.events)} 个事件 · {stats.source_notes} 个源音符 · 保留 {stats.kept_notes} · "
            f"近似 {stats.approximated_notes} · 丢弃 {stats.dropped_notes} · 越界 {stats.out_of_range_notes} · "
            f"和弦 {stats.chord_count} · 推荐 {result.beat_ms} ms/拍 · 预计 {result.duration_seconds:.1f} 秒"
        )
        complex_result = (
            stats.chord_count > max(30, len(result.events) // 4)
            or stats.out_of_range_notes > max(20, stats.source_notes // 5)
        )
        self.midi_status_var.set(
            "转换完成，但检测到大量和弦或越界音；请试听，必要时另做主旋律提取。"
            if complex_result
            else "转换完成：建议先试听前30秒，确认旋律轨和八度后再保存。"
        )
        self._render_midi_grid(result.events)

    def _render_midi_grid(self, events) -> None:
        canvas = self.midi_canvas
        canvas.delete("all")
        width = max(520, canvas.winfo_width())
        height = max(240, canvas.winfo_height())
        canvas.create_text(16, 14, anchor="nw", text="高音", fill="#8fa6a0", font=("Microsoft YaHei UI", 8))
        canvas.create_text(16, height - 14, anchor="sw", text="低音", fill="#8fa6a0", font=("Microsoft YaHei UI", 8))
        for row in range(3):
            y = 42 + row * ((height - 70) / 2)
            canvas.create_line(48, y, width - 12, y, fill="#29433e")
        event_list = list(events)[:120]
        if not event_list:
            canvas.create_text(width / 2, height / 2, text="转换后将在这里显示21键音符走向", fill="#8fa6a0", font=("Microsoft YaHei UI", 11))
            return
        low_to_high = "zxcvbnmasdfghjqwertyu"
        spacing = max(4.0, (width - 70) / max(1, len(event_list)))
        for index, event in enumerate(event_list):
            x = 55 + index * spacing
            if event.keys == "p":
                canvas.create_line(x, height - 30, x, height - 24, fill="#61746f")
                continue
            for key in event.keys:
                pitch = low_to_high.index(key)
                y = height - 30 - pitch * ((height - 58) / 20)
                canvas.create_oval(x - 2.5, y - 2.5, x + 2.5, y + 2.5, fill="#e1b65f", outline="")
        if len(list(events)) > 120:
            canvas.create_text(width - 12, 12, anchor="ne", text="仅显示前120个事件", fill="#8fa6a0", font=("Microsoft YaHei UI", 8))

    def _preview_midi_result(self) -> None:
        if self.midi_result is None:
            messagebox.showwarning("尚未转换", "请先完成 MIDI 转换。")
            return
        try:
            self.preview.start(list(self.midi_result.events), self.midi_result.beat_ms, max_seconds=30)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("无法试听", str(exc))
            return
        self.midi_status_var.set("正在本地试听前30秒；再次转换或关闭程序可停止。")

    def _save_midi_result(self) -> None:
        if self.midi_result is None:
            messagebox.showwarning("尚未转换", "请先完成 MIDI 转换。")
            return
        name = self.midi_name_var.get().strip().rstrip(". ")
        if not name or any(character in '<>:"/\\|?*' or ord(character) < 32 for character in name):
            messagebox.showerror("名称无效", "歌曲名称不能为空，也不能包含 < > : \" / \\ | ? *。")
            return
        destination = self.songs_dir / f"{name}.txt"
        if destination.exists() and not messagebox.askyesno("覆盖歌曲", f"曲库中已有 {destination.name}，是否覆盖？"):
            return
        source_name = self.midi_analysis.path.name if self.midi_analysis else "MIDI"
        text = format_song_txt(self.midi_result.events, beat_ms=self.midi_result.beat_ms)
        text = text.replace("# 由21键曲谱播放器生成", f"# 由21键曲谱播放器从 {source_name} 转换", 1)
        destination.write_text(text, encoding="utf-8")
        self.library_store.set_song_settings(
            name,
            beat_ms=self.midi_result.beat_ms,
            midi_transpose=self.midi_result.transpose,
            midi_strategy=self.midi_strategy_var.get(),
        )
        self.refresh_songs(select=name)
        self.pages.select(self.library_page)
        self.status_var.set(f"已从 MIDI 生成并载入：{name}")
        messagebox.showinfo("转换完成", f"已保存到个人曲库：\n{destination}")

    def open_song_folder(self) -> None:
        os.startfile(self.songs_dir)  # type: ignore[attr-defined]

    def _beat_ms(self, default: int | None = None) -> int:
        try:
            value = int(float(self.beat_var.get()))
        except ValueError:
            if default is not None:
                return default
            raise ValueError("一拍时间必须是数字。")
        if not 50 <= value <= 5000:
            raise ValueError("一拍时间必须在50到5000毫秒之间。")
        return value

    def _countdown(self) -> int:
        try:
            value = int(float(self.countdown_var.get()))
        except ValueError as exc:
            raise ValueError("倒计时必须是数字。") from exc
        if not 0 <= value <= 10:
            raise ValueError("倒计时必须在0到10秒之间。")
        return value

    def _sequence_delay(self) -> int:
        try:
            value = int(float(self.sequence_delay_var.get()))
        except ValueError as exc:
            raise ValueError("顺序弹琴间隔必须是数字。") from exc
        if not 0 <= value <= 600:
            raise ValueError("顺序弹琴间隔必须在0到600秒之间。")
        return value

    def _foreground_title(self) -> str:
        import ctypes
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buffer = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buffer, length + 1)
        return buffer.value

    def _enumerate_windows(self) -> list[tuple[int, str, int]]:
        user32 = ctypes.windll.user32
        windows: list[tuple[int, str, int]] = []
        callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

        def callback(hwnd, _lparam):
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            title = buffer.value.strip()
            if not title:
                return True
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value != os.getpid():
                windows.append((int(hwnd), title, int(pid.value)))
            return True

        user32.EnumWindows(callback_type(callback), 0)
        return sorted(windows, key=lambda item: item[1].casefold())

    def refresh_windows(self, auto_bind_title: str | None = None) -> None:
        current = self.window_choice_var.get()
        entries = self._enumerate_windows()
        self.window_choices = {
            f"{title}  [PID {pid}]": hwnd for hwnd, title, pid in entries
        }
        values = list(self.window_choices)
        self.window_combo.configure(values=values)
        selected = current if current in self.window_choices else ""
        if auto_bind_title:
            selected = next((label for label in values if label.rsplit("  [PID ", 1)[0] == auto_bind_title), selected)
        if not selected:
            selected = next((label for label in values if "一梦江湖" in label), values[0] if values else "")
        self.window_choice_var.set(selected)
        if auto_bind_title and selected:
            self.bind_selected_window(silent=True)

    def bind_selected_window(self, silent: bool = False) -> None:
        label = self.window_choice_var.get()
        hwnd = self.window_choices.get(label, 0)
        if not hwnd:
            if not silent:
                messagebox.showwarning("无法绑定", "请先刷新并选择一个有效窗口。")
            return
        self.window_backend.bind(hwnd)
        self.background_window_var.set(True)
        self.engine.backend = self.window_backend
        title = label.rsplit("  [PID ", 1)[0]
        self.bound_window_var.set(f"已绑定：{title}")
        if not silent:
            self.status_var.set(f"已绑定后台窗口：{title}")

    def unbind_window(self) -> None:
        if self.engine.running:
            self.status_var.set("请先停止播放，再解绑窗口。")
            return
        self.window_backend.clear()
        self.background_window_var.set(False)
        self.engine.backend = self.foreground_backend
        self.bound_window_var.set("未绑定窗口（按键发送到当前前台窗口）")
        self.status_var.set("已解绑，恢复当前前台窗口发送。")

    def _bound_window_title(self) -> str:
        text = self.bound_window_var.get()
        return text.removeprefix("已绑定：") if text.startswith("已绑定：") else ""

    def _switch_key_backend(self) -> None:
        if self.engine.running:
            self.background_window_var.set(self.engine.backend is self.window_backend)
            self.status_var.set("播放期间不能切换按键发送模式。")
            return
        self.engine.backend = self.window_backend if self.background_window_var.get() else self.foreground_backend
        mode = "绑定窗口后台发送" if self.background_window_var.get() else "当前前台窗口发送"
        self.status_var.set(f"按键模式：{mode}")

    def start_playback(self, *, sequence_start: bool = False) -> None:
        if self._seeking:
            self.status_var.set("正在定位播放位置…")
            return
        if not sequence_start:
            self._cancel_scheduled_sequence()
        if self.engine.running:
            self.engine.resume()
            return
        if (
            not sequence_start
            and not self._has_seek_position
            and self.sequence_enabled_var.get()
            and self.sequence_queue
        ):
            self._play_next_sequence_song()
            return
        if not self.events:
            messagebox.showwarning("没有歌曲", "请先选择或导入有效的TXT琴谱。")
            return
        if self.background_window_var.get():
            self.engine.backend = self.window_backend
            if not self.window_backend.is_bound():
                self.status_var.set("未开始：请先选择并绑定游戏窗口。")
                return
        else:
            self.engine.backend = self.foreground_backend
        if self.guard_var.get() and not self.background_window_var.get():
            expected = self.window_title_var.get().strip()
            if expected and expected.lower() not in self._foreground_title().lower():
                self.status_var.set(f"未开始：前台窗口标题不包含“{expected}”")
                return
        try:
            beat_ms = self._beat_ms()
            countdown = 0 if sequence_start else self._countdown()
            self._sequence_delay()
            self._validate_hotkeys()
            self.save_config()
            started_from = self._playback_start_index
            self.engine.start(
                self.events,
                beat_ms,
                countdown,
                start_index=self._playback_start_index,
            )
            self._has_seek_position = False
            if started_from == 0 and self.song_var.get():
                self.library_store.record_play(self.song_var.get())
                self._update_song_metadata_ui()
                if self.library_filter_var.get() == "最近播放":
                    self._apply_song_filter()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("无法开始", str(exc))

    def pause_playback(self) -> None:
        self.engine.toggle_pause()

    def stop_playback(self) -> None:
        self._cancel_scheduled_sequence()
        self._resume_after_seek = False
        self._seeking = False
        self.engine.stop()
        self._playback_start_index = 0
        self._has_seek_position = False
        self.progress_var.set(0)
        self._update_progress_text(0)
        self.current_var.set("尚未播放")
        self._highlight_keys("")

    def add_current_to_sequence(self) -> None:
        name = self.song_var.get()
        if not name or name not in self.song_paths:
            self.status_var.set("请先选择要加入队列的歌曲。")
            return
        self.sequence_queue.append(name)
        self._render_sequence_queue()
        self.status_var.set(f"已加入顺序队列：{name}")

    def remove_sequence_item(self) -> None:
        selection = self.sequence_list.curselection()
        if not selection:
            return
        del self.sequence_queue[selection[0]]
        self._render_sequence_queue()

    def clear_sequence(self) -> None:
        self.sequence_queue.clear()
        self._cancel_scheduled_sequence()
        self._render_sequence_queue()

    def _render_sequence_queue(self) -> None:
        if not hasattr(self, "sequence_list"):
            return
        self.sequence_list.delete(0, tk.END)
        for index, name in enumerate(self.sequence_queue, 1):
            self.sequence_list.insert(tk.END, f"{index}. {name}")
        self._update_sequence_status()

    def _update_sequence_status(self) -> None:
        if not hasattr(self, "sequence_status_var"):
            return
        try:
            delay = self._sequence_delay()
            delay_text = "立即下一首" if delay == 0 else f"每首结束后等待 {delay} 秒"
        except ValueError:
            delay_text = "间隔秒数无效"
        count = len(self.sequence_queue)
        prefix = "开始将从队列第 1 首播放" if self.sequence_enabled_var.get() and count else "待命"
        self.sequence_status_var.set(f"{count} 首待播 · {prefix} · {delay_text}")

    def _cancel_scheduled_sequence(self) -> None:
        if self._sequence_after_id is not None:
            try:
                self.after_cancel(self._sequence_after_id)
            except tk.TclError:
                pass
            self._sequence_after_id = None

    def _schedule_next_sequence_song(self) -> None:
        if not self.sequence_enabled_var.get() or not self.sequence_queue:
            return
        try:
            delay = self._sequence_delay()
        except ValueError as exc:
            self.status_var.set(str(exc))
            return
        next_name = self.sequence_queue[0]
        if delay:
            self.status_var.set(f"{delay} 秒后顺序播放：{next_name}")
        else:
            self.status_var.set(f"顺序播放：{next_name}")
        self._sequence_after_id = self.after(max(100, delay * 1000), self._play_next_sequence_song)

    def _play_next_sequence_song(self) -> None:
        self._sequence_after_id = None
        if not self.sequence_enabled_var.get() or not self.sequence_queue:
            self._update_sequence_status()
            return
        next_name = self.sequence_queue.pop(0)
        if next_name not in self.song_paths:
            self.status_var.set(f"队列歌曲不存在，已跳过：{next_name}")
            self._render_sequence_queue()
            self._schedule_next_sequence_song()
            return
        self.song_var.set(next_name)
        self._render_song_list(filter_song_names(list(self.song_paths), self.search_var.get()))
        recommended = recommended_beat_ms(next_name)
        if recommended is not None:
            self.beat_var.set(str(recommended))
        self.load_selected_song()
        self._render_sequence_queue()
        self.start_playback(sequence_start=True)

    def _replay_current_song(self) -> None:
        self._sequence_after_id = None
        if self.repeat_one_var.get():
            self.start_playback(sequence_start=True)

    def _validate_hotkeys(self) -> None:
        values = [self.start_key_var.get(), self.stop_key_var.get(), self.pause_key_var.get()]
        if len(set(values)) != 3:
            raise ValueError("开始、停止、暂停必须使用三个不同的热键。")
        if self.record_enabled_var.get():
            self._validate_record_hotkeys()

    def _hotkey_bindings(self) -> dict[str, str]:
        with self._hotkey_lock:
            return dict(self._hotkey_values)

    def _hotkey_action(self, action: str) -> None:
        if action == "start":
            self.start_playback()
        elif action == "stop":
            self.stop_playback()
        elif action == "pause":
            self.pause_playback()

    def _on_progress(self, index: int, total: int, event: SongEvent) -> None:
        if self._seeking:
            return
        self._playback_start_index = index - 1
        elapsed_beats = sum(item.beats for item in self.events[: index - 1])
        total_beats = sum(item.beats for item in self.events)
        percent = elapsed_beats * 100 / total_beats if total_beats else 0
        self.progress_var.set(percent)
        self._update_progress_text(percent)
        self.current_var.set(f"进度 {index}/{total}　按键 {event.keys}　拍数 {event.beats:g}")
        self._highlight_keys("" if event.keys == "p" else event.keys)

    def _event_index_at_percent(self, percent: float) -> int:
        if not self.events:
            return 0
        total_beats = sum(event.beats for event in self.events)
        target_beats = max(0.0, min(100.0, percent)) * total_beats / 100
        offsets: list[float] = []
        elapsed = 0.0
        for event in self.events:
            offsets.append(elapsed)
            elapsed += event.beats
        return min(range(len(offsets)), key=lambda index: abs(offsets[index] - target_beats))

    def _percent_at_event(self, index: int) -> float:
        if not self.events:
            return 0.0
        total_beats = sum(event.beats for event in self.events)
        return sum(event.beats for event in self.events[:index]) * 100 / total_beats

    @staticmethod
    def _format_time(seconds: float) -> str:
        seconds = max(0, int(seconds))
        return f"{seconds // 60}:{seconds % 60:02d}"

    def _update_progress_text(self, percent: float) -> None:
        if not self.events:
            self.progress_text_var.set("0%")
            return
        beat_ms = self._beat_ms(default=700)
        total_seconds = sum(event.beats for event in self.events) * beat_ms / 1000
        current_seconds = total_seconds * max(0.0, min(100.0, percent)) / 100
        self.progress_text_var.set(
            f"{self._format_time(current_seconds)} / {self._format_time(total_seconds)} · {percent:.0f}%"
        )

    def _on_seek_press(self, _event=None) -> None:
        if not self.events:
            return
        self._seeking = True
        self._resume_after_seek = self.engine.running and not self.engine.paused
        self._cancel_scheduled_sequence()
        self.engine.stop()
        self.engine.release_all()

    def _on_seek_changed(self, raw_value: str) -> None:
        if not self._seeking or not self.events:
            return
        percent = float(raw_value)
        self._seek_target_index = self._event_index_at_percent(percent)
        snapped_percent = self._percent_at_event(self._seek_target_index)
        self._update_progress_text(snapped_percent)
        self.current_var.set(f"定位到事件 {self._seek_target_index + 1}/{len(self.events)}")

    def _on_seek_release(self, _event=None) -> None:
        if not self._seeking or not self.events:
            return
        self._seek_target_index = self._event_index_at_percent(self.progress_var.get())
        self._finish_seek_when_stopped()

    def _finish_seek_when_stopped(self) -> None:
        if self.engine.running:
            self.after(20, self._finish_seek_when_stopped)
            return
        self._playback_start_index = self._seek_target_index
        self._has_seek_position = True
        percent = self._percent_at_event(self._playback_start_index)
        self.progress_var.set(percent)
        self._update_progress_text(percent)
        self._seeking = False
        should_resume = self._resume_after_seek
        self._resume_after_seek = False
        self.status_var.set(f"已定位到事件 {self._playback_start_index + 1}")
        if should_resume:
            self.start_playback(sequence_start=True)

    def _highlight_keys(self, keys: str) -> None:
        active = set(keys)
        for key, label in self.keyboard_labels.items():
            label.configure(style="DarkActiveKey.TLabel" if key in active else "DarkKey.TLabel")

    def _on_state(self, state: str, message: str) -> None:
        self.status_var.set(message)
        if hasattr(self, "pause_button"):
            self.pause_button.configure(text="▶ 继续" if state == "paused" else "⏸ 暂停")
            if state in {"countdown", "playing"}:
                self.start_button.state(["disabled"])
                self.pause_button.state(["!disabled"])
                self.stop_button.state(["!disabled"])
            elif state == "paused":
                self.start_button.state(["!disabled"])
                self.pause_button.state(["!disabled"])
                self.stop_button.state(["!disabled"])
            elif state in {"finished", "stopped", "error"}:
                self.start_button.state(["!disabled"])
                self.pause_button.state(["disabled"])
                self.stop_button.state(["disabled"])
                self._highlight_keys("")
        if state == "finished":
            self._playback_start_index = 0
            self._has_seek_position = False
            self.progress_var.set(100)
            self._update_progress_text(100)
            if self.repeat_one_var.get():
                self.status_var.set("单曲循环：即将重新播放")
                self._sequence_after_id = self.after(100, self._replay_current_song)
            else:
                self._schedule_next_sequence_song()

    def _save_with_notice(self) -> None:
        try:
            self._beat_ms()
            self._countdown()
            self._sequence_delay()
            self._validate_hotkeys()
            self.save_config()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("设置错误", str(exc))
            return
        self.status_var.set("设置已保存")

    def on_close(self) -> None:
        self.preview.stop()
        self.hotkeys.stop()
        self.recorder.cancel()
        self.recorder.close()
        self._cancel_scheduled_sequence()
        self.engine.stop()
        try:
            self.save_config()
        except Exception:
            pass
        self.after(80, self.destroy)


if __name__ == "__main__":
    app = JianpuPlayerApp()
    app.mainloop()
