PY := .venv/bin/python

.PHONY: setup data test web build

setup:
	python3 -m venv .venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install --only-binary=:all: -r pipeline/requirements.txt
	cd web && npm install

# Each pipeline step is added here as it is built.
data:
	@echo "No pipeline steps yet."

test:
	$(PY) -m pytest -q pipeline

web:
	cd web && npm run dev

build:
	cd web && npm run build
