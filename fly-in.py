import signal
import sys
import time
from display import *
from MLX.libmlx import *
from enum import Enum
from parsing import MapParser
from tools import *
from PIL import Image
from PixelFont import load_font


# COLORS
# ---------------------------------
C_BG = (0x2F2F2F << 8) + 0xff
C_FG = (0xDEDEDE << 8) + 0xff
C_GRID = (0x181818 << 8) + 0xff
# ---------------------------------
BLUE   = (0x729AFF << 8) + 0xff
GREEN  = (0x59AE6D << 8) + 0xff
RED    = (0xFE8282 << 8) + 0xff
YELLOW = (0xFFFB84  << 8) + 0xff
ORANGE = (0xFBA951  << 8) + 0xff
# ------------------------------


# dict color
COLORS: dict[str, int] = {
    # basics
    "none":        (0x000000 << 8) + 0xFF,
    "black":       (0x000000 << 8) + 0xFF,
    "white":       (0xFFFFFF << 8) + 0xFF,
    "gray":        (0x808080 << 8) + 0xFF,
    "grey":        (0x808080 << 8) + 0xFF,
    # reds
    "red":         (0xFF4242 << 8) + 0xFF,
    "darkred":     (0xB42F2F << 8) + 0xFF,
    "crimson":     (0xFF496E << 8) + 0xFF,
    "maroon":      (0x922424 << 8) + 0xFF,
    # oranges
    "orange":      (0xFF8C00 << 8) + 0xFF,
    "darkorange":  (0xFF6600 << 8) + 0xFF,
    "coral":       (0xFF6B6B << 8) + 0xFF,
    "salmon":      (0xFA8072 << 8) + 0xFF,
    # yellows
    "yellow":      (0xFFFF00 << 8) + 0xFF,
    "gold":        (0xFFD700 << 8) + 0xFF,
    "khaki":       (0xC3B091 << 8) + 0xFF,
    # greens
    "green":       (0x2DFF2D << 8) + 0xFF,
    "darkgreen":   (0x006400 << 8) + 0xFF,
    "lime":        (0x00FF00 << 8) + 0xFF,
    "olive":       (0x808000 << 8) + 0xFF,
    "teal":        (0x008080 << 8) + 0xFF,
    # blues
    "blue":        (0x0000FF << 8) + 0xFF,
    "darkblue":    (0x00008B << 8) + 0xFF,
    "navy":        (0x000080 << 8) + 0xFF,
    "cyan":        (0x00FFFF << 8) + 0xFF,
    "skyblue":     (0x87CEEB << 8) + 0xFF,
    "aqua":        (0x00FFFF << 8) + 0xFF,
    # purples
    "purple":      (0x800080 << 8) + 0xFF,
    "violet":      (0x7F00FF << 8) + 0xFF,
    "magenta":     (0xFF00FF << 8) + 0xFF,
    "lavender":    (0xB57EDC << 8) + 0xFF,
    "indigo":      (0x4B0082 << 8) + 0xFF,
    "plum":        (0x8E4585 << 8) + 0xFF,
    # pinks
    "pink":        (0xFF69B4 << 8) + 0xFF,
    "hotpink":     (0xFF1493 << 8) + 0xFF,
    "fuchsia":     (0xFF00FF << 8) + 0xFF,
    # browns
    "brown":       (0x8B4513 << 8) + 0xFF,
    "tan":         (0xD2B48C << 8) + 0xFF,
    "beige":       (0xF5F0DC << 8) + 0xFF,
    "chocolate":   (0xD2691E << 8) + 0xFF,
    # special
    "rainbow":     (0xFFFFFF << 8) + 0xFF,
}

def load_shape_from_png(path: str) -> set[tuple[int, int, int]]:
    img = Image.open(path).convert("RGBA")
    points = set()
    for y in range(img.height):
        for x in range(img.width):
            pixel = img.getpixel((x, y))  # type: ignore
            if pixel[3] > 0:  # type: ignore
                r, g, b, a = pixel  # type: ignore
                color = (r << 24) | (g << 16) | (b << 8) | a
                points.add((x, y, color))
    return points


class SHAPE(set[tuple[int, int, int]], Enum):
    def __call__(self):
        return self.value
    #drone = load_shape_from_png("Assets/pixel_objects/drone.png")
    #hub = load_shape_from_png("Assets/pixel_objects/ball.png")
    hub = {(i, j, 0xffffffff) for i in range(6) for j in range(6)}




def signal_handler(sig, frame):
    mlx.mlx_terminate(window.mlx_ptr)


def init_cfg(data: dict) -> dict[str, int]:

    min_x, max_x, min_y, max_y = data["bounding_box"]
    size_x = max_x - min_x + 1
    size_y = max_y - min_y + 1

    pxl = 1
    cell = 20
    space = 4
    padd_x = 4
    padd_y = 4

    cell_w = size_x * space - space + 1 + padd_x * 2
    cell_h = size_y * space - space + 1 + padd_y * 2
    width = cell_w * cell * pxl
    height = cell_h * cell * pxl

    return {
        "width": width,
        "height": height,
        "pxl": pxl,
        "cell": cell,
        "cell_abs": cell * pxl,
        "cell_w": cell_w,
        "cell_h": cell_h,
        "mid_h": cell_h // 2,
        "mid_w": cell_w // 2,
        "space": space,
        "min_x": min_x * space,
        "min_y": min_y * space,
        "padd_x": padd_x,
        "padd_y": padd_y,
    }


def init_window(cfg: dict[str, int]) -> MlxWindow:
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
    filename = "Assets/the_impossible_dream.txt"
    try:
        map = MapParser(filename)
        map.parse()
        map.validate()
        map.calculate()
    except Exception as e:
        sys.stderr.write(f"\033[31mError:\033[0m {e}\n")
        sys.exit(1)


    #-------------------------------------
    #tree(map.data)


    # data and mlx window init
    cfg = init_cfg(map.data)

    font = load_font()
    debug(font["B"], cfg)
    sys.exit(0)

    window = init_window(cfg)
    # --------------------------


    # grid mlx
    window.gridify(cfg["cell"], C_BG, C_GRID)

    # display hubs in map using manager
    for k, v in map.data["hubs"].items():
        x, y = v["pos"]
        h = Hub(
            window.mlx_ptr,
            k,
            SHAPE.hub,
            (
                x * cfg["space"] + -cfg["min_x"] + cfg["padd_x"],
                y * cfg["space"] + -cfg["min_y"] + cfg["padd_y"]
            ),
            cfg,
            )
        window.attach_draw([h], name_on=True, hitbox_on=True)

    # connection part
    for a, b, _ in map.data["connections"]:
        window.connect(a, b, COLORS["white"])

    # mlx run
    window.run()
    # -----------
