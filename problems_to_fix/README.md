# Problems to fix

Review recorded on 2026-09-28. This directory collects the findings, reproduction
maps, scripts, and original exploratory searches from the project review.
Application fixes have not been applied.

## Start here

Fix the two capacity violations first. They allow invalid schedules, including
on the map that was present during the review. Address the trail startup crash
and reset problems next; improve schedule length after correctness is reliable.

| Priority | Finding | Explanation |
| --- | --- | --- |
| High | Restricted journeys reserve a link for only one of their two turns | [Routing](notes/routing.md) |
| High | Waiting can exceed a hub's capacity | [Routing](notes/routing.md) |
| Medium | Setting `enable_trail = false` crashes startup | [Visualizer](notes/visualizer.md) |
| Medium | Replay keeps old turn counts; reset leaves stale occupancy and statistics | [Visualizer](notes/visualizer.md) |
| Medium | Greedy route reservations can finish the fleet later than necessary | [Routing](notes/routing.md) |
| Medium | Bounds include the origin, making small offset maps produce enormous windows | [Config and parser](notes/config_and_parser.md) |
| Lower | Held keys repeatedly toggle pause and trails | [Visualizer](notes/visualizer.md) |
| Lower | The supplied `enable_hub_stats` configuration key is silently ignored | [Config and parser](notes/config_and_parser.md) |
| Tooling | `make lint` succeeds even when both linters are missing | [Tooling and follow-up work](notes/tooling_and_follow_up.md) |

The config/parser notes also preserve smaller findings: incomplete configuration
defaults, documented colors that are rejected, and stale initial drone
coordinates after map translation. The coordinate inconsistency is currently
masked by visualization initialization; it was not presented as a visible crash.

## Run the reproductions

From the project root, using its existing virtual environment:

```bash
venv/bin/python problems_to_fix/scripts/algorithm_repros.py
venv/bin/python problems_to_fix/scripts/visual_checks.py
venv/bin/python problems_to_fix/scripts/config_checks.py
```

These scripts assert that the **original bugs are present**. A successful run
confirms the findings; it does not mean the application is correct. After a fix,
the corresponding assertions should fail or be rewritten to check the desired
behavior described in the notes. They are reproduction tools, not a finished
regression suite.

The scripts resolve the project and fixture paths relative to their own files.
The visualizer checks mock window operations and do not open a GUI, but importing
the existing MLX wrapper still requires the native library and its dependencies.
Config changes made by the reproduction scripts are temporary or in memory.

## Saved maps

| Map | Purpose |
| --- | --- |
| [wait_overflow.txt](maps/wait_overflow.txt) | Three drones, normal hubs, capacity one; a waiting drone conflicts with an arrival |
| [restricted_link.txt](maps/restricted_link.txt) | Two drones share a capacity-one link during a restricted journey |
| [greedy_paths.txt](maps/greedy_paths.txt) | The current planner needs four turns; a valid three-turn schedule exists |
| [offset_coordinates.txt](maps/offset_coordinates.txt) | Two nearby hubs at coordinates 100 and 101 cause an oversized window |
| [reviewed_main_map.txt](maps/reviewed_main_map.txt) | Snapshot of the main map from the reviewed Git version; its `start-gate` link exceeds capacity during turn two |

The reviewed main-map snapshot is independent of later edits to
`put_your_map_here.txt`. The reproduction scripts do not overwrite that file.

## Original exploratory files

- [find_wait.py](investigation/find_wait.py): seeded random search across graphs
  with normal and restricted zones.
- [find_wait_normal.py](investigation/find_wait_normal.py): seeded random search
  for capacity failures using normal zones only.

These are preserved investigation scratch scripts. Prefer the small deterministic
reproductions above when working on fixes.

## Review coverage

The review checked all 14 original map files through parsing and navigation:
seven routable maps and seven invalid maps. All invalid examples were rejected
by parsing or navigation. Independent schedule checks exposed link-capacity
violations on several routable maps. The 16 application Python files parsed
successfully. Visualizer findings were reproduced with real ctypes image buffers
and mocked window calls; interactive graphics behavior was not tested.

`make lint` returned success while skipping unavailable `flake8` and `mypy`.
Consequently, the review did not establish a successful lint/type-check run.
