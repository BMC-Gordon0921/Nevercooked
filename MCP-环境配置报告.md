# MCP 环境配置与验证报告

生成时间：2026-11-15 22:50（Asia/Shanghai）
项目：`D:\ECNU\计算机导论\Final-Game`（Pygame 2D 斜俯视像素游戏《乱灶：星港食堂》）
用途：课程期末作业的美术 / 音频资产生产线（Aseprite 实时作图、8-bit 音乐、AI 音效与配乐）

---

## 一、结论摘要

| MCP | 状态 | 用途 | 本次实测产物 |
|---|---|---|---|
| **Aseprite MCP** | ✅ **实时模式可用**（非 Headless） | 直接驱动 Aseprite 画布：建组/建图层/画像素/读像素/导出 PNG/动画帧 | 在真实画布上新建图层 `MCP Verify` 并绘制 40×40 矩形，revision 2→4 |
| **Soundbox MCP** | ✅ **可用**（含 2 个本地模型） | 本地 AI 音效 + 音乐生成，全离线、走 GPU | 生成菜刀切砧板音效、ACE-Step 配乐各 1 个 |
| **8-bits-music MCP** | ⚠️ **工具可调用，但导出是假的** | 8-bit 旋律/节奏/和弦的**参数生成** | 能返回音符与 trackId，但**不会真正写出 WAV**（见第六节） |

> 一句话：**美术（Aseprite）和音效/配乐（Soundbox）两条线已打通并有真实产物**；8-bits-music 只能当"乐谱参数生成器"用，音频文件需要另配渲染方案（已附替代方案与自制脚本）。

---

## 二、已安装清单

| 组件 | 版本 | 位置 | 说明 |
|---|---|---|---|
| Python（uv 托管） | 3.13.13 | `C:\Users\17038\AppData\Roaming\uv\python\cpython-3.13.13-windows-x86_64-none\` | 系统 Python 是 3.14.6，aseprite-mcp 要求 ≥3.13 且部分依赖在 3.14 上不稳，故用 3.13 |
| uv / uvx | 0.11.20 | `C:\Users\17038\AppData\Local\Microsoft\WinGet\Links\uv.exe` | 已存在，无需 winget 安装 |
| Node / npm | 24.16.0 / 11.13.0 | `C:\Program Files\nodejs\` | npx 可用 |
| Aseprite | 1.3.18.6-dev | `D:\Program Files\Aseprite\aseprite.exe` | 你手动编译的版本；API 41，满足扩展要求的 ≥28 |
| **aseprite-mcp** | 0.6.0（MIT） | `_sb\venv-aseprite\`（独立 venv） | PyPI 包 + **本地补丁**（见第五节问题 1） |
| **Aseprite 扩展** | 0.6.0 | `C:\Users\17038\AppData\Roaming\Aseprite\extensions\aseprite-mcp-live\` | 官方 release **没有** .aseprite-extension 附件，改为从 sdist 里的 `extension/` 自行打包安装 |
| **8-bits-music-mcp** | 1.0.6（npm 全局） | `C:\Users\17038\AppData\Roaming\npm\node_modules\8-bits-music-mcp\` | 服务端自报版本 1.0.2（包内版本号未同步） |
| **Soundbox** | 0.4.1（MIT） | `D:\Program Files\Soundbox\soundbox-desktop.exe` | 原默认装 C 盘，已按要求卸载重装到 D 盘 |
| Soundbox 数据目录 | — | `D:\AI\Soundbox` | 由用户环境变量 `SOUNDBOX_DATA_DIR` 指定；含 `models\`、`sounds\`、`soundbox.db` |
| **audio.cpp 引擎** | v0.9.5（CUDA 13.3） | `D:\AI\Soundbox\audiocpp\audiocpp_cli.exe` | 官方安装器因 GitHub 403 失败，改为手动部署二进制；由 `SOUNDBOX_AUDIOCPP_BIN` 指向 |
| 模型 1 | Stable Audio 3.0 SFX（q8_0 GGUF） | `D:\AI\Soundbox\models\audiocpp\Stable-Audio-3-Small-SFX-GGUF\` | 1,683,576,512 B，sha256 `bfe435d2c5841868a7025433929ee250e51e491be369a279f341221539c71841` ✅ 与官方一致 |
| 模型 2 | ACE-Step 1.5 Turbo（q8_0 GGUF） | `D:\AI\Soundbox\models\audiocpp\ACE-Step1.5-GGUF\turbo\` | 6,185,468,096 B，sha256 `1f0015f81c10a1182531e6207c7aeaa060b8cad3470a2f88daa3cb74ed636e63` ✅ 与官方一致 |

**未安装（按要求排除）**：`MiniMax Music 3`（约 9.8 GB 显存需求，8 GB 的 5060 Laptop 会爆）。

### DSH 侧注册的三个 MCP 服务
写入 `C:\Users\17038\.dsh\profiles\desktop\cordis.patch.yml` 的 `- insert:` 块（原有 blender、godot 两条，现共 5 条）：

| 服务名 | 传输 | 关键参数 |
|---|---|---|
| `mcp-aseprite` | stdio | `venv-aseprite\Scripts\python.exe -m aseprite_mcp --shared`；`ASEPRITE_MCP_TOOL_PROFILE=core`、`ASEPRITE_MCP_CAPABILITY_SETS=animation`、`ASEPRITE_PATH=D:/Program Files/Aseprite/aseprite.exe` |
| `mcp-8bit-music` | stdio | `node ...\8-bits-music-mcp\packages\mcp-server\dist\server.js` |
| `mcp-soundbox` | streamable-http | `http://127.0.0.1:17494/mcp`，`toolCallTimeoutMs=300001` |

