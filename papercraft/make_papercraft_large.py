"""LARGE version: closed 3D desktop-computer model on a 50 x 50 cm base.

Every part is a fully closed box. Big boxes are split into several pieces
so that every piece fits on one A4 sheet. Each glue tab carries the piece
code (e.g. T1) so cut-out pieces can always be identified.

Run:  python3 make_papercraft_large.py   ->  pdf_large/*.pdf
"""
import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, black
from reportlab.pdfgen import canvas

from make_papercraft import (
    Net, BLUE, BLUE_D, YELLOW, BLACK, DGRAY, MGRAY, TAB,
    tower_front, tower_side, tower_back, speaker_front, speaker_front_rgb,
    speaker_back, monitor_front, keyboard_top, mouse_top, blue_panel,
    black_panel, label, page_header,
)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf_large")

# ---------------------------------------------------------------- sizes (cm)
BASE = dict(W=50.0, D=50.0)
TOWER = dict(W=9.0, D=16.0, H=20.0)
SPK = dict(W=6.0, D=7.0, H=11.0)
MON = dict(W=24.0, H=15.0, T=1.2)
NECK = dict(W=4.0, D=1.2, H=9.5)
NECK_GLUE = (1.5, 5.0)          # glue zone on monitor back: from-bottom, height
FOOT = dict(W=11.0, D=7.0, T=0.6)
KB = dict(W=22.0, D=7.5, T=1.0)
MOUSE = dict(W=4.5, D=8.0, T=1.3)

# footprint on the base: x, y measured from the FRONT-LEFT corner
FOOTPRINTS = {
    "Speaker L": (2.0, 22.0, SPK["W"], SPK["D"]),
    "Monitor foot": (16.5, 24.0, FOOT["W"], FOOT["D"]),
    "Speaker R": (36.0, 22.0, SPK["W"], SPK["D"]),
    "Tower": (39.0, 31.0, TOWER["W"], TOWER["D"]),
    "Keyboard": (14.0, 6.0, KB["W"], KB["D"]),
    "Mouse": (38.5, 6.0, MOUSE["W"], MOUSE["D"]),
}
TILE_COLS = [17.0, 17.0, 16.0]
TILE_ROWS = [25.0, 25.0]

PRINT_NOTE = ("Print at 100 % / 'Actual size' (NOT 'Fit to page'). "
              "Best on 200-250 g/m2 card; or glue the print onto thin card (cereal box).")
TABD = 1.0  # standard glue tab depth


def scaled(deco, ref_w):
    """Re-use small-model artwork: draw it at its design size, scaled up."""
    def f(c, x, y, w, h):
        s = w / (ref_w * cm)
        c.translate(x, y)
        c.scale(s, s)
        deco(c, 0, 0, w / s, h / s)
    return f


def piece_title(c, net, ox, oy, text):
    x0, y0, x1, y1 = net.bbox()
    net.draw(c, ox, oy)
    c.setFillColor(BLUE_D)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(ox * cm, (oy + (y1 - y0) + 0.25) * cm, text)


def size(net):
    x0, y0, x1, y1 = net.bbox()
    return x1 - x0, y1 - y0


def panel(code, w, h, fill, deco=None, tabs=""):
    n = Net(code)
    f = n.face(0, 0, w, h, fill, deco)
    for s in tabs:
        n.tab(f, s, TABD)
    return n


def walls_strip(code, W, D, H, decos, fills):
    """4 walls in a row + side tab + tabs on every top and bottom edge
    (a separate top and bottom panel are glued onto those tabs)."""
    n = Net(code)
    x = 0
    ids = []
    for wd, deco, fill in zip([W, D, W, D], decos, fills):
        i = n.face(x, 0, wd, H, fill, deco)
        n.tab(i, "T", 0.8)
        n.tab(i, "B", 0.8)
        ids.append(i)
        x += wd
    n.tab(ids[3], "R", TABD)
    return n


