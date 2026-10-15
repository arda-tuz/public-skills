#!/usr/bin/env python3
"""Export every diagram of a page to standalone .svg and/or .png files.

    python3 export.py page.html                 # svg + png (scale 2) next to the page
    python3 export.py page.html --format svg    # svg only
    python3 export.py page.html --scale 3 --out figures/

Each <svg> becomes <slug>.svg / <slug>.png, where slug is the id prefix of its <title>
(e.g. decorator-class). PNGs are rendered by headless Chrome at the viewBox size times --scale,
with the page's web fonts (Geist, Geist Mono). The SVG files name the same fonts and fall back to
installed faces (Arial / Liberation Sans, a monospace) where Geist is not installed.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def chrome():
    for n in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        if shutil.which(n):
            return shutil.which(n)
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("page", type=Path)
    ap.add_argument("--format", choices=("svg", "png", "both"), default="both")
    ap.add_argument("--scale", type=float, default=2.0)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)
    out = a.out or a.page.parent
    out.mkdir(parents=True, exist_ok=True)
    html = a.page.read_text(encoding="utf-8")
    fonts = "".join(re.findall(r'<link [^>]*fonts\.googleapis\.com[^>]*>', html))
    svgs = re.findall(r"<svg\b.*?</svg>", html, re.DOTALL)
    if not svgs:
        print("no <svg> in page", file=sys.stderr)
        return 1
    exe = chrome() if a.format in ("png", "both") else None
    if a.format in ("png", "both") and not exe:
        print("png export needs google-chrome or chromium on PATH", file=sys.stderr)
        return 1
    for s in svgs:
        m = re.search(r'<title id="([^"]+)-title"', s)
        slug = m.group(1) if m else f"diagram-{svgs.index(s) + 1}"
        vb = re.search(r'viewBox="0 0 (\d+(?:\.\d+)?) (\d+(?:\.\d+)?)"', s)
        w, h = float(vb.group(1)), float(vb.group(2))
        standalone = re.sub(r'\sstyle="[^"]*"', "", s, count=1)
        standalone = standalone.replace("<svg ", f'<svg width="{w:g}" height="{h:g}" ', 1)
        if a.format in ("svg", "both"):
            p = out / f"{slug}.svg"
            p.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + standalone + "\n", encoding="utf-8")
            print(f"wrote {p}")
        if a.format in ("png", "both"):
            with tempfile.TemporaryDirectory() as td:
                wrap = Path(td) / "w.html"
                wrap.write_text('<!DOCTYPE html><html><head><meta charset="UTF-8">' + fonts + '<style>html,body{'
                                'margin:0;background:#f5f5f5}svg{display:block}</style></head><body>' + standalone +
                                "</body></html>", encoding="utf-8")
                p = (out / f"{slug}.png").resolve()
                subprocess.run([exe, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
                                f"--force-device-scale-factor={a.scale:g}",
                                f"--window-size={int(w)},{int(h)}", "--virtual-time-budget=3000",
                                f"--screenshot={p}", wrap.as_uri()], capture_output=True, timeout=120)
                print(f"wrote {p}" if p.exists() else f"FAILED {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
