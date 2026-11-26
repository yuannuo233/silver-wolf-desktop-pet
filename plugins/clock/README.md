# 报时插件 clock

## 它能干什么
告诉她现在几点。支持本机时区、UTC、IANA 时区名（如 `Asia/Shanghai`）。

## 怎么测
```bash
echo '{"t":"hello"}' | python main.py
echo '{"t":"ask","intent":"clock","args":{}}' | python main.py
echo '{"t":"ask","intent":"clock","args":{"timezone":"UTC"}}' | python main.py
```

## 意图与参数
| intent | 参数 | 返回 |
| --- | --- | --- |
| clock / time / 报时 / 时间 | `timezone`（可选）：local / UTC / IANA 名 | `text` + `iso` + `timezone` + `timestamp` |

## 依赖
仅 Python 标准库。无需安装任何东西。

## 装到桌宠
把整个 `clock/` 文件夹拷进桌宠的 `plugins/` 目录，重启桌宠，在「插件」页启用。
