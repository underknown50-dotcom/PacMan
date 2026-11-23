PYTHON ?= python3
VENV ?= .venv
CONFIG ?= config.json
BIN := $(VENV)/bin

.PHONY: install run debug clean lint lint-strict test release smoke
install:
	$(PYTHON) -m venv $(VENV)
	"$(BIN)/python" -m pip install -r requirements-dev.txt

run:
	"$(BIN)/python" pac-man.py "$(CONFIG)"

debug:
	"$(BIN)/python" -m pdb pac-man.py "$(CONFIG)"

lint:
	PATH="$(abspath $(BIN)):$$PATH" flake8 .
	PATH="$(abspath $(BIN)):$$PATH" mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	PATH="$(abspath $(BIN)):$$PATH" flake8 .
	PATH="$(abspath $(BIN)):$$PATH" mypy . --strict

test:
	@if [ -d dev_tests ]; then \
		"$(BIN)/python" -m pytest dev_tests -q; \
	else \
		echo "dev_tests excluded from submission per Chapter 3.3 (not submitted or graded)."; \
	fi

smoke:
	@smoke_data=$$(mktemp -d -t pacman-smoke.XXXXXX); \
	trap 'rm -rf -- "$$smoke_data"' EXIT HUP INT TERM; \
	XDG_DATA_HOME="$$smoke_data" SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PACMAN_SMOKE_TEST=1 "$(BIN)/python" pac-man.py "$(CONFIG)"

release:
	./build_release.sh

clean:
	"$(BIN)/python" tools/clean.py
