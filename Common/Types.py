from enum import Enum


class ColorType(int, Enum):
    """ Types of colors used in the simulation.
    """
    # main
    red = (0xE04749 << 8) + 0xFF
    green = (0x65CD28 << 8) + 0xFF
    blue = (0x4263eb << 8) + 0xFF
    yellow = (0xFAD91B << 8) + 0xFF

    orange = (0xffa500 << 8) + 0xFF
    teal = (0x008053 << 8) + 0xFF
    indigo = (0x4b369d << 8) + 0xFF
    cyan = (0x3bc9db << 8) + 0xFF
    gold = (0xFFD700 << 8) + 0xFF
    lime = (0x22B84C << 8) + 0xFF
    violet = (0x70369d << 8) + 0xFF
    brown = (0x8B4513 << 8) + 0xFF
    magenta = (0xEF5AB6 << 8) + 0xFF
    pink = (0xFF69B4 << 8) + 0xFF
    purple = (0xB609B6 << 8) + 0xFF

    darkred = (0x7F2B2C << 8) + 0xFF
    darkgreen = (0x006400 << 8) + 0xFF
    darkblue = (0x314AAE << 8) + 0xFF
    darkyellow = (0xBFA71C << 8) + 0xFF
    darkorange = (0xFF6600 << 8) + 0xFF

    none = (0x3D3D3D << 8) + 0xFF
    white = (0xFFFFFF << 8) + 0xFF
    black = (0x1F1F1F << 8) + 0xFF
    gray = (0x808080 << 8) + 0xFF

    # special
    rainbow = 0xFFFFFF << 8


class ZoneType(str, Enum):
    """ Types of zones used in the simulation.
    """
    normal = "normal"
    blocked = "blocked"
    restricted = "restricted"
    priority = "priority"


class HubType(str, Enum):
    """ Types of hubs used in the simulation.
    """
    start_hub = "start_hub"
    hub = "hub"
    end_hub = "end_hub"
