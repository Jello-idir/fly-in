These visualizer problems were reproduced with [visual_checks.py](../scripts/visual_checks.py). No application code has been changed. Run the reproductions from the project root:

```bash
venv/bin/python problems_to_fix/scripts/visual_checks.py
```

The script currently **asserts that the bugs are present**. A successful run confirms the recorded failures; after fixing them, replace these assertions with checks for the expected behavior described below. It creates an in-memory two-hub map with one drone and invokes animation methods directly, so no map file needs to be installed as the active map.

The script uses real `ctypes` image structures and pixel buffers, but replaces the native window, loop, and key functions with a fake implementation. It still imports the MLX wrapper, so its shared library must be loadable. This verifies Python state changes and the startup attribute error; it does not verify actual window rendering, native callback compatibility, platform key delivery, or real-time animation. The key reproduction supplies two callbacks with Space held instead of generating operating-system keyboard events.

1. **P2 — Disabling trails prevents startup.**

   Source: [Visualize.py, lines 830–832](../../Visualize/Visualize.py#L830).

   Trigger: set `[drone] enable_trail = false` in a configuration used to start the visualizer. `run()` accesses `self.img_trail.trail.contents.enabled`, although `img_trail` is already an image pointer. The reproduction raises `AttributeError: 'LP_mlx_image_t' object has no attribute 'trail'` before the event loop starts.

   Fix direction: use `self.img_trail.contents.enabled`, as the T-key handler already does, and initialize visibility from the configuration.

   Acceptance checks: both `enable_trail=true` and `false` reach the event loop; false starts with the trail image disabled; pressing T once enables it and pressing T again disables it. The existing reproduction checks only the false-setting startup failure.

2. **P2 — Replaying after completion increases the turn count beyond the total.**

   Sources: [completion handling at lines 751–754](../../Visualize/Visualize.py#L751), [reset at lines 535–579](../../Visualize/Visualize.py#L535), and [R-key-only bookkeeping at lines 809–814](../../Visualize/Visualize.py#L809).

   Trigger: let the one-turn animation `D1-E` finish, allow its automatic reset to run, then press Space to replay it. The drone returns to S, but `_turns_count` stays at 1. The replay's first turn then reports **2/1**. Each replay continues increasing the numerator. Automatic reset also retains the previous trail image because only the R-key handler clears it.

   Fix direction: put all restart bookkeeping in one reset method, including the turn counter, turn-label refresh, and trail clearing. Both the automatic completion path and R should use that method. If retaining the completed scene until an explicit replay is preferred, define that behavior consistently and reset the counter before replay begins.

   Acceptance checks: after a reset the counter and label are 0/N; the first replayed turn is 1/N; repeated complete replays never exceed N; the intended trail-reset behavior is the same for automatic and manual restart. The current script demonstrates a one-turn replay producing 2/1.

3. **P2 — Reset leaves stale connection occupancy.**

   Sources: [reset clears only hub containers at lines 554–560](../../Visualize/Visualize.py#L554) and [moves append destination occupancy at lines 711–721](../../Visualize/Visualize.py#L711).

   Trigger: start a move into a connection, then press R before leaving that connection. The script uses `D1-S-E` followed by `D1-E` to isolate this state; in normal solver output it occurs while traveling toward a restricted hub. Reset returns the drone to S but leaves its reference in `Connection.drones`. Starting the same connection move again produces `[drone1, drone1]` in that container.

   Fix direction: clear every connection's drone container together with the hub containers, then place each drone in exactly one starting location. Clear any pending animation queues as part of the same reset.

   Acceptance checks: reset while approaching a connection, while located inside one, and while leaving one. After every reset, all connections and non-start hubs are empty, the start contains each drone once, and every drone's `location` is the start. Repeating this cycle must not grow any occupancy container. Current visible connection labels show capacity rather than occupancy, so the demonstrated immediate effects are corrupted state and accumulating references, not a wrong on-screen connection count.

4. **P3 — Reset displays zero drones at the populated start hub.**

   Source: [Visualize.py, lines 554–560](../../Visualize/Visualize.py#L554).

   Trigger: press R in any nonempty simulation. Reset clears hub occupancy and redraws its labels before appending the drones to the start. The script captures the start's rendered occupancy as 0 while its actual occupancy after reset is 1. The label stays stale while paused, until a later completed animation turn redraws it.

   Fix direction: redraw hub statistics after all drones have been restored to their starting locations.

   Acceptance checks: immediately after either reset path, the start label shows `nb_drones/max_drones` and every other hub shows zero occupancy. Verify this before resuming playback. Disabling hub counts is not a separate crash: their image buffers are still allocated, and statistic updates do not access window instances.

5. **P2 — Holding a toggle key can toggle it repeatedly.**

   Sources: [Space and T handling at lines 800–807](../../Visualize/Visualize.py#L800), [R handling at lines 809–814](../../Visualize/Visualize.py#L809), and [callback registration at lines 863–872](../../Visualize/Visualize.py#L863).

   Trigger: hold Space while repeated key callbacks arrive, or press another key while Space remains held. `_hook_func()` ignores the supplied event and polls all held keys on every callback. Two calls with Space held change `ANIMATING` from false to true and back to false. T has the same toggle pattern; held R can repeatedly reset in response to other callbacks.

   Fix direction: use the existing typed MLX key callback and examine the event's `key` and `action`. Apply Space, T, and R actions once on a matching `MLX_PRESS`; ignore repeats and unrelated key events for these actions. Decide separately whether speed keys should repeat. The wrapper defines the expected callback type at [MLX/libmlx.py, line 284](../../MLX/libmlx.py#L284), while the current registration creates a one-argument callback.

   Acceptance checks: press/repeat/release for Space toggles playback once; the same sequence for T changes trail visibility once; unrelated key events while a toggle key is held have no effect on that toggle; R resets once per press. Confirm the corrected callback works in a real MLX window in addition to the headless event tests. The present script confirms the state-polling problem without proving a native callback crash.
