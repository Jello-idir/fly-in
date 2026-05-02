from PIL import Image
import os
from dataclasses import dataclass

UPPERCASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWERCASE = "abcdefghijklmnopqrstuvwxyz"
DIGITS    = """0123456789.,!?'"-_:; """

@dataclass
class Glyph:
    char:   str
    width:  int
    height: int
    pixels: list[tuple[int, int, int]]  # (x, y, rgba) — rgba packed as 0xRRGGBBAA


def _pack_rgba(r: int, g: int, b: int, a: int) -> int:
    return (r << 24) | (g << 16) | (b << 8) | a


def _parse_glyph_image(path: str, charset: str, glyph_w: int, glyph_h: int) -> list[Glyph]:
    img = Image.open(path).convert("RGBA")
    raw = img.load()
    glyphs = []
    for idx, char in enumerate(charset):
        x_off = idx * glyph_w
        pixels = [
            (col, row, _pack_rgba(*raw[x_off + col, row]))  # type: ignore
            for row in range(glyph_h)
            for col in range(glyph_w)
            if raw[x_off + col, row][3] > 0  # type: ignore
        ]
        glyphs.append(Glyph(char=char, width=glyph_w, height=glyph_h, pixels=pixels))
    return glyphs


def load_font() -> dict[str, Glyph]:
    base = os.path.dirname(os.path.abspath(__file__))
    font: dict[str, Glyph] = {}
    for path, charset, w, h in [
        ("glyphs/uppercase.png", UPPERCASE, 9, 12),
        ("glyphs/lowercase.png", LOWERCASE, 8, 12),
        ("glyphs/digits.png",    DIGITS,    9, 12),
    ]:
        for glyph in _parse_glyph_image(os.path.join(base, path), charset, w, h):
            font[glyph.char] = glyph
    return font
