from dataclasses import dataclass
from PixelFont import Glyph
from Common import Shapes


@dataclass
class RenderConfig:
    width: int
    height: int
    cell: int
    space: int
    min_x: int
    min_y: int
    padd_x: int
    padd_y: int
    font: dict[str, Glyph]
    shapes: type[Shapes]
