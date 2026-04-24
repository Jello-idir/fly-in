from MLX.libmlx import *


class Entity:
    def __init__(
            self, mlx_ptr, name: str,
            shape: list[tuple[int, int]],
            cell_pos: tuple[int, int],
            px_size: tuple[int, int],
            color: int,
            cfg: dict[str, int],
            align: bool = True
            ):
        self.name = name
        self.cfg = cfg
        self.px_size = px_size
        self.abs_size = (px_size[0] * self.cfg["pxl"], px_size[1] * self.cfg["pxl"])
        self.cell_pos = cell_pos
        self.px_pos = (cell_pos[0] * self.cfg["cell"], cell_pos[1] * self.cfg["cell"])
        if align:
            self.abs_pos = ((self.px_pos[0] + self.cfg["cell"] // 2 - self.px_size[0] // 2) * self.cfg["pxl"],
                            (self.px_pos[1] + self.cfg["cell"] // 2 - self.px_size[1] // 2) * self.cfg["pxl"])
        else:
            self.abs_pos = (self.px_pos[0] * self.cfg["pxl"], self.px_pos[1] * self.cfg["pxl"])
        self.shape = shape
        self.color = color
        self.img = mlx.mlx_new_image(mlx_ptr, self.abs_size[0], self.abs_size[1])

    def attach(self, window):
        mlx.mlx_image_to_window(window, self.img, self.abs_pos[0], self.abs_pos[1])

    def draw(self):
        for pixel in self.shape:
            for j in range(pixel[1] * self.cfg["pxl"], (pixel[1] + 1) * self.cfg["pxl"]):
                for i in range(pixel[0] * self.cfg["pxl"], (pixel[0] + 1) * self.cfg["pxl"]):
                    mlx.mlx_put_pixel(self.img, i, j, self.color)

    def fill(self, color: int = 0xffffffff):
        for y in range(self.img.contents.height):
            for x in range(self.img.contents.width):
                mlx.mlx_put_pixel(self.img, x, y, color)


class Drone(Entity):
    def __init__(
            self, mlx_ptr, name: str, shape: list[tuple[int, int]],
            cell_pos: tuple[int, int], color: int, cfg: dict[str, int]
            ):
        super().__init__(
            mlx_ptr, name, shape,
            (cell_pos[0], cell_pos[1]),
            (4, 2), color, cfg
            )


class Hub(Entity):
    def __init__(
            self, mlx_ptr, name: str, shape: list[tuple[int, int]],
            cell_pos: tuple[int, int], color: int, cfg: dict[str, int]
            ):
        super().__init__(
            mlx_ptr, name, shape,
            (cell_pos[0], cell_pos[1]),
            (8, 5), color, cfg
            )


class MlxMngr:
    def __init__(self, cfg):
        self.mlx_ptr = mlx.mlx_init(cfg["width"], cfg["height"], b"Fly-in", True)
        self.hubs: list[Hub] = []
        self.drones: list[Entity ]= []
        self.cfg: dict[str, int] = cfg
        self.grid = None

    def gridify(self, step, bg_color, lines_color):
        grid = mlx.mlx_new_image(self.mlx_ptr, self.cfg["width"], self.cfg["height"])
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

    def attach(self, entities: list[Entity]):
        for entity in entities:
            entity.attach(self.mlx_ptr)
            entity.draw()
            if isinstance(entity, Hub):
                mlx.mlx_put_string(self.mlx_ptr, entity.name.encode(), entity.abs_pos[0], entity.abs_pos[1] + self.cfg["pxl"] * 5, 0xffffffff)
            if isinstance(entity, Drone):
                self.drones.append(entity)
            elif isinstance(entity, Hub):
                self.hubs.append(entity)

    def run(self):
        mlx.mlx_loop(self.mlx_ptr)
        mlx.mlx_terminate(self.mlx_ptr)

