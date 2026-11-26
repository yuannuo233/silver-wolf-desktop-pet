# 物理反馈插件 pet-physics

## 它能干什么
把"戳一下/点击/拖拽/甩抛/松手/撞墙/摇晃"转成结构化物理意图：弹性系数、速度向量、强度。气泡给出对应台词。

## 怎么测
```bash
echo '{"t":"hello"}' | python main.py
echo '{"t":"ask","intent":"互动","args":{"event":"戳"}}' | python main.py
echo '{"t":"ask","intent":"pet_physics","args":{"event":"throw","vx":300,"vy":-200,"intensity":0.9}}' | python main.py
```

## 事件表
| event | 效果 effect | 台词 |
| --- | --- | --- |
| poke / click | bounce（Q弹） | 别戳我！ |
| drag | drag | 放手，我自己会走。 |
| throw | throw + 速度向量 | 哇——！ |
| release | drop | 哼，落地了。 |
| edge | edge_bounce + 弹性系数 | 哎哟，撞到了。 |
| shake | shake | 头晕了！ |

## 依赖
仅标准库。

## 重要
和 pet-actions 一样，本插件**只输出意图**，不真的让桌宠弹起来。宿主物理引擎读 `intent_payload` 实现位移/回弹。
