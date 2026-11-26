"""情绪插件：六轴情绪 + 惯性 + 精力。状态存 %APPDATA%/SilverWolfPet/plugins/pet-emotion/。"""
import json, sys, os, time
from pathlib import Path

INTENTS = ["emotion", "情绪", "心情", "mood", "表情"]

AXES = ["happy", "angry", "sad", "jealous", "clingy", "tired"]
AXIS_CN = {"happy": "开心", "angry": "生气", "sad": "委屈", "jealous": "吃醋",
           "clingy": "黏人", "tired": "疲惫"}
# 用户说法 → 轴
TRIGGER = {
    "开心": "happy", "高兴": "happy", "笑": "happy", "夸": "happy",
    "生气": "angry", "愤怒": "angry", "惹": "angry", "烦": "angry",
    "委屈": "sad", "难过": "sad", "哭": "sad", "伤心": "sad",
    "吃醋": "jealous", "嫉妒": "jealous",
    "黏人": "clingy", "想你": "clingy", "抱": "clingy",
    "累": "tired", "困": "tired", "睡": "tired",
}

def _state_path():
    base = os.environ.get("APPDATA")
    d = (Path(base) if base else Path.home() / ".config") / "SilverWolfPet" / "plugins" / "pet-emotion"
    d.mkdir(parents=True, exist_ok=True)
    return d / "emotion.json"

def _default():
    return {"axes": {a: 10 for a in AXES}, "energy": 80,
            "mood": "calm", "last_event": "", "updated_at": time.time()}

def _load():
    try:
        s = json.loads(_state_path().read_text(encoding="utf-8"))
        s.setdefault("axes", {})
        for a in AXES:
            s["axes"].setdefault(a, 10)
        s.setdefault("energy", 80)
        s.setdefault("mood", "calm")
        return s
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return _default()

def _save(s):
    s["updated_at"] = time.time()
    _state_path().write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")

def _decay(s, hours):
    """时间衰减：每小时各轴向 10 回落，精力向 70 回落。"""
    if hours <= 0: return
    for a in AXES:
        s["axes"][a] = max(0, int(s["axes"][a] - hours * 3))
    s["energy"] = max(20, min(100, int(s["energy"] + (70 - s["energy"]) * min(1, hours / 8))))

def _dominant(s):
    top = max(s["axes"].items(), key=lambda kv: kv[1])
    if top[1] < 20: return "calm"
    return top[0]

def handle(msg):
    t = msg.get("t")
    if t == "hello":
        return {"t": "reply", "ok": True, "intents": INTENTS,
                "description": "六轴情绪 + 惯性 + 精力，状态本地持久化"}
    if t != "ask":
        return {"t": "reply", "ok": False, "error": "未知消息类型"}
    intent = msg.get("intent", "")
    if intent not in INTENTS:
        return {"t": "reply", "ok": False, "error": "不支持的意图：" + str(intent)}
    args = msg.get("args") or {}
    op = str(args.get("action") or args.get("op") or "get").lower()
    s = _load()
    elapsed_h = (time.time() - s.get("updated_at", time.time())) / 3600
    _decay(s, elapsed_h)

    if op in ("set", "刺激", "update"):
        raw = str(args.get("value") or args.get("emotion") or args.get("text") or "").strip()
        axis = TRIGGER.get(raw, raw if raw in AXES else None)
        strength = int(args.get("strength") or 30)
        if not axis or axis not in AXES:
            return {"t": "reply", "ok": False, "error": f"未知情绪：{raw}。可用：{'、'.join(AXIS_CN.values())}"}
        # 情绪惯性：新情绪只部分覆盖旧的主导情绪，不会立刻翻脸
        for a in AXES:
            if a == axis:
                s["axes"][a] = min(100, s["axes"][a] + strength)
            else:
                s["axes"][a] = max(0, int(s["axes"][a] * 0.7))
        s["energy"] = max(0, min(100, s["energy"] - (5 if axis != "tired" else 0)))
        s["last_event"] = raw
        s["mood"] = _dominant(s)
        _save(s)
        label = AXIS_CN[axis]
        text = f"她现在有点{label}了（{s['axes'][axis]}/100）"
        return {"t": "reply", "ok": True, "text": text, "state": s,
                "intent_payload": {"type": "emotion", "mood": s["mood"], "axes": s["axes"],
                                   "expression": s["mood"]}}

    if op in ("reset", "重置"):
        s = _default()
        _save(s)
        return {"t": "reply", "ok": True, "text": "情绪已归零，她恢复平静了", "state": s}

    # get：查询
    s["mood"] = _dominant(s)
    _save(s)
    mood_cn = AXIS_CN.get(s["mood"], "平静")
    energy_note = "（有点累了）" if s["energy"] < 35 else ""
    return {"t": "reply", "ok": True,
            "text": f"她现在{mood_cn}，精力 {s['energy']}/100{energy_note}",
            "state": s, "intent_payload": {"type": "emotion_query", "mood": s["mood"],
                                          "expression": s["mood"], "energy": s["energy"]}}

if __name__ == "__main__":
    try:
        line = sys.stdin.readline()
        msg = json.loads(line) if line.strip() else {}
        reply = handle(msg)
    except Exception as exc:
        reply = {"t": "reply", "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
