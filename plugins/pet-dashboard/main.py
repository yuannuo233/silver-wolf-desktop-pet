"""数据看板插件：聚合时间、提醒、桌宠状态，输出一段播报。"""
import json, sys, os, sqlite3
from datetime import datetime
from pathlib import Path

INTENTS = ["dashboard", "看板", "今日", "日报", "summary"]

def _appdata():
    base = os.environ.get("APPDATA")
    return (Path(base) if base else Path.home() / ".config") / "SilverWolfPet" / "plugins"

def _read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default if default is not None else {}

def _reminders():
    db = _appdata() / "reminder" / "reminders.db"
    if not db.exists(): return []
    try:
        c = sqlite3.connect(str(db)); c.row_factory = sqlite3.Row
        rows = c.execute("SELECT content,due_at FROM reminders WHERE done=0 ORDER BY due_at LIMIT 5").fetchall()
        c.close()
        return [f"{r['content']}（{r['due_at'][:16]}）" for r in rows]
    except sqlite3.Error:
        return []

def handle(msg):
    t = msg.get("t")
    if t == "hello":
        return {"t": "reply", "ok": True, "intents": INTENTS,
                "description": "聚合时间/提醒/情绪/角色的一条播报"}
    if t != "ask":
        return {"t": "reply", "ok": False, "error": "未知消息类型"}
    intent = msg.get("intent", "")
    if intent not in INTENTS:
        return {"t": "reply", "ok": False, "error": "不支持的意图：" + str(intent)}
    now = datetime.now().astimezone()
    weekday = "星期" + "一二三四五六日"[now.weekday()]
    parts = [f"现在是 {now.strftime('%m月%d日 %H:%M')}，{weekday}"]

    emo = _read_json(_appdata() / "pet-emotion" / "emotion.json")
    if emo:
        parts.append("她心情不错" if emo.get("energy", 50) >= 50 else "她有点累了")

    rem = _read_json(_appdata() / "pet-character" / "character.json")
    if rem.get("id"):
        parts.append("当前角色：" + str(rem["id"]))

    todos = _reminders()
    if todos:
        parts.append("待办：" + "、".join(todos[:3]))
    else:
        parts.append("待办清空了，今天很轻松")

    args = msg.get("args") or {}
    if args.get("weather"):
        parts.append("天气：请在设置里启用 weather 插件后单独查询")

    text = "。".join(parts)
    return {"t": "reply", "ok": True, "text": text,
            "summary": {"time": now.isoformat(timespec="seconds"), "todos": todos,
                        "emotion": emo.get("mood"), "character": rem.get("id")},
            "intent_payload": {"type": "dashboard", "brief": text}}

if __name__ == "__main__":
    try:
        line = sys.stdin.readline()
        msg = json.loads(line) if line.strip() else {}
        reply = handle(msg)
    except Exception as exc:
        reply = {"t": "reply", "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