---

## 三、实测验证（全部为真实动作，不是"能启动"）

| 验证项 | 操作 | 结果 |
|---|---|---|
| Aseprite 连接 | 调 `get_connection_status` | `connected:true`，扩展 0.6.0，Aseprite 1.3.18.6-dev，api 41，`ws://127.0.0.1:8765` |
| Aseprite 读画布 | `list_documents` | 读到 64×64 RGB 文档，路径 `_sb\mcp-test.png`，图层 `l1 Layer` + `l2 MCP D-Drive Test` |
| Aseprite 写画布 | `apply_operations`（create_layer + rectangle） | `ok:true`，新建 `l3 MCP Verify`，绘制 40×40 矩形，revision 2→4 |
| Aseprite 工具数 | tools/list | **11 个**（含 `apply_animation`，因启用了 animation 能力集） |
| Soundbox 端点 | MCP initialize | `serverInfo {name:"soundbox", version:"0.4.1"}`，**24 个工具** |
| Soundbox 引擎 | `GET /api/models/audiocpp/runtime` | `{"installed":true,"backend":"cuda","source":"env"}` |
| 模型识别 | `GET /api/models` | `audiocpp-stable-audio-3-sfx: installed`、`audiocpp-ace-step: installed` |
| **音效生成** | `soundbox.generate`（Stable Audio 3 SFX） | 1.56 s / 44.1 kHz / 立体声，耗时 3.13 s |
| **音乐生成** | `soundbox.generate`（ACE-Step 1.5 Turbo） | 9.13 s / 48 kHz / 立体声，`peaks` 非空 |
| 8-bit 音乐 | `create_8bit_melody` / `create_8bit_rhythm` | 返回 trackId 与音符，但**导出无文件**（见第六节） |

### 生成的资产（响度用 dBFS 量，已核对格式）

