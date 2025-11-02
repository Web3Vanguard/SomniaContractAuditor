.PHONY: install build binary clean test

install:
	pip install -e .

build: install
	python -m build

binary: install
	python build_binary.py

clean:
	rm -rf build/ dist/ *.egg-info .eggs
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

test:
	python -m pytest

