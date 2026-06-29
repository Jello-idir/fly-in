from Common import Shapes
import tomllib
from pydantic import BaseModel, Field, ConfigDict
from typing import Any
from MapParser import MapData
from PixelFont import load_font


# ── TOML section models (1-to-1 with config.toml) ─────────────────────────────

class WindowSection(BaseModel):
    title: str = "FLY-OUT"
    min_width: int = Field(default=800, ge=0)

class AppearanceSection(BaseModel):
    background_color: int = 0x00000080
    cenimatic_bars: bool = True

class DroneSection(BaseModel):
    enable_trail: bool = True
    position_randomness: int = Field(default=5, ge=0, le=32)

class SizingSection(BaseModel):
    spacing: int = Field(default=32, ge=0)
    padding: tuple[int, int] = (50, 80)

class OtherSection(BaseModel):
    enable_help_tip: bool = True
    help_tip_text: str = ""

class AppConfig(BaseModel):
    window: WindowSection = Field(default_factory=WindowSection)
    appearance: AppearanceSection = Field(default_factory=AppearanceSection)
    drone: DroneSection = Field(default_factory=DroneSection)
    sizing: SizingSection = Field(default_factory=SizingSection)
    other: OtherSection = Field(default_factory=OtherSection)

    @classmethod
    def load(cls, path: str = "config.toml") -> AppConfig:
        with open(path, "rb") as f:
            return cls.model_validate(tomllib.load(f))

# ── Runtime config (TOML values + map-derived computed fields) ─────────────────

class RenderConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # From TOML
    window_title: str
    background_color: int
    cenimatic_bars: bool
    enable_help_tip: bool
    help_tip_text: str
    enable_drone_trail: bool
    drone_position_randomness: int

    # Computed from map + TOML
    window_size: tuple[int, int]
    min_coord: tuple[int, int]
    paddin: tuple[int, int]
    cell: int
    space: int

    # Runtime-loaded
    font: dict[str, Any]   # Glyph
    shapes: type           # Shapes

    @classmethod
    def from_mapdata(cls, mapdata: MapData, config_path: str = "config.toml") -> RenderConfig:
        cfg = AppConfig.load(config_path)

        min_x, max_x, min_y, max_y = mapdata.bounding_box
        map_width  = max_x - min_x + 1
        map_height = max_y - min_y + 1

        shapes   = Shapes
        hub_size = max(shapes.hub._size())
        spacing  = cfg.sizing.spacing

        pad_x = max(0,  cfg.sizing.padding[0])
        pad_y = max(80, cfg.sizing.padding[1])

        abs_width  = map_width  * hub_size + spacing * (map_width  - 1) + pad_x * 2
        abs_height = map_height * hub_size + spacing * (map_height - 1) + pad_y * 2

        if abs_width < cfg.window.min_width:
            abs_width = cfg.window.min_width
            pad_x = (abs_width - (map_width * hub_size + spacing * (map_width - 1))) // 2

        return cls(
            window_title=cfg.window.title,
            background_color=cfg.appearance.background_color,
            cenimatic_bars=cfg.appearance.cenimatic_bars,
            enable_help_tip=cfg.other.enable_help_tip,
            help_tip_text=cfg.other.help_tip_text,
            enable_drone_trail=cfg.drone.enable_trail,
            drone_position_randomness=cfg.drone.position_randomness,
            window_size=(abs_width, abs_height),
            min_coord=(min_x, min_y),
            paddin=(pad_x, pad_y),
            cell=hub_size,
            space=spacing,
            font=load_font(),
            shapes=shapes,
        )
