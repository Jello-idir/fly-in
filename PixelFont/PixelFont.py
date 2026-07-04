from PIL import Image
from dataclasses import dataclass

UPPERCASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWERCASE = "abcdefghijklmnopqrstuvwxyz"
DIGITS = """1234567890!"#%'()~+-/[]<>:.,_| """


@dataclass
class Glyph:
    """ Represents a single character glyph in a pixel font.
    """
    char: str
    width: int
    height: int
    pixels: list[list[bool]]


class Font:
    """ Represents a pixel font, containing a mapping
    of characters to their corresponding Glyph objects.
    """
    def __init__(self, glyphs: dict[str, Glyph]):
        """ Initializes a Font object with a dictionary of glyphs.

        Args:
            glyphs (dict[str, Glyph]): A dictionary mapping characters
            to their corresponding Glyph objects
        """
        self.glyphs = glyphs

    @classmethod
    def _font_loader(cls,
                     uppercase_path: str,
                     lowercase_path: str,
                     digits_path: str
                     ) -> 'Font':
        """ laods font from image files and returns a Font object.

        Args:
            uppercase_path (str): _path to the image file
            containing uppercase letters
            lowercase_path (str): _path to the image file
            containing lowercase letters
            digits_path (str): _path to the image file
            containing digits and special characters

        Returns:
            Font: Font object containing the loaded glyphs
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
        """ Parses a glyph image and returns a list of Glyph objects.

        Args:
            path (str): _path to the image file containing the glyphs
            charset (str): _characters represented in the glyph image
            glyph_w (int): _width of each glyph in pixels
            glyph_h (int): _height of each glyph in pixels

        Raises:
            ValueError: If the image cannot be loaded.

        Returns:
            list[Glyph]: A list of Glyph objects representing
            the characters in the charset
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
                    pixel = True if raw[
                        i * glyph_w + x, y][3] > 0 else False  # type: ignore
                    row.append(pixel)
                pixels.append(row)
            glyphs.append(Glyph(char, glyph_w, glyph_h, pixels))
        return glyphs