| 文件 | 格式 / 时长 | 峰值 / RMS | 来源 |
|---|---|---|---|
| `assets\audio\sfx_chop.wav` | 24-bit / 44.1 kHz 立体声 / 1.56 s / 414,068 B | −0.10 / −26.77 dBFS | Soundbox + Stable Audio 3.0 SFX |
| `assets\audio\bgm_ace_step_test.wav` | 24-bit / 48 kHz 立体声 / 9.13 s / 2,628,122 B | −4.02 / −16.84 dBFS | Soundbox + ACE-Step 1.5 Turbo |
| `assets\audio\bgm_8bit_120bpm.wav` | 16-bit / 44.1 kHz 单声道 / 16.00 s / 1,411,200 B | −0.72 / −9.84 dBFS | `_sb\make_8bit_bgm.py`（方波+三角波+噪声） |
| `assets\audio\bgm_from_mcp_score.wav` | 16-bit / 44.1 kHz 单声道 / 5.60 s | −12.96 / −14.00 dBFS | `_sb\render_score.py` 渲染 MCP 返回的谱子 |
| `assets\audio\score_demo.json` | JSON 谱子 | — | `8-bits-music-mcp` 的 `create_8bit_melody` 原样返回 |

**归一化版本**（峰值统一到 −1 dBFS、转 16-bit，供 Pygame 直接加载试听）：

| 文件 | 增益 | 结果 |
|---|---|---|
| `assets\audio\sfx_chop_-1dB.wav` | −0.90 dB | −1.00 dBFS 峰值 / −27.67 RMS |
| `assets\audio\bgm_ace_step_test_-1dB.wav` | **+3.02 dB** | −1.00 dBFS 峰值 / −13.82 RMS |
| `assets\audio\bgm_8bit_120bpm_-1dB.wav` | −0.28 dB | −1.00 dBFS 峰值 / −10.12 RMS |

> ⚠️ **修正一处早前的误判**：我第一版报告里写"ACE 与音效峰值 100%、有削波"，那是把 audio.cpp 输出的 **24-bit** PCM 当 16-bit 解析造成的假象。真实峰值是 −4.02 / −0.10 dBFS，**并没有削波**。也因此才有了 `_sb\normalize_wav.py`（支持 8/16/24/32-bit 读取、统一输出 16-bit）——Pygame / SDL_mixer 对 24-bit 支持不稳，进游戏前必须转 16-bit。

---

## 四、需要人工知道的操作顺序

1. **Aseprite 必须先启动**，它的 Lua 扩展是 WebSocket 客户端，主动连 `127.0.0.1:8765`；Aseprite 没开时 MCP 工具会一直 `connected:false`。
2. **Soundbox 必须先启动**，MCP 端点随应用进程存在（`127.0.0.1:17494/mcp`）。
3. DSH 侧的服务列表在**启动时**建立会话；如果 Soundbox 期间重启过（本次就发生了），DSH 会拿着失效的 session id 报 `no valid session ID provided`。解决办法：改一下 `cordis.patch.yml` 里该条目的任意参数（本报告用的就是 `toolCallTimeoutMs` 300000→300001）触发重载，或重启 DSH Desktop。**本次已用前者修复，现在面板里的 soundbox 工具可直接用。**
4. 改完配置后可以用 `python -c "import yaml;yaml.safe_load(open(...))"` 先验 YAML 再重启，避免整个配置解析失败。

---

## 五、踩过的坑与解法（可复用）

