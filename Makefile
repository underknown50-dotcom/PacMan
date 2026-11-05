PYTHON = python3
PIP = pip3
CONFIG = config.json

.PHONY: all install run debug clean lint lint-strict package test

all: run

install:
	$(PIP) install -r requirements.txt

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
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict
