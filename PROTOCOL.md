# 桌宠互操作协议（Pet Interop Protocol）

> 目标：让银狼桌宠**能接入别的宠物生态**，也让**别的桌宠能复用她的素材与状态**。
> 参考对象是 LongCat 那类"多宠物共存 / 可换角色"的框架。
> 协议只规定**数据长什么样**，不规定用什么语言、什么引擎实现。

写于 v0.6.17。本协议是**草案（draft）**，字段只增不改。

---

## 1. 设计原则

1. **零依赖**：协议本体只是目录约定 + 几个 JSON 文件，不需要装任何 SDK。
2. **可渐进接入**：只做「素材包」也能用；再往下做「状态包」「事件包」逐级增强。
3. **与引擎解耦**：同一份素材包，Tk 能读、Godot 能读、Web 也能读。
4. **单向兼容**：本项目的 `assets/stand/frames.json` 是协议的超集子集，不破坏现有代码。

---

## 2. 三级能力（Level）

| 级别 | 名字 | 提供什么 | 别的宠物系统能做什么 |
| --- | --- | --- | --- |
| **L1** | 素材包 Sprite Pack | 帧图 + 元数据 | 直接把银狼当皮肤用 |
| **L2** | 状态包 State Pack | 状态机 + 动作表 | 完整复刻她的行为 |
| **L3** | 事件包 Event Pack | 事件订阅 + 命令 | 双向联动（她响应你的事件） |

最低只要 L1 就能"接入"，L3 才是真正的互操作。

---

## 3. L1 素材包

### 3.1 目录

```text
<包名>.petpack/
├── pack.json            ← 必须
├── frames/              ← 必须
│   ├── idle_01.png
│   └── ...
├── preview.png          ← 建议（商店/列表里显示）
└── LICENSE              ← 必须（说明素材授权）
```

### 3.2 `pack.json`

```json
{
  "spec": "pet-interop/1",
  "id": "silver-wolf",
  "name": "银狼",
  "name_en": "Silver Wolf",
  "version": "0.6.17",
  "author": "yuannuo233",
  "license": "MIT (code) / fan-art (assets)",
  "attribution": "《崩坏：星穹铁道》非官方粉丝作品，不含游戏拆包素材",

  "canvas": {
    "width": 190,
    "height": 216,
    "baseline_y": 210,
    "center_x": 95,
    "character_height": 200
  },

  "alpha": {
    "mode": "binary",
    "threshold": 128,
    "key_color": "magenta",
    "note": "半透明像素必须二值化，否则 Tk 里边缘发黑"
  },

  "states": { ...见 3.3... }
}
```

### 3.3 `states`

键是**语义状态名**（见第 4 节标准表），值是该状态的帧序列：

```json
"idle": {
  "loop": true,
  "fps": 10,
  "frames": [
    { "file": "frames/idle_01.png", "duration_ms": 100 },
    { "file": "frames/idle_02.png", "duration_ms": 100 }
  ]
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `loop` | bool | `true` 循环；`false` 播一遍就回 `idle` |
| `frames[].file` | str | 相对包根的路径 |
| `frames[].duration_ms` | int | 这一帧显示多久 |
| `fps` | int | 可选，仅作参考（真实时长以 `duration_ms` 为准） |

> **兼容性**：本项目 `assets/stand/frames.json` 的结构已经是 `{sprite: {...}, states: {...}}`。
> 把 `sprite` 改名为 `canvas`、补上 `spec/id/name/license` 三个字段，
> 就是一个合法的 L1 包。**现有代码不需要改。**

---

## 4. 标准状态名（必读）

别的系统要"理解银狼在干什么"，就得有共同词汇。下表是**建议标准名**，
字面不一致的用 `aliases` 映射。

| 标准名 | 含义 | 是否必需 | 本项目对应 |
| --- | --- | --- | --- |
| `idle` | 待机 | **必需** | `idle` |
| `run_left` / `run_right` | 向左/右移动 | 强烈建议 | 同名 |
| `turn_left` / `turn_right` | 原地转身过渡 | 建议 | 同名 |
| `type` | 在打字 | 可选 | `typing` |
| `game` | 在玩游戏 | 可选 | `console` |
| `sleep` | 睡觉 | 可选 | `doze` |
| `wave` | 挥手 | 可选 | 同名 |
| `stretch` | 伸懒腰 | 可选 | 同名 |
| `eat` | 吃东西 | 可选 | `lollipop` |
| `drag` | 被拖拽 | 可选 | —（本项目用转向代替） |

映射写法（`pack.json` 里可选加）：

```json
"aliases": {
  "typing": "type",
  "console": "game",
  "doze": "sleep",
  "lollipop": "eat"
}
```

---

## 5. L2 状态包

在 `pack.json` 里加 `behavior` 段，描述"什么情况下切什么状态"：

```json
"behavior": {
  "default": "idle",
  "rules": [
    { "when": "dragging",            "state": "drag" },
    { "when": "moving",              "state": "run_right", "mirror": "run_left" },
    { "when": "host.activity=type",  "state": "typing" },
    { "when": "host.activity=game",  "state": "console" }
  ],
  "one_shot": ["wave", "doze", "stretch", "lollipop", "turn_left", "turn_right"],
  "priority": ["drag", "one_shot", "moving", "activity", "default"]
}
```

- `when` 是简单的布尔表达式：`dragging` / `moving` / `host.<字段>=<值>`
- `one_shot` 里的状态播完自动回 `default`
- `priority` 决定抢占顺序（本项目实测：拖拽 > 一次性动作 > 移动 > 活动跟随 > 待机）

---

## 6. L3 事件包（互通的关键）

### 6.1 双向通道

```text
别的宠物系统  ──事件──▶  银狼桌宠
银狼桌宠     ──命令──▶  别的宠物系统
```

**传输**（任选其一，实现者自己定，只要语义一致）：

| 方式 | 适合 | 说明 |
| --- | --- | --- |
| JSON Lines 文件 | 最省事 | 一行一个事件，双方 tail 同一个文件 |
| 本地 HTTP | 跨进程 | `POST http://127.0.0.1:PORT/event` |
| stdin/stdout | 子进程模式 | 一行一个 JSON |

