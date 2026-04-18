# Project suite — local workflows (Unix-style paths; on Windows use .venv\Scripts\...).

PYTHON ?= python3
VENV ?= .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
SUITE_GUI := $(VENV)/bin/suite-gui

.PHONY: venv install install-gui gui test lint

venv:
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

install-gui: venv
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev,gui]"

gui: install-gui
	$(SUITE_GUI)

test: install
	$(PY) -m pytest

lint: install
	$(PY) -m ruff check src tests
	$(PY) -m ruff format --check src tests
