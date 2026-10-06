"""Generate A4 printable papercraft nets for the blue desktop-computer model.

Run:  python3 make_papercraft.py
Output: pdf/*.pdf  (one file per part + ALL_PARTS.pdf)
All sizes are real centimetres when printed at 100 % ("Actual size").
"""
import math
import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf")

# ---------------------------------------------------------------- colours
BLUE = HexColor("#1f3cc4")
BLUE_D = HexColor("#16289a")
BLUE_L = HexColor("#3a5ae0")
YELLOW = HexColor("#ffd60a")
BLACK = HexColor("#111111")
DGRAY = HexColor("#2b2b2b")
MGRAY = HexColor("#8a8f96")
LGRAY = HexColor("#c9cdd2")
SILVER = HexColor("#dfe2e6")
TAB = HexColor("#d8d8d8")
KEY = HexColor("#f1effd")
CREAM = HexColor("#f2e7c4")

# ---------------------------------------------------------------- dimensions (cm)
TOWER = dict(W=6.0, D=10.5, H=13.0)
SPK = dict(W=4.0, D=5.0, H=7.5)
MON = dict(W=16.0, H=10.0, T=0.8)
NECK = dict(W=2.5, D=0.8, H=6.5)
FOOT = dict(W=7.5, D=4.5, T=0.4)
KB = dict(W=14.0, D=5.0, T=0.7)
MOUSE = dict(W=3.2, D=5.8, T=0.9)
BASE = dict(W=38.0, D=27.0)


# ================================================================ net engine
class Net:
    """Faces are rectangles (cm, net-local). Edges shared by two faces or by a
    face and a tab become fold lines; every other edge is a cut line."""

    def __init__(self):
        self.faces = []  # (x, y, w, h, fill, deco)
        self.tabs = []   # (face_index, side, depth)

    def face(self, x, y, w, h, fill, deco=None):
        self.faces.append((x, y, w, h, fill, deco))
        return len(self.faces) - 1

    def tab(self, fi, side, depth=0.8):
        self.tabs.append((fi, side, depth))

    # -- helpers
    @staticmethod
    def _edges(x, y, w, h):
        return {
            "B": ((x, y), (x + w, y)),
            "T": ((x, y + h), (x + w, y + h)),
            "L": ((x, y), (x, y + h)),
            "R": ((x + w, y), (x + w, y + h)),
        }

    @staticmethod
    def _key(seg):
        a, b = seg
        a = (round(a[0], 4), round(a[1], 4))
        b = (round(b[0], 4), round(b[1], 4))
        return tuple(sorted([a, b]))

    def _tab_poly(self, fi, side, d):
        x, y, w, h = self.faces[fi][:4]
        (ax, ay), (bx, by) = self._edges(x, y, w, h)[side]
        length = math.hypot(bx - ax, by - ay)
        ins = min(d * 0.9, length * 0.3)
        # outward normal
        nx, ny = {"B": (0, -1), "T": (0, 1), "L": (-1, 0), "R": (1, 0)}[side]
        ux, uy = (bx - ax) / length, (by - ay) / length
        return [
            (ax, ay),
            (ax + ux * ins + nx * d, ay + uy * ins + ny * d),
            (bx - ux * ins + nx * d, by - uy * ins + ny * d),
            (bx, by),
        ]

    def bbox(self):
        xs, ys = [], []
        for f in self.faces:
            x, y, w, h = f[:4]
            xs += [x, x + w]
            ys += [y, y + h]
        for fi, s, d in self.tabs:
            for px, py in self._tab_poly(fi, s, d):
                xs.append(px)
                ys.append(py)
        return min(xs), min(ys), max(xs), max(ys)

    def draw(self, c, ox, oy):
        """Draw with bbox lower-left at (ox, oy) cm."""
        bx0, by0, _, _ = self.bbox()
        dx, dy = ox - bx0, oy - by0
        P = lambda px, py: ((px + dx) * cm, (py + dy) * cm)

        # count edges
        count = {}
        for f in self.faces:
            for seg in self._edges(*f[:4]).values():
                k = self._key(seg)
                count[k] = count.get(k, 0) + 1
        tab_edges = set()
        for fi, s, d in self.tabs:
            tab_edges.add(self._key(self._edges(*self.faces[fi][:4])[s]))

        # tabs
        for fi, s, d in self.tabs:
            pts = [P(*p) for p in self._tab_poly(fi, s, d)]
            path = c.beginPath()
            path.moveTo(*pts[0])
            for p in pts[1:]:
                path.lineTo(*p)
            c.setFillColor(TAB)
            c.setStrokeColor(black)
            c.setLineWidth(0.6)
            c.setDash()
            c.drawPath(path, fill=1, stroke=0)
            # cut lines (3 outer sides)
            p = c.beginPath()
            p.moveTo(*pts[0])
            for q in pts[1:]:
                p.lineTo(*q)
            c.drawPath(p, fill=0, stroke=1)
            mx = sum(q[0] for q in pts) / 4
            my = sum(q[1] for q in pts) / 4
            c.setFillColor(MGRAY)
            c.setFont("Helvetica", 4.5)
            c.drawCentredString(mx, my - 1.5, "glue")

        # faces: fills + artwork
        for x, y, w, h, fill, deco in self.faces:
            X, Y = P(x, y)
            c.setFillColor(fill)
            c.rect(X, Y, w * cm, h * cm, fill=1, stroke=0)
            if deco:
                c.saveState()
                p = c.beginPath()
                p.rect(X, Y, w * cm, h * cm)
                c.clipPath(p, stroke=0, fill=0)
                deco(c, X, Y, w * cm, h * cm)
                c.restoreState()

        # edges
        drawn = set()
        for f in self.faces:
            for seg in self._edges(*f[:4]).values():
                k = self._key(seg)
                if k in drawn:
                    continue
                drawn.add(k)
                fold = count[k] > 1 or k in tab_edges
                (ax, ay), (bx, by) = seg
                c.setStrokeColor(HexColor("#555555") if fold else black)
                c.setLineWidth(0.5 if fold else 0.8)
                c.setDash(3, 2) if fold else c.setDash()
                c.line(*P(ax, ay), *P(bx, by))
        c.setDash()


