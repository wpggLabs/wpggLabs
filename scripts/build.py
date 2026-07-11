#!/usr/bin/env python3
"""
Generates assets/banner.svg for github.com/wpggLabs — a PowerShell-terminal
wordmark with the copy set in Cascadia Code and rendered to vector paths
(so it needs no font at display time and looks identical everywhere).

Static by design: edit the `lines` below and re-run.

    python scripts/build.py
"""
import os
from mono import Mono

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_BOLD = os.path.join(ROOT, "assets", "fonts", "CascadiaCode-Bold.ttf")

# ── terminal palette (black & white, one whisper of green for the prompt) ──
BG = "#0c0c0c"        # Windows Terminal default black
FG = "#f2f2f2"        # bright white text
DIM = "#8a8a8a"       # secondary grey
FAINT = "#3a3a3a"     # chrome lines
PROMPT = "#19c37d"    # terminal-green prompt glyph
CURSOR = "#f2f2f2"


def banner():
    M = Mono(FONT_BOLD)
    W = 1200
    fs = 26
    cw = M.cw(fs)
    x = 40
    top = 108
    lh = 46
    rows = []

    def put(cells, y):
        col = 0
        for text, color in cells:
            rows.append(f'<g fill="{color}">{M.line(text, fs, x + col * cw, y)}</g>')
            col += len(text)

    lines = [
        [("PS", PROMPT), (" C:\\wpggLabs> ", DIM), ("whoami", FG)],
        [("a guy in New York who codes instead of sleeping. no one asked.", DIM)],
        [("", FG)],
        [("PS", PROMPT), (" C:\\wpggLabs> ", DIM), ("Get-Job", FG)],
        [("lol no. this is a hobby. touching grass is the side project.", DIM)],
        [("", FG)],
        [("PS", PROMPT), (" C:\\wpggLabs> ", DIM), ("Get-Diagnosis", FG)],
        [("ADHD: opened 14 repos, shipped 3 · OCD: rebuilt those 3 twice", DIM)],
        [("", FG)],
        [("PS", PROMPT), (" C:\\wpggLabs> ", DIM), ("Get-Manifesto", FG)],
        [("i build tools for one user (me) and let you watch. you're welcome.", DIM)],
        [("", FG)],
        [("PS", PROMPT), (" C:\\wpggLabs> ", DIM)],
    ]
    for i, cells in enumerate(lines):
        put(cells, top + i * lh)
    H = top + len(lines) * lh + 28

    cur_x = x + len("PS C:\\wpggLabs> ") * cw
    cur_y = top + (len(lines) - 1) * lh
    cursor = (f'<rect x="{cur_x:.1f}" y="{cur_y - fs + 4:.1f}" width="{cw*0.9:.1f}" height="{fs:.1f}" '
              f'fill="{CURSOR}"><animate attributeName="opacity" values="1;1;0;0" dur="1.06s" '
              f'repeatCount="indefinite"/></rect>')

    title = M.line("Windows PowerShell", 20, 118, 48)
    dots = "".join(f'<circle cx="{40+i*26}" cy="41" r="7" fill="{c}"/>'
                   for i, c in enumerate(["#ff5f57", "#febc2e", "#28c840"]))
    ctrls = M.line("—  ▢  ✕", 20, W - 150, 48)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="wpggLabs — PowerShell">
<defs><clipPath id="w"><rect width="{W}" height="{H}" rx="12"/></clipPath></defs>
<g clip-path="url(#w)">
  <rect width="{W}" height="{H}" fill="{BG}"/>
  <rect width="{W}" height="72" fill="#161616"/>
  <line x1="0" y1="72" x2="{W}" y2="72" stroke="{FAINT}" stroke-width="1"/>
  {dots}
  <g fill="{DIM}">{title}</g>
  <g fill="{DIM}">{ctrls}</g>
  {''.join(rows)}
  {cursor}
  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FAINT}" stroke-width="1"/>
</g>
</svg>'''


def main():
    out = os.path.join(ROOT, "assets", "banner.svg")
    open(out, "w", encoding="utf-8").write(banner())
    print("· wrote assets/banner.svg")


if __name__ == "__main__":
    main()