### 6.2 事件（外部 → 银狼）

```json
{"t": "activity", "value": "type", "source": "longcat"}
{"t": "activity", "value": "game", "exe": "starrail.exe", "source": "longcat"}
{"t": "say", "text": "别熬夜了", "duration_ms": 4000}
{"t": "play", "state": "wave"}
{"t": "move_to", "x": 1600, "y": 700}
{"t": "theme", "value": "dark"}
```

| `t` | 字段 | 效果 |
| --- | --- | --- |
| `activity` | `value` = `type` / `game` / `none` | 直接切到对应状态，不用自己猜前台 |
| `say` | `text`、`duration_ms` | 头顶气泡说一句 |
| `play` | `state` | 播一次性动作 |
| `move_to` | `x`、`y` | 以自己的速度跑过去 |
| `theme` | `value` = `light` / `dark` / `cyber` | 换配色 |

### 6.3 命令（银狼 → 外部）

```json
{"t": "state",  "value": "run_right"}
{"t": "poked",  "times": 3}
{"t": "chat",   "role": "user", "text": "在吗"}
{"t": "config", "key": "follow_activity", "value": false}
```

| `t` | 触发时机 |
| --- | --- |
| `state` | 动画状态改变 |
| `poked` | 被单击/双击 |
| `chat` | AI 对话的一轮（`role` = `user` / `assistant`） |
| `config` | 设置项被改动 |

### 6.4 握手

启动后发一次能力声明，对方据此决定发哪些事件：

```json
{"t": "hello", "spec": "pet-interop/1",
 "levels": ["L1", "L2", "L3"],
 "states": ["idle", "run_left", "run_right", "turn_left", "turn_right",
            "typing", "console", "wave", "doze", "stretch", "lollipop"],
 "accepts": ["activity", "say", "play", "move_to", "theme"]}
```

---

## 7. 接入 LongCat 这类多宠物框架

LongCat 的核心模型是「一个宿主管理多个宠物，每个宠物有独立状态与位置」。
按本协议接入需要三步：

1. **做 L1 包**：把 `assets/stand` 打包成 `silver-wolf.petpack`，
   补 `spec/id/name/license` 和 `aliases`。宿主就能把银狼列为可换角色。
2. **做 L2 映射**：把本项目的 `_start_run` / `_apply_activity` 语义写进 `behavior.rules`，
   宿主的调度器就能推出"什么时候该播 run_left"。
3. **做 L3 桥**：宿主把「前台应用 / 是否在打字 / 是否在拖动」通过 `activity` 事件推过来，
   银狼就不用自己调 Win32 了 —— **这一步顺便把 Windows 依赖从素材层剥离**，
   将来 Mac/Linux 版只要宿主提供 `activity` 就能跑。

> 也就是说：**L3 是跨平台的正解**。把"感知前台"这件事交给宿主（宿主本来就跨平台），
> 银狼只负责"拿到活动状态 → 播对应动画"。

---

## 8. 版本策略

- `spec` 字段是协议版本，当前 `pet-interop/1`
- **只增不改**：新增字段必须有默认值，旧实现忽略未知字段即可
- 破坏性变更走 `pet-interop/2`
- 素材包与协议版本解耦：`pack.json` 的 `version` 是素材自己的版本

---

## 9. 现状与路线

| 项 | 状态 |
| --- | --- |
| L1 素材包导出 | ⬜ 未实现（结构已兼容，缺一个打包脚本） |
| L2 行为描述 | ⬜ 未实现（规则写死在 `pet.py` 里） |
| L3 事件通道 | ⬜ 未实现（需要加一个本地 socket / 文件监听线程） |
| 跨平台 | ⬜ 未实现（L3 就位后才有条件） |

**本协议先作为设计文档发布**，实现会按 L1 → L3 的顺序补。
有想接的系统可以照本文档先对字段，接口实现后直接对接。
