from enum import Enum


class ColorType(int, Enum):
    # if you change this enum,
    # make sure to update the color choice for drones
    # in Visualize/Visualize.py class MlxDrone

    # basics
    white = (0xFFFFFF << 8) + 0xFF
    none = (0x3D3D3D << 8) + 0xFF
    black = (0x1F1F1F << 8) + 0xFF
    gray = (0x808080 << 8) + 0xFF

    # reds
    red = (0xCF4141 << 8) + 0xFF
    darkred = (0xB42F2F << 8) + 0xFF
    crimson = (0xFF496E << 8) + 0xFF
    maroon = (0x922424 << 8) + 0xFF

    # oranges
    orange = (0xD07D16 << 8) + 0xFF
    darkorange = (0xFF6600 << 8) + 0xFF
    coral = (0xFF6B6B << 8) + 0xFF
    brown = (0x8B4513 << 8) + 0xFF

    # yellows
    yellow = (0xCCB72E << 8) + 0xFF
    darkyellow = (0x857908 << 8) + 0xFF
    gold = (0xFFD700 << 8) + 0xFF
    khaki = (0xC3B091 << 8) + 0xFF

    # greens
    green = (0x259B3B << 8) + 0xFF
    darkgreen = (0x006400 << 8) + 0xFF
    lime = (0x229E22 << 8) + 0xFF
    teal = (0x008053 << 8) + 0xFF

    # blues
    blue = (0x1964C5 << 8) + 0xFF
    darkblue = (0x2323CC << 8) + 0xFF
    cyan = (0x02CAF2 << 8) + 0xFF
    aqua = (0x58FFFF << 8) + 0xFF

    # purples
    purple = (0xB609B6 << 8) + 0xFF
    violet = (0x7F00FF << 8) + 0xFF
    magenta = (0xEF5AB6 << 8) + 0xFF
    pink = (0xFF69B4 << 8) + 0xFF

    # special
    rainbow = 0xFFFFFF << 8


class ZoneType(str, Enum):
    normal = "normal"
    blocked = "blocked"
    restricted = "restricted"
    priority = "priority"


class HubType(str, Enum):
    start_hub = "start_hub"
    hub = "hub"
    end_hub = "end_hub"
