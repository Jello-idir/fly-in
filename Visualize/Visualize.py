from MLX.libmlx import *
from Common import *
from MapParser import MapData
from collections import deque
import ctypes
import re
import time


HUB_DEPTH = 1
STATS_DEPTH = 2
DRONE_DEPTH = 3

ANIMATING = 0
ANIMATING_LINE = 0
LIST_OF_MOVES = []
QUEUE = {}
IS_QUEUE = False
STEPS = 60



def fill_image(img, color: int):
    for y in range(img.contents.height):
        for x in range(img.contents.width):
            idx = (y * img.contents.width + x) * 4
            img.contents.pixels[idx] = color >> 24 & 0xff
            img.contents.pixels[idx + 1] = color >> 16 & 0xff
            img.contents.pixels[idx + 2] = color >> 8 & 0xff
            img.contents.pixels[idx + 3] = color & 0xff


class Entity:
    def __init__(
        self,
        mlx_ptr,
        cfg: RenderConfig,
        coord: tuple[int, int],
        color: int,
        shape: set[tuple[int, int, int]],
    ):
        self.color = color
        self.shape = shape
        self.coord = coord
        self.size = (max(x[0] for x in shape) + 1, max(y[1] for y in shape) + 1)
        self.pos = (
            (coord[0] * cfg.space - cfg.min_x + cfg.padd_x) * cfg.cell,
            (coord[1] * cfg.space - cfg.min_y + cfg.padd_y) * cfg.cell,
        )
        self.img = mlx.mlx_new_image(
            mlx_ptr,
            self.size[0],
            self.size[1],
        )
        self.stats_img = None
        self.name_img = None


class Drone(Entity):
    def __init__(self, mlx_ptr, cfg: RenderConfig, drone_base: DroneBase, current_hub: HubStation) -> None:
        self.id: int = drone_base.id
        self.location: HubStation | Connection = current_hub
        color = list(ColorType)[(self.id % 7) * 4]
        super().__init__(mlx_ptr, cfg, drone_base.coord, color, cfg.drone_shape)


class HubStation(Entity):
    def __init__(
        self,
        mlx_ptr,
        cfg: RenderConfig,
        hub_model: HubBase,
    ) -> None:
        self.name: str = hub_model.name
        self.metadata = hub_model.metadata
        self.type = hub_model.type
        self.drones: dict[int, Drone] = {}
        self.connections: list[Connection] = []
        shape = cfg.hub_shape if self.metadata.zone != ZoneType.restricted else cfg.hub_restricted_shape
        super().__init__(
            mlx_ptr, cfg, hub_model.pos, hub_model.metadata.color, shape
        )

