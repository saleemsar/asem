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
    black_panel, label, TAB as _TAB,
)
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont("Ar", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("ArB", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))


def A(t):
    """Shape + reorder Arabic text so the PDF shows it right-to-left."""
    return get_display(arabic_reshaper.reshape(t), base_dir="R")


def label_ar(c, x, y, txt, size=6, color=None, bold=False):
    c.setFillColor(color if color is not None else MGRAY)
    c.setFont("ArB" if bold else "Ar", size)
    c.drawCentredString(x, y, A(txt))


def page_header(c, pw, ph, title, info):
    """Arabic page header (right aligned) + legend and 5 cm scale ruler."""
    c.setFillColor(BLUE_D)
    c.setFont("ArB", 12.5)
    c.drawRightString(pw - 1.0 * cm, ph - 1.0 * cm, A(title))
    c.setFillColor(HexColor("#444444"))
    c.setFont("Ar", 7.5)
    yy = ph - 1.5 * cm
    for line in info:
        c.drawRightString(pw - 1.0 * cm, yy, A(line))
        yy -= 0.36 * cm
    y0 = 0.55 * cm
    c.setFont("Ar", 6.5)
    c.setStrokeColor(black)
    c.setLineWidth(0.8)
    c.setDash()
    c.line(pw - 1.8 * cm, y0, pw - 1.0 * cm, y0)
    c.setFillColor(black)
    c.drawRightString(pw - 1.95 * cm, y0 - 2, A("قص"))
    c.setDash(3, 2)
    c.setStrokeColor(HexColor("#555555"))
    c.line(pw - 3.3 * cm, y0, pw - 2.5 * cm, y0)
    c.setDash()
    c.drawRightString(pw - 3.45 * cm, y0 - 2, A("طي (اضغط الخط أولاً)"))
    c.setFillColor(_TAB)
    c.rect(pw - 6.6 * cm, y0 - 0.12 * cm, 0.5 * cm, 0.25 * cm, fill=1, stroke=1)
    c.setFillColor(black)
    c.drawRightString(pw - 6.75 * cm, y0 - 2, A("لسان لصق"))
    rx = 1.0 * cm
    c.setLineWidth(0.6)
    c.line(rx, y0, rx + 5 * cm, y0)
    for i in range(6):
        c.line(rx + i * cm, y0, rx + i * cm, y0 + 0.18 * cm)
    c.drawString(rx + 5.15 * cm, y0 - 2, A("= 5 سم (تحقق من المقاس)"))

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

PRINT_NOTE = ("اطبع بحجم 100% (الحجم الفعلي) وليس «ملاءمة للصفحة». "
              "الأفضل ورق مقوى 200-250 غ/م2، أو الصق الطبعة على كرتون رقيق.")
FP_AR = {"Speaker L": "سماعة يسار", "Monitor foot": "قاعدة الشاشة", "Speaker R": "سماعة يمين",
         "Tower": "الكيس", "Keyboard": "لوحة المفاتيح", "Mouse": "الماوس"}
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
    c.setFont("ArB", 8)
    c.drawString(ox * cm, (oy + (y1 - y0) + 0.25) * cm, A(text))


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
    label_ar(c, x + w / 2, y + (gy + gh / 2) * cm, "الرقبة S1", 7)
    label_ar(c, x + w / 2, y + (gy + gh / 2 - 0.5) * cm, "الصق هنا", 7)
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
    label_ar(c, x + w / 2, y + h * 0.55 - 0.45 * cm, "الرقبة S1 هنا (الخلف)", 6)
    label_ar(c, x + w / 2, y + 0.4 * cm, "الأمام", 6)


def plain_dark(c, x, y, w, h):
    c.setFillColor(HexColor("#0f1a6b"))
    c.rect(x, y, w, h, fill=1, stroke=0)