def box_strip(W, D, H, front, right, back, left, top, bottom,
              fills=None, top_on=0, bottom_on=0):
    """Classic 4-wall strip net: Front|Right|Back|Left + glue tab,
    top and bottom hinged to the face index given."""
    fills = fills or {}
    n = Net()
    widths = [W, D, W, D]
    decos = [front, right, back, left]
    names = ["front", "right", "back", "left"]
    x = 0
    idx = []
    for wd, deco, nm in zip(widths, decos, names):
        idx.append(n.face(x, 0, wd, H, fills.get(nm, BLUE), deco))
        x += wd
    n.tab(idx[3], "R")
    tx = sum(widths[:top_on])
    t = n.face(tx, H, widths[top_on], D, fills.get("top", BLUE), top)
    n.tab(t, "L"), n.tab(t, "R"), n.tab(t, "T")
    if bottom is not False:
        bx = sum(widths[:bottom_on])
        b = n.face(bx, -D, widths[bottom_on], D, fills.get("bottom", BLUE), bottom)
        n.tab(b, "L"), n.tab(b, "R"), n.tab(b, "B")
    return n


def tray(W, D, T, top, wall_fill, top_fill, wall_deco=None):
    """Lid-shaped net (top + 4 walls, open bottom) for flat parts."""
    n = Net()
    t = n.face(0, 0, W, D, top_fill, top)
    s = n.face(0, -T, W, T, wall_fill, wall_deco)        # front wall
    nn = n.face(0, D, W, T, wall_fill, wall_deco)        # back wall
    n.face(-T, 0, T, D, wall_fill, wall_deco)            # left wall
    n.face(W, 0, T, D, wall_fill, wall_deco)             # right wall
    for f in (s, nn):
        n.tab(f, "L", min(0.6, T * 0.9))
        n.tab(f, "R", min(0.6, T * 0.9))
    return n


# ================================================================ artwork helpers
def rrect(c, x, y, w, h, r, fill, stroke=None, lw=0.5):
    c.setFillColor(fill)
    if stroke is not None:
        c.setStrokeColor(stroke)
        c.setLineWidth(lw)
    c.roundRect(x, y, w, h, r, fill=1, stroke=1 if stroke is not None else 0)


def gloss(c, x, y, w, h, base_dark, base_light):
    try:
        c.linearGradient(x, y, x + w, y + h, (base_dark, base_light), extend=False)
    except Exception:
        c.setFillColor(base_dark)
        c.rect(x, y, w, h, fill=1, stroke=0)


def blue_panel(c, x, y, w, h):
    gloss(c, x, y, w, h, BLUE_D, BLUE_L)


def label(c, x, y, txt, size=6, color=white, font="Helvetica-Bold"):
    c.setFillColor(color)
    c.setFont(font, size)
    c.drawCentredString(x, y, txt)


# ---- tower
def tower_front(c, x, y, w, h):
    blue_panel(c, x, y, w, h)
    # vertical vent mesh
    gx0, gx1 = x + w * 0.18, x + w * 0.72
    gy0, gy1 = y + h * 0.12, y + h * 0.78
    c.setFillColor(BLUE_D)
    c.rect(gx0 - 2, gy0 - 2, gx1 - gx0 + 4, gy1 - gy0 + 4, fill=1, stroke=0)
    c.setFillColor(HexColor("#0c1660"))
    step = 0.22 * cm
    yy = gy0 + step / 2
    row = 0
    while yy < gy1:
        xx = gx0 + step / 2 + (step / 2 if row % 2 else 0)
        while xx < gx1:
            c.circle(xx, yy, 0.055 * cm, fill=1, stroke=0)
            xx += step
        yy += step * 0.866
        row += 1
    # right accent strip
    c.setFillColor(HexColor("#2a49d6"))
    c.rect(x + w * 0.82, y + h * 0.1, w * 0.08, h * 0.8, fill=1, stroke=0)
    # power button + front USB
    c.setFillColor(SILVER)
    c.circle(x + w * 0.45, y + h * 0.9, 0.22 * cm, fill=1, stroke=0)
    c.setStrokeColor(BLUE_D)
    c.setLineWidth(0.8)
    c.circle(x + w * 0.45, y + h * 0.9, 0.11 * cm, fill=0, stroke=1)
    c.line(x + w * 0.45, y + h * 0.9, x + w * 0.45, y + h * 0.9 + 0.13 * cm)
    for i in range(2):
        rrect(c, x + w * 0.2 + i * 0.5 * cm, y + h * 0.84, 0.35 * cm, 0.12 * cm, 1, BLACK)


def tower_side(c, x, y, w, h):
    blue_panel(c, x, y, w, h)
    c.setFillColor(HexColor("#ffffff22"))
    c.setFillAlpha(0.12)
    p = c.beginPath()
    p.moveTo(x, y + h)
    p.lineTo(x + w * 0.45, y + h)
    p.lineTo(x, y + h * 0.55)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    c.setFillAlpha(1)


