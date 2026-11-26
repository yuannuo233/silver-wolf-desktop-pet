"""角色管理插件：扫描 characters/ 目录，列角色、统计帧数、切换。"""
import json, sys, os
from pathlib import Path

INTENTS = ["character", "角色", "换角色", "characters"]

def _app_root():
    """插件在 <app>/plugins/pet-character/main.py，往上两级是 app 根。可用环境变量覆盖。"""
    env = os.environ.get("SILVERWOLF_APP_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent.parent

def _state_path():
    base = os.environ.get("APPDATA")
    d = (Path(base) if base else Path.home() / ".config") / "SilverWolfPet" / "plugins" / "pet-character"
    d.mkdir(parents=True, exist_ok=True)
    return d / "character.json"

def _current():
    try:
        return json.loads(_state_path().read_text(encoding="utf-8")).get("id", "silver_wolf")
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return "silver_wolf"

def _set_current(cid):
    _state_path().write_text(json.dumps({"id": cid}, ensure_ascii=False), encoding="utf-8")

def _frames_count(folder):
    if not folder.is_dir(): return 0
    return len(list(folder.glob("*.png")))

def _list_chars():
    root = _app_root()
    out = []
    default_stand = root / "assets" / "stand"
    out.append({"id": "silver_wolf", "name": "银狼", "frames": _frames_count(default_stand),
                "builtin": True, "dir": str(default_stand)})
    base = root / "characters"
    if base.is_dir():
        for folder in sorted(p for p in base.iterdir() if p.is_dir()):
            spec = {}
            try:
                spec = json.loads((folder / "character.json").read_text(encoding="utf-8"))
            except (FileNotFoundError, json.JSONDecodeError, OSError):
                pass
            stand = folder / "stand"
            out.append({"id": folder.name, "name": spec.get("name") or folder.name,
                        "frames": _frames_count(stand), "builtin": False, "dir": str(stand)})
    return out

def handle(msg):
    t = msg.get("t")
    if t == "hello":
        return {"t": "reply", "ok": True, "intents": INTENTS,
                "description": "列角色包、按磁盘统计帧数、切换角色"}
    if t != "ask":
        return {"t": "reply", "ok": False, "error": "未知消息类型"}
    intent = msg.get("intent", "")
    if intent not in INTENTS:
        return {"t": "reply", "ok": False, "error": "不支持的意图：" + str(intent)}
    args = msg.get("args") or {}
    txt = str(args.get("text") or args.get("query") or "")
    op = str(args.get("action") or "list").lower()
    chars = _list_chars()
    cur = _current()
    wants_switch = (op in ("switch", "set", "切换", "换") or
                    any(k in txt for k in ("切换", "换成", "换角色", "选", "用")))
    if wants_switch:
        target = str(args.get("id") or args.get("name") or "").strip()
        if not target:
            for c in sorted(chars, key=lambda c: len(c["name"]), reverse=True):
                if c["name"] in txt or c["id"] in txt:
                    target = c["id"]
                    break
        if not target:
            return {"t": "reply", "ok": False, "error": "请说要切换的角色，比如「切换到银狼」"}
        hit = next((c for c in chars if c["id"] == target or c["name"] == target), None)
        if not hit:
            return {"t": "reply", "ok": False, "error": f"没找到角色：{target}"}
        if hit["frames"] == 0:
            return {"t": "reply", "ok": False, "error": f"角色「{hit['name']}」素材未就位（0 帧），不能切换"}
        _set_current(hit["id"])
        return {"t": "reply", "ok": True, "text": f"已切到「{hit['name']}」",
                "character": hit, "intent_payload": {"type": "switch_character", "id": hit["id"]}}
    # list
    lines = []
    for c in chars:
        mark = "●" if c["id"] == cur else "○"
        frames = f"{c['frames']} 帧" if c["frames"] else "素材未就位"
        lines.append(f"{mark} {c['name']}（{frames}）")
    return {"t": "reply", "ok": True,
            "text": "现有角色：" + "；".join(lines), "characters": chars, "current": cur}

if __name__ == "__main__":
    try:
        line = sys.stdin.readline()
        msg = json.loads(line) if line.strip() else {}
        reply = handle(msg)
    except Exception as exc:
        reply = {"t": "reply", "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
