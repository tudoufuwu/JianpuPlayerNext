# Project state

更新时间：2026-08-20（UTC+8）

| 项目 | 当前值 |
|---|---|
| 应用版本 | `1.0.0-beta.40` |
| 内置歌曲 | 239 首 |
| 曲库版本 | 174 |
| 自动测试 | 26/26 PASS |
| Windows 当前已核验产物 | `dist/JianpuPlayerNext-v1.0.0-beta.40.exe` |
| Windows 产物大小 | 14,850,064 bytes |
| Windows SHA-256 | `6F0FAD6D9C52E8C53D8659E522BCBCFC14AFA0FABE3D1494A860DCDD2B6B8C4C` |
| GitHub 状态 | 未上传；当前禁止创建或更新 Release |

本批新增14首经典候选：《普通DISCO》《达拉崩吧》《勾指起誓》《权御天下》《冠世一战》《神的随波逐流》《LOSER》《撒野》《unravel》《万神纪》《光年之外》《演员》《追梦赤子心》《世间美好与你环环相扣》，均已进入 Windows/Android 曲库，但状态仍为 `requires_in_game_audition`，不得描述为 final。

《须弥》确认为网易《一梦江湖》（原《楚留香》手游）少林门派曲，正式曲库中必须保留。当前对应 Android `song_157`，推荐节拍 511 ms/拍；跨端检查为 239/239，缺失、独有、哈希/资源错误均为 0。

《须弥》继续作为一梦江湖（原《楚留香》手游）少林门派曲保留；当前 Android `song_157` 与 Windows《须弥.txt》一致。

正式 `dist/` 产物已在最后5首同步后重建；EXE 源码内嵌 239 个 TXT。

发布脚本执行时读取最新版本与曲库。当前发布状态以本文件及双端 `PUBLISH_HANDOFF.md` 为准。