def tower_back(c, x, y, w, h):
    """Rear panel, modelled on the 2nd photo."""
    u = cm
    c.setFillColor(DGRAY)
    c.rect(x, y, w, h, fill=1, stroke=0)
    m = 0.25 * u
    # main plate
    rrect(c, x + m, y + m, w - 2 * m, h - 2 * m, 3, LGRAY)
    # I/O shield (left top)
    iox, ioy, iow, ioh = x + 0.45 * u, y + h * 0.43, w * 0.36, h * 0.52
    rrect(c, iox, ioy, iow, ioh, 2, SILVER, MGRAY, 0.4)
    cx = iox + iow * 0.3
    cy = ioy + ioh
    # audio jack
    c.setFillColor(HexColor("#7ac142"))
    c.circle(cx, cy - 0.35 * u, 0.13 * u, fill=1, stroke=0)
    c.setFillColor(BLACK)
    c.circle(cx, cy - 0.35 * u, 0.06 * u, fill=1, stroke=0)
    # DisplayPort, HDMI
    rrect(c, cx - 0.17 * u, cy - 1.15 * u, 0.34 * u, 0.55 * u, 1, BLACK)
    rrect(c, cx - 0.12 * u, cy - 1.85 * u, 0.24 * u, 0.5 * u, 1, BLACK)
    # 2 VGA / serial (blue)
    for i in range(2):
        vx = iox + iow * (0.27 + i * 0.5)
        rrect(c, vx - 0.17 * u, cy - 3.0 * u, 0.34 * u, 0.85 * u, 3, HexColor("#3b7ddd"), BLACK, 0.4)
        c.setFillColor(MGRAY)
        c.circle(vx, cy - 2.03 * u, 0.06 * u, fill=1, stroke=0)
        c.circle(vx, cy - 3.12 * u, 0.06 * u, fill=1, stroke=0)
    # 4 USB + LAN
    for r in range(2):
        for k in range(2):
            rrect(c, iox + 0.2 * u + k * 0.38 * u, cy - (4.0 + r * 0.8) * u, 0.26 * u, 0.6 * u, 1, BLACK)
    rrect(c, iox + 1.05 * u, cy - 4.0 * u, 0.42 * u, 0.42 * u, 1, BLACK)
    # fan hex grille (right top)
    fx, fy, fr = x + w * 0.7, y + h * 0.8, w * 0.27
    c.setFillColor(BLACK)
    step = 0.26 * u
    yy = fy - fr
    row = 0
    while yy <= fy + fr:
        xx = fx - fr + (step / 2 if row % 2 else 0)
        while xx <= fx + fr:
            if math.hypot(xx - fx, yy - fy) <= fr:
                c.circle(xx, yy, 0.09 * u, fill=1, stroke=0)
            xx += step
        yy += step * 0.866
        row += 1
    # small knock-out / cable cover
    rrect(c, x + w * 0.62, y + h * 0.47, w * 0.18, h * 0.12, 2, BLACK)
    # expansion slots
    sy = y + h * 0.40
    rrect(c, x + 0.45 * u, sy - 0.05 * u, w - 0.9 * u, 0.35 * u, 4, SILVER, MGRAY, 0.4)
    for i in range(3):
        yy = sy - (0.55 + i * 0.6) * u
        rrect(c, x + 0.6 * u, yy, w - 1.2 * u, 0.42 * u, 2, SILVER, MGRAY, 0.4)
        c.setFillColor(DGRAY)
        for k in range(14):
            c.circle(x + 0.9 * u + k * 0.27 * u, yy + 0.21 * u, 0.04 * u, fill=1, stroke=0)
    # PSU
    px, py, pw, ph = x + 0.4 * u, y + 0.4 * u, w - 0.8 * u, h * 0.2
    rrect(c, px, py, pw, ph, 3, MGRAY, DGRAY, 0.5)
    c.setFillColor(DGRAY)
    for r in range(7):
        for k in range(18):
            xx = px + 0.15 * u + k * 0.3 * u
            yy = py + 0.18 * u + r * 0.32 * u
            if not (px + pw * 0.3 < xx < px + pw * 0.62):
                c.circle(xx, yy, 0.07 * u, fill=1, stroke=0)
    rrect(c, px + pw * 0.33, py + ph * 0.3, pw * 0.26, ph * 0.42, 2, BLACK)
    c.setFillColor(MGRAY)
    for k in range(3):
        c.rect(px + pw * (0.37 + k * 0.07), py + ph * 0.48, 0.06 * u, 0.12 * u, fill=1, stroke=0)
    c.setFillColor(HexColor("#555555"))
    c.setFont("Helvetica", 5)
    c.drawCentredString(x + w / 2, y + h - 0.2 * u, "BACK")


# ---- speakers
def speaker_front(c, x, y, w, h):
    blue_panel(c, x, y, w, h)
    m = 0.22 * cm
    rrect(c, x + m, y + m, w - 2 * m, h - 2 * m, 8, BLACK)
    cx = x + w / 2
    # logo badge (chrome circle)
    ly = y + h * 0.76
    c.setFillColor(SILVER)
    c.circle(cx, ly, 0.5 * cm, fill=1, stroke=0)
    c.setFillColor(MGRAY)
    c.circle(cx, ly, 0.42 * cm, fill=1, stroke=0)
    c.setFillColor(BLACK)
    c.circle(cx, ly, 0.35 * cm, fill=1, stroke=0)
    c.setStrokeColor(SILVER)
    c.setLineWidth(1.6)
    c.arc(cx - 0.22 * cm, ly - 0.22 * cm, cx + 0.22 * cm, ly + 0.22 * cm, 30, 220)
    # small text line
    c.setFillColor(HexColor("#6f86ff"))
    c.setFont("Helvetica-Bold", 6)
    c.drawCentredString(cx, y + h * 0.6, "SOUND")
    # driver
    dy = y + h * 0.3
    c.setFillColor(BLUE_L)
    c.circle(cx, dy, 1.35 * cm, fill=1, stroke=0)
    c.setFillColor(BLACK)
    c.circle(cx, dy, 1.25 * cm, fill=1, stroke=0)
    c.setFillColor(CREAM)
    c.circle(cx, dy, 1.05 * cm, fill=1, stroke=0)
    c.setFillColor(white)
    c.circle(cx - 0.25 * cm, dy + 0.25 * cm, 0.55 * cm, fill=1, stroke=0)
    c.setStrokeColor(DGRAY)
    c.setLineWidth(2)
    c.arc(cx - 0.75 * cm, dy - 0.75 * cm, cx + 0.75 * cm, dy + 0.75 * cm, 200, 110)


def speaker_front_rgb(c, x, y, w, h):
    """Alternative front (3rd photo): black mesh + RGB light bar."""
    c.setFillColor(BLACK)
    c.rect(x, y, w, h, fill=1, stroke=0)
    c.setFillColor(HexColor("#2a2a2a"))
    s = 0.12 * cm
    yy = y
    while yy < y + h:
        xx = x
        while xx < x + w:
            c.circle(xx, yy, 0.025 * cm, fill=1, stroke=0)
            xx += s
        yy += s
    # driver (mesh circle)
    c.setFillColor(HexColor("#3a3a3a"))
    cx, cy = x + w * 0.6, y + h * 0.66
    c.circle(cx, cy, 1.1 * cm, fill=1, stroke=0)
    c.setFillColor(HexColor("#555555"))
    yy = cy - 1.1 * cm
    while yy < cy + 1.1 * cm:
        xx = cx - 1.1 * cm
        while xx < cx + 1.1 * cm:
            if math.hypot(xx - cx, yy - cy) < 1.05 * cm:
                c.circle(xx, yy, 0.03 * cm, fill=1, stroke=0)
            xx += s * 0.8
        yy += s * 0.8
    # RGB bar
    cols = ["#22c55e", "#84cc16", "#eab308", "#f97316", "#ef4444", "#e11d48",
            "#db2777", "#c026d3", "#9333ea", "#4f46e5", "#2563eb", "#1d4ed8"]
    bx, bw = x + w * 0.14, w * 0.17
    seg = h * 0.8 / 22
    for i in range(22):
        col = cols[min(int(i / 22 * len(cols)), len(cols) - 1)]
        rrect(c, bx, y + h * 0.08 + i * seg, bw, seg * 0.78, 1, HexColor(col))
    # name plate
    rrect(c, x + w * 0.42, y + h * 0.18, w * 0.5, h * 0.07, 1, HexColor("#1e2a44"))
    c.setFillColor(LGRAY)
    c.setFont("Helvetica-Bold", 5.5)
    c.drawCentredString(x + w * 0.67, y + h * 0.198, "SOUND")


