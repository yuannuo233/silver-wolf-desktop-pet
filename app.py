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

NAV = (("home", "主页", "◈"), ("chat", "聊天", "✧"), ("settings", "设置", "⚙"))
VERSION = "v0.6.19"


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


class MainApp:
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
        self.rail = None
        self.wrap = None

        root.title("银狼桌宠")
        # v0.6.13: no native title bar (the white strip + system buttons look like an OS
        # component); the whole UI is self-drawn, with TitleBar standing in at the top.
        root.overrideredirect(True)
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        w, h = min(1000, sw - 40), min(760, sh - 60)
        root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 3}")
        root.minsize(760, 560)
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
        """
        self.root.update_idletasks()
        w = self.root.winfo_width() or 1000
        page = self.pages[key or self.current_page]
        off = max(0, page.winfo_rooty() - self.root.winfo_rooty())
        need = off + page.winfo_reqheight() + 12
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
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
        builders = {"home": self._build_home, "chat": self._build_chat, "settings": self._build_settings}
        for key, build in builders.items():
            page = tk.Frame(container, bg=C["bg"])
            page.place(x=0, y=0, relwidth=1, relheight=1)
            build(page)
            self.pages[key] = page

    def show_page(self, key):
        self.current_page = key
        self.pages[key].tkraise()
        for k, item in self.nav_items.items():
            item.active = (k == key)
            item._draw()
        titles = {"home": ("主页", "银狼已经挂在你屏幕上了，随时待命"),
                  "chat": ("聊天", "说的话会同时出现在她头顶的气泡里"),
                  "settings": ("设置", "接一个 OpenAI 兼容接口，她就有脑子了")}
        t, s = titles[key]
        self.page_title.configure(text=t)
        self.page_sub.configure(text=s)
        if key == "home":
            self._refresh_status()
        if key == "chat":
            self.chat_entry.focus_set()
        if self._ready:
            self._fit_window(key)
            self.root.after(40, self._reflow)

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

    # ---------- Chat page ----------
    def _build_chat(self, page):
        log_card = Card(page, radius=16, pad=0, stretch=True)
        log_card.pack(fill="both", expand=True, padx=28, pady=(20, 0))
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




