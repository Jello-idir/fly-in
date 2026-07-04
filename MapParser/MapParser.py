import re
from pydantic import BaseModel, Field, computed_field, model_validator
from Common import (
    DroneBase,
    HubBase,
    ConnectionBase,
    HubMetadata,
    HubType,
    ColorType,
    ZoneType,
)


class MapData(BaseModel):
    """ class to represent the map data

    Raises:
        ValueError: if one of various validation errors occur.
    """
    nb_drones: int = Field(gt=0)
    hubs: dict[str, HubBase]
    connections: list[ConnectionBase]
    drones: dict[int, DroneBase]

    @computed_field
    @property
    def bounding_box(self) -> tuple[int, int, int, int]:
        """ property to return the bounding box of the map

        Returns:
            tuple[int, int, int, int]: (min_x, max_x, min_y, max_y) of the map
        """
        if not self.hubs:
            return (0, 0, 0, 0)
        min_x = min(hub.pos[0] for hub in self.hubs.values())
        max_x = max(hub.pos[0] for hub in self.hubs.values())
        min_y = min(hub.pos[1] for hub in self.hubs.values())
        max_y = max(hub.pos[1] for hub in self.hubs.values())
        return (min_x, max_x, min_y, max_y)

    @model_validator(mode="after")
    def validate_map(self) -> "MapData":
        """ validate the map data after model initialization

        Raises:
            ValueError: if no hubs or connections are defined,
            or if there is more than a single start_hub and end_hub,
        Returns:
            MapData: the validated map data
        """
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
            raise ValueError(
                f"must have exactly one start_hub, "
                f"found {counts['start_hub']}."
            )
        if counts["end_hub"] != 1:
            raise ValueError(
                f"must have exactly one end_hub, "
                f"found {counts['end_hub']}."
            )

        return self

    @classmethod
    def from_file(cls, file_path: str) -> "MapData":
        """ create a MapData instance from a map file

        Args:
            file_path (str): path to the map file

        Raises:
            ValueError: if the map file is invalid or contains errors

        Returns:
            MapData: instance of MapData created from the map file
        """
        nb_drones: int = 0
        hubs: dict[str, HubBase] = {}
        connections: list[ConnectionBase] = []
        occupied_positions: set[tuple[int, int]] = set()
        connection_pairs: set[frozenset[str]] = set()

        def _handle_nb_drones(match: re.Match) -> None:
            """ handle the number of drones defined in the map file

            Args:
                match (re.Match): regex match object for the number of drones

            Raises:
                ValueError: if the number of drones is defined multiple times
            """
            nonlocal nb_drones
            nb_drones = int(match.group(1))
            if nb_drones <= 0:
                raise ValueError("number of drones must be positive.")

        def _handle_hub(match: re.Match) -> None:
            """ handle a hub defined in the map file

            Args:
                match (re.Match): regex match object for the hub definition

            Raises:
                ValueError: if the hub name is a duplicate,
                or if the metadata format is invalid,
                or if the coordinates are invalid,
                or if the hub position overlaps with another hub.
            """

            hub_type, hub_name, x, y, metadata_str = match.groups()

            if hub_name in hubs:
                raise ValueError(f"duplicate hub name '{hub_name}'.")

            metadata = None

            if metadata_str:
                metadata_str = metadata_str.strip()
                if not re.fullmatch(r"(\w+\s*=\s*\w+\s*)*", metadata_str):
                    raise ValueError(
                        "invalid hub metadata."
                    )

                metadata_dict = dict(
                    re.findall(r"(\w+)\s*=\s*(\w+)", metadata_str))

                if "color" in metadata_dict:
                    try:
                        metadata_dict["color"] = ColorType[
                            metadata_dict["color"]
                            ]
                    except KeyError:
                        raise ValueError(
                            "invalid color."
                        )

                if "zone" in metadata_dict:
                    try:
                        metadata_dict["zone"] = ZoneType(metadata_dict["zone"])
                    except ValueError:
                        raise ValueError(
                            "invalid zone."
                        )

                if extra_keys := (
                        set(metadata_dict.keys())
                        - {"zone", "color", "max_drones"}
                        ):
                    raise ValueError(
                        f"invalid metadata keys: {extra_keys}"
                    )

                try:
                    metadata = HubMetadata(**metadata_dict)
                except Exception as e:
                    raise ValueError(f"invalid metadata.\nerror: {e}")

            if metadata is None:
                metadata = HubMetadata()

            x, y = int(x), int(y)

            if (x, y) in occupied_positions:
                raise ValueError(f"overlapping hubs ({x}, {y}).")
            occupied_positions.add((x, y))

            try:
                hubs[hub_name] = HubBase(
                    name=hub_name,
                    type=HubType(hub_type),
                    pos=(x, y),
                    metadata=metadata,
                )
            except Exception as e:
                raise ValueError(
                    f"invalid hub data.\n"
                    f"error: {e}"
                )

        def _handle_connection(match: re.Match) -> None:
            """ handle a connection defined in the map file

            Args:
                match (re.Match): regex match object for the connection

            Raises:
                ValueError: if the connection is a duplicate,
                or if the hubs are not defined,
                or if the connection data is invalid,
            """

            hub_a, hub_b, cap = match.groups()

            if hub_a == hub_b:
                raise ValueError("self loop connection detected.")
            if hub_a not in hubs:
                raise ValueError(f"hub '{hub_a}' not defined.")
            if hub_b not in hubs:
                raise ValueError(f"hub '{hub_b}' not defined.")

            key = frozenset({hub_a, hub_b})
            if key in connection_pairs:
                raise ValueError("duplicate connection detected.")
            connection_pairs.add(key)

            try:
                connections.append(
                    ConnectionBase(
                        hub_a=hub_a,
                        hub_b=hub_b,
                        **({"link_capacity": int(cap)} if cap else {}),
                    )
                )
            except Exception as e:
                raise ValueError(
                    f"invalid connection data.\n"
                    f"error: {e}"
                )

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
            (?:\s+\[\s*max_link_capacity\s*=\s*(\d+)\s*\])?
            $
            """,
            re.X,
        )

        with open(file_path, "r") as file:
            first_line = None
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                first_line = line.split("#", 1)[0].strip()
                break

            if first_line is None:
                raise ValueError(
                    "map file is empty or contains only comments."
                )
            try:
                if match := m_drones.match(first_line):
                    _handle_nb_drones(match)
                else:
                    raise ValueError(
                        "first line must define nb_drones."
                    )
            except ValueError as e:
                raise ValueError(
                    f"{e}\n"
                    f"line: -> '{first_line}'"
                    )

            for line in file:

                # strip whitespace from the line
                line = line.strip()

                # skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                # remove comments from the line
                line = line.split("#", 1)[0].strip()

                try:
                    if match := m_hubs.match(line):
                        _handle_hub(match)

                    elif match := m_connections.match(line):
                        _handle_connection(match)

                    elif match := m_drones.match(line):
                        raise ValueError(
                            "nb_drones must be defined in the first line."
                            )
                    else:
                        raise ValueError("no pattern matched.")

                except ValueError as e:
                    raise ValueError(f"{e}\n"
                                     f"line: --> '{line}'")

        try:
            start_hub_pos = next(
                hub for hub in hubs.values() if hub.type == HubType.start_hub
            ).pos
        except StopIteration:
            raise ValueError("no start_hub defined.")

        return MapData(
            nb_drones=nb_drones,
            hubs=hubs,
            connections=connections,
            drones={
                i: DroneBase(id=i, coord=start_hub_pos)
                for i in range(1, nb_drones + 1)
            },
        )
