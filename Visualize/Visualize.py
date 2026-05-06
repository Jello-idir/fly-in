from MLX.libmlx import *
from typing import Any
from Common import *
from MapParser import MapData
import queue
import ctypes

class Entity:
    def __init__(self, mlx_ptr, cfg: RenderConfig,
        coord: tuple[int, int],
        color: int,
        shape: set[tuple[int, int, int]]
    ):
        self.color = color
        self.shape = shape
        self.coord = coord
        self.size = (
            max(x[0] for x in shape) + 1,
            max(y[1] for y in shape) + 1
        )
        self.pos = (
            (coord[0] * cfg.space - cfg.min_x + cfg.padd_x) * cfg.cell,
            (coord[1] * cfg.space - cfg.min_y + cfg.padd_y) * cfg.cell
            )
        self.img = mlx.mlx_new_image(
            mlx_ptr,
            self.size[0],
            self.size[1],
        )
        self.img_name = None


class MlxDrone(Entity):
    def __init__(
            self,
            mlx_ptr,
            cfg: RenderConfig,
            drone_model: Drone
    ) -> None:
        self.id: int = drone_model.id
        super().__init__(
            mlx_ptr, cfg,
            drone_model.coord,
            drone_model.color,
            cfg.drone_shape
        )


class MlxHub(Entity):
    def __init__(
            self,
            mlx_ptr,
            cfg: RenderConfig,
            hub_model: Hub,
    ) -> None:
        self.name: str = hub_model.name
        self.data = hub_model
        super().__init__(
            mlx_ptr, cfg,
            hub_model.pos,
            hub_model.metadata.color,
            cfg.hub_shape
        )


