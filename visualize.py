import signal
import logging
import time
from math import sqrt
from MLX.libmlx import *
from enum import Enum
from collections.abc import Callable
import sys



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

# CONSTS
# ------------
WIDTH = 2048
HEIGHT = 1024
P_SIZE = 4
G_SIZE = 8

PIX_W = WIDTH // P_SIZE
PIX_H = HEIGHT // P_SIZE

SEG_W = WIDTH // (P_SIZE * G_SIZE)
SEG_H = HEIGHT // (P_SIZE * G_SIZE)
# ------------

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

# mlx hook for testing debuggin
# -------------------------------------------------------------
@mlx_loop_hook_func
def ft_hook(param):
    mlx_ptr = ctypes.cast(param, ctypes.POINTER(mlx_t))

    if mlx.mlx_is_key_down(mlx_ptr, MLX_KEY_TAB):
        current = manager.drones[1]
    if mlx.mlx_is_key_down(mlx_ptr, MLX_KEY_ESCAPE):
        mlx.mlx_close_window(mlx_ptr)
    if mlx.mlx_is_key_down(mlx_ptr, MLX_KEY_UP):
        current.contents.instances[0].y -= P_SIZE
    if mlx.mlx_is_key_down(mlx_ptr, MLX_KEY_DOWN):
        current.contents.instances[0].y += P_SIZE
    if mlx.mlx_is_key_down(mlx_ptr, MLX_KEY_LEFT):
        current.contents.instances[0].x -= P_SIZE
    if mlx.mlx_is_key_down(mlx_ptr, MLX_KEY_RIGHT):
        current.contents.instances[0].x += P_SIZE
# -------------------------------------------------------------

# grid drawin
# --------------------------------------------------------------


# --------------------------------------------------------------


class MlxMngr:
    def __init__(self):
        assert WIDTH % (P_SIZE * G_SIZE) == 0 and HEIGHT % (P_SIZE * G_SIZE) == 0, \
            f"WIDTH and HEIGHT must be multiples of PIXEL_SIZE * GRID_SIZE ({P_SIZE * G_SIZE})"
        self.mlx = mlx.mlx_init(WIDTH, HEIGHT, b"Fly-in", True)
        self.hubs = []
        self.drones = []

    def grid(self, step, bg_color, lines_color):
        grid = mlx.mlx_new_image(self.mlx, WIDTH, HEIGHT)
        step = step * P_SIZE
        for y in range(0, HEIGHT, step):
            for x in range(0, WIDTH, step):
                for j in range(y, y + step):
                    for i in range(x, x + step):
                        mlx.mlx_put_pixel(grid, i, j, bg_color)
                for j in range(y, y + step):
                    mlx.mlx_put_pixel(grid, x, j, lines_color)
                for i in range(x, x + step):
                    mlx.mlx_put_pixel(grid, i, y, lines_color)
        mlx.mlx_image_to_window(self.mlx, grid, 0, 0)


    def new_drone(self, pos):
        drone = Drone(self.mlx, (pos[0] * G_SIZE, pos[1] * G_SIZE))
        drone.attach(self.mlx)
        drone.draw()
        self.drones.append(drone)

    def new_hub(self, pos):
        hub = Hub(self.mlx, (pos[0] * G_SIZE, pos[1] * G_SIZE))
        hub.attach(self.mlx)
        hub.draw()
        self.hubs.append(hub)



class Entity:
    def __init__(self, mlx_ptr, shape: SHAPE, pos, size, color):
        self.pos = pos
        self.shape = shape.value
        self.color = color
        self.img = mlx.mlx_new_image(mlx_ptr, size[0] * P_SIZE, size[1] * P_SIZE)

    def attach(self, frame):
        mlx.mlx_image_to_window(frame, self.img, self.pos[0] * P_SIZE, self.pos[1] * P_SIZE)

    def draw(self):
        for pixel in self.shape:
            for j in range(pixel[1] * P_SIZE, (pixel[1] + 1) * P_SIZE):
                for i in range(pixel[0] * P_SIZE, (pixel[0] + 1) * P_SIZE):
                    mlx.mlx_put_pixel(self.img, i, j, self.color)

    def fill(self, color):
        for y in range(self.img.contents.height):
            for x in range(self.img.contents.width):
                mlx.mlx_put_pixel(self.img, x, y, color)

    def move_to(self, xy):
        self.pos = xy
        self.img.contents.instances[0].x = xy[0] * P_SIZE
        self.img.contents.instances[0].y = xy[1] * P_SIZE



class Hub(Entity):
    def __init__(self, mlx_ptr, pos: tuple[int, int] = (0, 0)):
        super().__init__(
            mlx_ptr, SHAPE.hub,
            (
                pos[0] + (G_SIZE // 2 - 4),
                pos[1] + (G_SIZE // 2 - 2)),
                (8, 5),
                GREEN)


class Drone(Entity):
    def __init__(self, mlx_ptr, pos: tuple[int, int] = (0, 0)):
        super().__init__(
            mlx_ptr, SHAPE.drone,
            (
                pos[0] + (G_SIZE // 2 - 2),
                pos[1] + (G_SIZE // 2 - 1)),
                (4, 2),
                BLUE)


def main():
    global manager


    try:
        manager = MlxMngr()
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)

    # Create a grid
# --------------------------------------------------------------
    manager.grid(G_SIZE, C_BG, C_GRID)
# --------------------------------------------------------------


    # manager with list of hubs and drones
# --------------------------------------------------------------
    manager.new_drone((0, 0))
    manager.new_drone((SEG_W - 1, SEG_H - 1))
    manager.new_hub((SEG_W // 2, SEG_H // 2))

# --------------------------------------------------------------



# mlx loop
# --------------------------------------------------------------
    mlx.mlx_loop(manager.mlx)
    mlx.mlx_terminate(manager.mlx)
# --------------------------------------------------------------


# When receiving SIGINT (Ctrl+C), terminate MLX properly
# Otherwise we get issues related to callbacks as MLX is trying
# invoke it during termination.
# --------------------------------------------------------------
def signal_handler(sig, frame):
    mlx.mlx_terminate(manager.mlx)
# --------------------------------------------------------------

# --------------------------------------------------------------
if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()
# --------------------------------------------------------------

#
