# One Day in the World — 22 November 2026
#
# A make.fun news-image entry (program/v1). The program draws, from code alone,
# a newspaper front page that sums up Sunday 22 November 2026 in one image:
# the COP31 climate talks deadlocked in Antalya, drones hitting a Russian cargo
# ship in the Baltic, the Trump-Xi-Putin summit in Shenzhen, the arrest of
# cartel boss "El Chapo Isidro" in Sinaloa, a global market sell-off, and
# India's new Nitish Setu bridge and the Wellington Test.
#
# Pure Python 3.13 standard library (zlib, struct, os). No network, no fonts,
# no image files: every pixel is computed here, including a hand-built 5x7
# bitmap font and a hand-built PNG encoder. The output is deterministic:
# the same bytes on every run.
#
# Run:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
# The grader runs it as:  python3 main.py   (writing /output/entry.png)

import os
import struct
import zlib

W, H = 1024, 1024

# --- palette ---------------------------------------------------------------
PAPER = (246, 241, 229)   # newsprint cream
INK = (24, 22, 18)        # near-black ink
RED = (178, 32, 44)       # headline red
BLUE = (31, 78, 121)      # deep blue
GREEN = (46, 110, 66)     # land green
SKY = (174, 205, 226)     # pale sky blue
SEA = (52, 110, 158)      # sea blue
GREY = (120, 116, 108)    # smoke grey
GOLD = (198, 148, 44)     # gold accent
WHITE = (255, 255, 255)
DARKRED = (140, 20, 30)


# --- canvas ----------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill_rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            row = bytes(c) * (x1 - x0)
            self.px[i:i + (x1 - x0) * 3] = row

    def rect(self, x, y, w, h, c, t=1):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    def hline(self, x, y, w, c, t=1):
        self.fill_rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.fill_rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            if t == 1:
                self.set(x0, y0, c)
            else:
                self.fill_rect(x0 - t // 2, y0 - t // 2, t, t, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c):
        # filled circle
        for yy in range(cy - r, cy + r + 1):
            dx = int((r * r - (yy - cy) ** 2) ** 0.5)
            self.fill_rect(cx - dx, yy, 2 * dx + 1, 1, c)

    def circle_outline(self, cx, cy, r, c, t=2):
        for k in range(t):
            rr = r - k
            x, y, d = 0, rr, 3 - 2 * rr
            while x <= y:
                for sx, sy in ((x, y), (y, x), (-x, y), (-y, x),
                               (x, -y), (y, -x), (-x, -y), (-y, -x)):
                    self.set(cx + sx, cy + sy, c)
                if d < 0:
                    d += 4 * x + 6
                else:
                    d += 4 * (x - y) + 10
                    y -= 1
                x += 1

    def ellipse(self, cx, cy, rx, ry, c):
        for yy in range(cy - ry, cy + ry + 1):
            t = 1.0 - ((yy - cy) / ry) ** 2
            if t < 0:
                continue
            dx = int(rx * (t ** 0.5))
            self.fill_rect(cx - dx, yy, 2 * dx + 1, 1, c)

    def triangle(self, p0, p1, p2, c):
        self.polygon([p0, p1, p2], c)

    def polygon(self, pts, c):
        # scanline fill for a simple polygon
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if y0 == y1:
                    continue
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[i]), y, int(xs[i + 1]) - int(xs[i]) + 1, 1, c)


# --- PNG encoder (hand-built, deterministic) -------------------------------
def _chunk(tag, data):
    out = struct.pack(">I", len(data)) + tag + data
    out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return out


def encode_png(cv):
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    return png


# --- 5x7 bitmap font (hand-drawn in this file) ------------------------------
# Each glyph is 7 rows of 5 bits, '#' = ink.
FONT = {}
def _g(ch, rows):
    FONT[ch] = rows