def speaker_back(c, x, y, w, h):
    blue_panel(c, x, y, w, h)
    c.setFillColor(BLACK)
    c.circle(x + w / 2, y + h * 0.3, 0.12 * cm, fill=1, stroke=0)
    rrect(c, x + w * 0.35, y + h * 0.15, w * 0.3, 0.2 * cm, 1, BLACK)


# ---- monitor
def monitor_front(c, x, y, w, h):
    c.setFillColor(BLACK)
    c.rect(x, y, w, h, fill=1, stroke=0)
    b = 0.3 * cm
    sx, sy, sw, sh = x + b, y + b, w - 2 * b, h - 2 * b
    # wallpaper: sky
    gloss(c, sx, sy, sw * 0.4, sh, HexColor("#0b3d91"), HexColor("#5aa9ff"))
    c.saveState()
    c.linearGradient(sx, sy, sx, sy + sh, (HexColor("#1b5fb8"), HexColor("#9fd0ff")), extend=False)
    c.restoreState()
    # mountains
    def poly(pts, col):
        p = c.beginPath()
        p.moveTo(*pts[0])
        for q in pts[1:]:
            p.lineTo(*q)
        p.close()
        c.setFillColor(col)
        c.drawPath(p, fill=1, stroke=0)
    poly([(sx + sw * .35, sy), (sx + sw * .72, sy + sh * .78), (sx + sw * .85, sy + sh * .55),
          (sx + sw, sy + sh * .7), (sx + sw, sy)], HexColor("#2c4a6e"))
    poly([(sx + sw * .55, sy + sh * .5), (sx + sw * .72, sy + sh * .78), (sx + sw * .8, sy + sh * .62),
          (sx + sw * .7, sy + sh * .55), (sx + sw * .65, sy + sh * .42)], HexColor("#f4f8ff"))
    poly([(sx + sw * .8, sy + sh * .62), (sx + sw * .85, sy + sh * .55), (sx + sw, sy + sh * .7),
          (sx + sw, sy + sh * .55), (sx + sw * .9, sy + sh * .5)], HexColor("#e6eefb"))
    poly([(sx + sw * .3, sy), (sx + sw * .6, sy + sh * .3), (sx + sw, sy + sh * .12), (sx + sw, sy)],
         HexColor("#1d3557"))
    # start menu
    mx, my, mw, mh = sx, sy + sh * 0.08, sw * 0.42, sh * 0.82
    c.setFillColor(HexColor("#1f2733"))
    c.rect(mx, my, mw, mh, fill=1, stroke=0)
    c.setFillColor(HexColor("#9aa4b1"))
    for i in range(9):
        c.rect(mx + 0.2 * cm, my + mh - (0.5 + i * 0.42) * cm, mw * 0.28, 0.06 * cm, fill=1, stroke=0)
    tiles = ["#0078d7", "#00a300", "#e81123", "#ff8c00", "#5c2d91", "#00b7c3",
             "#0063b1", "#2d7d9a", "#ffb900", "#e3008c", "#107c10", "#0099bc",
             "#c30052", "#4a5459", "#7a7574", "#0078d7"]
    tx0, ty0 = mx + mw * 0.4, my + mh - 0.35 * cm
    ts = mw * 0.135
    k = 0
    for r in range(5):
        for col in range(4):
            colr = tiles[k % len(tiles)]
            k += 1
            c.setFillColor(HexColor(colr))
            c.rect(tx0 + col * (ts + 0.06 * cm), ty0 - (r + 1) * (ts + 0.06 * cm), ts, ts, fill=1, stroke=0)
            c.setFillColor(white)
            c.circle(tx0 + col * (ts + 0.06 * cm) + ts / 2, ty0 - (r + 1) * (ts + 0.06 * cm) + ts / 2,
                     ts * 0.15, fill=1, stroke=0)
    # taskbar
    c.setFillColor(HexColor("#101418"))
    c.rect(sx, sy, sw, sh * 0.07, fill=1, stroke=0)
    c.setFillColor(HexColor("#4aa3ff"))
    c.rect(sx + 0.12 * cm, sy + 0.08 * cm, 0.18 * cm, 0.18 * cm, fill=1, stroke=0)
    c.setFillColor(HexColor("#d0d6dd"))
    for i in range(6):
        c.rect(sx + (1.4 + i * 0.4) * cm, sy + 0.1 * cm, 0.2 * cm, 0.15 * cm, fill=1, stroke=0)
    c.setFont("Helvetica", 4)
    c.drawRightString(sx + sw - 0.15 * cm, sy + 0.11 * cm, "12:00")


def black_panel(c, x, y, w, h):
    gloss(c, x, y, w, h, HexColor("#0b0b0b"), HexColor("#2c2c2c"))


def monitor_back(c, x, y, w, h):
    black_panel(c, x, y, w, h)
    # neck glue area (lower middle)
    nw, nh = NECK["W"] * cm, 3.0 * cm
    c.setStrokeColor(MGRAY)
    c.setDash(2, 2)
    c.setLineWidth(0.6)
    c.rect(x + (w - nw) / 2, y + 0.8 * cm, nw, nh, fill=0, stroke=1)
    c.setDash()
    label(c, x + w / 2, y + 0.8 * cm + nh / 2, "glue stand", 5, MGRAY, "Helvetica")
    label(c, x + w / 2, y + h - 0.6 * cm, "MONITOR BACK", 6, HexColor("#555555"))
    c.setFillColor(HexColor("#333333"))
    for i in range(10):
        c.rect(x + w * 0.3 + i * 0.6 * cm, y + h * 0.75, 0.3 * cm, 0.08 * cm, fill=1, stroke=0)


