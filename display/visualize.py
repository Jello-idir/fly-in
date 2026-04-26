from MLX.libmlx import *
import sys

class Entity:
    def __init__(
            self, mlx_ptr, name: str,
            shape: set[tuple[int, int, int]],
            cell_pos: tuple[int, int],
            px_size: tuple[int, int],
            cfg: dict[str, int],
            align: bool = True
            ):
        self.name = name
        self.cfg = cfg
        self.px_size = px_size
        self.abs_size = (px_size[0] * self.cfg["pxl"], px_size[1] * self.cfg["pxl"])
        self.cell_pos = cell_pos
        self.px_pos = (cell_pos[0] * self.cfg["cell"], cell_pos[1] * self.cfg["cell"])
        self.abs_pos = (
            self.px_pos[0] * self.cfg["pxl"],
            self.px_pos[1] * self.cfg["pxl"]
        )
        if align:
            self.abs_pos = (
                self.abs_pos[0] + self.cfg["cell_abs"] // 2 - self.abs_size[0] // 2,
                self.abs_pos[1] + self.cfg["cell_abs"] // 2 - self.abs_size[1] // 2
            )

        self.shape_pos = (
            self.abs_pos[0] + self.abs_size[0] // 2,
            self.abs_pos[1] + self.abs_size[1] // 2
        )
        self.shape = shape
        self.img = mlx.mlx_new_image(mlx_ptr, self.abs_size[0], self.abs_size[1])

    def attach(self, window):
        mlx.mlx_image_to_window(window, self.img, self.abs_pos[0], self.abs_pos[1])

    def draw(self):
        for pixel in self.shape:
            for j in range(pixel[1] * self.cfg["pxl"], (pixel[1] + 1) * self.cfg["pxl"]):
                for i in range(pixel[0] * self.cfg["pxl"], (pixel[0] + 1) * self.cfg["pxl"]):
                    mlx.mlx_put_pixel(self.img, i, j, pixel[2])

    def fill(self, color: int = 0xffffffff):
        for y in range(self.img.contents.height):
            for x in range(self.img.contents.width):
                mlx.mlx_put_pixel(self.img, x, y, color)


class Drone(Entity):
    def __init__(
            self, mlx_ptr, name: str, shape: set[tuple[int, int, int]],
            cell_pos: tuple[int, int], color: int, cfg: dict[str, int]
            ):

        # calculate shape size
        min_x = min(x[0] for x in shape)
        max_x = max(x[0] for x in shape)
        min_y = min(y[1] for y in shape)
        max_y = max(y[1] for y in shape)
        size_x = max_x - min_x + 1
        size_y = max_y - min_y + 1

        # adjusting offset
        shape = set((x - min_x, y - min_y, color) for x, y, _ in shape)


        super().__init__(
            mlx_ptr, name, shape,
            cell_pos, (size_x, size_y), cfg
            )


class Hub(Entity):
    def __init__(
            self, mlx_ptr, name: str, shape: set[tuple[int, int, int]],
            cell_pos: tuple[int, int], cfg: dict[str, int]
            ):
        # calculate shape size
        min_x = min(x[0] for x in shape)
        max_x = max(x[0] for x in shape)
        min_y = min(y[1] for y in shape)
        max_y = max(y[1] for y in shape)
        size_x = max_x - min_x + 1
        size_y = max_y - min_y + 1

        # adjusting offset
        shape = set((x - min_x, y - min_y, c) for x, y, c in shape)

        super().__init__(
            mlx_ptr, name, shape,
            cell_pos, (size_x, size_y), cfg
            )


class MlxWindow:
    def __init__(self, cfg):
        self.mlx_ptr = mlx.mlx_init(cfg["width"], cfg["height"], b"Fly-in", True)
        self.hubs: dict[str, Hub] = {}
        self.drones: dict[str, Drone] = {}
        self.cfg: dict[str, int] = cfg
        self.grid = None

    def gridify(self, step, bg_color, lines_color):
        grid = mlx.mlx_new_image(
            self.mlx_ptr, self.cfg["width"], self.cfg["height"])
        step = step * self.cfg["pxl"]
        for y in range(0, self.cfg["height"], step):
            for x in range(0, self.cfg["width"], step):
                for j in range(y, y + step):
                    for i in range(x, x + step):
                        mlx.mlx_put_pixel(grid, i, j, bg_color)
                for j in range(y, y + step):
                    mlx.mlx_put_pixel(grid, x, j, lines_color)
                for i in range(x, x + step):
                    mlx.mlx_put_pixel(grid, i, y, lines_color)
        mlx.mlx_image_to_window(self.mlx_ptr, grid, 0, 0)
        self.grid = grid

    def attach(self, entities: list[Entity], display_names: bool = True):
        for entity in entities:
            entity.attach(self.mlx_ptr)
            entity.draw()
            if isinstance(entity, Hub):
                if display_names and entity.name is not None:
                    mlx.mlx_put_string(
                        self.mlx_ptr, entity.name.encode(),
                        entity.abs_pos[0], entity.abs_pos[1] + self.cfg["pxl"] * 5,
                        0xffffffff
                        )
            if isinstance(entity, Drone):
                self.drones[entity.name] = entity
            elif isinstance(entity, Hub):
                self.hubs[entity.name] = entity

    def draw_line(
            self,
            pos1: tuple[int, int],
            pos2: tuple[int, int],
            color: int = 0xffffffff
            ) -> None:
        x1, y1 = pos1
        x2, y2 = pos2
        dx = x2 - x1
        dy = y2 - y1
        step = max(abs(dx), abs(dy))
        if step == 0:
            mlx.mlx_put_pixel(self.grid, x1, y1, color)
            return
        stepx = dx / step
        stepy = dy / step
        for i in range(step + 1):
            mlx.mlx_put_pixel(self.grid, int(x1 + i * stepx), int(y1 + i * stepy), color)

    def connect(self, hub1: str, hub2: str, color: int = 0xffffffff):
        # look for hubs in self.hubs
        if hub1 not in self.hubs:
            raise ValueError(f"hub '{hub1}' not found.")
        if hub2 not in self.hubs:
            raise ValueError(f"hub '{hub2}' not found.")

        pos1 = self.hubs[hub1].shape_pos
        pos2 = self.hubs[hub2].shape_pos
        # connect centers of hubs
        self.draw_line(pos1, pos2, color)


    def run(self):
        mlx.mlx_loop(self.mlx_ptr)
        mlx.mlx_terminate(self.mlx_ptr)

