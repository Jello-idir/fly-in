"""Assert current parser/config bug presence without changing application files.

These are reproductions, not regression tests for correct behavior. A check will
fail after its underlying bug is fixed; update it to assert the intended result.
"""

from pathlib import Path
import os
import re
import sys
from tempfile import TemporaryDirectory


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
os.chdir(REPO)  # Config loads theme and font assets relative to the working dir.

from Config import Config  # noqa: E402
from MapParser import MapData  # noqa: E402
from pydantic import ValidationError  # noqa: E402


def replace_once(content: str, old: str, new: str) -> str:
    assert content.count(old) == 1, f"Supplied config changed: expected {old!r}"
    return content.replace(old, new, 1)


def main() -> None:
    fixture = REPO / "problems_to_fix/maps/offset_coordinates.txt"
    mapdata = MapData.from_file(str(fixture))
    xs = [hub.pos[0] for hub in mapdata.hubs.values()]
    ys = [hub.pos[1] for hub in mapdata.hubs.values()]
    occupied_span = (max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
    assert occupied_span == (2, 2)
    assert mapdata.size == (102, 102), (
        f"Bounds bug no longer reproduced: {mapdata.size=}"
    )
    loaded = Config.from_mapdata(mapdata)
    print(f"BUG PRESENT: occupied span {occupied_span}, map size {mapdata.size}, "
          f"calculated window {loaded.window_size}; no window was allocated")

    supplied_config = (REPO / "config.toml").read_text()
    with TemporaryDirectory(prefix="fly-in-config-checks-") as temporary:
        temp_dir = Path(temporary)
        config_path = temp_dir / "config.toml"

        def load_config(content: str) -> Config:
            config_path.write_text(content)
            return Config.from_mapdata(mapdata, str(config_path))

        disabled_stats = replace_once(
            supplied_config, "enable_hub_stats = true", "enable_hub_stats = false"
        )
        assert load_config(disabled_stats).hub.enable_drone_count is True, (
            "Ignored statistics flag bug no longer reproduced"
        )
        print("BUG PRESENT: enable_hub_stats=false still enables drone counts")

        no_theme = replace_once(supplied_config, 'theme = "light"', "")
        try:
            load_config(no_theme)
        except FileNotFoundError as exc:
            assert "assets/themes/default/drone.png" in str(exc), str(exc)
        else:
            raise AssertionError("Missing default theme bug no longer reproduced")
        print("BUG PRESENT: omitted theme selects missing assets/themes/default")

        for setting, location in [
            ("spacing = 48", ("sizing", "spacing")),
            ("min_width = 500", ("window", "min_width")),
        ]:
            try:
                load_config(replace_once(supplied_config, setting, ""))
            except ValidationError as exc:
                assert any(error["loc"] == location for error in exc.errors()), exc
            else:
                raise AssertionError(f"Missing default bug not reproduced: {setting}")
            print(f"BUG PRESENT: omitted {location} fails despite local fallback")

        without_sizing, count = re.subn(
            r"(?ms)^\[sizing\]\n.*?(?=^\[|\Z)", "", supplied_config
        )
        assert count == 1, "Supplied config no longer has one [sizing] section"
        try:
            load_config(without_sizing)
        except KeyError as exc:
            assert exc.args == ("sizing",), exc
        else:
            raise AssertionError("Missing sizing section bug no longer reproduced")
        print("BUG PRESENT: omitted [sizing] raises KeyError")

        map_path = temp_dir / "map.txt"
        for color in ("coral", "khaki", "aqua"):
            map_path.write_text(
                "nb_drones: 1\n"
                f"start_hub: start 0 0 [color={color}]\n"
                "end_hub: end 1 0\n"
                "connection: start-end\n"
            )
            try:
                MapData.from_file(str(map_path))
            except ValueError as exc:
                assert "invalid color" in str(exc), str(exc)
            else:
                raise AssertionError(f"Unsupported documented color fixed: {color}")
            print(f"BUG PRESENT: documented color {color!r} is rejected")

        map_path.write_text(
            "nb_drones: 1\n"
            "start_hub: start -1 -1\n"
            "end_hub: end 0 0\n"
            "connection: start-end\n"
        )
        negative_map = MapData.from_file(str(map_path))
        assert negative_map.hubs["start"].pos == (0, 0)
        assert negative_map.drones[1].coord == (-1, -1), (
            "Stale initial drone coordinate bug no longer reproduced"
        )
        print("LATENT BUG PRESENT: normalized start=(0, 0), drone=(-1, -1); "
              "visualization resets pixel position before attachment")

    print("All current bug assertions passed; no application files changed.")


if __name__ == "__main__":
    main()
