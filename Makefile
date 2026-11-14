PY := .venv/bin/python

.PHONY: setup data test web build

setup:
	python3 -m venv .venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install --only-binary=:all: -r pipeline/requirements.txt
	cd web && npm install

# Downloads are cached in data/raw, so reruns only redo the scoring.
data:
	pipeline/fetch_cdl.sh 2019 2020 2021 2022 2023 2024 2025
	$(PY) -m pipeline.hls
	$(PY) -m pipeline.run

test:
	$(PY) -m pytest -q pipeline

web:
	cd web && npm run dev

build:
	cd web && npm run build
