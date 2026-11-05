"""Verify the packaged onefile exe: headless selftest + real GUI window startup."""
import ctypes
import json
import os
import subprocess
import sys
import tempfile
import time
from ctypes import wintypes

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(BASE, "dist", "Sherlock_GUI.exe")
OUT = os.path.join(tempfile.gettempdir(), "sherlock_gui_selftest.json")


def selftest():
    if os.path.exists(OUT):
        os.remove(OUT)
    result = subprocess.run([EXE, "--selftest"], timeout=180)
    info = {}
    if os.path.exists(OUT):
        with open(OUT, "r", encoding="utf-8") as fh:
            info = json.load(fh)
    return result.returncode, info


def enum_titles():
    titles = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def collect(hwnd, _lparam):
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        if length:
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            if buf.value:
                titles.append(buf.value)
        return True

    ctypes.windll.user32.EnumWindows(callback_type(collect), 0)
    return titles


def window_test():
    proc = subprocess.Popen([EXE])
    matched = []
    for _ in range(20):
        time.sleep(1)
        matched = [t for t in enum_titles() if "Sherlock" in t]
        if matched:
            break
    alive = proc.poll() is None
    if alive:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
    return alive, matched[:3]


if __name__ == "__main__":
    if not os.path.isfile(EXE):
        print("MISSING EXE:", EXE)
        sys.exit(1)
    print("exe:", EXE)
    print("size(MB):", round(os.path.getsize(EXE) / 1048576, 1))
    rc, info = selftest()
    print("selftest_exit:", rc)
    print("selftest_info:", json.dumps(info, ensure_ascii=False))
    alive, matched = window_test()
    print("gui_alive_after_6s:", alive)
    print("gui_window_titles:", matched)
    ok = (rc == 0 and info.get("frozen") and info.get("data_exists")
          and info.get("sites", 0) > 0 and info.get("query_ok")
          and not info.get("error") and alive and matched)
    print("RESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
