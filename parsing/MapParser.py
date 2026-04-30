import re
from typing import Any

class MapParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data: dict[str, Any] = {
            "nb_drones": None,
            "hubs": {},
            "connections": [],
        }

    def parse(self) -> dict[str, Any]:
        # open file and handle errors
        # ----------------------------
        try:
            file = open(self.file_path, 'r')
        except FileNotFoundError:
            raise Exception(f"File not found: {self.file_path}")
        except Exception:
            raise Exception(f"Failed to open file: {self.file_path}")


        # accepted stuff
        accepted_hub_types = {
            "start_hub", "hub", "end_hub"
            }
        accepted_colors = {
            # basics
            "none",
            "black",
            "white",
            "gray",
            "grey",
            # reds
            "red",
            "darkred",
            "crimson",
            "maroon",
            # oranges
            "orange",
            "darkorange",
            "coral",
            "salmon",
            # yellows
            "yellow",
            "gold",
            "khaki",
            # greens
            "green",
            "darkgreen",
            "lime",
            "olive",
            "teal",
            # blues
            "blue",
            "darkblue",
            "navy",
            "cyan",
            "skyblue",
            "aqua",
            # purples
            "purple",
            "violet",
            "magenta",
            "lavender",
            "indigo",
            "plum",
            # pinks
            "pink",
            "hotpink",
            "fuchsia",
            # browns
            "brown",
            "tan",
            "beige",
            "chocolate",
            # special
            "rainbow"
        }
        accepted_zone_types = {
            "normal", "blocked", "restricted", "priority"
            }
        acceptable = {
            "hub_types": accepted_hub_types,
            "colors": accepted_colors,
            "zone_types": accepted_zone_types
        }

        # regex patterns for matching lines
        m_drones = re.compile(
            r"nb_drones\s*:\s*(\d+)\s*$")
        m_hubs = re.compile(
            r"""
            (start_hub|hub|end_hub)\s*:\s*(\w+)
            \s+(-?\d+)\s+(-?\d+)
            (?:\s+\[([^\]]*)\])?
            $
            """, re.X)
        m_connections = re.compile(
            r"""
            connection\s*:\s*(\w+)-(\w+)
            (?:\s+\[\s*max_link_capacity=(\d+)\s*\])?
            $
            """, re.X)


        for line in file:
            # strip line from whitespace
            line = line.strip()

            # if line empty or comment skip
            if not line or line.startswith("#"):
                continue

            # if line is number of drones
            elif match := m_drones.match(line):
                try:
                    self._handle_nb_drones(match)
                except ValueError as e:
                    raise ValueError(f"{e}\nline: -> {line}")

            # if line is a hub
            elif match := m_hubs.match(line):
                try:
                    self._handle_hub(match, acceptable)
                except ValueError as e:
                    raise ValueError(f"{e}\nline: -> {line}")

            # if line is a connection
            elif match := m_connections.match(line):
                try:
                    self._handle_connection(match)
                except ValueError as e:
                    raise ValueError(f"{e}\nline: -> {line}")

            # if no matches found
            else:
                raise ValueError(f"no pattern matched.\nline: -> {line}")

        # closing the file
        file.close()
        return self.data

    def _handle_nb_drones(self, match):
        if not match:
            raise ValueError("invalid number of drones format.")
        if int(match.group(1)) <= 0:
            raise ValueError("number of drones must be positive.")
        if self.data.get("nb_drones") is not None:
            raise ValueError("number of drones defined multiple times.")
        self.data["nb_drones"] = int(match.group(1))

    def _handle_hub(self, match, acceptable: dict[str, set[str]]):
        if not match:
            raise ValueError("invalid hub format.")
        hub_type, hub_name, x, y, metadata_str = match.groups()

        # check if hub already exists
        if hub_name in self.data["hubs"]:
            raise ValueError(f"duplicate hub name '{hub_name}'.")

        if hub_type not in acceptable["hub_types"]:
            raise ValueError(f"invalid hub type '{hub_type}'.")

        # default metadata values
        metadata: dict[str, str | int] = {
            "zone": "normal",
            "color": "none",
            "max_drones": "1",
        }
        # parsing metadata
        if metadata_str:
            metadata_str = metadata_str.strip()
            if not re.fullmatch(r"(\w+=\w+\s*)*", metadata_str):
                raise ValueError("invalid metadata format.")

            # converting metadata string to dict and merging with default values
            metadata = metadata | dict(re.findall(r"(\w+)=(\w+)", metadata_str))

            # validate if its all valid key and colors are valid zone is valid
            for key, value in metadata.items():
                if key == "color":
                    if value not in acceptable["colors"]:
                        raise ValueError(f"invalid color value '{value}'.")
                elif key == "zone":
                    if value not in acceptable["zone_types"]:
                        raise ValueError(f"invalid zone value '{value}'.")
                elif key == "max_drones":
                    pass
                else:
                    raise ValueError(f"invalid metadata key '{key}'.")

        # validating max_drones value if present
        try:
            metadata["max_drones"] = int(metadata["max_drones"])
        except ValueError:
            raise ValueError(f"invalid max_drones value \
                             ({metadata["max_drones"]}).")

        self.data["hubs"][hub_name] = {
            "type": hub_type,
            "pos": (int(x), int(y)),
            "metadata": metadata
        }

    def _handle_connection(self, match):
        if not match:
            raise ValueError("invalid connection format.")
        a, b, cap = match.groups()
        if cap is not None:
            cap = int(cap)
        else:
            cap = 1
        if a == b:
            raise ValueError("self loop detected.")

        # check only a and b if already in connection no matter what cap is
        if any(
            (a == conn[0] and b == conn[1]) or (a == conn[1] and b == conn[0])
            for conn in self.data["connections"]):
            raise ValueError("duplicate connection detected.")
        if cap <= 0:
            raise ValueError("capacity must be positive.")
        self.data["connections"].append((a, b, cap))

    def validate(self):
        if not self.data["hubs"]:
            raise ValueError("no hubs defined.")
        if not self.data["connections"]:
            raise ValueError("no connections defined.")

        if self.data["nb_drones"] is None:
            raise ValueError("number of drones not defined.")
        # check if there is only one start and one end
        counter = {
            "start_hub": 0,
            "end_hub": 0
        }
        for hub in self.data["hubs"].values():
            if hub["type"] == "start_hub":
                counter["start_hub"] += 1
            elif hub["type"] == "end_hub":
                counter["end_hub"] += 1
        if counter["start_hub"] != 1:
            raise ValueError(f"there must be exactly one start_hub, \
                             found {counter['start_hub']}")
        if counter["end_hub"] != 1:
            raise ValueError(f"there must be exactly one end_hub, \
                             found {counter['end_hub']}")

        # check if all hubs in connections exist
        for hub1, hub2, _ in self.data["connections"]:
            if hub1 not in self.data["hubs"]:
                raise ValueError(f"hub '{hub1}' in connections does not exist")
            if hub2 not in self.data["hubs"]:
                raise ValueError(f"hub '{hub2}' in connections does not exist")

    def calculate(self):
        if not self.data["hubs"]:
            self.data["bounding_box"] = (0, 0, 0, 0)
            return
        min_x = min(hub["pos"][0] for hub in self.data["hubs"].values())
        max_x = max(hub["pos"][0] for hub in self.data["hubs"].values())
        min_y = min(hub["pos"][1] for hub in self.data["hubs"].values())
        max_y = max(hub["pos"][1] for hub in self.data["hubs"].values())
        self.data["bounding_box"] = (min_x, max_x, min_y, max_y)
