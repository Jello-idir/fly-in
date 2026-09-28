"""Headless reproductions of the original visualizer bugs.

Assertions confirm bugs, so they are expected to fail after fixes. Native MLX
still needs to load; window operations are mocked and no GUI is opened.
"""
import ctypes
import importlib
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from Common import ConnectionBase, DroneBase, HubBase, HubType
from Config import Config
from MapParser import MapData
from MLX.libmlx import MLX_KEY_SPACE, mlx_image_t, mlx_instance_t

V = importlib.import_module("Visualize.Visualize")


class FakeMlx:
    held = set()

    def mlx_init(self, *args):
        return None

    def mlx_new_image(self, ptr, width, height):
        pixels = (ctypes.c_uint8 * (width * height * 4))()
        instances = (mlx_instance_t * 1)()
        image = mlx_image_t(
            width=width, height=height, pixels=pixels,
            instances=instances, count=1, enabled=True,
        )
        return ctypes.pointer(image)

    def mlx_image_to_window(self, ptr, image, x, y):
        image.contents.instances[0].x = x
        image.contents.instances[0].y = y
        return 0

    def mlx_key_hook(self, *args):
        pass

    def mlx_loop_hook(self, *args):
        pass

    def mlx_loop(self, *args):
        pass

    def mlx_terminate(self, *args):
        pass

    def mlx_is_key_down(self, ptr, key):
        return key in self.held


fake = FakeMlx()
V.mlx = fake
mapdata = MapData(
    nb_drones=1,
    hubs={
        "S": HubBase(name="S", type=HubType.start_hub, pos=(0, 0)),
        "E": HubBase(name="E", type=HubType.end_hub, pos=(1, 0)),
    },
    connections=[ConnectionBase(hub_a="S", hub_b="E")],
    drones={1: DroneBase(id=1, coord=(0, 0))},
    size=(2, 1),
)
cfg = Config.from_mapdata(mapdata)
cfg.drone.position_randomness = 0
cfg.other.enable_help_tip = False

cfg.drone.enable_trail = False
win = V.MlxWindow.from_map(mapdata, cfg)
try:
    win.run("D1-E")
except AttributeError as exc:
    print("disable_trail:", type(exc).__name__, str(exc))
else:
    raise AssertionError("Expected disabled-trail startup AttributeError")

cfg.drone.enable_trail = True
win = V.MlxWindow.from_map(mapdata, cfg)
win.run("D1-E")
V.STEPS = 1
V.STEP_IDX = 1
win._animate()
win._animate()
win._animate()
assert win.drones[1].location.name == "E"
print("after arriving:", win._turns_count, win.drones[1].location.name)
win._animate()
assert win.drones[1].location.name == "S"
print("after auto reset:", win._turns_count, win.drones[1].location.name)
win._animate()
assert win._turns_count == 2
print("replay first turn:", win._turns_count, "total:", len(win._solution.splitlines()))

win._reset_simulation()
V.ANIMATING = False
fake.held = {MLX_KEY_SPACE}
win._hook_func(None)
assert V.ANIMATING
print("space press ANIMATING:", V.ANIMATING)
win._hook_func(None)
assert not V.ANIMATING
print("space repeat ANIMATING:", V.ANIMATING)
fake.held = set()

win._solution = "D1-S-E\nD1-E"
win._reset_simulation()
win._animate()
assert len(win.connections[0].drones) == 1
print("connection before reset:", [d.id for d in win.connections[0].drones])
win._reset_simulation()
assert len(win.connections[0].drones) == 1
print("connection after reset:", [d.id for d in win.connections[0].drones])
win._animate()
assert len(win.connections[0].drones) == 2
print("connection after replay first move:", [d.id for d in win.connections[0].drones])

captured = []
win._update_hub_stats = lambda hub, **kw: captured.append((hub.name, len(hub.drones)))
win._reset_simulation()
assert ("S", 0) in captured and len(win.hubs["S"].drones) == 1
print("reset rendered counts:", captured, "actual start count:", len(win.hubs["S"].drones))

print("All five visualizer problem reproductions confirmed.")
