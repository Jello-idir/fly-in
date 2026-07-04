from PIL import Image
from dataclasses import dataclass

UPPERCASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWERCASE = "abcdefghijklmnopqrstuvwxyz"
DIGITS = """1234567890!"#%'()~+-/[]<>:.,_| """


@dataclass
class Glyph:
    char: str
    width: int
    height: int
    pixels: list[list[bool]]


class Font:
    def __init__(self, glyphs: dict[str, Glyph]):
        self.glyphs = glyphs

    @classmethod
    def _font_from_3_images(cls, uppercase_path: str, lowercase_path: str, digits_path: str) -> 'Font':
        font: dict[str, Glyph] = {}
        for path, charset, w, h in [
            (uppercase_path, UPPERCASE, 6, 8),
            (lowercase_path, LOWERCASE, 6, 8),
            (digits_path, DIGITS, 6, 8),
        ]:
            for g in cls._parse_glyph(path, charset, w, h):
                font[g.char] = g
        return cls(font)

    @staticmethod
    def _parse_glyph(path: str, charset: str, glyph_w: int, glyph_h: int) -> list[Glyph]:
        img = Image.open(path).convert("RGBA")
        raw = img.load()
        if not raw:
            raise ValueError(f"Failed to load image from {path}")
        glyphs = []
        for i, char in enumerate(charset):
            pixels = []
            for y in range(glyph_h):
                row = []
                for x in range(glyph_w):
                    pixel = True if raw[i * glyph_w + x, y][3] > 0 else False  # type: ignore
                    row.append(pixel)
                pixels.append(row)
            glyphs.append(Glyph(char, glyph_w, glyph_h, pixels))
        return glyphs