# ---- keyboard
def keyboard_top(c, x, y, w, h):
    blue_panel(c, x, y, w, h)
    pad = 0.3 * cm
    kx, ky, kw, kh = x + pad, y + pad, w - 2 * pad, h - 2 * pad
    U = kw / 15.0
    # layout taken from the user's reference keyboard picture
    rows = [
        ([1] * 13 + [2], list("`1234567890-=") + ["Backspace"], 1),
        ([1.5] + [1] * 12 + [1.5], ["Tab"] + list("QWERTYUIOP[]") + ["\\"], 1),
        ([1.75] + [1] * 11 + [2.25], ["Caps Lock"] + list("ASDFGHJKL;'") + ["Enter"], 1),
        ([2.25] + [1] * 10 + [2.75], ["Shift"] + list("ZXCVBNM<>?") + ["Shift"], 1),
        ([1, 1, 1, 1, 7.5, 2, 1], ["Ctrl", "WIN", "fn", "Alt", "Space", "Control", "Alt"], 1),
    ]
    total_h = sum(r[2] for r in rows)
    rh = kh / total_h
    gap = 0.05 * cm
    yy = ky + kh
    for widths, labels_, hu in rows:
        s = sum(widths)
        scale = 15.0 / s
        xx = kx
        rhh = rh * hu
        yy -= rhh
        for wu, lb in zip(widths, labels_):
            kwid = wu * scale * U
            rrect(c, xx + gap, yy + gap, kwid - 2 * gap, rhh - 2 * gap, 1.5, KEY, HexColor("#3a3f6b"), 0.3)
            if lb == "WIN":
                q = rhh * 0.16
                kcx, kcy = xx + kwid / 2, yy + rhh / 2
                c.setFillColor(HexColor("#3a3f6b"))
                for ddx in (-1, 1):
                    for ddy in (-1, 1):
                        c.rect(kcx + (ddx - 1) * q * 0.55 + 0.3, kcy + (ddy - 1) * q * 0.55 + 0.3,
                               q, q, fill=1, stroke=0)
            elif lb:
                c.setFillColor(HexColor("#2b2f55"))
                c.setFont("Helvetica", 3.4 if len(lb) > 1 else 5)
                c.drawCentredString(xx + kwid / 2, yy + rhh / 2 - 1.4, lb)
            xx += kwid


def mouse_top(c, x, y, w, h):
    blue_panel(c, x, y, w, h)
    c.setFillColor(HexColor("#6f8cff"))
    c.setFillAlpha(0.35)
    c.ellipse(x + w * 0.12, y + h * 0.15, x + w * 0.62, y + h * 0.9, fill=1, stroke=0)
    c.setFillAlpha(1)
    c.setStrokeColor(BLUE_D)
    c.setLineWidth(0.8)
    c.line(x + w / 2, y + h * 0.6, x + w / 2, y + h)
    c.line(x, y + h * 0.6, x + w, y + h * 0.6)
    rrect(c, x + w / 2 - 0.12 * cm, y + h * 0.7, 0.24 * cm, 0.6 * cm, 2, BLACK)


# ================================================================ page helpers
def page_header(c, pw, ph, title, info):
    c.setFillColor(BLUE_D)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(1.0 * cm, ph - 1.0 * cm, title)
    c.setFillColor(HexColor("#444444"))
    c.setFont("Helvetica", 7.5)
    yy = ph - 1.45 * cm
    for line in info:
        c.drawString(1.0 * cm, yy, line)
        yy -= 0.32 * cm
    # legend + scale ruler (bottom)
    c.setFont("Helvetica", 6.5)
    c.setFillColor(black)
    y0 = 0.55 * cm
    c.setStrokeColor(black)
    c.setLineWidth(0.8)
    c.line(1 * cm, y0, 1.8 * cm, y0)
    c.drawString(1.9 * cm, y0 - 2, "cut")
    c.setDash(3, 2)
    c.setStrokeColor(HexColor("#555555"))
    c.line(2.6 * cm, y0, 3.4 * cm, y0)
    c.setDash()
    c.drawString(3.5 * cm, y0 - 2, "fold (score first)")
    c.setFillColor(TAB)
    c.rect(5.6 * cm, y0 - 0.12 * cm, 0.5 * cm, 0.25 * cm, fill=1, stroke=1)
    c.setFillColor(black)
    c.drawString(6.2 * cm, y0 - 2, "glue tab")
    # 5 cm ruler
    rx = pw - 6.5 * cm
    c.setLineWidth(0.6)
    c.line(rx, y0, rx + 5 * cm, y0)
    for i in range(6):
        c.line(rx + i * cm, y0, rx + i * cm, y0 + 0.18 * cm)
    c.drawString(rx + 5.15 * cm, y0 - 2, "= 5 cm (check scale)")


def new_page(c, size):
    c.setPageSize(size)
    return size


# ================================================================ pages
PRINT_NOTE = "Print at 100 % / 'Actual size' (NOT 'Fit to page'). Use 160-220 g/m2 card or glue the print onto thin card."


