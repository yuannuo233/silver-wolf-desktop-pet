# 数据看板插件 pet-dashboard

## 它能干什么
把时间、待办、情绪、当前角色聚合成一句话播报。像 dsh 桌宠的"工作看板"，但不侵入聊天上下文。

## 怎么测
```bash
echo '{"t":"hello"}' | python main.py
echo '{"t":"ask","intent":"dashboard","args":{}}' | python main.py
echo '{"t":"ask","intent":"看板","args":{"weather":true}}' | python main.py
```

## 数据来源
| 信息 | 从哪来 |
| --- | --- |
| 时间 | `datetime.now()` |
| 待办 | reminder 插件的 SQLite（只读） |
| 情绪/精力 | pet-emotion 的 emotion.json（只读） |
| 角色 | pet-character 的 character.json（只读） |

## 依赖
仅标准库。本插件**只读**其他插件的状态文件，不写。

## 装到桌宠
整个 `pet-dashboard/` 拷进 `plugins/`，重启启用。单独用也能跑（没装其他插件就少播报几项）。
