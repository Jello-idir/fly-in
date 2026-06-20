SHELL := /bin/bash
PYTHON = python3
PIP = pip3
MAIN_SCRIPT = fly-in.py

MYPY_FLAGS = --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

.PHONY: install run debug clean dev lint lint-flake8 lint-strict re-install lint-mypy lint-mypy-strict

define check_venv
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo -e "\033[33m!! WARNING\033[0m"; \
		echo "   Not running inside a virtual environment. Activate one first."; \
		exit 1; \
	fi
endef

install: .deps_installed

.deps_installed: re-install

re-install: requirements.txt
	$(call check_venv)
	$(PIP) install -r requirements.txt;
	touch .deps_installed;

run:
	$(call check_venv)
	@if [ ! -f ".deps_installed" ]; then \
		echo -e "\033[33m!! WARNING\033[0m";\
		echo "   Dependencies are not installed. run 'make install' to install dependencies."; \
	else \
		$(PYTHON) $(MAIN_SCRIPT); \
	fi

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +


lint-flake8:
	@if [ -z "$$(command -v flake8)" ]; then \
		echo -e "\033[33m!! WARNING\033[0m";\
		echo "   flake8 is not installed. run 'make dev' to install development dependencies."; \
		echo "   or activate a virtual envirement with flake8.."; \
	else \
		flake8 .; \
	fi

lint-mypy:
	@if [ -z "$$(command -v mypy)" ]; then \
		echo -e "\033[33m!! WARNING\033[0m";\
		echo "   mypy is not installed. run 'make dev' to install development dependencies."; \
		echo "   or activate a virtual envirement with mypy.."; \
	else \
		mypy . $(MYPY_FLAGS); \
	fi

lint-mypy-strict:
	@if [ -z "$$(command -v mypy)" ]; then \
		echo -e "\033[33m!! WARNING\033[0m";\
		echo "   mypy is not installed. run 'make dev' to install development dependencies."; \
		echo "   or activate a virtual envirement with mypy.."; \
	else \
		mypy . --strict; \
	fi

lint: lint-flake8 lint-mypy

lint-strict: lint-flake8 lint-mypy-strict

debug:
	$(call check_venv)
	$(PYTHON) -m pdb $(MAIN_SCRIPT);

dev:
	$(call check_venv)
	$(PIP) install -r requirements-dev.txt;

