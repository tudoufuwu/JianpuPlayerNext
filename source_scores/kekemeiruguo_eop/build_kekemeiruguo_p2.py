"""可惜没如果 第2页 (m21-44) 构建脚本 —— 断点续跑版，逐系统补充，每步闭合断言。

来源: source_scores/kekemeiruguo_eop/原谱_p2.png
已完成系统: m21-24 (k2_top + k21b 精读)
待补: m25-28 (k25_a/b 半读), m29-32, m33-36, m37-40, m41-44
运行: python build_kekemeiruguo_p2.py  → 全部闭合则打印 OK
"""

from __future__ import annotations


def n(text: str, durations: list[float]):
    keys = list(text)
    assert len(keys) == len(durations), (text, keys, durations)
    return list(zip(keys, durations))


MELODY = {
    # m21: 3gray(链2.0含dash) + 3 23 3gray(合并0.75) 1 7
    21: [("e", 1.0), ("e", 1.0), ("d", 0.5), ("s", 0.25), ("e", 0.75), ("q", 0.25), ("j", 0.25)],
    # m22: 5̇5̇·(gray链) + 3 23 3gray 76  [低置信: 5̇附点读法]
    22: [("t", 0.75), ("t", 0.25), ("t", 1.0), ("e", 0.5), ("s", 0.25), ("e", 0.25), ("e", 0.5), ("y", 0.25), ("y", 0.25)],
    # m23: [y+q]1.5 dyad + 5(1.0) + 4 3 3gray(tie) + 44
    23: [("yq", 1.5), ("t", 1.0), ("r", 0.25), ("e", 0.25), ("e", 0.5), ("r", 0.25), ("r", 0.25)],
    # m24: 43gray(链) 3· 0 3 23 3gray(合并) 76
    24: [("r", 0.75), ("e", 0.75), ("p", 0.5), ("e", 0.5), ("s", 0.25), ("e", 0.75), ("y", 0.25), ("y", 0.25)],
    # m25: 6gray(链自m24尾y.25) 6 5 43 3gray(tie) 45 5gray(弧=slur非tie)
    25: [("y", 1.0), ("y", 0.5), ("t", 0.5), ("r", 0.25), ("e", 0.25), ("e", 0.5), ("r", 0.25), ("t", 0.25), ("t", 0.5)],
    # m26: 5gray(链自m25末t.5, 共2.5) 3 3(弧tie→m27)
    26: [("t", 2.0), ("e", 1.0), ("e", 1.0)],
    # m27: [ḯ2̣ 3̲]型×4: 12 3 23 3gray 12 3 24 4gray (首弧=slur非tie, 低置信)
    27: n("qs", [0.25, 0.25]) + [("e", 0.5)] + n("se", [0.25, 0.25]) + [("e", 0.5)]
        + n("qs", [0.25, 0.25]) + [("e", 0.5)] + n("sr", [0.25, 0.25]) + [("t", 0.5)],
    # m28: 3 - 3 - (长音收尾, 尾音弧tie→m29 gray3)
    28: [("e", 2.0), ("e", 2.0)],
    # m29: 3gray(链自m28末e2.0) + 3 23 3gray 1 7
    29: [("e", 2.0), ("d", 0.5), ("s", 0.25), ("e", 0.25), ("e", 0.5), ("q", 0.25), ("j", 0.25)],
    # m30: 75 5 5gray + 3 23 3gray 76
    30: [("j", 0.5), ("t", 0.5), ("t", 1.0), ("e", 0.5), ("s", 0.25), ("e", 0.75), ("y", 0.25), ("y", 0.25)],
    # m31: 6 6 6gray + 5 33 3 44  [低置信: 33 3 细分]
    31: [("y", 0.5), ("y", 0.5), ("y", 1.0), ("g", 0.5), ("e", 0.25), ("e", 0.25), ("e", 0.5), ("r", 0.25), ("r", 0.25)],
    # m32: 43gray(链自m31末r.25→0.75) 3· 3 + 5 4 3 7 (中音下行)
    32: [("r", 0.75), ("e", 0.75), ("e", 0.5), ("g", 0.5), ("f", 0.5), ("d", 0.5), ("j", 0.5)],
}

ACCOMP29 = {
    29: n("agadg", [0.5, 0.25, 0.25, 0.5, 0.5]) * 2,
    30: n("jgjdg", [0.5, 0.25, 0.25, 0.5, 0.5]) * 2,   # 低置信: 7/57 八度
    31: n("yqydy", [0.5, 0.25, 0.25, 0.5, 0.5]) * 2,
    32: n("ggjdj", [0.5, 0.25, 0.25, 0.5, 0.5]) * 2,
}


def close(measures: dict, label: str) -> None:
    bad = []
    for m, events in sorted(measures.items()):
        total = sum(d for _, d in events)
        if abs(total - 4.0) > 1e-9:
            bad.append(f"m{m}={total}")
    if bad:
        raise AssertionError(f"{label} 不闭合: {', '.join(bad)}")
    print(f"{label}: {len(measures)} 小节全部闭合 4.0 ✓ ({sorted(measures)[0]}-{sorted(measures)[-1]})")


if __name__ == "__main__":
    close(MELODY, "p2-melody")
    close(ACCOMP29, "p2-accomp29")
