# -*- coding: utf-8 -*-
"""Sherlock GUI - desktop front-end for sherlock-project/sherlock.

Run:  python gui.py   /  pythonw gui.pyw   /  --selftest (headless check)
"""
from __future__ import annotations

import json
import os
import queue
import sys
import tempfile
import threading
import webbrowser
from datetime import datetime
from tkinter import BooleanVar, IntVar, StringVar, filedialog, messagebox, scrolledtext
import tkinter as tk
from tkinter import ttk

import sherlock_core as core

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

APP_TITLE = "Sherlock GUI"
REPO_URL = "https://github.com/sherlock-project/sherlock"
FONT = "Microsoft YaHei UI"
CONFIG_FILE = os.path.join(core.app_dir(), "config.json")

DEFAULTS = {
    "theme": "light",
    "timeout": 15,
    "proxy": "",
    "include_nsfw": False,
    "show_all": False,
    "topmost": False,
    "font_size": 10,
    "geometry": "1080x720",
}

THEMES = {
    "light": dict(bg="#F3F6FB", surface="#FFFFFF", fg="#1F2937", muted="#6B7280",
                  accent="#1D4ED8", accent_fg="#FFFFFF", border="#E2E8F0",
                  tree="#FFFFFF", alt="#F7FAFF", log_bg="#0F172A", log_fg="#E2E8F0"),
    "dark": dict(bg="#111827", surface="#1F2937", fg="#E5E7EB", muted="#9CA3AF",
                 accent="#3B82F6", accent_fg="#FFFFFF", border="#374151",
                 tree="#1B2433", alt="#232F42", log_bg="#0B1220", log_fg="#D1D5DB"),
}


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.cfg = self._load_config()
        self.q: queue.Queue = queue.Queue()
        self.rows: list[dict] = []
        self.worker = None
        self.stop_event = threading.Event()
        self.busy = False
        self._themed: list[tuple] = []
        self.style = ttk.Style()

        self.user_var = StringVar()
        self.site_var = StringVar()
        self.timeout_var = IntVar(value=self.cfg["timeout"])
        self.proxy_var = StringVar(value=self.cfg["proxy"])
        self.nsfw_var = BooleanVar(value=self.cfg["include_nsfw"])
        self.only_found_var = BooleanVar(value=not self.cfg["show_all"])
        self.status_var = StringVar(value="就绪")
        self.count_var = StringVar(value="命中 0 / 结果 0")
        self.theme_var = StringVar(value=self.cfg["theme"])
        self.font_var = IntVar(value=self.cfg["font_size"])
        self.topmost_var = BooleanVar(value=self.cfg["topmost"])

        self._build_ui()
        self._apply_theme()
        self.root.attributes("-topmost", bool(self.cfg["topmost"]))
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(80, self._poll)
        self.log(f"就绪 · Sherlock v{core.__version__} · 内置 {core.site_count()} 个站点", "ok")

    # ---------- config ----------
    def _load_config(self) -> dict:
        cfg = dict(DEFAULTS)
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
                cfg.update(json.load(fh))
        except (OSError, ValueError):
            pass
        return cfg

    def _save_config(self) -> None:
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as fh:
                json.dump(self.cfg, fh, ensure_ascii=False, indent=2)
        except OSError:
            pass

    # ---------- theme ----------
    def _f(self, delta=0, bold=False):
        size = max(8, int(self.cfg["font_size"]) + delta)
        return (FONT, size, "bold") if bold else (FONT, size)

    def _reg(self, widget, kind="frame"):
        self._themed.append((widget, kind))
        return widget

    def _apply_theme(self):
        c = THEMES.get(self.cfg["theme"], THEMES["light"])
        st = self.style
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        st.configure(".", background=c["bg"], foreground=c["fg"], font=self._f())
        st.configure("TFrame", background=c["bg"])
        st.configure("Card.TFrame", background=c["surface"])
        st.configure("TLabel", background=c["bg"], foreground=c["fg"])
        st.configure("Card.TLabel", background=c["surface"], foreground=c["fg"])
        st.configure("Muted.TLabel", background=c["surface"], foreground=c["muted"])
        st.configure("TButton", background=c["surface"], foreground=c["fg"],
                     bordercolor=c["border"], focusthickness=0, padding=(12, 6))
        st.map("TButton", background=[("active", c["alt"])])
        st.configure("Accent.TButton", background=c["accent"], foreground=c["accent_fg"],
                     borderwidth=0, padding=(18, 7), font=self._f(0, True))
        st.map("Accent.TButton", background=[("active", c["accent"])])
        st.configure("TCheckbutton", background=c["surface"], foreground=c["fg"])
        st.configure("TRadiobutton", background=c["surface"], foreground=c["fg"])
        st.configure("TEntry", fieldbackground=c["surface"], foreground=c["fg"],
                     bordercolor=c["border"], insertcolor=c["fg"], padding=6)
        st.configure("TSpinbox", fieldbackground=c["surface"], foreground=c["fg"],
                     bordercolor=c["border"], padding=4)
        st.configure("TNotebook", background=c["bg"], borderwidth=0)
        st.configure("TNotebook.Tab", background=c["bg"], foreground=c["muted"],
                     padding=(20, 9), font=self._f())
        st.map("TNotebook.Tab", background=[("selected", c["surface"])],
               foreground=[("selected", c["accent"])])
        st.configure("Treeview", background=c["tree"], fieldbackground=c["tree"],
                     foreground=c["fg"], rowheight=27, borderwidth=0, font=self._f())
        st.map("Treeview", background=[("selected", c["accent"])],
               foreground=[("selected", "#FFFFFF")])
        st.configure("Treeview.Heading", background=c["accent"], foreground="#FFFFFF",
                     borderwidth=0, font=self._f(0, True))
        st.configure("TProgressbar", background=c["accent"], troughcolor=c["surface"],
                     borderwidth=0, thickness=8)
        st.configure("Horizontal.TScale", background=c["surface"])
        for widget, kind in self._themed:
            try:
                if kind == "frame":
                    widget.configure(bg=c["surface"])
                elif kind == "header":
                    widget.configure(bg=c["bg"])
                elif kind == "label":
                    widget.configure(bg=c["surface"], fg=c["fg"])
                elif kind == "muted":
                    widget.configure(bg=c["surface"], fg=c["muted"])
                elif kind == "title":
                    widget.configure(bg=c["surface"], fg=c["accent"])
                elif kind == "log":
                    widget.configure(bg=c["log_bg"], fg=c["log_fg"],
                                     insertbackground=c["log_fg"])
            except tk.TclError:
                pass
        self.root.configure(bg=c["bg"])
        self.tree.tag_configure("odd", background=c["alt"])
        self.tree.tag_configure("found", foreground=c["accent"])

    # ---------- UI ----------
    def _build_ui(self):
        r = self.root
        r.title(f"{APP_TITLE} · 用户名检索工具")
        r.geometry(self.cfg.get("geometry", "1080x720"))
        r.minsize(960, 640)
        try:
            r.iconbitmap(core.resource_path("app.ico"))
        except Exception:
            pass

        head = self._reg(tk.Frame(r, height=68), "frame")
        head.pack(fill="x")
        head.pack_propagate(False)
        left = self._reg(tk.Frame(head), "frame")
        left.pack(side="left", padx=20)
        self._reg(tk.Label(left, text="SHERLOCK", font=(FONT, 17, "bold")), "title").pack(anchor="w")
        self._reg(tk.Label(left, text="用户名检索工具 · 图形界面版", font=(FONT, 9)), "muted").pack(anchor="w")
        right = self._reg(tk.Frame(head), "frame")
        right.pack(side="right", padx=18)
        ttk.Button(right, text="浅色 / 深色", command=self.toggle_theme).pack(side="right", padx=4)
        ttk.Button(right, text="置顶", command=self.toggle_topmost).pack(side="right", padx=4)
        ttk.Button(right, text="官方仓库", command=lambda: webbrowser.open(REPO_URL)).pack(side="right", padx=4)

        nb = ttk.Notebook(r)
        nb.pack(fill="both", expand=True, padx=14, pady=(10, 4))
        self._build_query_tab(nb)
        self._build_result_tab(nb)
        self._build_log_tab(nb)
        self._build_settings_tab(nb)
        self._build_about_tab(nb)

        foot = ttk.Frame(r, padding=(16, 7))
        foot.pack(fill="x")
        ttk.Label(foot, textvariable=self.status_var, style="TLabel").pack(side="left")
        self.progress = ttk.Progressbar(foot, mode="determinate", length=240, maximum=1, value=0)
        self.progress.pack(side="right", padx=(10, 0))
        ttk.Label(foot, textvariable=self.count_var, style="TLabel").pack(side="right", padx=12)

    def _build_query_tab(self, nb):
        tab = ttk.Frame(nb, padding=18)
        nb.add(tab, text="  查询  ")
        card = ttk.Frame(tab, style="Card.TFrame", padding=22)
        card.pack(fill="x")
        card.columnconfigure(1, weight=1)

        ttk.Label(card, text="用户名", style="Card.TLabel", font=self._f(0, True)).grid(row=0, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(card, textvariable=self.user_var, font=self._f(2)).grid(row=0, column=1, columnspan=3, sticky="ew", pady=(0, 6))
        ttk.Label(card, text="多个用户名用空格或逗号分隔，例如：octocat  oschina",
                  style="Muted.TLabel").grid(row=1, column=1, columnspan=3, sticky="w", pady=(0, 14))

        ttk.Label(card, text="站点筛选", style="Card.TLabel", font=self._f(0, True)).grid(row=2, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(card, textvariable=self.site_var).grid(row=2, column=1, columnspan=3, sticky="ew", pady=(0, 6))
        ttk.Label(card, text=f"留空 = 全部 {core.site_count()} 个站点；指定多个用逗号分隔，例如：GitHub, Gitee",
                  style="Muted.TLabel").grid(row=3, column=1, columnspan=3, sticky="w", pady=(0, 16))

        ttk.Label(card, text="超时(秒)", style="Card.TLabel").grid(row=4, column=0, sticky="w")
        ttk.Spinbox(card, from_=3, to=120, textvariable=self.timeout_var, width=8).grid(row=4, column=1, sticky="w")
        ttk.Label(card, text="代理(可选)", style="Card.TLabel").grid(row=4, column=2, sticky="e", padx=(16, 8))
        ttk.Entry(card, textvariable=self.proxy_var, width=30).grid(row=4, column=3, sticky="ew")

        opts = ttk.Frame(card, style="Card.TFrame")
        opts.grid(row=5, column=0, columnspan=4, sticky="w", pady=(16, 4))
        ttk.Checkbutton(opts, text="包含 NSFW 站点", variable=self.nsfw_var).pack(side="left", padx=(0, 18))
        ttk.Checkbutton(opts, text="结果只显示命中", variable=self.only_found_var,
                        command=self.refresh_tree).pack(side="left")

        btns = ttk.Frame(tab, padding=(0, 18, 0, 0))
        btns.pack(fill="x")
        self.btn_start = ttk.Button(btns, text="开始查询", style="Accent.TButton", command=self.start_query)
        self.btn_start.pack(side="left")
        self.btn_stop = ttk.Button(btns, text="停止", command=self.stop_query, state="disabled")
        self.btn_stop.pack(side="left", padx=8)
        ttk.Button(btns, text="清空结果", command=self.clear_results).pack(side="left", padx=8)
        ttk.Button(btns, text="清空日志", command=self.clear_log).pack(side="left")

        note = ttk.Frame(tab, style="Card.TFrame", padding=16)
        note.pack(fill="x", pady=(18, 0))
        ttk.Label(note, text="使用提示", style="Card.TLabel", font=self._f(0, True)).pack(anchor="w")
        ttk.Label(note, style="Muted.TLabel", justify="left", wraplength=900,
                  text=("· 站点列表随程序内置（离线可用），不会向 GitHub 请求最新列表。\n"
                        "· 境外站点可能受网络环境影响；如遇大量超时，可在「代理」填入 http://127.0.0.1:端口 或 socks5://...\n"
                        "· 仅可用于检索公开账号信息，请遵守法律法规与平台条款。")).pack(anchor="w", pady=(6, 0))

    def _build_result_tab(self, nb):
        tab = ttk.Frame(nb, padding=14)
        nb.add(tab, text="  结果  ")
        bar = ttk.Frame(tab)
        bar.pack(fill="x", pady=(0, 10))
        ttk.Button(bar, text="导出 TXT", command=lambda: self.export("txt")).pack(side="left")
        ttk.Button(bar, text="导出 CSV", command=lambda: self.export("csv")).pack(side="left", padx=6)
        ttk.Button(bar, text="导出 Excel", command=lambda: self.export("xlsx")).pack(side="left")
        ttk.Button(bar, text="打开选中链接", command=self.open_selected).pack(side="left", padx=6)
        ttk.Checkbutton(bar, text="只看命中", variable=self.only_found_var,
                        command=self.refresh_tree).pack(side="left", padx=12)
        ttk.Button(bar, text="清空", command=self.clear_results).pack(side="right")

        frame = ttk.Frame(tab)
        frame.pack(fill="both", expand=True)
        cols = ("user", "site", "status", "url", "time")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse")
        for key, text, width in [("user", "用户名", 150), ("site", "站点", 190),
                                 ("status", "状态", 130), ("url", "URL", 460),
                                 ("time", "耗时(s)", 90)]:
            self.tree.heading(key, text=text)
            self.tree.column(key, width=width, anchor="w", stretch=(key == "url"))
        vs = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        hs = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        self.tree.bind("<Double-1>", lambda e: self.open_selected())

    def _build_log_tab(self, nb):
        tab = ttk.Frame(nb, padding=14)
        nb.add(tab, text="  日志  ")
        bar = ttk.Frame(tab)
        bar.pack(fill="x", pady=(0, 8))
        ttk.Button(bar, text="保存日志", command=self.save_log).pack(side="left")
        ttk.Button(bar, text="清空", command=self.clear_log).pack(side="left", padx=6)
        self.log_text = self._reg(scrolledtext.ScrolledText(tab, wrap="word",
                                  font=("Consolas", 10), state="disabled"), "log")
        self.log_text.pack(fill="both", expand=True)
        self.log_text.tag_config("info", foreground="#CBD5E1")
        self.log_text.tag_config("ok", foreground="#4ADE80")
        self.log_text.tag_config("error", foreground="#F87171")

    def _build_settings_tab(self, nb):
        tab = ttk.Frame(nb, padding=18)
        nb.add(tab, text="  设置  ")
        card = ttk.Frame(tab, style="Card.TFrame", padding=22)
        card.pack(fill="x")
        card.columnconfigure(1, weight=1)
        ttk.Label(card, text="外观", style="Card.TLabel", font=self._f(0, True)).grid(row=0, column=0, sticky="w", pady=8)
        box = ttk.Frame(card, style="Card.TFrame")
        box.grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(box, text="浅色", value="light", variable=self.theme_var).pack(side="left")
        ttk.Radiobutton(box, text="深色", value="dark", variable=self.theme_var).pack(side="left", padx=16)
        ttk.Label(card, text="字号", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=8)
        ttk.Spinbox(card, from_=8, to=16, textvariable=self.font_var, width=8).grid(row=1, column=1, sticky="w")
        ttk.Label(card, text="默认超时(秒)", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=8)
        ttk.Spinbox(card, from_=3, to=120, textvariable=self.timeout_var, width=8).grid(row=2, column=1, sticky="w")
        ttk.Label(card, text="默认代理", style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=8)
        ttk.Entry(card, textvariable=self.proxy_var, width=42).grid(row=3, column=1, sticky="w")
        ttk.Checkbutton(card, text="窗口置顶", variable=self.topmost_var).grid(row=4, column=1, sticky="w", pady=8)
        btns = ttk.Frame(tab, padding=(0, 16))
        btns.pack(fill="x")
        ttk.Button(btns, text="保存并应用", style="Accent.TButton",
                   command=self.apply_settings).pack(side="left")
        ttk.Button(btns, text="恢复默认", command=self.reset_settings).pack(side="left", padx=8)
        ttk.Label(tab, style="Muted.TLabel", justify="left",
                  text="配置保存在程序目录的 config.json；关闭窗口时自动记忆窗口大小。").pack(anchor="w", pady=(10, 0))

    def _build_about_tab(self, nb):
        tab = ttk.Frame(nb, padding=18)
        nb.add(tab, text="  关于  ")
        card = ttk.Frame(tab, style="Card.TFrame", padding=26)
        card.pack(fill="x")
        ttk.Label(card, text="Sherlock GUI", style="Card.TLabel",
                  font=(FONT, 20, "bold")).pack(anchor="w")
        ttk.Label(card, text="把命令行 OSINT 工具变成可视化桌面应用",
                  style="Muted.TLabel").pack(anchor="w", pady=(2, 16))
        for line in [
            f"程序版本：v{core.__version__}（上游 sherlock-project/sherlock）",
            f"内置站点：{core.site_count()} 个（data.json 随程序分发，离线可用）",
            f"官方仓库：{REPO_URL}",
            "许可证：MIT",
        ]:
            ttk.Label(card, text=line, style="Card.TLabel").pack(anchor="w", pady=3)
        ttk.Button(card, text="打开官方仓库", command=lambda: webbrowser.open(REPO_URL)).pack(anchor="w", pady=(16, 0))
        ttk.Label(tab, style="Muted.TLabel", justify="left", wraplength=900,
                  text=("\n文件说明：gui.py / gui.pyw 主程序 · sherlock_core.py 业务封装 · "
                        "sherlock_project/ 上游引擎与站点数据 · app.ico 图标 · "
                        "启动.bat / 静默启动.vbs / 安装依赖.bat / 打包成EXE.bat 脚本。\n\n"
                        "免责声明：本工具仅检索公开可访问的账号页面，请仅用于合法合规用途，"
                        "不得用于骚扰、人肉搜索或任何侵犯他人隐私的行为。")).pack(anchor="w", pady=(18, 0))

    # ---------- logging ----------
    def log(self, text: str, level: str = "info"):
        ts = datetime.now().strftime("%H:%M:%S")
        try:
            self.log_text.configure(state="normal")
            self.log_text.insert("end", f"[{ts}] {text}\n", level)
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
        except tk.TclError:
            pass

    def clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def save_log(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            initialfile=f"sherlock_log_{datetime.now():%Y%m%d_%H%M%S}.txt",
                                            filetypes=[("Text", "*.txt")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.log_text.get("1.0", "end"))
        self.log(f"日志已保存：{path}", "ok")

    # ---------- query ----------
    def _set_busy(self, busy: bool):
        self.busy = busy
        self.btn_start.configure(state="disabled" if busy else "normal")
        self.btn_stop.configure(state="normal" if busy else "disabled")

    def start_query(self):
        if self.busy:
            return
        raw = self.user_var.get().strip()
        usernames = [u for u in raw.replace(",", " ").split() if u]
        if not usernames:
            messagebox.showwarning("缺少用户名", "请先输入要查询的用户名。")
            return
        only = [s.strip() for s in self.site_var.get().split(",") if s.strip()]
        try:
            timeout = max(3, min(120, int(self.timeout_var.get())))
        except (ValueError, tk.TclError):
            timeout = 15
        proxy = self.proxy_var.get().strip() or None
        nsfw = bool(self.nsfw_var.get())
        self.stop_event = threading.Event()
        self._set_busy(True)
        self.progress.configure(value=0)
        self.status_var.set("正在查询…")
        self.log(f"任务开始：{len(usernames)} 个用户名，超时 {timeout}s" + (f"，代理 {proxy}" if proxy else ""))
        self.worker = threading.Thread(target=self._worker,
                                       args=(usernames, only, nsfw, timeout, proxy), daemon=True)
        self.worker.start()

    def stop_query(self):
        if not self.busy:
            return
        self.stop_event.set()
        self.status_var.set("正在停止…（当前批次结束后生效）")
        self.log("收到停止请求。")

    def _worker(self, usernames, only, nsfw, timeout, proxy):
        try:
            data = core.load_sites(include_nsfw=nsfw, only=only)
            if not data:
                self.q.put(("error", "没有匹配的站点，请检查「站点筛选」的名称。"))
                return
            self.q.put(("log", f"已加载 {len(data)} 个站点（内置数据，离线可用）"))
            core.run_query(
                usernames, data,
                on_progress=lambda d, t, u: self.q.put(("progress", d, t, u)),
                on_row=lambda row: self.q.put(("row", row)),
                on_log=lambda text: self.q.put(("log", text)),
                stop_event=self.stop_event, proxy=proxy, timeout=timeout,
            )
        except Exception as exc:
            self.q.put(("error", f"{type(exc).__name__}: {exc}"))
        finally:
            self.q.put(("done",))

    def _poll(self):
        new_rows = []
        try:
            while True:
                ev = self.q.get_nowait()
                kind = ev[0]
                if kind == "log":
                    self.log(ev[1])
                elif kind == "progress":
                    done, total, user = ev[1], ev[2], ev[3]
                    self.progress.configure(maximum=max(1, total), value=done)
                    self.status_var.set(f"查询中 {user} · {done}/{total}")
                elif kind == "row":
                    new_rows.append(ev[1])
                elif kind == "error":
                    self.log("错误：" + ev[1], "error")
                    messagebox.showerror("查询错误", ev[1])
                elif kind == "done":
                    self._on_done()
        except queue.Empty:
            pass
        if new_rows:
            self.rows.extend(new_rows)
            self._insert_rows(new_rows)
            self._update_counts()
        self.root.after(80, self._poll)

    def _on_done(self):
        self._set_busy(False)
        hits = sum(1 for r in self.rows if r["found"])
        self.status_var.set(f"完成 · 命中 {hits} 条")
        self.log(f"全部完成，累计命中 {hits} 条", "ok")

    # ---------- results ----------
    def _insert_rows(self, rows):
        for row in rows:
            if self.only_found_var.get() and not row["found"]:
                continue
            iid = self.tree.insert("", "end", values=(row["username"], row["site"],
                                                      row["status"], row["url"], row["time"]))
            tags = []
            if len(self.tree.get_children()) % 2 == 0:
                tags.append("odd")
            if row["found"]:
                tags.append("found")
            self.tree.item(iid, tags=tags)

    def refresh_tree(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self._insert_rows(self.rows)
        self._update_counts()

    def _update_counts(self):
        hits = sum(1 for r in self.rows if r["found"])
        self.count_var.set(f"命中 {hits} / 结果 {len(self.rows)}")

    def clear_results(self):
        if self.busy:
            messagebox.showinfo("请稍候", "查询进行中，停止后再清空。")
            return
        self.rows.clear()
        self.refresh_tree()
        self.progress.configure(value=0)
        self.status_var.set("就绪")
        self.log("结果已清空。")

    def open_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("未选择", "请先在结果表格中选中一行。")
            return
        url = self.tree.item(sel[0], "values")[3]
        if url:
            webbrowser.open(url)
            self.log(f"打开链接：{url}")
        else:
            messagebox.showinfo("无链接", "该行没有可打开的 URL。")

    def export(self, kind: str):
        if not self.rows:
            messagebox.showinfo("无结果", "当前没有可导出的结果。")
            return
        ext = {"txt": ".txt", "csv": ".csv", "xlsx": ".xlsx"}[kind]
        types = {"txt": [("Text", "*.txt")], "csv": [("CSV", "*.csv")],
                 "xlsx": [("Excel", "*.xlsx")]}[kind]
        path = filedialog.asksaveasfilename(
            defaultextension=ext,
            initialfile=f"sherlock_{datetime.now():%Y%m%d_%H%M%S}{ext}",
            filetypes=types)
        if not path:
            return
        try:
            {"txt": core.export_txt, "csv": core.export_csv,
             "xlsx": core.export_xlsx}[kind](self.rows, path)
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))
            self.log(f"导出失败：{exc}", "error")
        else:
            self.log(f"已导出 {len(self.rows)} 条结果：{path}", "ok")
            messagebox.showinfo("导出成功", f"已保存到：\n{path}")

    # ---------- settings ----------
    def toggle_theme(self):
        self.cfg["theme"] = "dark" if self.cfg["theme"] == "light" else "light"
        self.theme_var.set(self.cfg["theme"])
        self._apply_theme()
        self._save_config()
        self.log(f"已切换为{'深色' if self.cfg['theme'] == 'dark' else '浅色'}主题。")

    def toggle_topmost(self):
        self.topmost_var.set(not bool(self.topmost_var.get()))
        self.cfg["topmost"] = bool(self.topmost_var.get())
        self.root.attributes("-topmost", self.cfg["topmost"])
        self._save_config()

    def apply_settings(self):
        self.cfg["theme"] = self.theme_var.get()
        self.cfg["font_size"] = int(self.font_var.get())
        self.cfg["timeout"] = int(self.timeout_var.get())
        self.cfg["proxy"] = self.proxy_var.get().strip()
        self.cfg["topmost"] = bool(self.topmost_var.get())
        self.cfg["include_nsfw"] = bool(self.nsfw_var.get())
        self.cfg["show_all"] = not bool(self.only_found_var.get())
        self.root.attributes("-topmost", self.cfg["topmost"])
        self._apply_theme()
        self._save_config()
        self.log("设置已保存。", "ok")
        messagebox.showinfo("已保存", "设置已保存并生效。")

    def reset_settings(self):
        self.cfg.update(DEFAULTS)
        self.theme_var.set(self.cfg["theme"])
        self.font_var.set(self.cfg["font_size"])
        self.timeout_var.set(self.cfg["timeout"])
        self.proxy_var.set(self.cfg["proxy"])
        self.topmost_var.set(self.cfg["topmost"])
        self.nsfw_var.set(self.cfg["include_nsfw"])
        self.only_found_var.set(not self.cfg["show_all"])
        self.root.attributes("-topmost", False)
        self._apply_theme()
        self._save_config()
        self.log("已恢复默认设置。", "ok")

    def on_close(self):
        try:
            self.cfg["geometry"] = self.root.geometry()
        except tk.TclError:
            pass
        self._save_config()
        self.root.destroy()


def run_selftest() -> int:
    info = core.selftest()
    out = os.path.join(tempfile.gettempdir(), "sherlock_gui_selftest.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(info, fh, ensure_ascii=False, indent=2)
    return 0 if info["data_exists"] and info["sites"] > 0 and not info["error"] else 1


def main():
    if "--selftest" in sys.argv:
        return run_selftest()
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    root = tk.Tk()
    App(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
