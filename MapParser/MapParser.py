import re
from typing import Any
from pydantic import BaseModel, Field, computed_field, model_validator
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


class HubMetadata(BaseModel):
    zone: ZoneType = ZoneType.normal
    color: ColorType = ColorType.none
    max_drones: int = Field(default=1, gt=0)


class Hub(BaseModel):
    name: str
    type: HubType
    pos: tuple[int, int]
    metadata: HubMetadata = HubMetadata()


class Connection(BaseModel):
    hub_a: str
    hub_b: str
    capacity: int = Field(default=1, gt=0)

    @model_validator(mode="after")
    def no_self_loop(self):
        if self.hub_a == self.hub_b:
            raise ValueError("self loop detected.")
        return self


class MapData(BaseModel):
    nb_drones: int = Field(gt=0)
    hubs: dict[str, Hub]
    connections: list[Connection]

    @computed_field
    @property
    def bounding_box(self) -> tuple[int, int, int, int]:
        if not self.hubs:
            return (0, 0, 0, 0)
        min_x = min(hub.pos[0] for hub in self.hubs.values())
        max_x = max(hub.pos[0] for hub in self.hubs.values())
        min_y = min(hub.pos[1] for hub in self.hubs.values())
        max_y = max(hub.pos[1] for hub in self.hubs.values())
        return (min_x, max_x, min_y, max_y)

    @model_validator(mode="after")
    def validate_map(self):
        if not self.hubs:
            raise ValueError("no hubs defined.")
        if not self.connections:
            raise ValueError("no connections defined.")

        counts = {"start_hub": 0, "end_hub": 0}
        for hub in self.hubs.values():
            if hub.type == HubType.start_hub:
                counts["start_hub"] += 1
            elif hub.type == HubType.end_hub:
                counts["end_hub"] += 1
        if counts["start_hub"] != 1:
            raise ValueError(f"must have exactly one start_hub, found {counts['start_hub']}.")
        if counts["end_hub"] != 1:
            raise ValueError(f"must have exactly one end_hub, found {counts['end_hub']}.")

        for conn in self.connections:
            if conn.hub_a not in self.hubs:
                raise ValueError(f"hub '{conn.hub_a}' in connections does not exist.")
            if conn.hub_b not in self.hubs:
                raise ValueError(f"hub '{conn.hub_b}' in connections does not exist.")
        return self

    @classmethod
    def from_file(cls, file_path: str) -> "MapData":
        nb_drones: int | None = None
        hubs: dict[str, Hub] = {}
        connections: list[Connection] = []


        def _handle_nb_drones(match: re.Match) -> None:
            nonlocal nb_drones

            if nb_drones is not None:
                raise ValueError("number of drones defined multiple times.")
            nb_drones = int(match.group(1))

        def _handle_hub(match: re.Match) -> None:

            hub_type, hub_name, x, y, metadata_str = match.groups()

            if hub_name in hubs:
                raise ValueError(f"duplicate hub name '{hub_name}'.")

            metadata = HubMetadata()

            if metadata_str:
                metadata_str = metadata_str.strip()
                if not re.fullmatch(r"(\w+=\w+\s*)*", metadata_str):
                    raise ValueError(f"invalid metadata format.\n\
                                    line: -> '{match.string}'")

                metadata_dict = dict(re.findall(r"(\w+)=(\w+)", metadata_str))

                if "color" in metadata_dict:
                    try:
                        metadata_dict["color"] = ColorType[metadata_dict["color"]]
                    except KeyError:
                        raise ValueError(f"invalid color.\n\
                                        line: -> '{match.string}'")

                if "zone" in metadata_dict:
                    try:
                        metadata_dict["zone"] = ZoneType(metadata_dict["zone"])
                    except ValueError:
                        raise ValueError(f"invalid zone.\n\
                                        line: -> '{match.string}'")

                try:
                    metadata = HubMetadata(**metadata_dict)
                except Exception as e:
                    raise ValueError(f"invalid metadata.\n\
                                    line: -> '{match.string}'")

            try:
                hubs[hub_name] = Hub(
                    name=hub_name,
                    type=HubType(hub_type),
                    pos=(int(x), int(y)),
                    metadata=metadata,
                )
            except Exception as e:
                raise ValueError(f"invalid hub data.\n\
                                line: -> '{match.string}'\nerror: {e}")

        def _handle_connection(match: re.Match) -> None:

            hub_a, hub_b, cap = match.groups()
            if any(
                (hub_a == conn.hub_a and hub_b == conn.hub_b)
                or (hub_a == conn.hub_b and hub_b == conn.hub_a)
                for conn in connections
            ):
                raise ValueError("duplicate connection detected.")

            try:
                connections.append(
                    Connection(hub_a=hub_a, hub_b=hub_b,
                            **({"capacity": int(cap)} if cap else {})))
            except Exception as e:
                raise ValueError(f"invalid connection data.\n\
                                line: -> '{match.string}'\nerror: {e}")


        m_drones = re.compile(r"nb_drones\s*:\s*(\d+)\s*$")
        m_hubs = re.compile(
            r"""
            (start_hub|hub|end_hub)\s*:\s*(\w+)
            \s+(-?\d+)\s+(-?\d+)
            (?:\s+\[([^\]]*)\])?
            $
            """,
            re.X,
        )
        m_connections = re.compile(
            r"""
            connection\s*:\s*(\w+)-(\w+)
            (?:\s+\[\s*max_link_capacity=(\d+)\s*\])?
            $
            """,
            re.X,
        )

        with open(file_path, "r") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                elif match := m_drones.match(line):
                    try:
                        _handle_nb_drones(match)
                    except ValueError as e:
                        raise ValueError(f"{e}\nline: -> '{line}'")
                elif match := m_hubs.match(line):
                    try:
                        _handle_hub(match)
                    except ValueError as e:
                        raise ValueError(f"{e}\nline: -> '{line}'")
                elif match := m_connections.match(line):
                    try:
                        _handle_connection(match)
                    except ValueError as e:
                        raise ValueError(f"{e}\nline: -> '{line}'")
                else:
                    raise ValueError(f"no pattern matched.\nline: -> '{line}'")

        return MapData(
            nb_drones=nb_drones,  # type: ignore
            hubs=hubs,
            connections=connections,
        )