| # | 现象 | 根因 | 解决 |
|---|---|---|---|
| 1 | aseprite-mcp 一握手就静默断开（rc=0、无输出） | 0.6.0 把裸 `JSONRPCMessage` 塞进 MCP SDK 流，mcp≥1.8 需要 `SessionMessage`，报 `AttributeError: 'JSONRPCMessage' object has no attribute 'message'` | 降级 mcp 到 1.7.1 会撞 pydantic 2.14 的 `eval_type_backport` 缺失，行不通；改为**在 `shared.py` 里双向适配**（入站包 `SessionMessage`、出站取 `.message`），保留 mcp 1.30.0 |
| 2 | `Shared configuration mismatch` | 客户端与服务端各自算 `configuration_id`（sha256），`ASEPRITE_PATH` 必须**逐字节一致**；YAML 里写 `'D:\\Program Files\\...'` 单引号不转义，实际值是**双反斜杠** | 配置改成正斜杠 `D:/Program Files/Aseprite/aseprite.exe`，与探针保持一致 |
| 3 | 服务端明明起来了却报配置不一致 | venv 的 `python.exe` 是 uv trampoline，`sys.executable` 指向 uv 托管的 3.13，派生的后台服务会 import **未打补丁的** 包 | 用 `StartsWithOpen` 定位 8765 监听者，按命令行含 `aseprite_mcp` 且 `Name -like python*` 精确清理；**不要**用 PowerShell 通配 `*aseprite_mcp*` 杀进程，会误杀 DSH 的 shell runner（曾导致 `SUBPROCESS_RUNNER_FAILED`） |
| 4 | 官方没有 `.aseprite-extension` 可下 | release 只挂 sdist，`releases/expanded_assets/0.6.0` 为空 | 从 sdist 的 `extension/` 目录自行打包成 zip，解包到 `%APPDATA%\Aseprite\extensions\` |
| 5 | `huggingface.co` 完全不可达（curl 返回 000） | 本机网络对 HF 域名封锁 | 走 `hf-mirror.com`；`raw.githubusercontent.com` 走 `cdn.jsdelivr.net/gh/...`；GitHub 直链走 `ghfast.top` 前缀 |
| 6 | audio.cpp 引擎装不上 | 二进制里**硬编码** `huggingface.co`，不认 `HF_ENDPOINT`；安装器查 GitHub release 又被 403 | 手动下载 v0.9.5 的 `bin-windows-x64-cuda13.3` + `cudart` 两个 zip，解压后设 `SOUNDBOX_AUDIOCPP_BIN` |
| 7 | 模型放 C 盘 | 默认数据目录是 `%USERPROFILE%\.soundbox` | 卸载 → `/S /D=D:\Program Files\Soundbox` 静默重装 → `SOUNDBOX_DATA_DIR=D:\AI\Soundbox` |

> 说明：第 1、3 条的调试过程中，我在 `venv-aseprite\Lib\site-packages\aseprite_mcp\shared.py` 临时加过日志与错误串注入，**已在收尾时全部清除**，现在文件里只剩 `SessionMessage` 兼容补丁（语法校验通过，清理后功能复测正常）。

---

## 六、三条与原方案的偏差（如实说明）

### 1. `ASEPRITE_MCP_BACKEND=headless` 这个变量不存在
原计划里写的回退方式是设 `ASEPRITE_MCP_BACKEND="headless"` + `ASEPRITE_PATH`。实测该包 README 与源码里**没有任何 `BACKEND` 环境变量**。真正的回退开关是：

```yaml
ASEPRITE_MCP_TOOL_PROFILE: cli     # 116 个磁盘文件工具，完全不建实时 WebSocket 连接
```

`core`（默认，10 个实时工具）/ `all` / `cli` 才是实际的三档。**当前实时模式已打通，不需要回退**，但这条要写进你的技术文档，避免以后按错误变量名排查。

### 2. Soundbox 的 MCP 不是 npm 包
`npm view soundbox-mcp` / `@soundbox/mcp` / `ace-step-mcp` / `stable-audio-mcp` **全部 404**（npm 上那个 `soundbox@0.1.0` 是同名的 Web Audio 播放库，无关）。Soundbox 是 Tauri 桌面应用，MCP 端点是应用**内置**的 `http://127.0.0.1:17494/mcp`（streamable-http），所以它必须在 DSH 之前启动。

### 3. `8-bits-music-mcp` 的导出是桩代码（重要）
不是"配置没对"，是包本身没实现音频渲染。证据在 `node_modules\@zwitterkaneda\8bits-music-audio-engine\dist\exporters\WAVExporter.js`：

