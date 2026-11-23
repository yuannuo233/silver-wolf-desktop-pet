"""Level 3 interop bridge (see PROTOCOL.md section 6).

Two directions, one JSON object per line:

  in   <APPDATA>/SilverWolfPet/interop/inbox.jsonl    a host app appends events here
  out  <APPDATA>/SilverWolfPet/interop/outbox.jsonl   this app appends state/chat events

Why files instead of a socket: zero dependencies, works across users and elevation levels,
and a host written in anything (Node, Python, C++, a shell script) can use it with one
open() call. A trailing partial line is tolerated, so writers do not need to lock.
"""

import json
import os
import threading
import time
from pathlib import Path

POLL_S = 0.25


def interop_dir() -> Path:
    base = Path(os.environ.get("APPDATA", Path.home() / ".config")) / "SilverWolfPet"
    return base / "interop"


class Interop:
    """Watches inbox.jsonl and forwards parsed events to the pet; writes outbox.jsonl."""

    def __init__(self, pet):
        self.pet = pet
        self.dir = interop_dir()
        self.inbox = self.dir / "inbox.jsonl"
        self.outbox = self.dir / "outbox.jsonl"
        self._in_pos = 0
        self._stop = threading.Event()
        self._thread = None
        self._out_lock = threading.Lock()

    # ---------- lifecycle ----------

    def start(self):
        try:
            self.dir.mkdir(parents=True, exist_ok=True)
            # Start at the end of the existing inbox: replaying stale events would make the
            # pet react to whatever happened before this launch.
            if self.inbox.exists():
                self._in_pos = self.inbox.stat().st_size
            else:
                self.inbox.touch()
            self.outbox.touch()
        except OSError:
            return False
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self.send({"t": "hello", "spec": "pet-interop/1",
                   "levels": ["L1", "L3"],
                   "states": sorted(getattr(self.pet, "anim", {}) or {}),
                   "accepts": ["activity", "say", "play", "move_to", "theme"]})
        return True

    def stop(self):
        self._stop.set()

    def _loop(self):
        while not self._stop.is_set():
            try:
                self._drain()
            except Exception:
                pass                       # never let the bridge kill the pet
            time.sleep(POLL_S)

    # ---------- inbound ----------

    def _drain(self):
        if not self.inbox.exists():
            return
        size = self.inbox.stat().st_size
        if size < self._in_pos:            # truncated/rotated by the host
            self._in_pos = 0
        if size == self._in_pos:
            return
        with self.inbox.open("r", encoding="utf-8", errors="replace") as f:
            f.seek(self._in_pos)
            chunk = f.read()
            self._in_pos = f.tell()
        for line in chunk.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue                   # half-written line; ignore
            if isinstance(ev, dict):
                self._handle(ev)

    def _handle(self, ev):
        kind = ev.get("t")
        # GUI mutation must happen on the Tk thread.
        self.pet.win.after(0, lambda: self._apply(kind, ev))

    def _apply(self, kind, ev):
        pet = self.pet
        try:
            if kind == "activity":
                value = ev.get("value")
                if value in ("type", "typing"):
                    # Take ownership so the local foreground probe stops overwriting this.
                    pet._host_activity = True
                    pet._act_state = "typing"
                    pet.set_anim_state("typing")
                elif value in ("game", "console"):
                    pet._host_activity = True
                    pet._act_state = "console"
                    pet.set_anim_state("console")
                else:
                    pet._host_activity = False
                    pet._act_state = None
                    pet.set_anim_state("idle")
            elif kind == "say":
                pet.show_bubble(str(ev.get("text", ""))[:280],
                                int(ev.get("duration_ms", 4000)))
            elif kind == "play":
                pet.play_action(ev.get("state", ""))
            elif kind == "move_to":
                pet._start_goto(int(ev.get("x", 0)), int(ev.get("y", 0)))
            elif kind == "theme":
                if pet.on_theme_request is not None:
                    pet.on_theme_request(str(ev.get("value", "light")))
        except Exception:
            pass

    # ---------- outbound ----------

    def send(self, obj):
        try:
            line = json.dumps(obj, ensure_ascii=False) + "\n"
        except (TypeError, ValueError):
            return
        try:
            with self._out_lock:
                with self.outbox.open("a", encoding="utf-8") as f:
                    f.write(line)
        except OSError:
            pass
