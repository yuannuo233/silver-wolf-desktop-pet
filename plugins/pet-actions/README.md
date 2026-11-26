# 动作点播插件 pet-actions

## 它能干什么
让桌宠播一个动作：待机呼吸、打盹、玩魔方、吃火锅、伸懒腰、挥手、棒棒糖、敲键盘、玩掌机、左右跑、转身。返回气泡台词 + **动作意图**。

## 怎么测
```bash
echo '{"t":"hello"}' | python main.py
echo '{"t":"ask","intent":"pet_action","args":{"action":"玩魔方"}}' | python main.py
echo '{"t":"ask","intent":"动作","args":{"action":"doze","duration_ms":5000}}' | python main.py
```

## 可用动作（14 个）
`breathe` `idle` `doze` `cube` `hotpot` `stretch` `wave` `lollipop` `typing` `console` `run_left` `run_right` `turn`
中文别名也能用：呼吸、打盹、魔方、火锅、伸懒腰、挥手、棒棒糖、打字、掌机、转身……

## 返回的关键字段
| 字段 | 含义 |
| --- | --- |
| `text` | 气泡台词 |
| `action` | 动作 id |
| `intent_payload` | 给宿主的动作意图：`type=play_action` + `action` + `duration_ms` + `loop` |

## 依赖
仅标准库。

## 重要
插件**不会自己让桌宠动起来**。它只输出意图，宿主引擎读取 `intent_payload` 后才播动画。详见技术路线。
