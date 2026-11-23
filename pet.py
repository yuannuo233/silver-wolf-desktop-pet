"""Silver Wolf desktop pet — the floating sprite layer.

Since v0.3 the pet is a Toplevel child of the main window (app.py),
not a standalone Tk root. It can still do everything on its own:
    left click    -> offline one-liner
    double click  -> quick chat input window
    drag          -> move
    right click   -> menu (main window / hide / settings / size / quit)
"""

import base64
import ctypes
import io
import json
import math
import os
import random
import threading
import time
import tkinter as tk
from ctypes import wintypes
from pathlib import Path

import ai_client
import config
import lines
from ui import C

KEY_COLOR = "magenta"
IDLE_AMPLITUDE = 3
IDLE_SPEED_MS = 60
BUBBLE_MS = 5000
AI_BUBBLE_MS = 9000
FONT = ("Microsoft YaHei UI", 11)
FONT_SMALL = ("Microsoft YaHei UI", 9)
HISTORY_LIMIT = 6

SIZE_PRESETS = [("迷你", 100), ("小", 140), ("标准", 200), ("大", 280), ("特大", 400)]

# Right-click actions: play once, then return to idle.
ACTIONS = (("wave", "挥手打招呼"), ("doze", "打个盹"), ("stretch", "伸个懒腰"), ("lollipop", "吃棒棒糖"))

# Speed (px/s) at which she runs to the drop point. One run cycle is 0.756s, so
# 320px/s matches the stride of those short legs — neither too fast nor too slow.
RUN_SPEED = 320
GOTO_MIN_DIST = 8         # closer than this, snap to the point instead of running.

# These games in front -> she pulls out a handheld (lowercase substring match on the exe).
GAME_EXES = ("starrail", "genshin", "zenless", "arknights", "steam", "epicgames",
             "battle.net", "league", "valorant", "cs2", "dota", "minecraft",
             "phigros", "musedash")
# Desktop / Explorer is not work: clicking around the desktop must not make her type.
SHELL_EXES = ("explorer.exe",)

ACTIVITY_MS = 1200        # how often the foreground window is checked.
TYPING_GAP_S = 2.5        # a keystroke this recent means you are typing.

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def _foreground_exe():
    """Return (foreground exe name, lowercased, pid). ("", 0) when unavailable."""
    try:
        u32, k32 = ctypes.windll.user32, ctypes.windll.kernel32
        hwnd = u32.GetForegroundWindow()
        if not hwnd:
            return "", 0
        pid = wintypes.DWORD()
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        h = k32.OpenProcess(0x1000, False, pid.value)   # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return "", pid.value
        try:
            buf = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(1024)
            if k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
                return Path(buf.value).name.lower(), pid.value
        finally:
            k32.CloseHandle(h)
        return "", pid.value
    except Exception:
        return "", 0


def _input_idle_seconds():
    """Seconds since the last keyboard or mouse input."""
    class _LII(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("dwTime", wintypes.DWORD)]
    try:
        info = _LII(ctypes.sizeof(_LII), 0)
        if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
            return 0.0
        return max(0.0, ((ctypes.windll.kernel32.GetTickCount() - info.dwTime) & 0xFFFFFFFF) / 1000.0)
    except Exception:
        return 0.0


# --- Keyboard hook: we only care about the time of the last keystroke ---
# GetLastInputInfo cannot tell keys from mouse moves, so on its own it reads mouse-only
# activity as typing. A low-level keyboard hook records a timestamp and passes events on.
_WH_KEYBOARD_LL = 13
_WM_KEYDOWN, _WM_SYSKEYDOWN = 0x0100, 0x0104
_key_ts = [0.0]           # monotonic time of the last key press.
_key_hook = [None, None]  # [handle, callback]; keep the callback alive or the system crashes.

