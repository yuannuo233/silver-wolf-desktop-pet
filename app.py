"""Main window: dark Silver Wolf terminal look — narrow nav rail left, content right.

v0.6 visual rework: near-black base + Silver Wolf purple, rounded cards, pill buttons,
mono accents. No default grey tkinter buttons and no big pale colour blocks.
"""

import ctypes
import tkinter as tk
import tkinter.font as tkfont

import config
import settings as settings_ui
import ui
from ui import C, F, Card, Pill, ThemeDots, label, rrect

NAV = (("home", "主页", "◈"), ("chat", "聊天", "✧"),
       ("characters", "角色", "☰"), ("announce", "公告", "✉"),
       ("plugins", "插件", "⊞"), ("settings", "设置", "⚙"))
VERSION = "v0.6.31"


def _force_foreground(hwnd):
    """Force the window to the foreground.

    overrideredirect windows do not come to the front on click, so keystrokes go elsewhere.
    SetForegroundWindow alone is usually refused (only the current foreground process qualifies),
    so attach to the foreground thread, grab, then detach.
    """
    u = ctypes.windll.user32
    k = ctypes.windll.kernel32
    fg = u.GetForegroundWindow()
    if not fg:
        return
    tid_fg = u.GetWindowThreadProcessId(fg, None)
    tid_me = k.GetCurrentThreadId()
    attached = False
    try:
        attached = bool(u.AttachThreadInput(tid_me, tid_fg, True))
        u.SetForegroundWindow(hwnd)
        u.SetFocus(hwnd)
    finally:
        if attached:
            u.AttachThreadInput(tid_me, tid_fg, False)


