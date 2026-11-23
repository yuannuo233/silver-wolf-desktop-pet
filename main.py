"""Silver Wolf desktop pet — entry point.

Double-clicking the app opens the main window (app.py); the floating
pet spawns as its always-on-top companion. Closing the window quits both.
"""

import base64
import io
import sys
from pathlib import Path

# ---- environment gate -------------------------------------------------------
# Fail loudly *and readably* on the wrong interpreter / OS. Without this, running on
# Python 3.8 or on macOS surfaces as a wall of traceback from deep inside ctypes, which
# tells a user nothing. See README "系统与环境要求" for the measured minimums.
MIN_PY = (3, 10)


def _bail(title, detail):
    """Show the reason in a message box when possible, print it otherwise, then exit.

    The text always goes to stderr FIRST: if the process was started from a console (the .bat,
    an IDE, a remote shell) the user sees it there even when no message box can appear.
    """
    msg = "%s\n\n%s" % (title, detail)
    try:
        sys.stderr.write("[SilverWolfPet] " + msg.replace("\n", "\n[SilverWolfPet] ") + "\n")
        sys.stderr.flush()
    except Exception:
        pass
    try:
        import tkinter.messagebox as mb
        import tkinter as _tk
        _r = _tk.Tk()
        _r.withdraw()
        mb.showerror("银狼桌宠 · 无法启动", msg)
        _r.destroy()
    except Exception:
        pass
    sys.exit(1)


if sys.version_info < MIN_PY:
    _bail(
        "Python 版本过低：%d.%d（需要 %d.%d 或更高）"
        % (sys.version_info[0], sys.version_info[1], MIN_PY[0], MIN_PY[1]),
        "当前解释器：%s\n\n请安装 Python %d.%d 或更高版本（64 位）后重试。\n"
        "下载：https://www.python.org/downloads/windows/\n"
        "安装时请勾选「tcl/tk and IDLE」（tkinter 界面库）。\n"
        "或者直接用发布页的 exe，完全不需装 Python。"
        % (sys.executable, MIN_PY[0], MIN_PY[1]),
    )

if sys.platform != "win32":
    _bail(
        "不支持当前操作系统：%s" % sys.platform,
        "本项目依赖 Windows 专有的窗口 API（透明桌宠窗口、任务栏按钮、键盘钩子），\n"
        "在 macOS / Linux 上无法运行。\n\n"
        "详细原因见仓库 LIMITATIONS.md。\n"
        "想跨平台用，请走 PROTOCOL.md 里的 L3 事件通道（由宿主提供活动状态）。",
    )

if sys.maxsize <= 2 ** 32:
    _bail(
        "需要 64 位 Python",
        "检测到 32 位解释器：%s\n\n"
        "程序里有多处 Win32 指针按 64 位声明，32 位下会崩溃。\n"
        "请安装 64 位 Python，或直接用发布页的 exe。" % sys.executable,
    )

# ★ Windows HiDPI (e.g. 150% scaling): make the process DPI-aware.
# Otherwise tkinter assumes a 1280x720 logical screen, so pet position,
# size and mouse coords all drift by the scale factor.
# Must run before any window is created.
import ctypes

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)   # per-monitor DPI
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import tkinter as tk

import config
import ui
from app import MainApp
from pet import SilverWolfPet

# ★ Set the palette before building widgets (ui.C is read at creation time).
ui.apply_theme(config.load().get("theme", "light"))


def resource_path(relative: str) -> Path:
    """Resolve a bundled file in both source mode and PyInstaller mode."""
    base = getattr(sys, "_MEIPASS", None)  # only set inside a PyInstaller exe
    if base:
        return Path(base) / relative
    return Path(__file__).resolve().parent / relative


