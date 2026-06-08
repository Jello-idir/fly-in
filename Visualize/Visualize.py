from MLX.libmlx import *
from typing import Any
from Common import *
from MapParser import MapData


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
    def __init__(self, mapdata: MapData, cfg: RenderConfig):
        self.map = mapdata
        self.mlx_ptr = mlx.mlx_init(cfg.width, cfg.height, b"Fly-in", True)
        self.hubs: dict[str, MlxHub] = {}
        self.drones: dict[int, MlxDrone] = {}
        self.cfg: RenderConfig = cfg
        self.img_tile = mlx.mlx_new_image(
            self.mlx_ptr, self.cfg.width, self.cfg.height)
        self.img_lines = mlx.mlx_new_image(
            self.mlx_ptr, self.cfg.width, self.cfg.height
        )

    @classmethod
    def from_map(cls, mapdata: MapData, cfg: RenderConfig):
        window = cls(mapdata, cfg)
        for hub in mapdata.hubs.values():
            window._add_entity(hub)
        for drone in mapdata.drones.values():
            window._add_entity(drone)
        return window


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

    def _draw_lines(self, color: int = 0xFFFFFFFF):

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

        for conn in self.map.connections:
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

    def display(self, with_label=False):

        mlx.mlx_image_to_window(self.mlx_ptr, self.img_tile, 0, 0)
        mlx.mlx_image_to_window(self.mlx_ptr, self.img_lines, 0 , 0)

        self._draw_entities()
        self._attach_entities()
        self._draw_lines()

        if with_label:
            self._draw_entities_names(upper=True)



        mlx.mlx_loop(self.mlx_ptr)
        mlx.mlx_terminate(self.mlx_ptr)