def closed_tray(code, W, D, T, top_deco, top_fill, wall_fill, wall_deco):
    """Top + 4 walls; corner tabs + outer tabs. A separate bottom closes it."""
    n = Net(code)
    n.face(0, 0, W, D, top_fill, top_deco)
    fw = n.face(0, -T, W, T, wall_fill, wall_deco)
    bw = n.face(0, D, W, T, wall_fill, wall_deco)
    lw = n.face(-T, 0, T, D, wall_fill, wall_deco)
    rw = n.face(W, 0, T, D, wall_fill, wall_deco)
    ct = min(0.6, T * 0.9)
    for f in (fw, bw):
        n.tab(f, "L", ct)
        n.tab(f, "R", ct)
    n.tab(fw, "B", 0.8)
    n.tab(bw, "T", 0.8)
    n.tab(lw, "L", 0.8)
    n.tab(rw, "R", 0.8)
    return n


# ================================================================ artwork
def monitor_back_l(c, x, y, w, h):
    black_panel(c, x, y, w, h)
    nw = NECK["W"] * cm
    gy, gh = NECK_GLUE
    c.setStrokeColor(MGRAY)
    c.setDash(3, 3)
    c.setLineWidth(0.8)
    c.rect(x + (w - nw) / 2, y + gy * cm, nw, gh * cm, fill=0, stroke=1)
    c.setDash()
    label(c, x + w / 2, y + (gy + gh / 2) * cm, "S1 neck", 7, MGRAY, "Helvetica")
    label(c, x + w / 2, y + (gy + gh / 2 - 0.5) * cm, "glue here", 7, MGRAY, "Helvetica")
    c.setFillColor(HexColor("#333333"))
    for i in range(14):
        c.rect(x + w * 0.22 + i * 0.95 * cm, y + h * 0.78, 0.5 * cm, 0.12 * cm, fill=1, stroke=0)
    c.setFillColor(HexColor("#2a2a2a"))
    c.roundRect(x + w * 0.38, y + h * 0.5, w * 0.24, h * 0.18, 6, fill=1, stroke=0)


def foot_top(c, x, y, w, h):
    black_panel(c, x, y, w, h)
    nw, nd = NECK["W"] * cm, NECK["D"] * cm
    c.setStrokeColor(MGRAY)
    c.setDash(3, 3)
    c.rect(x + (w - nw) / 2, y + h * 0.55, nw, nd, fill=0, stroke=1)
    c.setDash()
    label(c, x + w / 2, y + h * 0.55 - 0.45 * cm, "neck S1 here (back)", 6, MGRAY, "Helvetica")
    label(c, x + w / 2, y + 0.4 * cm, "FRONT", 6, MGRAY, "Helvetica")


def plain_dark(c, x, y, w, h):
    c.setFillColor(HexColor("#0f1a6b"))
    c.rect(x, y, w, h, fill=1, stroke=0)


def code_mark(text):
    """Bottom panels are hidden: print their code on them."""
    def f(c, x, y, w, h):
        plain_dark(c, x, y, w, h)
        label(c, x + w / 2, y + h / 2, text, 9, HexColor("#5568c8"))
        label(c, x + w / 2, y + h / 2 - 0.45 * cm, "(underside)", 6, HexColor("#5568c8"), "Helvetica")
    return f


def code_mark_black(text):
    def f(c, x, y, w, h):
        c.setFillColor(HexColor("#1a1a1a"))
        c.rect(x, y, w, h, fill=1, stroke=0)
        label(c, x + w / 2, y + h / 2 - 3, text, 8, HexColor("#666666"))
    return f