def hide_own_console() -> bool:
    """Hide the black console window that python.exe drags along.

    python.exe is a console program, so double-clicking main.py (or launching it from a
    .bat with `start`) creates a console just for us. Hiding it is safe *only* when the
    console belongs to us alone; a console the user opened themselves (cmd / PowerShell /
    Windows Terminal) also holds their shell, and hiding that would wipe their terminal.
    So: hide when every attached process is a Python launcher, leave it alone otherwise.
    A packaged exe has no console at all and this returns False.
    """
    try:
        k32 = ctypes.windll.kernel32
        k32.GetConsoleWindow.restype = ctypes.c_void_p
        k32.GetConsoleProcessList.restype = ctypes.c_uint
        k32.GetConsoleProcessList.argtypes = [ctypes.POINTER(ctypes.c_uint), ctypes.c_uint]
        k32.OpenProcess.restype = ctypes.c_void_p
        k32.OpenProcess.argtypes = [ctypes.c_uint, ctypes.c_int, ctypes.c_uint]
        k32.QueryFullProcessImageNameW.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                                   ctypes.c_wchar_p,
                                                   ctypes.POINTER(ctypes.c_uint)]
        k32.CloseHandle.argtypes = [ctypes.c_void_p]

        hwnd = k32.GetConsoleWindow()
        if not hwnd:
            return False                                  # console=False build: nothing to hide
        # GetConsoleProcessList(None, 0) does not report a required length (it fails with
        # error 87), so hand it a fixed buffer instead of asking first.
        cap = 16
        buf = (ctypes.c_uint * cap)()
        count = k32.GetConsoleProcessList(buf, cap)
        if count < 1 or count > cap:
            return False
        launchers = {"python.exe", "pythonw.exe", "py.exe", "pyw.exe"}
        for i in range(count):
            handle = k32.OpenProcess(0x1000, False, buf[i])   # QUERY_LIMITED_INFORMATION
            if not handle:
                return False                              # can't inspect -> assume it's not ours
            try:
                cb = ctypes.c_uint(1024)
                name = ctypes.create_unicode_buffer(1024)
                if not k32.QueryFullProcessImageNameW(handle, 0, name, ctypes.byref(cb)):
                    return False
            finally:
                k32.CloseHandle(handle)
            if Path(name.value).name.lower() not in launchers:
                return False                              # a real shell shares this console
        ctypes.windll.user32.ShowWindow(hwnd, 0)          # SW_HIDE
        return True
    except Exception:
        return False


def load_photo(path: Path):
    """Load an image for tkinter; returns None if missing."""
    try:
        return tk.PhotoImage(file=str(path))
    except tk.TclError:
        return None


def load_scaled_photo(path: Path, width: int, radius: int = 0, bg: str = None):
    """Scale an image to the requested width (needs Pillow; PNG -> base64)."""
    try:
        from PIL import Image, ImageDraw
        img = Image.open(path).convert("RGBA")
        height = max(1, round(img.height * width / img.width))
        img = img.resize((width, height), Image.LANCZOS)
        if radius:
            mask = Image.new("L", (width, height), 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, width - 1, height - 1),
                                                  radius=radius, fill=255)
            if bg:
                # Tk cannot alpha-blend: transparent corners render as black. Bake the corners
                # onto the real background colour instead, so no dark fringe shows.
                flat = Image.new("RGBA", img.size, bg)
                flat.paste(img, (0, 0), mask)
                img = flat
            else:
                img.putalpha(mask)
        buf = io.BytesIO()
        img.save(buf, "PNG")
        return tk.PhotoImage(data=base64.b64encode(buf.getvalue()))
    except Exception:
        return None


def build_images() -> dict:
    """Build the whole tk image set for the active palette."""
    return {
        "icon": load_photo(resource_path("icon.png")),
        # The icon is already a filled square, so no rounding here (radius=0).
        "icon_small": load_scaled_photo(resource_path("icon.png"), 56, radius=10,
                                        bg=ui.C["rail"]),
        # v0.6.13: small icon for the custom title bar (32px, inline with the title).
        "icon_tiny": load_scaled_photo(resource_path("icon.png"), 32, radius=7,
                                       bg=ui.C["rail"]),
        "banner": load_scaled_photo(resource_path("assets/banner.png"), 210, radius=14,
                                    bg=ui.C["card"]),
    }


