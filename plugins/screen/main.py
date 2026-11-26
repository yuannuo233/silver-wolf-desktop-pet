"""截屏插件：截屏存 PNG，OCR 可选。缺依赖时明确降级，不让插件崩。"""
import json, sys, os
from datetime import datetime
from pathlib import Path

INTENTS = ["screenshot", "截图", "截屏", "ocr", "屏幕"]

def _out_dir(custom=None):
    if custom:
        d = Path(custom).expanduser()
    else:
        base = os.environ.get("APPDATA")
        d = (Path(base) if base else Path.home() / ".config") / "SilverWolfPet" / "plugins" / "screen" / "screenshots"
    d.mkdir(parents=True, exist_ok=True)
    return d

def _capture(out_dir=None, filename=None):
    d = _out_dir(out_dir)
    name = filename or ("screen_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    path = d / (name + ".png")
    # 方案 A：mss（跨平台、快）
    try:
        import mss
        from PIL import Image
        with mss.mss() as sct:
            mon = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
            raw = sct.grab(mon)
            img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
            img.save(path, format="PNG")
        return {"ok": True, "path": str(path.resolve()), "width": img.width,
                "height": img.height, "bytes": path.stat().st_size, "via": "mss"}
    except ImportError:
        pass
    except Exception as exc:
        return {"ok": False, "error": f"mss 截屏失败：{exc}"}
    # 方案 B：Pillow ImageGrab（Windows/macOS）
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        img.save(path, format="PNG")
        return {"ok": True, "path": str(path.resolve()), "width": img.width,
                "height": img.height, "bytes": path.stat().st_size, "via": "ImageGrab"}
    except ImportError:
        pass
    except Exception as exc:
        return {"ok": False, "error": f"ImageGrab 截屏失败：{exc}"}
    # 都没有：明确降级
    return {"ok": True, "degraded": True, "path": None,
            "text": "这台机器没装截屏依赖。装一下 mss 和 Pillow 就能用：pip install mss pillow",
            "message": "缺少 mss / Pillow，截屏能力未启用"}

def _ocr(lang, out_dir):
    shot = _capture(out_dir)
    if not shot.get("ok"):
        return shot
    if shot.get("degraded"):
        return shot
    import shutil
    if shutil.which("tesseract") is None:
        return {"ok": True, "ocr_available": False, "image_path": shot["path"],
                "text": "截图已存好，但本机没装 Tesseract，认不出字。装了再把 tesseract.exe 加进 PATH 就能用。",
                "degraded": True}
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(shot["path"])
        text = pytesseract.image_to_string(img, lang=lang).strip()
        return {"ok": True, "ocr_available": True, "text": text or "图上没认出文字",
                "image_path": shot["path"], "lang": lang}
    except Exception as exc:
        return {"ok": True, "ocr_available": False, "image_path": shot["path"],
                "text": "OCR 执行失败：" + str(exc)[:60], "degraded": True}

def handle(msg):
    t = msg.get("t")
    if t == "hello":
        return {"t": "reply", "ok": True, "intents": INTENTS,
                "description": "截屏存 PNG；OCR 需装 Tesseract，缺依赖时降级"}
    if t != "ask":
        return {"t": "reply", "ok": False, "error": "未知消息类型"}
    intent = msg.get("intent", "")
    if intent not in INTENTS:
        return {"t": "reply", "ok": False, "error": "不支持的意图：" + str(intent)}
    args = msg.get("args") or {}
    out_dir = args.get("out_dir")
    if intent in ("ocr", "屏幕") or args.get("ocr"):
        r = _ocr(args.get("lang") or "eng", out_dir)
    else:
        r = _capture(out_dir, args.get("filename"))
    if not r.get("ok"):
        return {"t": "reply", "ok": False, "error": r.get("error")}
    text = r.get("text") or ("截图已保存到 " + str(r.get("path")) if r.get("path") else r.get("message", ""))
    return {"t": "reply", "ok": True, "text": text, **r}

if __name__ == "__main__":
    try:
        line = sys.stdin.readline()
        msg = json.loads(line) if line.strip() else {}
        reply = handle(msg)
    except Exception as exc:
        reply = {"t": "reply", "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
