"""Capture a running terminal-evidence.py session using real Windows screen pixels.

Windows only. Requires Pillow. Select exactly one existing terminal window by its
title; activate it, capture its visible bounds without edits, then advance SQL.
"""

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import time
from PIL import ImageGrab

ROOT = Path(__file__).resolve().parents[1]
IDS = [f'Q{i:02}' for i in range(1, 17)] + [f'B{i:02}' for i in range(1, 5)] + [f'M{i:02}' for i in range(1, 4)] + [f'E{i:02}' for i in range(1, 7)]


def publish_manifest(control):
    """Publish records only after all native executions and captures complete."""
    captures = json.loads((control / 'captures.json').read_text(encoding='utf-8'))
    completed = json.loads((control / 'completed.json').read_text(encoding='utf-8'))
    if [entry['id'] for entry in captures] != IDS:
        raise RuntimeError('All 29 captures are required')
    if [entry['execution'] for entry in captures] != completed['records']:
        raise RuntimeError('Execution and capture records differ')
    for entry in captures:
        if hashlib.sha256((ROOT / entry['screenshot']).read_bytes()).hexdigest() != entry['png_sha256']:
            raise RuntimeError('Screenshot hash mismatch: ' + entry['id'])
    manifest = {
        'method': 'Native sqlite3.exe inherits Windows Terminal stdout/stderr; Pillow ImageGrab captures visible terminal screen bounds. No HTML, log replay, or pixel editing.',
        'sqlite_version': completed['sqlite_version'],
        'text_results_environment': 'results/00_environment.txt (separate Python sqlite3 execution)',
        'final_core_counts': completed['final_counts'],
        'captures': captures,
    }
    destination = ROOT / 'results/screenshots'
    (destination / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    lines = ['# SQL 실제 터미널 실행 캡처', '',
             'Windows Terminal에서 sqlite3.exe가 SQL을 실행하고 직접 출력한 화면 29장이다.',
             '기존 HTML 문서 캡처는 모두 교체했다. [실행·캡처 방식](../../docs/screenshots.md)과',
             '[실행 기록 및 PNG 해시](manifest.json)를 함께 제공한다.', '',
             '텍스트 로그는 Python sqlite3로 별도 실행한 결과이며, 이미지는 독립 SQLite CLI 실행 화면이다.', '',
             '| 번호 | SQL 원본 | 별도 텍스트 결과 | 실제 터미널 PNG |', '|---|---|---|---|']
    for entry in captures:
        name = entry['id'].lower()
        source = entry['execution']['source']
        lines.append(f"| {entry['id']} | [{source}](../../{source}) | [{name}.txt](../{name}.txt) | [{name}.png]({name}.png) |")
    for entry in captures:
        name = entry['id'].lower()
        lines.extend(['', '## ' + entry['id'], '', f"![{entry['id']} 실제 SQLite 터미널 실행]({name}.png)"])
    (destination / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--title', default='B6-1 SQLite evidence')
    parser.add_argument('--count', type=int, default=29)
    parser.add_argument('--control', type=Path, default=ROOT / 'output/terminal-control')
    args = parser.parse_args()
    user32 = ctypes.windll.user32
    user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    matches = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @callback_type
    def enumerate_windows(handle, _):
        title = ctypes.create_unicode_buffer(1024)
        user32.GetWindowTextW(handle, title, len(title))
        if title.value == args.title and user32.IsWindowVisible(handle):
            matches.append(handle)
        return True

    user32.EnumWindows(enumerate_windows, 0)
    if len(matches) != 1:
        raise RuntimeError(f'Expected one terminal named {args.title!r}, found {len(matches)}')
    handle = matches[0]
    user32.ShowWindow(handle, 3)
    destination = ROOT / 'results/screenshots'
    destination.mkdir(exist_ok=True)
    journal = args.control / 'captures.json'
    captures = json.loads(journal.read_text(encoding='utf-8')) if journal.exists() else []
    for _ in range(args.count):
        position = len(captures)
        if position >= len(IDS):
            break
        expected = IDS[position]
        deadline = time.monotonic() + 30
        while True:
            ready = json.loads((args.control / 'ready.json').read_text(encoding='utf-8'))
            if ready['id'] == expected:
                break
            if time.monotonic() > deadline:
                raise RuntimeError(f'Waiting for {expected}; session is on {ready["id"]}')
            time.sleep(0.15)
        user32.SetForegroundWindow(handle)
        time.sleep(0.5)  # Let the actual terminal paint its completed CLI output.
        if user32.GetForegroundWindow() != handle:
            raise RuntimeError('Terminal is not foreground; no screenshot was saved')
        bounds = wintypes.RECT()
        user32.GetWindowRect(handle, ctypes.byref(bounds))
        class MonitorInfo(ctypes.Structure):
            _fields_ = [('cbSize', wintypes.DWORD), ('monitor', wintypes.RECT),
                        ('work', wintypes.RECT), ('flags', wintypes.DWORD)]
        user32.MonitorFromWindow.restype = wintypes.HANDLE
        monitor = user32.MonitorFromWindow(handle, 2)
        info = MonitorInfo(); info.cbSize = ctypes.sizeof(info)
        user32.GetMonitorInfoW(monitor, ctypes.byref(info))
        region = (max(bounds.left, info.work.left), max(bounds.top, info.work.top),
                  min(bounds.right, info.work.right), min(bounds.bottom, info.work.bottom))
        if region[2] <= region[0] or region[3] <= region[1]:
            raise RuntimeError('Invalid terminal screen bounds')
        screenshot = ImageGrab.grab(bbox=region, all_screens=True)
        if user32.GetForegroundWindow() != handle:
            raise RuntimeError('Foreground changed during capture; no screenshot was saved')
        if all(low == high for low, high in screenshot.getextrema()):
            raise RuntimeError('Blank screenshot; no screenshot was saved')
        image_path = destination / (expected.lower() + '.png')
        screenshot.save(image_path)
        captures.append({'id': expected, 'screenshot': image_path.relative_to(ROOT).as_posix(),
                         'png_sha256': hashlib.sha256(image_path.read_bytes()).hexdigest(),
                         'width': screenshot.width, 'height': screenshot.height,
                         'captured_at_local': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                         'sqlite_version': ready['sqlite_version'],
                         'execution': ready['records'][-1]})
        journal.write_text(json.dumps(captures, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        (args.control / (expected.lower() + '.next')).touch()
        print(f'Captured {expected}: {screenshot.width}x{screenshot.height}', flush=True)
    if len(captures) == len(IDS):
        deadline = time.monotonic() + 30
        while not (args.control / 'completed.json').exists():
            if time.monotonic() > deadline:
                raise RuntimeError('Native execution did not complete; manifest not published')
            time.sleep(0.15)
        publish_manifest(args.control)


if __name__ == '__main__':
    main()