_U32 = ctypes.windll.user32
_U32.GetAncestor.restype = ctypes.c_void_p
_U32.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
_U32.GetWindowLongW.restype = ctypes.c_uint
_U32.GetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int]
_U32.SetWindowLongW.restype = ctypes.c_uint
_U32.SetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_uint]
_U32.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]


def show_in_taskbar(win) -> bool:
    """Give the frameless window a taskbar button.

    overrideredirect windows carry WS_EX_TOOLWINDOW, and Windows gives those no taskbar
    entry at all. Flip that bit to WS_EX_APPWINDOW and re-show the window so the shell
    registers the button. Must run *after* the window is mapped (Tk only creates the real
    wrapper then), and without it a collapsed window has no way back except double-clicking
    the sprite.
    """
    try:
        hwnd = _U32.GetAncestor(int(win.winfo_id()), 2)       # 2 = GA_ROOT
        if not hwnd:
            return False                                      # not mapped yet
        GWL_EXSTYLE, TOOL, APP = -20, 0x00000080, 0x00040000
        style = _U32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        _U32.SetWindowLongW(hwnd, GWL_EXSTYLE, (style & ~TOOL) | APP)
        _U32.ShowWindow(hwnd, 0)      # hide + show is what makes the shell add the button
        _U32.ShowWindow(hwnd, 5)
        return True
    except Exception:
        return False


def set_window_icon(win) -> None:
    """Push icon.ico onto the window with WM_SETICON.

    Tk's iconphoto only sets the big icon, and iconbitmap is unreliable with non-ASCII
    paths, so the taskbar button kept the default Python mark. Loading the .ico directly
    and sending WM_SETICON for both sizes fixes the taskbar and Alt-Tab preview.
    """
    try:
        hwnd = _U32.GetAncestor(int(win.winfo_id()), 2)
        if not hwnd:
            return
        u = ctypes.windll.user32
        u.LoadImageW.restype = ctypes.c_void_p
        u.LoadImageW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint,
                                 ctypes.c_int, ctypes.c_int, ctypes.c_uint]
        u.SendMessageW.restype = ctypes.c_ssize_t
        u.SendMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                   ctypes.c_void_p, ctypes.c_void_p]
        path = str(resource_path("icon.ico"))
        # Sizes: ICON_BIG, ICON_SMALL, ICON_SMALL2. The taskbar and Alt-Tab read SMALL2 on
        # modern Windows, so leaving it unset falls back to the exe icon.
        for size, which in ((32, 1), (16, 0), (16, 2)):
            handle = u.LoadImageW(None, path, 1, size, size, 0x10)  # IMAGE_ICON | LR_LOADFROMFILE
            if handle:
                u.SendMessageW(hwnd, 0x0080, which, handle)         # WM_SETICON
    except Exception:
        pass


def claim_taskbar_identity() -> None:
    """Give this process its own AppUserModelID.

    Running from source means the process is python.exe, and Windows labels every taskbar
    button of a process with the identity its exe implies — so the button showed the Python
    logo no matter what WM_SETICON said. An explicit AppUserModelID detaches the process from
    python.exe's identity, after which the button uses the window icon instead. Must run
    before any window is created.
    """
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            ctypes.c_wchar_p("SilverWolf.DesktopPet"))
    except Exception:
        pass


def warn_missing_pillow() -> None:
    """Warn once when Pillow is absent.

    The app still starts without it (pet.py degrades to a single floating frame), and that
    silent degradation is exactly the confusing part: it looks like a broken animation rather
    than a missing dependency. Say so out loud, once, then let them carry on.
    """
    try:
        import PIL
        _ = PIL.__version__          # touch it so the import is not flagged as unused
        return
    except ImportError:
        pass
    msg = (
        "缺少 Pillow，帧动画将退化为单帧浮动模式。\n\n"
        "安装命令（在项目目录下执行）：\n"
        "    python -m pip install -r requirements.txt\n\n"
        "或直接安装：python -m pip install Pillow\n\n"
        "装好后重启本程序即可恢复完整动画。"
    )
    try:
        import tkinter.messagebox as mb
        mb.showwarning("银狼桌宠 · 缺少 Pillow", msg)
    except Exception:
        sys.stderr.write(msg + "\n")


