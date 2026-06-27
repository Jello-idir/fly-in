import signal
import sys
from Visualize import *
from MLX.libmlx import *
from MapParser import MapData
from PixelFont import load_font
from Common import RenderConfig, Shapes
from GraphAlgo import Graph
import types

def signal_handler(sig, frame):
    mlx.mlx_close_window(window.mlx_ptr)


def _init_render_cfg(mapdata: MapData) -> RenderConfig:

    min_x, max_x, min_y, max_y = mapdata.bounding_box

    grid_width = max_x - min_x + 1
    grid_height = max_y - min_y + 1

    shapes = Shapes

    hub_size = max(shapes.hub._size())

    space = 1
    padd_x = 1
    padd_y = 1

    space = space + 1

    abs_grid_width = grid_width * space - space + 1 + padd_x * 2
    abs_grid_height = grid_height * space - space + 1 + padd_y * 2

    abs_width = abs_grid_width * hub_size + padd_x * 2
    abs_height = abs_grid_height * hub_size + padd_y * 2

    font = load_font()

    return RenderConfig(
        width=abs_width,
        height=abs_height,
        cell=hub_size,
        cell_abs=hub_size,
        cell_w=None,
        cell_h=None,
        mid_h=abs_grid_height // 2,
        mid_w=abs_grid_width // 2,
        space=space,
        min_x=min_x * space,
        min_y=min_y * space,
        padd_x=padd_x,
        padd_y=padd_y,
        font=font,
        shapes=shapes
    )


if __name__ == "__main__":
    # Set up signal handler for graceful exit on Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    # ---------------------------------------

    # parsing
    try:
        mapdata = MapData.from_file("maps/blueprint.txt")
    except Exception as e:
        sys.stderr.write(f"\033[31mError:\033[0m {e}\n")
        sys.exit(1)
    #-------------------------------------

    multiplier = 1

    for conn in mapdata.connections:
        conn.link_capacity *= multiplier
    for hub in mapdata.hubs.values():
        hub.metadata.max_drones *= multiplier



    # config init
    cfg = _init_render_cfg(mapdata)

    # mlx window init
    window = MlxWindow.from_map(mapdata, cfg)

    g = Graph(mapdata)

    if True:
        g.navigate_drones()
        solution = g.solve_map()
    else:
        solution = open("maps/solution.txt").read()

    print(len(solution.splitlines()))

    window.run(solution=solution)
    #window.display(with_name=True, with_stats=True)
    # -----------
