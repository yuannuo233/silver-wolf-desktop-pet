# 自主行为插件 pet-companion

## 它能干什么
模拟 dsh 桌宠"会自己找事做"的感觉：看鼠标、歪头、眨眼、换重心、回头、发呆、微笑，外加碎碎念台词。每次输出一个，避免和上次重复。

## 怎么测
```bash
echo '{"t":"hello"}' | python main.py
echo '{"t":"ask","intent":"companion","args":{"action":"next"}}' | python main.py
echo '{"t":"ask","intent":"陪伴","args":{"action":"say"}}' | python main.py
```

## 意图与参数
| args.action | 说明 |
| --- | --- |
| `next`（默认） | 随机一个自主小动作，不与上次相同 |
| `say` | 随机一句碎碎念，不与上次相同 |
| `reset` | 清空记录 |

## 为什么记录上次行为
"自然"的反面是重复。连续两次播同一个动作会显得呆板，所以存 `last_idx`，用 `(idx+1) % len` 保证不重复。

## 依赖
仅标准库。状态存 `%APPDATA%\SilverWolfPet\plugins\pet-companion\companion.json`。
