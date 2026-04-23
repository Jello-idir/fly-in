import re
from typing import Any


class MapParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.map_data = {}

    def parse(self) -> dict[str, Any]:
        try:
            file = open(self.file_path, 'r')
        except FileNotFoundError:
            raise Exception(f"File not found: {self.file_path}")
        except Exception:
            raise Exception(f"Failed to open file: {self.file_path}")

        nb_drones = 0
        hubs = {}
        connections = {}
        for line in file:
            if not line or line.startswith("#"):
                continue
            elif match := re.match(r"nb_drones:\s*(\d+)", line):
                nb_drones = int(match.group(1))
            elif match := re.match(
                r"(start_hub|hub|end_hub):\s*(\w+)\s+(-?\d+)\s+(-?\d+)\s+\[([^\]]*)\]", line):
                hub_type, hub_name, x, y, metadata_str = match.groups()
                metadata = {
                    "zone": "normal",
                    "color": "none",
                    "max_drones": "1",
                }
                metadata = metadata | dict(re.findall(r"(\w+)=(\w+)", metadata_str))
                hubs[hub_name] = {
                    "type": hub_type,
                    "pos": (int(x), int(y)),
                    "metadata": metadata
                }
            elif match := re.match(r"connection:\s+(\w+)-(\w+)", line):
                connection1, connection2 = match.groups()
                connections = connections | {
                    connection1: connection2
                }

        self.map_data = {
            "nb_drones": nb_drones,
            "hubs": hubs,
            "connections": connections
        }
        return self.map_data

    def get_map_data(self):
        return self.map_data
