NAME = fly-in
PYTHON = python3
PIP = $(PYTHON) -m pip
STAMP = $(VIRTUAL_ENV)/.fly-in-deps-installed

MYPY_FLAGS = --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

.PHONY: all $(NAME) install re-install run debug clean fclean re dev check-venv lint lint-strict lint-flake8 lint-mypy lint-mypy-strict

all: $(NAME)

$(NAME): install

check-venv:
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

lint-flake8:
	$(PYTHON) -m flake8 .

lint-mypy:
	$(PYTHON) -m mypy . $(MYPY_FLAGS)

lint-mypy-strict:
	$(PYTHON) -m mypy . --strict
