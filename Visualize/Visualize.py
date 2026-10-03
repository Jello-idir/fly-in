from MLX.libmlx import (
    mlx,
    MLX_KEY_ESCAPE,
    MLX_KEY_Q,
    MLX_KEY_SPACE,
    MLX_KEY_RIGHT,
    MLX_KEY_LEFT,
    MLX_KEY_T,
    MLX_KEY_R,
    MLX_PRESS,
    MLX_REPEAT,
    mlx_key_data_t,
    mlx_keyfunc,
    mlx_image_t,
    mlx_t
)
from Common import (
    HubBase, DroneBase, HubMetadata, HubType, ZoneType, ColorType
)
from Config import Config, Shape
from MapParser import MapData
from collections import deque
import ctypes
import re
import random
import sys
import time


# depths
DEPTH_BG = 1
DEPTH_SIMULATION_TURNS = 8

# hub
DEPTH_HUB = 3
DEPTH_HUB_NAME = 4
DEPTH_HUB_STATS = 4
DEPTH_START_END_HUB = 7
MARGIN_HUB_STATS = 2

# drone depths
DEPTH_DRONE = 6
DEPTH_DRONE_TRAIL = 2

# Animation control variables
ANIMATING = False
SOLUTION_LINE: list[str] = []
DRONES_QUEUE: deque[
    tuple[
        'Drone',
        tuple[int, int],
        tuple[int, int],
        'HubStation | Connection'
        ]
    ] = deque()
STEPS = 80
STEP_IDX = STEPS
ANIMATION_FPS = 120
STEP_INTERVAL = 1 / ANIMATION_FPS
LAST_STEP_TIME = 0.0

# Speed variables
MAX_INDEX = 200
MIN_INDEX = 5


class Entity:
    """A colored sprite with grid coordinates and a screen position.

    Attributes:
        color: Packed RGBA sprite tint.
        shape: Visible sprite pixels and dimensions.
        coord: Grid coordinates.
        size: Sprite dimensions in pixels.
        pos: Top-left window position in pixels.
        img: Pointer to the native sprite image.
    """

    def __init__(
        self,
        mlx_ptr: mlx_t,
        cfg: Config,
        cord: tuple[int, int],
        color: int,
        shape: Shape,
    ):
        """Convert grid coordinates to pixels and allocate a sprite image.

        Args:
            mlx_ptr: Pointer to the native MLX window context.
            cfg: Display settings, sprite shapes, and font glyphs.
            cord: Grid coordinates before conversion to window pixels.
            color: Packed 32-bit RGBA drawing color.
            shape: Visible sprite pixels and dimensions.
        """
        self.color = color
        self.shape = shape
        self.coord = cord
        self.size = (shape.width, shape.height)
        self.pos = (
            int((cord[0]) * (cfg.cell + cfg.space) + cfg.paddin[0]),
            int((cord[1]) * (cfg.cell + cfg.space) + cfg.paddin[1]),
        )

        self.img = mlx.mlx_new_image(
            mlx_ptr,
            self.size[0],
            self.size[1],
        )


class Drone(Entity):
    """A rendered drone with an ID and current hub or connection.

    Attributes:
        id: Unique drone identifier.
        location: Current hub or connection during playback.
    """

    def __init__(
        self, mlx_ptr: mlx_t,
        cfg: Config,
        drone_base: DroneBase,
        current_hub: 'HubStation'
    ) -> None:
        """Assign the drone's starting location, color, and sprite.

        Args:
            mlx_ptr: Pointer to the native MLX window context.
            cfg: Display settings, sprite shapes, and font glyphs.
            drone_base: Drone identifier and initial grid coordinates.
            current_hub: Hub where the drone initially resides.
        """
        self.id: int = drone_base.id
        self.location: HubStation | Connection = current_hub
        color = list(ColorType)[(self.id - 1) % (len(list(ColorType)) - 1)]
        super().__init__(
            mlx_ptr, cfg,
            drone_base.coord,
            color, cfg.shapes.drone
            )


