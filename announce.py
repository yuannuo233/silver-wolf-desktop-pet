"""Announcements: the version notes shown in the app's 公告 page.

The text is authored by the project owner, not generated. It lives in `公告.md` next to the
code so it can be edited without touching Python, and it is packaged into the exe so users
see the same notes they read on GitHub.

Format (Markdown-ish, one section per release, newest first):

    ## v0.6.21
    186 帧重新抠图，眼白一个像素没动。

    ## v0.6.20
    角色页上线。

Only the part under the current version's heading is shown first; older ones are kept in the
same file so the page can list the history.
"""

import re
from pathlib import Path

ANNOUNCE_FILE = "公告.md"
MAX_ENTRIES = 40


def _root() -> Path:
    return Path(__file__).resolve().parent


def _find_file() -> Path:
    """The announcement file, whether running from source or from a packaged exe.

    PyInstaller onefile extracts data files into a temp folder at runtime, and
    sys._MEIPASS points there. The exe folder is also checked, so the user can drop a
    replacement next to the exe and it wins over the bundled copy.
    """
    candidates = []
    # 1) next to the exe (user-editable copy wins)
    import sys
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / ANNOUNCE_FILE)
        # 2) inside the onefile temp folder (the bundled copy)
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass) / ANNOUNCE_FILE)
    # 3) next to the source (running from source)
    candidates.append(_root() / ANNOUNCE_FILE)
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def _sections(text: str) -> list:
    """Split the file into [(version, body), ...], newest first as written in the file."""
    out = []
    # A heading line like "## v0.6.21" or "## v0.6.21 (2026-11-24)"
    pattern = re.compile(r"^##\s+(v?\d[\w.\-+]*)\s*(.*)$", re.M)
    matches = list(pattern.finditer(text))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        out.append({
            "version": m.group(1),
            "date": m.group(2).strip().strip("()"),
            "body": body,
            "lines": _lines(body),
        })
    return out


def _lines(body: str) -> list:
    """One display line per item.

    Two kinds of lines:
      · a group heading like 【素材】… -> kept as its own line, marked as a heading
      · a bullet "- xxx" or "xxx"       -> the bullet marker is dropped, the text kept
    Markdown emphasis (**bold**) is stripped for display but the text stays.
    """
    out = []
    for raw in body.splitlines():
        s = raw.strip()
        if not s:
            continue
        if s.startswith(("#", ">", "|")):
            continue
        if s.startswith(("-", "*", "·")):
            s = s[1:].strip()
        if not s:
            continue
        s = s.replace("**", "")
        # A 【…】 prefix marks a group heading. The text right after it is part of the
        # heading ("【素材】立绘重抠" is one title), so keep them together.
        if s.startswith("【") and "】" in s:
            head, _, rest = s.partition("】")
            head = head + "】"
            rest = rest.strip()
            if rest:
                head = head + " " + rest
            out.append({"text": head, "heading": True})
        else:
            out.append({"text": s, "heading": False})
    return out


def load() -> dict:
    """Read the announcement file.

    Returns {"entries": [...], "error": str|None}. Never raises: a missing or broken file
    must not stop the app from starting.
    """
    path = _find_file()
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"entries": [], "error": "没有找到公告文件（%s）" % path.name}
    except OSError as e:
        return {"entries": [], "error": "公告文件读不出来：%s" % e}
    try:
        entries = _sections(text)
    except Exception as e:
        return {"entries": [], "error": "公告格式不对：%s" % e}
    return {"entries": entries[:MAX_ENTRIES], "error": None}


def current(current_version: str) -> dict:
    """The announcement for the running version, or an empty one."""
    entries = load()["entries"]
    for e in entries:
        if e["version"].lstrip("v") == current_version.lstrip("v"):
            return e
    return {"version": current_version, "date": "", "body": "", "lines": []}


def history(current_version: str = "") -> list:
    """Every announcement, newest first, with the current version flagged."""
    out = []
    for e in load()["entries"]:
        e = dict(e)
        e["is_current"] = (e["version"].lstrip("v") == current_version.lstrip("v"))
        out.append(e)
    return out
