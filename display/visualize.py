from MLX.libmlx import *
import sys

class Entity:
    def __init__(
            self, mlx_ptr,
            name: str,
            shape: set[tuple[int, int, int]],
            cell_pos: tuple[int, int],
            px_size: tuple[int, int],
            cfg: dict[str, int],
            color: int = 0xffffffff,
            align: bool = True
            ):
        self.name = name
        self.color = color
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
        self.img = mlx.mlx_new_image(
            mlx_ptr, self.abs_size[0] + cfg["shadow"] * cfg["pxl"],
            self.abs_size[1] + cfg["shadow"] * cfg["pxl"],
            )

    def draw(self):
        # drawing the shadow bellow the entire shape
        shadow_color = (0x000000 << 8) + 0xff
        if self.cfg["shadow"] > 0:
            for j in range(self.abs_size[1] + self.cfg["shadow"] * self.cfg["pxl"]):
                for i in range(self.abs_size[0] + self.cfg["shadow"] * self.cfg["pxl"]):
                    mlx.mlx_put_pixel(self.img, i, j, shadow_color)

        # drawing the shape
        for pixel in self.shape:
            for j in range(pixel[1] * self.cfg["pxl"], (pixel[1] + 1) * self.cfg["pxl"]):
                for i in range(pixel[0] * self.cfg["pxl"], (pixel[0] + 1) * self.cfg["pxl"]):
                    r = (pixel[2] >> 24) & 0xFF
                    g = (pixel[2] >> 16) & 0xFF
                    b = (pixel[2] >> 8) & 0xFF
                    if (r == g and g == b):
                        mlx.mlx_put_pixel(self.img, i, j, pixel[2])
                    else:
                        mlx.mlx_put_pixel(self.img, i, j, self.color)

    def fill(self, color: int = 0xffffffff):
        for y in range(self.img.contents.height):
            for x in range(self.img.contents.width):
                mlx.mlx_put_pixel(self.img, x, y, color)

    @staticmethod
    def to_coords(font, text, width, height):
        pass


class Drone(Entity):
    def __init__(
            self, mlx_ptr,
            name: str,
            shape: set[tuple[int, int, int]],
            cell_pos: tuple[int, int],
            cfg: dict[str, int],
            color: int = 0xffffffff,
            align: bool = True,
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
            cell_pos, (size_x, size_y),
            cfg, color, align
            )


class Hub(Entity):
    def __init__(
            self, mlx_ptr,
            name: str,
            shape: set[tuple[int, int, int]],
            cell_pos: tuple[int, int],
            cfg: dict[str, int],
            color: int = 0xffffffff,
            align: bool= True,
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
            cell_pos, (size_x, size_y),
            cfg, color, align
            )


