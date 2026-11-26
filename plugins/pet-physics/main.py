"""物理反馈插件：输出 Q弹/甩抛/反弹意图。需宿主物理引擎驱动。"""
import json, sys, math

INTENTS = ["pet_physics", "互动", "物理", "bounce", "弹"]

EVENTS = {
    "poke": ("戳一下", "别戳我！", "bounce"),
    "click": ("点击", "干嘛？", "bounce"),
    "drag": ("拖拽", "放手，我自己会走。", "drag"),
    "throw": ("甩抛", "哇——！", "throw"),
    "release": ("松手", "哼，落地了。", "drop"),
    "edge": ("撞墙", "哎哟，撞到了。", "edge_bounce"),
    "shake": ("摇晃", "头晕了！", "shake"),
}
ALIAS = {"戳": "poke", "点": "click", "点击": "click", "拖": "drag", "拖拽": "drag",
         "甩": "throw", "抛": "throw", "扔": "throw", "松手": "release",
         "撞": "edge", "撞墙": "edge", "边缘": "edge", "摇": "shake", "晃": "shake"}

def handle(msg):
    t = msg.get("t")
    if t == "hello":
        return {"t": "reply", "ok": True, "intents": INTENTS,
                "description": "物理反馈意图（Q弹/甩抛/边缘反弹），需宿主物理引擎",
                "events": sorted(EVENTS)}
    if t != "ask":
        return {"t": "reply", "ok": False, "error": "未知消息类型"}
    intent = msg.get("intent", "")
    if intent not in INTENTS:
        return {"t": "reply", "ok": False, "error": "不支持的意图：" + str(intent)}
    args = msg.get("args") or {}
    raw = str(args.get("event") or args.get("action") or "poke").strip()
    key = ALIAS.get(raw, raw if raw in EVENTS else "poke")
    if key not in EVENTS:
        key = "poke"
    cn, line, effect = EVENTS[key]
    intensity = max(0.0, min(1.0, float(args.get("intensity") or 0.6)))
    vx = float(args.get("vx") or 0.0)
    vy = float(args.get("vy") or 0.0)
    payload = {"type": "physics", "event": effect, "intensity": round(intensity, 2)}
    if effect in ("throw", "drop", "edge_bounce"):
        speed = math.sqrt(vx * vx + vy * vy)
        payload["velocity"] = {"x": vx, "y": vy, "speed": round(speed, 2)}
        payload["restitution"] = round(0.4 + 0.5 * intensity, 2)  # 弹性系数
    return {"t": "reply", "ok": True, "text": line,
            "intent_payload": payload, "event": key, "event_name": cn, "effect": effect}

if __name__ == "__main__":
    try:
        line = sys.stdin.readline()
        msg = json.loads(line) if line.strip() else {}
        reply = handle(msg)
    except Exception as exc:
        reply = {"t": "reply", "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
