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
        self.cnxs: list[Edge] = []
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
            self.nodes[conn.hub_a].cnxs.append(edge)
            self.nodes[conn.hub_b].cnxs.append(edge)

            self.nodes[conn.hub_a].adjacents.append(self.nodes[conn.hub_b])
            self.nodes[conn.hub_b].adjacents.append(self.nodes[conn.hub_a])

        for drone_id in mapdata.drones.keys():
            self.drons[drone_id] = Drone(id=drone_id)


    def dijkstra(self, start: Node, end: Node, drone: Drone) -> list[Node | Edge]:
        counter = count(start=1,step=2)
        #priority_counter = count(start=0, step=2)
        h = [(1, next(counter), start, [start])]
        visited = set()
        while True:
            try:
                cost, _, current, path = heappop(h)
            except IndexError:
                raise ValueError(f"No path found for drone {drone.id} from {start.name} to {end.name}.")

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

                adj_cap = this_turn.get(adj, adj.capacity)
                cnx = next((c for c in current.cnxs if (c.node_a == adj or c.node_b == adj)))
                cnx_cap = this_turn.get(cnx, cnx.capacity)

                if adj.type == HubType.end_hub and adj_cap <= 0:
                    adj_cap = cnx_cap

                if adj_cap <= 0 or cnx_cap <= 0:
                    needs_wait = True

                else:
                    if adj.zone == ZoneType.restricted:
                        heappush(h, (cost + 2, next(counter), adj, path + [cnx, adj]))
                    else:
                        heappush(h, (cost + 1, next(counter), adj, path + [adj]))
            if needs_wait:
                heappush(h, (cost + 1, next(counter), current, path + [current]))

    def navigate_drones(self, debug: bool = False) -> None:
        start_node = next(node for node in self.nodes.values() if node.type == HubType.start_hub)
        end_node = next(node for node in self.nodes.values() if node.type == HubType.end_hub)

        def path_to_edges_path(path: list[Node | Edge]) -> list[Edge]:
            list_of_edges: list[Edge | None] = []
            i = 0
            while i < len(path) - 1:
                src = path[i]
                dst = path[i + 1]
                if isinstance(src, Node) and isinstance(dst, Node):
                    if src == dst:
                        conn = None
                    else:
                        conn = next((c for c in src.cnxs if (c.node_a == dst or c.node_b == dst)))
                    list_of_edges.append(conn)
                elif isinstance(src, Node) and isinstance(dst, Edge):
                    list_of_edges.append(dst)
                elif isinstance(src, Edge) and isinstance(dst, Node):
                    list_of_edges.append(None)

                i += 1
            return list_of_edges

        for drone in self.drons.values():

            if debug:
                print(f"\n\n{BLUE}Reducing capacity for D{drone.id}{RESET}")
                print("-" * 20)

            nodes_path = self.dijkstra(start_node, end_node, drone)
            edges_path = path_to_edges_path(nodes_path)

            drone.path = nodes_path

            if debug:
                print("".join([f"{x:<12}" for x in range(len(nodes_path))]))
                print(f"{"".join([f"{x.name:12}" for x in nodes_path])}")
            for turn_id, node in enumerate(nodes_path):
                if turn_id not in self.capacity_changes:
                    self.capacity_changes[turn_id] = {}
                if isinstance(node, Edge):
                    node = nodes_path[turn_id + 1]
                self.capacity_changes[turn_id][node] = self.capacity_changes[turn_id].get(node, node.capacity) - 1

            if debug:
                print("".join([f"{x.name:12}" if x is not None else f"{YELLOW}{'none':12}{RESET}" for x in edges_path]))
            for turn_id, edge in enumerate(edges_path):
                if not edge:
                    continue
                turn_id = turn_id + 1
                if turn_id not in self.capacity_changes:
                    self.capacity_changes[turn_id] = {}
                self.capacity_changes[turn_id][edge] = self.capacity_changes[turn_id].get(edge, edge.capacity) - 1


    def solve_map(self) -> str:
        solution_2d_list: list[list[str]] = []
        solution_str: str = ""

        for drone in self.drons.values():
            solution_2d_list.append([f"D{drone.id}-{move.name}" for move in drone.path[1:]])

        solution_str = "\n".join(" ".join(row) for row in zip_longest(*solution_2d_list, fillvalue=""))

        return solution_str
