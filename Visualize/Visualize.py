from MLX.libmlx import (
    mlx, MLX_KEY_ESCAPE, MLX_KEY_Q, MLX_KEY_SPACE,
    MLX_KEY_RIGHT, MLX_KEY_LEFT
)
from Common import (
    HubBase, DroneBase, HubMetadata, HubType, ZoneType, ColorType
)
from RenderConfig import RenderConfig, Shape
from MapParser import MapData
from collections import deque
import ctypes
import re
import random
import sys
import time

BG_DEPTH = 1
HUB_DEPTH = 3
STATS_DEPTH = 4
DRONE_DEPTH = 5
DRONE_TRAIL_DEPTH = 6
START_END_HUBS_DEPTH = 7

GLYPH_SIZE = 6

ANIMATING = False
SOLUTION_LINE = []
DRONES_QUEUE = deque()
STEPS = 80
STEP_IDX = STEPS

ANIMATION_FPS = 120
STEP_INTERVAL = 1 / ANIMATION_FPS
LAST_STEP_TIME = 0.0


class Entity:
    def __init__(
        self,
        mlx_ptr,
        cfg: RenderConfig,
        coord: tuple[int, int],
        color: int,
        shape: Shape,
    ):
        self.color = color
        self.shape = shape
        self.coord = coord
        self.size = (
            max(x[0] for x in shape.pixels) + 1,
            max(y[1] for y in shape.pixels) + 1
            )
        self.pos = (
            int((coord[0] - cfg.min_coord[0])
                * (cfg.cell + cfg.space) + cfg.paddin[0]),
            int((coord[1] - cfg.min_coord[1])
                * (cfg.cell + cfg.space) + cfg.paddin[1]),
        )

        self.img = mlx.mlx_new_image(
            mlx_ptr,
            self.size[0],
            self.size[1],
        )


class Drone(Entity):
    def __init__(
        self, mlx_ptr, cfg: RenderConfig,
        drone_base: DroneBase,
        current_hub: HubStation
    ) -> None:
        self.id: int = drone_base.id
        self.location: HubStation | Connection = current_hub
        color = list(ColorType)[(self.id % 7) * 4]
        super().__init__(
            mlx_ptr, cfg,
            drone_base.coord,
            color, cfg.shapes.drone
            )


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
            mlx_ptr, cfg, hub_model.pos,
            hub_model.metadata.color, shape
            )
        self.img_name = mlx.mlx_new_image(
            mlx_ptr,
            self.size[0],
            cfg.font["A"].height + 1,
        )
        self.img_stat = mlx.mlx_new_image(
            mlx_ptr,
            64,
            8,
        )

    @staticmethod
    def get_shape_by_type(
        hub_type: HubType, metadata: HubMetadata, cfg: RenderConfig
    ) -> Shape:
        if hub_type == HubType.start_hub:
            return cfg.shapes.hub_start
        elif hub_type == HubType.end_hub:
            return cfg.shapes.hub_end
        elif metadata.zone == ZoneType.restricted:
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
        self.start_pos = (
            hub_a.pos[0] + hub_a.size[0] // 2,
            hub_a.pos[1] + hub_a.size[1] // 2,
        )
        self.end_pos = (
            hub_b.pos[0] + hub_b.size[0] // 2,
            hub_b.pos[1] + hub_b.size[1] // 2,
        )
        self.center = (
            (self.start_pos[0] + self.end_pos[0]) // 2,
            (self.start_pos[1] + self.end_pos[1]) // 2,
        )
        self.drones: deque[Drone] = deque()


