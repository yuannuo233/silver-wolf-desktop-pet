# 情绪插件 pet-emotion

## 它能干什么
模拟 dsh 桌宠的情绪系统：六条情绪轴（开心/生气/委屈/吃醋/黏人/疲惫）、情绪惯性、精力值、时间衰减。状态存在本地，跨调用不丢。

## 怎么测
```bash
echo '{"t":"hello"}' | python main.py
echo '{"t":"ask","intent":"emotion","args":{"action":"get"}}' | python main.py
echo '{"t":"ask","intent":"emotion","args":{"action":"set","value":"生气","strength":40}}' | python main.py
echo '{"t":"ask","intent":"emotion","args":{"action":"reset"}}' | python main.py
```

## 意图与参数
| args.action | 参数 | 说明 |
| --- | --- | --- |
| `get`（默认） | — | 查当前情绪和精力 |
| `set` | `value`（情绪名/触发词）、`strength`（1~100，默认 30） | 施加情绪刺激 |
| `reset` | — | 归零 |

## 情绪惯性（重点）
被惹生气后，不会因为下一句"哄一下"就立刻开心——新情绪只提升对应轴，其余轴按 0.7 衰减。这模仿了 dsh 大肥鱼"情绪有惯性"的设计。

## 依赖
仅标准库。状态文件：`%APPDATA%\SilverWolfPet\plugins\pet-emotion\emotion.json`。
