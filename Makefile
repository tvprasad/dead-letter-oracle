PYTHON := C:/Users/AILabsByPrasad/AppData/Local/Python/bin/python.exe

.PHONY: install run test test-fast lint format check

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) main.py

test:
	$(PYTHON) -m pytest tests/ -v

test-fast:
	$(PYTHON) -m pytest tests/ -v -x

lint:
	$(PYTHON) -m ruff check . --exclude .dlq

format:
	$(PYTHON) -m ruff check . --fix --exclude .dlq

check: lint test
