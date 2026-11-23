"""Settings panel: provider presets / base URL, key and model / persona prompt.

Dark theme: shares the palette in ui.py; dark borderless inputs, pill presets.
"""

import threading
import tkinter as tk
from tkinter import ttk

import ai_client
import config
import prompts
import updater
from ui import C, F, Pill, label

PROVIDERS = [
    ("自定义", "", ""),
    ("DeepSeek", "https://api.deepseek.com/v1", "deepseek-chat"),
    ("智谱 GLM（有免费模型）", "https://open.bigmodel.cn/api/paas/v4", "glm-4-flash"),
    ("通义千问", "https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-turbo"),
    ("Kimi", "https://api.moonshot.cn/v1", "moonshot-v1-8k"),
    ("豆包·火山方舟", "https://ark.cn-beijing.volces.com/api/v3", ""),
    ("OpenAI", "https://api.openai.com/v1", "gpt-4o-mini"),
    ("Ollama 本地（无需密钥）", "http://127.0.0.1:11434/v1", "qwen2.5:7b"),
]


class SettingsPanel(tk.Frame):
    """The whole settings form, embeddable in the main window settings page."""

    def __init__(self, master, pet):
        super().__init__(master, bg=C["card"])
        self.pet = pet
        self.cfg = config.load()
        self.check_updates_var = tk.BooleanVar(value=bool(self.cfg.get("check_updates", True)))
        self._build()
        self._fill_form()

    # ---------- Small parts ----------
    def _section(self, text, hint="", parent=None):
        row = tk.Frame(parent or self, bg=C["card"])
        row.pack(fill="x", padx=18, pady=(8, 4))
        label(row, text, font=F["mono_s"], fg=C["acc"], bg=C["card"]).pack(side="left")
        if hint:
            label(row, hint, font=F["small"], fg=C["dim"], bg=C["card"]).pack(side="left", padx=8)

    def _entry(self, show="", parent=None):
        holder = tk.Frame(parent or self, bg=C["field"], highlightbackground=C["line"],
                          highlightthickness=1)
        holder.pack(fill="x", padx=18)
        entry = tk.Entry(holder, show=show, font=F["mono_s"], bg=C["field"], fg=C["txt"],
                         relief="flat", bd=0, insertbackground=C["acc"],
                         highlightthickness=0)
        entry.pack(fill="x", ipady=5, padx=10)
        return entry

    # ---------- Assemble ----------
    def _build(self):
        self._dark_combo_style()

        self._section("PROVIDER", "选一家就自动填地址和模型名")
        holder = tk.Frame(self, bg=C["line"], highlightthickness=0)
        holder.pack(fill="x", padx=18)
        self.provider = ttk.Combobox(holder, values=[p[0] for p in PROVIDERS],
                                     state="readonly", font=F["body"], height=10,
                                     style="Dark.TCombobox")
        self.provider.pack(fill="x", padx=1, pady=1)
        self.provider.bind("<<ComboboxSelected>>", self._apply_preset)

        self._section("BASE_URL", "OpenAI 兼容地址，结尾一般带 /v1")
        self.url = self._entry()

        self._section("API KEY", "只存在你电脑上，不上传")
        self.key = self._entry(show="*")

        self._section("MODEL", "模型名，照厂商文档填")
        self.model = self._entry()

        # Character switching lives on its own page (nav "角色") — it needs a list with
        # per-character state, which does not fit a one-line button row here.
        self._chosen_character = self.cfg.get("character", "")

        self._section("PERSONA", "三档人设，点一下填进去，之后随便改")
        row = tk.Frame(self, bg=C["card"])
        row.pack(fill="x", padx=18, pady=(0, 7))
        for i, name in enumerate(prompts.PROMPTS):
            Pill(row, name, lambda n=name: self._load_prompt(n),
                 kind="outline" if i else "ghost", h=28,
                 font=F["small"]).pack(side="left", padx=(0, 8))

        wrap = tk.Frame(self, bg=C["field"], highlightbackground=C["line"], highlightthickness=1)
        wrap.pack(fill="both", expand=True, padx=18, pady=(0, 8))
        self.prompt = tk.Text(wrap, height=4, wrap="word", font=F["small"],
                              bg=C["field"], fg=C["txt"], relief="flat", bd=0,
                              insertbackground=C["acc"], highlightthickness=0,
                              padx=10, pady=8, spacing1=1, spacing3=2)
        self.prompt.pack(fill="both", expand=True)

        bottom = tk.Frame(self, bg=C["card"])
        bottom.pack(fill="x", padx=18, pady=(2, 14))
        Pill(bottom, "保存", self._save, kind="primary", h=34).pack(side="left")
        Pill(bottom, "发一句测试", self._test, kind="ghost", h=34).pack(side="left", padx=10)
        Pill(bottom, "检查更新", self._check_update, kind="ghost", h=34).pack(side="left")
        self.status = label(bottom, "", font=F["small"], fg=C["dim"], bg=C["card"], wraplength=300,
                            justify="left")
        self.status.pack(side="left", padx=6)

        # Update-check switch. On by default: publishing a Release only notifies watchers, so
        # the app has to look for itself or nobody who merely downloaded the zip ever hears
        # about a new version. Off means zero network traffic beyond the AI chat you configured.
        opt = tk.Frame(self, bg=C["card"])
        opt.pack(fill="x", padx=18, pady=(0, 6))
        cb = tk.Checkbutton(
            opt, text="启动时检查新版本（只读取 GitHub 的版本号，不上传任何数据）",
            variable=self.check_updates_var, font=F["small"],
            bg=C["card"], fg=C["sub"], activebackground=C["card"], activeforeground=C["txt"],
            selectcolor=C["field"], bd=0, highlightthickness=0, anchor="w",
        )
        cb.pack(fill="x")

        # Terms notice. Kept short on purpose: the full text lives in TERMS.md / DISCLAIMER.md,
        # but the "you are responsible for your own use" line has to be visible in the app, not
        # only in the repository, or nobody will ever read it.
        notice = label(
            self,
            "本程序仅限桌面装饰与娱乐用途。使用、修改或再分发本程序的行为由实施者自行"
            "承担全部责任，与原作者无关；详见仓库 TERMS.md 与 DISCLAIMER.md。",
            font=F["small"], fg=C["dim"], bg=C["card"], wraplength=520, justify="left")
        notice.pack(fill="x", padx=18, pady=(0, 14))

    def _dark_combo_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Dark.TCombobox", fieldbackground=C["field"], background=C["field"],
                        foreground=C["txt"], arrowcolor=C["acc"], bordercolor=C["line"],
                        lightcolor=C["field"], darkcolor=C["field"], padding=6,
                        selectbackground=C["field"], selectforeground=C["txt"],
                        insertcolor=C["txt"])
        style.map("Dark.TCombobox", fieldbackground=[("readonly", C["field"])],
                  foreground=[("readonly", C["txt"])],
                  background=[("active", C["card_hover"])] if "card_hover" in C else [])
        try:
            self.winfo_toplevel().option_add("*TCombobox*Listbox.background", C["field"])
            self.winfo_toplevel().option_add("*TCombobox*Listbox.foreground", C["txt"])
            self.winfo_toplevel().option_add("*TCombobox*Listbox.selectBackground", C["acc_soft"])
            self.winfo_toplevel().option_add("*TCombobox*Listbox.selectForeground", C["txt"])
        except tk.TclError:
            pass

    # ---------- Data ----------
    def _fill_form(self):
        self.url.delete(0, "end")
        self.url.insert(0, self.cfg.get("base_url", ""))
        self.key.delete(0, "end")
        self.key.insert(0, self.cfg.get("api_key", ""))
        self.model.delete(0, "end")
        self.model.insert(0, self.cfg.get("model", ""))
        self.prompt.delete("1.0", "end")
        self.prompt.insert("1.0", self.cfg.get("prompt_text", prompts.PROMPTS["平衡版"]))
        # Fill the dropdown from the saved URL; an unknown URL falls back to "Custom".
        self.provider.set(self._match_provider(self.cfg.get("base_url", "")))

    def _match_provider(self, url: str) -> str:
        for name, purl, _m in PROVIDERS:
            if purl and purl == url:
                return name
        return PROVIDERS[0][0]

    def refresh(self):
        self.cfg = config.load()
        self._fill_form()

    def _apply_preset(self, _event=None):
        for name, url, model in PROVIDERS:
            if name == self.provider.get():
                self.url.delete(0, "end")
                self.url.insert(0, url)
                if model:
                    self.model.delete(0, "end")
                    self.model.insert(0, model)
                self.status.configure(text=f"已填 {name} 的默认地址", fg=C["dim"])
                break

    def _load_prompt(self, name):
        self.prompt.delete("1.0", "end")
        self.prompt.insert("1.0", prompts.PROMPTS[name])
        self.status.configure(text=f"已填入{name}，可继续编辑", fg=C["dim"])

    def _collect(self) -> dict:
        size = 200
        if self.pet is not None:
            size = self.pet.settings.get("size_height", 200)
        else:
            size = self.cfg.get("size_height", 200)
        # Start from the stored config and override only the fields this panel owns.
        # Returning a fresh dict (the old behaviour) silently wiped every other key — theme,
        # follow_activity, terms_seen, the update-dismissal tag — the moment the user hit Save.
        out = dict(self.cfg)
        out.update({
            "base_url": self.url.get().strip(),
            "api_key": self.key.get().strip(),
            "model": self.model.get().strip(),
            "prompt_text": self.prompt.get("1.0", "end").strip() or prompts.PROMPTS["平衡版"],
            "size_height": size,
            "check_updates": bool(self.check_updates_var.get()),
            "character": getattr(self, "_chosen_character", out.get("character", "")),
        })
        return out

    def _save(self):
        self.cfg = self._collect()
        config.save(self.cfg)
        if self.pet is not None:
            self.pet.settings = self.cfg
        self.status.configure(text="已保存", fg=C["mint"])

    def _test(self):
        cfg = self._collect()
        if not cfg["base_url"] or not cfg["model"]:
            self.status.configure(text="先填地址和模型名", fg=C["warn"])
            return
        self.status.configure(text="测试中…", fg=C["sub"])
        threading.Thread(target=self._test_worker, args=(cfg,), daemon=True).start()

    def _test_worker(self, cfg):
        try:
            reply = ai_client.chat(cfg["base_url"], cfg["api_key"], cfg["model"],
                                   cfg["prompt_text"], "你好，报上名来", None)
        except ai_client.AIError as err:
            # Python 3 deletes the exception variable when the except block ends, so capture the text first.
            msg = str(err)[:60]
            self.after(0, lambda: self.status.configure(text=msg, fg=C["warn"]))
            return
        self.after(0, lambda: self.status.configure(text="回复：" + reply[:24], fg=C["mint"]))

    # ---------- Update check ----------

    def _check_update(self):
        """Ask GitHub for the newest release and report it in the status line."""
        from app import VERSION      # imported lazily: app imports this module

        self.status.configure(text="正在检查更新…", fg=C["sub"])
        panel = self

        def done(info):
            # Marshal back to the Tk thread. Guarded because the panel can be destroyed
            # (theme switch rebuilds the whole page) before the request returns.
            try:
                panel.after(0, lambda: panel._show_update_result(info, VERSION))
            except (tk.TclError, AttributeError):
                pass          # widget gone; nothing to update

        updater.check_async(VERSION, done)

    def _show_update_result(self, info, current):
        """Report the outcome. `info` is None both for 'up to date' and for 'no answer', so
        distinguish them: an unreachable server must not be reported as 'up to date'."""
        try:
            if info:
                tag = info["tag"]
                self.status.configure(text="发现新版本 %s（点「去下载」打开下载页）" % tag,
                                      fg=C["warn"])
                self._bind_update_link(info.get("page"))
            elif updater.last_error is None:
                self.status.configure(text="已是最新版本（%s）" % current, fg=C["mint"])
            else:
                self.status.configure(text="检查失败：网络不通或被限流，稍后再试", fg=C["warn"])
        except tk.TclError:
            pass

    def _bind_update_link(self, page):
        if not page:
            return
        try:
            import webbrowser
            for w in self.status.master.winfo_children():
                if isinstance(w, Pill) and getattr(w, "_update_link", False):
                    return
            btn = Pill(self.status.master, "去下载", kind="primary", h=34)
            btn._update_link = True
            btn.configure(cursor="hand2")
            btn.pack(side="left", padx=6)
            btn.bind("<Button-1>", lambda _e: webbrowser.open(page))
        except Exception:
            pass


class SettingsWindow:
    """Standalone settings window used by the right-click menu."""

    def __init__(self, root, pet):
        self.win = tk.Toplevel(root)
        self.win.title("银狼桌宠 · 设置")
        self.win.attributes("-topmost", True)
        self.win.configure(bg=C["card"])
        self.win.resizable(False, False)
        self.panel = SettingsPanel(self.win, pet)
        self.panel.pack(fill="both", expand=True)
        self.win.update_idletasks()
        w, h = 500, 680
        x = self.win.winfo_screenwidth() - w - 80
        y = max(0, (self.win.winfo_screenheight() - h) // 2 - 40)
        self.win.geometry(f"{w}x{h}+{x}+{y}")


def rebind_theme():
    """Called by app after a theme switch; this module reads C[...], so it is a no-op."""
    return None
