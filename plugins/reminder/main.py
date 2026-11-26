"""提醒插件：SQLite 持久化，支持 add/list/check/done/delete。仅标准库。"""
import json, sys, sqlite3, os
from datetime import datetime, timedelta, timezone
from pathlib import Path

INTENTS = ["reminder", "提醒", "待办", "todo"]

def _db_path():
    base = os.environ.get("APPDATA")
    d = Path(base) if base else Path.home() / ".config"
    d = d / "SilverWolfPet" / "plugins" / "reminder"
    d.mkdir(parents=True, exist_ok=True)
    return d / "reminders.db"

def _conn():
    c = sqlite3.connect(str(_db_path()))
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL, due_at TEXT NOT NULL, created_at TEXT NOT NULL,
        done INTEGER NOT NULL DEFAULT 0, fired INTEGER NOT NULL DEFAULT 0, extra TEXT)""")
    return c

def _iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")

def _parse_due(due_at, in_seconds):
    if in_seconds is not None:
        try: n = int(in_seconds)
        except (TypeError, ValueError): return None, "in_seconds 必须是数字"
        if n <= 0: return None, "in_seconds 必须大于 0"
        return (datetime.now().astimezone() + timedelta(seconds=n)).isoformat(timespec="seconds"), None
    if not due_at: return None, "请给 due_at 或 in_seconds"
    try:
        dt = datetime.fromisoformat(str(due_at).replace("Z", "+00:00"))
        if dt.tzinfo is None: dt = dt.astimezone()
        return dt.isoformat(timespec="seconds"), None
    except ValueError as e:
        return None, "due_at 格式错误（需 ISO 8601）：" + str(e)

def _add(a):
    content = str(a.get("content") or a.get("text") or "").strip()
    if not content: return {"ok": False, "error": "提醒内容不能为空"}
    due, err = _parse_due(a.get("due_at"), a.get("in_seconds"))
    if err: return {"ok": False, "error": err}
    with _conn() as c:
        cur = c.execute("INSERT INTO reminders(content,due_at,created_at,done,fired,extra) VALUES(?,?,?,0,0,?)",
                        (content, due, _iso(), json.dumps(a.get("extra"), ensure_ascii=False) if a.get("extra") else None))
        rid = cur.lastrowid
    return {"ok": True, "text": f"记下了：{content}（id={rid}），{due} 提醒你", "id": rid, "due_at": due}

def _list(a):
    limit = int(a.get("limit") or 50)
    with _conn() as c:
        where = "" if a.get("include_done") else "WHERE done=0"
        rows = c.execute(f"SELECT * FROM reminders {where} ORDER BY due_at ASC LIMIT ?", (limit,)).fetchall()
    items = [dict(r) for r in rows]
    if not items:
        return {"ok": True, "text": "目前没有待办提醒", "count": 0, "reminders": []}
    lines = [f"{i['id']}. {i['content']}（{i['due_at']}）" for i in items[:10]]
    return {"ok": True, "text": "待办：" + "；".join(lines), "count": len(items), "reminders": items}

def _check(a):
    mark = a.get("mark_fired", True)
    now = datetime.fromisoformat(_iso())
    with _conn() as c:
        rows = c.execute("SELECT * FROM reminders WHERE done=0 AND fired=0 ORDER BY due_at").fetchall()
        due = []
        for r in rows:
            try:
                dt = datetime.fromisoformat(r["due_at"].replace("Z", "+00:00"))
                if dt.tzinfo is None: dt = dt.astimezone()
                if dt <= now: due.append(r)
            except (ValueError, TypeError): continue
        if mark and due:
            ids = [r["id"] for r in due]
            c.execute("UPDATE reminders SET fired=1 WHERE id IN (%s)" % ",".join("?" * len(ids)), ids)
    if not due:
        return {"ok": True, "text": "暂时没有到期的提醒", "count": 0, "due_reminders": []}
    texts = [r["content"] for r in due]
    return {"ok": True, "text": "到时间了：" + "；".join(texts), "count": len(texts),
            "due_reminders": [dict(r) for r in due]}

def _change(a, action):
    try: rid = int(a.get("id") or a.get("reminder_id"))
    except (TypeError, ValueError): return {"ok": False, "error": "请给数字 id"}
    with _conn() as c:
        if action == "done":
            cur = c.execute("UPDATE reminders SET done=1 WHERE id=?", (rid,))
            word = "完成"
        else:
            cur = c.execute("DELETE FROM reminders WHERE id=?", (rid,))
            word = "删除"
        if cur.rowcount == 0: return {"ok": False, "error": f"没找到 id={rid} 的提醒"}
    return {"ok": True, "text": f"提醒 {rid} 已{word}", "id": rid}

def handle(msg):
    t = msg.get("t")
    if t == "hello":
        return {"t": "reply", "ok": True, "intents": INTENTS, "description": "本地提醒，支持增删查改"}
    if t != "ask":
        return {"t": "reply", "ok": False, "error": "未知消息类型"}
    intent = msg.get("intent", "")
    if intent not in INTENTS:
        return {"t": "reply", "ok": False, "error": "不支持的意图：" + str(intent)}
    args = msg.get("args") or {}
    action = str(args.get("action") or "").lower()
    key = str(args.get("op") or "").lower()
    if action in ("add", "new") or key in ("add", "new") or intent == "提醒" and args.get("content"):
        return {"t": "reply", **_add(args)}
    if action in ("list", "all") or key in ("list", "all"):
        return {"t": "reply", **_list(args)}
    if action in ("check", "due") or key in ("check", "due"):
        return {"t": "reply", **_check(args)}
    if action in ("done", "complete") or key in ("done", "complete"):
        return {"t": "reply", **_change(args, "done")}
    if action in ("delete", "del", "remove") or key in ("delete", "del", "remove"):
        return {"t": "reply", **_change(args, "delete")}
    # 没写 action 时，默认按"列出"处理，最不容易误事
    return {"t": "reply", **_list(args)}

if __name__ == "__main__":
    try:
        line = sys.stdin.readline()
        msg = json.loads(line) if line.strip() else {}
        reply = handle(msg)
    except Exception as exc:
        reply = {"t": "reply", "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
