from dataclasses import dataclass
from PixelFont import Glyph
from Common import Shapes


@dataclass
class RenderConfig:
    window_size: tuple[int, int]
    min_coord: tuple[int, int]
    paddin: tuple[int, int]
    cell: int
    space: int
    font: dict[str, Glyph]
    shapes: type[Shapes]