def page_instructions(c):
    pw, ph = new_page(c, A4)
    c.setFillColor(YELLOW)
    c.rect(0, ph - 3.2 * cm, pw, 3.2 * cm, fill=1, stroke=0)
    c.setFillColor(BLUE_D)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(1.2 * cm, ph - 1.7 * cm, "Desktop Computer Papercraft Model")
    c.setFont("Helvetica", 10)
    c.setFillColor(BLACK)
    c.drawString(1.2 * cm, ph - 2.5 * cm, "Blue PC set on a yellow board  -  A4 cut, fold & glue templates")

    y = ph - 4.2 * cm
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(BLUE_D)
    c.drawString(1.2 * cm, y, "You need")
    c.setFont("Helvetica", 9.5)
    c.setFillColor(BLACK)
    items = [
        "A4 colour printer, thick paper/card (160-220 g/m2) - or normal paper glued onto cereal-box card",
        "Scissors or craft knife + ruler, a blunt point (empty pen) to score fold lines",
        "Glue stick / white PVA glue (or double-sided tape)",
        "Base: a piece of stiff cardboard or foam board, 38 x 27 cm",
    ]
    for it in items:
        y -= 0.5 * cm
        c.drawString(1.5 * cm, y, u"•  " + it)

    y -= 0.9 * cm
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(BLUE_D)
    c.drawString(1.2 * cm, y, "Parts list (finished sizes, cm)")
    c.setFont("Helvetica", 9.5)
    c.setFillColor(BLACK)
    parts = [
        ("01", "Base board - 2 yellow sheets + black edge strips", "38 x 27"),
        ("02", "PC tower - 2 sheets (piece A + piece B)", "%g W x %g D x %g H" % (TOWER["W"], TOWER["D"], TOWER["H"])),
        ("03", "Monitor screen box", "%g x %g x %g" % (MON["W"], MON["H"], MON["T"])),
        ("04", "Monitor stand (neck + foot)", "neck %g H, foot %g x %g" % (NECK["H"], FOOT["W"], FOOT["D"])),
        ("05", "Speaker LEFT and 06 Speaker RIGHT", "%g W x %g D x %g H" % (SPK["W"], SPK["D"], SPK["H"])),
        ("07", "Keyboard + mouse", "%g x %g  /  %g x %g" % (KB["W"], KB["D"], MOUSE["W"], MOUSE["D"])),
        ("08", "OPTIONAL: RGB speaker fronts (3rd photo style)", "glue over speaker fronts"),
    ]
    for n, name, size in parts:
        y -= 0.5 * cm
        c.drawString(1.5 * cm, y, n)
        c.drawString(2.4 * cm, y, name)
        c.drawRightString(pw - 1.5 * cm, y, size)

    y -= 0.9 * cm
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(BLUE_D)
    c.drawString(1.2 * cm, y, "How to build")
    c.setFont("Helvetica", 9.5)
    c.setFillColor(BLACK)
    steps = [
        "1. Print every page at 100 %. Measure the 5 cm ruler at the bottom of a page to check the scale.",
        "2. Cut along SOLID lines. Score DASHED lines with a ruler and blunt point, then fold them away from you",
        "   (printed side stays outside). Grey 'glue' tabs always go INSIDE the model.",
        "3. Close each box: glue the side tab first, then the top and bottom lids. Hold 30 s until the glue grabs.",
        "4. Tip: before closing big boxes (tower, speakers) put a crumpled paper or card inside to keep them firm.",
        "5. Tower: glue piece A tab under the edge of piece B's back face, then piece B's tab inside the front face.",
        "6. Monitor: fold the screen box, glue the neck to the 'glue stand' mark on the back, glue the neck into",
        "   the centre of the foot. Lean the screen slightly back if you like.",
        "7. Base: glue the 2 yellow sheets side by side on the cardboard (left + right). Wrap the black strips",
        "   around the cardboard edges. Dotted outlines on the base show where each part stands.",
        "8. Glue all parts on their outlines: speakers, monitor, tower, keyboard, mouse. Done!",
    ]
    for s in steps:
        y -= 0.48 * cm
        c.drawString(1.5 * cm, y, s)

    # mini layout drawing
    y -= 0.8 * cm
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(BLUE_D)
    c.drawString(1.2 * cm, y, "Layout on the base (top view)")
    sc = 0.3
    bx0, by0 = 1.5 * cm, y - 0.4 * cm - BASE["D"] * sc * cm
    c.setFillColor(YELLOW)
    c.setStrokeColor(black)
    c.rect(bx0, by0, BASE["W"] * sc * cm, BASE["D"] * sc * cm, fill=1, stroke=1)
    for name, (fx, fy, fw, fd) in FOOTPRINTS.items():
        c.setFillColor(BLUE if name != "Monitor" else BLACK)
        c.rect(bx0 + fx * sc * cm, by0 + fy * sc * cm, fw * sc * cm, fd * sc * cm, fill=1, stroke=0)
        c.setFillColor(BLACK)
        c.setFont("Helvetica", 6.5)
        c.drawString(bx0 + (fx + fw + 0.3) * sc * cm, by0 + (fy + fd / 2) * sc * cm, name)
    c.setFont("Helvetica-Oblique", 7)
    c.drawString(bx0, by0 - 0.35 * cm, "front edge (you sit here)")
    c.setFont("Helvetica", 7)
    c.setFillColor(HexColor("#666666"))
    c.drawString(1.2 * cm, 0.8 * cm, PRINT_NOTE)


# footprint positions on the base: x, y (from front-left), w, depth (cm)
FOOTPRINTS = {
    "Speaker L": (3.0, 12.0, SPK["W"], SPK["D"]),
    "Monitor": (9.0, 15.0, FOOT["W"], FOOT["D"]),
    "Speaker R": (19.0, 16.5, SPK["W"], SPK["D"]),
    "Tower": (27.5, 13.5, TOWER["W"], TOWER["D"]),
    "Keyboard": (10.0, 4.0, KB["W"], KB["D"]),
    "Mouse": (27.0, 5.0, MOUSE["W"], MOUSE["D"]),
}


def page_base(c, half):
    pw, ph = new_page(c, A4)
    W2 = BASE["W"] / 2
    ox, oy = (pw / cm - W2) / 2, (ph / cm - BASE["D"]) / 2 + 0.2
    c.setFillColor(YELLOW)
    c.rect(ox * cm, oy * cm, W2 * cm, BASE["D"] * cm, fill=1, stroke=0)
    # placement outlines
    shift = 0 if half == 0 else -W2
    c.saveState()
    p = c.beginPath()
    p.rect(ox * cm, oy * cm, W2 * cm, BASE["D"] * cm)
    c.clipPath(p, stroke=0, fill=0)
    for name, (fx, fy, fw, fd) in FOOTPRINTS.items():
        X = (ox + fx + shift) * cm
        Y = (oy + fy) * cm
        c.setStrokeColor(HexColor("#b39200"))
        c.setDash(1, 2)
        c.setLineWidth(0.7)
        c.rect(X, Y, fw * cm, fd * cm, fill=0, stroke=1)
        c.setDash()
        c.setFillColor(HexColor("#b39200"))
        c.setFont("Helvetica", 6)
        c.drawCentredString(X + fw * cm / 2, Y + fd * cm / 2 - 2, name)
    c.restoreState()
    # cut outline
    c.setStrokeColor(black)
    c.setLineWidth(0.8)
    c.rect(ox * cm, oy * cm, W2 * cm, BASE["D"] * cm, fill=0, stroke=1)
    c.setFillColor(BLUE_D)
    c.setFont("Helvetica-Bold", 11)
    side = "LEFT" if half == 0 else "RIGHT"
    c.drawString(1.0 * cm, ph - 0.8 * cm, "01  BASE BOARD - %s half  (%g x %g cm)" % (side, W2, BASE["D"]))
    c.setFont("Helvetica", 7)
    c.setFillColor(HexColor("#444444"))
    c.drawString(1.0 * cm, ph - 1.15 * cm,
                 "Glue on cardboard. The %s edge of this sheet touches the other half. Front edge = bottom of the page."
                 % ("RIGHT" if half == 0 else "LEFT"))
    c.setFont("Helvetica", 6.5)
    c.drawString(1.0 * cm, 0.45 * cm, "Print at 100 %. Cut on the black line.")