# The hook chain must pass events through, and lParam is a 64-bit pointer: without
# explicit argtypes ctypes converts it as c_int, overflows, and keystrokes stop flowing.
_u32 = ctypes.windll.user32
_u32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                wintypes.WPARAM, ctypes.c_void_p]
_u32.CallNextHookEx.restype = ctypes.c_ssize_t


def _install_key_hook() -> bool:
    if _key_hook[0] is not None:
        return True
    try:
        def _cb(n_code, w_param, l_param):
            if n_code >= 0 and w_param in (_WM_KEYDOWN, _WM_SYSKEYDOWN):
                _key_ts[0] = time.monotonic()
            try:
                return _u32.CallNextHookEx(None, n_code, w_param, l_param)
            except Exception:
                return 0           # never swallow a key, even if passing it on failed.
        cb = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int,
                                wintypes.WPARAM, ctypes.c_void_p)(_cb)
        handle = _u32.SetWindowsHookExW(_WH_KEYBOARD_LL, cb, None, 0)
        if not handle:
            return False
        _key_hook[0], _key_hook[1] = handle, cb
        return True
    except Exception:
        return False


def _key_idle_seconds():
    """Seconds since the last keystroke; None when the hook is not installed."""
    if _key_hook[0] is None:
        return None
    if _key_ts[0] <= 0.0:
        return 1e9
    return time.monotonic() - _key_ts[0]


def _typing_now() -> bool:
    """Are you typing? Prefer the keyboard hook; fall back to any input activity."""
    key = _key_idle_seconds()
    gap = TYPING_GAP_S if key is not None else 1.5
    return (key if key is not None else _input_idle_seconds()) <= gap


