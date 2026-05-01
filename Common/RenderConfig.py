from dataclasses import dataclass


@dataclass
class RenderConfig:
    width: int
    height: int
    pxl: int
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
    shadow: int
    font: dict[str, set[tuple[int, int]]]
