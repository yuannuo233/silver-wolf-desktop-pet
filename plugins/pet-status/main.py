"""状态查询插件：聚合桌宠状态，敏感信息（API Key）脱敏。"""
import json, sys, os
from datetime import datetime
from pathlib import Path

INTENTS = ["pet_status", "状态", "status", "在干嘛"]

def _appdata():
    base = os.environ.get("APPDATA")
    return (Path(base) if base else Path.home() / ".config") / "SilverWolfPet"

def _safe_conf():
    """读桌宠 config.json，但只挑非敏感字段，API Key 绝不外泄。"""
    p = _appdata() / "config.json"
    try:
        c = json.loads(p.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    safe = {}
    for k in ("theme", "size_height", "follow_activity", "check_updates", "character", "terms_seen"):
        if k in c: safe[k] = c[k]
    # api_key / base_url / model 刻意不返回
    return safe

def _read(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}

def handle(msg):
    t = msg.get("t")
    if t == "hello":
        return {"t": "reply", "ok": True, "intents": INTENTS,
                "description": "桌宠状态汇总（API Key 已脱敏）"}
    if t != "ask":
        return {"t": "reply", "ok": False, "error": "未知消息类型"}
    intent = msg.get("intent", "")
    if intent not in INTENTS:
        return {"t": "reply", "ok": False, "error": "不支持的意图：" + str(intent)}
    base = _appdata() / "plugins"
    emo = _read(base / "pet-emotion" / "emotion.json")
    companion = _read(base / "pet-companion" / "companion.json")
    char = _read(base / "pet-character" / "character.json")
    conf = _safe_conf()

    moods = {"happy":"开心","angry":"生气","sad":"委屈","jealous":"吃醋","clingy":"黏人","tired":"疲惫","calm":"平静"}
    mood = conf.get("_mood") or emo.get("mood") or "calm"
    mood_cn = moods.get(mood, mood)
    cid = char.get("id") or conf.get("character") or "silver_wolf"
    energy = emo.get("energy")

    bits = [f"当前角色 {cid}", f"心情{mood_cn}"]
    if energy is not None: bits.append(f"精力 {energy}/100")
    if conf.get("theme"): bits.append("主题 " + str(conf["theme"]))
    text = "她现在：" + "，".join(bits)

    return {"t": "reply", "ok": True, "text": text,
            "status": {"character": cid, "mood": mood, "energy": energy,
                       "theme": conf.get("theme"), "size_height": conf.get("size_height"),
                       "follow_activity": conf.get("follow_activity"),
                       "last_behavior_at": companion.get("last_at"),
                       "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                       "safe_config": conf},
            "intent_payload": {"type": "pet_status", "mood": mood, "character": cid}}

if __name__ == "__main__":
    try:
        line = sys.stdin.readline()
        msg = json.loads(line) if line.strip() else {}
        reply = handle(msg)
    except Exception as exc:
        reply = {"t": "reply", "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
