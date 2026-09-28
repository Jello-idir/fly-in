"""Reproduce the three routing bugs recorded in ../notes/routing.md.

Assertions confirm the original bugs; they are expected to fail after fixes.
Run with the project's Python environment from any working directory.
"""
from collections import Counter
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAPS = Path(__file__).resolve().parents[1] / "maps"
sys.path.insert(0, str(PROJECT_ROOT))

from GraphAlgo.GraphAlgo import Graph, Node, Edge
from MapParser import MapData
from Common import HubType

for name in ['wait_overflow', 'restricted_link', 'greedy_paths']:
    graph = Graph(MapData.from_file(str(MAPS / (name + '.txt'))))
    graph.navigate_drones()
    print(name)
    for drone in graph.drons.values():
        print(f'  D{drone.id}:', [p.name for p in drone.path])
    if name == 'wait_overflow':
        counts = Counter(d.path[2] for d in graph.drons.values())
        print('  turn 2, hub D:', counts[graph.nodes['D']], 'capacity:', graph.nodes['D'].capacity)
        assert counts[graph.nodes['D']] == 2 > graph.nodes['D'].capacity
    if name == 'restricted_link':
        counts = Counter()
        for drone in graph.drons.values():
            before, after = drone.path[1:3]
            if isinstance(before, Edge):
                counts[before] += 1
            elif isinstance(after, Edge):
                counts[after] += 1
        edge = graph.edges['S-R']
        print('  turn 2, link S-R:', counts[edge], 'capacity:', edge.capacity)
        assert counts[edge] == 2 > edge.capacity
    if name == 'greedy_paths':
        actual = max(len(d.path) - 1 for d in graph.drons.values())
        alternative = [['S','A','D','E'], ['S','B','C','E']]
        for turn in range(1, 4):
            nodes = Counter(path[turn] for path in alternative)
            for node, count in nodes.items():
                assert graph.nodes[node].type == HubType.end_hub or count <= graph.nodes[node].capacity
            links = Counter(frozenset(path[turn-1:turn+1]) for path in alternative)
            for ends, count in links.items():
                edge = next(e for e in graph.edges.values() if {e.node_a.name,e.node_b.name} == ends)
                assert count <= edge.capacity
        print('  actual makespan:', actual, 'valid alternative: 3')
        assert actual == 4
