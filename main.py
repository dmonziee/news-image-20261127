#!/usr/bin/env python3
"""THE WORLD, Friday 27 November 2026 -- a one-page newspaper front.

Stdlib-only and deterministic: every run writes the same bytes. The
program draws the day's world news as a 1024 by 1024 front page and
saves it as a PNG to /output/entry.png, or to $MAKEFUN_OUTPUT_DIR
when that variable is set. No clock, no randomness, no network.
"""

import binascii, os, struct, zlib

WIDTH = 1024
HEIGHT = 1024

# ---------------------------------------------------------------- colours
C = {
    "paper": (250, 246, 236),
    "ink": (22, 22, 22),
    "red": (158, 27, 27),
    "blue": (31, 78, 121),
    "grey": (107, 107, 107),
    "tint": (238, 233, 220),
    "flame": (214, 106, 24),
    "flare": (232, 178, 32),
    "green": (46, 110, 58),
    "teal": (36, 110, 110),
    "dusk": (216, 178, 140),
    "dusk2": (196, 140, 110),
    "ground": (90, 88, 80),
    "ember": (255, 240, 200),
    "white": (255, 255, 255),
}

# ---------------------------------------------------------------- 5x7 type
# One 35-character string per glyph: seven rows of five bits, row-major,
# "1" prints ink. Capitals carry the headlines, lower case the body.
GLYPHS = {
    "A": "01110100011000111111100011000110001",
    "B": "11110100011000111110100011000111110",
    "C": "01110100011000010000100001000101110",
    "D": "11110100011000110001100011000111110",
    "E": "11111100001000011110100001000011111",
    "F": "11111100001000011110100001000010000",
    "G": "01110100011000010111100011000101111",
    "H": "10001100011000111111100011000110001",
    "I": "01110001000010000100001000010001110",
    "J": "00111000100001000010000101001001100",
    "K": "10001100101010011000101001001010001",
    "L": "10000100001000010000100001000011111",
    "M": "10001110111010110101100011000110001",
    "N": "10001110011010110011100011000110001",
    "O": "01110100011000110001100011000101110",
    "P": "11110100011000111110100001000010000",
    "Q": "01110100011000110001101011001001101",
    "R": "11110100011000111110101001001010001",
    "S": "01111100001000001110000010000111110",
    "T": "11111001000010000100001000010000100",
    "U": "10001100011000110001100011000101110",
    "V": "10001100011000110001100010101000100",
    "W": "10001100011000110101101011101110001",
    "X": "10001100010101000100010101000110001",
    "Y": "10001100010101000100001000010000100",
    "Z": "11111000010001000100010001000011111",
    "0": "01110100011001110101110011000101110",
    "1": "00100011000010000100001000010001110",
    "2": "01110100010000100110010001000011111",
    "3": "11111000100010000010000011000101110",
    "4": "00010001100101010010111110001000010",
    "5": "11111100001111000001000011000101110",
    "6": "00110010001000011110100011000101110",
    "7": "11111000010001000100010000100001000",
    "8": "01110100011000101110100011000101110",
    "9": "01110100011000101111000010001001100",
    "a": "00000000000111000001011111000101111",
    "b": "10000100001111010001100011000111110",
    "c": "00000000000111010000100001000101110",
    "d": "00001000010111110001100011000101111",
    "e": "00000000000111010001111111000001110",
    "f": "00110010000100011110010000100001000",
    "g": "00000011111000110001011110000101110",
    "h": "10000100001111010001100011000110001",
    "i": "00000001000000001100001000010001110",
    "j": "00010000000011000010000100001000100",
    "k": "10000100001001010100110001010010010",
    "l": "01100001000010000100001000010001110",
    "m": "00000000001101010101101011010110101",
    "n": "00000000001111010001100011000110001",
    "o": "00000000000111010001100011000101110",
    "p": "00000111101000110001111101000010000",
    "q": "00000000000111110001100010111100001",
    "r": "00000000001011011001100001000010000",
    "s": "00000000000111110000011100000111110",
    "t": "01000010001111001000010000100000110",
    "u": "00000000001000110001100011001101101",
    "v": "00000000001000110001100010101000100",
    "w": "00000000001000110101101011010101010",
    "x": "00000000001000101010001000101010001",
    "y": "00000000001000110001011110000101110",
    "z": "00000000001111100010001000100011111",
    " ": "00000000000000000000000000000000000",
    ".": "00000000000000000000000000110001100",
    ",": "00000000000000000000011000010001000",
    ":": "00000011000110000000011000110000000",
    ";": "00000011000110000000011000010001000",
    "!": "00100001000010000100001000000000100",
    "?": "01110100010000100110001000000000100",
    "-": "00000000000000001110000000000000000",
    "'": "00100001000100000000000000000000000",
    '"': "01010010100101000000000000000000000",
    "(": "00010001000100001000010000010000010",
    ")": "01000001000001000010000100010001000",
    "/": "00001000100001000100010000100010000",
    "%": "11001110100001000100010000101110011",
    "$": "00100011111010001110001011111000100",
    "&": "01100100101010001000101011001001101",
    "+": "00000001000010011111001000010000000",
    "=": "00000000001111100000111110000000000",
    "*": "00000001001010101110101010010000000",
    "#": "01010010101111101010111110101001010",
    "@": "01110100011011110101101101000001110",
    "[": "01110010000100001000010000100001110",
    "]": "01110000100001000010000100001001110",
    "_": "00000000000000000000000000000011111",
}

