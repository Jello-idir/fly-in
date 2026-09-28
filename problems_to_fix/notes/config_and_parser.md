# Config and parser findings

These are review findings, not application changes. Run the checks from the repository root:

```bash
venv/bin/python problems_to_fix/scripts/config_checks.py
```

The script **asserts that the current bugs are present**. A passing check confirms a reproduction; it does not mean the application is correct. Once a bug is fixed, update its check to assert the desired behavior. The script creates temporary input files and does not change application files or initialize the graphical window.

## P2: Map bounds include unused space extending to the origin

**Source:** [MapParser/MapParser.py](../../MapParser/MapParser.py), lines 298–317.

The bounding box starts at `(0, 0, 0, 0)`, so its extrema always include the origin even when no hub is near it. [offset_coordinates.txt](../maps/offset_coordinates.txt) contains only hubs `(100, 100)` and `(101, 101)`. The occupied coordinate span is `2 x 2`, but `MapData.size` becomes `(102, 102)`, and the hubs retain coordinates `(100, 100)` and `(101, 101)`.

The renderer allocates images from this inflated size. With the current config the fixture produces a `11576 x 11526` window; moving the same graph to coordinates around one million produces dimensions around 112 million pixels on each axis. This can make a small valid map consume excessive memory or fail native allocation. The investigation checked the calculated sizes without allocating these images.

**Suggested fix:** Initialize bounds from actual hubs, then translate all positions by the actual minimum coordinates. A translated graph should have the same dimensions as its origin-centered equivalent.

## P2: The supplied hub-statistics toggle is silently ignored

**Sources:** [config.toml](../../config.toml), line 22; [Config/Config.py](../../Config/Config.py), lines 151–156; [Visualize/Visualize.py](../../Visualize/Visualize.py), lines 904–911.

The supplied config uses `enable_hub_stats = true`. The model and renderer use `enable_drone_count` instead. Setting the supplied flag to `false` still gives `cfg.hub.enable_drone_count == True`, so the displayed statistics remain enabled. Pydantic silently ignores the unknown key.

**Suggested fix:** Rename the supplied key to `enable_drone_count`, matching the model and README. Consider rejecting unknown configuration fields so future misspellings are reported.

## P2: Defaults in config loading do not consistently work

**Source:** [Config/Config.py](../../Config/Config.py), lines 225–240, 260–261, and 269–276.

The complete supplied config works, but these omissions fail during startup:

| Change to a temporary copy of the supplied config | Current result |
| --- | --- |
| Remove only `theme = "light"` | `FileNotFoundError` for `assets/themes/default/drone.png`; only `light` and `dark` themes are supplied. |
| Remove only `spacing = 48` | `ValidationError` for `sizing.spacing`, although calculation uses `SPACEING_DEFAULT`. |
| Remove only `min_width = 500` | `ValidationError` for `window.min_width`, although calculation uses `MINIMUM_WINDOW_WIDTH_DEFAULT`. |
| Remove the entire `[sizing]` section | `KeyError: 'sizing'` when the calculated padding is assigned. |

Fallback values are calculated locally and then the original, incomplete section dictionaries are passed to required model fields. The missing theme fallback independently names a directory that does not exist.

**Suggested fix:** Put defaults on the configuration models, validate the configuration before using it in calculations, and select a supplied theme as the default.

## P3: Three documented colors reject otherwise valid maps

**Sources:** [docs/map_file.md](../../docs/map_file.md), lines 87, 93, and 103; [Common/Types.py](../../Common/Types.py), lines 4–39; [MapParser/MapParser.py](../../MapParser/MapParser.py), lines 123–131.

The color table advertises `coral`, `khaki`, and `aqua`, but none exists in `ColorType`. Adding any of them as hub metadata, such as `[color=coral]`, causes `ValueError: invalid color`.

**Suggested fix:** Either implement those colors or remove them from the documented supported values.

## P3, latent: Drone coordinates are captured before hubs are translated

**Source:** [MapParser/MapParser.py](../../MapParser/MapParser.py), lines 291–325.

For a map with start `(-1, -1)` and end `(0, 0)`, the parsed start hub becomes `(0, 0)`, but each drone's `coord` remains `(-1, -1)`. The parser saves `start_hub_pos` before translating the hubs and uses that stale tuple when creating drones.

This is currently **masked in the visualization**: [Visualize/Visualize.py](../../Visualize/Visualize.py), lines 913–939, recalculates drone pixel positions from the start hub before attachment. It was not reproduced as a visible startup defect. It remains an inconsistent `MapData` invariant that could affect another consumer of drone coordinates.

**Suggested fix:** Obtain the start position after translating the hubs and use that position for all initial drone coordinates.