class MlxWindow:
    def __init__(self, cfg):
        self.mlx_ptr = mlx.mlx_init(cfg["width"], cfg["height"], b"Fly-in", True)
        self.hubs: dict[str, Hub] = {}
        self.drones: dict[str, Drone] = {}
        self.cfg: dict[str, int] = cfg
        self.img_grid = mlx.mlx_new_image(
            self.mlx_ptr, self.cfg["width"], self.cfg["height"])
        self.img_tile = mlx.mlx_new_image(
            self.mlx_ptr, self.cfg["width"], self.cfg["height"])
        self.img_lines = mlx.mlx_new_image(
            self.mlx_ptr, self.cfg["width"], self.cfg["height"])

    def gridify(self, step, bg_color, lines_color):
        step = step * self.cfg["pxl"]
        for y in range(0, self.cfg["height"], step):
            for x in range(0, self.cfg["width"], step):
                for j in range(y, y + step):
                    for i in range(x, x + step):
                        mlx.mlx_put_pixel(self.img_grid, i, j, bg_color)
                for j in range(y, y + step):
                    mlx.mlx_put_pixel(self.img_grid, x, j, lines_color)
                for i in range(x, x + step):
                    mlx.mlx_put_pixel(self.img_grid, i, y, lines_color)


    def tilify(self, shape: set[tuple[int, int, int]]):
        img_tile = mlx.mlx_new_image(
            self.mlx_ptr, self.cfg["width"], self.cfg["height"])
        x_size = max(x[0] for x in shape) + 1
        y_size = max(y[1] for y in shape) + 1
        x_offset = y_offset = 0
        for pixel in shape:
            for y in range(x_offset, self.cfg["height"], y_size):
                for x in range(y_offset, self.cfg["width"], x_size):
                    if (x + pixel[0] < self.cfg["width"]
                    and y + pixel[1] < self.cfg["height"]):
                        mlx.mlx_put_pixel(img_tile, x + pixel[0], y + pixel[1], pixel[2])

        self.img_tile = img_tile

    def add_entity(self, entities: list[Entity],
                    name_on: bool = False,
                    hitbox_on: bool = False,
                    hitbox_color: int = 0xFFFF0053,
                    ) -> None:
        for entity in entities:
            if hitbox_on:
                entity.fill(hitbox_color)
            entity.draw()
            if name_on and entity.name is not None:
                mlx.mlx_put_string(
                    self.mlx_ptr, entity.name[:3].encode(),
                    entity.abs_pos[0], entity.abs_pos[1] + entity.abs_size[1] + 5,
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
            mlx.mlx_put_pixel(self.img_lines, x1, y1, color)
            return
        stepx = dx / step
        stepy = dy / step
        for i in range(step + 1):
            mlx.mlx_put_pixel(
                self.img_lines,
                int(x1 + i * stepx),
                int(y1 + i * stepy),
                color
                )

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

    def pixel_putstr(
            self, font: dict[str, set[tuple[int, int]]],
            text: str, pos: tuple[int, int],
            color: int = 0xffffffff) -> None:

        pixels: set[tuple[int, int]] = set()
        x, y = pos
        for c in text:
            if c == "\n":
                y += 12
                x = pos[0]
                continue
            if c == "\t":
                x += 9 * 3
                continue
            if c not in font:
                x += 9
                continue
            pixels.update((x + px, y + py) for px, py in font[c])
            x += 9
        for pixel in pixels:
            mlx.mlx_put_pixel(self.img_grid, pixel[0], pixel[1], color)

    def display(self, with_label=False):
        # attach all images to mlx then run
        mlx.mlx_image_to_window(self.mlx_ptr, self.img_grid, 0, 0)
        mlx.mlx_image_to_window(self.mlx_ptr, self.img_tile, 0, 0)
        mlx.mlx_image_to_window(self.mlx_ptr, self.img_lines, 0, 0)

        # attach entities
        for entity in self.hubs.values():
            mlx.mlx_image_to_window(
                self.mlx_ptr, entity.img,
                entity.abs_pos[0], entity.abs_pos[1])

        # display names next to hubs
        if with_label:
            for entity in self.hubs.values():
                mlx.mlx_put_string(
                    self.mlx_ptr, entity.name[:3].encode(),
                    entity.abs_pos[0], entity.abs_pos[1] + entity.abs_size[1] + 5,
                    0xffffffff
                    )

        mlx.mlx_loop(self.mlx_ptr)
        mlx.mlx_terminate(self.mlx_ptr)


def fill_image(image, color: int = 0xffffffff):
    for y in range(image.contents.height):
        for x in range(image.contents.width):
            mlx.mlx_put_pixel(image, x, y, color)


def pixel_putstr(font: dict[str, set[tuple[int, int]]],
                 text: str, pos: tuple[int, int],
                 cfg: dict[str, int]) -> None:
    test_window = MlxWindow(cfg)
    test_image = mlx.mlx_new_image(test_window.mlx_ptr, cfg["width"], cfg["height"])
    pixels: set[tuple[int, int]] = set()
    x, y = pos
    for c in text:
        if c == '\n':
            y += 12
            x = pos[0]
            continue
        if c not in font:
            x += 9
            continue
        if c == "\t":
            x += 9 * 4
            continue
        pixels.update((x + px, y + py) for px, py in font[c])
        x += 9

    # draw hit box in image
    fill_image(test_image, (0x3D454F << 8) + 0xff)
    for pixel in pixels:
        mlx.mlx_put_pixel(test_image, pixel[0], pixel[1], 0xffffffff)
    mlx.mlx_image_to_window(test_window.mlx_ptr, test_image, 0, 0)
    test_window.display()