```js
static async export(tracks, outputPath) {
    await new Promise(resolve => setTimeout(resolve, 1000));   // 睡 1 秒
    return { success: true, outputPath,
             message: `WAV file exported successfully to ${outputPath}`,
             fileSize: 1024 * 1024 };                          // 写死的大小，磁盘上没有文件
}
```

`MIDIExporter.js` 同理（`fileSize: 1024 * 5`）。所以：
- ✅ 可以用它做**乐谱层**：`create_8bit_melody` 返回音符数组与 BPM、`generate_chord_progression` 返回和弦走向、`create_8bit_rhythm` 返回节奏型；
- ❌ **不要**指望 `export_audio_composition` 产出 wav/midi，它只会打印一句"导出成功"。

**替代方案（按推荐度）**：
1. **自己渲染（已落地）**：`_sb\make_8bit_bgm.py`，纯 stdlib，方波+三角波+噪声，120 BPM、8 小节、16 s，已产出 `assets\audio\bgm_8bit_120bpm.wav`。要什么调式/速度直接改数组，可控性最高，**零依赖、可进版本库**。
2. **jsfxr / sfxr**：`jsfxr` 为 UNLICENSE（公有领域），适合做**音效**（跳跃、翻锅、收银），不适合长 BGM。
3. **用 Soundbox 出 chiptune 风**：本次 `bgm_ace_step_test.wav` 就是"chiptune-ish"提示词的产物，适合做**成品感**配乐，但每次都要过 GPU、且不完全"8-bit 纯正交波形"。
4. **换 MCP**：目前没找到成熟的"8-bit 渲染"类 MCP，不建议再花时间。

---

## 七、8-bit 的两层：乐谱接口 vs 渲染脚本

`8-bits-music-mcp` 只做**乐谱层**，声音要靠**渲染层**，两者可以串起来用：

| | 乐谱接口（MCP 工具） | 渲染脚本（`_sb\make_8bit_bgm.py` / `render_score.py`） |
|---|---|---|
| 本质 | 参数计算器：把"音符 + 时值 + BPM"整理成结构化 JSON | 合成器 + 混音 + 写盘：真正产生声波 |
| 输入 | 音符数组、时值、BPM、波形名 | 同一份 JSON（或代码里写死的数组） |
| 输出 | `{trackId, notes, durations, bpm, duration, estimatedDuration}` | **WAV 文件**（方波/三角波/噪声 + 包络 + 归一化） |
| 是否出声 | ❌ 不出声（导出函数是桩） | ✅ 出声 |
| 能查到什么 | 旋律：**会返回音符**；节奏：只返回 `pattern/bars`；和弦：**只返回 `progression` 名称，不返回具体和弦音** | 全部可控：占空比、包络、混音比例、母带响度 |
| 生命周期 | `trackId` 只在服务进程内存里，进程一退就失效，无法存盘 | 谱子存成 `score_demo.json`，随时可重渲染、可 diff、可进 git |
| 依赖 | 需要 Node + MCP 服务常驻 | 纯 stdlib，`python render_score.py in.json out.wav` 即可 |
| 适合谁 | 想"先要个旋律草稿"、不想手写音符 | 想要可复现、可调参数、能进版本库的音频资产 |

**推荐工作流**：让 MCP 生成旋律草稿 → 把返回的 `notes/durations/bpm` 存成 `score_demo.json` → `render_score.py` 渲染成 WAV → 需要加鼓/贝斯就改脚本里的音轨。本次已跑通全链路，产物是 `bgm_from_mcp_score.wav`（16 个音、5.6 s、RMS −14 dBFS）。

**注意**：`generate_chord_progression` 只回一句"在 C 大调生成 I-V-vi-IV"，**不给和弦音**，实际用处接近于零；`create_8bit_rhythm` 同样只给模式名。真正有数据价值的只有 `create_8bit_melody`。

## 八、下一步建议

