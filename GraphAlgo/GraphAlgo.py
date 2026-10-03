from MapParser import MapData
from Common import ZoneType, HubType
from heapq import heappop, heappush
from itertools import count, zip_longest


class Node:
    """A hub with routing capacity, zone rules, and neighbors.

    Attributes:
        name: Unique hub name.
        capacity: Configured hub occupancy limit.
        type: Hub role.
        zone: Zone access and movement-cost category.
        cnxs: Incident undirected edges.
        adjacents: Neighboring nodes.
    """

    def __init__(
            self, name: str,
            capacity: int,
            hubtype: HubType,
            zonetype: ZoneType
            ):
        """Set hub properties and initialize its connection lists.

        Args:
            name: Unique hub or connection name.
            capacity: Maximum simultaneous occupants or crossings.
            hubtype: Role of the hub in the route.
            zonetype: Access rule and arrival cost for the hub.
        """
        self.name = name
        self.capacity = capacity
        self.type = hubtype
        self.zone = zonetype
        self.cnxs: list[Edge] = []
        self.adjacents: list[Node] = []


class Edge:
    """An undirected connection with a per-turn crossing capacity.

    Attributes:
        name: Connection name formed from its endpoints.
        capacity: Maximum crossings started per turn.
        node_a: First endpoint node.
        node_b: Second endpoint node.
    """

    def __init__(
            self, name: str,
            link_capacity: int,
            node_a: Node,
            node_b: Node
            ):
        """Store the connection name, capacity, and endpoint nodes.

        Args:
            name: Unique hub or connection name.
            link_capacity: Maximum drones entering this connection in one
                turn.
            node_a: First endpoint of the undirected connection.
            node_b: Second endpoint of the undirected connection.
        """
        self.name = name
        self.capacity = link_capacity
        self.node_a = node_a
        self.node_b = node_b


class Drone:
    """A drone and its planned position for each turn.

    Attributes:
        id: Unique drone identifier.
        path: Position at each planned turn, including the starting hub.
    """

    def __init__(
        self,
        id: int,
    ):
        """Assign the drone ID and initialize an empty route.

        Args:
            id: Unique drone identifier.
        """
        self.id = id
        self.path: list[Node | Edge] = []


class Graph:
    """The hub network and reservations for scheduled drone routes.

    Attributes:
        nodes: Hub nodes indexed by name.
        edges: Undirected connections indexed by name.
        drons: Drones indexed by ID.
        capacity_changes: Remaining node and edge capacity indexed by turn.
    """

    def __init__(self, mapdata: MapData):
        """Build nodes, edges, and drones from a validated map.

        Args:
            mapdata: Validated map containing hubs, connections, and
                drones.
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
        """Find an earliest-arrival route using existing reservations.

        Args:
            start: Starting node.
            end: Destination node.

        Returns:
            list[Node | Edge]: Positions from start to end, one per turn,
                including repeated nodes for waiting and edges for
                restricted-zone transit.

        Raises:
            ValueError: No route can be found with the existing
                reservations.
        """
        counter = count(start=1, step=2)
        last_reserved_turn = max(self.capacity_changes, default=0)
        h: list[tuple[int, int, int, Node, list[Node | Edge]]] = [
            (1, 0, next(counter), start, [start])
        ]
        visited: set[tuple[str, int]] = set()
        while True:
            try:
                cost, priority_count, _, current, path = heappop(h)
            except IndexError:
                raise ValueError(
                    f"No path found from {start.name} to {end.name}."
                )

            if current == end:
                return path

            state = (current.name, cost)
            if state in visited:
                continue
            visited.add(state)

            this_turn = self.capacity_changes.get(cost, {})

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
                    continue

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
            remaining_here = this_turn.get(current, current.capacity)
            if cost <= last_reserved_turn and (
                current.type == HubType.start_hub or remaining_here > 0
            ):
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
        """Plan each drone's route and reserve hub and link capacity.

        Raises:
            ValueError: A drone cannot be routed to the destination.
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
            """Return links reserved each turn, or None for no reservation.

            Args:
                path: Route positions, one per turn.

            Returns:
                list[Edge | None]: One reservation per transition. Waiting
                    and arrival from a restricted connection have no link
                    reservation.
            """
            list_of_edges: list[Edge | None] = []
            i = 0
            while i < len(path) - 1:
                src = path[i]
                dst = path[i + 1]
                # node to node
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
                # node to edge
                elif isinstance(src, Node) and isinstance(dst, Edge):
                    list_of_edges.append(dst)
                # edge to node
                elif isinstance(src, Edge) and isinstance(dst, Node):
                    list_of_edges.append(None)
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
        """Return movement output and animation frames as turn-by-turn text.

        Returns:
            tuple[str, str]: Movement-only output and animation frames, in
                that order. Both contain one line per turn; animation
                includes waits.
        """

        output_list: list[list[str]] = []
        animation_list: list[list[str]] = []

        for drone in self.drons.values():
            line = []
            animation_line = []
            for previous, node_edge in zip(drone.path, drone.path[1:]):
                move = f"D{drone.id}-{node_edge.name}"
                animation_line.append(move)
                if node_edge is previous:
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
