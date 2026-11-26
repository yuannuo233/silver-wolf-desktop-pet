# 角色管理插件 pet-character

## 它能干什么
扫描桌宠目录里的角色包，列出角色名和**磁盘上真实存在的帧数**，切换当前角色。

## 怎么测
```bash
echo '{"t":"hello"}' | python main.py
echo '{"t":"ask","intent":"character","args":{"action":"list"}}' | python main.py
echo '{"t":"ask","intent":"角色","args":{"action":"switch","id":"silver_wolf"}}' | python main.py
```

## 意图与参数
| args.action | 参数 | 说明 |
| --- | --- | --- |
| `list`（默认） | — | 列角色 + 帧数 + 当前标记 |
| `switch` | `id` 或 `name` | 切换（素材 0 帧会拒绝）；**重启桌宠后生效** |

## 找桌宠目录
默认假设插件在 `<桌宠根>/plugins/pet-character/`，往上两级就是根目录。也可用环境变量 `SILVERWOLF_APP_DIR` 显式指定。

## 依赖
仅标准库。当前角色 id 存在 `%APPDATA%\SilverWolfPet\plugins\pet-character\character.json`。