class MlxWindow:
    def __init__(self, cfg):
        self.mlx_ptr = mlx.mlx_init(cfg.width, cfg.height, b"Fly-in", True)
        self.hubs: dict[str, MlxHub] = {}
        self.drones: dict[int, MlxDrone] = {}
        self.cfg: RenderConfig = cfg
        self.img_grid = mlx.mlx_new_image(self.mlx_ptr, self.cfg.width, self.cfg.height)
        self.img_tile = mlx.mlx_new_image(self.mlx_ptr, self.cfg.width, self.cfg.height)
        self.img_lines = mlx.mlx_new_image(
            self.mlx_ptr, self.cfg.width, self.cfg.height
        )

    @classmethod
    def from_map(cls, map: MapData, cfg: RenderConfig):
        window = cls(cfg)
        for hub in map.hubs.values():
            window._add_entity(hub)
        for drone in map.drones.values():
            window._add_entity(drone)
        return window

    def gridify(self, step, bg_color, lines_color):
        for y in range(0, self.cfg.height, step):
            for x in range(0, self.cfg.width, step):
                for j in range(y, y + step):
                    for i in range(x, x + step):
                        mlx.mlx_put_pixel(self.img_grid, i, j, bg_color)
                for j in range(y, y + step):
                    mlx.mlx_put_pixel(self.img_grid, x, j, lines_color)
                for i in range(x, x + step):
                    mlx.mlx_put_pixel(self.img_grid, i, y, lines_color)

    def tilify(self, shape: set[tuple[int, int, int]]):
        img_tile = mlx.mlx_new_image(self.mlx_ptr, self.cfg.width, self.cfg.height)
        x_size = max(x[0] for x in shape) + 1
        y_size = max(y[1] for y in shape) + 1
        x_offset = y_offset = 0
        for pixel in shape:
            for y in range(y_offset, self.cfg.height, y_size):
                for x in range(x_offset, self.cfg.width, x_size):
                    if x + pixel[0] < self.cfg.width and y + pixel[1] < self.cfg.height:
                        mlx.mlx_put_pixel(
                            img_tile, x + pixel[0], y + pixel[1], pixel[2]
                        )
        self.img_tile = img_tile

    def _add_entity(self, obj: Drone | Hub) -> None:
        if isinstance(obj, Drone):
            self.drones[obj.id] = MlxDrone(
                self.mlx_ptr,
                self.cfg,
                obj
            )
        elif isinstance(obj, Hub):
            self.hubs[obj.name] = MlxHub(
                self.mlx_ptr,
                self.cfg,
                obj
            )

    def _draw_entity(self, entity: Entity):
        for pixel in entity.shape:
            for j in range(pixel[1], (pixel[1] + 1)):
                for i in range(pixel[0], (pixel[0] + 1)):
                    r = (pixel[2] >> 24) & 0xFF
                    g = (pixel[2] >> 16) & 0xFF
                    b = (pixel[2] >> 8) & 0xFF
                    if r == g and g == b:
                        mlx.mlx_put_pixel(entity.img, i, j, pixel[2])
                    else:
                        mlx.mlx_put_pixel(entity.img, i, j, entity.color)

    def _disable_entity(self, entity: Entity):
        entity.img.contents.enabled = False

    def _enable_entity(self, entity: Entity):
        entity.img.contents.enabled = True

    def _delete_entity_image(self, entity: Entity):
        mlx.mlx_delete_image(self.mlx_ptr, entity.img)

    def _draw_entities(self):
        for entity in [*self.hubs.values(), *self.drones.values()]:
            for pixel in entity.shape:
                for j in range(pixel[1], (pixel[1] + 1)):
                    for i in range(pixel[0], (pixel[0] + 1)):
                        r = (pixel[2] >> 24) & 0xFF
                        g = (pixel[2] >> 16) & 0xFF
                        b = (pixel[2] >> 8) & 0xFF
                        if r == g and g == b:
                            mlx.mlx_put_pixel(entity.img, i, j, pixel[2])
                        else:
                            mlx.mlx_put_pixel(entity.img, i, j, entity.color)

    def _attach_entity(self, entity: Entity):
        mlx.mlx_image_to_window(
            self.mlx_ptr, entity.img, entity.pos[0], entity.pos[1]
        )

    def _attach_entities(self):
        for entity in [*self.hubs.values(), *self.drones.values()]:
            mlx.mlx_image_to_window(
                self.mlx_ptr, entity.img, entity.pos[0], entity.pos[1]
            )

    def _draw_entities_names(self, upper: bool = False) -> None:
        for entity in [*self.hubs.values(), *self.drones.values()]:
            name = entity.name if isinstance(entity, MlxHub) else f"D-{entity.id}"
            if upper:
                name = name.upper()
            # calculate size of name image
            width = sum(self.cfg.font[c].width for c in name)
            height = 12

            # create name image
            entity.img_name = mlx.mlx_new_image(self.mlx_ptr, width, height)
            pixels: set[tuple[int, int, int]] = set()
            x, y = 0, 0

            # create pixels
            for c in name:
                new_pixels = set((px + x, py + y, c) for px, py, c in self.cfg.font[c].pixels)
                pixels.update(new_pixels)
                x += self.cfg.font[c].width

            # drawe pixels
            for pixel in pixels:
                if isinstance(entity, MlxHub):
                    mlx.mlx_put_pixel(entity.img_name, pixel[0], pixel[1], pixel[2])

            # attach self
            mlx.mlx_image_to_window(
                self.mlx_ptr, entity.img_name, entity.pos[0], entity.pos[1] - 12
                )

    def _delete_entity_name(self, entity: Entity):
        if entity.img_name:
            mlx.mlx_delete_image(self.mlx_ptr, entity.img_name)
            entity.img_name = None

    def _enable_entity_name(self, entity: Entity):
        if entity.img_name:
            entity.img_name.contents.enabled = True

    def _disable_entity_name(self, entity: Entity):
        if entity.img_name:
            entity.img_name.contents.enabled = False

    def _connect_hubs(self, map: MapData, color: int = 0xFFFFFFFF):
        def _draw_line(
            pos1: tuple[int, int],
            pos2: tuple[int, int],
            color: int = 0xFFFFFFFF
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
                    self.img_lines, int(x1 + i * stepx), int(y1 + i * stepy), color
                )

        for conn in map.connections:
            hub_a = self.hubs[conn.hub_a]
            hub_b = self.hubs[conn.hub_b]

            hub1_pos = (
                hub_b.pos[0] + hub_b.size[0] // 2,
                hub_b.pos[1] + hub_b.size[1] // 2
            )
            hub2_pos = (
                hub_a.pos[0] + hub_a.size[0] // 2,
                hub_a.pos[1] + hub_a.size[1] // 2
            )
            _draw_line(hub1_pos, hub2_pos, color)

    def testin(self, param):
        key = input("Enter command (format: move <drone_id> <x> <y>): ")
        parts = key.split()
        if parts[0] in ("move", "disable", "enable"):
            try:
                if parts[0] == "disable":
                    drone_id = int(parts[1])
                    self._disable_entity(self.drones[drone_id])
                elif parts[0] == "enable":
                    drone_id = int(parts[1])
                    self._enable_entity(self.drones[drone_id])
                elif parts[0] == "move" and len(parts) == 4:
                    drone_id = int(parts[1])
                    x = int(parts[2])
                    y = int(parts[3])
                    if drone_id in self.drones:
                        self._move_entity(self.drones[drone_id], (x, y))
            except Exception:
                print("Invalid command format. Please enter: move <drone_id> <x> <y>")
        else:
            print("Invalid command format. Please enter: move <drone_id> <x> <y>")

    def _move_entity(self, drone: Entity, new_coord: tuple[int, int]):
        drone.coord = new_coord
        drone.pos = (
            (new_coord[0] * self.cfg.space - self.cfg.min_x + self.cfg.padd_x) * self.cfg.cell,
            (new_coord[1] * self.cfg.space - self.cfg.min_y + self.cfg.padd_y) * self.cfg.cell
        )
        drone.img.contents.instances.contents.x = drone.pos[0]
        drone.img.contents.instances.contents.y = drone.pos[1]

    def display_and_hook(self, with_label=False):
        # attach all images to mlx then run
        mlx.mlx_image_to_window(self.mlx_ptr, self.img_grid, 0, 0)
        mlx.mlx_image_to_window(self.mlx_ptr, self.img_tile, 0, 0)
        mlx.mlx_image_to_window(self.mlx_ptr, self.img_lines, 0, 0)

        self._draw_entities()
        self._attach_entities()
        if with_label:
            self._draw_entities_names()

        self.a = ctypes.CFUNCTYPE(None, ctypes.c_void_p)(self.testin)

        mlx.mlx_loop_hook(self.mlx_ptr, self.a, None)  # type: ignore
        mlx.mlx_loop(self.mlx_ptr)
        mlx.mlx_terminate(self.mlx_ptr)

    def display(self, with_label=False):
        mlx.mlx_image_to_window(self.mlx_ptr, self.img_grid, 0, 0)
        mlx.mlx_image_to_window(self.mlx_ptr, self.img_tile, 0, 0)
        mlx.mlx_image_to_window(self.mlx_ptr, self.img_lines, 0, 0)

        self._draw_entities()
        self._attach_entities()
        if with_label:
            self._draw_entities_names(upper=True)
        mlx.mlx_loop(self.mlx_ptr)
        mlx.mlx_terminate(self.mlx_ptr)
