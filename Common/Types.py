from enum import Enum


class ColorType(int, Enum):
    # basics
    none = (0x3D3D3D << 8) + 0xFF
    black = (0x000000 << 8) + 0xFF
    white = (0xFFFFFF << 8) + 0xFF
    gray = (0x808080 << 8) + 0xFF
    grey = (0x808080 << 8) + 0xFF
    # reds
    red = (0xFF4242 << 8) + 0xFF
    darkred = (0xB42F2F << 8) + 0xFF
    crimson = (0xFF496E << 8) + 0xFF
    maroon = (0x922424 << 8) + 0xFF
    # oranges
    orange = (0xFF8C00 << 8) + 0xFF
    darkorange = (0xFF6600 << 8) + 0xFF
    coral = (0xFF6B6B << 8) + 0xFF
    salmon = (0xFA8072 << 8) + 0xFF
    # yellows
    yellow = (0xEFD633 << 8) + 0xFF
    gold = (0xFFD700 << 8) + 0xFF
    khaki = (0xC3B091 << 8) + 0xFF
    # greens
    green = (0x2BB845 << 8) + 0xFF
    darkgreen = (0x006400 << 8) + 0xFF
    lime = (0x229E22 << 8) + 0xFF
    olive = (0x808000 << 8) + 0xFF
    teal = (0x008053 << 8) + 0xFF
    # blues
    blue = (0x0000FF << 8) + 0xFF
    darkblue = (0x00008B << 8) + 0xFF
    navy = (0x000080 << 8) + 0xFF
    cyan = (0x05B9B9 << 8) + 0xFF
    skyblue = (0x87CEEB << 8) + 0xFF
    aqua = (0x00FFFF << 8) + 0xFF
    # purples
    purple = (0x800080 << 8) + 0xFF
    violet = (0x7F00FF << 8) + 0xFF
    magenta = (0xFF00FF << 8) + 0xFF
    lavender = (0xB57EDC << 8) + 0xFF
    indigo = (0x4B0082 << 8) + 0xFF
    plum = (0x8E4585 << 8) + 0xFF
    # pinks
    pink = (0xFF69B4 << 8) + 0xFF
    hotpink = (0xFF1493 << 8) + 0xFF
    fuchsia = (0xFF00FF << 8) + 0xFF
    # browns
    brown = (0x8B4513 << 8) + 0xFF
    tan = (0xD2B48C << 8) + 0xFF
    beige = (0xF5F0DC << 8) + 0xFF
    chocolate = (0xD2691E << 8) + 0xFF
    # special
    rainbow = (0xFFFFFF << 8) + 0xFF


class ZoneType(str, Enum):
    normal = "normal"
    blocked = "blocked"
    restricted = "restricted"
    priority = "priority"


class HubType(str, Enum):
    start_hub = "start_hub"
    hub = "hub"
    end_hub = "end_hub"
