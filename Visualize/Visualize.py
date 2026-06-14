from MLX.libmlx import *
from Common import *
from MapParser import MapData
import ctypes
import time

def fill_image(img, color: int):
    for y in range(img.contents.height):
        for x in range(img.contents.width):
            mlx.mlx_put_pixel(img, x, y, color)


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
        self.stats_img = None
        self.name_img = None


class MlxDrone(Entity):
    def __init__(
            self,
            mlx_ptr,
            cfg: RenderConfig,
            drone_model: Drone
    ) -> None:
        self.id: int = drone_model.id
        color = list(ColorType)[(self.id % 7) * 4]
        super().__init__(
            mlx_ptr, cfg,
            drone_model.coord,
            color,
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
        self.drones: list[MlxDrone] = []
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
        self.cfg: RenderConfig = cfg
        self._turns = []
        self._move_index = 0
        self._last_time = 0
        self.img_tile = mlx.mlx_new_image(
            self.mlx_ptr, self.cfg.width, self.cfg.height)
        self.img_bg = mlx.mlx_new_image(
            self.mlx_ptr, self.cfg.width, self.cfg.height
        )

    @classmethod
    def from_map(cls, mapdata: MapData, cfg: RenderConfig):
        window = cls(mapdata, cfg)
        for hub in mapdata.hubs.values():
            window._add_hub(hub)

        # finding the first hub
        start_hub = next(
            hub for hub in mapdata.hubs.values()
            if hub.type == HubType.start_hub
            )
        for drone in mapdata.drones.values():
            drone_entity = MlxDrone(window.mlx_ptr, window.cfg, drone)
            window.hubs[start_hub.name].drones.append(drone_entity)
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

    def _write_text(self, img, text: str, pos: tuple[int, int], with_shadow: bool = True):
        init_x, init_y = pos
        x, y = init_x, init_y

        for c in text:
            if c == '\n':
                y += 10
                x = init_x
                continue
            for px, py, col in self.cfg.font[c].pixels:
                mlx.mlx_put_pixel(
                    img, x + px, y + py, col
                )
                if with_shadow:
                    shadow_col = 0x000000ff
                    mlx.mlx_put_pixel(
                        img, x + px + 1, y + py + 1, shadow_col
                    )
            x += self.cfg.font[c].width

    def _add_hub(self, obj: Hub) -> None:
        if isinstance(obj, Hub):
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

    def _draw_hub_drones(self, hub: MlxHub):
        for idx, drone in enumerate(hub.drones):
            if idx >= 12:
                break
            offset_x = (idx % 3) * 16 + 10
            offset_y = (idx // 3) * 11 + 10
            self._attach_entity(drone, (hub.pos[0] + offset_x, hub.pos[1] + offset_y))

    def _attach_entity(self, entity: Entity, pos: tuple[int, int] | None = None):
        if pos is None:
            pos = entity.pos
        mlx.mlx_image_to_window(
            self.mlx_ptr, entity.img, pos[0], pos[1]
        )

    def _draw_entities_names(self, upper: bool = False) -> None:
        for entity in self.hubs.values():
            name = entity.name
            if upper:
                name = name.upper()
            self._write_text(self.img_bg, name, (entity.pos[0], entity.pos[1] - 12))

    def _draw_hub_stats(self, upper: bool = False) -> None:
        # stats are drawn in bottom
        for hub in self.hubs.values():
            stats = f"{len(hub.drones)}/{hub.data.metadata.max_drones} {hub.data.metadata.zone.value}"
            if upper:
                stats = stats.upper()
            self._write_text(self.img_bg, stats, (hub.pos[0], hub.pos[1] + hub.size[1] + 2))

    def _draw_lines(self, color: int = 0xFFFFFF50):
        for conn in self.map.connections:
            hub_a = self.hubs[conn.hub_a]
            hub_b = self.hubs[conn.hub_b]

            # calculating center points of hubs
            x1 = hub_a.pos[0] + hub_a.size[0] // 2
            y1 = hub_a.pos[1] + hub_a.size[1] // 2
            x2 = hub_b.pos[0] + hub_b.size[0] // 2
            y2 = hub_b.pos[1] + hub_b.size[1] // 2

            # calculating delta and steps
            dx = x2 - x1
            dy = y2 - y1
            steps = max(abs(dx), abs(dy))
            if steps == 0:
                continue
            x_inc = dx / steps
            y_inc = dy / steps

            x, y = x1, y1
            for _ in range(steps):
                for j in range(-conn.capacity * 3, conn.capacity * 3 + 1):
                    for i in range(-conn.capacity * 3, conn.capacity * 3 + 1):
                        mlx.mlx_put_pixel(self.img_bg, int(x) + i, int(y) + j, color)
                x += x_inc
                y += y_inc

            # write capacity
            capacity_text = str(conn.capacity)
            text_width = len(capacity_text) * 8
            text_x = int((x1 + x2) / 2 - text_width / 2)
            text_y = int((y1 + y2) / 2 - 3)
            self._write_text(self.img_bg, capacity_text, (text_x, text_y))

    def _do_animation(self):
        for line in self._turns:
            for mov in line.split():
                drone_id, hub_dest = mov.split("-")
                drone_id = int(mov[0][1:])
                print(f"Moving drone {drone_id} to {mov[1:]}")


    def display(self,
                with_name: bool = False,
                with_stats: bool = False
                ) -> None:

        mlx.mlx_image_to_window(self.mlx_ptr, self.img_tile, 0, 0)
        mlx.mlx_image_to_window(self.mlx_ptr, self.img_bg, 0 , 0)

        for hub in self.hubs.values():
            self._draw_entity(hub)
            for drone in hub.drones:
                self._draw_entity(drone)
            self._attach_entity(hub)
            self._draw_hub_drones(hub)

        self._draw_lines()

        if with_name:
            self._draw_entities_names(upper=True)
        if with_stats:
            self._draw_hub_stats(upper=False)

        mlx.mlx_loop(self.mlx_ptr)
        mlx.mlx_terminate(self.mlx_ptr)

    def _animate_solution_hook(self, keydata, param=None) -> None:

        if mlx.mlx_is_key_down(self.mlx_ptr, MLX_KEY_ESCAPE):
            mlx.mlx_close_window(self.mlx_ptr)

        elif mlx.mlx_is_key_down(self.mlx_ptr, MLX_KEY_SPACE):
            # start animation
            self._do_animation()

    def run(self, solution: str,
            with_name: bool = False,
            with_stats: bool = False,
            ) -> None:
        mlx.mlx_image_to_window(self.mlx_ptr, self.img_tile, 0, 0)
        mlx.mlx_image_to_window(self.mlx_ptr, self.img_bg, 0 , 0)

        for hub in self.hubs.values():
            self._draw_entity(hub)
            for drone in hub.drones:
                self._draw_entity(drone)
            self._attach_entity(hub)
            self._draw_hub_drones(hub)

        self._draw_lines()

        if with_name:
            self._draw_entities_names(upper=True)

        if with_stats:
            self._draw_hub_stats(upper=False)

        self._turns = solution.splitlines()
        self._move_index = 0
        self._last_time = 0

        self.hook_func = ctypes.CFUNCTYPE(None, ctypes.c_void_p)(self._animate_solution_hook)
        mlx.mlx_key_hook(self.mlx_ptr, self.hook_func, None)

        mlx.mlx_loop(self.mlx_ptr)
        mlx.mlx_terminate(self.mlx_ptr)
