from MLX.libmlx import *
from Common import *
from MapParser import MapData
from collections import deque
import ctypes
import re
import random


CONNECTION_AND_TRAIL_DEPTH = 1
HUB_DEPTH = 3
STATS_DEPTH = 4
DRONE_DEPTH = 5
START_END_HUBS_DEPTH = 6

RANDOM_AMOUNT = 5
TRAIL_OPACITY = 0xff

ANIMATING = 0
ANIMATING_LINE = 0
SOLUTION_LINE = []
DRONES_QUEUE = deque()
STEPS = 80
STEP_IDX = STEPS



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
        self.img_name = None
        self.img_stat = None


class Drone(Entity):
    def __init__(self, mlx_ptr, cfg: RenderConfig, drone_base: DroneBase, current_hub: HubStation) -> None:
        self.id: int = drone_base.id
        self.location: HubStation | Connection = current_hub
        color = list(ColorType)[(self.id % 7) * 4]
        super().__init__(mlx_ptr, cfg, drone_base.coord, color, cfg.shapes.drone)


class HubStation(Entity):
    def __init__(
        self,
        mlx_ptr,
        cfg: RenderConfig,
        hub_model: HubBase,
    ) -> None:
        self.name: str = hub_model.name
        self.metadata: HubMetadata = hub_model.metadata
        self.type: HubType = hub_model.type
        self.drones: deque[Drone] = deque()
        self.connections: list[Connection] = []
        shape = self.get_shape_by_type(self.type, self.metadata, cfg)
        super().__init__(
            mlx_ptr, cfg, hub_model.pos, hub_model.metadata.color, shape
        )

    @staticmethod
    def get_shape_by_type(hub_type: HubType, metadata: HubMetadata, cfg: RenderConfig) -> set[tuple[int, int, int]]:
        if metadata.zone == ZoneType.restricted:
            return cfg.shapes.hub_restricted
        elif metadata.zone == ZoneType.priority:
            return cfg.shapes.hub_priority
        elif metadata.zone == ZoneType.blocked:
            return cfg.shapes.hub_blocked
        else:
            return cfg.shapes.hub


