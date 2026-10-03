from PIL import Image
from dataclasses import dataclass
from typing import cast

UPPERCASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWERCASE = "abcdefghijklmnopqrstuvwxyz"
DIGITS = """1234567890!"#%'()~+-/[]<>:.,_| """


@dataclass
class Glyph:
    """A character's dimensions and visible-pixel mask.

    Attributes:
        char: Character represented by this glyph.
        width: Width in pixels.
        height: Height in pixels.
        pixels: Row-major boolean mask marking visible glyph pixels.
    """

    char: str
    width: int
    height: int
    pixels: list[list[bool]]


class Font:
    """Pixel glyphs indexed by character.

    Attributes:
        glyphs: Pixel glyphs indexed by character.
    """

    def __init__(self, glyphs: dict[str, Glyph]):
        """Store the supplied character-to-glyph mapping.

        Args:
            glyphs: Mapping from characters to their pixel glyphs.
        """
        self.glyphs = glyphs

    @classmethod
    def _font_loader(cls,
                     uppercase_path: str,
                     lowercase_path: str,
                     digits_path: str
                     ) -> 'Font':
        """Load letters, digits, and symbols from three sprite sheets.

        Args:
            uppercase_path: Path to the uppercase-letter PNG sprite sheet.
            lowercase_path: Path to the lowercase-letter PNG sprite sheet.
            digits_path: Path to the digits-and-symbols PNG sprite sheet.

        Returns:
            Font: Glyphs indexed by their corresponding characters.

        Raises:
            OSError: A sprite sheet cannot be read.
            ValueError: A sprite sheet has no accessible pixel buffer.
            IndexError: A sprite sheet does not contain the expected glyph
                layout.
        """
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
        """Slice a horizontal sprite sheet into glyph alpha masks.

        Args:
            path: Path to the source PNG image.
            charset: Characters in sprite-sheet order.
            glyph_w: Width of each glyph in pixels.
            glyph_h: Height of each glyph in pixels.

        Returns:
            list[Glyph]: Glyph masks in the same order as charset.

        Raises:
            OSError: The sprite sheet cannot be opened or decoded.
            ValueError: Pillow cannot provide a pixel buffer.
            IndexError: The sheet is too small for the specified glyph
                layout.
        """
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
                    rgba = cast(tuple[int, int, int, int],
                                raw[i * glyph_w + x, y])
                    pixel = rgba[3] > 0
                    row.append(pixel)
                pixels.append(row)
            glyphs.append(Glyph(char, glyph_w, glyph_h, pixels))
        return glyphs
