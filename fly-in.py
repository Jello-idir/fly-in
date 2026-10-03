import signal
import sys
from Visualize import MlxWindow
from MLX.libmlx import mlx
from MapParser import MapData
from GraphAlgo import Graph
from Config import Config

RED = "\033[31m"
RESET = "\033[0m"
window: MlxWindow | None = None


def signal_handler(sig, frame):  # type: ignore
    """Exit on SIGINT during setup or planning; close active playback.

    Args:
        sig: Signal number supplied by Python; unused by the handler.
        frame: Interrupted stack frame, or None; unused by the handler.

    Raises:
        SystemExit: No playback loop is active; exit with status 130.
    """
    if window is None or not window.is_running:
        raise SystemExit(130)
    mlx.mlx_close_window(window.mlx_ptr)


if __name__ == "__main__":
    # Set up signal handler for graceful exit on Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # parsing
    try:
        mapdata = MapData.from_file("./put_your_map_here.txt")
    except Exception as e:
        sys.stderr.write(f"{RED}Map Error:{RESET} {e}\n")
        sys.exit(1)

    # config init
    try:
        cfg = Config.from_mapdata(mapdata)
    except Exception as e:
        sys.stderr.write(f"{RED}Config Error:{RESET} {e}\n")
        sys.exit(1)

    # mlx window init
    try:
        window = MlxWindow.from_map(mapdata, cfg)
    except Exception as e:
        sys.stderr.write(f"{RED}Window Error:{RESET} {e}\n")
        sys.exit(1)

    try:
        g = Graph(mapdata)
    except Exception as e:
        sys.stderr.write(f"{RED}Graph Error:{RESET} {e}\n")
        sys.exit(1)

    try:
        g.navigate_drones()
    except Exception as e:
        sys.stderr.write(f"{RED}Navigation Error:{RESET} {e}\n")
        window.run(solution="")
        sys.exit(1)

    try:
        solution, animation_solution = g.get_solution()
    except Exception as e:
        sys.stderr.write(f"{RED}Solution Error:{RESET} {e}\n")
        sys.exit(1)

    print(solution)

    try:
        window.run(solution=animation_solution)
    except Exception as e:
        sys.stderr.write(f"{RED}Display Error:{RESET} {e}\n")
        sys.exit(1)

    sys.exit(0)
