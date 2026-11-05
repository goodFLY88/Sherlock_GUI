# -*- coding: utf-8 -*-
"""Sherlock GUI business layer.

Loads the bundled 482-site data.json, runs queries through the upstream
sherlock_project engine and exposes export helpers. No remote site-list
requests are made, so the GUI works offline.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from typing import Callable, Iterable

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def app_dir() -> str:
    """Directory that holds config.json (exe folder when frozen)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return BASE_DIR


def resource_path(relative: str) -> str:
    """Resolve a bundled resource both from source and from a PyInstaller onefile exe."""
    base = getattr(sys, "_MEIPASS", BASE_DIR)
    return os.path.join(base, relative)


DATA_FILE = resource_path(os.path.join("sherlock_project", "resources", "data.json"))

from sherlock_project import __version__              # noqa: E402
from sherlock_project.notify import QueryNotify        # noqa: E402
from sherlock_project.result import QueryStatus        # noqa: E402
from sherlock_project.sherlock import sherlock         # noqa: E402
from sherlock_project.sites import SitesInformation    # noqa: E402

STATUS_LABEL = {
    QueryStatus.CLAIMED: "已找到",
    QueryStatus.AVAILABLE: "未找到",
    QueryStatus.UNKNOWN: "未知 / 错误",
    QueryStatus.ILLEGAL: "用户名格式不符",
    QueryStatus.WAF: "被反爬拦截",
}

CSV_HEADER = ["用户名", "站点", "状态", "URL", "耗时(s)", "备注"]


def site_count() -> int:
    with open(DATA_FILE, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    data.pop("$schema", None)
    return len(data)


def load_sites(include_nsfw: bool = False, only: Iterable[str] | None = None) -> dict:
    """Build the site_data dict consumed by sherlock()."""
    names = [n.strip() for n in (only or []) if n.strip()]
    sites = SitesInformation(data_file_path=DATA_FILE, honor_exclusions=False)
    if not include_nsfw:
        sites.remove_nsfw_sites(do_not_remove=names)
    data = {s.name: s.information for s in sites}
    if names:
        wanted = {n.lower() for n in names}
        data = {k: v for k, v in data.items() if k.lower() in wanted}
    return data


class GuiNotify(QueryNotify):
    """Bridge upstream query callbacks to the GUI event queue."""

    def __init__(self, on_result=None, on_start=None, on_finish=None):
        super().__init__()
        self._on_result = on_result
        self._on_start = on_start
        self._on_finish = on_finish

    def start(self, message=None):
        if self._on_start:
            self._on_start(message)

    def update(self, result):
        super().update(result)
        if self._on_result:
            self._on_result(result)

    def finish(self, message=None):
        if self._on_finish:
            self._on_finish(message)


def result_to_row(username: str, result) -> dict:
    status = getattr(result, "status", QueryStatus.UNKNOWN)
    query_time = getattr(result, "query_time", None)
    return {
        "username": username,
        "site": getattr(result, "site_name", "") or "",
        "status": STATUS_LABEL.get(status, str(status)),
        "found": status == QueryStatus.CLAIMED,
        "url": getattr(result, "site_url_user", "") or "",
        "time": round(query_time, 3) if query_time is not None else "",
        "context": getattr(result, "context", "") or "",
    }


def run_query(usernames, site_data, *, on_progress: Callable, on_row: Callable,
              on_log: Callable, stop_event, proxy: str | None = None,
              timeout: int = 15) -> None:
    """Run one or more usernames against site_data in the calling (worker) thread."""
    total = max(1, len(site_data))
    for user in usernames:
        if stop_event.is_set():
            on_log("已停止，跳过剩余用户名。")
            break
        counter = {"n": 0}

        def _update(res, u=user, c=counter, t=total):
            c["n"] += 1
            on_progress(c["n"], t, u)
            on_row(result_to_row(u, res))

        notify = GuiNotify(
            _update,
            on_start=lambda msg, u=user: on_log(f"开始查询 {u}，共 {total} 个站点"),
            on_finish=lambda msg, u=user: on_log(f"{u} 查询完成"),
        )
        try:
            sherlock(user, site_data, notify, proxy=proxy or None, timeout=timeout)
        except Exception as exc:
            on_log(f"[{user}] 查询异常：{type(exc).__name__}: {exc}")


def _row_values(row: dict) -> list:
    return [row["username"], row["site"], row["status"], row["url"],
            row["time"], row["context"]]


def export_txt(rows: list, path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# Sherlock GUI 查询结果\n")
        for row in rows:
            if row["found"]:
                fh.write(f"{row['username']}\t{row['site']}\t{row['url']}\n")
        fh.write(f"\n命中数：{sum(1 for r in rows if r['found'])}\n")


def export_csv(rows: list, path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(CSV_HEADER)
        for row in rows:
            writer.writerow(_row_values(row))


def export_xlsx(rows: list, path: str) -> None:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "Sherlock 结果"
    ws.append(CSV_HEADER)
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1D4ED8")
        cell.alignment = Alignment(horizontal="center")
    for row in rows:
        ws.append(_row_values(row))
        if row["found"]:
            ws.cell(row=ws.max_row, column=3).font = Font(bold=True, color="1D4ED8")
    for idx, width in enumerate([18, 24, 18, 58, 12, 30], start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width
    ws.freeze_panes = "A2"
    wb.save(path)


def selftest() -> dict:
    """Headless check used to validate the packaged exe."""
    info = {
        "version": __version__,
        "frozen": bool(getattr(sys, "frozen", False)),
        "data_file": DATA_FILE,
        "data_exists": os.path.isfile(DATA_FILE),
        "sites": 0,
        "query_ok": False,
        "found": [],
        "error": None,
    }
    try:
        data = load_sites(include_nsfw=False)
        info["sites"] = len(data)
        subset = {k: v for k, v in data.items() if k.lower() == "gitee"}
        if not subset:
            subset = dict(list(data.items())[:1])
        rows = []
        notify = GuiNotify(lambda res: rows.append(result_to_row("oschina", res)))
        sherlock("oschina", subset, notify, timeout=12)
        info["query_ok"] = True
        info["found"] = [r["url"] for r in rows if r["found"]]
    except Exception as exc:
        info["error"] = f"{type(exc).__name__}: {exc}"
    return info
