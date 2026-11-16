# 乱灶：星港食堂 / Messy Wok: Starport Canteen

可玩 demo v0.1 —— 碗底港第七码头的一人食档口。3 分钟一局，边跑边切边炒。

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
| WASD / 方向键 | 八向移动，160 px/s（斜向已归一，不加速） |
| Shift / 鼠标右键 | 冲刺 0.45 秒（280 px/s），冷却 0.9 秒 |
| F / 鼠标左键 | 一键上下文交互：取料、放料、切、蒸、炒、装盘、出餐、丢 |
| Q | 把手上东西朝面向抛出去（1.5 格，用来隔空甩进设备） |
| Esc | 暂停 / 回标题 |
| Enter | 标题开始、结算再来一局 |

开局会自动关闭系统输入法组词（`stop_text_input`），窗口重新获得焦点时再关一次，所以 Shift 不会被中英文切换吃掉。

## 玩法

左上角是订单票：菜品图标、耐心条（绿→黄→红）、要价与工序提示。走到出餐口按 F 交给客人。耐心归零客人就走，倒计时结束结算。

三道菜：

1. **星尘蛋炒饭**（18 币）：米箱拿星米 → 蒸笼 8 秒 → 取出 → 灶台放进去 → 加星鸡蛋、星尘 → 炒 6 秒 → 取出 → 出餐
2. **陨石肉夹馍**（24 币）：面团箱 → 烤箱 6 秒 → 肉柜拿肉 → 砧板切 → 组装台放烤饼加肉片 → 出餐
3. **氧气沙拉**（20 币）：菜筐 → 砧板切 → 组装台放菜丝加星尘 → 出餐

切菜没有读条：站在砧板前按一下 F 就直接出成品（这一版刻意砍掉，先保节奏）。设备上的东西会**过火**再**糊掉**，糊了只能丢；手上有货时对料箱按 F 无效；任何动作都能被走位打断，物品只会落在手上、台面或地上，**不会消失**。

计分：单笔 = 基础价 × 新鲜度 × 连击倍率 + 小费；净收入再扣糊菜（8/份）与跑单（12/单），灶币 = 净收入 × 0.8。

## 目录

```
main.py            固定 60Hz 主循环、整数缩放、MW_FRAMES 限帧（自测用）
core/              config / text / input / assets / audio / ime
game/entities/     actor（角色）、item、station、base
game/systems/      movement、interaction、cooking、ordering、scoring、render、hud、camera
game/world.py      世界状态与物品唯一持有权、摄像机取景范围
scenes/            title、game、results
data/              tuning / palette / layout / stations / ingredients / dishes
tools/pixel/       pxlib + make_tiles / make_art / make_stations / make_chef（资产生成脚本）
tests/             见下
```

美术全部由 `tools/pixel/` 下的脚本逐像素生成（32 色锁定调色板，见 `data/palette.json`），改完脚本重跑即可覆盖 `assets/art/`。

## 自测

```bash
python tests/reach.py       # 13 台设备面向格交互，0 失败
python tests/chop.py        # 切菜一下完成且不锁人
python tests/smoke.py       # 世界校验、无泄漏
python tests/flow.py        # 真交互跑完一道炒饭并出餐
python tests/items_probe.py # 物品生命周期，leak 0
python tests/full_round.py  # 随机输入跑满 180 秒后进结算
python tests/bot.py         # 脚本玩家跑 180 秒，量吞吐（回归基线）
python tests/film.py        # bot 跑 10 帧存 tests/film/，看镜头与构图
python tests/shots.py       # 标题 / 游戏 / 结算三张截图
```

Linux/CI 上跑测试需要 `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`。

## 这一版还没做

- 灶罐（AI 帮厨）、合作模式、灶币消费与升级
- 音效是脚本合成的 12 个短音（`tools/audio/make_sfx.py`），BGM 1 首，没有语音；试听全部音效用 `tests/audio_preview.wav`
- 其余 9 道菜只有价目，没有工序链
- 只有一间厨房，设备摆位固定，不能自定义
- 没有存档、没有设置菜单、没有手柄
