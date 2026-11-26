# 提醒插件 reminder

## 它能干什么
添加 / 列出 / 检查到期 / 完成 / 删除提醒。存在本地 SQLite，不联网，不丢数据。

## 怎么测
```bash
echo '{"t":"hello"}' | python main.py
echo '{"t":"ask","intent":"reminder","args":{"action":"add","content":"开会","in_seconds":3600}}' | python main.py
echo '{"t":"ask","intent":"reminder","args":{"action":"list"}}' | python main.py
echo '{"t":"ask","intent":"reminder","args":{"action":"check"}}' | python main.py
```

## 意图与参数
| intent | args.action | 其他参数 |
| --- | --- | --- |
| reminder / 提醒 / 待办 / todo | `add` | `content`（必填）、`due_at`（ISO 8601）或 `in_seconds`（相对秒数） |
| | `list` | `include_done`、`limit`（默认 50） |
| | `check` | `mark_fired`（默认 true，避免重复提醒） |
| | `done` | `id` |
| | `delete` | `id` |

不写 `action` 时默认列出待办。

## 依赖
仅标准库 `sqlite3`。数据库位置：`%APPDATA%\SilverWolfPet\plugins\reminder\reminders.db`。

## 装到桌宠
整个 `reminder/` 文件夹拷进桌宠 `plugins/`，重启桌宠，在「插件」页启用。
