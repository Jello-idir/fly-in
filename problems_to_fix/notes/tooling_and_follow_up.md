# Tooling and follow-up work

Source line numbers refer to the project at review time, 2026-09-28.

## Confirmed: missing linters still produce success

**Location:** [Makefile](../../Makefile), lines 41-66.

If `flake8` or `mypy` is missing, the corresponding target prints a warning and
exits successfully. During the review, `make lint` printed both missing-tool
warnings and returned exit status zero. Automation can therefore report a green
check without examining any Python code.

**Fix direction:** exit with a nonzero status in each missing-tool branch. Keep
the instructions telling the developer to install the development dependencies.

**Acceptance checks:**

- Missing `flake8` makes `make lint-flake8` fail.
- Missing `mypy` makes both mypy targets fail.
- `make lint` succeeds only when its tools actually run and pass.

## Smaller installation bookkeeping problems

**Locations:** [Makefile](../../Makefile), lines 8 and 18-33;
the tracked root `.deps_installed` file.

- `re-install` is phony and is a prerequisite of `.deps_installed`. As a result,
  `make install` always invokes pip, despite the README saying it skips an
  up-to-date installation. This does not necessarily redownload packages, but
  the advertised skip behavior is not implemented.
- `.deps_installed` is committed and is not associated with a particular virtual
  environment. Its presence cannot establish that a fresh environment contains
  the dependencies. `make run` only checks that marker before starting Python.

**Fix direction:** remove the unreliable claim/check or replace it with an
environment-specific dependency check. These are lower priority than scheduling
correctness.

## Improvements to consider after fixing the bugs

These are recommendations, not additional confirmed failures.

1. Add an independent schedule validator. For every turn, check intermediate-hub
   occupancy, link usage for the full travel duration in either direction,
   blocked zones, legal movement, and completion of every drone.
2. Turn the saved reproductions into regression tests for the desired behavior.
   The current scripts deliberately assert the old failures, so do not treat
   their successful exit as evidence of correctness after a repair.
3. Keep validation independent of the planner's `capacity_changes` dictionary.
   Reusing that dictionary as the only oracle can reproduce the same accounting
   mistake in the test.
4. Add a map-path argument and a headless solving mode. This makes it easier to
   validate maps and compare schedules without changing the main map or creating
   a graphics window.
5. Measure fleet completion time separately from individual route length. The
   [greedy-path example](../maps/greedy_paths.txt) provides a small known optimum
   to start with; avoid describing the current greedy planner as globally optimal.

## Original validation limits

No interactive graphics session was opened. Visualizer checks mock the native
window functions while exercising Python state transitions. The environment
lacked the development linters, so successful syntax parsing and the reproduction
results do not substitute for a full lint/type-check pass.
