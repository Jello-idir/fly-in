from Common import Shapes
from pydantic import BaseModel, Field
from MapParser import MapData
from PixelFont import load_font, Glyph
import tomllib


class WindowSection(BaseModel):
    title: str = "FLY-OUT"
    min_width: int = Field(default=800, ge=0)

class AppearanceSection(BaseModel):
    background_color: int = 0x00000080
    cenimatic_bars: bool = True

class DroneSection(BaseModel):
    enable_trail: bool = True
    position_randomness: int = Field(default=5, ge=0, le=32)

class HubSection(BaseModel):
    enable_name: bool = True
    enable_drone_count: bool = True

class SizingSection(BaseModel):
    spacing: int = Field(default=32, ge=0)
    padding: tuple[int, int] = (50, 80)

class OtherSection(BaseModel):
    enable_help_tip: bool = True
    help_tip_text: str = ""


class RenderConfig(BaseModel):
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
    shapes: type

    @classmethod
    def from_mapdata(cls, mapdata: MapData, config_path: str = "config.toml") -> RenderConfig:
        with open(config_path, "rb") as f:
            # load toml as dict
            cfg = tomllib.load(f)

            min_x, max_x, min_y, max_y = mapdata.bounding_box
            map_width  = max_x - min_x + 1
            map_height = max_y - min_y + 1

            shapes   = Shapes
            hub_size = max(shapes.hub._size())
            spacing  = cfg["sizing"]["spacing"]

            pad_x = max(0,  cfg["sizing"]["padding"][0])
            pad_y = max(80, cfg["sizing"]["padding"][1])

            abs_width  = map_width  * hub_size + spacing * (map_width  - 1) + pad_x * 2
            abs_height = map_height * hub_size + spacing * (map_height - 1) + pad_y * 2

            if abs_width < cfg["window"]["min_width"]:
                abs_width = cfg["window"]["min_width"]
                pad_x = (abs_width - (map_width * hub_size + spacing * (map_width - 1))) // 2

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
