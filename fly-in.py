import signal
import sys
from Visualize import *
from MLX.libmlx import *
from MapParser import MapData
from Tools import *
from PixelFont import load_font
from Common import RenderConfig, Shapes
from GraphAlgo import Graph
import types

def signal_handler(sig, frame):
    mlx.mlx_close_window(window.mlx_ptr)


def _init_cfg(mapdata: MapData) -> RenderConfig:
    min_x, max_x, min_y, max_y = mapdata.bounding_box
    size_x = max_x - min_x + 1
    size_y = max_y - min_y + 1
    cell = 40
    space = 3
    padd_x = 2
    padd_y = 2

    space = space + 1
    cell_w = size_x * space - space + 1 + padd_x * 2
    cell_h = size_y * space - space + 1 + padd_y * 2
    width = cell_w * cell
    height = cell_h * cell

    font = load_font()

    return RenderConfig(
        width=width,
        height=height,
        cell=cell,
        cell_abs=cell,
        cell_w=cell_w,
        cell_h=cell_h,
        mid_h=cell_h // 2,
        mid_w=cell_w // 2,
        space=space,
        min_x=min_x * space,
        min_y=min_y * space,
        padd_x=padd_x,
        padd_y=padd_y,
        font=font,
        shapes=Shapes
    )


if __name__ == "__main__":
    # Set up signal handler for graceful exit on Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    # ---------------------------------------

    print("-" * 20)
    # parsing
    try:
        mapdata = MapData.from_file("maps/tst.txt")
    except Exception as e:
        sys.stderr.write(f"\033[31mError:\033[0m {e}\n")
        sys.exit(1)
    #-------------------------------------

    # config init
    cfg = _init_cfg(mapdata)

    # mlx window init
    try:
        window = MlxWindow.from_map(mapdata, cfg)
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)


    g = Graph(mapdata)

    try:
        g.navigate_drones()
    except Exception as e:
        sys.stderr.write(f"\033[31mError:\033[0m {e}\n")
        sys.exit(1)

    solution = g.solve_map()
    print("-" * 20)
    print(f"turns: {len(solution.splitlines())}")
    print("-" * 20)

    window.run(solution=solution)
    #window.display(with_name=True, with_stats=True)
    # -----------
