from MapParser import MapData
from Common import ZoneType, HubType
from collections import defaultdict
from heapq import heappop, heappush
from itertools import count, zip_longest


BLUE = "\033[34m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"

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
            node_a: Node,
            node_b: Node
            ):
        self.name = name
        self.capacity = link_capacity
        self.node_a = node_a
        self.node_b = node_b

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
        self.capacity_changes: dict[int, dict[Edge | Node, int]] = {}

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
                link_capacity=conn.link_capacity,
                node_a=self.nodes[conn.hub_a],
                node_b=self.nodes[conn.hub_b]
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


    def dijkstra(self, start: Node, end: Node, drone: Drone) -> list[Node | Edge]:
        counter = count(start=1,step=2)
        #priority_counter = count(start=0, step=2)
        h = [(1, next(counter), start, [start])]
        visited = set()
        while True:
            cost, _, current, path = heappop(h)
            if current == end:
                return path
            state = (current.name, cost)
            if state in visited:
                continue
            visited.add(state)

            this_turn = self.capacity_changes.get(cost, {})

            needs_wait = False

            for adj in current.adjacents:
                if adj.zone == ZoneType.blocked:
                    continue
                if adj in path:
                    continue

                adj_capp = this_turn.get(adj, adj.capacity)
                conn = next((c for c in current.conns if (c.node_a == adj or c.node_b == adj)))
                conn_capp = this_turn.get(conn, conn.capacity)

                if adj.type == HubType.end_hub and adj_capp <= 0:
                    adj_capp = conn_capp

                if adj_capp <= 0 or conn_capp <= 0:
                    needs_wait = True
                else:
                    if adj.zone == ZoneType.restricted:
                        heappush(h, (cost + 2, next(counter), adj, path + [conn, adj]))
                    else:
                        heappush(h, (cost + 1, next(counter), adj, path + [adj]))
            if needs_wait:
                heappush(h, (cost + 1, next(counter), current, path + [current]))

    def navigate_drones(self):
        start_node = next(node for node in self.nodes.values() if node.type == HubType.start_hub)
        end_node = next(node for node in self.nodes.values() if node.type == HubType.end_hub)

        for drone in self.drons.values():
            path = self.dijkstra(start_node, end_node, drone)
            drone.path = path
            # updating the changes
            for turn_id, node_or_edge in enumerate(path):
                if turn_id not in self.capacity_changes:
                    self.capacity_changes[turn_id] = {}
                self.capacity_changes[turn_id][node_or_edge] = self.capacity_changes[turn_id].get(node_or_edge, node_or_edge.capacity) - 1

    def solve_map(self) -> str:
        solution_2d_list: list[list[str]] = []
        solution_str: str = ""

        for drone in self.drons.values():
            solution_2d_list.append([f"D{drone.id}-{move.name}" for move in drone.path[1:]])

        solution_str = "\n".join(" ".join(row) for row in zip_longest(*solution_2d_list, fillvalue=""))

        return solution_str
