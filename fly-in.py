import signal
import sys
from Visualize import MlxWindow
from MLX.libmlx import mlx
from MapParser import MapData
from GraphAlgo import Graph
from RenderConfig import RenderConfig


def signal_handler(sig, frame):
    mlx.mlx_close_window(window.mlx_ptr)


if __name__ == "__main__":
    # Set up signal handler for graceful exit on Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    # ---------------------------------------

    # parsing
    try:
        mapdata = MapData.from_file("./put_your_map_here.txt")
    except Exception as e:
        sys.stderr.write(f"\033[31mMap Error:\033[0m {e}\n")
        sys.exit(1)
    # -------------------------------------

    # config init
    try:
        cfg = RenderConfig.from_mapdata(mapdata)
    except Exception as e:
        sys.stderr.write(f"\033[31mConfig Error:\033[0m {e}\n")
        sys.exit(1)

    # mlx window init
    window = MlxWindow.from_map(mapdata, cfg)

    g = Graph(mapdata)

    g.navigate_drones()
    solution, animation_solution = g.get_solution()

    print(solution)
    window.run(solution=animation_solution)
    sys.exit(0)
    # ----------
