VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(PYTHON) -m pip
CONFIG ?= config.json
# Prefer Python 3.13 when installed; allow overriding via PYTHON_BIN=...
PYTHON_BIN ?= $(shell command -v python3.13 || command -v python3)

.PHONY: install run debug clean lint package zip check-python

$(PYTHON):
	@command -v $(PYTHON_BIN) >/dev/null || { echo "Python not found. Install Python 3.13."; exit 1; }
	$(PYTHON_BIN) -m venv $(VENV)

check-python: $(PYTHON)
	@$(PYTHON) -c 'import sys; sys.exit("ERROR: This .venv uses Python 3.14+, but pygame==2.6.1 requires an older supported Python. Run: rm -rf .venv && make install (with Python 3.13 installed).") if sys.version_info >= (3, 14) else None'

install: check-python
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install packages/*.whl

# Running an already installed game must not reinstall packages every time.
run: check-python
	$(PYTHON) pac-man.py $(CONFIG)

debug: check-python
	$(PYTHON) -m pdb pac-man.py $(CONFIG)

clean:
	rm -rf src/__pycache__
	rm -rf koia/__pycache__
	rm -rf .mypy_cache

lint:
	flake8 . --exclude=.venv
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports \
		--disallow-untyped-defs --check-untyped-defs

package: check-python
	$(PYTHON) -m PyInstaller --noconfirm --clean PacMan.spec

zip: package
	cd dist && rm -f PacMan-linux.zip && zip -r PacMan-linux.zip PacMan