class NavItem(tk.Canvas):
    """One rail item: rounded plate + highlight bar on the left."""

    def __init__(self, parent, key, text, glyph, command):
        super().__init__(parent, bg=C["rail"], highlightthickness=0, bd=0,
                         height=42, width=180)
        self.key = key
        self.text = text
        self.glyph = glyph
        self.command = command
        self.active = False
        self.hover = False
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", lambda _e: self.command(key))
        self.configure(cursor="hand2")
        self._draw()

    def _on_enter(self, _e):
        self.hover = True
        self._draw()

    def _on_leave(self, _e):
        self.hover = False
        self._draw()

    def _draw(self):
        self.delete("all")
        w = self.winfo_width() if self.winfo_width() > 20 else 162
        h = self.winfo_height() if self.winfo_height() > 20 else 42
        if self.active:
            fill, fg = C["acc_soft"], C["acc"]
        elif self.hover:
            fill, fg = C["card"], C["txt"]
        else:
            fill, fg = C["rail"], C["sub"]
        rrect(self, 1, 1, w - 1, h - 1, 12, fill=fill, outline="")
        if self.active:
            rrect(self, 1, 10, 5, h - 10, 2, fill=C["acc"], outline="")
        self.create_text(18, h // 2, text=self.glyph, fill=fg,
                         font=("Segoe UI Symbol", 12), anchor="w")
        self.create_text(42, h // 2, text=self.text, fill=fg, font=F["body"], anchor="w")


class TitleBar(tk.Canvas):
    """Custom title bar (v0.6.13).

    The window used to rely on the native title bar — a white strip with the system
    buttons — which read as "just another system window" on a light desktop. The main
    window now runs overrideredirect, so this bar is the only window chrome:
    icon + name + version + self-drawn minimise / close buttons.
    Drag anywhere blank to move the window.
    """

    H = 46
    BTN = 30          # Button edge length.
    GAP = 8

    def __init__(self, parent, app, images):
        super().__init__(parent, bg=C["rail"], highlightthickness=0, bd=0,
                         height=self.H, cursor="hand2")
        self.app = app
        self.images = images
        self._press = None        # (mouse x_root, y_root, window x, window y)
        self._hover = None        # "min" / "close" / None
        self.bind("<Configure>", lambda _e: self._paint())
        self.bind("<Button-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Motion>", self._on_hover)
        self.bind("<Leave>", lambda _e: self._set_hover(None))

    # ---------- Draw ----------
    def _btn_rects(self):
        w = self.winfo_width() or 1000
        y0 = (self.H - self.BTN) // 2
        close = (w - 14 - self.BTN, y0, w - 14, y0 + self.BTN)
        mini = (close[0] - self.GAP - self.BTN, y0, close[0] - self.GAP, y0 + self.BTN)
        return mini, close

    def _paint(self):
        c = self
        c.delete("all")
        w = c.winfo_width() or 1000
        h = self.H

        # Plate: same colour as the rail, full width, rounding handled by the window region.
        c.create_rectangle(0, 0, w, h, fill=C["rail"], outline="")
        # Thin rule under the bar to separate it from the content area.
        c.create_line(0, h - 1, w, h - 1, fill=C["line"])

        # Icon (28~32px).
        icon = self.images.get("icon_tiny") or self.images.get("icon_small")
        if icon is not None:
            c.create_image(16, h // 2, image=icon, anchor="w")
            tx = 16 + icon.width() + 10
        else:
            tx = 18

        c.create_text(tx, h // 2 - 1, text="银狼桌宠", anchor="w",
                      fill=C["txt"], font=("Microsoft YaHei UI", 11, "bold"))
        c.create_text(tx + 74, h // 2, text=VERSION, anchor="w",
                      fill=C["dim"], font=F["mono_s"])

        mini, close = self._btn_rects()
        for rect, key in ((mini, "min"), (close, "close")):
            hovered = self._hover == key
            if key == "close" and hovered:
                fill = "#E5484D"
            elif hovered:
                fill = C["field"]
            else:
                fill = C["rail"]
            rrect(c, rect[0], rect[1], rect[2], rect[3], 6, fill=fill, outline="")
        # Minimise: a single short line.
        mx = (mini[0] + mini[2]) // 2
        my = (mini[1] + mini[3]) // 2
        c.create_line(mx - 7, my, mx + 7, my, fill=C["sub"], width=2)
        # Close: two diagonal strokes.
        cx0, cy0 = close[0], close[1]
        c.create_line(cx0 + 10, cy0 + 10, cx0 + 20, cy0 + 20,
                      fill="#FFF" if self._hover == "close" else C["sub"], width=2)
        c.create_line(cx0 + 20, cy0 + 10, cx0 + 10, cy0 + 20,
                      fill="#FFF" if self._hover == "close" else C["sub"], width=2)

    # ---------- Interaction ----------
    def _set_hover(self, key):
        if key != self._hover:
            self._hover = key
            self._paint()

    def _on_hover(self, event):
        mini, close = self._btn_rects()
        if self._in(close, event.x, event.y):
            self._set_hover("close")
        elif self._in(mini, event.x, event.y):
            self._set_hover("min")
        else:
            self._set_hover(None)

    @staticmethod
    def _in(rect, x, y):
        return rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]

    def _on_press(self, event):
        mini, close = self._btn_rects()
        if self._in(close, event.x, event.y):
            self.app.quit_app()
            return
        if self._in(mini, event.x, event.y):
            self.app.minimize_to_pet()
            return
        root = self.app.root
        self._press = (event.x_root, event.y_root, root.winfo_x(), root.winfo_y())

    def _on_drag(self, event):
        if not self._press:
            return
        px, py, wx, wy = self._press
        root = self.app.root
        root.geometry(f"+{wx + (event.x_root - px)}+{wy + (event.y_root - py)}")

    def _on_release(self, _event):
        self._press = None


class ScrollablePage(tk.Frame):
    """A page whose content can be scrolled when it does not fit.

    The window is frameless, so there is no system scrollbar. Pages are stacked with
    place() and each one is normally sized to fit the window; the problem is that on a short
    screen (1366x768) or with a large font scale, the bottom of a page gets clipped with no
    way to reach it.

    The content goes into a Canvas that is taller than the visible area; the scrollbar sits
    next to it and only shows when the content actually overflows. Mouse wheel scrolling
    works over the whole page.
    """

    def __init__(self, master, app, **kw):
        super().__init__(master, bg=C["bg"], **kw)
        self.app = app
        self.canvas = tk.Canvas(self, bg=C["bg"], highlightthickness=0, bd=0)
        self.vbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview,
                                 width=10, troughcolor=C["bg"], bg=C["line"],
                                 activebackground=C["acc"], bd=0, highlightthickness=0)
        self.canvas.configure(yscrollcommand=self._on_scroll)

        self.body = tk.Frame(self.canvas, bg=C["bg"])
        self._win = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self._bar_shown = False      # whether the scrollbar is currently packed

        self.canvas.pack(side="left", fill="both", expand=True)
        self.vbar.pack(side="right", fill="y")

        # The body keeps its own height; the canvas window must follow it, and the canvas
        # must follow the visible area.
        self.body.bind("<Configure>", self._on_body_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.bind("<MouseWheel>", self._on_wheel)
        self.body.bind("<MouseWheel>", self._on_wheel)

    def _on_scroll(self, first, last):
        """Show the scrollbar only when there is something to scroll.

        The decision is made from the numbers, not from winfo_ismapped(): packing a widget
        does not map it until the event loop runs, so the visibility check would lag one
        cycle behind and the bar would never appear.
        """
        try:
            f = float(first)
            l = float(last)
        except (TypeError, ValueError):
            return
        need = f > 0.001 or l < 0.999
        if need and not self._bar_shown:
            self.vbar.pack(side="right", fill="y")
            self._bar_shown = True
            self.after_idle(self._sync_width)
        elif not need and self._bar_shown:
            self.vbar.pack_forget()
            self._bar_shown = False
            self.after_idle(self._sync_width)
        self.vbar.set(first, last)
        # Keep the right edge strip in sync with this page's scrollbar.
        self.after_idle(lambda: self.app._sync_edge_strips())

    def _on_body_configure(self, _e=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._sync_width()

    def _on_canvas_configure(self, event):
        self._sync_width()

    def _sync_width(self):
        """Keep the inner frame exactly as wide as the visible canvas area.

        The canvas is wider than the visible strip when the scrollbar is packed, so the
        frame width must subtract it — otherwise the content is wider than the window and
        a horizontal scrollbar appears.
        """
        try:
            w = self.canvas.winfo_width()
            if self._bar_shown:
                w -= self.vbar.winfo_width()
            self.canvas.itemconfig(self._win, width=max(1, w))
        except tk.TclError:
            pass

    def _on_wheel(self, event):
        """Mouse wheel scrolling. step is platform-signed already."""
        try:
            self.canvas.yview_scroll(-int(event.delta / 120), "units")
        except tk.TclError:
            pass

    def scroll_to_top(self):
        try:
            self.canvas.yview_moveto(0)
        except tk.TclError:
            pass


class ResizeGrip(tk.Frame):
    """Drag handle in the bottom-right corner that resizes the window.

    The window is overrideredirect, so the system frame (and with it the native resize
    border) is gone. Without this the user cannot make the window bigger on a small screen,
    which is exactly when they need it most.

    It is drawn as three small diagonal strokes, the usual "grip corner" affordance.
    """

    SIZE = 18

    def __init__(self, parent, app):
        # Tk knows the X11 name "nwse-resize" but not the Windows one; "size_ne_sw" is the
        # standard Windows cursor for a south-east resize handle.
        super().__init__(parent, bg=C["bg"], cursor="size_ne_sw")
        self.app = app
        self._start = None       # (mouse x_root, y_root, window w, window h)
        self.canvas = tk.Canvas(self, bg=C["bg"], highlightthickness=0, bd=0,
                                width=self.SIZE, height=self.SIZE)
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Enter>", lambda _e: self._paint(True))
        self.canvas.bind("<Leave>", lambda _e: self._paint(False))
        self._paint(False)

    def _paint(self, hovered):
        c = self.canvas
        c.delete("all")
        col = C["acc"] if hovered else C["dim"]
        s = self.SIZE
        for i in range(3):
            off = 4 + i * 4
            c.create_line(s - off, s - 2, s - 2, s - off, fill=col, width=1)

    def _on_press(self, event):
        root = self.app.root
        self.app._user_sized = True
        self._start = (event.x_root, event.y_root,
                       root.winfo_width(), root.winfo_height())

    def _on_drag(self, event):
        if self._start is None:
            return
        mx, my, w0, h0 = self._start
        root = self.app.root
        # Allow both directions: dragging towards the top-left shrinks the window.
        nw = w0 + (event.x_root - mx)
        nh = h0 + (event.y_root - my)
        nw = max(self.app.MIN_W, nw)
        nh = max(self.app.MIN_H, nh)
        # Keep the window on screen.
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        nw = min(nw, sw - root.winfo_x())
        nh = min(nh, sh - root.winfo_y())
        root.geometry(f"{nw}x{nh}+{root.winfo_x()}+{root.winfo_y()}")
        # The grip sits on top of the content, so the page has to be told to re-measure.
        self.app.refresh_cards()
        self.app.root.update_idletasks()
        self.app._sync_edge_strips()

    def _on_release(self, _event):
        self._start = None
        self.app.refresh_cards()
        self.app.root.after(60, self.app._reflow)


class EdgeResizer(tk.Frame):
    """Invisible strip on a window edge that resizes when dragged.

    The window is overrideredirect, so the native resize border is gone. Users instinctively
    drag the *edge* of a window (that is how every normal window works), not a tiny corner
    mark. The corner ResizeGrip alone was too easy to miss. These strips restore the
    familiar "grab an edge and pull" behaviour.

    Three sides: left / right / bottom. The top is the self-drawn title bar, which is already
    used for moving the window, so it is deliberately left alone.
    """

    EDGE = 6                  # hit area thickness in px

    def __init__(self, parent, app, side):
        cursor = {
            "left": "sb_h_double_arrow",
            "right": "sb_h_double_arrow",
            "bottom": "sb_v_double_arrow",
        }[side]
        super().__init__(parent, bg=C["bg"], cursor=cursor)
        self.app = app
        self.side = side
        self._start = None
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _on_press(self, event):
        root = self.app.root
        self.app._user_sized = True
        self._start = (event.x_root, event.y_root,
                       root.winfo_x(), root.winfo_y(),
                       root.winfo_width(), root.winfo_height())

    def _on_drag(self, event):
        if self._start is None:
            return
        mx, my, x0, y0, w0, h0 = self._start
        root = self.app.root
        dx, dy = event.x_root - mx, event.y_root - my
        x, y, w, h = x0, y0, w0, h0
        if self.side == "right":
            w = max(self.app.MIN_W, min(w0 + dx, root.winfo_screenwidth() - x0))
        elif self.side == "left":
            nw = max(self.app.MIN_W, min(w0 - dx, x0 + w0))
            x = x0 + (w0 - nw)
            w = nw
        elif self.side == "bottom":
            h = max(self.app.MIN_H, min(h0 + dy, root.winfo_screenheight() - y0))
        root.geometry(f"{w}x{h}+{x}+{y}")
        self.app.refresh_cards()
        self.app.root.update_idletasks()
        self.app._sync_edge_strips()

    def _on_release(self, _event):
        self._start = None
        self.app.refresh_cards()
        self.app.root.after(60, self.app._reflow)


class MainApp:
    """Main window: dark Silver Wolf terminal look — narrow nav rail left, content right.

    v0.6 visual rework: near-black base + Silver Wolf purple, rounded cards, pill buttons,
    mono accents. No default grey tkinter buttons and no big pale colour blocks.
    """

    MIN_W = 560        # smallest the user may drag the window to
    MIN_H = 420

    def __init__(self, root: tk.Tk, images: dict, rebuild_images=None):
        self.root = root
        self.images = images
        self.rebuild_images = rebuild_images   # called after a theme switch to re-bake icons
        self.pet = None
        self.pages = {}
        self.nav_items = {}
        self.settings_panel = None
        self.current_page = "home"
        self._ready = False
        self._placed = False          # centre once on first height fit, then only resize.
        self._user_sized = False      # True after the user drags the resize grip.
        self.rail = None
        self.wrap = None

        root.title("银狼桌宠")
        # v0.6.13: no native title bar (the white strip + system buttons look like an OS
        # component); the whole UI is self-drawn, with TitleBar standing in at the top.
        root.overrideredirect(True)
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        w, h = min(1000, sw - 40), min(760, sh - 60)
        root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 3}")
        # Minimum size is small enough that the content can be squeezed on a short screen;
        # the pages scroll, so nothing gets lost.
        root.minsize(self.MIN_W, self.MIN_H)
        root.configure(bg=C["bg"])
        if images.get("icon") is not None:
            try:
                root.iconphoto(True, images["icon"])
            except tk.TclError:
                pass

        # Custom title bar, then the strip holding rail + content.
        # Two nested 1px frames make the outline: a darker outer ring plus a lighter inner
        # hairline. A single 1px line in one flat colour disappears against a white desktop.
        self.shell = tk.Frame(root, bg=C["edge"])
        self.shell.pack(fill="both", expand=True)
        self.bevel = tk.Frame(self.shell, bg=C["edge_in"])
        self.bevel.pack(fill="both", expand=True, padx=1, pady=1)
        self.inner = tk.Frame(self.bevel, bg=C["bg"])
        self.inner.pack(fill="both", expand=True, padx=1, pady=1)

        self.titlebar = TitleBar(self.inner, self, images)
        self.titlebar.pack(side="top", fill="x")
        self.body = tk.Frame(self.inner, bg=C["bg"])
        self.body.pack(side="top", fill="both", expand=True)

        # Resize grip in the bottom-right corner. It lives in `inner` (not `shell`) so it
        # sits inside the 1px outline and does not cover the border.
        self.grip = ResizeGrip(self.inner, self)
        self.grip.place(relx=1.0, rely=1.0, anchor="se",
                        x=-2, y=-2)

        # Invisible edge strips: let users grab the left/right/bottom edge to resize,
        # the way every normal window behaves. The corner grip stays as a visual hint.
        # Raised above content so the strip actually receives the mouse.
        e = EdgeResizer.EDGE
        self.edges = []
        for side in ("left", "right", "bottom"):
            strip = EdgeResizer(self.inner, self, side)
            if side == "left":
                strip.place(x=0, y=0, width=e, relheight=1.0)
            elif side == "right":
                strip.place(relx=1.0, x=-e, y=0, width=e, relheight=1.0)
            else:
                strip.place(x=0, rely=1.0, y=-e, relwidth=1.0, height=e)
            strip.lift()
            self.edges.append(strip)
        # Keep the corner grip above the edge strips so it remains clickable.
        self.grip.lift()

        # overrideredirect windows do not take keyboard focus on click; without this the inputs cannot type.
        root.bind("<Button-1>", self._wake_focus, add="+")
        root.bind("<FocusIn>", lambda _e: self._pet_on_top(False), add="+")
        root.bind("<FocusOut>", lambda _e: self._pet_on_top(True), add="+")

        self._build_rail()
        self._build_content()
        self.root.update_idletasks()
        self.refresh_cards()
        self.show_page("home")
        self._ready = True
        self._fit_window()
        self.root.after(60, self._reflow)

    def _reflow(self):
        """Re-fill cards once the width is settled, then correct the height once more."""
        self.root.update_idletasks()
        self.refresh_cards()
        self.root.update_idletasks()
        self._fit_window()
        self.root.after_idle(self._sync_edge_strips)

    def _build_edge(self):
        """Re-colour the window outline after a theme switch.

        The outline is two nested 1px Frames (`_build_shell`), not a Canvas overlay: an
        overlay would sit on top of every widget and swallow their clicks.
        """
        try:
            self.shell.configure(bg=C["edge"])
            self.bevel.configure(bg=C["edge_in"])
            self.inner.configure(bg=C["bg"])
        except (tk.TclError, AttributeError):
            pass

    def _fit_window(self, key=None):
        """Shrink to the height the current page actually needs, so nothing is clipped.

        v0.6.8: centre only on the very first placement; later page or theme switches just resize.
        A window the user has moved is never dragged back to the middle of the screen.

        Once the user has resized the window by hand, stop auto-fitting the height: the
        whole point of dragging the corner is to keep the size they chose. The pages scroll,
        so a short window no longer loses content.
        """
        self.root.update_idletasks()
        w = self.root.winfo_width() or 1000
        holder = self.pages[key or self.current_page]
        # Measure the content inside the scroll area, not the scroll area itself: the
        # holder is sized by the window, but the window should follow the content.
        page = getattr(holder, "body", holder)
        off = max(0, page.winfo_rooty() - self.root.winfo_rooty())
        need = off + page.winfo_reqheight() + 12
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        if self._user_sized:
            h = self.root.winfo_height() or 620
        else:
            h = max(560, min(need, sh - 60, 900))
        if self._placed:
            x, y = self.root.winfo_x(), self.root.winfo_y()
        else:
            x, y = (sw - w) // 2, max(20, (sh - h) // 3)
            self._placed = True
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def refresh_cards(self, widget=None):
        """Card sizes depend on content, so every card is refreshed once the page is built."""
        w = widget or self.root
        for ch in w.winfo_children():
            if isinstance(ch, Card):
                ch.refresh()
            self.refresh_cards(ch)

    # ---------- Rail ----------
    def _build_rail(self):
        rail = tk.Frame(self.body, width=186, bg=C["rail"])
        rail.pack(side="left", fill="y")
        rail.pack_propagate(False)
        self.rail = rail

        brand = tk.Frame(rail, bg=C["rail"])
        brand.pack(fill="x", padx=16, pady=(18, 14))
        if self.images.get("icon_small") is not None:
            tk.Label(brand, image=self.images["icon_small"], bg=C["rail"]).pack(anchor="w")
        label(brand, "银狼", font=("Microsoft YaHei UI", 16, "bold"), fg=C["txt"],
              bg=C["rail"]).pack(anchor="w", pady=(8, 0))
        label(brand, "SILVER WOLF", font=F["mono_s"], fg=C["dim"],
              bg=C["rail"]).pack(anchor="w")

        tk.Frame(rail, bg=C["line"], height=1).pack(fill="x", padx=16, pady=(2, 12))

        for key, text, glyph in NAV:
            item = NavItem(rail, key, text, glyph, self.show_page)
            item.pack(padx=12, pady=3)
            self.nav_items[key] = item

        foot = tk.Frame(rail, bg=C["rail"])
        foot.pack(side="bottom", fill="x", padx=18, pady=16)
        tk.Frame(foot, bg=C["line"], height=1).pack(fill="x", pady=(0, 12))
        label(foot, "AI 已接管这台电脑", font=F["small"], fg=C["sub"], bg=C["rail"]).pack(anchor="w")
        label(foot, VERSION, font=F["mono_s"], fg=C["acc"], bg=C["rail"]).pack(anchor="w", pady=(4, 0))
        # Keep a blank line between version and disclaimer; stacked together they read as an official version.
        label(foot, "非官方粉丝作品", font=F["mono_s"], fg=C["dim"],
              bg=C["rail"]).pack(anchor="w", pady=(12, 0))

        # Theme switcher: three swatches; clicking rebuilds the whole UI so colours follow.
        theme_box = tk.Frame(rail, bg=C["rail"])
        theme_box.pack(side="bottom", fill="x", padx=14, pady=(0, 4))
        label(theme_box, "主题", font=F["mono_s"], fg=C["dim"],
              bg=C["rail"]).pack(anchor="w", pady=(0, 4))
        ThemeDots(theme_box, self.set_theme).pack(anchor="w")

        # Hairline between rail and content (on the light theme two white blocks would merge).
        sep = tk.Frame(self.body, bg=C["line"], width=1)
        sep.pack(side="left", fill="y")
        self.sep = sep

    # ---------- Theme ----------
    def set_theme(self, name):
        """Switch theme: save to config, swap the palette, rebuild rail and content."""
        if name == ui.current_theme():
            return
        cfg = config.load()
        cfg["theme"] = name
        config.save(cfg)
        ui.apply_theme(name)
        settings_ui.rebind_theme()
        self._build_edge()
        self._refresh_images()
        if self.pet is not None:
            self.pet.refresh_theme()
        self._rebuild_ui()
        page = self.current_page if self.current_page in self.pages else "home"
        self.show_page(page)

    def _refresh_images(self):
        """Re-bake the icons after a theme switch.

        Their rounded corners are painted onto the old background colour, so a new palette
        needs new bitmaps — otherwise the corners show a fringe of the previous theme.
        """
        if not self.rebuild_images:
            return
        try:
            self.images.update(self.rebuild_images())
            self.titlebar.images = self.images
            self.titlebar._paint()
        except Exception:
            pass

    def _rebuild_ui(self):
        page_key = self.current_page
        for w in (self.rail, self.sep, self.wrap):
            try:
                w.destroy()
            except (tk.TclError, AttributeError):
                pass
        self.pages = {}
        self.nav_items = {}
        self.settings_panel = None
        self.current_page = page_key
        self.root.configure(bg=C["bg"])
        self._build_rail()
        self._build_content()
        self.root.update_idletasks()
        self.refresh_cards()
        if self.pet is not None and self.settings_panel is not None:
            self.settings_panel.pet = self.pet
        self._fit_window(page_key if page_key in self.pages else "home")

    # ---------- Content area ----------
    def _build_content(self):
        wrap = tk.Frame(self.body, bg=C["bg"])
        wrap.pack(side="left", fill="both", expand=True)
        self.wrap = wrap

        header = tk.Frame(wrap, bg=C["bg"])
        header.pack(fill="x", padx=28, pady=(22, 0))
        self.page_title = label(header, "主页", font=F["hero"], fg=C["txt"])
        self.page_title.pack(anchor="w")
        self.page_sub = label(header, "", font=F["small"], fg=C["sub"])
        self.page_sub.pack(anchor="w", pady=(2, 0))

        self.status_chip = tk.Canvas(header, bg=C["bg"], highlightthickness=0,
                                     bd=0, width=140, height=26)
        self.status_chip.pack(side="right", pady=(10, 0))

        tk.Frame(wrap, bg=C["line"], height=1).pack(fill="x", padx=28, pady=(16, 0))

        container = tk.Frame(wrap, bg=C["bg"])
        container.pack(fill="both", expand=True)
        self.container = container
        builders = {"home": self._build_home, "chat": self._build_chat,
                    "characters": self._build_characters, "announce": self._build_announce,
                    "plugins": self._build_plugins, "settings": self._build_settings}
        for key, build in builders.items():
            # Every page sits inside a ScrollablePage: when the content does not fit the
            # window (short screen, large font scale), the user can scroll instead of
            # losing the bottom of the page.
            holder = ScrollablePage(container, self)
            holder.place(x=0, y=0, relwidth=1, relheight=1)
            page = holder.body
            build(page)
            self.pages[key] = holder

    def show_page(self, key):
        self.current_page = key
        holder = self.pages[key]
        holder.tkraise()
        # A fresh page should start at the top, not wherever the last one was scrolled to.
        try:
            holder.scroll_to_top()
        except AttributeError:
            pass
        for k, item in self.nav_items.items():
            item.active = (k == key)
            item._draw()
        titles = {"home": ("主页", "银狼已经挂在你屏幕上了，随时待命"),
                  "chat": ("聊天", "说的话会同时出现在她头顶的气泡里"),
                  "characters": ("角色", "已经加入的角色都在这，点一下就能换"),
                  "announce": ("公告", "每次更新都改了什么，这里说得清清楚楚"),
                  "plugins": ("插件", "给她装点新本事，比如报时、天气"),
                  "settings": ("设置", "接一个 OpenAI 兼容接口，她就有脑子了")}
        t, s = titles[key]
        self.page_title.configure(text=t)
        self.page_sub.configure(text=s)
        if key == "home":
            self._refresh_status()
        if key == "chat":
            self.chat_entry.focus_set()
        if key == "characters":
            self._refresh_characters()
        if key == "announce":
            self._refresh_announce()
        if key == "plugins":
            self._refresh_plugins()
        if self._ready:
            self._fit_window(key)
            self.root.after(40, self._reflow)
        self.root.after_idle(self._sync_edge_strips)

    def _sync_edge_strips(self):
        """Hide the right resize strip when the visible page has a scrollbar.

        The strip sits in a top-level container and would swallow clicks meant for the
        scrollbar underneath it. When a scrollbar is visible on the current page, that 6px
        belongs to the scrollbar; otherwise the strip is restored for edge resizing.
        """
        try:
            holder = self.pages.get(self.current_page)
            has_bar = bool(holder and holder.vbar.winfo_ismapped())
            for strip in getattr(self, "edges", []):
                if strip.side != "right":
                    continue
                if has_bar:
                    strip.place_forget()
                elif not strip.winfo_ismapped():
                    strip.place(relx=1.0, x=-EdgeResizer.EDGE, y=0,
                                width=EdgeResizer.EDGE, relheight=1.0)
                    strip.lift()
        except Exception:
            pass

    # ---------- Status chip ----------
    def _draw_chip(self, text, fg):
        self.status_chip.delete("all")
        h = 26
        f = tkfont.Font(font=F["mono_s"])
        w = 26 + f.measure(text) + 18
        self.status_chip.configure(width=w, height=h)
        rrect(self.status_chip, 1, 1, w - 1, h - 1, h // 2, fill=C["card"], outline=C["line"])
        self.status_chip.create_oval(12, h // 2 - 3, 18, h // 2 + 3, fill=fg, outline="")
        self.status_chip.create_text(26, h // 2, text=text, fill=C["sub"],
                                     font=F["mono_s"], anchor="w")

    def _refresh_status(self):
        cfg = config.load()
        if cfg.get("base_url") and cfg.get("model"):
            self._draw_chip(f"AI 就绪 · {cfg['model'][:20]}", C["mint"])
        else:
            self._draw_chip("AI 未接线 · 去设置", C["warn"])

    # ---------- Home ----------
    def _build_home(self, page):
        hero = tk.Canvas(page, bg=C["bg"], highlightthickness=0, bd=0, height=150)
        hero.pack(fill="x", padx=24, pady=(16, 0))
        self.hero = hero
        hero.bind("<Configure>", self._paint_hero)

        acts = Card(page, radius=16, pad=8, stretch=True)
        acts.configure(height=196)
        acts.pack(fill="x", padx=24, pady=(12, 0))
        for title, desc, cmd, glyph in (
            ("召唤银狼", "请回屏幕上", self._summon, "◈"),
            ("和她聊天", "她会接话", lambda: self.show_page("chat"), "✧"),
            ("接线设置", "地址 / 密钥 / 人设", lambda: self.show_page("settings"), "⚙"),
        ):
            row = tk.Frame(acts.body, bg=C["card"], cursor="hand2")
            row.pack(fill="x")
            row.columnconfigure(2, weight=1)
            g = label(row, glyph, font=("Segoe UI Symbol", 13), fg=C["acc"], bg=C["card"])
            g.grid(row=0, column=0, padx=(12, 12), pady=9)
            t = label(row, title, font=F["sec"], fg=C["txt"], bg=C["card"])
            t.grid(row=0, column=1, sticky="w")
            d = label(row, desc, font=F["small"], fg=C["sub"], bg=C["card"])
            d.grid(row=0, column=2, sticky="w", padx=(10, 0))
            arrow = label(row, "›", font=F["body"], fg=C["dim"], bg=C["card"])
            arrow.grid(row=0, column=3, padx=(10, 16))
            for w in (row, g, t, d, arrow):
                w.bind("<Button-1>", lambda _e, c=cmd: c(), add="+")
            tk.Frame(acts.body, bg=C["line"], height=1).pack(fill="x", padx=12)

        hint = label(page, "拖她走 · 双击弹快聊 · 右键有菜单（说话 / 尺寸 / 设置 / 退出）",
                     font=F["mono_s"], fg=C["dim"])
        hint.pack(anchor="w", padx=28, pady=(14, 8))

    def _paint_hero(self, _e=None):
        c = self.hero
        c.delete("all")
        w = c.winfo_width() or 600
        h = 150
        rrect(c, 1, 1, w - 1, h - 1, 18, fill=C["card"], outline=C["line"])
        banner = self.images.get("banner")
        if banner is not None:
            bx = w - 20
            c.create_image(bx, h // 2, image=banner, anchor="e", tags="bn")
            rrect(c, 1, 1, w - 1, h - 1, 18, outline=C["line"], fill="")
        c.create_text(26, 48, text="银狼，已接管你的桌面。", fill=C["txt"],
                      font=("Microsoft YaHei UI", 18, "bold"), anchor="w")
        c.create_text(26, 90, text="她不会替你写作业，但会陪你熬到写完。", fill=C["sub"],
                      font=F["body"], anchor="w")
        c.create_text(26, h - 30, text="›  STATUS : ONLINE", fill=C["dim"],
                      font=F["mono_s"], anchor="w")

    def _summon(self):
        if self.pet is not None:
            self.pet.show()

    # ---------- Characters page ----------
    def _build_characters(self, page):
        """List every character pack found under characters/.

        Read from disk rather than a hard-coded list so dropping in a new pack is enough.
        Each row shows the current character, how many frames it has, and a switch button.
        """
        self._char_rows = []
        self._char_hint = label(page, "", font=F["mono_s"], fg=C["dim"])
        self._char_hint.pack(anchor="w", padx=28, pady=(14, 0))

        # Not stretch=True: the list lives inside the scroll area, whose container has no
        # height of its own. A stretch card asks for that height, gets 1px and collapses.
        card = Card(page, radius=16, pad=6)
        card.pack(fill="x", padx=24, pady=(10, 0))
        self._char_list = tk.Frame(card.body, bg=C["card"])
        self._char_list.pack(fill="both", expand=True)

        tip = label(page, "角色包放在 characters/ 里，一个文件夹就是一只；"
                          "放进新的重启后在列表里就能看到。",
                    font=F["mono_s"], fg=C["dim"], wraplength=620, justify="left")
        tip.pack(anchor="w", padx=28, pady=(12, 12))

        self._refresh_characters()

    def _refresh_characters(self):
        """Rebuild the list. Called on page show so a newly dropped-in pack appears."""
        lst = getattr(self, "_char_list", None)
        if lst is None:
            return
        for w in lst.winfo_children():
            w.destroy()

        try:
            import characters
            items = characters.list_characters()
        except Exception:
            items = []
        current = config.load().get("character", "") or characters.default_id()

        for i, spec in enumerate(items):
            row = tk.Frame(lst, bg=C["card"])
            row.pack(fill="x")
            row.columnconfigure(1, weight=1)

            active = (spec["id"] == current)
            mark = "●" if active else "○"
            label(row, mark, font=("Segoe UI Symbol", 11),
                  fg=C["acc"] if active else C["dim"], bg=C["card"]).grid(
                row=0, column=0, padx=(12, 10), pady=11)

            name = label(row, spec["name"], font=F["sec"], fg=C["txt"], bg=C["card"])
            name.grid(row=0, column=1, sticky="w")

            # Frame count doubles as a "is this pack actually complete" signal.
            n = self._count_frames(spec)
            detail = "%d 帧" % n if n else "素材未就位"
            label(row, detail, font=F["small"],
                  fg=C["sub"] if n else C["warn"], bg=C["card"]).grid(
                row=0, column=2, sticky="w", padx=(10, 0))

            if active:
                label(row, "使用中", font=F["small"], fg=C["acc"], bg=C["card"]).grid(
                    row=0, column=3, padx=(12, 16))
            elif not n:
                # A pack with no frames on disk cannot be drawn. Offering a switch button
                # here is how a user ends up with an unusable config and a start-up crash:
                # the id gets saved, then Image.open() fails on every launch.
                label(row, "不可切换", font=F["small"], fg=C["dim"], bg=C["card"]).grid(
                    row=0, column=3, padx=(12, 16))
            else:
                btn = Pill(row, "切换", kind="ghost", h=28, font=F["small"])
                btn.grid(row=0, column=3, padx=(12, 16))
                btn.configure(cursor="hand2")
                btn.bind("<Button-1>", lambda _e, sid=spec["id"]: self._switch_character(sid))

            if i < len(items) - 1:
                tk.Frame(lst, bg=C["line"], height=1).pack(fill="x", padx=12)

        if hasattr(self, "_char_hint"):
            self._char_hint.configure(
                text="共 %d 个角色 · 当前：%s" % (len(items), self._current_name(items, current)))

    @staticmethod
    def _count_frames(spec):
        """How many frames a pack actually has on disk (0 when it is not built yet)."""
        try:
            import json
            from pathlib import Path
            stand = spec.get("stand")
            if not stand:
                return 0
            fj = Path(stand) / "frames.json"
            if not fj.exists():
                return 0
            data = json.loads(fj.read_text(encoding="utf-8"))
            total = 0
            for sdef in data.get("states", {}).values():
                for fr in sdef.get("frames", []):
                    if (Path(stand) / fr["file"]).exists():
                        total += 1
            return total
        except Exception:
            return 0

    @staticmethod
    def _current_name(items, current):
        for spec in items:
            if spec["id"] == current:
                return spec["name"]
        return current

    def _switch_character(self, character_id):
        """Persist the choice and swap the sprite set immediately.

        It used to only save to config and tell the user to restart, which made the button
        look broken: the list still showed the old character and the pet kept its old face.
        """
        try:
            import characters
            spec = characters.get(character_id)
            # Refuse a pack that has no frames *before* touching the config: writing the id
            # first is what made the next launch die inside Image.open().
            if self._count_frames(spec) <= 0:
                self._char_hint.configure(
                    text="「%s」的图还没放进来，切过去启动会失败" % spec.get("name", character_id),
                    fg=C["warn"])
                return
            cfg = config.load()
            cfg["character"] = character_id
            config.save(cfg)
            name = spec["name"]
            swapped = False
            if self.pet is not None:
                try:
                    swapped = self.pet.reload_character(character_id)
                except Exception:
                    swapped = False
            if swapped:
                self._char_hint.configure(text="已切换到「%s」" % name, fg=C["mint"])
            else:
                self._char_hint.configure(
                    text="已选中「%s」，重启程序后生效" % name, fg=C["acc"])
            self._refresh_characters()
        except Exception:
            pass

    # ---------- Plugins ----------
    def _build_plugins(self, page):
        """The plugin marketplace: list every plugin folder, let the user enable them."""
        self._plugin_hint = label(page, "", font=F["mono_s"], fg=C["dim"])
        self._plugin_hint.pack(anchor="w", padx=28, pady=(14, 0))

        # Same reason as the character list: inside the scroll area a stretch card collapses.
        card = Card(page, radius=16, pad=6)
        card.pack(fill="x", padx=24, pady=(10, 0))
        self._plugin_list = tk.Frame(card.body, bg=C["card"])
        self._plugin_list.pack(fill="both", expand=True)

        tip = label(
            page,
            "插件放在程序目录的「plugins\\」里，一个文件夹就是一个插件；"
            "丢进去后回到这一页就能看到。\n"
            "点头像旁的「试一下」可以让她立刻演示一句。",
            font=F["mono_s"], fg=C["dim"], wraplength=640, justify="left")
        tip.pack(anchor="w", padx=28, pady=(12, 12))

        self._refresh_plugins()

    def _refresh_plugins(self):
        """Rebuild the plugin list from disk."""
        holder = getattr(self, "_plugin_list", None)
        if holder is None:
            return
        for w in holder.winfo_children():
            w.destroy()

        try:
            import plugins_engine as PE
            items = PE.list_plugins()
        except Exception:
            items = []
        enabled = set(config.load().get("plugins_enabled", []))

        for i, p in enumerate(items):
            row = tk.Frame(holder, bg=C["card"])
            row.pack(fill="x")
            row.columnconfigure(1, weight=1)

            pid = p.get("id", "")
            on = pid in enabled and p.get("available")
            mark = "●" if on else "○"
            label(row, mark, font=("Segoe UI Symbol", 11),
                  fg=C["acc"] if on else C["dim"], bg=C["card"]).grid(
                row=0, column=0, padx=(12, 10), pady=11)

            label(row, p.get("name", pid), font=F["sec"], fg=C["txt"],
                  bg=C["card"]).grid(row=0, column=1, sticky="w")

            ver = p.get("version", "")
            who = p.get("author", "")
            meta = "  ·  ".join(x for x in (ver, who) if x)
            label(row, meta, font=F["small"], fg=C["dim"], bg=C["card"]).grid(
                row=0, column=2, sticky="w", padx=(10, 0))

            if not p.get("available"):
                label(row, "入口缺失", font=F["small"], fg=C["warn"],
                      bg=C["card"]).grid(row=0, column=3, padx=(12, 16))
            else:
                btn = Pill(row, "关闭" if on else "启用",
                           lambda _sid=pid, _o=on: self._toggle_plugin(_sid, _o),
                           kind="ghost", h=28, font=F["small"])
                btn.grid(row=0, column=3, padx=(12, 16))
                btn.configure(cursor="hand2")
                # A quick demo: ask the plugin for its main intent and show the answer.
                demo = Pill(row, "试一下", lambda _p=p: self._demo_plugin(_p),
                            kind="ghost", h=28, font=F["small"])
                demo.grid(row=0, column=4, padx=(0, 16))
                demo.configure(cursor="hand2")

            if i < len(items) - 1:
                tk.Frame(holder, bg=C["line"], height=1).pack(fill="x", padx=12)

        if hasattr(self, "_plugin_hint"):
            self._plugin_hint.configure(text="共 %d 个插件 · 已启用 %d 个"
                                        % (len(items), len(enabled)))

    def _toggle_plugin(self, plugin_id, was_on):
        """Persist the enabled list. Takes effect the next time the app starts."""
        try:
            cfg = config.load()
            cur = list(cfg.get("plugins_enabled", []))
            if was_on:
                cur = [x for x in cur if x != plugin_id]
                word = "关闭"
            else:
                if plugin_id not in cur:
                    cur.append(plugin_id)
                word = "启用"
            cfg["plugins_enabled"] = cur
            config.save(cfg)
            self._refresh_plugins()
            if getattr(self, "_plugin_hint", None) is not None:
                self._plugin_hint.configure(
                    text="已%s插件，重启程序后生效" % word, fg=C["acc"])
        except Exception:
            pass

    def _demo_plugin(self, plugin):
        """Run a plugin right now and show its answer in the pet's bubble.

        Uses the first intent the plugin declares, with no arguments — enough to prove
        the wiring works. The real chat integration passes whatever the user asked.
        """
        try:
            import plugins_engine as PE
            intents = plugin.get("intents") or []
            if not intents:
                return
            result = PE.ask(plugin, intents[0], {})
            text = result.get("text") or result.get("error") or "插件没有返回内容"
            if self.pet is not None:
                payload = result.get("intent_payload")
                if isinstance(payload, dict) and hasattr(self.pet, "_apply_plugin_payload"):
                    self.pet._apply_plugin_payload(payload)
                self.pet.show_bubble(text, 8000)
            if getattr(self, "_plugin_hint", None) is not None:
                self._plugin_hint.configure(text="试了一下「%s」" % plugin.get("name", ""),
                                            fg=C["acc"])
        except Exception:
            pass

    # ---------- Announcements ----------
    def _build_announce(self, page):
        """Show the version notes.

        The text comes from 公告.md, which the project owner writes; this page only displays
        it. The newest entry is expanded, older ones are collapsed into one-line rows that
        can be clicked open, so the history stays reachable.
        """
        self._ann_list = tk.Frame(page, bg=C["bg"])
        self._ann_list.pack(fill="both", expand=True, padx=24, pady=(16, 0))

        self._ann_hint = label(page, "", font=F["mono_s"], fg=C["dim"])
        self._ann_hint.pack(anchor="w", padx=28, pady=(10, 0))

        tip = label(page, "公告写在程序目录的「公告.md」里，改完重启就能看到。",
                    font=F["mono_s"], fg=C["dim"], wraplength=620, justify="left")
        tip.pack(anchor="w", padx=28, pady=(12, 12))

        self._refresh_announce()

    def _refresh_announce(self):
        """Rebuild the announcement list from the file."""
        holder = getattr(self, "_ann_list", None)
        if holder is None:
            return
        for w in holder.winfo_children():
            w.destroy()

        try:
            import announce
        except Exception as e:
            label(holder, "公告模块加载失败：%s" % e, font=F["small"],
                  fg=C["warn"], bg=C["bg"], wraplength=600,
                  justify="left").pack(anchor="w")
            return

        data = announce.load()
        entries = data.get("entries") or []
        err = data.get("error")

        if err:
            label(holder, err, font=F["small"], fg=C["warn"], bg=C["bg"],
                  wraplength=600, justify="left").pack(anchor="w")
            return

        if not entries:
            label(holder, "还没有公告内容。", font=F["small"], fg=C["dim"],
                  bg=C["bg"]).pack(anchor="w")
            return

        for idx, e in enumerate(entries):
            self._ann_row(holder, e, expanded=(idx == 0))
            if idx < len(entries) - 1:
                tk.Frame(holder, bg=C["line"], height=1).pack(fill="x", padx=12, pady=2)

        cur = announce.current(VERSION)
        if getattr(self, "_ann_hint", None) is not None:
            if cur.get("lines"):
                self._ann_hint.configure(text="当前版本 %s 的公告" % VERSION)
            else:
                self._ann_hint.configure(text="当前版本 %s 还没有写公告" % VERSION)

    def _ann_row(self, holder, entry, expanded=False):
        """One version entry. Expanded shows the full notes; collapsed is a clickable header."""
        # Not stretch=True: these cards live inside the scroll area, where the container has
        # no height of its own. A stretch card asks the parent for its height, gets 1px, and
        # collapses to nothing — which is exactly why the announcement page looked blank.
        card = Card(holder, radius=14, pad=6)
        card.pack(fill="x")
        body = card.body

        head = tk.Frame(body, bg=C["card"])
        head.pack(fill="x")

        ver = entry.get("version", "")
        date = entry.get("date", "")
        title = ver + ("  " + date if date else "")
        t = label(head, title, font=F["sec"], fg=C["acc"], bg=C["card"])
        t.pack(side="left", padx=(12, 10))

        if entry.get("is_current"):
            label(head, "当前版本", font=F["small"], fg=C["mint"], bg=C["card"]).pack(
                side="left", padx=(0, 8))

        count = len(entry.get("lines") or [])
        if count and not expanded:
            label(head, "%d 条" % count, font=F["small"], fg=C["dim"], bg=C["card"]).pack(
                side="left", padx=(0, 8))

        arrow = label(head, "▾" if expanded else "▸", font=F["body"], fg=C["dim"], bg=C["card"])
        arrow.pack(side="right", padx=(6, 14))

        lines_box = tk.Frame(body, bg=C["card"])

        def fill():
            """(Re)build the note lines. Group headings like 【素材】 stand out."""
            for w in lines_box.winfo_children():
                w.destroy()
            for item in entry.get("lines") or []:
                if item.get("heading"):
                    label(lines_box, item["text"], font=F["sec"], fg=C["txt"],
                          bg=C["card"], anchor="w").pack(fill="x", pady=(6, 2))
                else:
                    label(lines_box, "· " + item["text"], font=F["small"], fg=C["sub"],
                          bg=C["card"], wraplength=700, justify="left",
                          anchor="w").pack(fill="x", pady=1)

        if expanded:
            lines_box.pack(fill="x", padx=(12, 12), pady=(6, 10))
            fill()

        # Clicking the header toggles the body.
        state = {"open": expanded}

        def toggle(_e=None):
            state["open"] = not state["open"]
            if state["open"]:
                lines_box.pack(fill="x", padx=(12, 12), pady=(6, 10))
                fill()
            else:
                lines_box.pack_forget()
            arrow.configure(text="▾" if state["open"] else "▸")

        # Keep a reference on the widget: the closure otherwise cannot be reached from
        # outside, which makes the toggle impossible to test or to drive programmatically.
        t._ann_toggle = toggle

        if count:
            for w in (head, t, arrow):
                w.bind("<Button-1>", toggle)
                w.configure(cursor="hand2")

    # ---------- Chat page ----------
    def _build_chat(self, page):
        # Inside the scroll area a stretch card has no height to stretch into, so give the
        # chat log a real height instead.
        log_card = Card(page, radius=16, pad=0)
        log_card.pack(fill="x", padx=28, pady=(20, 0))
        log_card.configure(height=360)
        inner = tk.Frame(log_card.body, bg=C["card"])
        inner.pack(fill="both", expand=True, pady=14, padx=16)

        self.chat_log = tk.Text(inner, state="disabled", wrap="word", font=F["body"],
                                bg=C["card"], fg=C["txt"], relief="flat", bd=0,
                                padx=0, pady=0, insertbackground=C["txt"],
                                spacing1=2, spacing3=10, height=10)
        self.chat_log.pack(side="left", fill="both", expand=True)
        bar = tk.Frame(inner, bg=C["card"], width=6)
        bar.pack(side="right", fill="y")
        self._log_widget = self.chat_log

        self.chat_log.tag_configure("wolf", foreground=C["acc"],
                                    font=("Microsoft YaHei UI", 10, "bold"))
        self.chat_log.tag_configure("user", foreground=C["mint"],
                                    font=("Microsoft YaHei UI", 10, "bold"))
        self.chat_log.tag_configure("msg", foreground=C["txt"], lmargin1=14, lmargin2=14)
        self._append_log("wolf", "银狼", "（她抬眼看了你一眼）有事？说。")

        row = tk.Frame(page, bg=C["bg"])
        row.pack(fill="x", padx=28, pady=16)

        field = tk.Frame(row, bg=C["field"], highlightbackground=C["line"], highlightthickness=1)
        field.pack(side="left", fill="x", expand=True, padx=(0, 12))
        label(field, "›", font=F["mono"], fg=C["acc"]).pack(side="left", padx=(14, 6), pady=8)
        self.chat_entry = tk.Entry(field, font=F["body"], bg=C["field"], fg=C["txt"],
                                   relief="flat", bd=0, insertbackground=C["txt"])
        self.chat_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 12))
        self.chat_entry.bind("<Return>", lambda _e: self.send_from_page())

        Pill(row, "发送", self.send_from_page, kind="primary", h=38).pack(side="left")

    def send_from_page(self):
        if self.pet is None:
            return
        text = self.chat_entry.get().strip()
        if not text:
            return
        self.chat_entry.delete(0, "end")
        self.pet.send_chat_text(text)

    def on_chat_event(self, role, text):
        if role == "user":
            self._append_log("user", "你", text)
        else:
            self._append_log("wolf", "银狼", text)

    def _append_log(self, tag, speaker, text):
        self.chat_log.configure(state="normal")
        self.chat_log.insert("end", f"{speaker}", tag)
        self.chat_log.insert("end", "   ", "msg")
        self.chat_log.insert("end", text + "\n", "msg")
        self.chat_log.see("end")
        self.chat_log.configure(state="disabled")

    # ---------- Settings page ----------
    def _build_settings(self, page):
        card = Card(page, radius=16, pad=10)
        card.pack(fill="x", padx=28, pady=(16, 16))
        self.settings_panel = settings_ui.SettingsPanel(card.body, None)
        self.settings_panel.pack(fill="x")

    def attach_pet(self, pet):
        self.pet = pet
        pet.on_chat_event = self.on_chat_event
        pet.on_open_main = self._open_main
        if self.settings_panel is not None:
            self.settings_panel.pet = pet
        self._refresh_status()

    def _open_main(self):
        self.root.deiconify()
        # SW_MINIMIZE leaves the window iconic; Tk's deiconify does not always clear that state,
        # so restore through Win32 as well. Without it, clicking "打开主界面" does nothing.
        try:
            u = ctypes.windll.user32
            u.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
            hwnd = u.GetAncestor(int(self.root.winfo_id()), 2)
            if hwnd:
                u.ShowWindow(hwnd, 9)   # SW_RESTORE
        except Exception:
            pass
        self.root.lift()
        self.show_page("home")

    # ---------- Window buttons (used by the custom title bar) ----------

    def _wake_focus(self, event):
        """Activate the frameless window by hand.

        overrideredirect windows are not raised by Windows on click (the foreground stays
        with another process), so keys go there — the caret shows but nothing can be typed.
        So we grab Tk focus and also push the window to the foreground through Win32.
        """
        try:
            self.root.focus_force()
        except tk.TclError:
            pass
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            _force_foreground(hwnd)
        except Exception:
            pass
        w = event.widget
        if hasattr(w, "focus_set"):   # canvas bindings may hand us a string; skip those.
            try:
                w.focus_set()
            except tk.TclError:
                pass
        self._pet_on_top(False)

    def _pet_on_top(self, on):
        """While the main window is in front, drop the pet to the normal layer so it stays clear."""
        if self.pet is None:
            return
        try:
            self.pet.set_on_top(on)
        except Exception:
            pass

    def minimize_to_pet(self):
        """Minimise to the taskbar (not `withdraw`), keeping the taskbar button alive.

        `withdraw()` unmaps the window, and Windows drops a taskbar entry together with it —
        so collapsing used to leave only the sprite on screen with no way back except
        double-clicking her. SW_MINIMIZE keeps the window mapped and iconic, which is exactly
        the state the shell draws a taskbar button for; one click there restores it.
        """
        hwnd = 0
        try:
            hwnd = ctypes.windll.user32.GetAncestor(int(self.root.winfo_id()), 2)  # GA_ROOT
        except Exception:
            hwnd = 0
        if not hwnd:
            self.root.iconify()
            return
        try:
            u = ctypes.windll.user32
            u.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
            u.ShowWindow(hwnd, 6)      # SW_MINIMIZE: iconic, still mapped, taskbar button kept
        except Exception:
            try:
                self.root.iconify()
            except tk.TclError:
                pass
        # The pet stays where it is; she is the way back in if someone loses the button.
        if self.pet is not None:
            try:
                self.pet.show_bubble("窗口收到下面了，点任务栏或者双击我就能叫回来。", 2600)
            except Exception:
                pass

    def quit_app(self):
        """Self-drawn close button: quits the pet as well."""
        try:
            self.root.destroy()
        except tk.TclError:
            pass




