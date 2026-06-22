from MapParser import MapData
from Common import Types
from collections import defaultdict
from heapq import heappop, heappush
from itertools import count

class Node:
    def __init__(
            self, name: str,
            capacity: int,
            hubtype: Types.HubType,
            zonetype: Types.ZoneType
            ):
        self.name = name
        self.capacity = capacity
        self.type = hubtype
        self.zone = zonetype
        self.conns: list[Edge] = []
        self.adjacents: list[Node] = []

class Edge:
    def __init__(
            self,
            name: str,
            link_capacity: int,
    ):
        self.name = name
        self.capacity = link_capacity


class Graph:
    def __init__(self, mapdata: MapData):
        self.nodes: dict[str, Node] = {}
        self.edges: dict[str, Edge] = {}
        for hub_name, hub in mapdata.hubs.items():
            self.nodes[hub_name] = Node(
                name=hub_name,
                capacity=hub.metadata.max_drones,
                hubtype=hub.type,
                zonetype=hub.metadata.zone
            )
        for conn in mapdata.connections:
            edge_name = f"{conn.hub_a}-{conn.hub_b}"
            edge = Edge(
                name=edge_name,
                link_capacity=conn.link_capacity
            )
            self.edges[edge_name] = edge
            self.nodes[conn.hub_a].conns.append(edge)
            self.nodes[conn.hub_b].conns.append(edge)

            self.nodes[conn.hub_a].adjacents.append(self.nodes[conn.hub_b])
            self.nodes[conn.hub_b].adjacents.append(self.nodes[conn.hub_a])


    def show_tree(self):
        blue = "\033[34m"
        bg_blue = "\033[44m"
        yellow = "\033[33m"
        reset = "\033[0m"

        for node in self.nodes.values():
            print("\n-----------------------------------------------")
            name = f"{bg_blue} {node.name} {reset}"
            max_drones = f"{blue}{node.capacity * "•"}{reset}"
            print(f"{name} {max_drones}")
            for edge in node.conns:
                hub_a, hub_b = edge.name.split("-")
                print(f" . {hub_a:>18}{yellow} -> {reset}{hub_b:18} {yellow}{"•" * edge.capacity}{reset}")
            print("-----------------------------------------------")

    def solve_map(self) -> str:
        start = next(node for node in self.nodes.values() if node.type == Types.HubType.start_hub)
        end = next(node for node in self.nodes.values() if node.type == Types.HubType.end_hub)
        shortest_path = self.dijkstra(start, end)

        return self.path_to_str(shortest_path)

    def path_to_str(self, path: list[Node]) -> str:
        path_str = ""
        for node in path:
            path_str += f"D1-{node.name}\n"
        print(path_str)
        return path_str


    def dijkstra(self, start: Node, end: Node) -> list[Node]:
        counter = count()
        h = [(0, next(counter), start, [])]
        visited = set()
        while True:
            _, _, current, path = heappop(h)
            if current == end:
                return path
            if current.name in visited:
                continue
            visited.add(current.name)
            for adj in current.adjacents:
                if adj in visited:
                    continue
                if adj.zone == Types.ZoneType.blocked:
                    continue
                cost = 2 if adj.zone == Types.ZoneType.restricted else 2
                heappush(h, (len(path) + cost, next(counter), adj, path + [adj]))


