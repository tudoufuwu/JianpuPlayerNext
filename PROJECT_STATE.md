# Project state

更新时间：2026-08-20（UTC+8）

| 项目 | 当前值 |
|---|---|
| 应用版本 | `1.0.0-beta.41` |
| 内置歌曲 | 240 首 |
| 曲库版本 | 175 |
| 自动测试 | 26/26 PASS |
| Windows 当前已核验产物 | `dist/JianpuPlayerNext-v1.0.0-beta.41.exe` |
| Windows 产物大小 | 14,850,457 bytes |
| Windows SHA-256 | `D15F10A339D60BAA98804912E4A8594BE3DA6814D90264DB5C127E3EC3A54C13` |
| GitHub 状态 | 未上传；当前禁止创建或更新 Release |

本批新增14首经典候选：《普通DISCO》《达拉崩吧》《勾指起誓》《权御天下》《冠世一战》《神的随波逐流》《LOSER》《撒野》《unravel》《万神纪》《光年之外》《演员》《追梦赤子心》《世间美好与你环环相扣》，均已进入 Windows/Android 曲库，但状态仍为 `requires_in_game_audition`，不得描述为 final。

发布前最后新增《尘外客》中文版本候选，来源为鸣潮先行公约官方 `BV1G48g68Ej1` p1 完整音频；推荐 441 ms/拍，状态 `requires_in_game_audition`。双端对应 `song_240`。

《须弥》确认为网易《一梦江湖》（原《楚留香》手游）少林门派曲，正式曲库中必须保留。当前对应 Android `song_157`，推荐节拍 511 ms/拍；跨端检查为 240/240，缺失、独有、哈希/资源错误均为 0。

《须弥》继续作为一梦江湖（原《楚留香》手游）少林门派曲保留；当前 Android `song_157` 与 Windows《须弥.txt》一致。

正式 `dist/` 产物已在《尘外客》同步后重建；EXE 源码内嵌 240 个 TXT。

发布脚本执行时读取最新版本与曲库。当前发布状态以本文件及双端 `PUBLISH_HANDOFF.md` 为准。
