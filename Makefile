PYTHON := C:/Users/AILabsByPrasad/AppData/Local/Python/bin/python.exe

.PHONY: install run test lint

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) main.py

test:
	$(PYTHON) -m pytest tests/ -v

test-fast:
	$(PYTHON) -m pytest tests/ -v -x

lint:
	$(PYTHON) -m py_compile main.py mcp_server/*.py agent/*.py governance/*.py observability/*.py && echo "OK"
