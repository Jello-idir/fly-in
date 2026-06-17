import signal
import sys
from Visualize import *
from MLX.libmlx import *
from enum import Enum
from MapParser import MapData
from Tools import *
from PIL import Image
from PixelFont import load_font
from Common import RenderConfig


# COLORS
# ---------------------------------
BLUE   = 0x729AFF << 8 | 0xff
GREEN  = 0x59AE6D << 8 | 0xff
RED    = 0xFE8282 << 8 | 0xff
YELLOW = 0xFFFB84  << 8 | 0xff
ORANGE = 0xFBA951  << 8 | 0xff
# ------------------------------


def load_shape_from_png(path: str) -> set[tuple[int, int, int]]:
    img = Image.open(path).convert("RGBA")
    points = set()
    for y in range(img.height):
        for x in range(img.width):
            pixel = img.getpixel((x, y))  # type: ignore
            if pixel[3] > 0:  # type: ignore
                r, g, b, a = pixel  # type: ignore
                color = (r << 24) + (g << 16) + (b << 8) + a
                points.add((x, y, color))
    return points


class SHAPE(set[tuple[int, int, int]], Enum):
    def __call__(self):
        return self.value
    drone = load_shape_from_png("Assets/drone.png")
    hub = load_shape_from_png("Assets/hub.png")
    hub_restricted = load_shape_from_png("Assets/hub_restricted.png")


def signal_handler(sig, frame):
    mlx.mlx_terminate(window.mlx_ptr)


def _init_cfg(mapdata: MapData) -> RenderConfig:
    min_x, max_x, min_y, max_y = mapdata.bounding_box
    size_x = max_x - min_x + 1
    size_y = max_y - min_y + 1
    cell = 40
    space = 3
    padd_x = 2
    padd_y = 2

    space = space + 1
    cell_w = size_x * space - space + 1 + padd_x * 2
    cell_h = size_y * space - space + 1 + padd_y * 2
    width = cell_w * cell
    height = cell_h * cell

    font = load_font()

    return RenderConfig(
        width=width,
        height=height,
        cell=cell,
        cell_abs=cell,
        cell_w=cell_w,
        cell_h=cell_h,
        mid_h=cell_h // 2,
        mid_w=cell_w // 2,
        space=space,
        min_x=min_x * space,
        min_y=min_y * space,
        padd_x=padd_x,
        padd_y=padd_y,
        font=font,
        drone_shape=SHAPE.drone(),
        hub_shape=SHAPE.hub(),
        hub_restricted_shape=SHAPE.hub_restricted()
    )



if __name__ == "__main__":
    # Set up signal handler for graceful exit on Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    # ---------------------------------------

    # parsing
    try:
        mapdata = MapData.from_file("maps/tst.txt" \
        "")
    except Exception as e:
        sys.stderr.write(f"\033[31mError:\033[0m {e}\n")
        sys.exit(1)
    #-------------------------------------

    # config init
    cfg = _init_cfg(mapdata)

    # mlx window init
    try:
        window = MlxWindow.from_map(mapdata, cfg)
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)

    # title, grid and tiling
    tile = load_shape_from_png("Assets/ground.png")
    window.tilify(tile)

    # mlx run
    solution = open("solution.txt").read()
    window.run(solution)
    #window.display(with_name=True, with_stats=True)
    # -----------
