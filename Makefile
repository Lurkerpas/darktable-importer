PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin
PIP := $(BIN)/pip
LOCAL_BIN ?= $(HOME)/.local/bin
LOCAL_APPS ?= $(HOME)/.local/share/applications
WRAPPER := $(LOCAL_BIN)/darktable-importer
LAUNCHER_BIN := $(abspath $(BIN))/darktable-importer

.PHONY: venv install run clean

venv:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel

install: venv
	$(PIP) install .
	mkdir -p $(LOCAL_BIN)
	printf '%s\n' '#!/usr/bin/env sh' 'LAUNCHER_BIN="$(LAUNCHER_BIN)"' '[ ! -x "$$LAUNCHER_BIN" ] && { echo "Error: darktable-importer not found at $$LAUNCHER_BIN. Has the virtual environment been removed or moved?"; exit 1; }' 'exec "$$LAUNCHER_BIN" "$$@"' > $(WRAPPER)
	chmod +x $(WRAPPER)

run: install
	$(BIN)/darktable-importer

clean:
	rm -rf $(VENV)
