#!/usr/bin/env python3
"""
Generates the Swiss-typographic hero for github.com/wpggLabs.

Renders a light-weight wordmark + manifesto to vector paths (Space Grotesk
Light), so it needs no font at display time and stays crisp everywhere.
Emits two theme variants over a transparent background:

    assets/hero-dark.svg   (light ink, for dark mode)
    assets/hero-light.svg  (dark ink,  for light mode)

Static by design: edit the copy below and re-run.

    python scripts/build.py
"""
import os
from typer import Typer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, "assets", "fonts", "SpaceGrotesk-Light.ttf")
T = Typer(FONT)
W, H = 1200, 440

WORDMARK = "wpggLabs"
LINE1 = "i build tools for an audience of one."
LINE2 = "local-first  ·  no accounts  ·  no telemetry"


def _centered(text, size, y, tracking):
    w = T.width(text, size, tracking)
    d, _ = T.path(text, size, (W - w) / 2, y, tracking)
    return d


def hero(fg, dim, faint):
    word = _centered(WORDMARK, 110, 210, 4)
    rulew = 64
    rule = (f'<line x1="{(W-rulew)/2}" y1="252" x2="{(W+rulew)/2}" y2="252" '
            f'stroke="{faint}" stroke-width="1.5"/>')
    l1 = _centered(LINE1, 27, 312, 0.5)
    l2 = _centered(LINE2, 19, 352, 1.5)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
            f'width="100%" role="img" aria-label="wpggLabs — {LINE1}">\n'
            f'<g fill="{fg}">{word}</g>\n{rule}\n'
            f'<g fill="{dim}">{l1}</g>\n<g fill="{faint}">{l2}</g>\n</svg>')


def main():
    variants = {
        "hero-dark.svg":  ("#f2f2f2", "#b8b8b8", "#6f6f6f"),
        "hero-light.svg": ("#141414", "#3f3f3f", "#8a8a8a"),
    }
    for name, cols in variants.items():
        open(os.path.join(ROOT, "assets", name), "w", encoding="utf-8").write(hero(*cols))
        print(f"· wrote assets/{name}")


if __name__ == "__main__":
    main()
