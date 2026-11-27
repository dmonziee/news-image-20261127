#!/usr/bin/env python3
"""THE WORLD -- front page for Friday, 27 November 2026.

A deterministic, standard-library-only generator. It draws a newspaper
front page summing up the day's world news and writes it as a 1024x1024
PNG to /output/entry.png (or $MAKEFUN_OUTPUT_DIR). Running it twice
produces byte-identical output: no randomness, no clock, no network.
"""

import binascii
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (250, 246, 236)   # warm newsprint cream
INK = (22, 22, 22)        # near-black type
RED = (158, 27, 27)       # kicker / rules accent
BLUE = (31, 78, 121)      # sea and sidebar blue
GREY = (107, 107, 107)    # fine print
LIGHT = (238, 233, 220)   # panel tint
ORANGE = (214, 106, 24)   # flame
YELLOW = (232, 178, 32)   # flare
GREEN = (46, 110, 58)     # containers
TEAL = (36, 110, 110)     # containers

# ---------------------------------------------------------------- 5x7 font
# Each glyph is 7 rows of 5 bits, "1" = ink. Drawn from scratch for this
# front page; capitals carry headlines, lower case carries body copy.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": ("00110", "01000", "01000", "11110", "01000", "01000", "01000"),
    "g": ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    "h": ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    "i": ("00000", "00100", "00000", "01100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "00110", "00010", "00010", "00010", "00100"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": ("00000", "11110", "10001", "10001", "11110", "10000", "10000"),
    "q": ("00000", "00000", "01111", "10001", "10001", "01111", "00001"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": ("01000", "01000", "11110", "01000", "01000", "01000", "00110"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
}


def glyph(ch):
    return FONT.get(ch, FONT["?"])


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * w * h)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def hline(self, x, y, w, color, t=1):
        self.rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.rect(x, y, t, h, color)

    def frame(self, x, y, w, h, color, t=1):
        self.hline(x, y, w, color, t)
        self.hline(x, y + h - t, w, color, t)
        self.vline(x, y, h, color, t)
        self.vline(x + w - t, y, h, color, t)

    def triangle(self, x0, y0, x1, y1, x2, y2, color):
        """Filled triangle by scanline interpolation (deterministic)."""
        ys = sorted(((x0, y0), (x1, y1), (x2, y2)), key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = ys
        for y in range(ay, cy + 1):
            if y < by:
                xa = ax + (bx - ax) * (y - ay) / max(1, by - ay)
                xb = ax + (cx - ax) * (y - ay) / max(1, cy - ay)
            else:
                xa = bx + (cx - bx) * (y - by) / max(1, cy - by)
                xb = ax + (cx - ax) * (y - ay) / max(1, cy - ay)
            lo, hi = sorted((int(xa), int(xb)))
            for x in range(lo, hi + 1):
                self.set(x, y, color)

    def disc(self, cx, cy, r, color):
        """Filled circle by scanlines (deterministic)."""
        for y in range(cy - r, cy + r + 1):
            dx = int((r * r - (y - cy) * (y - cy)) ** 0.5) if abs(y - cy) <= r else 0
            for x in range(cx - dx, cx + dx + 1):
                self.set(x, y, color)

    def circle(self, cx, cy, r, color):
        x, y, d = 0, r, 1 - r
        while x <= y:
            for sx, sy in ((x, y), (y, x), (-x, y), (-y, x),
                           (x, -y), (y, -x), (-x, -y), (-y, -x)):
                self.set(cx + sx, cy + sy, color)
            if d < 0:
                d += 2 * x + 3
            else:
                d += 2 * (x - y) + 5
                y -= 1
            x += 1

    def text(self, s, x, y, scale, color):
        cx = x
        for ch in s:
            g = glyph(ch)
            for row in range(7):
                bits = g[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx - x

    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale

    def center(self, s, y, scale, color, x0=0, x1=None):
        x1 = self.w if x1 is None else x1
        w = self.text_w(s, scale)
        self.text(s, x0 + (x1 - x0 - w) // 2, y, scale, color)

    def wrap(self, s, max_w, scale):
        """Greedy word wrap to lines that fit max_w pixels at scale."""
        lines, cur = [], ""
        for word in s.split(" "):
            trial = (cur + " " + word).strip()
            if self.text_w(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines


# ---------------------------------------------------------------- PNG
def write_png(canvas, path):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)  # filter: none
        raw += canvas.px[y * stride:(y + 1) * stride]
    data = zlib.compress(bytes(raw), 9)

    def chunk(tag, payload):
        c = struct.pack(">I", len(payload)) + tag + payload
        return c + struct.pack(">I", binascii.crc32(tag + payload) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", data) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ---------------------------------------------------------------- the page
MX = 36            # side margin
CW = W - 2 * MX    # content width


def draw_masthead(cv):
    cv.text("FRIDAY, 27 NOVEMBER 2026", MX, 24, 2, INK)
    right = "ONE DAY, ONE PICTURE"
    cv.text(right, W - MX - cv.text_w(right, 2), 24, 2, GREY)
    cv.hline(MX, 44, CW, INK, 2)
    cv.center("THE WORLD", 54, 12, INK)
    cv.center("THE DAY'S NEWS, IN ONE PAGE", 146, 2, GREY)
    cv.hline(MX, 166, CW, INK, 3)
    cv.hline(MX, 172, CW, INK, 1)


def draw_lead(cv):
    y = 186
    cv.text("UKRAINE WAR", MX, y, 2, RED)
    y = 206
    cv.text("TRUMP TO PUTIN:", MX, y, 5, INK)
    cv.text("END THE WAR NOW", MX, y + 43, 5, INK)
    y = 300
    for line in cv.wrap(
            "Zelensky warns of a mass Russian attack as Kyiv hits jets "
            "deep inside Russia and the US approves a $622m arms package.",
            CW, 2):
        cv.text(line, MX, y, 2, INK)
        y += 16
    cv.hline(MX, 330, CW, INK, 1)

    # --- lead picture: a jet over a burning airbase, fleet turning back
    ax, ay, aw, ah = MX, 342, 524, 228
    cv.frame(ax, ay, aw, ah, INK, 2)
    cv.rect(ax + 2, ay + 2, aw - 4, ah - 4, LIGHT)
    # dusk sky bands
    cv.rect(ax + 2, ay + 2, aw - 4, 60, (216, 178, 140))
    cv.rect(ax + 2, ay + 62, aw - 4, 40, (196, 140, 110))
    # ground + runway
    cv.rect(ax + 2, ay + 150, aw - 4, 76, (90, 88, 80))
    cv.rect(ax + 2, ay + 150, aw - 4, 4, INK)
    cv.rect(ax + 2, ay + 188, aw - 4, 6, YELLOW)
    # blast on the runway
    bx, by = ax + 150, ay + 150
    cv.disc(bx, by, 44, ORANGE)
    cv.disc(bx, by, 30, YELLOW)
    cv.disc(bx, by, 14, (255, 240, 200))
    cv.triangle(bx - 8, by - 44, bx + 8, by - 44, bx, by - 78, ORANGE)
    cv.triangle(bx - 4, by - 78, bx + 4, by - 78, bx, by - 104, YELLOW)
    # stricken jet on the ground, nose down
    jx, jy = ax + 320, ay + 128
    cv.triangle(jx, jy, jx + 90, jy + 6, jx + 10, jy + 18, INK)
    cv.triangle(jx + 30, jy + 4, jx + 52, jy - 16, jx + 58, jy + 8, INK)
    cv.triangle(jx + 62, jy + 8, jx + 84, jy + 22, jx + 58, jy + 16, INK)
    # second jet climbing away, top right
    kx, ky = ax + 400, ay + 40
    cv.triangle(kx, ky, kx + 64, ky + 10, kx + 8, ky + 14, INK)
    cv.triangle(kx + 22, ky + 6, kx + 36, ky - 12, kx + 42, ky + 8, INK)
    cv.text("SU-34 BASE", ax + 330, ay + 12, 2, INK)
    cv.text("HIT DEEP INSIDE", ax + 330, ay + 28, 2, INK)
    cv.text("KYIV STRIKES JETS DEEP INSIDE RUSSIA",
            ax + 10, ay + ah - 22, 2, INK)

    # --- lead body, right of the picture
    bx, bw = 584, W - MX - 584
    y = 342
    paras = [
        "WASHINGTON - President Donald Trump on Friday urged Vladimir "
        "Putin to halt any hostility in Eastern Europe, as Kyiv warned "
        "Moscow is preparing a large-scale attack within days.",
        "Ukraine said its Neptune missiles struck a Russian Su-34 base "
        "far inside Russia. Russia's fleet in the Mediterranean turned "
        "back after Ukrainian strikes in Libya.",
        "The US approved a $621.9m F-16 support package for Kyiv, "
        "funded by European allies, as talks on a ceasefire stalled.",
    ]
    for p in paras:
        for line in cv.wrap(p, bw, 2):
            cv.text(line, bx, y, 2, INK)
            y += 16
        y += 8
    cv.hline(MX, 582, CW, INK, 1)


def draw_second_row(cv):
    y0 = 596
    # --- COP31 fallout
    x, w = MX, 464
    cv.text("COP31 FALLOUT", x, y0, 2, RED)
    cv.text("EU SOFTENS CLIMATE", x, y0 + 20, 3, INK)
    cv.text("RULES AFTER COLLAPSE", x, y0 + 44, 3, INK)
    # globe pictogram
    gx, gy = x + w - 52, y0 + 2
    cv.disc(gx + 17, gy + 17, 17, BLUE)
    cv.disc(gx + 17, gy + 17, 12, GREEN)
    cv.circle(gx + 17, gy + 17, 17, INK)
    y = y0 + 76
    for line in cv.wrap(
            "Brussels moved to relax climate rules after the Antalya "
            "deal collapsed, as delegates blamed the failed summit for "
            "the drift.",
            w, 2):
        cv.text(line, x, y, 2, INK)
        y += 16
    # --- Kuwait drone strike
    x = 524
    cv.text("KUWAIT", x, y0, 2, RED)
    cv.text("IRAN DRONE KILLS", x, y0 + 20, 3, INK)
    cv.text("TWO ITALIANS", x, y0 + 44, 3, INK)
    # drone pictogram
    dx, dy = x + w - 52, y0 + 2
    cv.rect(dx, dy + 12, 34, 6, INK)
    cv.rect(dx + 14, dy + 2, 6, 26, INK)
    cv.circle(dx + 2, dy + 6, 6, INK)
    cv.circle(dx + 32, dy + 6, 6, INK)
    y = y0 + 76
    for line in cv.wrap(
            "Two Italians were killed in a Tehran drone attack in "
            "Kuwait, Italy said, in the sharpest spillover of the "
            "US-Iran standoff yet.",
            w, 2):
        cv.text(line, x, y, 2, INK)
        y += 16
    cv.hline(MX, 752, CW, INK, 1)


def draw_third_row(cv):
    y0 = 766
    cols = [
        ("GAZA", "ISRAEL WARNS 1M FACE",
         "RELOCATION",
         "Israel said a million Palestinians must move if Hamas does "
         "not disarm."),
        ("INDONESIA", "MINE FLOOD KILLS 13,",
         "13 STILL TRAPPED",
         "An illegal gold mine flooded in Indonesia; rescuers hunt "
         "for the missing."),
        ("AMERICA", "THANKSGIVING BLIZZARD",
         "CUTS POWER",
         "A blizzard cut power and delayed flights across the US East "
         "Coast."),
    ]
    cw = (CW - 48) // 3
    for i, (kick, h1, h2, body) in enumerate(cols):
        x = MX + i * (cw + 24)
        cv.text(kick, x, y0, 2, RED)
        cv.text(h1, x, y0 + 20, 2, INK)
        cv.text(h2, x, y0 + 36, 2, INK)
        y = y0 + 58
        for line in cv.wrap(body, cw, 2):
            cv.text(line, x, y, 2, INK)
            y += 16
        if i < 2:
            cv.vline(x + cw + 12, y0, 106, GREY, 1)
    cv.hline(MX, 882, CW, INK, 1)


def draw_briefs(cv):
    y0 = 896
    cv.text("IN BRIEF", MX, y0, 2, RED)
    briefs = [
        "BANGKOK OIL DEPOT BLAST",
        "KIM VISITS NUCLEAR SITES",
        "AFP HIT BY CYBERATTACK",
        "SAUDIS DOWN HOUTHI MISSILES",
        "SPAIN VOTES SUNDAY, RIGHT FAVOURED",
        "SOUTH KOREA LIFTS KEY RATE",
        "RUSSIAN FLEET TURNS BACK",
        "UN COURT: UNRWA FIRINGS UNSUPPORTED",
    ]
    col_w = (CW - 24) // 2
    for i, b in enumerate(briefs):
        x = MX + (i % 2) * (col_w + 24)
        y = y0 + 20 + (i // 2) * 16
        cv.text("* " + b, x, y, 2, INK)
    cv.hline(MX, 984, CW, INK, 1)
    cv.center("THE WORLD - FRIDAY, 27 NOVEMBER 2026 - ONE DAY, ONE PICTURE",
              994, 2, GREY)


def build():
    cv = Canvas(W, H, PAPER)
    draw_masthead(cv)
    draw_lead(cv)
    draw_second_row(cv)
    draw_third_row(cv)
    draw_briefs(cv)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")
    size = write_png(build(), out_path)
    # Best-effort local copy beside this file; the grading sandbox mounts
    # the repository read-only, so a failure here must never stop the run.
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        write_png(build(), os.path.join(here, "entry.png"))
    except OSError:
        pass
    print("wrote %s (%d bytes)" % (out_path, size))


if __name__ == "__main__":
    main()
