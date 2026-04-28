from PIL import Image
import os

UPPERCASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWERCASE = "abcdefghijklmnopqrstuvwxyz"
DIGITS    = """0123456789.,!?'"-_:; """


def _load_strip(
        path: str, charset: str,
        glyph_w,
        glyph_h,
        ) -> dict[str, set[tuple[int, int]]]:
    img = Image.open(path).convert("RGBA")
    pixels = img.load()
    glyphs: dict[str, set[tuple[int, int]]] = {}

    for idx, char in enumerate(charset):
        x_off = idx * glyph_w
        coords: set[tuple[int, int]] = set()
        for row in range(glyph_h):
            for col in range(glyph_w):
                _, _, _, a = pixels[x_off + col, row]  # type: ignore
                if a > 0:
                    coords.add((col, row))
        glyphs[char] = coords
    return glyphs

def load_font() -> dict[str, set[tuple[int, int]]]:
    base = os.path.dirname(os.path.abspath(__file__))
    glyphs: dict[str, set[tuple[int, int]]] = {}
    glyphs.update(
        _load_strip(
            os.path.join(
                base,
                "glyphs/uppercase.png"),
                UPPERCASE,
                9, 12,
                )
                )

    glyphs.update(
        _load_strip(
            os.path.join(
                base,
                "glyphs/lowercase.png"),
                LOWERCASE,
                8, 12
                )
                )

    glyphs.update(
        _load_strip(
            os.path.join(
                base,
                "glyphs/digits.png"),
                DIGITS,
                9, 12
                )
                )

    return glyphs