# ================================================================ pages
def p_instructions(c):
    pw, ph = A4
    c.setPageSize(A4)
    c.setFillColor(YELLOW)
    c.rect(0, ph - 3.0 * cm, pw, 3.0 * cm, fill=1, stroke=0)
    c.setFillColor(BLUE_D)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(1.2 * cm, ph - 1.6 * cm, "Desktop Computer Model - LARGE (50 x 50 cm)")
    c.setFillColor(BLACK)
    c.setFont("Helvetica", 9.5)
    c.drawString(1.2 * cm, ph - 2.4 * cm, "Closed 3D boxes, cut - fold - glue.  Every glue tab shows the piece code.")

    y = ph - 3.8 * cm

    def head(t):
        nonlocal y
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(BLUE_D)
        c.drawString(1.2 * cm, y, t)
        y -= 0.45 * cm
        c.setFont("Helvetica", 8.3)
        c.setFillColor(BLACK)

    def line(t, x=1.5):
        nonlocal y
        c.drawString(x * cm, y, t)
        y -= 0.38 * cm

    head("You need")
    line(u"•  Colour printer, 200-250 g/m2 card (or normal paper glued onto thin card)")
    line(u"•  Scissors / craft knife, metal ruler, empty pen to score folds, glue stick + white PVA glue")
    line(u"•  Base: cardboard or foam board 50 x 50 cm (5-10 mm thick)")
    y -= 0.15 * cm

    head("Pieces  (code - piece - file)")
    rows = [
        ("A1..C2", "Yellow base tiles (6)", "01_base"),
        ("E1..E8", "Black base edge strips", "01_base"),
        ("T1..T6", "PC tower: sides, front, back, top, bottom   9 x 16 x 20", "02_pc_tower"),
        ("M1, M2", "Monitor screen + back with top wall   24 x 15 x 1.2", "03_monitor"),
        ("M3, M4, M5", "Monitor bottom wall + 2 side walls", "07_small_parts"),
        ("S1, S2", "Stand neck + foot top", "04_monitor_stand"),
        ("S3", "Foot bottom", "07_small_parts"),
        ("L1, R1", "Speaker walls (left, right)   6 x 7 x 11", "05_speakers"),
        ("L2,L3,R2,R3", "Speaker tops + bottoms", "05_speakers"),
        ("K1 / K2", "Keyboard top+walls / bottom   22 x 7.5 x 1", "06_keyboard  /  07_small_parts"),
        ("U1 / U2", "Mouse top+walls / bottom   4.5 x 8 x 1.3", "07_small_parts"),
        ("X1, X2", "OPTIONAL RGB speaker fronts", "08_optional"),
    ]
    for code, name, f in rows:
        c.setFont("Helvetica-Bold", 8.3)
        c.drawString(1.5 * cm, y, code)
        c.setFont("Helvetica", 8.3)
        c.drawString(3.8 * cm, y, name)
        c.drawRightString(pw - 1.2 * cm, y, f)
        y -= 0.38 * cm
    y -= 0.15 * cm

    head("How to build")
    for t in [
        "1. Print at 100 %. Check the 5 cm ruler at the bottom of each page. Cut SOLID lines, score + fold DASHED lines.",
        "2. Grey tabs always go INSIDE. Fold every tab 90 deg first, put glue on the tab, then press the next panel on it.",
        "3. TOWER: fold all tabs of T1 + T2 (sides). Glue T3 (front) and T4 (back) between the sides, then T5 top, T6 bottom.",
        "4. SPEAKERS: close the wall strip L1 with its side tab, then glue L2 on top and L3 underneath (same for R).",
        "5. MONITOR: on M2 fold the top wall + its tabs. Glue M3 (bottom wall) and M4, M5 (side walls) to the back,",
        "   then glue the screen M1 on top of all the outer tabs. Keep it flat under a book while it dries.",
        "6. STAND: close neck S1, close foot S2 with bottom S3. Glue the neck into the foot, then the monitor onto the",
        "   neck's front face (dashed box on the monitor back).",
        "7. KEYBOARD / MOUSE: fold walls down, glue corner tabs, then glue K2 / U2 underneath.",
        "8. BASE: glue tiles on the board (A = left, C = right, row 1 = front). Wrap the black strips around the edges.",
        "9. Glue every part on its dotted outline. Big boxes stay firmer with crumpled paper or a card cross inside.",
    ]:
        line(t, 1.3)
    y -= 0.2 * cm

    head("Layout on the 50 x 50 cm base (top view)")
    sc = 0.17
    bx0, by0 = 1.5 * cm, y - BASE["D"] * sc * cm - 0.1 * cm
    c.setFillColor(YELLOW)
    c.setStrokeColor(black)
    c.rect(bx0, by0, BASE["W"] * sc * cm, BASE["D"] * sc * cm, fill=1, stroke=1)
    c.setStrokeColor(HexColor("#b39200"))
    c.setDash(1, 2)
    xx = 0
    for w in TILE_COLS[:-1]:
        xx += w
        c.line(bx0 + xx * sc * cm, by0, bx0 + xx * sc * cm, by0 + BASE["D"] * sc * cm)
    c.line(bx0, by0 + TILE_ROWS[0] * sc * cm, bx0 + BASE["W"] * sc * cm, by0 + TILE_ROWS[0] * sc * cm)
    c.setDash()
    for name, (fx, fy, fw, fd) in FOOTPRINTS.items():
        c.setFillColor(BLACK if "Monitor" in name else BLUE)
        c.rect(bx0 + fx * sc * cm, by0 + fy * sc * cm, fw * sc * cm, fd * sc * cm, fill=1, stroke=0)
    # screen outline
    c.setFillColor(DGRAY)
    c.rect(bx0 + 10 * sc * cm, by0 + 26.3 * sc * cm, MON["W"] * sc * cm, MON["T"] * sc * cm, fill=1, stroke=0)
    c.setFillColor(BLACK)
    c.setFont("Helvetica", 7)
    tx = bx0 + BASE["W"] * sc * cm + 0.6 * cm
    ty = by0 + BASE["D"] * sc * cm - 0.3 * cm
    for t in ["Tiles: A B C = left to right,", "row 1 = front, row 2 = back.", "",
              "Back right: tower", "Middle: monitor on stand", "Left + right: speakers",
              "Front: keyboard + mouse", "", "Front edge = bottom of the drawing."]:
        c.drawString(tx, ty, t)
        ty -= 0.35 * cm
    c.setFont("Helvetica", 6.5)
    c.setFillColor(HexColor("#666666"))
    c.drawString(1.2 * cm, 0.6 * cm, PRINT_NOTE)


