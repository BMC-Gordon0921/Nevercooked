# assets/audio — 《欢闹厨房！》音频清单

## 制作方式

| 类别 | 来源 |
|---|---|
| BGM `bgm_canteen_loop.wav` | Soundbox MCP / ACE-Step 1.5 Turbo 生成，100 BPM 无歌词，已切到 52.30 s 无缝循环（接缝跳变 −62 dB） |
| 12 个音效 `sfx_*.wav` | **脚本合成**：`tools/audio/make_sfx.py`（numpy 逐样本），2026-11-16 重写 |

旧版音效由 Stable Audio SFX 一次性生成为 1.0–1.2 s 的持续噪声，在游戏里连续触发听起来就是"静电噪声"，因此全部改由脚本合成：
每个音效 = **包络**（攻击 + 指数衰减）+ **一段滤波噪声**（明确的频带）+ **一到两个有音高的分音**。
工作室类音效刻意做成 0.24–0.58 s 的一次性事件，不再有持续噪音床。

## 文件清单

| 文件名 | 用途 | 时长 | 频谱重心 | RMS | 设计要点 |
|---|---|---|---|---|---|
| `sfx_pickup.wav` | 拿起食材 | 0.18 s | 706 Hz | −20 dB | 短促"嗒"：2.4–5 kHz 噪声瞬态 + 620 Hz 分音 |
| `sfx_place.wav` | 放到台面 | 0.22 s | 259 Hz | −20 dB | 木质闷响：236 Hz + 1.6 倍分音 + 短噪声 |
| `sfx_chop.wav` | 切一刀 | 0.24 s | 257 Hz | −18 dB | 刀口 2.4–7 kHz（4 ms）+ 900–2400 Hz（12 ms）+ 168 Hz 木墩 |
| `sfx_sizzle.wav` | 灶台开始炒 | 0.50 s | 2163 Hz | −20.5 dB | 96 Hz 下锅闷响 + 26 颗不规则油爆颗粒（900–3400 Hz） |
| `sfx_steam.wav` | 蒸笼开始蒸 | 0.50 s | 2272 Hz | −21 dB | 800–3400 Hz 气流 + 220–900 Hz 空气感，7.5 Hz 起伏避免死板 |
| `sfx_oven.wav` | 烤箱点火 | 0.58 s | 405 Hz | −20 dB | 110–900 Hz 呼呼声 + 78 Hz 低频体 + 点火"嗒" |
| `sfx_ready.wav` | **锅里做好了**（新增） | 0.55 s | 1549 Hz | −19 dB | E6 钟声（四段分音），每台设备完成时响一次 |
| `sfx_bell.wav` | 出餐成功 | 0.80 s | 1153 Hz | −17 dB | A5 → E6 两声铃，带 2/3/4 倍分音 |
| `sfx_order.wav` | 新订单 | 0.60 s | 742 Hz | −18 dB | C5 → G5 木琴感两声 |
| `sfx_fail.wav` | 跑单 / 放错 | 0.85 s | 349 Hz | −17 dB | A4 → F4 → D4 下行三音 |
| `sfx_tick.wav` | 最后 30 秒每秒 | 0.09 s | 1299 Hz | −21 dB | 木鱼：1.18 kHz 分音 + 1.6–5 kHz 瞬态 |
| `sfx_trash.wav` | 丢垃圾桶 | 0.45 s | 664 Hz | −20 dB | 110 Hz 闷响 + 786 Hz 金属余响 |

统一规格：**WAV / 44.1 kHz / 16-bit PCM / stereo**。
响度按表内 RMS 逐个归一（峰值 ≤ −1 dBFS，不削波），所以代码里的 `audio.play(name, volume)` 只需要 0.45–0.85 的微调，不用为每个音效找平衡。

## 混音

- BGM 音量 0.20（≈ −30 dB 有效电平），比音效低约 10 dB，只做背景。
- 设备音效 0.45–0.55，操作类 0.65–0.85。
- 每台设备**只在开始加工时**响一次（蒸笼 / 灶台 / 烤箱各自的音色），加工结束由 `sfx_ready` 提示，没有循环噪声。

## 试听

`python tools/audio/preview.py` → `tests/audio_preview.wav`（12 个音效按 0.75 s 间隔顺序播放，14.6 s）。

## 回归

`python tests/audio.py` → 检查代码引用的每个音效都有文件、三台热设备各自触发正确音效、完成提示只响一次。

## 旧文件（未接入游戏，保留备查）

`bgm_8bit_120bpm*.wav`、`bgm_ace_step_test*.wav`、`bgm_from_mcp_score.wav`、`bgm_theme_loop.wav`、`score_demo.json`、`sfx_chop_-1dB.wav` 为早期实验产物。
