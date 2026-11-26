"""自主行为插件：低频小动作 + 碎碎念轮换，状态持久化避免重复。"""
import json, sys, os, time, random
from pathlib import Path

INTENTS = ["companion", "陪伴", "碎碎念", "自主", "idle_chatter"]

BEHAVIORS = [
    ("look_mouse", "（她的目光跟着你的鼠标悄悄移过去）", "看鼠标"),
    ("tilt_head", "（她歪了歪头，像在琢磨什么）", "歪头"),
    ("blink", "（她眨了眨眼）", "眨眼"),
    ("shift_weight", "（她换了换重心，尾巴轻轻晃了一下）", "换重心"),
    ("glance_back", "（她回头看了你一眼，又转回去）", "回头"),
    ("daydream", "（她盯着窗外发了一会儿呆）", "发呆"),
    ("small_smile", "（她忽然自己笑了一下）", "微笑"),
]
LINES = [
    "今天写码顺利吗？", "你盯屏幕很久了，休息一下。", "我在呢。",
    "这个 bug 看着就烦，我帮你盯着。", "哼，我才不在乎你。",
    "要不要听我讲个冷笑话？", "别熬夜了，真的。",
]

def _state_path():
    base = os.environ.get("APPDATA")
    d = (Path(base) if base else Path.home() / ".config") / "SilverWolfPet" / "plugins" / "pet-companion"
    d.mkdir(parents=True, exist_ok=True)
    return d / "companion.json"

def _load():
    try:
        s = json.loads(_state_path().read_text(encoding="utf-8"))
        s.setdefault("last_idx", -1); s.setdefault("last_line", -1); s.setdefault("last_at", 0)
        return s
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {"last_idx": -1, "last_line": -1, "last_at": 0}

def _save(s):
    _state_path().write_text(json.dumps(s, ensure_ascii=False), encoding="utf-8")

def handle(msg):
    t = msg.get("t")
    if t == "hello":
        return {"t": "reply", "ok": True, "intents": INTENTS,
                "description": "低频自主行为 + 碎碎念，输出意图供宿主驱动"}
    if t != "ask":
        return {"t": "reply", "ok": False, "error": "未知消息类型"}
    intent = msg.get("intent", "")
    if intent not in INTENTS:
        return {"t": "reply", "ok": False, "error": "不支持的意图：" + str(intent)}
    args = msg.get("args") or {}
    op = str(args.get("action") or "next").lower()
    s = _load()
    now = time.time()

    if op in ("say", "碎碎念", "line"):
        idx = random.randrange(len(LINES))
        if idx == s["last_line"] and len(LINES) > 1:
            idx = (idx + 1) % len(LINES)
        s["last_line"] = idx; s["last_at"] = now; _save(s)
        return {"t": "reply", "ok": True, "text": LINES[idx],
                "intent_payload": {"type": "companion_chatter", "line": LINES[idx]}}

    if op in ("reset",):
        s = {"last_idx": -1, "last_line": -1, "last_at": 0}; _save(s)
        return {"t": "reply", "ok": True, "text": "自主行为记录已清空"}

    # next：挑一个和上次不同的行为
    idx = random.randrange(len(BEHAVIORS))
    if idx == s["last_idx"] and len(BEHAVIORS) > 1:
        idx = (idx + 1) % len(BEHAVIORS)
    s["last_idx"] = idx; s["last_at"] = now; _save(s)
    action, desc, name = BEHAVIORS[idx]
    return {"t": "reply", "ok": True, "text": desc,
            "intent_payload": {"type": "companion_action", "action": action, "name": name},
            "behavior": action}

if __name__ == "__main__":
    try:
        line = sys.stdin.readline()
        msg = json.loads(line) if line.strip() else {}
        reply = handle(msg)
    except Exception as exc:
        reply = {"t": "reply", "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
