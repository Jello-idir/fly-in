import signal
import sys
from Visualize import *
from MLX.libmlx import *
from enum import Enum
from MapParser import MapData
from MyTools import *
from PIL import Image
from PixelFont import load_font
from Common import RenderConfig


# COLORS
# ---------------------------------
C_BG = (0x303338 << 8) + 0xff
C_FG = (0xDEDEDE << 8) + 0xff
C_GRID = (0x191A1C << 8) + 0xff
# ---------------------------------
BLUE   = (0x729AFF << 8) + 0xff
GREEN  = (0x59AE6D << 8) + 0xff
RED    = (0xFE8282 << 8) + 0xff
YELLOW = (0xFFFB84  << 8) + 0xff
ORANGE = (0xFBA951  << 8) + 0xff
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


def signal_handler(sig, frame):
    mlx.mlx_terminate(window.mlx_ptr)


def _init_cfg(map: MapData) -> RenderConfig:
    min_x, max_x, min_y, max_y = map.bounding_box
    size_x = max_x - min_x + 1
    size_y = max_y - min_y + 1

    pxl = 1
    cell = 32
    space = 5
    padd_x = space // 2 + 1
    padd_y = space // 2 + 1
    shadow = 0

    cell_w = size_x * space - space + 1 + padd_x * 2
    cell_h = size_y * space - space + 1 + padd_y * 2
    width = cell_w * cell * pxl
    height = cell_h * cell * pxl

    font = load_font()

    return RenderConfig(
        width=width,
        height=height,
        pxl=pxl,
        cell=cell,
        cell_abs=cell * pxl,
        cell_w=cell_w,
        cell_h=cell_h,
        mid_h=cell_h // 2,
        mid_w=cell_w // 2,
        space=space,
        min_x=min_x * space,
        min_y=min_y * space,
        padd_x=padd_x,
        padd_y=padd_y,
        shadow=shadow,
        font=font
    )


def init_window(cfg) -> MlxWindow:
    global window
    try:
        window = MlxWindow(cfg)
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)
    return window


if __name__ == "__main__":
    # Set up signal handler for graceful exit on Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    # ---------------------------------------

    # parsing
    try:
        map = MapData.from_file("maps/the_impossible_dream.txt")
    except Exception as e:
        sys.stderr.write(f"\033[31mError:\033[0m {e}\n")
        sys.exit(1)
    #-------------------------------------


    # config init
    cfg = _init_cfg(map)


    # mlx window init
    window = init_window(cfg)


    # title, grid and tiling
    tile = load_shape_from_png("Assets/ground.png")
    window.gridify(cfg.cell, C_BG, C_GRID)
    #window.tilify(tile)

    # window.pixel_putstr(
    #     font, "FLY-IN",
    #     (7, 20), COLORS["white"]
    #     )

    # display hubs in map using manager
    for hub_name, hub in map.hubs.items():
        x, y = hub.pos
        h = Hub(
            window.mlx_ptr,
            hub_name,
            SHAPE.hub,
            (
                x * cfg.space + -cfg.min_x + cfg.padd_x,
                y * cfg.space + -cfg.min_y + cfg.padd_y
            ),
            cfg,
            color=hub.metadata.color,
            )
        window.draw_add_entity(h, hitbox_on=False)

    for drone in map.drones:
        x, y = drone.pos
        d = Drone(
            window.mlx_ptr,
            str(drone.id),
            SHAPE.drone,
            (
                x * cfg.space + -cfg.min_x + cfg.padd_x,
                y * cfg.space + -cfg.min_y + cfg.padd_y
            ),
            cfg,
            color=drone.color
        )
        window.draw_add_entity(d, hitbox_on=False)


    # connection part
    for conn in map.connections:
        window.connect(conn.hub_a, conn.hub_b, 0xffffffff)

    # mlx run
    window.display(with_label=True)
    # -----------