def code_mark(text):
    """Bottom panels are hidden: print their code on them."""
    def f(c, x, y, w, h):
        plain_dark(c, x, y, w, h)
        label(c, x + w / 2, y + h / 2, text, 9, HexColor("#5568c8"))
        label_ar(c, x + w / 2, y + h / 2 - 0.45 * cm, "(الجهة السفلية)", 6, HexColor("#5568c8"))
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
    R = pw - 1.2 * cm
    c.setFillColor(YELLOW)
    c.rect(0, ph - 3.0 * cm, pw, 3.0 * cm, fill=1, stroke=0)
    c.setFillColor(BLUE_D)
    c.setFont("ArB", 19)
    c.drawRightString(R, ph - 1.6 * cm, A("مجسم كمبيوتر مكتبي - الحجم الكبير (50 × 50 سم)"))
    c.setFillColor(BLACK)
    c.setFont("Ar", 9.5)
    c.drawRightString(R, ph - 2.4 * cm, A("صناديق ثلاثية الأبعاد مغلقة: قص - اطوِ - الصق. كل لسان لصق مكتوب عليه رمز القطعة."))

    y = ph - 3.8 * cm

    def head(t):
        nonlocal y
        c.setFont("ArB", 11)
        c.setFillColor(BLUE_D)
        c.drawRightString(R, y, A(t))
        y -= 0.48 * cm
        c.setFont("Ar", 8.2)
        c.setFillColor(BLACK)

    def line(t, indent=0.3):
        nonlocal y
        c.drawRightString(R - indent * cm, y, A(t))
        y -= 0.4 * cm

    head("ماذا تحتاج")
    line("•  طابعة ملونة، ورق مقوى 200-250 غ/م2 (أو ورق عادي ملصوق على كرتون رقيق)")
    line("•  مقص أو مشرط، مسطرة معدنية، قلم فارغ لتعليم خطوط الطي، صمغ أصابع + غراء أبيض")
    line("•  القاعدة: كرتون أو لوح فوم مقاس 50 × 50 سم (سماكة 5-10 مم)")
    y -= 0.15 * cm

    head("القطع  (الرمز - القطعة - الملف)")
    rows = [
        ("A1..C2", "بلاطات القاعدة الصفراء (6 قطع)", "01_base"),
        ("E1..E8", "أشرطة حواف القاعدة السوداء", "01_base"),
        ("T1..T6", "الكيس: جانبان، أمام، خلف، أعلى، أسفل   9 × 16 × 20", "02_pc_tower"),
        ("M1, M2", "واجهة الشاشة + ظهر الشاشة مع الجدار العلوي   24 × 15 × 1.2", "03_monitor"),
        ("M3, M4, M5", "الجدار السفلي للشاشة + الجداران الجانبيان", "07_small_parts"),
        ("S1, S2", "رقبة الحامل + أعلى قاعدة الحامل", "04_monitor_stand"),
        ("S3", "أسفل قاعدة الحامل", "07_small_parts"),
        ("L1, R1", "جدران السماعات (يسار، يمين)   6 × 7 × 11", "05_speakers"),
        ("L2, L3, R2, R3", "الأغطية العلوية والسفلية للسماعات", "05_speakers"),
        ("K1 / K2", "لوحة المفاتيح: الأعلى مع الجدران / الأسفل   22 × 7.5 × 1", "06_keyboard / 07_small_parts"),
        ("U1 / U2", "الماوس: الأعلى مع الجدران / الأسفل   4.5 × 8 × 1.3", "07_small_parts"),
        ("X1, X2", "اختياري: واجهات سماعات بإضاءة RGB", "08_optional"),
    ]
    for code, name, f in rows:
        c.setFont("Helvetica-Bold", 8.2)
        c.drawRightString(R - 0.3 * cm, y, code)
        c.setFont("Ar", 8.2)
        c.drawRightString(R - 3.0 * cm, y, A(name))
        c.setFont("Helvetica", 7.5)
        c.drawString(1.2 * cm, y, f)
        y -= 0.4 * cm
    y -= 0.15 * cm

    head("طريقة التركيب")
    for t in [
        "1. اطبع بحجم 100%. تحقق من مسطرة 5 سم أسفل كل صفحة. قص على الخطوط المتصلة، واضغط ثم اطوِ الخطوط المتقطعة.",
        "2. الألسنة الرمادية دائماً إلى الداخل. اطوِ كل لسان 90 درجة أولاً، ضع الصمغ على اللسان ثم اضغط القطعة التالية عليه.",
        "3. الكيس: اطوِ كل ألسنة T1 و T2 (الجانبين). الصق T3 (الأمام) و T4 (الخلف) بين الجانبين، ثم T5 الأعلى و T6 الأسفل.",
        "4. السماعات: اصنع أنبوباً من الجدران L1 باستخدام اللسان الجانبي، ثم الصق L2 في الأعلى و L3 في الأسفل (ونفس الشيء لـ R).",
        "5. الشاشة: في القطعة M2 اطوِ الجدار العلوي وألسنته. الصق M3 (الجدار السفلي) و M4 و M5 (الجدارين الجانبيين) بالظهر،",
        "    ثم الصق الواجهة M1 فوق كل الألسنة الخارجية. ضع كتاباً فوقها حتى يجف الغراء.",
        "6. الحامل: أغلق الرقبة S1، وأغلق القاعدة S2 بالقطعة S3. الصق الرقبة في القاعدة، ثم الصق الشاشة على",
        "    الوجه الأمامي للرقبة (المربع المتقطع على ظهر الشاشة).",
        "7. لوحة المفاتيح والماوس: اطوِ الجدران للأسفل، الصق ألسنة الزوايا، ثم الصق K2 و U2 من الأسفل.",
        "8. القاعدة: الصق البلاطات على اللوح (A يسار، C يمين، الصف 1 = الأمام). لُف الأشرطة السوداء حول الحواف.",
        "9. الصق كل قطعة على حدودها المنقطة. الصناديق الكبيرة تبقى أقوى بوضع ورق مجعد أو كرتون متقاطع داخلها.",
    ]:
        line(t, 0.1)
    y -= 0.2 * cm

    head("توزيع القطع على القاعدة 50 × 50 سم (منظر من الأعلى)")
    sc = 0.17
    bx0, by0 = pw - 1.5 * cm - BASE["W"] * sc * cm, y - BASE["D"] * sc * cm - 0.1 * cm
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
        c.setFillColor(BLACK if name == "Monitor foot" else BLUE)
        c.rect(bx0 + fx * sc * cm, by0 + fy * sc * cm, fw * sc * cm, fd * sc * cm, fill=1, stroke=0)
    c.setFillColor(DGRAY)
    c.rect(bx0 + 10 * sc * cm, by0 + 26.3 * sc * cm, MON["W"] * sc * cm, MON["T"] * sc * cm, fill=1, stroke=0)
    c.setFillColor(BLACK)
    c.setFont("Ar", 7.5)
    tx = bx0 - 0.6 * cm
    ty = by0 + BASE["D"] * sc * cm - 0.3 * cm
    for t in ["البلاطات: A B C = من اليسار إلى اليمين،", "الصف 1 = الأمام، الصف 2 = الخلف.", "",
              "الخلف يميناً: الكيس", "في الوسط: الشاشة على الحامل", "يساراً ويميناً: السماعات",
              "في الأمام: لوحة المفاتيح والماوس", "", "الحافة الأمامية = أسفل الرسم."]:
        if t:
            c.drawRightString(tx, ty, A(t))
        ty -= 0.38 * cm
    c.setFont("Ar", 6.5)
    c.setFillColor(HexColor("#666666"))
    c.drawRightString(R, 0.6 * cm, A(PRINT_NOTE))


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
        c.setFont("Ar", 8)
        c.drawCentredString(X + fw * cm / 2, Y + fd * cm / 2, A(FP_AR[name]))
    # small tile code in the corner (gets covered / is very light)
    c.setFillColor(HexColor("#e9c400"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString((ox + 0.3) * cm, (oy + 0.3) * cm, code)
    c.restoreState()
    c.setStrokeColor(black)
    c.setLineWidth(0.8)
    c.rect(ox * cm, oy * cm, W * cm, D * cm, fill=0, stroke=1)
    nb = []
    if col > 0:
        nb.append("الحافة اليسرى: %s%d" % ("ABC"[col - 1], row + 1))
    if col < 2:
        nb.append("الحافة اليمنى: %s%d" % ("ABC"[col + 1], row + 1))
    nb.append("الحافة العليا: %s2" % "ABC"[col] if row == 0 else "الحافة السفلى: %s1" % "ABC"[col])
    c.setFillColor(BLUE_D)
    c.setFont("ArB", 12)
    c.drawRightString(pw - 1.0 * cm, ph - 1.0 * cm, A("01  بلاطة القاعدة رقم %s - المقاس %g × %g سم" % (code, W, D)))
    c.setFont("Ar", 7.5)
    c.setFillColor(HexColor("#444444"))
    c.drawRightString(pw - 1.0 * cm, ph - 1.45 * cm,
                      A("قص على الخط الأسود والصقها على اللوح 50 × 50. تتصل بـ:  " + "،  ".join(nb)))
    c.drawRightString(pw - 1.0 * cm, ph - 1.85 * cm, A("أسفل الصفحة = الأمام."))
    c.setFont("Ar", 6.5)
    c.drawRightString(pw - 1.0 * cm, 0.6 * cm, A(PRINT_NOTE))


def p_edge_strips(c):
    size_ = landscape(A4)
    c.setPageSize(size_)
    pw, ph = size_
    page_header(c, pw, ph, "01  أشرطة حواف القاعدة  E1-E8",
                ["8 أشرطة × 25 سم = شريطان لكل حافة (4 حواف × 50 سم). اضغط الخط المتقطع ولُف الشريط حول حافة اللوح:",
                 "الجزء الضيق يذهب تحت اللوح. قص الزائد إذا كان لوحك أرق."])
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
    side = "الأيمن" if which == "R" else "الأيسر"
    page_header(c, pw, ph, "02  الكيس - الجانب %s  (%s)" % (side, code),
                ["%g × %g سم. اطوِ الألسنة الأربعة إلى الداخل." % (D, H),
                 "الحافة اليسرى (على الورقة) تلتقي بالأمام T3، والحافة اليمنى بالخلف T4." if which == "R" else
                 "الحافة اليسرى (على الورقة) تلتقي بالخلف T4، والحافة اليمنى بالأمام T3.",
                 "أعلى الصفحة = أعلى الكيس.", PRINT_NOTE])
    w, h = size(n)
    piece_title(c, n, (pw / cm - w) / 2, 2.0, code + "  الجانب " + side)


def p_tower_front_back(c):
    c.setPageSize(A4)
    pw, ph = A4
    W, H = TOWER["W"], TOWER["H"]
    f = panel("T3", W, H, BLUE, scaled(tower_front, 6), tabs="TB")
    b = panel("T4", W, H, DGRAY, scaled(tower_back, 6), tabs="TB")
    page_header(c, pw, ph, "02  الكيس - الأمام (T3) + الخلف (T4)",
                ["%g × %g سم لكل قطعة. ألسنتها العلوية والسفلية تذهب تحت الأعلى T5 والأسفل T6." % (W, H),
                 "الصقها على الألسنة الجانبية للقطعتين T1 و T2.", PRINT_NOTE])
    w, h = size(f)
    gap = 0.8
    x0 = (pw / cm - 2 * w - gap) / 2
    piece_title(c, f, x0, 2.0, "T3 الأمام")
    piece_title(c, b, x0 + w + gap, 2.0, "T4 الخلف (المنافذ)")


def p_tower_lids(c):
    c.setPageSize(A4)
    pw, ph = A4
    W, D = TOWER["W"], TOWER["D"]

    def top_art(c2, x, y, w, h):
        blue_panel(c2, x, y, w, h)
        c2.setFillColor(BLUE_D)
        for i in range(8):
            c2.rect(x + w * 0.2, y + h * 0.55 + i * 0.35 * cm, w * 0.6, 0.12 * cm, fill=1, stroke=0)
        label_ar(c2, x + w / 2, y + 0.4 * cm, "الحافة الأمامية", 6, HexColor("#8fa2ff"))

    t = panel("T5", W, D, BLUE, top_art)
    b = panel("T6", W, D, BLUE_D, code_mark("T6"))
    page_header(c, pw, ph, "02  الكيس - الأعلى (T5) + الأسفل (T6)",
                ["%g × %g سم لكل قطعة. تُلصق في النهاية على ألسنة T1 إلى T4." % (W, D),
                 "نصيحة: قبل الإغلاق ضع ورقاً مجعداً أو كرتوناً متقاطعاً داخل الكيس.", PRINT_NOTE])
    gap = 0.8
    x0 = (pw / cm - 2 * W - gap) / 2
    piece_title(c, t, x0, 4.0, "T5 الأعلى")
    piece_title(c, b, x0 + W + gap, 4.0, "T6 الأسفل")


def p_monitor_front(c):
    sz = landscape(A4)
    c.setPageSize(sz)
    pw, ph = sz
    n = panel("M1", MON["W"], MON["H"], BLACK, scaled(monitor_front, 16))
    page_header(c, pw, ph, "03  الشاشة - الواجهة  (M1)",
                ["%g × %g سم. تُلصق في النهاية على الألسنة الخارجية للقطع M2 و M3 و M4 و M5." % (MON["W"], MON["H"]),
                 PRINT_NOTE])
    w, h = size(n)
    piece_title(c, n, (pw / cm - w) / 2, 1.6, "M1 واجهة الشاشة")


def p_monitor_back(c):
    sz = landscape(A4)
    c.setPageSize(sz)
    pw, ph = sz
    W, H, T = MON["W"], MON["H"], MON["T"]
    n = Net("M2")
    n.face(0, 0, W, H, BLACK, monitor_back_l)
    tw = n.face(0, H, W, T, BLACK, black_panel)
    n.tab(tw, "L", 0.7), n.tab(tw, "R", 0.7), n.tab(tw, "T", 0.8)
    page_header(c, pw, ph, "03  الشاشة - الظهر + الجدار العلوي  (M2)",
                ["اطوِ الجدار العلوي 90 درجة. لسانا طرفيه يُلصقان داخل الجدارين M4 و M5، ولسانه الطويل تحت الواجهة M1.",
                 "الجدار السفلي M3 والجداران الجانبيان M4 و M5 موجودة في الملف رقم 07."])
    w, h = size(n)
    piece_title(c, n, (pw / cm - w) / 2, 1.3, "M2 ظهر الشاشة")


def p_stand(c):
    c.setPageSize(A4)
    pw, ph = A4
    from make_papercraft import box_strip
    neck = box_strip(NECK["W"], NECK["D"], NECK["H"], black_panel, black_panel, black_panel, black_panel,
                     black_panel, black_panel,
                     fills={k: BLACK for k in ["front", "right", "back", "left", "top", "bottom"]})
    neck.code = "S1"
    foot = closed_tray("S2", FOOT["W"], FOOT["D"], FOOT["T"], foot_top, BLACK, BLACK, black_panel)
    page_header(c, pw, ph, "04  حامل الشاشة - الرقبة (S1) + القاعدة (S2)",
                ["الرقبة %g × %g × %g سم (صندوق مغلق). القاعدة %g × %g × %g سم، وتُغلق بالقطعة S3 (في الملف رقم 07)."
                 % (NECK["W"], NECK["D"], NECK["H"], FOOT["W"], FOOT["D"], FOOT["T"]),
                 "عود خشبي أو كرتون ملفوف داخل الرقبة يجعلها قوية.", PRINT_NOTE])
    w1, h1 = size(neck)
    w2, h2 = size(foot)
    piece_title(c, neck, (pw / cm - w1) / 2, 12.4, "S1 الرقبة")
    piece_title(c, foot, (pw / cm - w2) / 2, 1.6, "S2 القاعدة (الأعلى + الجدران)")


def p_speaker(c, side):
    sz = landscape(A4)
    c.setPageSize(sz)
    pw, ph = sz
    W, D, H = SPK["W"], SPK["D"], SPK["H"]
    code = "L1" if side == "LEFT" else "R1"
    n = walls_strip(code, W, D, H,
                    [scaled(speaker_front, 4), blue_panel, scaled(speaker_back, 4), blue_panel],
                    [BLUE] * 4)
    side_ar = "اليسرى" if side == "LEFT" else "اليمنى"
    page_header(c, pw, ph, "05  السماعة %s - الجدران  (%s)" % (side_ar, code),
                ["من اليسار على الورقة: أمام | يمين | خلف | يسار. الصق اللسان الطرفي داخل حافة الأمام لتكوين أنبوب،",
                 "ثم الصق الغطاء العلوي %s2 والغطاء السفلي %s3 على الألسنة الصغيرة." % (code[0], code[0]), PRINT_NOTE])
    w, h = size(n)
    piece_title(c, n, (pw / cm - w) / 2, 2.0, "%s السماعة %s" % (code, side_ar))


def p_speaker_lids(c):
    c.setPageSize(A4)
    pw, ph = A4
    W, D = SPK["W"], SPK["D"]

    def top_art(c2, x, y, w, h):
        blue_panel(c2, x, y, w, h)
        label_ar(c2, x + w / 2, y + 0.35 * cm, "الحافة الأمامية", 6, HexColor("#8fa2ff"))

    page_header(c, pw, ph, "05  أغطية السماعات العلوية والسفلية  (L2, L3, R2, R3)",
                ["%g × %g سم لكل قطعة. تُلصق على ألسنة أنابيب السماعات L1 و R1." % (W, D), PRINT_NOTE])
    items = [("L2", "أعلى السماعة اليسرى", BLUE, top_art), ("L3", "أسفل السماعة اليسرى", BLUE_D, code_mark("L3")),
             ("R2", "أعلى السماعة اليمنى", BLUE, top_art), ("R3", "أسفل السماعة اليمنى", BLUE_D, code_mark("R3"))]
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
    page_header(c, pw, ph, "06  لوحة المفاتيح - الأعلى + الجدران  (K1)",
                ["%g × %g × %g سم. اطوِ الجدران للأسفل والصق ألسنة الزوايا الأربعة،"
                 % (KB["W"], KB["D"], KB["T"]),
                 "ثم الصق القطعة السفلية K2 (في الملف رقم 07) على الألسنة الخارجية.", PRINT_NOTE])
    w, h = size(n)
    piece_title(c, n, (pw / cm - w) / 2, 4.0, "K1 لوحة المفاتيح")


def p_bottoms(c):
    sz = landscape(A4)
    c.setPageSize(sz)
    pw, ph = sz
    page_header(c, pw, ph, "07  قطع صغيرة 1 - القطع السفلية  (K2, U2, S3)",
                ["هذه القطع تغلق لوحة المفاتيح والماوس وقاعدة الحامل من الأسفل (لن تظهر).", PRINT_NOTE])
    k2 = panel("K2", KB["W"], KB["D"], BLUE_D, code_mark("K2"))
    u2 = panel("U2", MOUSE["W"], MOUSE["D"], BLUE_D, code_mark("U2"))
    s3 = panel("S3", FOOT["W"], FOOT["D"], BLACK, code_mark_black("S3"))
    x0 = (pw / cm - KB["W"] - 1.0 - MOUSE["W"]) / 2
    piece_title(c, k2, x0, 11.0, "K2 أسفل لوحة المفاتيح")
    piece_title(c, u2, x0 + KB["W"] + 1.0, 10.5, "U2 أسفل الماوس")
    piece_title(c, s3, x0, 2.0, "S3 أسفل قاعدة الحامل")


def p_small2(c):
    c.setPageSize(A4)
    pw, ph = A4
    page_header(c, pw, ph, "07  قطع صغيرة 2 - الماوس (U1) + جدران الشاشة (M3, M4, M5)",
                ["U1: اطوِ الجدران للأسفل، الصق ألسنة الزوايا، ثم أغلقه بالقطعة U2.   M3 = الجدار السفلي للشاشة (24 سم).",
                 "M4 و M5 = الجداران الجانبيان للشاشة (15 سم). لسان طويل يُلصق داخل الظهر M2، والآخر تحت الواجهة M1."])
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
    piece_title(c, u1, 12.0, 12.0, "U1 الماوس")


def p_rgb(c):
    c.setPageSize(A4)
    pw, ph = A4
    page_header(c, pw, ph, "08  اختياري - واجهات سماعات بإضاءة ملونة  (X1, X2)",
                ["بنفس شكل الصورة الثالثة. قصها والصقها فوق واجهات السماعات (المقاس بالضبط %g × %g سم)." % (SPK["W"], SPK["H"]),
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
        label_ar(c, X + SPK["W"] * cm / 2, Y - 0.5 * cm, ["X1 يسار", "X2 يمين"][i], 8, BLUE_D, True)


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
