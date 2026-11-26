"""报时插件：当前时间 / 时区 / 星期。仅标准库。"""
import json, sys
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

INTENTS = ["clock", "time", "报时", "时间"]

def _now(tz_name=None):
    now = datetime.now().astimezone()
    if not tz_name or tz_name.lower() in ("local", "本机"):
        return now, str(now.tzinfo)
    if tz_name.upper() == "utc":
        return now.astimezone(timezone.utc), "UTC"
    try:
        return now.astimezone(ZoneInfo(tz_name)), tz_name
    except (ZoneInfoNotFoundError, ValueError):
        return now, str(now.tzinfo) + "（时区无效，已用本机）"

def handle(msg):
    t = msg.get("t")
    if t == "hello":
        return {"t": "reply", "ok": True, "intents": INTENTS, "description": "告诉她现在几点"}
    if t != "ask":
        return {"t": "reply", "ok": False, "error": "未知消息类型"}
    intent = msg.get("intent", "")
    args = msg.get("args") or {}
    if intent not in INTENTS:
        return {"t": "reply", "ok": False, "error": "不支持的意图：" + str(intent)}
    target, label = _now(args.get("timezone") or args.get("tz"))
    weekday = "星期" + "一二三四五六日"[target.weekday()]
    text = f"现在是 {target.strftime('%Y年%m月%d日 %H:%M:%S')}，{weekday}（{label}）"
    return {"t": "reply", "ok": True, "text": text,
            "iso": target.isoformat(timespec="seconds"), "timezone": label,
            "timestamp": int(target.timestamp())}

if __name__ == "__main__":
    try:
        line = sys.stdin.readline()
        msg = json.loads(line) if line.strip() else {}
        reply = handle(msg)
    except Exception as exc:
        reply = {"t": "reply", "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
