NAME = fly-in
PYTHON = python3
PIP = $(PYTHON) -m pip
STAMP = $(VIRTUAL_ENV)/.fly-in-deps-installed

MYPY_FLAGS = --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

.PHONY: all $(NAME) install re-install run debug clean fclean re dev check-python check-venv check-mypy lint lint-strict lint-flake8 lint-mypy lint-mypy-strict

all: $(NAME)

$(NAME): install

check-python:
	@$(PYTHON) -c "import sys; sys.exit(sys.version_info < (3, 10))" || (echo "Python 3.10+ is required. Activate a virtual environment created with Python 3.10 or newer."; exit 1)

check-venv: check-python
	@test -n "$(VIRTUAL_ENV)" || (echo "Activate a virtual environment first."; exit 1)

install: check-venv
	@if [ ! -f "$(STAMP)" ] || [ requirements.txt -nt "$(STAMP)" ] || [ "$(VIRTUAL_ENV)/pyvenv.cfg" -nt "$(STAMP)" ]; then \
		$(PIP) install -r requirements.txt && touch "$(STAMP)"; \
	fi

re-install: check-venv
	$(RM) "$(STAMP)"
	$(MAKE) install

run: install
	PYDANTIC_ERRORS_INCLUDE_URL=0 $(PYTHON) $(NAME).py

debug: install
	$(PYTHON) -m pdb $(NAME).py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

fclean: clean
	@if [ -n "$(VIRTUAL_ENV)" ]; then $(RM) "$(STAMP)"; fi

re:
	$(MAKE) fclean
	$(MAKE) all

dev: check-venv
	$(PIP) install -r requirements-dev.txt

lint: lint-flake8 lint-mypy

lint-strict: lint-flake8 lint-mypy-strict

lint-flake8: check-python
	@$(PYTHON) -c "import flake8" 2>/dev/null || (echo "flake8 is missing. Run 'make dev' to install development dependencies."; exit 1)
	$(PYTHON) -m flake8 .

check-mypy: check-python
	@$(PYTHON) -c "import mypy, pydantic, PIL, tomli" 2>/dev/null || (echo "Lint dependencies are missing. Run 'make dev' in your active virtual environment."; exit 1)

lint-mypy: check-mypy
	$(PYTHON) -m mypy . $(MYPY_FLAGS)

lint-mypy-strict: check-mypy
	$(PYTHON) -m mypy . --strict
