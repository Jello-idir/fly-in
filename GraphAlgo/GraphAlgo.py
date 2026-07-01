from MapParser import MapData
from Common import ZoneType, HubType
from heapq import heappop, heappush
from itertools import count, zip_longest


class Node:
    """ Node in the graph representing a hub.
    """
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
    """ Edge in the graph representing a connection between two hubs.
    """
    def __init__(
            self, name: str,
            link_capacity: int,
            node_a: Node,
            node_b: Node
            ):
        self.name = name
        self.capacity = link_capacity
        self.node_a = node_a
        self.node_b = node_b


class Drone:
    """ Drone that will navigate through the graph.
    """
    def __init__(
        self,
        id: int,
    ):
        self.id = id
        self.path: list[Node | Edge] = []


class Graph:
    """ Graph representing the network of hubs and connections,
    and managing the navigation of drones through it.
    """
    def __init__(self, mapdata: MapData):
        """ initializes the graph from the map data.

        Args:
            mapdata (MapData): The map data containing hubs,
            connections, and drones.
        """
        self.nodes: dict[str, Node] = {}
        self.edges: dict[str, Edge] = {}
        self.drons: dict[int, Drone] = {}
        self.capacity_changes: dict[int, dict[Edge | Node, int]] = {}

        for hub_name, hub in mapdata.hubs.items():
            self.nodes[hub_name] = Node(
                name=hub_name,
                capacity=hub.metadata.max_drones,
                hubtype=hub.type,
                zonetype=hub.metadata.zone,
            )

        for conn in mapdata.connections:
            edge_name = f"{conn.hub_a}-{conn.hub_b}"
            edge = Edge(
                name=edge_name,
                link_capacity=conn.link_capacity,
                node_a=self.nodes[conn.hub_a],
                node_b=self.nodes[conn.hub_b],
            )
            self.edges[edge_name] = edge
            self.nodes[conn.hub_a].cnxs.append(edge)
            self.nodes[conn.hub_b].cnxs.append(edge)

            self.nodes[conn.hub_a].adjacents.append(self.nodes[conn.hub_b])
            self.nodes[conn.hub_b].adjacents.append(self.nodes[conn.hub_a])

        for drone_id in mapdata.drones.keys():
            self.drons[drone_id] = Drone(id=drone_id)

    def dijkstra(self, start: Node, end: Node) -> list[Node | Edge]:
        """ Finds the shortest path from start node to end node,
        using a modified Dijkstra's algorithm

        Args:
            start (Node): Starting node for the pathfinding algorithm.
            end (Node): Ending node for the pathfinding algorithm.

        Raises:
            ValueError: If no path is found from start to end.

        Returns:
            list[Node | Edge]: The shortest path from start to end.
        """
        counter = count(start=1, step=2)
        # priority_counter = count(start=0, step=2)
        h: list[tuple[int, int, int, Node, list[Node | Edge]]] = [
            (1, 0, next(counter), start, [start])
        ]
        visited = set()
        while True:
            try:
                cost, priority_count, _, current, path = heappop(h)
            except IndexError:
                raise ValueError(
                    f"No path found found from {start.name} to {end.name}."
                )

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

                is_priority = -1 if adj.zone == ZoneType.priority else 0

                cnx = next(
                    (
                        c for c in current.cnxs
                        if (c.node_a == adj or c.node_b == adj)
                        )
                )

                cnx_cap = this_turn.get(cnx, cnx.capacity)
                adj_cap = this_turn.get(adj, adj.capacity)

                if adj.zone == ZoneType.restricted:
                    adj_cap = self.capacity_changes.get(cost + 1, {}).get(
                        adj, adj.capacity
                    )

                if adj.type == HubType.end_hub and adj_cap <= 0:
                    adj_cap = cnx_cap

                if adj_cap <= 0 or cnx_cap <= 0:
                    needs_wait = True

                else:
                    if adj.zone == ZoneType.restricted:
                        heappush(
                            h,
                            (
                                cost + 2,
                                priority_count,
                                next(counter),
                                adj,
                                path + [cnx, adj],
                            ),
                        )
                    else:
                        heappush(
                            h,
                            (
                                cost + 1,
                                priority_count + is_priority,
                                next(counter),
                                adj,
                                path + [adj],
                            ),
                        )
            if needs_wait:
                heappush(
                    h,
                    (
                        cost + 1,
                        priority_count,
                        next(counter),
                        current,
                        path + [current],
                    ),
                )

    def navigate_drones(self) -> None:
        """ Navigates all drones from the start hub to the end hub.

        Returns:
            None
        """
        start_node = next(
            node for node in self.nodes.values()
            if node.type == HubType.start_hub
        )
        end_node = next(
            node for node in self.nodes.values()
            if node.type == HubType.end_hub
        )

        def _nodes_to_edges_path(path: list[Node | Edge]) -> list[Edge | None]:
            """ Converts a path of nodes to a path of edges.

            Args:
                path (list[Node  |  Edge]): The path of nodes to convert.

            Returns:
                list[Edge | None]: The corresponding path of edges,
                with None for consecutive nodes that are the same.
            """
            list_of_edges: list[Edge | None] = []
            i = 0
            while i < len(path) - 1:
                src = path[i]
                dst = path[i + 1]
                if isinstance(src, Node) and isinstance(dst, Node):
                    if src == dst:
                        conn = None
                    else:
                        conn = next(
                            (
                                c
                                for c in src.cnxs
                                if (c.node_a == dst or c.node_b == dst)
                            )
                        )
                    list_of_edges.append(conn)
                elif isinstance(src, Node) and isinstance(dst, Edge):
                    list_of_edges.append(dst)
                elif isinstance(src, Edge) and isinstance(dst, Node):
                    list_of_edges.append(src)
                i += 1
            return list_of_edges

        for drone in self.drons.values():

            nodes_path = self.dijkstra(start_node, end_node)
            edges_path = _nodes_to_edges_path(nodes_path)
            drone.path = nodes_path

            for turn_id, node in enumerate(nodes_path):
                if isinstance(node, Edge):
                    continue
                if turn_id not in self.capacity_changes:
                    self.capacity_changes[turn_id] = {}
                self.capacity_changes[turn_id][node] = (
                    self.capacity_changes[turn_id].get(node, node.capacity) - 1
                )

            for turn_id, edge in enumerate(edges_path):
                if not edge:
                    continue
                turn_id = turn_id + 1
                if turn_id not in self.capacity_changes:
                    self.capacity_changes[turn_id] = {}
                self.capacity_changes[turn_id][edge] = (
                    self.capacity_changes[turn_id].get(edge, edge.capacity) - 1
                )

    def get_solution(self) -> tuple[str, str]:
        """ Generates the solution output of the drone navigation.

        Returns:
            tuple[str, str]: A tuple containing two strings:
            the first string represents the moves of the drones,
            and the second is the same as first but for Animation.
        """

        output_list: list[list[str]] = []
        animation_list: list[list[str]] = []

        for drone in self.drons.values():
            line = []
            animation_line = []
            for node_edge in drone.path[1:]:
                move = f"D{drone.id}-{node_edge.name}"
                animation_line.append(move)
                if move in line:
                    move = ""
                line.append(move)
            output_list.append(line)
            animation_list.append(animation_line)

        output_str = "\n".join(
            " ".join(row) for row in zip_longest(*output_list, fillvalue="")
        )

        animation_str = "\n".join(
            " ".join(row)
            for row in zip_longest(*animation_list, fillvalue="")
        )

        output_str = "\n".join(
            " ".join(filter(None, row.split(" ")))
            for row in output_str.splitlines()
        )

        animation_str = "\n".join(
            " ".join(filter(None, row.split(" ")))
            for row in animation_str.splitlines()
        )

        return output_str, animation_str
