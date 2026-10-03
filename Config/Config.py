from pydantic import BaseModel, Field
from MapParser import MapData
from PixelFont import Font, Glyph
from PIL import Image
from dataclasses import dataclass
import tomli


SPACEING_DEFAULT = 32
PADDING_X_DEFAULT = 25
PADDING_Y_DEFAULT = 50
MINIMUM_WINDOW_WIDTH_DEFAULT = 500

# themes prefix
THEMES_PREFIX = "assets/themes/"
ASSETS_LIST = [
    "drone",
    "hub",
    "hub_restricted",
    "hub_priority",
    "hub_blocked",
    "hub_start",
    "hub_end",
]


@dataclass
class Shape:
    """Visible PNG pixels as (x, y, RGBA) tuples and their extent.

    Attributes:
        pixels: Visible pixels represented as (x, y, packed RGBA) tuples.
        width: Width in pixels.
        height: Height in pixels.
    """

    pixels: set[tuple[int, int, int]]
    width: int
    height: int

    @classmethod
    def from_image(cls, path: str) -> "Shape":
        """Load visible pixels and their extent from a PNG file.

        Args:
            path: Path to the source PNG image.

        Returns:
            Shape: Visible pixels and bounds measured from the image
                origin.

        Raises:
            FileNotFoundError: The sprite file does not exist.
            ValueError: The file has no PNG signature or no visible pixels.
            RuntimeError: Pillow cannot decode the image.
        """

        try:
            with open(path, "rb") as f:
                if not f.read(8).startswith(b"\x89PNG\r\n\x1a\n"):
                    raise ValueError(f"File is not a valid PNG: {path}")
                pass
        except FileNotFoundError:
            raise FileNotFoundError(f"Asset not found: {path}")

        try:
            img = Image.open(path).convert("RGBA")
        except Exception as e:
            raise RuntimeError(f"Failed to load image {path}: {e}")

        pixels = set()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = img.getpixel((x, y))  # type: ignore
                if a > 0:
                    color = (r << 24) | (g << 16) | (b << 8) | a
                    pixels.add((x, y, color))

        img.close()

        return cls(
            pixels=pixels,
            width=max(p[0] for p in pixels) + 1,
            height=max(p[1] for p in pixels) + 1,
        )


@dataclass(frozen=True)
class Shapes:
    """Sprites for drones and every hub type.

    Attributes:
        drone: Drone sprite.
        hub: Ordinary hub sprite.
        hub_restricted: Restricted-zone sprite.
        hub_priority: Priority-zone sprite.
        hub_blocked: Blocked-zone sprite.
        hub_start: Starting-hub sprite.
        hub_end: Destination-hub sprite.
    """

    drone: Shape
    hub: Shape
    hub_restricted: Shape
    hub_priority: Shape
    hub_blocked: Shape
    hub_start: Shape
    hub_end: Shape

    @classmethod
    def from_assets(cls, assets: "AssetsSection") -> "Shapes":
        """Load all sprites from the configured asset paths.

        Args:
            assets: Paths to every required PNG sprite.

        Returns:
            Shapes: Loaded drone and hub sprites.

        Raises:
            OSError: A sprite file cannot be read.
            ValueError: A sprite is not a PNG or has no visible pixels.
            RuntimeError: A sprite cannot be decoded.
        """

        return cls(
            drone=Shape.from_image(assets.drone),
            hub=Shape.from_image(assets.hub),
            hub_restricted=Shape.from_image(assets.hub_restricted),
            hub_priority=Shape.from_image(assets.hub_priority),
            hub_blocked=Shape.from_image(assets.hub_blocked),
            hub_start=Shape.from_image(assets.hub_start),
            hub_end=Shape.from_image(assets.hub_end)
        )


class WindowSection(BaseModel):
    """Window title and minimum width.

    Attributes:
        title: Displayed window title.
        min_width: Minimum window width in pixels.
    """

    title: str = "FLY-OUT"
    min_width: int = Field(ge=0)


class AppearanceSection(BaseModel):
    """Background color and cinematic-bar visibility.

    Attributes:
        background_color: Packed RGBA background color.
        cenimatic_bars: Whether to draw top and bottom black bars.
    """

    background_color: int = 0x00000080
    cenimatic_bars: bool = True


class AssetsSection(BaseModel):
    """PNG paths for drone and hub sprites.

    Attributes:
        drone: Path to the drone PNG sprite.
        hub: Path to the hub PNG sprite.
        hub_restricted: Path to the hub restricted PNG sprite.
        hub_priority: Path to the hub priority PNG sprite.
        hub_blocked: Path to the hub blocked PNG sprite.
        hub_start: Path to the hub start PNG sprite.
        hub_end: Path to the hub end PNG sprite.
    """

    drone: str
    hub: str
    hub_restricted: str
    hub_priority: str
    hub_blocked: str
    hub_start: str
    hub_end: str


class DroneSection(BaseModel):
    """Trail visibility, opacity, and position randomness.

    Attributes:
        enable_trail: Whether to display drone trails.
        trail_opacity: Trail alpha multiplier between zero and one.
        position_randomness: Maximum random position offset in pixels, from
            zero to 32.
    """

    enable_trail: bool = True
    trail_opacity: float = Field(default=1, ge=0, le=1)
    position_randomness: int = Field(default=5, ge=0, le=32)


