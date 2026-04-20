import signal
import logging
import time
from math import sqrt
from MLX.libmlx import *
from enum import Enum


class SHAPE(Enum):
    drone = [
        (1, 0),
        (2, 0),
        (0, 1),
        (1, 1),
        (2, 1),
        (3, 1)
    ]
    hub = [
        (0, 0),
        (0, 1),
        (0, 2),
        (1, 2),
        (2, 2),
        (3, 2),
        (4, 2),
        (5, 2),
        (6, 2),
        (7, 2),
        (7, 1),
        (7, 0),
        (0, 4),
        (1, 4),
        (2, 4),
        (3, 4),
        (4, 4),
        (5, 4),
        (6, 4),
        (7, 4)
    ]

# CONSTS
WIDTH = 1024
HEIGHT = 512
PX = 4
# ------------

# COLORS
BLUE   = (0x729AFF << 8) + 0xff
GREEN  = (0x59AE6D << 8) + 0xff
RED    = (0xFE8282 << 8) + 0xff
YELLOW = (0xFFFB84  << 8) + 0xff
ORANGE = (0xFBA951  << 8) + 0xff

BG = (0x262626 << 8) + 0xff
FG = (0xDEDEDE << 8) + 0xff
GD = (0x2E2E2E << 8) + 0xff

# ------------------------------


@mlx_loop_hook_func
def ft_hook(param):
    mlx_ptr = ctypes.cast(param, ctypes.POINTER(mlx_t))

    if mlx.mlx_is_key_down(mlx_ptr, MLX_KEY_TAB):
        current = manager.drones[1]

    if mlx.mlx_is_key_down(mlx_ptr, MLX_KEY_ESCAPE):
        mlx.mlx_close_window(mlx_ptr)

    if mlx.mlx_is_key_down(mlx_ptr, MLX_KEY_UP):
        current.contents.instances[0].y -= PX
    if mlx.mlx_is_key_down(mlx_ptr, MLX_KEY_DOWN):
        current.contents.instances[0].y += PX
    if mlx.mlx_is_key_down(mlx_ptr, MLX_KEY_LEFT):
        current.contents.instances[0].x -= PX
    if mlx.mlx_is_key_down(mlx_ptr, MLX_KEY_RIGHT):
        current.contents.instances[0].x += PX


def fill_with_color(img, color):
    for y in range(img.contents.height):
        for x in range(img.contents.width):
            mlx.mlx_put_pixel(img, x, y, color)


def draw_rec(img, xy, wh, color):
    for j in range(xy[1], xy[1] + wh[1]):
        for i in range(xy[0], xy[0] + wh[0]):
            mlx.mlx_put_pixel(img, i, j, color)


def draw_rec_pixelart(img, xy, wh, color):
    for y in range(xy[1], xy[1] + wh[1]):
        for x in range(xy[0], xy[0] + wh[0]):
            draw_rec(img, (xy[0] * PX, xy[1] * PX), (wh[0] * PX, wh[1] * PX), color)


def draw_shape(shape, pixels, color):
    for p in pixels:
        draw_rec(shape, (p[0] * PX, p[1] * PX), (PX, PX), color)


def draw_grid(img, step, color):
    for y in range(0, img.contents.height):
        for x in range(0, img.contents.width):
            if x % step == 0 or y % step == 0:
                mlx.mlx_put_pixel(img, x, y, color)


class Entity:
    def __init__(self, shape: SHAPE, xy, img_w, img_h, color):
        self.pos = xy
        self.shape = shape.value
        self.color = color
        self.img = mlx.mlx_new_image(mlx_ptr, img_w * PX, img_h * PX)

    def attach(self, frame):
        mlx.mlx_image_to_window(frame, self.img, self.pos[0] * PX, self.pos[1] * PX)

    def draw(self):
        draw_shape(self.img, self.shape, self.color)

    def move_to(self, xy):
        self.pos = xy
        self.img.contents.instances[0].x = xy[0] * PX
        self.img.contents.instances[0].y = xy[1] * PX

class Manager:
    def __init__(self):
        self.hubs = []
        self.drones = []


class Hub(Entity):
    def __init__(self):
        super().__init__(SHAPE.hub, (0, 3), 8, 5, GREEN)


class Drone(Entity):
    def __init__(self):
        super().__init__(SHAPE.drone, (2, 2), 4, 2, BLUE)


def main():
    # Better to encapsulate in a class, but keeping it simple for the example
    global mlx_ptr
    global manager

    # Initialize MLX
    mlx_ptr = mlx.mlx_init(WIDTH, HEIGHT, b"Fly-in", True)

    # Create a grid
    grid = mlx.mlx_new_image(mlx_ptr, WIDTH, HEIGHT)
    fill_with_color(grid, BG)
    draw_grid(grid, 32, GD)
    mlx.mlx_image_to_window(mlx_ptr, grid, 0, 0)


    # manager with list of hubs and drones
    manager = Manager()

    hub1 = Hub()
    hub1.attach(mlx_ptr)
    hub1.draw()
    manager.hubs.append(hub1)


    drone1 = Drone()
    drone1.attach(mlx_ptr)
    drone1.draw()
    manager.drones.append(drone1)


    #draw_rec(img, (64, 32), (WIDTH - 64 * 2, 16), FG)
    #draw_rec_pixelart(squar, (1, 1), (2, 2), BLUE)


    mlx.mlx_loop_hook(mlx_ptr, ft_hook, ctypes.cast(mlx_ptr, c_void_p))
    mlx.mlx_loop(mlx_ptr)
    mlx.mlx_terminate(mlx_ptr)



# When receiving SIGINT (Ctrl+C), terminate MLX properly
# Otherwise we get issues related to callbacks as MLX is trying
# invoke it during termination.
def signal_handler(sig, frame):
    mlx.mlx_terminate(mlx_ptr)

# ============================================================================

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()
