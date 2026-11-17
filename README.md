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
| H | 显示 / 隐藏 顶部步骤条 + 每单工序提示（地面箭头由设置开关控制） |
| Tab | 打开设置（音效音量 / 背景音乐音量 / 地面箭头路径开关） |
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
- **手上有货时，台子优先于地上的散件**：站在灶台边、手上端着蒸饭、脚边还躺着一颗鸡蛋，按 F 先把饭放进锅，蛋留到下一次 —— 能收下手上东西的机器永远排在散件前面。
- **F 不会再把手上的原料丢在台子外**：站在台子旁边但没对着它时，F 只会提示"面朝 灶台 再按 F"，东西还在手上；真要放下就走到空地按 F（落在身前一步，看得见也捡得回），或直接 Q 抛出。
- 设备进度条带百分比，忙碌时头顶显示当前动作。

### 引导

- 首局有 4 张新手卡片，按你做的事推进（取料 → 装料 → 取出 → 出餐），空格跳过，H 随时开关。
- **地面粗箭头路径**：从厨师脚下一直铺到目标设备所在格，描边加流动箭头（chevron），目标格四角亮起 L 形括号。路径由 A* 在真实可走格上算出（`game/systems/nav.py`），绕开柱子和设备，不会贴墙穿模。
- **顶部步骤条**：居中一条深色卡片，左边方块是这一步的动词（取 / 送 / 加 / 切 / 等 / 交 / 扔），中间写着“去蒸笼 蒸 星米”，右边是 `1/3` 的进度计数 —— 一局要做几步、现在第几步，一眼可见。
- **订单票会跟着亮**：引导指向的那张票加青色边框和呼吸光晕，下面标“▲ 引导”，其余票自动往下让位，不会弄错该做哪一单。
- **顶部箭头被夹在视口内**：第一排料箱的半身本来会跑到画面上沿之外，现在箭头停在顶栏下面，永远看得见。
- 工序链从 `data/dishes.json` 的 transforms / recipes 反推（`game/systems/guide.py`），改菜谱引导自动跟着变；难度会影响显示哪些辅助：见下。

### 设置

游戏中按 `Tab`（标题页也可以）打开设置，改动**即时生效**并自动写进仓库根目录的 `profile.json`：

| 项 | 作用 |
| --- | --- |
| 音效音量 | 所有一次性音效的总音量（0–100%，调的时候会响一声试听） |
| 背景音乐 | 循环 BGM 音量，独立于音效 |
| 地面箭头路径 | 关掉以后只保留顶部步骤条和目标格括号，不再铺地面路径 |

↑↓ 选行、←→ 调整（音量 ±5%）、Enter / Esc 返回。设置界面会记住上一次的位置，下一局 `on_resume()` 重新读一遍，所以中途改完立刻能感觉到。

### 像素字体

界面上的字全部来自一张现烤的位图字集，不是系统字体缩放。

- `assets/font/pixel12.png`（+ `_bold.png` / `.json`）：32 列 × 122 行、每格 12×12，共 3875 个字形，用系统宋体 12px 关抗锯齿烘出来，所以边缘是硬的 1-bit 像素——不会出现灰边。
- `core/pixelfont.py` 只做整数倍放大：12 / 24 / 36 / 60 / 84px 五档，字距按 1px 补在相邻两个全宽字之间，标题的 wordmark（84px）也是同一套字画的。
- `core/text.py` 的对外接口（`render` / `shadow_text` / `font`）没变，字集里查不到的字自动回退系统 TTF，所以不会出现方块。
- 想换字源或补字：`python tools/font/bake_atlas.py`（`--font noto` 换成思源黑体，`--corpus-only` 只烘代码里真正用到的字）。

### 难度

难度写在 `data/difficulty.json`，标题页三张卡切换：

| 难度 | 耐心 | 出单间隔 | 结算倍率 | 保留的辅助 |
| --- | --- | --- | --- | --- |
| 轻松 | ×1.25 | ×1.25 | ×0.8 | 全部：瞄准格、原因、换手、鼠标点设备、引导 |
| 标准 | ×1.0 | ×1.0 | ×1.0 | 除鼠标点设备外全部 |
| 挑战 | ×0.85 | ×0.8 | ×1.5 | 全关：无瞄准格、无原因、无换手、无引导 |

