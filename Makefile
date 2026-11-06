VENV ?= .venv

ifneq ($(wildcard $(VENV)/bin/python3),)
    PYTHON ?= $(VENV)/bin/python3
    PIP ?= $(VENV)/bin/pip
else ifneq ($(wildcard $(VENV)/Scripts/python.exe),)
    PYTHON ?= $(VENV)/Scripts/python.exe
    PIP ?= $(VENV)/Scripts/pip.exe
else
    PYTHON ?= python3
    PIP ?= pip3
endif

CONFIG ?= config.json

.PHONY: all install run debug clean lint lint-strict package test

all: run

install:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment in $(VENV)..."; \
		python3 -m venv $(VENV); \
	fi
	@if [ -f "$(VENV)/bin/pip" ]; then \
		$(VENV)/bin/pip install -r requirements.txt; \
	elif [ -f "$(VENV)/Scripts/pip.exe" ]; then \
		$(VENV)/Scripts/pip.exe install -r requirements.txt; \
	else \
		$(PIP) install -r requirements.txt; \
	fi

run:
	$(PYTHON) pac-man.py $(CONFIG)

debug:
	$(PYTHON) -m pdb pac-man.py $(CONFIG)

package:
	$(PYTHON) package.py

test:
	$(PYTHON) -m unittest discover tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf __pycache__ .mypy_cache .pytest_cache build dist

lint:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . --strict
