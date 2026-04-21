import signal
from MLX.libmlx import *
from enum import Enum
import sys


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


class Entity:
    def __init__(
            self, mlx_ptr, shape: list[tuple[int, int]],
            cell_pos: tuple[int, int],
            px_size: tuple[int, int],
            color: int,
            data: dict[str, int],
            align: bool = True
            ):
        self.data = data
        self.px_size = px_size
        self.abs_size = (px_size[0] * self.data["pxl"], px_size[1] * self.data["pxl"])
        self.cell_pos = cell_pos
        self.px_pos = (cell_pos[0] * self.data["cell"], cell_pos[1] * self.data["cell"])
        if align:
            self.abs_pos = ((self.px_pos[0] + self.data["cell"] // 2 - self.px_size[0] // 2) * self.data["pxl"],
                            (self.px_pos[1] + self.data["cell"] // 2 - self.px_size[1] // 2) * self.data["pxl"])
        else:
            self.abs_pos = (self.px_pos[0] * self.data["pxl"], self.px_pos[1] * self.data["pxl"])
        self.shape = shape
        self.color = color
        self.img = mlx.mlx_new_image(mlx_ptr, self.abs_size[0], self.abs_size[1])

    def attach(self, window):
        mlx.mlx_image_to_window(window, self.img, self.abs_pos[0], self.abs_pos[1])

    def draw(self):
        for pixel in self.shape:
            for j in range(pixel[1] * self.data["pxl"], (pixel[1] + 1) * self.data["pxl"]):
                for i in range(pixel[0] * self.data["pxl"], (pixel[0] + 1) * self.data["pxl"]):
                    mlx.mlx_put_pixel(self.img, i, j, self.color)

    def fill(self, color: int = 0xffffffff):
        for y in range(self.img.contents.height):
            for x in range(self.img.contents.width):
                mlx.mlx_put_pixel(self.img, x, y, color)


class Drone(Entity):
    def __init__(self, mlx_ptr, cell_pos: tuple[int, int], shape: list[tuple[int, int]], color: int, data: dict[str, int]):
        super().__init__(
            mlx_ptr, shape, (cell_pos[0], cell_pos[1]), (4, 2), color, data
            )

class Hub(Entity):
    def __init__(self, mlx_ptr, cell_pos: tuple[int, int], shape: list[tuple[int, int]], color: int, data: dict[str, int]):
        super().__init__(
            mlx_ptr, shape, (cell_pos[0], cell_pos[1]), (8, 5), color, data
            )


class MlxMngr:
    def __init__(self, data):
        self.mlx_ptr = mlx.mlx_init(data["width"], data["height"], b"Fly-in", True)
        self.hubs: list[Hub] = []
        self.drones: list[Entity ]= []
        self.data: dict[str, int] = data

    def grid(self, step, bg_color, lines_color):
        grid = mlx.mlx_new_image(self.mlx_ptr, self.data["width"], self.data["height"])
        step = step * self.data["pxl"]
        for y in range(0, self.data["height"], step):
            for x in range(0, self.data["width"], step):
                for j in range(y, y + step):
                    for i in range(x, x + step):
                        mlx.mlx_put_pixel(grid, i, j, bg_color)
                for j in range(y, y + step):
                    mlx.mlx_put_pixel(grid, x, j, lines_color)
                for i in range(x, x + step):
                    mlx.mlx_put_pixel(grid, i, y, lines_color)
        mlx.mlx_image_to_window(self.mlx_ptr, grid, 0, 0)


    def attach(self, entity: Entity):
        entity.attach(self.mlx_ptr)
        entity.draw()
        if isinstance(entity, Drone):
            self.drones.append(entity)
        elif isinstance(entity, Hub):
            self.hubs.append(entity)

    def run(self):
        mlx.mlx_loop(self.mlx_ptr)
        mlx.mlx_terminate(self.mlx_ptr)


def main():
    global WIDTH, HEIGHT, PXL, CELL, manager
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



# mlx loop
# --------------------------------------------------------------
    manager.run()
# --------------------------------------------------------------


# When receiving SIGINT (Ctrl+C), terminate MLX properly
# Otherwise we get issues related to callbacks as MLX is trying
# invoke it during termination.
# --------------------------------------------------------------
def signal_handler(sig, frame):
    mlx.mlx_terminate(manager.mlx_ptr)
# --------------------------------------------------------------

# --------------------------------------------------------------
if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()
# --------------------------------------------------------------
