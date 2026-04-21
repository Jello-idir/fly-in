# import logging
import signal
import sys
import time
from display import *
from collections.abc import Callable
from display import *
from MLX.libmlx import *
from enum import Enum



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



class SHAPE(Enum):
    drone = [
        (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (3, 1)
        ]
    hub = [
        (0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (3, 2),
        (4, 2), (5, 2), (6, 2), (7, 2), (7, 1), (7, 0),
        (0, 4), (1, 4), (2, 4), (3, 4), (4, 4), (5, 4),
        (6, 4), (7, 4)
        ]


def main():
    global manager
    WIDTH = 1024
    HEIGHT = 512
    PXL = 4
    CELL = 8

    data = {
        "width": WIDTH,
        "height": HEIGHT,
        "pxl": PXL,
        "cell": CELL
    }

    try:
        manager = MlxMngr(data)
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)

    # Create a grid
# --------------------------------------------------------------
    manager.grid(CELL, C_BG, C_GRID)
# --------------------------------------------------------------


    # manager with list of hubs and drones
# --------------------------------------------------------------
    drone1 = Drone(manager.mlx_ptr, (2, 2), SHAPE.drone.value, BLUE, data)
    hub1 = Hub(manager.mlx_ptr, (10, 5), SHAPE.hub.value, RED, data)
    manager.attach(drone1)
    manager.attach(hub1)

# --------------------------------------------------------------






    manager.run()

def signal_handler(sig, frame):
    mlx.mlx_terminate(manager.mlx_ptr)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()
