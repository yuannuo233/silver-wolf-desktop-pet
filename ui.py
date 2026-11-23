"""UI design system: multi-theme (light / dark / cyber) + rounded cards + pill buttons.

Plain tkinter has no rounded corners, so everything is drawn on a Canvas.
Corners are smoothed polygons; each card body is a real Frame mounted via create_window,
so pack and grid keep working inside the cards.

Theme: C is a MUTABLE dict (one shared object). apply_theme() updates it in place, so
every "from ui import C" reference follows; built widgets need one rebuild to recolour.
"""

import tkinter as tk

from config import DEFAULTS

# ---------- Themes ----------
# Keys are fixed: all three themes must stay complete (a missing key is a KeyError).
THEMES = {
    # Light: default. White base, soft grey dividers, Silver Wolf purple as the accent.
    "light": {
        "bg": "#F6F6FA",
        "rail": "#FFFFFF",
        "card": "#FFFFFF",
        "card_hi": "#F4F5FA",
        "card_hover": "#F0F1F8",
        "ghost_hi": "#E8E9F3",
        "field": "#FFFFFF",
        "line": "#E3E4EF",
        "txt": "#1A1B24",
        "sub": "#6A6D80",
        "dim": "#9DA0B0",
        "acc": "#6D4BFF",
        "acc_hi": "#8A6BFF",
        "acc_soft": "#EDE8FF",
        "on_acc": "#FFFFFF",
        "mint": "#0E9F86",
        "mint_hi": "#22C3A5",
        "mag": "#D6438F",
        "warn": "#D9822B",
        "shadow": "#00000010",
        # Outer window outline: on a white desktop a pure-white frameless window has no
        # visible edge, so a darker ring defines it. "edge" is the 1px border, "edge_in" the
        # lighter inner hairline that gives the ring a slight bevel instead of a flat line.
        "edge": "#A8AEC6",
        "edge_in": "#E4E6F0",
    },
    # Dark: the original Silver Wolf terminal look.
    "dark": {
        "bg": "#0D0E13",
        "rail": "#101119",
        "card": "#151722",
        "card_hi": "#1B1E2B",
        "card_hover": "#232739",
        "ghost_hi": "#242838",
        "field": "#12141D",
        "line": "#262A3A",
        "txt": "#E8E9F3",
        "sub": "#8C90A6",
        "dim": "#5B5F73",
        "acc": "#A98CFF",
        "acc_hi": "#C0A9FF",
        "acc_soft": "#2A2440",
        "on_acc": "#0D0E13",
        "mint": "#63E2C6",
        "mint_hi": "#8CF3DC",
        "mag": "#FF79C6",
        "warn": "#FFB86B",
        "shadow": "#00000040",
        "edge": "#3A4060",
        "edge_in": "#1C1F2C",
    },
    # Cyber: near-black with electric cyan, matching the desktop icon set.
    "cyber": {
        "bg": "#080B12",
        "rail": "#0A0E17",
        "card": "#0E1420",
        "card_hi": "#131C2B",
        "card_hover": "#182334",
        "ghost_hi": "#1A2536",
        "field": "#0B1119",
        "line": "#17283D",
        "txt": "#DCE9F5",
        "sub": "#7E95AD",
        "dim": "#526A82",
        "acc": "#3FE0D0",
        "acc_hi": "#79F2E6",
        "acc_soft": "#0C2C2E",
        "on_acc": "#04110F",
        "mint": "#5CE1C4",
        "mint_hi": "#8CF3DC",
        "mag": "#6FA8FF",
        "warn": "#FFC46B",
        "shadow": "#00000050",
        "edge": "#2A5470",
        "edge_in": "#101A26",
    },
}

THEME_LABELS = (("light", "浅色"), ("dark", "深色"), ("cyber", "赛博蓝"))
_current = DEFAULTS.get("theme", "light")