def show_terms_once(root) -> None:
    """Show the terms notice the first time the app runs, then never again.

    The licence and TERMS.md already say the authors are not responsible for how anyone uses
    this code, but a file in a repository is easy to never open. Showing it once — in the app
    itself — makes the boundary visible to whoever actually runs it.
    """
    try:
        cfg = config.load()
        if cfg.get("terms_seen"):
            return
        cfg["terms_seen"] = True
        config.save(cfg)
    except Exception:
        return
    try:
        win = tk.Toplevel(root)
        win.title("使用条款")
        win.configure(bg=ui.C["card"])
        win.attributes("-topmost", True)
        win.resizable(False, False)
        body = (
            "本程序仅限桌面装饰与娱乐用途。\n\n"
            "使用、修改或再分发本程序的行为，由实施者自行承担全部责任，\n"
            "与原作者无关。原作者不认可、不参与、也无法监督任何下游使用。\n\n"
            "禁止用于违法、未授权入侵、恶意软件、窃取凭证、诈骗、\n"
            "侵权或商业用途。\n\n"
            "完整条款见仓库中的 TERMS.md、DISCLAIMER.md 与 LICENSE。"
        )
        tk.Label(win, text=body, bg=ui.C["card"], fg=ui.C["txt"],
                 font=("Microsoft YaHei UI", 10), justify="left",
                 padx=22, pady=18).pack()
        tk.Button(win, text="我知道了", width=14, relief="flat",
                  bg=ui.C["acc"], fg=ui.C["on_acc"],
                  font=("Microsoft YaHei UI", 10),
                  command=win.destroy).pack(pady=(0, 18))
        win.update_idletasks()
        w, h = win.winfo_reqwidth(), win.winfo_reqheight()
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f"+{(sw - w) // 2}+{(sh - h) // 3}")
    except tk.TclError:
        pass


def main() -> None:
    hide_own_console()
    claim_taskbar_identity()
    root = tk.Tk()
    # The taskbar button draws its icon from WM_SETICON(SMALL), which iconphoto does not set,
    # so without the .ico the taskbar shows the plain Python icon instead of Silver Wolf.
    try:
        root.iconbitmap(str(resource_path("icon.ico")))
    except Exception:
        pass

    images = build_images()

    app = MainApp(root, images, build_images)
    pet = SilverWolfPet(
        root,
        str(resource_path("assets/silver_wolf.png")),
        hd_path=str(resource_path("assets/silver_wolf_hd.png")),
    )
    app.attach_pet(pet)
    # Let an interop host ask for a theme switch (PROTOCOL.md, event "theme").
    pet.on_theme_request = app.set_theme

    # L3 interop bridge (PROTOCOL.md): lets another pet framework feed her activity state and
    # receive her state/chat events. Optional — if the directory cannot be created it stays off.
    try:
        import interop
        pet.interop = interop.Interop(pet)
        pet.interop.start()
    except Exception:
        pet.interop = None

    # Make sure the window shows up in FRONT on launch.
    root.update_idletasks()
    root.lift()
    root.focus_force()
    # Wait until Tk has actually mapped the real wrapper, then turn it into an app window
    # (taskbar button) and push the .ico onto it.
    for delay in (300, 1200):
        root.after(delay, lambda: (show_in_taskbar(root), set_window_icon(root)))
    root.attributes("-topmost", True)
    root.after(250, lambda: root.attributes("-topmost", False))

    root.after(700, warn_missing_pillow)
    root.after(900, lambda: show_terms_once(root))

    root.mainloop()


if __name__ == "__main__":
    main()
