import signal
import sys
import time
from display import *
from MLX.libmlx import *
from enum import Enum
from parsing import MapParser
from tools import *


# COLORS
# ---------------------------------
C_BG = (0x262626 << 8) + 0xff
C_FG = (0xDEDEDE << 8) + 0xff
C_GRID = (0x2E2E2E << 8) + 0xff
# ---------------------------------
BLUE   = (0x729AFF << 8) + 0xff
GREEN  = (0x59AE6D << 8) + 0xff
RED    = (0xFE8282 << 8) + 0xff
YELLOW = (0xFFFB84  << 8) + 0xff
ORANGE = (0xFBA951  << 8) + 0xff
# ------------------------------


class SHAPE(list[tuple[int, int]], Enum):
    def __call__(self):
        return self.value
    drone = [
        (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (3, 1)
        ]
    hub = [
        (0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (3, 2),
        (4, 2), (5, 2), (6, 2), (7, 2), (7, 1), (7, 0),
        (0, 4), (1, 4), (2, 4), (3, 4), (4, 4), (5, 4),
        (6, 4), (7, 4)
        ]


def signal_handler(sig, frame):
    mlx.mlx_terminate(window.mlx_ptr)


def init_cfg():
    return {
        "width": 2048,
        "height": 1024,
        "pxl": 4,
        "cell": 8
    }


def init_window(cfg: dict[str, int]) -> MlxMngr:
    global window
    try:
        window = MlxMngr(cfg)
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)
    return window


if __name__ == "__main__":
    # Set up signal handler for graceful exit on Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    # ---------------------------------------

    # parsing
    filename = "Assets/test.txt"
    try:
        map = MapParser(filename)
        map.parse()
        map.validate()
    except Exception as e:
        sys.stderr.write(f"\033[31mError:\033[0m {e}\n")
        sys.exit(1)

    sys.stdout.write(f"\nparsing {filename.split("/")[-1]}\n\n")
    tree(map.map_data)
    sys.stdout.write("\n")
    #-------------------------------------

    sys.exit(0)


    # data and mlx window init
    cfg = init_cfg()
    window = init_window(cfg)
    # --------------------------


    window.gridify(cfg["cell"], C_BG, C_GRID)
    drone1 = Drone(window.mlx_ptr, "d1", SHAPE.drone, (2, 2), C_FG, cfg)
    hub1 = Hub(window.mlx_ptr, "h1", SHAPE.hub, (10, 5), GREEN, cfg)
    hub2 = Hub(window.mlx_ptr, "h1", SHAPE.hub, (20, 10), BLUE, cfg)
    window.attach([drone1, hub1, hub2])

    # mlx run
    window.run()
    # -----------
