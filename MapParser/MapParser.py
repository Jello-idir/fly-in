import re
from pydantic import BaseModel, Field, computed_field, model_validator
from Common import (
    DroneBase, HubBase, ConnectionBase, HubMetadata, HubType, ColorType, ZoneType
    )


class MapData(BaseModel):
    nb_drones: int = Field(gt=0)
    hubs: dict[str, HubBase]
    connections: list[ConnectionBase]
    drones: dict[int, DroneBase]

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
        hubs: dict[str, HubBase] = {}
        connections: list[ConnectionBase] = []

        def _handle_nb_drones(match: re.Match) -> None:
            nonlocal nb_drones

            if nb_drones is not None:
                raise ValueError("number of drones defined multiple times.")
            nb_drones = int(match.group(1))

        def _handle_hub(match: re.Match) -> None:

            hub_type, hub_name, x, y, metadata_str = match.groups()

            if hub_name in hubs:
                raise ValueError(f"duplicate hub name '{hub_name}'.")

            metadata = None

            if metadata_str:
                metadata_str = metadata_str.strip()
                if not re.fullmatch(r"(\w+=\w+\s*)*", metadata_str):
                    raise ValueError(f"invalid metadata format.\nline: -> '{match.string}'")

                metadata_dict = dict(re.findall(r"(\w+)=(\w+)", metadata_str))

                if "color" in metadata_dict:
                    try:
                        metadata_dict["color"] = ColorType[metadata_dict["color"]]
                    except KeyError:
                        raise ValueError(f"invalid color.\nline: -> '{match.string}'")

                if "zone" in metadata_dict:
                    try:
                        metadata_dict["zone"] = ZoneType(metadata_dict["zone"])
                    except ValueError:
                        raise ValueError(f"invalid zone.\nline: -> '{match.string}'")

                try:
                    metadata = HubMetadata(**metadata_dict)
                except Exception as e:
                    raise ValueError(f"invalid metadata.\nline: -> '{match.string}'")

            if metadata is None:
                metadata = HubMetadata()

            try:
                x, y = int(x), int(y)
            except ValueError:
                raise ValueError(f"invalid coordinates.\nline: -> '{match.string}'")

            if (x, y) in (hub.pos for hub in hubs.values()):
                raise ValueError(f"overlaping hubs ({x}, {y}).\nline: -> '{match.string}'")

            try:
                hubs[hub_name] = HubBase(
                    name=hub_name,
                    type=HubType(hub_type),
                    pos=(x, y),
                    metadata=metadata,
                )
            except Exception as e:
                raise ValueError(f"invalid hub data.\nline: -> '{match.string}'\nerror: {e}")

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
                    ConnectionBase(hub_a=hub_a, hub_b=hub_b,
                            **({"link_capacity": int(cap)} if cap else {})))
            except Exception as e:
                raise ValueError(f"invalid connection data.\nline: -> '{match.string}'\nerror: {e}")


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
                line = line.split("#", 1)[0].strip()
                if match := m_drones.match(line):
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

        try:
            start_hub_pos = next(
                hub for hub in hubs.values() if hub.type == HubType.start_hub
                ).pos
        except StopIteration:
            raise ValueError("no start_hub defined.")

        return MapData(
            nb_drones=nb_drones,  # type: ignore
            hubs=hubs,
            connections=connections,
            drones={
                i: DroneBase(id=i, coord=start_hub_pos)
                for i in range(1, nb_drones + 1)  # type: ignore
            }
        )
