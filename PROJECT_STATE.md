# Project state

更新时间：2026-08-21（UTC+8）

| 项目 | 当前值 |
|---|---|
| 应用版本 | `1.0.0-beta.47` |
| 内置歌曲 | 267 首 |
| 曲库版本 | 184 |
| 自动测试 | 26/26 PASS |
| Windows 当前已核验产物 | `dist/JianpuPlayerNext-v1.0.0-beta.46.exe` |
| Windows 产物大小 | 14,924,412 bytes |
| Windows SHA-256 | `8FA86100D6C3FBB08A9D82FA8E577574346DE1FA582029BF95514DE0586416DE` |
| GitHub 状态 | 未上传；当前禁止创建或更新 Release |

本批新增14首经典候选：《普通DISCO》《达拉崩吧》《勾指起誓》《权御天下》《冠世一战》《神的随波逐流》《LOSER》《撒野》《unravel》《万神纪》《光年之外》《演员》《追梦赤子心》《世间美好与你环环相扣》，均已进入 Windows/Android 曲库，但状态仍为 `requires_in_game_audition`，不得描述为 final。

发布前最后新增《尘外客》中文版本候选，来源为鸣潮先行公约官方 `BV1G48g68Ej1` p1 完整音频；推荐 441 ms/拍，状态 `requires_in_game_audition`。双端对应 `song_240`。

本轮新增《轨迹》《江南》《枫》对应 `song_241`–`song_243`，均来自完整 B 站音频并通过 Basic Pitch、21 键转换、Parser round-trip 与全曲时长覆盖门禁；仍标记 `requires_in_game_audition`，不能称为人工 final。旧的阻塞报告已由实际下载音频和复现报告取代。

爆种批次随后新增《修炼爱情》《可惜没如果》《Megalovania》对应 `song_244`–`song_246`；三首均来自完整 B 站音频，覆盖率约 98.7%–99.6%，Parser/21键门禁通过，仍需游戏内试听。

《须弥》确认为网易《一梦江湖》（原《楚留香》手游）少林门派曲，正式曲库中必须保留。当前对应 Android `song_157`，推荐节拍 511 ms/拍；跨端检查为 240/240，缺失、独有、哈希/资源错误均为 0。

《须弥》继续作为一梦江湖（原《楚留香》手游）少林门派曲保留；当前 Android `song_157` 与 Windows《须弥.txt》一致。

正式 `dist/` 产物已在《尘外客》同步后重建；EXE 源码内嵌 240 个 TXT。

发布脚本执行时读取最新版本与曲库。当前发布状态以本文件及双端 `PUBLISH_HANDOFF.md` 为准。
