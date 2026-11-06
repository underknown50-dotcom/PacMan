PYTHON ?= python3
VENV ?= .venv
CONFIG ?= config.json
BIN := $(VENV)/bin

.PHONY: install run debug clean lint lint-strict test release smoke
install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m pip install -r requirements-dev.txt

run:
	$(BIN)/python pac-man.py "$(CONFIG)"

debug:
	$(BIN)/python -m pdb pac-man.py "$(CONFIG)"

lint:
	PATH="$(abspath $(BIN)):$$PATH" flake8 .
	PATH="$(abspath $(BIN)):$$PATH" mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	$(BIN)/flake8 .
	$(BIN)/mypy . --strict

test:
	$(BIN)/python -m pytest dev_tests -q

smoke:
	@smoke_data=$$(mktemp -d -t pacman-smoke.XXXXXX); \
	trap 'rm -rf -- "$$smoke_data"' EXIT HUP INT TERM; \
	XDG_DATA_HOME="$$smoke_data" SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PACMAN_SMOKE_TEST=1 $(BIN)/python pac-man.py "$(CONFIG)"

release:
	./build_release.sh

clean:
	$(BIN)/python tools/clean.py
