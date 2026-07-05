"""Fixed-width text -> SVG vector paths using Cascadia Code (no font dependency at render time)."""
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen


class Mono:
    def __init__(self, path):
        self.f = TTFont(path)
        self.gs = self.f.getGlyphSet()
        self.cmap = self.f.getBestCmap()
        self.upm = self.f["head"].unitsPerEm
        self.hmtx = self.f["hmtx"]
        self.adv = self.hmtx[self.cmap[ord("M")]][0]

    def cw(self, size):
        """advance width of one monospace cell at the given px size"""
        return self.adv * size / self.upm

    def line(self, text, size, x, y):
        """render a string on baseline y starting at x; returns concatenated <path> svg"""
        scale = size / self.upm
        cx = x
        out = []
        for ch in text:
            gn = self.cmap.get(ord(ch))
            if gn:
                pen = SVGPathPen(self.gs)
                self.gs[gn].draw(pen)
                d = pen.getCommands()
                if d:
                    out.append(
                        f'<path transform="translate({cx:.2f},{y:.2f}) '
                        f'scale({scale:.5f},{-scale:.5f})" d="{d}"/>'
                    )
            cx += self.adv * scale
        return "".join(out)