class MlxWindow:
    def __init__(self, cfg: RenderConfig) -> None:
        self.connections: list[Connection] = []
        self.mlx_ptr = mlx.mlx_init(
            cfg.window_size[0], cfg.window_size[1], b"Fly-in", True
        )
        self.hubs: dict[str, HubStation] = {}
        self.drones: dict[int, Drone] = {}
        self.cfg: RenderConfig = cfg
        self._solution: str = ""
        self._solution_queue = deque()
        self._turns_count: int = 0

        self.img_bg = mlx.mlx_new_image(
            self.mlx_ptr, self.cfg.window_size[0], self.cfg.window_size[1]
        )
        self.img_stats = mlx.mlx_new_image(self.mlx_ptr, 100, 8)
        self.img_trail = mlx.mlx_new_image(
            self.mlx_ptr, self.cfg.window_size[0], self.cfg.window_size[1]
        )

    @classmethod
    def from_map(cls, mapdata: MapData, cfg: RenderConfig):
        manager = cls(cfg)
        # creating hub entities
        for hub in mapdata.hubs.values():
            hub_entity = HubStation(manager.mlx_ptr, manager.cfg, hub)
            manager.hubs[hub_entity.name] = hub_entity

        # finding the first hub
        start_hub = next(
            hub for hub in mapdata.hubs.values()
            if hub.type == HubType.start_hub
        )
        # creating drone entities
        for drone in mapdata.drones.values():
            drone_entity = Drone(
                manager.mlx_ptr,
                manager.cfg,
                drone,
                manager.hubs[start_hub.name]
            )
            manager.drones[drone_entity.id] = drone_entity

        # attaching drones to the first hub
        manager.hubs[start_hub.name].drones.extend(manager.drones.values())

        # creating connections
        manager.connections = [
            Connection(
                manager.hubs[conn.hub_a],
                manager.hubs[conn.hub_b],
                conn.link_capacity
            )
            for conn in mapdata.connections
        ]
        # attaching connections to hubs
        for conn in manager.connections:
            conn.hub_a.connections.append(conn)
            conn.hub_b.connections.append(conn)

        return manager

    @staticmethod
    def _fill_image(img, color: int):
        for y in range(img.contents.height):
            for x in range(img.contents.width):
                idx = (y * img.contents.width + x) * 4
                img.contents.pixels[idx] = color >> 24 & 0xFF
                img.contents.pixels[idx + 1] = color >> 16 & 0xFF
                img.contents.pixels[idx + 2] = color >> 8 & 0xFF
                img.contents.pixels[idx + 3] = color & 0xFF


    def _draw_window_stats(
        self, turn_count: int | None = None,
        size: int = 1, color: int = 0xFFFFFFFF
    ):
        if not turn_count:
            turn_count = self._turns_count
        self._fill_image(self.img_stats, 0x00000000)
        total_turns_count = len(self._solution.splitlines())
        self._write_text(
            self.img_stats,
            f"Turn: {turn_count}/{total_turns_count}",
            (0, 0),
            size=size,
            color=color,
        )

    def _cenimatic_black_bars(self, img, bar_thickness: int = 50):
        for y in range(bar_thickness):
            for x in range(img.contents.width):
                # Top bar
                idx = (y * img.contents.width + x) * 4
                img.contents.pixels[idx] = 0
                img.contents.pixels[idx + 1] = 0
                img.contents.pixels[idx + 2] = 0
                img.contents.pixels[idx + 3] = 255

                # Bottom bar
                idx = (
                    (img.contents.height - 1 - y)
                    * img.contents.width + x
                    ) * 4
                img.contents.pixels[idx] = 0
                img.contents.pixels[idx + 1] = 0
                img.contents.pixels[idx + 2] = 0
                img.contents.pixels[idx + 3] = 255

    def _write_text(
        self,
        img,
        text: str,
        pos: tuple[int, int],
        size: int = 1,
        color: int = 0xFFFFFFFF,
    ) -> None:
        init_x, init_y = pos
        x, y = init_x, init_y

        for c in text:
            if c == "\n":
                y += 10 * size
                x = init_x
                continue
            for px, py, _ in self.cfg.font[c].pixels:
                for sy in range(size):
                    for sx in range(size):
                        actual_x = px * size + x + sx
                        actual_y = py * size + y + sy
                        idx = (actual_y * img.contents.width + actual_x) * 4

                        # pixel
                        img.contents.pixels[idx] = color >> 24 & 0xFF
                        img.contents.pixels[idx + 1] = color >> 16 & 0xFF
                        img.contents.pixels[idx + 2] = color >> 8 & 0xFF
                        img.contents.pixels[idx + 3] = color & 0xFF

                        # shadow
                        sidx = (
                            (
                                actual_y + 1
                            ) * img.contents.width + (actual_x + 1)
                        ) * 4
                        img.contents.pixels[sidx] = 0
                        img.contents.pixels[sidx + 1] = 0
                        img.contents.pixels[sidx + 2] = 0
                        img.contents.pixels[sidx + 3] = 255

            x += self.cfg.font[c].width * size

    def _draw_entity(self, entity: Entity) -> None:
        hub_color = entity.color
        if entity.color == ColorType.rainbow:
            color_list = [
                ColorType.red,
                ColorType.orange,
                ColorType.yellow,
                ColorType.green,
                ColorType.teal,
                ColorType.blue,
                ColorType.cyan,
                ColorType.purple,
                ColorType.violet,
                ColorType.magenta,
                ColorType.pink,
            ]
        height = entity.size[1]

        for pixel in entity.shape.pixels:
            x, y = pixel[0], pixel[1]
            r = (pixel[2] >> 24) & 0xFF
            g = (pixel[2] >> 16) & 0xFF
            b = (pixel[2] >> 8) & 0xFF
            if r == g and g == b:
                color = pixel[2]
            else:
                color = hub_color
                if entity.color == ColorType.rainbow:
                    try:
                        color = color_list[int(y / (height / len(color_list)))]
                    except (ZeroDivisionError, IndexError):
                        color = ColorType.white
            idx = (y * entity.img.contents.width + x) * 4
            entity.img.contents.pixels[idx] = color >> 24 & 0xFF
            entity.img.contents.pixels[idx + 1] = color >> 16 & 0xFF
            entity.img.contents.pixels[idx + 2] = color >> 8 & 0xFF
            entity.img.contents.pixels[idx + 3] = color & 0xFF

    def _attach_entity(
        self, entity: Entity, pos: tuple[int, int] | None = None
    ) -> None:
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

    def _draw_attach_hub_name(
            self, hub: HubStation, uppercase: bool = True
            ) -> None:
        name = hub.name
        if len(name) > 10:
            name = name[:8] + ".."

        name = name.upper() if uppercase else name.title()

        self._write_text(hub.img_name, name, (0, 0))
        mlx.mlx_image_to_window(
            self.mlx_ptr, hub.img_name,
            hub.pos[0], hub.pos[1] - 10
        )
        hub.img.contents.instances[0].z = HUB_DEPTH

    def _draw_drone_count(
            self, hub: HubStation, uppercase: bool = False
            ) -> None:
        n_of_drones = len(hub.drones)
        cap_of_hub = hub.metadata.max_drones

        if hub.type == HubType.end_hub or hub.type == HubType.start_hub:
            color = 0xBABABA << 8 | 0xFF
        elif n_of_drones > cap_of_hub:
            color = 0xFF7272 << 8 | 0xFF
        elif n_of_drones == cap_of_hub:
            color = 0xBABABA << 8 | 0xFF
        else:
            color = 0xFFFFFF << 8 | 0xFF
        stats = f"{n_of_drones}/{cap_of_hub}"
        stats = stats.upper() if uppercase else stats.title()
        self._write_text(hub.img_stat, stats, (0, 0), color=color)

    def _draw_attach_drone_count(
        self, hub: HubStation, uppercase: bool = False
    ) -> None:
        self._draw_drone_count(hub, uppercase=uppercase)
        mlx.mlx_image_to_window(
            self.mlx_ptr, hub.img_stat, hub.pos[0], hub.pos[1] + hub.size[1]
        )
        hub.img.contents.instances[0].z = STATS_DEPTH

    def _update_drone_count(
            self, hub: HubStation, is_upper: bool = False
            ) -> None:
        self._fill_image(hub.img_stat, 0x00000000)
        self._draw_attach_drone_count(hub, uppercase=is_upper)

    def _draw_line(
        self,
        img,
        start: tuple[int, int],
        end: tuple[int, int],
        color: int = 0xFFFFFFAA,
        thickness: int = 0,
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
                    idx = (
                        (int(y) + j) * img.contents.width + (int(x) + i)
                        ) * 4
                    img.contents.pixels[idx] = color >> 24 & 0xFF
                    img.contents.pixels[idx + 1] = color >> 16 & 0xFF
                    img.contents.pixels[idx + 2] = color >> 8 & 0xFF
                    img.contents.pixels[idx + 3] = color & 0xFF

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
                self.img_bg,
                (x1, y1),
                (x2, y2),
                color=color,
                thickness=min(conn.capacity, 8) * 3,
            )

            # calculating position for capacity text
            capacity_text = str(conn.capacity)
            text_width = len(capacity_text) * 8
            text_x = int((x1 + x2) / 2 - text_width / 2 + 2)
            text_y = int((y1 + y2) / 2 - 3)

            # write capacity
            self._write_text(self.img_bg, capacity_text, (text_x, text_y))

    def _animate_drones(self) -> None:
        global STEP_IDX

        for drone, start_pos, end_pos, dest in DRONES_QUEUE:

            pos_from = (
                drone.img.contents.instances[0].x,
                drone.img.contents.instances[0].y,
            )

            # bazier curve for more natural movement
            pos_to = (
                int(
                    start_pos[0]
                    + (end_pos[0] - start_pos[0]) * (STEPS - STEP_IDX) / STEPS
                ),
                int(
                    start_pos[1]
                    + (end_pos[1] - start_pos[1]) * (STEPS - STEP_IDX) / STEPS
                ),
            )

            drone.img.contents.instances[0].x = pos_to[0]
            drone.img.contents.instances[0].y = pos_to[1]

            # draw trail in img_trails
            if self.cfg.drone.enable_trail:
                self._draw_line(
                    self.img_trail,
                    (
                        pos_from[0] + drone.size[0] // 2,
                        pos_from[1] + drone.size[1] // 2,
                    ),
                    (
                        pos_to[0] + drone.size[0] // 2,
                        pos_to[1] + drone.size[1] // 2
                    ),
                    color=drone.color,
                )
            if STEP_IDX == 0:

                # drone has reached its destination
                if (
                    isinstance(dest, HubStation)
                    and dest.type == HubType.end_hub
                ):
                    drone.img.contents.enabled = False

                # update drone location and position
                if self.cfg.hub.enable_drone_count:
                    if isinstance(dest, HubStation):
                        self._update_drone_count(dest)
                    if isinstance(drone.location, HubStation):
                        self._update_drone_count(drone.location)

                drone.location = dest
                drone.pos = (end_pos[0], end_pos[1])

        if STEP_IDX == 0:
            SOLUTION_LINE.clear()
            DRONES_QUEUE.clear()
            STEP_IDX = STEPS
            return

        STEP_IDX -= 1

    def _animate_line(self) -> None:
        if DRONES_QUEUE:
            self._animate_drones()
            return

        # setting up queue for queue animation
        for move in SOLUTION_LINE:

            # going to a hub
            try:
                if to_hub := re.match(r"D(\d+)-(\w+)$", move):
                    drone_id = int(to_hub.group(1))
                    dest_name = to_hub.group(2)
                    drone = self.drones[drone_id]
                    dest = self.hubs[dest_name]
                    start_pos = (
                        drone.img.contents.instances[0].x,
                        drone.img.contents.instances[0].y,
                    )
                    end_pos = (
                        dest.pos[0] + dest.size[0] // 2 - drone.size[0] // 2,
                        dest.pos[1] + dest.size[1] // 2 - drone.size[1] // 2,
                    )

                # going to connection
                elif to_connection := re.match(r"D(\d+)-(\w+)-(\w+)$", move):
                    drone_id = int(to_connection.group(1))
                    hub_a_name = to_connection.group(2)
                    hub_b_name = to_connection.group(3)
                    drone = self.drones[drone_id]
                    hub_a = self.hubs[hub_a_name]
                    hub_b = self.hubs[hub_b_name]

                    dest = next(
                        conn
                        for conn in hub_a.connections
                        if (conn.hub_a == hub_b or conn.hub_b == hub_b)
                    )
                    # start and end should be the center of connection
                    start_pos = (
                        drone.img.contents.instances[0].x,
                        drone.img.contents.instances[0].y,
                    )
                    end_pos = (
                        dest.center[0] - drone.size[0] // 2,
                        dest.center[1] - drone.size[1] // 2,
                    )
                else:
                    continue
            except (KeyError, IndexError):
                sys.stderr.write(
                    f"\033[33m!!WARNING: \033[0mInvalid move '{move}'"
                    " in solution. Skipping.\n",
                )
                sys.stderr.flush()
                SOLUTION_LINE.remove(move)
                continue

            # remove drone from prev location
            drone.location.drones.remove(drone)

            # add drone to new location
            dest.drones.append(drone)

            # add randomness to the drone position if it's going to a hub
            randomamount = (
                self.cfg.drone.position_randomness
                if isinstance(dest, HubStation)
                else self.cfg.drone.position_randomness // 3
            )
            random_x = random.randint(-randomamount, randomamount)
            random_y = random.randint(-randomamount, randomamount)
            posx = end_pos[0] + random_x
            posy = end_pos[1] + random_y

            # append drone to the queue for animation
            DRONES_QUEUE.append((drone, start_pos, (posx, posy), dest))

    def _animate(self):
        global ANIMATING

        if SOLUTION_LINE:
            self._animate_line()

        else:
            try:
                line = self._solution_queue.popleft()
                for move in line.split():
                    SOLUTION_LINE.append(move.strip())
                self._animate_line()
                self._turns_count += 1
                self._draw_window_stats(color=0xFFFFFFAA)
            except IndexError:
                ANIMATING = False
                return

    def _loop_hook(self, param=None):
        global LAST_STEP_TIME

        if not ANIMATING:
            return

        now = time.perf_counter()
        if now - LAST_STEP_TIME < STEP_INTERVAL:
            return
        LAST_STEP_TIME = now

        self._animate()

    def _hook_func(self, keydata, param=None):
        global ANIMATING
        global STEPS
        global STEP_IDX

        # exit on ESC or Q
        if mlx.mlx_is_key_down(
            self.mlx_ptr, MLX_KEY_ESCAPE
            ) or mlx.mlx_is_key_down(
            self.mlx_ptr, MLX_KEY_Q
        ):
            mlx.mlx_close_window(self.mlx_ptr)

        # faster animation
        if mlx.mlx_is_key_down(self.mlx_ptr, MLX_KEY_RIGHT):
            if STEPS > 10:
                STEPS = int(STEPS / 1.5)
                STEP_IDX = int(STEP_IDX / 1.5)

        # slower animation
        if mlx.mlx_is_key_down(self.mlx_ptr, MLX_KEY_LEFT):
            if STEPS < 200:
                STEPS = int(STEPS * 1.5)
                STEP_IDX = int(STEP_IDX * 1.5)

        # toggle animation
        if mlx.mlx_is_key_down(self.mlx_ptr, MLX_KEY_SPACE):
            ANIMATING = not ANIMATING

    def run(
        self,
        solution: str | None = None,
    ) -> None:

        # background image
        mlx.mlx_image_to_window(self.mlx_ptr, self.img_bg, 0, 0)
        self.img_bg.contents.instances[0].z = BG_DEPTH
        self._fill_image(self.img_bg, self.cfg.appearance.background_color)

        # cenimatic black bars
        if self.cfg.appearance.cenimatic_bars:
            self._cenimatic_black_bars(self.img_bg, bar_thickness=50)

        # window title
        title = self.cfg.window.title.upper()
        centered_title_x = (
            self.cfg.window_size[0] // 2 - len(title) * GLYPH_SIZE
            )
        self._write_text(
            self.img_bg, title, (centered_title_x, 15),
            size=2, color=0xFFFFFF80
        )

        # help tip
        if self.cfg.other.enable_help_tip:
            help_tip = self.cfg.other.help_tip_text
            tip_pos = (
                self.cfg.window_size[0] // 2 - len(help_tip) * GLYPH_SIZE // 2,
                self.cfg.window_size[1] - 25,
            )
            self._write_text(
                self.img_bg, help_tip.upper(),
                tip_pos, size=1, color=0xFFFFFFAA
            )

        # draw hubs, name, stats and attach them to the window
        for hub in self.hubs.values():
            self._draw_entity(hub)
            self._attach_entity(hub)
            if self.cfg.hub.enable_name:
                self._draw_attach_hub_name(hub)
            if self.cfg.hub.enable_drone_count:
                self._draw_attach_drone_count(hub)

        # draw drones in start hub and attach them
        start_hub = next(
            (
                hub for hub in self.hubs.values()
                if hub.type == HubType.start_hub
            )
        )

        for drone in self.drones.values():
            drone.pos = (
                start_hub.pos[0]
                + start_hub.img.contents.width // 2
                - drone.size[0] // 2
                + random.randint(
                    -self.cfg.drone.position_randomness,
                    self.cfg.drone.position_randomness
                    ),
                start_hub.pos[1]
                + start_hub.img.contents.height // 2
                - drone.size[1] // 2
                + random.randint(
                    -self.cfg.drone.position_randomness,
                    self.cfg.drone.position_randomness
                    ),
            )
            self._draw_entity(drone)
            self._attach_entity(drone, drone.pos)

        # draw connections
        self._draw_connections()

        # animate solution if provided
        if solution:
            self._solution = solution
            self._solution_queue = deque(solution.splitlines())

            # draw stats image and attach it
            self._draw_window_stats(size=1, color=0xFFFFFFAA)
            mlx.mlx_image_to_window(self.mlx_ptr, self.img_stats, 10, 10)

        # hooking the key and loop functions
        self._hook_func_cb = ctypes.CFUNCTYPE(
            None, ctypes.c_void_p)(self._hook_func)

        self._loop_hook_cb = ctypes.CFUNCTYPE(
            None, ctypes.c_void_p)(self._loop_hook)

        mlx.mlx_key_hook(
            self.mlx_ptr, self._hook_func_cb, None
            )
        mlx.mlx_loop_hook(
            self.mlx_ptr, self._loop_hook_cb, None  # type: ignore
            )

        mlx.mlx_loop(self.mlx_ptr)
        mlx.mlx_terminate(self.mlx_ptr)