_g('A', ["01110", "10001", "10001", "11111", "10001", "10001", "10001"])
_g('B', ["11110", "10001", "10001", "11110", "10001", "10001", "11110"])
_g('C', ["01110", "10001", "10000", "10000", "10000", "10001", "01110"])
_g('D', ["11110", "10001", "10001", "10001", "10001", "10001", "11110"])
_g('E', ["11111", "10000", "10000", "11110", "10000", "10000", "11111"])
_g('F', ["11111", "10000", "10000", "11110", "10000", "10000", "10000"])
_g('G', ["01110", "10001", "10000", "10111", "10001", "10001", "01111"])
_g('H', ["10001", "10001", "10001", "11111", "10001", "10001", "10001"])
_g('I', ["01110", "00100", "00100", "00100", "00100", "00100", "01110"])
_g('J', ["00111", "00010", "00010", "00010", "00010", "10010", "01100"])
_g('K', ["10001", "10010", "10100", "11000", "10100", "10010", "10001"])
_g('L', ["10000", "10000", "10000", "10000", "10000", "10000", "11111"])
_g('M', ["10001", "11011", "10101", "10101", "10001", "10001", "10001"])
_g('N', ["10001", "11001", "10101", "10011", "10001", "10001", "10001"])
_g('O', ["01110", "10001", "10001", "10001", "10001", "10001", "01110"])
_g('P', ["11110", "10001", "10001", "11110", "10000", "10000", "10000"])
_g('Q', ["01110", "10001", "10001", "10001", "10101", "10010", "01101"])
_g('R', ["11110", "10001", "10001", "11110", "10100", "10010", "10001"])
_g('S', ["01111", "10000", "10000", "01110", "00001", "00001", "11110"])
_g('T', ["11111", "00100", "00100", "00100", "00100", "00100", "00100"])
_g('U', ["10001", "10001", "10001", "10001", "10001", "10001", "01110"])
_g('V', ["10001", "10001", "10001", "10001", "10001", "01010", "00100"])
_g('W', ["10001", "10001", "10001", "10101", "10101", "11011", "10001"])
_g('X', ["10001", "10001", "01010", "00100", "01010", "10001", "10001"])
_g('Y', ["10001", "10001", "01010", "00100", "00100", "00100", "00100"])
_g('Z', ["11111", "00001", "00010", "00100", "01000", "10000", "11111"])
_g('0', ["01110", "10001", "10011", "10101", "11001", "10001", "01110"])
_g('1', ["00100", "01100", "00100", "00100", "00100", "00100", "01110"])
_g('2', ["01110", "10001", "00001", "00010", "00100", "01000", "11111"])
_g('3', ["11111", "00010", "00100", "00010", "00001", "10001", "01110"])
_g('4', ["00010", "00110", "01010", "10010", "11111", "00010", "00010"])
_g('5', ["11111", "10000", "11110", "00001", "00001", "10001", "01110"])
_g('6', ["00110", "01000", "10000", "11110", "10001", "10001", "01110"])
_g('7', ["11111", "00001", "00010", "00100", "01000", "01000", "01000"])
_g('8', ["01110", "10001", "10001", "01110", "10001", "10001", "01110"])
_g('9', ["01110", "10001", "10001", "01111", "00001", "00010", "01100"])
_g('.', ["00000", "00000", "00000", "00000", "00000", "01100", "01100"])
_g(',', ["00000", "00000", "00000", "00000", "01100", "00100", "01000"])
_g(':', ["00000", "01100", "01100", "00000", "01100", "01100", "00000"])
_g(';', ["00000", "01100", "01100", "00000", "01100", "00100", "01000"])
_g("'", ["00100", "00100", "01000", "00000", "00000", "00000", "00000"])
_g('-', ["00000", "00000", "00000", "01110", "00000", "00000", "00000"])
_g('/', ["00001", "00010", "00010", "00100", "01000", "01000", "10000"])
_g('(', ["00010", "00100", "01000", "01000", "01000", "00100", "00010"])
_g(')', ["01000", "00100", "00010", "00010", "00010", "00100", "01000"])
_g('&', ["01100", "10010", "10100", "01000", "10101", "10010", "01101"])
_g('%', ["11001", "11010", "00010", "00100", "01000", "01011", "10011"])
_g('+', ["00000", "00100", "00100", "11111", "00100", "00100", "00000"])
_g('!', ["00100", "00100", "00100", "00100", "00100", "00000", "00100"])
_g('?', ["01110", "10001", "00001", "00010", "00100", "00000", "00100"])
_g('=', ["00000", "00000", "11111", "00000", "11111", "00000", "00000"])
_g('•', ["00000", "00000", "01100", "01100", "01100", "00000", "00000"])
_g(' ', ["00000", "00000", "00000", "00000", "00000", "00000", "00000"])
_g('—', ["00000", "00000", "00000", "11111", "00000", "00000", "00000"])


