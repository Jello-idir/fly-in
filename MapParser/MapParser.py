import re
import sys
from pydantic import BaseModel, Field, model_validator
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
    """Validated hubs, connections, drones, and normalized map bounds.

    Attributes:
        nb_drones: Positive number of drones to route.
        hubs: Hub definitions indexed by unique name.
        connections: Validated undirected links.
        drones: Initial drone models indexed by ID.
        size: Normalized map width and height in grid cells.
    """

    nb_drones: int = Field(gt=0)
    hubs: dict[str, HubBase]
    connections: list[ConnectionBase]
    drones: dict[int, DroneBase]
    size: tuple[int, int]

    @model_validator(mode="after")
    def validate_map(self) -> "MapData":
        """Require hubs, connections, and exactly one start and end hub.

        Returns:
            MapData: This map after structural validation.

        Raises:
            ValueError: Hubs or connections are absent, or endpoint counts
                differ from exactly one start and one end.
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
        """Parse and validate a map, then normalize its grid coordinates.

        Unsupported color names produce a warning on stderr and use the
        default display color without preventing the map from loading.

        Args:
            file_path: Path to the map text file.

        Returns:
            MapData: Parsed map with nonnegative coordinates and
                initialized drones.

        Raises:
            OSError: The map file cannot be read.
            ValueError: A definition or the completed map fails validation.
        """
        nb_drones: int = 0
        hubs: dict[str, HubBase] = {}
        connections: list[ConnectionBase] = []
        occupied_positions: set[tuple[int, int]] = set()
        connection_pairs: set[frozenset[str]] = set()

        def _handle_nb_drones(match: re.Match[str]) -> None:
            """Read a positive drone count from a matched definition.

            Args:
                match: Regular-expression match for the current map
                    definition.

            Raises:
                ValueError: The drone count is not positive.
            """
            nonlocal nb_drones
            nb_drones = int(match.group(1))
            if nb_drones <= 0:
                raise ValueError("number of drones must be positive.")

        def _handle_hub(match: re.Match[str]) -> None:
            """Validate and add a hub with a unique name and position.

            Args:
                match: Regular-expression match for the current map
                    definition.

            Raises:
                ValueError: The hub duplicates a name or position, or has
                    invalid data.
            """

            hub_type, hub_name, x, y, metadata_str = match.groups()

            if hub_name in hubs:
                raise ValueError(f"duplicate hub name '{hub_name}'.")

            metadata = None

            if metadata_str:
                metadata_str = metadata_str.strip()
                if metadata_str and not re.fullmatch(
                    r"\w+\s*=\s*[^\s\[\]=]+"
                    r"(?:\s+\w+\s*=\s*[^\s\[\]=]+)*", metadata_str
                ):
                    raise ValueError(
                        "invalid hub metadata."
                    )

                metadata_dict = {}
                for key, value in re.findall(
                    r"(\w+)\s*=\s*([^\s\[\]=]+)", metadata_str
                ):
                    if key in metadata_dict:
                        raise ValueError(f"duplicate metadata key '{key}'.")
                    metadata_dict[key] = value

                if "max_drones" in metadata_dict and not re.fullmatch(
                    r"\d+", metadata_dict["max_drones"]
                ):
                    raise ValueError("max_drones must be a positive integer.")

                if "color" in metadata_dict:
                    color_name = metadata_dict["color"]
                    try:
                        metadata_dict["color"] = ColorType[color_name]
                    except KeyError:
                        sys.stderr.write(
                            f"Warning: Color '{color_name}' is not supported "
                            f"for hub '{hub_name}'; using the default color.\n"
                        )
                        metadata_dict["color"] = ColorType.none

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

        def _handle_connection(match: re.Match[str]) -> None:
            """Validate and add a link between distinct, existing hubs.

            Args:
                match: Regular-expression match for the current map
                    definition.

            Raises:
                ValueError: The link is duplicated, self-referential,
                    undefined, or has invalid capacity.
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

        m_drones = re.compile(r"nb_drones\s*:\s*(-?\d+)\s*$")
        m_hubs = re.compile(
            r"""
            (start_hub|hub|end_hub)\s*:\s*([^\s-]+)
            \s+(-?\d+)\s+(-?\d+)
            (?:\s+\[([^\]]*)\])?
            $
            """,
            re.X,
        )
        m_connections = re.compile(
            r"""
            connection\s*:\s*([^\s-]+)-([^\s-]+)
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
            start_hub = next(
                hub for hub in hubs.values() if hub.type == HubType.start_hub
            )
        except StopIteration:
            raise ValueError("no start_hub defined.")

        # Initialize bounds from a real hub so unused origin space is excluded.
        start_x, start_y = start_hub.pos
        bounding_box = (start_x, start_x, start_y, start_y)
        for hub in hubs.values():
            x, y = hub.pos
            min_x, max_x, min_y, max_y = bounding_box
            bounding_box = (
                min(min_x, x),
                max(max_x, x),
                min(min_y, y),
                max(max_y, y),
            )

        # adjusting hub position offset
        for hub in hubs.values():
            x, y = hub.pos
            hub.pos = (x - bounding_box[0], y - bounding_box[2])

        mapsize = (
            bounding_box[1] - bounding_box[0] + 1,
            bounding_box[3] - bounding_box[2] + 1
            )

        return MapData(
            nb_drones=nb_drones,
            hubs=hubs,
            connections=connections,
            drones={
                i: DroneBase(id=i, coord=start_hub.pos)
                for i in range(1, nb_drones + 1)
            },
            size=mapsize
        )