class Connection:
    def __init__(self, hub_a: HubStation, hub_b: HubStation, capacity: int):
        self.hub_a = hub_a
        self.hub_b = hub_b
        self.capacity = capacity
        self.start_pos = (hub_a.pos[0] + hub_a.size[0] // 2, hub_a.pos[1] + hub_a.size[1] // 2)
        self.end_pos = (hub_b.pos[0] + hub_b.size[0] // 2, hub_b.pos[1] + hub_b.size[1] // 2)
        self.center = ((self.start_pos[0] + self.end_pos[0]) // 2, (self.start_pos[1] + self.end_pos[1]) // 2)


class MlxWindow:
    def __init__(self, cfg: RenderConfig) -> None:
        self.connections: list[Connection] = []
        self.mlx_ptr = mlx.mlx_init(cfg.width, cfg.height, b"Fly-in", True)
        self.hubs: dict[str, HubStation] = {}
        self.drones: dict[int, Drone] = {}
        self.cfg: RenderConfig = cfg
        self._solution_line = deque()
        self._solution_move = deque()
        self.img_tile = mlx.mlx_new_image(self.mlx_ptr, self.cfg.width, self.cfg.height)
        self.img_stats = mlx.mlx_new_image(self.mlx_ptr, self.cfg.width, self.cfg.height)

    @classmethod
    def from_map(cls, mapdata: MapData, cfg: RenderConfig):
        manager = cls(cfg)
        # creating hub entities
        for hub in mapdata.hubs.values():
            hub_entity = HubStation(manager.mlx_ptr, manager.cfg, hub)
            manager.hubs[hub_entity.name] = hub_entity

        # finding the first hub
        start_hub = next(
            hub for hub in mapdata.hubs.values() if hub.type == HubType.start_hub
        )
        # creating drone entities
        for drone in mapdata.drones.values():
            drone_entity = Drone(manager.mlx_ptr, manager.cfg, drone, manager.hubs[start_hub.name])
            manager.drones[drone_entity.id] = drone_entity

        # attaching drones to the first hub
        manager.hubs[start_hub.name].drones = manager.drones

        # creating connections
        manager.connections = [
            Connection(manager.hubs[conn.hub_a], manager.hubs[conn.hub_b], conn.capacity)
            for conn in mapdata.connections
        ]
        # attaching connections to hubs
        for conn in manager.connections:
            conn.hub_a.connections.append(conn)
            conn.hub_b.connections.append(conn)


        return manager

    def tilify(self, shape: set[tuple[int, int, int]]) -> None:
        img_tile = mlx.mlx_new_image(self.mlx_ptr, self.cfg.width, self.cfg.height)
        x_size = max(x[0] for x in shape) + 1
        y_size = max(y[1] for y in shape) + 1
        x_offset = y_offset = 0
        for pixel in shape:
            for y in range(y_offset, self.cfg.height, y_size):
                for x in range(x_offset, self.cfg.width, x_size):
                    if x + pixel[0] < self.cfg.width and y + pixel[1] < self.cfg.height:
                        idx = ((y + pixel[1]) * img_tile.contents.width + (x + pixel[0])) * 4
                        # pixel
                        img_tile.contents.pixels[idx] = pixel[2] >> 24 & 0xff
                        img_tile.contents.pixels[idx + 1] = pixel[2] >> 16 & 0xff
                        img_tile.contents.pixels[idx + 2] = pixel[2] >> 8 & 0xff
                        img_tile.contents.pixels[idx + 3] = pixel[2] & 0xff

        self.img_tile = img_tile

    def _write_text(self, img, text: str, pos: tuple[int, int]) -> None:
        init_x, init_y = pos
        x, y = init_x, init_y

        for c in text:
            if c == "\n":
                y += 10
                x = init_x
                continue
            for px, py, color in self.cfg.font[c].pixels:
                idx = ((py + y) * img.contents.width + (px + x)) * 4

                # pixel
                img.contents.pixels[idx] = color >> 24 & 0xff
                img.contents.pixels[idx + 1] = color >> 16 & 0xff
                img.contents.pixels[idx + 2] = color >> 8 & 0xff
                img.contents.pixels[idx + 3] = color & 0xff

                # shadow
                idx += img.contents.width * 4 + 4
                img.contents.pixels[idx] = 0
                img.contents.pixels[idx + 1] = 0
                img.contents.pixels[idx + 2] = 0
                img.contents.pixels[idx + 3] = 255

            x += self.cfg.font[c].width


    def _draw_entity(self, entity: Entity) -> None:
        for pixel in entity.shape:
            for y in range(pixel[1], (pixel[1] + 1)):
                for x in range(pixel[0], (pixel[0] + 1)):
                    r = (pixel[2] >> 24) & 0xFF
                    g = (pixel[2] >> 16) & 0xFF
                    b = (pixel[2] >> 8) & 0xFF
                    if r == g and g == b:
                        color = pixel[2]
                    else:
                        color = entity.color
                    idx = (y * entity.img.contents.width + x) * 4
                    entity.img.contents.pixels[idx] = color >> 24 & 0xff
                    entity.img.contents.pixels[idx + 1] = color >> 16 & 0xff
                    entity.img.contents.pixels[idx + 2] = color >> 8 & 0xff
                    entity.img.contents.pixels[idx + 3] = color & 0xff

    def _attach_hub_drones(self, hub: HubStation) -> None:
        idx = 0
        for id, drone in hub.drones.items():
            if idx >= 12:
                idx = 11
            offset_x = (idx % 3) * 16 + 10
            offset_y = (idx // 3) * 11 + 10
            idx += 1
            posx = hub.pos[0] + offset_x
            poxy = hub.pos[1] + offset_y
            drone.pos = (posx, poxy)
            self._attach_entity(drone, drone.pos)

    def _attach_entity(self, entity: Entity, pos: tuple[int, int] | None = None) -> None:
        if pos is None:
            pos = entity.pos
        mlx.mlx_image_to_window(self.mlx_ptr, entity.img, pos[0], pos[1])
        if isinstance(entity, HubStation):
            entity.img.contents.instances[0].z = HUB_DEPTH
        elif isinstance(entity, Drone):
            entity.img.contents.instances[0].z = DRONE_DEPTH

    def _draw_entities_names(self, uppercase: bool = True) -> None:
        for entity in self.hubs.values():
            name = entity.name
            name = name.upper() if uppercase else name.title()
            self._write_text(self.img_stats, name, (entity.pos[0], entity.pos[1] - 12))

    def _draw_hub_stats(self, uppercase: bool = False) -> None:
        # stats are drawn in bottom
        for hub in self.hubs.values():
            stats = f"{len(hub.drones)}/{hub.metadata.max_drones} {hub.metadata.zone.value}"
            stats = stats.upper() if uppercase else stats.title()
            self._write_text(
                self.img_stats, stats, (hub.pos[0], hub.pos[1] + hub.size[1] + 2)
            )

    def _draw_lines(self, color: int = 0xFFFFFF50) -> None:
        for conn in self.connections:
            hub_a = conn.hub_a
            hub_b = conn.hub_b

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
                        idx = ((int(y) + j) * self.img_tile.contents.width + (int(x) + i)) * 4
                        self.img_tile.contents.pixels[idx] = color >> 24 & 0xff
                        self.img_tile.contents.pixels[idx + 1] = color >> 16 & 0xff
                        self.img_tile.contents.pixels[idx + 2] = color >> 8 & 0xff
                        self.img_tile.contents.pixels[idx + 3] = color & 0xff

                x += x_inc
                y += y_inc

            # write capacity
            capacity_text = str(conn.capacity)
            text_width = len(capacity_text) * 8
            text_x = int((x1 + x2) / 2 - text_width / 2 + 2)
            text_y = int((y1 + y2) / 2 - 3)
            self._write_text(self.img_tile, capacity_text, (text_x, text_y))


    def _animate_queue(self) -> None:
        global STEPS
        global ANIMATING_LINE
        global IS_QUEUE
        global QUEUE


        for drone_id, (start_pos, end_pos, start_loc, dest) in QUEUE.items():
            drone = self.drones[drone_id]
            if STEPS == 0:
                drone.img.contents.instances[0].x = end_pos[0]
                drone.img.contents.instances[0].y = end_pos[1]
                drone.location = dest
                drone.pos = (end_pos[0], end_pos[1])

            elif STEPS == 60:
                drone.img.contents.instances[0].x = start_pos[0]
                drone.img.contents.instances[0].y = start_pos[1]
            else:
                drone.img.contents.instances[0].x = int(start_pos[0] + (end_pos[0] - start_pos[0]) * (60 - STEPS) / 60)
                drone.img.contents.instances[0].y = int(start_pos[1] + (end_pos[1] - start_pos[1]) * (60 - STEPS) / 60)

        if STEPS == 0:
            LIST_OF_MOVES.clear()
            QUEUE.clear()
            ANIMATING_LINE = 0
            IS_QUEUE = False
            STEPS = 60
            return
        STEPS -= 1



    def _animate_line(self) -> None:
        global ANIMATING_LINE
        global STEPS
        global IS_QUEUE
        global QUEUE

        if IS_QUEUE:
            self._animate_queue()
            return

        # setting up queue for queue animation
        for move in LIST_OF_MOVES:
            # going to a hub
            if path_to_hub := re.match(r"D(\d+)-(\w+)$", move):
                drone_id = int(path_to_hub.group(1))
                dest_name = path_to_hub.group(2)
                drone = self.drones[drone_id]
                dest = self.hubs[dest_name]
                if isinstance(drone.location, HubStation):
                    start_pos = drone.pos
                    end_pos = (
                        dest.pos[0] + dest.size[0] // 2 - drone.size[0] // 2,
                        dest.pos[1] + dest.size[1] // 2 - drone.size[1] // 2
                    )
                elif isinstance(drone.location, Connection):
                    start_pos = (
                        drone.location.center[0] - drone.size[0] // 2,
                        drone.location.center[1] - drone.size[1] // 2
                    )
                    end_pos = (
                        dest.pos[0] + dest.size[0] // 2 - drone.size[0] // 2,
                        dest.pos[1] + dest.size[1] // 2 - drone.size[1] // 2
                    )

            # going to connection
            elif path_to_connection := re.match(r"D(\d+)-(\w+)-(\w+)", move):
                drone_id = int(path_to_connection.group(1))
                hub_a_name = path_to_connection.group(2)
                hub_b_name = path_to_connection.group(3)
                drone = self.drones[drone_id]
                hub_a = self.hubs[hub_a_name]
                hub_b = self.hubs[hub_b_name]

                if isinstance(drone.location, HubStation):
                    dest = next(
                        conn for conn in hub_a.connections
                        if (conn.hub_a == hub_b or conn.hub_b == hub_b)
                    )
                    # start and end should be the center of connection
                    start_pos = (hub_a.pos[0] + hub_a.size[0] // 2 - drone.size[0] // 2,
                                 hub_a.pos[1] + hub_a.size[1] // 2 - drone.size[1] // 2
                                 )
                    end_pos = (
                        dest.center[0] - drone.size[0] // 2,
                        dest.center[1] - drone.size[1] // 2
                    )

            QUEUE[drone_id] = (start_pos, end_pos, drone.location, dest)

        IS_QUEUE = True
        self._animate_queue()


    def _animate(self):
        global ANIMATING_LINE
        global LIST_OF_MOVES

        if ANIMATING_LINE:
            self._animate_line()

        else:
            try:
                line = self._solution_line.popleft()
                ANIMATING_LINE = 1
                for move in line.split():
                    LIST_OF_MOVES.append(move.strip())
                self._animate_line()
            except IndexError:
                global ANIMATING
                ANIMATING = 0
                return


    def _loop_hook(self, param=None):
        if ANIMATING:
            self._animate()


    def _hook_func(self, keydata, param=None):
        global ANIMATING

        if mlx.mlx_is_key_down(self.mlx_ptr, MLX_KEY_ESCAPE) or mlx.mlx_is_key_down(self.mlx_ptr, MLX_KEY_Q):
            mlx.mlx_close_window(self.mlx_ptr)

        if not ANIMATING and mlx.mlx_is_key_down(self.mlx_ptr, MLX_KEY_SPACE):
            ANIMATING = 1

    def run(
        self,
        solution: str,
        no_name: bool = False,
        no_stats: bool = False,
    ) -> None:

        # attach tile and background images to window
        mlx.mlx_image_to_window(self.mlx_ptr, self.img_tile, 0, 0)
        mlx.mlx_image_to_window(self.mlx_ptr, self.img_stats, 0, 0)
        self.img_stats.contents.instances[0].z = 2

        for drone in self.drones.values():
            self._draw_entity(drone)

        for hub in self.hubs.values():
            self._draw_entity(hub)
            self._attach_entity(hub)
            self._attach_hub_drones(hub)

        self._draw_lines()

        if not no_name:
            self._draw_entities_names()

        if not no_stats:
            self._draw_hub_stats()


        # print(f"img_stats {self.img_stats.contents.instances[0].z}")
        # print(f"img_tile {self.img_tile.contents.instances[0].z}")
        # print(f"hub {self.hubs[next(iter(self.hubs))].img.contents.instances[0].z}")


        self._solution_line.extend(solution.splitlines())

        self._hook_func_cb = ctypes.CFUNCTYPE(None, ctypes.c_void_p)(self._hook_func)
        self._loop_hook_cb = ctypes.CFUNCTYPE(None, ctypes.c_void_p)(self._loop_hook)
        mlx.mlx_key_hook(self.mlx_ptr, self._hook_func_cb, None)
        mlx.mlx_loop_hook(self.mlx_ptr, self._loop_hook_cb, None) # type: ignore

        mlx.mlx_loop(self.mlx_ptr)
        mlx.mlx_terminate(self.mlx_ptr)