C = dict(THEMES[_current])   # ★ Mutable dict: never reassign, only clear/update.


def apply_theme(name: str) -> str:
    """Switch the global palette in place (C stays the same object). Returns the theme name."""
    global _current
    if name not in THEMES:
        name = "light"
    _current = name
    C.clear()
    C.update(THEMES[name])
    return name


def current_theme() -> str:
    return _current


F = {
    "hero": ("Microsoft YaHei UI", 22, "bold"),
    "title": ("Microsoft YaHei UI", 15, "bold"),
    "sec": ("Microsoft YaHei UI", 11, "bold"),
    "body": ("Microsoft YaHei UI", 10),
    "small": ("Microsoft YaHei UI", 9),
    "mono": ("Consolas", 10),
    "mono_s": ("Consolas", 9),
}


def rrect(cv, x0, y0, x1, y1, r, **kw):
    """Draw a rounded rectangle on a Canvas (smoothed polygon approximation)."""
    r = max(0, min(r, (x1 - x0) // 2, (y1 - y0) // 2))
    pts = [
        x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r,
        x1, y1 - r, x1, y1, x1 - r, y1, x0 + r, y1,
        x0, y1, x0, y1 - r, x0, y0 + r, x0, y0,
    ]
    return cv.create_polygon(pts, smooth=True, splinesteps=24, **kw)


class Card(tk.Canvas):
    """Rounded card: pack your widgets into .body."""

    def __init__(self, parent, radius=16, fill=None, border=None, pad=18,
                 stretch=False):
        pbg = parent.cget("bg") if isinstance(parent, (tk.Frame, tk.Tk, tk.Toplevel)) else C["bg"]
        super().__init__(parent, bg=pbg, highlightthickness=0, bd=0,
                         height=1, width=1)
        self._r = radius
        self._fill = fill if fill is not None else C["card"]
        self._border = border if border is not None else C["line"]
        self._pad = pad
        self._stretch = stretch
        self.body = tk.Frame(self, bg=self._fill)
        self._item = self.create_window(pad, pad, anchor="nw", window=self.body)
        self.body.bind("<Configure>", self._on_body)
        if stretch:
            self.bind("<Configure>", self._on_self)

    def _on_self(self, e):
        self.body.configure(width=max(1, e.width - 2 * self._pad),
                            height=max(1, e.height - 2 * self._pad))

    def refresh(self):
        """Call once after content is packed: resize the card and window item to fit."""
        bw = max(1, self.body.winfo_reqwidth())
        bh = max(1, self.body.winfo_reqheight())
        if self._stretch:
            cw = self.winfo_width()
            ch = self.winfo_height()
            if cw < 8 or ch < 8:
                cw, ch = bw + 2 * self._pad, bh + 2 * self._pad
            self.itemconfigure(self._item, width=max(1, cw - 2 * self._pad),
                               height=max(1, ch - 2 * self._pad))
        else:
            self.itemconfigure(self._item, width=bw, height=bh)
            self.configure(width=bw + 2 * self._pad, height=bh + 2 * self._pad)
        self._paint()

    def _paint(self):
        self.delete("shape")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 8 or h < 8:
            w, h = (self.body.winfo_reqwidth() + 2 * self._pad,
                    self.body.winfo_reqheight() + 2 * self._pad)
        rrect(self, 1, 1, w - 1, h - 1, self._r, fill=self._fill,
              outline=self._border, width=1, tags="shape")
        self.tag_lower("shape")
        self.coords(self._item, self._pad, self._pad)

    def _on_body(self, _e):
        self._paint()


class Pill(tk.Canvas):
    """Pill button drawn on Canvas with a hover tint (no grey tk.Button frames)."""

    KINDS = {
        "primary": ("acc", "acc_hi", "on_acc"),
        "ghost": ("card_hi", "ghost_hi", "txt"),
        "outline": ("card", "card_hi", "acc"),
        "mint": ("mint", "mint_hi", "on_acc"),
    }

    def __init__(self, parent, text, command=None, kind="primary", w=None, h=36,
                 icon="", font=None):
        pbg = parent.cget("bg") if isinstance(parent, (tk.Frame, tk.Canvas, tk.Tk, tk.Toplevel)) else C["bg"]
        self._bw = w or (len(text) * 14 + 46)
        super().__init__(parent, bg=pbg, highlightthickness=0, bd=0,
                         width=self._bw, height=h)
        self._h = h
        self._text = text
        self._icon = icon
        self._cmd = command
        self._font = font or F["body"]
        self._kind = kind if kind in self.KINDS else "primary"
        self._enabled = True
        self._hover = False
        self._draw()
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<Button-1>", self._click)
        self.configure(cursor="hand2")

    def _draw(self):
        self.delete("all")
        base, hi, fg = self.KINDS[self._kind]
        fill = C[hi] if self._hover else C[base]
        rrect(self, 1, 1, self._bw - 1, self._h - 1, self._h // 2, fill=fill, outline="")
        label = (self._icon + " " + self._text).strip()
        self.create_text(self._bw // 2, self._h // 2, text=label, fill=C[fg],
                         font=self._font)

    def _enter(self, _e):
        self._hover = True
        self._draw()

    def _leave(self, _e):
        self._hover = False
        self._draw()

    def _click(self, _e):
        if self._enabled and self._cmd:
            self._cmd()


class Divider(tk.Frame):
    def __init__(self, parent, pad_x=0):
        pbg = parent.cget("bg") if isinstance(parent, (tk.Frame, tk.Tk, tk.Toplevel)) else C["bg"]
        super().__init__(parent, bg=pbg, height=1)
        tk.Frame(self, bg=C["line"], height=1).pack(fill="x", padx=pad_x)


class ThemeDots(tk.Canvas):
    """The three theme swatches in the sidebar footer; the active one is outlined."""

    def __init__(self, parent, command):
        pbg = parent.cget("bg") if isinstance(parent, (tk.Frame, tk.Tk, tk.Toplevel)) else C["bg"]
        super().__init__(parent, bg=pbg, highlightthickness=0, bd=0, height=48, width=158)
        self._cmd = command
        self._hover = None
        self.bind("<Motion>", self._motion)
        self.bind("<Leave>", lambda _e: self._set_hover(None))
        self.bind("<Button-1>", self._click)
        self.configure(cursor="hand2")
        self._draw()

    def _x0(self, i):
        return 8 + i * 50

    def _hit(self, x):
        for i in range(len(THEME_LABELS)):
            if self._x0(i) <= x <= self._x0(i) + 44:
                return i
        return None

    def _motion(self, e):
        self._set_hover(self._hit(e.x))

    def _set_hover(self, i):
        if i != self._hover:
            self._hover = i
            self._draw()

    def _click(self, e):
        i = self._hit(e.x)
        if i is not None:
            self._cmd(THEME_LABELS[i][0])

    def _draw(self):
        self.delete("all")
        cur = current_theme()
        for i, (key, name) in enumerate(THEME_LABELS):
            x, y = self._x0(i), 0
            palette = THEMES[key]
            on = (key == cur)
            rrect(self, x, y + 1, x + 44, y + 21, 10,
                  fill=palette["acc"] if on else C["card_hi"],
                  outline=C["acc"] if on else C["line"], width=1)
            self.create_text(x + 22, y + 11, text=name, font=F["small"],
                             fill=C["on_acc"] if on else C["sub"])



def label(parent, text, font=None, fg=None, bg=None, **kw):
    pbg = parent.cget("bg") if isinstance(parent, (tk.Frame, tk.Canvas, tk.Tk, tk.Toplevel)) else C["bg"]
    return tk.Label(parent, text=text, font=font or F["body"],
                    fg=fg or C["txt"], bg=bg or pbg, **kw)