辅助开关就是 `difficulty.json` 里的 `assists`：`aim` / `reason` / `swap` / `mouse` / `tutorial` / `guide` / `dots` / `loose_aim` / `autoface` / `hold_f`，按难度逐个关。`autoface` 是“按 F 自动转向目标”，`hold_f` 是“按住 F 连做”（取完成品自动接着装料，间隔 0.3 秒），挑战模式两样都没有。

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
  "rows": ["############", "#.re*.v.dm.#", "#....@.....#", "#.SW..BA.OT#", "#....P.....#", "############"]
}
```

- 每行等宽，字符必须在 `legend` 里；房间边框必须是墙，内部 `#` 会变成实心柱子挡路。
- 必须恰好一个 `@`（出生点），至少一台设备。
- 改完直接跑游戏；写错了会在标题页显示红字提示并退回 `data/map_default.json`（不会崩）。
- `python tools/map_preview.py` 生成 `tests/map_preview.png`，换图后先用它检查连通性。
- 完整格式与规则见 `data/map.md`；想换文件就改 `core/config.py` 里的 `MAP_FILE`。
- 自带两张图：默认的「紧凑厨房」（料箱贴着蒸笼，取米到上锅两步路）和老版的「老厨房」（`data/map_classic.json`，料箱在左、设备一字排开）。把 `MAP_FILE` 改成 `"map_classic.json"` 就换回去，两边都跑得通。

### AI 帮厨算法

`game/systems/ai.py` 是一个不需要窗口的 AI：给定 `GameScene`，每帧返回一个 `Intent`，和玩家按的是同一套输入、走的是同一套交互判定（没有任何后门）。

- `Brain(profile)`，档位参数写在 `data/ai.json`：`strong`（全部辅助拉满、两单并行、8 秒蒸制提前开火）与 `relaxed`（一单一看、每步强制停顿、故意不抢单）。
- 规划方式：把每道菜拆成「手能一次拿完」的阶段，按依赖图调度两条流水线，寻路复用 `game/systems/nav.py`（和地面箭头引导同一套 A*）。
- 实测（挑战难度、180 秒、seed 1–5）：`strong` 824 / 827 / 746 / 879 / 758 ★（均值 807，全部 S 级，0 跑单）；`relaxed` 409 / 387 / 366 / 397 / 347 ★（均值 381，落在 A~S）。
- 为什么不是 900+：一局只刷 18 单，每单约 52★，理论上限 937；掉一单就少 55★，而最后一两单总在最后十秒落地。807 已经是一局只跑 18 单的厨房里「几乎全服务」的分数，再往上要靠改菜谱节奏或降低走动成本，不是调参数能挤出来的。
- 跑基准：`python tests/ai.py`（10 轮约 4 秒，不需要窗口）。

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
data/              tuning / palette / stations / ingredients / dishes / ai.json /
                   map.json + map_default.json（厨房地图）/ map_classic.json / difficulty.json
tools/pixel/       pxlib + make_tiles / make_art / make_stations / make_chef（资产生成脚本）
tools/audio/       make_sfx.py 音效合成 + wavio
tools/map_preview.py  地图预览图
tools/font/        bake_atlas.py（把系统宋体 12px 烘成字图集）+ sheet.py（样张）
assets/font/       pixel12.png / pixel12_bold.png / pixel12.json（3875 个字形）
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
python tests/fkey.py        # F 键：不会把原料丢在台子外、手上东西优先给机器、放下落在身前
python tests/items_probe.py # 物品生命周期，leak 0
python tests/full_round.py  # 随机输入跑满 180 秒后进结算
python tests/bot.py         # 脚本玩家跑 180 秒，量吞吐（回归基线）
python tests/film.py        # bot 跑 10 帧存 tests/film/，看镜头与构图
python tests/shots.py       # 标题 / 游戏 / 结算三张截图
python tests/shots2.py      # v0.2 截图：标题难度卡 / 瞄准与引导 / 加工中
python tests/shot_fkey.py   # 截图：F 不会丢在台子外 / 手上有货时机器优先
python tests/path.py        # 引导：阶段/动词/步数、A* 路径连续且每格可走、终点就是目标设备
python tests/settings.py    # 设置：默认值、音量步进与落盘、路径开关、返回上级场景
python tests/font.py        # 像素字体：语料全覆盖、无灰边（1-bit alpha）、整数倍缩放
python tests/ai.py          # AI 帮厨：两档 × 5 seed 跑满一局，打印星级与判决
python tests/shots3.py      # v0.3 截图：地面箭头路径 / 设置页
```

Linux/CI 上跑测试需要 `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`。

## 这一版还没做

- 灶罐（AI 帮厨）已经有算法与基准，但还没接进对局里当你的搭档；合作模式、灶币消费与升级也还没做
- 音效是脚本合成的 12 个短音（`tools/audio/make_sfx.py`），BGM 1 首，没有语音；试听全部音效用 `tests/audio_preview.wav`
- 其余 9 道菜只有价目，没有工序链
- 只有两张内置厨房（可以改 `data/map.json` 自定义，但没有游戏内编辑器）
- 没有多存档（只有 `profile.json` 记最佳成绩与设置）、没有手柄
- 难度只影响节奏、结算与辅助开关，不改菜谱与设备数量