class Connection:
    def __init__(self, hub_a: HubStation, hub_b: HubStation, capacity: int):
        self.hub_a = hub_a
        self.hub_b = hub_b
        self.capacity = capacity
        self.start_pos = (hub_a.pos[0] + hub_a.size[0] // 2, hub_a.pos[1] + hub_a.size[1] // 2)
        self.end_pos = (hub_b.pos[0] + hub_b.size[0] // 2, hub_b.pos[1] + hub_b.size[1] // 2)
        self.center = ((self.start_pos[0] + self.end_pos[0]) // 2, (self.start_pos[1] + self.end_pos[1]) // 2)
        self.drones: deque[Drone] = deque()


class MlxWindow:
    def __init__(self, cfg: RenderConfig) -> None:
        self.connections: list[Connection] = []
        self.mlx_ptr = mlx.mlx_init(cfg.width, cfg.height, b"Fly-in", True)
        self.hubs: dict[str, HubStation] = {}
        self.drones: dict[int, Drone] = {}
        self.cfg: RenderConfig = cfg
        self._solution = deque()
        self.img_lines = mlx.mlx_new_image(self.mlx_ptr, self.cfg.width, self.cfg.height)

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
        manager.hubs[start_hub.name].drones.extend(manager.drones.values())

        # creating connections
        manager.connections = [
            Connection(manager.hubs[conn.hub_a], manager.hubs[conn.hub_b], conn.link_capacity)
            for conn in mapdata.connections
        ]
        # attaching connections to hubs
        for conn in manager.connections:
            conn.hub_a.connections.append(conn)
            conn.hub_b.connections.append(conn)

        return manager

    @staticmethod
    def fill_image(img, color: int):
        for y in range(img.contents.height):
            for x in range(img.contents.width):
                idx = (y * img.contents.width + x) * 4
                img.contents.pixels[idx] = color >> 24 & 0xff
                img.contents.pixels[idx + 1] = color >> 16 & 0xff
                img.contents.pixels[idx + 2] = color >> 8 & 0xff
                img.contents.pixels[idx + 3] = color & 0xff

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

    def _attach_entity(self, entity: Entity, pos: tuple[int, int] | None = None) -> None:
        if pos is None:
            pos = entity.pos
        mlx.mlx_image_to_window(self.mlx_ptr, entity.img, pos[0], pos[1])
        if isinstance(entity, HubStation):
            depth = HUB_DEPTH
            if entity.type in (HubType.start_hub, HubType.end_hub):
                depth = START_END_HUBS_DEPTH + len(self.drones)
            entity.img.contents.instances[0].z = depth
        elif isinstance(entity, Drone):
            entity.img.contents.instances[0].z = DRONE_DEPTH + entity.id

    def _draw_hub_name(self, hub: HubStation, uppercase: bool = True) -> None:
        name = hub.name
        name = name.upper() if uppercase else name.title()
        hub.img_name = mlx.mlx_new_image(self.mlx_ptr, len(name) * 6, 10)
        self._write_text(hub.img_name, name, (0, 0))

    def _attach_hub_name(self, hub: HubStation) -> None:
        if hub.img_name:
            mlx.mlx_image_to_window(self.mlx_ptr, hub.img_name, hub.pos[0], hub.pos[1] - 12)
            hub.img_name.contents.instances[0].z = HUB_DEPTH

    def _draw_hubs_stats(self, uppercase: bool = False) -> None:

        # delete image and assign new one
        for hub in self.hubs.values():
            if hub.img_stat:
                mlx.mlx_delete_image(self.mlx_ptr, hub.img_stat)
                hub.img_stat = None
            self._draw_hub_stats(hub, uppercase)
            self._attach_hub_stats(hub)

    def _draw_line(self,
                   img, start: tuple[int, int],
                   end: tuple[int, int],
                   color: int = 0xffffffaa,
                   thickness: int = 0
                   ) -> None:
        x1, y1 = start
        x2, y2 = end

        dx = x2 - x1
        dy = y2 - y1
        steps = max(abs(dx), abs(dy))
        if steps == 0:
            return
        x_inc = dx / steps
        y_inc = dy / steps

        x, y = x1, y1
        for _ in range(steps):
            for j in range(-thickness, thickness + 1):
                for i in range(-thickness, thickness + 1):
                    idx = ((int(y) + j) * img.contents.width + (int(x) + i)) * 4
                    img.contents.pixels[idx] = color >> 24 & 0xff
                    img.contents.pixels[idx + 1] = color >> 16 & 0xff
                    img.contents.pixels[idx + 2] = color >> 8 & 0xff
                    img.contents.pixels[idx + 3] = color & 0xff

            x += x_inc
            y += y_inc

    def _draw_connections(self, color: int = 0xFFFFFF50) -> None:
        for conn in self.connections:
            hub_a = conn.hub_a
            hub_b = conn.hub_b

            # calculating center points of hubs
            x1 = hub_a.pos[0] + hub_a.size[0] // 2
            y1 = hub_a.pos[1] + hub_a.size[1] // 2
            x2 = hub_b.pos[0] + hub_b.size[0] // 2
            y2 = hub_b.pos[1] + hub_b.size[1] // 2

            # thickness based on capacity
            self._draw_line(
                self.img_lines,
                (x1, y1), (x2, y2),
                color=color,
                thickness=min(conn.capacity, 8) * 3
                )

            # write capacity
            capacity_text = str(conn.capacity)
            text_width = len(capacity_text) * 8
            text_x = int((x1 + x2) / 2 - text_width / 2 + 2)
            text_y = int((y1 + y2) / 2 - 3)
            self._write_text(self.img_lines, capacity_text, (text_x, text_y))

    def _draw_hub_stats(self, hub: HubStation, uppercase: bool = False) -> None:
        stats = f"{len(hub.drones)}/{hub.metadata.max_drones} {hub.metadata.zone.value}"
        stats = stats.upper() if uppercase else stats.title()
        hub.img_stat = mlx.mlx_new_image(self.mlx_ptr, len(stats) * 8, 10)
        self._write_text(
            hub.img_stat, stats, (0, 0)
        )

    def _attach_hub_stats(self, hub: HubStation) -> None:
        if hub.img_stat:
            mlx.mlx_image_to_window(self.mlx_ptr, hub.img_stat, hub.pos[0], hub.pos[1] + hub.size[1] + 2)
            hub.img_stat.contents.instances[0].z = STATS_DEPTH

    def _animate_drones(self) -> None:
        global STEP_IDX
        global ANIMATING_LINE
        global DRONES_QUEUE

        for (drone, start_pos, end_pos, dest) in DRONES_QUEUE:
            if STEP_IDX == 0:
                if isinstance(dest, HubStation) and dest.type == HubType.end_hub:
                    drone.img.contents.enabled = False
                drone.location = dest
                drone.pos = (end_pos[0], end_pos[1])
            else:
                from_x = drone.img.contents.instances[0].x
                from_y = drone.img.contents.instances[0].y
                to_x = int(start_pos[0] + (end_pos[0] - start_pos[0]) * (STEPS - STEP_IDX) / STEPS)
                to_y = int(start_pos[1] + (end_pos[1] - start_pos[1]) * (STEPS - STEP_IDX) / STEPS)
                drone.img.contents.instances[0].x = to_x
                drone.img.contents.instances[0].y = to_y

                # draw trail in img_trails
                self._draw_line(
                    self.img_lines,
                    (
                        from_x + drone.size[0] // 2,
                        from_y + drone.size[1] // 2
                    ),
                    (
                        to_x + drone.size[0] // 2,
                        to_y + drone.size[1] // 2
                    ),
                     color=drone.color
                     )

        if STEP_IDX == 0:
            SOLUTION_LINE.clear()
            DRONES_QUEUE.clear()
            ANIMATING_LINE = 0
            STEP_IDX = STEPS
            return
        STEP_IDX -= 1

    def _animate_line(self) -> None:
        global ANIMATING_LINE
        global STEP_IDX
        global DRONES_QUEUE

        if DRONES_QUEUE:
            self._animate_drones()
            return

        # setting up queue for queue animation
        for move in SOLUTION_LINE:
            # going to a hub
            if path_to_hub := re.match(r"D(\d+)-(\w+)$", move):
                drone_id = int(path_to_hub.group(1))
                dest_name = path_to_hub.group(2)
                drone = self.drones[drone_id]
                dest = self.hubs[dest_name]
                if isinstance(drone.location, HubStation):
                    start_pos = drone.img.contents.instances[0].x, drone.img.contents.instances[0].y
                    end_pos = (
                        dest.pos[0] + dest.size[0] // 2 - drone.size[0] // 2,
                        dest.pos[1] + dest.size[1] // 2 - drone.size[1] // 2
                    )
                elif isinstance(drone.location, Connection):
                    start_pos = drone.img.contents.instances[0].x, drone.img.contents.instances[0].y
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
                    start_pos = drone.img.contents.instances[0].x, drone.img.contents.instances[0].y
                    end_pos = (
                        dest.center[0] - drone.size[0] // 2,
                        dest.center[1] - drone.size[1] // 2
                    )
            # remove drone from prev location
            drone.location.drones.remove(drone)
            # add drone to new location
            dest.drones.append(drone)

            # add randomness to the drone position if it's going to a hub
            randomamount = RANDOM_AMOUNT if isinstance(dest, HubStation) else RANDOM_AMOUNT // 2
            random_x = random.randint(-randomamount, randomamount)
            random_y = random.randint(-randomamount, randomamount)
            posx = end_pos[0] + random_x
            posy = end_pos[1] + random_y

            # append drone to the queue for animation
            DRONES_QUEUE.append(
                    (drone, start_pos, (posx, posy), dest))

        self._animate_drones()

    def _animate(self):
        global ANIMATING_LINE
        global SOLUTION_LINE

        if ANIMATING_LINE:
            self._animate_line()

        else:
            try:
                line = self._solution.popleft()
                ANIMATING_LINE = 1
                for move in line.split():
                    SOLUTION_LINE.append(move.strip())
                self._animate_line()
            except IndexError:
                global ANIMATING
                ANIMATING = 0
                return

    def _loop_hook(self, param=None):
        if ANIMATING:
            self._animate()
        self._draw_hubs_stats()

    def _hook_func(self, keydata, param=None):
        global ANIMATING

        if mlx.mlx_is_key_down(self.mlx_ptr, MLX_KEY_ESCAPE) or mlx.mlx_is_key_down(self.mlx_ptr, MLX_KEY_Q):
            mlx.mlx_close_window(self.mlx_ptr)

        if not ANIMATING and mlx.mlx_is_key_down(self.mlx_ptr, MLX_KEY_SPACE):
            ANIMATING = 1

    def run(
        self,
        solution: str | None = None,
    ) -> None:

        mlx.mlx_image_to_window(self.mlx_ptr, self.img_lines, 0, 0)
        self.img_lines.contents.instances[0].z = CONNECTION_AND_TRAIL_DEPTH


        for hub in self.hubs.values():
            self._draw_entity(hub)
            self._attach_entity(hub)
            self._draw_hub_name(hub)
            self._attach_hub_name(hub)

        start_hub = next((hub for hub in self.hubs.values() if hub.type == HubType.start_hub), None)

        if start_hub:
            for drone in self.drones.values():
                drone.pos = (
                    start_hub.pos[0] + start_hub.img.contents.width // 2 - drone.size[0] // 2 + random.randint(-10, 10),
                    start_hub.pos[1] + start_hub.img.contents.height // 2 - drone.size[1] // 2 + random.randint(-10, 10)
                )
                self._draw_entity(drone)
                self._attach_entity(drone, drone.pos)
        else:
            raise ValueError("No start hub found in the map.")

        self._draw_connections()

        if solution:
            self._solution.extend(solution.splitlines())

        self._hook_func_cb = ctypes.CFUNCTYPE(None, ctypes.c_void_p)(self._hook_func)
        self._loop_hook_cb = ctypes.CFUNCTYPE(None, ctypes.c_void_p)(self._loop_hook)
        mlx.mlx_key_hook(self.mlx_ptr, self._hook_func_cb, None)
        mlx.mlx_loop_hook(self.mlx_ptr, self._loop_hook_cb, None) # type: ignore

        mlx.mlx_loop(self.mlx_ptr)
        mlx.mlx_terminate(self.mlx_ptr)