1. **资产规格对齐**：统一转 **16-bit**（`_sb\normalize_wav.py` 一条命令搞定，峰值 −1 dBFS），采样率保持各自原值或统一 44.1 kHz。当前 `_1dB` 版本即游戏可用格式。
2. **Aseprite 生产流程**：`mcp-test.png` 只是连通性测试图。正式流程建议"新建文档 → 建图层组 → 逐层画/导出"，并把 `assets\sprites\` 作为输出目录；32×32 瓦片、32×48 角色的规格见策划案 10.2 / 10.5 节。
3. **音效批量生成**：Soundbox 每次生成要重新加载模型（约 3 s/条），适合一次列 10~20 条提示词批量跑；`soundbox.enhance_prompt` 可以把"翻锅"这种抽象词补成材质+动作+空间的具体描述。
4. **git 忽略**：`_sb\` 里是 venv、探测脚本、临时图，体积大，建议加进 `.gitignore`；真正要保留的是 `assets\` 和 `_sb\make_8bit_bgm.py`。

---

## 九、待确认

1. **8-bit BGM 要不要继续用 npm 包那套乐谱接口**？还是直接用 `_sb\make_8bit_bgm.py`（可改参数、可进仓库、无需 GPU）？后者我建议留着当"快速出素材"的工具。
2. **音效与 BGM 的响度标准**：游戏里统一 −16 LUFS 左右？还是你打算在 Pygame 里用 `set_volume` 各自调？
3. **`MiniMax Music 3` 是否彻底不装**？（9.8 GB 显存需求，本机 8 GB，装了也用不了；若你以后换 16 GB 显卡可再议。）
4. **`_sb\` 目录要不要清掉**？里面是 venv（约 300 MB）、探测脚本、测试图。保留能复现排查过程，删掉更干净——我建议保留脚本、删 venv（需要时 `uv sync` 能重建，但重装补丁要重来，所以**保留 venv 更省事**）。

## 十、重启电脑 / 重启 DSH 之后怎么加载

**好消息：配置不用再做一次。** 五个服务器都写在 `C:\Users\17038\.dsh\profiles\desktop\cordis.patch.yml` 里，DSH 每次启动都会自动读，`/mcp` 能直接看到它们。

**真正要手动做的是「宿主程序」**——MCP 服务器只是给 AI 用的外壳，画布和音频引擎本身是外部程序：

| MCP 服务器 | DSH 连的端点 | 需要先开着什么 | 没开时的表现 |
|---|---|---|---|
| `aseprite` | `http://127.0.0.1:8770/mcp` | 网关 + **Aseprite 本体**（Lua 扩展连 `ws://127.0.0.1:8765`） | 端点 DOWN；或工具能调但 `connected:false` |
| `soundbox` | `http://127.0.0.1:17494/mcp` | **Soundbox 桌面版**（它自己就是 HTTP） | 工具整组不注册 |
| `8bit-music` | `http://127.0.0.1:8771/mcp` | 网关（内部 `node` 子进程） | 端点 DOWN |
| `blender` | `http://127.0.0.1:8772/mcp` | 网关（内部 `uvx` 子进程） | 端点 DOWN |
| `godot` | `http://127.0.0.1:8773/mcp` | 网关（内部 `node` 子进程） | 端点 DOWN |

> 2026-11-16 起五个服务器**全部改为 Streamable HTTP**，DSH 不再自己 spawn 任何 stdio 子进程（改动的来龙去脉见第十一节）。

**推荐顺序（3 步）**：

1. 开机后双击项目根目录的 [`启动MCP环境.cmd`](<D:/ECNU/计算机导论/Final-Game/启动MCP环境.cmd>)
   它做三件事：起 Soundbox → 起 Aseprite → 用 `pythonw` 拉起网关守护进程（4 个 Streamable HTTP 端点），最后打印状态表（五行的 OK / DOWN）。
   想要逐个握手自检就用 PowerShell：`powershell -NoProfile -ExecutionPolicy Bypass -File _sb\start_mcp_stack.ps1 -Probe`
   > 脚本里**硬编码**了 `SOUNDBOX_DATA_DIR=D:\AI\Soundbox`，因为刚 `setx` 过的环境变量对已存在的 shell 不可见，不显式赋值会回落到 `C:\Users\17038\.soundbox`（实测踩过）。
