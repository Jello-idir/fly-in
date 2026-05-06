from dataclasses import dataclass
from PixelFont import Glyph

@dataclass
class RenderConfig:
    width: int
    height: int
    cell: int
    cell_abs: int
    cell_w: int
    cell_h: int
    mid_h: int
    mid_w: int
    space: int
    min_x: int
    min_y: int
    padd_x: int
    padd_y: int
    font: dict[str, Glyph]
    drone_shape: set[tuple[int, int, int]]
    hub_shape: set[tuple[int, int, int]]