def page_edge_strips(c):
    pw, ph = new_page(c, A4)
    page_header(c, pw, ph, "01b  BASE BOARD - black edge strips",
                ["Cut out and glue around the cardboard edges (the black rim in the photo).",
                 "Strips are 1.5 cm wide: fold on the dashed line so ~0.5 cm wraps under the board.",
                 "Front + back edges: 2 x 19 cm each. Left + right edges: 2 x 13.5 cm each (= 27 cm)."])
    x0, y0 = 1.0, 2.0
    strips = [(19, "front (left half)"), (19, "front (right half)"), (19, "back (left half)"),
              (19, "back (right half)"), (13.5, "left side 1/2"), (13.5, "left side 2/2"),
              (13.5, "right side 1/2"), (13.5, "right side 2/2")]
    for i, (L, nm) in enumerate(strips):
        _strip(c, x0, y0 + i * 2.1, L, 1.5)
        c.setFillColor(BLUE_D)
        c.setFont("Helvetica", 7)
        c.drawString((x0 + 0.1) * cm, (y0 + i * 2.1 + 1.6) * cm, nm)


def _strip(c, x, y, L, Wd):
    c.setFillColor(BLACK)
    c.rect(x * cm, y * cm, L * cm, Wd * cm, fill=1, stroke=0)
    c.setStrokeColor(black)
    c.setLineWidth(0.8)
    c.rect(x * cm, y * cm, L * cm, Wd * cm, fill=0, stroke=1)
    c.setStrokeColor(MGRAY)
    c.setDash(3, 2)
    c.line(x * cm, (y + 0.5) * cm, (x + L) * cm, (y + 0.5) * cm)
    c.setDash()


def _vstrip(c, x, y, L, Wd):
    c.setFillColor(BLACK)
    c.rect(x * cm, y * cm, Wd * cm, L * cm, fill=1, stroke=0)
    c.setStrokeColor(black)
    c.setLineWidth(0.8)
    c.rect(x * cm, y * cm, Wd * cm, L * cm, fill=0, stroke=1)
    c.setStrokeColor(MGRAY)
    c.setDash(3, 2)
    c.line((x + 0.5) * cm, y * cm, (x + 0.5) * cm, (y + L) * cm)
    c.setDash()
    c.setFillColor(MGRAY)
    c.setFont("Helvetica", 6)
    c.drawString((x + 0.6) * cm, (y + L + 0.15) * cm, "+3.5 cm: join a")
    c.drawString((x + 0.6) * cm, (y + L - 0.15) * cm, "")


def place(c, net, pw, ph, top_space=2.6, bottom_space=1.2):
    x0, y0, x1, y1 = net.bbox()
    w, h = x1 - x0, y1 - y0
    ox = (pw / cm - w) / 2
    avail = ph / cm - top_space - bottom_space
    oy = bottom_space + (avail - h) / 2
    net.draw(c, ox, oy)


def page_tower(c, piece):
    pw, ph = new_page(c, A4)
    W, D, H = TOWER["W"], TOWER["D"], TOWER["H"]
    n = Net()
    if piece == "A":
        f = n.face(0, 0, W, H, BLUE, tower_front)
        r = n.face(W, 0, D, H, BLUE, tower_side)
        n.tab(r, "R")
        t = n.face(0, H, W, D, BLUE, blue_panel)
        n.tab(t, "L"), n.tab(t, "T"), n.tab(t, "R")
        info = ["Piece A = FRONT + RIGHT side + TOP.  Size %g x %g x %g cm." % (W, D, H),
                "The tab on the right side glues behind the left edge of piece B (back panel)."]
    else:
        b = n.face(0, 0, W, H, DGRAY, tower_back)
        l = n.face(W, 0, D, H, BLUE, tower_side)
        n.tab(l, "R")
        bt = n.face(0, -D, W, D, BLUE_D, None)
        n.tab(bt, "L"), n.tab(bt, "B"), n.tab(bt, "R")
        info = ["Piece B = BACK (ports panel) + LEFT side + BOTTOM.",
                "Its side tab glues inside the left edge of the FRONT face (piece A)."]
    page_header(c, pw, ph, "02%s  PC TOWER - piece %s" % ("a" if piece == "A" else "b", piece), info + [PRINT_NOTE])
    place(c, n, pw, ph)


def page_monitor(c):
    pw, ph = new_page(c, A4)
    W, H, T = MON["W"], MON["H"], MON["T"]
    n = Net()
    f = n.face(0, 0, W, H, BLACK, monitor_front)
    top = n.face(0, H, W, T, BLACK, black_panel)
    bot = n.face(0, -T, W, T, BLACK, black_panel)
    lf = n.face(-T, 0, T, H, BLACK, black_panel)
    rt = n.face(W, 0, T, H, BLACK, black_panel)
    back = n.face(0, H + T, W, H, BLACK, monitor_back)
    for s in (top, bot):
        n.tab(s, "L", 0.6), n.tab(s, "R", 0.6)
    n.tab(bot, "B", 0.8), n.tab(lf, "L", 0.8), n.tab(rt, "R", 0.8)
    page_header(c, pw, ph, "03  MONITOR screen box",
                ["Front = screen, the panel above it = monitor back. The thin black strips are the edges (%g cm)." % T,
                 "Fold the 4 edges up, glue the small corner tabs, then fold the back down and glue on the 3 long tabs.",
                 PRINT_NOTE])
    place(c, n, pw, ph)


