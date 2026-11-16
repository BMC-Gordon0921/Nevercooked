# 欢闹厨房！ / Nevercooked!

可玩 demo v0.2 —— 碗底港第七码头的一人食档口。3 分钟一局，边跑边切边炒。

> 原名《乱灶：星港食堂》（Messy Wok: Starport Canteen），2026-11 定名《欢闹厨房！》/ Nevercooked!。

仓库：<https://github.com/BMC-Gordon0921/Nevercooked>

## 获取与安装

```bash
git clone https://github.com/BMC-Gordon0921/Nevercooked.git
cd Nevercooked
python -m pip install -r requirements.txt
python main.py
```

Windows 上装好依赖后直接双击 `启动游戏.cmd` 即可。

> HTTPS 连不上 GitHub 的内网/校园网环境，把地址换成 SSH：`git clone git@github.com:BMC-Gordon0921/Nevercooked.git`（先在 GitHub 添加本机公钥）。

## 运行

双击 `启动游戏.cmd`，或者：

```bash
python main.py
```

依赖：Python 3.11+、`pygame-ce` 2.5+（`pip install pygame-ce`）。逻辑分辨率固定 1280×720，按桌面大小自动取整数缩放倍率（像素不会被拉糊）。

## 操作

| 键 | 作用 |
| --- | --- |
| WASD / 方向键 | 八向移动，`data/tuning.json` 里 `speed` = 200 px/s（斜向已归一，不加速） |
| Shift / 鼠标右键 | 冲刺 0.5 秒（340 px/s），冷却 0.9 秒 |
| F / 鼠标左键 | 一键上下文交互：取料、放料、切、蒸、炒、装盘、出餐、丢 |
| Q | 把手上东西朝面向抛出去（1.5 格，扔掉或隔空甩进设备） |
| 空格 | 跳过后面的新手引导卡片 |
| H | 显示 / 隐藏 新手卡 + 每单的路径引导 |
| C | 标题页打开兑换码输入框（直接解锁挑战模式） |
| ← → / 1 2 3 | 标题页选难度（高难度需先解锁） |
| Esc | 暂停 / 回标题 |
| Enter | 标题开始、结算再来一局（沿用当前难度） |

开局会自动关闭系统输入法组词（`stop_text_input`），窗口重新获得焦点时再关一次，所以 Shift 不会被中英文切换吃掉。

## 一局怎么打

标题页先选难度（左右键或 1/2/3），Enter 开锅。左上角是订单票：菜品图标、耐心条（绿→黄→红）、右下剩余秒数、要价与工序提示。走到出餐口按 F 交给客人。耐心归零客人就走，倒计时结束结算。

三道菜：

1. **星尘蛋炒饭**（18 币）：米箱拿星米 → 蒸笼 8 秒 → 取出 → 灶台放进去 → 加星鸡蛋、星尘 → 炒 6 秒 → 取出 → 出餐
2. **陨石肉夹馍**（24 币）：面团箱 → 烤箱 6 秒 → 肉柜拿肉 → 砧板切 → 组装台放烤饼加肉片 → 出餐
3. **氧气沙拉**（20 币）：菜筐 → 砧板切 → 组装台放菜丝加星尘 → 出餐

客人的耐心是 95 / 95 / 80 秒（按菜品，见 `data/dishes.json`），跑单判定要等到耐心只剩一半以下。

### 交互不再卡手（v0.2）

- **瞄准格始终可见**：面前那一格铺青色底、描边与 `F` 键帽；不可用时变冷灰。判定就是这一格，不再"贴边按 F 没反应"。
- **失败有原因**：目标标签下面一行小字会说清"这台机器要先放星米""你手上是烤饼"，而不是只响一声拒绝。
- **手上东西可以直接换**：对另一台设备按 F，能收下的就换过去；空地按 F 放下；仍可 Q 抛出。
- **会吃你手上东西的设备打琥珀 `!`**：省下一趟来回跑。
- **抛出会自动吸附**：扔向设备附近（设备格子外扩 20px）就按同一套规则直接入槽 / 上板 / 开火 / 投料 / 出餐；扔偏了就落在脚边，随时能捡回来。
- 设备进度条带百分比，忙碌时头顶显示当前动作。

### 引导

- 首局有 4 张新手卡片，按你做的事推进（取料 → 装料 → 取出 → 出餐），空格跳过，H 随时开关。
- 纸条之外还有**下一步提示**：底部左侧写着"下一步 · 去蒸笼 取出 星米饭"，目标设备上打青色脉冲环和箭头。工序链是从 `data/dishes.json` 的 transforms / recipes 反推的，改菜谱引导自动跟着变。
- 难度会影响辅助量：见下。

### 难度

难度写在 `data/difficulty.json`，标题页三张卡切换：

| 难度 | 耐心 | 出单间隔 | 结算倍率 | 保留的辅助 |
| --- | --- | --- | --- | --- |
| 轻松 | ×1.25 | ×1.25 | ×0.8 | 全部：瞄准格、原因、换手、鼠标点设备、引导 |
| 标准 | ×1.0 | ×1.0 | ×1.0 | 除鼠标点设备外全部 |
| 挑战 | ×0.85 | ×0.8 | ×1.5 | 全关：无瞄准格、无原因、无换手、无引导 |

