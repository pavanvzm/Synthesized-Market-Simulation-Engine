.PHONY: install dev test lint typecheck clean run-smoke run-sim report doctor

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/

typecheck:
	mypy src/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

run-smoke:
	sim run --config configs/smoke.yaml

run-sim:
	sim run --config configs/default.yaml

report:
	sim report --run latest --pdf reports/summary.pdf --evidently reports/drift.html

doctor:
	sim doctor

bootstrap:
	bash scripts/setup.sh
