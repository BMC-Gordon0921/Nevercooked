# 自定义地图

厨房的地图就是 `data/map.json` 里的一幅字符画。改字符画 = 改地图，不需要动代码。

```json
{
  "name": "第七码头 · 紧凑厨房",
  "tile": 64,                      // 每格像素（改这个会连带改变整间厨房的尺寸）
  "origin": [96, 160],             // 房间左上角在世界里的位置
  "legend": {
    "#": { "kind": "wall" },
    ".": { "kind": "floor" },
    "@": { "kind": "spawn" },
    "r": { "kind": "crate", "item": "rice", "label": "星米箱" },
    "S": { "kind": "station", "type": "steamer", "label": "蒸笼" }
  },
  "rows": [
    "########",
    "#r..S..#",
    "#...@..#",
    "########"
  ]
}
```

## 规则

- 每一行字符数必须相同，行数 × 列数就是房间大小。
- `legend` 每个键是一个字符，值必须带 `kind`：
  - `wall`——墙。在边界上会被画成墙；房间内部写 `#` 会变成一根柱子/隔断（实心，走不过去）。
  - `floor`——空地。
  - `spawn`——出生点，必须有且只有一个。
  - `crate`——料箱，必须给 `item`（取值见 `data/ingredients.json`），`label` 可选。
  - `station`——设备，必须给 `type`（`steamer` / `wok` / `oven` / `board` / `assemble` / `serve` / `trash`），`label` 可选。
- 出现 legend 里没有的字符、行宽不一致、没有出生点、没有设备，都会报错并**回退到 `data/map_default.json`**；错误信息在启动时打印，标题页左上角也会显示一行红字。
- 设备必须靠墙或至少留出一条能走的路：地图加载时只检查形状，不检查可达性。改完建议跑一次 `python tools/map_preview.py`，它会生成 `tests/map_preview.png`，一眼就能看出路通不通。

## 已有地图

| 文件 | 用途 |
| --- | --- |
| `data/map.json` | 当前生效的地图（随便改） |
| `data/map_default.json` | 出厂地图，出错时的兜底；建议别改 |
| `data/map_classic.json` | 老版厨房（料箱在左、设备一字排开），想换回去时用 |

## 换一张图

最简单：复制 `data/map_default.json` 到 `data/map.json`，在 `rows` 里重新画一遍，然后运行游戏。

想换回老厨房：把 `core/config.py` 里 `MAP_FILE = "map.json"` 改成 `"map_classic.json"`。想同时保留两张图，就把旧图另存成 `data/map_alt.json`，再按同样办法切换。

两张内置厨房的差别只有走位成本：紧凑厨房里米箱贴着蒸笼（取米两步、上锅一步），老厨房是料箱一排、设备一排，跑一趟要横穿厨房。
