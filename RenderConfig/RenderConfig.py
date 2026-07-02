from pydantic import BaseModel, Field
from MapParser import MapData
from PixelFont import load_font, Glyph
import tomllib
from PIL import Image
from enum import Enum


from dataclasses import dataclass
from PIL import Image


@dataclass
class Shape:
    """Pixel data loaded from a PNG asset.

    Attributes:
        pixels: Set of (x, y, color) tuples for every non-transparent pixel.
        width:  Bounding box width, precomputed at load time.
        height: Bounding box height, precomputed at load time.
    """
    pixels: set[tuple[int, int, int]]
    width: int
    height: int

    @classmethod
    def from_image(cls, path: str) -> "Shape":
        """Loads a PNG and converts non-transparent pixels into (x, y, color) tuples.

        Args:
            path: Path to the PNG asset.

        Returns:
            A Shape with pixels, width, and height populated.
        """
        img = Image.open(path).convert("RGBA")
        pixels = set()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = img.getpixel((x, y))  # type: ignore
                if a > 0:
                    color = (r << 24) | (g << 16) | (b << 8) | a
                    pixels.add((x, y, color))

        return cls(
            pixels=pixels,
            width=max(p[0] for p in pixels) + 1,
            height=max(p[1] for p in pixels) + 1,
        )


@dataclass(frozen=True)
class Shapes:
    """All pixel shapes used for rendering hubs and drones.

    Loaded from PNG assets at runtime via `from_assets`.
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
        """Loads all shapes from the paths defined in AssetsSection.

        Args:
            assets: An AssetsSection containing image paths.

        Returns:
            A Shapes instance with every shape loaded.
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

SPACEING_DEFAULT = 32
PADDING_X_DEFAULT = 25
PADDING_Y_DEFAULT = 50
MINIMUM_WINDOW_WIDTH_DEFAULT = 500


class WindowSection(BaseModel):
    """ window settings basemodel
    """
    title: str = "FLY-OUT"
    min_width: int = Field(ge=0)

class AppearanceSection(BaseModel):
    """ appearance settings basemodel
    """
    background_color: int = 0x00000080
    cenimatic_bars: bool = True

class AssetsSection(BaseModel):
    """ assets settings basemodel
    """
    drone: str
    hub: str
    hub_restricted: str
    hub_priority: str
    hub_blocked: str
    hub_start: str
    hub_end: str

class DroneSection(BaseModel):
    """ drone settings basemodel
    """
    enable_trail: bool = True
    position_randomness: int = Field(default=5, ge=0, le=32)


class HubSection(BaseModel):
    """ hub settings basemodel
    """
    enable_name: bool = True
    enable_drone_count: bool = True


class SizingSection(BaseModel):
    """ sizing settings basemodel
    """
    spacing: int = Field(ge=0)
    padding_x: int = Field(ge=PADDING_X_DEFAULT)
    padding_y: int = Field(ge=PADDING_Y_DEFAULT)


class OtherSection(BaseModel):
    """ other settings basemodel
    """
    enable_help_tip: bool = True
    help_tip_text: str = ""


class RenderConfig(BaseModel):
    """ render config basemodel
    """
    # from config file — nested, same shape as AppConfig
    window: WindowSection
    appearance: AppearanceSection
    drone: DroneSection
    hub: HubSection
    sizing: SizingSection
    other: OtherSection

    # from map + config file
    window_size: tuple[int, int]
    min_coord: tuple[int, int]
    paddin: tuple[int, int]
    cell: int
    space: int

    # runtime-loaded
    font: dict[str, Glyph]
    shapes: Shapes

    @classmethod
    def from_mapdata(
        cls, mapdata: MapData, config_path: str = "config.toml"
    ) -> RenderConfig:
        """ class method to create a RenderConfig from a MapData

        Args:
            mapdata (MapData): _mapdata object for calculating window size
            config_path (str, optional): path to config, Default "config.toml".

        Returns:
            RenderConfig: _renderconfig object
        """
        with open(config_path, "rb") as f:
            # load toml as dict
            cfg = tomllib.load(f)

            min_x, max_x, min_y, max_y = mapdata.bounding_box
            map_width = max_x - min_x + 1
            map_height = max_y - min_y + 1

            min_width = cfg.get("window", {}).get(
                "min_width", MINIMUM_WINDOW_WIDTH_DEFAULT
            )

            # load assets based on theme
            theme = cfg.get("appearance", {}).get("theme", "default")
            assets = {
                "drone": f"assets/{theme}/drone.png",
                "hub": f"assets/{theme}/hub.png",
                "hub_restricted": f"assets/{theme}/hub_restricted.png",
                "hub_priority": f"assets/{theme}/hub_priority.png",
                "hub_blocked": f"assets/{theme}/hub_blocked.png",
                "hub_start": f"assets/{theme}/hub_start.png",
                "hub_end": f"assets/{theme}/hub_end.png",
            }
            shapes = Shapes.from_assets(AssetsSection(**assets))

            # calculate window size based on map size, hub size, spacing, and padding
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

        return cls(
            window=cfg["window"],
            appearance=cfg["appearance"],
            drone=cfg["drone"],
            hub=cfg["hub"],
            sizing=cfg["sizing"],
            other=cfg["other"],
            window_size=(abs_width, abs_height),
            min_coord=(min_x, min_y),
            paddin=(pad_x, pad_y),
            cell=hub_size,
            space=spacing,
            font=load_font(),
            shapes=shapes,
        )
