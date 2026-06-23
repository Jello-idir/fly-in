from MapParser import MapData
from Common import ZoneType, HubType
from collections import defaultdict
from heapq import heappop, heappush
from itertools import count, zip_longest

class Node:
    def __init__(
            self, name: str,
            capacity: int,
            hubtype: HubType,
            zonetype: ZoneType
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

class Drone:
    def __init__(
            self,
            id: int,
            ):
        self.id = id
        self.path: list[Node | Edge] = []


class Graph:
    def __init__(self, mapdata: MapData):
        self.nodes: dict[str, Node] = {}
        self.edges: dict[str, Edge] = {}
        self.drons: dict[int, Drone] = {}
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
        for drone_id in mapdata.drones.keys():
            self.drons[drone_id] = Drone(id=drone_id)

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


    def dijkstra(self, start: Node, end: Node) -> list[Node | Edge]:
        counter = count(start=1,step=2)
        #priority_counter = count(start=0, step=2)
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
                if adj.zone == ZoneType.blocked:
                    continue
                if adj.zone == ZoneType.restricted:
                    conn = next(edge for edge in current.conns if adj.name in edge.name)
                    heappush(h, (len(path) + 2, next(counter), adj, path + [conn, adj]))
                else:
                    heappush(h, (len(path) + 1, next(counter), adj, path + [adj]))

    def navigate_drones(self):
        start_node = next(node for node in self.nodes.values() if node.type == HubType.start_hub)
        end_node = next(node for node in self.nodes.values() if node.type == HubType.end_hub)
        for drone in self.drons.values():
            path = self.dijkstra(start_node, end_node)
            drone.path = path

    def solve_map(self) -> str:
        solution_2d_list: list[list[str]] = []
        solution_str: str = ""

        for drone in self.drons.values():
            solution_2d_list.append([f"D{drone.id}-{move.name}" for move in drone.path])

        solution_str = "\n".join(" ".join(row) for row in zip_longest(*solution_2d_list, fillvalue=""))

        print(solution_str)
        return solution_str