辅助开关就是 `difficulty.json` 里的 `assists`：`aim` / `reason` / `swap` / `mouse` / `tutorial` / `guide` / `dots`，按难度逐个关。

**挑战模式解锁**：在轻松或标准难度打出 S 评级（★ ≥ 420）后自动开放；结果页会提示，档案存在仓库根目录的 `profile.json`（记录各难度最佳星数、总局数、已解锁难度）。

**兑换码**：标题页按 `C` 打开输入框，输入下面任一兑换码回车，直接解锁挑战模式（不区分大小写；输错会提示重试，Esc 取消）：

| 兑换码 | 效果 |
| --- | --- |
| `XINGGANG` | 解锁挑战模式 |
| `NEVERCOOKED` | 解锁挑战模式 |

兑换码配在 `data/difficulty.json` 的 `codes` 里（键 = 兑换码，值 = 要解锁的难度 id），增删随你；兑换结果同样写进 `profile.json`，解一次永久有效。

### 地图自定义

地图是一张 ASCII 图，写在 `data/map.json`：

```json
{
  "name": "碗底港 · 第七码头",
  "tile": 64,
  "origin": [96, 160],
  "legend": { "#": {"kind": "wall"}, ".": {"kind": "floor"}, "@": {"kind": "spawn"},
              "r": {"kind": "crate", "item": "rice"}, "S": {"kind": "station", "station": "steamer"} },
  "rows": ["############", "#re*.dmvS..#", "#....@.....#", "#B.W.O.A.T.#", "#...P......#", "############"]
}
```

- 每行等宽，字符必须在 `legend` 里；房间边框必须是墙，内部 `#` 会变成实心柱子挡路。
- 必须恰好一个 `@`（出生点），至少一台设备。
- 改完直接跑游戏；写错了会在标题页显示红字提示并退回 `data/map_default.json`（不会崩）。
- `python tools/map_preview.py` 生成 `tests/map_preview.png`，换图后先用它检查连通性。
- 完整格式与规则见 `data/map.md`；想换文件就改 `core/config.py` 里的 `MAP_FILE`。

## 计分

单笔 = 基础价 × 新鲜度 × 连击倍率 + 小费，再乘难度结算倍率；净收入再扣糊菜（8/份）与跑单（12/单），灶币 = 净收入 × 0.8，评级按净收入（S ≥ 420 / A ≥ 260 / B ≥ 130 / 其余 C）。

## 目录

```
main.py            固定 60Hz 主循环、整数缩放、MW_FRAMES 限帧（自测用）
core/              config / text / input / assets / audio / ime / mapfile / profile
game/entities/     actor（角色）、item、station、base
game/systems/      movement、interaction、throwing、cooking、ordering、scoring、
                   difficulty、guide、tutorial、render、hud、camera
game/world.py      世界状态与物品唯一持有权、摄像机取景范围
scenes/            title（难度选择）、game、results
data/              tuning / palette / stations / ingredients / dishes /
                   map.json + map_default.json（厨房地图）/ difficulty.json
tools/pixel/       pxlib + make_tiles / make_art / make_stations / make_chef（资产生成脚本）
tools/audio/       make_sfx.py 音效合成 + wavio
tools/map_preview.py  地图预览图
tests/             见下
```

美术全部由 `tools/pixel/` 下的脚本逐像素生成（32 色锁定调色板，见 `data/palette.json`），改完脚本重跑即可覆盖 `assets/art/`。

## 自测

```bash
python tests/reach.py       # 13 台设备面向格交互：硬核逐格 + 标准相邻，0 失败
python tests/chop.py        # 切菜一下完成且不锁人
python tests/smoke.py       # 世界校验、无泄漏
python tests/flow.py        # 真交互跑完一道炒饭并出餐
python tests/throw.py       # 抛出：吸附进设备 / 被拒落地 / 捡回 / 校验
python tests/map.py         # 地图解析、坏图报错、内外一致性
python tests/audio.py       # 每个被引用的音效都有文件、设备音效对位、完成提示只响一次
python tests/code.py        # 兑换码：文字输入/退格、解锁挑战、错误码、Esc 取消
python tests/items_probe.py # 物品生命周期，leak 0
python tests/full_round.py  # 随机输入跑满 180 秒后进结算
python tests/bot.py         # 脚本玩家跑 180 秒，量吞吐（回归基线）
python tests/film.py        # bot 跑 10 帧存 tests/film/，看镜头与构图
python tests/shots.py       # 标题 / 游戏 / 结算三张截图
python tests/shots2.py      # v0.2 截图：标题难度卡 / 瞄准与引导 / 加工中
```

Linux/CI 上跑测试需要 `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`。

## 这一版还没做

- 灶罐（AI 帮厨）、合作模式、灶币消费与升级
- 音效是脚本合成的 12 个短音（`tools/audio/make_sfx.py`），BGM 1 首，没有语音；试听全部音效用 `tests/audio_preview.wav`
- 其余 9 道菜只有价目，没有工序链
- 只有一间默认厨房（可以改 `data/map.json` 自定义，但没有游戏内编辑器）
- 没有存档（只有 `profile.json` 记最佳成绩）、没有设置菜单、没有手柄
- 难度只影响节奏、结算与辅助开关，不改菜谱与设备数量
