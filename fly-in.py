import signal
import sys
from Visualize import *
from MLX.libmlx import *
from MapParser import MapData
from PixelFont import load_font
from Common import RenderConfig, Shapes
from GraphAlgo import Graph


def signal_handler(sig, frame):
    mlx.mlx_close_window(window.mlx_ptr)


def _init_render_cfg(mapdata: MapData) -> RenderConfig:

    min_x, max_x, min_y, max_y = mapdata.bounding_box

    map_width = max_x - min_x + 1
    map_height = max_y - min_y + 1

    shapes = Shapes
    hub_size = max(shapes.hub._size())

    space = hub_size
    paddin = (50, 50)

    abs_width = map_width * hub_size + space * (map_width - 1) + paddin[0] * 2
    abs_height = map_height * hub_size + space * (map_height - 1) + paddin[1] * 2

    return RenderConfig(
        window_size=(abs_width, abs_height),
        min_coord=(min_x, min_y),
        paddin=paddin,
        cell=hub_size,
        space=space,
        font=load_font(),
        shapes=shapes
    )


if __name__ == "__main__":
    # Set up signal handler for graceful exit on Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    # ---------------------------------------

    # parsing
    try:
        f = "maps/custom/" + input("map file: ") + ".txt"
        mapdata = MapData.from_file(f)
    except Exception as e:
        sys.stderr.write(f"\033[31mError:\033[0m {e}\n")
        sys.exit(1)
    #-------------------------------------


    # config init
    cfg = _init_render_cfg(mapdata)

    # mlx window init
    window = MlxWindow.from_map(mapdata, cfg)

    g = Graph(mapdata)

    g.navigate_drones()
    solution , animation_solution = g.get_solution()

    print(len(solution.splitlines()))

    window.run(solution=animation_solution)
    # -----------
