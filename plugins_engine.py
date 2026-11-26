"""Plugin engine: discover, launch and talk to plugins.

What this is, in plain words:
  A plugin is a tiny separate program. We send it one JSON question on stdin,
  it answers one JSON line on stdout, then it exits. Like passing a note to a
  shopkeeper and getting a note back.

Why a separate program instead of importing Python code:
  - a broken plugin cannot crash the pet (it is a different process)
  - a hanging plugin can be killed after a timeout
  - the plugin can be written in ANY language, not just Python
  - this is the same stdin/stdout transport MCP uses, so upgrading later is easy

Protocol (one JSON object per line):
  ask   {"t":"ask", "id":"...", "intent":"weather", "args":{...}}
  reply {"t":"reply", "id":"...", "ok":true, "text":"..."}
  hello {"t":"hello"}  -> plugin reports its capabilities
"""

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

TIMEOUT_S = 15          # kill a plugin that takes too long
HELLO_TIMEOUT_S = 5


def app_dir() -> Path:
    """The directory that contains the app (source folder or the folder holding the exe)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


PLUGINS_DIR = app_dir() / "plugins"

MANIFEST = "plugin.json"


def list_plugins() -> list:
    """Scan plugins/. Returns manifests with an added 'dir' and 'available' flag.

    A folder is a plugin when it has plugin.json. Broken folders are skipped so one bad
    plugin never hides the others.
    """
    out = []
    if not PLUGINS_DIR.is_dir():
        return out
    for folder in sorted(PLUGINS_DIR.iterdir()):
        if not folder.is_dir():
            continue
        mf = folder / MANIFEST
        if not mf.exists():
            continue
        try:
            data = json.loads(mf.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not data.get("id"):
                continue
        except (OSError, ValueError):
            continue
        data["dir"] = str(folder)
        data["available"] = (folder / (data.get("entry") or "main.py")).exists()
        out.append(data)
    return out


def read_hello(plugin: dict) -> dict:
    """Ask a plugin what it can do. Returns its hello reply or an error dict."""
    return _call(plugin, {"t": "hello"}, timeout=HELLO_TIMEOUT_S)


def ask(plugin: dict, intent: str, args: dict = None) -> dict:
    """Send one question to a plugin and return its answer."""
    return _call(plugin, {
        "t": "ask",
        "id": uuid.uuid4().hex,
        "intent": intent,
        "args": args or {},
    }, timeout=TIMEOUT_S)


def _python_exe() -> str:
    """A real Python interpreter for running plugin scripts.

    In a PyInstaller onefile build sys.executable is the pet exe itself, not Python:
    launching it with a script argument just opens a second pet window that never answers
    stdin, so every plugin "times out". Prefer an installed python found on PATH; fall back
    to sys.executable only when we are genuinely running from source.
    """
    if not getattr(sys, "frozen", False):
        return sys.executable
    import shutil
    for name in ("python", "python3", "py"):
        found = shutil.which(name)
        if found:
            return found
    # PATH 里没有时，试几个常见安装位置（用户机器不一定把 Python 加进 PATH）
    import os
    local = os.environ.get("LOCALAPPDATA", "")
    cands = []
    if local:
        base = Path(local) / "Programs" / "Python"
        if base.is_dir():
            cands += sorted(base.glob("Python*/python.exe"), reverse=True)
    cands += [Path(r"C:\Python313\python.exe"), Path(r"C:\Python312\python.exe"),
              Path(r"C:\Python311\python.exe"), Path(r"C:\Python310\python.exe")]
    for c in cands:
        if c.exists():
            return str(c)
    return ""


def _call(plugin: dict, payload: dict, timeout: int) -> dict:
    """Launch the plugin, write one line, read one line, always clean up."""
    entry = plugin.get("entry") or "main.py"
    exe = Path(plugin["dir"]) / entry
    if not exe.exists():
        return {"t": "reply", "ok": False, "error": "找不到入口文件: %s" % entry}

    # Which python to use: a real interpreter (see _python_exe). For non-Python plugins the
    # manifest can set "command" to a full command line, e.g. ["node", "index.js"].
    cmd = plugin.get("command")
    if cmd:
        argv = list(cmd)
        if "{entry}" in argv:
            argv = [str(exe) if a == "{entry}" else a for a in argv]
    else:
        py = _python_exe()
        if not py:
            return {"t": "reply", "ok": False,
                    "error": "这台电脑没装 Python，跑不了 .py 插件。装一个 Python 3 并勾选 Add to PATH，或让插件作者提供 exe 版（plugin.json 里写 command）。"}
        argv = [py, str(exe)]

    try:
        p = subprocess.Popen(
            argv,
            cwd=str(exe.parent),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
    except OSError as e:
        return {"t": "reply", "ok": False, "error": "启动失败: %s" % e}

    try:
        line = json.dumps(payload, ensure_ascii=False) + "\n"
        out, _err = p.communicate(input=line, timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        p.communicate()
        return {"t": "reply", "ok": False, "error": "插件超时（%d 秒）" % timeout}
    except Exception as e:
        p.kill()
        return {"t": "reply", "ok": False, "error": "通信失败: %s" % e}

    for raw in (out or "").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            msg = json.loads(raw)
            if isinstance(msg, dict):
                return msg
        except ValueError:
            continue
    return {"t": "reply", "ok": False, "error": "插件没有返回合法 JSON（stderr: %s）"
            % (_err or "")[:120]}