2. Aseprite 里确认扩展连上：`File → Scripts → MCP: Connect`。首次会弹「允许脚本访问网络」，选允许（每个插件问一次，之后记住）。
3. DSH 里输入 `/mcp`（或设置页 → MCP）确认五项都是已连接。
4. 收工要停：`powershell -NoProfile -ExecutionPolicy Bypass -File _sb\start_mcp_stack.ps1 -Stop`（会先杀守护进程再清端口；顺序反了会被守护进程重新拉起——这个坑踩过）。

**为什么重启后工具可能「消失」**：DSH 的工具清单是在**会话启动时**注册的。如果那一刻 Soundbox / Aseprite 没开，对应的工具就不会出现在这个会话里，之后把程序打开也不会补注册——换一个新会话（或重启 DSH）即可。

**两条不要做的事**：
- 不要移动或删除 `D:\ECNU\计算机导论\Final-Game\_sb\venv-aseprite\`：`mcp-aseprite` 那条配置把 `python.exe` 路径写死在这里，挪了就得改配置。
- 不要用「按进程名批量杀 python」的方式清理 8765：会连带杀掉 DSH 自己的 shell runner（实测导致 `SUBPROCESS_RUNNER_FAILED`）。`启动MCP环境.cmd` 里已经按「命令行含 aseprite_mcp 且是 python 进程」精确匹配。

## 十一、stdio → Streamable HTTP 改造（2026-11-16）

### 11.1 为什么改

原来的 4 条（aseprite / 8bit-music / blender / godot）都是 `transport: stdio`，意味着 **DSH 每次会话启动都要自己 spawn 一个子进程**：进程生命周期绑在 DSH 上、每个会话各自一份、出错时错误散落在 DSH 日志里看不见。改成 HTTP 后，服务是**常驻的、可独立体检的**，DSH 只是客户端，`curl http://127.0.0.1:8770/healthz` 就能判断活着没有。

### 11.2 架构

```
┌──────────────────────────────────────────────────────────────┐
│ DSH（客户端）                                                │
│  cordis.patch.yml: transport=streamable-http + url           │
└───────┬───────────┬───────────┬───────────┬──────────┬───────┘
        │ 8770      │ 8771      │ 8772      │ 8773     │ 17494
        ▼           ▼           ▼           ▼          ▼
   supergateway ×4（node，守护进程托管）          Soundbox 桌面版
        │ stdin 常开、子进程挂了自动重启           （原生 HTTP，无需桥接）
        ▼
   aseprite-mcp --shared / node 8bit / uvx blender / node godot
        │
        ▼（aseprite 另有 ws 8765 → Aseprite Lua 扩展）
```

### 11.3 端口与文件

| 端点 | 服务 | 桥接命令 |
|---|---|---|
| `http://127.0.0.1:8770/mcp` | aseprite（11 工具） | `_sb\venv-aseprite\Scripts\python.exe -m aseprite_mcp --shared` |
| `http://127.0.0.1:8771/mcp` | 8bit-music（4 工具） | `node ...\8-bits-music-mcp\packages\mcp-server\dist\server.js` |
| `http://127.0.0.1:8772/mcp` | blender（10 工具） | `uvx mcp-for-blender` |
| `http://127.0.0.1:8773/mcp` | godot（14 工具） | `node ...\@coding-solo\godot-mcp\build\index.js` |
| `http://127.0.0.1:17494/mcp` | soundbox（24 工具） | 无（Soundbox 自带） |

新增/改动的文件：

