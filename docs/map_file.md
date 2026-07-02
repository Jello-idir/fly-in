# Map File Syntax

A map file defines the hubs network: how many drones there are, which hubs exist, and how those hubs link to each other. The parser is strict — any malformed line stops the program with an error pointing to the line that caused it.

---

## General Rules

- Encoding: plain text, one definition per line.
- `#` starts a comment — everything after it on the same line is ignored
- blank lines and comments are ignored
- Line order matters: **hubs must be defined before any connection that references them**, dont try to link unexisting hubs.

---

### Structure Overview

```
nb_drones: <n>          ← must be first non-comment line
```

```
start_hub: ...          ↑
hub: ...                │  hubs and connections in any order
end_hub: ...            │  as long as hubs come before their connections
connection: ...         ↓
```


### Number of Drones
```
nb_drones: 5   ← must be a positive integer
```


### Hubs
```
<type>: <name> <x> <y>
<type>: <name> <x> <y> [<metadata>]
```

### Hub types

```
start_hub:  ...     ←   must be exactly one, capacity in metadata is ignored
hub:        ...     ←   can be zero or more
end_hub:    ...     ←   must be exactly one, capacity in metadata is ignored
```
*start and end hub max_drones are accepted but ignored at runtime, any amount of drones can be in the start or end hub at any time.*

### Fields

```
<name>          ←   unique across all hubs, no dashes or spaces
<x> <y>         ←   integer coordinates, duplicates are rejected
```

### Hub metadata (optional)

Appended in square brackets after the coordinates:

```
hub: <name> <x> <y>    → [key=value key=value ...] ← metadata is optional
```
```
zone=...        ←   can be `normal`, `blocked`, `restricted`, or `priority`
color=...       ←   can be any of the colors in the color table below
max_drones=...  ←   positive integer, ignored for start_hub and end_hub
```

## Color Table

Used in hub metadata as `color=<name>`.

    -white
    -none
    -black
    -gray

    -red
    -darkred
    -crimson
    -maroon

    -orange
    -darkorange
    -coral
    -brown

    -yellow
    -darkyellow
    -gold
    -khaki

    -green
    -darkgreen
    -lime
    -teal

    -blue
    -darkblue
    -cyan
    -aqua

    -purple
    -violet
    -magenta
    -pink

    -rainbow


### hub definition examples

```
start_hub:  alpha  0 0
end_hub:  area51  5 3
hub:  bravo  2 1  [zone=restricted max_drones=3]
hub:  x21  4 0  [zone=priority color=teal max_drones=2]
hub:  some_place  1 2  [zone=blocked]
```

---

# 3. Connections

```
connection: <hub_a>-<hub_b>
connection: <hub_a>-<hub_b> [max_link_capacity=<positive_integer>]
```

- Both hubs must be defined **before** this line
- Connections are **undirected** — `a-b` and `b-a` are duplicates and rejected
- `max_link_capacity` sets how many drones may share the link simultaneously

### Examples

```
connection: alpha-bravo      ← default capacity of 1 if not specified
connection: bravo-some_place [max_link_capacity=3]
connection: some_place-area51 [max_link_capacity=1]
```


## Complete Example

```
nb_drones: 12

start_hub:      start       0 -1        [color=yellow]

hub:            gate        1 0         [color=blue zone=restricted max_drones=6]
hub:            hood        0 1         [color=black zone=priority]

hub:            A1          2 -1        [color=red max_drones=2 zone=restricted]
hub:            A3          2 1         [color=red max_drones=1 zone=restricted]
hub:            A2          2 0         [color=red max_drones=2 zone=restricted]

hub:            B1          3 -1        [color=blue max_drones=2]
hub:            B2          3 0         [color=orange zone=priority max_drones=30]
hub:            B3          3 1         [color=orange zone=priority]

hub:            N1          4 -1        [color=orange max_drones=3 zone=priority]
hub:            N2          4 1         [color=orange zone=priority]

end_hub:        E           5 0         [color=rainbow]


connection:    start-gate       [max_link_capacity=6]

connection:     gate-hood       [max_link_capacity=4]

connection:     gate-A3         [max_link_capacity=1]
connection:     gate-A1         [max_link_capacity=2]
connection:     gate-A2         [max_link_capacity=1]

connection:     A3-B3           [max_link_capacity=1]
connection:     A1-B1           [max_link_capacity=2]
connection:     A2-B2           [max_link_capacity=1]

connection:     B3-N2           [max_link_capacity=1]
connection:     B1-N1           [max_link_capacity=1]
connection:     B2-N1           [max_link_capacity=2]

connection:     B1-B2           [max_link_capacity=6]
connection:     B2-N2           [max_link_capacity=1]
connection:     A3-B2           [max_link_capacity=1]

connection:     N1-E            [max_link_capacity=3]
connection:     B2-E            [max_link_capacity=3]
connection:     N2-E            [max_link_capacity=1]
```
---

# WHY IM I GETTING AN ERROR?
check the line number in the error message, it will point to the exact line that is malformed, check for typos, missing fields, or invalid values.

### Possible errors:

    -nb_drones not the first line
    -nb_drones appears more than once
    -Duplicate hub name
    -Duplicate hub coordinates
    -Not exactly one `start_hub`
    -Not exactly one `end_hub`
    -Connection references an undefined hub
    -Duplicate connection (`a-b` / `b-a`)
    -Invalid zone type
    -Invalid color name
    -Non-positive `max_drones` or `max_link_capacity`
    -Malformed metadata block
    -Unrecognised line
