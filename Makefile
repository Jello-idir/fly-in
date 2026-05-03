PYTHON = python3
PIP = pip3
MAIN_SCRIPT = fly-in.py

.PHONY: install run debug clean dev

install: .deps_installed

.deps_installed: requirements.txt
	$(PIP) install -r requirements.txt
	touch .deps_installed

run: .deps_installed
	@$(PYTHON) $(MAIN_SCRIPT)

debug:
	@$(PYTHON) -m pdb $(MAIN_SCRIPT)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -f .deps_installed

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict

dev:
	$(PIP) install -r requirements-dev.txt
