from PIL import Image
from dataclasses import dataclass

UPPERCASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWERCASE = "abcdefghijklmnopqrstuvwxyz"
DIGITS = """1234567890!"#%'()~+-/[]<>:.,_| """


@dataclass
class Glyph:
    """A character's dimensions and visible-pixel mask."""
    char: str
    width: int
    height: int
    pixels: list[list[bool]]


class Font:
    """Pixel glyphs indexed by character."""
    def __init__(self, glyphs: dict[str, Glyph]):
        """Store the supplied character-to-glyph mapping."""
        self.glyphs = glyphs

    @classmethod
    def _font_loader(cls,
                     uppercase_path: str,
                     lowercase_path: str,
                     digits_path: str
                     ) -> 'Font':
        """Load letters, digits, and symbols from three sprite sheets."""
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
    def _parse_glyph(path: str,
                     charset: str,
                     glyph_w: int,
                     glyph_h: int
                     ) -> list[Glyph]:
        """Slice a horizontal sprite sheet into glyph alpha masks."""
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
                    pixel = True if raw[
                        i * glyph_w + x, y][3] > 0 else False  # type: ignore
                    row.append(pixel)
                pixels.append(row)
            glyphs.append(Glyph(char, glyph_w, glyph_h, pixels))
        return glyphs
