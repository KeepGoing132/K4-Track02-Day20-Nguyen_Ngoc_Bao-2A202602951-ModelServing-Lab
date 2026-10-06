#!/usr/bin/env python3
"""Build a browser viewer of actual logs for taking REAL screenshots.

This script does not create PNGs or imitate a terminal. Open the resulting HTML
and use your screenshot tool. All displayed output comes from run-lab.py logs.
"""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "benchmarks" / "evidence"


def read(name):
    return (EVIDENCE / name).read_text(encoding="utf-8")


def main():
    probe = read("probe.txt")
    bench = read("bench.txt")
    bench = "\n".join(bench.splitlines()[:3]) + "\n\n" + bench[bench.index("# 01 - Measure:"):]
    server = read("server.txt")
    server_summary = "\n".join(line for line in server.splitlines()
                               if any(key in line.lower() for key in
                                      ("started utc:", "command:", "environment:",
                                       "listening", "model loaded")))
    panels = [
        ("01-hardware-probe", "Hardware probe", probe, ["probe.txt"]),
        ("02-bench", "Benchmark: both quantizations", bench, ["bench.txt"]),
        ("03-serve-and-smoke", "Server + smoke + non-zero metrics",
         server_summary + "\n\n" + read("smoke.txt"), ["server.txt", "smoke.txt"]),
    ]
    for users, number in ((10, 4), (50, 5)):
        raw = read(f"locust-{users}.txt")
        marker = raw.rfind("Type     Name")
        prior = raw.rfind("Type     Name", 0, marker)
        summary = raw[prior:] if prior >= 0 else raw
        panels.append((f"0{number}-locust-{users}", f"Locust: {users} users / 60 seconds",
                       "\n".join(raw.splitlines()[:3]) + "\n\n" + summary,
                       [f"locust-{users}.txt"]))
    html = ['<!doctype html><html lang="vi"><meta charset="utf-8">',
            '<title>Day 20 — actual command output</title>',
            '<style>body{margin:24px;background:#f4f5f7;color:#17212b;font-family:Arial,sans-serif}'
            'nav a{margin-right:18px}section{background:white;border:1px solid #ccd2d9;'
            'padding:18px;margin:24px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;'
            'font:13px/1.5 Consolas,monospace}h2{font-size:20px}small{color:#53606c}'
            '@media print{section{break-before:page}nav{display:none}}</style>',
            '<h1>Day 20: đầu ra thực tế</h1>',
            '<p>Trang xem log gốc, không phải ảnh terminal. Chụp từng phần bằng công cụ '
            'chụp màn hình và lưu vào <code>submission/screenshots/</code>.</p>',
            '<nav>' + ''.join(f'<a href="#{key}">{i}</a>' for i, (key, *_) in enumerate(panels, 1)) + '</nav>']
    for key, title, content, logs in panels:
        links = ' · '.join(f'<a href="../benchmarks/evidence/{name}">{name}</a>' for name in logs)
        html.append(f'<section id="{key}"><h2>{escape(title)}</h2>'
                    f'<small>Source: {links}. Screenshot filename: {key}.png</small>'
                    f'<pre>{escape(content)}</pre></section>')
    html.append('</html>')
    out = ROOT / "submission" / "evidence.html"
    out.write_text('\n'.join(html), encoding="utf-8")
    print(f"Open {out} and capture the five sections. No screenshots were fabricated.")


if __name__ == "__main__":
    main()