UNKNOWN = GLYPHS["?"]


def rows_of(ch):
    """Split a glyph's 35-bit string into its seven 5-bit rows."""
    bits = GLYPHS.get(ch, UNKNOWN)
    return [bits[i * 5:(i + 1) * 5] for i in range(7)]


# ---------------------------------------------------------------- the sheet
class Sheet:
    """A flat RGB canvas with a tiny drawing vocabulary."""

    def __init__(self, bg):
        self.buf = bytearray(bg * WIDTH * HEIGHT)

    def put(self, x, y, colour):
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            at = (y * WIDTH + x) * 3
            self.buf[at:at + 3] = bytes(colour)

    def fill(self, x, y, w, h, colour):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.put(xx, yy, colour)

    def hrule(self, x, y, w, colour, thick=1):
        self.fill(x, y, w, thick, colour)

    def vrule(self, x, y, h, colour, thick=1):
        self.fill(x, y, thick, h, colour)

    def border(self, x, y, w, h, colour, thick=1):
        self.hrule(x, y, w, colour, thick)
        self.hrule(x, y + h - thick, w, colour, thick)
        self.vrule(x, y, h, colour, thick)
        self.vrule(x + w - thick, y, h, colour, thick)

    def tri(self, p, q, r, colour):
        """A filled triangle, scanline by scanline, deterministic."""
        pts = sorted((p, q, r), key=lambda pt: pt[1])
        (ax, ay), (bx, by), (cx, cy) = pts
        for y in range(ay, cy + 1):
            if y < by:
                xa = ax + (bx - ax) * (y - ay) / max(1, by - ay)
                xb = ax + (cx - ax) * (y - ay) / max(1, cy - ay)
            else:
                xa = bx + (cx - bx) * (y - by) / max(1, cy - by)
                xb = ax + (cx - ax) * (y - ay) / max(1, cy - ay)
            lo, hi = sorted((int(xa), int(xb)))
            for x in range(lo, hi + 1):
                self.put(x, y, colour)

    def spot(self, cx, cy, r, colour):
        """A filled disc, scanline by scanline, deterministic."""
        for y in range(cy - r, cy + r + 1):
            dy = y - cy
            dx = int((r * r - dy * dy) ** 0.5) if abs(dy) <= r else 0
            for x in range(cx - dx, cx + dx + 1):
                self.put(x, y, colour)

    def ring(self, cx, cy, r, colour):
        """A one-pixel circle outline (Bresenham)."""
        x, y, d = 0, r, 1 - r
        while x <= y:
            for sx, sy in ((x, y), (y, x), (-x, y), (-y, x),
                           (x, -y), (y, -x), (-x, -y), (-y, -x)):
                self.put(cx + sx, cy + sy, colour)
            if d < 0:
                d += 2 * x + 3
            else:
                d += 2 * (x - y) + 5
                y -= 1
            x += 1

    def write(self, s, x, y, scale, colour):
        """Typeset a string left-aligned at (x, y); returns its width."""
        cx = x
        for ch in s:
            for row, bits in enumerate(rows_of(ch)):
                for col in range(5):
                    if bits[col] == "1":
                        self.fill(cx + col * scale, y + row * scale,
                                  scale, scale, colour)
            cx += 6 * scale
        return cx - x

    def measure(self, s, scale):
        return len(s) * 6 * scale - scale

    def centred(self, s, y, scale, colour, x0=0, x1=None):
        x1 = WIDTH if x1 is None else x1
        w = self.measure(s, scale)
        self.write(s, x0 + (x1 - x0 - w) // 2, y, scale, colour)

    def flow(self, s, max_w, scale):
        """Greedy word wrap: lines that fit max_w pixels at scale."""
        lines, cur = [], ""
        for word in s.split(" "):
            trial = (cur + " " + word).strip()
            if self.measure(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines


# ---------------------------------------------------------------- PNG bytes
def png_bytes(sheet):
    raw = bytearray()
    stride = WIDTH * 3
    for y in range(HEIGHT):
        raw.append(0)
        raw += sheet.buf[y * stride:(y + 1) * stride]
    blob = zlib.compress(bytes(raw), 9)

    def chunk(tag, payload):
        head = struct.pack(">I", len(payload)) + tag + payload
        return head + struct.pack(">I", binascii.crc32(tag + payload) & 0xFFFFFFFF)

    head = struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", head)
            + chunk(b"IDAT", blob) + chunk(b"IEND", b""))


# ---------------------------------------------------------------- the page
MARGIN = 36
CONTENT = WIDTH - 2 * MARGIN


def masthead(sh):
    sh.write("FRIDAY, 27 NOVEMBER 2026", MARGIN, 24, 2, C["ink"])
    tag = "ONE DAY, ONE PICTURE"
    sh.write(tag, WIDTH - MARGIN - sh.measure(tag, 2), 24, 2, C["grey"])
    sh.hrule(MARGIN, 44, CONTENT, C["ink"], 2)
    sh.centred("THE WORLD", 54, 12, C["ink"])
    sh.centred("THE DAY'S NEWS, IN ONE PAGE", 146, 2, C["grey"])
    sh.hrule(MARGIN, 166, CONTENT, C["ink"], 3)
    sh.hrule(MARGIN, 172, CONTENT, C["ink"], 1)


def lead_story(sh):
    sh.write("UKRAINE WAR", MARGIN, 186, 2, C["red"])
    sh.write("TRUMP TO PUTIN:", MARGIN, 206, 5, C["ink"])
    sh.write("END THE WAR NOW", MARGIN, 249, 5, C["ink"])
    y = 300
    for line in sh.flow(
            "Zelensky warns of a mass Russian attack as Kyiv hits jets "
            "deep inside Russia and the US approves a $622m arms package.",
            CONTENT, 2):
        sh.write(line, MARGIN, y, 2, C["ink"])
        y += 16
    sh.hrule(MARGIN, 330, CONTENT, C["ink"], 1)

    # --- lead picture: a jet over a burning airbase
    ax, ay, aw, ah = MARGIN, 342, 524, 228
    sh.border(ax, ay, aw, ah, C["ink"], 2)
    sh.fill(ax + 2, ay + 2, aw - 4, ah - 4, C["tint"])
    sh.fill(ax + 2, ay + 2, aw - 4, 60, C["dusk"])
    sh.fill(ax + 2, ay + 62, aw - 4, 40, C["dusk2"])
    sh.fill(ax + 2, ay + 150, aw - 4, 76, C["ground"])
    sh.fill(ax + 2, ay + 150, aw - 4, 4, C["ink"])
    sh.fill(ax + 2, ay + 188, aw - 4, 6, C["flare"])
    # blast on the runway
    bx, by = ax + 150, ay + 150
    sh.spot(bx, by, 44, C["flame"])
    sh.spot(bx, by, 30, C["flare"])
    sh.spot(bx, by, 14, C["ember"])
    sh.tri((bx - 8, by - 44), (bx + 8, by - 44), (bx, by - 78), C["flame"])
    sh.tri((bx - 4, by - 78), (bx + 4, by - 78), (bx, by - 104), C["flare"])
    # stricken jet on the ground, nose down
    jx, jy = ax + 320, ay + 128
    sh.tri((jx, jy), (jx + 90, jy + 6), (jx + 10, jy + 18), C["ink"])
    sh.tri((jx + 30, jy + 4), (jx + 52, jy - 16), (jx + 58, jy + 8), C["ink"])
    sh.tri((jx + 62, jy + 8), (jx + 84, jy + 22), (jx + 58, jy + 16), C["ink"])
    # second jet climbing away, top right
    kx, ky = ax + 400, ay + 40
    sh.tri((kx, ky), (kx + 64, ky + 10), (kx + 8, ky + 14), C["ink"])
    sh.tri((kx + 22, ky + 6), (kx + 36, ky - 12), (kx + 42, ky + 8), C["ink"])
    sh.write("SU-34 BASE", ax + 330, ay + 12, 2, C["ink"])
    sh.write("HIT DEEP INSIDE", ax + 330, ay + 28, 2, C["ink"])
    sh.write("KYIV STRIKES JETS DEEP INSIDE RUSSIA",
             ax + 10, ay + ah - 22, 2, C["ink"])

    # --- lead body, right of the picture
    bx, bw = 584, WIDTH - MARGIN - 584
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
        for line in sh.flow(p, bw, 2):
            sh.write(line, bx, y, 2, C["ink"])
            y += 16
        y += 8
    sh.hrule(MARGIN, 582, CONTENT, C["ink"], 1)


def second_row(sh):
    y0 = 596
    # --- COP31 fallout
    x, w = MARGIN, 464
    sh.write("COP31 FALLOUT", x, y0, 2, C["red"])
    sh.write("EU SOFTENS CLIMATE", x, y0 + 20, 3, C["ink"])
    sh.write("RULES AFTER COLLAPSE", x, y0 + 44, 3, C["ink"])
    # globe pictogram
    gx, gy = x + w - 52, y0 + 2
    sh.spot(gx + 17, gy + 17, 17, C["blue"])
    sh.spot(gx + 17, gy + 17, 12, C["green"])
    sh.ring(gx + 17, gy + 17, 17, C["ink"])
    y = y0 + 76
    for line in sh.flow(
            "Brussels moved to relax climate rules after the Antalya "
            "deal collapsed, as delegates blamed the failed summit for "
            "the drift.",
            w, 2):
        sh.write(line, x, y, 2, C["ink"])
        y += 16
    # --- Kuwait drone strike
    x = 524
    sh.write("KUWAIT", x, y0, 2, C["red"])
    sh.write("IRAN DRONE KILLS", x, y0 + 20, 3, C["ink"])
    sh.write("TWO ITALIANS", x, y0 + 44, 3, C["ink"])
    # drone pictogram
    dx, dy = x + w - 52, y0 + 2
    sh.fill(dx, dy + 12, 34, 6, C["ink"])
    sh.fill(dx + 14, dy + 2, 6, 26, C["ink"])
    sh.ring(dx + 2, dy + 6, 6, C["ink"])
    sh.ring(dx + 32, dy + 6, 6, C["ink"])
    y = y0 + 76
    for line in sh.flow(
            "Two Italians were killed in a Tehran drone attack in "
            "Kuwait, Italy said, in the sharpest spillover of the "
            "US-Iran standoff yet.",
            w, 2):
        sh.write(line, x, y, 2, C["ink"])
        y += 16
    sh.hrule(MARGIN, 752, CONTENT, C["ink"], 1)


def third_row(sh):
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
    cw = (CONTENT - 48) // 3
    for i, (kick, h1, h2, body) in enumerate(cols):
        x = MARGIN + i * (cw + 24)
        sh.write(kick, x, y0, 2, C["red"])
        sh.write(h1, x, y0 + 20, 2, C["ink"])
        sh.write(h2, x, y0 + 36, 2, C["ink"])
        y = y0 + 58
        for line in sh.flow(body, cw, 2):
            sh.write(line, x, y, 2, C["ink"])
            y += 16
        if i < 2:
            sh.vrule(x + cw + 12, y0, 106, C["grey"], 1)
    sh.hrule(MARGIN, 882, CONTENT, C["ink"], 1)


def briefs(sh):
    y0 = 896
    sh.write("IN BRIEF", MARGIN, y0, 2, C["red"])
    items = [
        "BANGKOK OIL DEPOT BLAST",
        "KIM VISITS NUCLEAR SITES",
        "AFP HIT BY CYBERATTACK",
        "SAUDIS DOWN HOUTHI MISSILES",
        "SPAIN VOTES SUNDAY, RIGHT FAVOURED",
        "SOUTH KOREA LIFTS KEY RATE",
        "RUSSIAN FLEET TURNS BACK",
        "UN COURT: UNRWA FIRINGS UNSUPPORTED",
    ]
    col_w = (CONTENT - 24) // 2
    for i, b in enumerate(items):
        x = MARGIN + (i % 2) * (col_w + 24)
        y = y0 + 20 + (i // 2) * 16
        sh.write("* " + b, x, y, 2, C["ink"])
    sh.hrule(MARGIN, 984, CONTENT, C["ink"], 1)
    sh.centred("THE WORLD - FRIDAY, 27 NOVEMBER 2026 - ONE DAY, ONE PICTURE",
              994, 2, C["grey"])


def render():
    sh = Sheet(C["paper"])
    masthead(sh)
    lead_story(sh)
    second_row(sh)
    third_row(sh)
    briefs(sh)
    return sh


def main():
    folder = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(folder, exist_ok=True)
    target = os.path.join(folder, "entry.png")
    data = png_bytes(render())
    with open(target, "wb") as fh:
        fh.write(data)
    # Best-effort copy beside this file; the grading sandbox mounts the
    # repository read-only, so a failure here must never stop the run.
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "entry.png"), "wb") as fh:
            fh.write(data)
    except OSError:
        pass
    print("entry.png: %d bytes -> %s" % (len(data), target))


main() if __name__ == "__main__" else None
