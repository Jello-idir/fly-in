# Confirmed routing problems

These findings were reproduced during the project review on 2026-09-28. P1 means the scheduler can produce an invalid schedule; P2 means it produces an avoidably slower schedule.

The reproduction maps are self-contained. Run the bundled checker from the project root:

```bash
PYTHONPATH=. venv/bin/python problems_to_fix/scripts/algorithm_repros.py
```

**The [reproduction script](../scripts/algorithm_repros.py) asserts the current buggy behavior. A successful run confirms these bugs; it does not certify scheduler correctness. After fixing a problem, replace its assertions with the acceptance criteria below.**

## P1: Waiting can exceed hub capacity

Source: [GraphAlgo/GraphAlgo.py](../../GraphAlgo/GraphAlgo.py), lines 186–196, especially the unconditional wait transition at lines 193–194.

Reproduction: [wait_overflow.txt](../maps/wait_overflow.txt). It has three drones, only normal hubs, and capacity 1 for every hub and link. Connections, in file order, are `S-B`, `S-C`, `S-D`, `A-B`, `A-D`, `A-E`, and `C-D`.

The current scheduler returns the following paths. Each column after turn 0 is one elapsed turn; `—` means the drone has already finished.

| Drone | Turn 0 | Turn 1 | Turn 2 | Turn 3 | Turn 4 | Turn 5 |
| --- | --- | --- | --- | --- | --- | --- |
| D1 | S | B | A | E | — | — |
| D2 | S | C | D | A | E | — |
| D3 | S | D | D | D | A | E |

At turn 2, D2 arrives at D while D3 waits there: **2 drones occupy a hub whose capacity is 1**. The search checks destination capacity for movement but does not check whether staying at the current hub conflicts with an arrival reserved by another drone. The later reservation step can therefore reduce a hub's remaining capacity below zero.

Fix direction: treat waiting as a transition that consumes capacity at the current hub at the resulting turn, while preserving unlimited occupancy at the start and end hubs. Reject a conflicting wait and allow the search to choose a route or delay upstream that remains legal. In the current indexing scheme, a popped state with `cost` represents position at turn `cost - 1`, so its wait needs available hub capacity at turn `cost`.

Acceptance criteria:

- All three drones reach E on this map.
- At every turn, each ordinary hub's total occupancy is at most its configured capacity, including drones that wait.
- D2 and D3 never occupy D together. Delaying departures at S is a valid solution.
- An independent schedule checker validates waits and arrivals together; checking only movement destinations is insufficient.

## P1: Restricted journeys reserve their link for only one of two turns

Source: [GraphAlgo/GraphAlgo.py](../../GraphAlgo/GraphAlgo.py), line 149 checks link availability for just one turn; lines 164–173 create a two-turn restricted journey; lines 245–246 emit no link reservation for its second step; lines 265–273 then skip that step.

Reproduction: [restricted_link.txt](../maps/restricted_link.txt). Two drones travel `S-R-E`; R is restricted and can hold two drones, while each link has capacity 1.

| Drone | Turn 0 | Turn 1 | Turn 2 | Turn 3 | Turn 4 |
| --- | --- | --- | --- | --- | --- |
| D1 | S | S-R | R | E | — |
| D2 | S | S | S-R | R | E |

During turn 2, D1 completes its second traversal step on `S-R` while D2 starts its first traversal step on the same link. **Two drones travel on a capacity-1 link simultaneously.** Checking only end-of-turn positions hides this overlap because D1 reaches R at the end of that turn.

This also affected the original `put_your_map_here.txt` reviewed in the session: an independent checker found **10 simultaneous travelers on `start-gate`, capacity 6, during turn 2**. The user subsequently edited that root map; this historical observation should not be assumed to describe its current contents. The small reproduction map above remains the stable evidence.

Fix direction: check and reserve the same link for every turn of a restricted traversal, including the edge-to-hub step. Updating reservations alone is insufficient if admission still checks only the departure turn. Continue checking the restricted destination's capacity at the actual arrival turn.

Acceptance criteria:

- Both drones finish the reproduction map without any link exceeding capacity during any traversal interval.
- D2 cannot start traversing `S-R` until turn 3 if D1 starts on turn 1; the earliest fleet completion is turn 5.
- Capacity checks cover all occupied turns in both traversal directions and account for overlapping normal and restricted movements on an undirected link.
- The schedule checker counts both the first and second traversal steps, rather than counting only explicit `Edge` entries at turn boundaries.

## P2: Permanent greedy routes produce avoidably slower fleet schedules

Source: [GraphAlgo/GraphAlgo.py](../../GraphAlgo/GraphAlgo.py), lines 250–273, where each drone's individually selected path is committed before planning the next drone.

Reproduction: [greedy_paths.txt](../maps/greedy_paths.txt). It has two drones, normal hubs, capacity 1 throughout, and connections `S-A`, `S-B`, `A-C`, `A-D`, `B-C`, `C-E`, and `D-E`.

| Schedule | D1 path | D2 path | Fleet completion |
| --- | --- | --- | --- |
| Current output | `S-A-C-E` | `S-B-B-C-E` | 4 turns |
| Valid alternative | `S-A-D-E` | `S-B-C-E` | 3 turns |

The first choice uses resources from both routes that could otherwise run in parallel. Since earlier paths are never reconsidered, D2 must wait. Both alternative paths respect every hub and link capacity, and each shortest route requires three moves, so three turns is optimal for this map. This demonstrates that individual earliest-arrival routes do not guarantee earliest completion of the fleet.

Fix direction: after correcting capacity accounting, consider route reassignment or a global scheduling method. For example, a time-expanded flow model can represent movement, waiting, hub capacities, and shared link capacities over candidate completion times. Any implementation must preserve the two-turn restricted traversal rules and the intended priority-zone preference. If retaining a greedy heuristic, document that it does not guarantee minimum fleet completion time.

Acceptance criteria:

- The two drones complete this map in three turns using a legal schedule.
- A validator checks the proposed schedule independently of the pathfinding implementation.
- For claims of global optimality, compare small generated maps against an exhaustive or exact solver; this one example alone cannot establish that guarantee.