def page_stand(c):
    pw, ph = new_page(c, A4)
    page_header(c, pw, ph, "04  MONITOR STAND - neck + foot",
                ["Neck: %g x %g x %g cm box. Foot: %g x %g cm, %g cm high (open underneath)."
                 % (NECK["W"], NECK["D"], NECK["H"], FOOT["W"], FOOT["D"], FOOT["T"]),
                 "Glue the neck's top half to the 'glue stand' mark on the monitor back; glue its bottom in the foot centre.",
                 "Tip: a strip of card or a lolly stick inside the neck makes it much stronger.", PRINT_NOTE])
    neck = box_strip(NECK["W"], NECK["D"], NECK["H"], black_panel, black_panel, black_panel, black_panel,
                     black_panel, black_panel, fills={k: BLACK for k in
                                                       ["front", "right", "back", "left", "top", "bottom"]})

    def foot_top(c2, x, y, w, h):
        black_panel(c2, x, y, w, h)
        c2.setStrokeColor(MGRAY)
        c2.setDash(2, 2)
        nw, nd = NECK["W"] * cm, NECK["D"] * cm
        c2.rect(x + (w - nw) / 2, y + (h - nd) / 2 + 0.4 * cm, nw, nd, fill=0, stroke=1)
        c2.setDash()
        label(c2, x + w / 2, y + h / 2 - 0.5 * cm, "neck here", 5, MGRAY, "Helvetica")

    foot = tray(FOOT["W"], FOOT["D"], FOOT["T"], foot_top, BLACK, BLACK, black_panel)
    neck.draw(c, (pw / cm - 9.5) / 2, 15.0)
    foot.draw(c, (pw / cm - 8.5) / 2, 4.0)
    label(c, pw / 2, 14.3 * cm, "NECK", 8, BLUE_D)
    label(c, pw / 2, 3.2 * cm, "FOOT", 8, BLUE_D)


def page_speaker(c, side):
    pw, ph = new_page(c, A4)
    W, D, H = SPK["W"], SPK["D"], SPK["H"]
    n = box_strip(W, D, H, speaker_front, blue_panel, speaker_back, blue_panel, blue_panel, blue_panel)
    num = "05" if side == "LEFT" else "06"
    page_header(c, pw, ph, "%s  SPEAKER - %s" % (num, side),
                ["Box %g W x %g D x %g H cm. Front = black panel with the round driver." % (W, D, H),
                 "The net is printed sideways to fit the page.", PRINT_NOTE])
    x0, y0, x1, y1 = n.bbox()
    w, h = x1 - x0, y1 - y0          # drawn rotated: h becomes page width
    c.saveState()
    c.translate((pw / cm + h) / 2 * cm, (1.2 + (ph / cm - 3.8 - w) / 2) * cm)
    c.rotate(90)
    n.draw(c, 0, 0)
    c.restoreState()


def page_keyboard_mouse(c):
    pw, ph = new_page(c, A4)
    page_header(c, pw, ph, "07  KEYBOARD + MOUSE",
                ["Both are open underneath: fold the walls down, glue the corner tabs inside the side walls.",
                 "Mouse tip: after gluing, gently bend the top so it looks rounded.", PRINT_NOTE])
    kb = tray(KB["W"], KB["D"], KB["T"], keyboard_top, BLUE_D, BLUE, blue_panel)
    ms = tray(MOUSE["W"], MOUSE["D"], MOUSE["T"], mouse_top, BLUE_D, BLUE, blue_panel)
    kb.draw(c, (pw / cm - 16.6) / 2, 17.0)
    ms.draw(c, (pw / cm - 6.0) / 2, 4.5)
    label(c, pw / 2, 16.2 * cm, "KEYBOARD", 8, BLUE_D)
    label(c, pw / 2, 3.6 * cm, "MOUSE", 8, BLUE_D)


def page_rgb_fronts(c):
    pw, ph = new_page(c, A4)
    page_header(c, pw, ph, "08  OPTIONAL - RGB speaker fronts",
                ["Like the 3rd photo: cut these 2 panels and glue them over the speaker fronts.",
                 "Each panel is exactly %g x %g cm (same as the speaker front)." % (SPK["W"], SPK["H"]), PRINT_NOTE])
    for i in range(2):
        X = (pw / cm / 2 - SPK["W"] - 1 + i * (SPK["W"] + 2)) * cm
        Y = 12 * cm
        speaker_front_rgb(c, X, Y, SPK["W"] * cm, SPK["H"] * cm)
        c.setStrokeColor(black)
        c.setLineWidth(0.8)
        c.rect(X, Y, SPK["W"] * cm, SPK["H"] * cm, fill=0, stroke=1)
        label(c, X + SPK["W"] * cm / 2, Y - 0.5 * cm, ["LEFT", "RIGHT"][i], 7, BLUE_D)


# ================================================================ build
PAGES = [
    ("00_instructions", [page_instructions]),
    ("01_base_board", [lambda c: page_base(c, 0), lambda c: page_base(c, 1), page_edge_strips]),
    ("02_pc_tower", [lambda c: page_tower(c, "A"), lambda c: page_tower(c, "B")]),
    ("03_monitor_screen", [page_monitor]),
    ("04_monitor_stand", [page_stand]),
    ("05_06_speakers", [lambda c: page_speaker(c, "LEFT"), lambda c: page_speaker(c, "RIGHT")]),
    ("07_keyboard_mouse", [page_keyboard_mouse]),
    ("08_optional_rgb_speaker_fronts", [page_rgb_fronts]),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    allc = canvas.Canvas(os.path.join(OUT, "ALL_PARTS.pdf"), pagesize=A4)
    allc.setTitle("Desktop Computer Papercraft - all parts")
    for name, fns in PAGES:
        cc = canvas.Canvas(os.path.join(OUT, name + ".pdf"), pagesize=A4)
        cc.setTitle(name)
        for fn in fns:
            for cv in (cc, allc):
                fn(cv)
                cv.showPage()
        cc.save()
    allc.save()
    print("written to", OUT)


if __name__ == "__main__":
    main()