class HubSection(BaseModel):
    """Hub label colors and label/count visibility.

    Attributes:
        enable_name: Whether to display hub names.
        name_color: Packed RGBA hub-label color.
        enable_drone_count: Whether to show hub occupancy labels.
    """

    enable_name: bool = True
    name_color: int = 0xFFFFFFFF
    enable_drone_count: bool = True


class ConnectionSection(BaseModel):
    """Connection fill, outline, and capacity-label colors.

    Attributes:
        color: Packed RGBA color or special rainbow marker.
        text_color: Packed RGBA capacity-label color.
        stroke_color: Packed RGBA connection-outline color.
    """

    color: int = 0xFFFFFF50
    text_color: int = 0xFFFFFFFF
    stroke_color: int = 0xFFFFFFFF


class SizingSection(BaseModel):
    """Grid spacing and minimum window padding.

    Attributes:
        spacing: Gap between grid cells in pixels.
        padding_x: Horizontal window padding in pixels, at least 25.
        padding_y: Vertical window padding in pixels, at least 50.
    """

    spacing: int = Field(ge=0)
    padding_x: int = Field(ge=PADDING_X_DEFAULT)
    padding_y: int = Field(ge=PADDING_Y_DEFAULT)


class OtherSection(BaseModel):
    """Help-tip text and visibility.

    Attributes:
        enable_help_tip: Whether to display the help text.
        help_tip_text: Text displayed near the bottom of the window.
    """

    enable_help_tip: bool = True
    help_tip_text: str = ""


class Config(BaseModel):
    """Validated display settings, map dimensions, fonts, and sprites.

    Attributes:
        window: Window title and minimum size settings.
        appearance: Background and cinematic-bar settings.
        drone: Drone trail and position settings.
        hub: Hub label and occupancy-display settings.
        connection: Connection colors and outline settings.
        sizing: Grid spacing and padding settings.
        other: Help-tip settings.
        window_size: Computed window width and height in pixels.
        paddin: Computed horizontal and vertical padding in pixels.
        cell: Square grid-cell size in pixels.
        space: Gap between grid cells in pixels.
        font: Pixel glyphs indexed by character.
        shapes: Loaded sprite collection.
    """

    # from config file — nested, same shape as AppConfig
    window: WindowSection
    appearance: AppearanceSection
    drone: DroneSection
    hub: HubSection
    connection: ConnectionSection
    sizing: SizingSection
    other: OtherSection

    # from map + config file
    window_size: tuple[int, int]
    paddin: tuple[int, int]
    cell: int
    space: int

    # runtime-loaded
    font: dict[str, Glyph]
    shapes: Shapes

    @classmethod
    def from_mapdata(
        cls, mapdata: MapData, config_path: str = "config.toml"
    ) -> 'Config':
        """Load TOML settings and assets, then size the window for the map.

        Args:
            mapdata: Validated map containing hubs, connections, and
                drones.
            config_path: Path to the TOML display configuration.

        Returns:
            Config: Validated settings with computed dimensions and loaded
                assets.

        Raises:
            OSError: A configuration, sprite, or font file cannot be read.
            ValueError: TOML, settings, or image data are invalid.
            KeyError: A required configuration section is missing.
            RuntimeError: A sprite cannot be decoded.
        """
        with open(config_path, "rb") as f:
            # load toml as dict
            cfg = tomli.load(f)

            size_x, size_y = mapdata.size
            map_width = size_x
            map_height = size_y

            min_width = cfg.get("window", {}).get(
                "min_width", MINIMUM_WINDOW_WIDTH_DEFAULT
            )

            # load assets based on theme
            theme = cfg.get("appearance", {}).get("theme", "default")
            assets: dict[str, str] = {}
            for asset in ASSETS_LIST:
                assets[asset] = THEMES_PREFIX + theme + "/" + asset + ".png"

            # adding prefix
            shapes = Shapes.from_assets(AssetsSection(**assets))

            # calculate window size, hub size, spacing, and padding
            hub_size = max(shapes.hub.width, shapes.hub.height)
            spacing = cfg.get("sizing", {}).get("spacing", SPACEING_DEFAULT)

            pad_x = cfg.get("sizing", {}).get("padding_x", PADDING_X_DEFAULT)
            pad_y = cfg.get("sizing", {}).get("padding_y", PADDING_Y_DEFAULT)

            abs_width = (
                map_width * hub_size + spacing * (map_width - 1) + pad_x * 2
                )
            abs_height = (
                map_height * hub_size + spacing * (map_height - 1) + pad_y * 2
                )

            if abs_width < min_width:
                abs_width = min_width
                pad_x = (
                    abs_width - (
                        map_width * hub_size + spacing * (map_width - 1)
                        )
                ) // 2

            cfg["sizing"]["padding_x"] = pad_x
            cfg["sizing"]["padding_y"] = pad_y

            font = Font._font_loader(
                "assets/font/uppercase.png",
                "assets/font/lowercase.png",
                "assets/font/digits.png",
            ).glyphs

        return cls(
            window=cfg["window"],
            appearance=cfg["appearance"],
            drone=cfg["drone"],
            hub=cfg["hub"],
            connection=cfg["connection"],
            sizing=cfg["sizing"],
            other=cfg["other"],
            window_size=(abs_width, abs_height),
            paddin=(pad_x, pad_y),
            cell=hub_size,
            space=spacing,
            font=font,
            shapes=shapes,
        )