def p_base_tile(c, col, row):
    c.setPageSize(A4)
    pw, ph = A4
    W, D = TILE_COLS[col], TILE_ROWS[row]
    x0 = sum(TILE_COLS[:col])
    y0 = sum(TILE_ROWS[:row])
    ox, oy = (pw / cm - W) / 2, 1.6
    code = "ABC"[col] + str(row + 1)
    c.setFillColor(YELLOW)
    c.rect(ox * cm, oy * cm, W * cm, D * cm, fill=1, stroke=0)
    c.saveState()
    p = c.beginPath()
    p.rect(ox * cm, oy * cm, W * cm, D * cm)
    c.clipPath(p, stroke=0, fill=0)
    for name, (fx, fy, fw, fd) in FOOTPRINTS.items():
        X, Y = (ox + fx - x0) * cm, (oy + fy - y0) * cm
        c.setStrokeColor(HexColor("#b39200"))
        c.setDash(1, 2)
        c.setLineWidth(0.8)
        c.rect(X, Y, fw * cm, fd * cm, fill=0, stroke=1)
        c.setDash()
        c.setFillColor(HexColor("#b39200"))
        c.setFont("Helvetica", 8)
        c.drawCentredString(X + fw * cm / 2, Y + fd * cm / 2, name)
    # small tile code in the corner (gets covered / is very light)
    c.setFillColor(HexColor("#e9c400"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString((ox + 0.3) * cm, (oy + 0.3) * cm, code)
    c.restoreState()
    c.setStrokeColor(black)
    c.setLineWidth(0.8)
    c.rect(ox * cm, oy * cm, W * cm, D * cm, fill=0, stroke=1)
    c.setFillColor(BLUE_D)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1.0 * cm, ph - 1.0 * cm, "01  BASE TILE %s  (%g x %g cm)" % (code, W, D))
    nb = []
    if col > 0:
        nb.append("left edge -> %s%d" % ("ABC"[col - 1], row + 1))
    if col < 2:
        nb.append("right edge -> %s%d" % ("ABC"[col + 1], row + 1))
    nb.append("top edge -> %s2" % "ABC"[col] if row == 0 else "bottom edge -> %s1" % "ABC"[col])
    c.setFont("Helvetica", 7.5)
    c.setFillColor(HexColor("#444444"))
    c.drawString(1.0 * cm, ph - 1.45 * cm, "Cut on the black line, glue on the 50 x 50 board. Joins: " + ",  ".join(nb)
                 + ".  Bottom of page = front.")
    c.setFont("Helvetica", 6.5)
    c.drawString(1.0 * cm, 0.6 * cm, PRINT_NOTE)


def p_edge_strips(c):
    size_ = landscape(A4)
    c.setPageSize(size_)
    pw, ph = size_
    page_header(c, pw, ph, "01  BASE EDGE STRIPS  E1-E8",
                ["8 strips x 25 cm = 2 per edge (4 edges x 50 cm). Score the dashed line, wrap the strip around the",
                 "board edge: the narrow part goes under the board. Trim if your board is thinner."])
    L, Wd = 25.0, 1.8
    for i in range(8):
        x, y = 1.0 + (i % 1) * 0, 2.3 + i * 2.2
        x = (pw / cm - L) / 2
        c.setFillColor(BLACK)
        c.rect(x * cm, y * cm, L * cm, Wd * cm, fill=1, stroke=0)
        c.setStrokeColor(black)
        c.setLineWidth(0.8)
        c.rect(x * cm, y * cm, L * cm, Wd * cm, fill=0, stroke=1)
        c.setStrokeColor(MGRAY)
        c.setDash(3, 2)
        c.line(x * cm, (y + 0.6) * cm, (x + L) * cm, (y + 0.6) * cm)
        c.setDash()
        c.setFillColor(HexColor("#555555"))
        c.setFont("Helvetica", 6)
        c.drawString((x + 0.2) * cm, (y + 0.2) * cm, "E%d" % (i + 1))


def p_tower_sides(c, which):
    c.setPageSize(A4)
    pw, ph = A4
    W, D, H = TOWER["W"], TOWER["D"], TOWER["H"]
    code = "T1" if which == "R" else "T2"
    n = panel(code, D, H, BLUE, tower_side, tabs="LRTB")
    side = "RIGHT" if which == "R" else "LEFT"
    page_header(c, pw, ph, "02  PC TOWER - %s SIDE  (%s)" % (side, code),
                ["%g x %g cm. Fold all 4 tabs inward. %s" % (D, H,
                 "LEFT edge (on paper) meets the FRONT T3, right edge meets the BACK T4." if which == "R" else
                 "LEFT edge (on paper) meets the BACK T4, right edge meets the FRONT T3."),
                 "Top edge of the page = top of the tower.", PRINT_NOTE])
    w, h = size(n)
    piece_title(c, n, (pw / cm - w) / 2, 2.0, code + "  tower %s side" % side.lower())


def p_tower_front_back(c):
    c.setPageSize(A4)
    pw, ph = A4
    W, H = TOWER["W"], TOWER["H"]
    f = panel("T3", W, H, BLUE, scaled(tower_front, 6), tabs="TB")
    b = panel("T4", W, H, DGRAY, scaled(tower_back, 6), tabs="TB")
    page_header(c, pw, ph, "02  PC TOWER - FRONT (T3) + BACK (T4)",
                ["%g x %g cm each. Their top/bottom tabs go under the top T5 and bottom T6." % (W, H),
                 "Glue them onto the side tabs of T1 and T2.", PRINT_NOTE])
    w, h = size(f)
    gap = 0.8
    x0 = (pw / cm - 2 * w - gap) / 2
    piece_title(c, f, x0, 2.0, "T3 front")
    piece_title(c, b, x0 + w + gap, 2.0, "T4 back (ports)")


def p_tower_lids(c):
    c.setPageSize(A4)
    pw, ph = A4
    W, D = TOWER["W"], TOWER["D"]

    def top_art(c2, x, y, w, h):
        blue_panel(c2, x, y, w, h)
        c2.setFillColor(BLUE_D)
        for i in range(8):
            c2.rect(x + w * 0.2, y + h * 0.55 + i * 0.35 * cm, w * 0.6, 0.12 * cm, fill=1, stroke=0)
        label(c2, x + w / 2, y + 0.4 * cm, "front edge", 6, HexColor("#8fa2ff"), "Helvetica")

    t = panel("T5", W, D, BLUE, top_art)
    b = panel("T6", W, D, BLUE_D, code_mark("T6"))
    page_header(c, pw, ph, "02  PC TOWER - TOP (T5) + BOTTOM (T6)",
                ["%g x %g cm each. Glue last, onto the tabs of T1-T4." % (W, D),
                 "Tip: before closing, put crumpled paper or a cardboard cross inside the tower.", PRINT_NOTE])
    gap = 0.8
    x0 = (pw / cm - 2 * W - gap) / 2
    piece_title(c, t, x0, 4.0, "T5 top")
    piece_title(c, b, x0 + W + gap, 4.0, "T6 bottom")


def p_monitor_front(c):
    sz = landscape(A4)
    c.setPageSize(sz)
    pw, ph = sz
    n = panel("M1", MON["W"], MON["H"], BLACK, scaled(monitor_front, 16))
    page_header(c, pw, ph, "03  MONITOR - SCREEN  (M1)",
                ["%g x %g cm. Glue LAST, onto the outer tabs of M2, M3, M4, M5." % (MON["W"], MON["H"]),
                 PRINT_NOTE])
    w, h = size(n)
    piece_title(c, n, (pw / cm - w) / 2, 1.6, "M1 screen")


def p_monitor_back(c):
    sz = landscape(A4)
    c.setPageSize(sz)
    pw, ph = sz
    W, H, T = MON["W"], MON["H"], MON["T"]
    n = Net("M2")
    n.face(0, 0, W, H, BLACK, monitor_back_l)
    tw = n.face(0, H, W, T, BLACK, black_panel)
    n.tab(tw, "L", 0.7), n.tab(tw, "R", 0.7), n.tab(tw, "T", 0.8)
    page_header(c, pw, ph, "03  MONITOR - BACK + TOP WALL  (M2)",
                ["Fold the top wall up 90 deg. Its end tabs glue inside the side walls M4/M5, its long tab under the screen M1.",
                 "Bottom wall M3 and side walls M4, M5 are in 07_small_parts."])
    w, h = size(n)
    piece_title(c, n, (pw / cm - w) / 2, 1.3, "M2 monitor back")


def p_stand(c):
    c.setPageSize(A4)
    pw, ph = A4
    from make_papercraft import box_strip
    neck = box_strip(NECK["W"], NECK["D"], NECK["H"], black_panel, black_panel, black_panel, black_panel,
                     black_panel, black_panel,
                     fills={k: BLACK for k in ["front", "right", "back", "left", "top", "bottom"]})
    neck.code = "S1"
    foot = closed_tray("S2", FOOT["W"], FOOT["D"], FOOT["T"], foot_top, BLACK, BLACK, black_panel)
    page_header(c, pw, ph, "04  MONITOR STAND - NECK (S1) + FOOT (S2)",
                ["Neck %g x %g x %g cm (closed box). Foot %g x %g x %g cm, closed with S3 (in 07_small_parts)."
                 % (NECK["W"], NECK["D"], NECK["H"], FOOT["W"], FOOT["D"], FOOT["T"]),
                 "A wooden lolly stick or rolled card inside the neck makes it strong.", PRINT_NOTE])
    w1, h1 = size(neck)
    w2, h2 = size(foot)
    piece_title(c, neck, (pw / cm - w1) / 2, 12.4, "S1 neck")
    piece_title(c, foot, (pw / cm - w2) / 2, 1.6, "S2 foot (top + walls)")


def p_speaker(c, side):
    sz = landscape(A4)
    c.setPageSize(sz)
    pw, ph = sz
    W, D, H = SPK["W"], SPK["D"], SPK["H"]
    code = "L1" if side == "LEFT" else "R1"
    n = walls_strip(code, W, D, H,
                    [scaled(speaker_front, 4), blue_panel, scaled(speaker_back, 4), blue_panel],
                    [BLUE] * 4)
    page_header(c, pw, ph, "05  SPEAKER %s - WALLS  (%s)" % (side, code),
                ["Front | right | back | left. Glue the end tab inside the front edge to make a tube,",
                 "then glue top %s2 and bottom %s3 onto the small tabs." % (code[0], code[0]), PRINT_NOTE])
    w, h = size(n)
    piece_title(c, n, (pw / cm - w) / 2, 2.0, "%s speaker %s" % (code, side.lower()))


def p_speaker_lids(c):
    c.setPageSize(A4)
    pw, ph = A4
    W, D = SPK["W"], SPK["D"]

    def top_art(c2, x, y, w, h):
        blue_panel(c2, x, y, w, h)
        label(c2, x + w / 2, y + 0.35 * cm, "front edge", 6, HexColor("#8fa2ff"), "Helvetica")

    page_header(c, pw, ph, "05  SPEAKER TOPS + BOTTOMS  (L2, L3, R2, R3)",
                ["%g x %g cm each. Glue onto the tabs of the speaker tubes L1 / R1." % (W, D), PRINT_NOTE])
    items = [("L2", "left top", BLUE, top_art), ("L3", "left bottom", BLUE_D, code_mark("L3")),
             ("R2", "right top", BLUE, top_art), ("R3", "right bottom", BLUE_D, code_mark("R3"))]
    gap = 2.0
    x0 = (pw / cm - 2 * W - gap) / 2
    for i, (cd, nm, fill, art) in enumerate(items):
        n = panel(cd, W, D, fill, art)
        piece_title(c, n, x0 + (i % 2) * (W + gap), 15.0 - (i // 2) * (D + 2.0), cd + " " + nm)


def p_keyboard(c):
    sz = landscape(A4)
    c.setPageSize(sz)
    pw, ph = sz
    n = closed_tray("K1", KB["W"], KB["D"], KB["T"], scaled(keyboard_top, 14), BLUE, BLUE_D, blue_panel)
    page_header(c, pw, ph, "06  KEYBOARD - TOP + WALLS  (K1)",
                ["%g x %g x %g cm. Fold walls down, glue the 4 corner tabs, then glue the bottom K2 (07_small_parts)"
                 % (KB["W"], KB["D"], KB["T"]) + " onto the outer tabs.", PRINT_NOTE])
    w, h = size(n)
    piece_title(c, n, (pw / cm - w) / 2, 4.0, "K1 keyboard")


def p_bottoms(c):
    sz = landscape(A4)
    c.setPageSize(sz)
    pw, ph = sz
    page_header(c, pw, ph, "07  SMALL PARTS 1 - BOTTOM PANELS  (K2, U2, S3)",
                ["These close the keyboard, mouse and stand foot from underneath (they will not be seen).", PRINT_NOTE])
    k2 = panel("K2", KB["W"], KB["D"], BLUE_D, code_mark("K2 keyboard"))
    u2 = panel("U2", MOUSE["W"], MOUSE["D"], BLUE_D, code_mark("U2"))
    s3 = panel("S3", FOOT["W"], FOOT["D"], BLACK, code_mark_black("S3 foot"))
    x0 = (pw / cm - KB["W"] - 1.0 - MOUSE["W"]) / 2
    piece_title(c, k2, x0, 11.0, "K2 keyboard bottom")
    piece_title(c, u2, x0 + KB["W"] + 1.0, 10.5, "U2 mouse bottom")
    piece_title(c, s3, x0, 2.0, "S3 stand foot bottom")


def p_small2(c):
    c.setPageSize(A4)
    pw, ph = A4
    page_header(c, pw, ph, "07  SMALL PARTS 2 - MOUSE (U1) + MONITOR WALLS (M3, M4, M5)",
                ["U1: fold walls down, glue corner tabs, close with U2.  M3 = monitor bottom wall (24 cm),",
                 "M4 / M5 = monitor side walls (15 cm). One long tab glues inside the back M2, the other under the screen M1."])
    W, H, T = MON["W"], MON["H"], MON["T"]
    m3 = Net("M3")
    f = m3.face(0, 0, T, W, BLACK, black_panel)
    for s in "LRTB":
        m3.tab(f, s, 0.7 if s in "TB" else 0.8)
    m4 = panel("M4", T, H, BLACK, black_panel, tabs="LR")
    m5 = panel("M5", T, H, BLACK, black_panel, tabs="LR")
    for n in (m4, m5):
        for t in range(len(n.tabs)):
            n.tabs[t] = (n.tabs[t][0], n.tabs[t][1], 0.8)
    u1 = closed_tray("U1", MOUSE["W"], MOUSE["D"], MOUSE["T"], scaled(mouse_top, 3.2), BLUE, BLUE_D, blue_panel)
    piece_title(c, m3, 1.2, 1.3, "M3")
    piece_title(c, m4, 5.0, 11.0, "M4")
    piece_title(c, m5, 8.6, 11.0, "M5")
    wu, hu = size(u1)
    piece_title(c, u1, 12.0, 12.0, "U1 mouse")


def p_rgb(c):
    c.setPageSize(A4)
    pw, ph = A4
    page_header(c, pw, ph, "08  OPTIONAL - RGB SPEAKER FRONTS  (X1, X2)",
                ["Style of the 3rd photo. Cut and glue over the speaker fronts (exactly %g x %g cm)." % (SPK["W"], SPK["H"]),
                 PRINT_NOTE])
    for i in range(2):
        X = (pw / cm / 2 - SPK["W"] - 1 + i * (SPK["W"] + 2)) * cm
        Y = 10 * cm
        c.saveState()
        scaled(speaker_front_rgb, 4)(c, X, Y, SPK["W"] * cm, SPK["H"] * cm)
        c.restoreState()
        c.setStrokeColor(black)
        c.setLineWidth(0.8)
        c.rect(X, Y, SPK["W"] * cm, SPK["H"] * cm, fill=0, stroke=1)
        label(c, X + SPK["W"] * cm / 2, Y - 0.5 * cm, ["X1 left", "X2 right"][i], 8, BLUE_D)


FILES = [
    ("00_instructions", [p_instructions]),
    ("01_base", [lambda c, i=i, j=j: p_base_tile(c, i, j) for j in range(2) for i in range(3)] + [p_edge_strips]),
    ("02_pc_tower", [lambda c: p_tower_sides(c, "R"), lambda c: p_tower_sides(c, "L"),
                     p_tower_front_back, p_tower_lids]),
    ("03_monitor", [p_monitor_front, p_monitor_back]),
    ("04_monitor_stand", [p_stand]),
    ("05_speakers", [lambda c: p_speaker(c, "LEFT"), lambda c: p_speaker(c, "RIGHT"), p_speaker_lids]),
    ("06_keyboard", [p_keyboard]),
    ("07_small_parts", [p_bottoms, p_small2]),
    ("08_optional_rgb_speaker_fronts", [p_rgb]),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    allc = canvas.Canvas(os.path.join(OUT, "ALL_PARTS_LARGE.pdf"), pagesize=A4)
    allc.setTitle("Desktop Computer Papercraft - LARGE 50x50 cm")
    for name, fns in FILES:
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