class SilverWolfPet:
    """The floating sprite + interactions + idle animation + AI chat."""

    def __init__(self, owner: tk.Tk, image_path: str, hd_path: str = None):
        self.owner = owner            # the main window (destroying it quits all)
        self.base_path = image_path
        self.hd_path = hd_path
        self.settings = config.load()
        self.history = []
        self.on_chat_event = None     # callback(role, text) -> main chat page log
        self.on_open_main = None      # callback() -> raise the main window
        self.settings_win = None
        self.chat_win = None         # quick-chat card from double-click (must exist before use).
        self.chat_entry = None
        self.bubble_job = None
        self.bob_phase = 0.0
        self.drag_offset = (0, 0)
        self.dragged = False
        self.anim = None              # frame animation state machine {state: [(photo, ms), ...]}
        self.anim_state = "idle"
        self.anim_idx = 0
        self.anim_size = None
        self._drag_job = None
        self._last_drag_x = None
        self._dir_acc = 0            # accumulated drag direction, prevents left/right jitter.
        self._cur_photo = None       # the image on screen; skip the redraw when unchanged.
        self.anim_once = set()       # states that play once then return to idle (actions, turns).
        self._pending_run = None     # direction to run after the turn transition finishes.
        self._turning = False        # playing a turn transition; do not interrupt it with a run.
        self._click_job = None       # delayed single-click check (so a double-click can cancel it).
        self._act_state = None       # follow-activity state: None / typing / console.
        self._goto_target = None     # drop point she runs to at her own speed.
        self._goto_job = None
        self._goto_t = 0.0

        # --- the pet lives in its own frameless Toplevel window ---
        self.win = tk.Toplevel(owner)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-transparentcolor", KEY_COLOR)
        self.win.configure(bg=KEY_COLOR)

        self.canvas = tk.Canvas(self.win, bg=KEY_COLOR, highlightthickness=0)
        self.canvas.pack()
        self.sprite = None
        self._load_sprite(int(self.settings.get("size_height", 200)))

        # v0.4: load the multi-frame animation from frames.json, fall back to single-frame floating.
        self.anim_state = "idle"
        self.anim_idx = 0
        self.anim = None
        self.anim_size = None
        self._drag_job = None
        self._last_drag_x = None
        self._load_anim()
        if self.anim:
            self.width, self.canvas_h = self.anim_size
            self.canvas.configure(width=self.width, height=self.canvas_h)
            self.canvas.coords(self.sprite, self.width // 2, self.canvas_h // 2)
            self.canvas.itemconfigure(self.sprite, image=self.anim["idle"][0][0])

        self._bind_events()
        self._make_menu()
        self._make_bubble()
        self._place_window()
        self._start_animation()
        _install_key_hook()               # only used to detect typing; degrades silently if it fails.
        self.win.after(ACTIVITY_MS, self._watch_activity)
        self.win.after(600, lambda: self.show_bubble(lines.GREETING, AI_BUBBLE_MS))

    # ---------- sprite & size ----------

    def _load_sprite(self, target_height: int):
        src = self.hd_path or self.base_path
        if HAS_PIL:
            img = Image.open(src).convert("RGBA")
            scale = target_height / img.height
            size = (max(1, round(img.width * scale)), target_height)
            img = img.resize(size, Image.LANCZOS)
            alpha = img.getchannel("A").point(lambda a: 255 if a >= 128 else 0)
            img.putalpha(alpha)
            buf = io.BytesIO()
            img.save(buf, "PNG")
            self.photo = tk.PhotoImage(data=base64.b64encode(buf.getvalue()))
        else:
            photo = tk.PhotoImage(file=self.base_path)
            ratio = target_height / photo.height()
            if ratio <= 0.6:
                self.photo = photo.subsample(2)
            elif ratio <= 1.1:
                self.photo = photo
            elif ratio <= 1.6:
                self.photo = photo.zoom(3).subsample(2)
            elif ratio <= 2.2:
                self.photo = photo.zoom(2)
            else:
                self.photo = photo.zoom(3)

        self.width = self.photo.width()
        self.height = self.photo.height()
        self.canvas_h = self.height + 2 * IDLE_AMPLITUDE
        self.canvas.configure(width=self.width, height=self.canvas_h)
        if self.sprite is None:
            self.sprite = self.canvas.create_image(
                self.width // 2, self.canvas_h // 2, image=self.photo
            )
        else:
            self.canvas.itemconfigure(self.sprite, image=self.photo)
            self.canvas.coords(self.sprite, self.width // 2, self.canvas_h // 2)
            x, y = self.win.winfo_x(), self.win.winfo_y()
            self.win.geometry(f"{self.width}x{self.canvas_h}+{x}+{y}")

    def set_size(self, target_height: int):
        self.settings["size_height"] = target_height
        config.save(self.settings)
        if self.anim is not None:
            self._load_anim()   # rescale the frame animation for the new size.
            self.width, self.canvas_h = self.anim_size
            self.canvas.configure(width=self.width, height=self.canvas_h)
            self.canvas.coords(self.sprite, self.width // 2, self.canvas_h // 2)
            x, y = self.win.winfo_x(), self.win.winfo_y()
            self.win.geometry(f"{self.width}x{self.canvas_h}+{x}+{y}")
        else:
            self._load_sprite(target_height)

    # ---------- Frame animation engine (v0.4) ----------

    def _load_anim(self):
        """Read assets/stand/frames.json: idle / drag / run_right / run_left state machine.

        Each frame is a 190x216 transparent PNG, scaled to the current size with a binary alpha edge.
        Any failure falls back to single-frame floating — the pet must always start.
        """
        self.anim = None
        if not HAS_PIL:
            return
        try:
            stand = Path(self.base_path).parent / "stand"
            spec = json.loads((stand / "frames.json").read_text(encoding="utf-8"))
            cw, ch = spec["sprite"]["canvas_width"], spec["sprite"]["canvas_height"]
            scale = int(self.settings.get("size_height", 200)) / 200.0
            target = (max(1, round(cw * scale)), max(1, round(ch * scale)))
            states = {}
            once = set()
            for state, sdef in spec["states"].items():
                seq = []
                for fr in sdef["frames"]:
                    try:
                        img = Image.open(stand / fr["file"]).convert("RGBA")
                    except Exception:
                        continue        # skip a broken frame; one bad file must not kill the whole animation.
                    # ★ Always scale to the declared canvas size!
                    # Frames may be 2x (380x432) while the canvas declares 190x216 —
                    # unscaled, the head and feet fall outside the canvas and get clipped (the "headless" bug).
                    if img.size != target:
                        img = img.resize(target, Image.LANCZOS)
                    alpha = img.getchannel("A").point(lambda a: 255 if a >= 128 else 0)
                    img.putalpha(alpha)
                    buf = io.BytesIO()
                    img.save(buf, "PNG")
                    seq.append((tk.PhotoImage(data=base64.b64encode(buf.getvalue())),
                                fr["duration_ms"]))
                if seq:                 # never register empty states, or switching raises IndexError.
                    states[state] = seq
                    if not sdef.get("loop", True):
                        once.add(state)
            self.anim = states or None
            self.anim_once = once
            self.anim_size = target
        except Exception:
            self.anim = None   # missing assets or a broken file -> quietly fall back to single-frame.

    # ---------- Running to the drop point after release ----------
    #
    # Dragging is aiming, not moving: the window stays put, she turns in place to face the
    # drag direction, and only on release does she run to the drop point at her own speed
    # (RUN_SPEED), then settle back to idle. The window deliberately does not follow the
    # cursor — that is the whole point of this model.

    def _start_goto(self, x, y):
        if not self.anim:                 # no-Pillow fallback: snap straight to the point.
            self.win.geometry(f"+{x}+{y}")
            return
        self._goto_target = (x, y)
        self._goto_t = time.monotonic()
        dx = x - self.win.winfo_x()
        self._start_run("run_right" if dx >= 0 else "run_left")
        if self._goto_job is None:
            self._goto_job = self.win.after(16, self._goto_tick)

    def _goto_tick(self):
        self._goto_job = None
        tgt = self._goto_target
        if tgt is None:
            return
        # another state (right-click action etc.) took over -> drop the auto-run, no zombie target.
        if self.anim_state not in ("run_right", "run_left", "turn_right", "turn_left"):
            self._goto_target = None
            return
        now = time.monotonic()
        dt = min(0.05, now - self._goto_t)
        self._goto_t = now
        # no movement until the turn transition finishes (fixes moving while turning).
        if not self._turning and self.anim_state in ("run_right", "run_left"):
            x, y = self.win.winfo_x(), self.win.winfo_y()
            dx, dy = tgt[0] - x, tgt[1] - y
            dist = math.hypot(dx, dy)
            step = RUN_SPEED * dt
            if dist <= max(step, 2):
                self.win.geometry(f"+{tgt[0]}+{tgt[1]}")
                self._goto_target = None
                self._pending_run = None
                self.set_anim_state("idle")
                return
            self.win.geometry(f"+{round(x + dx / dist * step)}+{round(y + dy / dist * step)}")
        self._goto_job = self.win.after(16, self._goto_tick)

    def _cancel_goto(self):
        self._goto_target = None
        if self._goto_job is not None:
            try:
                self.win.after_cancel(self._goto_job)
            except tk.TclError:
                pass
            self._goto_job = None

    def _do_click(self):
        """Single click without a drag -> say a line."""
        self._click_job = None
        self.speak()

    def set_anim_state(self, state):
        """Switch animation state (idle / run_right / run_left / turn / action)."""
        if self.anim and state in self.anim and state != self.anim_state:
            self.anim_state = state
            self.anim_idx = 0

    def _start_run(self, state):
        """Start aiming with a turn from idle, then run; if already running, just flip direction.

        The turn (turn_right / turn_left) is one-shot; when it ends it chains to _pending_run.
        This is what makes dragging feel like aiming: she turns on the spot to face where you
        are pulling, and the window does not move until you release.
        """
        if self.anim_state == state or self._turning:
            return
        turn = "turn_right" if state == "run_right" else "turn_left"
        if self.anim_state == "idle" and turn in self.anim:
            self._turning = True
            self._pending_run = state
            self.anim_state = turn
            self.anim_idx = 0
            return
        self.set_anim_state(state)

    def play_action(self, state):
        """Right-click action: play once then return to idle (repeatable)."""
        if not self.anim or state not in self.anim:
            return
        self._pending_run = None
        self._turning = False
        self.anim_state = state
        self.anim_idx = 0

    def _start_animation(self):
        if self.anim:
            self._tick_anim()
        else:
            self._bob()

    def _tick_anim(self):
        seq = self.anim[self.anim_state]
        photo, ms = seq[self.anim_idx]
        if photo is not self._cur_photo:      # skip the redraw when the frame is unchanged.
            self.canvas.itemconfigure(self.sprite, image=photo)
            self._cur_photo = photo
        nxt = self.anim_idx + 1
        if nxt < len(seq):
            self.anim_idx = nxt
        elif self.anim_state in self.anim_once:
            # one-shot states end here: turn -> run in the pending direction; action -> idle.
            if self._pending_run and self._pending_run in self.anim:
                self.anim_state = self._pending_run
                self._pending_run = None
                self._turning = False
            else:
                self.anim_state = "idle"
            self.anim_idx = 0
        else:
            self.anim_idx = 0
        self.win.after(ms, self._tick_anim)

    def show(self):
        """Re-summon the pet (after 'hide')."""
        self.win.deiconify()

    def set_on_top(self, on):
        """Lower the pet while the main window is in front so it never covers the chat log."""
        try:
            self.win.attributes("-topmost", bool(on))
        except tk.TclError:
            pass

    # ---------- Follow my activity (typing / console) ----------
    #
    # Cadence: look at the foreground window every 1.2s, and only take over while idle:
    #   · keys pressed in any app                        -> typing: she types on a glowing keyboard
    #   · a game in front (Star Rail / Genshin / Steam)  -> console: she plays a handheld
    #   · anything else / no keystrokes / the pet itself  -> back to idle
    # Dragging, turning and one-shot actions never touch her state — they win over this.

    def _watch_activity(self):
        try:
            self._apply_activity()
        except Exception:
            pass
        try:
            self.win.after(ACTIVITY_MS, self._watch_activity)
        except tk.TclError:
            pass                       # window destroyed, stop polling.

    def _apply_activity(self):
        if not self.anim or not self.settings.get("follow_activity", True):
            return
        if self.dragged or self._turning or self.anim_state not in ("idle", "typing", "console"):
            return                     # dragging or a one-shot action is playing, do not take over.
        exe, pid = _foreground_exe()
        want = None
        if exe and pid != os.getpid() and exe not in SHELL_EXES:
            if any(g in exe for g in GAME_EXES):
                want = "console"      # you are gaming -> she plays her handheld.
            elif _typing_now():
                want = "typing"       # keys pressed anywhere -> she types along.
        if want not in self.anim:
            want = None
        if want == self._act_state:
            return
        self._act_state = want
        self.set_anim_state(want or "idle")

    def _toggle_follow(self):
        on = bool(self._follow_var.get())
        self.settings["follow_activity"] = on
        try:
            config.save(self.settings)
        except Exception:
            pass
        if not on:
            self._act_state = None
            if self.anim_state in ("typing", "console"):
                self.set_anim_state("idle")

    # ---------- mouse events ----------

    def _bind_events(self):
        # v0.6.13 fix for "still running in place after release": press/drag/release used to be
        # bound to that single image item, but the window flies with the mouse — drag fast and the
        # cursor leaves the item, so the release goes to another window, the pet never hears it
        # and stays in the run state (running in place). Binding on the whole canvas instead
        # (it fills the window) means any cursor inside the window delivers the release.
        for event, handler in (
            ("<ButtonPress-1>", self._on_press),
            ("<B1-Motion>", self._on_drag),
            ("<ButtonRelease-1>", self._on_release),
            ("<Button-3>", self._show_menu),
            ("<Double-Button-1>", self._on_double),
        ):
            self.canvas.bind(event, handler)

    def _on_press(self, event):
        self._cancel_goto()          # grabbed again while auto-running -> cancel it.
        self.drag_offset = (
            event.x_root - self.win.winfo_x(),
            event.y_root - self.win.winfo_y(),
        )
        self.dragged = False
        # Clear the previous drag direction on every press, otherwise dragged left then press-drag
        # right starts by judging the opposite direction — a visible jitter at the start.
        self._last_drag_x = None
        self._dir_acc = 0

    def _on_drag(self, event):
        # Safety net: if a Motion event no longer carries the left-button bit, the release was lost
        # (common when dragging fast); handle it here or she keeps running forever.
        if not (event.state & 0x100):
            self._on_release(event)
            return
        # Dragging is aiming: the window never moves here. It only counts as a drag so that the
        # release knows to issue a target instead of treating it as a click.
        if abs(event.x_root - (self.win.winfo_x() + self.drag_offset[0])) > 3 or \
           abs(event.y_root - (self.win.winfo_y() + self.drag_offset[1])) > 3:
            self.dragged = True
        self._hide_bubble()
        # Drag direction -> she turns to face it and treads in place; the accumulator keeps a
        # 1px tremor from flipping her left/right while your hand rests.
        if self.anim:
            if self._last_drag_x is not None:
                dx = event.x_root - self._last_drag_x
                if abs(dx) >= 2:
                    if abs(dx) >= 3 and abs(self._dir_acc) < 3:
                        self._dir_acc = dx * 3
                    else:
                        self._dir_acc = self._dir_acc * 0.55 + dx
                    if self._dir_acc > 5:
                        self._start_run("run_right")
                    elif self._dir_acc < -5:
                        self._start_run("run_left")
            self._last_drag_x = event.x_root

    def _on_release(self, event):
        self._last_drag_x = None
        self._dir_acc = 0
        if self.dragged:
            # Release = issue the target: she runs there at her own speed, then idles.
            tx = event.x_root - self.drag_offset[0]
            ty = event.y_root - self.drag_offset[1]
            if math.hypot(tx - self.win.winfo_x(), ty - self.win.winfo_y()) >= GOTO_MIN_DIST:
                self._start_goto(tx, ty)
            elif self.anim:
                self._pending_run = None
                self._turning = False
                self.set_anim_state("idle")
        else:
            if self.anim:
                self._pending_run = None
                self._turning = False
                self.set_anim_state("idle")
            # A single click waits a moment: a double-click cancels it.
            if self._click_job is not None:
                try:
                    self.win.after_cancel(self._click_job)
                except tk.TclError:
                    pass
            self._click_job = self.win.after(240, self._do_click)
        self.dragged = False

    def _on_double(self, _event):
        self._cancel_goto()
        if self._click_job is not None:
            try:
                self.win.after_cancel(self._click_job)
            except tk.TclError:
                pass
            self._click_job = None
        self.open_chat()

    def _show_menu(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)

    # ---------- speech bubble ----------

    def _make_bubble(self):
        self.bubble = tk.Toplevel(self.win)
        self.bubble.overrideredirect(True)
        self.bubble.attributes("-topmost", True)
        self.bubble_label = tk.Label(
            self.bubble, text="", bg=C["card"], fg=C["txt"], font=FONT,
            padx=12, pady=10, wraplength=240, justify="left",
        )
        self.bubble_label.pack()
        self.bubble.withdraw()

    def show_bubble(self, text: str, duration: int = BUBBLE_MS):
        self.bubble_label.configure(text=text)
        self.bubble.update_idletasks()
        w = self.bubble_label.winfo_reqwidth()
        h = self.bubble_label.winfo_reqheight()
        x = self.win.winfo_x() + (self.width - w) // 2
        y = self.win.winfo_y() - h - 8
        self.bubble.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.bubble.deiconify()
        if self.bubble_job is not None:
            self.win.after_cancel(self.bubble_job)
        self.bubble_job = self.win.after(duration, self._hide_bubble)

    def _hide_bubble(self):
        self.bubble.withdraw()
        self.bubble_job = None

    def speak(self):
        self.show_bubble(random.choice(lines.LINES), BUBBLE_MS)

    # ---------- chat ----------

    def refresh_theme(self):
        """Re-colour the bubble after a theme switch and drop the quick-chat card.

        The card is built once and keeps its colours, so reopening it is the cheapest way
        to make it follow the new palette.
        """
        try:
            self.bubble_label.configure(bg=C["card"], fg=C["txt"])
        except (tk.TclError, AttributeError):
            pass
        self._close_chat()

    def _close_chat(self):
        """Close the quick-chat card (and clear the handle so the next double-click rebuilds it)."""
        if self.chat_win is not None:
            try:
                self.chat_win.destroy()
            except tk.TclError:
                pass
        self.chat_win = None
        self.chat_entry = None

    def open_chat(self):
        """Quick chat card: no system title bar (that was the ugly part),
        custom dark header with drag support + close button."""
        if self.chat_win is not None:
            try:
                self.chat_win.deiconify()
                self.chat_entry.focus_set()
                return
            except tk.TclError:
                self.chat_win = None

        win = tk.Toplevel(self.win)
        win.title("和银狼聊天")
        win.overrideredirect(True)          # kill the ugly native title bar
        win.attributes("-topmost", True)
        win.configure(
            bg=C["card"],
            highlightbackground=C["line"], highlightthickness=1,
        )

        header = tk.Frame(win, bg=C["rail"])
        header.pack(fill="x")
        tk.Label(header, text="和银狼聊天", bg=C["rail"], fg=C["acc"],
                 font=FONT_SMALL).pack(side="left", padx=10, pady=6)
        close = tk.Label(header, text="✕", bg=C["rail"], fg=C["dim"],
                         font=FONT_SMALL, cursor="hand2")
        close.pack(side="right", padx=10, pady=4)
        close.bind("<Button-1>", lambda _e: self._close_chat())

        row = tk.Frame(win, bg=C["card"])
        row.pack(fill="x", padx=10, pady=10)
        entry = tk.Entry(
            row, width=30, font=FONT, bg=C["field"], fg=C["txt"],
            insertbackground=C["txt"], relief="flat",
        )
        entry.pack(side="left", ipady=5, padx=(0, 8))
        tk.Button(
            row, text="发送", font=FONT, bg=C["acc"], fg=C["on_acc"],
            relief="flat", width=6,
            command=lambda: self.send_chat_text(entry.get()),
        ).pack(side="left")
        entry.bind("<Return>", lambda _event: self.send_chat_text(entry.get()))
        entry.bind("<Escape>", lambda _e: self._close_chat())
        self.chat_win = win
        self.chat_entry = entry
        entry.focus_set()

        # place right under the pet, and make the header drag the window
        win.update_idletasks()
        w = win.winfo_reqwidth()
        x = self.win.winfo_x() + (self.width - w) // 2
        y = self.win.winfo_y() + self.canvas_h + 6
        win.geometry(f"+{max(x, 0)}+{max(y, 0)}")

        drag = {"x": 0, "y": 0}

        def start_move(event):
            drag["x"] = event.x_root - win.winfo_x()
            drag["y"] = event.y_root - win.winfo_y()

        def do_move(event):
            win.geometry(f"+{event.x_root - drag['x']}+{event.y_root - drag['y']}")

        header.bind("<ButtonPress-1>", start_move)
        header.bind("<B1-Motion>", do_move)

    def send_chat_text(self, text):
        """Send one user message (from the quick card OR the main chat page)."""
        text = (text or "").strip()
        if not text:
            return
        cfg = config.load()
        if not cfg["base_url"] or not cfg["model"]:
            msg = random.choice(lines.NO_CONFIG_LINES)
            self.show_bubble(msg, AI_BUBBLE_MS)
            self._emit("assistant", msg)
            return
        self.show_bubble("嗯……等我想一下。", AI_BUBBLE_MS)
        self._emit("user", text)
        threading.Thread(target=self._chat_worker, args=(text, cfg), daemon=True).start()

    def _chat_worker(self, text, cfg):
        try:
            reply = ai_client.chat(
                cfg["base_url"], cfg["api_key"], cfg["model"],
                cfg["prompt_text"], text, history=self.history,
            )
        except ai_client.AIError as e:
            message = "出错了：" + str(e)[:100]
            self.win.after(0, lambda: self._finish_turn(message))
            return
        self.history.append(("user", text))
        self.history.append(("assistant", reply))
        if len(self.history) > HISTORY_LIMIT:
            self.history[:] = self.history[-HISTORY_LIMIT:]
        self.win.after(0, lambda: self._finish_turn(reply))

    def _finish_turn(self, text):
        self.show_bubble(text, AI_BUBBLE_MS)
        self._emit("assistant", text)

    def _emit(self, role, text):
        """Forward chat events to the main window's chat page (if attached)."""
        if self.on_chat_event is not None:
            try:
                self.on_chat_event(role, text)
            except tk.TclError:
                pass  # the log widget is gone; bubble still works

    # ---------- menus / windows ----------

    def open_settings(self):
        import settings

        if self.settings_win is not None:
            try:
                self.settings_win.deiconify()
                self.settings_win.panel.refresh()
                return
            except tk.TclError:
                self.settings_win = None
        self.settings_win = settings.SettingsWindow(self.owner, self)

    def _open_main(self):
        if self.on_open_main is not None:
            self.on_open_main()

    def _make_menu(self):
        self.menu = tk.Menu(self.win, tearoff=0)
        self.menu.add_command(label="打开主界面", command=self._open_main)
        self.menu.add_command(label="和银狼聊天", command=self.open_chat)
        act_menu = tk.Menu(self.menu, tearoff=0)
        for key, label in ACTIONS:
            act_menu.add_command(label=label, command=lambda k=key: self.play_action(k))
        self.menu.add_cascade(label="动作", menu=act_menu)
        self._follow_var = tk.BooleanVar(value=bool(self.settings.get("follow_activity", True)))
        self.menu.add_checkbutton(
            label="跟着我做事（打字/打游戏）", variable=self._follow_var,
            command=self._toggle_follow,
        )
        self.menu.add_command(label="设置…", command=self.open_settings)
        size_menu = tk.Menu(self.menu, tearoff=0)
        for label, height in SIZE_PRESETS:
            size_menu.add_command(
                label=f"{label}（{height}px）",
                command=lambda h=height: self.set_size(h),
            )
        self.menu.add_cascade(label="尺寸", menu=size_menu)
        self.menu.add_separator()
        self.menu.add_command(label="隐藏桌宠", command=self.win.withdraw)
        self.menu.add_command(label="退出程序", command=self.owner.destroy)

    # ---------- idle animation ----------

    def _bob(self):
        self.bob_phase += 0.12
        y = self.canvas_h // 2 + IDLE_AMPLITUDE * math.sin(self.bob_phase)
        self.canvas.coords(self.sprite, self.width // 2, y)
        self.win.after(IDLE_SPEED_MS, self._bob)

    # ---------- window placement ----------

    def _place_window(self):
        self.win.geometry(f"{self.width}x{self.canvas_h}")
        self.win.update_idletasks()
        screen_w = self.win.winfo_screenwidth()
        screen_h = self.win.winfo_screenheight()
        x = screen_w - self.width - 60
        y = screen_h - self.canvas_h - 140
        self.win.geometry(f"{self.width}x{self.canvas_h}+{x}+{y}")