def text_w(s, scale):
    """Pixel width of string s at the given scale (1px gap between glyphs)."""
    if not s:
        return 0
    return len(s) * 6 * scale - scale


def draw_text(cv, x, y, s, scale, color, align="left"):
    """Draw uppercase text; s is normalised (curly quotes/dashes flattened)."""
    s = (s.replace("’", "'").replace("‘", "'").replace("–", "-")
         .replace("—", "-").replace("“", '"').replace("”", '"'))
    if align == "center":
        x -= text_w(s, scale) // 2
    elif align == "right":
        x -= text_w(s, scale)
    cx = x
    for ch in s:
        glyph = FONT.get(ch.upper(), FONT['?'])
        for r, row in enumerate(glyph):
            for c, bit in enumerate(row):
                if bit == '1':
                    cv.fill_rect(cx + c * scale, y + r * scale, scale, scale, color)
        cx += 6 * scale
    return cx


def wrap_lines(s, scale, max_w):
    """Greedy word wrap into lines that fit max_w pixels."""
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# --- pictograms (all drawn with the primitives above) ------------------------
def draw_globe_factory(cv, cx, cy, r):
    """Earth with a smoking factory in front: COP31's fossil-fuel deadlock."""
    # sky disc
    cv.circle(cx, cy, r, SKY)
    # land blobs (simple continents)
    cv.ellipse(cx - r // 3, cy - r // 3, r // 3, r // 4, GREEN)
    cv.ellipse(cx + r // 4, cy + r // 5, r // 4, r // 5, GREEN)
    cv.ellipse(cx - r // 5, cy + r // 2, r // 5, r // 6, GREEN)
    cv.circle_outline(cx, cy, r, INK, 3)
    # latitude lines
    for dy in (-r // 2, 0, r // 2):
        wdt = int((r * r - dy * dy) ** 0.5)
        cv.hline(cx - wdt, cy + dy, 2 * wdt, INK, 1)
    # factory silhouette at the foot of the globe, to its lower left
    fx, fy = cx - r - 54, cy + r - 52
    cv.fill_rect(fx, fy + 18, 64, 34, INK)
    cv.polygon([(fx, fy + 18), (fx + 14, fy), (fx + 28, fy + 18)], INK)
    cv.fill_rect(fx + 34, fy - 12, 9, 30, INK)
    cv.fill_rect(fx + 48, fy - 22, 9, 40, INK)
    # smoke puffs
    cv.circle(fx + 38, fy - 26, 8, GREY)
    cv.circle(fx + 50, fy - 40, 10, GREY)
    cv.circle(fx + 64, fy - 54, 8, GREY)
    # red deadlock cross over the globe
    cv.line(cx - r + 14, cy - r + 14, cx + r - 14, cy + r - 14, RED, 7)
    cv.line(cx + r - 14, cy - r + 14, cx - r + 14, cy + r - 14, RED, 7)


def draw_ship(cv, x, y, w, h):
    """Cargo ship on waves, a drone above it: the Baltic strike."""
    sea_y = y + h - 26
    cv.fill_rect(x, sea_y, w, 26, SEA)
    for wx in range(x + 4, x + w - 4, 34):
        cv.line(wx, sea_y + 8, wx + 16, sea_y + 8, WHITE, 2)
        cv.line(wx + 8, sea_y + 17, wx + 24, sea_y + 17, WHITE, 2)
    # hull
    hx, hy = x + w // 2 - 78, y + 58
    cv.polygon([(hx, hy), (hx + 156, hy), (hx + 140, hy + 34),
                (hx + 16, hy + 34)], INK)
    # containers
    cv.fill_rect(hx + 14, hy - 26, 34, 26, RED)
    cv.fill_rect(hx + 52, hy - 26, 34, 26, GOLD)
    cv.fill_rect(hx + 90, hy - 26, 34, 26, BLUE)
    cv.fill_rect(hx + 126, hy - 14, 20, 14, GREEN)
    # bridge tower
    cv.fill_rect(hx + 132, hy - 44, 18, 44, INK)
    cv.fill_rect(hx + 134, hy - 40, 14, 6, SKY)
    # drone above, with a strike flash
    dx, dy = x + w // 2 + 52, y + 8
    cv.fill_rect(dx - 12, dy, 24, 5, INK)
    cv.circle(dx - 14, dy + 2, 4, INK)
    cv.circle(dx + 14, dy + 2, 4, INK)
    cv.circle(dx, dy + 2, 5, RED)
    cv.line(dx, dy + 8, dx - 6, dy + 22, RED, 3)
    cv.line(dx, dy + 8, dx + 6, dy + 22, RED, 3)
    cv.line(dx - 8, dy + 16, dx + 8, dy + 16, RED, 2)


def draw_summit(cv, x, y, w, h):
    """Three leaders at a round table with three flags: Shenzhen."""
    # table
    tx, ty = x + w // 2, y + h - 22
    cv.ellipse(tx, ty, w // 2 - 16, 12, INK)
    cv.fill_rect(tx - 8, ty, 16, 16, INK)
    # three figures behind the table
    cols = [RED, BLUE, GREEN]
    for i, col in enumerate(cols):
        fx = x + 52 + i * (w - 104) // 2
        cv.circle(fx, y + h // 3, 15, col)              # head
        cv.polygon([(fx - 22, ty - 2), (fx + 22, ty - 2),
                    (fx + 12, y + h // 2), (fx - 12, y + h // 2)], col)  # suit
        cv.fill_rect(fx - 3, y + h // 2, 6, 16, WHITE)  # shirt
    # flags on the table
    for i, col in enumerate(cols):
        fx = x + 62 + i * (w - 124) // 2
        cv.vline(fx, ty - 28, 28, INK, 2)
        cv.fill_rect(fx + 2, ty - 28, 22, 13, col)


def draw_handcuffs(cv, x, y, w, h):
    """Open handcuffs and a star badge: the cartel arrest."""
    cy = y + h // 2 - 6
    for cx in (x + w // 2 - 52, x + w // 2 + 52):
        cv.circle_outline(cx, cy, 30, INK, 5)
        cv.circle_outline(cx, cy, 14, INK, 3)
    cv.line(x + w // 2 - 24, cy - 8, x + w // 2 + 24, cy - 8, INK, 5)
    # star badge below
    bx, by = x + w // 2, y + h - 34
    star = []
    import math as _m
    for i in range(10):
        ang = -_m.pi / 2 + i * _m.pi / 5
        rr = 22 if i % 2 == 0 else 9
        star.append((int(bx + rr * _m.cos(ang)), int(by + rr * _m.sin(ang))))
    cv.polygon(star, GOLD)
    cv.circle(bx, by, 6, RED)


def draw_chart(cv, x, y, w, h):
    """A falling market line over a grid, with a red down arrow."""
    gx, gy, gw, gh = x + 14, y + 10, w - 28, h - 34
    cv.fill_rect(gx, gy, gw, gh, WHITE)
    cv.rect(gx, gy, gw, gh, INK, 2)
    for i in range(1, 4):
        cv.hline(gx, gy + gh * i // 4, gw, GREY, 1)
        cv.vline(gx + gw * i // 4, gy, gh, GREY, 1)
    pts = [(gx + 6, gy + 14), (gx + gw // 4, gy + 30),
           (gx + gw // 2, gy + 26), (gx + 3 * gw // 4, gy + gh - 30),
           (gx + gw - 8, gy + gh - 8)]
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], RED, 4)
    for px, py in pts:
        cv.circle(px, py, 5, RED)
    # down arrow at the end
    ax, ay = gx + gw - 26, gy + gh - 26
    cv.line(ax, ay - 26, ax, ay + 8, RED, 5)
    cv.polygon([(ax - 12, ay - 4), (ax + 12, ay - 4), (ax, ay + 14)], RED)


def draw_bridge(cv, x, y, w, h):
    """A cable bridge over a river, with a cricket ball: India."""
    river_y = y + h - 22
    cv.fill_rect(x, river_y, w, 22, SEA)
    for wx in range(x + 6, x + w - 6, 36):
        cv.line(wx, river_y + 9, wx + 18, river_y + 9, WHITE, 2)
    # deck
    dy = y + h - 52
    cv.fill_rect(x + 10, dy, w - 20, 8, INK)
    # arch + cables
    ax = x + w // 2
    cv.line(x + 16, dy, ax, y + 18, INK, 4)
    cv.line(x + w - 16, dy, ax, y + 18, INK, 4)
    for i in range(1, 6):
        lx = x + 16 + (w - 32) * i // 6
        top = y + 18 + (dy - y - 18) * abs(lx - ax) / (w // 2)
        cv.line(lx, int(top), lx, dy, GREY, 2)
    # two towers
    cv.fill_rect(x + w // 2 - 40, y + 52, 8, dy - y - 52, INK)
    cv.fill_rect(x + w // 2 + 32, y + 52, 8, dy - y - 52, INK)
    # cricket ball
    cv.circle(x + w - 46, y + 26, 12, RED)
    cv.circle_outline(x + w - 46, y + 26, 12, WHITE, 1)


# --- layout ------------------------------------------------------------------
def panel(cv, x, y, w, h, kicker, kcolor=RED):
    cv.rect(x, y, w, h, INK, 2)
    return x, y, w, h


def kicker(cv, x, y, s, color=RED):
    draw_text(cv, x + 12, y + 10, s, 2, color)


def headline(cv, x, y, lines, scale=3, color=INK, max_w=None):
    yy = y
    for ln in lines:
        draw_text(cv, x + 12, yy, ln, scale, color)
        yy += 7 * scale + 6
    return yy


def sub(cv, x, y, s, scale=2, max_w=280, color=INK):
    yy = y
    for ln in wrap_lines(s, scale, max_w):
        draw_text(cv, x + 12, yy, ln, scale, color)
        yy += 7 * scale + 4
    return yy


def build():
    cv = Canvas(W, H, PAPER)
    # double outer border
    cv.rect(10, 10, W - 20, H - 20, INK, 3)
    cv.rect(18, 18, W - 36, H - 36, INK, 1)

    # ---- masthead ------------------------------------------------------
    draw_text(cv, W // 2, 34, "THE WORLD IN ONE PICTURE", 2, INK, "center")
    draw_text(cv, W // 2, 56, "SUNDAY 22 NOVEMBER 2026", 6, INK, "center")
    draw_text(cv, W // 2, 112, "THE DAY'S WORLD NEWS, IN ONE IMAGE", 2, RED, "center")
    cv.fill_rect(28, 140, W - 56, 4, INK)
    cv.fill_rect(28, 148, W - 56, 1, INK)

    # ---- lead story: COP31 --------------------------------------------
    lx, ly, lw, lh = 28, 162, W - 56, 268
    panel(cv, lx, ly, lw, lh, "")
    draw_globe_factory(cv, lx + lw - 150, ly + 118, 92)
    kicker(cv, lx, ly, "CLIMATE - ANTALYA, TURKEY")
    yy = headline(cv, lx, ly + 34, ["COP31 IN", "DEADLOCK"], scale=7)
    sub(cv, lx, yy + 4, "FOSSIL-FUEL FIGHT STALLS CLIMATE TALKS PAST THEIR DEADLINE",
        scale=3, max_w=560)
    draw_text(cv, lx + 12, ly + lh - 30, "NEGOTIATORS IN OVERTIME AS THE SUMMIT MISSES ITS FRIDAY DEADLINE",
              2, GREY)

    # ---- row of three --------------------------------------------------
    ry, rh = 444, 262
    pw = (W - 56 - 2 * 22) // 3  # 308
    cols = [28, 28 + pw + 22, 28 + 2 * (pw + 22)]

    # A: Baltic ship
    x = cols[0]
    panel(cv, x, ry, pw, rh, "")
    draw_ship(cv, x + 8, ry + 20, pw - 16, 92)
    kicker(cv, x, ry + 114, "EUROPE - BALTIC SEA")
    headline(cv, x, ry + 142, ["DRONES HIT", "SHIP IN BALTIC"], scale=3)
    sub(cv, x, ry + 200, "RUSSIAN CARGO SHIP ATTACKED; FINLAND TIGHTENS SECURITY",
        scale=2, max_w=pw - 24)

    # B: Shenzhen summit
    x = cols[1]
    panel(cv, x, ry, pw, rh, "")
    draw_summit(cv, x + 8, ry + 20, pw - 16, 92)
    kicker(cv, x, ry + 114, "DIPLOMACY - SHENZHEN")
    headline(cv, x, ry + 142, ["TRUMP, XI AND", "PUTIN MEET"], scale=3)
    sub(cv, x, ry + 200, "ZELENSKYY CALLS PUTIN A KILLER AFTER TRUMP CALLS HIM A FRIEND",
        scale=2, max_w=pw - 24)

    # C: cartel arrest
    x = cols[2]
    panel(cv, x, ry, pw, rh, "")
    draw_handcuffs(cv, x + 8, ry + 20, pw - 16, 92)
    kicker(cv, x, ry + 114, "AMERICAS - SINALOA")
    headline(cv, x, ry + 142, ["CARTEL BOSS", "HELD"], scale=3)
    sub(cv, x, ry + 200, "'EL CHAPO ISIDRO' ARRESTED IN SPECIAL FORCES RAID",
        scale=2, max_w=pw - 24)

    # ---- row of two ----------------------------------------------------
    ry2, rh2 = 720, 172
    pw2 = (W - 56 - 22) // 2  # 473
    x = 28
    panel(cv, x, ry2, pw2, rh2, "")
    draw_chart(cv, x + pw2 - 210, ry2 + 30, 196, 120)
    kicker(cv, x, ry2, "MARKETS")
    headline(cv, x, ry2 + 28, ["MARKETS SLIDE", "ON AI SELL-OFF"], scale=3)
    sub(cv, x, ry2 + 86, "S&P 500 -3.7% - NIKKEI -5.1%; TECH SHARES TUMBLE",
        scale=2, max_w=240)

    x = 28 + pw2 + 22
    panel(cv, x, ry2, pw2, rh2, "")
    draw_bridge(cv, x + pw2 - 210, ry2 + 30, 196, 120)
    kicker(cv, x, ry2, "ASIA - INDIA")
    headline(cv, x, ry2 + 28, ["MODI OPENS", "NITISH SETU"], scale=3)
    sub(cv, x, ry2 + 86, "PATNA-VAISHALI LINK OPENS; INDIA V NZ IN WELLINGTON",
        scale=2, max_w=240)

    # ---- footer strip --------------------------------------------------
    fy = 902
    cv.fill_rect(28, fy, W - 56, 3, INK)
    draw_text(cv, 28, fy + 12, "ALSO TODAY:", 2, RED)
    draw_text(cv, 28, fy + 34, "ESTONIA TO SHUT RUSSIA BORDER", 2, INK)
    draw_text(cv, 28, fy + 52, "BOLSONARO IN INTENSIVE CARE", 2, INK)
    draw_text(cv, W - 28, fy + 34, "US AIRLINES ON HOLIDAY ALERT", 2, INK, "right")
    draw_text(cv, W - 28, fy + 52, "CYCLONE AKVAN CANCELS FLIGHTS", 2, INK, "right")
    cv.fill_rect(28, fy + 76, W - 56, 1, INK)
    draw_text(cv, W // 2, fy + 86, "ONE DAY - ONE IMAGE - SUNDAY 22 NOVEMBER 2026", 2, INK, "center")
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    png = encode_png(build())
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(png)


if __name__ == "__main__":
    main()