- `_sb\gw_supervisor.py` —— 网关守护进程。为每个服务器起一个 `supergateway`，**保持子进程 stdin 常开**，每 4 s 探 `/healthz`，连续失败就重启；`--stop` 先杀自己再清端口，`--status` 只打印。
- `_sb\start_mcp_stack.ps1` —— 一键启动（含 Soundbox / Aseprite / 守护进程 / 状态表 / `-Probe` 自检 / `-Stop` 停止）。
- `启动MCP环境.cmd` —— 双击入口，调用上面的 ps1。
- `C:\Users\17038\.dsh\profiles\desktop\cordis.patch.yml` —— 5 条 MCP 全部改成 `transport: streamable-http` + `url`；旧文件备份在 `cordis.patch.yml.bak-stdio`（要回滚直接覆盖回去）。
- `_sb\gw\logs\<name>.out.log` / `.err.log` —— 每个网关的日志。

### 11.4 两个必须知道的坑

1. **`supergateway` 一见 stdin EOF 就退出。** 日志里是 `stdin closed. Exiting...`。用 `Start-Process -WindowStyle Hidden` 直接起它，子进程拿不到 stdin，起来就死——这就是第一版启动脚本"端口全 DOWN、进程全在"的原因。解法是守护进程用 `subprocess.Popen(..., stdin=PIPE)` 把管道攥在手里不关。
2. **`Start-Process -ArgumentList` 不会替你加引号。** 传数组时每一段都是原样拼接，`--stdio` 的值里带空格就会被拆成多个 argv，supergateway 报 `Ignored unexpected argument ... (an --stdio command with spaces must be quoted)`。解法是自己在值两端加引号，或者干脆交给守护进程用 `Popen` 的列表参数（现在的做法）。
3. **停的顺序不能反。** 先按端口杀 node、后杀守护进程 → 守护进程发现"挂了"立刻重启，看起来像停不掉。现在是先杀守护进程、再清端口，并做 3 轮确认。

### 11.5 验证证据（2026-11-16 09:27 实测）

`start_mcp_stack.ps1 -Probe` 的输出（全部是真实 MCP 握手，不是端口探测）：

```
aseprite    tools/list -> 11 tools
8bit-music  tools/list -> 4 tools
blender     tools/list -> 10 tools
godot       tools/list -> 14 tools
soundbox    tools/list -> 24 tools
```

合计 **63 个工具**。除了自写的裸 HTTP 探针，还用官方 MCP Python SDK 的 `streamablehttp_client` 做了第二遍验证（更接近 DSH 的客户端行为）：
`8770 → aseprite 1.30.0 / 11 工具，调用 get_connection_status 返回 connected:true`；`8771 → 8bit 工具可调用往返`；`17494 → soundbox 工具可调用往返`。两条路径都通，说明 stateless 模式不影响标准 SDK 客户端。

合计 **63 个工具**。`get_connection_status` 经 HTTP 调用返回 `connected:true`、`extension_version:"0.6.0"`、`aseprite_version:"1.3.18.6-dev"`、`api_version:41`——说明 8770 这条链路（HTTP → supergateway → aseprite-mcp → ws 8765 → Lua 扩展）是通的。

### 11.6 现在的限制（如实说）

- **网关不会被 DSH 自动拉起。** DSH 现在只是客户端，端口没人监听就整组工具消失。所以顺序还是：先双击 `启动MCP环境.cmd`，再开 DSH 会话。
- **supergateway 用的是 stateless 模式**（`Running stateless server`）：不返回 `Mcp-Session-Id`，所有客户端共享同一个子进程。对本项目的调用方式（工具调用都自带 `session_id` / `document_id` 参数）没有影响，但如果将来某个 MCP 依赖传输层会话做状态隔离，要加 `--stateful`。
- **多一层进程 = 多一个可能坏的地方**：现在故障点从"DSH 的 spawn"变成"守护进程 + supergateway + 子进程"三层。换来的是可观测性（日志分文件、`/healthz`、`--status`），本轮 6 个问题里有 3 个是靠日志定位的。
