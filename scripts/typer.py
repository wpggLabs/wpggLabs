from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

class Typer:
    def __init__(self, path):
        self.f=TTFont(path)
        self.gs=self.f.getGlyphSet()
        self.cmap=self.f.getBestCmap()
        self.upm=self.f["head"].unitsPerEm
        self.hmtx=self.f["hmtx"]
        self.cmap_rev=self.cmap
    def width(self, text, size, tracking=0):
        scale=size/self.upm
        w=0
        for ch in text:
            gn=self.cmap.get(ord(ch))
            if gn is None: continue
            adv=self.hmtx[gn][0]
            w+=adv*scale+tracking
        return w
    def path(self, text, size, x, y, tracking=0):
        # y is baseline
        scale=size/self.upm
        pen_paths=[]
        cx=x
        for ch in text:
            gn=self.cmap.get(ord(ch))
            if gn is None:
                cx+=size*0.3+tracking; continue
            pen=SVGPathPen(self.gs)
            self.gs[gn].draw(pen)
            d=pen.getCommands()
            adv=self.hmtx[gn][0]
            if d:
                # transform: flip y (font y-up to svg y-down), scale, translate
                pen_paths.append(f'<path transform="translate({cx:.2f},{y:.2f}) scale({scale:.5f},{-scale:.5f})" d="{d}"/>')
            cx+=adv*scale+tracking
        return "".join(pen_paths), cx-x
