"""动作点播插件：输出动作意图 JSON。不直接操作桌宠窗口，需宿主引擎驱动。"""
import json, sys

INTENTS = ["pet_action", "动作", "表演", "play", "animate"]

# 动作表：id -> (中文名, 气泡台词, 默认时长毫秒, 是否循环)
ACTIONS = {
    "breathe": ("呼吸", "呼……吸……（她深呼吸了一下）", 4000, True),
    "idle": ("待机", "我就在这儿待着，别管我。", 3000, True),
    "doze": ("打盹", "zzz……别吵，我眯一会儿。", 8000, False),
    "cube": ("玩魔方", "这魔方被我三秒复原，信不信？", 6000, True),
    "hotpot": ("吃火锅", "涮一片毛肚，七上八下——正好。", 7000, False),
    "stretch": ("伸懒腰", "嗯——脖子好酸。", 3500, False),
    "wave": ("挥手", "嗨！干嘛叫我？", 2500, False),
    "lollipop": ("吃棒棒糖", "草莓味的，要吗？不给你。", 5000, True),
    "typing": ("敲键盘", "我在写一个很厉害的程序，别看。", 5000, True),
    "console": ("玩掌机", "这关我打了一百遍了，今天必过。", 8000, True),
    "run_left": ("向左跑", "让开让开，她要冲了！", 2000, False),
    "run_right": ("向右跑", "让开让开，她要冲了！", 2000, False),
    "turn": ("转身", "嗯？你叫我？", 1200, False),
}
ALIAS = {
    "呼吸": "breathe", "待机": "idle", "打盹": "doze", "睡觉": "doze",
    "魔方": "cube", "玩魔方": "cube", "火锅": "hotpot", "吃火锅": "hotpot",
    "伸懒腰": "stretch", "懒腰": "stretch", "挥手": "wave", "招呼": "wave",
    "棒棒糖": "lollipop", "糖": "lollipop", "打字": "typing", "敲键盘": "typing",
    "掌机": "console", "游戏": "console", "左跑": "run_left", "右跑": "run_right",
    "转身": "turn", "打个盹": "doze", "伸个懒腰": "stretch", "打个哈欠": "doze",
    "跑一下": "run_left", "招手": "wave", "你好": "wave",
}

def handle(msg):
    t = msg.get("t")
    if t == "hello":
        return {"t": "reply", "ok": True, "intents": INTENTS,
                "description": "动作点播（输出意图，需宿主驱动动画）",
                "actions": sorted(ACTIONS)}
    if t != "ask":
        return {"t": "reply", "ok": False, "error": "未知消息类型"}
    intent = msg.get("intent", "")
    if intent not in INTENTS:
        return {"t": "reply", "ok": False, "error": "不支持的意图：" + str(intent)}
    args = msg.get("args") or {}
    raw = str(args.get("action") or args.get("name") or args.get("value") or "").strip()
    if not raw:
        txt = str(args.get("text") or "")
        for alias in ALIAS:
            if alias in txt:
                raw = alias
                break
    key = ALIAS.get(raw, raw)
    if not key:
        key = "wave"
    if key not in ACTIONS:
        return {"t": "reply", "ok": False, "error": f"没这个动作：{raw}。可用：{'、'.join(ACTIONS)}"}
    name, line, dur, loop = ACTIONS[key]
    return {"t": "reply", "ok": True, "text": line,
            "intent_payload": {"type": "play_action", "action": key,
                               "duration_ms": int(args.get("duration_ms") or dur),
                               "loop": bool(loop)},
            "action": key, "action_name": name}

if __name__ == "__main__":
    try:
        line = sys.stdin.readline()
        msg = json.loads(line) if line.strip() else {}
        reply = handle(msg)
    except Exception as exc:
        reply = {"t": "reply", "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