class HubStation(Entity):
    """A rendered hub with occupancy, labels, and incident connections.

    Attributes:
        name: Unique hub name.
        metadata: Zone, color, and capacity settings.
        type: Hub role.
        drones: Drones assigned to this hub.
        connections: Incident rendered connections.
        img_name: Native image for the name label.
        img_stat: Native image for the occupancy label.
    """

    def __init__(
        self,
        mlx_ptr: mlx_t,
        cfg: Config,
        hub_model: HubBase,
    ) -> None:
        """Create the hub sprite, label images, and occupancy lists.

        Args:
            mlx_ptr: Pointer to the native MLX window context.
            cfg: Display settings, sprite shapes, and font glyphs.
            hub_model: Validated hub definition to render.
        """
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
            cfg.font["A"].height,
        )
        self.img_stat = mlx.mlx_new_image(
            mlx_ptr,
            64,
            cfg.font["A"].height,
        )

    @staticmethod
    def get_shape_by_type(
        hub_type: HubType, metadata: HubMetadata, cfg: Config
    ) -> Shape:
        """Choose a sprite from the hub role, then its zone type.

        Args:
            hub_type: Start, intermediate, or destination role.
            metadata: Zone, color, and capacity settings for the hub.
            cfg: Display settings, sprite shapes, and font glyphs.

        Returns:
            Shape: Sprite for the hub role or, for ordinary hubs, its zone.
        """
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
    """A rendered link with capacity, endpoints, and drones in transit.

    Attributes:
        hub_a: First endpoint hub.
        hub_b: Second endpoint hub.
        capacity: Maximum simultaneous crossings.
        start_pos: Center of the first hub in window pixels.
        end_pos: Center of the second hub in window pixels.
        center: Midpoint of the connection in window pixels.
        drones: Drones in transit on this connection.
    """

    def __init__(self,
                 hub_a: HubStation,
                 hub_b: HubStation,
                 capacity: int
                 ):
        """Store the hubs and capacity, and calculate screen endpoints.

        Args:
            hub_a: First rendered endpoint hub.
            hub_b: Second rendered endpoint hub.
            capacity: Maximum simultaneous occupants or crossings.
        """
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
    """The MLX window, scene rendering, and drone animation controls.

    Attributes:
        connections: Rendered undirected links.
        mlx_ptr: Pointer to the native MLX window context.
        hubs: Rendered hubs indexed by name.
        drones: Rendered drones indexed by ID.
        cfg: Validated display settings and assets.
        is_running: Whether the native event loop is active.
        img_bg: Native background image.
        img_stats: Native turn-counter image.
        img_trail: Native drone-trail image.
    """

    def __init__(self, cfg: Config) -> None:
        """Create the window and drawing buffers; reject failed MLX setup.

        Args:
            cfg: Display settings, sprite shapes, and font glyphs.

        Raises:
            RuntimeError: The native MLX window cannot be initialized.
        """
        self.connections: list[Connection] = []
        self.mlx_ptr = mlx.mlx_init(
            cfg.window_size[0], cfg.window_size[1], b"Fly-in", True
        )
        if not self.mlx_ptr:
            raise RuntimeError("Failed to initialize the MLX window.")
        self.hubs: dict[str, HubStation] = {}
        self.drones: dict[int, Drone] = {}
        self.cfg: Config = cfg
        self._solution: str = ""
        self._solution_queue: deque[str] = deque()
        self._turns_count: int = 0
        self.is_running = False

        self.img_bg = mlx.mlx_new_image(
            self.mlx_ptr, self.cfg.window_size[0], self.cfg.window_size[1]
        )
        self.img_stats = mlx.mlx_new_image(self.mlx_ptr, 100, 8)
        self.img_trail = mlx.mlx_new_image(
            self.mlx_ptr, self.cfg.window_size[0], self.cfg.window_size[1]
        )

    @classmethod
    def from_map(cls, mapdata: MapData, cfg: Config) -> 'MlxWindow':
        """Create the scene and place every drone at the start hub.

        Args:
            mapdata: Validated map containing hubs, connections, and
                drones.
            cfg: Display settings, sprite shapes, and font glyphs.

        Returns:
            MlxWindow: Initialized window with hubs, drones, and
                connections.

        Raises:
            RuntimeError: The native MLX window cannot be initialized.
        """
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
    def _fill_image(
            img: mlx_image_t,
            color: int
            ) -> None:
        """Fill an RGBA image with one color, copying a row at a time.

        Args:
            img: Pointer to the MLX image whose pixel buffer is modified.
            color: Packed 32-bit RGBA drawing color.
        """
        width = img.contents.width
        height = img.contents.height
        pointer = ctypes.addressof(img.contents.pixels.contents)
        row = bytes((
            color >> 24 & 0xFF,
            color >> 16 & 0xFF,
            color >> 8 & 0xFF,
            color & 0xFF,
        )) * width
        row_bytes = width * 4
        for y in range(height):
            ctypes.memmove(pointer + row_bytes * y, row, row_bytes)

    def _draw_window_stats(
        self,
        size: int = 1,
        color: int = 0xFFFFFFFF
    ) -> None:
        """Redraw the current and total turn counts.

        Args:
            size: Integer scale factor for the pixel font.
            color: Packed 32-bit RGBA drawing color.
        """
        self._fill_image(self.img_stats, 0x00000000)
        total_turns_count = len(self._solution.splitlines())
        self._write_text(
            self.img_stats,
            f"Turn: {self._turns_count}/{total_turns_count}",
            (0, 0),
            size=size,
            color=color,
        )

    def _cenimatic_black_bars(
            self,
            img: mlx_image_t,
            bar_thickness: int = 50
            ) -> None:
        """Paint opaque black bars along the image's top and bottom.

        Args:
            img: Pointer to the MLX image whose pixel buffer is modified.
            bar_thickness: Height of each black bar in pixels.
        """
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
        img: mlx_image_t,
        text: str,
        pos: tuple[int, int],
        size: int = 1,
        color: int = 0xFFFFFFFF,
    ) -> None:
        """Draw scaled text with clipping and '#' for missing glyphs.

        Args:
            img: Pointer to the MLX image whose pixel buffer is modified.
            text: Text to render, including optional newlines.
            pos: Top-left drawing position in image pixels.
            size: Integer scale factor for the pixel font.
            color: Packed 32-bit RGBA drawing color.
        """
        is_trancated = False
        init_x, init_y = pos
        x, y = init_x, init_y
        buffer = img.contents.pixels
        img_w = img.contents.width
        img_h = img.contents.height
        for c in text:
            if c == "\n":
                y += 10 * size
                x = init_x
                continue
            glyph = self.cfg.font.get(c) or self.cfg.font["#"]
            for row_idx, row in enumerate(glyph.pixels):
                for pixel_idc, pixel in enumerate(row):
                    if pixel:
                        for sy in range(size):
                            for sx in range(size):
                                px = x + pixel_idc * size + sx
                                py = y + row_idx * size + sy
                                if 0 <= px < img_w and 0 <= py < img_h:
                                    idx = (py * img_w + px) * 4
                                    buffer[idx] = color >> 24 & 0xFF
                                    buffer[idx + 1] = color >> 16 & 0xFF
                                    buffer[idx + 2] = color >> 8 & 0xFF
                                    buffer[idx + 3] = color & 0xFF
                                elif not is_trancated:
                                    sys.stderr.write(
                                        "Warning: Text trancated! "
                                        "to solve it, "
                                        "increase minimum window width "
                                        "in config file.\n"
                                    )
                                    is_trancated = True
            x += glyph.width * size

    def _draw_entity(self, entity: Entity) -> None:
        """Paint a sprite with its entity color or rainbow bands.

        Args:
            entity: Sprite entity to draw or attach to the window.
        """
        hub_color = entity.color
        if (isinstance(entity, HubStation) and
                entity.color == ColorType.rainbow):
            color_list = [
                ColorType.red,
                ColorType.orange,
                ColorType.yellow,
                ColorType.green,
                ColorType.teal,
                ColorType.blue,
                ColorType.indigo,
                ColorType.violet,
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
        self,
        entity: Entity,
        pos: tuple[int, int] | None = None
    ) -> None:
        """Place a sprite in the window and assign its drawing depth.

        Args:
            entity: Sprite entity to draw or attach to the window.
            pos: Top-left window position in pixels; None uses entity.pos.
        """
        if pos is None:
            pos = entity.pos
        mlx.mlx_image_to_window(self.mlx_ptr, entity.img, pos[0], pos[1])
        if isinstance(entity, HubStation):
            depth = DEPTH_HUB
            if entity.type in (HubType.start_hub, HubType.end_hub):
                depth = DEPTH_START_END_HUB + len(self.drones)
            entity.img.contents.instances[0].z = depth
        elif isinstance(entity, Drone):
            entity.img.contents.instances[0].z = DEPTH_DRONE + entity.id

    def _draw_attach_hub_name(
            self, hub: HubStation,
            uppercase: bool = True
            ) -> None:
        """Draw and place a shortened hub label above its sprite.

        Args:
            hub: Hub whose label or occupancy is rendered.
            uppercase: Whether to use uppercase instead of title case.
        """
        name = hub.name
        if len(name) > 10:
            name = name[:8] + ".."

        name = name.upper() if uppercase else name.title()

        self._write_text(
            hub.img_name,
            name,
            (0, 0),
            color=self.cfg.hub.name_color
            )
        mlx.mlx_image_to_window(
            self.mlx_ptr, hub.img_name,
            hub.pos[0], hub.pos[1] - 10
        )
        hub.img_name.contents.instances[0].z = DEPTH_HUB_NAME

    def _draw_hub_stats(
            self, hub: HubStation,
            uppercase: bool = False
            ) -> None:
        """Draw the occupancy/capacity label, colored by fullness.

        Args:
            hub: Hub whose label or occupancy is rendered.
            uppercase: Whether to use uppercase instead of title case.
        """
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

    def _draw_attach_hub_stats(
        self, hub: HubStation, uppercase: bool = False
    ) -> None:
        """Draw and place the occupancy label below the hub.

        Args:
            hub: Hub whose label or occupancy is rendered.
            uppercase: Whether to use uppercase instead of title case.
        """
        self._draw_hub_stats(hub, uppercase=uppercase)
        mlx.mlx_image_to_window(
            self.mlx_ptr,
            hub.img_stat,
            hub.pos[0],
            hub.pos[1] + hub.size[1] + MARGIN_HUB_STATS
        )
        hub.img_stat.contents.instances[0].z = DEPTH_HUB_STATS

    def _update_hub_stats(
            self, hub: HubStation, is_upper: bool = False
            ) -> None:
        """Clear and redraw a hub's occupancy label.

        Args:
            hub: Hub whose label or occupancy is rendered.
            is_upper: Whether to render the occupancy text in uppercase.
        """
        self._fill_image(hub.img_stat, 0x00000000)
        self._draw_hub_stats(hub, uppercase=is_upper)

    def _draw_line(
        self,
        img: mlx_image_t,
        start: tuple[int, int],
        end: tuple[int, int],
        color: int = 0xFFFFFFAA,
        thickness: int = 0,
    ) -> None:
        """Draw a thick RGBA line clipped to the image bounds.

        Args:
            img: Pointer to the MLX image whose pixel buffer is modified.
            start: Starting point in image pixels.
            end: Ending point in image pixels.
            color: Packed 32-bit RGBA drawing color.
            thickness: Brush radius in pixels; zero draws a one-pixel-wide
                line.
        """
        x1, y1 = start
        x2, y2 = end

        dx = x2 - x1
        dy = y2 - y1
        steps = max(abs(dx), abs(dy))
        if steps == 0:
            return
        x_inc = dx / steps
        y_inc = dy / steps

        width = img.contents.width
        height = img.contents.height
        pixels = ctypes.addressof(img.contents.pixels.contents)
        brush_row = bytes((
            color >> 24 & 0xFF,
            color >> 16 & 0xFF,
            color >> 8 & 0xFF,
            color & 0xFF,
        )) * (2 * thickness + 1)
        x, y = float(x1), float(y1)
        for _ in range(steps):
            left = max(0, int(x) - thickness)
            right = min(width, int(x) + thickness + 1)
            if left < right:
                for py in range(max(0, int(y) - thickness),
                                min(height, int(y) + thickness + 1)):
                    ctypes.memmove(
                        pixels + (py * width + left) * 4,
                        brush_row,
                        (right - left) * 4,
                    )

            x += x_inc
            y += y_inc

    def _draw_line_with_stroke(
        self,
        img: mlx_image_t,
        start: tuple[int, int],
        end: tuple[int, int],
        color: int = 0xFFFFFFAA,
        thickness: int = 0,
    ) -> None:
        """Draw a connection line over a wider outline.

        Args:
            img: Pointer to the MLX image whose pixel buffer is modified.
            start: Starting point in image pixels.
            end: Ending point in image pixels.
            color: Packed 32-bit RGBA drawing color.
            thickness: Brush radius in pixels; zero draws a one-pixel-wide
                line.
        """
        stroke_color = self.cfg.connection.stroke_color
        self._draw_line(
            img, start, end, color=stroke_color, thickness=thickness + 1)
        self._draw_line(
            img, start, end, color=color, thickness=thickness)

    def _draw_connections(
            self, color: int = 0xFFFFFF50) -> None:
        """Draw all connections and their capacity labels.

        Args:
            color: Packed 32-bit RGBA drawing color.
        """
        for conn in self.connections:
            hub_a = conn.hub_a
            hub_b = conn.hub_b

            # calculating center points of hubs
            x1 = hub_a.pos[0] + hub_a.size[0] // 2
            y1 = hub_a.pos[1] + hub_a.size[1] // 2
            x2 = hub_b.pos[0] + hub_b.size[0] // 2
            y2 = hub_b.pos[1] + hub_b.size[1] // 2

            # thickness based on capacity
            self._draw_line_with_stroke(
                self.img_bg,
                (x1, y1),
                (x2, y2),
                color=color,
                thickness=min(conn.capacity, 8) * 3,
            )

            # calculating position for capacity text
            capacity_text = str(conn.capacity)
            text_width = len(capacity_text) * self.cfg.font["A"].width
            text_x = int((x1 + x2) / 2 - text_width / 2 + 2)
            text_y = int((y1 + y2) / 2 - 3)

            # write capacity
            self._write_text(
                self.img_bg,
                capacity_text,
                (text_x, text_y),
                color=self.cfg.connection.text_color
                )

    def _reset_simulation(self) -> None:
        """Clear playback and occupancy; return drones to the start."""
        self._solution_queue = deque(self._solution.splitlines())

        # clear animating variable
        global ANIMATING
        global LAST_STEP_TIME
        global STEP_IDX

        ANIMATING = False
        SOLUTION_LINE.clear()
        DRONES_QUEUE.clear()
        LAST_STEP_TIME = 0
        STEP_IDX = STEPS

        for connection in self.connections:
            connection.drones.clear()

        start_hub = next(
            hub for hub in self.hubs.values()
            if hub.type == HubType.start_hub
        )

        for hub in self.hubs.values():
            hub.drones.clear()
            self._update_hub_stats(hub, is_upper=True)

        for drone in self.drones.values():
            drone.location = start_hub
            start_hub.drones.append(drone)
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
            drone.img.contents.instances[0].x = drone.pos[0]
            drone.img.contents.instances[0].y = drone.pos[1]
            drone.img.contents.enabled = True

        self._update_hub_stats(start_hub, is_upper=True)
        self._turns_count = 0
        self._draw_window_stats()

    def _animate_drones(self) -> None:
        """Advance queued moves one frame and finalize completed arrivals."""
        global STEP_IDX

        for drone, start_pos, end_pos, dest in DRONES_QUEUE:

            pos_from = (
                drone.img.contents.instances[0].x,
                drone.img.contents.instances[0].y,
            )

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

            drone.img.contents.instances[0].y = pos_to[1]
            drone.img.contents.instances[0].x = pos_to[0]

            # draw trail in img_trails
            color = drone.color & 0xFFFFFF00 | int(
                self.cfg.drone.trail_opacity * 255)
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
                color=color
            )
            if STEP_IDX == 0:

                # drone has reached end
                if (
                    isinstance(dest, HubStation)
                    and dest.type == HubType.end_hub
                ):
                    drone.img.contents.enabled = False

                # update drone location and position
                drone.location = dest
                drone.pos = (end_pos[0], end_pos[1])

        if STEP_IDX == 0:
            # update hub stats
            for hub in self.hubs.values():
                self._update_hub_stats(hub, is_upper=True)
            SOLUTION_LINE.clear()
            DRONES_QUEUE.clear()
            STEP_IDX = STEPS
            return

        STEP_IDX -= 1

    def _animate_line(self) -> None:
        """Queue the current turn's moves or advance their animation."""
        if DRONES_QUEUE:
            self._animate_drones()
            return

        # setting up queue for queue animation
        for move in list(SOLUTION_LINE):
            dest: HubStation | Connection | None

            # going to a hub
            try:
                if to_hub := re.fullmatch(r"D(\d+)-([^\s-]+)", move):
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
                elif to_connection := re.fullmatch(
                    r"D(\d+)-([^\s-]+)-([^\s-]+)", move
                ):
                    drone_id = int(to_connection.group(1))
                    hub_a_name = to_connection.group(2)
                    hub_b_name = to_connection.group(3)
                    drone = self.drones[drone_id]
                    hub_a = self.hubs[hub_a_name]
                    hub_b = self.hubs[hub_b_name]

                    dest = next(
                        (
                            conn for conn in hub_a.connections
                            if (conn.hub_a == hub_b or conn.hub_b == hub_b)
                            ),
                        None
                    )
                    if dest is None:
                        sys.stderr.write(
                            f"\033[33m!!WARNING: \033[0mNo connection between "
                            f"'{hub_a_name}' and '{hub_b_name}'. Skipping.\n"
                            )
                        continue
                    if isinstance(dest, Connection):
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
            try:
                drone.location.drones.remove(drone)
            except ValueError:
                sys.stderr.write(
                    f"\033[33m!!WARNING: \033[0mDrone {drone.id} "
                    f"not found in location drones. Skipping.\n"
                )

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

    def _animate(self) -> None:
        """Advance playback, load the next turn, or reset at the end."""
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
                self._draw_window_stats()
            except IndexError:
                self._solution_queue = deque(self._solution.splitlines())
                self._reset_simulation()
                ANIMATING = False

    def _loop_hook(
            self, param: ctypes.c_void_p = None  # type: ignore
            ) -> None:
        """Advance animation when playback is active and a frame is due.

        Args:
            param: Unused user-data pointer supplied by the MLX callback.
        """
        global LAST_STEP_TIME

        if not ANIMATING:
            return

        now = time.perf_counter()
        if now - LAST_STEP_TIME < STEP_INTERVAL:
            return
        LAST_STEP_TIME = now

        self._animate()

    def _hook_func(
            self,
            keydata: mlx_key_data_t,
            param: ctypes.c_void_p = None  # type: ignore
            ) -> None:
        """Handle controls; repeat only speed changes and exit requests.

        Args:
            keydata: Keyboard event containing the key and press/repeat
                action.
            param: Unused user-data pointer supplied by the MLX callback.
        """
        global ANIMATING
        global STEPS
        global STEP_IDX

        if keydata.action not in (MLX_PRESS, MLX_REPEAT):
            return

        # exit on ESC or Q
        if keydata.key in (MLX_KEY_ESCAPE, MLX_KEY_Q):
            mlx.mlx_close_window(self.mlx_ptr)
            return

        new_steps = STEPS
        # faster animation
        if keydata.key == MLX_KEY_RIGHT:
            new_steps = max(MIN_INDEX, int(STEPS / 1.5))

        # slower animation
        if keydata.key == MLX_KEY_LEFT:
            new_steps = min(MAX_INDEX, int(STEPS * 1.5))

        if new_steps != STEPS:
            STEP_IDX = round(STEP_IDX * new_steps / STEPS)
            STEPS = new_steps

        if keydata.action != MLX_PRESS:
            return

        # toggle animation
        if keydata.key == MLX_KEY_SPACE:
            ANIMATING = not ANIMATING

        # toggle drone trail
        if keydata.key == MLX_KEY_T:
            self.cfg.drone.enable_trail = not self.cfg.drone.enable_trail
            self.img_trail.contents.enabled = self.cfg.drone.enable_trail

        # restart animation
        if keydata.key == MLX_KEY_R:
            self._reset_simulation()
            self._turns_count = 0
            self._fill_image(self.img_trail, 0x00000000)

    def run(
        self,
        solution: str,
    ) -> None:
        """Render the scene, play the supplied turns, and clean up the loop.

        Args:
            solution: Turn-by-turn animation text, including stationary
                drone positions.
        """
        # background image
        mlx.mlx_image_to_window(self.mlx_ptr, self.img_bg, 0, 0)
        self.img_bg.contents.instances[0].z = DEPTH_BG
        self._fill_image(self.img_bg, self.cfg.appearance.background_color)

        # trail image
        mlx.mlx_image_to_window(self.mlx_ptr, self.img_trail, 0, 0)
        self.img_trail.contents.instances[0].z = DEPTH_DRONE_TRAIL

        # drone trails image
        if not self.cfg.drone.enable_trail:
            self.img_trail.contents.enabled = False

        # cenimatic black bars
        if self.cfg.appearance.cenimatic_bars:
            self._cenimatic_black_bars(self.img_bg, bar_thickness=50)

        # window title
        self._draw_window_title()

        # help tip
        if self.cfg.other.enable_help_tip:
            self._draw_help_tip()

        # draw hubs, name, stats and attach them to the window
        self._init_hubs()

        # draw drones in start hub and attach them
        self._init_drones()

        # draw connections
        self._draw_connections(color=self.cfg.connection.color)

        # animate solution if provided
        self._solution = solution
        self._solution_queue = deque(solution.splitlines())
        self._turns_count = 0

        # draw stats image and attach it
        self._draw_window_stats()
        mlx.mlx_image_to_window(self.mlx_ptr, self.img_stats, 10, 10)
        self.img_stats.contents.instances[0].z = DEPTH_SIMULATION_TURNS

        # hooking the key and loop functions
        self._hook_func_cb = mlx_keyfunc(self._hook_func)

        self._loop_hook_cb = ctypes.CFUNCTYPE(
            None, ctypes.c_void_p)(self._loop_hook)

        mlx.mlx_key_hook(
            self.mlx_ptr, self._hook_func_cb, None
            )
        mlx.mlx_loop_hook(
            self.mlx_ptr, self._loop_hook_cb, None  # type: ignore
            )

        self.is_running = True
        try:
            mlx.mlx_loop(self.mlx_ptr)
        finally:
            self.is_running = False
            mlx.mlx_terminate(self.mlx_ptr)

    def _draw_help_tip(self) -> None:
        """Draw the configured help text near the bottom of the window."""
        help_tip = self.cfg.other.help_tip_text
        tip_pos = (
            self.cfg.window_size[0] // 2 - len(help_tip)
            * self.cfg.font["A"].width // 2,
            self.cfg.window_size[1] - 25,
        )
        self._write_text(
            self.img_bg, help_tip.upper(),
            tip_pos, size=1, color=0xFFFFFFAA
        )

    def _draw_window_title(self) -> None:
        """Draw the configured title at the top of the scene."""
        title = self.cfg.window.title
        title_pos = (
            self.cfg.window_size[0] // 2 - len(title)
            * self.cfg.font["A"].width // 2,
            15,
        )
        self._write_text(
            self.img_bg, title.upper(),
            title_pos, size=1, color=0xFFFFFFAA
        )

    def _init_hubs(self) -> None:
        """Draw and attach hubs with their enabled labels and counters."""
        for hub in self.hubs.values():
            self._draw_entity(hub)
            self._attach_entity(hub)
            if self.cfg.hub.enable_name:
                self._draw_attach_hub_name(hub)
            if self.cfg.hub.enable_drone_count:
                self._draw_attach_hub_stats(hub)

    def _init_drones(self) -> None:
        """Draw and attach drones around the center of the start hub."""
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
